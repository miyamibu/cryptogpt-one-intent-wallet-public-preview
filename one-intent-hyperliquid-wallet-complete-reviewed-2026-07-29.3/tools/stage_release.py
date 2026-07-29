#!/usr/bin/env python3
"""Stage this workspace into the canonical package root without mutating it.

The Desktop workspace is intentionally named for human use, while deterministic
release tooling requires ``<package>-<version>``. This command creates a new
staging directory outside the workspace, excludes OS metadata and stale derived
manifest/checksum files, and then runs the explicit preparation pipeline there.
It never deletes or renames the source workspace.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from canonical_hashes import strict_load_json
from package_metadata import ROOT


EXCLUDED_NAMES = {"manifest.json", "SHA256SUMS.txt", ".DS_Store", "DESKTOP_WORKSPACE_RELEASE_STATUS.json"}


def verify_desktop_workspace_status(*, canonical_root_name: str) -> None:
    status_path = ROOT / "DESKTOP_WORKSPACE_RELEASE_STATUS.json"
    if not status_path.is_file():
        raise SystemExit("missing DESKTOP_WORKSPACE_RELEASE_STATUS.json; refusing ambiguous Desktop distribution")
    status = strict_load_json(status_path)
    expected = {
        "status": "NON_CANONICAL_WORKSPACE",
        "workspaceRootName": ROOT.name,
        "canonicalPackageRootName": canonical_root_name,
        "distributionPolicy": "DISTRIBUTE_ONLY_EXTERNAL_STAGE_OR_ZIP",
        "manifestStatus": "NOT_AUTHORITATIVE",
        "checksumStatus": "NOT_AUTHORITATIVE",
    }
    for key, value in expected.items():
        if status.get(key) != value:
            raise SystemExit(f"Desktop workspace status drift: {key}")


def copy_tree(destination: Path) -> int:
    count = 0
    for source in sorted(ROOT.rglob("*")):
        relative = source.relative_to(ROOT)
        if any(part in {"__pycache__"} for part in relative.parts) or source.name in EXCLUDED_NAMES:
            continue
        target = destination / relative
        if source.is_symlink():
            raise RuntimeError(f"symlink is prohibited in release staging: {relative}")
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if not source.is_file() or source.suffix in {".pyc", ".pyo"}:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        os.chmod(target, source.stat().st_mode & 0o777)
        count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parent", type=Path, help="existing parent directory outside the workspace")
    parser.add_argument("--no-prepare", action="store_true", help="copy only; do not generate derived artifacts")
    args = parser.parse_args()

    metadata = strict_load_json(ROOT / "config/build-metadata.json")
    package = metadata["package"]
    version = metadata["version"]
    canonical_root_name = f"{package}-{version}"
    verify_desktop_workspace_status(canonical_root_name=canonical_root_name)
    destination = args.parent.resolve() / f"{package}-{version}"
    source_root = ROOT.resolve()
    try:
        destination.relative_to(source_root)
    except ValueError:
        pass
    else:
        raise SystemExit("release staging destination must be outside the workspace")
    if destination.exists():
        raise SystemExit(f"refusing to overwrite existing staging directory: {destination}")
    args.parent.resolve().mkdir(parents=True, exist_ok=True)
    destination.mkdir(mode=0o755)
    count = copy_tree(destination)
    if not args.no_prepare:
        command = [sys.executable, "-B", "tools/prepare_release_artifacts.py"]
        subprocess.run(command, cwd=destination, check=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    print(f"STAGED RELEASE ROOT: {destination}")
    print(f"SOURCE FILES COPIED: {count}")
    print(f"PREPARED: {str(not args.no_prepare).lower()}")
    print("SOURCE WORKSPACE CHANGED: false")
    print("DESKTOP MANIFEST/CHECKSUM: NON_AUTHORITATIVE (excluded from staged distribution)")
    print("DISTRIBUTION ROOT: canonical external stage or generated ZIP only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
