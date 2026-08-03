from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from shared.canonical import CanonicalizationError, canonical_hash, decimal_string, ensure_nfc


_MAX_TEXT = 512
_ACCOUNT_MODELS = {"EOA", "ERC4337", "SPONSORED", "RELAYER"}


def _text(value: object, *, maximum: int = _MAX_TEXT) -> bool:
    if not isinstance(value, str) or not value or len(value) > maximum:
        return False
    try:
        ensure_nfc(value)
    except CanonicalizationError:
        return False
    return not any(ord(char) < 32 or ord(char) == 127 for char in value)


def _strict_bool(value: object) -> bool:
    return type(value) is bool


def _strict_time(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 9_007_199_254_740_991


def _https_terms_url(value: object) -> bool:
    """Accept only an ordinary HTTPS terms origin without authority tricks."""
    if not isinstance(value, str) or not _text(value):
        return False
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and parsed.hostname is not None
            and parsed.username is None
            and parsed.password is None
            and parsed.query == ""
            and parsed.fragment == ""
            and parsed.path not in {"", "."}
            and parsed.port in {None, 443}
        )
    except ValueError:
        return False


@dataclass(frozen=True)
class FeeRouteCapability:
    account_model: str
    network: str
    token_asset_id: str
    provider_id: str
    terms_url: str
    support_route: str
    jurisdiction: str
    settlement_target: str
    supports_zero_native_balance: bool
    evidence_status: str
    evidence_expires_at: int
    revoked: bool
    reviewed: bool
    permit_bootstrap_without_gas: bool
    failure_charge_cap: str
    rate_limit_status: str
    liquidity_status: str


@dataclass(frozen=True)
class OperationBoundQuote:
    quote_id: str
    capability: FeeRouteCapability
    account: str
    operation_id: str
    amount: str
    nonce: str
    expiry: int
    estimated_fee: str
    maximum_fee: str
    failure_charge: str
    signature: str = ""
    signature_valid: bool = False

    @property
    def digest(self) -> str:
        return canonical_hash(
            "fee-route-quote-v1",
            {
                "quoteId": self.quote_id,
                "providerId": self.capability.provider_id,
                "network": self.capability.network,
                "tokenAssetId": self.capability.token_asset_id,
                "account": self.account,
                "operationId": self.operation_id,
                "amount": self.amount,
                "nonce": self.nonce,
                "expiry": self.expiry,
                "estimatedFee": self.estimated_fee,
                "maximumFee": self.maximum_fee,
                "failureCharge": self.failure_charge,
                "settlementTarget": self.capability.settlement_target,
            },
        )


def zero_native_balance_eligible(capability: FeeRouteCapability, quote: OperationBoundQuote | None, *, now: int) -> bool:
    """Return only a boolean and fail closed for every malformed capability/quote."""

    try:
        if not isinstance(capability, FeeRouteCapability) or not isinstance(quote, OperationBoundQuote):
            return False
        if not _strict_time(now):
            return False
        capability_text = (
            capability.account_model,
            capability.network,
            capability.token_asset_id,
            capability.provider_id,
            capability.terms_url,
            capability.support_route,
            capability.jurisdiction,
            capability.settlement_target,
            capability.evidence_status,
            capability.rate_limit_status,
            capability.liquidity_status,
        )
        if not all(_text(value) for value in capability_text):
            return False
        if capability.account_model not in _ACCOUNT_MODELS or not _https_terms_url(capability.terms_url):
            return False
        if not all(
            _strict_bool(value)
            for value in (
                capability.supports_zero_native_balance,
                capability.revoked,
                capability.reviewed,
                capability.permit_bootstrap_without_gas,
            )
        ):
            return False
        if not _strict_time(capability.evidence_expires_at) or now >= capability.evidence_expires_at:
            return False
        if not capability.supports_zero_native_balance:
            return False
        if capability.evidence_status != "VERIFIED" or capability.revoked or not capability.reviewed:
            return False
        if capability.rate_limit_status != "HEALTHY" or capability.liquidity_status != "HEALTHY":
            return False
        if not capability.permit_bootstrap_without_gas:
            return False

        if quote.capability != capability or not _strict_time(quote.expiry) or now >= quote.expiry:
            return False
        if not all(_text(value) for value in (quote.quote_id, quote.account, quote.operation_id, quote.nonce)):
            return False
        if not _text(quote.signature, maximum=4096) or quote.signature_valid is not True:
            return False
        amount = decimal_string(quote.amount)
        estimated_fee = decimal_string(quote.estimated_fee)
        maximum_fee = decimal_string(quote.maximum_fee)
        failure_charge = decimal_string(quote.failure_charge)
        cap = decimal_string(capability.failure_charge_cap)
        if amount <= 0 or maximum_fee < estimated_fee or failure_charge > cap:
            return False
        # decimal_string is non-negative; these explicit comparisons document
        # the intended contract and guard future parser changes.
        if estimated_fee < 0 or maximum_fee < 0 or failure_charge < 0 or cap < 0:
            return False
        _ = quote.digest
        return True
    except (CanonicalizationError, TypeError, ValueError, AttributeError):
        return False


def _manual_fallback(reason: str = "FEE_ROUTE_UNVERIFIED") -> dict[str, object]:
    return {
        "mode": "MANUAL_FALLBACK",
        "reasonCode": reason,
        "recommendedAmount": None,
        "message": "操作に必要な固定金額を確認できないため、まだ送らないでください。",
    }


def fee_readiness_plan(
    *,
    native_balance: str,
    capability: FeeRouteCapability,
    quote: OperationBoundQuote | None,
    now: int,
    expected_account: str | None = None,
    expected_operation_id: str | None = None,
    expected_amount: str | None = None,
) -> dict[str, object]:
    try:
        if not _strict_time(now):
            return _manual_fallback("INVALID_EVALUATION_TIME")
        balance = decimal_string(native_balance)
    except (CanonicalizationError, TypeError):
        return _manual_fallback("INVALID_NATIVE_BALANCE")
    if balance > 0:
        return {"mode": "NO_TOP_UP", "reasonCode": "NATIVE_BALANCE_SUFFICIENT"}

    # A zero-native route is executable only when the caller supplies and the
    # quote exactly matches all operation-bound inputs. Optional omissions must
    # never turn a generic provider quote into authority for a live operation.
    if not all(_text(value) for value in (expected_account, expected_operation_id)):
        return _manual_fallback()
    try:
        if not isinstance(expected_amount, str):
            return _manual_fallback()
        decimal_string(expected_amount)
    except CanonicalizationError:
        return _manual_fallback()
    bound_inputs_match = (
        isinstance(quote, OperationBoundQuote)
        and quote.account == expected_account
        and quote.operation_id == expected_operation_id
        and quote.amount == expected_amount
    )
    if bound_inputs_match and zero_native_balance_eligible(capability, quote, now=now):
        assert quote is not None
        return {
            "mode": "VERIFIED_OPERATION_BOUND_ROUTE",
            "providerId": capability.provider_id,
            "settlementTarget": capability.settlement_target,
            "quoteId": quote.quote_id,
            "quoteDigest": quote.digest,
            "maximumFee": quote.maximum_fee,
            "failureCharge": quote.failure_charge,
            "expiresAt": quote.expiry,
        }
    return _manual_fallback()


@dataclass
class ReimbursementLedger:
    """Idempotent provider charge/reimbursement bookkeeping for fake tests."""

    charged_operations: set[str]
    reimbursed_operations: set[str]

    def __post_init__(self) -> None:
        if not isinstance(self.charged_operations, set) or not isinstance(self.reimbursed_operations, set):
            raise ValueError("ledger collections must be sets")
        if any(not _text(item) for item in self.charged_operations | self.reimbursed_operations):
            raise ValueError("ledger operation id is invalid")
        if not self.reimbursed_operations <= self.charged_operations:
            raise ValueError("reimbursed operation must first be charged")

    def charge_once(self, operation_id: str) -> bool:
        if not _text(operation_id):
            raise ValueError("operation id is invalid")
        if operation_id in self.charged_operations:
            return False
        self.charged_operations.add(operation_id)
        return True

    def reimburse_once(self, operation_id: str) -> bool:
        if not _text(operation_id):
            raise ValueError("operation id is invalid")
        if operation_id not in self.charged_operations or operation_id in self.reimbursed_operations:
            return False
        self.reimbursed_operations.add(operation_id)
        return True
