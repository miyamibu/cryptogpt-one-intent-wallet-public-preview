"""Fail-closed contract for externally verified iOS App Attest evidence.

This module deliberately does not implement Apple's attestation signature
verification.  That operation belongs in a protected server verifier with
Apple's root certificates and the correct environment.  The local contract
prevents a caller from turning an unverified, stale, replayed, or
mis-bound record into authorization evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from shared.canonical import CanonicalizationError, canonical_hash, ensure_nfc
from shared.domain import DomainError


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_KEY_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_ENVIRONMENTS = {"development", "production"}


class AppAttestVerificationError(DomainError):
    """The evidence cannot be accepted as server-verified App Attest proof."""


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
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise AppAttestVerificationError(f"{label} must be a non-negative integer")
    return value


@dataclass(frozen=True)
class AppAttestEvidence:
    """A redacted result returned by a protected Apple verifier.

    `server_verified` is an assertion about an external verifier result, not a
    value the client may set to bypass verification.  The local package has
    no Apple private key, certificate chain, or production verifier.
    """

    key_id: str
    bundle_id: str
    team_id: str
    environment: str
    challenge_sha256: str
    capsule_sha256: str
    assertion_sha256: str
    attestation_chain_sha256: str
    counter: int
    server_verified: bool
    supported: bool = True
    reinstall_reenrolled: bool = True
    trusted_display_claim: bool = False

    def validate(
        self,
        *,
        expected_bundle_id: str,
        expected_team_id: str,
        expected_environment: str,
        expected_challenge_sha256: str,
        expected_capsule_sha256: str,
        minimum_counter: int | None = None,
    ) -> None:
        if not isinstance(self, AppAttestEvidence):
            raise AppAttestVerificationError("App Attest evidence has the wrong runtime type")
        if not _KEY_ID_RE.fullmatch(_text(self.key_id, "App Attest key id")):
            raise AppAttestVerificationError("App Attest key id contains an unsupported character")
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
        _hash(self.challenge_sha256, "challenge hash")
        _hash(self.capsule_sha256, "capsule hash")
        _hash(self.assertion_sha256, "assertion hash")
        _hash(self.attestation_chain_sha256, "attestation chain hash")
        if self.challenge_sha256 != _hash(expected_challenge_sha256, "expected challenge hash"):
            raise AppAttestVerificationError("App Attest challenge binding is invalid")
        if self.capsule_sha256 != _hash(expected_capsule_sha256, "expected capsule hash"):
            raise AppAttestVerificationError("App Attest capsule binding is invalid")
        _non_negative_int(self.counter, "App Attest counter")
        if minimum_counter is not None:
            minimum_counter = _non_negative_int(minimum_counter, "minimum App Attest counter")
            if self.counter <= minimum_counter:
                raise AppAttestVerificationError("App Attest counter replay or rollback detected")
        if type(self.supported) is not bool or not self.supported:
            raise AppAttestVerificationError("App Attest is unsupported")
        if type(self.reinstall_reenrolled) is not bool or not self.reinstall_reenrolled:
            raise AppAttestVerificationError("App Attest evidence is not re-enrolled after reinstall or migration")
        if type(self.trusted_display_claim) is not bool or self.trusted_display_claim:
            raise AppAttestVerificationError("App Attest must not claim a trusted display")
        if type(self.server_verified) is not bool or not self.server_verified:
            raise AppAttestVerificationError("Apple App Attest server verification is missing")

    @property
    def evidence_digest(self) -> str:
        """Digest of redacted evidence fields for an audit index."""

        return canonical_hash(
            "ios-app-attest-evidence-v1",
            {
                "keyId": self.key_id,
                "bundleId": self.bundle_id,
                "teamId": self.team_id,
                "environment": self.environment,
                "challengeSha256": self.challenge_sha256,
                "capsuleSha256": self.capsule_sha256,
                "assertionSha256": self.assertion_sha256,
                "attestationChainSha256": self.attestation_chain_sha256,
                "counter": self.counter,
                "serverVerified": self.server_verified,
                "supported": self.supported,
                "reinstallReenrolled": self.reinstall_reenrolled,
                "trustedDisplayClaim": self.trusted_display_claim,
            },
        )


def verify_server_evidence(
    value: Mapping[str, Any],
    *,
    expected_bundle_id: str,
    expected_team_id: str,
    expected_environment: str,
    expected_challenge_sha256: str,
    expected_capsule_sha256: str,
    minimum_counter: int | None = None,
) -> str:
    """Validate a redacted verifier result and return its stable evidence digest."""

    if not isinstance(value, Mapping):
        raise AppAttestVerificationError("App Attest evidence must be an object")
    fields = {
        "keyId": "key_id",
        "bundleId": "bundle_id",
        "teamId": "team_id",
        "environment": "environment",
        "challengeSha256": "challenge_sha256",
        "capsuleSha256": "capsule_sha256",
        "assertionSha256": "assertion_sha256",
        "attestationChainSha256": "attestation_chain_sha256",
        "counter": "counter",
        "serverVerified": "server_verified",
        "supported": "supported",
        "reinstallReenrolled": "reinstall_reenrolled",
        "trustedDisplayClaim": "trusted_display_claim",
    }
    missing = [key for key in fields if key not in value]
    if missing:
        raise AppAttestVerificationError(f"App Attest evidence is missing fields: {sorted(missing)}")
    evidence = AppAttestEvidence(**{target: value[source] for source, target in fields.items()})
    evidence.validate(
        expected_bundle_id=expected_bundle_id,
        expected_team_id=expected_team_id,
        expected_environment=expected_environment,
        expected_challenge_sha256=expected_challenge_sha256,
        expected_capsule_sha256=expected_capsule_sha256,
        minimum_counter=minimum_counter,
    )
    return evidence.evidence_digest
