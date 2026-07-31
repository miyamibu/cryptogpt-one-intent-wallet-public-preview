from __future__ import annotations

import base64
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from services.attestation.android_play_integrity import PlayIntegrityVerificationError, verify_play_integrity_receipt
from shared.canonical import canonical_bytes, canonical_hash
from shared.signature_trust_store import (
    SignatureTrustStore,
    TrustedVerifierKey,
    VerifierRole,
)


_PRIVATE = Ed25519PrivateKey.from_private_bytes(b"g" * 32)
_STORE = SignatureTrustStore(
    [TrustedVerifierKey(
        issuer="play-integrity-verifier-1",
        key_id="play-key-1",
        public_key=_PRIVATE.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw),
        role=VerifierRole.ATTESTATION,
        allowed_domains=frozenset({"android-play-integrity-verifier-receipt-v1"}),
    )]
)


def receipt(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "verifierId": "play-integrity-verifier-1",
        "packageName": "jp.offlinewallet.android.review",
        "certificateSha256": "a" * 64,
        "versionCode": 1,
        "environment": "TEST",
        "requestSha256": "b" * 64,
        "capsuleSha256": "c" * 64,
        "tokenSha256": "d" * 64,
        "nonce": "one-time-nonce-1",
        "deviceIntegrity": ["MEETS_DEVICE_INTEGRITY"],
        "appRecognitionVerdict": "PLAY_RECOGNIZED",
        "licensingVerdict": "LICENSED",
        "issuedAt": 1000,
        "expiresAt": 1100,
        "canonicalDigest": "",
        "signatureAlgorithm": "Ed25519",
        "verifierKeyId": "play-key-1",
        "signature": "",
        "revocationEpoch": 0,
    }
    value.update(changes)
    material = {key: item for key, item in value.items() if key not in {"canonicalDigest", "signature"}}
    value["canonicalDigest"] = canonical_hash("android-play-integrity-verifier-receipt-v1", material)
    signature = _PRIVATE.sign(b"android-play-integrity-verifier-receipt-v1\x00" + canonical_bytes(material))
    if "signature" not in changes:
        value["signature"] = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    return value


def verify(value: dict[str, object]) -> str:
    return verify_play_integrity_receipt(
        value,
        expected_package_name="jp.offlinewallet.android.review",
        expected_certificate_sha256="a" * 64,
        expected_version_code=1,
        expected_environment="TEST",
        expected_request_sha256="b" * 64,
        expected_capsule_sha256="c" * 64,
        expected_nonce="one-time-nonce-1",
        now=1001,
        trust_store=_STORE,
    )


class AndroidPlayIntegrityContractTests(unittest.TestCase):
    def test_accepts_exact_signed_receipt(self) -> None:
        self.assertEqual(len(verify(receipt())), 64)

    def test_rejects_substitution_stale_or_bad_signature(self) -> None:
        for changes in (
            {"packageName": "other.app"},
            {"requestSha256": "e" * 64},
            {"nonce": "replayed"},
            {"appRecognitionVerdict": "UNEVALUATED"},
            {"expiresAt": 1001},
            {"signature": "bad"},
        ):
            with self.subTest(changes=changes), self.assertRaises(PlayIntegrityVerificationError):
                verify(receipt(**changes))

    def test_rejects_caller_boolean_and_fake_trust_store(self) -> None:
        with self.assertRaises(PlayIntegrityVerificationError):
            verify(receipt(serverVerified=True))
        with self.assertRaises(PlayIntegrityVerificationError):
            verify_play_integrity_receipt(
                receipt(),
                expected_package_name="jp.offlinewallet.android.review",
                expected_certificate_sha256="a" * 64,
                expected_version_code=1,
                expected_environment="TEST",
                expected_request_sha256="b" * 64,
                expected_capsule_sha256="c" * 64,
                expected_nonce="one-time-nonce-1",
                now=1001,
                trust_store=lambda *_: True,  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
