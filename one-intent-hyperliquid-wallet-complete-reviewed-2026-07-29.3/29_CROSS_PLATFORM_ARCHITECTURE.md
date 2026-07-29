# Cross-Platform Architecture

## 決定

Flutter／React Nativeで一枚にまとめず、**AndroidとiOSはnative shell**にする。

- Android：Kotlin、Jetpack Compose
- iOS：Swift、SwiftUI
- 共有：決定論的domain／compiler／policy／state machine／canonical hash vector
- 共有しない：Keystore、Secure Enclave、biometrics、App Attest、Protected Confirmation、wallet handoff

金融署名アプリでプラットフォーム固有security APIを薄く隠しすぎると、対応していない安全機能まで「同じ」と見えてしまうためである。

## 推奨monorepo

```text
apps/
  android/
  ios/
core/
  shared-rust/
    domain/
    compiler/
    policy/
    state-machine/
    canonical-hash/
    test-vectors/
platform/
  android-security/
  ios-security/
services/
  control-api/
  state-quorum/
  reconciler/
  signer-policy/
  bridge-relayer/
adapters/
  hyperliquid/
  arbitrum/
  hyperevm/
  external-wallet/
contracts/
schemas/
tests/
  conformance/
  attack/
  visual/
  device/
```

## Shared Coreの境界

共有してよい：

- Decimal／integer financial arithmetic
- ActionPlanDraft validation
- asset／contract／address registry lookup
- Execution Capsule compile
- Policy evaluation
- risk tier classification
- hash canonicalization
- state machine
- error catalog
- display model生成

共有しない：

- OS key storage
- biometric prompt
- device attestation
- screen-capture response
- external wallet launch
- push notifications
- platform navigation／safe area

## Rust採用時の条件

Rustはshared pure coreに適するが、Hyperliquidの公式public SDKはPythonが基準である。Rustのcommunity SDKや独自署名コードだけを正解にしない。

署名Adapterは以下を満たす。

1. 公式Python SDKでgolden vectorを生成
2. Rust／Swift／Kotlin／backend実装がbyte-for-byte一致
3. field order、trailing zero、case、environment、vault address、expiresAfterを比較
4. user-signed actionとL1 actionを別test suiteにする
5. SDK／protocol changeでCIをfailさせる

## 2つのウォレットモード

### Existing Wallet Mode

- self-hosted root keyを作らない
- external walletへroot actionをhandoff
- trade-only pathは承認済みAPI Walletで高速化可能
- UXはroot actionで2回以上になる場合がある
- 最短でTestnet検証しやすい

### Managed Self-Custody Mode

- 監査済みThreshold ECDSA
- app内で1 intent体験を最大化
- security、recovery、custody、legal負担が大幅に増える
- MVPの公開条件にはしない

## Backend trust boundary

### Control API

- Authenticated plan creation
- no generic signing
- no raw LLM execution
- signed version registries
- feature gate validation

### State Quorum

- official API
- independent API／indexer
- local non-validating node or chain evidence
- same cache/providerを独立sourceと数えない

### Policy Signer

- capsule hash再計算
- OS authorization evidence検証
- state再検証
- operation-specific signer method only
- amount／destination／contract／chain hard bound

### Reconciler

- HTTP responseを完了扱いしない
- WebSocket＋REST＋chain receipt
- partial／unknown／recovery_required
- blind retry禁止

## iPhoneとAndroidの差をUIで隠さない

同じボタンを出せても、認証保証は同じではない。

| 項目 | Android | iOS |
|---|---|---|
| 通常生体認証 | BiometricPrompt | LocalAuthentication |
| app integrity | Play Integrity等 | App Attest |
| hardware authorization key | Keystore | Secure Enclave P-256 |
| general trusted confirmation | 対応端末でProtected Confirmation | 一般向け同等APIを前提にしない |
| Hyperliquid root curve | secp256k1 | secp256k1 |
| OS hardware enclave native curve | 端末依存、直接root利用を保証しない | P-256、root secp256k1ではない |

そのため、共通domain modelに `platform` と `authorizationAssurance` を含める。

## Cross-platform Definition of parity

Parityは「画面が同じ」ではない。以下が同じであることを証明する。

- 同一inputから同一ActionPlanDraft
- 同一registry／stateから同一semantic capsule
- 同一canonical bytes／hash
- 同一policy decision
- 同一risk tier
- 同一failure state
- 同一critical disclosure

OS固有認証だけは、保証の差を明示する。
