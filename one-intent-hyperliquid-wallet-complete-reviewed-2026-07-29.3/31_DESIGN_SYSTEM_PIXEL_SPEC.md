# Design System and Pixel-Level Specification

## 1. 「1mm単位」の扱い

スマートフォンUIでは物理mmを直接レイアウト単位にしない。画面密度、表示ズーム、Dynamic Type、font scaleが異なるためである。

本仕様では、厳密さを次で担保する。

- iOS：pt
- Android：dp／sp
- golden screenshot：logical pixel
- critical edge／baselineの許容差：1 logical pixel
- critical regionのvisual diff：0%
- non-critical decoration：0.1%以下
- 実機でsafe area、notch、home indicator、gesture navigationを確認

## 2. 共通グリッド

- 基本単位：4
- 画面左右：16
- card padding：16
- card間：12
- section間：20
- labelとvalue：8
- divider：1 logical px
- critical button：高さ52以上
- emergency button：高さ56以上

値を一時的に12や14へ逃がして「なんとなく合う」にしない。例外はdesign tokenへ登録し、理由と画面を残す。

## 3. タップ領域

- iOS最小44×44pt
- Android最小48×48dp
- 高リスクボタンは幅100%、高さ52以上
- iconが24でもhit areaは最小値を守る
- 隣接する反対操作のhit area間に8以上
- 「全決済」と「全取消」を隣接させる場合は形状・文言・間隔を変える

## 4. Typography

- iOS body：17pt相当
- iOS custom fontの絶対下限：11pt。ただし金融critical fieldでは使わない
- Android body：16sp以上を原則
- 数値：tabular figures
- 金額と単位を別行へ勝手に分断しない
- 小数点・桁区切りはlocaleで変えるが、canonical valueは変えない
- full addressはmonospace、4〜8文字単位で視線ガイド
- Dynamic Type／font scale 200%でcritical fieldを省略しない

## 5. Execution Card

### 必須順序

1. 操作名
2. asset／market
3. direction／source→destination network
4. amount／maximum amount
5. destination／Vault
6. min output／max fee／slippage
7. non-atomic／lock／risk warning
8. concrete action button

### 禁止

- 「続ける」「送信」「OK」だけのボタン
- amountを薄い補助文字へ落とす
- addressを先頭4＋末尾4だけで高リスク承認
- buy／sellを色だけで区別
- feeを実行後に初めて表示
- current estimateとhard maximumの混同

## 6. 色とcontrast

色はブランドより意味を優先する。

- long／buy：text＋direction icon
- short／sell：text＋direction icon
- destructive：red相当＋明示文言
- warning：icon＋heading＋本文
- success：check icon＋確定時刻／evidence
- pending：spinnerだけでなく状態名

light／dark、high contrast、color filtersで判読を確認する。

## 7. Safe areas

### iOS

- status bar／camera cutout／Dynamic Islandを避ける
- bottom actionはhome indicator safe areaに埋めない
- keyboard表示時もaction cardのcritical fieldsをscroll可能にする
- landscapeでもfull addressとamountが重ならない

### Android

- status／navigation／IME insetsをconsumeまたは適切にpadding
- gesture navigationと3-button navigation両方
- edge-to-edge時にbuttonがsystem barと重ならない

## 8. Loading／error／partial

- skeletonの幅は実値の意味を誤認させない
- price未取得で0を表示しない
- timeoutをFAILEDへ直結しない
- PARTIALはamber等だけでなく「一部完了」と文字で表示
- current asset locationを必ず表示
- recovery actionは実行済みstepを再実行しない

## 9. Visual regression対象

- iPhone small viewport
- iPhone 12基準390×844＋recent Face ID viewport
- Pixel 9a viewport
- 200% text
- Japanese／English
- 42文字address alias
- max-length asset symbol
- 12桁金額＋小数
- dark mode
- keyboard open
- offline／stale state／partial failure

## 10. UI完了条件

- critical text clipping 0件
- critical overlap 0件
- tappable overlap 0件
- VoiceOver／TalkBack focus order違反0件
- action button labelがoperation＋asset＋amountを含む
- screenshot diff規定内
- 小型端末で横スクロールなし（full address componentの内部scrollは例外）
