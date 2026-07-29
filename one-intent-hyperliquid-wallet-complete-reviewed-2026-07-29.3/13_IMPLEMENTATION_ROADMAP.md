# 実装ロードマップ

## Workstream A — Core domain

- ActionPlanDraft
- CompiledPlan
- ExecutionCapsule
- PolicyProfile
- ExecutionStatus
- Decimal／asset types
- canonicalization
- hash vectors

## Workstream B — Read path

- Hyperliquid info endpoint
- metadata cache
- account state
- positions
- orders
- fills
- vault details
- Bridge state

## Workstream C — AI

- Responses API
- strict schema
- prompt injection separation
- eval corpus
- model pin
- fallback parser
- telemetry without secrets

## Workstream D — Compiler／Policy

- intent resolver
- Address Book resolver
- contract registry
- fee/margin calculator
- SAFE_ALL
- risk tier
- state drift
- card view model

## Workstream E — Android

- Compose chat
- live card
- biometric
- Keystore
- manual emergency
- wallet adapter
- accessibility
- Play Integrity binding
- encrypted local storage

## Workstream F — Hyperliquid execution

- official SDK parity tests
- order/cancel/modify
- TP/SL
- Spot
- transfers
- withdraw
- agent approval
- nonce/cloid
- WebSocket/reconcile

## Workstream G — Bridge／Vault

- Bridge2 registry
- Permit
- relayer
- deposit credit reconciliation
- withdrawal reconciliation
- HLP
- user vault
- HyperEVM Adapter framework

## Workstream H — Signer

- trade signer
- root signer interface
- no arbitrary payload
- HSM/MPC evaluation
- recovery
- signed policy bundle
- audit

## Workstream I — Operations／Compliance

- feature gates
- admin two-person approval
- monitoring
- incident
- legal
- privacy
- user support
- source diff

## 推奨順序

```text
Domain → Read path → Compiler → Android Card
→ Testnet Trade → Reconciliation
→ Root wallet adapter → Transfer/Withdraw
→ Bridge → Vault
→ Managed key/MPC
→ Small Mainnet
```

すべてを設計対象に含めるが、同時に雑に実装しない。

## Cross-platform roadmap amendment

1. shared deterministic core
2. official Python SDK conformance harness
3. mock control API／signer
4. Android native shell
5. iOS native shell
6. Existing Wallet Mode
7. Testnet feature-by-feature
8. independent mobile／backend／cryptography audit
9. Ad Hoc／closed TestFlight／Play internal
10. only then own-wallet Mainnet canary

Managed Self-Custodyは別research trackであり、監査完了までMainnet gateを開かない。
