from __future__ import annotations

import base64
import copy
import inspect
import json
import tempfile
import threading
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from shared.atomic_signer_contract import (
    AssetRule,
    AtomicSignerBoundary,
    AtomicSignerConfiguration,
    AtomicSignerContractError,
    ClockRollbackError,
    JournalState,
    PINNED_V2_1_SCHEMA_SHA256,
    ReplayDetectedError,
    SQLiteOperationJournal,
    UnresolvedOperationError,
    parse_and_validate_atomic_signer_request,
    validate_atomic_signer_request,
)
from shared.canonical import CANONICAL_PROFILE_VERSION, canonical_bytes, canonical_hash
from shared.signature_trust_store import (
    SignatureTrustStore,
    TrustedVerifierKey,
    VerifierRole,
)


ACCOUNT = "0x" + "1" * 40
RECIPIENT = "0x" + "2" * 40
TOKEN_CONTRACT = "0x" + "3" * 40
FEE_RECIPIENT = "0x" + "4" * 40
RELEASE_DIGEST = "6" * 64
POLICY_DIGEST = "7" * 64

_PRIVATE_KEYS = {
    ("device-issuer", "device-key-1"): Ed25519PrivateKey.from_private_bytes(b"d" * 32),
    ("policy-issuer", "policy-key-1"): Ed25519PrivateKey.from_private_bytes(b"p" * 32),
    ("orchestrator-issuer", "orchestrator-key-1"): Ed25519PrivateKey.from_private_bytes(b"o" * 32),
}


class FixedClock:
    def __init__(self, wall: int = 1003, monotonic: int = 1_000_000) -> None:
        self.wall = wall
        self.monotonic = monotonic

    def wall_time(self) -> int:
        return self.wall

    def monotonic_ns(self) -> int:
        return self.monotonic


def _public(private: Ed25519PrivateKey) -> bytes:
    return private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def trust_store(*, policy_can_sign_review_domain: bool = False) -> SignatureTrustStore:
    common = {
        "allowed_audiences": frozenset({"atomic-signer"}),
        "allowed_environments": frozenset({"TESTNET"}),
        "allowed_deployments": frozenset({"deployment-1"}),
        "not_before": 900,
        "not_after": 1200,
    }
    policy_domains = {"runtime-decision-envelope-v2"}
    if policy_can_sign_review_domain:
        policy_domains.add("user-review-receipt-v2")
    return SignatureTrustStore(
        [
            TrustedVerifierKey(
                issuer="device-issuer",
                key_id="device-key-1",
                public_key=_public(_PRIVATE_KEYS[("device-issuer", "device-key-1")]),
                role=VerifierRole.HUMAN_REVIEW,
                allowed_domains=frozenset({"user-review-receipt-v2"}),
                **common,
            ),
            TrustedVerifierKey(
                issuer="policy-issuer",
                key_id="policy-key-1",
                public_key=_public(_PRIVATE_KEYS[("policy-issuer", "policy-key-1")]),
                role=VerifierRole.RUNTIME_POLICY,
                allowed_domains=frozenset(policy_domains),
                allowed_policy_bundle_digests=frozenset({POLICY_DIGEST}),
                allowed_release_subject_digests=frozenset({RELEASE_DIGEST}),
                **common,
            ),
            TrustedVerifierKey(
                issuer="orchestrator-issuer",
                key_id="orchestrator-key-1",
                public_key=_public(
                    _PRIVATE_KEYS[("orchestrator-issuer", "orchestrator-key-1")]
                ),
                role=VerifierRole.ORCHESTRATION,
                allowed_domains=frozenset({"atomic-signer-request-v2"}),
                allowed_policy_bundle_digests=frozenset({POLICY_DIGEST}),
                allowed_release_subject_digests=frozenset({RELEASE_DIGEST}),
                **common,
            ),
        ]
    )


def configuration(**changes: object) -> AtomicSignerConfiguration:
    values: dict[str, object] = {
        "expected_audience": "atomic-signer",
        "expected_environment": "TESTNET",
        "expected_deployment": "deployment-1",
        "expected_release_subject_digest": RELEASE_DIGEST,
        "expected_policy_bundle_digest": POLICY_DIGEST,
        "asset_registry": {
            "hyperliquid:USDC": AssetRule(
                asset_id="hyperliquid:USDC",
                decimals=6,
                allowed_networks=frozenset({"eip155:42161"}),
                token_contract=TOKEN_CONTRACT,
            )
        },
    }
    values.update(changes)
    return AtomicSignerConfiguration(**values)  # type: ignore[arg-type]


def sign(envelope: dict[str, object], domain: str) -> None:
    material = {
        key: value
        for key, value in envelope.items()
        if key not in {"canonicalDigest", "signature"}
    }
    envelope["canonicalDigest"] = canonical_hash(domain, material)
    private = _PRIVATE_KEYS[(str(envelope["issuer"]), str(envelope["keyId"]))]
    signature = private.sign(
        domain.encode("utf-8") + b"\x00" + canonical_bytes(material)
    )
    envelope["signature"] = (
        base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    )


def resign_all(request: dict[str, object]) -> None:
    operation = request["operationSpec"]
    review = request["reviewReceipt"]
    decision = request["runtimeDecision"]
    assert isinstance(operation, dict)
    assert isinstance(review, dict)
    assert isinstance(decision, dict)
    operation_digest = canonical_hash("operation-spec-v2", operation)
    review["operationSpecDigest"] = operation_digest
    decision["operationSpecDigest"] = operation_digest
    request["operationSpecDigest"] = operation_digest
    sign(review, "user-review-receipt-v2")
    review_digest = canonical_hash("user-review-receipt-v2", review)
    decision["reviewReceiptDigest"] = review_digest
    request["reviewReceiptDigest"] = review_digest
    sign(decision, "runtime-decision-envelope-v2")
    request["runtimeDecisionDigest"] = canonical_hash(
        "runtime-decision-envelope-v2", decision
    )
    sign(request, "atomic-signer-request-v2")


def fixture() -> dict[str, object]:
    operation: dict[str, object] = {
        "schemaVersion": "2.1",
        "canonicalProfile": CANONICAL_PROFILE_VERSION,
        "operationId": "operation-1",
        "operationType": "TRANSFER",
        "account": ACCOUNT,
        "network": "eip155:42161",
        "assetId": "hyperliquid:USDC",
        "orderedActions": ["TRANSFER"],
        "registryDigest": "1" * 64,
        "quoteDigest": "2" * 64,
        "sourceStateDigest": "3" * 64,
        "payloadCommitment": "4" * 64,
        "displayManifestDigest": "5" * 64,
        "operationDetails": {
            "amount": "1",
            "recipient": RECIPIENT,
            "tokenContract": TOKEN_CONTRACT,
            "fee": "0",
            "feeRecipient": FEE_RECIPIENT,
        },
        "expiresAt": 1100,
    }
    operation_digest = canonical_hash("operation-spec-v2", operation)
    review: dict[str, object] = {
        "schemaVersion": "2.1",
        "canonicalProfile": CANONICAL_PROFILE_VERSION,
        "issuer": "device-issuer",
        "subject": ACCOUNT,
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
        "notBefore": 1000,
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
        "canonicalProfile": CANONICAL_PROFILE_VERSION,
        "issuer": "policy-issuer",
        "subject": ACCOUNT,
        "audience": "atomic-signer",
        "environment": "TESTNET",
        "deployment": "deployment-1",
        "decisionId": "decision-1",
        "operationSpecDigest": operation_digest,
        "reviewReceiptDigest": review_digest,
        "releaseSubjectDigest": RELEASE_DIGEST,
        "policyBundleDigest": POLICY_DIGEST,
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
        "canonicalProfile": CANONICAL_PROFILE_VERSION,
        "issuer": "orchestrator-issuer",
        "subject": ACCOUNT,
        "audience": "atomic-signer",
        "environment": "TESTNET",
        "deployment": "deployment-1",
        "requestId": "request-1",
        "operationSpec": operation,
        "operationSpecDigest": operation_digest,
        "reviewReceipt": review,
        "reviewReceiptDigest": review_digest,
        "runtimeDecision": decision,
        "runtimeDecisionDigest": canonical_hash(
            "runtime-decision-envelope-v2", decision
        ),
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
    def make_boundary(
        self,
        *,
        database: Path | None = None,
        clock: FixedClock | None = None,
        store: SignatureTrustStore | None = None,
        config: AtomicSignerConfiguration | None = None,
    ) -> tuple[AtomicSignerBoundary, SQLiteOperationJournal, FixedClock, Path]:
        if database is None:
            temporary = tempfile.TemporaryDirectory()
            self.addCleanup(temporary.cleanup)
            database = Path(temporary.name) / "signer-journal.sqlite3"
        journal = SQLiteOperationJournal(database)
        self.addCleanup(journal.close)
        installed_clock = FixedClock() if clock is None else clock
        boundary = AtomicSignerBoundary(
            configuration=configuration() if config is None else config,
            trust_store=trust_store() if store is None else store,
            journal=journal,
            clock=installed_clock,
        )
        return boundary, journal, installed_clock, database

    def test_valid_raw_request_is_typed_immutable_and_reserved(self) -> None:
        boundary, _, _, _ = self.make_boundary()
        verified = validate_atomic_signer_request(
            canonical_bytes(fixture()), boundary=boundary
        )
        self.assertEqual(verified.operation.operation_type.value, "TRANSFER")
        self.assertEqual(len(verified.operation.account), 20)
        self.assertEqual(
            verified.reservation.state, JournalState.AUTHORIZATION_RESERVED
        )
        with self.assertRaises(TypeError):
            verified.request["requestId"] = "changed"  # type: ignore[index]

    def test_required_context_fields_cannot_be_missing_from_all_envelopes(self) -> None:
        for field in ("audience", "environment", "deployment"):
            request = fixture()
            for envelope in (
                request,
                request["reviewReceipt"],
                request["runtimeDecision"],
            ):
                assert isinstance(envelope, dict)
                envelope.pop(field)
            boundary, _, _, _ = self.make_boundary()
            with self.subTest(field=field), self.assertRaises(
                AtomicSignerContractError
            ):
                boundary.validate_and_reserve(canonical_bytes(request))

    def test_schema_rejects_unknown_field_version_short_nonce_and_es256(self) -> None:
        mutations = (
            lambda request: request.__setitem__("unknown", "field"),
            lambda request: request.__setitem__("schemaVersion", "2.2"),
            lambda request: request.__setitem__("nonce", "short"),
            lambda request: request.__setitem__("signatureAlgorithm", "ES256"),
        )
        for mutate in mutations:
            request = fixture()
            mutate(request)
            boundary, _, _, _ = self.make_boundary()
            with self.assertRaises(AtomicSignerContractError):
                boundary.validate_and_reserve(canonical_bytes(request))

    def test_only_exact_canonical_bytes_cross_the_boundary(self) -> None:
        boundary, _, _, _ = self.make_boundary()
        pretty = json.dumps(fixture(), ensure_ascii=False, indent=2).encode()
        with self.assertRaises(AtomicSignerContractError):
            parse_and_validate_atomic_signer_request(pretty, boundary=boundary)
        raw = canonical_bytes(fixture()).decode()
        duplicate = raw.replace(
            '"requestId":"request-1"',
            '"requestId":"request-1","requestId":"request-2"',
            1,
        ).encode()
        with self.assertRaises(AtomicSignerContractError):
            boundary.validate_and_reserve(duplicate)

    def test_binding_trust_boolean_blocked_decision_and_signature_fail_closed(self) -> None:
        requests = []
        binding = fixture()
        operation = binding["operationSpec"]
        assert isinstance(operation, dict)
        operation["payloadCommitment"] = "8" * 64
        requests.append(binding)
        trust = fixture()
        trust["signature_valid"] = True
        requests.append(trust)
        blocked = fixture()
        decision = blocked["runtimeDecision"]
        assert isinstance(decision, dict)
        decision["status"] = "BLOCKED"
        decision["blockingReasons"] = ["policy"]
        requests.append(blocked)
        bad_signature = fixture()
        review = bad_signature["reviewReceipt"]
        assert isinstance(review, dict)
        review["signature"] = "bad"
        requests.append(bad_signature)
        for request in requests:
            boundary, _, _, _ = self.make_boundary()
            with self.assertRaises(AtomicSignerContractError):
                boundary.validate_and_reserve(canonical_bytes(request))

    def test_review_cannot_be_signed_by_runtime_policy_key(self) -> None:
        request = fixture()
        review = request["reviewReceipt"]
        assert isinstance(review, dict)
        review["issuer"] = "policy-issuer"
        review["keyId"] = "policy-key-1"
        resign_all(request)
        boundary, _, _, _ = self.make_boundary(
            store=trust_store(policy_can_sign_review_domain=True)
        )
        with self.assertRaises(AtomicSignerContractError):
            boundary.validate_and_reserve(canonical_bytes(request))

    def test_signer_owned_context_release_and_policy_are_enforced(self) -> None:
        mutations = (
            ("environment", "STAGING"),
            ("deployment", "other-deployment"),
            ("audience", "other-audience"),
        )
        for field, value in mutations:
            request = fixture()
            for envelope in (
                request,
                request["reviewReceipt"],
                request["runtimeDecision"],
            ):
                assert isinstance(envelope, dict)
                envelope[field] = value
            resign_all(request)
            boundary, _, _, _ = self.make_boundary()
            with self.subTest(field=field), self.assertRaises(
                AtomicSignerContractError
            ):
                boundary.validate_and_reserve(canonical_bytes(request))
        for field in ("releaseSubjectDigest", "policyBundleDigest"):
            request = fixture()
            decision = request["runtimeDecision"]
            assert isinstance(decision, dict)
            decision[field] = "8" * 64
            resign_all(request)
            boundary, _, _, _ = self.make_boundary()
            with self.subTest(field=field), self.assertRaises(
                AtomicSignerContractError
            ):
                boundary.validate_and_reserve(canonical_bytes(request))

    def test_ttl_future_skew_and_clock_rollback_fail_closed(self) -> None:
        ttl = fixture()
        ttl["expiresAt"] = 1150
        resign_all(ttl)
        boundary, _, _, _ = self.make_boundary()
        with self.assertRaises(AtomicSignerContractError):
            boundary.validate_and_reserve(canonical_bytes(ttl))

        future = fixture()
        future["requestedAt"] = 1010
        future["notBefore"] = 1010
        resign_all(future)
        boundary, _, _, _ = self.make_boundary()
        with self.assertRaises(AtomicSignerContractError):
            boundary.validate_and_reserve(canonical_bytes(future))

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        database = Path(temporary.name) / "rollback.sqlite3"
        clock = FixedClock()
        boundary, journal, _, _ = self.make_boundary(database=database, clock=clock)
        verified = boundary.validate_and_reserve(canonical_bytes(fixture()))
        journal.transition(
            verified.operation.operation_id,
            fencing_token=verified.reservation.fencing_token,
            expected_state=JournalState.AUTHORIZATION_RESERVED,
            new_state=JournalState.ABORTED_BEFORE_SIGNING,
            event_type="ABORTED_BEFORE_SIGNING",
            payload_digest="4" * 64,
            observed_at=1003,
        )
        clock.wall = 990
        clock.monotonic += 1
        fresh = fixture()
        fresh["requestId"] = "request-2"
        fresh["authorizationId"] = "authorization-2"
        fresh["nonce"] = "one-time-nonce-2"
        operation = fresh["operationSpec"]
        assert isinstance(operation, dict)
        operation["operationId"] = "operation-2"
        resign_all(fresh)
        with self.assertRaises(ClockRollbackError):
            boundary.validate_and_reserve(canonical_bytes(fresh))

    def test_typed_operation_rejects_action_network_address_and_decimal_alias(self) -> None:
        changes = (
            ("orderedActions", ["SWAP"]),
            ("network", "unknown:network"),
            ("account", "0x" + "A" * 40),
        )
        for field, value in changes:
            request = fixture()
            operation = request["operationSpec"]
            assert isinstance(operation, dict)
            operation[field] = value
            resign_all(request)
            boundary, _, _, _ = self.make_boundary()
            with self.subTest(field=field), self.assertRaises(
                AtomicSignerContractError
            ):
                boundary.validate_and_reserve(canonical_bytes(request))
        request = fixture()
        operation = request["operationSpec"]
        assert isinstance(operation, dict)
        details = operation["operationDetails"]
        assert isinstance(details, dict)
        details["amount"] = "1.0"
        resign_all(request)
        boundary, _, _, _ = self.make_boundary()
        with self.assertRaises(AtomicSignerContractError):
            boundary.validate_and_reserve(canonical_bytes(request))

    def test_schema_pin_cannot_be_replaced_by_caller(self) -> None:
        pins = dict(PINNED_V2_1_SCHEMA_SHA256)
        pins["atomic-signer-request-v2.schema.json"] = "0" * 64
        with self.assertRaises(ValueError):
            configuration(schema_sha256=pins)

    def test_replay_claims_survive_restart_and_unresolved_work_blocks_new_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "journal.sqlite3"
            first_journal = SQLiteOperationJournal(database)
            first_boundary = AtomicSignerBoundary(
                configuration=configuration(),
                trust_store=trust_store(),
                journal=first_journal,
                clock=FixedClock(),
            )
            raw = canonical_bytes(fixture())
            first_boundary.validate_and_reserve(raw)
            first_journal.close()

            second_journal = SQLiteOperationJournal(database)
            self.addCleanup(second_journal.close)
            second_boundary = AtomicSignerBoundary(
                configuration=configuration(),
                trust_store=trust_store(),
                journal=second_journal,
                clock=FixedClock(monotonic=2_000_000),
            )
            with self.assertRaises(ReplayDetectedError):
                second_boundary.validate_and_reserve(raw)
            fresh = fixture()
            fresh["requestId"] = "request-2"
            fresh["authorizationId"] = "authorization-2"
            fresh["nonce"] = "one-time-nonce-2"
            operation = fresh["operationSpec"]
            assert isinstance(operation, dict)
            operation["operationId"] = "operation-2"
            resign_all(fresh)
            with self.assertRaises(UnresolvedOperationError):
                second_boundary.validate_and_reserve(canonical_bytes(fresh))
            self.assertEqual(
                second_journal.unresolved_operations()[0].state,
                JournalState.AUTHORIZATION_RESERVED,
            )

    def test_parallel_duplicate_reservation_has_at_most_one_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "journal.sqlite3"
            journals = [SQLiteOperationJournal(database), SQLiteOperationJournal(database)]
            self.addCleanup(journals[0].close)
            self.addCleanup(journals[1].close)
            boundaries = [
                AtomicSignerBoundary(
                    configuration=configuration(),
                    trust_store=trust_store(),
                    journal=journal,
                    clock=FixedClock(monotonic=1_000_000 + index),
                )
                for index, journal in enumerate(journals)
            ]
            results: list[str] = []
            lock = threading.Lock()

            def run(boundary: AtomicSignerBoundary) -> None:
                try:
                    boundary.validate_and_reserve(canonical_bytes(fixture()))
                    outcome = "success"
                except AtomicSignerContractError:
                    outcome = "rejected"
                with lock:
                    results.append(outcome)

            threads = [threading.Thread(target=run, args=(boundary,)) for boundary in boundaries]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(results.count("success"), 1)
            self.assertEqual(results.count("rejected"), 1)

    def test_signed_unknown_state_and_fencing_survive_restart(self) -> None:
        boundary, journal, _, _ = self.make_boundary()
        verified = boundary.validate_and_reserve(canonical_bytes(fixture()))
        with self.assertRaises(AtomicSignerContractError):
            journal.transition(
                verified.operation.operation_id,
                fencing_token=verified.reservation.fencing_token + 1,
                expected_state=JournalState.AUTHORIZATION_RESERVED,
                new_state=JournalState.SIGNING_INTENT_RECORDED,
                event_type="SIGNING_INTENT_RECORDED",
                payload_digest="4" * 64,
                observed_at=1003,
            )
        journal.transition(
            verified.operation.operation_id,
            fencing_token=verified.reservation.fencing_token,
            expected_state=JournalState.AUTHORIZATION_RESERVED,
            new_state=JournalState.SIGNING_INTENT_RECORDED,
            event_type="SIGNING_INTENT_RECORDED",
            payload_digest="4" * 64,
            observed_at=1003,
        )
        operation = journal.transition(
            verified.operation.operation_id,
            fencing_token=verified.reservation.fencing_token,
            expected_state=JournalState.SIGNING_INTENT_RECORDED,
            new_state=JournalState.SIGNED_BROADCAST_UNKNOWN,
            event_type="SIGNATURE_RECORDED",
            payload_digest="8" * 64,
            observed_at=1004,
        )
        self.assertEqual(operation.state, JournalState.SIGNED_BROADCAST_UNKNOWN)

    def test_api_has_no_caller_owned_now_or_mapping_shortcut(self) -> None:
        self.assertNotIn("now", inspect.signature(validate_atomic_signer_request).parameters)
        boundary, _, _, _ = self.make_boundary()
        with self.assertRaises(AtomicSignerContractError):
            validate_atomic_signer_request(fixture(), boundary=boundary)  # type: ignore[arg-type]

    def test_atomic_boundary_does_not_import_legacy_domain_module(self) -> None:
        source = inspect.getsource(inspect.getmodule(AtomicSignerBoundary))
        self.assertNotIn("from .domain", source)
        self.assertNotIn("import shared.domain", source)

    def test_duplicate_public_key_material_cannot_cross_roles(self) -> None:
        public = _public(next(iter(_PRIVATE_KEYS.values())))
        with self.assertRaises(ValueError):
            SignatureTrustStore(
                [
                    TrustedVerifierKey(
                        "issuer-1",
                        "key-1",
                        public,
                        VerifierRole.HUMAN_REVIEW,
                        frozenset({"user-review-receipt-v2"}),
                    ),
                    TrustedVerifierKey(
                        "issuer-2",
                        "key-2",
                        public,
                        VerifierRole.RUNTIME_POLICY,
                        frozenset({"runtime-decision-envelope-v2"}),
                    ),
                ]
            )


if __name__ == "__main__":
    unittest.main()
