#!/usr/bin/env python3
from __future__ import annotations

import html.parser
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True
from package_metadata import ROOT

MD_LINK = re.compile(r"!?\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+['\"][^'\"]*['\"])?\s*\)")
MD_REFERENCE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(?:<([^>]+)>|(\S+))", re.MULTILINE)
MD_AUTOLINK = re.compile(r"<([A-Za-z][A-Za-z0-9+.-]*:[^<>\s]+)>")
FENCE_LINE = re.compile(r"^\s*(`{3,}|~{3,})")
UNSAFE_SCHEMES = {"javascript", "data", "vbscript", "file"}


class LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            key = key.lower()
            if value and key in {"href", "src"}:
                self.links.append(value)
            if value and key == "id":
                self.ids.append(value)


def strip_fenced_code(text: str) -> tuple[str, bool]:
    output: list[str] = []
    opener: str | None = None
    for line in text.splitlines(keepends=True):
        match = FENCE_LINE.match(line)
        if match:
            marker = match.group(1)
            if opener is None:
                opener = marker
            elif marker[0] == opener[0] and len(marker) >= len(opener):
                opener = None
            output.append("\n" if line.endswith("\n") else "")
        elif opener is None:
            output.append(line)
        else:
            output.append("\n" if line.endswith("\n") else "")
    return "".join(output), opener is not None


def local_target(source: Path, raw: str) -> tuple[Path | None, str]:
    raw = raw.strip().strip("<>")
    parts = urlsplit(raw)
    if parts.scheme.lower() in UNSAFE_SCHEMES:
        raise ValueError(f"unsafe URI scheme: {parts.scheme}")
    if parts.scheme or parts.netloc or raw.startswith("//"):
        return None, parts.fragment
    path_part = unquote(parts.path)
    target = source if not path_part else (source.parent / path_part).resolve()
    return target, unquote(parts.fragment)


def html_ids(path: Path) -> set[str]:
    parser = LinkParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return set(parser.ids)


def parse_html_links(text: str) -> tuple[list[str], list[str]]:
    parser = LinkParser()
    parser.feed(text)
    parser.close()
    return parser.links, parser.ids


def main() -> int:
    errors: list[str] = []
    html_id_cache: dict[Path, set[str]] = {}
    for source in sorted(ROOT.rglob("*")):
        if not source.is_file() or source.suffix.lower() not in {".md", ".html"}:
            continue
        text = source.read_text(encoding="utf-8", errors="strict")
        try:
            if source.suffix.lower() == ".md":
                scan_text, unclosed = strip_fenced_code(text)
                if unclosed:
                    errors.append(f"unclosed Markdown fence: {source.relative_to(ROOT)}")
                links = [a or b for a, b in MD_LINK.findall(scan_text)]
                links += [a or b for a, b in MD_REFERENCE.findall(scan_text)]
                links += MD_AUTOLINK.findall(scan_text)
                raw_links, raw_ids = parse_html_links(scan_text)
                links += raw_links
                duplicates = sorted({value for value in raw_ids if raw_ids.count(value) > 1})
                for value in duplicates:
                    errors.append(f"duplicate raw-HTML id in Markdown: {source.relative_to(ROOT)}#{value}")
            else:
                links, ids = parse_html_links(text)
                duplicates = sorted({value for value in ids if ids.count(value) > 1})
                for value in duplicates:
                    errors.append(f"duplicate HTML id: {source.relative_to(ROOT)}#{value}")
                html_id_cache[source.resolve()] = set(ids)
        except Exception as exc:
            errors.append(f"markup parse failure: {source.relative_to(ROOT)}: {exc}")
            continue

        for raw in dict.fromkeys(links):
            try:
                target, fragment = local_target(source.resolve(), raw)
            except ValueError as exc:
                errors.append(f"unsafe link: {source.relative_to(ROOT)} -> {raw}: {exc}")
                continue
            if target is None:
                continue
            try:
                target.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(f"path escapes package: {source.relative_to(ROOT)} -> {raw}")
                continue
            if not target.exists():
                errors.append(f"broken local link: {source.relative_to(ROOT)} -> {raw}")
                continue
            if fragment and target.is_file() and target.suffix.lower() == ".html":
                ids = html_id_cache.get(target)
                if ids is None:
                    ids = html_ids(target)
                    html_id_cache[target] = ids
                if fragment not in ids:
                    errors.append(f"broken HTML fragment: {source.relative_to(ROOT)} -> {raw}")
    if errors:
        print("LOCAL LINK/MARKUP CHECK FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("LOCAL LINK/MARKUP CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
