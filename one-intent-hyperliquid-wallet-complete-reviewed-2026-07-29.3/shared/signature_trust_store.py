"""Immutable public-key trust store for protected verifier boundaries.

The trust store contains public verification material only.  It deliberately
does not accept caller callbacks or precomputed trust booleans, so request
handlers cannot replace signature verification with ``lambda: True``.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


@dataclass(frozen=True)
class TrustedVerifierKey:
    issuer: str
    key_id: str
    public_key: bytes
    minimum_revocation_epoch: int = 0
    revoked: bool = False
    algorithm: str = "Ed25519"

    def __post_init__(self) -> None:
        if not self.issuer or not self.key_id:
            raise ValueError("trusted verifier issuer and key id are required")
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
        registry: dict[tuple[str, str, str], tuple[Ed25519PublicKey, int, bool]] = {}
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
            registry[identity] = (
                Ed25519PublicKey.from_public_bytes(entry.public_key),
                entry.minimum_revocation_epoch,
                entry.revoked,
            )
        if not registry:
            raise ValueError("trust store must contain at least one verifier key")
        self._registry: Mapping[tuple[str, str, str], tuple[Ed25519PublicKey, int, bool]] = MappingProxyType(registry)

    def verify(
        self,
        issuer: str,
        key_id: str,
        algorithm: str,
        payload: bytes,
        signature: str,
        revocation_epoch: int,
    ) -> bool:
        if not isinstance(payload, bytes) or not payload:
            return False
        if not isinstance(revocation_epoch, int) or isinstance(revocation_epoch, bool):
            return False
        entry = self._registry.get((issuer, key_id, algorithm))
        if entry is None:
            return False
        public_key, minimum_epoch, revoked = entry
        if revoked or revocation_epoch < minimum_epoch:
            return False
        try:
            raw_signature = _decode_unpadded_base64url(signature)
            if len(raw_signature) != 64:
                return False
            public_key.verify(raw_signature, payload)
        except (InvalidSignature, ValueError, TypeError):
            return False
        return True
