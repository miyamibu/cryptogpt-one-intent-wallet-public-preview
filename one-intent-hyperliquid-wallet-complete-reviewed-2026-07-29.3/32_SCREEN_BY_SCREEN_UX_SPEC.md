# Screen-by-Screen UX Specification

## S01 Onboarding

表示：

- 非公式Hyperliquidクライアント
- 2つのwallet mode
- AIは注文を決定せず、文を下書きへ変換するだけ
- Mainnet／Testnet表示

分岐：

- Existing Wallet Mode
- Managed Self-Custody Mode（feature gate OFFなら選択不可＋理由）

失敗状態：wallet接続失敗、unsupported network、App Attest unavailable、integrity risk。

## S02 Security Setup

- passkey／account login
- biometrics availability
- device registration
- address book recovery policy
- session duration
- transaction limits

iOSではApp Attest unavailableをsilent passしない。既定は`READ_ONLY`へ制限し、外部wallet等の別保証経路を使う場合だけsigned policyで個別writeを許可する。R1を「閲覧」と呼ばない。

## S03 Chat + Execution Composer

上部：account、environment、connection state。  
中央：conversation。  
下部：inputとinline execution card。

具体的注文では入力中にcardを作る。曖昧項目はchat往復よりinline chipsを優先する。ただし新規宛先、contract、chainはAIに推測させない。

## S04 Perp Order

必須：market、long/short、notional、leverage、order type、max slippage、reduce-only、TP/SL、estimated liquidation、fee estimate。

button例：`BTCを500 USDC、3倍でロング`。

## S05 Spot Order

必須：pair、buy/sell、input amount、minimum output、price impact、fee、safe-all maximum。

全売却ではreserved fee／dust／open order分を考慮したSAFE_ALLを使う。

## S06 Internal Transfer

`HyperCore内送金`と`Arbitrum出金`を同じ単語「送る」で表示しない。

必須：source domain、destination domain、asset、amount、full address、address source、registration age。

## S07 Arbitrum Withdrawal

- Hyperliquid → Arbitrum
- exact／maximum amount
- destination
- fee
- estimated stages
- request acceptedとArbitrum creditedを別表示

## S08 Bridge Deposit

- Arbitrum native USDC
- official Bridge2／external bridge区分
- minimum amount
- permit／relayer
- owner／credited account
- gas sponsor
- source chain balance

## S09 Vault

- protocol／user／external classification
- TVL、PnL、max DD、positions、profit share、lock duration
- unlock timestamp
- contract／adapter version
- APYだけを強調しない

## S10 Composite Action

step graphを上から順に表示。

```text
1 HYPEを売却
2 HLPへ300 USDC
3 残りをArbitrumへ出金
```

- non-atomic banner
- per-step max／min
- expected confirmations
- root actionのタイミング
- partial recovery plan

## S11 Execution Timeline

状態：AUTHORIZED、SIGNING、SUBMITTED、RESTING、PARTIALLY_FILLED、FILLED、PENDING_BRIDGE、CREDITED、PARTIAL、UNKNOWN、RECOVERY_REQUIRED。

HTTP 200だけでCOMPLETEにしない。

## S12 Emergency

常時到達可能：

- 全注文取消
- reduce-only全決済
- API Wallet停止
- 新規write停止
- 安全先へ退避（policyで許可された場合）

AIを経由しない。操作ごとに影響を具体表示する。

## S13 Address Book

- alias
- full address
- chain
- verified source
- fingerprint
- created at
- cooling status
- last used
- change history

編集後は未実行Capsuleを無効化する。

## S14 Settings／Limits

- per order
- daily transfer
- daily loss
- allowed assets
- allowed chains
- session time
- biometric policy
- privacy／AI data sharing

上限引上げは引下げより強い認証を要求する。

## S15 Admin Console（別アプリ／別権限）

ユーザーアプリに管理者feature gate UIを埋め込まない。管理者consoleはhardware MFA、RBAC、two-person approval、immutable auditを要求する。

## S16 External Wallet Handoff

- expected wallet、account、chain、operation count、戻り先を表示
- handoff request IDとCapsule hashを束縛
- wrong account／wrong chain／payload substitution／callback replayを拒否
- root actionでは追加確認回数を事前表示し、One-IntentをOne-Signatureと偽らない

## S17 Devices／Recovery

- 登録端末、last seen、attestation state、standing authorizationを表示
- 旧端末失効、new device cooling、agent rotation、recovery progress
- iPhone restore／reinstallとAndroid D2Dを通常loginと同じ扱いにしない

## S18 Activity／Receipt

- plan ID、operation、chain、amount、fee、cloid／tx／withdrawal identifier
- request accepted、filled、creditedを分離
- `PARTIAL`／`UNKNOWN`／`RECOVERY_REQUIRED`をfilterで隠さない
- support exportはsecret allowlistを通す

## S19 Blocked／Degraded Mode

- source divergence、stale state、attestation unavailable、feature gate、region blockを具体表示
- 「不明なエラー」で一括しない
- read-only、cancel、emergency、support evidenceの利用可否を個別表示

## S20 Region／Legal／Risk Disclosure

- 提供地域、非公式表示、Perp／Vault／Bridgeの主要risk、AIの限定役割
- acceptance version、privacy controls、support／incident contact
- region change／policy expiry時にwrite gateを再評価


## 2026-07-29.1追加画面

### S-14 期限なし先物の確認

表示順:

1. 読み取った内容
2. 取引種類「期限なし先物」
3. 元手と取引の大きさ
4. 取引倍率
5. 予想成立価格
6. 清算価格の目安
7. 清算までの距離
8. 損切り価格の目安
9. 予定価格と成立価格のずれ
10. 取引手数料
11. 取得時刻と口座方式
12. 実行ボタン

清算価格が取得不能なら値を隠すのではなく、「正確に確認できないため実行を止めました」、理由、口座情報更新、公式読み取り画面の手順を表示する。

### S-15 JPYCを受け取る

- 日本円金額
- JPYC受取見込み
- 受取ネットワーク
- 受取アドレス
- JPYC EXで本人確認・最終申込みを行う説明
- 「JPYC EXで発行手続きを始める」
- 戻った後の「入金を確認」
- 正式コントラクト／ネットワーク不一致時の停止

### S-16 ネットワーク手数料を準備

- JPYC残高
- 予定送金額
- 手数料用資産と現在残高
- 必要手数料と目標残高
- 残高十分／少額交換／代理支払い／手動入金／停止の状態
- JPYCから使う最大額
- 月間上限の残り
- 予定価格と成立価格のずれ
- provider／経路の説明
- 手数料準備と元操作の順番

残高が十分なら「準備不要」と表示し、交換ボタンを出さない。残高0で代理支払いが使えない場合は、通常交換を提案せずS-19へ移る。

### S-17 最初の一度だけ設定

- 有効期限
- 1回／1日／1か月上限
- 対象資産・ネットワーク
- 最大取引倍率
- 登録済み送金先
- 自動手数料準備の月間上限
- いつ補充するか
- 毎回確認が必要な操作
- 一時停止／失効方法

画面見出し近くに「無制限の権限ではありません」を表示する。

### S-18 JPYC発行／送金の途中状態

JPYC EX手続き中、入金待ち、手数料準備中、送金受付済み、到着待ちを別状態で表示し、受付済みを完了にしない。

### S-19 自動でできない場合

1手順ごとに以下をカード表示する。

- 手順番号
- 現在画面
- 押すボタンの正確な名前
- 操作
- 期待結果
- 安全確認

下部に再試行ボタンとsupport codeを置く。手順はスクロール可能で、実行ボタンは固定領域へ置く。

### S-20 ChatGPT連携状態

読み取り専用であることを表示する。

- 共有している残高範囲
- 共有している履歴範囲
- 最終アクセス
- 接続解除
- 「ChatGPTから注文・送金はできません」
- 独立ウォレット内で操作する説明
