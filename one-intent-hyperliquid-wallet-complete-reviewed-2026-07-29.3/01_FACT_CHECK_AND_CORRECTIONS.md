# 前案の抜け穴監査と修正

以下は、前案で誤解されやすかった点、断定が強すぎた点、設計上の穴を洗い出した結果である。

## 1. 「ChatGPTにプラグインして発注」は不可

### 問題
ChatGPT Apps SDK、カスタムMCP、GPT Actionsの中から取引・送金を実行できるようにする案。

### 修正
OpenAI App Developer Termsは、OpenAIサービスを通じて金銭移転、暗号資産移転、金融・投資取引を開始・実行・促進することを禁止している。したがって、実行機能は独立したAndroid／iPhoneネイティブアプリに置く。

### 採用仕様
- ChatGPT／OpenAI-facing: 抽象read-only状態、固定用語・エラー、一般安全案内、固定中立handoffだけ
- 独立モバイルアプリ: Android／iPhoneで会話、承認、署名、Hyperliquid実行
- 取引Intent解析: 端末内の決定論parserを第一候補。必要時もOpenAIから分離された独立運用の非OpenAIコンポーネントだけを候補にする
- 人間の具体的な実行操作を必須化

## 2. 「API Walletは注文専用」はプロトコル保証ではない

### 問題
API Walletを、OAuthの`trade-only`権限のように扱っていた。

### 事実
Hyperliquidの`approveAgent`はagent address、name、nonce等を承認するが、銘柄、金額、操作種別の細粒度スコープをプロトコル上付与する仕組みではない。

### 修正
- API Walletを**限定権限そのもの**と呼ばない
- Signer Serviceのコードとネットワーク経路を注文・取消系だけに制限
- 取引用残高を別アカウント／サブアカウントで制限
- root user-signed actionの署名経路を完全分離
- agent key漏えいを「全注文・レバレッジ変更等が可能な重大侵害」として扱う

## 3. サブアカウントを全ユーザー前提にしない

### 問題
全ユーザーが取引用サブアカウントを使える前提だった。

### 修正
利用資格や上限はruntimeで照会し、使えないユーザーには次を適用する。

- 単一アカウント＋アプリ内の厳格な取引上限
- agent keyの短寿命運用・即時失効導線
- 残高の安全ウォレットへの定期退避
- 高額資産を同一ホットアカウントへ置かない運用ガイド

## 4. Android Keystoreへsecp256k1鍵を直接置けると断定しない

### 問題
Ethereum／Hyperliquidのsecp256k1秘密鍵を、Android Keystoreでネイティブ生成・利用できる前提だった。

### 修正
Android KeyMintで広く保証されるEC曲線とsecp256k1は同一ではない。そこで以下のいずれかを採用する。

**案A: 監査済みThreshold ECDSA**
- 端末share
- Policy signer share
- 独立recovery share
- 完全秘密鍵を平文復元しない

**案B: ローカルsecp256k1鍵のhardware-backed wrapping**
- secp256k1鍵はアプリ領域の暗号化blob
- wrapping keyはAndroid KeystoreのAES-GCM
- P-256 auth keyでExecution Capsuleを認証
- 高額操作はauth-per-use

案Aを推奨するが、採用製品・監査・復旧性を確認するまで確定しない。

## 5. 「MPCなら非カストディアル」は自動成立しない

### 問題
2-of-3 MPCを使えば自動的に安全・非カストディアルと扱っていた。

### 修正
実際の評価は次で決まる。

- サービス側が単独または共謀して署名できるか
- shareの再構成・バックアップ・更新方法
- サービス停止時にユーザーだけで回収できるか
- Policy signerが署名を拒否・検閲できるか
- 法的に「他人のための管理」と評価されるか

よって、MPCベンダー選定と日本法上の評価をMainnet公開ゲートにする。

## 6. 「1回承認」は「1トランザクション」ではない

### 問題
Spot売却→Vault入金→出金を、一括承認すれば一体の処理のように見える。

### 修正
HyperCore、Bridge、HyperEVMの複数操作は原子的でない。Execution Capsuleは1回承認を実現するが、実行はSagaであり部分成功し得る。

必須表示:
- どこまで成功したか
- 資産が現在どこにあるか
- 次に安全に再開できる処理
- 巻き戻しが新しい市場取引になる場合の損失可能性

## 7. 「送信1回」を承認と呼ぶ条件

### 問題
どんな文章でも送信すれば即実行されると、質問と命令の誤判定が起きる。

### 修正
即実行できるのは、次を満たす場合だけ。

- 操作種別が確定
- 資産が一意
- 方向が確定
- 金額または安全な`ALL`計算が確定
- 宛先が保存済みか、画面上で完全表示
- 最大スリッページ・最小受取・手数料上限が確定
- Execution Cardが送信前に表示済み
- ボタン文言が具体的

質問、提案、曖昧語は実行へ昇格させない。

## 8. `ALL`は残高全額ではない

### 問題
「全部売る」「残りを出金」を単純な全残高として扱うと、証拠金・手数料・ガス・dust不足になる。

### 修正
`ALL`はcompilerが次を差し引いた動的上限とする。

- 未約定注文拘束
- 維持証拠金・安全バッファ
- 出金手数料
- 後続stepで必要な金額
- Bridge／token minimum
- rounding／dust
- Vaultロック中資産

## 9. Bridgeの手数料・時間・アドレスを固定しない

### 問題
「1 USDC」「3～4分」「公式アドレス」をコードへ固定すると仕様変更で壊れる。

### 修正
- 公式資料の基準値は説明用
- 実行時はchain ID、contract address、bytecode hash、paused state、token address、minimum、feeを検証
- 情報が取得不能またはallowlist不一致なら停止
- UIには取得時刻を表示

## 10. Vaultを同じ商品として扱わない

### 問題
HLP、HyperCore user vault、HyperEVM vaultを同一の`vaultTransfer`で抽象化しすぎる。

### 修正
別Adapterと別リスクモデルにする。

- HLP: protocol vault、ロック期間等をruntime照会
- HyperCore User Vault: owner profit share、open positions、withdrawal slippage
- HyperEVM Vault: 外部コントラクト、監査、upgradeability、oracle、allowance、chain riskを別評価

未承認のHyperEVM contractは一般署名しない。

## 11. Multi-sigとHyperEVMの境界

### 問題
HyperCore native multi-sigを万能のroot securityとして使う案。

### 修正
HyperCore multi-sigとHyperEVMの支配関係は同一でない。HyperEVMやArbitrumまで統一したい場合、EOA互換署名を扱うMPC等を検討する。ただしMPCを採用しても法務・復旧・ベンダーリスクは別途残る。

## 12. LLMがアドレス・トークン・コントラクトを解決してはならない

### 問題
「友人A」「HLP」「USDC」などをAIが直接アドレスへ変換すると、幻覚・プロンプトインジェクション・同名トークン攻撃が起きる。

### 修正
LLMはalias文字列まで。実アドレスは決定論的Resolverが次からのみ取得する。

- ユーザーが保存したAddress Book
- 公式metadata
- 署名済みallowlist
- chain上で検証したcontract registry

外部Webページの文章を実行入力へ混ぜない。

## 13. WebSocketだけで完了判定しない

### 修正
- WebSocketは低遅延通知
- REST／info endpointは再照合
- BridgeはArbitrum event・HyperCore creditを両方追跡
- タイムアウトを失敗とみなして盲目的に再送しない
- 注文は`cloid`、署名actionはnonce、複合処理はstep idで冪等化

## 14. Play Integrityやroot検知を絶対条件にしすぎない

### 問題
Integrity verdictだけで安全を保証できるように見える。

### 修正
これは補助信号であり、鍵分離・明示承認・署名内容固定の代替ではない。

- 高リスク時のstep-up
- screen capture／control riskの警告
- 改変アプリの拒否
- requestHashでExecution Capsuleと判定を結び付ける
- 誤判定時の安全なread-only fallback

## 15. 「初日から全部」は公開範囲ではなくコード構造

### 修正
全Adapterを最初から設計・実装対象に含めるが、Mainnet Feature Gateは個別に閉じる。未検証機能を「全部入り」の見栄で有効化しない。

## 16. OpenAIへ取引文・取引条件を送らない

### 修正
OpenAIサービスへ送らないもの:
- 取引文・音声原文
- 送金先、Address Book、金額、asset／network選択、売買方向、取引倍率
- quote、Execution Capsule、authorization、payload、署名材料
- 秘密鍵、seed、raw署名、MPC share
- ウォレット全履歴、正確な残高、本人確認情報
- API credential

OpenAIを使う任意の非取引サポートへ送れるのは、固定用語ID、固定安全トピックID、固定エラーコード、UI言語、取引内容をエンコードしない短期限の不透明なread-only reference IDだけである。Responses APIを使う場合は`store:false`、厳格Schema、field allowlist、ZDR/MAM適格性確認を適用する。

取引Intent解析は端末内の決定論parserを第一候補とし、必要時もOpenAIから分離された独立運用の非OpenAIコンポーネントだけを候補にする。

## 17. 日本法は製品名ではなく実態で判断される

### 問題
「非カストディアル」「単なるUI」「AIは翻訳だけ」と呼べば登録不要と考えること。

### 修正
少なくとも次の論点について日本の専門弁護士の書面意見を得る。

- 暗号資産デリバティブ注文の媒介・取次・代理
- 投資助言に該当する会話・ランキング・提案
- Spot交換の媒介
- 暗号資産・電子決済手段の送付・管理
- MPC／policy signerによる管理権限
- builder fee・subscription・成功報酬
- AML/CFT、Travel Rule、制裁、反社、未成年者
- 海外業者への誘導・日本居住者向け勧誘

## 18. 変更監視がない完成版は完成ではない

### 修正
毎日またはリリース前に監視する。

- OpenAI terms／usage policies／API data controls
- Hyperliquid docs／SDK／contract code／chain parameters
- Bridge address／bytecode／paused state
- Android security・Play Integrity
- 日本法令・金融庁発表
- 公式Xアカウントの過去7日投稿

仕様差分が検出されたら、影響機能を自動停止できるようにする。

## 19. agent keyはアプリ外からpolicyを迂回できる

### 問題

Signer Serviceがaction allowlistを持てば、API Wallet自体も限定権限になるように見える。

### 修正

agent private keyを盗んだ攻撃者は、製品のSigner Serviceを通らずに署名できる。製品policyはprotocolによる暗号学的scopeではない。

- agent keyをbearer credentialとして扱う
- dedicated account／subaccountと資産上限
- device-localまたは監査済みthreshold保護
- agentの全L1 actionをTestnet characterization
- 異常action監視
- 即時revoke／replace
- 漏えいaddressを永久にburn扱い

## 20. agentをUIセッションごとに無制限発行しない

Hyperliquidはapproved agent数に上限がある。nonce衝突回避は「取引process／並列subaccount単位」で設計し、短いUIセッションごとにagentを増殖させない。上限とreplacement影響をruntimeで扱う。

## 21. BiometricPromptはTrusted Displayではない

### 問題

生体認証と`semanticHash`があれば、人間が正しい取引内容を確認したと扱うこと。

### 修正

BiometricPromptは鍵利用の認証。表示内容の高保証確認は別問題である。R4とstanding例外を満たさないR3はAndroid Protected Confirmation、外部wallet Trusted Display、またはhardware walletを要求する。R3 standing例外は事前R4 ceremony＋cooling＋hard capを必須とする。

## 22. Pixel 9aのProtected Confirmation対応を断定しない

`ConfirmationPrompt.isSupported()`と実際の`presentPrompt`成功を実機で確認する。accessibility service等により利用不能になる場合も試験する。未対応時に通常認証へ静かに降格しない。

## 23. `promptText`と`extraData`を混同しない

Protected Confirmationでは、人間が承認した内容は`promptText`である。Capsule hashを`extraData`へ入れるだけでは、そのhashの意味を人間が読んだことにはならない。critical fieldをcanonical prompt textへ含め、Relying Partyが文字列一致を検査する。

## 24. 単一APIを真実の唯一ソースにしない

公式APIまたは自社APIがstale／侵害された場合、CompilerとReconcilerが同じ誤状態を信じる可能性がある。

- R2以上は独立二系統の状態証拠
- R3/R4は自前non-validating node／chain receipt等を優先
- 同一cacheを複数sourceと数えない
- 乖離時はwrite停止

## 25. TestnetとMainnet、Bridgeを同一視しない

HyperCore Testnet成功は、Bridge2、HyperEVM、Mainnet流動性・rate limit・運用の完全な同等性を証明しない。

- HyperCore: Testnet
- Bridge2: official testnet pathが明示された機能＋local contract harness／Arbitrum fork
- HyperEVM: test environment／fork
- Mainnet:全ゲート後、自分の少額資金だけでcanary

Hyperliquid bug bountyのルールに従い、無許可の攻撃試験をMainnetで行わない。

## 26. Testnet faucetの前提をonboardingへ入れる

現行の公式案内では、同じaddressでMainnet deposit履歴がないとTestnet faucetを使えない。Testnet利用を「完全に無資金・無前提」と説明しない。テスト用address、資金、法務・運用手順を準備する。

## 27. Google Play配布は別の公開ゲート

Financial features declaration、cryptocurrency wallet／exchange、digital wallet、money transfer、financial advice等の該当性を正確に申告する。暗号資産アプリの地域規制・必要資料をGoogleが要求できるため、法務完了だけで配布可能と断定しない。

## 28. 「1つのIntent」と「1回の署名」を同一視しない

**前案の穴:** Existing Wallet Modeでも、送金・出金・Bridge・複合Sagaが常にアプリ内1タップで終わるように読めた。

**修正:** Trade Agent承認後の通常取引は1タップ化できる。一方、root user-signed actionは外部walletで都度確認が必要になり得る。全機能のアプリ内1回認証は、監査済みManaged Self-Custody Modeでのみ有効化する。

## 29. HashだけでTrusted Displayを代替しない

**前案の穴:** `semanticHash`、render、prompt、state evidenceの相互束縛が文書上は曖昧だった。

**修正:** `ONE_INTENT_HASH_PROFILE_V1`を定義し、派生hashを再計算する。実行時Authorization Envelopeはsemantic、render、state、trusted prompt、challengeを同時に束縛する。

## 30. ChatGPTからaction carrying deep linkを出さない

**前案の穴:** ChatGPT側をread-onlyとしても、注文内容入りdeep linkで外部アプリを起動すれば、取引をfacilitateしたと評価される余地が残る。

**修正:** ChatGPT側からは取引payload、宛先、金額、署名challengeを含むlink／QRを発行しない。独立アプリ内でユーザーが改めて入力・確認する。

## 31. iOSをAndroidと同じ安全機能として扱わない

### 問題

Android Protected Confirmationと同等の一般目的APIがiOSにもある前提で、R4／R3の保証経路を同一と仮定して押し込むこと。

### 修正

- iOSは`IOS_APP_ATTESTED_AUTHENTICATED_UI`を定義
- App Attestはapp instance、Secure Enclave P-256はAuthorization Key、Face IDは鍵利用認証として使う
- `trustedDisplayClaim=false`をSchemaで固定
- 新規宛先、高額／全額出金、鍵・復旧変更はexternal／hardware pathまたは事前登録＋cooling ceremony

## 32. Secure EnclaveへHyperliquid root keyを直接置かない

Secure Enclaveの一般的なCryptoKit署名はP-256であり、Hyperliquid／Ethereum root actionのsecp256k1とは異なる。Managed Self-Custodyは監査済みThreshold ECDSA、Existing Walletはexternal walletを使う。

## 33. iPhone公開はApp Storeの独立NO-GO

ウォレット、暗号資産取引、暗号資産先物はApp Review上の提出主体・認可要件を持つ。コード完成、TestFlight、非カストディ表示はその代替にならない。

## 34. 2026-07-29.1追加訂正

### ChatGPTプラグインで送金・取引を全部実行できるか

2026-07-29時点では、その構成を採用しない。OpenAI App Developer Termsは、OpenAI Servicesを通じた金銭移転、暗号資産移転、金融・投資取引の開始、実行、その他の促進を禁止している。ChatGPT App／MCPは、抽象化したread-only状態、固定用語・固定エラー説明、一般安全案内、中立的な独立ウォレット起動案内だけに限定し、取引固有の下書きやボタン手順も返さない。自然言語での実行体験は独立ウォレット内へ実装し、取引Intent解析には端末内の決定論parserまたはOpenAIから分離された独立運用の非OpenAIコンポーネントを使う。

### JPYCしかない場合はJPYCを少し交換すれば必ず送れるか

必ずではない。通常のオンチェーン交換自体にもネットワーク手数料用資産が必要である。残高が0なら、監査済みのsponsor／paymaster／relayerが使える場合だけ一時立替を行い、使えなければ外部から必要最小限の手数料用資産を受け取る手順へ切り替える。

### JPYC EX連携APIでwalletが発行を確定できるか

できない。連携はログイン・アカウント連携、発行／償還画面への導線、address登録補助、status連携であり、審査、追加認証、最終受付、確定はJPYC側で行う。

### 先物の清算価格は注文前後で同じか

同じとは限らない。注文前は最新口座状態からの目安、成立後は実際のposition stateに含まれる`liquidationPx`を表示する。他position、口座残高、mark price、cross／isolated方式で変動するため、取得時刻と口座方式を併記する。

## 35. 依頼にない損切りを画面例へ足してはいけない

**前版の穴:** 音声依頼は「3倍」と清算価格表示だけだったのに、画面例が「損切り2%」を追加していた。

**訂正:** 取引条件を発明しない。画面例は「損切りは未設定」と表示し、利用者が明示した場合だけ別operationとして保持する。別の仕様例で利用者原文に損切り2%が含まれるケースとは区別する。

## 36. まとめ操作の最低額と最大額を混ぜない

**前版の穴:** 売却後の最低受取から預入額を引いた値を「残り最大額」と表現し、さらに送金費用との算数が不整合だった。

**訂正:** min/max、費用差引前後、step input/outputを別型へ分ける。画面例は948.50−300.00＝648.50、さらに費用上限1.00を引き最低到着647.50とする。

## 37. 固定CTAの見えやすさより重要明細の到達性を優先する

**前版の穴:** 常時表示のボタンが短い端末で明細や手順を覆い、自動testもscroll状態を変えて見逃した。

**訂正:** primary actionをreview末尾へ置き、固定領域は「下に続く／ここが最後」だけにする。初期状態、途中、末尾を別々に検査する。

## 38. 代理支払いはprovider名だけでなく契約・quoteへ結び付ける

**前版の穴:** 「確認済みの提供者」とだけ表示しても、法人、連絡先、規約、精算先、失敗請求、対象操作の識別がなかった。

**訂正:** provider identityとterms hashをregistryへ置き、quoteをaccount、network、operation digest、nonce、費用、期限、精算先へ束縛する。欠ければzero-gas自動経路はNO-GOとする。

## 39. 手動補充量を静的な固定値にしない

**前版の穴:** 0.05 POLのような固定値は、混雑、価格、送金元最低出金額、対象操作の差を無視する。

**訂正:** live operation-bound estimateのID、推奨量、上限、生成時刻、有効期限を取得できる場合だけ数量を案内する。静的な例では数量をnullにし、取得不能なら送らない。

## 40. 複数のCodexプロンプトを正本として残さない

**前版の穴:** 同一内容の長いプロンプトが3か所にあり、将来1つだけ更新される可能性があった。

**訂正:** `codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md`だけを正本とし、rootの17/34は短い案内にする。検証で重複化を拒否する。

## 41. 自動検証器そのものを監査対象にする

**前版の穴:** 旧validatorは120条件・旧画像名を期待し、新しい証拠形式と矛盾していた。

**訂正:** 288条件、10画像、locale、source/test hash、両themeを厳密に照合する。adversarial auditをmanifest生成前に実行し、古い主張や配布ごみも拒否する。
