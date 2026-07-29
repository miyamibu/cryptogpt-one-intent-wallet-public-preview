#!/usr/bin/env python3
"""Fail closed if any review-register ID disappears from the traceability matrix."""
from __future__ import annotations

import re
import sys

sys.dont_write_bytecode = True
from canonical_hashes import strict_load_json
from package_metadata import ROOT, load_package_metadata


def main() -> int:
    metadata = load_package_metadata()
    document = strict_load_json(ROOT / "tests/coverage-matrix-v1.json")
    errors: list[str] = []
    if document.get("releaseVersion") != metadata.version or document.get("status") != "LOCAL_TRACEABILITY_NOT_RELEASE_EVIDENCE":
        errors.append("coverage matrix is not bound to the current local-only package")
    loophole_text = (ROOT / "24_KNOWN_LOOPHOLE_REGISTER.md").read_text(encoding="utf-8")
    expected_loopholes = set(re.findall(r"^\|\s*([A-Z][A-Z0-9-]*-\d{3})\s*\|", loophole_text, re.MULTILINE))
    invariant_text = (ROOT / "25_SECURITY_INVARIANTS.md").read_text(encoding="utf-8")
    expected_invariants = {f"INV-{value:03d}" for value in map(int, re.findall(r"^(\d+)\.\s", invariant_text, re.MULTILINE))}
    regressions = strict_load_json(ROOT / "tests/loophole-regression-cases.json").get("cases", [])
    expected_regressions = {case.get("id") for case in regressions}
    rows = document.get("rows", [])
    ids = [row.get("id") for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("coverage matrix IDs must be unique")
    expected = expected_loopholes | expected_invariants | expected_regressions
    if set(ids) != expected:
        errors.append(f"coverage matrix ID set drift: missing={sorted(expected - set(ids))[:10]}, extra={sorted(set(ids) - expected)[:10]}")
    counts = document.get("counts", {})
    expected_counts = {
        "knownLoopholes": len(expected_loopholes),
        "securityInvariants": len(expected_invariants),
        "regressionCases": len(expected_regressions),
        "rows": len(expected),
    }
    if counts != expected_counts:
        errors.append(f"coverage matrix counts drift: expected={expected_counts}, actual={counts}")
    for row in rows:
        if not row.get("runner") or row.get("productionEvidence") is not False:
            errors.append(f"coverage row is missing runner or false production boundary: {row.get('id')}")
        if row.get("executionStatus") not in {"DOCUMENT_ONLY", "FIXTURE_PRESENT_NO_PER_CASE_DISPATCH"}:
            errors.append(f"coverage row has an unknown execution status: {row.get('id')}")
    if errors:
        print("COVERAGE MATRIX VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("COVERAGE MATRIX VALIDATION PASSED")
    print(f"Rows: {len(rows)} (known loopholes={len(expected_loopholes)}, invariants={len(expected_invariants)}, regressions={len(expected_regressions)})")
    print("Executable per-ID evidence: NOT PROVIDED; rows remain explicit blockers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
