from __future__ import annotations

import base64
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from services.attestation.ios_app_attest import AppAttestVerificationError, verify_server_evidence
from shared.canonical import CanonicalizationError, canonical_bytes, canonical_hash
from shared.signature_trust_store import (
    SignatureTrustStore,
    TrustedVerifierKey,
    VerifierRole,
)


_PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(b"a" * 32)
_TRUST_STORE = SignatureTrustStore(
    [
        TrustedVerifierKey(
            issuer="app-attest-verifier-1",
            key_id="verifier-key-1",
            public_key=_PRIVATE_KEY.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            ),
            role=VerifierRole.ATTESTATION,
            allowed_domains=frozenset({"ios-app-attest-verifier-receipt-v2"}),
        )
    ]
)


def evidence(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "verifierId": "app-attest-verifier-1",
        "keyId": "ios-key-001",
        "bundleId": "jp.offlinewallet.ios.review",
        "teamId": "PUBLICTEAM",
        "environment": "development",
        "challengeSha256": "a" * 64,
        "capsuleSha256": "b" * 64,
        "assertionSha256": "c" * 64,
        "attestationChainSha256": "d" * 64,
        "counter": 7,
        "issuedAt": 1000,
        "expiresAt": 1100,
        "canonicalDigest": "",
        "signatureAlgorithm": "Ed25519",
        "verifierKeyId": "verifier-key-1",
        "signature": "",
        "revocationEpoch": 1,
        "supported": True,
        "reinstallReenrolled": True,
        "trustedDisplayClaim": False,
    }
    value.update(changes)
    material = {key: item for key, item in value.items() if key not in {"canonicalDigest", "signature"}}
    try:
        value["canonicalDigest"] = canonical_hash("ios-app-attest-verifier-receipt-v2", material)
        signature = _PRIVATE_KEY.sign(
            b"ios-app-attest-verifier-receipt-v2\x00" + canonical_bytes(material)
        )
        if "signature" not in changes:
            value["signature"] = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    except CanonicalizationError:
        value["canonicalDigest"] = "0" * 64
    return value


def verify(value: dict[str, object], *, minimum_counter: int | None = None) -> str:
    return verify_server_evidence(
        value,
        expected_bundle_id="jp.offlinewallet.ios.review",
        expected_team_id="PUBLICTEAM",
        expected_environment="development",
        expected_challenge_sha256="a" * 64,
        expected_capsule_sha256="b" * 64,
        now=1001,
        trust_store=_TRUST_STORE,
        minimum_counter=minimum_counter,
    )


class IOSAppAttestContractTests(unittest.TestCase):
    def test_accepts_exact_signed_verifier_binding(self) -> None:
        self.assertEqual(len(verify(evidence(), minimum_counter=6)), 64)

    def test_caller_boolean_is_rejected_and_signature_is_required(self) -> None:
        for changes in (
            {"serverVerified": True},
            {"signature": "bad"},
            {"trustedDisplayClaim": True},
            {"supported": False},
        ):
            with self.subTest(changes=changes), self.assertRaises(AppAttestVerificationError):
                verify(evidence(**changes))

    def test_rejects_binding_mismatch_counter_replay_expiry_and_reinstall_reuse(self) -> None:
        cases = (
            ({"bundleId": "other.bundle"}, None),
            ({"challengeSha256": "e" * 64}, None),
            ({"counter": 6}, 6),
            ({"expiresAt": 1001}, None),
            ({"reinstallReenrolled": False}, None),
        )
        for changes, minimum_counter in cases:
            with self.subTest(changes=changes), self.assertRaises(AppAttestVerificationError):
                verify(evidence(**changes), minimum_counter=minimum_counter)

    def test_rejects_ambiguous_shape_and_unsafe_counter(self) -> None:
        for changes in ({"unexpectedAuthorization": True}, {"counter": True}, {"counter": 2**63}):
            with self.subTest(changes=changes), self.assertRaises(AppAttestVerificationError):
                verify(evidence(**changes))


if __name__ == "__main__":
    unittest.main()
