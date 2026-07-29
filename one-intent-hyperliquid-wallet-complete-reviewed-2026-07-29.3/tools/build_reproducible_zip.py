#!/usr/bin/env python3
from __future__ import annotations

import argparse
import stat
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
from archive_policy import EXPECTED_ASCII_ZIP_FLAGS
from package_metadata import ROOT, load_package_metadata
from secure_tree import snapshot

EXPECTED_COMMENT = b"Operationalization design package; production writes disabled until signed gates pass."


def package_files() -> list[Path]:
    return [ROOT / record.path for record in snapshot(ROOT)]


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
        for path in paths:
            rel = path.relative_to(ROOT).as_posix()
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
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(output)
    print(f"Files: {len(paths)}")
    print(f"Root: {metadata.root_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
