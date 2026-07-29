# Pixel / Point QA Checklist — 嫌な目線

## Alignment

- [ ] card左右端が全画面で同じgridに揃う
- [ ] heading baselineが1 logical px以上ずれない
- [ ] amountの小数点位置がrow間で揃う
- [ ] iconのoptical centerがtext centerと一致する
- [ ] dividerがhalf-pixelでぼやけない
- [ ] corner radiusがnested cardで不自然に競合しない

## Overflow

- [ ] 日本語長文でbuttonが2行になっても高さが追従
- [ ] full addressがcard外へ出ない
- [ ] 12桁金額＋8桁小数がwarning iconと重ならない
- [ ] Dynamic Type 200%でfee／destinationが消えない
- [ ] keyboardでprimary actionがhome indicatorへ隠れない
- [ ] landscapeでheaderとstatus pillが衝突しない

## Interaction

- [ ] iOS 44pt、Android 48dpのhit target
- [ ] close iconとback gestureが競合しない
- [ ] loading中の二重tapが二重送信にならない
- [ ] disabled buttonの理由を読める
- [ ] destructive actionとordinary actionの間隔が8以上
- [ ] scroll中の誤tapを実行扱いしない

## State honesty

- [ ] `注文送信済み`と`約定済み`を分ける
- [ ] `出金要求済み`と`着金済み`を分ける
- [ ] stale priceをcurrent priceとして表示しない
- [ ] UNKNOWNをFAILEDへ勝手に変換しない
- [ ] PARTIALで緑の完了checkを出さない
- [ ] retryが同一idempotency keyを使う

## Platform

- [ ] iPhone camera cutout／Dynamic Island safe area
- [ ] iPhone home indicator safe area
- [ ] iPhone screen recording検出時の高リスク画面
- [ ] Pixel 9a gesture navigation／3-button navigation
- [ ] Android display size／font size最大
- [ ] dark mode／high contrast／reduce motion

## Accessibility

- [ ] VoiceOver／TalkBack focus order
- [ ] amountを一つの意味あるlabelとして読む
- [ ] `0.01 BTC`を不自然な文字列として読まない
- [ ] 色だけに依存しない
- [ ] timeout／warningがlive regionで過剰連呼しない
- [ ] QRにtext alternativeがある

## Visual regression

- [ ] baseline screenshotにversion／device／localeを記録
- [ ] critical regionsはpixel diff 0%
- [ ] intentional changeはdesign review IDを紐付け
- [ ] antialias差だけを安易に全無視しない
- [ ] screenshotに実秘密・実addressを使わない
