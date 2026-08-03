from __future__ import annotations

from shared.domain import RegistrySignatureVerifier, SignedRegistry


def validate_registry(
    registry: SignedRegistry,
    *,
    now: int,
    asset_id: str,
    network: str,
    production: bool = False,
    signature_verifier: RegistrySignatureVerifier | None = None,
):
    """Resolve only a signed, current, non-revoked registry entry."""
    return registry.resolve(
        asset_id,
        network,
        now,
        production=production,
        signature_verifier=signature_verifier,
    )
