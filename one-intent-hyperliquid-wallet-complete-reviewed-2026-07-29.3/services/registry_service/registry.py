from __future__ import annotations

from shared.domain import SignedRegistry


def validate_registry(registry: SignedRegistry, *, now: int, asset_id: str, network: str, production: bool = False):
    """Resolve only a signed, current, non-revoked registry entry."""
    return registry.resolve(asset_id, network, now, production=production)
