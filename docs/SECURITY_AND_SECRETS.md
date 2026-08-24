# Security and secrets policy

## Rules
- Never commit API keys, API secrets, private keys, seed phrases, session cookies or banking credentials.
- Use environment variables locally and a managed secret store in production.
- The application defaults to `READ_ONLY_MODE=true` and `EXECUTION_ENABLED=false`.
- Execution credentials, if ever introduced, must be isolated from read-only credentials and require explicit policy gates.
- Wallet monitoring uses public addresses only.

## Required production controls before execution
- MFA on all provider accounts.
- Least-privilege API keys.
- IP restrictions where supported.
- Withdrawal permissions disabled.
- Separate paper-trading and live credentials.
- Kill switch.
- Audit log for every attempted order.
- Transaction simulation and slippage limits.
- Independent smart-contract review.

## Personal information
No private user information is required to create the MVP codebase. Do not send credentials or secrets to ChatGPT. When configuration is needed, populate the placeholders directly in your deployment secret manager.
