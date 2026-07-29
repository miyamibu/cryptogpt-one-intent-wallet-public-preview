# 最終納品インデックス

**版:** 2026-07-29.3  
**ZIP内ローカル状態:** `LOCAL_SANDBOX_OPERATIONAL_GO`  
**本番状態:** `BLOCKED_NOT_OPERATIONAL`

## 最初に開く

1. `START_HERE.html` — 状態と実際の画面見本
2. `RUNNABILITY_AND_STATUS.md` — 今使える範囲と未実装範囲
3. `51_OPERATIONAL_READINESS_AND_RUNTIME_ACTIVATION.md` — 37 gate・93 claimとruntime条件
4. `52_FINAL_OPERATIONAL_GAP_REVIEW.md` — 多視点の最終不足分析
5. `53_CODEX_OPERATIONAL_COMPLETION_CONTRACT.md` — Codex完了契約
6. `54_CANONICAL_QUOTE_REGISTRY_AND_ATOMIC_SIGNER.md` — quote・registry・chain・final payload・atomic signer
7. `CODEX_START_HERE.md` — Codexへ渡す2層の正本案内
8. `codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md` — 機能・安全要件の正本
9. `codex/CODEX_EXTERNAL_OPERATIONALIZATION_PROMPT_2026-07-29.md` — 外部環境・資格・実機・監査・法務・Storeの実行契約

## 運用化の正本

- `config/operational-readiness.json`
- `config/operational-trust-policy.template.json`
- `delivery/evidence-index.json`
- `delivery/OPERATIONAL_READINESS_REPORT.json`
- `schemas/operational-*.schema.json`
- `schemas/trusted-time-attestation.schema.json`
- `schemas/runtime-state-bundle.schema.json`
- `schemas/runtime-control-plane-lease.schema.json`
- `schemas/per-operation-authorization.schema.json`
- `tools/operational_readiness.py`
- `tools/check_operational_readiness.py`
- `tools/test_operational_readiness_negative.py`
- `schemas/operation-quote.schema.json`
- `tools/runtime_authorization.py`
- `tools/check_runtime_authorization.py`
- `tools/test_runtime_authorization_positive.py`
- `tools/test_runtime_authorization_negative.py`

## 検証

派生物を生成する明示工程:

```bash
python3 -B tools/prepare_release_artifacts.py
```

packageを変更しない完全検証:

```bash
python3 -B tools/run_full_validation.py
```

現在の設計packageが本番を開けないことの検証:

```bash
python3 -B tools/check_operational_readiness.py
```

再現可能ZIPの生成とclean-extract再検証:

```bash
python3 -B tools/build_release.py ../one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.3.zip
```

## 現在の境界

このZIPは、本番ウォレットbinary、live signer、実資金接続、外部監査、法務・Store承認を含まない。Codexと外部関係者が機能仕様と外部運用化契約をすべて実装・証拠化し、37 gate・93 claimをexact release subjectへ結合した場合だけ`PRODUCTION_OPERATIONAL_GO`候補になる。GO後もfresh runtime state、短期限lease、single-use操作別承認なしには実行できない。
