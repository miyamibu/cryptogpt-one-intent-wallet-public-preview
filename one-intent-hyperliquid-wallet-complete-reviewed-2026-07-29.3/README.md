# クリプトGPT — 検証済みローカルサンドボックス＋安全境界参照実装

このリポジトリは、`codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md`の機能要件に基づく決定論的コア、契約、fake adapter、非変異検証、証跡テンプレートと、`codex/CODEX_EXTERNAL_OPERATIONALIZATION_PROMPT_2026-07-29.md`の外部運用化手順を収録します。本番ウォレット、署名鍵、外部資格、実在のJPYC契約情報、Testnet／Mainnetの実行権限は含みません。

ZIP内だけで起動する非取引ローカルモードは`LOCAL_SANDBOX_OPERATIONAL_GO`です。実資金・外部サービスを伴う本番判定は、引き続き次のとおりです。

```text
BLOCKED_NOT_OPERATIONAL
```

## ZIP単体で起動

```bash
python3 -B tools/run_local_sandbox.py self-test
python3 -B tools/run_local_sandbox.py serve
```

ブラウザで`http://127.0.0.1:8765/`を開きます。loopback以外へのbind、署名、送信、外部network、秘密鍵、provider credentialは実装されていません。HTTP境界はloopback Hostを厳密検証し、cross-origin、request smuggling系header、圧縮request、query context、例外詳細の漏えいをfail closedで拒否します。

## 検証・releaseコマンド

```bash
python3 -B tools/prepare_release_artifacts.py
python3 -B tools/run_full_validation.py
python3 -B tools/check_operational_readiness.py
python3 -B tools/check_python_sources.py
python3 -B tools/test_python_unit_suite.py
python3 -B tools/build_release.py /tmp/one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.3.zip
python3 -B tools/generate_operationalization_evidence_binding.py --check
```

`prepare_release_artifacts.py`だけが派生証跡を生成します。`run_full_validation.py`は全Pythonソース、全単体テスト、ローカルHTTP境界、browser検査を含みます。`run_full_validation.py`と`check_operational_readiness.py`は読み取り専用です。`build_release.py`は正本名のZIPをリポジトリ外へだけ書き込み、二重build、byte一致、clean-extract再検証を行います。

801項目・37ゲート・93クレームの現時点の結合状態は`delivery/evidence/operationalization/EXECUTION_EVIDENCE_BINDING_20260729.json`に固定しています。現在は801行のper-ID実行証拠が未結合、37ゲート・93クレームが未承認であり、ローカル／read-only証拠を本番証拠として扱いません。

## 実装済みの安全境界

- 金額は文字列Decimalのみで扱い、浮動小数点・指数表記・負のゼロ・過大入力を拒否します。
- canonical JSONは重複key、非文字列key、無効Unicode scalar、循環参照、過剰な深さ・node数・文字列長を拒否します。
- AI／音声解析は未信頼のdraftだけを作り、signer、policy、broadcast、アドレス選択を行いません。
- ChatGPT/OpenAI向け契約は4操作の固定read-only surfaceだけを公開します。
- registry、quote、fee capability、runtime lease、per-operation authorizationはそれぞれ独立して検証します。
- authorization IDとnonceはdurableな一意制約で原子的に消費し、署名後の未確定状態では照合完了まで別承認も再署名しません。
- 実装済み、fakeでテスト済み、外部未検証、監査済み、法務承認済み、本番有効化を分けて記録します。

## Codexへの引継ぎ

機能仕様は`codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md`、外部環境・資格情報・実機・HSM／MPC・Testnet・法務・Store・独立監査の実行契約は`codex/CODEX_EXTERNAL_OPERATIONALIZATION_PROMPT_2026-07-29.md`です。後者は前者を上書きせず、外部作業を証拠へ結合するために使います。

## 配置

`shared/`が決定論的コア、`services/`が境界サービス、`adapters/`がfake／契約adapter、`apps/`がbrowser／native shell、`tools/`が検証・パッケージング、`delivery/`が証跡です。
