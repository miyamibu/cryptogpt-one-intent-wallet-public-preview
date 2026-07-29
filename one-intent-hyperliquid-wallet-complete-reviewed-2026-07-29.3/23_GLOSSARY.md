# 用語集

- **ActionPlanDraft**: AIが生成する未信頼の操作下書き。
- **CompiledPlan**: 決定論的Compilerがstate・metadataを適用した候補。
- **Execution Capsule**: ユーザーが許可する具体的な操作集合。
- **Execution Card**: Capsuleの人間向け表示。
- **semanticHash**: 実行意味を固定するhash。
- **renderReceiptHash**: 実際の表示情報を監査するhash。
- **Saga**: 非原子的な複数処理の状態管理。
- **Trade Agent／API Wallet**: Hyperliquidでmaster/subaccountの代理署名を行うagent wallet。
- **Root signer**: user-signed actionやEVM actionを担う署名経路。
- **SAFE_ALL**: fee・margin・後続処理分を除いた安全な全量。
- **cloid**: client order ID。
- **user-signed action**: EIP-712形式の送金・出金等。
- **L1 action**: Hyperliquid独自action hashを利用する注文等。
- **Feature Gate**: 機能を環境ごとに停止・解放する制御。
- **Source Pin**: 仕様・SDK・contractの検証済みversion。
- **Existing Wallet Mode**: 外部／既存walletがroot署名する方式。
- **Managed Self-Custody Mode**: 監査済み鍵分割等を用いる候補方式。
- **R0–R5**: 操作リスク層。R0=read-only、R1=上限内trade、R2=既知Vault／same-user official bridge等、R3=事前登録済み宛先への上限内送金／出金、R4=新規宛先・高額／全額・鍵／recovery変更、R5=registry／Mainnet release管理。`26_TRUSTED_DISPLAY_AND_STATE_QUORUM.md`を唯一の正本とする。
- **Reconciliation**: upstream結果と内部状態の照合。

## Cross-platform terms

**App Attest** — 正規app instanceからの要求である可能性を高めるAppleのattestation。Trusted Displayではない。  
**Authorization Key** — Capsule／Envelopeのhashへ署名する端末鍵。Hyperliquid root keyとは別。  
**Standing Authorization** — 保存済み宛先・chain・asset・hard cap・期間を事前に許可するpolicy。  
**Native Shell** — Android Compose／iOS SwiftUIのplatform固有UI・security層。  
**Shared Pure Core** — OS権限を持たないdomain／compiler／policy／hash／state machine。

## 利用者向けのやさしい日本語

| 技術語 | 主要画面の表示 |
|---|---|
| Perp / Perpetual | 期限なし先物取引 |
| Spot | 現物取引 |
| Slippage | 予定価格と成立価格のずれ |
| Bridge | 別ネットワークへの資金移動 |
| Vault | 運用口座 |
| Gas | ネットワーク手数料 |
| Gas token | ネットワーク手数料を払う資産 |
| Leverage | 取引倍率 |
| Margin | 取引の担保 |
| Liquidation Price | 清算価格 |
| Mark Price | 清算判定に使う価格 |
| Reduce-only | ポジションを増やさず減らすだけ |
| IOC | すぐ成立する分だけ |
| APY | 1年あたりの利益の目安 |
| TVL | 運用中の総額 |
| Drawdown | 過去の最大下落 |
| Lock period | 引き出せない期間 |

完全な機械可読辞書は `config/user-facing-terms.ja.json` を正本とする。
