# Control API

実装時の原則：

- LLM callable execute endpointなし
- generic sign／broadcastなし
- all writes require Authorization Envelope
- signer rechecks capsule／policy／state
- Mainnet feature gates default OFF
- append-only audit and idempotency
