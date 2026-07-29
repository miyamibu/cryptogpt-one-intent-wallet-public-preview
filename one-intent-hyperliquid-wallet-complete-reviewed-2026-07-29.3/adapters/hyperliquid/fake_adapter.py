from __future__ import annotations

from dataclasses import dataclass

from shared.canonical import CanonicalizationError, decimal_string, ensure_nfc
from shared.domain import DomainError


def _text(value: object, label: str, *, maximum: int = 256) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise DomainError(f"{label} is missing or oversized")
    try:
        ensure_nfc(value)
    except CanonicalizationError as exc:
        raise DomainError(f"{label} is not canonical text") from exc
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise DomainError(f"{label} contains a control character")
    return value


@dataclass
class FakeOrder:
    account: str
    client_id: str
    market_id: str
    side: str
    amount: str
    state: str = "accepted"
    filled_amount: str = "0"
    liquidation_price: str | None = None
    reference_price_age_seconds: int | None = None


class FakeHyperliquidAdapter:
    """Simulates protocol states without signing or contacting a network."""

    def __init__(self, *, testnet_write_enabled: bool = False) -> None:
        if type(testnet_write_enabled) is not bool:
            raise DomainError("fake Testnet write gate must be a boolean")
        self.testnet_write_enabled = testnet_write_enabled
        self.orders: dict[str, FakeOrder] = {}
        self.emergency_cancel_enabled = True

    def read_account(self, account: str) -> dict[str, object]:
        _text(account, "account")
        visible = sorted(client_id for client_id, order in self.orders.items() if order.account == account)
        return {"account": account, "source": "fake", "confirmed": True, "positions": [], "orders": visible}

    def place_order(self, *, account: str, market_id: str, side: str, amount: str, client_id: str) -> FakeOrder:
        if not self.testnet_write_enabled:
            raise DomainError("fake Testnet write gate is disabled")
        account = _text(account, "account")
        market_id = _text(market_id, "market identity")
        client_id = _text(client_id, "client id")
        if side not in {"buy", "sell"}:
            raise DomainError("side must be buy or sell")
        if not isinstance(amount, str):
            raise DomainError("order amount must be text")
        try:
            parsed_amount = decimal_string(amount)
        except CanonicalizationError as exc:
            raise DomainError("order amount is invalid") from exc
        if parsed_amount <= 0:
            raise DomainError("order amount must be positive")
        existing = self.orders.get(client_id)
        if existing is not None:
            if (existing.account, existing.market_id, existing.side, existing.amount) != (account, market_id, side, amount):
                raise DomainError("client id was reused with different order material")
            return existing
        order = FakeOrder(account, client_id, market_id, side, amount)
        self.orders[client_id] = order
        return order

    def cancel_all(self) -> list[str]:
        if type(self.emergency_cancel_enabled) is not bool or not self.emergency_cancel_enabled:
            raise DomainError("emergency cancel is disabled")
        for order in self.orders.values():
            if order.state in {"accepted", "partial"}:
                order.state = "cancelled"
        return sorted(self.orders)

    def apply_fill(
        self,
        client_id: str,
        filled_amount: str,
        *,
        liquidation_price: str | None,
        reference_price_age_seconds: int | None,
    ) -> FakeOrder:
        _text(client_id, "client id")
        order = self.orders.get(client_id)
        if order is None:
            raise DomainError("unknown client id")
        if order.state in {"cancelled", "filled"}:
            raise DomainError("terminal order cannot receive another fill")
        if not isinstance(filled_amount, str):
            raise DomainError("filled amount must be text")
        try:
            filled = decimal_string(filled_amount)
            total = decimal_string(order.amount)
        except CanonicalizationError as exc:
            raise DomainError("filled amount is invalid") from exc
        if filled < 0 or filled > total:
            raise DomainError("filled amount is outside the order amount")
        if liquidation_price is not None:
            if not isinstance(liquidation_price, str):
                raise DomainError("liquidation price must be text or null")
            try:
                if decimal_string(liquidation_price) <= 0:
                    raise DomainError("liquidation price must be positive")
            except CanonicalizationError as exc:
                raise DomainError("liquidation price is invalid") from exc
        if reference_price_age_seconds is not None and (
            not isinstance(reference_price_age_seconds, int)
            or isinstance(reference_price_age_seconds, bool)
            or reference_price_age_seconds < 0
        ):
            raise DomainError("reference price age must be a non-negative integer or null")
        order.filled_amount = filled_amount
        if filled == total:
            order.state = "filled"
        elif filled == 0:
            order.state = "accepted"
        else:
            order.state = "partial"
        order.liquidation_price = liquidation_price
        order.reference_price_age_seconds = reference_price_age_seconds
        return order

    def validate_perpetual_review(self, client_id: str, *, now_age_limit: int = 10) -> None:
        _text(client_id, "client id")
        if not isinstance(now_age_limit, int) or isinstance(now_age_limit, bool) or now_age_limit < 0:
            raise DomainError("reference price age limit must be a non-negative integer")
        order = self.orders.get(client_id)
        if order is None:
            raise DomainError("unknown client id")
        if order.liquidation_price is None or order.reference_price_age_seconds is None:
            raise DomainError("liquidation or reference price data is unavailable")
        try:
            if decimal_string(order.liquidation_price) <= 0:
                raise DomainError("liquidation price is invalid")
        except CanonicalizationError as exc:
            raise DomainError("liquidation price is invalid") from exc
        if order.reference_price_age_seconds < 0 or order.reference_price_age_seconds > now_age_limit:
            raise DomainError("reference price is stale")
