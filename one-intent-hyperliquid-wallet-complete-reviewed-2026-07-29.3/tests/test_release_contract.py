"""Negative fixtures for the canonical release-contract checks."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from canonical_hashes import strict_load_json
from check_release_contract import check_canonical_traceability
from wallet_dependency import GATES_BY_WALLET_DEPENDENCY, validate_gate_partition, wallet_dependency_for_gate


class ReleaseContractNegativeTests(unittest.TestCase):
    def test_wallet_dependency_partition_covers_every_gate_once(self) -> None:
        config = strict_load_json(ROOT / "config/operational-readiness.json")
        gate_ids = {gate["gateId"] for gate in config["gates"]}
        validate_gate_partition(gate_ids)
        self.assertEqual(sum(len(gates) for gates in GATES_BY_WALLET_DEPENDENCY.values()), len(gate_ids))
        self.assertEqual(
            {wallet_dependency_for_gate(gate_id) for gate_id in gate_ids},
            set(GATES_BY_WALLET_DEPENDENCY),
        )

    def test_traceability_explicitly_never_requires_personal_wallet(self) -> None:
        trace = strict_load_json(ROOT / "delivery/external-blocker-traceability.json")
        coverage = trace["coverage"]
        self.assertFalse(coverage["personalWalletRequired"])
        self.assertTrue(all(not entry["personalWalletRequired"] for entry in coverage["gates"]))
        self.assertTrue(all(not entry["personalWalletRequired"] for entry in coverage["claims"]))

    def test_runtime_activation_report_rejects_extra_fields(self) -> None:
        schema = strict_load_json(ROOT / "schemas/runtime-activation-report.schema.json")
        report = strict_load_json(ROOT / "delivery/RUNTIME_ACTIVATION_REPORT.json")
        report["operationallyReady"] = True
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(report))
        self.assertTrue(errors, "runtime report must reject unreviewed extra claims")

    def test_release_subject_is_exactly_bound_to_index(self) -> None:
        subject = strict_load_json(ROOT / "release/release-subject.json")
        index = strict_load_json(ROOT / "delivery/evidence-index.json")
        tampered = copy.deepcopy(index["releaseSubject"])
        tampered["releaseId"] = "tampered-release-subject"
        self.assertNotEqual(subject, tampered)

    def test_traceability_rejects_claim_parent_gate_drift(self) -> None:
        config = strict_load_json(ROOT / "config/operational-readiness.json")
        trace = strict_load_json(ROOT / "delivery/external-blocker-traceability.json")
        tampered = copy.deepcopy(trace)
        tampered["blockers"][0]["directGateIds"] = ["RUNTIME_ACTIVATION"]
        errors = check_canonical_traceability(
            config_value=config,
            trace_value=tampered,
            document_text="\n".join(f"## {item['id']}" for item in trace["blockers"]),
        )
        self.assertTrue(errors, "claim-to-parent-gate drift must fail closed")

    def test_traceability_rejects_duplicate_gate_coverage_id(self) -> None:
        config = strict_load_json(ROOT / "config/operational-readiness.json")
        trace = strict_load_json(ROOT / "delivery/external-blocker-traceability.json")
        tampered = copy.deepcopy(trace)
        tampered["coverage"]["gates"].append(copy.deepcopy(tampered["coverage"]["gates"][0]))
        document = (ROOT / "delivery/EXTERNAL_BLOCKERS.md").read_text(encoding="utf-8")
        errors = check_canonical_traceability(config_value=config, trace_value=tampered, document_text=document)
        self.assertTrue(errors, "duplicate gate coverage IDs must fail closed")

    def test_traceability_rejects_duplicate_claim_coverage_id(self) -> None:
        config = strict_load_json(ROOT / "config/operational-readiness.json")
        trace = strict_load_json(ROOT / "delivery/external-blocker-traceability.json")
        tampered = copy.deepcopy(trace)
        tampered["coverage"]["claims"].append(copy.deepcopy(tampered["coverage"]["claims"][0]))
        document = (ROOT / "delivery/EXTERNAL_BLOCKERS.md").read_text(encoding="utf-8")
        errors = check_canonical_traceability(config_value=config, trace_value=tampered, document_text=document)
        self.assertTrue(errors, "duplicate claim coverage IDs must fail closed")


if __name__ == "__main__":
    unittest.main()
