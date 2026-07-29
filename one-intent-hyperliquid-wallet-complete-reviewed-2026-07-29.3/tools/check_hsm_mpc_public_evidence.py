#!/usr/bin/env python3
"""Validate only redacted HSM/MPC evidence; never load secret material."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
from canonical_hashes import strict_load_json


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "delivery/evidence/security/HSM_MPC_PUBLIC_EVIDENCE.json"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_KEY_PARTS = ("privatekey", "mnemonic", "seedphrase", "secretvalue", "hsmshare", "mpcshare")


def _walk_keys(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower().replace("_", "")
            if any(part in key_text for part in _FORBIDDEN_KEY_PARTS):
                found.append(f"{path}.{key}")
            found.extend(_walk_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_walk_keys(child, f"{path}[{index}]"))
    return found


def check(path: Path, *, require_configured: bool) -> list[str]:
    errors: list[str] = []
    document = strict_load_json(path)
    if not isinstance(document, dict):
        return ["HSM/MPC evidence must be an object"]
    forbidden = _walk_keys(document)
    if forbidden:
        errors.append("secret-bearing key names are not permitted: " + ", ".join(forbidden))
    if document.get("secrets") != {
        "privateMaterialAccessed": False,
        "privateMaterialPresentInPackage": False,
        "sharesExported": False,
    }:
        errors.append("secret boundary must explicitly remain false")
    status = document.get("status")
    if status not in {"NOT_PROVISIONED", "PUBLIC_EVIDENCE_VERIFIED"}:
        errors.append("status must be NOT_PROVISIONED or PUBLIC_EVIDENCE_VERIFIED")
    ceremony = document.get("ceremony")
    if not isinstance(ceremony, dict) or ceremony.get("required") is not True:
        errors.append("two-person ceremony must be required")
    if status == "NOT_PROVISIONED":
        if document.get("provider") is not None or document.get("publicKeyIds") != []:
            errors.append("NOT_PROVISIONED evidence must not contain provider or key IDs")
        if require_configured:
            errors.append("configured HSM/MPC public evidence is required by strict mode")
    else:
        if not isinstance(document.get("provider"), str) or not document["provider"]:
            errors.append("verified public evidence requires provider name")
        if not isinstance(document.get("publicKeyIds"), list) or not document["publicKeyIds"]:
            errors.append("verified public evidence requires public key IDs")
        for field in ("tenantReferenceSha256", "attestationSha256"):
            if not isinstance(document.get(field), str) or not _SHA256.fullmatch(document[field]):
                errors.append(f"verified public evidence requires {field}")
        if not isinstance(ceremony, dict) or ceremony.get("completed") is not True or ceremony.get("independentOperators", 0) < 2 or ceremony.get("reviewerSignatures", 0) < 2:
            errors.append("verified public evidence requires two independent operators and two reviewer signatures")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--require-configured", action="store_true")
    args = parser.parse_args()
    try:
        errors = check(args.path, require_configured=args.require_configured)
    except Exception as exc:
        print(f"HSM/MPC public evidence check ERROR: {exc}", file=sys.stderr)
        return 1
    if errors:
        print("HSM/MPC public evidence check BLOCKED/ERROR:")
        for error in errors:
            print(f"- {error}")
        return 1
    document = strict_load_json(args.path)
    print(f"HSM/MPC public evidence check PASS: status={document['status']}")
    if document["status"] == "NOT_PROVISIONED":
        print("HSM/MPC operational readiness: BLOCKED_NOT_OPERATIONAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
