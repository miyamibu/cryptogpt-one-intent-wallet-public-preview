#!/usr/bin/env python3
"""Run the complete Python unittest suite as a mandatory release validator."""
from __future__ import annotations

import os
import subprocess
import sys

sys.dont_write_bytecode = True
from package_metadata import ROOT


def main() -> int:
    command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]
    proc = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if proc.returncode:
        print("PYTHON UNIT SUITE FAILED", file=sys.stderr)
        return proc.returncode if 0 < proc.returncode < 126 else 1
    print("PYTHON UNIT SUITE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
