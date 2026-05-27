// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/src/Script.sol";
import {console} from "forge-std/src/console.sol";
import {AutoCompoundVault} from "../src/autocompounder.sol";

// ─────────────────────────────────────────────────────────────────────────────
//  Deploy AutoCompoundVault on Optimism
//
//  The vault's token / pool / gauge addresses are hardcoded in the contract
//  to the live Optimism mainnet values:
//    USDC:          0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85
//    ITP:           0x0a7B751FcDBBAA8BB988B9217ad5Fb5cfe7bf7A0
//    VELO:          0x9560e827aF36c94D2Ac33a39bCE1Fe78631088Db
//    Velodrome V2:  0xa062aE8A9c5e11aaA026fc2670B0D65cCc8B2858
//    ITP-USDC pool: 0xB84C932059A49e82C2c1bb96E29D59Ec921998Be
//    Staking gauge: 0x571E95563A6798C76144c8C5ed293406Ed81A437
//
//  Required env vars:
//    DEPLOYER_PRIVATE_KEY         – deployer wallet private key (no 0x prefix)
//    KEEPER_ADDRESS               – address authorised to call autoCompound()
//    RPC_URL                      – Optimism mainnet RPC endpoint
//    API_KEY_OPTIMISTIC_ETHERSCAN – OP Etherscan key (only needed for --verify)
//
//  ── One-line deploy + verify ─────────────────────────────────────────────────
//    source .env && forge script script/DeployAutoCompoundVault.s.sol \
//      --rpc-url $RPC_URL --broadcast --verify \
//      --etherscan-api-key $API_KEY_OPTIMISTIC_ETHERSCAN -vvvv
//
//  ── Dry-run (no broadcast, no gas) ──────────────────────────────────────────
//    source .env && forge script script/DeployAutoCompoundVault.s.sol \
//      --rpc-url $RPC_URL -vvvv
// ─────────────────────────────────────────────────────────────────────────────

contract DeployAutoCompoundVault is Script {

    function run() external {
        uint256 deployerKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        address keeper      = vm.envAddress("KEEPER_ADDRESS");

        address deployer = vm.addr(deployerKey);

        console.log("=== AutoCompoundVault Deployment ===");
        console.log("Deployer:  ", deployer);
        console.log("Keeper:    ", keeper);
        console.log("Network:   Optimism");
        console.log("USDC:      0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85");
        console.log("ITP:       0x0a7B751FcDBBAA8BB988B9217ad5Fb5cfe7bf7A0");
        console.log("VELO:      0x9560e827aF36c94D2Ac33a39bCE1Fe78631088Db");
        console.log("DEX:       0xa062aE8A9c5e11aaA026fc2670B0D65cCc8B2858");
        console.log("LP Pool:   0xB84C932059A49e82C2c1bb96E29D59Ec921998Be");
        console.log("Gauge:     0x571E95563A6798C76144c8C5ed293406Ed81A437");

        vm.startBroadcast(deployerKey);

        AutoCompoundVault vault = new AutoCompoundVault(keeper);

        vm.stopBroadcast();

        console.log("--------------------------------------");
        console.log("Deployed at:  ", address(vault));
        console.log("Keeper:       ", vault.chainlinkKeeper());
    }
}
