#!/usr/bin/env python3
"""Validate the recorded design-only toolchain contract without probing a host."""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True
from canonical_hashes import strict_load_json
from package_metadata import ROOT, load_package_metadata


def main() -> int:
    metadata = load_package_metadata()
    lock = strict_load_json(ROOT / "config/toolchain-lock.json")
    errors: list[str] = []
    required = {
        "schemaVersion", "packageVersion", "status", "complete", "recordedAt",
        "validationHost", "python", "browser", "swift", "android", "java",
        "releaseControls", "limitations",
    }
    if set(lock) != required:
        errors.append(f"toolchain lock keys mismatch: missing={sorted(required - set(lock))}, unknown={sorted(set(lock) - required)}")
    if lock.get("schemaVersion") != "1.0" or lock.get("packageVersion") != metadata.version:
        errors.append("toolchain lock is not bound to the package version")
    if lock.get("status") != "PARTIAL_DESIGN_LOCK_NOT_RELEASE_LOCK" or lock.get("complete") is not False:
        errors.append("toolchain lock must remain explicitly incomplete and non-release")
    for component in ("validationHost", "python", "browser", "swift", "android", "java", "releaseControls"):
        if not isinstance(lock.get(component), dict) or not lock[component]:
            errors.append(f"toolchain lock component is missing: {component}")
    android = lock.get("android", {})
    for key in ("gradleWrapper", "gradle", "androidSdk", "sdkManager"):
        value = android.get(key)
        if not isinstance(value, str) or not value.endswith("_LOCAL_ONLY"):
            errors.append(f"Android {key} must be recorded as PRESENT_LOCAL_ONLY and cannot be a release attestation")
    wrapper = (ROOT / "apps/android/gradle/wrapper/gradle-wrapper.properties").read_text(encoding="utf-8")
    expected_distribution_hash = "b266d5ff6b90eada6dc3b20cb090e3731302e553a27c5d3e4df1f0d76beaff06"
    if f"distributionSha256Sum={expected_distribution_hash}" not in wrapper:
        errors.append("Gradle 9.3.1 wrapper distribution checksum is not pinned")
    controls = lock.get("releaseControls", {})
    for key in ("networkAccessForValidation", "productionWritePermitted", "nativeSignedArtifactsAvailable", "sourcePinContentHashesPopulated", "artifactSigningAvailable", "twoPersonApprovalProvisioned"):
        if controls.get(key) is not False:
            errors.append(f"release control must be false in design package: {key}")
    if not isinstance(lock.get("limitations"), list) or not lock["limitations"]:
        errors.append("toolchain lock must retain explicit limitations")
    if errors:
        print("TOOLCHAIN LOCK VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("TOOLCHAIN LOCK VALIDATION PASSED")
    print("Recorded Python/Swift/browser versions are pinned for local evidence")
    print("Android local build toolchain: PRESENT_LOCAL_ONLY")
    print("Android signed release artifact/AAB and release device matrix: NOT_PROVIDED")
    print("Production release/toolchain attestation: NOT PROVIDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
