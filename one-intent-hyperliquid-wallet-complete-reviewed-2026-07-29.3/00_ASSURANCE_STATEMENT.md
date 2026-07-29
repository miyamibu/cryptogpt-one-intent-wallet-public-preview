# 100%確信についての保証声明

## 結論

**文字どおり100%の確信はない。**

理由は単純で、現時点では次が未完了だからである。

- production用Android／iOSアプリ、backend、signerの実装コードがない（offline prototypeと設計用scaffoldのみ）
- Hyperliquid Testnetの実取引試験を行っていない
- 少額Mainnet試験を行っていない
- Pixel 9a実機で鍵失効・生体認証・バックアップ挙動を検証していない
- 外部セキュリティ監査を受けていない
- 採用するMPC／署名方式が最終選定されていない
- 日本法上の書面意見を得ていない
- OpenAI・Hyperliquid・Android・法令は将来変更され得る

この状況で「100%安全」「必ず適法」「絶対に資産を失わない」と言えば、ただの強がりである。金融アプリで強がりは、だいたい請求書の前座になる。

## それでも「事実上100%」へ近づける方法

不確実な事項を推測で埋めず、すべて**検証項目または公開停止条件**へ変換する。

### 本パッケージの保証レベル

| 項目 | 判定 | 意味 |
|---|---|---|
| 仕様の論理整合性 | PASS_WITH_RESIDUAL_RISK | 文書・Schema・API骨格を相互検証する |
| 公式資料との整合 | PASS_AS_OF_DATE | 2026-07-29時点の一次資料を基準にした |
| 技術的実現可能性 | CONDITIONAL_GO | 主要経路は実現可能だが、MPC・実機・プロトコル検証が必要 |
| Codex実装開始 | GO | source実装を開始できる。Testnet writeはまだNO_GO |
| 個人用少額Mainnet | NO_GO | 実装・試験・鍵復旧試験が未完了 |
| 日本向け一般公開 | NO_GO | 法務意見・監査・運用体制が未完了 |
| 100%安全の主張 | PROHIBITED | 将来も表示してはならない |

## 絶対条件

次のいずれかが未確認なら、システムは自動的に`NO_GO`となる。

1. 署名対象と画面表示の同一性
2. 宛先、チェーン、トークン、コントラクトの決定論的解決
3. API Wallet／root signerの権限分離
4. nonce・cloid・リトライの重複防止
5. Bridge／Vaultのruntime allowlistとcode hash確認
6. Pixel 9aでの鍵失効・復旧試験
7. 対応するHyperCore Testnet、Bridge2 local fork、HyperEVM test/forkでの操作・失敗系試験
8. 外部セキュリティ監査の重大指摘ゼロ
9. 日本向け公開に必要な登録・媒介・助言・AMLの法務意見
10. インシデント時にAIなしで停止・退避できること
11. 高リスク操作のTrusted Display経路、または未対応端末での明示的NO_GO
12. 重要状態の独立ソース照合と乖離時fail closed
13. Google Playの金融機能申告・暗号資産ポリシー・地域適格性の承認

## 現時点の最終判定

```text
設計の採用             GO
Codexによる実装開始     GO
Android build           NO_GO
iOS build               NO_GO
Hyperliquid Testnet write NO_GO
個人用少額Mainnet       NO_GO
一般公開Mainnet         NO_GO
ChatGPT内での直接発注   PROHIBITED
```

## 「事実上100%」の定義

本パッケージでいう「事実上100%へ近づける」とは、未知の危険をゼロと断言することではない。既知・合理的に予見できる危険を、次のいずれかへ変換した状態を指す。

- 実装上の不変条件
- 自動テスト
- 独立監査
- runtime fail-closed
- 資産上限
- Feature Gate
- 公開停止条件

未知の脆弱性、将来の仕様変更、市場損失、法解釈の変更は残る。したがって、`100%安全`、`絶対適法`、`資産を失わない`という表示は永久に禁止する。

## Cross-Platform追加保証条件

未完了項目へ次を追加する。

- Swift／SwiftUI／Xcode projectがない
- iPhone実機でSecure Enclave、Keychain、App Attest、Face ID／Touch IDを検証していない
- App Attestのunsupported、再install、migration、restoreを検証していない
- Apple Developer organization enrollment、TestFlight、App Store適格性を確認していない
- iOS公開に必要な提出主体・ライセンス・地域要件を確認していない

絶対条件へ次を追加する。

14. iPhone実機の鍵失効、再install、migration、App Attest evidence
15. Android／iOSでcanonical hash、policy decision、critical disclosureが一致すること
16. iOS App Attest modeがTrusted Displayを主張しないこと
17. Public iOS distributionはorganization、written legal opinion、licensing／permissions、App Review readinessが揃うまでNO_GO

現在の正確な判定：

```text
DESIGN_GO
OFFLINE_PROTOTYPE_GO
CODEX_IMPLEMENTATION_GO
ANDROID_BUILD_NO_GO
IOS_BUILD_NO_GO
TESTNET_WRITE_NO_GO
PERSONAL_SMALL_MAINNET_NO_GO
CLOSED_ALPHA_NO_GO
PUBLIC_ANDROID_STORE_NO_GO
PUBLIC_IOS_APP_STORE_NO_GO
```
