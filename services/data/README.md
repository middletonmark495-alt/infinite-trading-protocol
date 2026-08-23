# Data service boundary

Existing market/DeFi integrations should be wrapped behind stable read-only interfaces before the dashboard depends on them.

Initial domains:

- market data
- blockchain balances
- transactions
- liquidity/pool data
- gas/network cost data

Provider adapters should normalize external responses into internal schemas and never leak provider-specific payloads through the public API.
