# Multi-Perspective Review — 対立する視点の統合監査

## 総合結論

製品コンセプトは成立する。ただし、次の2つを同時に真と表示してはならない。

- 「全機能が常に1タップ」
- 「外部ウォレットでもroot actionを非カストディで安全に実行」

Existing Wallet Modeでは追加署名が発生し得る。Managed Self-Custody Modeならアプリ内体験を短くできるが、MPC、復旧、法務、運用の負担が増える。最終仕様はこのtrade-offを隠さない。

## 1. ユーザー視点

### 求めるもの

- 会話が短い
- 誰に、何を、いくら送るか一目で分かる
- 失敗時に資産の場所が分かる
- AIが落ちても決済・出金できる
- 毎回wallet popup地獄にならない

### 指摘

- 「1 Intent」は魅力的だが、複合操作の途中失敗が理解しにくい
- saved destinationの意味を知らないユーザーが多い
- Vault lockやBridge待ち時間はbutton付近に必要
- 送金／出金／Bridgeの用語差が専門的

### 修正

- operation cardにsource→destinationを明示
- expected confirmation countを事前表示
- partial timelineとasset locationを常時表示
- beginner wordingとadvanced detailを同居

## 2. デザイナー視点

### 求めるもの

- 画面を移動せずに確認できる
- hierarchyが明確
- warningを増やしすぎない
- platformらしい操作感

### 指摘

- warningを全部赤くすると、本当に危険な警告が埋もれる
- AndroidとiOSを完全同形にするとnative conventionを壊す
- address全表示は情報密度が高い
- chatとexecution cardが競合する

### 修正

- warningをblocking／material／informationalに分類
- shared tokens＋native components
- addressはfull表示可能、fingerprint／aliasを併記
- execution composerがactiveな間はchatを視覚的に後退

## 3. セキュリティ視点

### 求めるもの

- LLMに権限なし
- generic signerなし
- root／trade分離
- state quorum
- fail closed

### 指摘

- App Attestはtrusted displayではない
- API Walletはアプリ側上限をprotocolが強制しない
- device biometricsは盗難・coercion・malwareを完全解決しない
- one-tap UXはnew destinationに不適切

### 修正

- iOS mode名にNOT_TRUSTED_DISPLAYを明示
- API Walletはbounded account＋revocation＋characterization
- R4とstanding例外を満たさないR3はstrong path
- standing authorizationにcooling periodとhard cap

## 4. 管理者／運用視点

### 求めるもの

- feature gate
- incident visibility
- account freeze／agent revoke
- audit trail
- rollback

### 指摘

- user-facing kill switchとadmin kill switchを混同している
- kill switchが同じ障害ドメインにあると役に立たない
- source registry変更が未実行planへ反映されない恐れ
- supportが秘密情報を要求する事故

### 修正

- admin console別系統
- out-of-band emergency gate
- registry version mismatchでcapsule失効
- verified support channelと「seedを聞かない」policy

## 5. 開発者視点

### 求めるもの

- shared logic
- testable contracts
- platform adapters
- reproducible builds

### 指摘

- Swift／Kotlin二重実装はdriftしやすい
- Rust一本化はsecurity API差を隠す
- official Hyperliquid SDKがPython基準でmobile parityが難しい
- visual specが実装へ落ちない可能性

### 修正

- pure shared coreだけ共有
- platform capabilityは明示型
- official Python SDKをgolden oracleにする
- screenshot matrixとCI gate

## 6. 法務／Store視点

### 求めるもの

- 適切なentity／license
- accurate disclosure
- region controls
- marketing claim control

### 指摘

- 「非カストディ」だけでは規制評価を回避できない
- PerpはApp Store guideline上も厳しい
- AI説明が投資助言へ近づく恐れ
- Store承認と合法性を混同しやすい

### 修正

- legal opinion gate
- iOS public distribution default OFF
- neutral execution assistant boundary
- region allowlistとstore/legal独立証拠

## 7. アクセシビリティ視点

### 指摘

- address／decimal／directionをscreen readerが誤読し得る
- 200% textでbutton labelが切れる
- hapticだけで成功を伝えるのは不可
- chartだけでriskを示すのは不可

### 修正

- semantic accessibility labels
- multiline critical buttons
- text＋icon＋haptic
- riskを数値と文章で表示

## 8. SRE／障害対応視点

### 指摘

- WebSocket切断で状態漏れ
- timeout後のblind retry
- Bridge finalization遅延
- partial Sagaの再開競合
- nonce coordinator split-brain

### 修正

- REST reconciliation
- state=UNKNOWN
- destination creditまで追跡
- lease／fencing token
- per-signer atomic nonce service

## 9. 「嫌な目線」

- button文言のassetとcardのassetが1文字違う
- warningとhome indicatorが4pt重なる
- 999.9999が1,000へ丸められて見える
- 日本語では収まるが英語でbuttonがclip
- address末尾だけ太字で先頭が変わっている
- offline badgeがdark modeで見えない
- Face ID cancel後にbuttonが有効のまま
- app復帰時に古いcapsuleが画面に残る
- keyboardが開いたままemergency buttonを誤tap
- partial successなのにpush通知が「完了」

全項目を `design/PIXEL_QA_CHECKLIST.md`、`tests/visual-regression-cases.yaml`、`24_KNOWN_LOOPHOLE_REGISTER.md`へ変換する。

## 最終的な対立解決

| 対立 | 決定 |
|---|---|
| 最短UX vs 新規宛先安全 | saved destinationは短く、新規はstrong ceremony |
| 共通UI vs native UI | tokens／domainは共通、controls／securityはnative |
| self-custody vs recovery | 2 modeを分け、Managedは監査完了までOFF |
| AI便利 vs deterministic | AIはdraftのみ、実行はpure compiler |
| 全機能初期搭載 vs release risk | code pathは用意、Mainnet gateは個別OFF |
| 見た目の簡潔さ vs disclosure | progressive disclosure。ただしcritical fieldは常時表示 |
