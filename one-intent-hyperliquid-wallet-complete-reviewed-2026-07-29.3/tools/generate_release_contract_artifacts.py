#!/usr/bin/env python3
"""Generate design-only canonical release contract artifacts.

This is intentionally limited to derived local metadata. It does not create
signatures, production SBOM/provenance, credentials, external approvals, or a
runtime authorization. The output remains NO_GO until external evidence exists.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import re
import sys

sys.dont_write_bytecode = True
from artifact_io import json_bytes, text_bytes, write_or_check
from canonical_hashes import strict_load_json
from package_metadata import ROOT, load_package_metadata
from release_digest_policy import DIGEST_DOMAIN, design_source_tree_digest
from wallet_dependency import WALLET_DEPENDENCY_VERSION, validate_gate_partition, wallet_dependency_for_gate


METADATA = load_package_metadata()
RELEASE_DIR = ROOT / "release"
RELEASE_ARTIFACTS = (
    "release/release-subject.json",
    "release/RELEASE_SUBJECT.json",
    "release/SOURCE_PINS.json",
    "release/SBOM.spdx.json",
    "release/PROVENANCE.json",
    "release/ARTIFACT_HASHES.txt",
    "release/BUILD_ENVIRONMENT.md",
    "release/REPRODUCIBILITY_REPORT.md",
    "release/CODEX_EXECUTION_REPORT.md",
    "release/UNRESOLVED_EXTERNAL_BLOCKERS.md",
    "release/OPERATIONAL_HANDOFF.md",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path) -> str:
    return sha256_bytes(path.read_bytes())


def build_gate_decisions() -> dict:
    config = strict_load_json(ROOT / "config/operational-readiness.json")
    return {
        "schemaVersion": "1.0",
        "release": METADATA.version,
        "status": "DESIGN_ONLY_NO_GO",
        "decisions": [
            {
                "gateId": gate["gateId"],
                "decision": "NO_GO",
                "claimIds": [claim["claimId"] for claim in gate["claims"]],
                "reason": "No signed production evidence is present for this design-only package; local reference tests cannot satisfy the gate.",
            }
            for gate in config["gates"]
        ],
    }


def build_design_subject() -> dict:
    return {
        "releaseId": f"{METADATA.version}-design-package",
        "environment": "DESIGN_ONLY",
        "sourceCommit": None,
        "sourceTreeSha256": None,
        "androidArtifactSha256": None,
        "iosArtifactSha256": None,
        "backendImageDigest": None,
        "signerImageDigest": None,
        "configurationBundleSha256": None,
        "policyBundleSha256": None,
        "assetRegistrySha256": None,
        "sbomSha256": None,
    }


def build_runtime_report() -> dict:
    return {
        "status": "BLOCKED_NOT_OPERATIONAL",
        "releaseEligibleForRuntimeActivation": False,
        "productionWritePermitted": False,
        "runtimeLease": None,
        "leaseMaxLifetimeSeconds": 300,
        "leaseAuthorizesTransaction": False,
        "runtimeDeployment": "NOT_DEPLOYED",
        "writeGate": "STATICALLY_DISABLED",
        "killSwitch": "STATIC_FAIL_CLOSED_ONLY",
        "killSwitchOperationallyVerified": False,
        "reason": "No production runtime deployment, signed health bundle, protected high-water marks, or trusted-time attestation exists; this report does not prove an operational kill-switch endpoint.",
    }


def build_sbom() -> dict:
    packages = [
        ("jsonschema", "4.26.0", "PyPI"),
        ("PyYAML", "6.0.3", "PyPI"),
        ("cryptography", "46.0.4", "PyPI"),
        ("playwright", "1.57.0", "PyPI"),
        ("Chromium", "143.0.7499.4", "Playwright managed browser"),
        ("Firefox", "Playwright build 1497", "Playwright managed browser"),
        ("WebKit", "Playwright build 2227", "Playwright managed browser"),
        ("Android Gradle Plugin", "8.7.3", "apps/android/build.gradle.kts"),
        ("Kotlin", "2.0.21", "apps/android/build.gradle.kts"),
        ("Compose BOM", "2024.09.03", "apps/android/app/build.gradle.kts"),
        ("activity-compose", "1.9.2", "apps/android/app/build.gradle.kts"),
        ("JUnit", "4.13.2", "apps/android/app/build.gradle.kts"),
    ]
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"{METADATA.root_name}-design-only-sbom",
        "documentNamespace": f"https://example.invalid/cryptogpt/{METADATA.version}/sbom",
        "creationInfo": {
            "created": METADATA.deterministic_build_timestamp,
            "creators": ["Tool: CryptoGPT Design Artifact Generator 1.0"],
        },
        "documentDescribes": ["SPDXRef-Package-CryptoGPTDesign"],
        "packages": [
            {
                "SPDXID": "SPDXRef-Package-CryptoGPTDesign",
                "name": METADATA.root_name,
                "versionInfo": METADATA.version,
                "downloadLocation": "NOASSERTION",
                "supplier": "NOASSERTION",
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "filesAnalyzed": False,
            }
        ] + [
            {
                "SPDXID": f"SPDXRef-Dependency-{index:02d}",
                "name": name,
                "versionInfo": version,
                "downloadLocation": "NOASSERTION",
                "supplier": "NOASSERTION",
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "filesAnalyzed": False,
                "annotations": [{"annotationType": "OTHER", "comment": f"Recorded source: {source}"}],
            }
            for index, (name, version, source) in enumerate(packages, start=1)
        ],
        "designOnly": True,
        "signed": False,
        "productionEvidence": False,
        "notes": [
            "This SPDX document records declared design/build inputs only.",
            "NOASSERTION means license, integrity, supplier, and provenance claims require independent release-time verification.",
            "No native signed artifact, production image, wallet key, or live dependency fetch is included.",
        ],
    }


def _material(rel: str) -> dict[str, object]:
    path = ROOT / rel
    return {"uri": rel, "digest": {"sha256": sha256_file(path)}}


def build_provenance() -> dict:
    return {
        "schemaVersion": "0.1",
        "format": "SLSA_DESIGN_ONLY_UNSIGNED",
        "status": "DESIGN_ONLY_NOT_RELEASE_EVIDENCE",
        "subject": [{
            "name": METADATA.root_name,
            "digest": {"sha256": design_source_tree_digest(ROOT)},
        }],
        "source": {
            "sourceCommit": None,
            "sourceTreeSha256": design_source_tree_digest(ROOT),
            "sourceTreeDigestDomain": DIGEST_DOMAIN,
            "sourceControlCommitRecordedOutsidePackage": True,
        },
        "builder": {
            "id": "https://example.invalid/cryptogpt/design-only-builder",
            "version": "1.0",
            "authenticated": False,
        },
        "invocation": {
            "entrypoint": "python3 -B tools/prepare_release_artifacts.py",
            "networkAccess": False,
            "productionWritePermitted": False,
            "walletKeyAccess": False,
        },
        "materials": [_material(rel) for rel in (
            "config/build-metadata.json",
            "config/toolchain-lock.json",
            "config/source-pins.json",
            "shared/canonical-vectors-v1.json",
            "apps/android/app/gradle.lockfile",
            "apps/android/gradle/verification-metadata.xml",
        )],
        "signatures": [],
        "independentReview": False,
        "notes": [
            "This is a deterministic design provenance record, not a signed SLSA attestation.",
            "The source-control commit is maintained by the external canonical-stage Git repository and is not inferred inside a clean ZIP extraction.",
        ],
    }


def build_build_environment() -> str:
    lock = strict_load_json(ROOT / "config/toolchain-lock.json")
    android = lock["android"]
    controls = lock["releaseControls"]
    return f"""# Build Environment — design-only

package={METADATA.root_name}
recordedAt={METADATA.deterministic_build_timestamp}
status={lock['status']}
complete={str(lock['complete']).lower()}

## Recorded tools

- Python: {lock['python']['version']} ({lock['python']['executable']})
- Python dependencies: jsonschema {lock['python']['requirements']['jsonschema']}, PyYAML {lock['python']['requirements']['PyYAML']}, cryptography {lock['python']['requirements']['cryptography']}, Playwright {lock['python']['requirements']['playwright']}
- Browser: Playwright {lock['browser']['playwright']} / Chromium {lock['browser']['chromium']}
- Swift: {lock['swift']['swift']}; Xcode {lock['swift']['xcode']}; iPhoneOS SDK {lock['swift']['iphoneOsSdk']}
- Java: {lock['java']['distribution']} {lock['java']['version']}

## Native build boundary

- Android Gradle Wrapper: `{android['gradleWrapper']}`
- Android Gradle CLI: `{android['gradle']}`
- Android SDK/sdkmanager: `{android['androidSdk']}` / `{android['sdkManager']}`
- iOS target: `OfflineWalletApp` Xcode app target plus Swift Package on `{lock['swift']['packageTarget']}`; local Team `PUBLICTEAM` signed iPhoneOS device proof and unsigned Simulator compile, with no archive/IPA.

## Safety controls

- networkAccessForValidation: `{str(controls['networkAccessForValidation']).lower()}`
- productionWritePermitted: `{str(controls['productionWritePermitted']).lower()}`
- nativeSignedArtifactsAvailable: `{str(controls['nativeSignedArtifactsAvailable']).lower()}`
- artifactSigningAvailable: `{str(controls['artifactSigningAvailable']).lower()}`
- twoPersonApprovalProvisioned: `{str(controls['twoPersonApprovalProvisioned']).lower()}`

`BUILD_ENVIRONMENT.md` is a recorded local design environment, not a hermetic builder attestation. Local Android debug/device proof and the Team `PUBLICTEAM` iPhone 12 signed debug/device proof do not close release archive/IPA, distribution signing, custody, or production gates.
"""


def current_evidence() -> dict:
    path = ROOT / "delivery/evidence/core/reference-tests-current.json"
    return strict_load_json(path) if path.is_file() else {}


def build_reproducibility_report(*, phase: str) -> str:
    validation = "PASS" if phase == "validated" else "PENDING_FINAL_NON_MUTATING_VALIDATION"
    return f"""# Reproducibility Report — design-only

package={METADATA.root_name}
phase={phase}
fullValidationStatus={validation}
doubleBuildStatus=CONTRACT_DEFINED_NOT_RUN_BY_PREPARATION
cleanExtractStatus=CONTRACT_DEFINED_NOT_RUN_BY_PREPARATION
sourceTreeDigestDomain={DIGEST_DOMAIN}

## Required release proof

`tools/build_release.py` must prepare the package, run non-mutating validation,
freeze the tree, build the ZIP twice, compare bytes and SHA-256, clean-extract
each candidate, and rerun the full validation. The current design package has
no signed native/service artifact, so this report does not claim production
reproducibility or release eligibility.

The recorded local preparation phase is `{phase}`. An external clean builder,
artifact signer, independent verifier, and protected release subject remain
required before any operational GO.
"""


def build_codex_execution_report(*, phase: str) -> str:
    evidence = current_evidence()
    validation = "PASS" if phase == "validated" else "PENDING_FINAL_NON_MUTATING_VALIDATION"
    property_result = evidence.get("propertyTests", {})
    fuzz_result = evidence.get("fuzzSmoke", {})
    return f"""# Codex Execution Report — design-only

package={METADATA.root_name}
phase={phase}
fullValidationStatus={validation}
operationalReadiness=BLOCKED_NOT_OPERATIONAL
productionWritePermitted=false
walletKeyAccess=false
testnetWritePerformed=false
mainnetCanaryPerformed=false
externalNetworkUsed=false

## Local evidence

- Python source compile: {evidence.get('pythonSourceFilesCompiled', 'NOT_RUN')}
- Python unit tests: {evidence.get('testCount', 'NOT_RUN')}
- Swift Package contract tests: {evidence.get('swiftContractTests', 'NOT_RUN')}
- Swift Package contract-test scope: {evidence.get('swiftContractTestScope', 'NOT_RECORDED')}
- Browser logical cases: {evidence.get('browserLogicalCases', 'NOT_RUN')}
- Property checks: {property_result.get('propertyCases', 'NOT_RUN') if isinstance(property_result, dict) else 'NOT_RUN'}
- Fuzz smoke iterations: {fuzz_result.get('iterations', 'NOT_RUN') if isinstance(fuzz_result, dict) else 'NOT_RUN'}
- Android Gradle wrapper tests/build: PASS_LOCAL_ONLY (Gradle 9.3.1; unsigned debug APK only)
- Android Pixel 9a physical UI: PASS_LOCAL_DEVICE_PROOF_ONLY (serial `[REDACTED_FOR_PUBLIC_PREVIEW]`; no key, signer, network, or transaction)
- iOS `OfflineWalletApp` target: PASS_LOCAL_SIGNED_DEBUG_ONLY (Team `PUBLICTEAM`; signed iPhoneOS build; no archive/IPA)
- iPhone 12 physical UI: VERIFIED_LOCAL_DEVICE_PROOF_ONLY (Appium/WDA; installed/launched; disabled CTA unchanged after tap; up/down gestures; screenshot SHA-256 `8a1e808d66fc9580e74c5ae90d4f34549986f87e05f3b4b0e3269fdbae7444ea`)
- Source tree digest: {evidence.get('sourceTreeDigest', 'NOT_RUN')}

## Requested reviewer roles

- 指示者: `GPT-5.6 Sol 最大`（このローカル成果物ではモデル識別を独立証明していない）
- 確認者: `GPT-5.6 Sol 最大`（独立レビュー記録は現行版へ結合されるまでrelease evidenceではない）

複数のread-only監査視点を実行し、ローカルAndroid debug buildとPixel 9aの画面操作、Team `PUBLICTEAM` のiPhone 12 signed debug build、インストール、起動、Appium/WDA操作を確認した。秘密値、HSM/MPC、Testnet/Mainnet、外部監査、法務、Store、provider契約、Apple配布署名・archive/IPAにはアクセスしていない。`fullValidationStatus=PASS`はこの設計packageとローカル限定のnative確認だけを示し、本番GO・配布用署名済み証拠・資金利用を示さない。
"""


def build_unresolved_blockers() -> str:
    return f"""# Unresolved External Blockers — {METADATA.version}

status=BLOCKED_EXTERNAL
productionWritePermitted=false
releaseEvidenceStatus=NOT_RELEASE_EVIDENCE

The following items cannot be completed from an offline design package:

| blocker | owner/authority | missing evidence | closes |
|---|---|---|---|
| native Android build | Android release owner / Android SDK portal | release signing, signed APK/AAB, instrumentation, compact/recent device matrix and release-bound evidence | ANDROID_BUILD |
| native iOS release | Apple release owner / Apple Developer portal | archive/IPA, distribution signing, App Store provisioning, full physical-device matrix and release-bound evidence | IOS_BUILD |
| custody and signer | Security owner / HSM-MPC provider | real key ceremony, rotation, revocation, recovery, break-glass and independent audit | SIGNER_CUSTODY |
| backend and ledger | Backend/SRE owner | deployed auth, DB migration, outbox, double-entry ledger, reconciliation and restore drill | BACKEND_OPERATIONAL |
| protocol/provider | Protocol and provider owners | official source pins, JPYC/fee route contract, Hyperliquid Testnet lifecycle and reconciliation | PROTOCOL_LIVE |
| legal/store | Legal counsel / Apple / Google | jurisdictional opinion, provider contracts, app review and store approval | LEGAL_STORE |
| operations | SRE and security owners | monitoring, on-call, incident/key-compromise/kill-switch drills | OPERATIONS |
| independent assurance | independent security/mobile/protocol reviewers | critical/high findings closed and exact release subject approval | INDEPENDENT_GO |

Each blocker requires owner, portal, evidence path, callback, retest command and gate decision in the external operationalization contract. No blocker is closed by this file's existence.
"""


def build_operational_handoff() -> str:
    return f"""# Operational Handoff — design-only

package={METADATA.root_name}
status=BLOCKED_NOT_OPERATIONAL
localSandboxStatus=LOCAL_SANDBOX_OPERATIONAL_GO
productionWritePermitted=false
runtimeActivation=NOT_ISSUED
PRE_WALLET_GO=NOT_USED

## Canonical stage commands

```bash
python3 -B tools/prepare_release_artifacts.py
python3 -B tools/run_full_validation.py
python3 -B tools/check_operational_readiness.py
python3 -B tools/build_release.py ../{METADATA.root_name}.zip
```

The first command is the only mutating preparation step. The second and third
commands are non-mutating/readiness checks. The fourth command performs the
deterministic double-build and clean-extract verification outside the package.

## Handoff boundary

Do not connect a wallet, add a production key, enable a Testnet/Mainnet write,
publish to Apple/Google, or activate a runtime lease based on this package.
Before any wallet-connected work, external owners must complete the blockers in
`release/UNRESOLVED_EXTERNAL_BLOCKERS.md`, regenerate all evidence, bind it to
one exact signed release subject, and obtain independent two-person approval.
"""


def build_production_trust_policy() -> dict:
    policy = copy.deepcopy(strict_load_json(ROOT / "config/operational-trust-policy.template.json"))
    policy["policyVersion"] = "PRODUCTION_NOT_PROVISIONED"
    policy["notes"] = [
        "Canonical production-shaped placeholder for this design package; it is disabled and contains no trusted keys.",
        "A separately controlled, signed production trust policy must be provisioned and pinned out of band before any runtime activation.",
    ]
    return policy


def build_production_runtime_policy() -> dict:
    policy = copy.deepcopy(strict_load_json(ROOT / "config/runtime-authorization-policy.template.json"))
    policy["policyVersion"] = "PRODUCTION_NOT_PROVISIONED"
    policy["notes"] = [
        "Canonical production-shaped placeholder for this design package; it is disabled and cannot authorize a transaction.",
        "A separately controlled, signed runtime policy and trusted-time attestation must exist outside this package before any activation.",
    ]
    return policy


def build_traceability_coverage() -> dict:
    """Materialize an exact 37-gate/93-claim coverage index.

    The blocker list is intentionally narrower than the readiness model: claims
    not yet assigned to an external blocker are still represented as internal
    implementation gaps. This prevents an omitted blocker entry from looking
    like an accepted or untracked claim.
    """
    config = strict_load_json(ROOT / "config/operational-readiness.json")
    trace = strict_load_json(ROOT / "delivery/external-blocker-traceability.json")
    blockers = trace.get("blockers", [])
    blocker_by_gate: dict[str, set[str]] = {}
    blocker_by_claim: dict[str, set[str]] = {}
    for blocker in blockers:
        blocker_id = blocker["id"]
        for gate_id in set(blocker.get("directGateIds", [])) | set(blocker.get("dependentGateIds", [])):
            blocker_by_gate.setdefault(gate_id, set()).add(blocker_id)
        for claim_id in blocker.get("claimIds", []):
            blocker_by_claim.setdefault(claim_id, set()).add(blocker_id)

    validate_gate_partition({gate["gateId"] for gate in config["gates"]})
    gate_entries: list[dict] = []
    claim_entries: list[dict] = []
    for gate in config["gates"]:
        gate_id = gate["gateId"]
        gate_claim_ids = [claim["claimId"] for claim in gate["claims"]]
        gate_blocker_ids = sorted(blocker_by_gate.get(gate_id, set()))
        external_claims = [claim_id for claim_id in gate_claim_ids if claim_id in blocker_by_claim]
        if not external_claims:
            classification = "INTERNAL_IMPLEMENTATION"
        elif len(external_claims) == len(gate_claim_ids):
            classification = "EXTERNAL_BLOCKER"
        else:
            classification = "MIXED"
        gate_entries.append(
            {
                "gateId": gate_id,
                "claimIds": gate_claim_ids,
                "blockerIds": gate_blocker_ids,
                "classification": classification,
                "walletDependency": wallet_dependency_for_gate(gate_id),
                "personalWalletRequired": False,
            }
        )
        for claim_id in gate_claim_ids:
            claim_blocker_ids = sorted(blocker_by_claim.get(claim_id, set()))
            claim_entries.append(
                {
                    "claimId": claim_id,
                    "gateId": gate_id,
                    "blockerIds": claim_blocker_ids,
                    "classification": "EXTERNAL_BLOCKER" if claim_blocker_ids else "INTERNAL_IMPLEMENTATION",
                    "walletDependency": wallet_dependency_for_gate(gate_id),
                    "personalWalletRequired": False,
                }
            )
    return {
        "coverageVersion": "1.0",
        "walletDependencyVersion": WALLET_DEPENDENCY_VERSION,
        "personalWalletRequired": False,
        "gateCount": len(gate_entries),
        "claimCount": len(claim_entries),
        "gates": gate_entries,
        "claims": claim_entries,
    }


def build_traceability() -> dict:
    trace = strict_load_json(ROOT / "delivery/external-blocker-traceability.json")
    trace["coverage"] = build_traceability_coverage()
    return trace


def build_outputs(*, phase: str) -> dict:
    source_pins = strict_load_json(ROOT / "examples/source-pins.json")
    subject = build_design_subject()
    json_outputs = {
        ROOT / "config/source-pins.json": source_pins,
        ROOT / "delivery/external-blocker-traceability.json": build_traceability(),
        ROOT / "delivery/GATE_DECISIONS.json": build_gate_decisions(),
        ROOT / "release/release-subject.json": subject,
        ROOT / "release/RELEASE_SUBJECT.json": subject,
        ROOT / "release/SOURCE_PINS.json": source_pins,
        ROOT / "release/SBOM.spdx.json": build_sbom(),
        ROOT / "release/PROVENANCE.json": build_provenance(),
        ROOT / "delivery/RUNTIME_ACTIVATION_REPORT.json": build_runtime_report(),
        ROOT / "config/operational-trust-policy.production.json": build_production_trust_policy(),
        ROOT / "config/runtime-policy.production.json": build_production_runtime_policy(),
    }
    text_outputs = {
        ROOT / "release/BUILD_ENVIRONMENT.md": build_build_environment(),
        ROOT / "release/REPRODUCIBILITY_REPORT.md": build_reproducibility_report(phase=phase),
        ROOT / "release/CODEX_EXECUTION_REPORT.md": build_codex_execution_report(phase=phase),
        ROOT / "release/UNRESOLVED_EXTERNAL_BLOCKERS.md": build_unresolved_blockers(),
        ROOT / "release/OPERATIONAL_HANDOFF.md": build_operational_handoff(),
    }
    serialized: dict = {path: json_bytes(value) for path, value in json_outputs.items()}
    serialized.update({path: text_bytes(value) for path, value in text_outputs.items()})
    source_digest = design_source_tree_digest(ROOT)
    hash_lines = [
        "format=DESIGN_ONLY_UNSIGNED_ARTIFACT_HASHES_V1",
        f"releaseVersion={METADATA.version}",
        f"releasePhase={phase}",
        f"sourceTreeSha256={source_digest}",
        "sourceTreeDigestDomain=" + DIGEST_DOMAIN,
    ]
    for path in sorted(serialized, key=lambda item: item.relative_to(ROOT).as_posix()):
        rel = path.relative_to(ROOT).as_posix()
        if rel == "release/ARTIFACT_HASHES.txt":
            continue
        if rel.startswith("release/"):
            hash_lines.append(f"artifact={rel} sha256={sha256_bytes(serialized[path])}")
    for rel in (
        "config/build-metadata.json",
        "config/toolchain-lock.json",
        "config/source-pins.json",
        "shared/canonical-vectors-v1.json",
        "apps/android/app/gradle.lockfile",
        "apps/android/gradle/verification-metadata.xml",
    ):
        hash_lines.append(f"input={rel} sha256={sha256_file(ROOT / rel)}")
    text_outputs[ROOT / "release/ARTIFACT_HASHES.txt"] = "\n".join(hash_lines) + "\n"
    serialized[ROOT / "release/ARTIFACT_HASHES.txt"] = text_bytes(text_outputs[ROOT / "release/ARTIFACT_HASHES.txt"])
    return serialized


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare derived bytes without writing")
    parser.add_argument("--phase", choices=("prepared", "validated"), default=None)
    args = parser.parse_args()
    phase = args.phase
    if phase is None and args.check:
        report_path = ROOT / "release/CODEX_EXECUTION_REPORT.md"
        phase = "validated" if report_path.is_file() and re.search(r"^fullValidationStatus=PASS$", report_path.read_text(encoding="utf-8"), re.MULTILINE) else "prepared"
    phase = phase or "prepared"
    for path, value in build_outputs(phase=phase).items():
        write_or_check(path, value, check=args.check, label=path.relative_to(ROOT).as_posix())
    print("DESIGN RELEASE CONTRACT ARTIFACTS " + ("VERIFIED" if args.check else "GENERATED"))
    print(f"Preparation phase: {phase}")
    print("Production credentials, signatures, approvals, live SBOM/provenance, and runtime authorization: NOT GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
