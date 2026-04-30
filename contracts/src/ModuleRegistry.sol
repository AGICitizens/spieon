// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

contract ModuleRegistry {
    enum Severity { Low, Medium, High, Critical }

    struct Module {
        address author;
        string metadataURI;
        Severity severityCap;
        bytes32 owaspId;
        bytes32 atlasTechniqueId;
        bytes32 maestroId;
        uint64 registeredAt;
        uint128 timesUsed;
        uint128 successCount;
        bool exists;
    }

    address public owner;
    mapping(bytes32 => Module) private _modules;
    bytes32[] private _moduleHashes;

    event ModuleRegistered(
        bytes32 indexed moduleHash,
        address indexed author,
        Severity severityCap,
        string metadataURI,
        bytes32 owaspId,
        bytes32 atlasTechniqueId
    );
    event ModuleUsed(bytes32 indexed moduleHash, bool succeeded);
    event MetadataUpdated(bytes32 indexed moduleHash, string metadataURI);
    event OwnershipTransferred(address indexed previous, address indexed next);

    error AlreadyRegistered();
    error UnknownModule();
    error NotAuthor();
    error NotOwner();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor() {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);
    }

    function transferOwnership(address next) external onlyOwner {
        emit OwnershipTransferred(owner, next);
        owner = next;
    }

    function register(
        bytes32 moduleHash,
        string calldata metadataURI,
        Severity severityCap,
        bytes32 owaspId,
        bytes32 atlasTechniqueId,
        bytes32 maestroId
    ) external returns (bytes32) {
        if (_modules[moduleHash].exists) revert AlreadyRegistered();
        _modules[moduleHash] = Module({
            author: msg.sender,
            metadataURI: metadataURI,
            severityCap: severityCap,
            owaspId: owaspId,
            atlasTechniqueId: atlasTechniqueId,
            maestroId: maestroId,
            registeredAt: uint64(block.timestamp),
            timesUsed: 0,
            successCount: 0,
            exists: true
        });
        _moduleHashes.push(moduleHash);
        emit ModuleRegistered(
            moduleHash,
            msg.sender,
            severityCap,
            metadataURI,
            owaspId,
            atlasTechniqueId
        );
        return moduleHash;
    }

    function updateMetadata(bytes32 moduleHash, string calldata metadataURI) external {
        Module storage module = _modules[moduleHash];
        if (!module.exists) revert UnknownModule();
        if (module.author != msg.sender) revert NotAuthor();
        module.metadataURI = metadataURI;
        emit MetadataUpdated(moduleHash, metadataURI);
    }

    function recordUsage(bytes32 moduleHash, bool succeeded) external onlyOwner {
        Module storage module = _modules[moduleHash];
        if (!module.exists) revert UnknownModule();
        unchecked {
            module.timesUsed += 1;
            if (succeeded) module.successCount += 1;
        }
        emit ModuleUsed(moduleHash, succeeded);
    }

    function isRegistered(bytes32 moduleHash) external view returns (bool) {
        return _modules[moduleHash].exists;
    }

    function getModule(bytes32 moduleHash) external view returns (Module memory) {
        Module memory m = _modules[moduleHash];
        if (!m.exists) revert UnknownModule();
        return m;
    }

    function moduleHashes(uint256 cursor, uint256 limit)
        external
        view
        returns (bytes32[] memory page, uint256 nextCursor)
    {
        uint256 total = _moduleHashes.length;
        if (cursor >= total) {
            return (new bytes32[](0), total);
        }
        uint256 end = cursor + limit;
        if (end > total) end = total;
        page = new bytes32[](end - cursor);
        for (uint256 i = cursor; i < end; ++i) {
            page[i - cursor] = _moduleHashes[i];
        }
        nextCursor = end;
    }

    function totalModules() external view returns (uint256) {
        return _moduleHashes.length;
    }
}
