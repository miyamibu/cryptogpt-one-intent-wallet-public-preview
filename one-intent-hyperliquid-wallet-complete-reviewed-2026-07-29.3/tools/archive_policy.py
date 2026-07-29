#!/usr/bin/env python3
"""Portable path and archive policy shared by filesystem and ZIP validators."""
from __future__ import annotations

import re
import unicodedata
from pathlib import PurePosixPath

MAX_ENTRIES = 10_000
MAX_SINGLE_UNCOMPRESSED = 256 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED = 1024 * 1024 * 1024
MAX_COMPRESSION_RATIO = 1_000
MAX_PATH_CHARACTERS = 240
MAX_PATH_DEPTH = 24
EXPECTED_ASCII_ZIP_FLAGS = 0
WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
WINDOWS_FORBIDDEN = set('<>:"\\|?*')
BIDI_CONTROLS = {
    "\u061c", "\u200e", "\u200f", "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
    "\u2066", "\u2067", "\u2068", "\u2069",
}
ASCII_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


def component_problem(component: str) -> str | None:
    if component in {"", ".", ".."}:
        return "empty/dot path component"
    if component != component.strip():
        return "leading or trailing whitespace"
    if not component.isascii():
        return "non-ASCII path component"
    if component.endswith((" ", ".")):
        return "trailing space or dot"
    if len(component.encode("utf-8")) > 255:
        return "path component exceeds 255 UTF-8 bytes"
    if any(ch in WINDOWS_FORBIDDEN for ch in component):
        return "Windows-forbidden character or alternate data stream separator"
    if ASCII_CONTROL_RE.search(component) or any(ch in BIDI_CONTROLS for ch in component):
        return "control or bidirectional override character"
    if unicodedata.normalize("NFC", component) != component:
        return "component is not NFC-normalized"
    base = component.split(".", 1)[0].upper()
    if base in WINDOWS_RESERVED:
        return "Windows reserved device name"
    if component in {".DS_Store", "Thumbs.db", "desktop.ini"}:
        return "platform metadata file"
    return None


def member_name_problems(name: str, *, is_directory: bool = False) -> list[str]:
    problems: list[str] = []
    if not isinstance(name, str) or not name:
        return ["empty member name"]
    if "\\" in name:
        problems.append("backslash path separator")
    if len(name) > MAX_PATH_CHARACTERS:
        problems.append(f"path exceeds {MAX_PATH_CHARACTERS} characters")
    if name.startswith("/") or PurePosixPath(name).is_absolute():
        problems.append("absolute path")
    if unicodedata.normalize("NFC", name) != name:
        problems.append("path is not NFC-normalized")
    raw = name[:-1] if is_directory and name.endswith("/") else name
    parts = raw.split("/")
    if len(parts) > MAX_PATH_DEPTH:
        problems.append(f"path depth exceeds {MAX_PATH_DEPTH}")
    for component in parts:
        problem = component_problem(component)
        if problem:
            problems.append(f"{problem}: {component!r}")
    return problems
