"""Fail-closed contract for a protected Play Integrity verifier receipt.

This validates a receipt emitted by a deployment-controlled verifier.  It does
not include Google service credentials, call the Play Integrity API, or prove a
production Play Console configuration.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from shared.canonical import CanonicalizationError, canonical_bytes, canonical_hash, ensure_nfc
from shared.domain import DomainError
from shared.signature_trust_store import SignatureTrustStore


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_DEVICE_VERDICTS = {"MEETS_BASIC_INTEGRITY", "MEETS_DEVICE_INTEGRITY", "MEETS_STRONG_INTEGRITY"}
_MAX_TIME = 2**63 - 1


class PlayIntegrityVerificationError(DomainError):
    pass


def _text(value: object, label: str, *, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise PlayIntegrityVerificationError(f"{label} is missing or oversized")
    try:
        ensure_nfc(value)
    except CanonicalizationError as exc:
        raise PlayIntegrityVerificationError(f"{label} is not canonical text") from exc
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise PlayIntegrityVerificationError(f"{label} contains a control character")
    return value


def _digest(value: object, label: str) -> str:
    value = _text(value, label, maximum=64)
    if not _SHA256_RE.fullmatch(value):
        raise PlayIntegrityVerificationError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= _MAX_TIME:
        raise PlayIntegrityVerificationError(f"{label} must be a non-negative signed 64-bit integer")
    return value


def verify_play_integrity_receipt(
    value: Mapping[str, Any],
    *,
    expected_package_name: str,
    expected_certificate_sha256: str,
    expected_version_code: int,
    expected_environment: str,
    expected_request_sha256: str,
    expected_capsule_sha256: str,
    expected_nonce: str,
    now: int,
    trust_store: SignatureTrustStore,
) -> str:
    fields = {
        "verifierId", "packageName", "certificateSha256", "versionCode", "environment",
        "requestSha256", "capsuleSha256", "tokenSha256", "nonce", "deviceIntegrity",
        "appRecognitionVerdict", "licensingVerdict", "issuedAt", "expiresAt",
        "canonicalDigest", "signatureAlgorithm", "verifierKeyId", "signature", "revocationEpoch",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise PlayIntegrityVerificationError("Play Integrity receipt fields do not match the protected contract")
    if not isinstance(trust_store, SignatureTrustStore):
        raise PlayIntegrityVerificationError("a protected Play Integrity verifier trust store is required")
    for actual, expected, label in (
        (value["packageName"], expected_package_name, "package name"),
        (value["environment"], expected_environment, "environment"),
        (value["nonce"], expected_nonce, "nonce"),
    ):
        if _text(actual, label) != _text(expected, f"expected {label}"):
            raise PlayIntegrityVerificationError(f"Play Integrity {label} binding is invalid")
    if _digest(value["certificateSha256"], "certificate digest") != _digest(expected_certificate_sha256, "expected certificate digest"):
        raise PlayIntegrityVerificationError("Play Integrity signing certificate binding is invalid")
    if _digest(value["requestSha256"], "request digest") != _digest(expected_request_sha256, "expected request digest"):
        raise PlayIntegrityVerificationError("Play Integrity request binding is invalid")
    if _digest(value["capsuleSha256"], "capsule digest") != _digest(expected_capsule_sha256, "expected capsule digest"):
        raise PlayIntegrityVerificationError("Play Integrity capsule binding is invalid")
    _digest(value["tokenSha256"], "token digest")
    if _integer(value["versionCode"], "version code") != _integer(expected_version_code, "expected version code"):
        raise PlayIntegrityVerificationError("Play Integrity app version binding is invalid")
    issued_at = _integer(value["issuedAt"], "receipt issued time")
    expires_at = _integer(value["expiresAt"], "receipt expiry")
    now = _integer(now, "current time")
    if not issued_at <= now < expires_at or expires_at - issued_at > 300:
        raise PlayIntegrityVerificationError("Play Integrity receipt is future-dated, expired, or too long-lived")
    verdicts = value["deviceIntegrity"]
    if not isinstance(verdicts, list) or not verdicts or any(item not in _ALLOWED_DEVICE_VERDICTS for item in verdicts):
        raise PlayIntegrityVerificationError("Play Integrity device verdict is not accepted")
    if value["appRecognitionVerdict"] != "PLAY_RECOGNIZED" or value["licensingVerdict"] != "LICENSED":
        raise PlayIntegrityVerificationError("Play Integrity app or licensing verdict is not accepted")
    material = {key: item for key, item in value.items() if key not in {"canonicalDigest", "signature"}}
    expected_digest = canonical_hash("android-play-integrity-verifier-receipt-v1", material)
    if value["canonicalDigest"] != expected_digest:
        raise PlayIntegrityVerificationError("Play Integrity receipt digest mismatch")
    try:
        verified = trust_store.verify(
            _text(value["verifierId"], "verifier id"),
            _text(value["verifierKeyId"], "verifier key id"),
            _text(value["signatureAlgorithm"], "signature algorithm"),
            b"android-play-integrity-verifier-receipt-v1\x00" + canonical_bytes(material),
            _text(value["signature"], "signature", maximum=512),
            _integer(value["revocationEpoch"], "revocation epoch"),
        )
    except Exception as exc:
        raise PlayIntegrityVerificationError("Play Integrity signature check failed closed") from exc
    if verified is not True:
        raise PlayIntegrityVerificationError("Play Integrity verifier signature is invalid")
    return canonical_hash(
        "android-play-integrity-evidence-v1",
        {**material, "canonicalDigest": expected_digest, "signature": value["signature"]},
    )
