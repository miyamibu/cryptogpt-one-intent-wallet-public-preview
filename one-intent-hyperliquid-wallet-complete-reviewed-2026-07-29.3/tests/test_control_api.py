from __future__ import annotations

import unittest

from services.control_api.control import ControlApi
from shared.domain import DomainError, ExecutionCapsule, PolicyDecision


class ControlApiTests(unittest.TestCase):
    def test_write_requires_all_three_gate_inputs(self) -> None:
        capsule = ExecutionCapsule("REFERENCE", "acct", "device", "intent", "eip155:0", "asset", "1", None, ("reference",), "registry", "quote", "quote-digest", {}, 2000)
        api = ControlApi(write_enabled=True)
        with self.assertRaises(DomainError):
            api.execute(capsule, now=1000)

    def test_expired_capsule_is_not_accepted_even_when_flag_is_enabled(self) -> None:
        capsule = ExecutionCapsule("REFERENCE", "acct", "device", "intent", "eip155:0", "asset", "1", None, ("reference",), "registry", "quote", "quote-digest", {}, 1000)
        api = ControlApi(write_enabled=True)
        with self.assertRaises(DomainError):
            api.execute(capsule, authorization=None, policy_decision=PolicyDecision(True, "OK", "ok"), release={"status": "PRODUCTION_OPERATIONAL_GO"}, runtime={"leaseValid": True, "leaseLifetimeSeconds": 1}, now=1000)
