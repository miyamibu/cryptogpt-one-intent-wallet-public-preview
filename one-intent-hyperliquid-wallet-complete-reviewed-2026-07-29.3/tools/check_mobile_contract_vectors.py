#!/usr/bin/env python3
"""Validate the platform-neutral offline review contract vector.

This is a conformance fixture for Android and Swift implementers. It is not a
native build, a UI test, or an authorization proof.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from package_metadata import ROOT


EXPECTED = {
    "ambiguous-draft": ("BLOCKED_AMBIGUITIES", "disabled"),
    "resolved-unconfirmed": ("BLOCKED_EXPLICIT_CONFIRMATION_REQUIRED", "disabled"),
    "resolved-confirmed": ("READY_FOR_LOCAL_FINAL_REVIEW", "enabled"),
    "ambiguous-confirmed": ("INVALID_CONTRACT", "disabled"),
}


def classify(source: str, interpretation: str, ambiguities: list[str], confirmed: bool) -> tuple[str, str]:
    if (
        not source.strip()
        or not interpretation.strip()
        or any(not value.strip() for value in ambiguities)
        or len(ambiguities) != len(set(ambiguities))
        or (confirmed and ambiguities)
    ):
        return "INVALID_CONTRACT", "disabled"
    if ambiguities:
        return "BLOCKED_AMBIGUITIES", "disabled"
    if not confirmed:
        return "BLOCKED_EXPLICIT_CONFIRMATION_REQUIRED", "disabled"
    return "READY_FOR_LOCAL_FINAL_REVIEW", "enabled"


def main() -> int:
    path = ROOT / "shared/mobile-review-contract-v1.tsv"
    rows: list[list[str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if not row or row[0].startswith("#"):
                continue
            rows.append(row)
    errors: list[str] = []
    if {row[0] for row in rows} != set(EXPECTED):
        errors.append("mobile contract vector case set drift")
    for row in rows:
        if len(row) != 7:
            errors.append(f"{row[0] if row else '<empty>'}: expected seven TSV fields")
            continue
        case_id, source, interpretation, ambiguity_text, confirmed_text, expected_reason, expected_action = row
        ambiguities = [] if not ambiguity_text else ambiguity_text.split("|")
        if confirmed_text not in {"true", "false"}:
            errors.append(f"{case_id}: confirmation must be true or false")
            continue
        actual_reason, actual_action = classify(source, interpretation, ambiguities, confirmed_text == "true")
        if (actual_reason, actual_action) != (expected_reason, expected_action):
            errors.append(f"{case_id}: expected={expected_reason}/{expected_action}, actual={actual_reason}/{actual_action}")
        if case_id in EXPECTED and (expected_reason, expected_action) != EXPECTED[case_id]:
            errors.append(f"{case_id}: canonical expected result drift")
    if errors:
        print("MOBILE CONTRACT VECTOR VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("MOBILE CONTRACT VECTOR VALIDATION PASSED")
    print(f"Cases: {len(rows)}")
    print("Scope: offline review contract only; native/device/authorization proof: NOT PROVIDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
