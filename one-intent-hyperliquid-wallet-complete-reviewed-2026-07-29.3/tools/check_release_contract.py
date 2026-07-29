#!/usr/bin/env python3
"""Fail-closed checks for release evidence, canonical IDs, and design-only pointers.

This validator does not create evidence and never upgrades the package to GO.
It detects the classes of drift found in the 2026-07-29.3 adversarial review:
historical evidence being mistaken for current evidence, legacy blocker IDs not
mapping to the semantic readiness model, production-named policy files not being
connected to the evaluator, and release subjects using a second field vocabulary.
"""
from __future__ import annotations

import re
import hashlib
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

sys.dont_write_bytecode = True
from canonical_hashes import strict_load_json, strict_load_json_text
from package_metadata import ROOT, load_package_metadata
from release_digest_policy import design_source_tree_digest
from strict_data import strict_load_yaml
from wallet_dependency import WALLET_DEPENDENCY_VERSION, validate_gate_partition, wallet_dependency_for_gate


METADATA = load_package_metadata()


def load_json(rel: str) -> Any:
    return strict_load_json(ROOT / rel)


def schema_errors(value: Any, schema_rel: str, label: str) -> list[str]:
    schema = load_json(schema_rel)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{label}: {error.message} at {'/'.join(str(part) for part in error.absolute_path) or '<root>'}"
        for error in sorted(validator.iter_errors(value), key=lambda item: tuple(str(part) for part in item.absolute_path))
    ]


def check_canonical_traceability(
    config_value: dict[str, Any] | None = None,
    trace_value: dict[str, Any] | None = None,
    document_text: str | None = None,
) -> list[str]:
    errors: list[str] = []
    config = config_value if config_value is not None else load_json("config/operational-readiness.json")
    gate_ids = {gate.get("gateId") for gate in config.get("gates", [])}
    claim_ids = {
        claim.get("claimId")
        for gate in config.get("gates", [])
        for claim in gate.get("claims", [])
    }
    claim_gate = {
        claim.get("claimId"): gate.get("gateId")
        for gate in config.get("gates", [])
        for claim in gate.get("claims", [])
    }
    trace = trace_value if trace_value is not None else load_json("delivery/external-blocker-traceability.json")
    errors.extend(schema_errors(trace, "schemas/external-blocker-traceability.schema.json", "external blocker traceability"))
    blockers = trace.get("blockers", [])
    expected_ids = {item.get("id") for item in blockers}
    if len(expected_ids) != len(blockers) or not expected_ids:
        errors.append("external blocker IDs must be non-empty and unique")
    actual_ids = {item.get("id") for item in blockers}
    if actual_ids != expected_ids:
        errors.append("external blocker IDs are inconsistent")
    for blocker in blockers:
        direct_gate_ids = set(blocker.get("directGateIds", []))
        dependent_gate_ids = set(blocker.get("dependentGateIds", []))
        all_gate_ids = direct_gate_ids | dependent_gate_ids
        unknown_gates = all_gate_ids - gate_ids
        unknown_claims = set(blocker.get("claimIds", [])) - claim_ids
        if unknown_gates:
            errors.append(f"{blocker.get('id')}: unknown canonical gates: {sorted(unknown_gates)}")
        if unknown_claims:
            errors.append(f"{blocker.get('id')}: unknown canonical claims: {sorted(unknown_claims)}")
        for claim_id in blocker.get("claimIds", []):
            if claim_gate.get(claim_id) not in direct_gate_ids:
                errors.append(f"{blocker.get('id')}: claim is not listed under its canonical gate: {claim_id}")
        if direct_gate_ids & dependent_gate_ids:
            errors.append(f"{blocker.get('id')}: direct and dependent gates must be disjoint")
        expected_direct_gates = {
            claim_gate[claim_id]
            for claim_id in blocker.get("claimIds", [])
            if claim_id in claim_gate
        }
        if direct_gate_ids != expected_direct_gates:
            errors.append(
                f"{blocker.get('id')}: direct gates must equal the parent gates of its claims; "
                f"expected {sorted(expected_direct_gates)}"
            )
        if not blocker.get("legacyAliases"):
            errors.append(f"{blocker.get('id')}: legacy aliases must remain traceable during migration")
    coverage = trace.get("coverage", {})
    try:
        validate_gate_partition(gate_ids)
    except ValueError as exc:
        errors.append(str(exc))
    if coverage.get("walletDependencyVersion") != WALLET_DEPENDENCY_VERSION:
        errors.append("traceability coverage wallet dependency version mismatch")
    if coverage.get("personalWalletRequired") is not False:
        errors.append("traceability coverage must explicitly prohibit personal wallet dependency")
    expected_gate_entries: dict[str, dict[str, Any]] = {}
    expected_claim_entries: dict[str, dict[str, Any]] = {}
    blocker_gate_ids: dict[str, set[str]] = {}
    blocker_claim_ids: dict[str, set[str]] = {}
    for blocker in blockers:
        blocker_id = blocker.get("id")
        all_blocker_gates = set(blocker.get("directGateIds", [])) | set(blocker.get("dependentGateIds", []))
        for gate_id in all_blocker_gates:
            blocker_gate_ids.setdefault(gate_id, set()).add(blocker_id)
        for claim_id in blocker.get("claimIds", []):
            blocker_claim_ids.setdefault(claim_id, set()).add(blocker_id)
    for gate in config.get("gates", []):
        gate_id = gate.get("gateId")
        claim_list = [claim.get("claimId") for claim in gate.get("claims", [])]
        external_claims = [claim_id for claim_id in claim_list if claim_id in blocker_claim_ids]
        expected_gate_entries[gate_id] = {
            "claimIds": set(claim_list),
            "blockerIds": blocker_gate_ids.get(gate_id, set()),
            "classification": (
                "INTERNAL_IMPLEMENTATION"
                if not external_claims
                else "EXTERNAL_BLOCKER"
                if len(external_claims) == len(claim_list)
                else "MIXED"
            ),
            "walletDependency": wallet_dependency_for_gate(gate_id),
            "personalWalletRequired": False,
        }
        for claim_id in claim_list:
            expected_claim_entries[claim_id] = {
                "gateId": gate_id,
                "blockerIds": blocker_claim_ids.get(claim_id, set()),
                "classification": "EXTERNAL_BLOCKER" if claim_id in blocker_claim_ids else "INTERNAL_IMPLEMENTATION",
                "walletDependency": wallet_dependency_for_gate(gate_id),
                "personalWalletRequired": False,
            }
    if coverage.get("coverageVersion") != "1.0":
        errors.append("traceability coverage must declare coverageVersion 1.0")
    if coverage.get("gateCount") != len(expected_gate_entries) or coverage.get("claimCount") != len(expected_claim_entries):
        errors.append(
            "traceability coverage counts must equal the configured readiness model "
            f"({len(expected_gate_entries)} gates / {len(expected_claim_entries)} claims)"
        )
    actual_gate_entries = {entry.get("gateId"): entry for entry in coverage.get("gates", [])}
    actual_claim_entries = {entry.get("claimId"): entry for entry in coverage.get("claims", [])}
    actual_gate_list = coverage.get("gates", [])
    actual_claim_list = coverage.get("claims", [])
    if len(actual_gate_list) != len(actual_gate_entries):
        errors.append("traceability coverage must reject duplicate gate IDs")
    if len(actual_claim_list) != len(actual_claim_entries):
        errors.append("traceability coverage must reject duplicate claim IDs")
    if len(actual_gate_list) != len(expected_gate_entries):
        errors.append("traceability coverage gate array length must equal the configured gate count")
    if len(actual_claim_list) != len(expected_claim_entries):
        errors.append("traceability coverage claim array length must equal the configured claim count")
    if set(actual_gate_entries) != set(expected_gate_entries):
        errors.append("traceability coverage must list every configured gate exactly once")
    if set(actual_claim_entries) != set(expected_claim_entries):
        errors.append("traceability coverage must list every configured claim exactly once")
    for gate_id, expected in expected_gate_entries.items():
        entry = actual_gate_entries.get(gate_id)
        if entry is None:
            continue
        if set(entry.get("claimIds", [])) != expected["claimIds"]:
            errors.append(f"traceability gate coverage claim set drift: {gate_id}")
        if set(entry.get("blockerIds", [])) != expected["blockerIds"]:
            errors.append(f"traceability gate coverage blocker set drift: {gate_id}")
        if entry.get("classification") != expected["classification"]:
            errors.append(f"traceability gate coverage classification drift: {gate_id}")
        if entry.get("walletDependency") != expected["walletDependency"]:
            errors.append(f"traceability gate wallet dependency drift: {gate_id}")
        if entry.get("personalWalletRequired") is not False:
            errors.append(f"traceability gate personal wallet dependency must remain false: {gate_id}")
    for claim_id, expected in expected_claim_entries.items():
        entry = actual_claim_entries.get(claim_id)
        if entry is None:
            continue
        if entry.get("gateId") != expected["gateId"]:
            errors.append(f"traceability claim coverage parent gate drift: {claim_id}")
        if set(entry.get("blockerIds", [])) != expected["blockerIds"]:
            errors.append(f"traceability claim coverage blocker set drift: {claim_id}")
        if entry.get("classification") != expected["classification"]:
            errors.append(f"traceability claim coverage classification drift: {claim_id}")
        if entry.get("walletDependency") != expected["walletDependency"]:
            errors.append(f"traceability claim wallet dependency drift: {claim_id}")
        if entry.get("personalWalletRequired") is not False:
            errors.append(f"traceability claim personal wallet dependency must remain false: {claim_id}")
    document = document_text if document_text is not None else (ROOT / "delivery/EXTERNAL_BLOCKERS.md").read_text(encoding="utf-8")
    if "delivery/external-blocker-traceability.json" not in document or "legacy alias" not in document:
        errors.append("EXTERNAL_BLOCKERS.md must identify the canonical mapping and demote numeric aliases")
    headings = set(re.findall(r"^## (EXT-[0-9]{3})\b", document, re.MULTILINE))
    if headings != expected_ids:
        errors.append("EXTERNAL_BLOCKERS.md headings do not match the canonical blocker set")
    return errors


def check_policy_profiles() -> list[str]:
    errors: list[str] = []
    profiles = (
        (
            "config/operational-trust-policy.production.json",
            "schemas/operational-trust-policy.schema.json",
            "config/operational-trust-policy.template.json",
        ),
        (
            "config/runtime-policy.production.json",
            "schemas/runtime-authorization-policy.schema.json",
            "config/runtime-authorization-policy.template.json",
        ),
    )
    for rel, schema_rel, template_rel in profiles:
        profile = load_json(rel)
        errors.extend(schema_errors(profile, schema_rel, rel))
        template = load_json(template_rel)
        if profile.get("enabled") is not False:
            errors.append(f"{rel}: production-named placeholder must remain disabled")
        if profile.get("policyVersion") != "PRODUCTION_NOT_PROVISIONED":
            errors.append(f"{rel}: production-named placeholder must declare PRODUCTION_NOT_PROVISIONED")
        for key in ("profileId", "signatureProfile", "canonicalization"):
            if profile.get(key) != template.get(key):
                errors.append(f"{rel}: canonical {key} drift from the design template")
        if rel.endswith("operational-trust-policy.production.json"):
            if profile.get("trustedKeys") or profile.get("revokedKeyIds"):
                errors.append(f"{rel}: no production keys may be provisioned in this design package")
        else:
            network = profile.get("network", {})
            if network.get("allowedSourceNetworkIds") or network.get("allowedDestinationNetworkIds"):
                errors.append(f"{rel}: production placeholder must not allow network writes")
    return errors


def check_release_subject() -> list[str]:
    errors = schema_errors(
        load_json("release/release-subject.json"),
        "schemas/release-subject.schema.json",
        "release subject",
    )
    subject = load_json("release/release-subject.json")
    index = load_json("delivery/evidence-index.json")
    if subject != index.get("releaseSubject"):
        errors.append("standalone release subject must exactly equal delivery/evidence-index.json releaseSubject")
    if subject.get("releaseId") != f"{METADATA.version}-design-package":
        errors.append("release subject releaseId is not bound to the package version")
    legacy_fields = {"sourceTreeDigest", "backendImageSha256", "signerImageSha256"}
    if legacy_fields & set(subject):
        errors.append(f"release subject contains legacy fields: {sorted(legacy_fields & set(subject))}")
    if subject.get("environment") != "DESIGN_ONLY":
        errors.append("design release subject must remain explicitly non-production")
    if any(value is not None for key, value in subject.items() if key.endswith("Sha256") or key.endswith("Digest")):
        errors.append("design release subject must not contain artifact digests")
    return errors


def check_release_artifacts() -> list[str]:
    errors: list[str] = []
    upper_subject = load_json("release/RELEASE_SUBJECT.json")
    lower_subject = load_json("release/release-subject.json")
    if upper_subject != lower_subject:
        errors.append("release/RELEASE_SUBJECT.json must exactly equal lowercase release subject")
    if upper_subject.get("environment") != "DESIGN_ONLY":
        errors.append("uppercase release subject must remain DESIGN_ONLY")
    source_pins = load_json("release/SOURCE_PINS.json")
    if source_pins != load_json("config/source-pins.json"):
        errors.append("release/SOURCE_PINS.json must exactly equal config/source-pins.json")
    sbom = load_json("release/SBOM.spdx.json")
    if (
        sbom.get("spdxVersion") != "SPDX-2.3"
        or sbom.get("designOnly") is not True
        or sbom.get("signed") is not False
        or sbom.get("productionEvidence") is not False
        or not sbom.get("packages")
    ):
        errors.append("release/SBOM.spdx.json must be a non-production unsigned design inventory")
    provenance = load_json("release/PROVENANCE.json")
    source_digest = design_source_tree_digest(ROOT)
    if (
        provenance.get("status") != "DESIGN_ONLY_NOT_RELEASE_EVIDENCE"
        or provenance.get("format") != "SLSA_DESIGN_ONLY_UNSIGNED"
        or provenance.get("source", {}).get("sourceTreeSha256") != source_digest
        or provenance.get("source", {}).get("sourceCommit") is not None
        or provenance.get("signatures") != []
        or provenance.get("independentReview") is not False
    ):
        errors.append("release/PROVENANCE.json must remain unsigned design-only provenance")
    environment = (ROOT / "release/BUILD_ENVIRONMENT.md").read_text(encoding="utf-8")
    if (
        "PARTIAL_DESIGN_LOCK_NOT_RELEASE_LOCK" not in environment
        or ("PRESENT_LOCAL_ONLY" not in environment and "BLOCKED_MISSING" not in environment)
        or "productionWritePermitted: `false`" not in environment
    ):
        errors.append("release/BUILD_ENVIRONMENT.md must expose the incomplete toolchain and write boundary")
    reproducibility = (ROOT / "release/REPRODUCIBILITY_REPORT.md").read_text(encoding="utf-8")
    if "design-only" not in reproducibility or "doubleBuildStatus=CONTRACT_DEFINED_NOT_RUN_BY_PREPARATION" not in reproducibility:
        errors.append("release/REPRODUCIBILITY_REPORT.md must not claim an unperformed production build")
    execution = (ROOT / "release/CODEX_EXECUTION_REPORT.md").read_text(encoding="utf-8")
    if (
        "operationalReadiness=BLOCKED_NOT_OPERATIONAL" not in execution
        or "productionWritePermitted=false" not in execution
        or "walletKeyAccess=false" not in execution
        or not re.search(r"fullValidationStatus=(?:PASS|PENDING_FINAL_NON_MUTATING_VALIDATION)\n", execution)
    ):
        errors.append("release/CODEX_EXECUTION_REPORT.md must retain the local-only execution boundary")
    blockers = (ROOT / "release/UNRESOLVED_EXTERNAL_BLOCKERS.md").read_text(encoding="utf-8")
    if "status=BLOCKED_EXTERNAL" not in blockers or "releaseEvidenceStatus=NOT_RELEASE_EVIDENCE" not in blockers:
        errors.append("release/UNRESOLVED_EXTERNAL_BLOCKERS.md must remain an explicit external blocker record")
    handoff = (ROOT / "release/OPERATIONAL_HANDOFF.md").read_text(encoding="utf-8")
    if "status=BLOCKED_NOT_OPERATIONAL" not in handoff or "productionWritePermitted=false" not in handoff or "PRE_WALLET_GO=NOT_USED" not in handoff:
        errors.append("release/OPERATIONAL_HANDOFF.md must remain stopped before wallet connection")

    hash_file = (ROOT / "release/ARTIFACT_HASHES.txt").read_text(encoding="utf-8")
    if "format=DESIGN_ONLY_UNSIGNED_ARTIFACT_HASHES_V1" not in hash_file or f"sourceTreeSha256={source_digest}" not in hash_file:
        errors.append("release/ARTIFACT_HASHES.txt source digest is missing or stale")
    for line in hash_file.splitlines():
        match = re.fullmatch(r"artifact=(release/[A-Za-z0-9._/-]+) sha256=([0-9a-f]{64})", line)
        if not match:
            continue
        rel, expected_hash = match.groups()
        if rel == "release/ARTIFACT_HASHES.txt":
            errors.append("release/ARTIFACT_HASHES.txt must not hash itself")
            continue
        actual_hash = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            errors.append(f"release artifact hash drift: {rel}")
    return errors


def check_evidence_versioning() -> list[str]:
    errors: list[str] = []
    current = load_json("delivery/evidence/core/reference-tests-current.json")
    if current.get("releaseVersion") != METADATA.version:
        errors.append("current reference test evidence is not bound to package version")
    if current.get("status") != "LOCAL_VALIDATION_NOT_RELEASE_EVIDENCE":
        errors.append("current reference test evidence must remain local-only")
    if current.get("signed") is not False or current.get("independentReview") is not False:
        errors.append("current reference test evidence must not claim signing or independent review")
    if current.get("result") != "PASS" or not isinstance(current.get("testCount"), int) or current.get("testCount", 0) <= 0:
        errors.append("current reference test evidence has invalid local result metadata")
    if not isinstance(current.get("swiftContractTests"), int) or current.get("swiftContractTests", 0) <= 0:
        errors.append("current reference test evidence has an invalid Swift contract-test count")
    if current.get("swiftContractTestScope") not in {
        "CURRENT_HOST_EXECUTION_RECORDED",
        "RECORDED_MACOS_EVIDENCE_NOT_EXECUTED_ON_CURRENT_HOST",
        "CURRENT_HOST_EXECUTION_FAILED",
    }:
        errors.append("current reference test evidence has an invalid Swift contract-test scope")
    if not isinstance(current.get("pythonSourceFilesCompiled"), int) or current.get("pythonSourceFilesCompiled", 0) <= 0:
        errors.append("current reference test evidence must record the current Python compile count")
    if current.get("sourceTreeDigest") != design_source_tree_digest(ROOT):
        errors.append("current reference test evidence source-tree digest is stale or manually altered")
    historical = load_json("delivery/evidence/core/reference-tests.json")
    if historical.get("status") != "HISTORICAL_NOT_RELEASE_EVIDENCE":
        errors.append("old reference test evidence must be explicitly historical")
    review = (ROOT / "delivery/evidence/security/REVIEW_GPT56_SOL_MAX.md").read_text(encoding="utf-8")
    if "HISTORICAL / STALE" not in review or "NOT RELEASE EVIDENCE" not in review:
        errors.append("old Sol review must be explicitly demoted from current release evidence")
    try:
        project_status = strict_load_yaml(ROOT / "PROJECT_STATUS.yaml")
        implementation_status = strict_load_yaml(ROOT / "delivery/IMPLEMENTATION_STATUS.yaml")
    except Exception as exc:
        errors.append(f"current validation status YAML could not be loaded strictly: {exc}")
    else:
        validation = project_status.get("validation", {})
        tested_locally = implementation_status.get("tested_locally", {})
        expected_values = {
            "python_source_files_compiled": current.get("pythonSourceFilesCompiled"),
            "python_unit_tests": current.get("testCount"),
            "swift_contract_tests": current.get("swiftContractTests"),
        }
        if project_status.get("version") != METADATA.version or project_status.get("operational_readiness") != "BLOCKED_NOT_OPERATIONAL":
            errors.append("PROJECT_STATUS.yaml is not bound to the current blocked package")
        if validation.get("python_source_files_compiled") != expected_values["python_source_files_compiled"]:
            errors.append("PROJECT_STATUS.yaml Python compile count is stale")
        if validation.get("python_unit_tests") != expected_values["python_unit_tests"]:
            errors.append("PROJECT_STATUS.yaml Python unit count is stale")
        if validation.get("swift_contract_tests") != expected_values["swift_contract_tests"]:
            errors.append("PROJECT_STATUS.yaml Swift contract count is stale")
        if tested_locally.get("python_source_files_compiled") != expected_values["python_source_files_compiled"]:
            errors.append("delivery/IMPLEMENTATION_STATUS.yaml Python compile count is stale")
        if tested_locally.get("test_count") != expected_values["python_unit_tests"]:
            errors.append("delivery/IMPLEMENTATION_STATUS.yaml Python unit count is stale")
        if tested_locally.get("swift_contract_tests") != expected_values["swift_contract_tests"]:
            errors.append("delivery/IMPLEMENTATION_STATUS.yaml Swift contract count is stale")
    command_log = ROOT / "delivery/TEST_COMMANDS.jsonl"
    if command_log.is_file():
        try:
            records = [strict_load_json_text(line) for line in command_log.read_text(encoding="utf-8").splitlines() if line.strip()]
        except Exception as exc:
            errors.append(f"delivery/TEST_COMMANDS.jsonl is not strict JSONL: {exc}")
        else:
            by_command = {record.get("command"): record for record in records}
            compile_record = by_command.get("python3 -B tools/check_python_sources.py")
            unit_record = by_command.get("python3 -B tools/test_python_unit_suite.py")
            swift_record = next((record for record in records if record.get("command", "").startswith("swift test --package-path apps/ios")), None)
            if compile_record is None or str(expected_values["python_source_files_compiled"]) not in compile_record.get("notes", ""):
                errors.append("delivery/TEST_COMMANDS.jsonl Python compile record is stale")
            if unit_record is None or str(expected_values["python_unit_tests"]) not in unit_record.get("notes", ""):
                errors.append("delivery/TEST_COMMANDS.jsonl Python unit record is stale")
            if swift_record is None or str(expected_values["swift_contract_tests"]) not in swift_record.get("notes", ""):
                errors.append("delivery/TEST_COMMANDS.jsonl Swift contract record is stale")
    return errors


def check_runtime_report() -> list[str]:
    report = load_json("delivery/RUNTIME_ACTIVATION_REPORT.json")
    errors: list[str] = []
    errors.extend(schema_errors(report, "schemas/runtime-activation-report.schema.json", "runtime activation report"))
    if report.get("status") != "BLOCKED_NOT_OPERATIONAL":
        errors.append("runtime activation report must remain blocked")
    if report.get("runtimeDeployment") != "NOT_DEPLOYED":
        errors.append("runtime activation report must distinguish non-deployment")
    if report.get("writeGate") != "STATICALLY_DISABLED":
        errors.append("runtime activation report must distinguish static write disablement")
    if report.get("killSwitch") != "STATIC_FAIL_CLOSED_ONLY" or report.get("killSwitchOperationallyVerified") is not False:
        errors.append("runtime activation report must not imply an operational kill-switch endpoint")
    return errors


def check_mobile_target_binding() -> list[str]:
    errors: list[str] = []
    loose_draft = (ROOT / "apps/ios/ReviewScreen.swift").read_text(encoding="utf-8")
    loose_tests = (ROOT / "apps/ios/ReviewScreenTests.swift").read_text(encoding="utf-8")
    active_ui = (ROOT / "apps/ios/Sources/OfflineWalletUI/ReviewScreen.swift").read_text(encoding="utf-8")
    package = (ROOT / "apps/ios/Package.swift").read_text(encoding="utf-8")
    for label, text in (("apps/ios/ReviewScreen.swift", loose_draft), ("apps/ios/ReviewScreenTests.swift", loose_tests)):
        if "HISTORICAL / NOT ACTIVE" not in text or "NO EXECUTABLE" not in text:
            errors.append(f"{label} must remain an explicit non-active marker")
        if re.search(r"\b(import SwiftUI|import XCTest|struct\s+ReviewScreen|Button\s*\()", text):
            errors.append(f"{label} contains executable loose-draft code")
    if "OfflineWalletUI" not in package or 'path: "Sources/OfflineWalletUI"' not in package:
        errors.append("apps/ios/Package.swift must identify the authoritative OfflineWalletUI target")
    if "OfflineWalletContract" not in active_ui or "primaryActionEnabled" not in active_ui:
        errors.append("active iOS review screen must bind its action to the shared review contract")
    if "Button(\"最終確認へ\")" not in active_ui or ".disabled(!draft.primaryActionEnabled)" not in active_ui:
        errors.append("active iOS review screen must retain the fail-closed local action gate")
    return errors


def check_release_contract_docs() -> list[str]:
    errors: list[str] = []
    release_readme = (ROOT / "release/README.md").read_text(encoding="utf-8")
    if "DESIGN_ONLY" not in release_readme or "RELEASE_SUBJECT.json" not in release_readme:
        errors.append("release/README.md must list the design-only release output contract")
    source_pins = load_json("config/source-pins.json")
    expected_pins = load_json("examples/source-pins.json")
    if source_pins != expected_pins:
        errors.append("config/source-pins.json must be the canonical semantic copy of examples/source-pins.json")
    for item in source_pins.get("sources", []):
        name = item.get("name", "<unnamed>")
        if item.get("contentHash") is not None or item.get("contentSha256") is not None or item.get("status") != "MONITOR":
            errors.append(f"source pin {name} must remain explicitly unpinned in design-only package")
    decisions = load_json("delivery/GATE_DECISIONS.json")
    errors.extend(schema_errors(decisions, "schemas/gate-decisions.schema.json", "gate decisions"))
    configured = load_json("config/operational-readiness.json")
    expected_gate_ids = {gate["gateId"] for gate in configured["gates"]}
    decision_ids = {item.get("gateId") for item in decisions.get("decisions", [])}
    if decision_ids != expected_gate_ids:
        errors.append("delivery/GATE_DECISIONS.json must contain exactly the configured semantic gate IDs")
    expected_claims = {
        gate["gateId"]: {claim["claimId"] for claim in gate["claims"]}
        for gate in configured["gates"]
    }
    for decision in decisions.get("decisions", []):
        if set(decision.get("claimIds", [])) != expected_claims.get(decision.get("gateId"), set()):
            errors.append(f"gate decision claim set drift: {decision.get('gateId')}")
    return errors


def main() -> int:
    errors: list[str] = []
    for check in (
        check_canonical_traceability,
        check_policy_profiles,
        check_release_subject,
        check_release_artifacts,
        check_evidence_versioning,
        check_runtime_report,
        check_mobile_target_binding,
        check_release_contract_docs,
    ):
        try:
            errors.extend(check())
        except Exception as exc:
            errors.append(f"release contract check failed in {check.__name__}: {exc}")
    if errors:
        print("RELEASE CONTRACT VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("RELEASE CONTRACT VALIDATION PASSED")
    print("Canonical IDs, evidence versioning, canonical policy profiles, release subject, and runtime status: PASS")
    print("Production readiness is unchanged: BLOCKED_NOT_OPERATIONAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
