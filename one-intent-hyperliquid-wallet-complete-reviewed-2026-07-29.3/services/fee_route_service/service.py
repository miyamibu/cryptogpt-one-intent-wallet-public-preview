from __future__ import annotations

from adapters.fee_route.fee import FeeRouteCapability, OperationBoundQuote, fee_readiness_plan


def plan_fee_readiness(native_balance: str, capability: FeeRouteCapability, quote: OperationBoundQuote | None, *, now: int, expected_account: str | None = None, expected_operation_id: str | None = None, expected_amount: str | None = None):
    return fee_readiness_plan(native_balance=native_balance, capability=capability, quote=quote, now=now, expected_account=expected_account, expected_operation_id=expected_operation_id, expected_amount=expected_amount)
