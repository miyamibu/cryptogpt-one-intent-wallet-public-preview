# データモデル

## User

```text
id
status
jurisdiction
ageAttestation
legalAcceptanceVersion
createdAt
```

## Device

```text
id
userId
platform
appVersion
signingCertDigest
authPublicKey
integrityState
status
registeredAt
lastSeenAt
```

## WalletAccount

```text
id
userId
environment
address
accountMode
custodyMode
label
status
```

## Signer

```text
id
accountId
role: TRADE_AGENT | ROOT | RECOVERY
publicAddress
provider
version
status
approvedAt
revokedAt
```

秘密はDBに置かない。

## AddressBookEntry

```text
id
userId
alias
chain
address
addressHash
source
verifiedAt
cooldownUntil
status
version
```

## PolicyProfile

```text
id
userId
version
allowedAssets
limits
destinations
vaults
riskThresholds
sessionRules
effectiveAt
```

## ActionPlanDraft

AI output。実行不可。

## CompiledPlan

```text
id
draftId
accountId
snapshotId
steps
constraints
warnings
riskTier
compilerVersion
expiresAt
```

## ExecutionCapsule

```text
id
planId
semanticHash
renderReceiptHash
authorizationPresentation
stateEvidence
trustedPromptTextHash
policyVersion
registryVersions
authRequirement
status
```

## Authorization

```text
id
capsuleId
deviceId
authType
authPublicKey
signature
integrityTokenHash
trustedDisplayMode
confirmationPromptText
confirmationResponseHash
challengeId
authorizedAt
```

## ExecutionStep

```text
id
planId
ordinal
type
idempotencyKey
remoteIdentifier
state
attemptGeneration
submittedAt
confirmedAt
failureCode
```

## AuditEvent

```text
id
aggregateType
aggregateId
sequence
eventType
payloadRedacted
previousHash
eventHash
createdAt
actor
```

## SourcePin

```text
source
url
retrievedAt
version
commit
contentHash
status
```

## FeatureGate

```text
name
environment
enabled
reason
evidenceBundle
approvedBy
signature
effectiveAt
```

## 不変条件

- capsule semanticHashは変更不可
- authorizationはcapsuleに一対一または明示複数factor
- remote identifierは再利用しない
- event sequenceは単調増加
- Address Book変更で旧compiled planは無効
- feature gate version変更で未実行planは再コンパイル

## StateEvidenceSource

```text
id
provider
kind: OFFICIAL_API | INDEPENDENT_API | LOCAL_NODE | CHAIN_RPC | CONTRACT_RECEIPT
independenceClass
observedAt
blockHeight
stateDigest
freshnessMs
status
```

## DistributionEvidence

```text
releaseId
playDeclarationVersion
playReviewStatus
targetCountries
legalMemoVersion
storeListingVersion
packageName
signingCertDigest
approvedAt
```

## AuthorizationEnvelope

- authorization_id PK
- plan_id FK
- semantic_hash
- render_receipt_hash
- source_state_hash
- prompt_text_hash nullable
- device_id
- presentation_mode
- auth_type
- challenge_hash
- issued_at／expires_at／consumed_at
- evidence_kind
- evidence_digest
- confirmation_key_id／wallet_address nullable
- verification_result

raw confirmation token／wallet signatureの保持は必要最小限とし、長期監査にはdigestと検証結果を保存する。

## Platform data additions

追加entity／field：

- Device.platform
- Device.capabilities
- Device.appAttestKeyId／counter state
- Authorization.authorizationAssurance
- Authorization.presentationMode
- StandingAuthorization
- DestinationRegistrationEvidence
- DistributionGate
- PlatformEvidenceBundle

App Attest key IDはdevice registrationと束縛し、再install後に旧registrationを無条件再利用しない。
