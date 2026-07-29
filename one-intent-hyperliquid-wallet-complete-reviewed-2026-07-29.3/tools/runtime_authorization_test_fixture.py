#!/usr/bin/env python3
"""Ephemeral signed runtime-authorization fixture for positive and negative tests.

All keys are throw-away and every artifact is written to a private temporary
folder outside the package tree. Nothing generated here is production evidence.
"""
from __future__ import annotations

import base64
import copy
import datetime as dt
import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from canonical_hashes import domain_hash, expected_hashes
from operational_readiness import (
    CANONICALIZATION_PROFILE,
    SIGNATURE_PROFILE,
    canonical_payload,
    format_time,
    readiness_bundle_hash,
    secure_file_snapshot,
    subject_hash,
)
from package_metadata import ROOT
from runtime_authorization import (
    CAPSULE_AUTHORIZATION_DOMAIN,
    account_binding_payload,
    evaluate_runtime_authorization,
    operation_authorization_payload,
    runtime_authorizer_bundle_hash,
    runtime_lease_payload,
    runtime_state_payload,
)


@dataclass(frozen=True)
class Identity:
    key_id: str
    principal_id: str
    organization: str
    role: str
    private: Ed25519PrivateKey

    @classmethod
    def create(cls, token: str, role: str, organization: str) -> "Identity":
        return cls(
            key_id=f"KEY-{token}",
            principal_id=f"PRINCIPAL-{token}",
            organization=organization,
            role=role,
            private=Ed25519PrivateKey.generate(),
        )

    def public_pem(self) -> str:
        return self.private.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")

    def policy_entry(self, valid_from: str, valid_until: str) -> dict[str, Any]:
        return {
            "keyId": self.key_id,
            "principalId": self.principal_id,
            "organization": self.organization,
            "roles": [self.role],
            "publicKeyPem": self.public_pem(),
            "validFrom": valid_from,
            "validUntil": valid_until,
        }

    def signature_envelope(self, payload: bytes, *, role: str | None = None) -> dict[str, Any]:
        return {
            "profile": SIGNATURE_PROFILE,
            "keyId": self.key_id,
            "role": role or self.role,
            "principalId": self.principal_id,
            "organization": self.organization,
            "signatureBase64": base64.b64encode(self.private.sign(payload)).decode("ascii"),
        }


def dump_json(path: Path, value: dict[str, Any]) -> None:
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_bytes(data)
    os.chmod(path, 0o600)


def utc(value: dt.datetime) -> str:
    return format_time(value)


@dataclass
class RuntimeFixture:
    root: Path
    now: dt.datetime
    identities: dict[str, Identity]
    docs: dict[str, dict[str, Any]]
    paths: dict[str, Path]
    old_env: dict[str, str | None] = field(default_factory=dict)

    @classmethod
    def create(cls) -> "RuntimeFixture":
        now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
        temp_root = Path(tempfile.mkdtemp(prefix="one-intent-runtime-auth-"))
        os.chmod(temp_root, 0o700)

        identities = {
            "time": Identity.create("TIME", "TRUSTED_TIME_AUTHORITY", "SYNTHETIC-TIME-ORG"),
            "registry": Identity.create("REGISTRY", "ACCOUNT_REGISTRY", "SYNTHETIC-REGISTRY-ORG"),
            "security": Identity.create("SECURITY", "SECURITY_APPROVER", "SYNTHETIC-SECURITY-ORG"),
            "control": Identity.create("CONTROL", "CONTROL_PLANE", "SYNTHETIC-CONTROL-ORG"),
            "sre": Identity.create("SRE", "SRE_LEAD", "SYNTHETIC-SRE-ORG"),
            "risk": Identity.create("RISK", "RISK_OWNER", "SYNTHETIC-RISK-ORG"),
            "policy": Identity.create("POLICY", "EXECUTION_POLICY_ENGINE", "SYNTHETIC-POLICY-ORG"),
            "user": Identity.create("USER", "WALLET_USER", "SYNTHETIC-USER"),
            "device": Identity.create("DEVICE", "ATTESTED_DEVICE", "SYNTHETIC-DEVICE"),
        }
        profile = "JAPAN_PUBLIC_CROSS_PLATFORM_MAINNET_V1"
        subject = {
            "releaseId": "SYNTHETIC-PRODUCTION-RUNTIME-001",
            "environment": "PRODUCTION",
            "sourceCommit": "1" * 40,
            "sourceTreeSha256": "2" * 64,
            "androidArtifactSha256": "3" * 64,
            "iosArtifactSha256": "4" * 64,
            "backendImageDigest": "sha256:" + "5" * 64,
            "signerImageDigest": "sha256:" + "6" * 64,
            "configurationBundleSha256": "7" * 64,
            "policyBundleSha256": "8" * 64,
            "assetRegistrySha256": "9" * 64,
            "sbomSha256": "a" * 64,
        }
        valid_from = utc(now - dt.timedelta(days=1))
        valid_until = utc(now + dt.timedelta(days=365))
        trusted_ids = [
            identities[name]
            for name in ("time", "registry", "security", "control", "sre", "risk", "policy")
        ]
        trust = {
            "schemaVersion": "1.0",
            "profileId": profile,
            "policyVersion": "SYNTHETIC-RUNTIME-TRUST-V1",
            "enabled": True,
            "signatureProfile": SIGNATURE_PROFILE,
            "canonicalization": CANONICALIZATION_PROFILE,
            "trustedKeys": sorted(
                [item.policy_entry(valid_from, valid_until) for item in trusted_ids],
                key=lambda item: item["keyId"],
            ),
            "revokedKeyIds": [],
            "requiredOutOfBandEnvironment": {
                "ONE_INTENT_TRUST_POLICY_SHA256": "protected synthetic test anchor",
                "ONE_INTENT_READINESS_CHECKER_SHA256": "protected synthetic test anchor",
                "ONE_INTENT_RELEASE_SUBJECT_SHA256": "protected synthetic test anchor",
                "ONE_INTENT_TRUSTED_TIME_ATTESTATION_SHA256": "protected synthetic test anchor",
                "ONE_INTENT_EVIDENCE_INDEX_SHA256": "protected synthetic test anchor",
            },
            "roleSeparation": {
                "issuerMustDifferFromEveryReviewer": True,
                "indexSignerMustDifferFromClaimIssuersAndReviewers": True,
                "trustedTimeSignerMustHaveDedicatedRole": True,
                "oneKeyCannotSatisfyTwoApprovalSlots": True,
            },
            "notes": ["Synthetic runtime authorization reachability test only."],
        }
        runtime_policy = json.loads((ROOT / "config/runtime-authorization-policy.template.json").read_text(encoding="utf-8"))
        runtime_policy["policyVersion"] = "SYNTHETIC-RUNTIME-AUTHORIZATION-V1"
        runtime_policy["enabled"] = True
        runtime_policy["network"] = {
            "networkRegistrySha256": "2" * 64,
            "allowedSourceNetworkIds": ["hyperliquid:mainnet"],
            "allowedDestinationNetworkIds": [],
        }

        observed = now
        time_doc = {
            "schemaVersion": "1.0",
            "attestationId": "SYNTHETIC-TIME-ATTESTATION-001",
            "profileId": profile,
            "sequence": 1,
            "observedAt": utc(observed),
            "validUntil": utc(now + dt.timedelta(seconds=240)),
            "trusted": True,
            "authority": {
                "keyId": identities["time"].key_id,
                "role": identities["time"].role,
                "principalId": identities["time"].principal_id,
                "organization": identities["time"].organization,
            },
            "signature": {"profile": SIGNATURE_PROFILE, "keyId": identities["time"].key_id, "signatureBase64": "AA=="},
        }
        time_doc["signature"]["signatureBase64"] = base64.b64encode(
            identities["time"].private.sign(canonical_payload(time_doc, "signature"))
        ).decode("ascii")

        config = json.loads((ROOT / "config/operational-readiness.json").read_text(encoding="utf-8"))
        gates = []
        for gate in config["gates"]:
            required = len(gate["claims"])
            gates.append({
                "gateId": gate["gateId"],
                "titleJa": gate["titleJa"],
                "status": "PASS",
                "requiredClaims": required,
                "acceptedClaims": required,
                "blockingClaims": [],
            })
        readiness = {
            "schemaVersion": "1.0",
            "profileId": profile,
            "evaluatedArtifactVersion": "2026-07-29.3",
            "generatedAt": utc(now - dt.timedelta(seconds=40)),
            "validUntil": utc(now + dt.timedelta(seconds=180)),
            "decisionInputs": {
                "operationalTrustPolicySha256": "0" * 64,
                "readinessVerifierBundleSha256": readiness_bundle_hash(),
                "releaseSubjectSha256": subject_hash(subject),
                "evidenceIndexSha256": "b" * 64,
                "evidenceIndexSequence": 1,
                "trustedTimeAttestationSha256": "0" * 64,
                "trustedTimeSequence": time_doc["sequence"],
            },
            "status": "PRODUCTION_OPERATIONAL_GO",
            "releaseEligibleForRuntimeActivation": True,
            "productionWritePermitted": False,
            "releaseSubject": copy.deepcopy(subject),
            "summary": {
                "mandatoryGates": len(gates),
                "passedGates": len(gates),
                "blockedGates": 0,
                "requiredClaims": sum(item["requiredClaims"] for item in gates),
                "acceptedClaims": sum(item["acceptedClaims"] for item in gates),
                "missingOrRejectedClaims": 0,
            },
            "gates": gates,
            "blockingReasons": [],
            "disclaimer": "Synthetic positive-path report; it is not production evidence and never grants a transaction.",
        }

        account = "0x1111111111111111111111111111111111111111"
        deployment = "DEPLOYMENT-SYNTHETIC-001"
        binding = {
            "schemaVersion": "1.0",
            "bindingId": "ACCOUNT-BINDING-SYNTHETIC-001",
            "profileId": profile,
            "releaseSubject": copy.deepcopy(subject),
            "deploymentId": deployment,
            "sequence": 1,
            "registrySha256": "c" * 64,
            "account": account,
            "userKey": {
                "keyId": identities["user"].key_id,
                "principalId": identities["user"].principal_id,
                "organization": identities["user"].organization,
                "publicKeyPem": identities["user"].public_pem(),
            },
            "deviceKey": {
                "keyId": identities["device"].key_id,
                "principalId": identities["device"].principal_id,
                "organization": identities["device"].organization,
                "publicKeyPem": identities["device"].public_pem(),
            },
            "deviceAttestationSha256": "d" * 64,
            "issuedAt": utc(now - dt.timedelta(seconds=30)),
            "expiresAt": utc(now + dt.timedelta(seconds=180)),
            "status": "ACTIVE",
            "signatures": [],
        }
        binding["signatures"] = sorted(
            [
                identities["registry"].signature_envelope(account_binding_payload(binding)),
                identities["security"].signature_envelope(account_binding_payload(binding)),
            ],
            key=lambda item: item["keyId"],
        )

        state = {
            "schemaVersion": "1.0",
            "bundleId": "RUNTIME-BUNDLE-SYNTHETIC-001",
            "profileId": profile,
            "releaseSubject": copy.deepcopy(subject),
            "deploymentId": deployment,
            "sequence": 1,
            "issuedAt": utc(now - dt.timedelta(seconds=20)),
            "expiresAt": utc(now + dt.timedelta(seconds=90)),
            "killSwitch": False,
            "writesEnabled": True,
            "incidentState": "HEALTHY",
            "reconciliationState": "MATCHED",
            "sourceFreshnessState": "FRESH",
            "providerHealthState": "HEALTHY",
            "networkRegistrySha256": runtime_policy["network"]["networkRegistrySha256"],
            "accountRegistrySha256": binding["registrySha256"],
            "policyBundleSha256": subject["policyBundleSha256"],
            "assetRegistrySha256": subject["assetRegistrySha256"],
            "signatures": [],
        }
        state_payload = runtime_state_payload(state)
        state["signatures"] = sorted(
            [identities[name].signature_envelope(state_payload) for name in ("control", "risk", "sre")],
            key=lambda item: item["keyId"],
        )

        lease = {
            "schemaVersion": "1.0",
            "leaseId": "RUNTIME-LEASE-SYNTHETIC-001",
            "profileId": profile,
            "releaseSubject": copy.deepcopy(subject),
            "deploymentId": deployment,
            "runtimeBundleId": state["bundleId"],
            "sequence": 1,
            "issuedAt": utc(now - dt.timedelta(seconds=15)),
            "expiresAt": utc(now + dt.timedelta(seconds=60)),
            "capabilities": ["PERP_TRADE"],
            "transactionAuthorizationGranted": False,
            "signatures": [],
        }
        lease_payload = runtime_lease_payload(lease)
        lease["signatures"] = sorted(
            [identities[name].signature_envelope(lease_payload) for name in ("control", "security")],
            key=lambda item: item["keyId"],
        )

        capsule = json.loads((ROOT / "examples/execution-capsule-perp.json").read_text(encoding="utf-8"))
        capsule["capsuleId"] = "capsule-runtime-synthetic-001"
        capsule["planId"] = "plan-runtime-synthetic-001"
        capsule["environment"] = "MAINNET"
        capsule["account"] = account
        capsule["networkContext"] = {
            "sourceNetworkId": "hyperliquid:mainnet",
            "destinationNetworkIds": [],
            "networkRegistrySha256": runtime_policy["network"]["networkRegistrySha256"],
            "chainId": None,
        }
        capsule["createdAt"] = utc(now - dt.timedelta(seconds=10))
        capsule["expiresAt"] = utc(now + dt.timedelta(seconds=45))
        capsule["warnings"] = ["SYNTHETIC_TEST_ONLY"]
        capsule["steps"] = [copy.deepcopy(capsule["steps"][0])]
        step = capsule["steps"][0]
        step["stepId"] = "step-runtime-order-001"
        step["account"] = account
        step["expiresAt"] = capsule["expiresAt"]
        step["dependsOn"] = []
        step["idempotencyKey"] = "runtime-synthetic-plan:step-order:1"
        step["requiredAuth"] = "AUTH_PER_USE"
        step["riskTier"] = "R1"
        capsule["renderReceipt"] = {
            "locale": "ja-JP",
            "buttonLabel": "内容を確認して先物注文を承認",
            "warningIds": ["SYNTHETIC_TEST_ONLY"],
            "renderedAt": utc(now - dt.timedelta(seconds=5)),
        }
        capsule["stateEvidence"] = {
            "policy": "SINGLE_SOURCE_R1",
            "sources": [{
                "sourceId": "synthetic-official-api-001",
                "kind": "OFFICIAL_API",
                "independenceClass": "synthetic-official-api",
                "observedAt": utc(now - dt.timedelta(seconds=2)),
                "blockHeight": None,
                "digest": "0x" + "e" * 64,
            }],
            "observedAt": utc(now - dt.timedelta(seconds=2)),
            "stateHash": "0x" + "f" * 64,
            "divergenceStatus": "CONSISTENT",
            "maxAgeMs": 5000,
        }
        capsule["authorizationPresentation"] = {
            "mode": "ANDROID_PROTECTED_CONFIRMATION",
            "criticalFields": ["OPERATION", "ASSET", "AMOUNT", "SLIPPAGE", "PLAN_FINGERPRINT"],
            "promptText": "BTCの期限なし先物注文を確認して承認します。",
            "promptTextHash": None,
            "fallbackPolicy": "DENY",
            "assurance": "TRUSTED_CONFIRMATION",
            "standingAuthorizationId": None,
            "destinationRegistrationEvidenceId": None,
        }
        derived = expected_hashes(capsule)
        for field in ("sourceStateHash", "renderReceiptHash", "semanticHash"):
            capsule[field] = derived[field]
        capsule["authorizationPresentation"]["promptTextHash"] = derived["promptTextHash"]
        capsule_hash = domain_hash(CAPSULE_AUTHORIZATION_DOMAIN, capsule)

        operation = {
            "schemaVersion": "1.0",
            "authorizationId": "OPERATION-AUTH-SYNTHETIC-001",
            "profileId": profile,
            "releaseSubject": copy.deepcopy(subject),
            "deploymentId": deployment,
            "runtimeBundleId": state["bundleId"],
            "runtimeLeaseId": lease["leaseId"],
            "accountBindingId": binding["bindingId"],
            "account": account,
            "executionCapsuleHash": capsule_hash,
            "sourceStateHash": capsule["sourceStateHash"],
            "quoteHash": "0x" + "1" * 64,
            "quoteValidUntil": utc(now + dt.timedelta(seconds=20)),
            "nonce": "NONCE-RUNTIME-SYNTHETIC-0001",
            "issuedAt": utc(now - dt.timedelta(seconds=5)),
            "expiresAt": utc(now + dt.timedelta(seconds=30)),
            "requiredCapabilities": ["PERP_TRADE"],
            "authorized": True,
            "userAuthorization": None,
            "deviceAuthorization": None,
            "policyAuthorization": None,
            "oneTimeUse": True,
        }
        op_payload = operation_authorization_payload(operation)
        operation["userAuthorization"] = identities["user"].signature_envelope(op_payload)
        operation["deviceAuthorization"] = identities["device"].signature_envelope(op_payload)
        operation["policyAuthorization"] = identities["policy"].signature_envelope(op_payload)

        docs = {
            "trust": trust,
            "runtime_policy": runtime_policy,
            "trusted_time": time_doc,
            "readiness": readiness,
            "binding": binding,
            "state": state,
            "lease": lease,
            "capsule": capsule,
            "operation": operation,
        }
        paths = {name: temp_root / f"{name}.json" for name in docs}
        fixture = cls(temp_root, now, identities, docs, paths)
        fixture.write_all()
        # Bind the readiness report to the exact trust/time files, then rewrite it.
        fixture.docs["readiness"]["decisionInputs"]["operationalTrustPolicySha256"] = fixture.digest("trust")
        fixture.docs["readiness"]["decisionInputs"]["trustedTimeAttestationSha256"] = fixture.digest("trusted_time")
        fixture.write("readiness")
        fixture.install_anchors()
        return fixture

    def write(self, name: str) -> None:
        dump_json(self.paths[name], self.docs[name])

    def write_all(self) -> None:
        for name in self.docs:
            self.write(name)

    def digest(self, name: str) -> str:
        return secure_file_snapshot(self.paths[name]).digest

    def resign_runtime_document(self, name: str) -> None:
        if name == "binding":
            self.docs[name]["signatures"] = []
            payload = account_binding_payload(self.docs[name])
            signers = ("registry", "security")
        elif name == "state":
            self.docs[name]["signatures"] = []
            payload = runtime_state_payload(self.docs[name])
            signers = ("control", "risk", "sre")
        elif name == "lease":
            self.docs[name]["signatures"] = []
            payload = runtime_lease_payload(self.docs[name])
            signers = ("control", "security")
        else:
            raise ValueError(f"unsupported runtime document: {name}")
        self.docs[name]["signatures"] = sorted(
            [self.identities[item].signature_envelope(payload) for item in signers],
            key=lambda item: item["keyId"],
        )
        self.write(name)

    def resign_operation(self) -> None:
        operation = self.docs["operation"]
        operation["userAuthorization"] = None
        operation["deviceAuthorization"] = None
        operation["policyAuthorization"] = None
        payload = operation_authorization_payload(operation)
        operation["userAuthorization"] = self.identities["user"].signature_envelope(payload)
        operation["deviceAuthorization"] = self.identities["device"].signature_envelope(payload)
        operation["policyAuthorization"] = self.identities["policy"].signature_envelope(payload)
        self.write("operation")

    def resign_trusted_time(self) -> None:
        value = self.docs["trusted_time"]
        value["signature"] = {"profile": SIGNATURE_PROFILE, "keyId": self.identities["time"].key_id, "signatureBase64": "AA=="}
        value["signature"]["signatureBase64"] = base64.b64encode(
            self.identities["time"].private.sign(canonical_payload(value, "signature"))
        ).decode("ascii")
        self.write("trusted_time")

    def refresh_operation_hashes(self) -> None:
        capsule = self.docs["capsule"]
        derived = expected_hashes(capsule)
        for field in ("sourceStateHash", "renderReceiptHash", "semanticHash"):
            capsule[field] = derived[field]
        capsule["authorizationPresentation"]["promptTextHash"] = derived["promptTextHash"]
        self.write("capsule")
        operation = self.docs["operation"]
        operation["executionCapsuleHash"] = domain_hash(CAPSULE_AUTHORIZATION_DOMAIN, capsule)
        operation["sourceStateHash"] = capsule["sourceStateHash"]
        self.resign_operation()

    def install_anchors(self) -> None:
        names = (
            "ONE_INTENT_TRUST_POLICY_SHA256",
            "ONE_INTENT_RUNTIME_AUTHORIZATION_POLICY_SHA256",
            "ONE_INTENT_RUNTIME_AUTHORIZER_SHA256",
            "ONE_INTENT_RELEASE_READINESS_REPORT_SHA256",
            "ONE_INTENT_RELEASE_SUBJECT_SHA256",
            "ONE_INTENT_TRUSTED_TIME_ATTESTATION_SHA256",
        )
        if not self.old_env:
            self.old_env = {name: os.environ.get(name) for name in names}
        values = {
            "ONE_INTENT_TRUST_POLICY_SHA256": self.digest("trust"),
            "ONE_INTENT_RUNTIME_AUTHORIZATION_POLICY_SHA256": self.digest("runtime_policy"),
            "ONE_INTENT_RUNTIME_AUTHORIZER_SHA256": runtime_authorizer_bundle_hash(),
            "ONE_INTENT_RELEASE_READINESS_REPORT_SHA256": self.digest("readiness"),
            "ONE_INTENT_RELEASE_SUBJECT_SHA256": subject_hash(self.docs["readiness"]["releaseSubject"]),
            "ONE_INTENT_TRUSTED_TIME_ATTESTATION_SHA256": self.digest("trusted_time"),
        }
        os.environ.update(values)

    def evaluate(
        self,
        *,
        min_time: int = 0,
        min_index: int = 0,
        min_binding: int = 0,
        min_state: int = 0,
        min_lease: int = 0,
        consumed_authorization_ids: frozenset[str] = frozenset(),
        consumed_nonces: frozenset[str] = frozenset(),
    ):
        return evaluate_runtime_authorization(
            trust_policy_path=self.paths["trust"],
            runtime_policy_path=self.paths["runtime_policy"],
            readiness_report_path=self.paths["readiness"],
            trusted_time_path=self.paths["trusted_time"],
            account_binding_path=self.paths["binding"],
            runtime_state_path=self.paths["state"],
            runtime_lease_path=self.paths["lease"],
            operation_authorization_path=self.paths["operation"],
            execution_capsule_path=self.paths["capsule"],
            minimum_trusted_time_sequence=min_time,
            minimum_evidence_index_sequence=min_index,
            minimum_account_binding_sequence=min_binding,
            minimum_runtime_state_sequence=min_state,
            minimum_runtime_lease_sequence=min_lease,
            consumed_authorization_ids=consumed_authorization_ids,
            consumed_nonces=consumed_nonces,
        )

    def close(self) -> None:
        for name, value in self.old_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        shutil.rmtree(self.root, ignore_errors=True)

    def __enter__(self) -> "RuntimeFixture":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
