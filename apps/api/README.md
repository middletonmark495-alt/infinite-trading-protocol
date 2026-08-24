# API application boundary

The first application layer is read-only. Keep external provider credentials and adapters behind service interfaces. Do not expose Coinbase trading, contract deployment, or wallet-signing functions through this API.

Suggested endpoints:

- `GET /health`
- `GET /markets`
- `GET /markets/{asset}`
- `GET /wallets/{address}`
- `GET /wallets/{address}/balances`
- `GET /wallets/{address}/transactions`
- `GET /portfolios/{id}`
- `GET /portfolios/{id}/performance`
- `GET /risk/{id}`
- `GET /opportunities`
- `GET /alerts`
- `POST /alerts`

All endpoints must remain read-only until the execution subsystem passes a separate security and product review.
