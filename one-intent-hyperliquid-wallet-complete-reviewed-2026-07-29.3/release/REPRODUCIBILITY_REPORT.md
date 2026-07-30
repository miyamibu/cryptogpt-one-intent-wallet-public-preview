# Reproducibility Report — design-only

package=one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.3
phase=validated
fullValidationStatus=PASS
doubleBuildStatus=CONTRACT_DEFINED_NOT_RUN_BY_PREPARATION
cleanExtractStatus=CONTRACT_DEFINED_NOT_RUN_BY_PREPARATION
sourceTreeDigestDomain=secure_tree content snapshot with canonical archive file mode 0644, excluding manifest.json, SHA256SUMS.txt, delivery/evidence/core/reference-tests-current.json, delivery/evidence/core/PROPERTY_TEST_REPORT.json, delivery/evidence/core/FUZZ_REPORT.json, tests/coverage-matrix-v1.json, delivery/GATE_DECISIONS.json, delivery/OPERATIONAL_READINESS_REPORT.json, delivery/RUNTIME_ACTIVATION_REPORT.json, delivery/STATUS_MANIFEST.json, delivery/STATUS_MANIFEST.md, delivery/evidence/operationalization/EXECUTION_EVIDENCE_BINDING_20260729.json, FINAL_AUDIT_REPORT.md, VALIDATION_REPORT.md, release contract artifacts, and OS metadata

## Required release proof

`tools/build_release.py` must prepare the package, run non-mutating validation,
freeze the tree, build the ZIP twice, compare bytes and SHA-256, clean-extract
each candidate, and rerun the full validation. The current design package has
no signed native/service artifact, so this report does not claim production
reproducibility or release eligibility.

The recorded local preparation phase is `validated`. An external clean builder,
artifact signer, independent verifier, and protected release subject remain
required before any operational GO.
