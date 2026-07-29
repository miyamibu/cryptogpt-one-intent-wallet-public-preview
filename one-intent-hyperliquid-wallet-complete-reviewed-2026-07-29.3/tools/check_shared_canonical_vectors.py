#!/usr/bin/env python3
"""Execute the shared canonical bytes/hash vector against the reference core."""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True
from canonical_hashes import strict_load_json
from package_metadata import ROOT
from shared.canonical import (
    DuplicateKeyError,
    NonNFCError,
    UnsafeNumberError,
    canonical_bytes,
    canonical_hash,
    strict_loads,
)


def expected_error(exc: Exception) -> str:
    if isinstance(exc, DuplicateKeyError):
        return "REJECT_DUPLICATE_KEY"
    if isinstance(exc, NonNFCError):
        return "REJECT_NON_NFC"
    if isinstance(exc, UnsafeNumberError):
        if "exponent" in str(exc):
            return "REJECT_EXPONENT"
        if "negative zero" in str(exc):
            return "REJECT_NEGATIVE_ZERO"
        return "REJECT_INTEGER_RANGE"
    return "REJECT_OTHER_CANONICAL_ERROR"


def main() -> int:
    document = strict_load_json(ROOT / "shared/canonical-vectors-v1.json")
    errors: list[str] = []
    if document.get("schemaVersion") != "shared-canonical-v1" or document.get("status") != "EXECUTABLE_CROSS_LANGUAGE_VECTOR":
        errors.append("shared vector document is not executable/bound to shared-canonical-v1")
    cases = document.get("cases", [])
    if not isinstance(cases, list) or len(cases) < 7:
        errors.append("shared canonical vector set is unexpectedly small")
    for case in cases:
        case_id = case.get("id", "<missing>")
        try:
            value = strict_loads(case["input"])
            if case.get("expectedError") is not None:
                errors.append(f"{case_id}: expected rejection but input was accepted")
                continue
            actual_bytes = canonical_bytes(value).hex()
            actual_hash = canonical_hash(case["domain"], value)
            if actual_bytes != case.get("canonicalBytesHex"):
                errors.append(f"{case_id}: canonical bytes drift")
            if actual_hash != case.get("sha256"):
                errors.append(f"{case_id}: canonical hash drift")
        except Exception as exc:
            expected = case.get("expectedError")
            if expected is None:
                errors.append(f"{case_id}: unexpected rejection: {exc}")
            elif expected_error(exc) != expected:
                errors.append(f"{case_id}: expected {expected}, actual {expected_error(exc)}")
    if errors:
        print("SHARED CANONICAL VECTOR VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("SHARED CANONICAL VECTOR VALIDATION PASSED")
    print(f"Cases: {len(cases)}")
    print("Python reference and cross-language expected bytes/hash: PASS")
    print("Native build/device proof: NOT PROVIDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
