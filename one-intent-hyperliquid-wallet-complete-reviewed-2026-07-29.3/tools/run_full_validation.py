#!/usr/bin/env python3
"""Run the complete validation suite without allowing validators to alter the source tree.

The public entry point validates an exact byte-for-byte isolated copy.  The internal
runner additionally snapshots that copy after every validator, including failure
paths.  This prevents an accidental mutating checker from deleting or rewriting
release evidence in the working package.
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
from package_metadata import ROOT, load_package_metadata
from secure_tree import FileRecord, compare_snapshots, digest_records, snapshot

_INTERNAL_ENV = "ONE_INTENT_VALIDATION_ISOLATED_COPY"

_VALIDATORS: tuple[tuple[str, ...], ...] = (
    ("test_validation_harness.py",),
    ("check_python_sources.py",),
    ("test_python_unit_suite.py",),
    ("test_canonical_properties.py",),
    ("test_canonical_fuzz.py",),
    ("run_local_sandbox.py", "self-test"),
    ("update_example_hashes.py", "--check"),
    ("test_prototype.py", "--check"),
    ("test_start_here.py", "--check"),
    ("generate_coverage_matrix.py", "--check"),
    ("generate_release_contract_artifacts.py", "--check"),
    ("check_toolchain_lock.py",),
    ("check_shared_canonical_vectors.py",),
    ("check_coverage_matrix.py",),
    ("generate_current_validation_evidence.py", "--check"),
    ("generate_operational_readiness_report.py", "--check"),
    ("generate_reports.py", "--check"),
    ("check_release_contract.py",),
    ("check_mobile_contract_vectors.py",),
    ("check_operational_readiness.py",),
    ("test_operational_readiness_positive.py",),
    ("test_operational_readiness_negative.py",),
    ("check_runtime_authorization.py",),
    ("test_runtime_authorization_positive.py",),
    ("test_runtime_authorization_negative.py",),
    ("check_plain_japanese.py",),
    ("check_archive_safety.py",),
    ("check_security_hygiene.py",),
    ("check_links_and_markdown.py",),
    ("adversarial_audit.py",),
    ("generate_manifest.py", "--check"),
    ("validate_package.py",),
)


def _print_mutations(*, phase: str, before: tuple[FileRecord, ...], after: tuple[FileRecord, ...]) -> None:
    print(f"VALIDATION MUTATED THE ISOLATED PACKAGE DURING {phase}", file=sys.stderr)
    for mutation in compare_snapshots(before, after)[:200]:
        print(f"- {mutation}", file=sys.stderr)
    print(f"before={digest_records(before)}", file=sys.stderr)
    print(f"after={digest_records(after)}", file=sys.stderr)


def _run_internal() -> int:
    """Run each validator against the isolated copy and check immutability after every step."""
    initial = snapshot(ROOT)
    initial_digest = digest_records(initial)
    print(f"NON-MUTATING VALIDATION INPUT TREE: {initial_digest}", flush=True)

    for spec in _VALIDATORS:
        script, *args = spec
        before_step = snapshot(ROOT)
        command = [sys.executable, str(ROOT / "tools" / script), *args]
        print("+", " ".join(command), flush=True)
        proc = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", _INTERNAL_ENV: "1"},
        )
        after_step = snapshot(ROOT)
        mutations = compare_snapshots(before_step, after_step)
        if mutations:
            _print_mutations(phase=script, before=before_step, after=after_step)
            return 1
        if proc.returncode:
            print(f"VALIDATOR FAILED WITHOUT MUTATING THE PACKAGE: {script} (exit {proc.returncode})", file=sys.stderr)
            return proc.returncode if 0 < proc.returncode < 126 else 1

    final = snapshot(ROOT)
    if compare_snapshots(initial, final) or digest_records(final) != initial_digest:
        _print_mutations(phase="the full internal pipeline", before=initial, after=final)
        return 1
    print("FULL NON-MUTATING VALIDATION PIPELINE PASSED", flush=True)
    print(f"UNCHANGED ISOLATED TREE: {initial_digest}", flush=True)
    return 0


def _copy_exact_tree(records: tuple[FileRecord, ...], destination: Path) -> None:
    destination.mkdir(mode=0o755, parents=False, exist_ok=False)
    for record in records:
        source = ROOT / record.path
        target = destination / record.path
        target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        # Open with exclusive creation so a pre-existing or injected path is never overwritten.
        with source.open("rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
            dst.flush()
            os.fsync(dst.fileno())
        os.chmod(target, record.mode & 0o777)


def _run_isolated() -> int:
    metadata = load_package_metadata()
    original_before = snapshot(ROOT)
    original_digest = digest_records(original_before)
    print(f"SOURCE TREE PROTECTED BY ISOLATED VALIDATION: {original_digest}", flush=True)

    proc: subprocess.CompletedProcess[bytes] | None = None
    with tempfile.TemporaryDirectory(prefix="one-intent-validation-sandbox-") as temp_dir:
        sandbox_root = Path(temp_dir) / metadata.root_name
        _copy_exact_tree(original_before, sandbox_root)
        copied = snapshot(sandbox_root)
        if copied != original_before:
            print("ISOLATED COPY DOES NOT MATCH THE SOURCE TREE", file=sys.stderr)
            for mutation in compare_snapshots(original_before, copied)[:200]:
                print(f"- {mutation}", file=sys.stderr)
            return 1
        command = [sys.executable, str(sandbox_root / "tools" / "run_full_validation.py")]
        proc = subprocess.run(
            command,
            cwd=sandbox_root,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", _INTERNAL_ENV: "1"},
        )
        sandbox_after = snapshot(sandbox_root)
        if compare_snapshots(copied, sandbox_after):
            _print_mutations(phase="isolated validation", before=copied, after=sandbox_after)
            return 1

    original_after = snapshot(ROOT)
    if compare_snapshots(original_before, original_after) or digest_records(original_after) != original_digest:
        print("ISOLATED VALIDATION CHANGED THE SOURCE PACKAGE", file=sys.stderr)
        for mutation in compare_snapshots(original_before, original_after)[:200]:
            print(f"- {mutation}", file=sys.stderr)
        return 1
    if proc is None or proc.returncode:
        return 1 if proc is None else proc.returncode
    print("SOURCE TREE REMAINED UNCHANGED", flush=True)
    print(f"UNCHANGED SOURCE TREE: {original_digest}", flush=True)
    return 0


def main() -> int:
    if sys.version_info < (3, 10):
        print("Python 3.10 or newer is required", file=sys.stderr)
        return 2
    # The environment marker is set only for the exact isolated copy.  Internal
    # mode does not skip a validator; it merely prevents recursive cloning.
    if os.environ.get(_INTERNAL_ENV) == "1":
        return _run_internal()
    return _run_isolated()


if __name__ == "__main__":
    raise SystemExit(main())
