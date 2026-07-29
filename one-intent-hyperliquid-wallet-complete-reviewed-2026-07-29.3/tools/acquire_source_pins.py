#!/usr/bin/env python3
"""Acquire secret-free evidence for the 25 canonical public source URLs.

The canonical SOURCE_PINS documents are read-only inputs.  This tool only writes
an evidence JSON document below delivery/evidence/source-pins/ and never treats
successful retrieval as production approval.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import html
import ipaddress
import json
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "release/SOURCE_PINS.json"
DEFAULT_OUTPUT = ROOT / "delivery/evidence/source-pins/SOURCE_PIN_ACQUISITION_CURRENT.json"
EXPECTED_SOURCE_COUNT = 25
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_BYTES = 16 * 1024 * 1024
DEFAULT_WORKERS = 4
USER_AGENT = "CryptoGPT-Source-Pin-Evidence/1.0 (public-read-only; no-auth)"

# Every canonical URL and every provider-specific metadata URL must remain on an
# official publisher host.  Redirects are checked against the same allowlist.
OFFICIAL_HOSTS = frozenset(
    {
        "api.github.com",
        "developer.android.com",
        "developer.apple.com",
        "developers.openai.com",
        "github.com",
        "hyperliquid.gitbook.io",
        "openai.com",
        "platform.openai.com",
        "raw.githubusercontent.com",
        "source.android.com",
        "support.google.com",
        "www.fsa.go.jp",
        "www.openai.com",
    }
)

SAFE_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/json,text/plain;q=0.9,*/*;q=0.1",
    "Accept-Encoding": "identity",
    "User-Agent": USER_AGENT,
}

VERSION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "json-ld-dateModified",
        re.compile(r'"dateModified"\s*:\s*"([^"\\]{4,100})"', re.IGNORECASE),
    ),
    (
        "meta-article-modified-time",
        re.compile(
            r'<meta[^>]+(?:property|name)=["\'](?:article:modified_time|dateModified|last-modified)'
            r'["\'][^>]+content=["\']([^"\']{4,100})["\']',
            re.IGNORECASE,
        ),
    ),
    (
        "meta-article-modified-time-reversed",
        re.compile(
            r'<meta[^>]+content=["\']([^"\']{4,100})["\'][^>]+'
            r'(?:property|name)=["\'](?:article:modified_time|dateModified|last-modified)["\']',
            re.IGNORECASE,
        ),
    ),
)

VISIBLE_VERSION_PATTERN = re.compile(
    r"\b(Last\s+updated|Updated|Effective|Page\s+updated)\s*[:\-]?\s*"
    r"([A-Z][a-z]{2,8}\s+\d{1,2},?\s+\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b",
    re.IGNORECASE,
)


class AcquisitionError(RuntimeError):
    """A safe, user-visible acquisition failure with no response body."""

    def __init__(
        self,
        message: str,
        *,
        http_status: int | None = None,
        final_url: str | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.final_url = final_url
        self.etag = etag
        self.last_modified = last_modified


@dataclass(frozen=True)
class FetchResult:
    requested_url: str
    final_url: str
    http_status: int
    retrieved_at: str
    body: bytes
    content_type: str | None
    etag: str | None
    last_modified: str | None


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def strict_json_load(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    if not isinstance(value, dict):
        raise ValueError("source-pin input must be a JSON object")
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_public_official_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() != "https":
        raise ValueError("only HTTPS URLs are permitted")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL credentials are prohibited")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("invalid URL port") from exc
    if port not in (None, 443):
        raise ValueError("only the default HTTPS port is permitted")
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        raise ValueError("URL host is missing")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("IP-literal URLs are prohibited")
    if host not in OFFICIAL_HOSTS:
        raise ValueError(f"host is not an approved official publisher: {host}")
    return host


class OfficialRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        absolute_url = urllib.parse.urljoin(req.full_url, newurl)
        validate_public_official_url(absolute_url)
        return super().redirect_request(req, fp, code, msg, headers, absolute_url)


OPENER = urllib.request.build_opener(OfficialRedirectHandler())


def safe_header(headers: Any, name: str) -> str | None:
    value = headers.get(name) if headers is not None else None
    if value is None:
        return None
    # Prevent control characters from entering the evidence JSON.
    return re.sub(r"[\x00-\x1f\x7f]+", " ", str(value)).strip()[:1024] or None


def read_limited(response: Any, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = response.read(min(64 * 1024, max_bytes + 1 - total))
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise AcquisitionError(f"response exceeded {max_bytes} byte limit")
        chunks.append(chunk)
    return b"".join(chunks)


def fetch_public_url(url: str, *, timeout: float, max_bytes: int, attempts: int = 2) -> FetchResult:
    validate_public_official_url(url)
    last_error: AcquisitionError | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(url, headers=SAFE_REQUEST_HEADERS, method="GET")
        try:
            with OPENER.open(request, timeout=timeout) as response:
                final_url = response.geturl()
                validate_public_official_url(final_url)
                status = int(response.status)
                body = read_limited(response, max_bytes)
                if status < 200 or status >= 300:
                    raise AcquisitionError(
                        f"HTTP {status}",
                        http_status=status,
                        final_url=final_url,
                        etag=safe_header(response.headers, "ETag"),
                        last_modified=safe_header(response.headers, "Last-Modified"),
                    )
                return FetchResult(
                    requested_url=url,
                    final_url=final_url,
                    http_status=status,
                    retrieved_at=utc_now(),
                    body=body,
                    content_type=safe_header(response.headers, "Content-Type"),
                    etag=safe_header(response.headers, "ETag"),
                    last_modified=safe_header(response.headers, "Last-Modified"),
                )
        except urllib.error.HTTPError as exc:
            final_url = exc.geturl() if hasattr(exc, "geturl") else url
            try:
                validate_public_official_url(final_url)
            except ValueError:
                final_url = None
            last_error = AcquisitionError(
                f"HTTP {exc.code} {exc.reason}"[:240],
                http_status=int(exc.code),
                final_url=final_url,
                etag=safe_header(exc.headers, "ETag"),
                last_modified=safe_header(exc.headers, "Last-Modified"),
            )
            if exc.code not in {408, 425, 429, 500, 502, 503, 504}:
                break
        except (urllib.error.URLError, TimeoutError, socket.timeout, ssl.SSLError) as exc:
            reason = getattr(exc, "reason", None)
            reason_name = type(reason).__name__ if reason is not None else type(exc).__name__
            last_error = AcquisitionError(f"network error: {reason_name}")
        except AcquisitionError as exc:
            last_error = exc
            break
        if attempt < attempts:
            time.sleep(float(attempt))
    assert last_error is not None
    raise last_error

def decode_text(result: FetchResult) -> str:
    charset = "utf-8"
    if result.content_type:
        match = re.search(r"charset=([A-Za-z0-9._-]+)", result.content_type, re.IGNORECASE)
        if match:
            charset = match.group(1)
    try:
        return result.body.decode(charset, errors="replace")
    except LookupError:
        return result.body.decode("utf-8", errors="replace")


def clean_observed_value(value: str) -> str | None:
    cleaned = html.unescape(re.sub(r"\s+", " ", value)).strip(" \t\r\n:;,-")
    return cleaned[:160] or None


def extract_publisher_version(result: FetchResult) -> dict[str, Any]:
    text = decode_text(result)
    for method, pattern in VERSION_PATTERNS:
        match = pattern.search(text)
        if match:
            value = clean_observed_value(match.group(1))
            if value:
                return {"status": "OBSERVED", "value": value, "method": method}

    # Strip scripts/styles and tags before matching visible publisher labels.
    visible = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    visible = html.unescape(re.sub(r"<[^>]+>", " ", visible))
    visible = re.sub(r"\s+", " ", visible)
    match = VISIBLE_VERSION_PATTERN.search(visible)
    if match:
        value = clean_observed_value(f"{match.group(1)} {match.group(2)}")
        if value:
            return {"status": "OBSERVED", "value": value, "method": "visible-update-label"}
    return {"status": "UNAVAILABLE", "value": None, "method": None}


def github_coordinates(url: str) -> dict[str, str] | None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.hostname != "github.com":
        return None
    parts = [urllib.parse.unquote(part) for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return None
    result = {"owner": parts[0], "repository": parts[1], "ref": "", "path": ""}
    if len(parts) >= 5 and parts[2] == "blob":
        result["ref"] = parts[3]
        result["path"] = "/".join(parts[4:])
    return result


def fetch_json(url: str, *, timeout: float, max_bytes: int) -> tuple[Any, FetchResult]:
    result = fetch_public_url(url, timeout=timeout, max_bytes=max_bytes)
    try:
        value = json.loads(result.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AcquisitionError("official metadata response was not valid JSON") from exc
    return value, result


def acquire_github_metadata(
    source_url: str, *, timeout: float, max_bytes: int
) -> dict[str, Any]:
    coordinates = github_coordinates(source_url)
    if coordinates is None:
        return {
            "publisherCommit": {"status": "NOT_APPLICABLE", "value": None, "evidenceUrl": None},
            "publisherVersion": None,
        }

    owner = urllib.parse.quote(coordinates["owner"], safe="")
    repository = urllib.parse.quote(coordinates["repository"], safe="")
    try:
        if coordinates["path"]:
            ref = urllib.parse.quote(coordinates["ref"], safe="")
            path = urllib.parse.quote(coordinates["path"], safe="/")
            api_url = (
                f"https://api.github.com/repos/{owner}/{repository}/commits"
                f"?sha={ref}&path={path}&per_page=1"
            )
            payload, evidence = fetch_json(api_url, timeout=timeout, max_bytes=max_bytes)
            if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
                raise AcquisitionError("GitHub returned no commit for the source path")
            commit = payload[0].get("sha")
        else:
            repo_url = f"https://api.github.com/repos/{owner}/{repository}"
            repo_payload, _ = fetch_json(repo_url, timeout=timeout, max_bytes=max_bytes)
            if not isinstance(repo_payload, dict) or not isinstance(repo_payload.get("default_branch"), str):
                raise AcquisitionError("GitHub repository metadata omitted default_branch")
            ref = urllib.parse.quote(repo_payload["default_branch"], safe="")
            api_url = f"https://api.github.com/repos/{owner}/{repository}/commits/{ref}"
            payload, evidence = fetch_json(api_url, timeout=timeout, max_bytes=max_bytes)
            if not isinstance(payload, dict):
                raise AcquisitionError("GitHub commit metadata was not an object")
            commit = payload.get("sha")
        if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
            raise AcquisitionError("GitHub commit metadata omitted a full commit SHA")

        version: dict[str, Any] | None = None
        if coordinates["repository"] == "hyperliquid-python-sdk" and not coordinates["path"]:
            raw_url = (
                f"https://raw.githubusercontent.com/{owner}/{repository}/{commit}/pyproject.toml"
            )
            raw = fetch_public_url(raw_url, timeout=timeout, max_bytes=max_bytes)
            match = re.search(
                rb"(?m)^version\s*=\s*[\"']([^\"'\r\n]{1,80})[\"']\s*$",
                raw.body,
            )
            if match:
                version = {
                    "status": "OBSERVED",
                    "value": match.group(1).decode("utf-8", errors="replace"),
                    "method": "pinned-pyproject-toml",
                    "evidenceUrl": raw.final_url,
                    "evidenceContentSha256": sha256_bytes(raw.body),
                }
        return {
            "publisherCommit": {
                "status": "OBSERVED",
                "value": commit,
                "evidenceUrl": evidence.final_url,
                "retrievedAt": evidence.retrieved_at,
                "httpStatus": evidence.http_status,
            },
            "publisherVersion": version,
        }
    except (AcquisitionError, ValueError) as exc:
        return {
            "publisherCommit": {
                "status": "UNAVAILABLE",
                "value": None,
                "evidenceUrl": None,
                "reason": str(exc)[:240],
            },
            "publisherVersion": None,
        }


def unavailable_entry(index: int, source: dict[str, Any], exc: Exception) -> dict[str, Any]:
    http_status = exc.http_status if isinstance(exc, AcquisitionError) else None
    final_url = exc.final_url if isinstance(exc, AcquisitionError) else None
    etag = exc.etag if isinstance(exc, AcquisitionError) else None
    last_modified = exc.last_modified if isinstance(exc, AcquisitionError) else None
    reason = str(exc)[:240] or type(exc).__name__
    commit_status = "UNAVAILABLE" if github_coordinates(source["url"]) is not None else "NOT_APPLICABLE"
    return {
        "index": index,
        "name": source["name"],
        "category": source["category"],
        "sourceUrl": source["url"],
        "status": "UNAVAILABLE",
        "httpStatus": http_status,
        "finalUrl": final_url,
        "retrievedAt": utc_now(),
        "contentSha256": None,
        "contentLengthBytes": None,
        "contentType": None,
        "etag": etag,
        "lastModified": last_modified,
        "publisherVersion": {"status": "UNAVAILABLE", "value": None, "method": None},
        "publisherCommit": {"status": commit_status, "value": None, "evidenceUrl": None},
        "unavailableReason": reason,
        "productionGo": False,
    }


def acquire_one(
    index: int,
    source: dict[str, Any],
    *,
    timeout: float,
    max_bytes: int,
) -> dict[str, Any]:
    try:
        result = fetch_public_url(source["url"], timeout=timeout, max_bytes=max_bytes)
        publisher_version = extract_publisher_version(result)
        github = acquire_github_metadata(source["url"], timeout=timeout, max_bytes=max_bytes)
        if github["publisherVersion"] is not None:
            publisher_version = github["publisherVersion"]
        return {
            "index": index,
            "name": source["name"],
            "category": source["category"],
            "sourceUrl": source["url"],
            "status": "AVAILABLE",
            "httpStatus": result.http_status,
            "finalUrl": result.final_url,
            "retrievedAt": result.retrieved_at,
            "contentSha256": sha256_bytes(result.body),
            "contentLengthBytes": len(result.body),
            "contentType": result.content_type,
            "etag": result.etag,
            "lastModified": result.last_modified,
            "publisherVersion": publisher_version,
            "publisherCommit": github["publisherCommit"],
            "unavailableReason": None,
            "productionGo": False,
        }
    except (AcquisitionError, ValueError, OSError) as exc:
        return unavailable_entry(index, source, exc)


def validate_sources(document: dict[str, Any]) -> list[dict[str, Any]]:
    sources = document.get("sources")
    if not isinstance(sources, list):
        raise ValueError("input sources must be an array")
    if len(sources) != EXPECTED_SOURCE_COUNT:
        raise ValueError(f"expected {EXPECTED_SOURCE_COUNT} sources, found {len(sources)}")
    names: set[str] = set()
    urls: set[str] = set()
    validated: list[dict[str, Any]] = []
    for index, value in enumerate(sources, start=1):
        if not isinstance(value, dict):
            raise ValueError(f"source {index} must be an object")
        name = value.get("name")
        category = value.get("category")
        url = value.get("url")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"source {index} has no valid name")
        if not isinstance(category, str) or not category.strip():
            raise ValueError(f"source {index} has no valid category")
        if not isinstance(url, str):
            raise ValueError(f"source {index} has no valid URL")
        validate_public_official_url(url)
        if name in names or url in urls:
            raise ValueError(f"source {index} duplicates a name or URL")
        names.add(name)
        urls.add(url)
        validated.append({"name": name, "category": category, "url": url})
    return validated


def ensure_output_scope(path: Path) -> Path:
    evidence_root = (ROOT / "delivery/evidence/source-pins").resolve()
    resolved = path.expanduser().resolve()
    if resolved.parent != evidence_root:
        raise ValueError(f"output must be directly below {evidence_root}")
    if resolved.suffix != ".json":
        raise ValueError("output must be a JSON file")
    return resolved


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n").encode("utf-8")
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def build_evidence(
    input_path: Path,
    sources: list[dict[str, Any]],
    *,
    timeout: float,
    max_bytes: int,
    workers: int,
) -> dict[str, Any]:
    started_at = utc_now()
    input_before = input_path.read_bytes()
    entries: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_by_index = {
            executor.submit(
                acquire_one,
                index,
                source,
                timeout=timeout,
                max_bytes=max_bytes,
            ): index
            for index, source in enumerate(sources, start=1)
        }
        for future in concurrent.futures.as_completed(future_by_index):
            index = future_by_index[future]
            try:
                entries.append(future.result())
            except Exception as exc:  # Defensive: one URL must not erase evidence for the other 24.
                entries.append(unavailable_entry(index, sources[index - 1], exc))
    entries.sort(key=lambda value: value["index"])
    input_after = input_path.read_bytes()
    if input_before != input_after:
        raise RuntimeError("canonical source-pin input changed during acquisition")

    available = sum(entry["status"] == "AVAILABLE" for entry in entries)
    unavailable = len(entries) - available
    versions = sum(entry["publisherVersion"]["status"] == "OBSERVED" for entry in entries)
    commits = sum(entry["publisherCommit"]["status"] == "OBSERVED" for entry in entries)
    return {
        "schemaVersion": "1.0",
        "evidenceType": "PUBLIC_OFFICIAL_SOURCE_ACQUISITION",
        "generatedAt": utc_now(),
        "startedAt": started_at,
        "decision": "EVIDENCE_ONLY_NOT_PRODUCTION_GO",
        "productionGo": False,
        "constraints": {
            "officialPrimarySourcesOnly": True,
            "publicHttpsOnly": True,
            "authenticationUsed": False,
            "secretsReadOrRecorded": False,
            "canonicalSourcePinsModified": False,
            "responseBodiesPersisted": False,
            "failurePolicy": "RECORD_UNAVAILABLE",
        },
        "input": {
            "path": input_path.relative_to(ROOT).as_posix(),
            "sha256": sha256_bytes(input_before),
            "sourceCount": len(sources),
            "unchangedDuringAcquisition": True,
        },
        "acquisitionPolicy": {
            "timeoutSeconds": timeout,
            "maximumResponseBytes": max_bytes,
            "workers": workers,
            "userAgent": USER_AGENT,
            "allowedHosts": sorted(OFFICIAL_HOSTS),
            "contentHashDefinition": "SHA-256 of exact successful HTTP GET response body with Accept-Encoding identity",
        },
        "summary": {
            "total": len(entries),
            "available": available,
            "unavailable": unavailable,
            "publisherVersionsObserved": versions,
            "publisherCommitsObserved": commits,
            "allSourcesAvailable": unavailable == 0,
        },
        "sources": entries,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Acquire secret-free HTTP and content-hash evidence for the 25 canonical official source URLs."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="read-only canonical SOURCE_PINS JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="evidence JSON output")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="per-request timeout seconds")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES, help="maximum bytes per response")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="parallel public fetches")
    parser.add_argument(
        "--fail-on-unavailable",
        action="store_true",
        help="return exit status 2 after writing evidence when any source is UNAVAILABLE",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = args.input.expanduser().resolve()
    output_path = ensure_output_scope(args.output)
    if input_path != DEFAULT_INPUT.resolve():
        raise ValueError(f"input must be the canonical read-only file {DEFAULT_INPUT}")
    if args.timeout <= 0 or args.timeout > 120:
        raise ValueError("timeout must be greater than 0 and at most 120 seconds")
    if args.max_bytes < 1024 or args.max_bytes > 64 * 1024 * 1024:
        raise ValueError("max-bytes must be between 1024 and 67108864")
    if args.workers < 1 or args.workers > 8:
        raise ValueError("workers must be between 1 and 8")

    document = strict_json_load(input_path)
    sources = validate_sources(document)
    evidence = build_evidence(
        input_path,
        sources,
        timeout=args.timeout,
        max_bytes=args.max_bytes,
        workers=args.workers,
    )
    write_json_atomic(output_path, evidence)
    summary = evidence["summary"]
    print(
        "SOURCE PIN EVIDENCE WRITTEN "
        f"total={summary['total']} available={summary['available']} unavailable={summary['unavailable']} "
        f"output={output_path} productionGo=false"
    )
    if args.fail_on_unavailable and summary["unavailable"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
