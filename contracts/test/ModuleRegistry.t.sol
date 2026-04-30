// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {ModuleRegistry} from "../src/ModuleRegistry.sol";

contract ModuleRegistryTest is Test {
    ModuleRegistry registry;
    address author = address(0xA11CE);
    bytes32 sampleHash = keccak256("native.x402-replay-attack");

    function setUp() public {
        registry = new ModuleRegistry();
    }

    function test_register_writes_module() public {
        vm.prank(author);
        registry.register(
            sampleHash,
            "ipfs://meta",
            ModuleRegistry.Severity.High,
            bytes32("API07"),
            bytes32("AML.T0049"),
            bytes32(0)
        );
        assertTrue(registry.isRegistered(sampleHash));
        ModuleRegistry.Module memory m = registry.getModule(sampleHash);
        assertEq(m.author, author);
        assertEq(uint8(m.severityCap), uint8(ModuleRegistry.Severity.High));
    }

    function test_double_register_reverts() public {
        vm.startPrank(author);
        registry.register(sampleHash, "uri", ModuleRegistry.Severity.High, 0, 0, 0);
        vm.expectRevert(ModuleRegistry.AlreadyRegistered.selector);
        registry.register(sampleHash, "uri", ModuleRegistry.Severity.High, 0, 0, 0);
        vm.stopPrank();
    }

    function test_record_usage_only_owner() public {
        vm.prank(author);
        registry.register(sampleHash, "uri", ModuleRegistry.Severity.High, 0, 0, 0);

        vm.prank(author);
        vm.expectRevert(ModuleRegistry.NotOwner.selector);
        registry.recordUsage(sampleHash, true);

        registry.recordUsage(sampleHash, true);
        registry.recordUsage(sampleHash, false);
        ModuleRegistry.Module memory m = registry.getModule(sampleHash);
        assertEq(m.timesUsed, 2);
        assertEq(m.successCount, 1);
    }
}
