# 製品要件

## 目的

ユーザーが自然言語でHyperliquid関連操作を指示し、通常は1回の具体的な実行操作で完了できること。

## 必須ユーザーストーリー

1. BTC／ETH等のPerpを金額、レバレッジ、TP/SL付きで注文できる。
2. Spotをquote金額またはbase数量で売買できる。
3. 保存済み相手へHyperCore内送金できる。
4. 自分の保存済みArbitrum addressへ出金できる。
5. Arbitrum Native USDCを公式Bridge2経由で入金できる。
6. HLP／許可済みVaultへ入出金できる。
7. 上記を1つの複合Action Graph／Intentとして承認できる。Managed Self-Custody Modeでは原則1回のアプリ内認証を目標とし、Existing Wallet Modeでは必要な外部wallet署名回数を隠さない。
8. AIなしの手動画面から取消・決済・出金・失効ができる。
9. 途中失敗時、資産の現在位置と再開方法が分かる。
10. 新規宛先・高額操作・鍵変更では追加認証が自動で入る。

## 機能要件

- Natural-language intent
- deterministic compile
- live Execution Card
- exact button label
- policy profile
- address book
- contract registry
- decimal-safe calculations
- account mode support
- Hyperliquid info／exchange adapters
- WebSocket＋REST reconciliation
- Saga orchestration
- feature gates
- audit log
- emergency mode
- source change monitoring

## 非機能要件

| 分野 | 要件 |
|---|---|
| Security | 任意署名APIを持たない |
| Privacy | OpenAIへ取引文・取引条件・秘密情報を送らない |
| Reliability | crash後に実行状態を再構築 |
| Performance | 通常注文カードの更新を体感遅延なく行う |
| Accessibility | TalkBack、文字拡大、色以外の警告 |
| Localization | 金額・時刻・小数点をlocale対応 |
| Auditability | 表示、認証、署名、送信、照合を追跡 |
| Change safety | 仕様差分でFeature Gate停止 |
| Legal | 一般公開前に書面法務判定 |

## UX KPI

- 明確な注文の追加会話往復: 0
- 明確な注文の確認画面遷移: 0
- 通常注文のユーザー操作: 1
- 新規宛先の誤送金: 0
- AIによる無断実行: 0
- 実行内容と表示内容の不一致: 0
- 部分失敗の不明表示: 0

## 初期スコープ

「すべて実装対象」と「すべてMainnet有効」を区別する。

- Code scope: 全機能
- Testnet: 順次全機能
- Small Mainnet: own account、own destinations、低上限
- Public Mainnet: release gate通過機能のみ

## Cross-platform追加要件

- AndroidとiOSはnative shellを持つ
- pure domain／compiler／policy／hash／state machineだけを共有する
- platform capabilityとauthorization assuranceをdomain modelへ含める
- AndroidとiOSで同じsemantic inputから同じcanonical hashを生成する
- iOSはDynamic Type、VoiceOver、Secure Enclave、App Attest、Keychain、Universal Linksへ対応する
- AndroidはPixel 9a、iOSは小型iPhoneと現行Face ID端末をP0とする
- iOS public App Store gateは独立してdefault OFF

UX KPIへ追加：

- critical text clipping：0
- platform間semantic drift：0
- iOSでTrusted Displayと誤表示：0
- expected signature countの隠蔽：0

## Semantic completeness

- ユーザー入力中のすべてのactionable clauseは、operation、missing field、warning、またはunsupported reasonのいずれかへ対応付ける。
- 「注文＋損切り」のうち注文だけを実行候補へ残すsilent omissionは禁止する。
- fill依存のTP／SLはactual weighted fillを参照するformulaとして承認し、placement timeout時のrecoveryを表示する。
