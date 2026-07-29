#!/usr/bin/env python3
from __future__ import annotations

import base64
import copy
import datetime as dt
import sys
import unicodedata

sys.dont_write_bytecode = True
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from canonical_hashes import strict_load_json
from operational_readiness import (
    CONFIG_PATH,
    INDEX_PATH,
    TEMPLATE_TRUST_PATH,
    _key_map,
    canonical_payload,
    evaluate_design_package,
    evaluate_production,
    readiness_bundle_hash,
    required_claims,
    safe_evidence_path,
    subject_hash,
    verify_signature,
)
from package_metadata import ROOT


def reject(label: str, fn, errors: list[str]) -> None:
    try:
        fn()
    except Exception:
        return
    errors.append(f"negative assertion unexpectedly accepted: {label}")


def main() -> int:
    errors: list[str] = []
    assertions = 0
    config = strict_load_json(CONFIG_PATH)
    index = strict_load_json(INDEX_PATH)
    evaluation = evaluate_design_package()
    if evaluation.errors or evaluation.report["status"] != "BLOCKED_NOT_OPERATIONAL":
        errors.append("design package must evaluate cleanly as BLOCKED_NOT_OPERATIONAL")
    assertions += 1
    claims = required_claims(config)
    if len(config["gates"]) != 37 or len(claims) != 93:
        errors.append("operational profile count drift")
    assertions += 1
    if evaluation.report["productionWritePermitted"] is not False:
        errors.append("release evaluator must never grant direct transaction writes")
    assertions += 1
    if evaluation.report["releaseEligibleForRuntimeActivation"] is not False:
        errors.append("design package must not be eligible for runtime activation")
    assertions += 1
    if evaluation.report["summary"]["acceptedClaims"] != 0:
        errors.append("design package must not accept operational claims")
    assertions += 1
    design_inputs = evaluation.report.get("decisionInputs", {})
    if (
        evaluation.report.get("validUntil") != evaluation.report.get("generatedAt")
        or not design_inputs.get("operationalTrustPolicySha256")
        or not design_inputs.get("readinessVerifierBundleSha256")
        or not design_inputs.get("releaseSubjectSha256")
        or not design_inputs.get("evidenceIndexSha256")
        or design_inputs.get("evidenceIndexSequence") != 0
        or design_inputs.get("trustedTimeAttestationSha256") is not None
    ):
        errors.append("design readiness decision-input bindings are incomplete or unexpectedly live")
    assertions += 1

    production = evaluate_production(TEMPLATE_TRUST_PATH, INDEX_PATH)
    if production.report["status"] != "BLOCKED_NOT_OPERATIONAL" or not production.errors:
        errors.append("disabled trust policy and empty index must never evaluate to GO")
    assertions += 1
    if production.report["productionWritePermitted"] is not False:
        errors.append("even a production evaluation may not directly authorize a transaction")
    assertions += 1
    if not any("out-of-band anchor" in item for item in production.errors):
        errors.append("production evaluator did not require out-of-band anchors")
    assertions += 1
    if not any("ONE_INTENT_EVIDENCE_INDEX_SHA256" in item for item in production.errors):
        errors.append("production evaluator did not require the exact evidence-index anchor")
    assertions += 1

    bundle_hash = readiness_bundle_hash()
    if len(bundle_hash) != 64 or any(ch not in "0123456789abcdef" for ch in bundle_hash):
        errors.append("readiness verifier bundle hash is malformed")
    assertions += 1

    private = Ed25519PrivateKey.generate()
    public_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    policy = {
        "trustedKeys": [{
            "keyId": "TEST-KEY",
            "principalId": "TEST-PRINCIPAL",
            "organization": "TEST-ORG",
            "roles": ["SECURITY_AUDITOR"],
            "publicKeyPem": public_pem,
            "validFrom": "2026-01-01T00:00:00Z",
            "validUntil": "2027-01-01T00:00:00Z",
        }],
        "revokedKeyIds": [],
    }
    doc = {
        "statementId": "TEST-STATEMENT-DOMAIN",
        "value": "bound",
        "counter": 1,
        "signature": {
            "profile": "ONE_INTENT_ED25519_CANONICAL_JSON_V2",
            "keyId": "TEST-KEY",
            "signatureBase64": "",
        },
    }
    signed = copy.deepcopy(doc)
    signed["signature"]["signatureBase64"] = base64.b64encode(private.sign(canonical_payload(doc, "signature"))).decode("ascii")
    evaluated_at = dt.datetime(2026, 7, 28, tzinfo=dt.timezone.utc)
    try:
        identity = verify_signature(
            signed,
            signature_field="signature",
            policy=policy,
            required_roles={"SECURITY_AUDITOR"},
            evaluated_at=evaluated_at,
            signed_at=evaluated_at,
            expected_identity_key_id="TEST-KEY",
            expected_principal_id="TEST-PRINCIPAL",
            expected_organization="TEST-ORG",
            declared_role="SECURITY_AUDITOR",
        )
        if identity.key_id != "TEST-KEY" or identity.principal_id != "TEST-PRINCIPAL":
            errors.append("valid test signature returned wrong identity")
    except Exception as exc:
        errors.append(f"valid Ed25519 test signature was rejected: {exc}")
    assertions += 1

    tampered = copy.deepcopy(signed)
    tampered["value"] = "changed"
    reject("tampered signed payload", lambda: verify_signature(tampered, signature_field="signature", policy=policy, required_roles={"SECURITY_AUDITOR"}, evaluated_at=evaluated_at), errors)
    assertions += 1
    reject("wrong signer role", lambda: verify_signature(signed, signature_field="signature", policy=policy, required_roles={"LEGAL_REVIEWER"}, evaluated_at=evaluated_at), errors)
    assertions += 1
    reject("wrong declared principal", lambda: verify_signature(signed, signature_field="signature", policy=policy, required_roles={"SECURITY_AUDITOR"}, evaluated_at=evaluated_at, expected_principal_id="OTHER"), errors)
    assertions += 1
    reject("wrong declared organization", lambda: verify_signature(signed, signature_field="signature", policy=policy, required_roles={"SECURITY_AUDITOR"}, evaluated_at=evaluated_at, expected_organization="OTHER"), errors)
    assertions += 1
    reject("wrong declared role", lambda: verify_signature(signed, signature_field="signature", policy=policy, required_roles={"SECURITY_AUDITOR"}, evaluated_at=evaluated_at, declared_role="LEGAL_REVIEWER"), errors)
    assertions += 1
    revoked = copy.deepcopy(policy)
    revoked["revokedKeyIds"] = ["TEST-KEY"]
    reject("revoked key", lambda: verify_signature(signed, signature_field="signature", policy=revoked, required_roles={"SECURITY_AUDITOR"}, evaluated_at=evaluated_at), errors)
    assertions += 1
    expired = copy.deepcopy(policy)
    expired["trustedKeys"][0]["validUntil"] = "2026-01-02T00:00:00Z"
    reject("expired key", lambda: verify_signature(signed, signature_field="signature", policy=expired, required_roles={"SECURITY_AUDITOR"}, evaluated_at=evaluated_at), errors)
    assertions += 1
    future_sign = dt.datetime(2025, 12, 31, tzinfo=dt.timezone.utc)
    reject("key not valid at signed time", lambda: verify_signature(signed, signature_field="signature", policy=policy, required_roles={"SECURITY_AUDITOR"}, evaluated_at=evaluated_at, signed_at=future_sign), errors)
    assertions += 1
    duplicate_material = copy.deepcopy(policy)
    duplicate_material["trustedKeys"].append({**copy.deepcopy(policy["trustedKeys"][0]), "keyId": "TEST-KEY-2", "principalId": "TEST-PRINCIPAL-2"})
    reject("duplicate public key under another keyId", lambda: _key_map(duplicate_material), errors)
    assertions += 1
    mixed_time_role = copy.deepcopy(policy)
    mixed_time_role["trustedKeys"][0]["roles"] = ["TRUSTED_TIME_AUTHORITY", "SECURITY_AUDITOR"]
    reject("trusted-time key with mixed roles", lambda: _key_map(mixed_time_role), errors)
    assertions += 1
    reject("float in signed payload", lambda: canonical_payload({"x": 1.5, "signature": {}}, "signature", domain="ONE_INTENT_TEST_DOCUMENT_V1"), errors)
    assertions += 1
    reject("unsafe integer in signed payload", lambda: canonical_payload({"x": 9_007_199_254_740_992, "signature": {}}, "signature", domain="ONE_INTENT_TEST_DOCUMENT_V1"), errors)
    assertions += 1
    nfd = unicodedata.normalize("NFD", "ガ")
    reject("non-NFC string in signed payload", lambda: canonical_payload({"x": nfd, "signature": {}}, "signature", domain="ONE_INTENT_TEST_DOCUMENT_V1"), errors)
    assertions += 1
    if canonical_payload({"b": 2, "a": 1, "signature": {}}, "signature", domain="ONE_INTENT_TEST_DOCUMENT_V1") != canonical_payload({"a": 1, "b": 2, "signature": {}}, "signature", domain="ONE_INTENT_TEST_DOCUMENT_V1"):
        errors.append("canonical signing payload depends on mapping insertion order")
    assertions += 1
    reject("lone surrogate in signed payload", lambda: canonical_payload({"x": "\ud800", "signature": {}}, "signature", domain="ONE_INTENT_TEST_DOCUMENT_V1"), errors)
    assertions += 1
    approval_shaped = copy.deepcopy(signed)
    approval_shaped.pop("statementId", None)
    approval_shaped["approvalId"] = "TEST-APPROVAL-DOMAIN"
    reject("cross-document signature replay", lambda: verify_signature(approval_shaped, signature_field="signature", policy=policy, required_roles={"SECURITY_AUDITOR"}, evaluated_at=evaluated_at), errors)
    assertions += 1
    reject("path traversal", lambda: safe_evidence_path("delivery/evidence/artifacts/../secret.json"), errors)
    assertions += 1
    reject("outside evidence root", lambda: safe_evidence_path("README_FIRST.md"), errors)
    assertions += 1
    if subject_hash(index["releaseSubject"]) != subject_hash(copy.deepcopy(index["releaseSubject"])):
        errors.append("release subject hash is not deterministic")
    assertions += 1

    lease = strict_load_json(ROOT / "examples/runtime-control-plane-lease-disabled.json")
    if lease["transactionAuthorizationGranted"] is not False or lease["capabilities"]:
        errors.append("disabled runtime lease example accidentally grants capabilities")
    assertions += 1
    state = strict_load_json(ROOT / "examples/runtime-state-bundle-stopped.json")
    if state["killSwitch"] is not True or state["writesEnabled"] is not False:
        errors.append("stopped runtime state example accidentally enables writes")
    assertions += 1
    operation = strict_load_json(ROOT / "examples/per-operation-authorization-denied.json")
    if operation["authorized"] is not False or operation["oneTimeUse"] is not True:
        errors.append("denied per-operation example has unsafe flags")
    assertions += 1

    if assertions != 34:
        errors.append(f"operational-readiness assertion count drift: {assertions} != 34")
    if errors:
        print("OPERATIONAL READINESS NEGATIVE TEST FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("OPERATIONAL READINESS NEGATIVE TEST PASSED")
    print(f"Assertions: {assertions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
