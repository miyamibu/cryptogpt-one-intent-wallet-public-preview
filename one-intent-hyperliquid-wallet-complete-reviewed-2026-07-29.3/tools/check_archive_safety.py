#!/usr/bin/env python3
from __future__ import annotations

import os
import stat
import sys
import unicodedata
from pathlib import Path

sys.dont_write_bytecode = True
from archive_policy import MAX_ENTRIES, MAX_SINGLE_UNCOMPRESSED, MAX_TOTAL_UNCOMPRESSED, member_name_problems
from package_metadata import ROOT, load_package_metadata

PROHIBITED_NAMES = {
    ".env", ".env.local", ".npmrc", ".pypirc", ".netrc", "id_rsa", "id_ed25519",
    "credentials.json", "service-account.json", "known_hosts", "authorized_keys",
}
PROHIBITED_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".jks", ".keystore", ".mobileprovision"}


def main() -> int:
    errors: list[str] = []
    seen: dict[str, str] = {}
    paths = sorted(ROOT.rglob("*"), key=lambda p: p.relative_to(ROOT).as_posix())
    if len(paths) > MAX_ENTRIES:
        errors.append(f"too many package paths: {len(paths)} > {MAX_ENTRIES}")
    total = 0
    files = 0
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        if path.is_symlink():
            errors.append(f"symlink is prohibited: {rel}")
            continue
        problems = member_name_problems(rel, is_directory=path.is_dir())
        for problem in problems:
            errors.append(f"unsafe/non-portable path ({problem}): {rel}")
        key = unicodedata.normalize("NFC", rel).casefold()
        if key in seen and seen[key] != rel:
            errors.append(f"case/Unicode path collision: {seen[key]} <> {rel}")
        seen[key] = rel
        try:
            st = path.lstat()
        except OSError as exc:
            errors.append(f"cannot stat path {rel}: {exc}")
            continue
        kind = stat.S_IFMT(st.st_mode)
        if kind not in {stat.S_IFREG, stat.S_IFDIR}:
            errors.append(f"special filesystem object prohibited: {rel}")
        if stat.S_ISREG(st.st_mode) and st.st_mode & 0o6000:
            errors.append(f"setuid/setgid bit prohibited on regular file: {rel}")
        if st.st_mode & 0o002:
            errors.append(f"world-writable path prohibited: {rel}")
        if path.is_file():
            files += 1
            total += st.st_size
            if st.st_size > MAX_SINGLE_UNCOMPRESSED:
                errors.append(f"file exceeds package size limit: {rel}")
            if path.name.lower() in {name.lower() for name in PROHIBITED_NAMES} or path.suffix.lower() in PROHIBITED_SUFFIXES:
                errors.append(f"secret/key-container filename prohibited: {rel}")
            if path.suffix.lower() != ".py" and st.st_mode & 0o111:
                errors.append(f"unexpected executable bit on non-Python file: {rel}")
    if total > MAX_TOTAL_UNCOMPRESSED:
        errors.append(f"package total bytes exceed limit: {total}")
    try:
        load_package_metadata()
    except Exception as exc:
        errors.append(f"build metadata/root identity invalid: {exc}")
    if errors:
        print("ARCHIVE SAFETY CHECK FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("ARCHIVE SAFETY CHECK PASSED")
    print(f"Paths checked: {len(paths)}")
    print(f"Files: {files}")
    print(f"Bytes: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
