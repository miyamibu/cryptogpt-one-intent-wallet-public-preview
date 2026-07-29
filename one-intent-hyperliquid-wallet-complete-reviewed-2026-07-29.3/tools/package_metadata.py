#!/usr/bin/env python3
"""Single source of truth for package identity and deterministic timestamp."""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from canonical_hashes import strict_load_json

ROOT = Path(__file__).resolve().parents[1]
_METADATA_PATH = ROOT / "config/build-metadata.json"
_PACKAGE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_VERSION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.\d+$")


@dataclass(frozen=True)
class PackageMetadata:
    schema_version: str
    package: str
    version: str
    deterministic_build_timestamp: str
    deterministic_datetime: dt.datetime
    assurance_scope: str
    native_builds_included: bool
    live_credentials_included: bool
    mainnet_enabled: bool
    production_ready_claim_allowed: bool

    @property
    def root_name(self) -> str:
        return f"{self.package}-{self.version}"

    @property
    def source_date_epoch(self) -> int:
        return int(self.deterministic_datetime.timestamp())

    @property
    def zip_datetime(self) -> tuple[int, int, int, int, int, int]:
        value = self.deterministic_datetime.astimezone(dt.timezone.utc)
        return (value.year, value.month, value.day, value.hour, value.minute, value.second)


def _require_bool(data: dict[str, Any], key: str) -> bool:
    value = data.get(key)
    if type(value) is not bool:
        raise ValueError(f"build metadata {key} must be a JSON boolean")
    return value


def load_package_metadata(path: Path = _METADATA_PATH) -> PackageMetadata:
    data = strict_load_json(path)
    if not isinstance(data, dict):
        raise ValueError("build metadata must be a JSON object")
    expected_keys = {
        "schemaVersion",
        "package",
        "version",
        "deterministicBuildTimestamp",
        "assuranceScope",
        "nativeBuildsIncluded",
        "liveCredentialsIncluded",
        "mainnetEnabled",
        "productionReadyClaimAllowed",
    }
    unknown = set(data) - expected_keys
    missing = expected_keys - set(data)
    if unknown or missing:
        raise ValueError(f"build metadata keys mismatch; missing={sorted(missing)}, unknown={sorted(unknown)}")
    if data["schemaVersion"] != "1.0":
        raise ValueError("unsupported build metadata schemaVersion")
    package = data["package"]
    version = data["version"]
    timestamp = data["deterministicBuildTimestamp"]
    scope = data["assuranceScope"]
    if not isinstance(package, str) or not _PACKAGE_RE.fullmatch(package):
        raise ValueError("build metadata package must be a lowercase portable slug")
    if not isinstance(version, str) or not _VERSION_RE.fullmatch(version):
        raise ValueError("build metadata version must match YYYY-MM-DD.N")
    if not isinstance(timestamp, str) or not timestamp.endswith("Z"):
        raise ValueError("deterministicBuildTimestamp must be an explicit UTC Z timestamp")
    try:
        parsed = dt.datetime.fromisoformat(timestamp[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("invalid deterministicBuildTimestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0) or parsed.microsecond:
        raise ValueError("deterministicBuildTimestamp must be UTC and second-precision")
    if parsed.year < 1980 or parsed.year > 2107:
        raise ValueError("ZIP timestamp year must be in 1980..2107")
    if parsed.second % 2:
        raise ValueError("ZIP timestamp second must be even for exact DOS timestamp representation")
    if not isinstance(scope, str) or len(scope.strip()) < 32:
        raise ValueError("assuranceScope must be explicit")
    metadata = PackageMetadata(
        schema_version=data["schemaVersion"],
        package=package,
        version=version,
        deterministic_build_timestamp=timestamp,
        deterministic_datetime=parsed,
        assurance_scope=scope,
        native_builds_included=_require_bool(data, "nativeBuildsIncluded"),
        live_credentials_included=_require_bool(data, "liveCredentialsIncluded"),
        mainnet_enabled=_require_bool(data, "mainnetEnabled"),
        production_ready_claim_allowed=_require_bool(data, "productionReadyClaimAllowed"),
    )
    if any((metadata.native_builds_included, metadata.live_credentials_included, metadata.mainnet_enabled, metadata.production_ready_claim_allowed)):
        raise ValueError("this design-only release must keep all production/native claims false")
    if ROOT.name != metadata.root_name:
        raise ValueError(f"package root name mismatch: {ROOT.name!r} != {metadata.root_name!r}")
    return metadata
