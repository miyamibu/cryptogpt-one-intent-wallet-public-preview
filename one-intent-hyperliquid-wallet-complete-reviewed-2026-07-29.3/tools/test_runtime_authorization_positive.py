#!/usr/bin/env python3
"""Prove the runtime contract has one reachable, synthetic, fail-closed positive path."""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True

from runtime_authorization_test_fixture import RuntimeFixture


def main() -> int:
    with RuntimeFixture.create() as fixture:
        result = fixture.evaluate()
        failures: list[str] = []
        if result.errors:
            failures.extend(result.errors)
        report = result.report
        if report.get("status") != "ELIGIBLE_FOR_ATOMIC_SIGNER_FINALIZATION":
            failures.append(f"unexpected runtime status: {report.get('status')!r}")
        if report.get("eligibleForAtomicSignerFinalization") is not True:
            failures.append("positive fixture did not reach atomic signer finalization eligibility")
        if report.get("transactionAuthorizationGranted") is not False:
            failures.append("reference runtime evaluator must never grant transaction authorization")
        if report.get("authorizationId") != fixture.docs["operation"]["authorizationId"]:
            failures.append("decision is not bound to the exact operation authorization ID")
        if report.get("nonce") != fixture.docs["operation"]["nonce"]:
            failures.append("decision is not bound to the exact one-time nonce")
        if report.get("requiredCapabilities") != ["PERP_TRADE"]:
            failures.append("derived capability set is incorrect")
        expected_inputs = {
            "operationalTrustPolicySha256": fixture.digest("trust"),
            "runtimeAuthorizationPolicySha256": fixture.digest("runtime_policy"),
            "releaseReadinessReportSha256": fixture.digest("readiness"),
            "trustedTimeAttestationSha256": fixture.digest("trusted_time"),
            "trustedTimeSequence": fixture.docs["trusted_time"]["sequence"],
            "evidenceIndexSequence": fixture.docs["readiness"]["decisionInputs"]["evidenceIndexSequence"],
            "accountAuthorizationBindingSha256": fixture.digest("binding"),
            "runtimeStateBundleSha256": fixture.digest("state"),
            "runtimeLeaseSha256": fixture.digest("lease"),
            "operationAuthorizationSha256": fixture.digest("operation"),
            "executionCapsuleSha256": fixture.digest("capsule"),
        }
        for field, expected in expected_inputs.items():
            if report.get("decisionInputs", {}).get(field) != expected:
                failures.append(f"decision input hash mismatch: {field}")
        if failures:
            print("SYNTHETIC RUNTIME AUTHORIZATION POSITIVE TEST FAILED")
            for item in failures:
                print(f"- {item}")
            return 1
    print("SYNTHETIC RUNTIME AUTHORIZATION POSITIVE TEST PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
