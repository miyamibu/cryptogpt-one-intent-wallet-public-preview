# Canonical Quote, Registry Resolution, and Atomic Signer Closure

**Version:** 2026-07-29.3  
**Current package status:** `BLOCKED_NOT_OPERATIONAL`

## Purpose

A hash-shaped string does not prove that a quote contains the meaning the user approved. A network name does not prove which chain the signer will use. A timeout after signing does not prove that nothing happened. These three gaps must be closed inside the protected signer boundary before production activation.

## Canonical operation quote

`schemas/operation-quote.schema.json` defines the minimum portable contract. `examples/operation-quote-simulation.json` is deliberately unsigned and cannot be used as production evidence.

The production implementation must domain-separate and canonically hash the exact quote document, authenticate its provider, and bind it to:

- the exact release, deployment, account and Execution Capsule;
- source state and registry versions;
- source/destination networks and numeric chain identities;
- every asset, contract, amount, recipient and ordered action;
- minimum output, maximum fee, slippage/limit/trigger conditions;
- provider route, reimbursement and failure-charge terms where applicable;
- generation/expiry time and a one-time quote nonce;
- the exact final Hyperliquid wire action or EVM transaction commitment.

The protected signer reconstructs the final payload and recomputes the commitment. Any difference requires a new quote and new user authorization.

## Exact signed registry resolution

The signer must load the exact registry bytes whose SHA-256 is bound to the release subject, runtime state, account binding, quote, Execution Capsule and operation authorization. It verifies signature, role, validity, revocation and monotonic sequence, then resolves:

```text
CAIP-2 network ID
→ numeric chain ID / protocol environment
→ provider-reported chain ID
→ asset ID / market ID
→ contract and proxy implementation
→ runtime code hash
→ decimals and capability flags
```

A mismatch, missing entry, stale sequence, production-ineligible entry or source conflict is a hard stop. A symbol or display label is never authoritative.

## Rollback-resistant counters

Trusted-time, evidence-index, registry, account-binding, runtime-state, lease, deployment and revocation counters live outside the release archive in rollback-resistant storage. Equality with the stored high-water mark is stale/replay; accepted candidates must be strictly newer wherever monotonicity is required. Disaster recovery must prove that restoring a database or region cannot reactivate older authority.

## Atomic signer state machine

Reservation, final verification, payload commitment, signature creation and durable consumption must be one protected state transition. The signature and consumed authorization are persisted before broadcast.

Required ambiguous states include:

```text
SIGNED_BROADCAST_UNKNOWN
BROADCAST_ACCEPTED_UNCONFIRMED
PARTIAL
MANUAL_RESOLUTION_REQUIRED
```

None may trigger blind re-signing. Reconciliation uses the exact transaction hash, Hyperliquid `cloid`/order/fill state, bridge message ID and account-state change. Timeout alone is never treated as proof of failure.

## Production acceptance

Codex may close these gaps only after positive and negative tests demonstrate:

1. every material quote field changes the quote digest and/or final-payload commitment;
2. a quote cannot be replayed for another account, operation, chain, asset, recipient, amount or state;
3. CAIP-2, numeric chain ID and provider-reported chain ID must agree;
4. registry rollback and code/proxy/decimals drift fail closed;
5. process crashes at every reserve/sign/persist/broadcast point cannot produce a second signature;
6. ambiguous broadcast outcomes reconcile without a duplicate economic effect;
7. all evidence is release-bound, signed, independently reviewed and included in the 37-gate/93-claim readiness decision.
