from __future__ import annotations

import unittest

from adapters.fee_route.fee import FeeRouteCapability, OperationBoundQuote, ReimbursementLedger, fee_readiness_plan, zero_native_balance_eligible
from adapters.hyperliquid.fake_adapter import FakeHyperliquidAdapter
from adapters.jpyc_ex_handoff.adapter import prepare_handoff, reconcile_return, validate_return
from shared.domain import DomainError


class FeeJpycHyperliquidTests(unittest.TestCase):
    def capability(self, **changes):
        values = dict(account_model="EOA", network="eip155:42161", token_asset_id="JPYC-test", provider_id="provider", terms_url="https://offline.invalid/terms", support_route="ticket", jurisdiction="JP", settlement_target="settlement", supports_zero_native_balance=True, evidence_status="VERIFIED", evidence_expires_at=2000, revoked=False, reviewed=True, permit_bootstrap_without_gas=True, failure_charge_cap="1", rate_limit_status="HEALTHY", liquidity_status="HEALTHY")
        values.update(changes)
        return FeeRouteCapability(**values)

    def quote(self, capability):
        return OperationBoundQuote("fee-quote", capability, "acct", "op", "500", "nonce", 1500, "0.1", "1", "0.2", "quote-signature", True)

    def test_zero_native_route_requires_all_conditions(self) -> None:
        capability = self.capability()
        quote = self.quote(capability)
        self.assertTrue(zero_native_balance_eligible(capability, quote, now=1000))
        self.assertFalse(zero_native_balance_eligible(self.capability(revoked=True), quote, now=1000))
        self.assertEqual(fee_readiness_plan(native_balance="0", capability=capability, quote=quote, now=1000, expected_account="acct", expected_operation_id="op", expected_amount="500")["mode"], "VERIFIED_OPERATION_BOUND_ROUTE")
        self.assertEqual(fee_readiness_plan(native_balance="0.0", capability=capability, quote=quote, now=1000, expected_account="acct", expected_operation_id="op", expected_amount="500")["mode"], "VERIFIED_OPERATION_BOUND_ROUTE")
        self.assertEqual(fee_readiness_plan(native_balance="0", capability=capability, quote=quote, now=1000, expected_amount="501")["mode"], "MANUAL_FALLBACK")
        self.assertEqual(fee_readiness_plan(native_balance="0", capability=self.capability(evidence_status="MONITOR"), quote=quote, now=1000)["mode"], "MANUAL_FALLBACK")
        self.assertFalse(zero_native_balance_eligible(capability, quote.__class__(**{**quote.__dict__, "capability": self.capability(provider_id="other")}), now=1000))
        self.assertFalse(zero_native_balance_eligible(capability, quote.__class__(**{**quote.__dict__, "expiry": 1000}), now=1000))

    def test_fee_terms_url_rejects_authority_tricks_and_query_context(self) -> None:
        capability = self.capability()
        quote = self.quote(capability)
        for url in (
            "https://user:[REDACTED_EMAIL]/terms",
            "https://offline.invalid/terms?redirect=https://evil.invalid",
            "https://offline.invalid/terms#fragment",
            "https://offline.invalid:444/terms",
        ):
            with self.subTest(url=url):
                invalid = FeeRouteCapability(**{**capability.__dict__, "terms_url": url})
                self.assertFalse(zero_native_balance_eligible(invalid, quote, now=1000))

    def test_failed_action_charge_is_capped_and_reimbursement_is_idempotent(self) -> None:
        capability = self.capability(failure_charge_cap="0.1")
        quote = self.quote(capability)
        too_expensive = quote.__class__(**{**quote.__dict__, "failure_charge": "0.2"})
        self.assertFalse(zero_native_balance_eligible(capability, too_expensive, now=1000))
        ledger = ReimbursementLedger(set(), set())
        self.assertTrue(ledger.charge_once("op-1"))
        self.assertFalse(ledger.charge_once("op-1"))
        self.assertTrue(ledger.reimburse_once("op-1"))
        self.assertFalse(ledger.reimburse_once("op-1"))

    def test_jpyc_handoff_expiry_and_changed_address_stop(self) -> None:
        handoff = prepare_handoff(handoff_id="h1", amount="100", network="eip155:42161", address="address-1", now=1000, expires_at=1100)
        validate_return(handoff, now=1050, network="eip155:42161", address="address-1")
        with self.assertRaises(ValueError):
            validate_return(handoff, now=1050, network="eip155:42161", address="address-2")
        self.assertEqual(reconcile_return(on_chain_receipt=True, application_state="pending"), "PARTIAL_RECONCILIATION_REQUIRED")

    def test_jpyc_handoff_requires_caip2_network_identity(self) -> None:
        with self.assertRaises(ValueError):
            prepare_handoff(handoff_id="h1", amount="1", network="mainnet", address="address-1", now=1000, expires_at=1100)

    def test_fake_hyperliquid_write_gate_and_stale_liquidation_stop(self) -> None:
        adapter = FakeHyperliquidAdapter()
        with self.assertRaises(DomainError):
            adapter.place_order(account="acct", market_id="BTC-PERP", side="buy", amount="1", client_id="c1")
        adapter = FakeHyperliquidAdapter(testnet_write_enabled=True)
        order = adapter.place_order(account="acct", market_id="BTC-PERP", side="buy", amount="1", client_id="c1")
        adapter.place_order(account="other", market_id="BTC-PERP", side="sell", amount="1", client_id="c2")
        self.assertEqual(adapter.read_account("acct")["orders"], ["c1"])
        adapter.apply_fill(order.client_id, "0.5", liquidation_price="100", reference_price_age_seconds=20)
        with self.assertRaises(DomainError):
            adapter.validate_perpetual_review(order.client_id)
        adapter.cancel_all()
        self.assertEqual(adapter.orders["c1"].state, "SIMULATED_CANCELLED")
