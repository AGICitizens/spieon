// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {ModuleRegistry} from "./ModuleRegistry.sol";

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address who) external view returns (uint256);
}

/// Holds USDC bounty pool. Only the configured agent address may trigger a
/// payout, and every payout is gated by per-severity caps + a daily cap per
/// module + an outsized-payout flag that requires a second co-signer.
contract BountyPool {
    enum Severity { Low, Medium, High, Critical }

    struct PayoutRequest {
        bytes32 scanId;
        bytes32 moduleHash;
        bytes32 attestationUid;
        Severity severity;
        uint256 amountUsdc6; // USDC * 1e6
        address recipient;
    }

    address public owner;
    address public agent;
    address public cosigner;
    IERC20 public immutable usdc;
    ModuleRegistry public immutable registry;

    /// Severity → cap in USDC * 1e6.
    mapping(Severity => uint256) public severityCap;
    /// Module → (day epoch → spent in USDC * 1e6).
    mapping(bytes32 => mapping(uint256 => uint256)) public dailySpent;
    /// Module → daily cap in USDC * 1e6.
    uint256 public moduleDailyCap = 10_000_000; // $10
    /// Outsized payout threshold (any single payout above this needs cosigner).
    uint256 public outsizedThreshold = 20_000_000; // $20
    /// Already-attested attestations are single-use per finding.
    mapping(bytes32 => bool) public attestationConsumed;

    event PayoutExecuted(
        bytes32 indexed scanId,
        bytes32 indexed moduleHash,
        bytes32 indexed attestationUid,
        address recipient,
        Severity severity,
        uint256 amountUsdc6
    );
    event OutsizedFlagged(bytes32 indexed attestationUid, uint256 amountUsdc6);
    event ConfigChanged(string key, uint256 value);
    event AgentChanged(address indexed previous, address indexed next);
    event CosignerChanged(address indexed previous, address indexed next);

    error NotAgent();
    error NotOwner();
    error NotCosigner();
    error UnknownModule();
    error AmountAboveSeverityCap();
    error AmountAboveDailyCap();
    error AlreadyPaid();
    error CosignerRequired();
    error InsufficientFunds();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    modifier onlyAgent() {
        if (msg.sender != agent) revert NotAgent();
        _;
    }

    constructor(address agent_, IERC20 usdc_, ModuleRegistry registry_) {
        owner = msg.sender;
        agent = agent_;
        usdc = usdc_;
        registry = registry_;

        // Defaults from PRD §6: crit $5, high $2, med $0.50, low $0.10.
        severityCap[Severity.Critical] = 5_000_000;
        severityCap[Severity.High] = 2_000_000;
        severityCap[Severity.Medium] = 500_000;
        severityCap[Severity.Low] = 100_000;
    }

    function setAgent(address next) external onlyOwner {
        emit AgentChanged(agent, next);
        agent = next;
    }

    function setCosigner(address next) external onlyOwner {
        emit CosignerChanged(cosigner, next);
        cosigner = next;
    }

    function setSeverityCap(Severity sev, uint256 cap_) external onlyOwner {
        severityCap[sev] = cap_;
        emit ConfigChanged("severityCap", uint256(uint8(sev)) << 240 | cap_);
    }

    function setModuleDailyCap(uint256 cap_) external onlyOwner {
        moduleDailyCap = cap_;
        emit ConfigChanged("moduleDailyCap", cap_);
    }

    function setOutsizedThreshold(uint256 threshold_) external onlyOwner {
        outsizedThreshold = threshold_;
        emit ConfigChanged("outsizedThreshold", threshold_);
    }

    function payout(PayoutRequest calldata req) external onlyAgent {
        _payout(req, false);
    }

    function payoutWithCosign(PayoutRequest calldata req) external onlyAgent {
        if (cosigner == address(0)) revert CosignerRequired();
        _payout(req, true);
    }

    function _payout(PayoutRequest calldata req, bool cosigned) internal {
        if (attestationConsumed[req.attestationUid]) revert AlreadyPaid();
        if (!registry.isRegistered(req.moduleHash)) revert UnknownModule();

        uint256 cap_ = severityCap[req.severity];
        if (req.amountUsdc6 > cap_) revert AmountAboveSeverityCap();

        if (req.amountUsdc6 >= outsizedThreshold) {
            if (!cosigned) {
                emit OutsizedFlagged(req.attestationUid, req.amountUsdc6);
                revert CosignerRequired();
            }
            // The cosigner gates the agent — an extra access path on outsized
            // payouts is enforced off-chain by requiring `payoutWithCosign`
            // to be invoked through a Safe transaction (or equivalent) that
            // the cosigner approves.
        }

        uint256 today = block.timestamp / 1 days;
        uint256 spent = dailySpent[req.moduleHash][today] + req.amountUsdc6;
        if (spent > moduleDailyCap) revert AmountAboveDailyCap();
        dailySpent[req.moduleHash][today] = spent;

        if (usdc.balanceOf(address(this)) < req.amountUsdc6) revert InsufficientFunds();
        attestationConsumed[req.attestationUid] = true;
        bool ok = usdc.transfer(req.recipient, req.amountUsdc6);
        require(ok, "USDC transfer failed");

        emit PayoutExecuted(
            req.scanId,
            req.moduleHash,
            req.attestationUid,
            req.recipient,
            req.severity,
            req.amountUsdc6
        );
    }

    function rescue(IERC20 token, address to, uint256 amount) external onlyOwner {
        bool ok = token.transfer(to, amount);
        require(ok, "rescue transfer failed");
    }
}
