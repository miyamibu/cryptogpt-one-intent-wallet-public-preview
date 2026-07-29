#!/usr/bin/env python3
"""Generate an explicit traceability matrix for every large review register."""
from __future__ import annotations

import argparse
import re
import sys

sys.dont_write_bytecode = True
from artifact_io import json_bytes, write_or_check
from canonical_hashes import strict_load_json
from package_metadata import ROOT, load_package_metadata


METADATA = load_package_metadata()
OUTPUT = ROOT / "tests/coverage-matrix-v1.json"


def build_matrix() -> dict[str, object]:
    loophole_text = (ROOT / "24_KNOWN_LOOPHOLE_REGISTER.md").read_text(encoding="utf-8")
    loopholes = re.findall(r"^\|\s*([A-Z][A-Z0-9-]*-\d{3})\s*\|", loophole_text, re.MULTILINE)
    invariant_text = (ROOT / "25_SECURITY_INVARIANTS.md").read_text(encoding="utf-8")
    invariant_numbers = [int(value) for value in re.findall(r"^(\d+)\.\s", invariant_text, re.MULTILINE)]
    regressions = strict_load_json(ROOT / "tests/loophole-regression-cases.json").get("cases", [])
    rows: list[dict[str, object]] = []
    for item in loopholes:
        rows.append({
            "id": item,
            "kind": "KNOWN_LOOPHOLE",
            "source": "24_KNOWN_LOOPHOLE_REGISTER.md",
            "runner": "adversarial_audit.py",
            "executionStatus": "DOCUMENT_ONLY",
            "evidencePath": None,
            "productionEvidence": False,
        })
    for number in invariant_numbers:
        rows.append({
            "id": f"INV-{number:03d}",
            "kind": "SECURITY_INVARIANT",
            "source": "25_SECURITY_INVARIANTS.md",
            "runner": "adversarial_audit.py",
            "executionStatus": "DOCUMENT_ONLY",
            "evidencePath": None,
            "productionEvidence": False,
        })
    for case in regressions:
        rows.append({
            "id": case.get("id"),
            "kind": "LOOPHOLE_REGRESSION_CASE",
            "source": "tests/loophole-regression-cases.json",
            "runner": "adversarial_audit.py",
            "executionStatus": "FIXTURE_PRESENT_NO_PER_CASE_DISPATCH",
            "evidencePath": None,
            "productionEvidence": False,
        })
    return {
        "schemaVersion": "1.0",
        "releaseVersion": METADATA.version,
        "status": "LOCAL_TRACEABILITY_NOT_RELEASE_EVIDENCE",
        "counts": {
            "knownLoopholes": len(loopholes),
            "securityInvariants": len(invariant_numbers),
            "regressionCases": len(regressions),
            "rows": len(rows),
        },
        "rows": rows,
        "limitations": [
            "The matrix makes every register item visible and prevents an omitted ID from looking covered.",
            "DOCUMENT_ONLY and FIXTURE_PRESENT_NO_PER_CASE_DISPATCH are not executable security proof.",
            "Per-case dispatch, property testing, mutation score, fuzz campaign, and independent review remain separate gates.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    write_or_check(OUTPUT, json_bytes(build_matrix()), check=args.check, label=OUTPUT.relative_to(ROOT).as_posix())
    print("COVERAGE MATRIX " + ("VERIFIED" if args.check else "GENERATED"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
