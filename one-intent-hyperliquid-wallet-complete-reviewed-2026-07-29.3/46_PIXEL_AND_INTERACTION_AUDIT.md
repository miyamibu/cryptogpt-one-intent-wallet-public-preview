# Pixel・Interaction敵対的監査

**版:** 2026-07-29.3  
**対象:** `prototype/index.html`  
**範囲:** browser logical-pixel proxy。native SwiftUI/Composeや物理mmの証明ではない。

## 1. 検査マトリクス

| 端末proxy | logical size | 目的 |
|---|---:|---|
| iPhone SE stress | 320×568 | 最小幅・小高さ・長い日本語の最悪条件 |
| iPhone small | 375×667 | 小型iPhone |
| iPhone Face ID | 390×844 | 基準iPhone |
| iPhone large | 430×932 | 大型iPhone |
| Android compact | 360×800 | 小型Android |
| Pixel 9a logical | 412×915 | P0 Android |

各端末で12 flow、通常/大きな文字、明/暗を検査する。

```text
6 × 12 × 2 × 2 = 288 conditions
```

## 2. 1mm目線で確認した項目

### 境界と重なり

- phone frame内へscreenが収まる
- header、simulation strip、permission rail、conversation、execution card、composerがscreen外へ出ない
- button同士の可視領域が1pxを超えて重ならない
- primary buttonが末尾でcomposerやsticky summaryに覆われない
- full addressが横へ抜けない
- text rangeが実際のclip境界外へ出ない

### 到達性

- 画面切替時のscrollTopは0
- contentが長い場合、固定表示は「下に続きがあります」
- 中間位置は「上下に続きがあります」
- 末尾は「ここが最後です」
- primary actionはreview contentの最後のblockに存在
- 末尾まで自然に到達し、enabled buttonの中央点をhit-testできる
- 検査のための`scrollIntoView()`で初期状態を汚染しない

### 文字

- source utteranceを大きな文字でも消さない
- 重要な数値・警告・ボタンで横/縦clipを検出
- WCAG text-spacing proxyを適用しても横clipしない
- full-width日本語glyphの光学的overhangと実clipを分離
- addressはmonospace＋break-all、それ以外は意味のある折返し

### 操作

- iOS 44pt相当、Android 48dp相当をlogical-pixel proxyで検査
- primaryは54px以上、大きな文字で58px以上
- keyboard modalityでfocus-visible outlineを検査
- reduced-motion時に意味が失われない
- warningは色だけに依存しない

### 色

- light/dark全288条件でtext/background contrast proxy
- muted、warning、danger、disabled、badge、buttonを対象
- forced-colors用border/fallbackを定義

## 3. 発見した具体的欠陥

1. 旧版の固定CTAが短い画面で明細を隠した。
2. CTA footer全体が明細viewportより高く、末尾へ行ってもbutton上端がsticky summaryに重なった。
3. source requestを大きな文字時に非表示にする案は、誤認確認の証拠を失った。
4. 画面切替後に前画面のscroll位置が残る検査レースがあった。
5. `scrollWidth`だけでは、日本語glyphの5px程度のoverhangを実clipと誤認した。
6. programmatic focusだけでは`:focus-visible`のkeyboard状態を検証できなかった。
7. 画面見本の外部sidebar見出しが不自然に分割される旧案があった。

## 4. 採用した修正

- CTAをscroll contentの最後へ移動
- CTA内の説明をbuttonより前へ置き、buttonを末尾へ固定
- sticky summaryとは別にscroll statusを設置
- renderとflow/theme/text切替で同期的にscroll reset
- 小高さcontainer queryで非本質copyを圧縮し、依頼原文は保持
- 320px幅ではrowsを1列化
- clipping検査をtext Range＋nearest clip boundaryへ変更
- keyboard modalityを実際のTab入力で起動してfocus test

## 5. 安定スクリーンショット

- `iphone-perp-before-confirmation.png`
- `iphone-perp-after-confirmation.png`
- `pixel9a-fee-dark.png`
- `iphone-large-withdraw.png`
- `pixel9a-manual.png`
- `iphone-limited-authorization.png`
- `android-tall-partial-dark.png`
- `iphone-jpyc-large.png`
- `iphone-se-composite-top.png`
- `android-compact-spot-large-dark.png`

各画像はreview用であり、native golden imageではない。

## 6. 物理1mmを保証しない理由

CSS pixel、iOS point、Android dp、物理mmは同一ではない。device pixel ratio、表示倍率、font renderer、safe area、OS accessibility settingで変わる。このパッケージが保証するのはlogical geometryの境界と到達性である。

物理端末での最終検査は、Pixel 9a、iPhone 12、小型iPhone、現行Face ID端末で、実際のOS font、VoiceOver/TalkBack、IME、rotation policy、screenshot diffを使って実施する。これがない限りnative buildはNO-GOである。
