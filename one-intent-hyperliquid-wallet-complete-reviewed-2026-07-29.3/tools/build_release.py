#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
from package_metadata import ROOT, load_package_metadata
from secure_tree import tree_digest


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_sha256_sidecar(output: Path, digest: str) -> Path:
    """Publish the archive checksum beside the exact archive atomically."""
    sidecar = output.with_name(output.name + ".sha256")
    staged = sidecar.with_name(sidecar.name + ".tmp")
    staged.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    os.replace(staged, sidecar)
    return sidecar


def run(script: str, *args: str) -> None:
    command = [sys.executable, str(ROOT / "tools" / script), *args]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})


def assert_tree(expected: str, phase: str) -> None:
    actual = tree_digest(ROOT)
    if actual != expected:
        raise RuntimeError(f"source tree changed during {phase}: {expected} != {actual}")


def main() -> int:
    metadata = load_package_metadata()
    parser = argparse.ArgumentParser(
        description=(
            "Explicitly prepare derived evidence, perform non-mutating validation, freeze the source tree, "
            "build twice, require byte equality, safely clean-extract and fully revalidate, then atomically publish one ZIP."
        )
    )
    parser.add_argument("output", nargs="?", type=Path, default=ROOT.parent / f"{metadata.root_name}.zip")
    args = parser.parse_args()
    output = args.output.resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise SystemExit("output ZIP must be outside the package root")
    if output.name != f"{metadata.root_name}.zip":
        raise SystemExit(f"release ZIP filename must be {metadata.root_name}.zip")
    output.parent.mkdir(parents=True, exist_ok=True)

    run("prepare_release_artifacts.py")
    # Keep the release orchestrator independently fail-closed even if the
    # preparation implementation changes later. This second pass is pure,
    # isolated, and must leave the prepared source tree byte-for-byte unchanged.
    run("run_full_validation.py")
    validated_tree = tree_digest(ROOT)

    with tempfile.TemporaryDirectory(prefix="wallet-release-double-build-", dir=output.parent) as temp_dir:
        temp = Path(temp_dir)
        first = temp / f"{metadata.root_name}.first.zip"
        second = temp / f"{metadata.root_name}.second.zip"
        run("build_reproducible_zip.py", str(first))
        assert_tree(validated_tree, "first ZIP build")
        run("build_reproducible_zip.py", str(second))
        assert_tree(validated_tree, "second ZIP build")
        first_hash = sha256(first)
        second_hash = sha256(second)
        if first_hash != second_hash or first.read_bytes() != second.read_bytes():
            raise RuntimeError(f"deterministic double-build mismatch: {first_hash} != {second_hash}")
        run("verify_zip.py", str(first))
        assert_tree(validated_tree, "first clean-extract verification")
        run("verify_zip.py", str(second))
        assert_tree(validated_tree, "second clean-extract verification")
        staged = output.with_name(output.name + ".tmp")
        staged.unlink(missing_ok=True)
        shutil.copyfile(first, staged)
        os.replace(staged, output)

    run("verify_zip.py", str(output))
    assert_tree(validated_tree, "final release verification")
    output_hash = sha256(output)
    sidecar = write_sha256_sidecar(output, output_hash)
    print("RELEASE BUILD PASSED")
    print("Hidden validation repair/bypass: NOT AVAILABLE")
    print("Preparation and validation are separate: PASS")
    print("Source tree immutable after freeze: PASS")
    print("Deterministic double-build: PASS")
    print("Clean-extract full non-mutating validation: PASS")
    print(f"ZIP: {output}")
    print(f"SHA-256: {output_hash}")
    print(f"SHA-256 sidecar: {sidecar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
