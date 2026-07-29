# Android Security Requirements — Pixel 9a基準

## Platform

- min SDKはsecurity featureと市場を考慮して決定
- target latest stable Android
- Pixel 9aを第一実機
- monthly patch levelを記録
- device capabilityを推測せずruntime＋evidenceで記録

## Keystore

- P-256 auth key
- Protected Confirmation用attested key（対応時）
- AES-256-GCM wrapping key
- hardware-backed／StrongBox statusを記録
- auth-per-use for R3/R4。R3 standing例外でも毎回認証
- timed auth for R1
- key invalidation handling
- attestation challenge
- no secp256k1 native availability assumption

## Trusted Display

BiometricPromptだけをtransaction semanticsのTrusted Displayと呼ばない。

R4およびstanding例外を満たさないR3:

1. `ConfirmationPrompt.isSupported(context)`を確認
2. canonical `promptText`を生成
3. server challengeを`extraData`へ設定
4. returned confirmation blobをattested keyで署名
5. Relying Partyがcertificate chain、confirmation tag、signature、promptText、challenge、one-time useを検証
6. success後のみroot signerへ進む

`promptText`へ最低限、operation、network、asset、amount／bound、destination fingerprint、max fee、plan fingerprintを含める。`extraData`は人間可視ではない。

### Fallback

- Protected Confirmation unavailable → external wallet／hardware wallet Trusted Display
- fallbackも不可 → R4／non-exempt R3 write block
- silent downgrade禁止
- accessibility serviceにより利用不能となるケースを試験
- Pixel 9a対応可否は実機証跡が出るまでUNKNOWN

## Storage

- encrypted database
- no secret in SharedPreferences plaintext
- backup／D2D exclude
- screenshot secure flag on secret/recovery screens
- clipboard disabled for secret
- logs／crash report redacted
- agent key memory zeroization test

## UI attacks

- overlay/accessibility risk signal
- screen capture/control warning
- sensitive action blocking policy
- new address full verification or pre-registration
- no hidden webview transaction
- deep link allowlist／app link verification
- trusted prompt critical-field completeness

## Integrity

Play Integrity `requestHash`へ、`semanticHash + deviceId + sessionId + challenge`のdigestを結び付ける。Integrityは補助信号であり、署名境界やTrusted Displayの代替ではない。

## Network／State

- TLS／no cleartext
- certificate rotation/recovery設計
- DNS/TLS error fail closed for write
- request signing／replay protection
- critical stateは独立sourceと照合
- same-provider／same-cacheをquorumと数えない

## Wallet

- external wallet package allowlist optional
- returned address binding
- typed data displayを実機確認
- chain switch verification
- no silent fallback to raw signing
- high-risk walletがcritical fieldsを表示しない場合は不採用

## Testing

- rooted／hooked／repackaged environment
- screen overlay／accessibility service
- Protected Confirmation supported／unsupported／temporarily unavailable
- canonical promptText mismatch
- challenge replay
- clock change
- biometric enrollment
- app restore／process death／multi-window
- notification redaction
- Pixel 9a OS update後の再試験
