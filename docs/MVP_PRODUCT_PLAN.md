# Infinite Trading Intelligence — MVP Plan

## Product
A read-only crypto/DeFi intelligence service that combines market, wallet, liquidity, portfolio and risk data into one dashboard. No customer funds are moved in MVP.

## MVP scope
1. Market data: Coinbase/public market data and approved public blockchain/DEX sources.
2. Wallet monitoring: address-based balances and transaction history; no private keys.
3. Portfolio analytics: valuation, P&L, allocation, concentration and volatility metrics.
4. Liquidity intelligence: pool TVL/volume/liquidity and basic opportunity scoring.
5. Risk engine: transparent, deterministic scores with explainable inputs.
6. Alerts: configurable thresholds and webhook/notification delivery.
7. API: read-only endpoints for dashboard and future customers.

## Explicitly out of scope
- Autonomous trading.
- Customer private-key custody.
- Automatic withdrawals.
- Unrestricted exchange orders.
- Smart-contract deployment from the application.
- AI-controlled money movement.

## Architecture
- Python: data adapters and analytics.
- TypeScript: web/API product layer as it is introduced.
- Solidity: protocol contracts remain isolated from the SaaS MVP.
- R: research/backtesting only; never a production request dependency.

## Revenue path
Free: one wallet + basic analytics.
Pro: multi-wallet monitoring, alerts, advanced analytics and opportunity/risk views.
Business: API, webhooks, scheduled reports and team access.

## Acceptance criteria
- All MVP endpoints are read-only.
- No secret is stored in source control.
- Unit tests cover normalization and scoring.
- Integration tests use mocks/fixtures by default.
- External API failures degrade safely.
- Every score is explainable from recorded inputs.

## Legal/IP gate
The repository is a public fork and currently has no `LICENSE` file even though the existing README references an MIT license and contains an upstream copyright notice. Commercialization of upstream-derived code must remain blocked until licensing/ownership rights are verified.
