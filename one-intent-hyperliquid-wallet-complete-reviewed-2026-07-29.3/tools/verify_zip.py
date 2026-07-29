#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import stat
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

sys.dont_write_bytecode = True
from archive_policy import (
    EXPECTED_ASCII_ZIP_FLAGS,
    MAX_COMPRESSION_RATIO,
    MAX_ENTRIES,
    MAX_SINGLE_UNCOMPRESSED,
    MAX_TOTAL_UNCOMPRESSED,
    member_name_problems,
)
from canonical_hashes import strict_load_json_bytes, strict_load_json
from package_metadata import ROOT, load_package_metadata
from secure_tree import tree_digest as secure_tree_digest

EXPECTED_COMMENT = b"Operationalization design package; production writes disabled until signed gates pass."
STATIC_SCRIPTS = ("run_full_validation.py",)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_digest(root: Path) -> str:
    return secure_tree_digest(root)


def parse_manifest_and_sums(root: Path, errors: list[str]) -> None:
    try:
        metadata = strict_load_json(root / "config/build-metadata.json")
        manifest = strict_load_json(root / "manifest.json")
    except Exception as exc:
        errors.append(f"strict metadata/manifest parse failed: {exc}")
        return
    source_meta = load_package_metadata()
    expected_meta = {
        "package": source_meta.package,
        "version": source_meta.version,
        "deterministicBuildTimestamp": source_meta.deterministic_build_timestamp,
        "nativeBuildsIncluded": False,
        "liveCredentialsIncluded": False,
        "mainnetEnabled": False,
        "productionReadyClaimAllowed": False,
    }
    for key, value in expected_meta.items():
        if metadata.get(key) != value:
            errors.append(f"archive build metadata {key} mismatch")
    expected_header = {
        "schemaVersion": "2.0",
        "package": source_meta.package,
        "version": source_meta.version,
        "rootName": source_meta.root_name,
        "generatedAt": source_meta.deterministic_build_timestamp,
        "hashAlgorithm": "SHA-256",
        "excludes": ["SHA256SUMS.txt", "manifest.json"],
    }
    for key, value in expected_header.items():
        if manifest.get(key) != value:
            errors.append(f"archive manifest {key} mismatch")
    entries = manifest.get("files", [])
    if not isinstance(entries, list):
        errors.append("archive manifest files is not an array")
        return
    expected: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "size", "sha256"}:
            errors.append("archive manifest entry shape invalid")
            continue
        rel = entry.get("path")
        if not isinstance(rel, str) or member_name_problems(rel):
            errors.append(f"archive manifest unsafe path: {rel!r}")
            continue
        if rel in expected:
            errors.append(f"archive manifest duplicate path: {rel}")
        expected[rel] = entry
        order.append(rel)
    if order != sorted(order):
        errors.append("archive manifest entries are not sorted")
    excluded = set(manifest.get("excludes", []))
    actual = {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file()
        and path.relative_to(root).as_posix() not in excluded
        and "__pycache__" not in path.parts
        and path.suffix.lower() not in {".pyc", ".pyo"}
    }
    if set(expected) != set(actual):
        errors.append("archive manifest file set differs after extraction")
    for rel, path in actual.items():
        entry = expected.get(rel)
        if entry and (entry.get("size") != path.stat().st_size or entry.get("sha256") != sha256(path)):
            errors.append(f"archive manifest mismatch: {rel}")

    sums: dict[str, str] = {}
    order = []
    try:
        lines = (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        errors.append(f"cannot read SHA256SUMS.txt: {exc}")
        return
    import re
    for index, line in enumerate(lines, 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            errors.append(f"malformed SHA256SUMS line {index}")
            continue
        digest, rel = match.groups()
        if member_name_problems(rel):
            errors.append(f"unsafe SHA256SUMS path: {rel!r}")
        if rel in sums:
            errors.append(f"duplicate checksum entry: {rel}")
        sums[rel] = digest
        order.append(rel)
    if order != sorted(order):
        errors.append("SHA256SUMS entries are not sorted")
    targets = {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file()
        and path.name != "SHA256SUMS.txt"
        and "__pycache__" not in path.parts
        and path.suffix.lower() not in {".pyc", ".pyo"}
    }
    if set(sums) != set(targets):
        errors.append("SHA256SUMS file set differs after extraction")
    for rel, path in targets.items():
        if sums.get(rel) != sha256(path):
            errors.append(f"SHA256SUMS mismatch: {rel}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reject unsafe/non-deterministic ZIPs, safely extract, verify every digest, and run immutable static validation."
    )
    parser.add_argument("zip_path", type=Path)
    args = parser.parse_args()
    zip_path = args.zip_path.resolve()
    errors: list[str] = []
    seen_raw: set[str] = set()
    seen_folded: dict[str, str] = {}
    top: set[str] = set()
    total_uncompressed = 0
    source_meta = load_package_metadata()

    try:
        zf = zipfile.ZipFile(zip_path)
    except (OSError, zipfile.BadZipFile) as exc:
        print(f"ZIP VERIFICATION FAILED\n- cannot open ZIP: {exc}")
        return 1

    with zf:
        infos = zf.infolist()
        names = [info.filename for info in infos]
        if not infos:
            errors.append("empty archive")
        if len(infos) > MAX_ENTRIES:
            errors.append(f"too many archive entries: {len(infos)} > {MAX_ENTRIES}")
        if names != sorted(names):
            errors.append("archive members are not lexicographically sorted")
        if zf.comment != EXPECTED_COMMENT:
            errors.append("deterministic release ZIP comment mismatch")
        for info in infos:
            name = info.filename
            if info.is_dir() or name.endswith("/"):
                errors.append(f"explicit directory member prohibited: {name}")
                continue
            problems = member_name_problems(name)
            for problem in problems:
                errors.append(f"unsafe ZIP member ({problem}): {name}")
            p = PurePosixPath(name)
            if not p.parts:
                errors.append(f"empty member path: {name!r}")
                continue
            top.add(p.parts[0])
            if name in seen_raw:
                errors.append(f"duplicate raw member name: {name}")
            seen_raw.add(name)
            folded = unicodedata.normalize("NFC", name).casefold()
            if folded in seen_folded:
                errors.append(f"duplicate/case/Unicode member collision: {seen_folded[folded]} <> {name}")
            seen_folded[folded] = name
            if info.flag_bits & 0x1:
                errors.append(f"encrypted member prohibited: {name}")
            if info.flag_bits != EXPECTED_ASCII_ZIP_FLAGS:
                errors.append(f"unexpected ZIP flags for ASCII-only member {name}: 0x{info.flag_bits:x}")
            if info.compress_type != zipfile.ZIP_DEFLATED:
                errors.append(f"unexpected compression method for {name}: {info.compress_type}")
            if info.create_system != 3:
                errors.append(f"unexpected create_system for {name}: {info.create_system}")
            if info.extra or info.comment:
                errors.append(f"extra per-entry metadata prohibited: {name}")
            mode = (info.external_attr >> 16) & 0xFFFF
            if mode != (stat.S_IFREG | 0o644):
                errors.append(f"unexpected archive mode for {name}: {oct(mode)}")
            if info.internal_attr != 0:
                errors.append(f"unexpected internal attributes for {name}")
            if info.date_time != source_meta.zip_datetime:
                errors.append(f"non-deterministic ZIP timestamp: {name} {info.date_time} != {source_meta.zip_datetime}")
            total_uncompressed += info.file_size
            if info.file_size > MAX_SINGLE_UNCOMPRESSED:
                errors.append(f"member exceeds uncompressed size limit: {name}")
            if info.file_size > 1024 * 1024:
                ratio = info.file_size / max(1, info.compress_size)
                if ratio > MAX_COMPRESSION_RATIO:
                    errors.append(f"suspicious compression ratio {ratio:.1f}: {name}")
        if total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
            errors.append(f"archive uncompressed total exceeds limit: {total_uncompressed}")
        if top != {source_meta.root_name}:
            errors.append(f"archive root mismatch: {sorted(top)} != {[source_meta.root_name]}")
        metadata_name = f"{source_meta.root_name}/config/build-metadata.json"
        if metadata_name not in seen_raw:
            errors.append("archive is missing build metadata")
        else:
            try:
                raw_metadata = strict_load_json_bytes(zf.read(metadata_name))
                if raw_metadata.get("package") != source_meta.package or raw_metadata.get("version") != source_meta.version:
                    errors.append("embedded build metadata identity mismatch")
            except Exception as exc:
                errors.append(f"embedded build metadata strict parse failed: {exc}")
        bad = zf.testzip()
        if bad:
            errors.append(f"CRC failure: {bad}")
        if errors:
            print("ZIP VERIFICATION FAILED")
            for error in errors:
                print(f"- {error}")
            return 1

        with tempfile.TemporaryDirectory(prefix="wallet-zip-verify-") as temp_dir:
            dest = Path(temp_dir)
            for info in infos:
                rel = PurePosixPath(info.filename)
                target = dest.joinpath(*rel.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info, "r") as src, target.open("xb") as out:
                    while True:
                        chunk = src.read(1024 * 1024)
                        if not chunk:
                            break
                        out.write(chunk)
                os.chmod(target, 0o644)
            root = dest / source_meta.root_name
            parse_manifest_and_sums(root, errors)
            before = tree_digest(root)
            if not errors:
                for script in STATIC_SCRIPTS:
                    proc = subprocess.run(
                        [sys.executable, str(root / "tools" / script)],
                        cwd=root,
                        text=True,
                        capture_output=True,
                        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                    )
                    if proc.returncode:
                        errors.append(f"clean-extract static validation failed in {script}:\n{proc.stdout}{proc.stderr}")
                        break
            after = tree_digest(root)
            if before != after:
                errors.append(f"clean-extract validation mutated the package tree: {before} != {after}")

    if errors:
        print("ZIP VERIFICATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("ZIP VERIFICATION PASSED")
    print(f"Entries: {len(infos)}")
    print(f"Uncompressed bytes: {total_uncompressed}")
    print(f"SHA-256: {sha256(zip_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
