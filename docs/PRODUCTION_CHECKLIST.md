# Production Checklist

## Application
- [ ] FastAPI health endpoint
- [ ] Persistent database configured
- [ ] Database migrations
- [ ] Wallet/address ingestion
- [ ] Portfolio valuation snapshots
- [ ] Risk scoring
- [ ] Opportunity scoring
- [ ] Alert rules and delivery
- [ ] Owner Control Center

## Security
- [ ] Authentication provider configured
- [ ] Tenant isolation tested
- [ ] Rate limiting enabled
- [ ] Audit logging enabled
- [ ] HTTPS enforced
- [ ] Secrets stored outside Git
- [ ] Dependency/security scanning
- [ ] Backup and restore test

## Commercial
- [ ] Terms and privacy policy reviewed
- [ ] Licensing/provenance verified
- [ ] Billing provider configured
- [ ] Product entitlements enforced server-side
- [ ] Customer support/contact path

## Trading safety
- [ ] Execution disabled by default
- [ ] Paper trading tested
- [ ] Transaction simulation
- [ ] Position limits
- [ ] Slippage limits
- [ ] Daily loss limit
- [ ] Kill switch
- [ ] Explicit execution confirmation
- [ ] Independent security review

## Launch gate
The product is not considered production-ready until every mandatory item above is checked and verified in CI or deployment infrastructure.
