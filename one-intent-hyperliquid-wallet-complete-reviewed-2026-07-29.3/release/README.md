# Release output contract

このpackageは`DESIGN_ONLY`です。要求されたrelease metadataの雛形とローカル検証証跡は生成済みですが、production用の署名済みartifact、production SBOM/provenance、確定済みsource pin、approval、runtime handoffは存在しません。成果物が存在すること自体は`GO`を意味せず、現在の判定は`BLOCKED_NOT_OPERATIONAL`です。

production候補releaseでは、次の成果物を同一のexact release subjectへ結合し、署名・独立レビュー・clean environmentで検証します。

canonical stageの配布ZIPは、package外に同名の`one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.3.zip.sha256` sidecarを持ちます。sidecarは`tools/build_release.py`が生成するZIPのSHA-256とfilenameを照合するだけの配布整合性証跡であり、署名済みproduction provenanceやrelease approvalの代わりにはなりません。

```text
RELEASE_SUBJECT.json
SOURCE_PINS.json
SBOM.spdx.json
PROVENANCE.json
ARTIFACT_HASHES.txt
BUILD_ENVIRONMENT.md
REPRODUCIBILITY_REPORT.md
CODEX_EXECUTION_REPORT.md
UNRESOLVED_EXTERNAL_BLOCKERS.md
OPERATIONAL_HANDOFF.md
```

lowercaseの`release-subject.json`は、`delivery/evidence-index.json`の`releaseSubject`とbyte-levelで同一になる設計用canonical subjectです。production subjectの代用品ではありません。`config/operational-trust-policy.production.json`と`config/runtime-policy.production.json`は既存のcanonical policy schemaに沿ったdisabled／`PRODUCTION_NOT_PROVISIONED` placeholderであり、pointerや実運用資格情報ではありません。source-tree digestの定義は、`manifest.json`、`SHA256SUMS.txt`、生成された証跡、OS metadataを除外し、ZIPのcanonical regular-file mode `0644`へ正規化するdomainとして固定し、生成器とvalidatorで同じ計算を使います。

uppercaseの10成果物は`tools/generate_release_contract_artifacts.py`が決定論的に生成するdesign-only metadataです。`SBOM.spdx.json`と`PROVENANCE.json`は署名なし・`NOASSERTION`を含む記録で、native binary、秘密鍵、live service、外部承認を証明しません。`CODEX_EXECUTION_REPORT.md`の`fullValidationStatus=PASS`も、このpackageの非破壊ローカル検証だけを示します。

`config/toolchain-lock.json`は記録された検証環境を固定しますが、AndroidのGradle Wrapper／SDK／sdkmanagerが`BLOCKED_MISSING`であるため、native release lockやsigned APK/AABの代わりにはなりません。`release/UNRESOLVED_EXTERNAL_BLOCKERS.md`と`release/OPERATIONAL_HANDOFF.md`は、未完了の外部作業を明示するための引継ぎ資料です。

このファイルの存在、ローカルchecksum、offline test PASSだけでは、production GOを意味しません。
