#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from canonical_hashes import strict_load_json
from package_metadata import ROOT, load_package_metadata
from strict_data import strict_load_yaml

TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".html", ".css", ".js", ".py", ".mmd"}
SKIP_CONTENT = {"tools/check_security_hygiene.py"}
PROHIBITED_ARTIFACT_SUFFIXES = {".log", ".sqlite", ".db", ".core", ".dmp", ".har", ".pcap", ".mobileprovision"}
PATTERNS = [
    ("private-key PEM block", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("OpenAI-style secret key", re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}\b")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("GitLab token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("Stripe live secret", re.compile(r"\bsk_live_[A-Za-z0-9]{20,}\b")),
    ("npm token", re.compile(r"\bnpm_[A-Za-z0-9]{30,}\b")),
    ("assigned 32-byte EVM secret", re.compile(r"(?i)(?:private[_-]?key|secret[_-]?key|mnemonic[_-]?key)\s*[:=]\s*['\"]?0x[0-9a-f]{64}\b")),
    ("assigned long API secret", re.compile(r"(?i)(?:api[_-]?key|client[_-]?secret|access[_-]?token|refresh[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_./+=-]{32,}['\"]")),
    ("BIP39 recovery phrase assignment", re.compile(r"(?i)(?:seed|mnemonic|recovery[_ -]?phrase)\s*[:=]\s*['\"](?:[a-z]{3,12}\s+){11,23}[a-z]{3,12}['\"]")),
]


def main() -> int:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT).as_posix()
        if path.is_dir() and path.name in {".git", ".svn", ".hg", "node_modules", ".gradle", "DerivedData"}:
            errors.append(f"build/VCS directory prohibited in release package: {rel}")
        if not path.is_file():
            continue
        if path.suffix.lower() in PROHIBITED_ARTIFACT_SUFFIXES:
            errors.append(f"runtime/debug artifact prohibited: {rel}")
        if path.suffix.lower() not in TEXT_SUFFIXES or rel in SKIP_CONTENT:
            continue
        text = path.read_text(encoding="utf-8", errors="strict")
        for label, pattern in PATTERNS:
            if pattern.search(text):
                errors.append(f"{label}: {rel}")
    gates = strict_load_yaml(ROOT / "config/feature-gates.example.yaml")
    mainnet = gates.get("environments", {}).get("mainnet", {})
    for key, value in mainnet.items():
        if key not in {"read_only", "ai_intent"} and value is not False:
            errors.append(f"mainnet write-like feature must remain false: {key}={value!r}")
    metadata = load_package_metadata()
    if any((metadata.mainnet_enabled, metadata.production_ready_claim_allowed, metadata.native_builds_included, metadata.live_credentials_included)):
        errors.append("build metadata must prohibit Mainnet/native/credential/production-ready claims")
    trust_policy = strict_load_json(ROOT / "config/operational-trust-policy.template.json")
    if trust_policy.get("enabled") is not False or trust_policy.get("trustedKeys") or trust_policy.get("revokedKeyIds"):
        errors.append("design package trust-policy template must be disabled and contain no keys")
    runtime_policy = strict_load_json(ROOT / "config/runtime-authorization-policy.template.json")
    if runtime_policy.get("enabled") is not False or runtime_policy.get("policyVersion") != "TEMPLATE-NOT-ACTIVE":
        errors.append("design package runtime-authorization policy must remain a disabled template")
    binding = strict_load_json(ROOT / "examples/account-authorization-binding-suspended.json")
    state = strict_load_json(ROOT / "examples/runtime-state-bundle-stopped.json")
    lease = strict_load_json(ROOT / "examples/runtime-control-plane-lease-disabled.json")
    operation = strict_load_json(ROOT / "examples/per-operation-authorization-denied.json")
    if binding.get("status") != "SUSPENDED" or binding.get("signatures"):
        errors.append("design account binding must be suspended and unsigned")
    if state.get("killSwitch") is not True or state.get("writesEnabled") is not False or state.get("signatures"):
        errors.append("design runtime state must be stopped, write-disabled, and unsigned")
    if lease.get("transactionAuthorizationGranted") is not False or lease.get("capabilities") or lease.get("signatures"):
        errors.append("design runtime lease must carry no capability or transaction authority")
    if operation.get("authorized") is not False or any(operation.get(name) is not None for name in ("userAuthorization", "deviceAuthorization", "policyAuthorization")):
        errors.append("design operation authorization must remain denied and unsigned")
    evidence_index = strict_load_json(ROOT / "delivery/evidence-index.json")
    if (
        evidence_index.get("sequence") != 0
        or evidence_index.get("records")
        or evidence_index.get("trustedTimeAttestationPath") is not None
        or evidence_index.get("indexSignature") is not None
        or evidence_index.get("releaseSubject", {}).get("environment") != "DESIGN_ONLY"
    ):
        errors.append("design package evidence index accidentally contains production evidence or activation material")
    readiness = strict_load_json(ROOT / "delivery/OPERATIONAL_READINESS_REPORT.json")
    if (
        readiness.get("status") != "BLOCKED_NOT_OPERATIONAL"
        or readiness.get("releaseEligibleForRuntimeActivation") is not False
        or readiness.get("productionWritePermitted") is not False
    ):
        errors.append("design package readiness report must be blocked and unable to grant activation/write authority")
    evidence_artifacts = ROOT / "delivery/evidence/artifacts"
    if any(path.is_file() for path in evidence_artifacts.rglob("*")):
        errors.append("design release must not ship synthetic or production operational evidence artifacts")
    chat = strict_load_yaml(ROOT / "contracts/chatgpt-readonly-openapi.yaml")
    scope_keys = (
        chat.get("components", {})
        .get("securitySchemes", {})
        .get("oauth2ReadOnly", {})
        .get("flows", {})
        .get("authorizationCode", {})
        .get("scopes", {})
    )
    if any("write" in key.lower() for key in scope_keys):
        errors.append("ChatGPT contract contains a write scope")
    if errors:
        print("SECURITY HYGIENE CHECK FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("SECURITY HYGIENE CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
