# External Actions Required

このファイルは、現在の実行環境だけでは完了できない作業を、担当・入力・証拠・合格条件へ分解する。「あとで実機確認」ではなく、完了判定可能な契約として使う。

## 1. Apple開発・配布

| 作業 | 主担当 | 必要入力 | 必須証拠 | 合格条件 |
|---|---|---|---|---|
| Apple Developer組織登録 | Product／Legal | 法人情報、権限者 | enrollment receipt、Team ID | 組織アカウントで署名可能 |
| Xcode build | iOS Lead | Mac、pinned Xcode | build log、toolchain lock | warning policyを満たして成功 |
| iPhone実機 | iOS＋Security | iPhone 12、最小対応端末、現行Face ID端末 | device model／OS／test log／動画 | 3端末区分ごとにDoD Dを全項目PASS |
| App Attest production | Backend＋iOS | entitlement、server keys | attestation/assertion/counter evidence | unsupported／reinstallを含めfail closed |
| TestFlight | Release | signed archive、privacy answers | TestFlight build、tester report | write gateはTestnet限定 |
| App Store適格性 | Legal＋Product | business model、対象地域、license | written memo、review packet | public gate承認者2名が署名 |

## 2. Android

| 作業 | 主担当 | 必要入力 | 必須証拠 | 合格条件 |
|---|---|---|---|---|
| Pixel 9a実機 | Android＋Security | Pixel 9a、対象Android build | device／OS／KeyMint／biometric evidence | DoD Cを全項目PASS |
| Protected Confirmation probe | Android＋Security | runtime capability | success／unsupported／cancel logs | unsupported時にR4／non-exempt R3がsilent downgradeしない |
| Play Integrity／signing | Release | Play Console、upload key | signed AAB、integrity evidence | release keyとbackend allowlist一致 |
| Closed testing | QA | test accounts | crash、ANR、accessibility report | P0/P1未解決0 |
| Google Play適格性 | Legal＋Product | region、financial declarations | written memo、submission packet | public gate承認者2名が署名 |

## 3. Hyperliquid／chains

| 作業 | 主担当 | 必要入力 | 必須証拠 | 合格条件 |
|---|---|---|---|---|
| official SDK pin | Protocol Lead | commit／release | SBOM、golden vectors | Rust／backend parity byte一致 |
| Testnet write | Protocol＋QA | funded test wallet | action／response／reconciliation log | all failure injection cases PASS |
| agent characterization | Security | deterministic key | allowed action report | 想定外actionはMainnet blocker |
| Bridge2 fork | Chain Lead | pinned contract／Arbitrum fork | deposit／withdraw／dispute receipts | state machineと一致 |
| HyperEVM fork | Chain Lead | pinned RPC／contracts | codehash／receipt／reorg test | allowlistとstate evidence PASS |
| own-wallet Mainnet canary | Release Board | written approval、hard cap | signed plan、live evidence、postmortem | external audit＋legal gate後のみ |

## 4. Custody／MPC

- 監査済みThreshold ECDSA vendor／library比較
- DKG、sign、reshare、rotation、device loss、service shutdown、independent recovery
- server shareのHSM／TEE要件
- device share wrappingとbackup禁止条件
- vendor compromise／exit plan
- cryptography audit

**合格条件:** critical／high finding 0、recovery drill成功、単独主体でroot signature不能、generic signing endpoint不在。

## 5. 法務

日本の専門弁護士へ最低限、次を一つの事実関係資料として提出する。

- Perp／Spot／Vault／USDC送付／Bridge
- Existing Wallet／Managed Self-Custody
- API Wallet、MPC、recovery、fee、builder fee
- AIの役割と人間承認
- 対象地域、利用者、広告、助言表示
- AML／sanctions／privacy／consumer protection
- Apple／Googleへの申告内容

**合格条件:** 対象機能・地域・主体・必要登録・禁止事項・運用条件が書面で明確になり、release gateへ変換されている。

## 6. 外部監査

- iOS／Android mobile security
- backend／API／authorization
- Hyperliquid adapter／signing parity
- MPC／key ceremony
- supply chain／SBOM
- privacy／logging
- incident response／recovery

**合格条件:** critical／high 0。mediumはowner、期限、compensating control、release decisionを記録。

## 7. 任意の非取引AI provider／Support Gateway運用

| 作業 | 主担当 | 必要入力 | 必須証拠 | 合格条件 |
|---|---|---|---|---|
| provider credential管理 | Backend＋Security | production secret manager、rotation policy | key inventory、rotation／revocation log | mobile artifact／remote configへのcredential 0 |
| Support Gateway abuse test | Backend＋SRE | fixed schema、auth、nonce、rate／cost budget | transaction-field／replay／bot／spend injection report | 禁止field拒否、replay拒否、budget cap、alert、circuit breaker PASS |
| network isolation | Platform＋Security | service identity、network policy | reachability test | Transaction Intent→OpenAI到達0、Support Gateway→取引処理面／Signer／broadcast／root action到達0 |
| telemetry redaction | Privacy＋SRE | APM／logs／support console | transaction utterance／address／amount／asset／network／auth／fake-key canary scan | canary残存0、retention／access audit PASS |

# 2026-07-29.1追加の外部作業

## JPYC EX本番連携

**担当:** 事業責任者、法務、backend担当  
**必要なもの:** JPYC株式会社との接続契約、連携API仕様、client credential、redirect URI登録、利用規約・プライバシー表示、sandbox／production環境情報。  
**作業:** JPYC EXの事業者窓口で申込み、wallet bundle ID／package name、redirect URI、受取network、security contactを登録する。発行／償還の最終申込みをwalletが代行しないことを画面と契約で確認する。  
**完了証拠:** 契約番号、production credentialのsecret manager登録、登録済みredirect URI、sandbox／production contract test、JPYC側の承認記録。  
**再実行:** 新releaseでJPYC EX sandbox integration testとreceipt reconciliation testを実装・記録したうえで、`python3 -B tools/run_full_validation.py && python3 -B tools/check_operational_readiness.py`を実行する。現baselineにはlive partner test scriptがないため、追加前はblockerを閉じない。  
**有効化候補:** `jpyc_ex_handoff_staging=true`。Mainnet発行導線は法務・security review後だけ。

## JPYCの正式コントラクトとnetwork registry

**担当:** protocol担当＋security reviewer  
**作業:** JPYC公式developer資料、公式GitHub、JPYC EX提供資料を照合し、network、chain ID、contract、decimals、開始日、旧JPYCとの区別をversioned registryへ登録する。deployed bytecodeとruntime挙動も確認する。  
**完了証拠:** source pin、照合ログ、code hash、two-person approval。  
**有効化候補:** 該当networkの`jpyc_asset_registry=true`。

## ネットワーク手数料の代理支払い／初回立替

**担当:** security、treasury、fraud、backend、法務  
**必要なもの:** sponsor／paymaster／relayer provider、監査報告、資金口座、rate limit、reimbursement契約、停止手段。  
**作業:** providerとcontractをallowlistへ固定し、operation hash、max fee、expiry、idempotency、月間cap、二重回収防止、残高枯渇alertをTestnet／stagingで検証する。  
**完了証拠:** 外部監査、abuse test、incident drill、treasury reconciliation、残高監視alert。  
**再実行:** 新releaseでfee-provider sandbox、zero-native-balance canary、reimbursement／failure-charge ledger testを実装・記録したうえで、`python3 -B tools/run_full_validation.py && python3 -B tools/check_operational_readiness.py`を実行する。現baselineにはlive provider test scriptがないため、追加前はblockerを閉じない。  
**有効化候補:** `fee_sponsor_staging=true`。Mainnetは別のtwo-person approval。

## JPYCから手数料用資産への交換経路

**担当:** protocol、security、legal、treasury  
**必要なもの:** 対象DEX／aggregator、route、liquidity、正式token pair、quote API、spender／router contract。  
**作業:** exact input／minimum receive、価格ずれ、quote expiry、approval scope、simulation、MEVリスク、route停止時のmanual fallbackを検証する。日本の規制・提供地域の法務確認も行う。  
**完了証拠:** contract／bytecode pin、liquidity test、price impact test、legal sign-off、security review。  
**有効化候補:** networkごとの`jpyc_fee_swap_staging=true`。

## OpenAI／ChatGPT読み取り専用連携

**担当:** product、security、privacy、legal  
**作業:** current OpenAI App Developer TermsとUsage Policiesを再確認し、tool一覧が残高概要・状態・説明・手順だけであることを審査する。注文、送金、swap、出金、署名、action carrying linkがないことをcontract testで証明する。  
**完了証拠:** tool manifest、read-only annotations、privacy review、OpenAI review evidence（必要な場合）、禁止tool CI結果。  
**注意:** 規約が変わっても金融writeを自動有効化しない。

## Hyperliquid Testnetと清算価格

**担当:** protocol、QA  
**必要なもの:** Testnet account、agent key、test funds、official API access。  
**作業:** long／short、isolated／cross、partial fill、`liquidationPx=null`、stale state、複数positionを実行し、previewと成立後の清算価格表示を照合する。  
**完了証拠:** request／response fixture、fill ID、account state、screen recording、expected／actual comparison。  
**有効化候補:** `hyperliquid_testnet_write=true`。Mainnetとは別gate。

## iPhone／Android実機とStore

既存項目に加え、JPYC、清算価格、手数料準備、Standing Authorization、manual fallbackをVoiceOver／TalkBack、文字200%、暗い表示、通信断、外部wallet復帰で検査する。Store公開は組織account、地域別法務、金融機能申告、外部監査が揃うまでNO_GO。
