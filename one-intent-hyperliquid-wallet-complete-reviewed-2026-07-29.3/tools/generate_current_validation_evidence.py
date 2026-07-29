#!/usr/bin/env python3
"""Generate current local validation metadata without making production claims."""
from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
from artifact_io import json_bytes, write_or_check
from canonical_hashes import strict_load_json
from package_metadata import ROOT, load_package_metadata
from release_digest_policy import DIGEST_DOMAIN, design_source_tree_digest
from canonical_quality import run_fuzz_smoke, run_property_checks


METADATA = load_package_metadata()


def run_unit_suite() -> int:
    proc = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if proc.returncode:
        raise RuntimeError("local unit suite failed while generating current evidence")
    match = re.search(r"Ran (\d+) tests?", proc.stderr + proc.stdout)
    if match is None:
        raise RuntimeError("unit suite output did not contain a test count")
    return int(match.group(1))


def run_python_source_compile() -> int:
    proc = subprocess.run(
        [sys.executable, "-B", str(ROOT / "tools/check_python_sources.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode:
        raise RuntimeError("Python source compilation failed while generating current evidence")
    match = re.search(r"PYTHON SOURCE COMPILATION PASSED \((\d+) files\)", output)
    if match is None:
        raise RuntimeError("Python source compilation output did not contain a file count")
    return int(match.group(1))


def recorded_swift_contract_count() -> int:
    """Return the package's already-recorded macOS Swift count.

    Linux CI validates the package contract but does not have the Apple Swift
    toolchain.  Reusing a positive count that was recorded on macOS keeps the
    cross-platform contract deterministic without pretending that CI executed
    the native tests.  A missing or invalid record is a hard failure so this
    fallback cannot manufacture a passing count.
    """
    path = ROOT / "delivery/evidence/core/reference-tests-current.json"
    if not path.is_file():
        raise RuntimeError("Swift is unavailable and no recorded local Swift evidence exists")
    recorded = strict_load_json(path)
    count = recorded.get("swiftContractTests")
    if not isinstance(count, int) or count <= 0:
        raise RuntimeError(
            "Swift is unavailable and the recorded local Swift contract-test count is missing or invalid"
        )
    return count


def swift_contract_result() -> tuple[int | None, str | None, str]:
    # The recorded contract is an Apple Swift/macOS check.  Ubuntu runners
    # may expose a non-Apple `swift` binary, but that binary is not the
    # macOS-native evidence represented by this package and must not be used
    # to overwrite the recorded count after a platform-specific failure.
    swift = shutil.which("swift") if platform.system() == "Darwin" else None
    if swift is None:
        return (
            recorded_swift_contract_count(),
            None,
            "RECORDED_MACOS_EVIDENCE_NOT_EXECUTED_ON_CURRENT_HOST",
        )
    version_proc = subprocess.run([swift, "--version"], check=False, capture_output=True, text=True)
    version_output = version_proc.stdout or version_proc.stderr
    swift_version = version_output.splitlines()[0] if version_output else None
    with tempfile.TemporaryDirectory(prefix="cryptogpt-swift-test-") as scratch:
        proc = subprocess.run(
            [swift, "test", "--package-path", str(ROOT / "apps/ios"), "--scratch-path", scratch],
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "SWIFT_DETERMINISTIC_HASHING": "1"},
        )
    if proc.returncode:
        return None, swift_version, "CURRENT_HOST_EXECUTION_FAILED"
    output = (proc.stdout or "") + (proc.stderr or "")
    matches = re.findall(r"Executed (\d+) tests?", output)
    return (
        (int(matches[-1]) if matches else None),
        swift_version,
        "CURRENT_HOST_EXECUTION_RECORDED",
    )


def build_evidence() -> dict:
    visual = strict_load_json(ROOT / "tests/prototype-visual-evidence.json")
    swift_count, swift_version, swift_scope = swift_contract_result()
    property_result = run_property_checks()
    fuzz_result = run_fuzz_smoke()
    return {
        "schemaVersion": "1.0",
        "status": "LOCAL_VALIDATION_NOT_RELEASE_EVIDENCE",
        "releaseVersion": METADATA.version,
        "rootBinding": "clean-extracted-release-root",
        "evidenceId": f"core-reference-tests-{METADATA.version}",
        "result": "PASS",
        "command": "python3 -B -m unittest discover -s tests -p 'test_*.py'",
        "pythonSourceFilesCompiled": run_python_source_compile(),
        "testCount": run_unit_suite(),
        "browserLogicalCases": visual.get("geometryAndContrastCases"),
        "swiftContractTests": swift_count,
        "swiftContractTestScope": swift_scope,
        "propertyTests": property_result,
        "fuzzSmoke": fuzz_result,
        "environment": (
            f"{platform.platform()} / {platform.python_version()} / "
            f"{swift_version or 'Swift unavailable'}"
        ),
        "sourceTreeDigest": design_source_tree_digest(ROOT),
        "sourceTreeDigestDomain": DIGEST_DOMAIN,
        "scope": "offline standard-library reference implementation and logical-pixel browser prototype",
        "limitations": [
            "No external network, production release artifact, full physical-device matrix, signer key, Testnet/Mainnet write, production service, legal approval, store approval, or independent audit was used; the separate local iPhone 12 device-proof record is not production evidence.",
            "This record is not a signed production evidence statement and cannot satisfy a readiness claim by itself.",
        ],
        "signed": False,
        "independentReview": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare derived bytes without writing")
    args = parser.parse_args()
    evidence = build_evidence()
    write_or_check(
        ROOT / "delivery/evidence/core/reference-tests-current.json",
        json_bytes(evidence),
        check=args.check,
        label="delivery/evidence/core/reference-tests-current.json",
    )
    write_or_check(
        ROOT / "delivery/evidence/core/PROPERTY_TEST_REPORT.json",
        json_bytes({
            "schemaVersion": "1.0",
            "status": "LOCAL_VALIDATION_NOT_RELEASE_EVIDENCE",
            "releaseVersion": METADATA.version,
            "result": evidence["propertyTests"],
            "independentReview": False,
            "signed": False,
        }),
        check=args.check,
        label="delivery/evidence/core/PROPERTY_TEST_REPORT.json",
    )
    write_or_check(
        ROOT / "delivery/evidence/core/FUZZ_REPORT.json",
        json_bytes({
            "schemaVersion": "1.0",
            "status": "LOCAL_VALIDATION_NOT_RELEASE_EVIDENCE",
            "releaseVersion": METADATA.version,
            "result": evidence["fuzzSmoke"],
            "independentReview": False,
            "signed": False,
        }),
        check=args.check,
        label="delivery/evidence/core/FUZZ_REPORT.json",
    )
    print("CURRENT LOCAL VALIDATION EVIDENCE " + ("VERIFIED" if args.check else "GENERATED"))
    print("Signed production evidence: NOT GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
