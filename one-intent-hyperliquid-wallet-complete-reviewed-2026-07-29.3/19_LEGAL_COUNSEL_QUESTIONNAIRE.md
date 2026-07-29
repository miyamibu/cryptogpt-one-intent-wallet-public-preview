# 法律事務所向け質問票

## 製品概要

- 日本語の自然言語からHyperliquid関連操作を構造化
- ユーザーが具体的実行ボタンを押す
- Perp、Spot、transfer、withdraw、Bridge、Vault
- 独立したAndroid／iPhoneアプリ
- 取引Intent解析は端末内の決定論parserを第一候補とし、必要時もOpenAIから分離された独立運用の非OpenAIコンポーネントだけを候補にする。OpenAI-facing機能は固定の非取引サポートだけ
- 既存wallet modeと将来のMPC mode
- 収益候補: subscription、builder fee等

## 回答を求める事項

### 業規制

1. Perp注文API送信は第一種／第二種金融商品取引業、媒介、取次、代理、投資運用のどれに該当し得るか。
2. AIが「買い」「売り」「レバレッジ」を提案する場合、投資助言・代理業に該当するか。
3. ユーザー自身が数量・方向を指定し、AIが文法変換だけする場合の評価。
4. Spot注文送信は暗号資産交換業またはサービス仲介業に該当するか。
5. 2026年6月1日開始の仲介制度を利用できる前提と、Hyperliquidとの関係。
6. USDCの送付・Bridgeは電子決済手段関連規制にどう該当するか。
7. Vault depositは集団投資スキーム、ファンド持分、媒介、助言等に該当し得るか。
8. HyperEVM第三者Vaultの紹介・実行の追加論点。

### カストディ

9. Existing Wallet Modeで当社が署名できない場合の評価。
10. 2-of-3 MPCで当社が1 shareを持つ場合の評価。
11. policy signerとdevice shareの組合せで当社単独署名不可でも「管理」に当たるか。
12. vendorが復旧に関与する場合。
13. account recovery／key rotation時の管理権限。

### 海外事業者

14. 日本で未登録の海外プロトコル／取引所へ接続するUI提供の評価。
15. geo-block、disclosure、自己責任表示で足りるか。
16. 日本語マーケティング・日本居住者向け提供の影響。

### 収益

17. 月額
18. builder fee
19. affiliate
20. performance fee
21. Vault紹介料
22. relayer fee
23. token incentive

### AML／制裁

24. KYC要否
25. Travel Rule
26. unhosted wallet
27. sanctions screening
28. transaction monitoring
29. suspicious activity
30. record retention

### 消費者・広告

31. 適合性
32. risk disclosure
33.未成年者
34. AI表示
35.「一回で実行」の広告
36. non-custodial表示
37. incident liability
38. complaint handling

## 必須成果物

- 法的分類表
- 必要登録
- 不要とする場合の条件
- 禁止機能
- 必須Feature Gate
- Terms／Privacy／Risk Disclosureの条項
- 日本向けlaunch判定
- 関係当局への事前相談推奨

## Apple／iOS提出に関する質問

1. App Storeのwallet／exchange／crypto futures条項上、当社／個人は提出主体として適格か。
2. organization enrollment以外に、どのlicense／permission evidenceが必要か。
3. 日本だけ、海外だけ、TestFlightだけで評価はどう変わるか。
4. Existing Wallet ModeとManaged Self-Custody Modeでcustody／intermediation評価はどう変わるか。
5. Builder fee、subscription、spread、referralの利益相反と開示は何か。
6. AIの説明・提案が投資助言へ該当しない境界はどこか。
