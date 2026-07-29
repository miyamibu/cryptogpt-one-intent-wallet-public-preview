# One-Tap UXフロー

## 原則

「承認画面を消す」のではなく、入力中にExecution Cardを完成させる。ここでいうOne-Tapは通常のR1取引を指す。Existing Wallet Modeのroot action、R4、standing例外を満たさないR3では、外部wallet／保護確認の追加操作を隠さない。1つのIntentと、1つの暗号署名は同義ではない。

## 意図分類

| 入力 | 分類 | 実行 |
|---|---|---|
| 「BTCどう？」 | QUESTION | なし |
| 「BTC買うなら？」 | ADVICE_REQUEST | なし |
| 「BTCを買って」 | AMBIGUOUS_ACTION | 金額chipを提示 |
| 「BTCを500 USDC、3倍でロング」 | EXPLICIT_ACTION | Card＋1ボタン |
| 「良さそうなら500 USDC買って」 | CONDITIONAL_DISCRETION | 条件を構造化し、ユーザー承認必須 |
| 「自動で儲かるようにやって」 | UNBOUNDED_AUTOMATION | 拒否／rule builderへ誘導 |

## 曖昧さ解消

会話の往復よりinline controlを優先する。

```text
金額: [100] [300] [500] [入力]
レバレッジ: [1x] [2x] [3x]
SL: [なし] [-1%] [-2%]
```

選択後、同じ画面でCardを完成。

## ボタン文言

- 動詞
- asset
- amount
- destination／direction
- 高リスク警告

例:

```text
[BTCを500 USDCロング]
[HYPEを最低948.50 USDCで売る]
[友人Aへ50 USDC送る]
[Arbitrumへ200 USDC出金]
[HLPへ300 USDC入金・4日ロック]
```

## 新規宛先

同一画面で:

1. full address表示
2. chain表示
3. address source表示
4. QR／manual／contactの由来
5. address poisoning警告
6. auth-per-use
7. cooldownまたはtest transfer選択

新規宛先を「保存しながら即全額送金」は禁止。

## 高額

ユーザー設定の`highRiskThreshold`以上:

- auth-per-use
- remaining balance
- % of total assets
- daily total
- no hidden toggle
- optional delayed execution

## ALL

UIで「全部」とだけ表示しない。

```text
利用可能な安全上限: 948.20 HYPE
保持: 0.03 HYPE（手数料／dust予備）
```

## Partial

```text
3操作中2件完了

✓ HYPE売却
✓ HLPへ300 USDC
! Arbitrum出金は未実行

現在地: HyperCoreに647.20 USDC
資産損失の兆候: なし
[出金だけ再確認]
```

## Accessibility

- TalkBackでCardの全項目を読み上げ
- Long addressの区切り読み上げ
- 色だけでbuy/sellを区別しない
- 最低48dp touch target
- Dynamic Type
- reduced motion
- locale-aware decimal
- warning severityをtext/iconで表示

## iPhone one-intent flow

通常取引：Execution Cardの具体ボタン→必要時Face ID→App Attest assertion＋Secure Enclave P-256 Authorization署名。これは内容のTrusted Displayではない。

保存済み自分宛出金：standing authorization、chain、hard cap、cooling evidenceが有効な場合だけ同じ場のFace IDで許可する。新規宛先、高額、全額はexternal／hardware confirmationへ送る。

## JPYCと手数料準備を含む会話フロー

### JPYC発行

`日本円から1万円分のJPYCを受け取りたい` → 金額、network、受取address → JPYC EXへ安全に移動 → JPYC EXで最終申込み → walletへ戻る → 正式contractの入金確認。

### JPYCだけで送金

`JPYCしかないけど3,000 JPYCを友人Aへ送って` → 手数料用残高を確認 → 十分なら準備なし → 少なければ必要最小限だけ交換 → 0ならallowlisted sponsorを検査 → 利用不能ならPolygon／POLの具体的入金手順 → 元の送金を再preview。

### 初回の限定設定

`最初の一回だけ承認して、あとは会話で進めたい` → 期限、資産、network、取引倍率、1回／月間上限、保存済み相手、手数料準備上限を表示 → 強い確認 → 範囲内だけ自動化。新規相手、高額／全額、鍵変更は毎回確認。
