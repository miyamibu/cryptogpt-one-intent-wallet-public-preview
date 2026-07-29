from __future__ import annotations

from dataclasses import dataclass

from shared.canonical import CanonicalizationError, address_fingerprint, canonical_hash, decimal_string, ensure_nfc


MAX_HANDOFF_LIFETIME_SECONDS = 30 * 60


def _text(value: object, label: str, *, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ValueError(f"{label} is missing or oversized")
    try:
        ensure_nfc(value)
    except CanonicalizationError as exc:
        raise ValueError(f"{label} is not canonical text") from exc
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError(f"{label} contains a control character")
    return value


def _time(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


@dataclass(frozen=True)
class JpycHandoff:
    handoff_id: str
    amount: str
    destination_network: str
    receiving_address: str
    address_fingerprint: str
    created_at: int
    expires_at: int
    production_enabled: bool = False

    @property
    def digest(self) -> str:
        return canonical_hash(
            "jpyc-ex-handoff-v1",
            {
                "handoffId": self.handoff_id,
                "amount": self.amount,
                "destinationNetwork": self.destination_network,
                "receivingAddress": self.receiving_address,
                "addressFingerprint": self.address_fingerprint,
                "createdAt": self.created_at,
                "expiresAt": self.expires_at,
            },
        )

    def validate(self) -> None:
        _text(self.handoff_id, "handoff id")
        _text(self.destination_network, "destination network")
        _text(self.receiving_address, "receiving address")
        _text(self.address_fingerprint, "address fingerprint", maximum=32)
        if type(self.production_enabled) is not bool or self.production_enabled:
            raise ValueError("reference handoff must not be production enabled")
        try:
            if decimal_string(self.amount) <= 0:
                raise ValueError("handoff amount must be positive")
        except CanonicalizationError as exc:
            raise ValueError("handoff amount is invalid") from exc
        created_at = _time(self.created_at, "handoff creation time")
        expires_at = _time(self.expires_at, "handoff expiry")
        if not 0 < expires_at - created_at <= MAX_HANDOFF_LIFETIME_SECONDS:
            raise ValueError("handoff lifetime is invalid")
        if self.address_fingerprint != address_fingerprint(self.receiving_address):
            raise ValueError("handoff address fingerprint does not match")
        _ = self.digest


def prepare_handoff(*, handoff_id: str, amount: str, network: str, address: str, now: int, expires_at: int) -> JpycHandoff:
    _text(handoff_id, "handoff id")
    _text(network, "destination network")
    _text(address, "receiving address")
    now = _time(now, "handoff creation time")
    expires_at = _time(expires_at, "handoff expiry")
    try:
        if decimal_string(amount) <= 0:
            raise ValueError("handoff amount must be positive")
    except CanonicalizationError as exc:
        raise ValueError("handoff amount is invalid") from exc
    if not 0 < expires_at - now <= MAX_HANDOFF_LIFETIME_SECONDS:
        raise ValueError("handoff must have a future bounded expiry")
    handoff = JpycHandoff(handoff_id, amount, network, address, address_fingerprint(address), now, expires_at)
    handoff.validate()
    return handoff


def validate_return(handoff: JpycHandoff, *, now: int, network: str, address: str) -> None:
    if not isinstance(handoff, JpycHandoff):
        raise ValueError("handoff has the wrong runtime type")
    handoff.validate()
    now = _time(now, "return validation time")
    _text(network, "return network")
    _text(address, "return address")
    if now < handoff.created_at or now >= handoff.expires_at:
        raise ValueError("handoff expired or is not yet valid")
    if network != handoff.destination_network or address != handoff.receiving_address:
        raise ValueError("destination changed; handoff is invalid")
    if address_fingerprint(address) != handoff.address_fingerprint:
        raise ValueError("destination fingerprint changed; handoff is invalid")


def reconcile_return(*, on_chain_receipt: bool, application_state: str) -> str:
    if type(on_chain_receipt) is not bool:
        raise ValueError("on-chain receipt flag must be boolean")
    _text(application_state, "application state", maximum=32)
    if application_state not in {"completed", "submitted", "pending", "failed", "not_received"}:
        raise ValueError("unknown handoff application state")
    if on_chain_receipt and application_state == "completed":
        return "RECONCILED"
    if on_chain_receipt or application_state in {"submitted", "pending"}:
        return "PARTIAL_RECONCILIATION_REQUIRED"
    return "NOT_RECEIVED"
