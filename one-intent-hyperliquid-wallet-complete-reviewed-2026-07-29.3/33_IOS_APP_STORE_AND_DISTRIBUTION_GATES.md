# iOS App Store and Distribution Gates

## 現時点の判定

```text
XCODE_DEVELOPMENT: READY_AFTER_SOURCE_IMPLEMENTATION
REGISTERED_DEVICE_AD_HOC: NO_GO_UNTIL_SIGNED_BUILD
CLOSED_TESTFLIGHT: NO_GO_UNTIL_BUILD_SECURITY_LEGAL_REVIEW
PUBLIC_IOS_APP_STORE: NO_GO
```

## 公開App Storeの主な障壁

AppleのApp Review Guidelinesでは、暗号資産ウォレットは組織として登録されたデベロッパが提供する必要がある。暗号資産取引は、対象国・地域で適切なライセンスと認可を持つ取引所に限る。暗号資産先物等を扱うアプリには、提出主体に関するより厳しい要件がある。

したがって、次を満たすまで公開提出しない。

- Apple Developer Programのorganization enrollment
- 開発主体の法的entity確認
- 日本でのPerp／Spot／USDC／送金／MPCの書面法務意見
- Hyperliquid利用規約・ブランド利用・API利用の確認
- 地域別availability plan
- App Review guideline 3.1.5と3.2のmemo
- demo account／demo modeとreview notes
- privacy nutrition、accessibility、financial featuresの正確な申告
- external auditとpenetration test
- support、incident、asset recovery体制

## 配布ルート

### Xcode Development

- 開発端末を登録
- development certificate／profile
- 実機でのみSecure Enclave、App Attest、本物のFace IDを評価

### Ad Hoc

- 登録済み端末のみ
- distribution certificate／Ad Hoc profile
- 個人・限定実機試験に利用
- 一般公開手段として扱わない

### TestFlight

- closed alphaへ利用
- Mainnet資金は初期禁止
- tester consent、risk disclosure、support channel、kill switch必須
- external testing前にApp Reviewが関与し得ることを前提にする

### Public App Store

- 法務／license／organization／review strategyが揃うまでNO_GO
- 「非公式クライアントだから金融アプリではない」という主張に依存しない

## App Review packet

- app purposeと非公式表示
- account／custody mode説明
- signing model diagram
- demo flow
- all features and regions
- root action authorization説明
- no seed collection statement
- no automatic investment decision statement
- OpenAI boundary説明
- incident response contact
- legal memo reference
- security audit executive summary
- third-party SDK inventory／SBOM

## Rejectionを避けるための設計

- 未完成ボタン、placeholder、秘密のfeature flagを提出しない
- review時だけ機能を隠す挙動を作らない
- Hyperliquid公式を装わない
- trading resultsや利益を誤認表示しない
- demo modeを完全機能のように偽らない
- App Review notesにPerp、Spot、Vault、Bridge、AIの役割を具体記載
