#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from canonical_hashes import strict_load_json
from package_metadata import ROOT, load_package_metadata
from strict_data import strict_load_yaml
from test_validation_harness import EXPECTED_ASSERTIONS

METADATA = load_package_metadata()
VERSION = METADATA.version
EXPECTED_SCREENSHOTS = {
    "prototype/screenshots/iphone-perp-before-confirmation.png",
    "prototype/screenshots/iphone-perp-after-confirmation.png",
    "prototype/screenshots/pixel9a-fee-dark.png",
    "prototype/screenshots/iphone-large-withdraw.png",
    "prototype/screenshots/pixel9a-manual.png",
    "prototype/screenshots/iphone-limited-authorization.png",
    "prototype/screenshots/android-tall-partial-dark.png",
    "prototype/screenshots/iphone-jpyc-large.png",
    "prototype/screenshots/iphone-se-composite-top.png",
    "prototype/screenshots/android-compact-spot-large-dark.png",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    errors: list[str] = []
    read = lambda rel: (ROOT / rel).read_text(encoding="utf-8")
    data = lambda rel: strict_load_json(ROOT / rel)

    evidence = data("tests/prototype-visual-evidence.json")
    if evidence.get("schemaVersion") != "2.0" or evidence.get("release") != VERSION:
        errors.append("visual evidence version/schema mismatch")
    if evidence.get("geometryAndContrastCases") != 288:
        errors.append("visual matrix must be 288 cases")
    if len(evidence.get("viewports", [])) != 6 or len(evidence.get("flows", [])) != 12:
        errors.append("visual matrix must contain 6 viewports and 12 flows")
    if len(evidence.get("textModes", [])) != 2 or len(evidence.get("themes", [])) != 2:
        errors.append("visual matrix must contain 2 text modes and 2 themes")
    if evidence.get("localeExecuted") != ["ja-JP"]:
        errors.append("visual evidence must record ja-JP locale")
    if set(evidence.get("screenshots", [])) != EXPECTED_SCREENSHOTS:
        errors.append("visual evidence screenshot set mismatch")
    states = evidence.get("screenshotReviewStates", {})
    expected_names = {Path(x).name for x in EXPECTED_SCREENSHOTS}
    if set(states) != expected_names:
        errors.append("visual evidence screenshot state set mismatch")
    bottom_action_shots = {
        "android-compact-spot-large-dark.png",
        "android-tall-partial-dark.png",
        "iphone-jpyc-large.png",
        "iphone-perp-after-confirmation.png",
    }
    for name in expected_names:
        state = states.get(name, {})
        mode = "BOTTOM_ACTION" if name in bottom_action_shots else "TOP"
        if state.get("captureMode") != mode or state.get("partialTopBlocks") != 0:
            errors.append(f"visual evidence screenshot boundary failure: {name}")
        if mode == "BOTTOM_ACTION" and (state.get("actionVisible") is not True or state.get("scrollCue") not in {"bottom", "all"}):
            errors.append(f"visual evidence bottom action/cue failure: {name}")
        if mode == "TOP" and (abs(float(state.get("scrollTop", -999))) > 1 or state.get("scrollCue") not in {"top", "all"}):
            errors.append(f"visual evidence natural top/cue failure: {name}")
    checks = evidence.get("checks", [])
    if len(checks) != len(set(checks)):
        errors.append("visual evidence check names must be unique")
    for required in ("control_overlap_and_center_hit_testing", "evidence_screenshot_boundary_alignment", "invented_value_example_markers"):
        if required not in checks:
            errors.append(f"visual evidence required check missing: {required}")
    if evidence.get("testHarness", {}).get("sha256") != sha256(ROOT / "tools/test_prototype.py"):
        errors.append("visual evidence harness hash is stale")
    for rel, digest in evidence.get("prototypeFiles", {}).items():
        if not (ROOT / rel).exists() or sha256(ROOT / rel) != digest:
            errors.append(f"visual evidence source hash is stale: {rel}")
    for rel in EXPECTED_SCREENSHOTS:
        path = ROOT / rel
        if not path.exists() or path.stat().st_size < 10_000:
            errors.append(f"missing or implausibly small screenshot: {rel}")

    html = read("prototype/index.html")
    css = read("prototype/styles.css")
    js = read("prototype/app.js")
    all_proto = html + "\n" + css + "\n" + js
    for phrase in (
        "画面見本です — 実際の送金・取引・署名・外部通信は行いません",
        "清算価格の目安",
        "口座と経路の証明が必要",
        "固定金額では案内しない",
        "無期限・無制限",
    ):
        if phrase not in all_proto:
            errors.append(f"prototype safety copy missing: {phrase}")
    if "requiresCorrectionConfirmation: true" not in js or "confirmInterpretation" not in js:
        errors.append("voice correction hard gate missing")
    for marker in ("画面例のダミー", "初期値ではありません", "画面例・利用者設定ではない"):
        if marker not in js:
            errors.append(f"invented-value marker missing: {marker}")
    if re.search(r"\.large-text[^\{]*\.bubble\.user[^\{]*\{[^}]*display\s*:\s*none", css, re.S):
        errors.append("large text hides source request")
    for forbidden in ("損切り2%", "0.05 POL"):
        for rel in ("prototype/app.js", "prototype/index.html", "43_MANUAL_FALLBACK_PLAYBOOK.md", "examples/manual-fallback-zero-gas.json"):
            if forbidden in read(rel):
                errors.append(f"forbidden fixed/invented value {forbidden!r} in {rel}")

    registry = data("examples/asset-registry-simulation.json")
    entry = registry["entries"][0]
    if registry.get("environment") != "SIMULATION" or entry.get("productionEligible") is not False:
        errors.append("simulation asset registry must be production-ineligible")
    if entry["jpyc"].get("verificationStatus") != "SIMULATION_ONLY" or entry["jpyc"].get("contract") != "0x0000000000000000000000000000000000000137":
        errors.append("simulation JPYC entry must use explicit dummy data")

    capability = data("examples/fee-route-capability-simulation.json")
    if capability.get("productionEligible") is not False or capability.get("evidence", {}).get("status") != "SIMULATION_ONLY":
        errors.append("simulation fee route must be production-ineligible")
    required_bindings = {"account", "networkId", "asset", "operation", "amount", "nonce", "expiresAt", "maxJpycCost", "feeAssetCost", "providerSettlementTarget"}
    if not required_bindings.issubset(set(capability.get("quoteBinding", {}).get("requiredFields", []))):
        errors.append("fee route quote binding is incomplete")

    fee_plan = data("examples/fee-readiness-jpyc-only.json")
    if fee_plan.get("schemaVersion") != "2.1" or fee_plan.get("capabilityProofState") != "VERIFIED" or fee_plan.get("exampleOnly") is not True:
        errors.append("fee plan fixture version/proof/example-only mismatch")
    provider = fee_plan.get("provider", {})
    for key in ("providerId", "legalNameJa", "contact", "termsVersion", "termsSha256"):
        if not provider.get(key):
            errors.append(f"fee plan provider disclosure missing: {key}")
    if fee_plan.get("quote", {}).get("providerId") != provider.get("providerId"):
        errors.append("fee plan quote/provider identity mismatch")
    if fee_plan.get("environment") != "SIMULATION" or fee_plan.get("quote", {}).get("signatureState") != "SIMULATION_ONLY":
        errors.append("fee plan must not masquerade as production proof")
    if not required_bindings.issubset(set(fee_plan.get("quote", {}).get("boundFields", []))):
        errors.append("fee plan quote is not operation-bound")

    manual = data("examples/manual-fallback-zero-gas.json")
    if manual.get("schemaVersion") != "2.1" or manual.get("exampleOnly") is not True or manual.get("amountSource") != "NOT_AVAILABLE":
        errors.append("manual fallback fixture must be example-only and fail closed")
    for key in ("recommendedAmount", "maximumAmount", "estimateId", "operationDigest", "estimateGeneratedAt", "estimateExpiresAt"):
        if manual.get(key) is not None:
            errors.append(f"manual fallback must keep unavailable estimate field null: {key}")

    gates = strict_load_yaml(ROOT / "config/feature-gates.example.yaml")
    for key, value in gates.get("environments", {}).get("mainnet", {}).items():
        if key not in {"read_only", "ai_intent"} and value is not False:
            errors.append(f"Mainnet write gate enabled: {key}")

    canonical = read("codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md")
    for phrase in (
        "Mainnet", "signed asset registry", "zero-native-balance", "JPYC EX", "Hyperliquid",
        "VoiceOver", "TalkBack", "two-person", "clean extract", "ChatGPT",
        "sender-constrained", "SBOM", "SLSA", "no validation bypass",
        "BLOCKED_NOT_OPERATIONAL", "PRODUCTION_OPERATIONAL_GO",
        "operational-readiness.json", "out-of-band", "trusted time",
        "runtime lease", "per-operation", "37", "93", "non-mutating",
        "canonical quote", "final-payload commitment", "SIGNED_BROADCAST_UNKNOWN",
        "high-water", "RPC chain ID",
    ):
        if phrase.lower() not in canonical.lower():
            errors.append(f"Codex master prompt missing requirement: {phrase}")
    for rel in ("17_CODEX_IMPLEMENTATION_MASTER_PROMPT.md", "34_CODEX_REMAINING_WORK_MASTER_PROMPT.md"):
        text = read(rel)
        if "codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md" not in text or len(text) > 2500:
            errors.append(f"{rel} must be a short pointer to the canonical prompt")

    harness_source = read("tools/test_prototype.py")
    if "scrollIntoView" in harness_source:
        errors.append("visual harness must not manufacture reachability with scrollIntoView")
    for shot in ("iphone-se-composite-top.png", "android-compact-spot-large-dark.png", "android-tall-partial-dark.png"):
        if shot not in harness_source:
            errors.append(f"adversarial screenshot missing from harness: {shot}")

    start = data("tests/start-here-layout-evidence.json")
    if start.get("schemaVersion") != "1.0" or start.get("release") != VERSION or start.get("result") != "PASS":
        errors.append("START_HERE evidence version/result mismatch")
    start_cases = {(x.get("viewport"), x.get("theme")) for x in start.get("cases", [])}
    expected_start = {(name, theme) for name in ("mobile-narrow", "mobile-standard", "desktop") for theme in ("LIGHT", "DARK")}
    if start_cases != expected_start:
        errors.append("START_HERE evidence case set mismatch")
    if start.get("source", {}).get("sha256") != sha256(ROOT / "START_HERE.html"):
        errors.append("START_HERE evidence source hash is stale")
    if start.get("testHarness", {}).get("sha256") != sha256(ROOT / "tools/test_start_here.py"):
        errors.append("START_HERE evidence harness hash is stale")
    start_html = read("START_HERE.html")
    regression_cases = data("tests/loophole-regression-cases.json").get("cases", [])
    regression_metric = f'<div class="metric">{len(regression_cases)}</div>'
    if ('<div class="metric">288</div>' not in start_html or regression_metric not in start_html or '<div class="metric">10</div>' not in start_html):
        errors.append(f"START_HERE metrics are stale; expected 288/{len(regression_cases)}/10")

    chat = strict_load_yaml(ROOT / "contracts/chatgpt-readonly-openapi.yaml")
    chat_ids = {
        op.get("operationId")
        for item in chat.get("paths", {}).values()
        for method, op in item.items()
        if method in {"get", "post"} and isinstance(op, dict)
    }
    if chat_ids != {"getReadOnlyStatus", "getPlainJapaneseTerm", "explainNonTransactionalError", "getGenericSafetyHelp"}:
        errors.append("ChatGPT read-only contract operation allowlist mismatch")
    if chat.get("components", {}).get("schemas", {}).get("SupportExplanation", {}).get("properties", {}).get("executable", {}).get("const") is not False:
        errors.append("ChatGPT SupportExplanation must be non-executable")
    support_props = chat.get("components", {}).get("schemas", {}).get("SupportExplanation", {}).get("properties", {})
    if support_props.get("neutralHandoffJa", {}).get("const") != "独立したウォレットアプリを開いて、内容を確認してください。":
        errors.append("ChatGPT neutral handoff must be one fixed non-transactional string")
    boundary_doc = read("42_NATURAL_LANGUAGE_AND_CHATGPT_BOUNDARY.md")
    if "get_manual_steps" in boundary_doc or "manual button-by-button instructions" in canonical:
        errors.append("ChatGPT boundary still exposes transaction-specific manual instructions")
    for required in (
        "取引文、送金先、金額、資産・ネットワーク選択、承認情報、payload、署名材料をOpenAIサービスへ送って取引用下書きを作らない",
        "手動復旧catalogは独立ウォレット内だけ",
        "fixed neutral handoff",
        "transaction-specific manual fallback remains available only inside the standalone wallet",
    ):
        corpus = boundary_doc + "\n" + canonical
        if required.lower() not in corpus.lower():
            errors.append(f"OpenAI boundary hardening phrase missing: {required}")

    source_json = data("examples/source-pins.json")
    source_yaml = strict_load_yaml(ROOT / "config/source-pins.example.yaml")
    if source_json != source_yaml:
        errors.append("source pin JSON/YAML drift")
    for source in source_json.get("sources", []):
        if source.get("contentHash") is None and source.get("status") != "MONITOR":
            errors.append(f"unpinned source is not MONITOR: {source.get('name')}")

    generator = read("tools/generate_manifest.py")
    if "one-intent-hyperliquid-wallet-cross-platform-complete" in generator or 'version": "2026-' in generator:
        errors.append("manifest generator hard-codes package identity/version")
    build_release = read("tools/build_release.py")
    full_validation = read("tools/run_full_validation.py")
    if "skip-full-validation" in build_release or "skip_full_validation" in build_release or "skip-visual" in full_validation:
        errors.append("release/full-validation tooling exposes a validation bypass")
    for required in (
        'update_example_hashes.py", "--check"',
        'test_prototype.py", "--check"',
        'test_start_here.py", "--check"',
        'generate_release_contract_artifacts.py", "--check"',
        'check_toolchain_lock.py',
        'check_shared_canonical_vectors.py',
        'check_coverage_matrix.py',
        'generate_current_validation_evidence.py", "--check"',
        'generate_operational_readiness_report.py", "--check"',
        'generate_reports.py", "--check"',
        'check_release_contract.py',
        'check_mobile_contract_vectors.py',
        'test_operational_readiness_positive.py',
        'test_operational_readiness_negative.py',
        'check_runtime_authorization.py',
        'test_runtime_authorization_positive.py',
        'test_runtime_authorization_negative.py',
        'generate_manifest.py", "--check"',
        "compare_snapshots",
        "FULL NON-MUTATING VALIDATION PIPELINE PASSED",
    ):
        if required not in full_validation:
            errors.append(f"full validation missing non-mutating control: {required}")
    prepare = read("tools/prepare_release_artifacts.py")
    for required in (
        "update_example_hashes.py", "test_prototype.py", "test_start_here.py",
        "generate_coverage_matrix.py", "generate_release_contract_artifacts.py", "generate_current_validation_evidence.py", "generate_reports.py", "generate_manifest.py",
        "generate_operational_readiness_report.py",
        "run_full_validation.py",
    ):
        if required not in prepare:
            errors.append(f"prepare stage missing canonical generator/validator: {required}")
    if '"--check"' in prepare:
        errors.append("prepare stage unexpectedly uses check-only mode for all derivation")
    readiness = data("delivery/OPERATIONAL_READINESS_REPORT.json")
    summary = readiness.get("summary", {})
    if (
        readiness.get("status") != "BLOCKED_NOT_OPERATIONAL"
        or readiness.get("releaseEligibleForRuntimeActivation") is not False
        or readiness.get("productionWritePermitted") is not False
    ):
        errors.append("current design package must be blocked and must not grant runtime activation or transaction writes")
    if summary.get("mandatoryGates") != 37 or summary.get("requiredClaims") != 93 or summary.get("acceptedClaims") != 0:
        errors.append("operational readiness gate/claim summary drift")
    runtime_lease = data("examples/runtime-control-plane-lease-disabled.json")
    operation_auth = data("examples/per-operation-authorization-denied.json")
    account_binding = data("examples/account-authorization-binding-suspended.json")
    runtime_policy = data("config/runtime-authorization-policy.template.json")
    if runtime_lease.get("transactionAuthorizationGranted") is not False:
        errors.append("runtime lease must never grant transaction authorization")
    if operation_auth.get("authorized") is not False:
        errors.append("default operation authorization example must remain denied")
    if account_binding.get("status") != "SUSPENDED":
        errors.append("default account authorization binding must remain suspended")
    if runtime_policy.get("enabled") is not False:
        errors.append("runtime authorization policy template must remain disabled")
    runtime_evaluator = read("tools/runtime_authorization.py")
    for required in (
        '"transactionAuthorizationGranted": False',
        "eligibleForAtomicSignerFinalization",
        "runtime_authorizer_bundle_hash",
        "ONE_INTENT_RUNTIME_AUTHORIZER_SHA256",
        "consumed_authorization_ids",
        "consumed_nonces",
    ):
        if required not in runtime_evaluator:
            errors.append(f"runtime evaluator missing required fail-closed control: {required}")
    for required in ("run_full_validation.py", "tree_digest", "build_reproducible_zip.py", "verify_zip.py", "deterministic double-build"):
        if required.lower() not in build_release.lower():
            errors.append(f"release orchestrator missing canonical step: {required}")
    verifier = read("tools/verify_zip.py")
    for required in ("EXPECTED_ASCII_ZIP_FLAGS", "external_attr", "extra per-entry metadata", "tree_digest", "member_name_problems"):
        if required not in verifier:
            errors.append(f"ZIP verifier missing strict control: {required}")
    selftest = read("tools/test_validation_harness.py")
    for required in ("duplicate-root", "negative-zero", "unsafe-large-integer", "duplicate-yaml-root", "yaml-alias", "yaml-nan", "Windows alternate stream", "bidi override", "non-ASCII confusable"):
        if required not in selftest:
            errors.append(f"validator negative self-test missing: {required}")

    metadata = data("config/build-metadata.json")
    if metadata.get("package") != METADATA.package or metadata.get("version") != VERSION or metadata.get("deterministicBuildTimestamp") != METADATA.deterministic_build_timestamp:
        errors.append("deterministic build metadata mismatch")
    if metadata.get("productionReadyClaimAllowed") is not False:
        errors.append("production-ready claim must be prohibited")

    regressions = data("tests/loophole-regression-cases.json").get("cases", [])
    ids = [case.get("id") for case in regressions]
    expected_ids = [f"LR-{index:03d}" for index in range(1, len(ids) + 1)]
    if len(ids) < 97 or ids != expected_ids:
        errors.append(f"loophole regression cases must be contiguous LR-001..LR-{len(ids):03d} with at least 97 cases")

    final_audit = read("FINAL_AUDIT_REPORT.md")
    validation_report = read("VALIDATION_REPORT.md")
    for stale in ("131ファイル", "287件", "110件", "120条件", "dark-mode smoke", "iphone-overview.png", "pixel9a-composite.png"):
        if stale in final_audit or stale in validation_report:
            errors.append(f"generated report contains stale metric/artifact: {stale}")
    for rel in (
        "47_FEE_ROUTE_AND_ASSET_REGISTRY_SPEC.md", "48_RELEASE_SOURCE_PINNING_AND_EXPIRY.md",
        "49_REPRODUCIBLE_BUILD_AND_ARCHIVE_SAFETY.md", "50_FINAL_MULTI_PERSPECTIVE_REVIEW.md",
        "51_OPERATIONAL_READINESS_AND_RUNTIME_ACTIVATION.md", "52_FINAL_OPERATIONAL_GAP_REVIEW.md",
        "53_CODEX_OPERATIONAL_COMPLETION_CONTRACT.md", "54_CANONICAL_QUOTE_REGISTRY_AND_ATOMIC_SIGNER.md",
        "FINAL_DELIVERY_INDEX.md", "AUDIT_ITERATION_LOG.md",
    ):
        if not (ROOT / rel).exists():
            errors.append(f"final review artifact missing: {rel}")

    if errors:
        print("ADVERSARIAL AUDIT FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("ADVERSARIAL AUDIT PASSED")
    print(f"Loophole regression cases: {len(regressions)}")
    print(f"Validator self-test assertions: {EXPECTED_ASSERTIONS}")
    print("Visual matrix: 288")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
