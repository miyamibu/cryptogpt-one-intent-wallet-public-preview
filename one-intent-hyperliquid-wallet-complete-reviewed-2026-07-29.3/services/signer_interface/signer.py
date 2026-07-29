"""Protected signer policy facade around the shared no-key reference signer."""

from __future__ import annotations

import re
from typing import Any

from shared.domain import AuthorizationEnvelope, DomainError, DurableAuthorizationStore, ExecutionCapsule, SignerGate


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class SignerInterface:
    def __init__(self, store: DurableAuthorizationStore | None = None) -> None:
        self._gate = SignerGate(store=store, require_durable_store=True)

    @property
    def state(self) -> str:
        return self._gate.state.value

    def sign_if_all_gates_pass(
        self,
        capsule: ExecutionCapsule,
        authorization: AuthorizationEnvelope,
        *,
        release: dict[str, Any],
        runtime: dict[str, Any],
        now: int,
    ) -> bytes:
        if not isinstance(release, dict) or not isinstance(runtime, dict):
            raise DomainError("release and runtime inputs must be objects")
        if release.get("status") != "PRODUCTION_OPERATIONAL_GO" or release.get("releaseEligibleForRuntimeActivation") is not True:
            raise DomainError("release layer is not GO")
        release_subject = release.get("releaseSubjectSha256")
        runtime_subject = runtime.get("releaseSubjectSha256")
        if not isinstance(release_subject, str) or not _SHA256_RE.fullmatch(release_subject) or runtime_subject != release_subject:
            raise DomainError("runtime lease is not bound to the exact release subject")
        if runtime.get("leaseValid") is not True or runtime.get("transactionAuthorizationGranted") is not False:
            raise DomainError("runtime lease is missing or grants transaction authority")
        lifetime = runtime.get("leaseLifetimeSeconds")
        issued_at = runtime.get("issuedAt")
        expires_at = runtime.get("expiresAt")
        if any(not isinstance(value, int) or isinstance(value, bool) for value in (now, lifetime, issued_at, expires_at)):
            raise DomainError("runtime lease times must be integers")
        if not 0 < lifetime <= 300 or expires_at - issued_at != lifetime or now < issued_at or now >= expires_at:
            raise DomainError("runtime lease is stale, future-dated, or too long")
        return self._gate.sign(
            capsule,
            authorization,
            release_go=True,
            runtime_lease_valid=True,
            now=now,
        )

    def reconcile(self, outcome: str) -> str:
        return self._gate.reconcile(outcome).value
