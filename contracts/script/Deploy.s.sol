// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script, console2} from "forge-std/Script.sol";
import {ModuleRegistry} from "../src/ModuleRegistry.sol";
import {BountyPool, IERC20} from "../src/BountyPool.sol";

contract DeploySpieon is Script {
    function run() external returns (ModuleRegistry registry, BountyPool pool) {
        address agent = vm.envAddress("AGENT_ADDRESS");
        address usdc = vm.envOr("X402_USDC_ADDRESS", address(0x036CbD53842c5426634e7929541eC2318f3dCF7e));

        vm.startBroadcast();
        registry = new ModuleRegistry();
        pool = new BountyPool(agent, IERC20(usdc), registry);
        vm.stopBroadcast();

        console2.log("ModuleRegistry deployed at", address(registry));
        console2.log("BountyPool deployed at", address(pool));
        console2.log("Agent (payout caller)", agent);
    }
}
