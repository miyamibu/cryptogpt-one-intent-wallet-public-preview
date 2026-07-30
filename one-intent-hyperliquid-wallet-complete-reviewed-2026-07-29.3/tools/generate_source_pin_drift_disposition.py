#!/usr/bin/env python3
"""Classify all 25 public source acquisitions without auto-promoting a pin."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from artifact_io import json_bytes, write_or_check
from package_metadata import ROOT

PREVIOUS = ROOT / "delivery/evidence/source-pins/SOURCE_PIN_ACQUISITION_20260729.json"
CURRENT = ROOT / "delivery/evidence/source-pins/SOURCE_PIN_ACQUISITION_CURRENT.json"
OUTPUT = ROOT / "delivery/evidence/source-pins/SOURCE_PIN_DRIFT_DISPOSITION.json"
EXPECTED = 25


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(entry: dict[str, Any]) -> tuple[object, object]:
    return (entry.get("name"), entry.get("sourceUrl"))


def observed(entry: dict[str, Any], field: str) -> object:
    value = entry.get(field)
    return value.get("value") if isinstance(value, dict) else None


def build() -> dict[str, Any]:
    previous = load(PREVIOUS)
    current = load(CURRENT)
    old = previous.get("sources")
    new = current.get("sources")
    if not isinstance(old, list) or not isinstance(new, list) or len(old) != EXPECTED or len(new) != EXPECTED:
        raise ValueError("both source acquisitions must contain exactly 25 sources")
    if [identity(item) for item in old] != [identity(item) for item in new]:
        raise ValueError("source acquisition identity/order drift")

    rows: list[dict[str, Any]] = []
    for prior, latest in zip(old, new, strict=True):
        if latest.get("status") != "AVAILABLE":
            disposition = "UNAVAILABLE"
            reason = "Current official source retrieval did not succeed."
        elif prior.get("status") != "AVAILABLE":
            disposition = "REVIEW_REQUIRED"
            reason = "The previous acquisition was unavailable; there is no comparable approved byte baseline."
        elif observed(prior, "publisherVersion") != observed(latest, "publisherVersion") or observed(prior, "publisherCommit") != observed(latest, "publisherCommit"):
            disposition = "REVIEW_REQUIRED"
            reason = "Publisher version or commit identity changed."
        elif prior.get("contentSha256") != latest.get("contentSha256"):
            disposition = "REVIEW_REQUIRED"
            reason = "Exact HTTP response bytes changed without a publisher identity change."
        else:
            disposition = "UNCHANGED"
            reason = "Exact response hash and observed publisher identity are unchanged."
        rows.append({
            "index": latest.get("index"),
            "name": latest.get("name"),
            "category": latest.get("category"),
            "sourceUrl": latest.get("sourceUrl"),
            "disposition": disposition,
            "reason": reason,
            "previousContentSha256": prior.get("contentSha256"),
            "currentContentSha256": latest.get("contentSha256"),
            "previousPublisherVersion": observed(prior, "publisherVersion"),
            "currentPublisherVersion": observed(latest, "publisherVersion"),
            "previousPublisherCommit": observed(prior, "publisherCommit"),
            "currentPublisherCommit": observed(latest, "publisherCommit"),
            "canonicalPinUpdated": False,
            "productionGo": False,
        })

    counts = {status: sum(row["disposition"] == status for row in rows) for status in ("UNCHANGED", "REVIEW_REQUIRED", "UNAVAILABLE")}
    return {
        "schemaVersion": "1.0",
        "evidenceType": "SOURCE_PIN_DRIFT_DISPOSITION",
        "generatedAt": current.get("generatedAt"),
        "decision": "FAIL_CLOSED_PENDING_SEMANTIC_REVIEW" if counts["REVIEW_REQUIRED"] or counts["UNAVAILABLE"] else "NO_DRIFT_OBSERVED",
        "productionGo": False,
        "canonicalPinsModified": False,
        "inputs": [
            {"path": PREVIOUS.relative_to(ROOT).as_posix(), "sha256": digest(PREVIOUS)},
            {"path": CURRENT.relative_to(ROOT).as_posix(), "sha256": digest(CURRENT)},
        ],
        "summary": {"total": len(rows), **counts},
        "sources": rows,
        "limitations": [
            "Response-byte equality is not a legal, protocol, or security approval.",
            "Any changed or unavailable source remains blocked until a named independent reviewer approves exact semantic content.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build()
    if value["summary"]["total"] != EXPECTED or value["productionGo"] is not False:
        raise ValueError("unsafe source-pin disposition summary")
    write_or_check(OUTPUT, json_bytes(value), check=args.check, label=OUTPUT.relative_to(ROOT).as_posix())
    summary = value["summary"]
    print(f"SOURCE PIN DRIFT DISPOSITION VERIFIED total={summary['total']} unchanged={summary['UNCHANGED']} review={summary['REVIEW_REQUIRED']} unavailable={summary['UNAVAILABLE']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
