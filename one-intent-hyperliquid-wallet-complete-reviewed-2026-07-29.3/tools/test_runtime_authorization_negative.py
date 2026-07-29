#!/usr/bin/env python3
"""Adversarial fail-closed tests for runtime authorization and replay boundaries."""
from __future__ import annotations

import base64
import copy
import datetime as dt
import os
import sys
from typing import Callable

sys.dont_write_bytecode = True
from canonical_hashes import canonical_json
from operational_readiness import format_time
from runtime_authorization import (
    account_binding_payload,
    operation_authorization_payload,
    runtime_lease_payload,
    runtime_state_payload,
)
from runtime_authorization_test_fixture import RuntimeFixture


Mutation = Callable[[RuntimeFixture], None]


def block_case(name: str, mutation: Mutation, *, refresh_anchors: bool = False, eval_kwargs: dict | None = None) -> str | None:
    with RuntimeFixture.create() as fixture:
        mutation(fixture)
        if refresh_anchors:
            fixture.install_anchors()
        result = fixture.evaluate(**(eval_kwargs or {}))
        if result.report.get("transactionAuthorizationGranted") is not False:
            return f"{name}: evaluator granted transaction authorization"
        if result.report.get("eligibleForAtomicSignerFinalization") is True or result.report.get("status") != "BLOCKED":
            return f"{name}: mutation did not fail closed"
        if not result.errors:
            return f"{name}: blocked without a machine-visible error"
    return None


def main() -> int:
    failures: list[str] = []
    assertions = 0

    # Design defaults must stay blocked without protected anchors.
    saved = {name: os.environ.pop(name, None) for name in list(os.environ) if name.startswith("ONE_INTENT_")}
    try:
        from package_metadata import ROOT
        from runtime_authorization import evaluate_runtime_authorization
        result = evaluate_runtime_authorization(
            trust_policy_path=ROOT / "config/operational-trust-policy.template.json",
            runtime_policy_path=ROOT / "config/runtime-authorization-policy.template.json",
            readiness_report_path=ROOT / "delivery/OPERATIONAL_READINESS_REPORT.json",
            trusted_time_path=ROOT / "examples/trusted-time-attestation-untrusted.json",
            account_binding_path=ROOT / "examples/account-authorization-binding-suspended.json",
            runtime_state_path=ROOT / "examples/runtime-state-bundle-stopped.json",
            runtime_lease_path=ROOT / "examples/runtime-control-plane-lease-disabled.json",
            operation_authorization_path=ROOT / "examples/per-operation-authorization-denied.json",
            execution_capsule_path=ROOT / "examples/execution-capsule-perp.json",
        )
        assertions += 1
        if result.report.get("status") != "BLOCKED" or result.report.get("transactionAuthorizationGranted") is not False:
            failures.append("design defaults are not safely blocked")
    finally:
        os.environ.update({k: v for k, v in saved.items() if v is not None})

    cases: list[tuple[str, Mutation, bool, dict | None]] = []

    def case(name: str, mutation: Mutation, refresh: bool = False, kwargs: dict | None = None) -> None:
        cases.append((name, mutation, refresh, kwargs))

    case("missing authorizer anchor", lambda f: os.environ.pop("ONE_INTENT_RUNTIME_AUTHORIZER_SHA256", None))
    case("expired readiness", lambda f: (f.docs["readiness"].__setitem__("validUntil", format_time(f.now - dt.timedelta(seconds=1))), f.write("readiness")), True)
    case("readiness direct-write claim", lambda f: (f.docs["readiness"].__setitem__("productionWritePermitted", True), f.write("readiness")), True)
    case("readiness summary forgery", lambda f: (f.docs["readiness"]["summary"].__setitem__("acceptedClaims", 92), f.write("readiness")), True)
    case("readiness gate blocked", lambda f: (f.docs["readiness"]["gates"][0].__setitem__("status", "BLOCKED"), f.write("readiness")), True)
    case("readiness trusted-time sequence mismatch", lambda f: (f.docs["readiness"]["decisionInputs"].__setitem__("trustedTimeSequence", 2), f.write("readiness")), True)
    case("release subject mismatch", lambda f: (f.docs["state"]["releaseSubject"].__setitem__("sourceCommit", "f" * 40), f.resign_runtime_document("state")))
    case("kill switch", lambda f: (f.docs["state"].__setitem__("killSwitch", True), f.resign_runtime_document("state")))
    case("writes disabled", lambda f: (f.docs["state"].__setitem__("writesEnabled", False), f.resign_runtime_document("state")))
    case("reconciliation mismatch", lambda f: (f.docs["state"].__setitem__("reconciliationState", "MISMATCH"), f.resign_runtime_document("state")))
    case("provider degraded", lambda f: (f.docs["state"].__setitem__("providerHealthState", "DEGRADED"), f.resign_runtime_document("state")))
    case("trusted-time rollback", lambda f: None, False, {"min_time": 1})
    case("evidence-index rollback", lambda f: None, False, {"min_index": 1})
    case("state rollback", lambda f: None, False, {"min_state": 1})
    case("binding rollback", lambda f: None, False, {"min_binding": 1})
    case("lease rollback", lambda f: None, False, {"min_lease": 1})
    case("tampered state signature", lambda f: (f.docs["state"]["signatures"][0].__setitem__("signatureBase64", base64.b64encode(b"X" * 64).decode("ascii")), f.write("state")))
    case("lease outlives state", lambda f: (f.docs["lease"].__setitem__("expiresAt", format_time(f.now + dt.timedelta(seconds=100))), f.resign_runtime_document("lease")))
    case("lease claims transaction auth", lambda f: (f.docs["lease"].__setitem__("transactionAuthorizationGranted", True), f.resign_runtime_document("lease")))
    case("lease capability missing", lambda f: (f.docs["lease"].__setitem__("capabilities", ["SPOT_TRADE"]), f.resign_runtime_document("lease")))
    case("binding suspended", lambda f: (f.docs["binding"].__setitem__("status", "SUSPENDED"), f.resign_runtime_document("binding")))
    case("registry digest mismatch", lambda f: (f.docs["binding"].__setitem__("registrySha256", "0" * 64), f.resign_runtime_document("binding")))
    case("same user/device key", lambda f: (f.docs["binding"].__setitem__("deviceKey", copy.deepcopy(f.docs["binding"]["userKey"])), f.resign_runtime_document("binding")))
    case("zero device attestation", lambda f: (f.docs["binding"].__setitem__("deviceAttestationSha256", "0" * 64), f.resign_runtime_document("binding")))
    case("capsule hash mismatch", lambda f: (f.docs["operation"].__setitem__("executionCapsuleHash", "0x" + "0" * 64), f.resign_operation()))
    case("source state mismatch", lambda f: (f.docs["operation"].__setitem__("sourceStateHash", "0x" + "0" * 64), f.resign_operation()))
    case("stale capsule evidence", lambda f: (f.docs["capsule"]["stateEvidence"].__setitem__("observedAt", format_time(f.now - dt.timedelta(minutes=10))), f.refresh_operation_hashes()))
    case("required capability mismatch", lambda f: (f.docs["operation"].__setitem__("requiredCapabilities", ["SPOT_TRADE"]), f.resign_operation()))
    case("missing quote hash", lambda f: (f.docs["operation"].__setitem__("quoteHash", None), f.resign_operation()))
    case("expired quote", lambda f: (f.docs["operation"].__setitem__("quoteValidUntil", format_time(f.now - dt.timedelta(seconds=1))), f.resign_operation()))
    case("expired operation", lambda f: (f.docs["operation"].__setitem__("expiresAt", format_time(f.now - dt.timedelta(seconds=1))), f.resign_operation()))
    case("reused authorization ID", lambda f: None, False, {"consumed_authorization_ids": frozenset({"OPERATION-AUTH-SYNTHETIC-001"})})
    case("reused nonce", lambda f: None, False, {"consumed_nonces": frozenset({"NONCE-RUNTIME-SYNTHETIC-0001"})})
    case("tampered user signature", lambda f: (f.docs["operation"]["userAuthorization"].__setitem__("signatureBase64", base64.b64encode(b"U" * 64).decode("ascii")), f.write("operation")))
    case("tampered device signature", lambda f: (f.docs["operation"]["deviceAuthorization"].__setitem__("signatureBase64", base64.b64encode(b"D" * 64).decode("ascii")), f.write("operation")))
    case("tampered policy signature", lambda f: (f.docs["operation"]["policyAuthorization"].__setitem__("signatureBase64", base64.b64encode(b"P" * 64).decode("ascii")), f.write("operation")))
    case("cross-document signature replay", lambda f: (f.docs["lease"].__setitem__("signatures", copy.deepcopy(f.docs["binding"]["signatures"])), f.write("lease")))
    case("operation not single use", lambda f: (f.docs["operation"].__setitem__("oneTimeUse", False), f.resign_operation()))
    case("operation denied", lambda f: (f.docs["operation"].__setitem__("authorized", False), f.resign_operation()))
    case("operation account changed", lambda f: (f.docs["operation"].__setitem__("account", "0x2222222222222222222222222222222222222222"), f.resign_operation()))
    case("operation runtime bundle changed", lambda f: (f.docs["operation"].__setitem__("runtimeBundleId", "RUNTIME-BUNDLE-OTHER-001"), f.resign_operation()))
    case("malformed nonce", lambda f: (f.docs["operation"].__setitem__("nonce", "EXAMPLE-ONLY"), f.resign_operation()))
    case("capsule presentation downgraded", lambda f: (f.docs["capsule"]["authorizationPresentation"].__setitem__("assurance", "APP_RENDER_ONLY"), f.refresh_operation_hashes()))
    case("capsule environment testnet", lambda f: (f.docs["capsule"].__setitem__("environment", "TESTNET"), f.refresh_operation_hashes()))
    case("unapproved source network", lambda f: (f.docs["capsule"]["networkContext"].__setitem__("sourceNetworkId", "eip155:1"), f.refresh_operation_hashes()))
    case("network registry mismatch", lambda f: (f.docs["capsule"]["networkContext"].__setitem__("networkRegistrySha256", "3" * 64), f.refresh_operation_hashes()))
    case("unapproved destination network", lambda f: (f.docs["capsule"]["networkContext"].__setitem__("destinationNetworkIds", ["eip155:137"]), f.refresh_operation_hashes()))
    case("capsule derived hash tampered", lambda f: (f.docs["capsule"].__setitem__("semanticHash", "0x" + "0" * 64), f.write("capsule"), f.docs["operation"].__setitem__("executionCapsuleHash", __import__('canonical_hashes').domain_hash("ONE_INTENT_EXECUTION_CAPSULE_AUTHORIZATION_V1", f.docs["capsule"])), f.resign_operation()))

    for name, mutation, refresh, kwargs in cases:
        assertions += 1
        error = block_case(name, mutation, refresh_anchors=refresh, eval_kwargs=kwargs)
        if error:
            failures.append(error)

    # Canonicalizer must reject lone surrogates rather than producing cross-language ambiguity.
    assertions += 1
    try:
        canonical_json({"value": "\ud800"})
        failures.append("lone Unicode surrogate was accepted by canonical JSON")
    except Exception:
        pass

    if failures:
        print("RUNTIME AUTHORIZATION NEGATIVE TEST FAILED")
        for item in failures:
            print(f"- {item}")
        print(f"Assertions: {assertions}")
        return 1
    print("RUNTIME AUTHORIZATION NEGATIVE TEST PASSED")
    print(f"Assertions: {assertions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
