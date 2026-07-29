#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> int:
    html = (ROOT / "prototype/index.html").read_text(encoding="utf-8")
    js = (ROOT / "prototype/app.js").read_text(encoding="utf-8")
    visible_sources = html + "\n" + js

    required = (
        "先物取引（期限なし）",
        "現物取引",
        "別ネットワーク",
        "運用口座",
        "価格のずれ",
        "清算価格",
        "送金手数料",
        "手数料用",
        "最初の一回だけ",
        "自動でできない場合",
    )
    for phrase in required:
        if phrase not in visible_sources:
            fail(f"required plain-Japanese phrase missing: {phrase}")

    forbidden_primary_fragments = (
        ">Perp<",
        ">Spot<",
        ">Bridge<",
        ">Vault<",
        "最大スリッページ",
        "最大価格影響",
        "Protocol Vault",
        "Root action",
        "Agent wallet",
        "最大DD",
        "APY",
        "TVL",
        ">IOC<",
    )
    for fragment in forbidden_primary_fragments:
        if fragment.lower() in visible_sources.lower():
            fail(f"hard term remains in primary prototype copy: {fragment}")

    if re.search(r"['\"](?:Perp|Spot|Bridge|Vault)['\"]", js):
        fail("hard English label remains as a standalone user-facing value")

    terms_path = ROOT / "config/user-facing-terms.ja.json"
    data = json.loads(terms_path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != "1.0" or data.get("defaultMode") != "plain-ja":
        fail("user-facing term dictionary metadata mismatch")
    entries = data.get("entries")
    if not isinstance(entries, list) or len(entries) < 20:
        fail("user-facing term dictionary must contain at least 20 entries")
    internals: set[str] = set()
    preferred: set[str] = set()
    for index, entry in enumerate(entries):
        for field in ("internal", "preferred", "explanation", "forbiddenPrimaryLabels", "advancedAliases"):
            if field not in entry:
                fail(f"term entry {index} missing {field}")
        if entry["internal"] in internals:
            fail(f"duplicate internal term: {entry['internal']}")
        if entry["preferred"] in preferred:
            fail(f"duplicate preferred term: {entry['preferred']}")
        internals.add(entry["internal"])
        preferred.add(entry["preferred"])
        if not entry["explanation"].endswith("。"):
            fail(f"explanation should be a complete Japanese sentence: {entry['internal']}")

    cases = json.loads((ROOT / "tests/plain-japanese-copy-cases.json").read_text(encoding="utf-8"))
    ids = [case.get("id") for case in cases.get("cases", [])]
    expected_ids = {
        "voice-perp",
        "voice-liquidation-typo",
        "voice-spot",
        "voice-bridge",
        "voice-vault",
        "all-send-ambiguous",
        "unknown-recipient",
        "jpyc-only-zero-fee",
    }
    if set(ids) != expected_ids:
        fail("plain-Japanese voice/copy test case set mismatch")

    print("PLAIN JAPANESE COPY CHECK PASSED")
    print(f"Terms: {len(entries)}")
    print(f"Voice/copy cases: {len(ids)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"PLAIN JAPANESE COPY CHECK FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
