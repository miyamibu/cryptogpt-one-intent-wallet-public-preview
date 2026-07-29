# API契約概要

詳細は`contracts/openapi.yaml`。

## Read

```text
GET /v1/accounts/{accountId}/snapshot
GET /v1/accounts/{accountId}/positions
GET /v1/accounts/{accountId}/orders
GET /v1/markets
GET /v1/vaults/{vaultId}
GET /v1/executions/{planId}
GET /v1/state-evidence/{snapshotId}
GET /v1/devices/{deviceId}/confirmation-capability
```

## AI／Compile

```text
POST /v1/intents/parse
POST /v1/plans/compile
POST /v1/plans/{planId}/refresh
```

## Authorization／Execute

```text
POST /v1/plans/{planId}/confirmation-challenge
POST /v1/plans/{planId}/authorize
POST /v1/plans/{planId}/execute
POST /v1/plans/{planId}/resume
POST /v1/plans/{planId}/cancel-before-execution
```

`execute`はLLMから呼べない。Android appのauthenticated user gestureからのみ。

## Emergency

```text
POST /v1/emergency/cancel-all-orders
POST /v1/emergency/close-position
POST /v1/emergency/revoke-agent
POST /v1/emergency/disable-writes
```

## Admin

別domain・別auth。

```text
POST /admin/feature-gates/propose
POST /admin/feature-gates/approve
POST /admin/registries/propose
POST /admin/registries/approve
```

## Idempotency

write requestは:

```text
Idempotency-Key
X-Execution-Capsule-Hash
X-Device-Authorization
```

を要求する。

## Error

- stable code
- Japanese user message
- technical detail ID
- retryability
- asset location
- next safe action

秘密情報やraw upstream responseをそのまま返さない。

## Trusted Display

R4およびstanding例外を満たさないR3 authorizationは次を要求する。R3 standing例外では同じCapsule hashにregistration evidence、cooling、hard cap、standing authorization、auth-per-use evidenceを束縛する。

```text
X-Execution-Capsule-Hash
X-Confirmation-Challenge
X-Confirmation-Response
X-Device-Attestation
```

Protected Confirmationを利用しないapproved fallbackでは、外部wallet／hardware-wallet receipt typeを明示する。通常BiometricPromptへ暗黙降格しない。

## State quorum

`compile`／`refresh`レスポンスはstate evidence summaryを返す。`execute`時、Signerが独立再検証し、divergenceなら`STATE_EVIDENCE_DIVERGENT`を返す。

## Authorization Envelope

`POST /v1/plans/{planId}/authorize`は`schemas/authorization-envelope.schema.json`を受け取る。serverは次を再計算・照合する。

- planIdと保存済みCapsule
- semanticHash
- renderReceiptHash
- sourceStateHash
- promptTextHash
- challengeの発行先、期限、未使用性
- presentation modeとevidence kind
- Protected Confirmationのattested key、returned promptText、challenge
- external／hardware walletのsigner addressとdisplay capability evidence

`authorizationId`は一回だけ消費できる。execute endpointへraw signatureやgeneric typed dataを直接渡す経路は作らない。

## iOS authorization API additions

- `POST /v1/devices/ios/app-attest/challenge`
- `POST /v1/devices/ios/app-attest/register`
- `POST /v1/plans/{planId}/authorization/challenge`
- `POST /v1/plans/{planId}/authorize/ios`

serverはattestation／assertion、bundle ID、team ID、environment、counter、challenge、4 hash、device、policy、expiryを検証する。App Attest unavailableをclient booleanだけで許可しない。

## 2026-07-29.1追加予定endpoint

Codex実装時に `contracts/openapi.yaml` へ型を追加し、生成clientとcontract testを更新する。

### `POST /v1/fee-readiness/preview`

入力: wallet、network、予定操作のcanonical hash。  
出力: `FeeReadinessPlan`。  
制約: AI toolとして公開しない。残高、quote、月間使用量、allowlistをserver-sideで検査する。

### `POST /v1/liquidation-preview`

入力: canonical perpetual plan、fresh account evidence。  
出力: estimate、mark price、distance、account mode、freshness。  
制約: model出力を計算値に使わない。stale／nullは明示的なunavailable response。

### `GET /v1/manual-guidance/{fallbackId}`

出力: `ManualFallback`。  
制約: app version、OS、locale、feature gateに一致する署名済み手順だけを返す。

### `POST /v1/standing-authorizations`

限定権限の作成。scope expansionは新しいAuthorization Envelopeと強い確認を要求する。

### `DELETE /v1/standing-authorizations/{authorizationId}`

即時失効。SignerとControl APIの両方で失効を確認する。

### ChatGPT／OpenAI non-transactional support surface

別serviceで、`contracts/chatgpt-readonly-openapi.yaml`の次の4 operationだけを提供する。

- `getReadOnlyStatus`: 不透明なreference IDについて抽象状態と固定message codeだけ
- `getPlainJapaneseTerm`: 固定用語catalog
- `explainNonTransactionalError`: 固定エラーcatalog
- `getGenericSafetyHelp`: 固定一般安全topic

取引文、宛先、金額、asset／network、quote、下書き、画面・ボタン手順、ManualFallback、注文／送金／交換／出金／署名／broadcast endpointをChatGPT surfaceへrouteしない。中立handoffは固定文で、取引内容、画面位置、token、deep linkを持たせない。
