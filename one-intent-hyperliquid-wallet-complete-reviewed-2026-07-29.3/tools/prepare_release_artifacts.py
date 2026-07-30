#!/usr/bin/env python3
"""Explicitly prepare derived release artifacts, then run pure validation.

This is the only canonical mutating preparation step. `run_full_validation.py`
never repairs or rewrites evidence.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from package_metadata import ROOT


def run(script: str, *args: str) -> None:
    command = [sys.executable, str(ROOT / "tools" / script), *args]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})


def purge_generated_python_debris() -> None:
    removed: list[str] = []
    for path in sorted(ROOT.rglob("__pycache__"), key=lambda value: len(value.parts), reverse=True):
        rel = path.relative_to(ROOT).as_posix()
        if path.is_symlink():
            raise RuntimeError(f"refusing to follow symlink while removing generated debris: {rel}")
        shutil.rmtree(path)
        removed.append(rel)
    for pattern in ("*.pyc", "*.pyo"):
        for path in sorted(ROOT.rglob(pattern)):
            if path.is_symlink() or not path.is_file():
                raise RuntimeError(f"unexpected generated-debris object: {path.relative_to(ROOT)}")
            removed.append(path.relative_to(ROOT).as_posix())
            path.unlink()
    if removed:
        print(f"Explicit preparation removed {len(removed)} generated Python item(s)", flush=True)


def main() -> int:
    if sys.version_info < (3, 10):
        print("Python 3.10 or newer is required", file=sys.stderr)
        return 2
    purge_generated_python_debris()
    run("test_validation_harness.py")
    run("update_example_hashes.py")
    run("test_prototype.py")
    run("test_start_here.py")
    run("generate_coverage_matrix.py")
    run("generate_source_pin_drift_disposition.py")
    run("generate_release_contract_artifacts.py")
    run("generate_operational_readiness_report.py")
    run("generate_current_validation_evidence.py")
    run("generate_reports.py")
    run("generate_status_outputs.py")
    # Refresh release metadata after current validation evidence exists. The
    # final phase is written only after a successful pure validation pass below.
    run("generate_release_contract_artifacts.py")
    run("generate_operationalization_evidence_binding.py", "--write")
    run("generate_manifest.py")
    run("run_full_validation.py")
    run("generate_release_contract_artifacts.py", "--phase", "validated")
    run("generate_operationalization_evidence_binding.py", "--write")
    run("generate_status_outputs.py")
    run("generate_manifest.py")
    run("run_full_validation.py")
    print("RELEASE ARTIFACT PREPARATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
