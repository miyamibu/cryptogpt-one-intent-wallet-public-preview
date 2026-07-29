# Key Management Requirements

## KMR-01 Separation

Trade agent、root signer、recovery、admin keysを分離する。

## KMR-02 No raw export

production serviceはprivate key／shareのraw export APIを持たない。

## KMR-03 User factor

root asset移動は、Existing Walletの署名または独立user factorを必要とする。

## KMR-04 Hardware protection

- Android auth/wrapping key: hardware-backed where available
- server keys: HSM/KMS or audited threshold component
- admin: hardware security keys

## KMR-05 Lifecycle

```text
GENERATED
ATTESTED
ACTIVE
SUSPENDED
REVOKED
DESTROYED
COMPROMISED
```

## KMR-06 Rotation

- service keys regular rotation
- agent replacement on compromise／session boundary policy
- root share refresh
- registry key rotation with overlap
- no reuse of deregistered agent address

## KMR-07 Recovery

Recovery must work during:

- vendor outage
- backend outage
- mobile loss
- app delisting
- company shutdown

## KMR-08 Audit

- key creation ceremony
- public key
- provider version
- policy
- attestation
- rotation
- recovery drill
- destruction evidence

## KMR-09 Android

- Auto Backup and D2D exclusions
- key invalidation handling
- StrongBox capability check
- AES-GCM unique nonce
- associated data binding
- no screenshots
- no clipboard

## KMR-10 Signer API

Allowed:

```text
signHyperliquidOrder(capsuleId)
signUsdSend(capsuleId)
signWithdraw3(capsuleId)
signBridgePermit(capsuleId)
```

Forbidden:

```text
sign(bytes)
signTypedData(any)
signTransaction(any)
eth_sign
personal_sign
```
