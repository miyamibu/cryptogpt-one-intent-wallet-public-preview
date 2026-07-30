"""Fail-closed contract for a signed iOS App Attest verifier receipt.

The package still does not contain Apple's production trust roots or a live
App Attest service.  It no longer accepts a caller-supplied ``serverVerified``
boolean: a protected verifier must sign the exact receipt and an injected
trust-root verifier must validate that signature.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from shared.canonical import CanonicalizationError, canonical_bytes, canonical_hash, ensure_nfc
from shared.domain import DomainError
from shared.signature_trust_store import SignatureTrustStore


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_KEY_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_ENVIRONMENTS = {"development", "production"}
_MAX_COUNTER = 2**63 - 1
class AppAttestVerificationError(DomainError):
    """The evidence cannot be accepted as a signed App Attest verifier receipt."""


def _text(value: object, label: str, *, maximum: int = 256) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise AppAttestVerificationError(f"{label} is missing or oversized")
    try:
        ensure_nfc(value)
    except CanonicalizationError as exc:
        raise AppAttestVerificationError(f"{label} is not canonical text") from exc
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise AppAttestVerificationError(f"{label} contains a control character")
    return value


def _hash(value: object, label: str) -> str:
    value = _text(value, label, maximum=64)
    if not _SHA256_RE.fullmatch(value):
        raise AppAttestVerificationError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _non_negative_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > _MAX_COUNTER:
        raise AppAttestVerificationError(f"{label} must be a non-negative signed 64-bit integer")
    return value


@dataclass(frozen=True)
class AppAttestEvidence:
    verifier_id: str
    key_id: str
    bundle_id: str
    team_id: str
    environment: str
    challenge_sha256: str
    capsule_sha256: str
    assertion_sha256: str
    attestation_chain_sha256: str
    counter: int
    issued_at: int
    expires_at: int
    canonical_digest: str
    signature_algorithm: str
    verifier_key_id: str
    signature: str
    revocation_epoch: int
    supported: bool = True
    reinstall_reenrolled: bool = True
    trusted_display_claim: bool = False

    def material(self) -> dict[str, object]:
        return {
            "verifierId": self.verifier_id,
            "keyId": self.key_id,
            "bundleId": self.bundle_id,
            "teamId": self.team_id,
            "environment": self.environment,
            "challengeSha256": self.challenge_sha256,
            "capsuleSha256": self.capsule_sha256,
            "assertionSha256": self.assertion_sha256,
            "attestationChainSha256": self.attestation_chain_sha256,
            "counter": self.counter,
            "issuedAt": self.issued_at,
            "expiresAt": self.expires_at,
            "signatureAlgorithm": self.signature_algorithm,
            "verifierKeyId": self.verifier_key_id,
            "revocationEpoch": self.revocation_epoch,
            "supported": self.supported,
            "reinstallReenrolled": self.reinstall_reenrolled,
            "trustedDisplayClaim": self.trusted_display_claim,
        }

    def validate(
        self,
        *,
        expected_bundle_id: str,
        expected_team_id: str,
        expected_environment: str,
        expected_challenge_sha256: str,
        expected_capsule_sha256: str,
        now: int,
        trust_store: SignatureTrustStore,
        minimum_counter: int | None = None,
    ) -> None:
        if not _KEY_ID_RE.fullmatch(_text(self.key_id, "App Attest key id")):
            raise AppAttestVerificationError("App Attest key id contains an unsupported character")
        _text(self.verifier_id, "verifier id")
        _text(self.verifier_key_id, "verifier key id")
        for value, label in (
            (self.bundle_id, "bundle id"),
            (self.team_id, "team id"),
            (expected_bundle_id, "expected bundle id"),
            (expected_team_id, "expected team id"),
        ):
            _text(value, label)
        environment = _text(self.environment, "App Attest environment", maximum=32)
        expected_environment = _text(expected_environment, "expected App Attest environment", maximum=32)
        if environment not in _ENVIRONMENTS or environment != expected_environment:
            raise AppAttestVerificationError("App Attest environment is not the expected environment")
        if self.bundle_id != expected_bundle_id or self.team_id != expected_team_id:
            raise AppAttestVerificationError("App Attest bundle/team binding is invalid")
        for value, label in (
            (self.challenge_sha256, "challenge hash"),
            (self.capsule_sha256, "capsule hash"),
            (self.assertion_sha256, "assertion hash"),
            (self.attestation_chain_sha256, "attestation chain hash"),
        ):
            _hash(value, label)
        if self.challenge_sha256 != _hash(expected_challenge_sha256, "expected challenge hash"):
            raise AppAttestVerificationError("App Attest challenge binding is invalid")
        if self.capsule_sha256 != _hash(expected_capsule_sha256, "expected capsule hash"):
            raise AppAttestVerificationError("App Attest capsule binding is invalid")
        _non_negative_int(self.counter, "App Attest counter")
        now = _non_negative_int(now, "current time")
        issued_at = _non_negative_int(self.issued_at, "receipt issued time")
        expires_at = _non_negative_int(self.expires_at, "receipt expiry")
        if not issued_at <= now < expires_at:
            raise AppAttestVerificationError("App Attest verifier receipt is future-dated or expired")
        if minimum_counter is not None and self.counter <= _non_negative_int(minimum_counter, "minimum App Attest counter"):
            raise AppAttestVerificationError("App Attest counter replay or rollback detected")
        if type(self.supported) is not bool or not self.supported:
            raise AppAttestVerificationError("App Attest is unsupported")
        if type(self.reinstall_reenrolled) is not bool or not self.reinstall_reenrolled:
            raise AppAttestVerificationError("App Attest evidence is not re-enrolled after reinstall or migration")
        if type(self.trusted_display_claim) is not bool or self.trusted_display_claim:
            raise AppAttestVerificationError("App Attest must not claim a trusted display")
        expected_digest = canonical_hash("ios-app-attest-verifier-receipt-v2", self.material())
        if self.canonical_digest != expected_digest:
            raise AppAttestVerificationError("App Attest verifier receipt digest mismatch")
        if not isinstance(trust_store, SignatureTrustStore):
            raise AppAttestVerificationError("a protected App Attest verifier trust store is required")
        try:
            verified = trust_store.verify(
                self.verifier_id,
                self.verifier_key_id,
                self.signature_algorithm,
                b"ios-app-attest-verifier-receipt-v2\x00" + canonical_bytes(self.material()),
                self.signature,
                self.revocation_epoch,
            )
        except Exception as exc:
            raise AppAttestVerificationError("App Attest verifier signature check failed closed") from exc
        if verified is not True:
            raise AppAttestVerificationError("App Attest verifier signature is invalid")

    @property
    def evidence_digest(self) -> str:
        return canonical_hash(
            "ios-app-attest-evidence-v2",
            {**self.material(), "canonicalDigest": self.canonical_digest, "signature": self.signature},
        )


def verify_server_evidence(
    value: Mapping[str, Any],
    *,
    expected_bundle_id: str,
    expected_team_id: str,
    expected_environment: str,
    expected_challenge_sha256: str,
    expected_capsule_sha256: str,
    now: int,
    trust_store: SignatureTrustStore,
    minimum_counter: int | None = None,
) -> str:
    """Validate a signed protected-verifier receipt and return its evidence digest."""

    if not isinstance(value, Mapping):
        raise AppAttestVerificationError("App Attest evidence must be an object")
    fields = {
        "verifierId": "verifier_id",
        "keyId": "key_id",
        "bundleId": "bundle_id",
        "teamId": "team_id",
        "environment": "environment",
        "challengeSha256": "challenge_sha256",
        "capsuleSha256": "capsule_sha256",
        "assertionSha256": "assertion_sha256",
        "attestationChainSha256": "attestation_chain_sha256",
        "counter": "counter",
        "issuedAt": "issued_at",
        "expiresAt": "expires_at",
        "canonicalDigest": "canonical_digest",
        "signatureAlgorithm": "signature_algorithm",
        "verifierKeyId": "verifier_key_id",
        "signature": "signature",
        "revocationEpoch": "revocation_epoch",
        "supported": "supported",
        "reinstallReenrolled": "reinstall_reenrolled",
        "trustedDisplayClaim": "trusted_display_claim",
    }
    if set(value) != set(fields):
        raise AppAttestVerificationError(
            f"App Attest evidence fields mismatch: missing={sorted(set(fields) - set(value))}, "
            f"unexpected={sorted(set(value) - set(fields))}"
        )
    evidence = AppAttestEvidence(**{target: value[source] for source, target in fields.items()})
    evidence.validate(
        expected_bundle_id=expected_bundle_id,
        expected_team_id=expected_team_id,
        expected_environment=expected_environment,
        expected_challenge_sha256=expected_challenge_sha256,
        expected_capsule_sha256=expected_capsule_sha256,
        now=now,
        trust_store=trust_store,
        minimum_counter=minimum_counter,
    )
    return evidence.evidence_digest
