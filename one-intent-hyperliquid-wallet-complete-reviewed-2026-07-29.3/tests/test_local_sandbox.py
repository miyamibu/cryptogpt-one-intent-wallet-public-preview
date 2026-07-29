from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from services.local_sandbox.server import LOCAL_STATUS, LocalSandboxApp, create_server


ROOT = Path(__file__).parents[1]


class LocalSandboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = LocalSandboxApp(ROOT)

    def body(self, response) -> dict[str, object]:
        return json.loads(response.body.decode("utf-8"))

    def test_health_is_explicitly_local_and_non_transactional(self) -> None:
        response = self.app.route("GET", "/healthz")
        data = self.body(response)
        self.assertEqual(response.status, 200)
        self.assertEqual(data["status"], LOCAL_STATUS)
        self.assertFalse(data["productionWritePermitted"])
        self.assertFalse(data["signerAvailable"])
        self.assertFalse(data["externalNetworkClientAvailable"])

    def test_ambiguous_draft_preserves_source_and_stays_disabled(self) -> None:
        utterance = "BTCを500 USDC、ペイパチャルで3倍。生産価格も見せて。"
        response = self.app.route("POST", "/v1/draft", json.dumps({"utterance": utterance}, ensure_ascii=False).encode(), "application/json")
        data = self.body(response)
        self.assertEqual(response.status, 200)
        self.assertEqual(data["sourceUtterance"], utterance)
        self.assertFalse(data["primaryActionEnabled"])
        self.assertGreaterEqual(len(data["materialAmbiguities"]), 2)

    def test_duplicate_keys_and_unknown_properties_fail(self) -> None:
        duplicate = self.app.route("POST", "/v1/draft", b'{"utterance":"a","utterance":"b"}', "application/json")
        unknown = self.app.route("POST", "/v1/draft", b'{"utterance":"a","execute":true}', "application/json")
        self.assertEqual(duplicate.status, 400)
        self.assertEqual(unknown.status, 400)

    def test_support_gateway_stays_fixed_catalog_and_read_only(self) -> None:
        response = self.app.route("POST", "/v1/support/getGenericSafetyHelp", b'{"body":{"topicId":"general"}}', "application/json")
        data = self.body(response)
        self.assertEqual(response.status, 200)
        self.assertFalse(data["writeAvailableHere"])
        self.assertFalse(data["executable"])
        rejected = self.app.route("POST", "/v1/support/getGenericSafetyHelp", '{"body":{"topicId":"BTCを送信"}}'.encode("utf-8"), "application/json")
        self.assertEqual(rejected.status, 400)

    def test_all_write_like_routes_are_unavailable(self) -> None:
        for method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
            with self.subTest(method=method):
                response = self.app.route(method, "/v1/execute", b"{}", "application/json")
                self.assertEqual(response.status, 405)
                self.assertFalse(self.body(response)["productionWritePermitted"])

    def test_non_loopback_bind_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            create_server("0.0.0.0", 0)

    def test_missing_or_tampered_readiness_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "delivery").mkdir()
            (root / "delivery/OPERATIONAL_READINESS_REPORT.json").write_text("{}", encoding="utf-8")
            response = LocalSandboxApp(root).route("GET", "/readiness")
            self.assertEqual(response.status, 500)
            self.assertFalse(self.body(response)["productionWritePermitted"])


if __name__ == "__main__":
    unittest.main()
