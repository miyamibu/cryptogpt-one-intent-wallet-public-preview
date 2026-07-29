#!/usr/bin/env python3
"""Fail-closed reference evaluator for signer-side runtime authorization.

This module deliberately cannot sign or broadcast a transaction. A successful
result means only that an exact operation is eligible to enter an *atomic signer
finalization* step that must consume the nonce/authorization ID and revalidate
all hashes inside the protected signer boundary. The decision always keeps
``transactionAuthorizationGranted`` false.
"""
from __future__ import annotations

import base64
import copy
import datetime as dt
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from canonical_hashes import canonical_json, domain_hash, expected_hashes
from operational_readiness import (
    CANONICALIZATION_PROFILE,
    HEX64,
    SIGNATURE_PROFILE,
    TrustedKey,
    _key_map,
    _load_ed25519_public_key,
    format_time,
    parse_time,
    readiness_bundle_hash,
    secure_file_snapshot,
    secure_load_json,
    subject_hash,
    validate_schema,
    verify_signature,
)
from package_metadata import ROOT

RUNTIME_POLICY_TEMPLATE_PATH = ROOT / "config/runtime-authorization-policy.template.json"
READINESS_REPORT_PATH = ROOT / "delivery/OPERATIONAL_READINESS_REPORT.json"
ACCOUNT_BINDING_EXAMPLE_PATH = ROOT / "examples/account-authorization-binding-suspended.json"
RUNTIME_STATE_EXAMPLE_PATH = ROOT / "examples/runtime-state-bundle-stopped.json"
RUNTIME_LEASE_EXAMPLE_PATH = ROOT / "examples/runtime-control-plane-lease-disabled.json"
OPERATION_EXAMPLE_PATH = ROOT / "examples/per-operation-authorization-denied.json"
CAPSULE_EXAMPLE_PATH = ROOT / "examples/execution-capsule-perp.json"
TIME_EXAMPLE_PATH = ROOT / "examples/trusted-time-attestation-untrusted.json"
TRUST_TEMPLATE_PATH = ROOT / "config/operational-trust-policy.template.json"

RUNTIME_SIGNED_DOCUMENT_DOMAIN = b"ONE_INTENT_SIGNED_DOCUMENT_V2"
RUNTIME_DOMAINS = {
    "accountBinding": "ONE_INTENT_ACCOUNT_AUTHORIZATION_BINDING_V1",
    "runtimeState": "ONE_INTENT_RUNTIME_STATE_BUNDLE_V1",
    "runtimeLease": "ONE_INTENT_RUNTIME_CONTROL_PLANE_LEASE_V1",
    "operationAuthorization": "ONE_INTENT_PER_OPERATION_AUTHORIZATION_V1",
}
CAPSULE_AUTHORIZATION_DOMAIN = "ONE_INTENT_EXECUTION_CAPSULE_AUTHORIZATION_V1"
MAX_RUNTIME_JSON_BYTES = 4 * 1024 * 1024
CANONICAL_ID = re.compile(r"^[A-Za-z0-9._:-]{8,160}$")

RUNTIME_AUTHORIZER_BUNDLE_FILES = (
    "config/build-metadata.json",
    "config/operational-readiness.json",
    "config/runtime-authorization-policy.template.json",
    "schemas/operational-trust-policy.schema.json",
    "schemas/operational-readiness-report.schema.json",
    "schemas/trusted-time-attestation.schema.json",
    "schemas/account-authorization-binding.schema.json",
    "schemas/runtime-authorization-policy.schema.json",
    "schemas/runtime-state-bundle.schema.json",
    "schemas/runtime-control-plane-lease.schema.json",
    "schemas/per-operation-authorization.schema.json",
    "schemas/operation-quote.schema.json",
    "schemas/runtime-authorization-decision.schema.json",
    "schemas/execution-capsule.schema.json",
    "tools/canonical_hashes.py",
    "tools/package_metadata.py",
    "tools/operational_readiness.py",
    "tools/runtime_authorization.py",
    "tools/check_runtime_authorization.py",
    "tools/test_runtime_authorization_positive.py",
    "tools/test_runtime_authorization_negative.py",
    "tools/runtime_authorization_test_fixture.py",
    "tools/run_full_validation.py",
    "tools/requirements.txt",
)


@dataclass(frozen=True)
class RuntimeEvaluation:
    report: dict[str, Any]
    errors: tuple[str, ...]


def runtime_authorizer_bundle_hash() -> str:
    digest = hashlib.sha256()
    digest.update(b"ONE_INTENT_RUNTIME_AUTHORIZER_BUNDLE_V1\x00")
    for rel in sorted(RUNTIME_AUTHORIZER_BUNDLE_FILES):
        snapshot = secure_file_snapshot(ROOT / rel, max_bytes=16 * 1024 * 1024, include_data=True)
        assert snapshot.data is not None
        rel_bytes = rel.encode("ascii")
        digest.update(len(rel_bytes).to_bytes(4, "big"))
        digest.update(rel_bytes)
        digest.update(len(snapshot.data).to_bytes(8, "big"))
        digest.update(snapshot.data)
    return digest.hexdigest()


def _check_anchor(name: str, actual: str, errors: list[str]) -> None:
    expected = os.environ.get(name)
    if expected is None:
        errors.append(f"missing protected out-of-band anchor: {name}")
    elif not HEX64.fullmatch(expected):
        errors.append(f"invalid protected out-of-band anchor format: {name}")
    elif expected != actual:
        errors.append(f"protected out-of-band anchor mismatch: {name}")


def _runtime_payload(document: dict[str, Any], *, remove_fields: Iterable[str], domain: str) -> bytes:
    if not re.fullmatch(r"ONE_INTENT_[A-Z0-9_]{3,96}_V\d+", domain):
        raise ValueError(f"invalid runtime signature domain: {domain!r}")
    unsigned = copy.deepcopy(document)
    for field in remove_fields:
        unsigned.pop(field, None)
    encoded = domain.encode("ascii")
    return (
        RUNTIME_SIGNED_DOCUMENT_DOMAIN
        + b"\x00"
        + len(encoded).to_bytes(2, "big")
        + encoded
        + b"\x00"
        + canonical_json(unsigned)
    )


def account_binding_payload(document: dict[str, Any]) -> bytes:
    return _runtime_payload(document, remove_fields=("signatures",), domain=RUNTIME_DOMAINS["accountBinding"])


def runtime_state_payload(document: dict[str, Any]) -> bytes:
    return _runtime_payload(document, remove_fields=("signatures",), domain=RUNTIME_DOMAINS["runtimeState"])


def runtime_lease_payload(document: dict[str, Any]) -> bytes:
    return _runtime_payload(document, remove_fields=("signatures",), domain=RUNTIME_DOMAINS["runtimeLease"])


def operation_authorization_payload(document: dict[str, Any]) -> bytes:
    return _runtime_payload(
        document,
        remove_fields=("userAuthorization", "deviceAuthorization", "policyAuthorization"),
        domain=RUNTIME_DOMAINS["operationAuthorization"],
    )


def _canonical_signature_bytes(signature: dict[str, Any]) -> bytes:
    if signature.get("profile") != SIGNATURE_PROFILE:
        raise ValueError("unsupported runtime signature profile")
    encoded = signature.get("signatureBase64")
    if not isinstance(encoded, str):
        raise ValueError("runtime signatureBase64 is missing")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError(f"runtime signature is not canonical base64: {exc}") from exc
    if len(raw) != 64 or base64.b64encode(raw).decode("ascii") != encoded:
        raise ValueError("runtime signature must be a canonical 64-byte Ed25519 value")
    return raw


def _verify_trusted_runtime_signature(
    signature: dict[str, Any],
    payload: bytes,
    *,
    key_map: dict[str, TrustedKey],
    revoked_key_ids: set[str],
    allowed_roles: set[str],
    evaluated_at: dt.datetime,
    signed_at: dt.datetime,
) -> TrustedKey:
    if not isinstance(signature, dict):
        raise ValueError("runtime signature entry must be an object")
    key_id = signature.get("keyId")
    role = signature.get("role")
    principal = signature.get("principalId")
    organization = signature.get("organization")
    if role not in allowed_roles:
        raise ValueError(f"runtime signature declares unauthorized role: {role!r}")
    key = key_map.get(key_id)
    if key is None:
        raise ValueError(f"runtime signature key is not trusted: {key_id!r}")
    if key_id in revoked_key_ids:
        raise ValueError(f"runtime signature key is revoked: {key_id!r}")
    if role not in key.roles:
        raise ValueError(f"runtime signature role is not assigned to key: {key_id!r}/{role!r}")
    if key.principal_id != principal or key.organization != organization:
        raise ValueError(f"runtime signature identity does not match trust policy: {key_id!r}")
    if not (key.valid_from <= signed_at <= evaluated_at < key.valid_until):
        raise ValueError(f"runtime signature key is outside its validity interval: {key_id!r}")
    raw = _canonical_signature_bytes(signature)
    try:
        key.public_key.verify(raw, payload)
    except Exception as exc:
        raise ValueError(f"runtime signature verification failed for {key_id!r}: {exc}") from exc
    return key


def _verify_multisig(
    document: dict[str, Any],
    *,
    payload: bytes,
    key_map: dict[str, TrustedKey],
    revoked_key_ids: set[str],
    required_roles: list[str],
    threshold: int,
    minimum_organizations: int,
    evaluated_at: dt.datetime,
    signed_at: dt.datetime,
) -> list[TrustedKey]:
    signatures = document.get("signatures")
    if not isinstance(signatures, list):
        raise ValueError("runtime signatures must be an array")
    key_ids = [item.get("keyId") if isinstance(item, dict) else None for item in signatures]
    if key_ids != sorted(key_ids, key=lambda value: "" if value is None else str(value)):
        raise ValueError("runtime signatures must be sorted by keyId for a unique representation")
    identities: list[TrustedKey] = []
    seen_keys: set[str] = set()
    seen_principals: set[str] = set()
    covered_roles: set[str] = set()
    organizations: set[str] = set()
    allowed = set(required_roles)
    for signature in signatures:
        identity = _verify_trusted_runtime_signature(
            signature,
            payload,
            key_map=key_map,
            revoked_key_ids=revoked_key_ids,
            allowed_roles=allowed,
            evaluated_at=evaluated_at,
            signed_at=signed_at,
        )
        if identity.key_id in seen_keys or identity.principal_id in seen_principals:
            raise ValueError("one runtime key/principal cannot satisfy multiple signature slots")
        seen_keys.add(identity.key_id)
        seen_principals.add(identity.principal_id)
        covered_roles.add(str(signature["role"]))
        organizations.add(identity.organization)
        identities.append(identity)
    if len(identities) < threshold:
        raise ValueError(f"runtime signature threshold not met: {len(identities)} < {threshold}")
    missing = set(required_roles) - covered_roles
    if missing:
        raise ValueError(f"required runtime signer roles are missing: {sorted(missing)}")
    if len(organizations) < minimum_organizations:
        raise ValueError(
            f"runtime signer organization separation not met: {len(organizations)} < {minimum_organizations}"
        )
    return identities


def _verify_embedded_authorization_signature(
    signature: dict[str, Any],
    payload: bytes,
    *,
    binding_key: dict[str, Any],
    expected_role: str,
) -> str:
    if not isinstance(signature, dict):
        raise ValueError(f"{expected_role} authorization signature is missing")
    if signature.get("role") != expected_role:
        raise ValueError(f"embedded authorization role mismatch: {signature.get('role')!r} != {expected_role!r}")
    for field in ("keyId", "principalId", "organization"):
        if signature.get(field) != binding_key.get(field):
            raise ValueError(f"embedded authorization {field} does not match active account binding")
    public_key, fingerprint = _load_ed25519_public_key(binding_key.get("publicKeyPem", ""))
    raw = _canonical_signature_bytes(signature)
    try:
        public_key.verify(raw, payload)
    except Exception as exc:
        raise ValueError(f"embedded {expected_role} authorization signature failed: {exc}") from exc
    return fingerprint


def _parse_iso_timestamp(value: Any, label: str) -> dt.datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a timestamp string")
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{label} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed.astimezone(dt.timezone.utc)


def _load_with_fallback(
    path: Path,
    fallback: Path,
    schema_rel: str,
    label: str,
    errors: list[str],
) -> tuple[dict[str, Any], Any]:
    try:
        value, snapshot = secure_load_json(path, max_bytes=MAX_RUNTIME_JSON_BYTES)
    except Exception as exc:
        errors.append(f"{label} rejected: {exc}")
        value, snapshot = secure_load_json(fallback, max_bytes=MAX_RUNTIME_JSON_BYTES)
    if not isinstance(value, dict):
        errors.append(f"{label} must be a JSON object")
        value, snapshot = secure_load_json(fallback, max_bytes=MAX_RUNTIME_JSON_BYTES)
    errors.extend(validate_schema(value, schema_rel, label))
    return value, snapshot


def _decision_report(
    *,
    profile_id: str,
    evaluated_at: dt.datetime,
    valid_until: dt.datetime,
    release_subject: dict[str, Any],
    state: dict[str, Any],
    lease: dict[str, Any],
    operation: dict[str, Any],
    required_capabilities: list[str],
    decision_inputs: dict[str, Any],
    errors: list[str],
) -> dict[str, Any]:
    eligible = not errors and valid_until > evaluated_at
    return {
        "schemaVersion": "1.0",
        "profileId": profile_id,
        "evaluatedAt": format_time(evaluated_at),
        "decisionValidUntil": format_time(valid_until),
        "status": "ELIGIBLE_FOR_ATOMIC_SIGNER_FINALIZATION" if eligible else "BLOCKED",
        "eligibleForAtomicSignerFinalization": eligible,
        # A reference evaluator is never a signer and can never authorize/broadcast.
        "transactionAuthorizationGranted": False,
        "releaseSubject": release_subject,
        "deploymentId": state.get("deploymentId") if isinstance(state, dict) else None,
        "runtimeBundleId": state.get("bundleId") if isinstance(state, dict) else None,
        "leaseId": lease.get("leaseId") if isinstance(lease, dict) else None,
        "authorizationId": operation.get("authorizationId") if isinstance(operation, dict) else None,
        "account": operation.get("account") if isinstance(operation, dict) else None,
        "executionCapsuleHash": operation.get("executionCapsuleHash") if isinstance(operation, dict) else None,
        "nonce": operation.get("nonce") if isinstance(operation, dict) else None,
        "requiredCapabilities": required_capabilities,
        "decisionInputs": decision_inputs,
        "blockingReasons": [] if eligible else sorted(set(errors or ["runtime authorization conditions are incomplete"])),
        "disclaimer": (
            "This decision never signs, broadcasts, or grants a transaction. The protected signer must re-read immutable inputs, "
            "atomically consume the exact authorization ID and nonce, enforce high-water marks, recompute the final transaction, "
            "and reject any hash, state, quote, account, capability, destination, amount, chain, or expiry difference."
        ),
    }


def evaluate_runtime_authorization(
    *,
    trust_policy_path: Path,
    runtime_policy_path: Path,
    readiness_report_path: Path,
    trusted_time_path: Path,
    account_binding_path: Path,
    runtime_state_path: Path,
    runtime_lease_path: Path,
    operation_authorization_path: Path,
    execution_capsule_path: Path,
    minimum_trusted_time_sequence: int = 0,
    minimum_evidence_index_sequence: int = 0,
    minimum_account_binding_sequence: int = 0,
    minimum_runtime_state_sequence: int = 0,
    minimum_runtime_lease_sequence: int = 0,
    consumed_authorization_ids: frozenset[str] = frozenset(),
    consumed_nonces: frozenset[str] = frozenset(),
) -> RuntimeEvaluation:
    errors: list[str] = []
    for label, value in (
        ("minimum_trusted_time_sequence", minimum_trusted_time_sequence),
        ("minimum_evidence_index_sequence", minimum_evidence_index_sequence),
        ("minimum_account_binding_sequence", minimum_account_binding_sequence),
        ("minimum_runtime_state_sequence", minimum_runtime_state_sequence),
        ("minimum_runtime_lease_sequence", minimum_runtime_lease_sequence),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"{label} must be a non-negative integer")
    trust, trust_snapshot = _load_with_fallback(
        Path(trust_policy_path), TRUST_TEMPLATE_PATH, "schemas/operational-trust-policy.schema.json", "operational trust policy", errors
    )
    runtime_policy, runtime_policy_snapshot = _load_with_fallback(
        Path(runtime_policy_path), RUNTIME_POLICY_TEMPLATE_PATH, "schemas/runtime-authorization-policy.schema.json", "runtime authorization policy", errors
    )
    readiness, readiness_snapshot = _load_with_fallback(
        Path(readiness_report_path), READINESS_REPORT_PATH, "schemas/operational-readiness-report.schema.json", "release readiness report", errors
    )
    trusted_time, trusted_time_snapshot = _load_with_fallback(
        Path(trusted_time_path), TIME_EXAMPLE_PATH, "schemas/trusted-time-attestation.schema.json", "trusted time attestation", errors
    )
    binding, binding_snapshot = _load_with_fallback(
        Path(account_binding_path), ACCOUNT_BINDING_EXAMPLE_PATH, "schemas/account-authorization-binding.schema.json", "account authorization binding", errors
    )
    state, state_snapshot = _load_with_fallback(
        Path(runtime_state_path), RUNTIME_STATE_EXAMPLE_PATH, "schemas/runtime-state-bundle.schema.json", "runtime state bundle", errors
    )
    lease, lease_snapshot = _load_with_fallback(
        Path(runtime_lease_path), RUNTIME_LEASE_EXAMPLE_PATH, "schemas/runtime-control-plane-lease.schema.json", "runtime lease", errors
    )
    operation, operation_snapshot = _load_with_fallback(
        Path(operation_authorization_path), OPERATION_EXAMPLE_PATH, "schemas/per-operation-authorization.schema.json", "operation authorization", errors
    )
    capsule, capsule_snapshot = _load_with_fallback(
        Path(execution_capsule_path), CAPSULE_EXAMPLE_PATH, "schemas/execution-capsule.schema.json", "execution capsule", errors
    )

    try:
        authorizer_hash = runtime_authorizer_bundle_hash()
    except Exception as exc:
        authorizer_hash = "0" * 64
        errors.append(f"runtime authorizer bundle could not be hashed: {exc}")

    _check_anchor("ONE_INTENT_TRUST_POLICY_SHA256", trust_snapshot.digest, errors)
    _check_anchor("ONE_INTENT_RUNTIME_AUTHORIZATION_POLICY_SHA256", runtime_policy_snapshot.digest, errors)
    _check_anchor("ONE_INTENT_RUNTIME_AUTHORIZER_SHA256", authorizer_hash, errors)
    _check_anchor("ONE_INTENT_RELEASE_READINESS_REPORT_SHA256", readiness_snapshot.digest, errors)
    _check_anchor("ONE_INTENT_TRUSTED_TIME_ATTESTATION_SHA256", trusted_time_snapshot.digest, errors)

    profile_id = str(runtime_policy.get("profileId") or readiness.get("profileId") or "INVALID_PROFILE")
    if trust.get("enabled") is not True or trust.get("policyVersion") in {None, "TEMPLATE-NOT-ACTIVE"}:
        errors.append("operational trust policy is disabled or still a template")
    if runtime_policy.get("enabled") is not True or runtime_policy.get("policyVersion") in {None, "TEMPLATE-NOT-ACTIVE"}:
        errors.append("runtime authorization policy is disabled or still a template")
    if trust.get("canonicalization") != CANONICALIZATION_PROFILE or runtime_policy.get("canonicalization") != CANONICALIZATION_PROFILE:
        errors.append("canonicalization profile mismatch")
    if trust.get("signatureProfile") != SIGNATURE_PROFILE or runtime_policy.get("signatureProfile") != SIGNATURE_PROFILE:
        errors.append("signature profile mismatch")
    try:
        lease_allowed = runtime_policy["lease"]["allowedCapabilities"]
        operation_allowed = runtime_policy["operation"]["allowedCapabilities"]
        mapping_values = list(runtime_policy["operation"]["stepTypeCapabilityMap"].values())
        if lease_allowed != sorted(set(lease_allowed)) or operation_allowed != sorted(set(operation_allowed)):
            errors.append("runtime capability allowlists must be sorted and duplicate-free")
        if not set(mapping_values) <= set(lease_allowed) or not set(mapping_values) <= set(operation_allowed):
            errors.append("runtime step capability mapping escapes a policy allowlist")
        if runtime_policy["operation"].get("requireQuoteHash") is not True or runtime_policy["operation"].get("requireQuoteValidUntil") is not True:
            errors.append("production runtime policy must require a quote hash and quote expiry")
        network_policy = runtime_policy["network"]
        if network_policy.get("networkRegistrySha256") == "0" * 64:
            errors.append("production runtime policy has no real network-registry digest")
        for field in ("allowedSourceNetworkIds", "allowedDestinationNetworkIds"):
            values = network_policy.get(field, [])
            if values != sorted(set(values)):
                errors.append(f"runtime network allowlist must be sorted and duplicate-free: {field}")
        if not network_policy.get("allowedSourceNetworkIds"):
            errors.append("production runtime policy has no allowed source network")
    except Exception as exc:
        errors.append(f"runtime authorization policy structure rejected: {exc}")
    documents = (trust, runtime_policy, readiness, trusted_time, binding, state, lease, operation)
    if any(item.get("profileId") != profile_id for item in documents if isinstance(item, dict) and "profileId" in item):
        errors.append("profileId mismatch across runtime authorization inputs")

    try:
        key_map = _key_map(trust)
    except Exception as exc:
        key_map = {}
        errors.append(f"runtime trust-key map rejected: {exc}")
    revoked = set(trust.get("revokedKeyIds", []))

    evaluated_at = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
    time_valid_until = evaluated_at
    try:
        evaluated_at = parse_time(trusted_time["observedAt"], "trusted runtime time observedAt")
        time_valid_until = parse_time(trusted_time["validUntil"], "trusted runtime time validUntil")
        time_sequence = trusted_time.get("sequence")
        if not isinstance(time_sequence, int) or isinstance(time_sequence, bool) or time_sequence < 1:
            errors.append("runtime trusted time sequence must be positive")
            time_sequence = 0
        if time_sequence <= minimum_trusted_time_sequence:
            errors.append("runtime trusted time sequence is not above the protected high-water mark")
        if trusted_time.get("trusted") is not True or not (evaluated_at < time_valid_until):
            errors.append("runtime trusted time is untrusted or has an invalid interval")
        if time_valid_until - evaluated_at > dt.timedelta(seconds=300):
            errors.append("runtime trusted time exceeds 300 seconds")
        local_now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
        if not (evaluated_at - dt.timedelta(seconds=60) <= local_now < time_valid_until):
            errors.append("runtime trusted time is not fresh for the verifier clock")
        authority = trusted_time.get("authority", {})
        verify_signature(
            trusted_time,
            signature_field="signature",
            policy=trust,
            required_roles={"TRUSTED_TIME_AUTHORITY"},
            evaluated_at=evaluated_at,
            signed_at=evaluated_at,
            expected_identity_key_id=authority.get("keyId"),
            expected_principal_id=authority.get("principalId"),
            expected_organization=authority.get("organization"),
            declared_role=authority.get("role"),
            key_map=key_map,
        )
    except Exception as exc:
        errors.append(f"runtime trusted time rejected: {exc}")

    release_subject = readiness.get("releaseSubject")
    if not isinstance(release_subject, dict):
        fallback_report, _ = secure_load_json(READINESS_REPORT_PATH)
        release_subject = fallback_report["releaseSubject"]
        errors.append("release readiness subject is missing")
    try:
        release_subject_digest = subject_hash(release_subject)
    except Exception as exc:
        release_subject_digest = "0" * 64
        errors.append(f"release subject hash failed: {exc}")
    _check_anchor("ONE_INTENT_RELEASE_SUBJECT_SHA256", release_subject_digest, errors)

    decision_expiries: list[dt.datetime] = [time_valid_until]
    try:
        readiness_generated = parse_time(readiness["generatedAt"], "readiness generatedAt")
        readiness_valid_until = parse_time(readiness["validUntil"], "readiness validUntil")
        decision_expiries.append(readiness_valid_until)
        if not (readiness_generated <= evaluated_at < readiness_valid_until):
            errors.append("release readiness decision is not current")
        summary = readiness.get("summary", {})
        if (
            readiness.get("status") != "PRODUCTION_OPERATIONAL_GO"
            or readiness.get("releaseEligibleForRuntimeActivation") is not True
            or readiness.get("productionWritePermitted") is not False
            or summary.get("mandatoryGates") != 37
            or summary.get("passedGates") != 37
            or summary.get("blockedGates") != 0
            or summary.get("requiredClaims") != 93
            or summary.get("acceptedClaims") != 93
            or summary.get("missingOrRejectedClaims") != 0
        ):
            errors.append("release readiness report is not an exact 37/93 GO decision")
        readiness_config, _ = secure_load_json(ROOT / "config/operational-readiness.json")
        expected_gates = {
            gate["gateId"]: len(gate["claims"])
            for gate in readiness_config.get("gates", [])
            if gate.get("mandatory") is True
        }
        actual_gates = readiness.get("gates", [])
        if not isinstance(actual_gates, list) or len(actual_gates) != len(expected_gates):
            errors.append("release readiness gate rows do not match the mandatory gate inventory")
        else:
            seen_gate_ids: set[str] = set()
            for row in actual_gates:
                gate_id = row.get("gateId") if isinstance(row, dict) else None
                expected_claims = expected_gates.get(gate_id)
                if gate_id in seen_gate_ids or expected_claims is None:
                    errors.append(f"release readiness contains an unknown or duplicate gate row: {gate_id!r}")
                    continue
                seen_gate_ids.add(gate_id)
                expected_gate = next(item for item in readiness_config["gates"] if item["gateId"] == gate_id)
                if (
                    row.get("titleJa") != expected_gate.get("titleJa")
                    or row.get("status") != "PASS"
                    or row.get("requiredClaims") != expected_claims
                    or row.get("acceptedClaims") != expected_claims
                    or row.get("blockingClaims") != []
                ):
                    errors.append(f"release readiness gate is not an exact PASS row: {gate_id}")
            if seen_gate_ids != set(expected_gates):
                errors.append("release readiness gate set is incomplete")
        if readiness.get("blockingReasons") != []:
            errors.append("GO release readiness report still contains blocking reasons")
        if release_subject.get("environment") != "PRODUCTION" or any(
            release_subject.get(field) in {None, ""}
            for field in (
                "sourceCommit", "sourceTreeSha256", "androidArtifactSha256", "iosArtifactSha256",
                "backendImageDigest", "signerImageDigest", "configurationBundleSha256", "policyBundleSha256",
                "assetRegistrySha256", "sbomSha256",
            )
        ):
            errors.append("release readiness subject is not a complete PRODUCTION subject")
        inputs = readiness.get("decisionInputs", {})
        if inputs.get("operationalTrustPolicySha256") != trust_snapshot.digest:
            errors.append("readiness report is bound to a different operational trust policy")
        if inputs.get("readinessVerifierBundleSha256") != readiness_bundle_hash():
            errors.append("readiness report is bound to a different readiness verifier bundle")
        if inputs.get("releaseSubjectSha256") != release_subject_digest:
            errors.append("readiness report release-subject digest mismatch")
        if inputs.get("trustedTimeAttestationSha256") != trusted_time_snapshot.digest:
            errors.append("readiness report and runtime evaluation do not use the same trusted-time attestation")
        evidence_index_sequence = inputs.get("evidenceIndexSequence")
        if (
            not HEX64.fullmatch(str(inputs.get("evidenceIndexSha256", "")))
            or not isinstance(evidence_index_sequence, int)
            or isinstance(evidence_index_sequence, bool)
            or evidence_index_sequence < 1
        ):
            errors.append("readiness report lacks a positive, exact evidence-index binding")
            evidence_index_sequence = 0
        if evidence_index_sequence <= minimum_evidence_index_sequence:
            errors.append("readiness evidence-index sequence is not above the protected high-water mark")
        readiness_time_sequence = inputs.get("trustedTimeSequence")
        if readiness_time_sequence != trusted_time.get("sequence"):
            errors.append("readiness report trusted-time sequence does not match the runtime attestation")
        if (
            not isinstance(readiness_time_sequence, int)
            or isinstance(readiness_time_sequence, bool)
            or readiness_time_sequence <= minimum_trusted_time_sequence
        ):
            errors.append("readiness trusted-time sequence is not above the protected high-water mark")
        if readiness_valid_until > time_valid_until:
            errors.append("readiness decision outlives its bound trusted-time attestation")
    except Exception as exc:
        errors.append(f"release readiness decision rejected: {exc}")

    for label, document in (("account binding", binding), ("runtime state", state), ("runtime lease", lease), ("operation", operation)):
        if document.get("releaseSubject") != release_subject:
            errors.append(f"{label} is bound to a different release subject")

    deployment_id = state.get("deploymentId")
    if not isinstance(deployment_id, str) or not CANONICAL_ID.fullmatch(deployment_id):
        errors.append("runtime deploymentId is invalid")
    for label, document in (("account binding", binding), ("runtime lease", lease), ("operation", operation)):
        if document.get("deploymentId") != deployment_id:
            errors.append(f"{label} deploymentId mismatch")

    # Account-to-user/device key binding.
    binding_identities: list[TrustedKey] = []
    binding_issued = evaluated_at
    binding_expires = evaluated_at
    try:
        binding_issued = parse_time(binding["issuedAt"], "account binding issuedAt")
        binding_expires = parse_time(binding["expiresAt"], "account binding expiresAt")
        decision_expiries.append(binding_expires)
        binding_policy = runtime_policy["accountBinding"]
        if not (binding_issued <= evaluated_at < binding_expires):
            errors.append("account authorization binding is not current")
        if binding_expires - binding_issued > dt.timedelta(seconds=int(binding_policy["maxLifetimeSeconds"])):
            errors.append("account authorization binding exceeds policy lifetime")
        if binding.get("status") != "ACTIVE" or int(binding.get("sequence", 0)) <= minimum_account_binding_sequence:
            errors.append("account authorization binding is inactive or replayed")
        if binding.get("registrySha256") != state.get("accountRegistrySha256"):
            errors.append("account binding registry digest does not match runtime state")
        if binding.get("account") != operation.get("account") or binding.get("bindingId") != operation.get("accountBindingId"):
            errors.append("operation is not bound to the exact account authorization binding")
        if binding.get("deviceAttestationSha256") == "0" * 64:
            errors.append("account binding has no real device-attestation digest")
        user_fingerprint = _load_ed25519_public_key(binding.get("userKey", {}).get("publicKeyPem", ""))[1]
        device_fingerprint = _load_ed25519_public_key(binding.get("deviceKey", {}).get("publicKeyPem", ""))[1]
        if user_fingerprint == device_fingerprint:
            errors.append("user and device authorization keys must be cryptographically distinct")
        binding_identities = _verify_multisig(
            binding,
            payload=account_binding_payload(binding),
            key_map=key_map,
            revoked_key_ids=revoked,
            required_roles=list(binding_policy["requiredRoles"]),
            threshold=int(binding_policy["signatureThreshold"]),
            minimum_organizations=int(binding_policy["minimumDistinctOrganizations"]),
            evaluated_at=evaluated_at,
            signed_at=binding_issued,
        )
        decision_expiries.extend(identity.valid_until for identity in binding_identities)
    except Exception as exc:
        errors.append(f"account authorization binding rejected: {exc}")

    # Runtime health state.
    state_identities: list[TrustedKey] = []
    state_issued = evaluated_at
    state_expires = evaluated_at
    try:
        state_issued = parse_time(state["issuedAt"], "runtime state issuedAt")
        state_expires = parse_time(state["expiresAt"], "runtime state expiresAt")
        decision_expiries.append(state_expires)
        state_policy = runtime_policy["runtimeState"]
        if not (state_issued <= evaluated_at < state_expires):
            errors.append("runtime state bundle is not current")
        if state_expires - state_issued > dt.timedelta(seconds=int(state_policy["maxLifetimeSeconds"])):
            errors.append("runtime state bundle exceeds policy lifetime")
        if int(state.get("sequence", 0)) <= minimum_runtime_state_sequence:
            errors.append("runtime state sequence is not above the protected high-water mark")
        if (
            state.get("killSwitch") is not False
            or state.get("writesEnabled") is not True
            or state.get("incidentState") != "HEALTHY"
            or state.get("reconciliationState") != "MATCHED"
            or state.get("sourceFreshnessState") != "FRESH"
            or state.get("providerHealthState") != "HEALTHY"
        ):
            errors.append("runtime state is not fully healthy/write-enabled")
        if state.get("policyBundleSha256") != release_subject.get("policyBundleSha256"):
            errors.append("runtime policy bundle digest differs from release subject")
        if state.get("assetRegistrySha256") != release_subject.get("assetRegistrySha256"):
            errors.append("runtime asset registry digest differs from release subject")
        if state.get("networkRegistrySha256") != runtime_policy.get("network", {}).get("networkRegistrySha256"):
            errors.append("runtime network registry digest differs from the anchored runtime policy")
        state_identities = _verify_multisig(
            state,
            payload=runtime_state_payload(state),
            key_map=key_map,
            revoked_key_ids=revoked,
            required_roles=list(state_policy["requiredRoles"]),
            threshold=int(state_policy["signatureThreshold"]),
            minimum_organizations=int(state_policy["minimumDistinctOrganizations"]),
            evaluated_at=evaluated_at,
            signed_at=state_issued,
        )
        decision_expiries.extend(identity.valid_until for identity in state_identities)
    except Exception as exc:
        errors.append(f"runtime state rejected: {exc}")

    # Short-lived service capability lease. It never represents user consent.
    lease_identities: list[TrustedKey] = []
    lease_issued = evaluated_at
    lease_expires = evaluated_at
    lease_capabilities: set[str] = set()
    try:
        lease_issued = parse_time(lease["issuedAt"], "runtime lease issuedAt")
        lease_expires = parse_time(lease["expiresAt"], "runtime lease expiresAt")
        decision_expiries.append(lease_expires)
        lease_policy = runtime_policy["lease"]
        if not (state_issued <= lease_issued <= evaluated_at < lease_expires <= state_expires):
            errors.append("runtime lease chronology is invalid or outlives runtime state")
        if lease_expires - lease_issued > dt.timedelta(seconds=int(lease_policy["maxLifetimeSeconds"])):
            errors.append("runtime lease exceeds policy lifetime")
        if int(lease.get("sequence", 0)) <= minimum_runtime_lease_sequence:
            errors.append("runtime lease sequence is not above the protected high-water mark")
        if lease.get("runtimeBundleId") != state.get("bundleId"):
            errors.append("runtime lease does not reference the exact runtime state bundle")
        if lease.get("transactionAuthorizationGranted") is not False:
            errors.append("runtime lease illegally claims transaction authorization")
        capabilities = lease.get("capabilities", [])
        if not isinstance(capabilities, list) or not capabilities or capabilities != sorted(capabilities) or len(capabilities) != len(set(capabilities)):
            errors.append("runtime lease capabilities must be a non-empty sorted duplicate-free list")
            capabilities = capabilities if isinstance(capabilities, list) else []
        lease_capabilities = set(capabilities)
        if not lease_capabilities <= set(lease_policy["allowedCapabilities"]):
            errors.append("runtime lease contains a capability outside the policy allowlist")
        lease_identities = _verify_multisig(
            lease,
            payload=runtime_lease_payload(lease),
            key_map=key_map,
            revoked_key_ids=revoked,
            required_roles=list(lease_policy["requiredRoles"]),
            threshold=int(lease_policy["signatureThreshold"]),
            minimum_organizations=int(lease_policy["minimumDistinctOrganizations"]),
            evaluated_at=evaluated_at,
            signed_at=lease_issued,
        )
        decision_expiries.extend(identity.valid_until for identity in lease_identities)
    except Exception as exc:
        errors.append(f"runtime lease rejected: {exc}")

    # Exact execution capsule and state/presentation binding.
    capsule_hash: str | None = None
    derived_capabilities: list[str] = []
    capsule_expires = evaluated_at
    try:
        capsule_hash = domain_hash(CAPSULE_AUTHORIZATION_DOMAIN, capsule)
        expected = expected_hashes(capsule)
        for field, value in expected.items():
            actual = (
                capsule.get("authorizationPresentation", {}).get("promptTextHash")
                if field == "promptTextHash"
                else capsule.get(field)
            )
            if actual != value:
                errors.append(f"execution capsule derived hash mismatch: {field}")
        capsule_created = _parse_iso_timestamp(capsule["createdAt"], "execution capsule createdAt")
        capsule_expires = _parse_iso_timestamp(capsule["expiresAt"], "execution capsule expiresAt")
        decision_expiries.append(capsule_expires)
        if not (capsule_created <= evaluated_at < capsule_expires):
            errors.append("execution capsule is not current")
        if capsule.get("environment") != "MAINNET" or capsule.get("accountMode") == "UNKNOWN":
            errors.append("production runtime requires a MAINNET capsule with a known account mode")
        if capsule.get("account") != operation.get("account"):
            errors.append("execution capsule account differs from operation authorization")
        network_context = capsule.get("networkContext", {})
        network_policy = runtime_policy.get("network", {})
        source_network = network_context.get("sourceNetworkId")
        destination_networks = network_context.get("destinationNetworkIds", [])
        if network_context.get("networkRegistrySha256") != network_policy.get("networkRegistrySha256"):
            errors.append("execution capsule network registry digest mismatch")
        if source_network not in set(network_policy.get("allowedSourceNetworkIds", [])):
            errors.append("execution capsule source network is not allowed by runtime policy")
        if not isinstance(destination_networks, list) or destination_networks != sorted(set(destination_networks)):
            errors.append("execution capsule destination networks must be sorted and duplicate-free")
        elif not set(destination_networks) <= set(network_policy.get("allowedDestinationNetworkIds", [])):
            errors.append("execution capsule contains an unapproved destination network")
        mapping = runtime_policy["operation"]["stepTypeCapabilityMap"]
        capabilities: set[str] = set()
        high_risk = False
        for step in capsule.get("steps", []):
            step_type = step.get("type")
            if step_type not in mapping:
                errors.append(f"execution step has no capability mapping: {step_type!r}")
                continue
            capabilities.add(mapping[step_type])
            if step.get("account") != capsule.get("account"):
                errors.append(f"execution step account mismatch: {step.get('stepId')}")
            if step.get("requiredAuth") in {None, "NONE"}:
                errors.append(f"Mainnet execution step lacks explicit authorization: {step.get('stepId')}")
            step_expiry = _parse_iso_timestamp(step.get("expiresAt"), f"step {step.get('stepId')} expiresAt")
            if not (evaluated_at < step_expiry <= capsule_expires):
                errors.append(f"execution step expiry is invalid: {step.get('stepId')}")
            if step.get("riskTier") in {"R2", "R3", "R4"}:
                high_risk = True
        derived_capabilities = sorted(capabilities)
        if not capabilities or not capabilities <= set(runtime_policy["operation"]["allowedCapabilities"]):
            errors.append("execution capsule capabilities are empty or outside the runtime policy")
        state_evidence = capsule.get("stateEvidence", {})
        observed = _parse_iso_timestamp(state_evidence.get("observedAt"), "capsule stateEvidence observedAt")
        max_age = int(state_evidence.get("maxAgeMs", 0))
        if observed > evaluated_at or evaluated_at - observed > dt.timedelta(milliseconds=max_age):
            errors.append("execution capsule state evidence is stale")
        if state_evidence.get("stateHash") == "0x" + "0" * 64:
            errors.append("execution capsule state evidence uses a zero state hash")
        source_ids: set[str] = set()
        for source in state_evidence.get("sources", []):
            source_id = source.get("sourceId")
            if source_id in source_ids:
                errors.append(f"execution capsule repeats state sourceId: {source_id!r}")
            source_ids.add(source_id)
            source_observed = _parse_iso_timestamp(source.get("observedAt"), f"state source {source_id} observedAt")
            if not (capsule_created <= source_observed <= observed <= evaluated_at):
                errors.append(f"execution capsule state-source chronology is invalid: {source_id!r}")
            if source.get("digest") == "0x" + "0" * 64:
                errors.append(f"execution capsule state source uses a zero digest: {source_id!r}")
        rendered_at = _parse_iso_timestamp(capsule.get("renderReceipt", {}).get("renderedAt"), "render receipt renderedAt")
        if not (capsule_created <= rendered_at <= evaluated_at < capsule_expires):
            errors.append("execution capsule render receipt chronology is invalid")
        if state_evidence.get("divergenceStatus") not in {"CONSISTENT", "WITHIN_TOLERANCE"}:
            errors.append("execution capsule state evidence is divergent or unchecked")
        if high_risk:
            classes = {source.get("independenceClass") for source in state_evidence.get("sources", [])}
            if state_evidence.get("policy") == "SINGLE_SOURCE_R1" or len(classes) < 2:
                errors.append("R2+ execution capsule lacks independent state-source quorum")
        presentation = capsule.get("authorizationPresentation", {})
        if presentation.get("mode") == "BLOCKED_UNAVAILABLE" or presentation.get("assurance") in {"BLOCKED", "APP_RENDER_ONLY"}:
            errors.append("execution capsule lacks an acceptable authenticated authorization presentation")
        if capsule.get("renderReceipt", {}).get("locale") != "ja-JP":
            errors.append("Japan production profile requires a ja-JP confirmation receipt")
    except Exception as exc:
        errors.append(f"execution capsule rejected: {exc}")

    # One operation, exact user/device/policy signatures, and replay protection.
    operation_issued = evaluated_at
    operation_expires = evaluated_at
    policy_identity: TrustedKey | None = None
    try:
        operation_issued = parse_time(operation["issuedAt"], "operation authorization issuedAt")
        operation_expires = parse_time(operation["expiresAt"], "operation authorization expiresAt")
        decision_expiries.append(operation_expires)
        operation_policy = runtime_policy["operation"]
        if not (max(binding_issued, state_issued, lease_issued) <= operation_issued <= evaluated_at < operation_expires):
            errors.append("operation authorization chronology is invalid")
        if operation_expires - operation_issued > dt.timedelta(seconds=int(operation_policy["maxLifetimeSeconds"])):
            errors.append("operation authorization exceeds policy lifetime")
        if operation_expires > min(binding_expires, state_expires, lease_expires, capsule_expires):
            errors.append("operation authorization outlives a bound input")
        if operation.get("runtimeBundleId") != state.get("bundleId") or operation.get("runtimeLeaseId") != lease.get("leaseId"):
            errors.append("operation authorization is not bound to exact runtime state/lease IDs")
        if operation.get("executionCapsuleHash") != capsule_hash:
            errors.append("operation authorization executionCapsuleHash mismatch")
        if operation.get("sourceStateHash") != capsule.get("sourceStateHash"):
            errors.append("operation authorization sourceStateHash mismatch")
        quote_hash = operation.get("quoteHash")
        if operation_policy.get("requireQuoteHash") is True and (
            quote_hash is None or quote_hash == "0x" + "0" * 64
        ):
            errors.append("operation authorization lacks a non-zero mandatory quote hash")
        quote_valid_until = operation_expires
        if operation_policy.get("requireQuoteValidUntil") is True:
            quote_valid_until = parse_time(operation.get("quoteValidUntil"), "operation quoteValidUntil")
            decision_expiries.append(quote_valid_until)
            if not (operation_issued <= evaluated_at < quote_valid_until <= min(operation_expires, capsule_expires, lease_expires)):
                errors.append("operation quote is expired or outlives a bound authorization input")
        if not (capsule_created <= operation_issued and rendered_at <= operation_issued):
            errors.append("operation authorization predates its execution capsule or rendered confirmation")
        readiness_generated = parse_time(readiness["generatedAt"], "readiness generatedAt")
        if binding_issued < readiness_generated or state_issued < readiness_generated or lease_issued < readiness_generated:
            errors.append("runtime binding/state/lease predates the approved release decision")
        required = operation.get("requiredCapabilities", [])
        if not isinstance(required, list) or required != sorted(required) or len(required) != len(set(required)) or required != derived_capabilities:
            errors.append("operation requiredCapabilities do not exactly match the execution capsule")
        if not set(derived_capabilities) <= lease_capabilities:
            errors.append("runtime lease does not cover every capability required by the operation")
        if operation.get("authorized") is not True or operation.get("oneTimeUse") is not True:
            errors.append("operation authorization is denied or not single-use")
        authorization_id = operation.get("authorizationId")
        nonce = operation.get("nonce")
        if authorization_id in consumed_authorization_ids:
            errors.append("operation authorizationId has already been consumed")
        if nonce in consumed_nonces:
            errors.append("operation nonce has already been consumed")
        if not isinstance(nonce, str) or not CANONICAL_ID.fullmatch(nonce) or "EXAMPLE" in nonce.upper():
            errors.append("operation nonce is not a production-grade canonical nonce")
        payload = operation_authorization_payload(operation)
        user_fingerprint = _verify_embedded_authorization_signature(
            operation.get("userAuthorization"), payload,
            binding_key=binding.get("userKey", {}), expected_role=str(operation_policy["userRole"]),
        )
        device_fingerprint = _verify_embedded_authorization_signature(
            operation.get("deviceAuthorization"), payload,
            binding_key=binding.get("deviceKey", {}), expected_role=str(operation_policy["deviceRole"]),
        )
        if user_fingerprint == device_fingerprint:
            errors.append("operation user/device signatures resolve to the same public key")
        policy_signature = operation.get("policyAuthorization")
        policy_identity = _verify_trusted_runtime_signature(
            policy_signature,
            payload,
            key_map=key_map,
            revoked_key_ids=revoked,
            allowed_roles={str(operation_policy["policyEngineRole"])},
            evaluated_at=evaluated_at,
            signed_at=operation_issued,
        )
        decision_expiries.append(policy_identity.valid_until)
        signed_key_ids = {
            operation.get("userAuthorization", {}).get("keyId"),
            operation.get("deviceAuthorization", {}).get("keyId"),
            operation.get("policyAuthorization", {}).get("keyId"),
        }
        signed_principals = {
            operation.get("userAuthorization", {}).get("principalId"),
            operation.get("deviceAuthorization", {}).get("principalId"),
            operation.get("policyAuthorization", {}).get("principalId"),
        }
        if len(signed_key_ids) != 3 or len(signed_principals) != 3:
            errors.append("user, device, and policy authorizations must use distinct keys and principals")
    except Exception as exc:
        errors.append(f"operation authorization rejected: {exc}")

    valid_until = min(decision_expiries) if decision_expiries else evaluated_at
    if valid_until <= evaluated_at:
        errors.append("runtime authorization decision has no positive validity window")

    decision_inputs = {
        "operationalTrustPolicySha256": trust_snapshot.digest,
        "runtimeAuthorizationPolicySha256": runtime_policy_snapshot.digest,
        "runtimeAuthorizerBundleSha256": authorizer_hash if HEX64.fullmatch(authorizer_hash) else None,
        "releaseReadinessReportSha256": readiness_snapshot.digest,
        "releaseSubjectSha256": release_subject_digest if HEX64.fullmatch(release_subject_digest) else None,
        "trustedTimeAttestationSha256": trusted_time_snapshot.digest,
        "trustedTimeSequence": trusted_time.get("sequence", 0) if isinstance(trusted_time.get("sequence"), int) and not isinstance(trusted_time.get("sequence"), bool) else 0,
        "evidenceIndexSequence": readiness.get("decisionInputs", {}).get("evidenceIndexSequence", 0) if isinstance(readiness.get("decisionInputs"), dict) and isinstance(readiness.get("decisionInputs", {}).get("evidenceIndexSequence"), int) and not isinstance(readiness.get("decisionInputs", {}).get("evidenceIndexSequence"), bool) else 0,
        "accountAuthorizationBindingSha256": binding_snapshot.digest,
        "runtimeStateBundleSha256": state_snapshot.digest,
        "runtimeLeaseSha256": lease_snapshot.digest,
        "operationAuthorizationSha256": operation_snapshot.digest,
        "executionCapsuleSha256": capsule_snapshot.digest,
    }
    report = _decision_report(
        profile_id=profile_id,
        evaluated_at=evaluated_at,
        valid_until=valid_until,
        release_subject=release_subject,
        state=state,
        lease=lease,
        operation=operation,
        required_capabilities=derived_capabilities,
        decision_inputs=decision_inputs,
        errors=errors,
    )
    report_schema_errors = validate_schema(report, "schemas/runtime-authorization-decision.schema.json", "runtime authorization decision")
    if report_schema_errors:
        errors.extend(report_schema_errors)
        report = _decision_report(
            profile_id=profile_id,
            evaluated_at=evaluated_at,
            valid_until=valid_until,
            release_subject=release_subject,
            state=state,
            lease=lease,
            operation=operation,
            required_capabilities=derived_capabilities,
            decision_inputs=decision_inputs,
            errors=errors,
        )
    return RuntimeEvaluation(report=report, errors=tuple(errors))
