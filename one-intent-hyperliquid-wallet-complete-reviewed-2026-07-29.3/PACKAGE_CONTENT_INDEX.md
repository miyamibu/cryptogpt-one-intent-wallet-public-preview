# Package Content Index

**版:** 2026-07-29.3  
**ZIP内ローカル状態:** `LOCAL_SANDBOX_OPERATIONAL_GO`  
**本番の機械判定:** `BLOCKED_NOT_OPERATIONAL`

| 区分 | 主な場所 | 役割 |
|---|---|---|
| 入口 | `START_HERE.html`, `README_FIRST.md`, `RUNNABILITY_AND_STATUS.md` | デザイン確認、現在の停止状態、実行方法 |
| 統合仕様 | `COMPLETE_SPEC.md`, `02_*`〜`43_*` | 要件、architecture、custody、失敗復旧、法務・Store gate、UX |
| 敵対監査 | `24_KNOWN_LOOPHOLE_REGISTER.md`, `25_SECURITY_INVARIANTS.md`, `44_*`〜`54_*` | 436件の抜け穴、268 invariant、97回帰、運用化の主張と証拠 |
| Deterministic core | `shared/*`, `tests/test_security_hardening.py` | canonical資源制限、strict domain型、nonce一意制約、atomic signer／Saga |
| Local runtime | `services/local_sandbox/*`, `tools/run_local_sandbox.py` | loopback限定、Host／Origin検証、smuggling対策、非取引read-only runtime |
| Prototype | `prototype/*`, `tests/prototype-visual-evidence.json` | 日本語12画面の完全offline UI review、288条件、10画像 |
| Contracts | `schemas/*`, `contracts/*`, `examples/*` | strict JSON Schema、OpenAPI、simulation fixture、operation-bound evidence |
| Operational readiness | `config/operational-readiness.json`, `delivery/evidence-index.json`, `delivery/OPERATIONAL_READINESS_REPORT.json` | 37 gate・93 claim、現在のBLOCKED判定 |
| Runtime controls | `schemas/runtime-state-bundle.schema.json`, `schemas/runtime-control-plane-lease.schema.json`, `schemas/per-operation-authorization.schema.json` | release GO、service lease、本人承認の分離 |
| Quote／registry／atomic signer | `54_CANONICAL_QUOTE_REGISTRY_AND_ATOMIC_SIGNER.md`, `schemas/operation-quote.schema.json`, `tools/runtime_authorization.py` | quote本文・chain identity・最終payload・high-water・結果不明時の再署名禁止 |
| Trust and evidence | `config/operational-trust-policy.template.json`, `schemas/operational-*.schema.json`, `tools/operational_readiness.py` | 署名、独立review、trusted time、out-of-band anchor、release binding |
| Plain Japanese | `config/user-facing-terms.ja.json`, `tests/plain-japanese-copy-cases.json`, `41_*` | 用語辞書、音声表記揺れ、初心者向け表示 |
| JPYC／fee | `47_FEE_ROUTE_AND_ASSET_REGISTRY_SPEC.md`, fee/asset Schema | registry、zero-gas capability、provider/quote、固定量なしの手動復旧 |
| Platform scaffold | `mobile/*`, `apps/*`, `core/shared/*`, `services/*` | Android/iOS/backendの境界。完成sourceではない |
| Test | `tests/*`, `tools/run_full_validation.py` | 112 Python source compile、118 Python unit tests、5 Swift contract tests、schema、hash、copy、archive、secret、link、visual、adversarial、non-mutating validation |
| Release | `config/build-metadata.json`, `tools/prepare_release_artifacts.py`, `tools/build_release.py`, `tools/verify_zip.py` | 生成と検証の分離、再現可能ZIP、clean extract |
| Codex | `CODEX_START_HERE.md`, `codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md`, `codex/CODEX_EXTERNAL_OPERATIONALIZATION_PROMPT_2026-07-29.md` | 機能仕様と、外部運用化・証拠取得の実行契約 |
| Sources | `references/SOURCES.md`, `references/CLAIM_TO_SOURCE_MATRIX.md`, `config/source-pins.example.yaml` | 公式情報、主張との対応、freshness/revocation方針 |

## 意図的に未実装の領域

`apps/android`、`apps/ios`、`core/shared`、`services/control-api`等は完成sourceではない。APK/AAB、archive/IPA、live backend、Signer、Testnet/Mainnet receiptがないことは現在の`BLOCKED_NOT_OPERATIONAL`を表す。

## Codexの正本構成

```text
機能・安全要件:
  codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md
外部運用化・証拠取得:
  codex/CODEX_EXTERNAL_OPERATIONALIZATION_PROMPT_2026-07-29.md
```

外部運用化プロンプトは機能仕様を上書きせず、資格・実機・HSM／MPC・Testnet・法務・Store・監査を実際に完了または具体的blocker化する。
