#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from artifact_io import json_bytes, write_or_check
from canonical_hashes import expected_hashes, source_text_hash, strict_load_json
from package_metadata import ROOT

CAPSULES = (
    "examples/execution-capsule-perp.json",
    "examples/execution-capsule-composite.json",
    "examples/execution-capsule-ios-saved-withdrawal.json",
)
AUTH_BINDINGS = (
    ("examples/execution-capsule-composite.json", "examples/authorization-envelope-protected-confirmation.json"),
    ("examples/execution-capsule-ios-saved-withdrawal.json", "examples/authorization-envelope-ios-app-attest.json"),
)


def updated_capsule(rel: str) -> dict:
    capsule = copy.deepcopy(strict_load_json(ROOT / rel))
    first = expected_hashes(capsule)
    presentation = capsule["authorizationPresentation"]
    prompt = presentation.get("promptText")
    if prompt is not None:
        fingerprint = first["semanticHash"][2:10].upper()
        if re.search(r"PLAN [0-9A-Fa-f]{8}", prompt):
            prompt = re.sub(r"PLAN [0-9A-Fa-f]{8}", f"PLAN {fingerprint}", prompt)
        elif "PLAN " not in prompt:
            prompt = prompt.rstrip() + f"; PLAN {fingerprint}"
        presentation["promptText"] = prompt
    hashes = expected_hashes(capsule)
    capsule["semanticHash"] = hashes["semanticHash"]
    capsule["renderReceiptHash"] = hashes["renderReceiptHash"]
    capsule["sourceStateHash"] = hashes["sourceStateHash"]
    presentation["promptTextHash"] = hashes["promptTextHash"]
    return capsule


def build_artifacts() -> dict[Path, bytes]:
    capsules = {rel: updated_capsule(rel) for rel in CAPSULES}
    artifacts: dict[Path, bytes] = {ROOT / rel: json_bytes(value) for rel, value in capsules.items()}
    for capsule_rel, auth_rel in AUTH_BINDINGS:
        capsule = capsules[capsule_rel]
        auth = copy.deepcopy(strict_load_json(ROOT / auth_rel))
        auth["semanticHash"] = capsule["semanticHash"]
        auth["renderReceiptHash"] = capsule["renderReceiptHash"]
        auth["sourceStateHash"] = capsule["sourceStateHash"]
        auth["promptTextHash"] = capsule["authorizationPresentation"]["promptTextHash"]
        artifacts[ROOT / auth_rel] = json_bytes(auth)

    action_rel = "examples/action-plan-btc-long.json"
    action = copy.deepcopy(strict_load_json(ROOT / action_rel))
    source_text = (ROOT / "examples/source-text-btc-long.txt").read_text(encoding="utf-8").rstrip("\n")
    action["sourceTextHashProfile"] = "ONE_INTENT_SOURCE_TEXT_HASH_V1"
    action["sourceTextHash"] = source_text_hash(source_text)
    artifacts[ROOT / action_rel] = json_bytes(action)
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or verify canonical hashes in JSON examples without hidden mutation.")
    parser.add_argument("--check", action="store_true", help="compare expected bytes and fail instead of writing")
    args = parser.parse_args()
    for path, expected in build_artifacts().items():
        write_or_check(path, expected, check=args.check, label=path.relative_to(ROOT).as_posix())
    print("CANONICAL EXAMPLE HASHES " + ("VERIFIED" if args.check else "UPDATED"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
