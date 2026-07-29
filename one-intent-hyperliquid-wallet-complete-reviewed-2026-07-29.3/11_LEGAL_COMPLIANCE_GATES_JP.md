# 日本向け法務・コンプライアンスゲート

> これは法律意見ではない。一般公開前に、日本の金融規制・暗号資産・デリバティブ・資金決済・AMLに詳しい弁護士の書面意見が必要。

## 現在の判定

```text
個人の設計・Testnet: GO
個人の少額Mainnet: 法務確認推奨、技術ゲート未完了
Closed Alpha: NO_GO
日本向け一般公開: NO_GO
```

## 問題となる機能

### Perp

暗号資産デリバティブの注文を他者のために伝達・実行・媒介する場合、金融商品取引業との関係を評価する。

質問:

- UI提供だけか
- 注文をAPIへ送る主体は誰か
- 価格・数量をAIが提案するか
- builder feeを得るか
- ユーザーごとに裁量判断するか
- 日本居住者へ勧誘するか

### Spot

暗号資産の売買・交換の媒介、暗号資産交換業、2026-06-01開始の電子決済手段・暗号資産サービス仲介業との関係を評価する。

新仲介制度は、登録された所属業者の委託を受け、限定された媒介を行う枠組みであり、任意の海外プロトコルへの接続を自動的に許容するものではない。

### USDC／送金

- USDCの法的分類
- 電子決済手段関連規制
- transfer／withdrawの媒介
- Travel Rule
- sanctions
- beneficiary／originator data
- unhosted wallet risk

### MPC／Signer

- 他人の資産を管理する権限
- service側の単独署名可否
- user recovery
- custody／control
- bankruptcy remoteness
- vendor role
- key shareの法的評価

### AI

- 一般情報
- 個別助言
- 推奨銘柄
- risk score
-「買い時」回答
- 自動売買
- 適合性
- 誇大広告

## 収益モデル

次を別々に評価する。

- 月額subscription
- builder fee
- spread／markup
- affiliate
- Vault紹介料
-成功報酬
- withdrawal fee
- relayer fee
- priority fee

手数料が注文量・損益・特定商品に連動すると、利益相反と規制評価が変わり得る。

## AML/CFT

一般公開時の最低検討事項:

- customer identification
- sanctions screening
- PEP
- adverse media
- wallet risk screening
- source of funds
- transaction monitoring
- suspicious activity escalation
- Travel Rule
- record retention
- law enforcement response
- geo restriction
- self-hosted wallet controls

## 消費者保護

- Hyperliquid公式ではない
- 元本保証なし
- liquidation
- smart contract／bridge／L1／oracle risk
- Vault loss／lock
- AI error
- price delay
- unsupported assets
- incident support
- complaint handling
- Japanese language terms
- privacy policy
- risk disclosure
- underage policy

## 書面で必要な最終回答

1. どの登録が必要か、または不要か
2. 不要とする根拠・前提条件
3. 個人利用／closed alpha／publicの境界
4. non-custodial／MPCの評価
5. Hyperliquidが日本で未登録の場合の提供可否
6. PerpとSpotの別評価
7. USDC／Bridge／送金の評価
8. 投資助言の回避条件
9. builder fee等の収益モデル
10. AML／Travel Rule
11. 適用する利用規約・準拠法・紛争
12. 必要なgeo block・KYC・年齢制限

この書面がない限り、日本向けpublic Mainnet gateは開かない。

## iOS／App Store追加質問

- organization developerとして提出可能か
- ウォレット、暗号資産取引、暗号資産先物のApp Review要件へ適合する提出主体か
- Hyperliquid Perpを日本向けに提供する行為の評価
- non-custodial／MPC／external walletの各modeでcontrol／custody評価が変わるか
- TestFlight／Ad Hocでの限定試験に必要な利用者同意と制限
- region restrictionの設計が十分か

Apple審査通過と日本法の適法性は別々に判定する。
