# Execution subsystem

## Status: DISABLED

This directory is a quarantine boundary for future paper/live execution work. The MVP must not import or expose authenticated order-placement functions from the existing Coinbase client or smart-contract deployment scripts.

Future progression:

`signal -> risk check -> paper trade -> approval -> execution`

Live execution requires a separate security review, least-privilege credentials, transaction simulation, audit logging, limits and an emergency kill switch.
