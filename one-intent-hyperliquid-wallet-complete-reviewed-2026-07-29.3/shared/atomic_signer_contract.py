"""Fail-closed validation for the V2 atomic-signer request contract.

This module verifies signed envelope structure and cross-object bindings.  It
does not sign, broadcast, load keys, or turn an eligible request into a
production authorization.  Verification uses a deployment-owned immutable
public-key trust store; callbacks and precomputed trust booleans are rejected.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from .canonical import canonical_bytes, canonical_hash, ensure_nfc, strict_loads
from .signature_trust_store import SignatureTrustStore


_TRUST_BOOLEAN_KEYS = frozenset(
    {
        "allowed",
        "release_go",
        "runtime_lease_valid",
        "server_verified",
        "signature_valid",
        "trust_valid",
        "verified",
    }
)
_SIGNED_FIELDS = frozenset({"canonicalDigest", "signature"})


class AtomicSignerContractError(ValueError):
    """The request cannot cross the protected signer boundary."""


@dataclass(frozen=True)
class VerifiedAtomicSignerRequest:
    request_id: str
    authorization_id: str
    nonce: str
    operation_spec_digest: str
    review_receipt_digest: str
    runtime_decision_digest: str
    canonical_digest: str
    request: Mapping[str, Any]


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AtomicSignerContractError(f"{label} must be an object")
    ensure_nfc(value)
    return value


def _integer(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise AtomicSignerContractError(f"{label} must be a non-negative integer")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise AtomicSignerContractError(f"{label} must be non-empty text")
    ensure_nfc(value)
    return value


def _reject_trust_booleans(value: Any, path: str = "request") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise AtomicSignerContractError(f"{path} contains a non-text key")
            if key.lower() in _TRUST_BOOLEAN_KEYS:
                raise AtomicSignerContractError(f"caller-supplied trust field is prohibited: {path}.{key}")
            _reject_trust_booleans(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_trust_booleans(child, f"{path}[{index}]")


def _signed_material(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in envelope.items() if key not in _SIGNED_FIELDS}


def _verify_envelope_signature(
    envelope: Mapping[str, Any],
    *,
    domain: str,
    trust_store: SignatureTrustStore,
) -> str:
    material = _signed_material(envelope)
    expected = canonical_hash(domain, material)
    if envelope.get("canonicalDigest") != expected:
        raise AtomicSignerContractError(f"{domain} canonical digest mismatch")
    issuer = _text(envelope.get("issuer"), f"{domain} issuer")
    key_id = _text(envelope.get("keyId"), f"{domain} key ID")
    algorithm = _text(envelope.get("signatureAlgorithm"), f"{domain} signature algorithm")
    signature = _text(envelope.get("signature"), f"{domain} signature")
    revocation_epoch = _integer(envelope.get("revocationEpoch"), f"{domain} revocation epoch")
    try:
        verified = trust_store.verify(
            issuer,
            key_id,
            algorithm,
            domain.encode("utf-8") + b"\x00" + canonical_bytes(material),
            signature,
            revocation_epoch,
        )
    except Exception as exc:
        raise AtomicSignerContractError(f"{domain} signature verifier failed closed") from exc
    if verified is not True:
        raise AtomicSignerContractError(f"{domain} signature is not valid")
    return expected


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(child) for child in value)
    if isinstance(value, tuple):
        return tuple(_freeze(child) for child in value)
    return value


def validate_atomic_signer_request(
    request: Mapping[str, Any],
    *,
    now: int,
    trust_store: SignatureTrustStore,
) -> VerifiedAtomicSignerRequest:
    """Validate all embedded digests, signatures, time bounds, and identities."""

    request = _mapping(request, "atomic signer request")
    _reject_trust_booleans(request)
    now = _integer(now, "current time")
    operation = _mapping(request.get("operationSpec"), "operation spec")
    review = _mapping(request.get("reviewReceipt"), "review receipt")
    decision = _mapping(request.get("runtimeDecision"), "runtime decision")

    operation_digest = canonical_hash("operation-spec-v2", operation)
    review_digest = canonical_hash("user-review-receipt-v2", review)
    decision_digest = canonical_hash("runtime-decision-envelope-v2", decision)
    if request.get("operationSpecDigest") != operation_digest:
        raise AtomicSignerContractError("operation spec digest mismatch")
    if request.get("reviewReceiptDigest") != review_digest:
        raise AtomicSignerContractError("review receipt digest mismatch")
    if request.get("runtimeDecisionDigest") != decision_digest:
        raise AtomicSignerContractError("runtime decision digest mismatch")
    if review.get("operationSpecDigest") != operation_digest:
        raise AtomicSignerContractError("review receipt is not bound to the operation")
    if decision.get("operationSpecDigest") != operation_digest:
        raise AtomicSignerContractError("runtime decision is not bound to the operation")
    if decision.get("reviewReceiptDigest") != review_digest:
        raise AtomicSignerContractError("runtime decision is not bound to the review receipt")
    operation_account = operation.get("account")
    if not isinstance(operation_account, str) or not operation_account:
        raise AtomicSignerContractError("operation account is missing")
    if request.get("subject") != operation_account:
        raise AtomicSignerContractError("request subject is not the operation account")
    if review.get("subject") != operation_account:
        raise AtomicSignerContractError("review subject is not the operation account")
    if decision.get("subject") != operation_account:
        raise AtomicSignerContractError("runtime decision subject is not the operation account")

    bindings = {
        "displayDigest": "displayManifestDigest",
        "quoteDigest": "quoteDigest",
        "sourceStateDigest": "sourceStateDigest",
        "finalPayloadDigest": "payloadCommitment",
    }
    for review_field, operation_field in bindings.items():
        if review.get(review_field) != operation.get(operation_field):
            raise AtomicSignerContractError(
                f"review {review_field} is not bound to operation {operation_field}"
            )

    environment = request.get("environment")
    deployment = request.get("deployment")
    audience = request.get("audience")
    for label, envelope in (("review", review), ("decision", decision)):
        if envelope.get("environment") != environment:
            raise AtomicSignerContractError(f"{label} environment mismatch")
        if envelope.get("deployment") != deployment:
            raise AtomicSignerContractError(f"{label} deployment mismatch")
        if envelope.get("audience") != audience:
            raise AtomicSignerContractError(f"{label} audience mismatch")

    requested_at = _integer(request.get("requestedAt"), "requestedAt")
    not_before = _integer(request.get("notBefore"), "request notBefore")
    expires_at = _integer(request.get("expiresAt"), "request expiresAt")
    operation_expires_at = _integer(operation.get("expiresAt"), "operation expiresAt")
    review_time = _integer(review.get("reviewedAt"), "reviewedAt")
    review_not_before = _integer(review.get("notBefore"), "review notBefore")
    review_expires_at = _integer(review.get("expiresAt"), "review expiresAt")
    issued_at = _integer(decision.get("issuedAt"), "decision issuedAt")
    decision_not_before = _integer(decision.get("notBefore"), "decision notBefore")
    evaluated_at = _integer(decision.get("evaluatedAt"), "decision evaluatedAt")
    decision_expires_at = _integer(decision.get("expiresAt"), "decision expiresAt")
    if not (not_before <= requested_at <= now < expires_at):
        raise AtomicSignerContractError("atomic signer request is future-dated or expired")
    if not (review_not_before <= review_time <= now < review_expires_at):
        raise AtomicSignerContractError("review receipt is future-dated or expired")
    if not (issued_at <= decision_not_before <= evaluated_at <= now < decision_expires_at):
        raise AtomicSignerContractError("runtime decision time ordering is invalid")
    if min(operation_expires_at, review_expires_at, decision_expires_at) < expires_at:
        raise AtomicSignerContractError("request outlives an embedded authorization object")

    status = decision.get("status")
    reasons = decision.get("blockingReasons")
    if not isinstance(reasons, list):
        raise AtomicSignerContractError("runtime blocking reasons must be an array")
    if status == "ELIGIBLE_FOR_ATOMIC_SIGNER_FINALIZATION" and reasons:
        raise AtomicSignerContractError("eligible decision cannot contain blocking reasons")
    if status == "BLOCKED" and not reasons:
        raise AtomicSignerContractError("blocked decision must contain a blocking reason")
    if status != "ELIGIBLE_FOR_ATOMIC_SIGNER_FINALIZATION":
        raise AtomicSignerContractError("runtime decision is not eligible for finalization")

    if not isinstance(trust_store, SignatureTrustStore):
        raise AtomicSignerContractError("a protected signature trust store is required")
    _verify_envelope_signature(review, domain="user-review-receipt-v2", trust_store=trust_store)
    _verify_envelope_signature(decision, domain="runtime-decision-envelope-v2", trust_store=trust_store)
    request_digest = _verify_envelope_signature(
        request,
        domain="atomic-signer-request-v2",
        trust_store=trust_store,
    )

    return VerifiedAtomicSignerRequest(
        request_id=_text(request.get("requestId"), "request ID"),
        authorization_id=_text(request.get("authorizationId"), "authorization ID"),
        nonce=_text(request.get("nonce"), "nonce"),
        operation_spec_digest=operation_digest,
        review_receipt_digest=review_digest,
        runtime_decision_digest=decision_digest,
        canonical_digest=request_digest,
        request=_freeze(request),
    )


def parse_and_validate_atomic_signer_request(
    raw_request: str,
    *,
    now: int,
    trust_store: SignatureTrustStore,
) -> VerifiedAtomicSignerRequest:
    """Strict-JSON boundary that rejects duplicate keys before verification."""

    try:
        parsed = strict_loads(raw_request)
    except (TypeError, ValueError) as exc:
        raise AtomicSignerContractError("atomic signer request is not strict canonical JSON") from exc
    if not isinstance(parsed, Mapping):
        raise AtomicSignerContractError("atomic signer request must be an object")
    return validate_atomic_signer_request(parsed, now=now, trust_store=trust_store)
