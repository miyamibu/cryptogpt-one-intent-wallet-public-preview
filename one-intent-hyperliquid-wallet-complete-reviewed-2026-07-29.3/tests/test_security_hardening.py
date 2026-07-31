from __future__ import annotations

import http.client
import json
import socket
import sqlite3
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path

from adapters.fee_route.fee import FeeRouteCapability, OperationBoundQuote, fee_readiness_plan, zero_native_balance_eligible
from adapters.hyperliquid.fake_adapter import FakeHyperliquidAdapter
from adapters.jpyc_ex_handoff.adapter import JpycHandoff, prepare_handoff, validate_return
from services.local_sandbox.server import LocalSandboxApp, create_server
from services.signer_interface.signer import SignerInterface
from shared.canonical import CanonicalizationError, ResourceLimitError, canonical_bytes, decimal_string, strict_loads
from shared.domain import (
    ActionPlanDraft,
    AssetIdentity,
    AuthorizationEnvelope,
    CanonicalQuote,
    DomainError,
    DurableAuthorizationStore,
    DurableSaga,
    ExecutionCapsule,
    PolicyInput,
    SagaStepState,
    SignedRegistry,
    SignerGate,
    evaluate_policy,
)
from tests.test_capsule_signer import fixtures, proof


ROOT = Path(__file__).parents[1]


class CanonicalHardeningTests(unittest.TestCase):
    def test_depth_cycle_and_non_text_keys_fail_closed(self) -> None:
        with self.assertRaises(ResourceLimitError):
            strict_loads("[" * 129 + "0" + "]" * 129)
        cyclic: list[object] = []
        cyclic.append(cyclic)
        with self.assertRaises(CanonicalizationError):
            canonical_bytes(cyclic)
        with self.assertRaises(CanonicalizationError):
            canonical_bytes({1: "not-json"})

    def test_decimal_resource_limits_are_enforced(self) -> None:
        with self.assertRaises(CanonicalizationError):
            decimal_string("1" * 129)
        with self.assertRaises(CanonicalizationError):
            decimal_string("0." + "1" * 39)
        with self.assertRaises(CanonicalizationError):
            decimal_string("1", scale=True)


class DomainHardeningTests(unittest.TestCase):
    def test_draft_rejects_runtime_type_coercion_and_oversize(self) -> None:
        with self.assertRaises(DomainError):
            ActionPlanDraft("x", "y", {}, (), 1).validate()  # type: ignore[arg-type]
        with self.assertRaises(DomainError):
            ActionPlanDraft("x", "y", {"alias": 123}).validate()
        with self.assertRaises(DomainError):
            ActionPlanDraft("x" * 2049, "y", {}).validate()

    def test_registry_rejects_key_identity_and_boolean_integer_confusion(self) -> None:
        identity = AssetIdentity("BTC-USDC", "eip155:42161", "contract", 8, "code")
        mismatched = SignedRegistry("registry", 1, 1, 10, "key", "sig", True, False, {"ETH-USDC": identity})
        with self.assertRaises(DomainError):
            mismatched.verify(5)
        bad_sequence = replace(mismatched, sequence=True, entries={"BTC-USDC": identity})  # type: ignore[arg-type]
        with self.assertRaises(DomainError):
            bad_sequence.verify(5)

    def test_quote_and_capsule_reject_missing_binding_and_payload_type_confusion(self) -> None:
        _, quote, capsule = fixtures()
        with self.assertRaises(DomainError):
            replace(quote, execution_capsule_hash="").verify(
                1000,
                network=quote.network,
                asset_id=quote.asset_id,
                account=quote.account,
                amount=quote.amount,
            )
        with self.assertRaises(DomainError):
            replace(capsule, final_payload={"amount": 500}).validate(1000)
        with self.assertRaises(DomainError):
            replace(capsule, ordered_actions=("place-order", 1)).validate(1000)  # type: ignore[arg-type]

    def test_zero_native_policy_requires_verified_fresh_finite_route(self) -> None:
        missing_expiry = evaluate_policy(PolicyInput(False, True, "EOA", "0.0", True, None, 1000))
        self.assertFalse(missing_expiry.allowed)
        self.assertEqual(missing_expiry.reason_code, "FEE_ROUTE_EXPIRY_MISSING")
        unverified = evaluate_policy(PolicyInput(False, True, "EOA", "0", False, 1100, 1000))
        self.assertEqual(unverified.reason_code, "FEE_ROUTE_UNVERIFIED")
        malformed = evaluate_policy(PolicyInput(1, True, "EOA", "1", False, None, 1000))  # type: ignore[arg-type]
        self.assertEqual(malformed.reason_code, "INVALID_POLICY_INPUT")

    def test_unsafe_existing_authorization_store_schema_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = f"{directory}/unsafe.sqlite"
            connection = sqlite3.connect(path)
            connection.execute("CREATE TABLE consumed_authorization (authorization_id TEXT PRIMARY KEY, nonce TEXT NOT NULL)")
            connection.commit()
            connection.close()
            with self.assertRaises(DomainError):
                DurableAuthorizationStore(path)

    def test_pending_or_unknown_signer_state_blocks_different_authorization(self) -> None:
        _, _, capsule = fixtures()
        first = AuthorizationEnvelope(
            "auth-state-a", "device-1", "acct-1", capsule.hash, capsule.operation_type,
            1000, 1100, "nonce-state-a", "review",
            proof("auth-state-a", "device-1", "acct-1", capsule.hash, "nonce-state-a"),
        )
        second = AuthorizationEnvelope(
            "auth-state-b", "device-1", "acct-1", capsule.hash, capsule.operation_type,
            1000, 1100, "nonce-state-b", "review",
            proof("auth-state-b", "device-1", "acct-1", capsule.hash, "nonce-state-b"),
        )
        signer = SignerGate()
        with self.assertRaises(RuntimeError):
            signer.sign(capsule, first, release_go=True, runtime_lease_valid=True, now=1001, fail_after_sign=True)
        with self.assertRaises(DomainError):
            signer.sign(capsule, second, release_go=True, runtime_lease_valid=True, now=1001)
        signer.reconcile("unknown")
        with self.assertRaises(DomainError):
            signer.sign(capsule, second, release_go=True, runtime_lease_valid=True, now=1001)
        signer.reconcile("confirmed")
        with self.assertRaises(DomainError):
            signer.sign(capsule, second, release_go=True, runtime_lease_valid=True, now=1001)

    def test_reconcile_without_pending_signature_is_rejected(self) -> None:
        with self.assertRaises(DomainError):
            SignerGate().reconcile("confirmed")

    def test_saga_idempotency_material_and_transitions_are_strict(self) -> None:
        saga = DurableSaga("operation")
        saga.submit("step", "idem", "external")
        with self.assertRaises(DomainError):
            saga.submit("step", "idem", "changed")
        with self.assertRaises(DomainError):
            saga.submit("step", "other-idem", "external")
        saga.reconcile("step", SagaStepState.FINALIZED)
        with self.assertRaises(DomainError):
            saga.reconcile("step", SagaStepState.ACCEPTED)


class AdapterHardeningTests(unittest.TestCase):
    def capability(self, **changes: object) -> FeeRouteCapability:
        values: dict[str, object] = {
            "account_model": "EOA",
            "network": "eip155:42161",
            "token_asset_id": "JPYC-test",
            "provider_id": "provider",
            "terms_url": "https://offline.invalid/terms",
            "support_route": "ticket",
            "jurisdiction": "JP",
            "settlement_target": "settlement",
            "supports_zero_native_balance": True,
            "evidence_status": "VERIFIED",
            "evidence_expires_at": 2000,
            "revoked": False,
            "reviewed": True,
            "permit_bootstrap_without_gas": True,
            "failure_charge_cap": "1",
            "rate_limit_status": "HEALTHY",
            "liquidity_status": "HEALTHY",
        }
        values.update(changes)
        return FeeRouteCapability(**values)  # type: ignore[arg-type]

    def quote(self, capability: FeeRouteCapability, **changes: object) -> OperationBoundQuote:
        values: dict[str, object] = {
            "quote_id": "quote",
            "capability": capability,
            "account": "acct",
            "operation_id": "op",
            "amount": "500",
            "nonce": "nonce",
            "expiry": 1500,
            "estimated_fee": "0.1",
            "maximum_fee": "1",
            "failure_charge": "0.2",
            "signature": "signature",
            "signature_valid": True,
        }
        values.update(changes)
        return OperationBoundQuote(**values)  # type: ignore[arg-type]

    def test_fee_route_boolean_api_never_accepts_malformed_quote_or_unbound_plan(self) -> None:
        capability = self.capability()
        self.assertFalse(zero_native_balance_eligible(capability, self.quote(capability, amount="NaN"), now=1000))
        self.assertFalse(zero_native_balance_eligible(self.capability(reviewed=1), self.quote(capability), now=1000))
        plan = fee_readiness_plan(native_balance="0", capability=capability, quote=self.quote(capability), now=1000)
        self.assertEqual(plan["mode"], "MANUAL_FALLBACK")

    def test_fake_hyperliquid_rejects_idempotency_conflict_overfill_and_negative_age(self) -> None:
        adapter = FakeHyperliquidAdapter(testnet_write_enabled=True)
        account = adapter.read_account("acct")
        self.assertEqual(account["confirmationState"], "SIMULATED_ACCEPTED")
        self.assertFalse(account["confirmed"])
        adapter.place_order(account="acct", market_id="BTC-PERP", side="buy", amount="1", client_id="client")
        with self.assertRaises(DomainError):
            adapter.place_order(account="acct", market_id="BTC-PERP", side="buy", amount="2", client_id="client")
        with self.assertRaises(DomainError):
            adapter.apply_fill("client", "2", liquidation_price="100", reference_price_age_seconds=1)
        with self.assertRaises(DomainError):
            adapter.apply_fill("client", "0.5", liquidation_price="100", reference_price_age_seconds=-1)

    def test_jpyc_handoff_rejects_zero_unbounded_lifetime_and_tampered_fingerprint(self) -> None:
        with self.assertRaises(ValueError):
            prepare_handoff(handoff_id="handoff", amount="0", network="eip155:42161", address="address", now=1000, expires_at=1100)
        with self.assertRaises(ValueError):
            prepare_handoff(handoff_id="handoff", amount="1", network="eip155:42161", address="address", now=1000, expires_at=3001)
        valid = prepare_handoff(handoff_id="handoff", amount="1", network="eip155:42161", address="address", now=1000, expires_at=1100)
        tampered: JpycHandoff = replace(valid, address_fingerprint="BADFINGERPRINT")
        with self.assertRaises(ValueError):
            validate_return(tampered, now=1050, network="eip155:42161", address="address")


class SignerInterfaceHardeningTests(unittest.TestCase):
    def test_runtime_lease_must_be_current_and_bound_to_exact_release(self) -> None:
        _, _, capsule = fixtures()
        auth = AuthorizationEnvelope(
            "auth-interface", "device-1", "acct-1", capsule.hash, capsule.operation_type,
            1000, 1100, "nonce-interface", "review",
            proof("auth-interface", "device-1", "acct-1", capsule.hash, "nonce-interface"),
        )
        release = {
            "status": "PRODUCTION_OPERATIONAL_GO",
            "releaseEligibleForRuntimeActivation": True,
            "releaseSubjectSha256": "a" * 64,
        }
        runtime = {
            "leaseValid": True,
            "transactionAuthorizationGranted": False,
            "releaseSubjectSha256": "a" * 64,
            "leaseLifetimeSeconds": 100,
            "issuedAt": 1000,
            "expiresAt": 1100,
        }
        with tempfile.TemporaryDirectory() as directory:
            store = DurableAuthorizationStore(f"{directory}/auth.sqlite")
            signer = SignerInterface(store)
            with self.assertRaises(DomainError):
                signer.sign_if_all_gates_pass(capsule, auth, release=release, runtime={**runtime, "releaseSubjectSha256": "b" * 64}, now=1001)
            with self.assertRaises(DomainError):
                signer.sign_if_all_gates_pass(capsule, auth, release=release, runtime={**runtime, "expiresAt": 1301}, now=1001)
            signer.sign_if_all_gates_pass(capsule, auth, release=release, runtime=runtime, now=1001)
            store.close()


class LocalSandboxHardeningTests(unittest.TestCase):
    def test_router_hides_parser_details_and_rejects_query_context(self) -> None:
        app = LocalSandboxApp(ROOT)
        duplicate = app.route("POST", "/v1/draft", b'{"utterance":"a","utterance":"b"}', "application/json")
        payload = json.loads(duplicate.body)
        self.assertEqual(payload["error"]["message"], "入力を確認できません。")
        self.assertNotIn("duplicate", duplicate.body.decode("utf-8").lower())
        queried = app.route("GET", "/healthz?token=secret")
        self.assertEqual(queried.status, 400)

    def test_readiness_cannot_be_changed_to_go_inside_design_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "delivery").mkdir()
            report = {
                "status": "PRODUCTION_OPERATIONAL_GO",
                "productionWritePermitted": True,
                "releaseEligibleForRuntimeActivation": True,
                "summary": {"mandatoryGates": 37, "passedGates": 37, "requiredClaims": 93, "acceptedClaims": 93},
            }
            (root / "delivery/OPERATIONAL_READINESS_REPORT.json").write_text(json.dumps(report), encoding="utf-8")
            response = LocalSandboxApp(root).route("GET", "/readiness")
            self.assertEqual(response.status, 500)
            self.assertFalse(json.loads(response.body)["productionWritePermitted"])

    @staticmethod
    def raw_status(port: int, request: bytes) -> int:
        with socket.create_connection(("127.0.0.1", port), timeout=5) as connection:
            connection.sendall(request)
            response = connection.recv(4096)
        return int(response.split(b"\r\n", 1)[0].split()[1])

    def test_http_boundary_rejects_host_origin_and_transfer_encoding_and_sets_headers(self) -> None:
        server = create_server("127.0.0.1", 0, root=ROOT)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        thread.start()
        port = server.server_address[1]
        try:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request("GET", "/healthz")
            response = connection.getresponse()
            response.read()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.getheader("X-Frame-Options"), "DENY")
            self.assertEqual(response.getheader("Cross-Origin-Opener-Policy"), "same-origin")
            connection.close()

            invalid_host = b"GET /healthz HTTP/1.1\r\nHost: evil.example\r\nConnection: close\r\n\r\n"
            self.assertEqual(self.raw_status(port, invalid_host), 421)
            invalid_origin = (
                f"GET /healthz HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nOrigin: http://evil.example\r\nConnection: close\r\n\r\n"
            ).encode()
            self.assertEqual(self.raw_status(port, invalid_origin), 403)
            transfer_encoding = (
                f"POST /v1/draft HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nTransfer-Encoding: chunked\r\n"
                "Content-Type: application/json\r\nConnection: close\r\n\r\n0\r\n\r\n"
            ).encode()
            self.assertEqual(self.raw_status(port, transfer_encoding), 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
