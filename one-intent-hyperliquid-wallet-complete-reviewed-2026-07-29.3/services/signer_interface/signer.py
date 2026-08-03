"""Protected signer policy facade around the shared no-key reference signer."""

from __future__ import annotations

import re
from typing import Any

from shared.canonical import canonical_hash
from shared.domain import (
    AuthorizationEnvelope,
    AuthorizationProofVerifier,
    CanonicalQuote,
    DomainError,
    DurableAuthorizationStore,
    QuoteSignatureVerifier,
    RegistrySignatureVerifier,
    ExecutionCapsule,
    SignedRegistry,
    SignerGate,
)


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class SignerInterface:
    def __init__(
        self,
        store: DurableAuthorizationStore | None = None,
        *,
        proof_verifier: AuthorizationProofVerifier | None = None,
        registry_verifier: RegistrySignatureVerifier | None = None,
        quote_verifier: QuoteSignatureVerifier | None = None,
    ) -> None:
        if any(
            verifier is not None and getattr(verifier, "reference_only", False)
            for verifier in (proof_verifier, registry_verifier, quote_verifier)
        ):
            raise DomainError("reference-only verifier cannot authorize the signer interface")
        self._registry_verifier = registry_verifier
        self._quote_verifier = quote_verifier
        self._gate = SignerGate(
            store=store,
            require_durable_store=True,
            proof_verifier=proof_verifier,
        )

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
        registry: SignedRegistry | None = None,
        quote: CanonicalQuote | None = None,
        now: int,
    ) -> bytes:
        if not isinstance(capsule, ExecutionCapsule) or not isinstance(authorization, AuthorizationEnvelope):
            raise DomainError("capsule and authorization runtime types are required")
        if not isinstance(release, dict) or not isinstance(runtime, dict):
            raise DomainError("release and runtime inputs must be objects")
        if (
            release.get("status") != "PRODUCTION_OPERATIONAL_GO"
            or release.get("environment") != "PRODUCTION"
            or release.get("releaseEligibleForRuntimeActivation") is not True
        ):
            raise DomainError("release layer is not GO")
        release_subject = release.get("releaseSubjectSha256")
        runtime_subject = runtime.get("releaseSubjectSha256")
        if not isinstance(release_subject, str) or not _SHA256_RE.fullmatch(release_subject) or runtime_subject != release_subject:
            raise DomainError("runtime lease is not bound to the exact release subject")
        if runtime.get("leaseValid") is not True or runtime.get("transactionAuthorizationGranted") is not False:
            raise DomainError("runtime lease is missing or grants transaction authority")
        if not isinstance(registry, SignedRegistry) or not isinstance(quote, CanonicalQuote):
            raise DomainError("exact signed registry and quote are required")
        if self._registry_verifier is None or self._quote_verifier is None:
            raise DomainError("cryptographic registry and quote verifiers are not provisioned")
        runtime_bindings = {
            "executionCapsuleHash": capsule.hash,
            "authorizationId": authorization.authorization_id,
            "nonce": authorization.nonce,
            "account": capsule.account,
        }
        if any(runtime.get(key) != expected for key, expected in runtime_bindings.items()):
            raise DomainError("runtime lease is not bound to the exact operation authorization")
        if authorization.user_review_digest != capsule.review_digest:
            raise DomainError("authorization is not bound to the exact user review material")
        if registry.digest != capsule.registry_digest:
            raise DomainError("registry digest is not bound to the capsule")
        production = release.get("environment") == "PRODUCTION"
        registry.resolve(
            capsule.asset_id,
            capsule.network,
            now,
            production=production,
            signature_verifier=self._registry_verifier,
        )
        quote.verify(
            now,
            network=capsule.network,
            asset_id=capsule.asset_id,
            account=capsule.account,
            amount=capsule.amount,
            signature_verifier=self._quote_verifier,
        )
        if quote.quote_id != capsule.quote_id or quote.digest != capsule.quote_digest:
            raise DomainError("quote identity is not bound to the capsule")
        if quote.execution_capsule_hash != capsule.hash:
            raise DomainError("quote is not bound to the exact capsule")
        if quote.final_payload_commitment != canonical_hash("final-payload-v1", dict(capsule.final_payload)):
            raise DomainError("final payload commitment is not bound to the quote")
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
