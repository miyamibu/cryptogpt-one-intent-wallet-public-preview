#!/usr/bin/env python3
"""Compile every tracked Python source in memory without creating bytecode."""
from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
from package_metadata import ROOT
from secure_tree import snapshot


def main() -> int:
    errors: list[str] = []
    checked = 0
    for record in snapshot(ROOT):
        if not record.path.endswith(".py"):
            continue
        path = ROOT / record.path
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, record.path, "exec", dont_inherit=True)
        except Exception as exc:
            errors.append(f"{record.path}: {exc}")
        checked += 1
    if errors:
        print("PYTHON SOURCE COMPILATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PYTHON SOURCE COMPILATION PASSED ({checked} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
