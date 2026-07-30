#!/usr/bin/env python3
"""Bind current local evidence to the 801/37/93 release-readiness model.

This tool is deliberately conservative.  It never upgrades a design claim to
production evidence, never reads secrets, and keeps per-ID coverage rows
unbound when the source matrix does not contain executable evidence for that
specific row.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from artifact_io import json_bytes, write_or_check


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "delivery/evidence/operationalization/EXECUTION_EVIDENCE_BINDING_20260729.json"
COVERAGE_PATH = Path("tests/coverage-matrix-v1.json")
READINESS_PATH = Path("config/operational-readiness.json")

EVIDENCE_PATHS = (
    Path("delivery/evidence/android/LOCAL_RECHECK_20260729.md"),
    Path("delivery/evidence/android/RELEASE_BUILD_RECHECK_20260729.md"),
    Path("delivery/evidence/android/RELEASE_BUILD_RECHECK_20260730.md"),
    Path("delivery/evidence/android/PIXEL9A_LOCAL_RECHECK_20260729.png"),
    Path("delivery/evidence/ios/LOCAL_RECHECK_20260729.md"),
    Path("delivery/evidence/ios/ARCHIVE_RECHECK_20260729.md"),
    Path("delivery/evidence/ios/APP_ATTEST_CLIENT_BUILD_20260729.md"),
    Path("delivery/evidence/ios/DEVELOPMENT_IPA_RECHECK_20260730.md"),
    Path("delivery/evidence/ios/iphone12-final-20260729.png"),
    Path("delivery/evidence/core/reference-tests-current.json"),
    Path("delivery/evidence/core/FUZZ_REPORT.json"),
    Path("delivery/evidence/core/PROPERTY_TEST_REPORT.json"),
    Path("delivery/evidence/protocol/HYPERLIQUID_TESTNET_READ_ONLY_20260729.json"),
    Path("delivery/evidence/provider/JPYC_PUBLIC_READ_ONLY_20260729.json"),
    Path("delivery/evidence/security/HSM_MPC_PUBLIC_EVIDENCE.json"),
    Path("delivery/evidence/source-pins/SOURCE_PIN_ACQUISITION_20260729.json"),
    Path("delivery/evidence/source-pins/SOURCE_PIN_ACQUISITION_CURRENT.json"),
    Path("delivery/evidence/source-pins/SOURCE_PIN_DRIFT_DISPOSITION.json"),
    Path("delivery/reports/FINAL_ENGINEERING_REPORT.md"),
    Path("delivery/reports/FINAL_OPERATIONS_REPORT.md"),
    Path("delivery/reports/FINAL_SECURITY_REPORT.md"),
    Path("services/ledger_store/store.py"),
    Path("tests/test_ledger_store.py"),
    Path("release/SBOM.spdx.json"),
    Path("release/PROVENANCE.json"),
)

GATE_STATUS: dict[str, tuple[str, str]] = {
    "ANDROID_RELEASE": ("LOCAL_PARTIAL_NOT_ACCEPTED", "Debug device proof and unsigned release artifacts do not satisfy signed production release evidence."),
    "IOS_RELEASE": ("DEVELOPMENT_SIGNED_DEVICE_AND_IPA_NOT_DISTRIBUTION", "Development signing, physical-device proof, and a development IPA exist; distribution signing, export, and Store evidence are absent."),
    "DETERMINISTIC_CORE": ("LOCAL_TESTS_NOT_RELEASE_ACCEPTANCE", "Local vector/property/fuzz evidence exists, but no independent release approval is attached."),
    "RECONCILIATION_LEDGER": ("LOCAL_IMPLEMENTATION_TESTED_NOT_OPERATIONAL", "SQLite ledger and outbox tests are local implementation evidence; no staging backend or production reconciliation exists."),
    "AI_NATURAL_LANGUAGE": ("LOCAL_VALIDATION_NOT_OPERATIONAL", "Local ambiguity and injection checks exist, but runtime model and production policy evidence are absent."),
    "CHATGPT_BOUNDARY": ("LOCAL_CONTRACT_ONLY_EXTERNAL_TERMS_UNVERIFIED", "The read-only boundary is represented locally; current legal/terms approval is not evidence-bound."),
    "UX_PLAIN_JAPANESE": ("LOCAL_UI_PARTIAL_NOT_ACCEPTED", "Local Android/iOS screen evidence is partial and is not a complete user-acceptance result."),
    "ACCESSIBILITY": ("PARTIAL_DEVICE_CHECK_NOT_FULL_MATRIX", "Limited device UI checks exist; VoiceOver/TalkBack, Dynamic Type, IME, and the full matrix are not complete."),
    "DEVICE_ATTESTATION": ("CLIENT_AND_FAIL_CLOSED_SERVER_CONTRACT_NOT_APPLE_VERIFIED", "App Attest client build and a fail-closed server evidence contract exist; Apple attestation-chain verification in a protected server is not proven."),
    "SUPPLY_CHAIN": ("LOCAL_ARTIFACTS_UNSIGNED", "SBOM and provenance files exist locally but are design-only and unsigned."),
    "KEY_CUSTODY_SIGNER": ("HSM_MPC_NOT_PROVISIONED", "The public-evidence checker is present, but no HSM/MPC tenant, attestation, ceremony, or signer is provisioned."),
    "HYPERLIQUID_INTEGRATION": ("PUBLIC_TESTNET_READ_ONLY_NOT_E2E", "The official Testnet read-only info smoke passed; account, write, lifecycle, and margin E2E did not run."),
    "JPYC_INTEGRATION": ("PUBLIC_READ_ONLY_NOT_CONTRACT_OR_E2E", "Official public pages were hashed; partner contract, exact network/contract, and transaction E2E are absent."),
    "TESTNET_E2E": ("PUBLIC_READ_ONLY_NOT_E2E", "Only a public read-only smoke was performed; no isolated Testnet identity or bounded write was used."),
}

GATE_EVIDENCE: dict[str, list[str]] = {
    "ANDROID_RELEASE": ["delivery/evidence/android/LOCAL_RECHECK_20260729.md", "delivery/evidence/android/RELEASE_BUILD_RECHECK_20260730.md", "delivery/evidence/android/PIXEL9A_LOCAL_RECHECK_20260729.png"],
    "IOS_RELEASE": ["delivery/evidence/ios/LOCAL_RECHECK_20260729.md", "delivery/evidence/ios/DEVELOPMENT_IPA_RECHECK_20260730.md", "delivery/evidence/ios/iphone12-final-20260729.png", "delivery/evidence/ios/APP_ATTEST_CLIENT_BUILD_20260729.md"],
    "DETERMINISTIC_CORE": ["delivery/evidence/core/reference-tests-current.json", "delivery/evidence/core/FUZZ_REPORT.json", "delivery/evidence/core/PROPERTY_TEST_REPORT.json"],
    "RECONCILIATION_LEDGER": ["services/ledger_store/store.py", "tests/test_ledger_store.py"],
    "AI_NATURAL_LANGUAGE": ["delivery/reports/FINAL_ENGINEERING_REPORT.md", "delivery/reports/FINAL_SECURITY_REPORT.md"],
    "CHATGPT_BOUNDARY": ["delivery/reports/FINAL_LEGAL_STORE_REPORT.md"],
    "UX_PLAIN_JAPANESE": ["delivery/evidence/android/LOCAL_RECHECK_20260729.md", "delivery/evidence/ios/LOCAL_RECHECK_20260729.md"],
    "ACCESSIBILITY": ["delivery/evidence/android/LOCAL_RECHECK_20260729.md", "delivery/evidence/ios/LOCAL_RECHECK_20260729.md"],
    "DEVICE_ATTESTATION": ["delivery/evidence/ios/APP_ATTEST_CLIENT_BUILD_20260729.md", "services/attestation/ios_app_attest.py", "tests/test_ios_app_attest.py"],
    "SUPPLY_CHAIN": ["release/SBOM.spdx.json", "release/PROVENANCE.json"],
    "KEY_CUSTODY_SIGNER": ["delivery/evidence/security/HSM_MPC_PUBLIC_EVIDENCE.json"],
    "HYPERLIQUID_INTEGRATION": ["delivery/evidence/protocol/HYPERLIQUID_TESTNET_READ_ONLY_20260729.json"],
    "JPYC_INTEGRATION": ["delivery/evidence/provider/JPYC_PUBLIC_READ_ONLY_20260729.json", "delivery/evidence/source-pins/SOURCE_PIN_ACQUISITION_CURRENT.json", "delivery/evidence/source-pins/SOURCE_PIN_DRIFT_DISPOSITION.json"],
    "TESTNET_E2E": ["delivery/evidence/protocol/HYPERLIQUID_TESTNET_READ_ONLY_20260729.json"],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def input_record(path: Path) -> dict[str, Any]:
    absolute = ROOT / path
    if not absolute.is_file():
        raise FileNotFoundError(path)
    return {"path": path.as_posix(), "sha256": sha256(absolute), "bytes": absolute.stat().st_size}


def build_binding(generated_at: str) -> dict[str, Any]:
    coverage = load_json(ROOT / COVERAGE_PATH)
    readiness = load_json(ROOT / READINESS_PATH)
    rows = coverage.get("rows")
    gates = readiness.get("gates")
    if not isinstance(rows, list) or len(rows) != 801:
        raise ValueError(f"coverage matrix must contain 801 rows, got {len(rows) if isinstance(rows, list) else 'invalid'}")
    if not isinstance(gates, list) or len(gates) != 37:
        raise ValueError(f"readiness model must contain 37 gates, got {len(gates) if isinstance(gates, list) else 'invalid'}")
    claims = [claim for gate in gates for claim in gate.get("claims", [])]
    if len(claims) != 93:
        raise ValueError(f"readiness model must contain 93 claims, got {len(claims)}")

    coverage_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("id"):
            raise ValueError("coverage row has no id")
        coverage_rows.append(
            {
                "id": row["id"],
                "kind": row.get("kind"),
                "source": row.get("source"),
                "runner": row.get("runner"),
                "matrixExecutionStatus": row.get("executionStatus"),
                "bindingStatus": "NOT_BOUND",
                "evidenceRefs": [],
                "productionEvidence": False,
                "unboundReason": "The current coverage matrix explicitly provides DOCUMENT_ONLY rows and no per-ID executable evidence path.",
            }
        )

    evidence_bundles = [input_record(path) | {"operationalStatus": "LOCAL_OR_READ_ONLY_NOT_PRODUCTION_ACCEPTANCE"} for path in EVIDENCE_PATHS]
    gate_bindings: list[dict[str, Any]] = []
    claim_bindings: list[dict[str, Any]] = []
    for gate in gates:
        gate_id = gate.get("gateId")
        status, blocker = GATE_STATUS.get(gate_id, ("EXTERNAL_EVIDENCE_REQUIRED", "No release-bound external evidence is present for this gate."))
        refs = GATE_EVIDENCE.get(gate_id, [])
        gate_bindings.append(
            {
                "gateId": gate_id,
                "category": gate.get("category"),
                "mandatory": gate.get("mandatory"),
                "bindingStatus": status,
                "acceptanceStatus": "NOT_ACCEPTED",
                "evidenceRefs": refs,
                "productionEvidence": False,
                "blocker": blocker,
            }
        )
        for claim in gate.get("claims", []):
            claim_bindings.append(
                {
                    "gateId": gate_id,
                    "claimId": claim.get("claimId"),
                    "titleJa": claim.get("titleJa"),
                    "configuredEvidenceTypes": claim.get("evidenceTypes", []),
                    "configuredEnvironments": claim.get("environments", []),
                    "issuerRoles": claim.get("issuerRoles", []),
                    "reviewerRoles": claim.get("reviewerRoles", []),
                    "bindingStatus": status,
                    "acceptanceStatus": "NOT_ACCEPTED",
                    "evidenceRefs": refs,
                    "productionEvidence": False,
                    "blocker": blocker,
                }
            )

    return {
        "schemaVersion": "1.0",
        "bindingId": "operationalization-evidence-binding-2026-07-29.3",
        "generatedAt": generated_at,
        "status": "LOCAL_EVIDENCE_BOUND_EXTERNAL_BLOCKERS_REMAIN",
        "approvalStatus": "NOT_A_RELEASE_APPROVAL",
        "productionEvidence": False,
        "productionWritePermitted": False,
        "mainnetCanaryPerformed": False,
        "walletConnectionUsed": False,
        "secretPolicy": "No passwords, tokens, 2FA values, private keys, seed phrases, HSM shares, or response bodies were read or stored.",
        "inputs": [input_record(COVERAGE_PATH), input_record(READINESS_PATH)],
        "evidenceBundles": evidence_bundles,
        "summary": {
            "coverageRows": len(coverage_rows),
            "coverageRowsBoundToPerIdExecutionEvidence": 0,
            "coverageRowsUnbound": len(coverage_rows),
            "gates": len(gate_bindings),
            "gatesWithLocalOrReadOnlyContext": sum(bool(item["evidenceRefs"]) for item in gate_bindings),
            "acceptedGates": 0,
            "claims": len(claim_bindings),
            "claimsWithLocalOrReadOnlyContext": sum(bool(item["evidenceRefs"]) for item in claim_bindings),
            "acceptedClaims": 0,
        },
        "coverageBindings": coverage_rows,
        "gateBindings": gate_bindings,
        "claimBindings": claim_bindings,
        "limitations": [
            "Per-ID execution evidence for the 801 coverage rows is not supplied by the current matrix; every row remains explicitly unbound.",
            "Local tests, builds, screenshots, read-only HTTP retrieval, and design artifacts are contextual evidence only and cannot satisfy production gates by themselves.",
            "The canonical design evidence-index.json and release/SOURCE_PINS.json remain design-only; this binding artifact does not upgrade either one.",
            "Independent audit, legal/store approval, protected repository controls, release signing, staging backend, HSM/MPC signer, Testnet E2E, and runtime activation remain external blockers.",
        ],
    }


def verify_binding(value: dict[str, Any]) -> None:
    summary = value.get("summary", {})
    coverage = value.get("coverageBindings", [])
    gates = value.get("gateBindings", [])
    claims = value.get("claimBindings", [])
    if summary.get("coverageRows") != 801 or len(coverage) != 801:
        raise ValueError("binding coverage count is not 801")
    if summary.get("gates") != 37 or len(gates) != 37:
        raise ValueError("binding gate count is not 37")
    if summary.get("claims") != 93 or len(claims) != 93:
        raise ValueError("binding claim count is not 93")
    if summary.get("coverageRowsBoundToPerIdExecutionEvidence") != 0:
        raise ValueError("per-ID evidence must remain unbound until supplied")
    if summary.get("acceptedGates") != 0 or summary.get("acceptedClaims") != 0:
        raise ValueError("this artifact cannot accept production gates or claims")
    if value.get("productionEvidence") is not False or value.get("productionWritePermitted") is not False:
        raise ValueError("production flags must remain false")
    for row in coverage:
        if row.get("bindingStatus") != "NOT_BOUND" or row.get("productionEvidence") is not False:
            raise ValueError(f"coverage row was unexpectedly accepted: {row.get('id')}")
    for item in gates + claims:
        if item.get("acceptanceStatus") != "NOT_ACCEPTED" or item.get("productionEvidence") is not False:
            raise ValueError(f"gate or claim was unexpectedly accepted: {item.get('gateId')}/{item.get('claimId')}")
        for ref in item.get("evidenceRefs", []):
            if not (ROOT / ref).is_file():
                raise FileNotFoundError(ref)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--generated-at", default="2026-07-29T14:05:00Z")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if args.check and not output.is_file():
        raise FileNotFoundError(output)
    if args.write:
        value = build_binding(args.generated_at)
        verify_binding(value)
        write_or_check(output, json_bytes(value), check=False, label=output.relative_to(ROOT).as_posix())
    elif args.check:
        value = build_binding(args.generated_at)
        verify_binding(value)
        write_or_check(output, json_bytes(value), check=True, label=output.relative_to(ROOT).as_posix())
    value = load_json(output)
    verify_binding(value)
    print(f"OPERATIONALIZATION_EVIDENCE_BINDING=PASS coverage=801 gates=37 claims=93 acceptedGates=0 acceptedClaims=0 output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
