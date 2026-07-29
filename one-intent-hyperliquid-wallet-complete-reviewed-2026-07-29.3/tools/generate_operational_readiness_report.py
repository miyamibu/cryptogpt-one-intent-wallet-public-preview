#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

sys.dont_write_bytecode = True
from artifact_io import json_bytes, write_or_check
from operational_readiness import REPORT_PATH, evaluate_design_package


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or verify the fail-closed operational-readiness report for this design package.")
    parser.add_argument("--check", action="store_true", help="compare expected report and do not write")
    args = parser.parse_args()
    evaluation = evaluate_design_package()
    if evaluation.errors:
        print("OPERATIONAL READINESS DESIGN EVALUATION FAILED")
        for error in evaluation.errors:
            print(f"- {error}")
        return 1
    write_or_check(REPORT_PATH, json_bytes(evaluation.report), check=args.check, label="delivery/OPERATIONAL_READINESS_REPORT.json")
    print("OPERATIONAL READINESS REPORT " + ("VERIFIED" if args.check else "GENERATED"))
    print("Status: BLOCKED_NOT_OPERATIONAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
