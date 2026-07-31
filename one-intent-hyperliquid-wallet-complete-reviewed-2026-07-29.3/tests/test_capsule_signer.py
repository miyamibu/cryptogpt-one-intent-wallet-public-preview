from __future__ import annotations

import unittest
from tempfile import TemporaryDirectory

from shared.canonical import canonical_hash
from shared.domain import (
    ActionPlanDraft,
    AssetIdentity,
    AuthorizationEnvelope,
    CanonicalQuote,
    DomainError,
    DurableAuthorizationStore,
    ExecutionCapsule,
    SignedRegistry,
    SignerGate,
    compile_capsule,
    parse_intent_locally,
)


def proof(authorization_id: str, device_id: str, account: str, capsule_hash: str, nonce: str) -> str:
    return canonical_hash("dpop-proof-v1", {"authorizationId": authorization_id, "deviceId": device_id, "account": account, "capsuleHash": capsule_hash, "nonce": nonce})


def typed_resolutions(draft: ActionPlanDraft) -> dict[str, str]:
    values = {
        "ペイパチャルという語の意味": "PERPETUAL_ORDER",
        "生産価格という語の意味": "LIQUIDATION_PRICE",
        "方向": "LONG",
        "ネットワーク": "eip155:42161",
    }
    return {ambiguity: values[ambiguity] for ambiguity in draft.material_ambiguities}


def fixtures(now: int = 1000):
    draft = parse_intent_locally("BTCを500 USDC、ペイパチャルで3倍。生産価格も見せて。")
    draft = draft.confirm(typed_resolutions(draft), "BTCを500 USDCで先物取引（期限なし）。清算価格を表示。")
    registry = SignedRegistry(
        registry_id="registry-test-1", sequence=1, valid_from=900, expires_at=2000,
        signer_key_id="test-key", signature="test-signature", signature_valid=True,
        revoked=False,
        entries={"BTC-USDC": AssetIdentity("BTC-USDC", "eip155:42161", "contract-test", 8, "code-test", False)},
    )
    payload = {"marketId": "BTC-USDC-PERP", "side": "buy", "amount": "500"}
    payload_hash = canonical_hash("final-payload-v1", payload)
    temporary_quote = CanonicalQuote("quote-test", "provider-test", "route-test", "eip155:42161", "BTC-USDC", "acct-1", "500", "1", "ETH", "settlement-test", 950, 1500, "", payload_hash, "quote-signature", True)
    temporary_capsule = ExecutionCapsule("PERPETUAL_ORDER", "acct-1", "device-1", draft.intent_commitment, "eip155:42161", "BTC-USDC", "500", "address-1", ("place-order",), registry.digest, temporary_quote.quote_id, temporary_quote.digest, payload, 1400)
    quote = CanonicalQuote("quote-test", "provider-test", "route-test", "eip155:42161", "BTC-USDC", "acct-1", "500", "1", "ETH", "settlement-test", 950, 1500, temporary_capsule.hash, payload_hash, "quote-signature", True)
    live = {
        "operationType": "PERPETUAL_ORDER", "account": "acct-1", "deviceId": "device-1",
        "intentCommitment": draft.intent_commitment,
        "network": "eip155:42161", "assetId": "BTC-USDC", "amount": "500", "recipient": "address-1",
        "orderedActions": ["place-order"], "finalPayload": payload, "expiresAt": 1400,
    }
    capsule = compile_capsule(draft, live_state=live, registry=registry, quote=quote, now=now)
    return registry, quote, capsule


class CapsuleSignerTests(unittest.TestCase):
    def test_exact_quote_registry_and_payload_are_bound(self) -> None:
        _, _, capsule = fixtures()
        self.assertTrue(capsule.hash)
        self.assertEqual(capsule.asset_id, "BTC-USDC")

    def test_quote_substitution_changes_capsule_binding(self) -> None:
        registry, quote, capsule = fixtures()
        replacement = CanonicalQuote(**{**quote.__dict__, "provider_id": "other-provider", "execution_capsule_hash": quote.execution_capsule_hash})
        live = {
            "operationType": capsule.operation_type, "account": capsule.account, "deviceId": capsule.device_id,
            "intentCommitment": capsule.intent_commitment, "network": capsule.network, "assetId": capsule.asset_id,
            "amount": capsule.amount, "recipient": capsule.recipient, "orderedActions": list(capsule.ordered_actions),
            "finalPayload": dict(capsule.final_payload), "expiresAt": capsule.expires_at,
        }
        draft = parse_intent_locally("BTCを500 USDC、ペイパチャルで3倍。生産価格も見せて。").confirm(
            typed_resolutions(parse_intent_locally("BTCを500 USDC、ペイパチャルで3倍。生産価格も見せて。")), "確認"
        )
        with self.assertRaises(DomainError):
            compile_capsule(draft, live_state=live, registry=registry, quote=replacement, now=1000)

    def test_expired_quote_and_changed_amount_fail_closed(self) -> None:
        registry, quote, capsule = fixtures()
        altered_live = {
            "operationType": capsule.operation_type,
            "account": capsule.account,
            "deviceId": capsule.device_id,
            "intentCommitment": capsule.intent_commitment,
            "network": capsule.network,
            "assetId": capsule.asset_id,
            "amount": "501",
            "recipient": capsule.recipient,
            "orderedActions": list(capsule.ordered_actions),
            "finalPayload": dict(capsule.final_payload),
            "expiresAt": capsule.expires_at,
        }
        draft = parse_intent_locally("BTCを500 USDC、ペイパチャルで3倍。生産価格も見せて。")
        draft = draft.confirm(typed_resolutions(draft), "確認")
        with self.assertRaises(DomainError):
            compile_capsule(draft, live_state=altered_live, registry=registry, quote=quote, now=1000)
        expired = quote.__class__(**{**quote.__dict__, "expires_at": 1000})
        with self.assertRaises(DomainError):
            expired.verify(1000, network=expired.network, asset_id=expired.asset_id, account=expired.account, amount=expired.amount)

    def test_signer_requires_release_runtime_and_consumes_authorization(self) -> None:
        _, _, capsule = fixtures()
        auth = __import__("shared.domain", fromlist=["AuthorizationEnvelope"]).AuthorizationEnvelope("auth-1", "device-1", "acct-1", capsule.hash, capsule.operation_type, 1000, 1100, "nonce-1", "review", proof("auth-1", "device-1", "acct-1", capsule.hash, "nonce-1"))
        signer = SignerGate()
        with self.assertRaises(DomainError):
            signer.sign(capsule, auth, release_go=False, runtime_lease_valid=True, now=1001)
        signer.sign(capsule, auth, release_go=True, runtime_lease_valid=True, now=1001)
        with self.assertRaises(DomainError):
            signer.sign(capsule, auth, release_go=True, runtime_lease_valid=True, now=1001)

    def test_crash_after_sign_never_allows_second_signature(self) -> None:
        _, _, capsule = fixtures()
        auth = AuthorizationEnvelope("auth-crash", "device-1", "acct-1", capsule.hash, capsule.operation_type, 1000, 1100, "nonce-crash", "review", proof("auth-crash", "device-1", "acct-1", capsule.hash, "nonce-crash"))
        signer = SignerGate()
        with self.assertRaises(RuntimeError):
            signer.sign(capsule, auth, release_go=True, runtime_lease_valid=True, now=1001, fail_after_sign=True)
        self.assertEqual(signer.state.value, "SIGNED_BROADCAST_UNKNOWN")
        with self.assertRaises(DomainError):
            signer.sign(capsule, auth, release_go=True, runtime_lease_valid=True, now=1001)

    def test_durable_store_rejects_replay_after_signer_restart(self) -> None:
        _, _, capsule = fixtures()
        auth = AuthorizationEnvelope("auth-durable", "device-1", "acct-1", capsule.hash, capsule.operation_type, 1000, 1100, "nonce-durable", "review", proof("auth-durable", "device-1", "acct-1", capsule.hash, "nonce-durable"))
        with TemporaryDirectory() as directory:
            database = f"{directory}/authorization.sqlite"
            first = SignerGate(store=DurableAuthorizationStore(database), require_durable_store=True)
            first.sign(capsule, auth, release_go=True, runtime_lease_valid=True, now=1001)
            restarted = SignerGate(store=DurableAuthorizationStore(database), require_durable_store=True)
            with self.assertRaises(DomainError):
                restarted.sign(capsule, auth, release_go=True, runtime_lease_valid=True, now=1001)

    def test_durable_store_rejects_same_operation_after_reauthorization(self) -> None:
        _, _, capsule = fixtures()
        first = AuthorizationEnvelope("auth-op-a", "device-1", "acct-1", capsule.hash, capsule.operation_type, 1000, 1100, "nonce-op-a", "review", proof("auth-op-a", "device-1", "acct-1", capsule.hash, "nonce-op-a"))
        second = AuthorizationEnvelope("auth-op-b", "device-1", "acct-1", capsule.hash, capsule.operation_type, 1000, 1100, "nonce-op-b", "review", proof("auth-op-b", "device-1", "acct-1", capsule.hash, "nonce-op-b"))
        with TemporaryDirectory() as directory:
            database = f"{directory}/authorization.sqlite"
            initial = SignerGate(store=DurableAuthorizationStore(database), require_durable_store=True)
            initial.sign(capsule, first, release_go=True, runtime_lease_valid=True, now=1001)
            restarted = SignerGate(store=DurableAuthorizationStore(database), require_durable_store=True)
            with self.assertRaises(DomainError):
                restarted.sign(capsule, second, release_go=True, runtime_lease_valid=True, now=1001)
    def test_future_or_outliving_authorization_fails_closed(self) -> None:
        _, _, capsule = fixtures()
        future = AuthorizationEnvelope("auth-future", "device-1", "acct-1", capsule.hash, capsule.operation_type, 1010, 1100, "nonce-future", "review", proof("auth-future", "device-1", "acct-1", capsule.hash, "nonce-future"))
        with self.assertRaises(DomainError):
            future.validate(1001, capsule)
        outliving = AuthorizationEnvelope("auth-long", "device-1", "acct-1", capsule.hash, capsule.operation_type, 1390, 1450, "nonce-long", "review", proof("auth-long", "device-1", "acct-1", capsule.hash, "nonce-long"))
        with self.assertRaises(DomainError):
            outliving.validate(1391, capsule)

    def test_nonce_reuse_with_new_authorization_id_is_rejected(self) -> None:
        _, _, capsule = fixtures()
        first = AuthorizationEnvelope("auth-nonce-a", "device-1", "acct-1", capsule.hash, capsule.operation_type, 1000, 1100, "shared-nonce", "review", proof("auth-nonce-a", "device-1", "acct-1", capsule.hash, "shared-nonce"))
        second = AuthorizationEnvelope("auth-nonce-b", "device-1", "acct-1", capsule.hash, capsule.operation_type, 1000, 1100, "shared-nonce", "review", proof("auth-nonce-b", "device-1", "acct-1", capsule.hash, "shared-nonce"))
        signer = SignerGate()
        signer.sign(capsule, first, release_go=True, runtime_lease_valid=True, now=1001)
        signer.reconcile("confirmed")
        with self.assertRaises(DomainError):
            signer.sign(capsule, second, release_go=True, runtime_lease_valid=True, now=1001)

    def test_asset_prefix_substitution_is_rejected(self) -> None:
        registry, quote, capsule = fixtures()
        fake_asset = "BTCFAKE-USDC"
        fake_registry = SignedRegistry(
            registry_id=registry.registry_id, sequence=registry.sequence, valid_from=registry.valid_from, expires_at=registry.expires_at,
            signer_key_id=registry.signer_key_id, signature=registry.signature, signature_valid=True, revoked=False,
            entries={fake_asset: AssetIdentity(fake_asset, capsule.network, "contract-fake", 8, "code-fake", False)},
        )
        payload = dict(capsule.final_payload)
        fake_quote = CanonicalQuote(
            quote.quote_id, quote.provider_id, quote.route_id, quote.network, fake_asset, quote.account, quote.amount, quote.max_fee,
            quote.fee_asset, quote.settlement_target, quote.generated_at, quote.expires_at, quote.execution_capsule_hash,
            quote.final_payload_commitment, quote.signature, True,
        )
        live = {
            "operationType": capsule.operation_type, "account": capsule.account, "deviceId": capsule.device_id,
            "intentCommitment": capsule.intent_commitment, "network": capsule.network, "assetId": fake_asset,
            "amount": capsule.amount, "recipient": capsule.recipient, "orderedActions": list(capsule.ordered_actions),
            "finalPayload": payload, "expiresAt": capsule.expires_at,
        }
        draft = parse_intent_locally("BTCを500 USDC、ペイパチャルで3倍。生産価格も見せて。")
        draft = draft.confirm(typed_resolutions(draft), "確認")
        with self.assertRaises(DomainError):
            compile_capsule(draft, live_state=live, registry=fake_registry, quote=fake_quote, now=1000)
