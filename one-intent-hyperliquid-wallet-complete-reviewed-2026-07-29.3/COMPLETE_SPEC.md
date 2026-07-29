# One-Intent Hyperliquid Wallet — 統合完全仕様

## 0. 文書ステータス

- **文書版:** 2026-07-29.3
- **基準日:** 2026-07-29 JST
- **対象端末:** Android（Pixel 9aをP0）／iPhone（iPhone 12実機＋小型端末＋現行Face ID端末をP0）
- **製品形態:** 独立した非公式Hyperliquidクライアント
- **現在のリリース判定:** `DESIGN_GO / OFFLINE_PROTOTYPE_GO / CODEX_IMPLEMENTATION_GO / ANDROID_BUILD_NO_GO / IOS_BUILD_NO_GO / TESTNET_WRITE_NO_GO / PERSONAL_SMALL_MAINNET_NO_GO / CLOSED_ALPHA_NO_GO / PUBLIC_ANDROID_STORE_NO_GO / PUBLIC_IOS_APP_STORE_NO_GO`

この仕様は、会話による操作性を最大化しながら、AIが署名権限を持たない構造を定義する。Perp、Spot、送金、出金、Bridge、Vaultを最初から同一の製品モデルで扱うが、異なるリスクを無理に同一視しない。

---

## 1. 製品の一文定義

> 自然言語から、画面表示と暗号学的に結び付いたExecution Capsuleを生成し、ユーザーの原則1回の明示操作で、許可されたHyperliquid関連アクションだけを実行するAndroid／iPhone対応ウォレット。

---

## 2. 非交渉原則

### 2.1 ChatGPT内から実行しない

ChatGPT App、Apps SDK、MCP、GPT Actionに書き込みツールを公開しない。ChatGPT／OpenAI-facing側で可能なのは、抽象read-only状態、固定用語・固定エラー説明、一般安全案内、固定中立handoffだけ。

独立アプリの取引Intent解析は、端末内の決定論parserを第一候補とし、必要時もOpenAIから分離された独立運用の非OpenAIコンポーネントだけを候補にする。取引文、宛先、金額、資産・network選択、authorization、payload、署名材料をOpenAIサービスへ送らない。

```text
独立ウォレット内の自然言語 → UNTRUSTED ActionPlanDraft
```

Parserは署名、送信、再試行、宛先解決、コントラクト解決、金額丸め、リスク判定を行わない。OpenAIを使う任意機能は、固定用語・固定エラー・一般安全案内・抽象read-only状態だけの非取引Support Gatewayへ分離する。

### 2.2 人間の確認を残す

具体的な実行は、ユーザーが画面上の具体的なボタンを押すことを起点とする。

悪い例:

```text
[送信]
```

良い例:

```text
[BTCを500 USDC、3倍でロング＋損切り2%]
[0x12…89ABへ50 USDC送る]
[HLPへ300 USDC入金]
```

### 2.3 簡単さは表面、安全性は裏側

通常操作は1回でも、裏側で次を省略しない。

- account state snapshot
- token・asset metadata
- chain・contract verification
- amount・fee・margin calculation
- policy evaluation
- stale-state検知
- nonce・cloid・idempotency
- signing domain verification
- trusted-display requirement
- independent state evidence／source divergence
- broadcast result reconciliation
- partial success recovery

### 2.4 画面表示と署名内容を一致させる

ユーザーが見た内容、端末が承認した内容、Policy Signerが許可した内容、実際に署名するpayloadは、同一Execution Capsuleのcanonical hashから派生しなければならない。ただし通常UIのhashだけでは人間が正しい意味を見た証明にならない。R4は必ずprotected／external／hardware経路を要求する。R3は原則同様だが、R4相当ceremonyで事前登録・cooling済みの宛先に対するhard-cap付きstanding authorizationだけを明示的例外とする。

### 2.5 機能単位で停止できる

Feature Gateは最低限、次を独立させる。

- `perp_trade`
- `spot_trade`
- `internal_usd_send`
- `internal_spot_send`
- `arbitrum_withdraw`
- `arbitrum_bridge_deposit`
- `hlp_deposit`
- `hlp_withdraw`
- `user_vault_deposit`
- `user_vault_withdraw`
- `hyperevm_vault`
- `external_bridge`
- `builder_fee`
- `account_mode_change`
- `agent_approval`

---

## 3. ユーザー体験

## 3.1 初回セットアップ

### Step 1: アプリの真正性を確認

- Google Play配布は審査・地域適格性完了後のみ。開発中は署名済みinternal distribution
- package name、signing certificate、versionをサーバーと照合
- Hyperliquid公式ではないことを明記
- 正式なサポート窓口とドメインを表示

### Step 2: ウォレット方式を選択

初期版では二つのモードを用意する。

#### A. Existing Wallet Mode

- 初回に既存ウォレットでTrade Agentを承認し、上限内のPerp／Spotはアプリ内agentで1タップ化できる
- `usdSend`、`spotSend`、`withdraw3`、Permit、鍵変更等のroot actionは、外部ウォレット／hardware walletで原則都度署名する
- 外部ウォレットの「セッション署名」をHyperliquidの標準機能として仮定しない。採用するwallet/session-key方式ごとに表示・失効・権限を検証する
- 秘密鍵をアプリが生成・保管しない
- root actionを含む複合Sagaでは、1つのIntentでも複数のwallet確認が発生し得ることを実行前に表示する
- UXは少し遅いが、MPC導入前の安全な基準実装

#### B. Managed Self-Custody Mode

- 監査済みThreshold ECDSAまたはhardware-wrapped local key
- 復旧経路を先に試験
- サービス側だけで署名できない
- 公開前に法務評価が必要

MVP TestnetはAから始め、Bは別Feature Gateとする。

### Step 3: 取引ポリシー

一度だけ、次を設定する。

```text
許可銘柄
1注文上限
総エクスポージャー上限
最大レバレッジ
日次損失上限
最大スリッページ
登録済み送金先
登録済みVault
セッション時間
高リスク認証閾値
```

### Step 4: 端末認証

- Pixel 9aの強い生体認証またはdevice credential
- Android Keystore auth key作成
- `ConfirmationPrompt.isSupported()`を記録し、R4およびstanding例外を満たさないR3のTrusted Display経路を確定
- recovery drill
- backup／D2D対象から秘密情報を除外

---

## 3.2 日常のPerp取引

入力:

```text
BTCを500 USDC、3倍でロング。損切り2%
```

入力欄の直上:

```text
BTC-PERP  ロング
注文元本     500.00 USDC
レバレッジ   3x
推定建玉     1,500.00 USDC
注文方式     IOC
最大滑り     0.30%
損切り水準   実約定平均価格 -2.00%（Markでtrigger）
最大想定損失 30.00 USDC + fee（概算）
価格基準時刻 12:34:56.210 JST

[BTCを500 USDC、3倍でロング＋損切り2%]
```

ボタン押下後:

1. 最新stateで再コンパイル
2. 許容範囲内なら同じCapsuleを認証
3. agent signerでorder action署名
4. `/exchange`送信
5. WebSocketでorder update
6. REST／infoで実約定数量と加重平均約定価格を照合
7. 許可済みformulaから損切り数量・trigger priceを導出し、2秒以内にreduceOnly triggerを配置
8. 配置失敗時は、Cardで開示済みの`REDUCE_ONLY_MARKET_CLOSE`を実行し、裸のポジションを残さない
9. entry、protective order、recoveryの各状態をチャットへ表示

価格または条件が許容範囲を超えたら、勝手に変えず再承認を求める。ユーザー文の「損切り」などのactionable clauseを黙って落としたActionPlanDraft／Execution Capsuleは無効とする。

---

## 3.3 Spot

入力:

```text
SpotでHYPEを300 USDC分買う
```

必須表示:

- pair
- quote amount
- estimated base amount
- minimum received
- max slippage
- fee
- metadata version
- account mode

Spot asset ID、tick、lot、symbol mappingはruntime metadataから決定する。LLMや固定配列を使わない。

---

## 3.4 内部送金

入力:

```text
友人Aに50 USDC送る
```

ResolverがAddress Bookからのみ解決する。

```text
HyperCore内送金
宛先名     友人A
宛先       0x1234…89AB
金額       50.00 USDC
チェーン   HyperCore（Arbitrum出金ではない）

[友人Aへ50 USDC送る]
```

初回宛先、新規変更直後、高額送金はauth-per-use、cooldown、任意のtest transferに加え、Protected Confirmation／外部wallet／hardware walletのTrusted Displayを要求する。

---

## 3.5 Arbitrum出金

入力:

```text
自分のArbitrumへ200 USDC出金
```

```text
Hyperliquid → Arbitrum One
宛先       自分のArbitrum
アドレス   0xABCD…1234
金額       200.00 USDC
手数料     runtime取得値
最低受取   199.00 USDC（例）
推定時間   runtime取得値・保証ではない
情報取得   12:35:02 JST

[Arbitrumへ200 USDC出金]
```

`withdraw3`はroot user-signed action経路。API Wallet経路と混ぜない。

---

## 3.6 公式Bridge2入金

入力:

```text
Arbitrumから500 USDC入金
```

検証:

- chain IDがArbitrum One
- tokenがNative USDC
- bridge addressが署名済みallowlistと一致
- bytecode hashが期待値と一致
- contractがpausedでない
- minimum以上
- Permit domain／spender／value／deadlineが一致

Permit後、relayerが`batchedDepositWithPermit`を送れる。ただし「ガススポンサー」は製品側の運用機能であり、Hyperliquidが保証するものではない。

入金完了はArbitrum tx successだけでなく、HyperCore creditまで確認する。

---

## 3.7 Vault

Vaultは一つの一般名で表示しても、実装を分離する。

### HLP

- protocol vault
- lock status
- available withdrawal time
- TVL
- current positions
- historical PnL／drawdown
- withdrawal slippage risk

### HyperCore User Vault

- leader
- profit share
- age
- TVL
- open positions
- depositor lock
- withdrawal impact

### HyperEVM／外部Vault

次をすべて確認できる場合だけ。

- exact chain ID
- contract address
- bytecode hash
- proxy implementation
- admin／upgradeability
- audit report
- oracle
- deposit asset
- allowance target
- withdraw function
- emergency pause
- known exploit status

未確認ならread-only。

---

## 3.8 複合操作

入力:

```text
HYPEを全部売って、300 USDCをHLPに入れ、残りを自分のArbitrumへ出金
```

CompilerはAction Graphへ変換する。

```text
S1 SPOT_SELL HYPE amount=SAFE_ALL
S2 HLP_DEPOSIT amount=300 USDC dependsOn=S1
S3 WITHDRAW_ARBITRUM amount=S1.actualOutput-S2.actualAmount-fees-reserve
   dependsOn=S1,S2
```

表示:

```text
3段階の複合操作（原子的ではありません）

1. HYPEをSpotで売却
   最低受取: 948.50 USDC
2. HLPへ300 USDC
   出金可能時刻: runtime計算
3. 残りをArbitrumへ出金
   推定: 647.50 USDC - withdrawal fee

途中失敗時は、完了済み処理を自動で逆取引しません。

[3つの操作をまとめて実行]
```

1回のユーザー承認は、複数stepの許可であって、チェーン上の原子性ではない。

---

## 4. システム構成

```text
┌──────────────── Android App ────────────────┐
│ Chat UI / Execution Card / Manual Escape    │
│ Local Policy Cache / Keystore Auth Key       │
│ Address Book / Device Share or Wrapped Key   │
└───────────────────┬──────────────────────────┘
                    │ TLS + certificate pin policy
                    ▼
┌──────────────── Backend Control Plane ───────┐
│ Auth / Device Registry / Policy API           │
│ Transaction Intent Parser / Support Gateway   │
│ Deterministic Compiler                        │
│ Execution Capsule Service                     │
│ Risk & Policy Engine                          │
│ Saga Orchestrator / Reconciler                │
│ Metadata & Contract Registry                  │
│ Audit Event Store                             │
└──────┬─────────────────┬─────────────────────┘
       │                 │
       ▼                 ▼
 Trade Signer        Root Signer / Wallet Adapter
(agent L1 actions)   (user-signed actions / EVM)
       │                 │
       └────────┬────────┘
                ▼
 Hyperliquid API / HyperCore / Arbitrum / HyperEVM
```

### Trust boundary

- LLM outputはuntrusted
- 取引Intent ParserはOpenAI endpointへ接続しない
- 任意の非取引Support Gatewayでも、mobile appはOpenAIへ直接接続しない。AI provider credentialはbackend secret managerだけに置く
- Support Gatewayは固定入力Schema、user／device auth、nonce、replay防止、rate／cost budgetを強制し、取引文・宛先・金額・asset／network・quote・payloadを拒否する
- Android UI inputも改変可能性を考慮
- Backend compilerだけが実行payloadを作る
- SignerはCapsule hashとallowlistを独立検証
- Browser／external contentはexecution contextへ入れない
- observability systemへ秘密を送らない

---

## 5. 自然言語処理とOpenAI境界

### 5.1 独立ウォレットの取引Intent Parserへ渡してよい入力

- ユーザーの操作文
- 端末内の登録済みalias候補
- 許可されたasset／networkの識別子
- UI上の選択肢
- ユーザー設定の単位・言語

これらは取引処理面の中だけで扱い、OpenAIサービスへ送らない。Parserは端末内の決定論処理を第一候補とし、必要時もOpenAIから分離された独立運用の非OpenAIコンポーネントだけを候補にする。

### 5.2 OpenAIを使う任意の非取引サポートへ渡してよい入力

- 固定用語ID
- 固定安全トピックID
- 固定エラーコード
- `ja-JP`等のlocale
- 取引内容をエンコードしない短期限の不透明なread-only reference ID

取引文、recipient、amount、asset／network、order、approval、transaction、quote、payload、signatureを受け付けない。

### 5.3 いかなるAI／Parserにも渡さないもの

- seed phrase
- private key／MPC share
- raw signature
- exact signer secret
- API key
- 完全なAddress Book
- recovery material
- contract admin key
- unredacted audit log
- external Web page contentと同じprompt内の実行権限

### 5.4 取引Parser output

取引Parserは厳格な`ActionPlanDraft` Schemaに従う。出力は次の状態から始まる。

```text
UNTRUSTED_DRAFT
```

決定論Compilerを通過して初めて:

```text
COMPILED_PLAN
```

になる。OpenAI-facing support outputから`ActionPlanDraft`または`COMPILED_PLAN`を作成してはならない。

### 5.5 禁止されるAI／Parserツール

```text
sign
broadcast
place_order
withdraw
transfer
approve_agent
approve_allowance
change_policy
export_key
resolve_arbitrary_address
resolve_contract_from_web
```

---

## 6. Execution Capsule

Capsuleには最低限次を含む。

```text
version
environment
userId
account
accountMode
deviceId
sessionId
planId
step graph
source state snapshot
asset metadata versions
contract allowlist versions
amounts
min outputs
max fees
max slippage
destinations
deadlines
failure policies
policy version
UI rendering digest
nonce strategy
idempotency keys
risk tier
required auth
```

### Canonicalization

- RFC 8785 JCS相当のcanonical JSON
- 数値は科学表記を禁止し、Decimal string
- アドレスはcanonical lowercase保存＋checksum表示
- fieldの省略と`null`を区別
- domain separator:
  `ONE_INTENT_EXECUTION_CAPSULE_V1`
- hash:
  `SHA-256(domain || 0x00 || canonical_json)`

### UI digest

`displayHash`だけでは人間が何を見たか証明できない。そこでsemantic／renderを分離し、さらにauthorization presentation evidenceを持つ。

1. `semanticHash` — 実行意味のcanonical data
2. `renderReceiptHash` — locale、formatted values、button label、warning IDsを含む表示receipt

署名の基準は`semanticHash`。監査証跡として`renderReceiptHash`を保存する。R4およびstanding例外を満たさないR3はcanonical `promptText`、challenge、attested confirmation response、または外部Trusted Display evidenceも要求する。R3 standing例外はregistration evidence、cooling、hard cap、per-use auth、device／app evidenceをEnvelopeへ束縛する。

### Authorization Envelope

実行許可は`semanticHash`だけでは成立しない。`schemas/authorization-envelope.schema.json`に従い、semantic、render、state、trusted promptの各hash、fresh challenge、device、presentation mode、one-time-useを一つに束縛する。Existing Wallet／hardware walletではその表示能力のevidenceも記録する。

`ONE_INTENT_HASH_PROFILE_V1`のtest vectorは`tools/update_example_hashes.py`で再計算し、CI不一致をrelease failureにする。

---

## 7. 認証階層

| Risk Tier | 例 | 認証 |
|---|---|---|
| R0 | read-only | なし |
| R1 | 許可範囲内のPerp／Spot | 有効な短時間セッション＋具体的ボタン |
| R2 | 既知Vault、同一userへの公式Bridge入金、cancel-all等 | 具体的ボタン＋per-use認証または厳格なpolicy。独立状態証拠 |
| R3 | 事前登録済み宛先への上限内送金／出金 | 原則protected／external display。事前R4 ceremony＋cooling＋hard cap＋standing authorization＋auth-per-useを全て満たす場合だけapp内限定経路可 |
| R4 | 新規宛先、高額／全額、recovery、key／policy変更、agent／builder承認 | external／hardware displayまたは事前登録ceremony＋cooldown＋追加factor |
| R5 | contract／Bridge／Vault allowlist追加、Mainnet全体解放 | 管理者二者承認＋監査＋release evidence |

セッション承認は、root actionを無制限に許可しない。高額・新規宛先・policy変更は毎回認証。

---

## 8. 鍵・署名

## 8.1 Trade Agent

用途候補:

- order
- cancel
- modify
- scheduleCancel
- leverage/margin系L1 action
- 対象アカウントで許可された他L1 action

重要: Hyperliquid側のAPI Wallet承認はアプリの細粒度ポリシーを強制しない。さらにagent keyが漏れればproduct Signer Serviceを迂回できる。よって鍵保護、資産隔離、characterization、監視に加え、Signer利用時は以下を行う。

- action type allowlist
- asset allowlist
- max notional
- max leverage
- account address binding
- environment binding
- Capsule hash binding
- nonce coordinator
- no arbitrary payload endpoint
- out-of-band agent action monitoring
- bounded account/subaccount exposure
- rapid revoke/replace

## 8.2 Root signer

対象:

- `usdSend`
- `spotSend`
- `withdraw3`
- `usdClassTransfer`
- `sendAsset`
- `approveAgent`
- EVM Permit／transaction
- recovery／key management

Root signerは汎用`signTypedData`や`signTransaction` APIを外部へ公開しない。操作種別ごとにtyped builderを持つ。

## 8.3 鍵方式

### Testnet基準

- 既存wallet adapter
- ユーザーがtyped dataを確認・署名
- 実装ロジックの正確性を先に検証

### Managed Self-Custody候補

- 監査済み2-of-3 threshold ECDSA
- device share
- policy share
- independent recovery share

採用条件:

- secp256k1 ECDSA互換
- deterministic low-s
- key refresh
- share backup／rotation
- disaster recovery
- service exit
- mobile SDK security audit
- no vendor unilateral signing
- export／migration path
- Japanese legal opinion

### Android Keystore

- P-256 device auth key
- AES-GCM wrapping key
- auth-per-use key for R3/R4。R3 app内例外は事前登録evidence＋cooling＋hard capを追加
- time-bound key for R1 session
- StrongBox利用可能性をruntime確認
- Protected Confirmation capabilityをruntime／実機確認
- BiometricPromptをTrusted Displayと呼ばない
- key invalidationを通常障害として扱う
- backup除外

---

## 9. Hyperliquid Adapter

## 9.1 数値

- 内部計算はDecimalまたは整数最小単位
- IEEE-754 floatを資産計算のsource of truthにしない
- wire formatは公式SDKとgolden testで照合
- tick／lot／sz decimalsをruntime metadataから取得
- 末尾ゼロ・field order・address casingの署名testを固定

## 9.2 Perp

- GTC、IOC、ALO
- trigger TP／SL
- entry-fill連動TP／SLはactual weighted fillから許可済みformulaで導出し、placement deadlineとfailure recoveryを束縛
- reduceOnly
- batch order／cancel
- cloid
- stale mark／oracle check
- open interest cap rejection handling
- liquidation risk snapshot
- scheduleCancelを限定的なdead-man switchに使用
- scheduleCancelはポジションを閉じないことをUIに明示

## 9.3 Spot

- metadata dynamic load
- `10000 + index`等の内部asset mappingをAdapterに隔離
- UI symbolとcanonical token IDを分離
- quote token verification
- minimum received
- token deployer／freeze risk metadataを可能な範囲で表示

## 9.4 Account mode

- Standard
- Unified
- Portfolio Margin

初期値を固定せず、現在modeを取得してCompilerを切り替える。Portfolio Marginはpre-alpha等の状態変化を監視し、Feature Gateで制御する。

## 9.5 State Evidence

- official APIを唯一の権威にしない
- R2以上は独立二系統またはself-run non-validating nodeを使用
- source ID、provider、cache、block/time、digest、independence classを記録
- CompilerとSignerはcritical fieldを別経路で検査
- divergence、stale、unknown independenceはfail closed
- official Foundation node等もsole authoritative sourceとみなさない

## 9.6 Nonce

- signer単位
- atomic allocator
- clock skew guard
- allowed timestamp window check
- top nonce behaviorをテスト
- signerごとにqueue分離
- deregistered agent addressを再利用しない
- signed payloadを永続キューに長期保存しない

---

## 10. Bridge Adapter

## 10.1 Official Arbitrum Bridge2

実行時検証:

```text
chainId
bridge address
bridge bytecode hash
USDC address
paused state
minimum deposit
withdraw fee
permit domain separator
deadline
spender
amount
destination
```

### Deposit state machine

```text
DRAFT
PERMIT_AUTHORIZED
ARBITRUM_SUBMITTED
ARBITRUM_CONFIRMED
DEPOSIT_EVENT_OBSERVED
HYPERCORE_CREDITED
COMPLETE
```

`ARBITRUM_CONFIRMED`を完了扱いしない。

### Withdrawal state machine

```text
DRAFT
USER_SIGNED
HYPERCORE_ACCEPTED
BALANCE_DEBITED
VALIDATOR_REQUEST_OBSERVED
ARBITRUM_PENDING
ARBITRUM_FINALIZED
DESTINATION_CREDITED
COMPLETE
```

## 10.2 External Bridge

初期Mainnetでは無効。公開条件:

- legal review
- security audit
- exact route allowlist
- contract upgrade monitoring
- token mapping
- simulation
- minimum output
- MEV/slippage model
- support ownership
- incident kill switch

「任意のBridge AggregatorへAIが接続」は禁止。

---

## 11. Vault Adapter

### HLP／HyperCore

- vault address allowlist
- deposit／withdraw capability
- lock calculation
- owner/protocol classification
- profit share
- TVL
- open positions
- withdrawal effect
- latest metadata timestamp

### HyperEVM

- arbitrary call禁止
- ABI allowlist
- selector allowlist
- exact calldata builder
- allowance cap
- revoke allowance
- proxy implementation monitor
- storage／admin change monitor
- static call simulation
- fork test
- chain confirmation policy

---

## 12. Saga Orchestration

各step:

```text
PENDING
READY
AUTHORIZING
SIGNED
SUBMITTED
OBSERVED
CONFIRMED
COMPLETE
FAILED_RETRYABLE
FAILED_FINAL
UNKNOWN
MANUAL_REVIEW
```

全体:

```text
DRAFT
COMPILED
SIMULATED
USER_AUTHORIZED
EXECUTING
PARTIAL
COMPLETE
FAILED
RECOVERY_REQUIRED
CANCELED_BEFORE_EXECUTION
```

### Failure policy

- `STOP`: 失敗後、後続を実行しない
- `CONTINUE_SAFE`: 独立したread-only等だけ継続
- `REPLAN_REQUIRES_USER`: 新条件を提示し再承認
- `MANUAL_RECOVERY`: 自動処理を止める

自動compensationは、資産移動の単純な逆操作だけに限定。市場取引、Vault deposit、Bridgeは勝手に逆転させない。

---

## 13. 冪等性・再試行

### Order

- deterministic unique `cloid`
- `planId + stepId + attemptGeneration`
- timeout時はorder status照会
- 同一cloidで結果確定前に新規注文しない

### User-signed action

- nonceを唯一化
- HTTP timeout後に残高／history／destinationを照合
- 署名を新nonceで再生成する前にmanual or deterministic proof
- stale signed actionの保存禁止

### EVM

- tx hash追跡
- replacement tx policy
- nonce manager
- chain reorg confirmations
- receipt＋balance delta
- Permit replay／deadline

---

## 14. セキュリティ

### 主要脅威

- prompt injection
- model hallucination
- address poisoning
- clipboard hijack
- overlay／screen control
- malware／root
- API Wallet theft
- root key share theft
- backend compromise
- signer policy bypass
- supply-chain compromise
- contract upgrade
- bridge pause／attack
- malicious vault
- nonce replay
- duplicate execution
- stale state
- insider abuse
- recovery takeover
- support impersonation

### 必須対策

- LLMとSignerのネットワーク分離
- no arbitrary signing endpoint
- canonical Capsule
- button label binding
- address full-view gesture
- QR checksum／chain display
- new destination quarantine
- per-action limits
- audit event hash chain
- production admin MFA＋hardware key
- two-person approval
- secret scanning
- dependency pinning＋SBOM
- reproducible release evidence
- kill switch
- read-only degraded mode

---

## 15. プライバシー

- 取引文、recipient、amount、asset／network、quote、authorization、payload、signature materialをOpenAIサービスへ送らない
- OpenAIを使う任意の非取引Support Gatewayだけに`store:false`を適用
- `OPENAI_API_KEY`等のprovider credentialはserver-side secret managerのみ。mobile binary／remote config／client logへ含めない
- Android／iOSからprovider endpointへの直接通信は禁止し、first-party Support Gatewayで固定input schema、model、retention、budgetを強制
- Support GatewayはSigner／Control API write／broadcast／root action／Address Book／quote／Execution Capsule networkへ到達不能
- ZDR/MAMを評価
- 非取引support dataを短期間・仮名化
- raw addressは端末または自社の取引処理面だけで解決
- model promptへ取引文、address、amount、asset／network、seed/private key/raw signature禁止
- logsへ自由文、token、auth header、typed signature禁止
- user export／deletion
- retention table
- vendor DPA
- breach response

---

## 16. 日本向け公開

現時点では一般公開`NO_GO`。

必要な書面意見:

1. Perp注文伝達が金融商品取引業の媒介・取次・代理に当たるか
2. AIの分析・提案が投資助言に当たるか
3. Spot売買媒介が暗号資産交換業または仲介業に当たるか
4. USDC等の扱いが電子決済手段関連規制にどう該当するか
5. MPC／policy signerが他人資産の管理に当たるか
6. builder fee／subscription／affiliate収益の影響
7. AML/CFT、Travel Rule、制裁、本人確認
8. 未成年者・適合性・広告・リスク表示
9. 海外無登録業者への接続を日本向け提供するリスク
10. 個人利用、closed alpha、一般公開の境界

法律相談前にMainnet一般公開しない。

---

## 17. 緊急導線

AIが停止しても使える。

```text
全注文取消
ポジションをreduceOnlyで決済
API Wallet失効
root action署名停止
Bridge／Vault停止
安全ウォレットへ退避
read-only残高確認
recovery mode
```

「全ポジション決済」は市場流動性・slippageを伴うため、長押し＋具体表示。

---

## 18. 監視

- Hyperliquid docs diff
- SDK release／commit pin
- contract bytecode
- Bridge paused state
- API error distribution
- nonce rejection
- WS disconnect
- open-order divergence
- balance divergence
- model drift
- false intent rate
- unauthorized draft rate
- Android security status
- OpenAI policy changes
- FSA／law changes
- official X updates

重大変更時は該当Feature Gateを自動停止。

---

## 19. 検証段階

### Phase 0 — Static

- Schema validation
- OpenAPI lint
- signing golden vectors
- canonicalization vectors
- threat model
- legal issue list

### Phase 1 — Simulator

- mocked exchange
- fault injection
- duplicate／timeout
- model adversarial cases

### Phase 2A — HyperCore Testnet

- 対応するL1／user-signed action
- rejection／unknown／WS reconnect／nonce collision
- agent capability characterization
- faucet prerequisite記録

### Phase 2B — Bridge2 harness／Arbitrum fork

- Permit、contract state、deposit／withdraw state machine
- pinned bytecode／block

### Phase 2C — HyperEVM／Vault fork

- ABI／selector／allowance／proxy／reorg

### Phase 3A — Pixel 9a

Android固有の実機証拠を取得する。

### Phase 3B — iPhone

SwiftUI、Secure Enclave P-256、Keychain、App Attest、Face ID／Touch ID、Dynamic Type、VoiceOver、再install／migrationを実機検証する。App AttestをTrusted Displayと扱わない。

- biometric
- Protected Confirmation capability／promptText／challenge
- trusted-display fallback
- device credential
- key invalidation
- backup／restore
- app upgrade
- screen control risk
- offline／clock skew

### Phase 4 — External audit

- mobile
- backend
- signer
- cloud IAM
- cryptography
- contract adapters
- business logic

### Phase 5 — Personal small Mainnet

- hard cap
- allowlisted own destinations
- no external users
- incident rehearsal

### Phase 6 — Closed alpha

- written legal approval
- support／on-call
- monitoring
- user limits
- no unresolved high/critical findings

### Phase 7 — Public

全release gateを満たす場合のみ。

---

## 20. 受入基準

### One-tap UX

- 具体的な上限内注文は追加画面0
- 操作ボタン1回
- R1は同じ流れで1タップ。R4とstanding例外を満たさないR3はTrusted Displayを追加し、未対応時はNO_GO
- AIの提案は必ずユーザーが具体的ボタンを押す
- 価格条件変更は再承認

### Safety

- 任意payload署名不可
- UIとpayloadの差分で署名拒否
- new destination差替え拒否
- stale state拒否
- duplicate executionゼロ
- partial state明示
- root signer compromise単独で署名不可（採用方式に応じる）
- agent key bearer riskを口座上限で封じる
- independent state divergenceで署名拒否

### Reliability

- process restart後にSaga再構築
- WebSocket欠落をRESTで回復
- timeout後のblind retryゼロ
- audit eventから全操作を再現可能

---

## 21. 最終判断

この設計のブレイクスルーは、承認を消すことではない。

> **ユーザーが押す前に操作を完全にコンパイルし、見た内容・許可した内容・署名される内容を一つのExecution Capsuleへ固定すること。**

それにより、Perp、Spot、送金、出金、Bridge、Vault、複合操作を1つのIntentとして扱える。通常取引は原則1タップにできる。root actionまで1回のアプリ内認証で完結するのは、監査・復旧・法務ゲートを通過したManaged Self-Custody Modeに限る。Existing Wallet Modeでは外部walletの追加確認を隠さない。

ただし、Mainnet公開は設計書だけでは許可されない。実装、Testnet、Pixel 9a／iPhone実機、外部監査、法務意見、運用体制が揃うまで`NO_GO`である。

## 22. Google Play・配布ゲート

- Financial features declarationを正確に提出する
- cryptocurrency wallet／exchange、digital wallet、money transfer、financial advice等の該当性を確認する
- target countryの規制／ライセンス証拠を提出できる状態にする
- Play審査通過と日本法適法性を互いの代替にしない
- Hyperliquid公式を名乗らない
- gate未完なら`PUBLIC_MAINNET_WRITE=false`

## 23. 100%に関する最終表現

本仕様は、既知・合理的に予見できる失敗をfail-closedへ変換する。未知の脆弱性、市場損失、protocol／OS／法令変更を消すものではない。`100%安全`という製品表示は禁止する。

## 31. Cross-platform最終統合

### 31.1 Native shells

AndroidはKotlin／Compose、iOSはSwift／SwiftUI。domain、compiler、policy、canonical hash、state machine、display modelのみをshared pure coreとして共有する。

### 31.2 iOS security

- Secure Enclave P-256：Authorization Envelope署名
- Keychain ThisDeviceOnly：wrapped device share／registration state
- App Attest：正規app instanceのrisk evidence
- LocalAuthentication：鍵利用認証
- Hyperliquid root secp256k1：external walletまたは監査済みThreshold ECDSA

App Attest＋Face IDはTrusted Displayではない。Schema上も`IOS_APP_ATTESTED_AUTHENTICATED_UI`、`AUTHENTICATED_APP_UI_NOT_TRUSTED_DISPLAY`、`trustedDisplayClaim=false`を要求する。

### 31.3 iOS one-intent boundary

- R1：通常のPerp／Spotは1回
- R2：既知Vault等はpolicy内で都度認証
- R3：保存済み宛先、standing authorization、hard cap、cooling evidenceがある場合だけapp内認証を許容
- R4：新規宛先、高額／全額、鍵／recovery変更はexternal／hardware path

### 31.4 Store boundary

Google PlayとApp Storeは別release gate。iOS public distributionはorganization、license／permission、written legal opinion、App Review readiness、external auditまでOFF。

### 31.5 UI quality

`31_DESIGN_SYSTEM_PIXEL_SPEC.md`、`32_SCREEN_BY_SCREEN_UX_SPEC.md`、`design/PIXEL_QA_CHECKLIST.md`をnormativeとする。critical edge／baselineのvisual regression許容差は1 logical pixel、critical regionの意図しない差分は0%。

### 31.6 現在の判定

```text
DESIGN_GO
OFFLINE_PROTOTYPE_GO
CODEX_IMPLEMENTATION_GO
ANDROID_BUILD_NO_GO
IOS_BUILD_NO_GO
TESTNET_WRITE_NO_GO
PERSONAL_SMALL_MAINNET_NO_GO
CLOSED_ALPHA_NO_GO
PUBLIC_ANDROID_STORE_NO_GO
PUBLIC_IOS_APP_STORE_NO_GO
```

# 2026-07-29.1統合追加仕様

## A. 利用者が見る言葉

主要画面は `config/user-facing-terms.ja.json` の日本語を正本とする。期限なし先物、現物取引、別ネットワークへの資金移動、運用口座、予定価格と成立価格のずれ、ネットワーク手数料、取引倍率、清算価格を使う。技術語は詳細説明だけに残す。

音声入力は原文と読み取った内容を分けて表示する。先物文脈の「ペイパチャル」「生産価格」は「期限なし先物」「清算価格」の候補にできるが、変換したことを利用者へ示す。金額、資産、相手、network、方向を推測で補完しない。

## B. 清算価格

先物previewは最新のaccount state、mark price、注文サイズ、口座方式、手数料から決定論的に清算価格の目安を作り、距離と取得時刻を表示する。成立後は対象positionの最新`liquidationPx`へ更新する。null、stale、position不一致、cross marginで単一値が誤解を生む場合は、値を捏造せず実行停止または担保使用率表示へ切り替える。

## C. JPYC発行と受け取り

JPYC EX連携は、login／account link、発行・償還画面への導線、wallet address登録補助、status連携を対象にする。本人確認、追加認証、審査、申込みの最終受付、取引可否、発行／償還確定はJPYC EX側で行う。walletは戻り値を検証し、正式なnetwork／contract／amountの入金を確認してから完了表示する。

## D. JPYCしかない場合のネットワーク手数料

`FeeReadinessPlan`は次の5状態を持つ。

- `SUFFICIENT`: 手数料用残高が十分。何も交換しない。
- `LOW_SWAP_POSSIBLE`: swap開始分はあり、目標reserveとの差分だけ交換できる。
- `LOW_ZERO_SPONSOR_AVAILABLE`: 残高0だがallowlisted sponsorによる一時立替が可能。
- `MANUAL_REQUIRED`: 外部から手数料用資産を受け取る必要がある。
- `BLOCKED`: 正式資産、network、route、quote、liquidity、providerを検証できない。

通常のオンチェーンswap自体にもネットワーク手数料が必要である。native balance 0でsponsorがない場合、JPYC swapを無条件に試さず、正確な画面・ボタン手順を表示する。

自動準備は明示的opt-in、対象network／contract／route／sponsor allowlist、1回上限、月間上限、目標reserve、価格ずれ上限、expiry、revocationへ限定する。AIは補充量を決めない。

## E. 最初の一度だけ承認

一度の設定で無制限権限を渡さない。期限、資産、network、取引種類、取引倍率、1回／日／月上限、登録済み送金先、手数料準備上限をStanding Authorizationへ束縛する。新規送金先、高額／全額、鍵・権限変更、scope expansion、初回Mainnetは個別の強い確認を要求する。

## F. ChatGPT境界

ChatGPT App／MCPは、抽象化した照合済みread-only状態、固定用語説明、固定エラー説明、一般安全案内、中立的な「独立ウォレットを開く」案内だけを提供する。取引文、金額、送金先、asset／network、取引固有の下書き・ボタン手順・復旧手順、注文、送金、暗号資産移転、swap、出金、署名、broadcast、実行内容を持つdeep linkを公開しない。

自然言語での実行は独立ウォレット内で提供する。取引Intent Parserは端末内の決定論処理を第一候補とし、必要時もOpenAIから分離された独立運用の非OpenAIコンポーネントだけを候補にする。出力はDraftに留め、決定論Compiler／Policy、Authorization、Control API、Signer、Adapter、Reconcilerを通過した操作だけを実行候補にする。

## G. 自動化不能時

recoverable errorは独立ウォレット内の `ManualFallback` へ結び、止めた理由、資産の現在位置、現在画面、押すボタン名、操作、期待結果、安全確認、再試行、support codeを表示する。手順はapp version／OS／feature gateへ紐づく署名済みcatalogとし、自由生成モデルだけで生成しない。ChatGPT／OpenAI-facing contractへは公開しない。

## H. 検証

オフライン画面見本は6端末proxy×12画面×通常／大きな文字×明／暗＝288条件を検査する。10枚の安定画像、source/test/toolchain hash、追加Schema、example、copy dictionary、manual guidance、archive安全性、secret scan、local link、adversarial audit、manifest、checksumsは `tools/run_full_validation.py` で一括検証する。
