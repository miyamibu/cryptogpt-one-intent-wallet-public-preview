#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from artifact_io import json_bytes
from operational_readiness import (
    REPORT_PATH,
    TEMPLATE_TRUST_PATH,
    evaluate_design_package,
    evaluate_production,
    readiness_bundle_hash,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed operational readiness evaluator.")
    parser.add_argument("--require-go", action="store_true", help="require signed production evidence and protected out-of-band anchors")
    parser.add_argument("--trust-policy", type=Path, default=TEMPLATE_TRUST_PATH)
    parser.add_argument("--evidence-index", type=Path, default=None)
    parser.add_argument("--minimum-trusted-time-sequence", type=int, default=0, help="protected rollback-resistant high-water mark")
    parser.add_argument("--minimum-evidence-index-sequence", type=int, default=0, help="protected rollback-resistant high-water mark")
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--print-checker-bundle-sha256", action="store_true", help="print the deterministic hash to pin in protected configuration")
    args = parser.parse_args()

    if args.print_checker_bundle_sha256:
        print(readiness_bundle_hash())
        return 0
    if min(args.minimum_trusted_time_sequence, args.minimum_evidence_index_sequence) < 0:
        print("sequence high-water marks must be non-negative", file=sys.stderr)
        return 2

    if args.require_go:
        from operational_readiness import INDEX_PATH
        evaluation = evaluate_production(
            args.trust_policy.resolve(),
            (args.evidence_index or INDEX_PATH).resolve(),
            minimum_trusted_time_sequence=args.minimum_trusted_time_sequence,
            minimum_evidence_index_sequence=args.minimum_evidence_index_sequence,
        )
        required_status = "PRODUCTION_OPERATIONAL_GO"
    else:
        evaluation = evaluate_design_package()
        required_status = "BLOCKED_NOT_OPERATIONAL"
        if not REPORT_PATH.is_file() or REPORT_PATH.read_bytes() != json_bytes(evaluation.report):
            print("OPERATIONAL READINESS CHECK FAILED\n- stored design-package readiness report is missing or stale")
            return 1

    if args.print_json:
        print(json.dumps(evaluation.report, ensure_ascii=False, indent=2))
    report = evaluation.report
    unsafe_direct_write = report.get("productionWritePermitted") is not False
    release_eligibility_mismatch = (
        report.get("releaseEligibleForRuntimeActivation") is not (required_status == "PRODUCTION_OPERATIONAL_GO")
    )
    if report.get("status") != required_status or evaluation.errors or unsafe_direct_write or release_eligibility_mismatch:
        print("OPERATIONAL READINESS CHECK FAILED")
        print(f"Status: {report.get('status')}")
        if unsafe_direct_write:
            print("- release-readiness output must never grant direct transaction writes")
        if release_eligibility_mismatch:
            print("- releaseEligibleForRuntimeActivation does not match the evaluated status")
        for error in evaluation.errors:
            print(f"- {error}")
        return 1
    print("OPERATIONAL READINESS CHECK PASSED")
    print(f"Status: {required_status}")
    if args.require_go:
        print("Release is eligible for runtime activation; this does not authorize any transaction.")
    else:
        print("Production writes remain prohibited by design.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
