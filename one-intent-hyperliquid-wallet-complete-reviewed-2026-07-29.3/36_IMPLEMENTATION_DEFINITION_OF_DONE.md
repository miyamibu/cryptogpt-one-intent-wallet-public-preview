# Implementation Definition of Done

「コードがある」「ビルドが通る」「Testnet注文が1回通る」を完成としない。

## A. Shared Core

- [ ] ActionPlanDraft／Execution Capsule／Authorization EnvelopeがSchema適合
- [ ] Android、iOS、backendでcanonical bytesとhashが一致
- [ ] floats不使用、Decimal／integer
- [ ] duplicate key、Unicode normalization、case、trailing zero vector
- [ ] policy engineのdecision table 100% branch test
- [ ] Saga state machine model／property test
- [ ] unknown stateのblind retry 0

## B. Hyperliquid Adapter

- [ ] 公式Python SDKとgolden vector一致
- [ ] L1 action／user-signed action分離
- [ ] Perp、Spot、cancel、modify、TP/SL
- [ ] entry-fill連動TP/SLのweighted-fill formula、rounding、placement deadline、failure recovery
- [ ] usdSend、spotSend、withdraw3、vaultTransfer、Bridge2
- [ ] API Wallet action characterization
- [ ] nonce concurrency／replay／expiresAfter test
- [ ] cloid idempotency
- [ ] WebSocket gap recovery

## C. Android

- [ ] Pixel 9a real device build
- [ ] Keystore keys hardware-backed status recorded
- [ ] biometric cancellation／lockout／enrollment change
- [ ] Protected Confirmation capability runtime evidence
- [ ] unsupported fallback fail closed
- [ ] font scale 200%、TalkBack、dark、gesture／3-button
- [ ] release APK／AAB signed and SBOM generated

## D. iOS

- [ ] SwiftUI project builds on pinned Xcode
- [ ] iPhone 12、smallest supported iPhone、recent Face ID iPhoneのreal-device evidence
- [ ] Secure Enclave P-256 authorization key
- [ ] Keychain ThisDeviceOnly／non-sync／biometry policy
- [ ] App Attest dev→production validation
- [ ] unsupported／reinstall／migration／restore behavior
- [ ] screen capture／background blur／pasteboard tests
- [ ] Dynamic Type 200%、VoiceOver、dark、reduce motion
- [ ] signed archive／TestFlight artifact

## E. Signing／Custody

- [ ] Existing Wallet Mode end-to-end
- [ ] expected confirmation count shown
- [ ] external payload revalidation
- [ ] Managed Self-Custody remains OFF unless third-party audit complete
- [ ] generic signing endpoint absent
- [ ] DKG／reshare／recovery／rotation drill
- [ ] service shutdown recovery test

## F. Backend／Operations

- [ ] two independent state sources
- [ ] state divergence blocks write
- [ ] feature gates signed／two-person
- [ ] append-only audit
- [ ] per-signer nonce fencing
- [ ] incident kill switches independent of AI
- [ ] backup restore／regional outage／queue replay tests
- [ ] no secret in logs／traces／crash reports
- [ ] AI provider credentialがmobile artifact／remote configに存在しないsecret-scan evidence
- [ ] 取引Intent ParserからOpenAIへのegress 0。任意の非取引Support Gatewayはuser＋device auth、固定schema、nonce／replay防止、rate／cost budgetを強制
- [ ] 非取引Support Gateway service identityからTransaction Intent／Address Book／quote／Compiler write／Signer／broadcast／root actionへのnetwork reachabilityが0
- [ ] AI telemetry redaction canary test

## G. UX／Design

- [ ] all screens in `32_SCREEN_BY_SCREEN_UX_SPEC.md`
- [ ] visual regression matrix（browser／native toolchain version、viewport、locale、theme、text scaleを証跡化）
- [ ] critical pixel diff 0%
- [ ] critical overlap／clip 0
- [ ] concrete action button labels
- [ ] PARTIAL／UNKNOWN honesty
- [ ] address poisoning study
- [ ] usability test with novice and active trader

## H. Security

- [ ] threat model reviewed by independent reviewer
- [ ] mobile pentest
- [ ] backend/API pentest
- [ ] cryptography/MPC audit
- [ ] supply-chain/SBOM review
- [ ] critical/high findings closed or formal NO_GO
- [ ] bug bounty／disclosure channel

## I. Legal／Store

- [ ] written Japan legal opinion
- [ ] Perp／Spot／USDC／MPC／AI／fee analysis
- [ ] privacy policy／terms／risk disclosure
- [ ] Apple organization／licensing/App Review memo
- [ ] Google Play declarations／region evidence
- [ ] Hyperliquid API／brand permission review

## J. Progressive Release

- [ ] simulator
- [ ] mocked signer
- [ ] Testnet read
- [ ] Testnet write
- [ ] own-wallet Mainnet canary with hard cap
- [ ] monitored personal pilot
- [ ] closed alpha
- [ ] public review

各段階の証拠が前段を置換しない。Testnet成功はMainnet安全の証明ではない。

## 2026-07-29.1追加の完成条件

### やさしい日本語

- [ ] `config/user-facing-terms.ja.json`をAndroid、iOS、backend、通知、手動手順が共通利用する。
- [ ] 主要UIにPerp／Spot／Bridge／Vault／Slippage／Gasを単独ラベルとして出さない。
- [ ] `python tools/check_plain_japanese.py`とmobile copy lintがCIでPASSする。
- [ ] 音声の「ペイパチャル」「生産価格」「スポット」「ブリッジ」「ボルト」の確認ケースがPASSする。
- [ ] 金額、資産、送金先、ネットワークを音声から推測で補完しないnegative testがPASSする。

### 清算価格

- [ ] 先物previewに清算価格の目安、清算判定価格、距離、口座方式、取得時刻がある。
- [ ] 約定後に最新口座状態の`liquidationPx`へ更新する。
- [ ] null、stale、position不一致、口座全体担保の誤解ケースをfail closedまたは説明表示で処理する。
- [ ] 端末とbackendで同じpreview inputに対する計算・丸めが一致する。

### JPYCとネットワーク手数料

- [ ] JPYC EXのfake adapterでlogin link、発行手続き、status return、入金確認のE2EがPASSする。
- [ ] 本人確認、審査、最終申込み確定をwallet側が代行しないcontract testがPASSする。
- [ ] `SUFFICIENT`、`LOW_SWAP_POSSIBLE`、`LOW_ZERO_SPONSOR_AVAILABLE`、`MANUAL_REQUIRED`、`BLOCKED`の全状態がPASSする。
- [ ] 手数料残高が十分な場合にswapしない。
- [ ] native balance 0の場合に通常swapを無条件開始しない。
- [ ] 1回上限、月間上限、価格ずれ、quote期限、route／sponsor allowlistをserver-sideで強制する。
- [ ] sponsorの二重回収、並行要求、残高枯渇、timeoutをテストする。

### 自然言語とChatGPT境界

- [ ] 取引Intent ParserからOpenAIへのegressがなく、非取引Support Gatewayから取引処理面／Signer／broadcastへnetwork reachabilityがない。
- [ ] 独立ウォレットの取引Parser出力はDraftだけで、決定論コアの再検証なしにExecution Capsuleにならない。OpenAI-facing出力はDraftにならない。
- [ ] ChatGPT／MCPのtool一覧は、抽象状態・固定用語・固定エラー・一般安全案内のexact 4-operation allowlistだけである。
- [ ] `execute`、`trade`、`send`、`transfer`、`swap`、`withdraw`、`sign`、`broadcast`相当toolをCIが拒否する。
- [ ] action内容を持つdeep link／QR、取引固有draft、quote、ボタン手順、復旧手順をChatGPTが返さない。

### 最初の限定承認と手動復旧

- [ ] Standing Authorizationにexpiry、資産、network、金額、取引倍率、保存済み送金先、月間手数料上限、revocationがある。
- [ ] 新規送金先、高額／全額、鍵・権限変更、scope expansionは毎回強い確認を要求する。
- [ ] 全recoverable errorがversioned manual fallbackへ結び付く。
- [ ] 手順に画面名、正確なボタン名、期待結果、安全確認、再試行、support codeがある。
- [ ] UI変更でボタン名と手順が不一致になった場合、CIが失敗する。
