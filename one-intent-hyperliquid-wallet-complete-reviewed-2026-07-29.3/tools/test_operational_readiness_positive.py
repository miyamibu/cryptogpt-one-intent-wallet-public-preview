#!/usr/bin/env python3
"""Construct a complete ephemeral 37-gate/93-claim evidence set and prove GO is reachable.

Nothing from this synthetic test is accepted as production evidence. Every file is
created under a unique temporary directory, signed with throw-away keys, evaluated,
then removed. The test exists to detect an accidentally impossible, self-contradictory
or fail-open readiness contract.
"""
from __future__ import annotations

import base64
import copy
import datetime as dt
import hashlib
import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

sys.dont_write_bytecode = True
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from canonical_hashes import strict_load_json
from operational_readiness import (
    CONFIG_PATH,
    SIGNATURE_PROFILE,
    canonical_payload,
    evaluate_production,
    readiness_bundle_hash,
    secure_file_snapshot,
    subject_hash,
)
from package_metadata import ROOT


@dataclass(frozen=True)
class Identity:
    key_id: str
    principal_id: str
    organization: str
    role: str
    private: Ed25519PrivateKey

    def policy_entry(self, valid_from: str, valid_until: str) -> dict:
        public_pem = self.private.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")
        return {
            "keyId": self.key_id,
            "principalId": self.principal_id,
            "organization": self.organization,
            "roles": [self.role],
            "publicKeyPem": public_pem,
            "validFrom": valid_from,
            "validUntil": valid_until,
        }


def utc(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def dump(path: Path, value: dict) -> bytes:
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    os.chmod(path, 0o600)
    return data


def sign(value: dict, field: str, identity: Identity) -> None:
    value[field] = {
        "profile": SIGNATURE_PROFILE,
        "keyId": identity.key_id,
        "signatureBase64": "AA==",
    }
    signature = identity.private.sign(canonical_payload(value, field))
    value[field]["signatureBase64"] = base64.b64encode(signature).decode("ascii")


def identity(prefix: str, role: str, serial: int = 0) -> Identity:
    token = f"{prefix}-{role}-{serial}".replace("_", "-")
    return Identity(
        key_id=f"KEY-{token}",
        principal_id=f"PRINCIPAL-{token}",
        organization=f"SYNTHETIC-{prefix}-ORG",
        role=role,
        private=Ed25519PrivateKey.generate(),
    )


def main() -> int:
    config = strict_load_json(CONFIG_PATH)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    collected_at = now - dt.timedelta(seconds=120)
    statement_issued = now - dt.timedelta(seconds=90)
    reviewed_at = now - dt.timedelta(seconds=60)
    index_issued = now - dt.timedelta(seconds=30)
    statement_expires = now + dt.timedelta(hours=12)
    index_expires = now + dt.timedelta(minutes=15)
    time_expires = now + dt.timedelta(minutes=4)
    valid_from = utc(now - dt.timedelta(days=1))
    valid_until = utc(now + dt.timedelta(days=365))

    issuer_roles = sorted({role for gate in config["gates"] for claim in gate["claims"] for role in claim["issuerRoles"]})
    reviewer_roles = sorted({role for gate in config["gates"] for claim in gate["claims"] for role in claim["reviewerRoles"]})
    issuer_ids = {role: identity("ISSUER", role) for role in issuer_roles}
    reviewer_ids = {role: [identity("REVIEWER", role, i) for i in range(4)] for role in reviewer_roles}
    index_id = identity("INDEX", "RELEASE_EVIDENCE_CUSTODIAN")
    time_id = identity("TIME", "TRUSTED_TIME_AUTHORITY")
    all_ids = list(issuer_ids.values()) + [item for values in reviewer_ids.values() for item in values] + [index_id, time_id]
    if len(all_ids) > 256:
        print(f"SYNTHETIC OPERATIONAL READINESS TEST FAILED\n- generated too many trust keys: {len(all_ids)}")
        return 1

    subject = {
        "releaseId": "SYNTHETIC-PRODUCTION-RELEASE-001",
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

    test_name = f"synthetic-positive-{os.getpid()}"
    evidence_base = ROOT / "delivery/evidence"
    evidence_parent = evidence_base / "artifacts"
    evidence_base_existed = evidence_base.exists()
    evidence_parent_existed = evidence_parent.exists()
    evidence_root = evidence_parent / test_name
    if evidence_root.exists():
        shutil.rmtree(evidence_root)
    # Exact-tree validation copies files rather than empty directories. Create the
    # synthetic-only parent path when absent, then remove only the directories this
    # test created so the package remains byte-for-byte unchanged.
    evidence_root.mkdir(mode=0o700, parents=True)

    old_env = {name: os.environ.get(name) for name in (
        "ONE_INTENT_TRUST_POLICY_SHA256",
        "ONE_INTENT_READINESS_CHECKER_SHA256",
        "ONE_INTENT_RELEASE_SUBJECT_SHA256",
        "ONE_INTENT_EVIDENCE_INDEX_SHA256",
        "ONE_INTENT_TRUSTED_TIME_ATTESTATION_SHA256",
    )}
    try:
        # One immutable text artifact per evidence type is enough for the synthetic
        # contract test; real production evidence must contain the actual reports.
        evidence_type_paths: dict[str, tuple[str, str, int]] = {}
        all_types = sorted({kind for gate in config["gates"] for claim in gate["claims"] for kind in claim["evidenceTypes"]})
        for kind in all_types:
            rel = f"delivery/evidence/artifacts/{test_name}/evidence/{kind}.txt"
            path = ROOT / rel
            data = dump(path, {"syntheticEvidenceType": kind, "productionEvidence": False})
            evidence_type_paths[kind] = (rel, hashlib.sha256(data).hexdigest(), len(data))

        records: list[dict] = []
        statement_counter = 0
        approval_counter = 0
        for gate in config["gates"]:
            for claim in gate["claims"]:
                statement_counter += 1
                issuer = issuer_ids[claim["issuerRoles"][0]]
                statement = {
                    "schemaVersion": "1.0",
                    "statementId": f"SYNTHETIC-STATEMENT-{statement_counter:03d}",
                    "profileId": config["profileId"],
                    "gateId": gate["gateId"],
                    "claimId": claim["claimId"],
                    "subject": copy.deepcopy(subject),
                    "environment": "PRODUCTION",
                    "outcome": "PASS",
                    "issuedAt": utc(statement_issued),
                    "expiresAt": utc(statement_expires),
                    "issuer": {
                        "keyId": issuer.key_id,
                        "role": issuer.role,
                        "principalId": issuer.principal_id,
                        "organization": issuer.organization,
                    },
                    "evidence": [],
                    "limitations": [],
                }
                for kind in claim["evidenceTypes"]:
                    rel, digest, size = evidence_type_paths[kind]
                    statement["evidence"].append({
                        "type": kind,
                        "path": rel,
                        "sha256": digest,
                        "sizeBytes": size,
                        "mediaType": "text/plain",
                        "collectedAt": utc(collected_at),
                        "description": "Synthetic contract-path evidence; never valid for a production release.",
                    })
                sign(statement, "signature", issuer)
                statement_rel = f"delivery/evidence/artifacts/{test_name}/statements/{statement_counter:03d}.json"
                statement_data = dump(ROOT / statement_rel, statement)
                statement_digest = hashlib.sha256(statement_data).hexdigest()

                approval_refs: list[dict] = []
                used_per_role: dict[str, int] = {}
                roles = claim["reviewerRoles"]
                for slot in range(int(claim["approvalThreshold"])):
                    role = roles[slot] if slot < len(roles) else roles[0]
                    pool_index = used_per_role.get(role, 0)
                    used_per_role[role] = pool_index + 1
                    reviewer = reviewer_ids[role][pool_index]
                    approval_counter += 1
                    approval = {
                        "schemaVersion": "1.0",
                        "approvalId": f"SYNTHETIC-APPROVAL-{approval_counter:03d}",
                        "profileId": config["profileId"],
                        "statementId": statement["statementId"],
                        "statementSha256": statement_digest,
                        "subject": copy.deepcopy(subject),
                        "decision": "APPROVE",
                        "reviewer": {
                            "keyId": reviewer.key_id,
                            "role": reviewer.role,
                            "principalId": reviewer.principal_id,
                            "organization": reviewer.organization,
                        },
                        "reviewedAt": utc(reviewed_at),
                        "comments": "Synthetic independent approval for evaluator reachability testing only.",
                    }
                    sign(approval, "signature", reviewer)
                    approval_rel = f"delivery/evidence/artifacts/{test_name}/approvals/{approval_counter:03d}.json"
                    approval_data = dump(ROOT / approval_rel, approval)
                    approval_refs.append({"path": approval_rel, "sha256": hashlib.sha256(approval_data).hexdigest()})
                records.append({
                    "gateId": gate["gateId"],
                    "claimId": claim["claimId"],
                    "statementPath": statement_rel,
                    "statementSha256": statement_digest,
                    "approvalArtifacts": approval_refs,
                })

        time_doc = {
            "schemaVersion": "1.0",
            "attestationId": "SYNTHETIC-TIME-001",
            "profileId": config["profileId"],
            "sequence": 1,
            "observedAt": utc(now),
            "validUntil": utc(time_expires),
            "trusted": True,
            "authority": {
                "keyId": time_id.key_id,
                "role": time_id.role,
                "principalId": time_id.principal_id,
                "organization": time_id.organization,
            },
        }
        sign(time_doc, "signature", time_id)
        time_rel = f"delivery/evidence/artifacts/{test_name}/trusted-time.json"
        time_data = dump(ROOT / time_rel, time_doc)

        policy = {
            "schemaVersion": "1.0",
            "profileId": config["profileId"],
            "policyVersion": "SYNTHETIC-POSITIVE-TEST-1",
            "enabled": True,
            "signatureProfile": SIGNATURE_PROFILE,
            "canonicalization": "ONE_INTENT_CANONICAL_JSON_SUBSET_V1",
            "trustedKeys": [item.policy_entry(valid_from, valid_until) for item in all_ids],
            "revokedKeyIds": [],
            "requiredOutOfBandEnvironment": {
                "ONE_INTENT_TRUST_POLICY_SHA256": "protected test anchor",
                "ONE_INTENT_READINESS_CHECKER_SHA256": "protected test anchor",
                "ONE_INTENT_RELEASE_SUBJECT_SHA256": "protected test anchor",
                "ONE_INTENT_EVIDENCE_INDEX_SHA256": "protected test anchor",
                "ONE_INTENT_TRUSTED_TIME_ATTESTATION_SHA256": "protected test anchor",
            },
            "roleSeparation": {
                "issuerMustDifferFromEveryReviewer": True,
                "indexSignerMustDifferFromClaimIssuersAndReviewers": True,
                "trustedTimeSignerMustHaveDedicatedRole": True,
                "oneKeyCannotSatisfyTwoApprovalSlots": True,
            },
            "notes": ["Synthetic positive-path test policy. Never provision in production."],
        }

        index = {
            "schemaVersion": "1.0",
            "profileId": config["profileId"],
            "sequence": 1,
            "issuedAt": utc(index_issued),
            "expiresAt": utc(index_expires),
            "releaseSubject": copy.deepcopy(subject),
            "trustedTimeAttestationPath": time_rel,
            "records": records,
            "currentPackageDeclaration": "Synthetic complete evidence set used only to prove evaluator reachability.",
        }
        sign(index, "indexSignature", index_id)

        with tempfile.TemporaryDirectory(prefix="one-intent-positive-") as temp_name:
            temp = Path(temp_name)
            policy_path = temp / "policy.json"
            index_path = temp / "index.json"
            dump(policy_path, policy)
            index_data = dump(index_path, index)
            os.environ["ONE_INTENT_TRUST_POLICY_SHA256"] = secure_file_snapshot(policy_path).digest
            os.environ["ONE_INTENT_READINESS_CHECKER_SHA256"] = readiness_bundle_hash()
            os.environ["ONE_INTENT_RELEASE_SUBJECT_SHA256"] = subject_hash(subject)
            os.environ["ONE_INTENT_EVIDENCE_INDEX_SHA256"] = hashlib.sha256(index_data).hexdigest()
            os.environ["ONE_INTENT_TRUSTED_TIME_ATTESTATION_SHA256"] = hashlib.sha256(time_data).hexdigest()

            evaluation = evaluate_production(policy_path, index_path)
            if evaluation.errors:
                print("SYNTHETIC OPERATIONAL READINESS TEST FAILED")
                for error in evaluation.errors[:100]:
                    print(f"- {error}")
                return 1
            report = evaluation.report
            if (
                report["status"] != "PRODUCTION_OPERATIONAL_GO"
                or report["releaseEligibleForRuntimeActivation"] is not True
                or report["productionWritePermitted"] is not False
                or report["summary"]["mandatoryGates"] != 37
                or report["summary"]["requiredClaims"] != 93
                or report["summary"]["acceptedClaims"] != 93
                or report["decisionInputs"]["evidenceIndexSha256"] != hashlib.sha256(index_data).hexdigest()
                or report["decisionInputs"]["evidenceIndexSequence"] != 1
                or report["decisionInputs"]["trustedTimeSequence"] != 1
                or report["decisionInputs"]["readinessVerifierBundleSha256"] != readiness_bundle_hash()
                or report["decisionInputs"]["releaseSubjectSha256"] != subject_hash(subject)
                or report["validUntil"] <= report["generatedAt"]
            ):
                print("SYNTHETIC OPERATIONAL READINESS TEST FAILED")
                print(f"- unexpected report: {report['status']}, {report['summary']}")
                return 1

            # A protected high-water mark equal to the signed sequence proves the
            # candidate is stale/replayed and must fail closed. Production stores
            # these counters outside the release bundle in rollback-resistant state.
            stale_time = evaluate_production(
                policy_path,
                index_path,
                minimum_trusted_time_sequence=1,
            )
            if stale_time.report["status"] != "BLOCKED_NOT_OPERATIONAL" or not any(
                "trusted time sequence" in error for error in stale_time.errors
            ):
                print("SYNTHETIC OPERATIONAL READINESS TEST FAILED")
                print("- trusted-time rollback high-water mark was not enforced")
                return 1
            stale_index = evaluate_production(
                policy_path,
                index_path,
                minimum_evidence_index_sequence=1,
            )
            if stale_index.report["status"] != "BLOCKED_NOT_OPERATIONAL" or not any(
                "evidence index sequence" in error for error in stale_index.errors
            ):
                print("SYNTHETIC OPERATIONAL READINESS TEST FAILED")
                print("- evidence-index rollback high-water mark was not enforced")
                return 1

        print("SYNTHETIC OPERATIONAL READINESS POSITIVE TEST PASSED")
        print("Gates: 37; claims accepted: 93; direct transaction authorization: false")
        return 0
    finally:
        for name, value in old_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        shutil.rmtree(evidence_root, ignore_errors=True)
        if not evidence_parent_existed:
            try:
                evidence_parent.rmdir()
            except OSError:
                pass
        if not evidence_base_existed:
            try:
                evidence_base.rmdir()
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
