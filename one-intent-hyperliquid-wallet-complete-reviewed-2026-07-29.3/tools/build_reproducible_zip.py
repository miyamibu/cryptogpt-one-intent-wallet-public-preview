#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import stat
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
from archive_policy import EXPECTED_ASCII_ZIP_FLAGS
from package_metadata import ROOT, load_package_metadata
from secure_tree import snapshot

EXPECTED_COMMENT = b"Operationalization design package; production writes disabled until signed gates pass."


def package_files() -> list[tuple[str, bytes]]:
    """Read the snapshotted tree through no-follow descriptors before zipping."""
    files: list[tuple[str, bytes]] = []
    for record in snapshot(ROOT):
        path = ROOT / record.path
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            file_stat = os.fstat(descriptor)
            if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_nlink != 1:
                raise RuntimeError(f"package input changed to a non-regular file: {record.path}")
            chunks = list(iter(lambda: os.read(descriptor, 1024 * 1024), b""))
        finally:
            os.close(descriptor)
        data = b"".join(chunks)
        if len(data) != record.size or hashlib.sha256(data).hexdigest() != record.sha256:
            raise RuntimeError(f"package input changed during ZIP build: {record.path}")
        files.append((record.path, data))
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a sorted, metadata-stable ZIP with exactly one root directory.")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    metadata = load_package_metadata()
    paths = package_files()
    output = args.output.resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise SystemExit("output ZIP must be outside the package root")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=True) as archive:
        archive.comment = EXPECTED_COMMENT
        for rel, data in paths:
            info = zipfile.ZipInfo(f"{metadata.root_name}/{rel}", date_time=metadata.zip_datetime)
            info.create_system = 3
            info.create_version = 20
            info.extract_version = 20
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.internal_attr = 0
            info.compress_type = zipfile.ZIP_DEFLATED
            info.flag_bits = EXPECTED_ASCII_ZIP_FLAGS
            info.extra = b""
            info.comment = b""
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(output)
    print(f"Files: {len(paths)}")
    print(f"Root: {metadata.root_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
