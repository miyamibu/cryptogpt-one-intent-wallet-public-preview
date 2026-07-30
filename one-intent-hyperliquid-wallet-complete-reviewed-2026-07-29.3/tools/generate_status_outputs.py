#!/usr/bin/env python3
"""Generate and verify the single local status-manifest output."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/status-manifest.v2.json"
JSON_OUTPUT = ROOT / "delivery/STATUS_MANIFEST.json"
MD_OUTPUT = ROOT / "delivery/STATUS_MANIFEST.md"
GENERATED = {CONFIG, JSON_OUTPUT, MD_OUTPUT}
DERIVED_PREFIXES = (
    "delivery/",
    "release/",
    "tests/",
)
DERIVED_FILES = {"manifest.json", "SHA256SUMS.txt", "FINAL_AUDIT_REPORT.md", "VALIDATION_REPORT.md"}


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _tree_digest() -> str:
    digest = hashlib.sha256()
    files = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT).as_posix()
        if not path.is_file() or path in GENERATED or ".git" in path.parts:
            continue
        if relative in DERIVED_FILES or relative.startswith(DERIVED_PREFIXES):
            continue
        files.append(path)
    files.sort()
    for path in files:
        relative = path.relative_to(ROOT).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big")); digest.update(relative)
        digest.update(len(content).to_bytes(8, "big")); digest.update(content)
    return "sha256:" + digest.hexdigest()


def _build() -> dict[str, Any]:
    manifest = json.loads(CONFIG.read_text(encoding="utf-8"))
    if manifest.get("productionWriteEnabled") is not False or manifest.get("mainnetEnabled") is not False:
        raise SystemExit("status manifest must remain fail-closed")
    if manifest.get("status") != "BLOCKED_NOT_OPERATIONAL":
        raise SystemExit("status manifest must remain BLOCKED_NOT_OPERATIONAL")
    source_commit = manifest.get("sourceCommit")
    if source_commit is not None and (
        not isinstance(source_commit, str)
        or len(source_commit) not in {40, 64}
        or any(character not in "0123456789abcdef" for character in source_commit)
    ):
        raise SystemExit("sourceCommit must be null or an explicit lowercase commit digest")
    manifest["sourceTreeDigest"] = _tree_digest()
    unsigned = dict(manifest)
    unsigned["artifactDigest"] = None
    manifest["artifactDigest"] = "sha256:" + hashlib.sha256(_canonical(unsigned)).hexdigest()
    return manifest


def _markdown(manifest: dict[str, Any]) -> str:
    profile = manifest["profile"]
    rows = [
        f"- release: `{manifest['releaseId']}`",
        f"- status: `{manifest['status']}`",
        f"- productionWriteEnabled: `{str(manifest['productionWriteEnabled']).lower()}`",
        f"- mainnetEnabled: `{str(manifest['mainnetEnabled']).lower()}`",
        f"- gates: `{profile['passedGates']}/{profile['mandatoryGates']}` passed",
        f"- claims: `{profile['acceptedClaims']}/{profile['requiredClaims']}` accepted",
        f"- sourceCommit: `{manifest['sourceCommit'] or 'unavailable'}`",
        f"- sourceTreeDigest: `{manifest['sourceTreeDigest']}`",
        f"- artifactDigest: `{manifest['artifactDigest']}`",
    ]
    return "# Status Manifest\n\n" + "\n".join(rows) + "\n\n> This is local design/evidence status only. It is not production approval.\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest = _build()
    expected_json = _canonical(manifest)
    expected_md = _markdown(manifest).encode("utf-8")
    if args.check:
        actual_json = JSON_OUTPUT.read_bytes() if JSON_OUTPUT.exists() else b""
        actual_md = MD_OUTPUT.read_bytes() if MD_OUTPUT.exists() else b""
        if actual_json != expected_json or actual_md != expected_md:
            print("status outputs are stale")
            return 1
        print("status outputs are current")
        return 0
    JSON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_bytes(expected_json)
    MD_OUTPUT.write_bytes(expected_md)
    print(f"generated {JSON_OUTPUT.relative_to(ROOT)}")
    print(f"generated {MD_OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
