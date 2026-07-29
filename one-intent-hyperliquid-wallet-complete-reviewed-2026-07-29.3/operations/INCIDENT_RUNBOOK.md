# Incident Runbook

## Severity

- SEV0: active root asset theft／arbitrary signing
- SEV1: unauthorized trade、agent compromise、duplicate execution
- SEV2: Bridge/Vault outage、status divergence
- SEV3: AI degradation、read-path outage

## First 15 minutes

1. incident commander
2. write feature gates OFF
3. signer requests suspended
4. preserve audit logs
5. current asset state snapshot
6. affected users/accounts
7. upstream status
8. do not blind-retry
9. legal/security notification
10. user-facing holding message

## SEV0

- revoke agent where safe
- block root signer
- migrate remaining assets
- inspect HyperEVM and pending Bridge
- rotate admin/service keys
- forensic image
- notify affected users
- regulatory/legal evaluation

## SEV1

- cancel open orders
- compare cloid／fills
- disable affected signer
- cap all accounts
- reconcile balances
- root cause

## Communication

State facts only:

- what is confirmed
- what is suspected
- affected functions
- asset location
- user action
- next update time is not promised unless operations actually supports it
- support identity

## Recovery criteria

- vulnerability fixed
- keys rotated
- state reconciled
- external review for SEV0/1
- feature-specific canary
- postmortem
- control update
