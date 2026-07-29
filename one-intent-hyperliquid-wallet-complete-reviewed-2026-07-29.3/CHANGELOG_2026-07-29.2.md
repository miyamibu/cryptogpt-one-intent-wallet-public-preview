# Changelog — 2026-07-29.2

## 位置付け

2026-07-29.1の基準版を保持したうえで、画面到達性の修正と配布版メタデータの整合を反映した修正版。

## 今回の修正

- 短い画面高でsticky要約が主要CTAを覆わないよう、要約表示を通常フローへ戻した。
- 短い画面高のカード／タイムラインに上部余白を追加し、初期表示の操作要素が切れないようにした。
- 340px以下かつ大きな文字の行で、値表示が横方向にはみ出さないよう文字間隔を調整した。
- `config/build-metadata.json`を`2026-07-29.2`へ更新し、現行ドキュメント、回帰条件、証跡識別子を整合させた。
- `.1`の基準資料・履歴は上書きせず、`.2`の変更履歴を追加した。
- Android Gradle Wrapper 9.3.1、Compose theme、unsigned debug build、Pixel 9a local UI proofを追加した。
- iOS `OfflineWalletApp` Xcode target、Info.plist、SwiftUI entrypoint、iPhoneOS／Simulator unsigned compileを追加した。
- Team `8R3B5675ZJ` のiOS Development signed device build、iPhone 12へのインストール・起動、Appium/WDA画面取得、無効CTAタップ不変、上下ジェスチャのlocal proofを追加した。証跡画像SHA-256は `8a1e808d66fc9580e74c5ae90d4f34549986f87e05f3b4b0e3269fdbae7444ea`。

## 検証

- 6 viewport × 12 flow × 2文字モード × 2themeの288条件をPASS。
- Pythonソース93件のcompile、Python unit 62件、Swift contract 5件、validator self-test 36 assertionsをPASS。
- Android unit 5件／unsigned debug build、Pixel 9aの起動・表示・tap・scrollをlocal-onlyでPASS。iOS iPhone 12のsigned debug device proofはPASS。ただしarchive・IPA・配布署名・完全な実機matrixは未検証。
- START_HERE独立6条件、readiness、archive safety、security hygiene、link/markup、adversarial auditをPASS。
- 本成果物はオフライン設計／ローカルsandboxの検証物であり、native build、実機、Testnet/Mainnet、production、Store、法務、独立監査の完了を意味しない。
