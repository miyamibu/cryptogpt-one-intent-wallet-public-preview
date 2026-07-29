#!/usr/bin/env python3
"""Evaluate runtime eligibility without ever signing or broadcasting a transaction."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from package_metadata import ROOT
from runtime_authorization import evaluate_runtime_authorization, runtime_authorizer_bundle_hash
from canonical_hashes import strict_load_json


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--trust-policy", type=Path, default=ROOT / "config/operational-trust-policy.template.json")
    value.add_argument("--runtime-policy", type=Path, default=ROOT / "config/runtime-authorization-policy.template.json")
    value.add_argument("--readiness-report", type=Path, default=ROOT / "delivery/OPERATIONAL_READINESS_REPORT.json")
    value.add_argument("--trusted-time", type=Path, default=ROOT / "examples/trusted-time-attestation-untrusted.json")
    value.add_argument("--account-binding", type=Path, default=ROOT / "examples/account-authorization-binding-suspended.json")
    value.add_argument("--runtime-state", type=Path, default=ROOT / "examples/runtime-state-bundle-stopped.json")
    value.add_argument("--runtime-lease", type=Path, default=ROOT / "examples/runtime-control-plane-lease-disabled.json")
    value.add_argument("--operation-authorization", type=Path, default=ROOT / "examples/per-operation-authorization-denied.json")
    value.add_argument("--execution-capsule", type=Path, default=ROOT / "examples/execution-capsule-perp.json")
    value.add_argument("--minimum-trusted-time-sequence", type=int, default=0)
    value.add_argument("--minimum-evidence-index-sequence", type=int, default=0)
    value.add_argument("--minimum-account-binding-sequence", type=int, default=0)
    value.add_argument("--minimum-runtime-state-sequence", type=int, default=0)
    value.add_argument("--minimum-runtime-lease-sequence", type=int, default=0)
    value.add_argument("--replay-set", type=Path, help="JSON with consumedAuthorizationIds and consumedNonces arrays")
    value.add_argument("--require-eligible", action="store_true", help="Exit nonzero unless eligible for atomic signer finalization")
    value.add_argument("--print-authorizer-bundle-sha256", action="store_true")
    return value


def load_replay_set(path: Path | None) -> tuple[frozenset[str], frozenset[str]]:
    if path is None:
        return frozenset(), frozenset()
    value = strict_load_json(path)
    if not isinstance(value, dict):
        raise ValueError("replay-set must be a JSON object")
    allowed = {"consumedAuthorizationIds", "consumedNonces"}
    if set(value) - allowed:
        raise ValueError(f"unknown replay-set fields: {sorted(set(value) - allowed)}")
    ids = value.get("consumedAuthorizationIds", [])
    nonces = value.get("consumedNonces", [])
    if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
        raise ValueError("consumedAuthorizationIds must be an array of strings")
    if not isinstance(nonces, list) or not all(isinstance(item, str) for item in nonces):
        raise ValueError("consumedNonces must be an array of strings")
    if len(ids) != len(set(ids)) or len(nonces) != len(set(nonces)):
        raise ValueError("replay-set arrays must not contain duplicates")
    return frozenset(ids), frozenset(nonces)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if min(
        args.minimum_trusted_time_sequence,
        args.minimum_evidence_index_sequence,
        args.minimum_account_binding_sequence,
        args.minimum_runtime_state_sequence,
        args.minimum_runtime_lease_sequence,
    ) < 0:
        print("high-water sequence arguments must be non-negative", file=sys.stderr)
        return 2
    if args.print_authorizer_bundle_sha256:
        print(runtime_authorizer_bundle_hash())
        return 0
    try:
        consumed_ids, consumed_nonces = load_replay_set(args.replay_set)
        result = evaluate_runtime_authorization(
            trust_policy_path=args.trust_policy,
            runtime_policy_path=args.runtime_policy,
            readiness_report_path=args.readiness_report,
            trusted_time_path=args.trusted_time,
            account_binding_path=args.account_binding,
            runtime_state_path=args.runtime_state,
            runtime_lease_path=args.runtime_lease,
            operation_authorization_path=args.operation_authorization,
            execution_capsule_path=args.execution_capsule,
            minimum_trusted_time_sequence=args.minimum_trusted_time_sequence,
            minimum_evidence_index_sequence=args.minimum_evidence_index_sequence,
            minimum_account_binding_sequence=args.minimum_account_binding_sequence,
            minimum_runtime_state_sequence=args.minimum_runtime_state_sequence,
            minimum_runtime_lease_sequence=args.minimum_runtime_lease_sequence,
            consumed_authorization_ids=consumed_ids,
            consumed_nonces=consumed_nonces,
        )
    except Exception as exc:
        print(json.dumps({
            "status": "BLOCKED",
            "eligibleForAtomicSignerFinalization": False,
            "transactionAuthorizationGranted": False,
            "blockingReasons": [f"runtime evaluator failed closed: {exc}"],
        }, ensure_ascii=False, indent=2))
        return 1 if args.require_eligible else 0
    print(json.dumps(result.report, ensure_ascii=False, indent=2, sort_keys=True))
    eligible = result.report.get("eligibleForAtomicSignerFinalization") is True and not result.errors
    if result.report.get("transactionAuthorizationGranted") is not False:
        print("runtime evaluator violated its non-authorization invariant", file=sys.stderr)
        return 3
    return 0 if (eligible or not args.require_eligible) else 1


if __name__ == "__main__":
    raise SystemExit(main())
