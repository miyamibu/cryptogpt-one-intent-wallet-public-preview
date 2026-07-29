#!/usr/bin/env python3
"""Single source of truth for the design release source-tree digest domain."""
from __future__ import annotations

from pathlib import Path

from secure_tree import FileRecord, digest_records, snapshot


EXCLUDED_DERIVED_PATHS = frozenset(
    {
        "manifest.json",
        "SHA256SUMS.txt",
        "delivery/evidence/core/reference-tests-current.json",
        "delivery/evidence/core/PROPERTY_TEST_REPORT.json",
        "delivery/evidence/core/FUZZ_REPORT.json",
        "tests/coverage-matrix-v1.json",
        "delivery/GATE_DECISIONS.json",
        "delivery/OPERATIONAL_READINESS_REPORT.json",
        "delivery/RUNTIME_ACTIVATION_REPORT.json",
        "FINAL_AUDIT_REPORT.md",
        "VALIDATION_REPORT.md",
        "release/release-subject.json",
        "release/RELEASE_SUBJECT.json",
        "release/SOURCE_PINS.json",
        "release/SBOM.spdx.json",
        "release/PROVENANCE.json",
        "release/ARTIFACT_HASHES.txt",
        "release/BUILD_ENVIRONMENT.md",
        "release/REPRODUCIBILITY_REPORT.md",
        "release/CODEX_EXECUTION_REPORT.md",
        "release/UNRESOLVED_EXTERNAL_BLOCKERS.md",
        "release/OPERATIONAL_HANDOFF.md",
    }
)

DIGEST_DOMAIN = (
    "secure_tree content snapshot with canonical archive file mode 0644, excluding manifest.json, SHA256SUMS.txt, "
    "delivery/evidence/core/reference-tests-current.json, delivery/evidence/core/PROPERTY_TEST_REPORT.json, "
    "delivery/evidence/core/FUZZ_REPORT.json, tests/coverage-matrix-v1.json, delivery/GATE_DECISIONS.json, "
    "delivery/OPERATIONAL_READINESS_REPORT.json, delivery/RUNTIME_ACTIVATION_REPORT.json, "
    "FINAL_AUDIT_REPORT.md, VALIDATION_REPORT.md, release contract artifacts, and OS metadata"
)


def design_source_tree_digest(root: Path) -> str:
    records = snapshot(root, exclude=set(EXCLUDED_DERIVED_PATHS))
    # The reproducible ZIP deliberately canonicalizes every regular-file mode
    # to 0644. Normalize the digest to that archive mode so the evidence hash
    # survives a clean extraction without dropping the separate archive-mode
    # safety check.
    canonical_records = tuple(
        FileRecord(path=item.path, mode=0o644, size=item.size, sha256=item.sha256)
        for item in records
    )
    return digest_records(canonical_records)
