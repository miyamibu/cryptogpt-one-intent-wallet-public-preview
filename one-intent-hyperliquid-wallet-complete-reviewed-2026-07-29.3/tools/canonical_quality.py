"""Deterministic property and fuzz-smoke checks for the shared canonical core."""
from __future__ import annotations

import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

from shared.canonical import (
    CanonicalizationError,
    UnsafeNumberError,
    canonical_bytes,
    canonical_hash,
    decimal_string,
    strict_loads,
)


def run_property_checks() -> dict[str, object]:
    cases = 0
    for index in range(128):
        value = {
            "amount": f"{index}.{index % 100:02d}",
            "flags": [index % 2 == 0, None, f"case-{index}"],
            "nested": {"b": index, "a": "固定"},
        }
        encoded = canonical_bytes(value)
        reparsed = strict_loads(encoded.decode("utf-8"))
        if canonical_bytes(reparsed) != encoded:
            raise AssertionError(f"canonical idempotence failed at {index}")
        reordered = {"nested": value["nested"], "flags": value["flags"], "amount": value["amount"]}
        if canonical_bytes(reordered) != encoded:
            raise AssertionError(f"object key ordering failed at {index}")
        if canonical_hash("property-v1", value) != canonical_hash("property-v1", reparsed):
            raise AssertionError(f"hash stability failed at {index}")
        cases += 3

    for raw in ("0", "1", "1.00", "9007199254740991.123", "0.00000000000000000000000000000000000001"):
        decimal_string(raw)
        cases += 1
    for raw in ("01", "1e2", "-1", "1." , "1." + "0" * 39):
        try:
            decimal_string(raw)
        except CanonicalizationError:
            cases += 1
        else:
            raise AssertionError(f"invalid decimal accepted: {raw}")
    try:
        strict_loads('{"amount":9007199254740992}')
    except UnsafeNumberError:
        cases += 1
    else:
        raise AssertionError("unsafe integer accepted")
    return {
        "status": "PASS",
        "propertyCases": cases,
        "properties": ["canonical_idempotence", "object_key_order_independence", "domain_hash_stability", "decimal_boundaries"],
        "productionEvidence": False,
    }


def run_fuzz_smoke() -> dict[str, object]:
    state = 0xC0DEC0DE
    accepted = 0
    rejected = 0
    for index in range(256):
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        number = state % 10_000
        if index % 4 == 0:
            raw = f'{{"value":{number}}}'
        elif index % 4 == 1:
            raw = f'{{"value":{number}e2}}'
        elif index % 4 == 2:
            raw = '{"a":1,"a":2}'
        else:
            raw = f'{{"value":"case-{number}"}}'
        try:
            strict_loads(raw)
        except (CanonicalizationError, UnicodeError, ValueError):
            rejected += 1
        else:
            accepted += 1
    return {
        "status": "PASS",
        "iterations": accepted + rejected,
        "accepted": accepted,
        "rejected": rejected,
        "unexpectedCrashes": 0,
        "mode": "deterministic-bounded-fuzz-smoke",
        "productionEvidence": False,
    }
