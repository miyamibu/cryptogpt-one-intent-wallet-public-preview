# Accessibility and Localization Test Matrix

| Case | iOS | Android | Pass condition |
|---|---|---|---|
| Screen reader order | VoiceOver | TalkBack | visual orderと一致 |
| Text 200% | Dynamic Type | font scale | critical field欠落0 |
| Bold text | Accessibility setting | bold/high contrast | overlap 0 |
| Reduce motion | Reduce Motion | animator scale／setting | meaning消失0 |
| Color filters | iOS filters | color correction | direction識別可能 |
| Switch control | Switch Control | Switch Access | execution可能、誤focusなし |
| Japanese | ja-JP | ja-JP | 金額・単位自然 |
| English | en-US | en-US | button clipなし |
| RTL smoke | Arabic test | Arabic test | address／number順序破損なし |
| Long alias | 42+ chars | 42+ chars | full detailsへ到達可能 |
| Decimal speech | VoiceOver | TalkBack | 0.001を正確に読む |

## Accessibility labels

悪い例：`500 USDC 3x BTC`  
良い例：`BTC perpetual、ロング、注文額500 USDC、レバレッジ3倍`。

Addressは一文字ずつ読ませるmodeと、fingerprintを読み上げるmodeを提供する。
