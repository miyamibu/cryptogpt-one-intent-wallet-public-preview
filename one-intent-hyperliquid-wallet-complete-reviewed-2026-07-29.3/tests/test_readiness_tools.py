from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class ReadinessToolTests(unittest.TestCase):
    def test_model_has_exact_gate_and_claim_counts_and_is_blocked(self) -> None:
        data = json.loads((ROOT / "config/operational-readiness.json").read_text(encoding="utf-8"))
        gates = data["gates"]
        claims = [claim for gate in gates for claim in gate["claims"]]
        self.assertEqual(len(gates), 37)
        self.assertEqual(len(claims), 93)
        self.assertTrue(all(gate["mandatory"] is True for gate in gates))
        self.assertEqual(data["globalRules"]["currentPackageExpectedStatus"], "BLOCKED_NOT_OPERATIONAL")
        self.assertEqual(data["globalRules"]["productionGoStatus"], "PRODUCTION_OPERATIONAL_GO")

    def test_checker_accepts_the_expected_blocked_design_state(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", "tools/check_operational_readiness.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OPERATIONAL READINESS CHECK PASSED", result.stdout)
        self.assertIn("BLOCKED_NOT_OPERATIONAL", result.stdout)
        self.assertIn("Production writes remain prohibited", result.stdout)

    def test_require_go_fails_closed_without_protected_production_inputs(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", "tools/check_operational_readiness.py", "--require-go"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("OPERATIONAL READINESS CHECK FAILED", result.stdout)
        self.assertIn("BLOCKED_NOT_OPERATIONAL", result.stdout)
        self.assertIn("missing protected out-of-band anchor", result.stdout)
        self.assertIn("production trust policy is not enabled", result.stdout)


if __name__ == "__main__":
    unittest.main()
