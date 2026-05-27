/**
 * ITP Dashboard — Contract Configuration
 * Fill in contract addresses after deployment, then reload the dashboard.
 */
window.ITP_CONFIG = {
  dao: "0xfbC61F8A651622B82829046afb3f10AF666c19e1",

  contracts: {
    // ── Base mainnet ────────────────────────────────────────────────────────
    UniV3AutoCompounder: {
      address: "",          // paste address after: forge script DeployUniV3AutoCompounder.s.sol
      network: "base",
      rpc:     "https://mainnet.base.org",
      chainId: 8453,
    },

    // ── Optimism mainnet ────────────────────────────────────────────────────
    InfiniteBoost: {
      address: "",          // paste address after: forge script DeployInfiniteBoost.s.sol
      network: "optimism",
      rpc:     "https://mainnet.optimism.io",
      chainId: 10,
    },

    AutoCompoundVault: {
      address: "",          // paste address after: forge script DeployAutoCompoundVault.s.sol
      network: "optimism",
      rpc:     "https://mainnet.optimism.io",
      chainId: 10,
    },
  },

  // ── RPC endpoints (public, no key needed for reads) ──────────────────────
  rpc: {
    ethereum: "https://cloudflare-eth.com",
    base:     "https://mainnet.base.org",
    optimism: "https://mainnet.optimism.io",
  },
};
