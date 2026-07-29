#!/usr/bin/env python3
"""Deterministic artifact serialization and explicit write-vs-check behavior."""
from __future__ import annotations

import difflib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False, allow_nan=False) + "\n").encode("utf-8")


def text_bytes(value: str) -> bytes:
    return value.encode("utf-8")


def _diff(expected: bytes, actual: bytes, path: Path) -> str:
    try:
        expected_text = expected.decode("utf-8").splitlines(keepends=True)
        actual_text = actual.decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        return f"binary artifact differs: {path} (expected {len(expected)} bytes, found {len(actual)} bytes)"
    diff = "".join(
        difflib.unified_diff(
            actual_text,
            expected_text,
            fromfile=f"{path} (stored)",
            tofile=f"{path} (expected)",
            n=3,
        )
    )
    return diff[:12000] or f"artifact differs: {path}"


def write_or_check(path: Path, expected: bytes, *, check: bool, label: str | None = None) -> None:
    """Write atomically during preparation, or compare without mutating during validation."""
    name = label or path.as_posix()
    if check:
        if not path.is_file():
            raise RuntimeError(f"missing generated artifact in --check mode: {name}")
        actual = path.read_bytes()
        if actual != expected:
            raise RuntimeError(f"generated artifact is stale: {name}\n{_diff(expected, actual, path)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(expected)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
