#!/usr/bin/env python3
"""Fail-closed operational-readiness evidence evaluator.

The current design package is expected to be ``BLOCKED_NOT_OPERATIONAL``. A
future immutable production release may obtain ``PRODUCTION_OPERATIONAL_GO``
only when every mandatory claim is backed by current, release-bound, signed and
independently reviewed evidence, and the verifier receives protected anchors
that were provisioned outside the repository.

A release GO is deliberately *not* a transaction authorization. The report
always keeps ``productionWritePermitted`` false. Runtime writes require a
separate fresh runtime-state quorum, a short-lived service lease and a
single-use operation authorization checked by the production signer.
"""
from __future__ import annotations

import base64
import copy
import datetime as dt
import hashlib
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from canonical_hashes import canonical_json, strict_load_json, strict_load_json_bytes
from package_metadata import ROOT, load_package_metadata

CONFIG_PATH = ROOT / "config/operational-readiness.json"
TEMPLATE_TRUST_PATH = ROOT / "config/operational-trust-policy.template.json"
INDEX_PATH = ROOT / "delivery/evidence-index.json"
REPORT_PATH = ROOT / "delivery/OPERATIONAL_READINESS_REPORT.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
CANONICAL_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
MIME = re.compile(r"^[a-z0-9][a-z0-9.+-]*/[a-z0-9][a-z0-9.+-]*$")
SIGNATURE_PROFILE = "ONE_INTENT_ED25519_CANONICAL_JSON_V2"
CANONICALIZATION_PROFILE = "ONE_INTENT_CANONICAL_JSON_SUBSET_V1"
MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_SIGNED_JSON_BYTES = 2 * 1024 * 1024
MAX_TIME_JSON_BYTES = 64 * 1024
MAX_EVIDENCE_BYTES = 256 * 1024 * 1024
MAX_GENERAL_FILE_BYTES = 512 * 1024 * 1024

# The protected checker anchor binds the evaluator *and* every local input that
# could weaken it. Hashing only this Python file would let an attacker replace
# the gate profile or JSON schemas while leaving the checker unchanged.
READINESS_BUNDLE_FILES = (
    "config/build-metadata.json",
    "config/operational-readiness.json",
    "schemas/operational-readiness-config.schema.json",
    "schemas/operational-trust-policy.schema.json",
    "schemas/operational-evidence-index.schema.json",
    "schemas/operational-evidence-statement.schema.json",
    "schemas/operational-review-approval.schema.json",
    "schemas/operational-readiness-report.schema.json",
    "schemas/trusted-time-attestation.schema.json",
    "schemas/runtime-state-bundle.schema.json",
    "schemas/runtime-control-plane-lease.schema.json",
    "schemas/per-operation-authorization.schema.json",
    "tools/canonical_hashes.py",
    "tools/package_metadata.py",
    "tools/operational_readiness.py",
    "tools/check_operational_readiness.py",
    "tools/test_operational_readiness_positive.py",
    "tools/test_operational_readiness_negative.py",
    "tools/run_full_validation.py",
    "tools/requirements.txt",
)


@dataclass(frozen=True)
class Evaluation:
    report: dict[str, Any]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class FileSnapshot:
    digest: str
    size: int
    data: bytes | None


@dataclass(frozen=True)
class TrustedKey:
    key_id: str
    principal_id: str
    organization: str
    roles: frozenset[str]
    valid_from: dt.datetime
    valid_until: dt.datetime
    public_key: Any
    fingerprint: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_regular_file_stat(path: Path, value: os.stat_result, max_bytes: int) -> None:
    if not stat.S_ISREG(value.st_mode):
        raise ValueError(f"not a regular file: {path}")
    if value.st_nlink != 1:
        raise ValueError(f"hard-linked files are prohibited for trusted input: {path}")
    if os.name == "posix" and value.st_mode & 0o022:
        raise ValueError(f"group/world-writable trusted input is prohibited: {path}")
    if value.st_mode & (stat.S_ISUID | stat.S_ISGID | stat.S_ISVTX):
        raise ValueError(f"special mode bits are prohibited on trusted input: {path}")
    if value.st_size < 0 or value.st_size > max_bytes:
        raise ValueError(f"trusted input size is outside 0..{max_bytes} bytes: {path}")


def secure_file_snapshot(path: Path, *, max_bytes: int = MAX_GENERAL_FILE_BYTES, include_data: bool = False) -> FileSnapshot:
    """Read one immutable regular file without following a final-component link.

    The descriptor is checked before and after reading so a concurrent size,
    inode or timestamp change fails closed. Evidence paths additionally reject
    symlinks in every path component in :func:`safe_evidence_path`.
    """
    path = Path(path)
    try:
        before_path = path.lstat()
    except OSError as exc:
        raise ValueError(f"cannot stat trusted input {path}: {exc}") from exc
    if stat.S_ISLNK(before_path.st_mode):
        raise ValueError(f"symlink trusted input is prohibited: {path}")
    _validate_regular_file_stat(path, before_path, max_bytes)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError(f"cannot securely open trusted input {path}: {exc}") from exc
    digest = hashlib.sha256()
    chunks: list[bytes] | None = [] if include_data else None
    total = 0
    try:
        opened = os.fstat(descriptor)
        _validate_regular_file_stat(path, opened, max_bytes)
        if (opened.st_dev, opened.st_ino) != (before_path.st_dev, before_path.st_ino):
            raise ValueError(f"trusted input changed before open: {path}")
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(f"trusted input exceeded maximum while reading: {path}")
            digest.update(chunk)
            if chunks is not None:
                chunks.append(chunk)
        after = os.fstat(descriptor)
        if (
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            != (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns)
        ):
            raise ValueError(f"trusted input changed while reading: {path}")
        if total != opened.st_size:
            raise ValueError(f"trusted input byte count changed while reading: {path}")
    finally:
        os.close(descriptor)
    return FileSnapshot(digest=digest.hexdigest(), size=total, data=b"".join(chunks) if chunks is not None else None)


def sha256_file(path: Path) -> str:
    return secure_file_snapshot(path).digest


def secure_load_json(path: Path, *, max_bytes: int = MAX_JSON_BYTES) -> tuple[Any, FileSnapshot]:
    snapshot = secure_file_snapshot(path, max_bytes=max_bytes, include_data=True)
    assert snapshot.data is not None
    try:
        return strict_load_json_bytes(snapshot.data), snapshot
    except Exception as exc:
        raise ValueError(f"invalid strict JSON in {path}: {exc}") from exc


SIGNATURE_ENVELOPE_DOMAIN = b"ONE_INTENT_SIGNED_DOCUMENT_V2"
SIGNATURE_DOCUMENT_DOMAINS = {
    "statementId": "ONE_INTENT_OPERATIONAL_EVIDENCE_STATEMENT_V1",
    "approvalId": "ONE_INTENT_OPERATIONAL_REVIEW_APPROVAL_V1",
    "attestationId": "ONE_INTENT_TRUSTED_TIME_ATTESTATION_V1",
}
RELEASE_SUBJECT_DOMAIN = b"ONE_INTENT_RELEASE_SUBJECT_V1"


def _infer_signature_domain(value: dict[str, Any], signature_field: str) -> str:
    if signature_field == "indexSignature":
        if "records" not in value or "releaseSubject" not in value:
            raise ValueError("evidence-index signature domain markers are missing")
        return "ONE_INTENT_OPERATIONAL_EVIDENCE_INDEX_V1"
    if signature_field != "signature":
        raise ValueError(f"unsupported signature field for domain separation: {signature_field!r}")
    # An approval legitimately contains both its own approvalId and the reviewed
    # statementId. Select by the most-specific top-level object identity while
    # rejecting incompatible mixtures.
    if "approvalId" in value:
        if "attestationId" in value:
            raise ValueError("signed document contains conflicting approval/time domain markers")
        return SIGNATURE_DOCUMENT_DOMAINS["approvalId"]
    if "attestationId" in value:
        if "statementId" in value:
            raise ValueError("signed document contains conflicting time/statement domain markers")
        return SIGNATURE_DOCUMENT_DOMAINS["attestationId"]
    if "statementId" in value:
        return SIGNATURE_DOCUMENT_DOMAINS["statementId"]
    raise ValueError("signed document has no recognized signature-domain marker")


def canonical_payload(
    value: dict[str, Any],
    signature_field: str,
    *,
    domain: str | None = None,
) -> bytes:
    """Return a domain-separated canonical signing payload.

    Removing the signature envelope avoids circularity; a fixed document-type
    prefix prevents a valid Ed25519 signature from being replayed as another
    signed protocol object with coincidentally identical JSON.
    """
    selected = domain or _infer_signature_domain(value, signature_field)
    if not isinstance(selected, str) or not re.fullmatch(r"ONE_INTENT_[A-Z0-9_]{3,96}_V\d+", selected):
        raise ValueError(f"invalid signature domain: {selected!r}")
    unsigned = copy.deepcopy(value)
    unsigned.pop(signature_field, None)
    encoded_domain = selected.encode("ascii")
    return (
        SIGNATURE_ENVELOPE_DOMAIN
        + b"\x00"
        + len(encoded_domain).to_bytes(2, "big")
        + encoded_domain
        + b"\x00"
        + canonical_json(unsigned)
    )


def subject_hash(subject: dict[str, Any]) -> str:
    return sha256_bytes(RELEASE_SUBJECT_DOMAIN + b"\x00" + canonical_json(subject))


def parse_time(value: str, label: str) -> dt.datetime:
    if not isinstance(value, str) or not CANONICAL_UTC.fullmatch(value):
        raise ValueError(f"{label} must use canonical UTC second precision (YYYY-MM-DDTHH:MM:SSZ)")
    try:
        return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError as exc:
        raise ValueError(f"{label} is not a valid UTC timestamp") from exc


def format_time(value: dt.datetime) -> str:
    value = value.astimezone(dt.timezone.utc).replace(microsecond=0)
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_schema(instance: Any, schema_rel: str, label: str) -> list[str]:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:  # pragma: no cover
        return [f"jsonschema is required to validate {label}: {exc}"]
    try:
        schema, _ = secure_load_json(ROOT / schema_rel)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        return [
            f"{label}: {error.message} at /{'/'.join(str(x) for x in error.path)}"
            for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path))
        ]
    except Exception as exc:
        return [f"cannot validate {label} against {schema_rel}: {exc}"]


def _check_secure_directory(path: Path) -> None:
    value = path.lstat()
    if stat.S_ISLNK(value.st_mode) or not stat.S_ISDIR(value.st_mode):
        raise ValueError(f"evidence path component is not a real directory: {path}")
    if os.name == "posix" and value.st_mode & 0o022:
        raise ValueError(f"group/world-writable evidence directory is prohibited: {path}")


def safe_evidence_path(rel: str) -> Path:
    prefix = "delivery/evidence/artifacts/"
    if not isinstance(rel, str) or not rel.startswith(prefix) or not rel.isascii() or len(rel) > 400:
        raise ValueError(f"operational evidence must be an ASCII path under {prefix}: {rel!r}")
    if "\\" in rel or rel.startswith("/") or any(part in {"", ".", ".."} for part in rel.split("/")):
        raise ValueError(f"unsafe operational evidence path: {rel!r}")
    evidence_root = ROOT / "delivery/evidence/artifacts"
    _check_secure_directory(evidence_root)
    relative_parts = rel[len(prefix):].split("/")
    current = evidence_root
    for part in relative_parts[:-1]:
        current = current / part
        _check_secure_directory(current)
    target = current / relative_parts[-1]
    resolved_root = evidence_root.resolve(strict=True)
    resolved = target.resolve(strict=True)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"operational evidence escaped evidence root: {rel!r}") from exc
    value = target.lstat()
    if stat.S_ISLNK(value.st_mode):
        raise ValueError(f"symlink operational evidence is prohibited: {rel!r}")
    _validate_regular_file_stat(target, value, MAX_EVIDENCE_BYTES)
    return target


def readiness_bundle_hash() -> str:
    digest = hashlib.sha256()
    digest.update(b"ONE_INTENT_READINESS_VERIFIER_BUNDLE_V1\x00")
    for rel in sorted(READINESS_BUNDLE_FILES):
        path = ROOT / rel
        snapshot = secure_file_snapshot(path, max_bytes=16 * 1024 * 1024, include_data=True)
        assert snapshot.data is not None
        rel_bytes = rel.encode("ascii")
        digest.update(len(rel_bytes).to_bytes(4, "big"))
        digest.update(rel_bytes)
        digest.update(len(snapshot.data).to_bytes(8, "big"))
        digest.update(snapshot.data)
    return digest.hexdigest()


def _load_ed25519_public_key(public_pem: str) -> tuple[Any, str]:
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        raw = public_pem.encode("ascii")
        public_key = serialization.load_pem_public_key(raw)
        if not isinstance(public_key, Ed25519PublicKey):
            raise ValueError("trusted key is not Ed25519")
        canonical = public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        if raw != canonical:
            raise ValueError("public key PEM must use the unique canonical SubjectPublicKeyInfo encoding")
        der = public_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return public_key, sha256_bytes(der)
    except Exception as exc:
        raise ValueError(f"invalid Ed25519 public key: {exc}") from exc


def _key_map(policy: dict[str, Any]) -> dict[str, TrustedKey]:
    raw_keys = policy.get("trustedKeys", [])
    if not isinstance(raw_keys, list) or len(raw_keys) > 256:
        raise ValueError("trustedKeys must be an array of at most 256 keys")
    result: dict[str, TrustedKey] = {}
    fingerprints: dict[str, str] = {}
    for raw in raw_keys:
        if not isinstance(raw, dict):
            raise ValueError("trusted key entry must be an object")
        key_id = raw.get("keyId")
        if not isinstance(key_id, str) or key_id in result:
            raise ValueError(f"duplicate or invalid trusted keyId: {key_id!r}")
        principal_id = raw.get("principalId")
        organization = raw.get("organization")
        if not isinstance(principal_id, str) or not principal_id or not isinstance(organization, str) or not organization:
            raise ValueError(f"trusted key lacks principal/organization identity: {key_id!r}")
        roles = frozenset(raw.get("roles", []))
        if not roles:
            raise ValueError(f"trusted key has no roles: {key_id!r}")
        if "TRUSTED_TIME_AUTHORITY" in roles and roles != {"TRUSTED_TIME_AUTHORITY"}:
            raise ValueError(f"trusted-time authority key must have a dedicated role: {key_id!r}")
        valid_from = parse_time(raw.get("validFrom"), f"trustedKeys[{key_id}].validFrom")
        valid_until = parse_time(raw.get("validUntil"), f"trustedKeys[{key_id}].validUntil")
        if valid_from >= valid_until:
            raise ValueError(f"trusted key has an invalid validity interval: {key_id!r}")
        public_key, fingerprint = _load_ed25519_public_key(raw.get("publicKeyPem", ""))
        prior = fingerprints.get(fingerprint)
        if prior is not None:
            raise ValueError(f"the same public key material is registered under multiple keyIds: {prior!r}, {key_id!r}")
        fingerprints[fingerprint] = key_id
        result[key_id] = TrustedKey(
            key_id=key_id,
            principal_id=principal_id,
            organization=organization,
            roles=roles,
            valid_from=valid_from,
            valid_until=valid_until,
            public_key=public_key,
            fingerprint=fingerprint,
        )
    revoked = policy.get("revokedKeyIds", [])
    if not isinstance(revoked, list) or len(revoked) != len(set(revoked)):
        raise ValueError("revokedKeyIds must be a duplicate-free array")
    return result


def verify_signature(
    document: dict[str, Any],
    *,
    signature_field: str,
    policy: dict[str, Any],
    required_roles: set[str],
    evaluated_at: dt.datetime,
    signed_at: dt.datetime | None = None,
    expected_identity_key_id: str | None = None,
    expected_principal_id: str | None = None,
    expected_organization: str | None = None,
    declared_role: str | None = None,
    key_map: dict[str, TrustedKey] | None = None,
) -> TrustedKey:
    signature = document.get(signature_field)
    if not isinstance(signature, dict):
        raise ValueError(f"missing {signature_field}")
    if signature.get("profile") != SIGNATURE_PROFILE:
        raise ValueError(f"unsupported signature profile in {signature_field}")
    key_id = signature.get("keyId")
    if expected_identity_key_id is not None and key_id != expected_identity_key_id:
        raise ValueError(f"signature key does not match declared identity: {key_id!r} != {expected_identity_key_id!r}")
    keys = key_map if key_map is not None else _key_map(policy)
    key = keys.get(key_id)
    if key is None:
        raise ValueError(f"signature key is not trusted: {key_id!r}")
    if key_id in set(policy.get("revokedKeyIds", [])):
        raise ValueError(f"signature key is revoked: {key_id!r}")
    if required_roles and not (key.roles & required_roles):
        raise ValueError(f"signature key {key_id!r} lacks required role; has={sorted(key.roles)}, required={sorted(required_roles)}")
    if declared_role is not None and (declared_role not in required_roles or declared_role not in key.roles):
        raise ValueError(f"declared role {declared_role!r} is not authorized for key {key_id!r}")
    if expected_principal_id is not None and key.principal_id != expected_principal_id:
        raise ValueError(f"signature principal does not match declared identity for {key_id!r}")
    if expected_organization is not None and key.organization != expected_organization:
        raise ValueError(f"signature organization does not match declared identity for {key_id!r}")
    if not (key.valid_from <= evaluated_at < key.valid_until):
        raise ValueError(f"signature key is outside validity interval at evaluation time: {key_id!r}")
    if signed_at is not None and not (key.valid_from <= signed_at < key.valid_until):
        raise ValueError(f"signature key was outside validity interval at signing time: {key_id!r}")
    try:
        encoded = signature["signatureBase64"]
        signature_bytes = base64.b64decode(encoded, validate=True)
        if len(signature_bytes) != 64 or base64.b64encode(signature_bytes).decode("ascii") != encoded:
            raise ValueError("signature must be a canonical 64-byte Ed25519 value")
        key.public_key.verify(signature_bytes, canonical_payload(document, signature_field))
    except Exception as exc:
        raise ValueError(f"signature verification failed for {key_id!r}: {exc}") from exc
    return key


def required_claims(config: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    gate_ids: set[str] = set()
    claim_ids: set[str] = set()
    for gate in config["gates"]:
        gate_id = gate["gateId"]
        if gate_id in gate_ids:
            raise ValueError(f"duplicate gateId: {gate_id}")
        gate_ids.add(gate_id)
        for claim in gate["claims"]:
            claim_id = claim["claimId"]
            if claim_id in claim_ids:
                raise ValueError(f"claimId must be globally unique: {claim_id}")
            claim_ids.add(claim_id)
            result[(gate_id, claim_id)] = {"gate": gate, "claim": claim}
    return result


def blocked_report(
    config: dict[str, Any],
    index: dict[str, Any],
    accepted: set[tuple[str, str]] | None = None,
    reasons: list[str] | None = None,
    generated_at: dt.datetime | None = None,
    valid_until: dt.datetime | None = None,
    decision_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = load_package_metadata()
    accepted = accepted or set()
    gate_rows: list[dict[str, Any]] = []
    required_total = 0
    accepted_total = 0
    for gate in config["gates"]:
        keys = [(gate["gateId"], claim["claimId"]) for claim in gate["claims"]]
        missing = [claim_id for gate_id, claim_id in keys if (gate_id, claim_id) not in accepted]
        count = len(keys)
        passed = count - len(missing)
        required_total += count
        accepted_total += passed
        gate_rows.append({
            "gateId": gate["gateId"],
            "titleJa": gate["titleJa"],
            "status": "PASS" if not missing else "BLOCKED",
            "requiredClaims": count,
            "acceptedClaims": passed,
            "blockingClaims": missing,
        })
    passed_gates = sum(row["status"] == "PASS" for row in gate_rows)
    is_release_go = passed_gates == len(gate_rows) and not reasons
    status = "PRODUCTION_OPERATIONAL_GO" if is_release_go else "BLOCKED_NOT_OPERATIONAL"
    if generated_at is None:
        generated_text = metadata.deterministic_build_timestamp
        generated_value = parse_time(generated_text, "deterministic build timestamp")
    else:
        generated_value = generated_at
        generated_text = format_time(generated_at)
    valid_text = format_time(valid_until if valid_until is not None else generated_value)
    inputs = decision_inputs or {
        "operationalTrustPolicySha256": None,
        "readinessVerifierBundleSha256": None,
        "releaseSubjectSha256": None,
        "evidenceIndexSha256": None,
        "evidenceIndexSequence": int(index.get("sequence", 0)) if isinstance(index.get("sequence", 0), int) else 0,
        "trustedTimeAttestationSha256": None,
        "trustedTimeSequence": 0,
    }
    default_reason = "No signed production operational evidence is included in this design package."
    return {
        "schemaVersion": "1.0",
        "profileId": config["profileId"],
        "evaluatedArtifactVersion": metadata.version,
        "generatedAt": generated_text,
        "validUntil": valid_text,
        "decisionInputs": inputs,
        "status": status,
        "releaseEligibleForRuntimeActivation": is_release_go,
        # This evaluator is intentionally unable to authorize a transaction.
        "productionWritePermitted": False,
        "releaseSubject": index["releaseSubject"],
        "summary": {
            "mandatoryGates": len(gate_rows),
            "passedGates": passed_gates,
            "blockedGates": len(gate_rows) - passed_gates,
            "requiredClaims": required_total,
            "acceptedClaims": accepted_total,
            "missingOrRejectedClaims": required_total - accepted_total,
        },
        "gates": gate_rows,
        "blockingReasons": [] if is_release_go else sorted(set(reasons or [default_reason])),
        "disclaimer": "This result is a finite, exact-release gate evaluation. It never proves the absence of unknown vulnerabilities, market loss, external-service change, or future legal/policy change. It never grants a transaction. Runtime writes still require a fresh signed runtime state, a short-lived capability lease, exact single-use user/device authorization, signer-side revalidation, and an unused nonce.",
    }


def evaluate_design_package() -> Evaluation:
    errors: list[str] = []
    config, _ = secure_load_json(CONFIG_PATH)
    policy, policy_snapshot = secure_load_json(TEMPLATE_TRUST_PATH)
    index, index_snapshot = secure_load_json(INDEX_PATH)
    errors.extend(validate_schema(config, "schemas/operational-readiness-config.schema.json", "operational-readiness config"))
    errors.extend(validate_schema(policy, "schemas/operational-trust-policy.schema.json", "operational trust-policy template"))
    errors.extend(validate_schema(index, "schemas/operational-evidence-index.schema.json", "operational evidence index"))
    try:
        claims = required_claims(config)
        if len(config["gates"]) != 37 or len(claims) != 93:
            errors.append(f"operational profile count drift: {len(config['gates'])} gates, {len(claims)} claims")
    except Exception as exc:
        errors.append(str(exc))
    if policy.get("enabled") is not False or policy.get("trustedKeys") or policy.get("revokedKeyIds"):
        errors.append("design-package trust policy must be disabled and contain no trusted/revoked keys")
    if policy.get("canonicalization") != CANONICALIZATION_PROFILE:
        errors.append("design-package canonicalization profile drift")
    if index.get("records") or index.get("indexSignature") is not None or index.get("trustedTimeAttestationPath") is not None:
        errors.append("design-package evidence index must contain no production evidence or signatures")
    if index.get("sequence") != 0 or index.get("issuedAt") != index.get("expiresAt"):
        errors.append("design-package evidence index must be a deliberately non-current sequence-zero example")
    if index.get("releaseSubject", {}).get("environment") != "DESIGN_ONLY":
        errors.append("design-package release subject must remain DESIGN_ONLY")
    if any(index.get("releaseSubject", {}).get(field) is not None for field in config.get("releaseSubjectRequiredFields", [])):
        errors.append("design-package release subject must not fabricate native/server artifact digests")
    metadata = load_package_metadata()
    deterministic_time = parse_time(metadata.deterministic_build_timestamp, "deterministic build timestamp")
    decision_inputs = {
        "operationalTrustPolicySha256": policy_snapshot.digest,
        "readinessVerifierBundleSha256": readiness_bundle_hash(),
        "releaseSubjectSha256": subject_hash(index["releaseSubject"]),
        "evidenceIndexSha256": index_snapshot.digest,
        "evidenceIndexSequence": int(index.get("sequence", 0)),
        "trustedTimeAttestationSha256": None,
        "trustedTimeSequence": 0,
    }
    report = blocked_report(
        config,
        index,
        reasons=errors or None,
        generated_at=deterministic_time,
        valid_until=deterministic_time,
        decision_inputs=decision_inputs,
    )
    if (
        report["status"] != "BLOCKED_NOT_OPERATIONAL"
        or report["releaseEligibleForRuntimeActivation"] is not False
        or report["productionWritePermitted"] is not False
    ):
        errors.append("current design package must remain blocked and transaction-incapable")
    errors.extend(validate_schema(report, "schemas/operational-readiness-report.schema.json", "design operational-readiness report"))
    return Evaluation(report=report, errors=tuple(errors))


def _check_anchor(env_name: str, actual: str, errors: list[str]) -> None:
    expected = os.environ.get(env_name)
    if expected is None:
        errors.append(f"missing protected out-of-band anchor: {env_name}")
    elif not HEX64.fullmatch(expected):
        errors.append(f"invalid protected out-of-band anchor format: {env_name}")
    elif expected != actual:
        errors.append(f"protected out-of-band anchor mismatch: {env_name}")


def _fallback_index() -> dict[str, Any]:
    try:
        return strict_load_json(INDEX_PATH)
    except Exception:
        return {
            "releaseSubject": {
                "releaseId": "invalid-evidence-index",
                "environment": "DESIGN_ONLY",
                "sourceCommit": None,
                "sourceTreeSha256": None,
                "androidArtifactSha256": None,
                "iosArtifactSha256": None,
                "backendImageDigest": None,
                "signerImageDigest": None,
                "configurationBundleSha256": None,
                "policyBundleSha256": None,
                "assetRegistrySha256": None,
                "sbomSha256": None,
            }
        }


def evaluate_production(
    trust_policy_path: Path,
    evidence_index_path: Path,
    *,
    minimum_trusted_time_sequence: int = 0,
    minimum_evidence_index_sequence: int = 0,
) -> Evaluation:
    errors: list[str] = []
    for label, value in (
        ("minimum_trusted_time_sequence", minimum_trusted_time_sequence),
        ("minimum_evidence_index_sequence", minimum_evidence_index_sequence),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"{label} must be a non-negative integer")
    accepted: set[tuple[str, str]] = set()
    try:
        config, _ = secure_load_json(CONFIG_PATH)
    except Exception as exc:  # local checker corruption must still produce a block
        config = strict_load_json(CONFIG_PATH)
        errors.append(f"readiness config rejected: {exc}")
    try:
        policy, policy_snapshot = secure_load_json(trust_policy_path)
    except Exception as exc:
        policy = strict_load_json(TEMPLATE_TRUST_PATH)
        policy_snapshot = secure_file_snapshot(TEMPLATE_TRUST_PATH)
        errors.append(f"production trust policy rejected: {exc}")
    index_snapshot: FileSnapshot | None = None
    try:
        index, index_snapshot = secure_load_json(evidence_index_path)
    except Exception as exc:
        index = _fallback_index()
        errors.append(f"production evidence index rejected: {exc}")

    errors.extend(validate_schema(config, "schemas/operational-readiness-config.schema.json", "operational-readiness config"))
    errors.extend(validate_schema(policy, "schemas/operational-trust-policy.schema.json", "production trust policy"))
    errors.extend(validate_schema(index, "schemas/operational-evidence-index.schema.json", "production evidence index"))
    try:
        claim_map = required_claims(config)
        if len(config["gates"]) != 37 or len(claim_map) != 93:
            errors.append(f"protected readiness profile count drift: {len(config['gates'])} gates, {len(claim_map)} claims")
    except Exception as exc:
        claim_map = {}
        errors.append(str(exc))
    try:
        key_map = _key_map(policy)
    except Exception as exc:
        key_map = {}
        errors.append(f"trusted-key policy rejected: {exc}")

    if policy.get("profileId") != config.get("profileId") or index.get("profileId") != config.get("profileId"):
        errors.append("profileId mismatch between config, trust policy, and evidence index")
    if policy.get("enabled") is not True:
        errors.append("production trust policy is not enabled")
    if policy.get("policyVersion") in {None, "TEMPLATE-NOT-ACTIVE"}:
        errors.append("production trust policy still uses a template/undefined policyVersion")
    if policy.get("canonicalization") != CANONICALIZATION_PROFILE:
        errors.append("production trust policy canonicalization profile mismatch")

    subject = index.get("releaseSubject", _fallback_index()["releaseSubject"])
    if not isinstance(subject, dict) or subject.get("environment") != "PRODUCTION":
        errors.append("release subject environment must be PRODUCTION")
        subject = subject if isinstance(subject, dict) else _fallback_index()["releaseSubject"]
    for field in config.get("releaseSubjectRequiredFields", []):
        if not subject.get(field):
            errors.append(f"release subject field is missing: {field}")

    _check_anchor("ONE_INTENT_TRUST_POLICY_SHA256", policy_snapshot.digest, errors)
    try:
        checker_hash = readiness_bundle_hash()
    except Exception as exc:
        checker_hash = "0" * 64
        errors.append(f"readiness verifier bundle could not be hashed: {exc}")
    _check_anchor("ONE_INTENT_READINESS_CHECKER_SHA256", checker_hash, errors)
    try:
        release_subject_hash = subject_hash(subject)
    except Exception as exc:
        release_subject_hash = "0" * 64
        errors.append(f"release subject canonicalization failed: {exc}")
    _check_anchor("ONE_INTENT_RELEASE_SUBJECT_SHA256", release_subject_hash, errors)
    evidence_index_hash = index_snapshot.digest if index_snapshot is not None else "0" * 64
    _check_anchor("ONE_INTENT_EVIDENCE_INDEX_SHA256", evidence_index_hash, errors)

    evaluated_at: dt.datetime | None = None
    time_valid_until: dt.datetime | None = None
    time_attestation_hash: str | None = None
    time_doc: dict[str, Any] = {}
    time_signer: TrustedKey | None = None
    decision_expiries: list[dt.datetime] = []
    time_path_value = index.get("trustedTimeAttestationPath")
    if not time_path_value:
        errors.append("trusted time attestation is missing")
    else:
        try:
            time_path = safe_evidence_path(time_path_value)
            time_doc, time_snapshot = secure_load_json(time_path, max_bytes=MAX_TIME_JSON_BYTES)
            time_attestation_hash = time_snapshot.digest
            _check_anchor("ONE_INTENT_TRUSTED_TIME_ATTESTATION_SHA256", time_snapshot.digest, errors)
            errors.extend(validate_schema(time_doc, "schemas/trusted-time-attestation.schema.json", "trusted time attestation"))
            if time_doc.get("profileId") != config.get("profileId"):
                errors.append("trusted time profileId mismatch")
            time_sequence = time_doc.get("sequence")
            if not isinstance(time_sequence, int) or isinstance(time_sequence, bool) or time_sequence < 1:
                errors.append("production trusted time sequence must be positive")
                time_sequence = 0
            if time_sequence <= minimum_trusted_time_sequence:
                errors.append("trusted time sequence is not above the protected high-water mark")
            evaluated_at = parse_time(time_doc["observedAt"], "trusted time observedAt")
            valid_until = parse_time(time_doc["validUntil"], "trusted time validUntil")
            time_valid_until = valid_until
            max_time = int(config["globalRules"]["maxTrustedTimeAttestationSeconds"])
            if time_doc.get("trusted") is not True or not (evaluated_at < valid_until):
                errors.append("trusted time attestation is untrusted or has an invalid interval")
            if valid_until - evaluated_at > dt.timedelta(seconds=max_time):
                errors.append("trusted time attestation exceeds the configured maximum lifetime")
            now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
            if not (evaluated_at - dt.timedelta(seconds=60) <= now < valid_until):
                errors.append("trusted time attestation is not fresh for the verifier clock")
            authority = time_doc.get("authority", {})
            time_signer = verify_signature(
                time_doc,
                signature_field="signature",
                policy=policy,
                required_roles={"TRUSTED_TIME_AUTHORITY"},
                evaluated_at=evaluated_at,
                signed_at=evaluated_at,
                expected_identity_key_id=authority.get("keyId"),
                expected_principal_id=authority.get("principalId"),
                expected_organization=authority.get("organization"),
                declared_role=authority.get("role"),
                key_map=key_map,
            )
            decision_expiries.extend([valid_until, time_signer.valid_until])
        except Exception as exc:
            errors.append(f"trusted time attestation rejected: {exc}")
    if evaluated_at is None:
        evaluated_at = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)

    index_issued = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
    index_expires = index_issued
    try:
        index_sequence = index.get("sequence")
        if not isinstance(index_sequence, int) or isinstance(index_sequence, bool) or index_sequence < 1:
            errors.append("production evidence index sequence must be positive")
            index_sequence = 0
        if index_sequence <= minimum_evidence_index_sequence:
            errors.append("evidence index sequence is not above the protected high-water mark")
        index_issued = parse_time(index["issuedAt"], "evidence index issuedAt")
        index_expires = parse_time(index["expiresAt"], "evidence index expiresAt")
        if not (index_issued < index_expires):
            errors.append("evidence index has an invalid validity interval")
        max_index = int(config["globalRules"]["maxEvidenceIndexAgeSeconds"])
        if index_expires - index_issued > dt.timedelta(seconds=max_index):
            errors.append("evidence index exceeds the configured maximum lifetime")
        if not (index_issued <= evaluated_at < index_expires):
            errors.append("evidence index is not current at trusted evaluation time")
        decision_expiries.append(index_expires)
        declaration = str(index.get("currentPackageDeclaration", "")).lower()
        if "design package" in declaration or "blocked_not_operational" in declaration:
            errors.append("production evidence index still contains the design-package declaration")
    except Exception as exc:
        errors.append(f"evidence index validity rejected: {exc}")

    index_signer: TrustedKey | None = None
    try:
        index_signer = verify_signature(
            index,
            signature_field="indexSignature",
            policy=policy,
            required_roles={"RELEASE_EVIDENCE_CUSTODIAN"},
            evaluated_at=evaluated_at,
            signed_at=index_issued,
            key_map=key_map,
        )
        decision_expiries.append(index_signer.valid_until)
    except Exception as exc:
        errors.append(f"evidence index signature rejected: {exc}")

    records: dict[tuple[str, str], dict[str, Any]] = {}
    statement_paths: set[str] = set()
    approval_paths: set[str] = set()
    statement_ids: set[str] = set()
    approval_ids: set[str] = set()
    for record in index.get("records", []) if isinstance(index.get("records"), list) else []:
        key = (record.get("gateId"), record.get("claimId"))
        if key in records:
            errors.append(f"duplicate evidence record for {key}")
        records[key] = record
    unknown = sorted(set(records) - set(claim_map))
    if unknown:
        errors.append(f"evidence index contains unknown claims: {unknown}")

    all_evidence_keys: set[str] = set()
    all_evidence_principals: set[str] = set()
    for key, definition in claim_map.items():
        claim = definition["claim"]
        record = records.get(key)
        if record is None:
            errors.append(f"missing evidence record: {key[0]}/{key[1]}")
            continue
        local_errors: list[str] = []
        try:
            statement_rel = record["statementPath"]
            if statement_rel in statement_paths:
                local_errors.append(f"statement path is reused by another claim: {statement_rel}")
            statement_paths.add(statement_rel)
            statement_path = safe_evidence_path(statement_rel)
            statement, statement_snapshot = secure_load_json(statement_path, max_bytes=MAX_SIGNED_JSON_BYTES)
            if statement_snapshot.digest != record["statementSha256"]:
                raise ValueError("statement digest mismatch")
            local_errors.extend(validate_schema(statement, "schemas/operational-evidence-statement.schema.json", f"statement {key[1]}"))
            statement_id = statement.get("statementId")
            if statement_id in statement_ids:
                local_errors.append(f"statementId is reused: {statement_id!r}")
            statement_ids.add(statement_id)
            if statement.get("profileId") != config["profileId"] or statement.get("gateId") != key[0] or statement.get("claimId") != key[1]:
                local_errors.append("statement identity does not match index/config")
            if statement.get("subject") != subject:
                local_errors.append("statement release subject mismatch")
            if statement.get("environment") != "PRODUCTION" or statement.get("outcome") != "PASS":
                local_errors.append("statement must be a PRODUCTION PASS")
            if statement.get("limitations"):
                local_errors.append("a production PASS statement must have no unresolved limitations")
            issued = parse_time(statement["issuedAt"], "statement issuedAt")
            expires = parse_time(statement["expiresAt"], "statement expiresAt")
            if not (issued < expires):
                local_errors.append("statement has an invalid validity interval")
            if not (issued <= index_issued <= evaluated_at < expires):
                local_errors.append("statement/index/evaluation chronology is invalid")
            max_age = dt.timedelta(days=int(claim["maxAgeDays"]))
            if evaluated_at - issued > max_age:
                local_errors.append("statement exceeds claim maxAgeDays")
            issuer = statement.get("issuer", {})
            if issuer.get("role") not in set(claim["issuerRoles"]):
                local_errors.append("statement declares an unauthorized issuer role")
            issuer_identity = verify_signature(
                statement,
                signature_field="signature",
                policy=policy,
                required_roles=set(claim["issuerRoles"]),
                evaluated_at=evaluated_at,
                signed_at=issued,
                expected_identity_key_id=issuer.get("keyId"),
                expected_principal_id=issuer.get("principalId"),
                expected_organization=issuer.get("organization"),
                declared_role=issuer.get("role"),
                key_map=key_map,
            )
            all_evidence_keys.add(issuer_identity.key_id)
            all_evidence_principals.add(issuer_identity.principal_id)
            decision_expiries.extend([expires, issuer_identity.valid_until])

            provided_types: set[str] = set()
            local_artifact_paths: set[str] = set()
            for artifact in statement.get("evidence", []):
                artifact_rel = artifact["path"]
                if artifact_rel in local_artifact_paths:
                    local_errors.append(f"duplicate evidence artifact path: {artifact_rel}")
                    continue
                local_artifact_paths.add(artifact_rel)
                artifact_path = safe_evidence_path(artifact_rel)
                artifact_snapshot = secure_file_snapshot(artifact_path, max_bytes=MAX_EVIDENCE_BYTES)
                if artifact_snapshot.digest != artifact["sha256"]:
                    local_errors.append(f"evidence artifact digest mismatch: {artifact_rel}")
                if artifact_snapshot.size != artifact["sizeBytes"]:
                    local_errors.append(f"evidence artifact size mismatch: {artifact_rel}")
                if not MIME.fullmatch(artifact.get("mediaType", "")):
                    local_errors.append(f"evidence artifact has a non-canonical media type: {artifact_rel}")
                collected = parse_time(artifact["collectedAt"], "artifact collectedAt")
                if not (evaluated_at - max_age <= collected <= issued):
                    local_errors.append(f"evidence artifact time is outside the claim/statement interval: {artifact_rel}")
                provided_types.add(artifact["type"])
            missing_types = set(claim["evidenceTypes"]) - provided_types
            if missing_types:
                local_errors.append(f"required evidence types missing: {sorted(missing_types)}")

            reviewer_keys: set[str] = set()
            reviewer_principals: set[str] = set()
            reviewer_roles: set[str] = set()
            valid_approvals = 0
            for approval_ref in record.get("approvalArtifacts", []):
                approval_rel = approval_ref["path"]
                if approval_rel in approval_paths:
                    local_errors.append(f"approval artifact path is reused: {approval_rel}")
                    continue
                approval_paths.add(approval_rel)
                approval_path = safe_evidence_path(approval_rel)
                approval, approval_snapshot = secure_load_json(approval_path, max_bytes=MAX_SIGNED_JSON_BYTES)
                if approval_snapshot.digest != approval_ref["sha256"]:
                    local_errors.append(f"approval digest mismatch: {approval_rel}")
                    continue
                local_errors.extend(validate_schema(approval, "schemas/operational-review-approval.schema.json", f"approval {approval_rel}"))
                approval_id = approval.get("approvalId")
                if approval_id in approval_ids:
                    local_errors.append(f"approvalId is reused: {approval_id!r}")
                    continue
                approval_ids.add(approval_id)
                if (
                    approval.get("statementId") != statement_id
                    or approval.get("statementSha256") != statement_snapshot.digest
                    or approval.get("subject") != subject
                    or approval.get("profileId") != config["profileId"]
                ):
                    local_errors.append(f"approval is not bound to the exact statement/release: {approval_rel}")
                    continue
                if approval.get("decision") != "APPROVE":
                    local_errors.append(f"approval decision is not APPROVE: {approval_rel}")
                    continue
                reviewed = parse_time(approval["reviewedAt"], "approval reviewedAt")
                if not (issued <= reviewed <= index_issued <= evaluated_at and reviewed < expires):
                    local_errors.append(f"approval chronology is invalid: {approval_rel}")
                    continue
                reviewer = approval.get("reviewer", {})
                if reviewer.get("role") not in set(claim["reviewerRoles"]):
                    local_errors.append(f"approval declares an unauthorized reviewer role: {approval_rel}")
                    continue
                reviewer_identity = verify_signature(
                    approval,
                    signature_field="signature",
                    policy=policy,
                    required_roles=set(claim["reviewerRoles"]),
                    evaluated_at=evaluated_at,
                    signed_at=reviewed,
                    expected_identity_key_id=reviewer.get("keyId"),
                    expected_principal_id=reviewer.get("principalId"),
                    expected_organization=reviewer.get("organization"),
                    declared_role=reviewer.get("role"),
                    key_map=key_map,
                )
                if reviewer_identity.key_id == issuer_identity.key_id or reviewer_identity.principal_id == issuer_identity.principal_id:
                    local_errors.append("issuer and reviewer must be different keys and principals")
                    continue
                if reviewer_identity.key_id in reviewer_keys or reviewer_identity.principal_id in reviewer_principals:
                    local_errors.append("one reviewer key/principal cannot fill multiple approval slots")
                    continue
                reviewer_keys.add(reviewer_identity.key_id)
                reviewer_principals.add(reviewer_identity.principal_id)
                reviewer_roles.add(str(reviewer.get("role")))
                all_evidence_keys.add(reviewer_identity.key_id)
                all_evidence_principals.add(reviewer_identity.principal_id)
                decision_expiries.append(reviewer_identity.valid_until)
                valid_approvals += 1
            threshold = int(claim["approvalThreshold"])
            if valid_approvals < threshold:
                local_errors.append(f"approval threshold not met: {valid_approvals} < {threshold}")
            required_role_coverage = min(threshold, len(set(claim["reviewerRoles"])))
            if len(reviewer_roles) < required_role_coverage:
                local_errors.append(
                    f"distinct reviewer-role coverage not met: {len(reviewer_roles)} < {required_role_coverage}"
                )
        except Exception as exc:
            local_errors.append(str(exc))
        if local_errors:
            errors.extend(f"{key[0]}/{key[1]}: {message}" for message in local_errors)
        else:
            accepted.add(key)

    if index_signer is not None:
        if index_signer.key_id in all_evidence_keys or index_signer.principal_id in all_evidence_principals:
            errors.append("evidence-index signer must be independent from all claim issuers/reviewers")
        if time_signer is not None and (
            index_signer.key_id == time_signer.key_id or index_signer.principal_id == time_signer.principal_id
        ):
            errors.append("evidence-index signer and trusted-time signer must be independent")
    if time_signer is not None and (
        time_signer.key_id in all_evidence_keys or time_signer.principal_id in all_evidence_principals
    ):
        errors.append("trusted-time signer must be independent from all claim issuers/reviewers")
    if set(records) != set(claim_map):
        errors.append("evidence index does not contain exactly one record for every required claim")

    report_valid_until = min(decision_expiries) if decision_expiries else evaluated_at
    if report_valid_until <= evaluated_at:
        errors.append("operational-readiness decision has no positive validity window")
    sequence_value = index.get("sequence", 0)
    if not isinstance(sequence_value, int) or isinstance(sequence_value, bool) or sequence_value < 0:
        sequence_value = 0
    decision_inputs = {
        "operationalTrustPolicySha256": policy_snapshot.digest,
        "readinessVerifierBundleSha256": checker_hash if HEX64.fullmatch(checker_hash) else None,
        "releaseSubjectSha256": release_subject_hash if HEX64.fullmatch(release_subject_hash) else None,
        "evidenceIndexSha256": evidence_index_hash if HEX64.fullmatch(evidence_index_hash) else None,
        "evidenceIndexSequence": sequence_value,
        "trustedTimeAttestationSha256": time_attestation_hash,
        "trustedTimeSequence": time_doc.get("sequence", 0) if isinstance(time_doc, dict) and isinstance(time_doc.get("sequence"), int) and not isinstance(time_doc.get("sequence"), bool) else 0,
    }
    expected_go = len(accepted) == len(claim_map) and not errors
    report = blocked_report(
        config,
        index,
        accepted=accepted,
        reasons=[] if expected_go else errors,
        generated_at=evaluated_at,
        valid_until=report_valid_until,
        decision_inputs=decision_inputs,
    )
    report_errors = validate_schema(report, "schemas/operational-readiness-report.schema.json", "production operational-readiness report")
    if report_errors:
        errors.extend(report_errors)
        expected_go = False
        report = blocked_report(
            config,
            index,
            accepted=accepted,
            reasons=errors,
            generated_at=evaluated_at,
            valid_until=report_valid_until,
            decision_inputs=decision_inputs,
        )
    if expected_go:
        report["status"] = "PRODUCTION_OPERATIONAL_GO"
        report["releaseEligibleForRuntimeActivation"] = True
        report["productionWritePermitted"] = False
        report["blockingReasons"] = []
    else:
        report["status"] = "BLOCKED_NOT_OPERATIONAL"
        report["releaseEligibleForRuntimeActivation"] = False
        report["productionWritePermitted"] = False
    return Evaluation(report=report, errors=tuple(errors))
