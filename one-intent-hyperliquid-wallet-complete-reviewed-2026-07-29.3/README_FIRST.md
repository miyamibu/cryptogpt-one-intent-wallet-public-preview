# One-Intent Hyperliquid Wallet — 完全レビュー版

**版:** 2026-07-29.3  
**対象:** Android／iPhone向け会話ウォレット  
**製品表示:** Hyperliquid連携・非公式  
**ZIP内ローカル運用:** `LOCAL_SANDBOX_OPERATIONAL_GO`  
**本番の機械判定:** `BLOCKED_NOT_OPERATIONAL`  
**本番GOとして許可する唯一の名称:** `PRODUCTION_OPERATIONAL_GO`

## まず開くもの

ブラウザで`START_HERE.html`を開く。状態説明と、12画面の完全オフライン見本を同じページで確認できる。

読む順番は次のとおり。

1. `RUNNABILITY_AND_STATUS.md`
2. `44_ADVERSARIAL_REVIEW_AND_RESOLUTION.md`
3. `51_OPERATIONAL_READINESS_AND_RUNTIME_ACTIVATION.md`
4. `52_FINAL_OPERATIONAL_GAP_REVIEW.md`
5. `53_CODEX_OPERATIONAL_COMPLETION_CONTRACT.md`
6. `54_CANONICAL_QUOTE_REGISTRY_AND_ATOMIC_SIGNER.md`
7. `45_RELEASE_ASSURANCE_CASE.md`
8. `PACKAGE_CONTENT_INDEX.md`
9. `codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md`
10. `codex/CODEX_EXTERNAL_OPERATIONALIZATION_PROMPT_2026-07-29.md`

## このZIPに入っているもの

- 製品要件、脅威モデル、アーキテクチャ、署名・保管、障害復旧
- Android／iOS設計、アクセシビリティ、Store／法務gate
- JSON Schema、OpenAPI、canonical hash vectors、feature gates
- やさしい日本語の12画面オフラインプロトタイプ
- 6画面サイズ × 12 flow × 2文字設定 × 2テーマ＝288条件のbrowser検査
- 10枚の安定レビュー用スクリーンショット
- `START_HERE.html`の320／390／1440幅×明暗＝6条件の入口画面検査
- JPYC登録情報、手数料経路能力、今回の見積もり、手動復旧を分離したSchema
- ZIP path、symlink、Unicode／大文字小文字衝突、secret混入、local linkを確認する検査
- 436件の既知抜け穴、268件のSecurity Invariants、97件の敵対的回帰
- 37 gate・93 claimのoperational readiness profile
- loopback限定・外部通信なし・署名送信なしのローカルサンドボックス
- Codexへ渡す機能仕様の正本と、外部運用化・証拠取得の実行契約


## ZIP単体で今すぐ起動する

```bash
python3 -B tools/run_local_sandbox.py self-test
python3 -B tools/run_local_sandbox.py serve
```

`http://127.0.0.1:8765/`で入口と画面見本を開ける。`/healthz`、`/readiness`、ローカルdraft parser、固定catalogのread-only supportだけを公開し、未知の`/v1/*`、署名、送信、外部network、秘密鍵を拒否する。このGOはローカル非取引モードだけを指し、本番GOではない。

## このZIPに入っていないもの

- Kotlin／Swiftの完成アプリ
- APK／IPA
- live backend、Signer、MPC／HSM
- JPYC EX本番資格情報または契約
- 検証済みpaymaster／relayer／fee provider
- Hyperliquid Testnet／Mainnet書き込み
- 実機検査、外部セキュリティ監査
- 法務の書面判断、Apple／Googleの審査結果

したがって、これは**実装開始可能な設計・契約・オフライン画面見本・非破壊検証・運用証拠・引継ぎパッケージ**であり、実資金を置ける完成wallet binaryではない。現在のreadiness reportは37 gate・93 claimを0件承認として`BLOCKED_NOT_OPERATIONAL`を返す。

## 前版から重大に直した点

- 大きな文字でも利用者の依頼原文を残した。
- 「ペイパチャル」「生産価格」を候補として解釈しても、確認まで注文へ進めないhard gateを設けた。
- 依頼されていない損切りを追加しない。
- 清算価格を保証値として扱わず、欠損・古い・不整合なら停止する。
- 実行ボタンを明細末尾へ置き、固定領域の裏へ隠れないようにした。
- 暗い表示、focus、文字間隔、最小画面を含めて検査した。
- 手動復旧から固定のPOL量を削除した。
- 画面例のJPYCに明示的なdummy addressを使用し、本番利用不可とした。
- 資産登録、zero-native-balance経路能力、operation-bound quoteを別々に証明する設計へ変更した。
- validator自身の古い期待値を見直し、288条件と現在の画像名を照合するようにした。
- ZIPの再現生成とclean-extract検証を追加した。
- Codexの機能仕様を一つの正本へ統合し、外部作業は役割の異なる運用化プロンプトへ分離した。
- 検証器をisolated copyで実行し、各validatorの成功・失敗後にsource treeが不変であることを確認するようにした。
- trusted-timeとevidence-indexのsequence rollbackを、package外のhigh-water markで拒否するようにした。
- canonical quote本文、signed registry、CAIP-2／RPC chain ID、最終payloadをSigner直前に再計算する契約を追加した。
- 署名後に送信結果が不明な操作を再署名せず、`SIGNED_BROADCAST_UNKNOWN`として照合へ送るようにした。
- canonical入力の深さ・node数・文字列長・金額桁数を制限し、循環参照、非文字列key、無効Unicode、型の暗黙変換を拒否した。
- authorizationの期限とnonce一意制約を検証し、既存SQLite schemaに一意indexがない場合も起動を拒否した。
- local sandboxへHost／Origin／Sec-Fetch-Site検証、request smuggling対策、security header、例外詳細の秘匿を追加した。

詳細は`44_ADVERSARIAL_REVIEW_AND_RESOLUTION.md`、`45_RELEASE_ASSURANCE_CASE.md`、`46_PIXEL_AND_INTERACTION_AUDIT.md`、`41_PLAIN_JAPANESE_AND_JPYC_FEE_READINESS.md`を読む。

## ChatGPTの境界

ChatGPT／OpenAI側は、抽象化した照合済み状態、固定用語説明、固定エラー説明、一般的な安全案内、中立的な「独立ウォレットを開く」案内だけに限定する。取引文、宛先、金額、資産・network、取引固有の下書き・ボタン手順、payload、署名要求、実行deep link、write toolを公開しない。取引解析、手動復旧、確認、署名、送信は、将来実装する独立wallet app内だけで行う。

## 「最初の一回だけ承認」の意味

無期限・無制限の権限ではない。保存期間、active session、無操作停止、資産、network、保存済み相手、1回／日／月の金額、取引倍率、費用上限を限定する。新規相手、高額、全額、鍵・権限変更、異常な費用、古い状態では再確認する。

## 検証

Python 3.10以上を使う。

```bash
python3 -m pip install -r tools/requirements.txt
python3 -m pip install -r tools/requirements-visual.txt
python3 -B tools/run_local_sandbox.py self-test
python3 -B tools/run_full_validation.py
python3 -B tools/check_operational_readiness.py
```

派生物の生成は検証と分離し、必要時だけ次を実行します。

```bash
python3 -B tools/prepare_release_artifacts.py
```

配布ZIPは次の一つの入口から生成します。

```bash
python3 -B tools/build_release.py ../one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.3.zip
```

`run_full_validation.py`にvisual工程のskip optionはない。Playwright／Chromiumを準備できない環境はrelease-gradeのFULL VALIDATIONを名乗らず、必要な依存を導入してから正本コマンドを再実行する。

`PASS`が証明するのは、列挙された有限な検査範囲である。browserのlogical pixelは、SwiftUI／Compose、実機safe area、VoiceOver／TalkBack、物理mmを証明しない。

## Codexへ渡す

展開したrepository全体と、役割の異なる次の2ファイルを使う。

```text
codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md
codex/CODEX_EXTERNAL_OPERATIONALIZATION_PROMPT_2026-07-29.md
```

前者は機能・安全要件の唯一の正本、後者は外部環境でその要件を実装し、資格情報、実機、HSM／MPC、Testnet、法務、Store、独立監査の証拠を取得する実行契約である。外部資格情報や実機などがなければ、fake adapterで実装・検査し、外部作業を担当role、portal、画面、field、必要資料、証拠path、再検査commandまで具体化する。証拠なしでMainnet gateを開けない。37 gate・93 claim、out-of-band trust anchors、trusted time、runtime state、短期限lease、single-use操作別承認をすべて実装・証拠化する。
