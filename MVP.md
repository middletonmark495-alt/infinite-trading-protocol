# Infinite Trading Intelligence MVP

A read-only crypto/DeFi portfolio intelligence service for valuation, explainable risk, market data, liquidity/opportunity ranking, and alerts.

## Safety
- `READ_ONLY_MODE=true` by default.
- `EXECUTION_ENABLED=false` by default.
- No private keys, seed phrases, banking credentials, or exchange secrets are stored in Git.
- Live execution is intentionally absent from the MVP API.

## Built
- FastAPI health/capabilities endpoints.
- Deterministic portfolio valuation and concentration risk scoring.
- CoinGecko public read-only market adapter.
- DexScreener read-only liquidity/opportunity adapter.
- Unit tests and GitHub Actions workflow.
- Minimal browser dashboard shell.

## Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-mvp.txt
PYTHONPATH=. uvicorn apps.api.main:app --reload --port 8000
```

## API
```bash
curl -X POST http://127.0.0.1:8000/v1/portfolio/analyze \
  -H 'content-type: application/json' \
  -d '{"holdings":[{"symbol":"ETH","quantity":2,"price_usd":2000},{"symbol":"USDC","quantity":1000,"price_usd":1}]}'
```

## Next
1. Wallet/RPC normalization.
2. Historical persistence.
3. Authentication and tenant isolation.
4. Alerts/webhooks.
5. Billing after licensing/provenance clearance.
6. Paper trading, then a separately reviewed execution service.

## Commercial gate
Verify provenance, license, trademark, copyright, and commercial rights before a paid launch. The repository README references MIT licensing, but the fork's licensing/provenance should be explicit and verified.
