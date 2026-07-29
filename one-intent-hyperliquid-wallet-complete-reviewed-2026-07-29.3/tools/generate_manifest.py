#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from artifact_io import json_bytes, text_bytes, write_or_check
from package_metadata import ROOT, load_package_metadata
from secure_tree import snapshot

EXCLUDE = {"manifest.json", "SHA256SUMS.txt"}


def build_manifest_bytes() -> tuple[bytes, tuple]:
    metadata = load_package_metadata()
    records = snapshot(ROOT, exclude=EXCLUDE)
    manifest = {
        "schemaVersion": "2.0",
        "package": metadata.package,
        "version": metadata.version,
        "rootName": metadata.root_name,
        "generatedAt": metadata.deterministic_build_timestamp,
        "hashAlgorithm": "SHA-256",
        "excludes": sorted(EXCLUDE),
        "files": [
            {"path": record.path, "size": record.size, "sha256": record.sha256}
            for record in records
        ],
    }
    return json_bytes(manifest), records


def build_checksum_bytes(manifest_bytes: bytes, records: tuple) -> bytes:
    digests = {record.path: record.sha256 for record in records}
    digests["manifest.json"] = hashlib.sha256(manifest_bytes).hexdigest()
    lines = [f"{digests[rel]}  {rel}" for rel in sorted(digests)]
    return text_bytes("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or verify deterministic manifest/checksum artifacts.")
    parser.add_argument("--check", action="store_true", help="compare expected bytes and do not modify the package")
    args = parser.parse_args()
    metadata = load_package_metadata()
    manifest_bytes, records = build_manifest_bytes()
    checksum_bytes = build_checksum_bytes(manifest_bytes, records)
    write_or_check(ROOT / "manifest.json", manifest_bytes, check=args.check, label="manifest.json")
    write_or_check(ROOT / "SHA256SUMS.txt", checksum_bytes, check=args.check, label="SHA256SUMS.txt")
    print(("VERIFIED" if args.check else "GENERATED") + f" manifest for {len(records)} files")
    print(f"Package: {metadata.root_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
