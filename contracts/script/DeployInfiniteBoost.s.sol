// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/src/Script.sol";
import {console} from "forge-std/src/console.sol";
import {InfiniteBoost} from "../src/InfiniteBoost.sol";

// ─────────────────────────────────────────────────────────────────────────────
//  Deploy InfiniteBoost on Optimism
//
//  All parameters are supplied via environment variables.
//
//  Required env vars:
//    DEPLOYER_PRIVATE_KEY         – deployer wallet private key (no 0x prefix)
//    ITP_TOKEN_ADDRESS            – ITP reward token (paid to stakers)
//    VELO_TOKEN_ADDRESS           – VELO / base reward token (claimed by DAO)
//    WETH_TOKEN_ADDRESS           – WETH on Optimism
//    USDT_TOKEN_ADDRESS           – Connector token (USDC on Optimism)
//    ROUTER_ADDRESS               – Velodrome V2 router
//    ORACULE_ADDRESS              – 1inch Spot Price Aggregator
//    ITP_DAO                      – DAO multisig; becomes owner
//    RPC_URL                      – Optimism mainnet RPC endpoint
//    API_KEY_OPTIMISTIC_ETHERSCAN – OP Etherscan key (only needed for --verify)
//
//  ── Pre-filled values (see .env) ────────────────────────────────────────────
//    ITP_TOKEN_ADDRESS  = 0x0a7B751FcDBBAA8BB988B9217ad5Fb5cfe7bf7A0
//    VELO_TOKEN_ADDRESS = 0x9560e827aF36c94D2Ac33a39bCE1Fe78631088Db
//    WETH_TOKEN_ADDRESS = 0x4200000000000000000000000000000000000006
//    USDT_TOKEN_ADDRESS = 0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85  (USDC)
//    ROUTER_ADDRESS     = 0xa062aE8A9c5e11aaA026fc2670B0D65cCc8B2858  (Velodrome V2)
//    ORACULE_ADDRESS    = 0x59BCE8a6c8D9Bc7Db3e4B3aB97A0a1cB3aa9E47b  (1inch v5)
//
//  ── One-line deploy + verify ─────────────────────────────────────────────────
//    source .env && forge script script/DeployInfiniteBoost.s.sol \
//      --rpc-url $RPC_URL --broadcast --verify \
//      --etherscan-api-key $API_KEY_OPTIMISTIC_ETHERSCAN -vvvv
//
//  ── Dry-run (no broadcast, no gas) ──────────────────────────────────────────
//    source .env && forge script script/DeployInfiniteBoost.s.sol \
//      --rpc-url $RPC_URL -vvvv
// ─────────────────────────────────────────────────────────────────────────────

contract DeployInfiniteBoost is Script {

    function run() external {
        uint256 deployerKey = vm.envUint("DEPLOYER_PRIVATE_KEY");

        address boostRewardToken = vm.envAddress("ITP_TOKEN_ADDRESS");
        address baseRewardToken  = vm.envAddress("VELO_TOKEN_ADDRESS");
        address weth             = vm.envAddress("WETH_TOKEN_ADDRESS");
        address connectorToken   = vm.envAddress("USDT_TOKEN_ADDRESS");
        address router           = vm.envAddress("ROUTER_ADDRESS");
        address oracle           = vm.envAddress("ORACULE_ADDRESS");
        address owner            = vm.envAddress("ITP_DAO");

        address deployer = vm.addr(deployerKey);

        console.log("=== InfiniteBoost Deployment ===");
        console.log("Deployer:          ", deployer);
        console.log("boostRewardToken:  ", boostRewardToken);
        console.log("baseRewardToken:   ", baseRewardToken);
        console.log("weth:              ", weth);
        console.log("connectorToken:    ", connectorToken);
        console.log("router:            ", router);
        console.log("oracle:            ", oracle);
        console.log("owner (ITP DAO):   ", owner);

        vm.startBroadcast(deployerKey);

        InfiniteBoost booster = new InfiniteBoost(
            boostRewardToken,
            baseRewardToken,
            weth,
            connectorToken,
            router,
            oracle,
            owner
        );

        vm.stopBroadcast();

        console.log("--------------------------------------");
        console.log("Deployed at:       ", address(booster));
        console.log("Owner:             ", booster.owner());
        console.log("boostRewardToken:  ", address(booster.boostRewardToken()));
        console.log("baseRewardToken:   ", address(booster.baseRewardToken()));
        console.log("feePercentage:     ", booster.feePercentage());
    }
}
