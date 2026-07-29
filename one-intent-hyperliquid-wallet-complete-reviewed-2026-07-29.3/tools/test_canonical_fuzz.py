#!/usr/bin/env python3
from __future__ import annotations

import sys

sys.dont_write_bytecode = True
from canonical_quality import run_fuzz_smoke


def main() -> int:
    result = run_fuzz_smoke()
    if result["unexpectedCrashes"] != 0:
        print("CANONICAL FUZZ SMOKE FAILED")
        return 1
    print("CANONICAL FUZZ SMOKE PASSED")
    print(f"Iterations: {result['iterations']}; accepted={result['accepted']}; rejected={result['rejected']}")
    print("Independent fuzz campaign: NOT PROVIDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
