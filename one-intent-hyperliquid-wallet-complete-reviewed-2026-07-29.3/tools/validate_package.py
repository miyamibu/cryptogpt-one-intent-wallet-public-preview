#!/usr/bin/env python3
from __future__ import annotations

import sys
sys.dont_write_bytecode = True

import hashlib
import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from canonical_hashes import CanonicalizationError, expected_hashes, source_text_hash, strict_load_json
from package_metadata import ROOT, load_package_metadata
from strict_data import strict_load_yaml
from archive_policy import member_name_problems
from operational_readiness import evaluate_design_package, required_claims

METADATA = load_package_metadata()
PACKAGE_VERSION = METADATA.version
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}

SCHEMA_EXAMPLES = {
    "schemas/action-plan.schema.json": ["examples/action-plan-btc-long.json"],
    "schemas/execution-capsule.schema.json": [
        "examples/execution-capsule-perp.json",
        "examples/execution-capsule-composite.json",
        "examples/execution-capsule-ios-saved-withdrawal.json",
    ],
    "schemas/authorization-envelope.schema.json": [
        "examples/authorization-envelope-protected-confirmation.json",
        "examples/authorization-envelope-ios-app-attest.json",
    ],
    "schemas/policy-profile.schema.json": [
        "examples/policy-profile-personal.json",
        "examples/policy-profile-production.json",
    ],
    "schemas/execution-status.schema.json": ["examples/execution-status-partial.json"],
    "schemas/source-pin.schema.json": ["examples/source-pins.json"],
    "schemas/fee-readiness-plan.schema.json": ["examples/fee-readiness-jpyc-only.json"],
    "schemas/manual-fallback.schema.json": ["examples/manual-fallback-zero-gas.json"],
    "schemas/asset-registry.schema.json": ["examples/asset-registry-simulation.json"],
    "schemas/fee-route-capability.schema.json": ["examples/fee-route-capability-simulation.json"],
    "schemas/operation-quote.schema.json": ["examples/operation-quote-simulation.json"],
    "schemas/operational-readiness-config.schema.json": ["config/operational-readiness.json"],
    "schemas/operational-trust-policy.schema.json": [
        "config/operational-trust-policy.template.json",
        "config/operational-trust-policy.production.json",
    ],
    "schemas/operational-evidence-statement.schema.json": ["examples/operational-evidence-statement-blocked.json"],
    "schemas/operational-review-approval.schema.json": ["examples/operational-review-approval-rejected.json"],
    "schemas/operational-evidence-index.schema.json": ["delivery/evidence-index.json"],
    "schemas/operational-readiness-report.schema.json": ["delivery/OPERATIONAL_READINESS_REPORT.json"],
    "schemas/trusted-time-attestation.schema.json": ["examples/trusted-time-attestation-untrusted.json"],
    "schemas/runtime-state-bundle.schema.json": ["examples/runtime-state-bundle-stopped.json"],
    "schemas/runtime-control-plane-lease.schema.json": ["examples/runtime-control-plane-lease-disabled.json"],
    "schemas/per-operation-authorization.schema.json": ["examples/per-operation-authorization-denied.json"],
    "schemas/account-authorization-binding.schema.json": ["examples/account-authorization-binding-suspended.json"],
    "schemas/runtime-authorization-policy.schema.json": [
        "config/runtime-authorization-policy.template.json",
        "config/runtime-policy.production.json",
    ],
    "schemas/runtime-authorization-decision.schema.json": [],
    "schemas/resolved-intent-v2.schema.json": [],
    "schemas/operation-spec-v2.schema.json": [],
    "schemas/user-review-receipt-v2.schema.json": [],
    "schemas/runtime-decision-envelope-v2.schema.json": [],
    "schemas/atomic-signer-request-v2.schema.json": [],
    "schemas/status-manifest.v2.schema.json": ["config/status-manifest.v2.json"],
    "schemas/production-policy-pointer.schema.json": [],
    "schemas/release-subject.schema.json": ["release/release-subject.json"],
    "schemas/external-blocker-traceability.schema.json": ["delivery/external-blocker-traceability.json"],
    "schemas/gate-decisions.schema.json": ["delivery/GATE_DECISIONS.json"],
    "schemas/runtime-activation-report.schema.json": ["delivery/RUNTIME_ACTIVATION_REPORT.json"],
}

REQUIRED_FILES = [
    "RUNNABILITY_AND_STATUS.md",
    "29_CROSS_PLATFORM_ARCHITECTURE.md",
    "30_MULTI_PERSPECTIVE_REVIEW.md",
    "31_DESIGN_SYSTEM_PIXEL_SPEC.md",
    "32_SCREEN_BY_SCREEN_UX_SPEC.md",
    "33_IOS_APP_STORE_AND_DISTRIBUTION_GATES.md",
    "34_CODEX_REMAINING_WORK_MASTER_PROMPT.md",
    "35_PLATFORM_SECURITY_CAPABILITY_MATRIX.md",
    "36_IMPLEMENTATION_DEFINITION_OF_DONE.md",
    "37_UI_ADVERSARIAL_REVIEW.md",
    "38_ADMIN_OPERATIONS_CONSOLE_SPEC.md",
    "39_ACCESSIBILITY_LOCALIZATION_TEST_MATRIX.md",
    "40_EVIDENCE_BUNDLE_CONTRACT.md",
    "41_PLAIN_JAPANESE_AND_JPYC_FEE_READINESS.md",
    "42_NATURAL_LANGUAGE_AND_CHATGPT_BOUNDARY.md",
    "43_MANUAL_FALLBACK_PLAYBOOK.md",
    "44_ADVERSARIAL_REVIEW_AND_RESOLUTION.md",
    "45_RELEASE_ASSURANCE_CASE.md",
    "46_PIXEL_AND_INTERACTION_AUDIT.md",
    "47_FEE_ROUTE_AND_ASSET_REGISTRY_SPEC.md",
    "48_RELEASE_SOURCE_PINNING_AND_EXPIRY.md",
    "49_REPRODUCIBLE_BUILD_AND_ARCHIVE_SAFETY.md",
    "50_FINAL_MULTI_PERSPECTIVE_REVIEW.md",
    "54_CANONICAL_QUOTE_REGISTRY_AND_ATOMIC_SIGNER.md",
    "FINAL_DELIVERY_INDEX.md",
    "AUDIT_ITERATION_LOG.md",
    "START_HERE.html",
    "START_HERE.css",
    "PROJECT_STATUS.yaml",
    f"CHANGELOG_{PACKAGE_VERSION}.md",
    "EXTERNAL_ACTIONS_REQUIRED.md",
    "PACKAGE_CONTENT_INDEX.md",
    "CODEX_START_HERE.md",
    "codex/CODEX_EXTERNAL_OPERATIONALIZATION_PROMPT_2026-07-29.md",
    "mobile/IOS_SECURITY_REQUIREMENTS.md",
    "apps/android/build.gradle.kts",
    "apps/android/app/gradle.lockfile",
    "apps/android/gradle/verification-metadata.xml",
    "design/DESIGN_TOKENS.json",
    "design/PIXEL_QA_CHECKLIST.md",
    "prototype/index.html",
    "prototype/styles.css",
    "prototype/app.js",
    "tools/run_full_validation.py",
    "tools/check_python_sources.py",
    "tools/test_python_unit_suite.py",
    "tools/test_canonical_properties.py",
    "tools/test_canonical_fuzz.py",
    "tools/canonical_quality.py",
    "tools/run_local_sandbox.py",
    "services/local_sandbox/server.py",
    "services/local_sandbox/README.md",
    "tests/test_security_hardening.py",
    "tools/test_start_here.py",
    "tools/generate_reports.py",
    "tests/start-here-layout-evidence.json",
    "prototype/screenshots/iphone-perp-before-confirmation.png",
    "prototype/screenshots/iphone-perp-after-confirmation.png",
    "prototype/screenshots/pixel9a-fee-dark.png",
    "prototype/screenshots/iphone-large-withdraw.png",
    "prototype/screenshots/pixel9a-manual.png",
    "prototype/screenshots/iphone-limited-authorization.png",
    "prototype/screenshots/android-tall-partial-dark.png",
    "prototype/screenshots/iphone-jpyc-large.png",
    "prototype/screenshots/iphone-se-composite-top.png",
    "prototype/screenshots/android-compact-spot-large-dark.png",
    "tests/prototype-visual-evidence.json",
    "tests/plain-japanese-copy-cases.json",
    "codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md",
    "examples/execution-capsule-ios-saved-withdrawal.json",
    "examples/source-text-btc-long.txt",
    "examples/authorization-envelope-ios-app-attest.json",
    "README_FIRST.md",
    "COMPLETE_SPEC.md",
    "FINAL_AUDIT_REPORT.md",
    "VALIDATION_REPORT.md",
    "00_ASSURANCE_STATEMENT.md",
    "01_FACT_CHECK_AND_CORRECTIONS.md",
    "08_THREAT_MODEL.md",
    "11_LEGAL_COMPLIANCE_GATES_JP.md",
    "12_TEST_AND_RELEASE_GATES.md",
    "17_CODEX_IMPLEMENTATION_MASTER_PROMPT.md",
    "22_GO_NO_GO_MATRIX.md",
    "24_KNOWN_LOOPHOLE_REGISTER.md",
    "25_SECURITY_INVARIANTS.md",
    "26_TRUSTED_DISPLAY_AND_STATE_QUORUM.md",
    "27_DISTRIBUTION_AND_STORE_GATES.md",
    "contracts/openapi.yaml",
    "contracts/chatgpt-readonly-openapi.yaml",
    "contracts/error-catalog.yaml",
    "config/feature-gates.example.yaml",
    "config/build-metadata.json",
    "config/toolchain-lock.json",
    "config/release-source-policy.yaml",
    "config/user-facing-terms.ja.json",
    "references/SOURCES.md",
    "schemas/authorization-envelope.schema.json",
    "schemas/asset-registry.schema.json",
    "schemas/fee-route-capability.schema.json",
    "schemas/fee-readiness-plan.schema.json",
    "schemas/manual-fallback.schema.json",
    "schemas/operation-quote.schema.json",
    "examples/operation-quote-simulation.json",
    "examples/authorization-envelope-protected-confirmation.json",
    "examples/asset-registry-simulation.json",
    "examples/fee-route-capability-simulation.json",
    "examples/fee-readiness-jpyc-only.json",
    "examples/manual-fallback-zero-gas.json",
    "tools/canonical_hashes.py",
    "tools/strict_data.py",
    "tools/package_metadata.py",
    "tools/archive_policy.py",
    "tools/test_validation_harness.py",
    "tools/update_example_hashes.py",
    "tools/check_plain_japanese.py",
    "tools/check_archive_safety.py",
    "tools/check_security_hygiene.py",
    "tools/check_links_and_markdown.py",
    "tools/adversarial_audit.py",
    "tools/build_release.py",
    "tools/build_reproducible_zip.py",
    "tools/verify_zip.py",
    "tests/loophole-regression-cases.json",
    "51_OPERATIONAL_READINESS_AND_RUNTIME_ACTIVATION.md",
    "52_FINAL_OPERATIONAL_GAP_REVIEW.md",
    "53_CODEX_OPERATIONAL_COMPLETION_CONTRACT.md",
    "config/operational-readiness.json",
    "config/operational-trust-policy.template.json",
    "config/operational-trust-policy.production.json",
    "config/runtime-policy.production.json",
    "config/source-pins.json",
    "delivery/evidence-index.json",
    "delivery/OPERATIONAL_READINESS_REPORT.json",
    "delivery/GATE_DECISIONS.json",
    "delivery/RUNTIME_ACTIVATION_REPORT.json",
    "delivery/EXTERNAL_BLOCKERS.md",
    "delivery/external-blocker-traceability.json",
    "delivery/evidence/README.md",
    "delivery/evidence/core/reference-tests.json",
    "delivery/evidence/core/reference-tests-current.json",
    "delivery/evidence/core/PROPERTY_TEST_REPORT.json",
    "delivery/evidence/core/FUZZ_REPORT.json",
    "delivery/evidence/security/REVIEW_GPT56_SOL_MAX.md",
    "release/README.md",
    "release/release-subject.json",
    "release/RELEASE_SUBJECT.json",
    "release/SOURCE_PINS.json",
    "release/SBOM.spdx.json",
    "release/PROVENANCE.json",
    "release/ARTIFACT_HASHES.txt",
    "release/BUILD_ENVIRONMENT.md",
    "release/REPRODUCIBILITY_REPORT.md",
    "release/CODEX_EXECUTION_REPORT.md",
    "release/UNRESOLVED_EXTERNAL_BLOCKERS.md",
    "release/OPERATIONAL_HANDOFF.md",
    "shared/mobile-review-contract-v1.tsv",
    "shared/canonical-vectors-v1.json",
    "tests/coverage-matrix-v1.json",
    "schemas/operational-readiness-config.schema.json",
    "schemas/operational-trust-policy.schema.json",
    "schemas/production-policy-pointer.schema.json",
    "schemas/release-subject.schema.json",
    "schemas/external-blocker-traceability.schema.json",
    "schemas/gate-decisions.schema.json",
    "schemas/runtime-activation-report.schema.json",
    "schemas/operational-evidence-statement.schema.json",
    "schemas/operational-review-approval.schema.json",
    "schemas/operational-evidence-index.schema.json",
    "schemas/operational-readiness-report.schema.json",
    "schemas/trusted-time-attestation.schema.json",
    "schemas/runtime-state-bundle.schema.json",
    "schemas/runtime-control-plane-lease.schema.json",
    "schemas/per-operation-authorization.schema.json",
    "schemas/account-authorization-binding.schema.json",
    "schemas/runtime-authorization-policy.schema.json",
    "schemas/runtime-authorization-decision.schema.json",
    "schemas/resolved-intent-v2.schema.json",
    "schemas/operation-spec-v2.schema.json",
    "schemas/user-review-receipt-v2.schema.json",
    "schemas/runtime-decision-envelope-v2.schema.json",
    "schemas/atomic-signer-request-v2.schema.json",
    "examples/operational-evidence-statement-blocked.json",
    "examples/operational-review-approval-rejected.json",
    "examples/trusted-time-attestation-untrusted.json",
    "examples/runtime-state-bundle-stopped.json",
    "examples/runtime-control-plane-lease-disabled.json",
    "examples/per-operation-authorization-denied.json",
    "examples/account-authorization-binding-suspended.json",
    "config/runtime-authorization-policy.template.json",
    "tools/artifact_io.py",
    "tools/secure_tree.py",
    "tools/prepare_release_artifacts.py",
    "tools/operational_readiness.py",
    "tools/generate_operational_readiness_report.py",
    "tools/check_operational_readiness.py",
    "tools/test_operational_readiness_positive.py",
    "tools/test_operational_readiness_negative.py",
    "tools/runtime_authorization.py",
    "tools/runtime_authorization_test_fixture.py",
    "tools/check_runtime_authorization.py",
    "tools/check_release_contract.py",
    "tools/check_toolchain_lock.py",
    "tools/check_shared_canonical_vectors.py",
    "tools/check_coverage_matrix.py",
    "tools/check_mobile_contract_vectors.py",
    "tools/stage_release.py",
    "tools/generate_release_contract_artifacts.py",
    "tools/generate_coverage_matrix.py",
    "tools/generate_current_validation_evidence.py",
    "tools/release_digest_policy.py",
    "tools/test_runtime_authorization_positive.py",
    "tools/test_runtime_authorization_negative.py",
    "manifest.json",
    "SHA256SUMS.txt",
]


def load_json(rel: str) -> Any:
    return strict_load_json(ROOT / rel)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def check_files() -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing required file: {rel}")
        elif path.stat().st_size == 0:
            errors.append(f"empty required file: {rel}")
    for path in ROOT.rglob("*"):
        if path.is_symlink():
            errors.append(f"symlink prohibited in package: {path.relative_to(ROOT)}")
        if "__pycache__" in path.parts or (path.is_file() and path.suffix == ".pyc"):
            errors.append(f"generated Python debris prohibited: {path.relative_to(ROOT)}")
        if path.is_file() and path.name in {".env", "id_rsa", "id_ed25519"}:
            errors.append(f"secret-like file prohibited: {path.relative_to(ROOT)}")
        if path.is_file() and path.suffix.lower() in {".pem", ".p12", ".pfx", ".jks", ".keystore"}:
            errors.append(f"key container prohibited: {path.relative_to(ROOT)}")
    return errors


def check_strict_json() -> list[str]:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.json")):
        try:
            strict_load_json(path)
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)}: strict JSON error: {exc}")
    return errors


def check_schema_and_examples() -> list[str]:
    errors: list[str] = []
    checker = FormatChecker()
    schema_paths = sorted((ROOT / "schemas").glob("*.json"))
    mapped = set(SCHEMA_EXAMPLES)
    actual = {path.relative_to(ROOT).as_posix() for path in schema_paths}
    if mapped != actual:
        errors.append(f"schema/example mapping mismatch; missing={sorted(actual - mapped)}, extra={sorted(mapped - actual)}")

    ids: dict[str, str] = {}
    for path in schema_paths:
        rel = path.relative_to(ROOT).as_posix()
        try:
            schema = strict_load_json(path)
        except Exception as exc:
            errors.append(f"{rel}: strict JSON error: {exc}")
            continue
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            errors.append(f"{rel}: invalid schema: {exc}")
            continue
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append(f"{rel}: must declare JSON Schema draft 2020-12")
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id.startswith("https://"):
            errors.append(f"{rel}: missing absolute HTTPS $id")
        elif schema_id in ids:
            errors.append(f"duplicate schema $id {schema_id}: {ids[schema_id]} and {rel}")
        else:
            ids[schema_id] = rel

        def walk_refs(value: Any) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    if key == "$ref" and isinstance(item, str):
                        if item.startswith("#"):
                            try:
                                _resolve_json_pointer(schema, item[1:])
                            except Exception:
                                errors.append(f"{rel}: unresolved internal $ref {item}")
                        else:
                            file_part, _, fragment = item.partition("#")
                            target = (path.parent / file_part).resolve()
                            try:
                                target.relative_to(ROOT.resolve())
                            except ValueError:
                                errors.append(f"{rel}: $ref escapes package: {item}")
                                continue
                            if not target.exists():
                                errors.append(f"{rel}: unresolved external $ref {item}")
                            elif fragment:
                                try:
                                    _resolve_json_pointer(strict_load_json(target), fragment)
                                except Exception:
                                    errors.append(f"{rel}: unresolved external fragment {item}")
                    else:
                        walk_refs(item)
            elif isinstance(value, list):
                for item in value:
                    walk_refs(item)

        walk_refs(schema)
        validator = Draft202012Validator(schema, format_checker=checker)
        for example_rel in SCHEMA_EXAMPLES.get(rel, []):
            try:
                instance = load_json(example_rel)
            except Exception as exc:
                errors.append(f"{example_rel}: strict JSON error: {exc}")
                continue
            for err in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
                errors.append(f"{example_rel}: {list(err.path)}: {err.message}")

    source_schema = load_json("schemas/source-pin.schema.json")
    yaml_instance = strict_load_yaml(ROOT / "config/source-pins.example.yaml")
    for err in Draft202012Validator(source_schema, format_checker=checker).iter_errors(yaml_instance):
        errors.append(f"config/source-pins.example.yaml: {list(err.path)}: {err.message}")
    if yaml_instance != load_json("examples/source-pins.json"):
        errors.append("source pin JSON and YAML copies differ semantically")
    return errors

def check_yaml() -> list[str]:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.yaml")) + sorted(ROOT.rglob("*.yml")):
        try:
            data = strict_load_yaml(path)
            if data is None:
                errors.append(f"{path.relative_to(ROOT)}: empty YAML")
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)}: YAML parse error: {exc}")
    return errors


def _resolve_json_pointer(doc: Any, pointer: str) -> Any:
    if pointer in {"", "/"}:
        return doc
    cur = doc
    for raw in pointer.lstrip("/").split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, list):
            cur = cur[int(token)]
        elif isinstance(cur, dict) and token in cur:
            cur = cur[token]
        else:
            raise KeyError(pointer)
    return cur


def check_openapi() -> list[str]:
    errors: list[str] = []
    methods = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}

    def resolve_ref(doc: Any, source: Path, ref: str) -> Any:
        if ref.startswith("#"):
            return _resolve_json_pointer(doc, ref[1:])
        file_part, _, fragment = ref.partition("#")
        target = (source.parent / file_part).resolve()
        target.relative_to(ROOT.resolve())
        if not target.exists():
            raise FileNotFoundError(target)
        ext = strict_load_json(target) if target.suffix == ".json" else strict_load_yaml(target)
        return _resolve_json_pointer(ext, fragment) if fragment else ext

    def inspect_contract(rel: str) -> tuple[Any, dict[str, str]]:
        source = ROOT / rel
        doc = strict_load_yaml(source)
        if not isinstance(doc, dict) or doc.get("openapi") != "3.1.0":
            errors.append(f"{rel}: expected OpenAPI 3.1.0 object")
            return doc, {}
        for key in ("info", "paths", "components"):
            if key not in doc:
                errors.append(f"{rel}: missing {key}")
        servers = doc.get("servers", [])
        if not servers or any(not isinstance(x, dict) or not str(x.get("url", "")).startswith("https://") or ".invalid" not in str(x.get("url", "")) for x in servers):
            errors.append(f"{rel}: package contracts must use non-routable HTTPS .invalid servers")
        operation_ids: dict[str, str] = {}
        for route, path_item in doc.get("paths", {}).items():
            if not isinstance(path_item, dict):
                errors.append(f"{rel}: path item must be an object: {route}")
                continue
            template_names = set(re.findall(r"\{([^{}]+)\}", route))
            for method, op in path_item.items():
                if method not in methods:
                    continue
                label = f"{method.upper()} {route}"
                if not isinstance(op, dict):
                    errors.append(f"{rel}: {label} operation must be an object")
                    continue
                op_id = op.get("operationId")
                if not isinstance(op_id, str) or not op_id:
                    errors.append(f"{rel}: {label} missing operationId")
                elif op_id in operation_ids:
                    errors.append(f"{rel}: duplicate operationId {op_id}: {operation_ids[op_id]} and {label}")
                else:
                    operation_ids[op_id] = label
                if not isinstance(op.get("summary"), str) or not op.get("summary", "").strip():
                    errors.append(f"{rel}: {label} missing summary")
                responses = op.get("responses")
                if not isinstance(responses, dict) or not responses:
                    errors.append(f"{rel}: {label} missing responses")
                declared_path: set[str] = set()
                for raw_param in list(path_item.get("parameters", [])) + list(op.get("parameters", [])):
                    try:
                        param = resolve_ref(doc, source, raw_param["$ref"]) if isinstance(raw_param, dict) and "$ref" in raw_param else raw_param
                    except Exception as exc:
                        errors.append(f"{rel}: {label} unresolved parameter ref: {exc}")
                        continue
                    if isinstance(param, dict) and param.get("in") == "path":
                        name = param.get("name")
                        if param.get("required") is not True:
                            errors.append(f"{rel}: {label} path parameter {name!r} must be required")
                        if isinstance(name, str):
                            declared_path.add(name)
                if declared_path != template_names:
                    errors.append(f"{rel}: {label} path template parameters differ: template={sorted(template_names)}, declared={sorted(declared_path)}")

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    if key == "$ref" and isinstance(item, str):
                        try:
                            resolve_ref(doc, source, item)
                        except Exception:
                            errors.append(f"{rel}: unresolved or escaping $ref {item}")
                    else:
                        walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)

        walk(doc)
        return doc, operation_ids

    rel = "contracts/openapi.yaml"
    doc, operations = inspect_contract(rel)
    execute = doc.get("paths", {}).get("/v1/plans/{planId}/execute", {}).get("post", {})
    execute_description = execute.get("description", "")
    if not all(word in execute_description for word in ("LLM", "ChatGPT", "MCP")):
        errors.append("first-party execute endpoint must explicitly prohibit LLM/ChatGPT/MCP exposure")
    auth = doc.get("components", {}).get("schemas", {}).get("AuthorizationRequest", {})
    if auth.get("$ref") != "../schemas/authorization-envelope.schema.json":
        errors.append("AuthorizationRequest must reference authorization-envelope.schema.json")
    authorize_responses = (
        doc.get("paths", {})
        .get("/v1/plans/{planId}/authorize", {})
        .get("post", {})
        .get("responses", {})
    )
    receipt_schema = (
        authorize_responses.get("201", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    if receipt_schema.get("$ref") != "#/components/schemas/AuthorizationReceiptResponse":
        errors.append("authorize must return a signed one-time receipt in a 201 response")
    if "204" in authorize_responses:
        errors.append("authorize must not hide receipt creation behind an empty 204 response")
    receipt = doc.get("components", {}).get("schemas", {}).get("AuthorizationReceiptResponse", {})
    receipt_required = set(receipt.get("required", []))
    if not {
        "authorizationReceipt",
        "authorizationReceiptHash",
        "expiresAt",
        "oneTimeChallenge",
        "signerKeyId",
        "signatureAlgorithm",
        "signature",
    }.issubset(receipt_required):
        errors.append("AuthorizationReceiptResponse lacks signed receipt binding fields")
    bearer_description = doc.get("components", {}).get("securitySchemes", {}).get("bearerAuth", {}).get("description", "")
    if "sender" not in bearer_description.lower() or "DPoP" not in bearer_description:
        errors.append("first-party bearer authentication must be explicitly sender-constrained")

    required_headers = {
        "/v1/intents/parse": {"IdempotencyKey", "DPoP"},
        "/v1/plans/compile": {"IdempotencyKey", "DPoP"},
        "/v1/plans/{planId}/refresh": {"IdempotencyKey", "DPoP"},
        "/v1/plans/{planId}/authorize": {"IdempotencyKey", "CapsuleHash", "DeviceChallenge", "DeviceEvidenceHash", "DPoP"},
        "/v1/plans/{planId}/execute": {"IdempotencyKey", "CapsuleHash", "AuthorizationReceiptHash", "DPoP"},
        "/v1/plans/{planId}/resume": {"IdempotencyKey", "CapsuleHash", "AuthorizationReceiptHash", "DPoP"},
        "/v1/emergency/cancel-all-orders": {"IdempotencyKey", "EmergencyActionDigest", "DeviceChallenge", "DeviceEvidenceHash", "DPoP"},
        "/v1/emergency/disable-writes": {"IdempotencyKey", "EmergencyActionDigest", "DeviceChallenge", "DeviceEvidenceHash", "DPoP"},
    }
    for route, expected in required_headers.items():
        op = doc.get("paths", {}).get(route, {}).get("post", {})
        refs = {
            str(param.get("$ref", "")).rsplit("/", 1)[-1]
            for param in op.get("parameters", [])
            if isinstance(param, dict) and "$ref" in param
        }
        if not expected.issubset(refs):
            errors.append(f"{rel}: POST {route} lacks binding/auth headers: {sorted(expected - refs)}")
        if op.get("security") == []:
            errors.append(f"{rel}: POST {route} must not disable authentication")

    chat_rel = "contracts/chatgpt-readonly-openapi.yaml"
    chat, chat_ops = inspect_contract(chat_rel)
    expected_ops = {
        "getReadOnlyStatus",
        "getPlainJapaneseTerm",
        "explainNonTransactionalError",
        "getGenericSafetyHelp",
    }
    if set(chat_ops) != expected_ops:
        errors.append(f"{chat_rel}: operation set differs from fixed read-only allowlist: {sorted(set(chat_ops) ^ expected_ops)}")
    expected_path_methods = {
        "/v1/support/status/{referenceId}": {"get"},
        "/v1/support/glossary/{termId}": {"get"},
        "/v1/support/explain-error": {"post"},
        "/v1/support/safety-help": {"post"},
    }
    actual_path_methods = {
        str(path): {str(method).lower() for method in item if str(method).lower() in HTTP_METHODS}
        for path, item in chat.get("paths", {}).items()
        if isinstance(item, dict)
    }
    if actual_path_methods != expected_path_methods:
        errors.append(f"{chat_rel}: path/method allowlist mismatch: {actual_path_methods!r}")
    if any(label.startswith(("PUT ", "PATCH ", "DELETE ")) for label in chat_ops.values()):
        errors.append(f"{chat_rel}: state-changing HTTP methods are prohibited")
    chat_text = (ROOT / chat_rel).read_text(encoding="utf-8")
    for forbidden in (
        "../schemas/execution-capsule",
        "../schemas/authorization-envelope",
        "walletconnect",
    ):
        if forbidden.lower() in chat_text.lower():
            errors.append(f"{chat_rel}: prohibited executable contract marker: {forbidden}")
    schemas = chat.get("components", {}).get("schemas", {})
    exact_request_fields = {
        "ErrorExplanationRequest": {"errorCode", "locale", "supportReference"},
        "SafetyHelpRequest": {"topic", "locale"},
    }
    forbidden_request_fields = {
        "amount", "quantity", "address", "recipient", "destination", "asset", "network", "chain",
        "transaction", "tx", "order", "trade", "swap", "transfer", "withdrawal", "deposit", "approval",
        "signature", "challenge", "calldata", "payload", "deepLink", "url",
    }
    for schema_name, expected_fields in exact_request_fields.items():
        properties = set(schemas.get(schema_name, {}).get("properties", {}))
        if properties != expected_fields:
            errors.append(f"{chat_rel}: {schema_name} property allowlist mismatch: {sorted(properties)}")
        if {x.lower() for x in properties} & {x.lower() for x in forbidden_request_fields}:
            errors.append(f"{chat_rel}: {schema_name} accepts transaction-like fields")
    if schemas.get("ReadOnlyStatus", {}).get("properties", {}).get("writeAvailableHere", {}).get("const") is not False:
        errors.append(f"{chat_rel}: ReadOnlyStatus must hard-code writeAvailableHere=false")
    if schemas.get("SupportExplanation", {}).get("properties", {}).get("executable", {}).get("const") is not False:
        errors.append(f"{chat_rel}: SupportExplanation must hard-code executable=false")
    support_properties = schemas.get("SupportExplanation", {}).get("properties", {})
    if support_properties.get("neutralHandoffJa", {}).get("const") != "独立したウォレットアプリを開いて、内容を確認してください。":
        errors.append(f"{chat_rel}: neutral handoff must be one fixed non-transactional string")
    if not {"catalogEntryId", "catalogVersion"}.issubset(set(schemas.get("SupportExplanation", {}).get("required", []))):
        errors.append(f"{chat_rel}: fixed support catalog identity/version are required")
    status_schema = schemas.get("ReadOnlyStatus", {})
    status_properties = status_schema.get("properties", {})
    if "userMessageJa" in status_properties or "messageCode" not in status_properties:
        errors.append(f"{chat_rel}: read-only status must use a fixed message code, not arbitrary transaction text")
    for schema_name in exact_request_fields:
        if schemas.get(schema_name, {}).get("additionalProperties") is not False:
            errors.append(f"{chat_rel}: {schema_name} must reject arbitrary additional properties")
    reference_description = (
        chat.get("components", {}).get("parameters", {}).get("ReferenceId", {}).get("description", "")
    )
    if "must not encode" not in reference_description:
        errors.append(f"{chat_rel}: referenceId must be explicitly opaque and non-transactional")
    reference_schema = chat.get("components", {}).get("parameters", {}).get("ReferenceId", {}).get("schema", {})
    if reference_schema.get("minLength") != 24 or reference_schema.get("pattern") != "^[A-Za-z0-9_-]{24,128}$":
        errors.append(f"{chat_rel}: referenceId must use the high-entropy opaque identifier profile")
    support_reference = schemas.get("ErrorExplanationRequest", {}).get("properties", {}).get("supportReference", {})
    if support_reference.get("minLength") != 24 or support_reference.get("pattern") != "^[A-Za-z0-9_-]{24,128}$":
        errors.append(f"{chat_rel}: supportReference must use the high-entropy opaque identifier profile")
    boundary_doc = (ROOT / "42_NATURAL_LANGUAGE_AND_CHATGPT_BOUNDARY.md").read_text(encoding="utf-8")
    canonical_prompt = (ROOT / "codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md").read_text(encoding="utf-8")
    if "get_manual_steps" in boundary_doc or "manual button-by-button instructions" in canonical_prompt:
        errors.append("ChatGPT boundary exposes transaction-specific manual instructions")
    boundary_corpus = boundary_doc + "\n" + canonical_prompt
    for required in (
        "手動復旧catalogは独立ウォレット内だけ",
        "取引固有の下書きやボタン手順も返さない",
        "transaction-specific manual fallback remains available only inside the standalone wallet",
    ):
        if required.lower() not in boundary_corpus.lower():
            errors.append(f"ChatGPT/OpenAI boundary requirement missing: {required}")
    scopes = (
        chat.get("components", {})
        .get("securitySchemes", {})
        .get("oauth2ReadOnly", {})
        .get("flows", {})
        .get("authorizationCode", {})
        .get("scopes", {})
    )
    if not scopes or any("write" in key.lower() or not key.endswith(".read") for key in scopes):
        errors.append(f"{chat_rel}: only explicit .read OAuth scopes are allowed")
    return errors

def check_feature_gates() -> list[str]:
    errors: list[str] = []
    doc = strict_load_yaml(ROOT / "config/feature-gates.example.yaml")
    mainnet = doc["environments"]["mainnet"]
    write_keys = [k for k in mainnet if k not in {"read_only", "ai_intent"}]
    enabled = [k for k in write_keys if mainnet[k] is not False]
    if enabled:
        errors.append(f"mainnet write gates must default false: {enabled}")
    return errors


def _check_dag(steps: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ids = [step["stepId"] for step in steps]
    if len(ids) != len(set(ids)):
        errors.append("execution capsule has duplicate stepId")
        return errors
    graph = {step["stepId"]: list(step["dependsOn"]) for step in steps}
    all_ids = set(graph)
    for node, deps in graph.items():
        missing = set(deps) - all_ids
        if missing:
            errors.append(f"unknown dependencies for {node}: {sorted(missing)}")
        if node in deps:
            errors.append(f"self dependency for {node}")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visited or node not in graph:
            return
        if node in visiting:
            errors.append(f"dependency cycle detected at {node}")
            return
        visiting.add(node)
        for dep in graph[node]:
            visit(dep)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    return errors


def check_semantics() -> list[str]:
    errors: list[str] = []
    capsules = [
        load_json("examples/execution-capsule-perp.json"),
        load_json("examples/execution-capsule-composite.json"),
        load_json("examples/execution-capsule-ios-saved-withdrawal.json"),
    ]
    for capsule in capsules:
        label = capsule["capsuleId"]
        errors.extend(f"{label}: {e}" for e in _check_dag(capsule["steps"]))
        try:
            if dt(capsule["createdAt"]) >= dt(capsule["expiresAt"]):
                errors.append(f"{label}: capsule expiry must be after creation")
            for step in capsule["steps"]:
                if step["account"].lower() != capsule["account"].lower():
                    errors.append(f"{label}/{step['stepId']}: step account mismatch")
                if dt(step["expiresAt"]) > dt(capsule["expiresAt"]):
                    errors.append(f"{label}/{step['stepId']}: step expires after capsule")
                if step["type"] in {"INTERNAL_USD_SEND", "INTERNAL_SPOT_SEND", "ARBITRUM_WITHDRAW"} and not step.get("destination"):
                    errors.append(f"{label}/{step['stepId']}: destination required")
                if step["type"] == "PERP_ORDER" and step["signerRole"] != "TRADE_AGENT":
                    errors.append(f"{label}/{step['stepId']}: example policy requires TRADE_AGENT for Perp")
                if step["amountMode"] == "REMAINDER" and (not step.get("computedMaximumAmount") or not step["dependsOn"]):
                    errors.append(f"{label}/{step['stepId']}: REMAINDER requires hard maximum and dependency")
                derivation = step.get("dynamicDerivation")
                if derivation is not None:
                    quantity_ref = derivation["quantity"]["stepId"]
                    trigger_ref = derivation["triggerPrice"]["stepId"]
                    if quantity_ref not in step["dependsOn"] or trigger_ref not in step["dependsOn"]:
                        errors.append(f"{label}/{step['stepId']}: dynamic derivation references must be dependencies")
                    if step.get("orderType") not in {"TRIGGER_MARKET", "TRIGGER_LIMIT"}:
                        errors.append(f"{label}/{step['stepId']}: dynamic trigger derivation requires trigger order")
                    if step.get("triggerPrice") is not None:
                        errors.append(f"{label}/{step['stepId']}: fixed triggerPrice conflicts with dynamic derivation")
                    if step.get("amount") is not None or step.get("amountMode") != "PERCENT":
                        errors.append(f"{label}/{step['stepId']}: fill-derived quantity must use PERCENT with null amount")
                    if step.get("reduceOnly") is not True:
                        errors.append(f"{label}/{step['stepId']}: protective order must be reduceOnly")
                    if step.get("failurePolicy") != "EMERGENCY_REDUCE_ONLY_CLOSE" or not step.get("failureRecovery"):
                        errors.append(f"{label}/{step['stepId']}: protective order requires explicit emergency close recovery")
                    if not step.get("maxDelayAfterDependencyMs"):
                        errors.append(f"{label}/{step['stepId']}: protective order placement deadline missing")
        except Exception as exc:
            errors.append(f"{label}: timestamp validation failed: {exc}")

        max_risk = max(int(step["riskTier"][1:]) for step in capsule["steps"])
        mode = capsule["authorizationPresentation"]["mode"]
        platform = capsule["platform"]
        assurance = capsule["authorizationPresentation"]["assurance"]
        if platform == "IOS" and mode == "ANDROID_PROTECTED_CONFIRMATION":
            errors.append(f"{label}: iOS cannot use Android Protected Confirmation mode")
        if platform == "ANDROID" and mode == "IOS_APP_ATTESTED_AUTHENTICATED_UI":
            errors.append(f"{label}: Android cannot use iOS authorization mode")
        if mode == "IOS_APP_ATTESTED_AUTHENTICATED_UI" and assurance != "AUTHENTICATED_APP_UI_NOT_TRUSTED_DISPLAY":
            errors.append(f"{label}: iOS App Attest mode must not claim trusted display")
        if max_risk >= 3 and mode == "APP_EXECUTION_CARD":
            errors.append(f"{label}: R3/R4 cannot rely on an unauthenticated app card")
        if max_risk >= 4 and mode == "IOS_APP_ATTESTED_AUTHENTICATED_UI":
            errors.append(f"{label}: R4 cannot use iOS app-authenticated UI without external/protected ceremony")
        if max_risk == 3 and mode == "IOS_APP_ATTESTED_AUTHENTICATED_UI":
            presentation = capsule["authorizationPresentation"]
            if not presentation.get("standingAuthorizationId") or not presentation.get("destinationRegistrationEvidenceId"):
                errors.append(f"{label}: R3 iOS app mode requires pre-existing standing authorization and registration evidence")
        if max_risk >= 2:
            classes = {s["independenceClass"] for s in capsule["stateEvidence"]["sources"]}
            if len(classes) < 2:
                errors.append(f"{label}: R2+ requires independent state classes")
            if capsule["stateEvidence"]["divergenceStatus"] not in {"CONSISTENT", "WITHIN_TOLERANCE"}:
                errors.append(f"{label}: R2+ state evidence not executable")
        if max_risk == 1 and capsule["stateEvidence"]["policy"] != "SINGLE_SOURCE_R1":
            errors.append(f"{label}: R1 example should state its single-source policy")

        try:
            expected = expected_hashes(capsule)
            for key in ("semanticHash", "renderReceiptHash", "sourceStateHash"):
                if capsule[key].lower() != str(expected[key]).lower():
                    errors.append(f"{label}: {key} mismatch; run tools/update_example_hashes.py")
            actual_prompt = capsule["authorizationPresentation"]["promptTextHash"]
            if actual_prompt != expected["promptTextHash"]:
                errors.append(f"{label}: promptTextHash mismatch; run tools/update_example_hashes.py")
            prompt = capsule["authorizationPresentation"].get("promptText") or ""
            if max_risk >= 3 and mode in {"ANDROID_PROTECTED_CONFIRMATION", "EXTERNAL_WALLET_TRUSTED_DISPLAY", "HARDWARE_WALLET"}:
                for step in capsule["steps"]:
                    if step.get("destination") and step["destination"] not in prompt:
                        errors.append(f"{label}: R3 trusted prompt must include full destination in test vector")
                    if step["amountMode"] == "REMAINDER" and step.get("computedMaximumAmount") not in prompt:
                        errors.append(f"{label}: R3 trusted prompt must include remainder maximum")
        except CanonicalizationError as exc:
            errors.append(f"{label}: canonical hash error: {exc}")

    composite = capsules[1]
    last = composite["steps"][-1]
    if last["type"] != "ARBITRUM_WITHDRAW" or last["requiredAuth"] != "AUTH_PER_USE":
        errors.append("composite withdrawal must be AUTH_PER_USE")

    auth = load_json("examples/authorization-envelope-protected-confirmation.json")
    for key in ("planId", "semanticHash", "renderReceiptHash", "sourceStateHash"):
        source_key = key
        if auth[key] != composite[source_key]:
            errors.append(f"authorization envelope {key} does not bind composite capsule")
    if auth["promptTextHash"] != composite["authorizationPresentation"]["promptTextHash"]:
        errors.append("authorization envelope promptTextHash mismatch")
    if auth["presentationMode"] != composite["authorizationPresentation"]["mode"]:
        errors.append("authorization envelope presentation mode mismatch")
    if auth["deviceId"] != composite["deviceId"]:
        errors.append("authorization envelope device mismatch")
    if dt(auth["issuedAt"]) >= dt(auth["expiresAt"]) or dt(auth["expiresAt"]) > dt(composite["expiresAt"]):
        errors.append("authorization envelope expiry invalid")

    ios_capsule = capsules[2]
    ios_auth = load_json("examples/authorization-envelope-ios-app-attest.json")
    for key in ("planId", "semanticHash", "renderReceiptHash", "sourceStateHash"):
        if ios_auth[key] != ios_capsule[key]:
            errors.append(f"iOS authorization envelope {key} does not bind iOS capsule")
    if ios_auth["deviceId"] != ios_capsule["deviceId"] or ios_auth["platform"] != "IOS":
        errors.append("iOS authorization envelope device/platform mismatch")
    if ios_auth["authorizationAssurance"] != "AUTHENTICATED_APP_UI_NOT_TRUSTED_DISPLAY":
        errors.append("iOS authorization must explicitly avoid trusted-display claim")
    if ios_auth["evidence"].get("trustedDisplayClaim") is not False:
        errors.append("iOS evidence must set trustedDisplayClaim=false")
    if not ios_capsule["authorizationPresentation"].get("standingAuthorizationId"):
        errors.append("iOS R3 saved-destination example requires standing authorization")
    if not ios_capsule["authorizationPresentation"].get("destinationRegistrationEvidenceId"):
        errors.append("iOS R3 saved-destination example requires destination registration evidence")
    if dt(ios_auth["issuedAt"]) >= dt(ios_auth["expiresAt"]) or dt(ios_auth["expiresAt"]) > dt(ios_capsule["expiresAt"]):
        errors.append("iOS authorization envelope expiry invalid")

    action = load_json("examples/action-plan-btc-long.json")
    if action["classification"] == "EXPLICIT_ACTION" and not action["operations"]:
        errors.append("explicit action must contain an operation")
    source_text = (ROOT / "examples/source-text-btc-long.txt").read_text(encoding="utf-8").rstrip("\n")
    if action.get("sourceTextHashProfile") != "ONE_INTENT_SOURCE_TEXT_HASH_V1":
        errors.append("ActionPlan sourceTextHashProfile mismatch")
    if action.get("sourceTextHash") != source_text_hash(source_text):
        errors.append("ActionPlan sourceTextHash mismatch")
    if action.get("sourceTextHash") == "0x" + "0" * 64:
        errors.append("ActionPlan sourceTextHash must not be a dummy zero hash")
    operation_ids = {op["operationId"] for op in action["operations"]}
    stop_ops = [op for op in action["operations"] if op.get("triggerKind") == "SL"]
    if len(stop_ops) != 1:
        errors.append("BTC long example must preserve exactly one stop-loss operation")
    else:
        stop = stop_ops[0]
        ref = stop.get("quantityReferenceOperationId")
        if ref not in operation_ids or ref not in stop.get("dependsOn", []):
            errors.append("stop-loss must reference and depend on the entry operation")
        if stop.get("triggerReference") != "ENTRY_FILL_PRICE" or stop.get("triggerOffsetPercent") != "2":
            errors.append("stop-loss must preserve 2% from actual entry fill semantics")
        if stop.get("reduceOnly") is not True or stop.get("percent") != "100":
            errors.append("stop-loss must be reduceOnly for 100% of filled entry size")
    perp = capsules[0]
    protective = [step for step in perp["steps"] if step.get("triggerKind") == "SL"]
    if len(protective) != 1:
        errors.append("Perp capsule must contain exactly one protective stop step")
    if "損切り" not in perp["renderReceipt"]["buttonLabel"]:
        errors.append("Perp execution button must disclose the stop-loss")
    if "RECOVERY_POLICY" not in perp["authorizationPresentation"]["criticalFields"]:
        errors.append("Perp authorization must disclose protective-order recovery policy")

    fee = load_json("examples/fee-readiness-jpyc-only.json")
    if fee.get("schemaVersion") != "2.1" or fee.get("exampleOnly") is not True or fee.get("environment") != "SIMULATION":
        errors.append("fee-readiness example must be v2.1, simulation, and example-only")
    provider = fee.get("provider", {})
    quote = fee.get("quote", {})
    if quote.get("providerId") != provider.get("providerId"):
        errors.append("fee-readiness quote/provider identity mismatch")
    if quote.get("expiresAt") != fee.get("expiresAt"):
        errors.append("fee-readiness quote/top-level expiry mismatch")
    if dt(fee["generatedAt"]) >= dt(fee["expiresAt"]):
        errors.append("fee-readiness plan expiry invalid")
    if dt(quote["generatedAt"]) >= dt(quote["expiresAt"]):
        errors.append("fee-readiness quote expiry invalid")
    if quote.get("signatureState") != "SIMULATION_ONLY":
        errors.append("static fee-readiness fixture must not claim a verified production signature")
    required_bound = {"account", "networkId", "asset", "operation", "amount", "nonce", "expiresAt", "maxJpycCost", "feeAssetCost", "providerSettlementTarget"}
    if not required_bound.issubset(set(quote.get("boundFields", []))):
        errors.append("fee-readiness quote is not bound to all material fields")
    if Decimal(quote["jpycCostExpected"]) > Decimal(quote["maxJpycCost"]):
        errors.append("fee-readiness expected JPYC cost exceeds cap")
    if Decimal(quote["chargeIfActionFails"]) > Decimal(quote["maxJpycCost"]):
        errors.append("fee-readiness failed-action charge exceeds cap")
    if not provider.get("legalNameJa") or not provider.get("contact") or not provider.get("termsVersion"):
        errors.append("fee-readiness provider disclosure incomplete")

    manual = load_json("examples/manual-fallback-zero-gas.json")
    if manual.get("schemaVersion") != "2.1" or manual.get("exampleOnly") is not True:
        errors.append("manual-fallback example must be v2.1 and example-only")
    if manual.get("amountSource") == "NOT_AVAILABLE":
        for key in ("recommendedAmount", "maximumAmount", "estimateId", "operationDigest", "estimateGeneratedAt", "estimateExpiresAt"):
            if manual.get(key) is not None:
                errors.append(f"manual-fallback unavailable estimate must keep {key}=null")
    elif manual.get("amountSource") == "LIVE_OPERATION_BOUND_ESTIMATE":
        for key in ("recommendedAmount", "maximumAmount", "estimateId", "operationDigest", "estimateGeneratedAt", "estimateExpiresAt"):
            if not manual.get(key):
                errors.append(f"manual-fallback live estimate missing {key}")
        if Decimal(manual["recommendedAmount"]) > Decimal(manual["maximumAmount"]):
            errors.append("manual-fallback recommended amount exceeds maximum")
        if dt(manual["estimateGeneratedAt"]) >= dt(manual["estimateExpiresAt"]):
            errors.append("manual-fallback estimate expiry invalid")
    orders = [step.get("order") for step in manual.get("steps", [])]
    if orders != list(range(1, len(orders) + 1)):
        errors.append("manual-fallback step order is not contiguous")
    manual_text = json.dumps(manual, ensure_ascii=False)
    if "0.05 POL" in manual_text:
        errors.append("manual-fallback must not contain a timeless fixed POL amount")
    for phrase in ("対象のJPYC送金に結び付いた", "推奨量", "有効期限", "上限"):
        if phrase not in manual_text:
            errors.append(f"manual-fallback live-estimate guidance missing: {phrase}")
    return errors


def check_registers() -> list[str]:
    errors: list[str] = []
    loopholes = (ROOT / "24_KNOWN_LOOPHOLE_REGISTER.md").read_text(encoding="utf-8")
    rows = [x for x in loopholes.splitlines() if x.startswith("| ") and not x.startswith("| ID ") and not x.startswith("|---")]
    match = re.search(r"登録件数: \*\*(\d+)\*\*", loopholes)
    if not match or int(match.group(1)) != len(rows):
        errors.append(f"loophole count mismatch: declared={match.group(1) if match else None}, actual={len(rows)}")
    ids = [row.split("|")[1].strip() for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate loophole IDs")
    if len(rows) < 240:
        errors.append(f"expected at least 240 registered loopholes, got {len(rows)}")
    invariants = (ROOT / "25_SECURITY_INVARIANTS.md").read_text(encoding="utf-8")
    inv_numbers = [int(x) for x in re.findall(r"^(\d+)\. ", invariants, re.MULTILINE)]
    if len(inv_numbers) < 80:
        errors.append(f"expected at least 80 invariants, got {len(inv_numbers)}")
    if inv_numbers != list(range(1, len(inv_numbers) + 1)):
        errors.append("security invariant numbering is not contiguous")
    regression = load_json("tests/loophole-regression-cases.json")
    regression_ids = [x.get("id") for x in regression.get("cases", [])]
    expected_regression_ids = [f"LR-{i:03d}" for i in range(1, len(regression_ids) + 1)]
    if len(regression_ids) < 24 or regression_ids != expected_regression_ids:
        errors.append(f"loophole regression cases must be contiguous LR-001..LR-{len(regression_ids):03d} with at least 24 cases")
    return errors


def check_version_and_placeholders() -> list[str]:
    errors: list[str] = []
    privacy = (ROOT / "10_PRIVACY_AND_AI_BOUNDARY.md").read_text(encoding="utf-8")
    architecture = (ROOT / "03_SYSTEM_ARCHITECTURE.md").read_text(encoding="utf-8")
    if "mobile appはOpenAIへ直接接続せず" not in privacy or "backend secret manager" not in privacy:
        errors.append("provider credential boundary missing from privacy specification")
    if "Transaction Intent ParserはSignerに到達不可" not in architecture or "取引Intent ParserはOpenAI endpointへegress不可" not in architecture:
        errors.append("transaction-intent/OpenAI network isolation missing from architecture")
    risk_doc = (ROOT / "26_TRUSTED_DISPLAY_AND_STATE_QUORUM.md").read_text(encoding="utf-8")
    required_risk_rows = (
        "| R1 | 上限内Perp／Spot |",
        "| R2 | 既知Vault、同一userへの公式Bridge入金、cancel-all等 |",
        "| R3 | 事前登録済み宛先への上限内送金／出金 |",
        "| R4 | 新規宛先、高額／全額、recovery、鍵・policy変更、agent／builder承認 |",
    )
    for row in required_risk_rows:
        if row not in risk_doc:
            errors.append(f"canonical risk-tier row missing: {row}")
    for rel in ("README_FIRST.md", "COMPLETE_SPEC.md", "FINAL_AUDIT_REPORT.md"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        if PACKAGE_VERSION not in text:
            errors.append(f"{rel}: package version mismatch")
    validation = (ROOT / "VALIDATION_REPORT.md").read_text(encoding="utf-8")
    if "PENDING_FINAL_VALIDATION" in validation:
        errors.append("VALIDATION_REPORT.md still pending")
    final_audit = (ROOT / "FINAL_AUDIT_REPORT.md").read_text(encoding="utf-8")
    start_here = (ROOT / "START_HERE.html").read_text(encoding="utf-8")
    loophole_count = len(re.findall(r"^\|\s*[A-Z][A-Z0-9-]*-\d{3}\s*\|", (ROOT / "24_KNOWN_LOOPHOLE_REGISTER.md").read_text(encoding="utf-8"), re.MULTILINE))
    invariant_count = len(re.findall(r"^\d+\.\s", (ROOT / "25_SECURITY_INVARIANTS.md").read_text(encoding="utf-8"), re.MULTILINE))
    for label, value in (("loophole", loophole_count), ("invariant", invariant_count)):
        if str(value) not in final_audit or str(value) not in validation:
            errors.append(f"generated report is stale for {label} count: {value}")
    for stale in ("131ファイル", "287件", "110件", "120条件", "dark-mode smoke", "iphone-overview.png", "pixel9a-composite.png"):
        if stale in final_audit or stale in validation:
            errors.append(f"generated report contains stale metric/artifact: {stale}")
    regression_count = len(load_json("tests/loophole-regression-cases.json").get("cases", []))
    regression_metric = f'<div class="metric">{regression_count}</div>'
    if ('<div class="metric">10</div>' not in start_here or '<div class="metric">288</div>' not in start_here or regression_metric not in start_here):
        errors.append(f"START_HERE summary metrics must show 288 visual cases, {regression_count} regression cases and 10 screenshots")

    canonical_statuses = (
        "DESIGN_GO",
        "OFFLINE_PROTOTYPE_GO",
        "CODEX_IMPLEMENTATION_GO",
        "ANDROID_RELEASE_SIGNING_NO_GO",
        "IOS_DISTRIBUTION_ARCHIVE_NO_GO",
        "TESTNET_WRITE_NO_GO",
        "PERSONAL_SMALL_MAINNET_NO_GO",
        "CLOSED_ALPHA_NO_GO",
        "PUBLIC_ANDROID_STORE_NO_GO",
        "PUBLIC_IOS_APP_STORE_NO_GO",
    )
    status_text = "\n".join((ROOT / rel).read_text(encoding="utf-8") for rel in (
        "RUNNABILITY_AND_STATUS.md", "PROJECT_STATUS.yaml", "FINAL_AUDIT_REPORT.md"
    ))
    for status in canonical_statuses:
        if status not in status_text:
            errors.append(f"canonical status missing: {status}")

    stale_patterns = (
        "DESIGN_GO / BUILD_GO",
        "TESTNET_GO_AFTER_IMPLEMENTATION",
        "iOS_BUILD_NO_GO",
        "正規アプリ实例",
    )
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".yaml", ".yml", ".html"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for stale in stale_patterns:
            if stale in text:
                errors.append(f"stale wording {stale!r}: {path.relative_to(ROOT)}")
    return errors


def check_manifest() -> list[str]:
    errors: list[str] = []
    manifest = load_json("manifest.json")
    expected_header = {
        "schemaVersion": "2.0",
        "package": METADATA.package,
        "version": METADATA.version,
        "rootName": METADATA.root_name,
        "generatedAt": METADATA.deterministic_build_timestamp,
        "hashAlgorithm": "SHA-256",
        "excludes": ["SHA256SUMS.txt", "manifest.json"],
    }
    for key, value in expected_header.items():
        if manifest.get(key) != value:
            errors.append(f"manifest {key} mismatch: {manifest.get(key)!r} != {value!r}")
    entries = manifest.get("files")
    if not isinstance(entries, list):
        return errors + ["manifest files must be an array"]
    entry_paths: list[str] = []
    expected: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) != {"path", "size", "sha256"}:
            errors.append(f"manifest entry {index} must contain exactly path,size,sha256")
            continue
        rel = entry.get("path")
        if not isinstance(rel, str):
            errors.append(f"manifest entry {index} path must be string")
            continue
        if member_name_problems(rel):
            errors.append(f"manifest unsafe path {rel!r}: {member_name_problems(rel)}")
        if rel in expected:
            errors.append(f"duplicate manifest path: {rel}")
        expected[rel] = entry
        entry_paths.append(rel)
        if type(entry.get("size")) is not int or entry["size"] < 0:
            errors.append(f"manifest invalid size: {rel}")
        if not isinstance(entry.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            errors.append(f"manifest invalid SHA-256: {rel}")
    if entry_paths != sorted(entry_paths):
        errors.append("manifest entries must be lexicographically sorted")

    excluded = {"manifest.json", "SHA256SUMS.txt"}
    actual_paths = sorted(
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.relative_to(ROOT).as_posix() not in excluded
        and "__pycache__" not in path.parts
        and path.suffix.lower() not in {".pyc", ".pyo"}
    )
    if set(expected) != set(actual_paths):
        errors.append(f"manifest file set mismatch; missing={sorted(set(actual_paths)-set(expected))}, extra={sorted(set(expected)-set(actual_paths))}")
    for rel in actual_paths:
        path = ROOT / rel
        entry = expected.get(rel)
        if entry and (entry.get("size") != path.stat().st_size or entry.get("sha256") != sha256(path)):
            errors.append(f"manifest mismatch: {rel}")

    checksum_lines = (ROOT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    checksum_map: dict[str, str] = {}
    checksum_paths: list[str] = []
    for index, line in enumerate(checksum_lines, 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            errors.append(f"invalid SHA256SUMS line {index}: {line!r}")
            continue
        digest, rel = match.groups()
        if member_name_problems(rel):
            errors.append(f"SHA256SUMS unsafe path {rel!r}: {member_name_problems(rel)}")
        if rel in checksum_map:
            errors.append(f"duplicate checksum entry: {rel}")
        checksum_map[rel] = digest
        checksum_paths.append(rel)
    if checksum_paths != sorted(checksum_paths):
        errors.append("SHA256SUMS entries must be lexicographically sorted")
    checksum_targets = sorted(
        (
            path
            for path in ROOT.rglob("*")
            if path.is_file()
            and path.name != "SHA256SUMS.txt"
            and "__pycache__" not in path.parts
            and path.suffix.lower() not in {".pyc", ".pyo"}
        ),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )
    expected_targets = {path.relative_to(ROOT).as_posix() for path in checksum_targets}
    if set(checksum_map) != expected_targets:
        errors.append(f"SHA256SUMS file set mismatch; missing={sorted(expected_targets-set(checksum_map))}, extra={sorted(set(checksum_map)-expected_targets)}")
    for path in checksum_targets:
        rel = path.relative_to(ROOT).as_posix()
        if checksum_map.get(rel) != sha256(path):
            errors.append(f"SHA256SUMS mismatch: {rel}")
    return errors

def check_prototype() -> list[str]:
    errors: list[str] = []
    html = (ROOT / "prototype/index.html").read_text(encoding="utf-8")
    css = (ROOT / "prototype/styles.css").read_text(encoding="utf-8")
    js = (ROOT / "prototype/app.js").read_text(encoding="utf-8")
    blob = html + "\n" + css + "\n" + js
    watermark = "画面見本です — 実際の送金・取引・署名・外部通信は行いません"
    if watermark not in html:
        errors.append("prototype must retain the complete simulation-only watermark")
    for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket(", "walletconnect", "privateKey", "seed phrase"):
        if forbidden.lower() in blob.lower():
            errors.append(f"prototype contains forbidden live/network/key marker: {forbidden}")
    if "44px" not in css or "54px" not in css:
        errors.append("prototype missing minimum touch/action target tokens")
    for marker in (
        "summary: '元手500 USDC・損切りは未設定'",
        "requiresCorrectionConfirmation: true",
        "window.__WALLET_PROTOTYPE__",
        "resetScrollAndStatus",
        "document.getElementById('scrollStatus')",
        "class=\"action-footer\"",
    ):
        if marker not in js:
            errors.append(f"prototype safety/review structure missing: {marker}")
    if "損切り2%" in js:
        errors.append("prototype must not silently invent a 2% stop-loss")
    if "0.05 POL" in js:
        errors.append("prototype must not hard-code a manual POL top-up amount")
    for value in ("948.50 USDC", "300.00 USDC", "648.50 USDC", "1.00 USDC", "647.50 USDC"):
        if value not in js:
            errors.append(f"prototype composite arithmetic value missing: {value}")
    for marker in ("画面例のダミー", "初期値ではありません", "画面例・利用者設定ではない"):
        if marker not in js:
            errors.append(f"prototype invented-value marker missing: {marker}")
    for disclosure in ("代理支払いの提供者", "精算先", "失敗時の請求", "見積もりID", "見積もりの有効期限"):
        if disclosure not in js:
            errors.append(f"prototype fee-route disclosure missing: {disclosure}")

    screenshot_names = (
        "iphone-perp-before-confirmation.png",
        "iphone-perp-after-confirmation.png",
        "pixel9a-fee-dark.png",
        "iphone-large-withdraw.png",
        "pixel9a-manual.png",
        "iphone-limited-authorization.png",
        "android-tall-partial-dark.png",
        "iphone-jpyc-large.png",
        "iphone-se-composite-top.png",
        "android-compact-spot-large-dark.png",
    )
    for name in screenshot_names:
        rel = f"prototype/screenshots/{name}"
        p = ROOT / rel
        if not p.exists() or p.stat().st_size < 10_000:
            errors.append(f"prototype screenshot missing or implausibly small: {rel}")

    evidence = load_json("tests/prototype-visual-evidence.json")
    if evidence.get("schemaVersion") != "2.0" or evidence.get("release") != PACKAGE_VERSION:
        errors.append("prototype visual evidence schema/release mismatch")
    if evidence.get("result") != "PASS":
        errors.append("prototype visual evidence result must be PASS")
    if evidence.get("geometryAndContrastCases") != 288:
        errors.append("prototype visual evidence matrix count must be 288")
    if len(evidence.get("viewports", [])) != 6 or len(evidence.get("flows", [])) != 12:
        errors.append("prototype visual evidence viewport/flow count mismatch")
    if len(evidence.get("textModes", [])) != 2 or len(evidence.get("themes", [])) != 2:
        errors.append("prototype visual evidence text/theme count mismatch")
    if evidence.get("localeExecuted") != ["ja-JP"]:
        errors.append("prototype evidence must honestly record the executed locale")
    expected_shots = {f"prototype/screenshots/{name}" for name in screenshot_names}
    if set(evidence.get("screenshots", [])) != expected_shots:
        errors.append("prototype visual evidence screenshot set mismatch")
    review_states = evidence.get("screenshotReviewStates", {})
    if set(review_states) != set(screenshot_names):
        errors.append("prototype screenshot review-state set mismatch")
    bottom_action_shots = ['android-compact-spot-large-dark.png', 'android-tall-partial-dark.png', 'iphone-jpyc-large.png', 'iphone-perp-after-confirmation.png']
    top_shots = ['iphone-large-withdraw.png', 'iphone-limited-authorization.png', 'iphone-perp-before-confirmation.png', 'iphone-se-composite-top.png', 'pixel9a-fee-dark.png', 'pixel9a-manual.png']
    if set(screenshot_names) != set(bottom_action_shots) | set(top_shots):
        errors.append("prototype screenshot capture-mode contract mismatch")
    for name in screenshot_names:
        state = review_states.get(name, {})
        expected_mode = "BOTTOM_ACTION" if name in bottom_action_shots else "TOP"
        if state.get("captureMode") != expected_mode or state.get("partialTopBlocks") != 0:
            errors.append(f"prototype evidence screenshot is not cleanly aligned: {name}")
        if expected_mode == "BOTTOM_ACTION":
            if state.get("actionVisible") is not True:
                errors.append(f"prototype bottom-action screenshot does not show the full action: {name}")
            if state.get("scrollCue") not in {"bottom", "all"}:
                errors.append(f"prototype bottom-action screenshot has a misleading continuation cue: {name}")
        if expected_mode == "TOP":
            if abs(float(state.get("scrollTop", -999))) > 1:
                errors.append(f"prototype top screenshot is not at the natural top: {name}")
            if state.get("scrollCue") not in {"top", "all"}:
                errors.append(f"prototype top screenshot has an invalid initial cue: {name}")
    checks = evidence.get("checks", [])
    if len(checks) != len(set(checks)):
        errors.append("prototype visual evidence contains duplicate check names")
    for required in ("control_overlap_and_center_hit_testing", "evidence_screenshot_boundary_alignment", "invented_value_example_markers"):
        if required not in checks:
            errors.append(f"prototype visual evidence required check missing: {required}")
    visual_requirements = (ROOT / "tools/requirements-visual.txt").read_text(encoding="utf-8")
    if "playwright==1.57.0" not in visual_requirements:
        errors.append("requirements-visual.txt must pin Playwright 1.57.0")
    toolchain = evidence.get("toolchain", {})
    if toolchain.get("playwrightPython") != "1.57.0":
        errors.append("prototype evidence Playwright version must match pinned requirements-visual.txt")
    if not isinstance(toolchain.get("browser"), str) or not toolchain.get("browser"):
        errors.append("prototype evidence must record browser version")
    harness = evidence.get("testHarness", {})
    harness_path = harness.get("path")
    if harness_path != "tools/test_prototype.py" or not (ROOT / harness_path).exists() or sha256(ROOT / harness_path) != harness.get("sha256"):
        errors.append("prototype evidence test harness hash mismatch")
    expected_sources = {"prototype/index.html", "prototype/styles.css", "prototype/app.js"}
    if set(evidence.get("prototypeFiles", {})) != expected_sources:
        errors.append("prototype evidence source set mismatch")
    for rel, expected in evidence.get("prototypeFiles", {}).items():
        path = ROOT / rel
        if not path.exists() or sha256(path) != expected:
            errors.append(f"prototype evidence source hash mismatch: {rel}")
    for required_copy in ("清算価格の目安", "JPYCしかない", "最初の一回だけ", "自動でできない場合", "損切りは未設定"):
        if required_copy not in html + js:
            errors.append(f"prototype required plain-Japanese flow missing: {required_copy}")
    terms = load_json("config/user-facing-terms.ja.json")
    if terms.get("defaultMode") != "plain-ja" or len(terms.get("entries", [])) < 20:
        errors.append("plain-Japanese term dictionary is incomplete")
    return errors


def check_start_here() -> list[str]:
    errors: list[str] = []
    evidence = load_json("tests/start-here-layout-evidence.json")
    if evidence.get("schemaVersion") != "1.0" or evidence.get("release") != PACKAGE_VERSION or evidence.get("result") != "PASS":
        errors.append("START_HERE layout evidence schema/release/result mismatch")
    cases = evidence.get("cases", [])
    expected = {(name, theme) for name in ("mobile-narrow", "mobile-standard", "desktop") for theme in ("LIGHT", "DARK")}
    actual = {(x.get("viewport"), x.get("theme")) for x in cases}
    if actual != expected or any(x.get("result") != "PASS" for x in cases):
        errors.append("START_HERE layout evidence case set mismatch")
    if evidence.get("localeExecuted") != ["ja-JP"]:
        errors.append("START_HERE evidence locale mismatch")
    source = evidence.get("source", {})
    if source.get("path") != "START_HERE.html" or sha256(ROOT / "START_HERE.html") != source.get("sha256"):
        errors.append("START_HERE evidence source hash mismatch")
    harness = evidence.get("testHarness", {})
    if harness.get("path") != "tools/test_start_here.py" or sha256(ROOT / "tools/test_start_here.py") != harness.get("sha256"):
        errors.append("START_HERE evidence harness hash mismatch")
    checks = evidence.get("checks", [])
    if len(checks) != len(set(checks)) or "focus_and_center_hit_testing" not in checks:
        errors.append("START_HERE evidence check list invalid")
    return errors



def check_operational_readiness_contract() -> list[str]:
    errors: list[str] = []
    try:
        evaluation = evaluate_design_package()
        errors.extend(f"operational readiness: {item}" for item in evaluation.errors)
        report = evaluation.report
        if (
            report.get("status") != "BLOCKED_NOT_OPERATIONAL"
            or report.get("releaseEligibleForRuntimeActivation") is not False
            or report.get("productionWritePermitted") is not False
        ):
            errors.append("current package must be blocked, ineligible for runtime activation, and unable to grant direct writes")
        stored = load_json("delivery/OPERATIONAL_READINESS_REPORT.json")
        if stored != report:
            errors.append("stored operational-readiness report is stale")
        config = load_json("config/operational-readiness.json")
        claims = required_claims(config)
        if len(config.get("gates", [])) != 37 or len(claims) != 93:
            errors.append("operational-readiness profile must contain exactly 37 gates and 93 release/runtime claims")
        if config.get("target", {}).get("executionSurface") != "STANDALONE_WALLET_ONLY":
            errors.append("operational target must keep execution in the standalone wallet")
        if config.get("target", {}).get("chatgptBoundary") != "READ_ONLY_STATUS_GLOSSARY_GENERIC_SAFETY_AND_NEUTRAL_HANDOFF":
            errors.append("ChatGPT boundary drift in operational profile")
        lease = load_json("examples/runtime-control-plane-lease-disabled.json")
        if lease.get("transactionAuthorizationGranted") is not False or lease.get("capabilities"):
            errors.append("runtime lease example must not authorize transactions or capabilities")
        state = load_json("examples/runtime-state-bundle-stopped.json")
        if state.get("killSwitch") is not True or state.get("writesEnabled") is not False:
            errors.append("runtime stopped example must keep kill switch on and writes off")
        binding = load_json("examples/account-authorization-binding-suspended.json")
        if binding.get("status") != "SUSPENDED" or binding.get("sequence") != 0:
            errors.append("account authorization binding example must remain suspended and non-replayable")
        runtime_policy = load_json("config/runtime-authorization-policy.template.json")
        if runtime_policy.get("enabled") is not False or runtime_policy.get("policyVersion") != "TEMPLATE-NOT-ACTIVE":
            errors.append("runtime authorization policy template must remain disabled")
        operation = load_json("examples/per-operation-authorization-denied.json")
        if operation.get("authorized") is not False or operation.get("userAuthorization") is not None:
            errors.append("operation authorization example must remain explicitly denied")
        runtime_source = (ROOT / "tools/runtime_authorization.py").read_text(encoding="utf-8")
        for marker in (
            '"transactionAuthorizationGranted": False',
            'ELIGIBLE_FOR_ATOMIC_SIGNER_FINALIZATION',
            'ONE_INTENT_RUNTIME_AUTHORIZER_BUNDLE_V1',
            'consumed_authorization_ids',
            'consumed_nonces',
        ):
            if marker not in runtime_source:
                errors.append(f"runtime authorization evaluator missing fail-closed marker: {marker}")
    except Exception as exc:
        errors.append(f"operational-readiness contract validation failed: {exc}")
    return errors

def main() -> int:
    errors: list[str] = []
    for check in (
        check_files,
        check_strict_json,
        check_schema_and_examples,
        check_yaml,
        check_openapi,
        check_feature_gates,
        check_semantics,
        check_registers,
        check_version_and_placeholders,
        check_prototype,
        check_start_here,
        check_operational_readiness_contract,
        check_manifest,
    ):
        errors.extend(check())
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALIDATION PASSED")
    print(f"Files: {sum(1 for p in ROOT.rglob('*') if p.is_file())}")
    print("Schemas/examples: PASS")
    print("Canonical hashes: PASS")
    print("OpenAPI refs/operationIds: PASS")
    print("Feature gates: PASS")
    print("Operational readiness: BLOCKED_NOT_OPERATIONAL (expected and enforced)")
    print("Manifest/checksums: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
