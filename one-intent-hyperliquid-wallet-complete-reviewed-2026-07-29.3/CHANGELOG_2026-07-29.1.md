# Changelog — 2026-07-29.1

## 位置付け

前版の自動検証PASSを無条件の完成証明として扱わず、設計・画面・Schema・検証器・配布手順を敵対的に再監査した版。

## 利用者向け表示

- 主要機能名をやさしい日本語へ統一。
- 音声の「ペイパチャル」「生産価格」を候補として正規化するが、原文を残し、清算価格の意味を確認するまで先物確認を停止。
- 依頼にない「損切り2%」を画面例から削除し、「損切りは未設定」と明示。
- 先物に清算価格の目安、距離、口座方式、取得時刻、取得不能時停止を表示。
- 複合操作の算数を`948.50−300.00−1.00＝647.50`へ統一。
- CTAを重要明細の末尾へ移動し、上端・途中・末尾のscroll状態を表示。
- 320×568、大きな文字、dark themeを含むレイアウト修正。

## JPYC／ネットワーク手数料

- JPYC-only／native fee asset 0を通常swap可能と仮定しない。
- simulation asset registryとfee route capabilityをproduction-ineligibleとして分離。
- provider IDだけでなく、法人名、連絡先、規約version/hashをFee Readiness Plan v2.1へ追加。
- quoteをaccount、network、asset、operation、amount、nonce、期限、費用上限、fee asset cost、精算先へ束縛。
- 手動復旧Schemaをv2.1へ更新し、static exampleでは数量・上限・estimate ID・operation digestをnullに固定。
- 0.05 POLなどの固定補充量を削除。live operation-bound estimateがない場合は送らない。

## 検証

- 6 viewport×12 flow×2文字モード×2theme＝288条件を同じgeometry/contrast検査で実行。
- 10枚の安定スクリーンショットへ拡張。
- evidenceへja-JP locale、Playwright/Chromium、prototype source hash、test harness hashを記録。
- `scrollIntoView()`で検査状態を都合よく変えない。
- archive safety、secret hygiene、local link、adversarial auditをfull pipelineへ追加。
- 436件のKnown-Loophole Register、268件のSecurity Invariantsへ拡張。
- deterministic build metadata、sorted ZIP、single root、safe extraction、manifest/checksum検証を追加。
- scroll／overflow祖先で切り取った実描画領域を使い、完全に非表示の部品の誤検知と本当の中心点遮蔽を分離。
- `START_HERE.html`を320／390／1440幅×明暗の独立6条件で検査。
- 画面例の承認期間・上限・手数料上限・アドレス・指紋を「初期値ではない／ダミー」と明記。
- レビュー画像がsticky要約直下で内容blockを途中から切らないことを検査。
- 敵対的な抜け穴回帰ケースを97件へ拡張。
- full validation開始時に`__pycache__`／`.pyc`だけを除去し、archive safetyと最終validatorでも残存を拒否。
- package identity／version／timestampを`config/build-metadata.json`へ一本化し、manifest・ZIP root・report・evidenceのdriftを拒否。
- strict JSONでduplicate key、float、NaN／Infinity、negative zero、2^53安全範囲外の整数を拒否。
- strict YAMLでduplicate key、alias、NaN／Infinity、暗黙timestampを拒否。
- ChatGPT向けOpenAPIをfirst-party write contractから分離し、exact path/method/operation/schema/scope allowlistを検査。
- first-party write APIへsender-constrained proofとoperation固有のidempotency／capsule／device／receipt bindingを追加。
- full validationからvisual skipを削除し、generated report作成後にarchive／security／link検査を実行。
- ZIP pathをportable ASCIIへ限定し、固定timestampがDOS ZIPで正確に表現できる偶数秒・1980..2107年であることを事前検査。
- validator自身のnegative／positive self-testを36 assertionsへ拡張。
- ASCII-only ZIPではPythonがUTF-8 flagを0へ正規化する実挙動を踏まえ、builder／verifierの共有flag policyを0へ修正。

## 最終運用化ハードニング

- `test_prototype.py --check`が正本screenshotを削除できた経路を修正し、check modeの出力先をtemporary directoryだけに限定。
- `check_runtime_authorization.py`のimport失敗を修正し、validator allowlistをexact setでself-test。
- `run_full_validation.py`をexact isolated copyで実行し、各validatorの成功・失敗後に内容・mode・file setの不変を確認。
- trusted-time sequenceとevidence-index sequenceをpackage外の保護high-water markより必ず大きくするrollback防止を追加。
- readiness reportのtrusted-time sequenceとruntime時点の署名済みtrusted timeが一致しなければ停止。
- strictな`operation-quote.schema.json`を追加し、quote本文、source state、network identity、registry hash、期限、nonce、最終payload commitmentを固定。
- signed registryのCAIP-2、numeric chain ID、RPC chain ID、market／contract／proxy／code hash／decimalsをSigner直前に照合。
- reserve／sign／persist／broadcastを原子的state machine化し、`SIGNED_BROADCAST_UNKNOWN`は照合完了まで再署名禁止。
- 97件の敵対的回帰、436件のKnown-Loophole Register、268件のSecurity Invariantsへ最終更新。

## 決定論的コアとローカル境界の追加ハードニング

- canonical JSON／Decimalへdepth、node、string、document、hash-domain、金額桁数・scaleの資源上限を追加し、cycle、非文字列key、無効Unicode scalarを拒否。
- domain objectのbool/int混同、暗黙型変換、過大文字列、asset key不一致、quote binding欠落、payload型不一致を拒否。
- authorization expiry、nonce replay、既存SQLite tableのnonce UNIQUE index欠落、unexpected triggerをfail closedで検出。
- 署名後のpending／unknown／partial／manual状態では別authorizationも署名せず、authoritative reconciliation後だけ再開。
- local HTTP serverへanti-DNS-rebinding Host検証、same-origin／Sec-Fetch-Site検証、Transfer-Encoding／duplicate Content-Length／Expect／compressed request拒否、security header、例外詳細秘匿を追加。
- fee route、Hyperliquid fake、JPYC handoff、Sagaのmalformed input、idempotency conflict、overfill、negative age、unbounded lifetime、逆向きtransitionを拒否。
- release gateへ全Python source compileと57件のPython unit suiteを追加。

## Codex引継ぎ

- `codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md`を機能・安全要件の唯一の正本へ統一。
- 外部資格・実機・HSM／MPC・Testnet・法務・Store・監査を実行する`codex/CODEX_EXTERNAL_OPERATIONALIZATION_PROMPT_2026-07-29.md`を追加。
- rootの17/34は両正本へ案内する短いpointerへ変更。
- 無断条件補完、UI到達性、fee provider/quote、固定補充量、negative mutation、native/Testnet/Mainnet gateの追加要件を正本へ追記。

## 判定

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

- OpenAI-facing境界を再監査し、取引固有の下書き・ボタン手順・復旧手順も禁止。固定read-only状態、固定用語・エラー、一般安全案内、固定中立handoffだけへ縮小。
- 取引Intent解析を端末内決定論parser／独立運用の非OpenAIコンポーネントへ分離し、OpenAIへの取引文・宛先・金額・asset／network送信を禁止。
