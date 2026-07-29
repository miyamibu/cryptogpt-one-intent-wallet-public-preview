# クリプトGPT リポジトリ指示

## Goal

自己保管型ウォレットの安全境界を検証できる、オフラインの参照実装・契約・証跡ツールを維持する。ZIP内の非取引local sandboxは`LOCAL_SANDBOX_OPERATIONAL_GO`だが、本番は`BLOCKED_NOT_OPERATIONAL`を初期値とする。

## Canonical instructions

- 機能・安全要件の唯一の正本は`codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md`。
- 外部環境、資格情報、実機、HSM／MPC、Testnet、法務、Store、独立監査の実行契約は`codex/CODEX_EXTERNAL_OPERATIONALIZATION_PROMPT_2026-07-29.md`。
- 外部実行契約は機能仕様を上書きできない。矛盾時はfail-closedとし、decision logへ記録する。

## Constraints

- ChatGPT/OpenAI境界はread-only・固定カタログ・非トランザクションに限定する。
- 実在の秘密、契約アドレス、資格情報、KYC、銀行情報は追加しない。
- 検証器は非変異とし、検証を通すためにアサーションやゲートを弱めない。
- 本番、Testnet、ストア、法務、監査、実機の証拠がない限り`NO_GO`を維持する。
- 削除、履歴変更、commit、push、deployは明示された外部運用化作業を除き、依頼なしに行わない。

## Validation

```bash
python3 -B tools/prepare_release_artifacts.py
python3 -B tools/run_full_validation.py
python3 -B tools/check_operational_readiness.py
python3 -B tools/check_python_sources.py
python3 -B tools/test_python_unit_suite.py
python3 -B tools/run_local_sandbox.py self-test
python3 -B tools/generate_operationalization_evidence_binding.py --check
```

`run_full_validation.py`はソースツリーを変更してはならない。出力ZIPを作る場合はリポジトリ外へ、正本名`one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.3.zip`で指定する。

801項目・37ゲート・93クレームの実行証拠対応は`delivery/evidence/operationalization/EXECUTION_EVIDENCE_BINDING_20260729.json`で追跡する。このbindingはローカル／read-only証拠を参照するが、production evidenceやrelease approvalへ昇格させない。再生成時は`python3 -B tools/generate_operationalization_evidence_binding.py --write`を使う。

## Failure handling

不足する資格、契約、端末、監査、法務、ストア判断は`delivery/EXTERNAL_BLOCKERS.md`へ具体的な担当者手順として記録し、実装済みのfake／offline部分と混同しない。外部作業全体の実行形式は`codex/CODEX_EXTERNAL_OPERATIONALIZATION_PROMPT_2026-07-29.md`に従う。
