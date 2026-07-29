# Execution Capsule仕様

## 目的

一回の承認で複数操作を許可しながら、金額・宛先・asset・fee・slippage・順序の改変を防ぐ。さらに、どの状態証拠を使い、どのTrusted Displayで認証したかを固定する。

## オブジェクト

- `ActionPlanDraft`: AIが出す未信頼下書き
- `CompiledPlan`: metadataとstateを反映した実行可能候補
- `StateEvidence`: state source、freshness、digest、divergence
- `ExecutionCapsule`: ユーザー認証対象
- `AuthorizationPresentation`: 人間へ何をどの経路で見せるか
- `SignedAction`: Hyperliquid／EVM固有payload
- `ExecutionReceipt`: 最終結果

## Hash Profile V1

`hashProfile`は`ONE_INTENT_HASH_PROFILE_V1`に固定する。循環参照を避けながら、認証時にすべてを束縛する。

### 1. Semantic core

```text
semanticCore = capsuleから次を除外したもの
- semanticHash
- renderReceiptHash
- sourceStateHash
- renderReceipt
- authorizationPresentation.promptText
- authorizationPresentation.promptTextHash

semanticHash = SHA-256(
  UTF8("ONE_INTENT_EXECUTION_CAPSULE_V1")
  || 0x00
  || CANONICAL_JSON(semanticCore)
)
```

### 2. 派生hash

```text
renderReceiptHash = H("ONE_INTENT_RENDER_RECEIPT_V1", renderReceipt)
sourceStateHash   = H("ONE_INTENT_STATE_EVIDENCE_V1", stateEvidence)
promptTextHash    = SHA-256(UTF8("ONE_INTENT_TRUSTED_PROMPT_V1") || 0x00 || UTF8(promptText))
```

### 3. Authorization Envelope

ユーザー認証は次を同時に束縛する。

- `semanticHash`
- `renderReceiptHash`
- `sourceStateHash`
- `promptTextHash`
- `planId`／`deviceId`
- presentation mode
- fresh challenge
- expiry／one-time-use

これにより、semantic hashを先に計算し、その短いfingerprintをTrusted Promptへ表示しても循環しない。SignerはCapsuleだけでなくAuthorization Envelopeも検証する。

### Canonical JSON制約

- duplicate key拒否
- object keyは本SchemaのASCII固定名だけ
- stringはNFC
- NaN／Infinity／JSON float拒否
- 金融数値はDecimal string
- scientific notation拒否
- field omissionと`null`を区別

`tools/canonical_hashes.py`はpackage test vector用の限定profileである。productionはレビュー済みRFC 8785実装またはbyte-for-byte互換性の証明を必要とする。raw user textではなくCompilerが作ったcanonical valueだけをhashする。

## 固定するもの

- network／chain ID
- account／account mode
- signer role
- action type
- asset canonical ID
- size／notional
- exact or bounded price
- minimum output
- maximum fee
- maximum slippage
- destination
- vault／contract／selector
- step dependencies
- expiry／maximum Saga duration
- source state version／state evidence
- policy／feature gate／registry version
- failure policy
- idempotency key
- authorization presentation mode
- canonical trusted prompt textまたは外部wallet表示要件

## StateEvidence

最低限:

- `policy`
- source ID／kind／independence class
- source observation time
- source digest
- aggregate state hash
- divergence status
- max age

R2以上で`DIVERGENT`、`NOT_CHECKED`、staleなら実行不可。

## AuthorizationPresentation

- `APP_EXECUTION_CARD`: R0/R1中心
- `ANDROID_PROTECTED_CONFIRMATION`: 対応端末のR3/R4
- `EXTERNAL_WALLET_TRUSTED_DISPLAY`
- `HARDWARE_WALLET`
- `BLOCKED_UNAVAILABLE`

`renderReceiptHash`は監査用であり、人間が見たことの暗号学的証明ではない。Protected Confirmationでは、Relying Partyが返却blobの`promptText`とchallengeを検証する。

## 再コンパイル

次の場合、旧Capsuleを破棄する。

- price drift超過
- balance／position change
- state source divergence
- address book／contract registry version change
- account mode change
- feature gate／policy／signer change
- trusted-display capability change
- expiry／maximum duration超過
- chain mismatch
- model output変更

再コンパイル結果が意味的に同一で、許容band内なら既存ボタン押下から継続してよい。意味が変わる場合は新しいCardとTrusted Displayで再承認。

## 表示Receipt

- locale
- display units
- full destinationまたは事前承認済みalias＋fingerprint
- button label
- warnings
- price／fee／state timestamp
- source IDs
- semanticHash short fingerprint
- authorization presentation mode

`renderReceiptHash`は監査用で、実行許可のsource of truthはsemanticHashと有効なauthorization evidenceである。

## Platform binding

Execution Capsuleは`platform`を必須とし、Authorization Presentationは`assurance`、`standingAuthorizationId`、`destinationRegistrationEvidenceId`を含む。

iOSの`IOS_APP_ATTESTED_AUTHENTICATED_UI`は`AUTHENTICATED_APP_UI_NOT_TRUSTED_DISPLAY`に固定する。R3 saved destination例では事前登録evidenceとstanding authorizationを必須とする。
