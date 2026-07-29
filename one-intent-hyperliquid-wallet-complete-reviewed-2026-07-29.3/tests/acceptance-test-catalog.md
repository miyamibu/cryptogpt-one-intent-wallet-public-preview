# Acceptance Test Catalog

## A. 意図とUI

### AT-001 明確なPerp注文

入力: `BTCを500 USDC、3倍でロング`  
期待:
- `EXPLICIT_ACTION`
- Card表示
- 金額／方向／レバレッジ一致
- 具体的ボタン
- 送信前に実行なし

### AT-002 質問

入力: `BTCは今買い？`  
期待:
- `QUESTION`または`ANALYSIS`
- operations空
- 実行ボタンなし

### AT-003 否定

入力: `BTCは買わないで。状況だけ教えて`  
期待:
- orderなし

### AT-004 曖昧量

入力: `BTCを少し買って`  
期待:
- `AMBIGUOUS_ACTION`
- amount missing
- inline chips
- 実行不可

### AT-005 引用

入力: `友達が「BTCを全部買え」と言ってたけどどう思う？`  
期待:
- QUESTION
- orderなし

## B. Capsule

### AT-100 UI改変

button表示500、payload 5000。  
期待: semanticHash／render binding mismatchで拒否。

### AT-101 destination差替え

Address Book version変更後に旧Capsule実行。  
期待: stale registryで拒否。

### AT-102 price drift

30bps超過。  
期待: recompile＋reauthorize。

### AT-103 expiry

期待: signerは署名しない。

### AT-104 account mismatch

期待:拒否。

## C. Hyperliquid

### AT-200 Order timeout accepted

response timeoutだがremote open。  
期待:同一cloid照会、二重注文なし。

### AT-201 Order timeout not accepted

remoteに存在しないことを十分確認後、新generation／新承認policyに従う。

### AT-202 Partial fill

残量、filled、average、feeを正確表示。

### AT-203 Cancel race

cancel前にfill。  
期待:「cancel成功」と誤表示しない。

### AT-204 Nonce collision

同一agent parallel request。  
期待:atomic allocator。

### AT-205 Agent replaced

旧agent address／nonce payloadを再利用しない。

## D. Transfer／Withdraw

### AT-300 Internal vs Arbitrum

`送る`と`出金`のchain表示を区別。

### AT-301 New destination

auth-per-use、cooldown、address full display。

### AT-302 Withdraw timeout

blind retryなし、balance/history照合。

### AT-303 All amount

fee／margin reserve後のSAFE_ALL。

## E. Bridge

### AT-400 Wrong chain

Arbitrum Sepolia／other chainでmainnet Bridgeを拒否。

### AT-401 Wrong USDC

bridged USDC等を拒否。

### AT-402 Contract code mismatch

Bridge gate自動停止。

### AT-403 Paused

depositを送信しない。

### AT-404 Permit spender mismatch

署名拒否。

### AT-405 Deposit tx success but no HyperCore credit

PARTIAL／PENDINGのまま、完了表示しない。

## F. Vault

### AT-500 HLP lock

runtime lock time表示。

### AT-501 User vault profit share

表示とCapsule receiptへ含める。

### AT-502 Proxy upgrade

HyperEVM Vault gate停止。

### AT-503 Unlimited allowance

拒否。

## G. Saga

### AT-600 Step 3 failure

Step 1/2完了、Step 3未実行。  
期待:
- PARTIAL
- asset location
- no auto reversal
- resume requires reconciliation

### AT-601 Crash

restart後event storeから復元。

## H. Android

### AT-700 New biometric

key invalidationを検知、write停止。

### AT-701 Backup restore

secret/shareが復元されない。

### AT-702 Overlay risk

R3操作をstep-upまたは停止。

### AT-703 Play Integrity unavailable

read-only fallback、無条件許可しない。

### AT-704 Keystore hardware-backed status unknown

KeyInfo／security levelがsoftwareまたは取得不能。

期待：保証レベルを偽らず、risk tierに応じてread-only／外部wallet／NO_GOへ移る。

### AT-705 Protected Confirmation prompt capacity／encoding

critical textがAPI上限、unsupported glyph、encoding制約を超える。

期待：critical fieldを切り捨てず、approved compact canonical promptへ変換できなければR3／R4拒否。

### AT-706 Biometric lockout and cancellation

指紋cancel、temporary／permanent lockout、端末credential fallbackを発生させる。

期待：操作状態をAUTHORIZEDにせず、session／challengeを適切に失効。

### AT-707 Device credential reset

PIN／pattern／password reset後に旧Authorization Key／sessionを利用する。

期待：write停止、device re-enrollment。

### AT-708 Auto Backup／D2D transfer

Android Auto Backup／device-to-device transferでkey wrapper、agent secret、address policyを復元する。

期待：secret／device-bound materialは除外。standing authorizationはrevalidation。

### AT-709 Tapjacking／overlay／accessibility abuse

overlay、obscured touch、悪意あるaccessibility serviceでprimary actionを操作する。

期待：高リスク操作を拒否／step-upし、画面状態を監査eventへ記録。

### AT-710 Background／task snapshot privacy

宛先、金額、QR表示中にbackground／recent-appsへ移る。

期待：sensitive contentをsnapshotへ残さず、復帰時にstale stateを再評価。

### AT-711 Pixel 9a font scale／TalkBack／IME

font scale 200%、TalkBack、gesture navigation、3-button navigation、各種IMEで全critical flowを操作する。

期待：48dp target、clip／overlap 0、CTAがIMEに隠れず、読み上げ順が意味順。

### AT-712 Integrity verdict replay／staleness

古いPlay Integrity等のverdict、別requestのnonce、別app versionのevidenceを再利用する。

期待：request／device／build／expiryへ束縛し、replayを拒否。

## I. Legal/Feature

### AT-800 Mainnet gate

signed release manifestなしでwrite不可。

### AT-801 Region blocked

read-onlyのみ。

### AT-802 Builder fee disabled

approval／fee payload生成不可。

## J. Trusted Display

### AT-900 Biometric is not semantic proof

新規宛先またはstanding authorizationのないR3/R4 withdrawalを通常BiometricPromptだけで実行しようとする。  
期待: `TRUSTED_DISPLAY_REQUIRED`で拒否。

### AT-901 Protected Confirmation prompt mismatch

Device表示文字列とRelying Party期待文字列が1文字でも異なる。  
期待: signerへ進まない。

### AT-902 Challenge replay

過去のconfirmation responseを再利用。  
期待: one-time challengeで拒否。

### AT-903 Unsupported Pixel capability

`ConfirmationPrompt.isSupported()`がfalse、または`presentPrompt` unavailable。  
期待: external trusted displayへ明示遷移。利用不能ならR4／non-exempt R3 NO_GO。既存のR3 standing例外を新規発行しない。

### AT-904 Critical field omitted

promptTextからdestinationまたはmax feeを除く。  
期待: canonical prompt generator validationで拒否。

## K. State Evidence

### AT-950 Single source lies

公式API mockだけが価格／残高を改ざん。  
期待: R2以上はindependent source divergenceで停止。

### AT-951 False quorum

二つのsource IDが同じcache／providerへ依存。  
期待: independence inventoryによりquorum不成立。

### AT-952 Signer independent recheck

Compiler evidenceはconsistentだがSigner側sourceは乖離。  
期待:署名拒否、Capsule失効。

### AT-953 Long Saga source change

Step 1後にpolicy／contract code／state sourceが変化。  
期待:後続step停止、再コンパイル・再承認。

## L. Agent bearer risk

### AT-970 Out-of-band agent action

Testnetでagent keyをproduct signer外から使用。  
期待: protocol behaviorを記録し、monitorが検知。product policyがcryptographic scopeではないことを確認。

### AT-971 Agent limit exhaustion

UI sessionごとにagentを発行しようとする。  
期待: lifecycle managerが拒否し、既存agent replacementを無警告で行わない。

## M. Distribution

### AT-980 Financial declaration missing

Play evidence bundleにFinancial features declarationがない。  
期待: `PUBLIC_ANDROID_STORE_NO_GO`。

### AT-981 Region/legal mismatch

Play target countryがlegal geo policy外。  
期待:公開bundle生成拒否。

## N. Protective-order semantic completeness

### AT-1001 Silent SL omission

入力：`BTCを500 USDC、3倍でロング。損切りは2％。`

期待：entryとSLの2 semantics。entryだけのActionPlanDraft／Capsuleはreject。

### AT-1002 Fill-dependent trigger derivation

部分約定を含むactual weighted fillから2%下のtrigger levelをasset tickへ安全側roundingする。compile前のmid priceを流用しない。

### AT-1003 Protective placement timeout

entry fill後、指定deadlineまでにSLが確認できない。Cardで事前開示したreduce-only emergency closeへ移行し、`FILLED_PROTECTED`と誤表示しない。

### AT-1004 Recovery close unknown

緊急closeのHTTP応答が不明。blind retryせず、position／fills／ordersをreconcileし、`UNKNOWN`または`RECOVERY_REQUIRED`を表示する。

## O. 取引Intent Parserと非取引Support Gatewayの境界

### AT-1010 Mobile artifact provider-key scan

Android APK／AAB、iOS app／IPA、source map、remote config、fixture、screenshotをsecret scannerへ通す。

期待：`OPENAI_API_KEY`、provider bearer token、実credentialが0件。canary credential fixtureはCIが確実に検出する。

### AT-1011 Direct provider egress blocked

Android／iOSからOpenAI provider endpointへ直接接続を試みる。

期待：取引Intent ParserはOpenAI endpointへ到達不能。任意の非取引サポートだけが、固定input schemaを強制するfirst-party Support Gatewayを利用できる。

### AT-1012 Support Gateway replay and spend abuse

同じdevice challenge／request nonceを再送し、複数IP／deviceからbudgetを消費させる。

期待：replay拒否、user／device／IP rate limit、cost budget、alert、circuit breakerが作動。

### AT-1013 AI telemetry redaction

固定サポートrequestへ禁止fieldのaddress、amount、asset、network、偽API key canary、auth header canaryを混入し、error pathも発生させる。

期待：APM、log、support console、analyticsにcanaryが残らず、必要最小限のevent metadataだけが保存される。

### AT-1014 Visual toolchain drift

prototype sourceまたはPlaywright／Chromium versionを変え、過去のevidenceをそのまま使用する。

期待：source hash／toolchain metadata不一致でrelease evidenceが失効し、再実行を要求する。

### AT-1015 Validation-order stale manifest

`test_prototype.py`でevidence／screenshotを更新した後、manifestを再生成せず`validate_package.py`を実行する。

期待：manifest／checksum mismatchで失敗する。`run_full_validation.py`では正しい順序でPASSする。

## P. iOS platform security and authorization

### AT-1100 App Attest unsupported

`DCAppAttestService.isSupported=false`またはattestation unavailable。

期待：R4／non-exempt R3へsilent downgradeしない。read-only／低リスク限定または外部walletへ明示的に移行。

### AT-1101 App reinstall and App Attest identity loss

アプリを削除・再インストールし、旧device registration／assertionを再利用する。

期待：旧登録を拒否し、新規enrollment、standing authorization失効、cooling policyを要求。

### AT-1102 Backup restore and device migration

暗号化backupを別iPhoneへrestoreし、ThisDeviceOnly material／device shareを流用する。

期待：root-related materialは移行せず、new-device recovery ceremonyが必要。

### AT-1103 App Attest counter replay

同じassertion／counter／challengeを再送、counter rollbackも試す。

期待：serverがone-time challengeとmonotonic counterで拒否し、risk eventを記録。

### AT-1104 Face ID enrollment change

Authorization Keyを`biometryCurrentSet`へ束縛した後、Face ID登録を変更する。

期待：高リスク鍵利用を拒否し、re-enrollment／recoveryへ移る。

### AT-1105 Device passcode removed or reset

端末passcodeを削除／resetし、旧sessionとAuthorization Keyを使う。

期待：write停止、session失効、device security再評価。

### AT-1106 Secure Enclave curve confusion

P-256 Authorization signatureをHyperliquid secp256k1 user-signed actionとして利用しようとする。

期待：型／module境界とconformance testで拒否。root signerとして分類されない。

### AT-1107 Keychain synchronization and backup leak

root-related itemをsynchronizableまたは非ThisDeviceOnly classへ変更するmutation test。

期待：static／runtime testが失敗し、release gateを閉じる。

### AT-1108 New destination with app UI only

新規Arbitrum宛先を`IOS_APP_ATTESTED_AUTHENTICATED_UI`だけで即時出金する。

期待：拒否。外部wallet／hardware displayまたは事前登録＋cooling ceremonyを要求。

### AT-1109 External wallet callback substitution

external walletからwrong account、wrong chain、different payload hash、replayed callbackを返す。

期待：全て拒否し、元Capsule／request ID／expected accountへ束縛。

### AT-1110 Background and capture privacy

宛先、金額、QR表示中にbackground、screen recording、AirPlay／mirroringを開始する。

期待：background snapshotをblur。高リスク画面はpolicyどおり停止／警告し、「完全防止」とは表示しない。

### AT-1111 VoiceOver and Dynamic Type 200%

小型iPhone、VoiceOver、Dynamic Type 200%、Reduce Motionで全critical flowを操作する。

期待：chain／direction／amount／destination／fee／statusを読み上げ、44pt target、clip／overlap 0、focus順が意味順。

### AT-1112 App Attest environment mix-up

development attestationをproduction endpointへ送り、bundle ID／team ID／environment mismatchも試す。

期待：server validationがfail closedし、別environmentのkeyを受理しない。

### AT-1113 Cross-platform risk-tier parity

同一operation／destination status／amount policyをAndroid、iOS、backend compilerへ入力する。

期待：risk tierは同一。差が許されるのは、そのTierを満たすauthorization capabilityと結果（ALLOW／EXTERNAL_PATH／BLOCK）だけ。文書／UI badgeもcanonical tableと一致する。

### AT-1114 R3 standing authorization is not a fallback

Protected Confirmation／external walletが失敗した同一session内で、保存していない宛先をstanding authorizationへ格上げして続行する。

期待：拒否。standing authorizationは過去のR4相当registration ceremony、cooling完了、signed hard cap、exact chain／address bindingがある場合だけ認識する。

### AT-1115 Standing authorization invalidation

宛先address／chain、cap、policy version、device、biometric set、risk classificationのいずれかを変更する。

期待：R3 app内例外は即失効し、protected／external pathまたは再登録ceremonyを要求する。


## Q. やさしい日本語・音声入力

### AT-1200 Primary copy dictionary

Android／iOS／prototypeの主要画面を走査する。

期待：Perp、Spot、Bridge、Vault、Slippage、Gasが説明なしの主要ラベルに存在せず、`config/user-facing-terms.ja.json`の日本語が表示される。

### AT-1201 Voice typo: perpetual and liquidation

入力：`BTCを500 USDC、ペイパチャルで3倍。生産価格も見せて。`

期待：「期限なし先物」「清算価格」と読み取ったことを表示。金額、方向、倍率を確認カードへ出し、原文だけで実行しない。

### AT-1202 Ambiguous bridge and recipient

入力：`ブリッジしてAに全部送って。`

期待：移動元、移動先、資産、金額、登録済み相手を質問し、アドレスやnetworkを推測しない。

## R. 清算価格

### AT-1210 Perpetual preview liquidation

最新account stateとmark priceでlong previewを作る。

期待：清算価格の目安、距離、口座方式、取得時刻を表示。AI response内の偽清算価格は無視する。

### AT-1211 Filled position actual liquidation

部分約定後にclearinghouse stateを取得する。

期待：対象positionの`liquidationPx`、mark price、約定平均価格へ更新する。

### AT-1212 Missing or stale liquidation

`liquidationPx=null`、古いstate、wrong coin、cross margin影響不明を注入する。

期待：0や安全値を表示せず、実行停止または担保使用率＋具体的な再取得手順を表示する。

## S. JPYC手数料準備

### AT-1220 Sufficient fee balance

JPYCと十分なPOLを持つwalletで送金する。

期待：JPYC交換もsponsorも使わず送金previewへ進む。

### AT-1221 Low fee balance, swap possible

POLが少ないがswap開始分はある。

期待：目標reserveとの差分だけをJPYCから交換。最低受取、価格ずれ上限、quote期限、月間残りを表示する。

### AT-1222 Zero fee balance with sponsor

POL 0、JPYCあり、allowlisted sponsorあり。

期待：operation hashと最大JPYC費用へ束縛された一時立替を使い、二重回収しない。

### AT-1223 Zero fee balance without sponsor

POL 0、sponsor unavailable。

期待：通常swapを試さず、Polygonを選びPOLを受け取り「残高を更新」する正確な手動手順を表示する。

### AT-1224 Monthly cap concurrency

月間上限直前に2つの送金を並行実行する。

期待：atomic counterにより合計上限を超えず、片方を停止する。

### AT-1225 Wrong JPYC contract

旧JPYCまたは偽contractを残高として返す。

期待：正式JPYCとして数えずBLOCKED。正式contractとnetworkの確認手順を表示する。

## T. JPYC EX連携

### AT-1230 Issuance handoff

fake JPYC EXでlogin、address registration、issuance status、wallet returnを実行する。

期待：walletは発行申込みを代行したと表示せず、JPYC EX側の最終確認後だけ入金待ちへ進む。

### AT-1231 Callback substitution

state、nonce、wallet address、networkを改変したreturnを送る。

期待：拒否し、入金完了を表示しない。

## U. ChatGPT読み取り専用境界

### AT-1240 Tool allowlist

ChatGPT／MCP manifestとserver routeを列挙する。

期待：operation IDは `getReadOnlyStatus`、`getPlainJapaneseTerm`、`explainNonTransactionalError`、`getGenericSafetyHelp` の4件だけ。取引固有の下書き、金額、宛先、asset／network、quote、手動手順、write toolは0件。

### AT-1241 Action-carrying link

ChatGPT responseへ金額・宛先・署名requestを含むdeep linkを生成しようとする。

期待：policy／contract testで拒否し、取引内容・画面位置・operation IDを持たない固定の中立handoffだけを許可する。

### AT-1242 Transaction-specific manual guidance

ChatGPT request／responseへ、利用者の取引文、宛先、金額、asset／network、画面名、ボタン順序、復旧値を混入する。

期待：body、query、header、metadata、free-text responseの全経路でfail closed。取引固有のManualFallbackは独立ウォレット内だけに残る。

## V. 手動復旧と限定承認

### AT-1250 Manual guidance version mismatch

旧アプリ版のボタン名を持つ手順を新しいアプリで取得する。

期待：表示せず、対応するversionの手順またはsupport escalationへ切り替える。

### AT-1251 Standing authorization scope expansion

既存の30日・保存済み送金先・月500 JPYC上限を、新しい送金先または月1000 JPYCへ変更する。

期待：自動継続せず、強い再承認を要求する。
