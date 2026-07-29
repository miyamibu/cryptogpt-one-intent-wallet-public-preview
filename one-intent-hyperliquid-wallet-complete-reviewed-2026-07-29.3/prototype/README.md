# Offline Prototype

`prototype/index.html`をブラウザで直接開く。外部script、API、wallet、network request、署名、送金、注文は使用しない。

## 用途

- iPhone／Android logical viewportのlayout review
- 期限なし先物、現物、送金、別network移動、運用口座、JPYC、手数料準備、限定承認、複合操作、部分成功、手動復旧の情報設計
- 音声原文と正規化後理解、清算価格、最低受取、fee quoteの確認
- 大きな文字、明／暗、focus、text spacing、最小tap target、scroll末尾の検査
- 6 viewport×12 flow×2文字モード×2theme＝288条件の自動検査

## 非用途

- 署名、鍵生成、Testnet／Mainnet
- App Attest／Protected Confirmation／MPCの実装証明
- JPYC EX、Hyperliquid、価格、残高、手数料のlive lookup
- SwiftUI／Compose、実機safe area、IME、VoiceOver／TalkBack、物理mmのpixel-perfect保証

## Screenshot evidence

- `screenshots/iphone-perp-before-confirmation.png`
- `screenshots/iphone-perp-after-confirmation.png`
- `screenshots/pixel9a-fee-dark.png`
- `screenshots/iphone-large-withdraw.png`
- `screenshots/pixel9a-manual.png`
- `screenshots/iphone-limited-authorization.png`
- `screenshots/android-tall-partial-dark.png`
- `screenshots/iphone-jpyc-large.png`
- `screenshots/iphone-se-composite-top.png`
- `screenshots/android-compact-spot-large-dark.png`

証拠のsource/test/toolchain hashとlimitationsは`../tests/prototype-visual-evidence.json`に記録する。prototypeのPASSをnative mobileのPASSへ流用しない。
