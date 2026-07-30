from __future__ import annotations

import copy
import base64
import json
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from shared.atomic_signer_contract import (
    AtomicSignerContractError,
    parse_and_validate_atomic_signer_request,
    validate_atomic_signer_request,
)
from shared.canonical import canonical_bytes, canonical_hash
from shared.signature_trust_store import SignatureTrustStore, TrustedVerifierKey


_PRIVATE_KEYS = {
    ("device-issuer", "device-key-1"): Ed25519PrivateKey.from_private_bytes(b"d" * 32),
    ("policy-issuer", "policy-key-1"): Ed25519PrivateKey.from_private_bytes(b"p" * 32),
    ("orchestrator-issuer", "orchestrator-key-1"): Ed25519PrivateKey.from_private_bytes(b"o" * 32),
}
_TRUST_STORE = SignatureTrustStore(
    TrustedVerifierKey(
        issuer=issuer,
        key_id=key_id,
        public_key=private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ),
    )
    for (issuer, key_id), private in _PRIVATE_KEYS.items()
)


def sign(envelope: dict[str, object], domain: str) -> None:
    material = {key: value for key, value in envelope.items() if key not in {"canonicalDigest", "signature"}}
    envelope["canonicalDigest"] = canonical_hash(domain, material)
    private = _PRIVATE_KEYS[(str(envelope["issuer"]), str(envelope["keyId"]))]
    signature = private.sign(domain.encode("utf-8") + b"\x00" + canonical_bytes(material))
    envelope["signature"] = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")


def fixture() -> dict[str, object]:
    operation: dict[str, object] = {
        "schemaVersion": "2.1",
        "operationId": "operation-1",
        "operationType": "TRANSFER",
        "account": "account-1",
        "network": "eip155:42161",
        "assetId": "asset-1",
        "orderedActions": ["transfer"],
        "registryDigest": "1" * 64,
        "quoteDigest": "2" * 64,
        "sourceStateDigest": "3" * 64,
        "payloadCommitment": "4" * 64,
        "displayManifestDigest": "5" * 64,
        "operationDetails": {
            "amount": "1",
            "recipient": "recipient-1",
            "tokenContract": "contract-1",
            "fee": "0",
            "feeRecipient": "fee-recipient-1",
        },
        "expiresAt": 1100,
    }
    operation_digest = canonical_hash("operation-spec-v2", operation)
    review: dict[str, object] = {
        "schemaVersion": "2.1",
        "issuer": "device-issuer",
        "subject": "account-1",
        "audience": "atomic-signer",
        "environment": "TESTNET",
        "deployment": "deployment-1",
        "receiptId": "review-1",
        "operationSpecDigest": operation_digest,
        "displayDigest": "5" * 64,
        "quoteDigest": "2" * 64,
        "sourceStateDigest": "3" * 64,
        "finalPayloadDigest": "4" * 64,
        "locale": "ja-JP",
        "formattingVersion": "1",
        "deviceId": "device-1",
        "challengeNonce": "challenge-nonce-1",
        "reviewedAt": 1000,
        "notBefore": 990,
        "expiresAt": 1080,
        "canonicalDigest": "",
        "signatureAlgorithm": "Ed25519",
        "keyId": "device-key-1",
        "signature": "",
        "revocationEpoch": 1,
    }
    sign(review, "user-review-receipt-v2")
    review_digest = canonical_hash("user-review-receipt-v2", review)
    decision: dict[str, object] = {
        "schemaVersion": "2.1",
        "issuer": "policy-issuer",
        "subject": "account-1",
        "audience": "atomic-signer",
        "environment": "TESTNET",
        "deployment": "deployment-1",
        "decisionId": "decision-1",
        "operationSpecDigest": operation_digest,
        "reviewReceiptDigest": review_digest,
        "releaseSubjectDigest": "6" * 64,
        "policyBundleDigest": "7" * 64,
        "status": "ELIGIBLE_FOR_ATOMIC_SIGNER_FINALIZATION",
        "blockingReasons": [],
        "issuedAt": 990,
        "notBefore": 995,
        "evaluatedAt": 1001,
        "expiresAt": 1070,
        "canonicalDigest": "",
        "signatureAlgorithm": "Ed25519",
        "keyId": "policy-key-1",
        "signature": "",
        "revocationEpoch": 1,
    }
    sign(decision, "runtime-decision-envelope-v2")
    request: dict[str, object] = {
        "schemaVersion": "2.1",
        "issuer": "orchestrator-issuer",
        "subject": "account-1",
        "audience": "atomic-signer",
        "environment": "TESTNET",
        "deployment": "deployment-1",
        "requestId": "request-1",
        "operationSpec": operation,
        "operationSpecDigest": operation_digest,
        "reviewReceipt": review,
        "reviewReceiptDigest": review_digest,
        "runtimeDecision": decision,
        "runtimeDecisionDigest": canonical_hash("runtime-decision-envelope-v2", decision),
        "authorizationId": "authorization-1",
        "nonce": "one-time-nonce-1",
        "requestedAt": 1002,
        "notBefore": 1000,
        "expiresAt": 1060,
        "canonicalDigest": "",
        "signatureAlgorithm": "Ed25519",
        "keyId": "orchestrator-key-1",
        "signature": "",
        "revocationEpoch": 1,
    }
    sign(request, "atomic-signer-request-v2")
    return request


class AtomicSignerContractTests(unittest.TestCase):
    def test_valid_request_is_deeply_immutable_after_verification(self) -> None:
        verified = validate_atomic_signer_request(fixture(), now=1003, trust_store=_TRUST_STORE)
        self.assertEqual(verified.request_id, "request-1")
        with self.assertRaises(TypeError):
            verified.request["requestId"] = "changed"  # type: ignore[index]

    def test_every_material_binding_fails_closed(self) -> None:
        mutations = [
            ("operationSpec", "payloadCommitment", "8" * 64),
            ("reviewReceipt", "quoteDigest", "8" * 64),
            ("runtimeDecision", "operationSpecDigest", "8" * 64),
        ]
        for container, field, value in mutations:
            request = copy.deepcopy(fixture())
            request[container][field] = value  # type: ignore[index]
            with self.subTest(field=field), self.assertRaises(AtomicSignerContractError):
                validate_atomic_signer_request(request, now=1003, trust_store=_TRUST_STORE)

    def test_trust_boolean_blocked_decision_and_bad_signature_are_rejected(self) -> None:
        trust = fixture()
        trust["signature_valid"] = True
        with self.assertRaises(AtomicSignerContractError):
            validate_atomic_signer_request(trust, now=1003, trust_store=_TRUST_STORE)

        blocked = fixture()
        blocked["runtimeDecision"]["status"] = "BLOCKED"  # type: ignore[index]
        blocked["runtimeDecision"]["blockingReasons"] = ["policy"]  # type: ignore[index]
        with self.assertRaises(AtomicSignerContractError):
            validate_atomic_signer_request(blocked, now=1003, trust_store=_TRUST_STORE)

        bad_signature = fixture()
        bad_signature["reviewReceipt"]["signature"] = "bad"  # type: ignore[index]
        with self.assertRaises(AtomicSignerContractError):
            validate_atomic_signer_request(bad_signature, now=1003, trust_store=_TRUST_STORE)

    def test_duplicate_keys_and_subject_substitution_are_rejected(self) -> None:
        raw = json.dumps(fixture(), ensure_ascii=False, separators=(",", ":"))
        duplicate = raw.replace('"requestId":"request-1"', '"requestId":"request-1","requestId":"request-2"', 1)
        with self.assertRaises(AtomicSignerContractError):
            parse_and_validate_atomic_signer_request(duplicate, now=1003, trust_store=_TRUST_STORE)
        substituted = fixture()
        substituted["subject"] = "other-account"
        with self.assertRaises(AtomicSignerContractError):
            validate_atomic_signer_request(substituted, now=1003, trust_store=_TRUST_STORE)

    def test_callback_or_duplicate_key_material_cannot_replace_trust_store(self) -> None:
        with self.assertRaises(AtomicSignerContractError):
            validate_atomic_signer_request(fixture(), now=1003, trust_store=lambda *_: True)  # type: ignore[arg-type]
        public = next(iter(_PRIVATE_KEYS.values())).public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        with self.assertRaises(ValueError):
            SignatureTrustStore(
                [
                    TrustedVerifierKey("issuer-1", "key-1", public),
                    TrustedVerifierKey("issuer-2", "key-2", public),
                ]
            )


if __name__ == "__main__":
    unittest.main()
