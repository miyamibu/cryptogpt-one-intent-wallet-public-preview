# Google Play／App Store・配布・地域ゲート

## 結論

APKが動くことと、Google Playで配布できることは別である。本アプリは金融機能と暗号資産機能を持つため、Play審査・地域適格性を独立した`NO_GO`ゲートとする。

## Financial features declaration

少なくとも、実装内容に応じて次を検討・正確に申告する。

- Mobile payments and digital wallets
- Money transfer and wire services
- Cryptocurrency wallet
- Cryptocurrency exchange
- Financial advice
- Other

機能を「AIチャット」や「非カストディUI」と呼び替えて過少申告しない。

## Blockchain／crypto policy

- 対象地域の法令・ライセンス要件に適合する。
- 提供禁止地域へ公開しない。
- Googleから要求された規制・登録・提携等の資料を提出できる状態にする。
- certified service／regulated jurisdiction要件の当てはまりをPlay policy counselと確認する。
- Hyperliquidへの接続自体がPlay審査で受理されると推定しない。

## 日本向け

Google Play審査通過は、日本法上の登録不要・適法を意味しない。逆も同じである。

公開前に、次を別々に満たす。

1. 日本法の書面意見
2. 対象業務の登録・提携・非提供判断
3. Google Play Financial features declaration
4. Google Play crypto policy evidence
5. privacy／risk disclosure
6. region／age／sanctions policy
7. support／incident response

## Branding

Hyperliquid公式サポートは、公式HyperliquidアプリがApp Storeに存在しないと注意喚起している。本製品は独立した非公式クライアントとして、開発者名、運営者、サポート、署名証明、ドメインを明示する。

## Release evidence

- Play Console declaration screenshot／export
- 審査結果
- 追加資料提出記録
- target countries
- counsel memo version
- package name
- signing certificate digest
- privacy policy version
- store listing review
- unofficial branding review
- geo-block test

未完なら`PUBLIC_MAINNET_WRITE=false`のままにする。

## iOS／App Store

Public App Storeは、次が揃うまでNO_GO。

- organization developer enrollment
- wallet／exchange／crypto futures条項の適格性memo
-対象地域のlicense／permission evidence
- written Japan legal opinion
- signed iOS build／privacy／accessibility／security audit
- App Review demo／notes／support packet

Ad Hocは登録済み端末用、TestFlightはclosed testing用として別管理する。どちらもpublic Mainnet許可の代替ではない。
