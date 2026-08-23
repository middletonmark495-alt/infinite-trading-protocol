# Infinite Trading Intelligence MVP

## Product
A read-only crypto/DeFi portfolio intelligence service: valuation, concentration risk, market data adapters, liquidity/opportunity ranking, and alerts as the next layer.

## Runtime safety
- `READ_ONLY_MODE=true` by default.
- `EXECUTION_ENABLED=false` by default.
- No private keys, seed phrases, banking credentials, or exchange secrets are stored in Git.
- Live execution is intentionally absent from the MVP API.

## Built now
- FastAPI health/capabilities endpoints.
- Deterministic portfolio valuation and concentration risk scoring.
- CoinGecko public read-only market adapter.
- DexScreener read-only liquidity/opportunity adapter.
- Unit tests and GitHub Actions test workflow.
- Minimal browser dashboard shell.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-mvp.txt
PYTHONPATH=. uvicorn apps.api.main:app --reload --port 8000
```

## API example
```bash
curl -X POST http://127.0.0.1:8000/v1/portfolio/analyze \
  -H 'content-type: application/json' \
  -d '{"holdings":[{"symbol":"ETH","quantity":2,"price_usd":2000},{"symbol":"USDC","quantity":1000,"price_usd":1}]}'
```

## Next production layers
1. Normalize wallet/RPC adapters.
2. Persist portfolios and historical valuations.
3. Add authentication and tenant isolation.
4. Add alert rules/webhooks.
5. Add billing only after licensing/provenance is cleared.
6. Paper trading and execution remain separate projects.

## Commercial gate
Before a paid launch, verify provenance, license, trademark, copyright, and rights to commercialize upstream-derived code. The current repository's README references MIT licensing but the fork's licensing/provenance should be made explicit and verified.
