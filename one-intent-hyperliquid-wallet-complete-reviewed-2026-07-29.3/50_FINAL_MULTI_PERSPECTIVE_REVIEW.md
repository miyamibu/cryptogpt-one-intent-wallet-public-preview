# 最終・多視点レビュー

**版:** 2026-07-29.3  
**対象:** 完成ZIPに入る設計、オフライン画面見本、Schema、検証、Codex引継ぎ

## 結論

前版へ無条件の100%自信を置くことはできなかった。実際に、表示、言葉、経路証明、固定値、証跡、validatorの古い前提に複数の穴があった。本版では、発見した穴を「修正」「自動回帰検査」「明示的NO-GO」のいずれかへ変換した。

この版で高い信頼を置ける範囲は、次に限定される。

- 収録ファイルの完全性とhash
- Schemaと例の内部整合
- オフライン画面見本の検査対象範囲
- Mainnet等が無効であること
- Codexへ残作業が具体的に引き継がれていること

実資金を扱うnativeアプリ、外部提供者、Testnet/Mainnet、法務、Store審査の安全・適格性は未証明でありNO-GOである。

## 視点別の最終判定

| 視点 | 合格した点 | 残る停止条件 |
|---|---|---|
| 初心者 | 英語を日本語化、原文と解釈を併記、手動手順を具体化 | 実機での理解度テスト |
| 経験者 | 完全アドレス、指紋、期限、上限、情報の新しさ | live protocol値の照合 |
| デザイナー | 情報階層、末尾CTA、明暗、大文字、短い端末 | native renderingと実機差分 |
| 1px/1mmを疑うQA | 320×568を含む288条件、重なり、clip、scroll到達 | 物理mmは未保証、SwiftUI/Compose実機必須 |
| セキュリティ | fail closed、最小権限、quote/registry binding、二重実行防止 | signer/MPC/HSM外部監査 |
| 管理者/SRE | kill switch、二人承認、失効、reconciliation要件 | 実装と運用訓練 |
| 法務/Store | 技術GOと配布GOを分離 | 書面判断、申告、地域資格 |
| 実装者 | 正本prompt、Schema、DoD、証拠形式 | native/serviceコードは未実装 |
| 悪意ある攻撃者 | zero-gas、quote差替え、alias、stale、path traversalを回帰項目化 | 未知の脆弱性と外部依存 |

## 重大な修正

1. 大きな文字でも依頼原文を消さない。
2. 音声誤変換を明示確認するまで実行ボタンを無効にする。
3. CTAを明細末尾へ置き、固定領域で隠さない。
4. 明暗双方のコントラストを288条件で検査する。
5. 手動入金から固定のPOL量を削除する。
6. JPYCの画面例に本番アドレスを置かない。
7. 資産登録、経路能力、今回の見積もりを別々の証明へ分ける。
8. 見積もりを口座、network、資産、操作、金額、nonce、期限、上限、精算先へ束縛する。
9. visual evidenceとmanifestを固定時刻にし、再現性を高める。
10. ZIP path traversal、symlink、Unicode/case衝突を検査する。
11. Codexの機能仕様を一つの正本へ統合し、外部運用化は上書き不能な別実行契約へ分離する。
12. ChatGPT側から実行payloadやwrite toolへ到達できない要件を明文化する。
13. scroll領域で完全に切り取られた部品と、本当に遮蔽された部品を区別し、実描画領域の中心が押下先へ届かなければ失敗にする。
14. `START_HERE.html`を狭幅・標準・desktop、明暗の独立6条件で検査する。
15. 任意の承認期間・上限・address・fingerprintを「画面例・初期値ではない／ダミー」と値の近くで示す。
16. 証拠画像の上端で明細blockを途中から切らない。

## 「嫌な目線」で残した指摘

- 画面例の数値は、枠や色だけでなく文言で例示と示す必要がある。
- 長い行の冒頭がscroll境界で一部だけ見えるスクリーンショットは、機能不良ではなくてもレビュー資料として誤解を招く。native evidenceでは上端・中間・末尾を分ける。
- 44pt／48dpはbrowser上のlogical proxyに過ぎない。
- ダーク表示のdisabled状態は、低コントラストになり過ぎると「押せない理由」が読めない。
- 「確認済み」は、誰が、何を、いつ、どのhashで確認したかがなければ証拠ではない。
- provider名を表示しても、法人・規約・精算先・失効状態が結び付かなければ偽装耐性がない。
- 「残高を更新」は、元操作の再送ではなく再照合であることをUIとAPIの両方で保証する必要がある。
- 一度の承認は、設定保存期間と実行session期間を分けて見せる必要がある。
- 清算価格は、口座全体の状態で変動し、取得できないときに推定を出す方が危険である。
- validatorがPASSしても、そのvalidatorが見ていない条件は保証されない。検証コードもレビュー対象である。

## 最終判定

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
## 2026-07-29.1 追加の独立監査

旧PASSを前提にせずvalidator自身を実行・破壊fixture・source reviewで再確認した。実際に、package identity drift、Markdown checkerのcompile failure、OAuth URLのfalse positive、visual skip、negative zero／巨大整数、YAML implicit type、host directory mode依存、ZIP timestamp表現差を発見した。各問題は実装修正、LR-025〜LR-032、Security Invariants 153〜160、validator self-testへ変換した。production／native／Testnet／MainnetのNO-GOは変更していない。
