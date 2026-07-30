#!/usr/bin/env python3
"""Negative self-tests for the release validation harness.

A package validator is security-sensitive code. These tests prove that important
malformed inputs are rejected instead of merely confirming that the current tree
passes. The fixtures are created in a temporary directory and never enter the ZIP.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Callable

sys.dont_write_bytecode = True
from archive_policy import EXPECTED_ASCII_ZIP_FLAGS, member_name_problems
from canonical_hashes import strict_load_json
from check_archive_safety import is_allowed_executable
from check_links_and_markdown import MD_LINK, local_target
from package_metadata import ROOT, load_package_metadata
from strict_data import strict_load_yaml

EXPECTED_ASSERTIONS = 38


def expect_reject(label: str, action: Callable[[], object], errors: list[str]) -> None:
    try:
        action()
    except Exception:
        return
    errors.append(f"negative fixture was accepted: {label}")


def main() -> int:
    errors: list[str] = []
    cases = 0
    with tempfile.TemporaryDirectory(prefix="wallet-validator-selftest-") as temp_dir:
        temp = Path(temp_dir)
        json_fixtures = {
            "duplicate-root": '{"a":1,"a":2}',
            "duplicate-nested": '{"a":{"b":1,"b":2}}',
            "float": '{"amount":0.1}',
            "exponent": '{"amount":1e3}',
            "nan": '{"amount":NaN}',
            "infinity": '{"amount":Infinity}',
            "negative-zero": '{"amount":-0}',
            "unsafe-large-integer": '{"amount":9007199254740992}',
        }
        for label, text in json_fixtures.items():
            path = temp / f"{label}.json"
            path.write_text(text, encoding="utf-8")
            expect_reject(label, lambda path=path: strict_load_json(path), errors)
            cases += 1

        yaml_fixtures = {
            "duplicate-yaml-root": "a: 1\na: 2\n",
            "duplicate-yaml-nested": "a:\n  b: 1\n  b: 2\n",
            "yaml-alias": "base: &base\n  x: 1\ncopy: *base\n",
            "yaml-nan": "value: .nan\n",
        }
        for label, text in yaml_fixtures.items():
            path = temp / f"{label}.yaml"
            path.write_text(text, encoding="utf-8")
            expect_reject(label, lambda path=path: strict_load_yaml(path), errors)
            cases += 1

    unsafe_names = {
        "parent traversal": "../evil.txt",
        "embedded traversal": "safe/../evil.txt",
        "Windows alternate stream": "safe/file.txt:secret",
        "Windows reserved": "safe/CON.txt",
        "trailing dot": "safe/file.",
        "leading whitespace": "safe/ file.txt",
        "control character": "safe/a\x01.txt",
        "bidi override": "safe/a\u202etxt.exe",
        "non-NFC": "safe/" + unicodedata.normalize("NFD", "が") + ".txt",
        "absolute": "/safe/file.txt",
        "backslash": "safe\\file.txt",
        "non-ASCII confusable": "safe/ｃon.txt",
    }
    for label, name in unsafe_names.items():
        if not member_name_problems(name):
            errors.append(f"unsafe path was accepted: {label}: {name!r}")
        cases += 1
    for name in ("README_FIRST.md", "tools/validate_package.py", "prototype/screenshots/iphone-jpyc-large.png"):
        if member_name_problems(name):
            errors.append(f"safe package path was rejected: {name}: {member_name_problems(name)}")
        cases += 1

    if EXPECTED_ASCII_ZIP_FLAGS != 0:
        errors.append("ASCII-only ZIP filename flags must be exactly zero")
    cases += 1

    if not is_allowed_executable("apps/android/gradlew", Path("apps/android/gradlew")):
        errors.append("the exact Gradle wrapper path must be executable")
    cases += 1
    if is_allowed_executable("apps/android/untrusted", Path("apps/android/untrusted")):
        errors.append("arbitrary non-Python executables must remain prohibited")
    cases += 1

    metadata = load_package_metadata()
    if metadata.root_name != ROOT.name or not metadata.version.startswith("2026-"):
        errors.append("metadata/root/version single source of truth failed")
    cases += 1

    source_json = strict_load_json(ROOT / "examples/source-pins.json")
    source_yaml = strict_load_yaml(ROOT / "config/source-pins.example.yaml")
    if source_json != source_yaml:
        errors.append("source pin JSON/YAML semantic equality test failed")
    cases += 1

    expect_reject("unsafe javascript link", lambda: local_target(ROOT / "README_FIRST.md", "javascript:alert(1)"), errors)
    cases += 1
    if not MD_LINK.findall("[入口](START_HERE.html)"):
        errors.append("Markdown link parser positive fixture failed")
    cases += 1

    chat = strict_load_yaml(ROOT / "contracts/chatgpt-readonly-openapi.yaml")
    operation_ids = {
        operation.get("operationId")
        for item in chat.get("paths", {}).values()
        if isinstance(item, dict)
        for method, operation in item.items()
        if method in {"get", "post"} and isinstance(operation, dict)
    }
    expected = {"getReadOnlyStatus", "getPlainJapaneseTerm", "explainNonTransactionalError", "getGenericSafetyHelp"}
    if operation_ids != expected:
        errors.append("ChatGPT read-only operation allowlist self-test failed")
    cases += 1

    prototype_source = (ROOT / "tools/test_prototype.py").read_text(encoding="utf-8")
    if 'for stale in output_shots.glob("*.png")' not in prototype_source or 'for stale in SHOTS.glob("*.png")' in prototype_source:
        errors.append("prototype --check screenshot isolation regression")
    cases += 1

    from run_full_validation import _VALIDATORS
    validator_names = [item[0] for item in _VALIDATORS]
    required_validators = {
        "test_validation_harness.py", "check_python_sources.py", "test_python_unit_suite.py",
        "test_canonical_properties.py", "test_canonical_fuzz.py",
        "run_local_sandbox.py", "update_example_hashes.py", "test_prototype.py", "test_start_here.py",
        "test_local_preview_http.py", "generate_status_outputs.py",
        "generate_coverage_matrix.py", "generate_source_pin_drift_disposition.py",
        "generate_release_contract_artifacts.py", "generate_current_validation_evidence.py",
        "generate_operational_readiness_report.py", "generate_reports.py",
        "generate_operationalization_evidence_binding.py", "check_release_contract.py",
        "check_toolchain_lock.py", "check_shared_canonical_vectors.py", "check_coverage_matrix.py",
        "check_mobile_contract_vectors.py", "check_operational_readiness.py",
        "test_operational_readiness_positive.py", "test_operational_readiness_negative.py",
        "check_runtime_authorization.py", "test_runtime_authorization_positive.py",
        "test_runtime_authorization_negative.py", "check_plain_japanese.py", "check_archive_safety.py",
        "check_security_hygiene.py", "check_links_and_markdown.py", "adversarial_audit.py",
        "generate_manifest.py", "validate_package.py",
    }
    if set(validator_names) != required_validators or len(validator_names) != len(set(validator_names)):
        errors.append("full validation validator allowlist drift or duplication")
    cases += 1

    check_specs = set(_VALIDATORS)
    required_check_specs = {
        ("update_example_hashes.py", "--check"),
        ("test_prototype.py", "--check"),
        ("test_start_here.py", "--check"),
        ("generate_status_outputs.py", "--check"),
        ("generate_release_contract_artifacts.py", "--check"),
        ("generate_coverage_matrix.py", "--check"),
        ("generate_source_pin_drift_disposition.py", "--check"),
        ("generate_current_validation_evidence.py", "--check"),
        ("generate_operational_readiness_report.py", "--check"),
        ("generate_reports.py", "--check"),
        ("generate_operationalization_evidence_binding.py", "--check"),
        ("generate_manifest.py", "--check"),
    }
    if not required_check_specs.issubset(check_specs):
        errors.append("generated-artifact validators are not locked to --check mode")
    cases += 1

    if cases != EXPECTED_ASSERTIONS:
        errors.append(f"self-test assertion count drift: {cases} != {EXPECTED_ASSERTIONS}")
    if errors:
        print("VALIDATION HARNESS SELF-TEST FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALIDATION HARNESS SELF-TEST PASSED")
    print(f"Negative/positive assertions: {EXPECTED_ASSERTIONS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
