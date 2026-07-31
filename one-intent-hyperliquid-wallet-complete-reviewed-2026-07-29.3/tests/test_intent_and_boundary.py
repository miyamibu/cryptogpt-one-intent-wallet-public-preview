from __future__ import annotations

import unittest

from shared.domain import DomainError, parse_intent_locally
from services.nontransactional_support_gateway.gateway import BoundaryViolation, handle, handle_json


SAMPLE = "BTCを500 USDC、ペイパチャルで3倍。生産価格も見せて。"


class IntentBoundaryTests(unittest.TestCase):
    def test_voice_regression_preserves_source_and_disables_action(self) -> None:
        draft = parse_intent_locally(SAMPLE)
        self.assertEqual(draft.source_utterance, SAMPLE)
        self.assertFalse(draft.executable)
        self.assertIn("ペイパチャルという語の意味", draft.material_ambiguities)
        self.assertIn("生産価格という語の意味", draft.material_ambiguities)
        self.assertNotIn("stopLoss", draft.proposed)

    def test_ambiguous_draft_cannot_be_confirmed_with_missing_resolution(self) -> None:
        draft = parse_intent_locally(SAMPLE)
        with self.assertRaises(DomainError):
            draft.confirm(set(), "候補")

    def test_typed_resolution_is_applied_and_draft_is_deeply_immutable(self) -> None:
        nested = {"route": {"steps": ["one"]}}
        draft = __import__("shared.domain", fromlist=["ActionPlanDraft"]).ActionPlanDraft(
            "source", "candidate", nested, (), False
        )
        nested["route"]["steps"].append("two")
        self.assertEqual(draft.proposed["route"]["steps"], ("one",))
        parsed = parse_intent_locally(SAMPLE)
        resolutions = {
            "ペイパチャルという語の意味": "PERPETUAL_ORDER",
            "生産価格という語の意味": "LIQUIDATION_PRICE",
            "方向": "LONG",
            "ネットワーク": "eip155:42161",
        }
        confirmed = parsed.confirm(resolutions, "確認")
        self.assertEqual(confirmed.proposed["positionSide"], "LONG")
        self.assertEqual(confirmed.proposed["network"], "eip155:42161")

    def test_chatgpt_surface_has_exact_four_read_only_operations(self) -> None:
        request = {"path": {"termId": "execution-capsule"}}
        response = handle("getPlainJapaneseTerm", request)
        self.assertEqual(response["termId"], "execution-capsule")
        self.assertEqual(set(response), {"termId", "labelJa", "explanationJa"})

    def test_chatgpt_rejects_transaction_context_in_all_locations(self) -> None:
        for location in ("body", "query", "path", "headers", "metadata", "toolContext"):
            request = {location: {"termId": "send transaction"}}
            with self.subTest(location=location), self.assertRaises(BoundaryViolation):
                handle("getPlainJapaneseTerm", request)

    def test_chatgpt_rejects_unknown_properties_and_write_operation(self) -> None:
        with self.assertRaises(BoundaryViolation):
            handle("getPlainJapaneseTerm", {"path": {"termId": "execution-capsule", "extra": "x"}})
        with self.assertRaises(BoundaryViolation):
            handle("execute", {"body": {"termId": "execution_capsule"}})

    def test_chatgpt_json_duplicate_keys_fail_before_routing(self) -> None:
        with self.assertRaises(BoundaryViolation):
            handle_json("getPlainJapaneseTerm", '{"path":{"termId":"execution-capsule","termId":"reconciliation"}}')

    def test_chatgpt_rejects_benign_query_or_header_context_too(self) -> None:
        with self.assertRaises(BoundaryViolation):
            handle("getPlainJapaneseTerm", {"path": {"termId": "execution-capsule"}, "query": {"termId": "execution-capsule"}})

    def test_gateway_shapes_match_read_only_openapi(self) -> None:
        status = handle("getReadOnlyStatus", {"path": {"referenceId": "status-ref-1234"}})
        self.assertEqual(status["status"], "INFORMATION_ONLY")
        self.assertFalse(status["writeAvailableHere"])
        safety = handle("getGenericSafetyHelp", {"body": {"topic": "CONTACT_SUPPORT", "locale": "ja-JP"}})
        self.assertFalse(safety["executable"])
        self.assertEqual(safety["catalogEntryId"], "CONTACT_SUPPORT")
