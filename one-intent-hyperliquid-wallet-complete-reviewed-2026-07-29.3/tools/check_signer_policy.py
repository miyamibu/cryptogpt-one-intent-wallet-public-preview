#!/usr/bin/env python3
"""Independent signer-side denial check; it never contacts a network or stores keys."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shared.domain import AuthorizationEnvelope, DomainError, ExecutionCapsule, ReferenceOnlyProofVerifier, SignerGate  # noqa: E402


def denied(callable_):
    try:
        callable_()
    except (DomainError, ValueError):
        return True
    return False


def main() -> int:
    capsule = ExecutionCapsule(
        operation_type="REFERENCE_ONLY", account="acct", device_id="device", intent_commitment="intent", network="eip155:0",
        asset_id="asset", amount="1", recipient=None, ordered_actions=("reference",),
        registry_digest="registry", quote_id="quote", quote_digest="quote-digest",
        final_payload={}, expires_at=2000,
    )
    valid = AuthorizationEnvelope("auth", "device", "acct", capsule.hash, capsule.operation_type, 1000, 1100, "nonce", "review", "")
    valid = AuthorizationEnvelope(**{**valid.__dict__, "proof_of_possession": valid.expected_proof_of_possession})
    expired = AuthorizationEnvelope("expired", "device", "acct", capsule.hash, capsule.operation_type, 900, 1000, "nonce-expired", "review", "")
    expired = AuthorizationEnvelope(**{**expired.__dict__, "proof_of_possession": expired.expected_proof_of_possession})
    signer = SignerGate(proof_verifier=ReferenceOnlyProofVerifier())
    checks = {
        "release_go_required": denied(lambda: signer.sign(capsule, valid, release_go=False, runtime_lease_valid=True, now=1001)),
        "runtime_lease_required": denied(lambda: signer.sign(capsule, valid, release_go=True, runtime_lease_valid=False, now=1001)),
        "fresh_authorization_required": denied(lambda: signer.sign(capsule, expired, release_go=True, runtime_lease_valid=True, now=1001)),
    }
    signer.sign(capsule, valid, release_go=True, runtime_lease_valid=True, now=1001)
    checks["single_use_replay_rejected"] = denied(lambda: signer.sign(capsule, valid, release_go=True, runtime_lease_valid=True, now=1001))
    passed = all(checks.values())
    print(json.dumps({"status": "PASS" if passed else "FAIL", "checks": checks, "privateKeyPresent": False, "networkCalled": False}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
