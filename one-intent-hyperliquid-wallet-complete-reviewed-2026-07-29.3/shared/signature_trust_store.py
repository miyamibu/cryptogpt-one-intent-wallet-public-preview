"""Immutable, role-scoped public-key trust store for verifier boundaries.

The trust store contains public verification material only.  It deliberately
does not accept caller callbacks or precomputed trust booleans, so request
handlers cannot replace signature verification with ``lambda: True``.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class VerifierRole(str, Enum):
    HUMAN_REVIEW = "human-review"
    RUNTIME_POLICY = "runtime-policy"
    ORCHESTRATION = "orchestration"
    ATTESTATION = "attestation"
    RELEASE = "release"


_UNBOUNDED_NOT_AFTER = 9_007_199_254_740_991


def _frozen_text_scope(value: Iterable[str], label: str, *, required: bool = False) -> frozenset[str]:
    try:
        result = frozenset(value)
    except TypeError as exc:
        raise ValueError(f"{label} must be an iterable of text values") from exc
    if required and not result:
        raise ValueError(f"{label} must not be empty")
    if any(not isinstance(item, str) or not item for item in result):
        raise ValueError(f"{label} must contain non-empty text values")
    return result


@dataclass(frozen=True)
class TrustedVerifierKey:
    issuer: str
    key_id: str
    public_key: bytes
    role: VerifierRole
    allowed_domains: frozenset[str]
    allowed_audiences: frozenset[str] = frozenset()
    allowed_environments: frozenset[str] = frozenset()
    allowed_deployments: frozenset[str] = frozenset()
    allowed_policy_bundle_digests: frozenset[str] = frozenset()
    allowed_release_subject_digests: frozenset[str] = frozenset()
    not_before: int = 0
    not_after: int = _UNBOUNDED_NOT_AFTER
    minimum_revocation_epoch: int = 0
    revoked: bool = False
    algorithm: str = "Ed25519"

    def __post_init__(self) -> None:
        if not self.issuer or not self.key_id:
            raise ValueError("trusted verifier issuer and key id are required")
        try:
            role = VerifierRole(self.role)
        except (TypeError, ValueError) as exc:
            raise ValueError("trusted verifier role is not supported") from exc
        object.__setattr__(self, "role", role)
        object.__setattr__(
            self,
            "allowed_domains",
            _frozen_text_scope(self.allowed_domains, "allowed domains", required=True),
        )
        for attribute, label in (
            ("allowed_audiences", "allowed audiences"),
            ("allowed_environments", "allowed environments"),
            ("allowed_deployments", "allowed deployments"),
            ("allowed_policy_bundle_digests", "allowed policy bundle digests"),
            ("allowed_release_subject_digests", "allowed release subject digests"),
        ):
            object.__setattr__(
                self,
                attribute,
                _frozen_text_scope(getattr(self, attribute), label),
            )
        if self.algorithm != "Ed25519":
            raise ValueError("only Ed25519 verifier keys are supported")
        if not isinstance(self.public_key, bytes) or len(self.public_key) != 32:
            raise ValueError("Ed25519 public key must contain exactly 32 bytes")
        if (
            not isinstance(self.minimum_revocation_epoch, int)
            or isinstance(self.minimum_revocation_epoch, bool)
            or self.minimum_revocation_epoch < 0
        ):
            raise ValueError("minimum revocation epoch must be a non-negative integer")
        if (
            not isinstance(self.not_before, int)
            or isinstance(self.not_before, bool)
            or not isinstance(self.not_after, int)
            or isinstance(self.not_after, bool)
            or self.not_before < 0
            or self.not_after <= self.not_before
        ):
            raise ValueError("trusted verifier validity window is invalid")
        if type(self.revoked) is not bool:
            raise ValueError("revoked must be a strict boolean")


def _decode_unpadded_base64url(value: str) -> bytes:
    if not isinstance(value, str) or not value or "=" in value:
        raise ValueError("signature must be unpadded base64url text")
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, binascii.Error) as exc:
        raise ValueError("signature is not valid base64url") from exc
    if base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii") != value:
        raise ValueError("signature is not canonical base64url")
    return decoded


class SignatureTrustStore:
    """Deployment-owned immutable verifier registry."""

    def __init__(self, keys: Iterable[TrustedVerifierKey]) -> None:
        registry: dict[tuple[str, str, str], tuple[TrustedVerifierKey, Ed25519PublicKey]] = {}
        fingerprints: set[bytes] = set()
        for entry in keys:
            if not isinstance(entry, TrustedVerifierKey):
                raise ValueError("trust store entries must be TrustedVerifierKey values")
            identity = (entry.issuer, entry.key_id, entry.algorithm)
            if identity in registry:
                raise ValueError("duplicate trusted verifier identity")
            if entry.public_key in fingerprints:
                raise ValueError("duplicate public-key material cannot satisfy distinct identities")
            fingerprints.add(entry.public_key)
            registry[identity] = (entry, Ed25519PublicKey.from_public_bytes(entry.public_key))
        if not registry:
            raise ValueError("trust store must contain at least one verifier key")
        self._registry: Mapping[
            tuple[str, str, str],
            tuple[TrustedVerifierKey, Ed25519PublicKey],
        ] = MappingProxyType(registry)

    def verify(
        self,
        issuer: str,
        key_id: str,
        algorithm: str,
        payload: bytes,
        signature: str,
        revocation_epoch: int,
        *,
        domain: str | None = None,
        required_role: VerifierRole | str | None = None,
        audience: str | None = None,
        environment: str | None = None,
        deployment: str | None = None,
        policy_bundle_digest: str | None = None,
        release_subject_digest: str | None = None,
        now: int | None = None,
    ) -> bool:
        if not isinstance(payload, bytes) or not payload:
            return False
        if not isinstance(revocation_epoch, int) or isinstance(revocation_epoch, bool):
            return False
        entry = self._registry.get((issuer, key_id, algorithm))
        if entry is None:
            return False
        trusted, public_key = entry
        if trusted.revoked or revocation_epoch < trusted.minimum_revocation_epoch:
            return False
        prefix, separator, _ = payload.partition(b"\x00")
        if not separator:
            return False
        try:
            payload_domain = prefix.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return False
        if domain is not None and payload_domain != domain:
            return False
        if payload_domain not in trusted.allowed_domains:
            return False
        if required_role is not None:
            try:
                role = VerifierRole(required_role)
            except (TypeError, ValueError):
                return False
            if trusted.role is not role:
                return False
        if now is None:
            if trusted.not_before != 0 or trusted.not_after != _UNBOUNDED_NOT_AFTER:
                return False
        elif (
            not isinstance(now, int)
            or isinstance(now, bool)
            or not trusted.not_before <= now < trusted.not_after
        ):
            return False
        scopes = (
            (trusted.allowed_audiences, audience),
            (trusted.allowed_environments, environment),
            (trusted.allowed_deployments, deployment),
            (trusted.allowed_policy_bundle_digests, policy_bundle_digest),
            (trusted.allowed_release_subject_digests, release_subject_digest),
        )
        for allowed, supplied in scopes:
            if allowed and supplied not in allowed:
                return False
            if not allowed and supplied is not None:
                return False
        try:
            raw_signature = _decode_unpadded_base64url(signature)
            if len(raw_signature) != 64:
                return False
            public_key.verify(raw_signature, payload)
        except (InvalidSignature, ValueError, TypeError):
            return False
        return True
