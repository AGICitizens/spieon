// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {ModuleRegistry} from "../src/ModuleRegistry.sol";
import {BountyPool, IERC20} from "../src/BountyPool.sol";

contract MockUSDC is IERC20 {
    mapping(address => uint256) public balances;

    function mint(address to, uint256 amount) external {
        balances[to] += amount;
    }

    function balanceOf(address who) external view returns (uint256) {
        return balances[who];
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        balances[msg.sender] -= amount;
        balances[to] += amount;
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        balances[from] -= amount;
        balances[to] += amount;
        return true;
    }
}

contract BountyPoolTest is Test {
    ModuleRegistry registry;
    BountyPool pool;
    MockUSDC usdc;

    address agent = address(0xA9E47);
    address author = address(0xA11CE);
    address recipient = address(0xBEEF);

    bytes32 moduleHash = keccak256("module-1");

    function setUp() public {
        registry = new ModuleRegistry();
        usdc = new MockUSDC();
        pool = new BountyPool(agent, IERC20(address(usdc)), registry);

        vm.prank(author);
        registry.register(
            moduleHash, "uri", ModuleRegistry.Severity.High, 0, 0, 0
        );
        usdc.mint(address(pool), 100_000_000); // $100
    }

    function _request(uint256 amount, BountyPool.Severity sev, bytes32 uid)
        internal
        view
        returns (BountyPool.PayoutRequest memory)
    {
        return BountyPool.PayoutRequest({
            scanId: bytes32("scan-1"),
            moduleHash: moduleHash,
            attestationUid: uid,
            severity: sev,
            amountUsdc6: amount,
            recipient: recipient
        });
    }

    function test_payout_succeeds_within_severity_cap() public {
        BountyPool.PayoutRequest memory req = _request(
            2_000_000, BountyPool.Severity.High, bytes32("uid-1")
        );
        vm.prank(agent);
        pool.payout(req);
        assertEq(usdc.balanceOf(recipient), 2_000_000);
        assertTrue(pool.attestationConsumed(req.attestationUid));
    }

    function test_payout_above_severity_cap_reverts() public {
        BountyPool.PayoutRequest memory req = _request(
            3_000_000, BountyPool.Severity.High, bytes32("uid-2")
        );
        vm.prank(agent);
        vm.expectRevert(BountyPool.AmountAboveSeverityCap.selector);
        pool.payout(req);
    }

    function test_replay_same_attestation_reverts() public {
        BountyPool.PayoutRequest memory req = _request(
            2_000_000, BountyPool.Severity.High, bytes32("uid-3")
        );
        vm.startPrank(agent);
        pool.payout(req);
        vm.expectRevert(BountyPool.AlreadyPaid.selector);
        pool.payout(req);
        vm.stopPrank();
    }

    function test_daily_cap_blocks_after_threshold() public {
        // critical $5 cap; daily $10 cap → third payout in same day reverts.
        vm.startPrank(agent);
        pool.payout(_request(5_000_000, BountyPool.Severity.Critical, bytes32("u1")));
        pool.payout(_request(5_000_000, BountyPool.Severity.Critical, bytes32("u2")));
        BountyPool.PayoutRequest memory bust = _request(
            500_000, BountyPool.Severity.Medium, bytes32("u3")
        );
        vm.expectRevert(BountyPool.AmountAboveDailyCap.selector);
        pool.payout(bust);
        vm.stopPrank();
    }

    function test_outsized_payout_requires_cosign() public {
        pool.setSeverityCap(BountyPool.Severity.Critical, 50_000_000);
        pool.setModuleDailyCap(50_000_000);

        BountyPool.PayoutRequest memory req = _request(
            25_000_000, BountyPool.Severity.Critical, bytes32("uid-out")
        );

        vm.prank(agent);
        vm.expectRevert(BountyPool.CosignerRequired.selector);
        pool.payout(req);

        pool.setCosigner(address(this));

        vm.prank(agent);
        pool.payoutWithCosign(req);
        assertEq(usdc.balanceOf(recipient), 25_000_000);
    }

    function test_unregistered_module_reverts() public {
        BountyPool.PayoutRequest memory req = _request(
            1_000_000, BountyPool.Severity.High, bytes32("uid-x")
        );
        req.moduleHash = keccak256("ghost-module");

        vm.prank(agent);
        vm.expectRevert(BountyPool.UnknownModule.selector);
        pool.payout(req);
    }

    function test_only_agent_can_payout() public {
        BountyPool.PayoutRequest memory req = _request(
            1_000_000, BountyPool.Severity.High, bytes32("uid-y")
        );
        vm.prank(author);
        vm.expectRevert(BountyPool.NotAgent.selector);
        pool.payout(req);
    }
}
