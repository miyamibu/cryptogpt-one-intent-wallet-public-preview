#!/usr/bin/env python3
"""Fail-closed package-tree traversal and deterministic tree snapshots."""
from __future__ import annotations

import hashlib
import os
import stat
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from archive_policy import MAX_ENTRIES, MAX_TOTAL_UNCOMPRESSED, member_name_problems


@dataclass(frozen=True)
class FileRecord:
    path: str
    mode: int
    size: int
    sha256: str


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise ValueError(f"hash target is not a regular file: {path}")
        for chunk in iter(lambda: os.read(descriptor, 1024 * 1024), b""):
            digest.update(chunk)
    finally:
        os.close(descriptor)
    return digest.hexdigest()


def _scan(root: Path, current: Path, records: list[FileRecord], seen: dict[str, str]) -> None:
    with os.scandir(current) as entries:
        for entry in sorted(entries, key=lambda item: item.name):
            path = Path(entry.path)
            rel = path.relative_to(root).as_posix()
            # A working checkout may contain Git's administrative worktree
            # metadata. It is never a package input and must not be traversed
            # (it can contain arbitrary worktree names and control files).
            if rel == ".git" or rel.startswith(".git/"):
                continue
            problems = member_name_problems(rel, is_directory=entry.is_dir(follow_symlinks=False))
            if problems:
                raise ValueError(f"unsafe package path {rel!r}: {problems}")
            folded = unicodedata.normalize("NFC", rel).casefold()
            previous = seen.get(folded)
            if previous is not None:
                raise ValueError(f"case/Unicode package-path collision: {previous!r} <> {rel!r}")
            seen[folded] = rel
            st = entry.stat(follow_symlinks=False)
            mode = st.st_mode
            if stat.S_ISLNK(mode):
                raise ValueError(f"symlink prohibited: {rel}")
            if stat.S_ISDIR(mode):
                # Directory execute bits are necessary for traversal. Host setgid is not inherited into ZIP metadata.
                if mode & stat.S_IWOTH:
                    raise ValueError(f"world-writable directory prohibited: {rel}")
                _scan(root, path, records, seen)
                continue
            if not stat.S_ISREG(mode):
                raise ValueError(f"special filesystem object prohibited: {rel} ({oct(mode)})")
            if st.st_nlink != 1:
                raise ValueError(f"hard-linked file prohibited: {rel} (nlink={st.st_nlink})")
            if mode & (stat.S_ISUID | stat.S_ISGID | stat.S_ISVTX):
                raise ValueError(f"special permission bits prohibited on file: {rel}")
            if mode & (stat.S_IWGRP | stat.S_IWOTH):
                raise ValueError(f"group/world-writable file prohibited: {rel}")
            if "__pycache__" in path.parts or path.suffix.lower() in {".pyc", ".pyo"}:
                raise ValueError(f"generated Python debris prohibited: {rel}")
            records.append(
                FileRecord(
                    path=rel,
                    mode=stat.S_IMODE(mode),
                    size=st.st_size,
                    sha256=file_sha256(path),
                )
            )


def snapshot(root: Path, *, exclude: Iterable[str] = ()) -> tuple[FileRecord, ...]:
    requested_root = Path(root)
    requested_stat = requested_root.lstat()
    if stat.S_ISLNK(requested_stat.st_mode):
        raise ValueError(f"package root must be a real directory: {requested_root}")
    root = requested_root.resolve(strict=True)
    root_stat = root.lstat()
    if not stat.S_ISDIR(root_stat.st_mode):
        raise ValueError(f"package root must be a real directory: {root}")
    records: list[FileRecord] = []
    _scan(root, root, records, {})
    excluded = set(exclude)
    records = [record for record in records if record.path not in excluded]
    records.sort(key=lambda record: record.path)
    if len(records) > MAX_ENTRIES:
        raise ValueError(f"package has too many files: {len(records)} > {MAX_ENTRIES}")
    total = sum(record.size for record in records)
    if total > MAX_TOTAL_UNCOMPRESSED:
        raise ValueError(f"package total size exceeds limit: {total} > {MAX_TOTAL_UNCOMPRESSED}")
    return tuple(records)


def digest_records(records: Iterable[FileRecord]) -> str:
    digest = hashlib.sha256()
    for record in records:
        rel = record.path.encode("utf-8")
        digest.update(len(rel).to_bytes(4, "big"))
        digest.update(rel)
        digest.update(record.mode.to_bytes(4, "big"))
        digest.update(record.size.to_bytes(8, "big"))
        digest.update(bytes.fromhex(record.sha256))
    return digest.hexdigest()


def tree_digest(root: Path, *, exclude: Iterable[str] = ()) -> str:
    return digest_records(snapshot(root, exclude=exclude))


def compare_snapshots(before: Iterable[FileRecord], after: Iterable[FileRecord]) -> list[str]:
    left = {record.path: record for record in before}
    right = {record.path: record for record in after}
    errors: list[str] = []
    for rel in sorted(set(left) - set(right)):
        errors.append(f"deleted: {rel}")
    for rel in sorted(set(right) - set(left)):
        errors.append(f"added: {rel}")
    for rel in sorted(set(left) & set(right)):
        if left[rel] != right[rel]:
            errors.append(f"changed: {rel}")
    return errors
