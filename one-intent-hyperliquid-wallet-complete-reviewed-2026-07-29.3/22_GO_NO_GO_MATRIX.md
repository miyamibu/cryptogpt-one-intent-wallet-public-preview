# GO / NO-GOマトリクス

## 現在

| 対象 | 判定 | 理由 |
|---|---|---|
| 設計採用 | GO | 主要境界と残余リスクを定義 |
| Codex実装 | GO | Schema／API／test planあり |
| Simulator | GO | 資金を扱わない |
| Hyperliquid Testnet | GO_AFTER_IMPLEMENTATION | 実装後 |
| Pixel 9a検証 | GO_AFTER_BUILD | Biometric、Protected Confirmation capability、鍵失効の実機証跡後 |
| 個人少額Mainnet | NO_GO | Testnet・監査・復旧未完 |
| Closed Alpha | NO_GO | 法務・運用未完 |
| Public Mainnet | NO_GO | 全ゲート未完 |
| ChatGPT内write | PROHIBITED | OpenAI App規約 |
| 無確認自動売買 | PROHIBITED | 人間確認・安全境界 |

## Mainnet解除条件

### Technical

- [ ] complete implementation
- [ ] official SDK parity
- [ ] all schemas/evals
- [ ] Testnet evidence
- [ ] Pixel 9a evidence
- [ ] no arbitrary signing
- [ ] recovery drill
- [ ] external audit
- [ ] incident rehearsal
- [ ] monitoring
- [ ] source pin verification
- [ ] Trusted Display path for R4／non-exempt R3, plus signed evidence for R3 standing exception
- [ ] independent state quorum
- [ ] agent bearer-risk characterization
- [ ] environment-specific Bridge/HyperEVM evidence

### Legal

- [ ] written counsel opinion
- [ ] registration decision
- [ ] AML decision
- [ ] Terms
- [ ] Privacy
- [ ] Risk Disclosure
- [ ] fee model
- [ ] geo policy
- [ ] marketing review
- [ ] Google Play financial declaration／crypto policy evidence
- [ ] region-specific store eligibility

### Operational

- [ ] 24/7 kill switch
- [ ] support
- [ ] alerting
- [ ] vulnerability disclosure
- [ ] user notification
- [ ] backup
- [ ] business continuity
- [ ] admin hardware MFA
- [ ] two-person approvals

## NO-GO自動条件

- source mismatch
- signer policy mismatch
- bridge bytecode mismatch
- unknown contract
- stale metadata
- unresolved High/Critical
- legal opinion expired／assumptions changed
- model eval regression
- duplicate execution defect
- recovery failure
- audit log gap
- Protected Confirmation required but unavailable with no approved fallback
- state-source divergence／unknown independence
- agent capability characterization incomplete
- Google Play or regional distribution evidence missing

## Cross-platform GO／NO-GO additions

| 項目 | 現在 | GO条件 |
|---|---|---|
| Android build | NO_GO | Compose実装、CI、Pixel 9a実機 |
| iOS build | NO_GO | SwiftUI実装、Xcode、実機、signing |
| iOS App Attest | NO_GO | server validation、unsupported、reinstall evidence |
| Cross-platform hash parity | NO_GO | Android／iOS／backend golden vectors一致 |
| Ad Hoc／closed TestFlight | NO_GO | signed build、privacy、Testnet-only、support |
| Public App Store | NO_GO | organization、license、legal memo、audit、App Review readiness |
| Managed Self-Custody | NO_GO | external crypto audit、recovery drill、legal evaluation |

追加チェック：

- [ ] iPhone real-device evidence
- [ ] Secure Enclave／Keychain evidence
- [ ] App Attest production assertion evidence
- [ ] Dynamic Type／VoiceOver evidence
- [ ] Apple organization／license／region evidence
- [ ] platform canonical parity evidence

## 2026-07-29.1追加gate

| Gate | GO条件 | 未達時 |
|---|---|---|
| PLAIN_JAPANESE_COPY | 共通辞書、copy lint、Android／iOS／prototypeの主要画面一致 | release NO_GO |
| LIQUIDATION_PRICE_DISPLAY | Testnetでpreview／actual照合、stale／null fail closed、口座方式説明 | 先物write NO_GO |
| JPYC_EX_HANDOFF | 契約、credential、redirect検証、最終申込み非代行、入金照合 | JPYC発行導線 NO_GO |
| JPYC_FEE_READINESS | 5状態、cap、route／sponsor監査、manual fallback、二重回収防止 | 自動手数料準備 NO_GO |
| STANDING_AUTHORIZATION | exact scope、expiry、revocation、strong confirmation exceptions、実機証拠 | 初回限定自動化 NO_GO |
| CHATGPT_READ_ONLY | financial write tool 0、action carrying link 0、privacy／OpenAI規約review | ChatGPT連携 NO_GO |
| MANUAL_FALLBACK | versioned手順、正確なボタン名、主要失敗理由の実機検証 | closed alpha NO_GO |
