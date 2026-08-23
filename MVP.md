# Infinite Trading Intelligence MVP

## Product
A read-only crypto/DeFi portfolio intelligence service: valuation, concentration risk, market data adapters, liquidity/opportunity ranking, and alerts as the next layer.

## Runtime safety
- `READ_ONLY_MODE=true` by default.
- `EXECUTION_ENABLED=false` by default.
- No private keys, seed phrases, banking credentials, or exchange secrets are stored in Git.
- Live execution is intentionally absent from the MVP API.

## Current API
- `GET /health`
- `GET /capabilities`
- `POST /v1/portfolio/analyze`

## Example
```bash
curl -X POST http://127.0.0.1:8000/v1/portfolio/analyze \
  -H 'content-type: application/json' \
  -d '{"holdings":[{"symbol":"ETH","quantity":2,"price_usd":2000},{"symbol":"USDC","quantity":1000,"price_usd":1}]}'
```

## Architecture
`apps/api` -> `src/python/api` -> `services/analytics` and `services/market_data`.

Existing protocol contracts and trading research remain outside the MVP runtime. Execution should only be introduced after independent security, licensing, and operational review.

## Commercial gate
Before a paid launch, verify provenance, license, trademark, copyright, and rights to commercialize upstream-derived code. The current repository's README references MIT licensing but the fork's licensing/provenance should be made explicit and verified.
