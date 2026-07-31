"""Fail-closed domain objects shared by the offline adapters and tests.

These objects are reference controls, not a production signer or network client.
Every public boundary validates runtime types explicitly so Python coercions
cannot turn malformed untrusted data into executable material.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .canonical import (
    MAX_SAFE_INTEGER,
    CanonicalizationError,
    canonical_bytes,
    canonical_hash,
    decimal_string,
    ensure_nfc,
    validate_alias,
)


MAX_TEXT_FIELD = 256
MAX_SIGNATURE_FIELD = 4096
MAX_DRAFT_UTTERANCE = 2048
MAX_DRAFT_INTERPRETATION = 4096
MAX_PROPOSED_FIELDS = 64
MAX_AMBIGUITIES = 32
MAX_FINAL_PAYLOAD_FIELDS = 128
_CAIP2_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}:[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class DomainError(ValueError):
    pass


class FrozenDict(dict[str, Any]):
    """A JSON-compatible dictionary that cannot be mutated after creation."""

    def _blocked(self, *_args: Any, **_kwargs: Any) -> None:
        raise TypeError("frozen mapping cannot be mutated")

    __setitem__ = _blocked
    __delitem__ = _blocked
    clear = _blocked
    pop = _blocked
    popitem = _blocked
    setdefault = _blocked
    update = _blocked


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return FrozenDict({key: _deep_freeze(child) for key, child in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(child) for child in value)
    return value


class GateStatus(str, Enum):
    NO_GO = "NO_GO"
    BLOCKED_INTERNAL = "BLOCKED_INTERNAL"
    BLOCKED_EXTERNAL = "BLOCKED_EXTERNAL"
    PASS = "PASS"


def _bounded_text(value: Any, label: str, *, maximum: int = MAX_TEXT_FIELD, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise DomainError(f"{label} must be text")
    if (not allow_empty and not value) or len(value) > maximum:
        raise DomainError(f"{label} is missing or oversized")
    try:
        ensure_nfc(value)
    except CanonicalizationError as exc:
        raise DomainError(f"{label} is not canonical text") from exc
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise DomainError(f"{label} contains a control character")
    return value


def _strict_int(value: Any, label: str, *, minimum: int | None = None, maximum: int = MAX_SAFE_INTEGER) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise DomainError(f"{label} must be an integer")
    if value > maximum or (minimum is not None and value < minimum):
        raise DomainError(f"{label} is outside the permitted range")
    return value


def _strict_bool(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise DomainError(f"{label} must be a boolean")
    return value


def _mapping(value: Any, label: str, *, maximum_fields: int) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise DomainError(f"{label} must be an object")
    result = dict(value)
    if len(result) > maximum_fields:
        raise DomainError(f"{label} has too many fields")
    try:
        ensure_nfc(result)
    except CanonicalizationError as exc:
        raise DomainError(f"{label} is not canonical") from exc
    return result


@dataclass(frozen=True)
class ActionPlanDraft:
    source_utterance: str
    normalized_interpretation: str
    proposed: Mapping[str, Any]
    material_ambiguities: tuple[str, ...] = ()
    user_confirmed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.proposed, Mapping):
            raise DomainError("proposed intent must be an object")
        object.__setattr__(self, "proposed", _deep_freeze(self.proposed))

    @property
    def executable(self) -> bool:
        return self.user_confirmed is True and not self.material_ambiguities

    @property
    def intent_commitment(self) -> str:
        self.validate()
        return canonical_hash(
            "intent-draft-v1",
            {
                "sourceUtterance": self.source_utterance,
                "normalizedInterpretation": self.normalized_interpretation,
                "proposed": dict(self.proposed),
                "materialAmbiguities": list(self.material_ambiguities),
                "userConfirmed": self.user_confirmed,
            },
        )

    def validate(self) -> None:
        source = _bounded_text(self.source_utterance, "source utterance", maximum=MAX_DRAFT_UTTERANCE)
        if not source.strip():
            raise DomainError("source utterance must contain visible text")
        interpretation = _bounded_text(
            self.normalized_interpretation,
            "normalized interpretation",
            maximum=MAX_DRAFT_INTERPRETATION,
        )
        if not interpretation.strip():
            raise DomainError("normalized interpretation must contain visible text")
        proposed = _mapping(self.proposed, "proposed intent", maximum_fields=MAX_PROPOSED_FIELDS)
        if not isinstance(self.material_ambiguities, tuple) or len(self.material_ambiguities) > MAX_AMBIGUITIES:
            raise DomainError("material ambiguities must be a bounded tuple")
        ambiguities: list[str] = []
        for ambiguity in self.material_ambiguities:
            text = _bounded_text(ambiguity, "material ambiguity")
            if not text.strip():
                raise DomainError("material ambiguity must contain visible text")
            ambiguities.append(text)
        if len(set(ambiguities)) != len(ambiguities):
            raise DomainError("material ambiguities must be unique")
        _strict_bool(self.user_confirmed, "user confirmation")
        if "alias" in proposed:
            alias = proposed["alias"]
            if not isinstance(alias, str):
                raise DomainError("alias candidate must be text")
            try:
                validate_alias(alias)
            except CanonicalizationError as exc:
                raise DomainError("alias candidate is unsafe") from exc
        if "stopLoss" in proposed:
            raise DomainError("intent parser must not invent stop-loss")
        if ambiguities and self.user_confirmed:
            raise DomainError("ambiguous draft cannot be confirmed")
        canonical_bytes(proposed)

    def confirm(self, resolved_ambiguities: Mapping[str, str], interpretation: str) -> "ActionPlanDraft":
        if not isinstance(resolved_ambiguities, Mapping) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in resolved_ambiguities.items()
        ):
            raise DomainError("resolved ambiguities must be a typed mapping")
        missing = set(self.material_ambiguities) - set(resolved_ambiguities)
        unknown = set(resolved_ambiguities) - set(self.material_ambiguities)
        if missing:
            raise DomainError(f"material ambiguity remains: {sorted(missing)}")
        if unknown:
            raise DomainError(f"unknown ambiguity resolution supplied: {sorted(unknown)}")
        typed = dict(self.proposed)
        for ambiguity, resolution in resolved_ambiguities.items():
            _bounded_text(resolution, f"resolution for {ambiguity}", maximum=512)
            if ambiguity == "方向":
                if resolution not in {"LONG", "SHORT"}:
                    raise DomainError("position side resolution must be LONG or SHORT")
                typed["positionSide"] = resolution
            elif ambiguity == "ネットワーク":
                if not _CAIP2_RE.fullmatch(resolution):
                    raise DomainError("network resolution must be a CAIP-2 identifier")
                typed["network"] = resolution
            elif ambiguity == "ペイパチャルという語の意味":
                if resolution != "PERPETUAL_ORDER":
                    raise DomainError("ambiguous product term must resolve to a typed operation")
                typed["operationType"] = resolution
            elif ambiguity == "生産価格という語の意味":
                if resolution != "LIQUIDATION_PRICE":
                    raise DomainError("ambiguous risk term must resolve to a typed field")
                typed["riskDisplay"] = resolution
            else:
                raise DomainError(f"no typed resolution rule exists for: {ambiguity}")
        confirmed = ActionPlanDraft(
            source_utterance=self.source_utterance,
            normalized_interpretation=interpretation,
            proposed=typed,
            material_ambiguities=(),
            user_confirmed=True,
        )
        confirmed.validate()
        return confirmed


def parse_intent_locally(utterance: str) -> ActionPlanDraft:
    """Small deterministic parser used only to create an untrusted draft."""

    _bounded_text(utterance, "utterance", maximum=MAX_DRAFT_UTTERANCE)
    if not utterance.strip():
        raise DomainError("utterance must contain visible text")
    proposed: dict[str, Any] = {}
    ambiguities: list[str] = []
    if "BTC" in utterance.upper():
        proposed["assetSymbolCandidate"] = "BTC"
    if re.search(r"500\s*USDC", utterance, re.IGNORECASE):
        proposed["amountCandidate"] = "500"
        proposed["quoteAssetCandidate"] = "USDC"
    if "ペイパチャル" in utterance:
        proposed["termCandidate"] = "先物取引（期限なし）"
        ambiguities.append("ペイパチャルという語の意味")
    if "生産価格" in utterance:
        proposed["riskTermCandidate"] = "清算価格"
        ambiguities.append("生産価格という語の意味")
    if not any(word in utterance for word in ("買", "売", "ロング", "ショート")):
        ambiguities.append("方向")
    if not any(word in utterance for word in ("Arbitrum", "HyperEVM", "Testnet", "Mainnet")):
        ambiguities.append("ネットワーク")
    draft = ActionPlanDraft(
        source_utterance=utterance,
        normalized_interpretation="候補を表示しています。意味を確認してください。",
        proposed=proposed,
        material_ambiguities=tuple(ambiguities),
    )
    draft.validate()
    return draft


@dataclass(frozen=True)
class AssetIdentity:
    asset_id: str
    caip2_network: str
    contract: str
    decimals: int
    code_hash: str
    production_eligible: bool = False

    def validate(self, *, expected_asset_id: str | None = None) -> None:
        _bounded_text(self.asset_id, "asset id")
        network = _bounded_text(self.caip2_network, "CAIP-2 network")
        if not _CAIP2_RE.fullmatch(network):
            raise DomainError("asset network is not a bounded CAIP-2 identifier")
        _bounded_text(self.contract, "asset contract", maximum=512)
        _strict_int(self.decimals, "asset decimals", minimum=0, maximum=255)
        _bounded_text(self.code_hash, "asset code hash", maximum=512)
        _strict_bool(self.production_eligible, "asset production eligibility")
        if expected_asset_id is not None and self.asset_id != expected_asset_id:
            raise DomainError("asset registry key differs from embedded asset identity")

    def as_dict(self) -> dict[str, Any]:
        return {
            "assetId": self.asset_id,
            "caip2Network": self.caip2_network,
            "contract": self.contract,
            "decimals": self.decimals,
            "codeHash": self.code_hash,
            "productionEligible": self.production_eligible,
        }


@dataclass(frozen=True)
class SignedRegistry:
    registry_id: str
    sequence: int
    valid_from: int
    expires_at: int
    signer_key_id: str
    signature: str
    signature_valid: bool
    revoked: bool
    entries: Mapping[str, AssetIdentity]

    @property
    def digest(self) -> str:
        payload = {
            "registryId": self.registry_id,
            "sequence": self.sequence,
            "validFrom": self.valid_from,
            "expiresAt": self.expires_at,
            "signerKeyId": self.signer_key_id,
            "entries": {key: value.as_dict() for key, value in self.entries.items()},
        }
        return canonical_hash("asset-registry-v1", payload)

    def verify(self, now: int) -> None:
        _strict_int(now, "registry verification time", minimum=0)
        _bounded_text(self.registry_id, "registry id")
        _strict_int(self.sequence, "registry sequence", minimum=1)
        valid_from = _strict_int(self.valid_from, "registry valid-from", minimum=0)
        expires_at = _strict_int(self.expires_at, "registry expiry", minimum=0)
        _bounded_text(self.signer_key_id, "registry signer key id")
        _bounded_text(self.signature, "registry signature", maximum=MAX_SIGNATURE_FIELD)
        _strict_bool(self.signature_valid, "registry signature validity")
        _strict_bool(self.revoked, "registry revoked flag")
        if valid_from >= expires_at:
            raise DomainError("asset registry validity interval is invalid")
        if not self.signature_valid:
            raise DomainError("asset registry signature is invalid")
        if self.revoked:
            raise DomainError("asset registry is revoked")
        if now < valid_from or now >= expires_at:
            raise DomainError("asset registry is stale or not yet valid")
        if not isinstance(self.entries, Mapping) or not 1 <= len(self.entries) <= 4096:
            raise DomainError("asset registry entries are missing or excessive")
        for key, entry in self.entries.items():
            _bounded_text(key, "asset registry key")
            if not isinstance(entry, AssetIdentity):
                raise DomainError("asset registry entry has the wrong runtime type")
            entry.validate(expected_asset_id=key)
        # Force the complete signed material through canonicalization after all
        # runtime type checks; this also applies the shared resource limits.
        _ = self.digest

    def resolve(self, asset_id: str, network: str, now: int, *, production: bool) -> AssetIdentity:
        _bounded_text(asset_id, "requested asset id")
        _bounded_text(network, "requested network")
        _strict_bool(production, "production mode")
        self.verify(now)
        entry = self.entries.get(asset_id)
        if entry is None or entry.caip2_network != network:
            raise DomainError("asset or network identity mismatch")
        if production and not entry.production_eligible:
            raise DomainError("asset is not production eligible")
        return entry


@dataclass(frozen=True)
class CanonicalQuote:
    quote_id: str
    provider_id: str
    route_id: str
    network: str
    asset_id: str
    account: str
    amount: str
    max_fee: str
    fee_asset: str
    settlement_target: str
    generated_at: int
    expires_at: int
    execution_capsule_hash: str
    final_payload_commitment: str
    signature: str
    signature_valid: bool
    provider_revoked: bool = False

    def payload(self) -> dict[str, Any]:
        return {
            "quoteId": self.quote_id,
            "providerId": self.provider_id,
            "routeId": self.route_id,
            "network": self.network,
            "assetId": self.asset_id,
            "account": self.account,
            "amount": self.amount,
            "maxFee": self.max_fee,
            "feeAsset": self.fee_asset,
            "settlementTarget": self.settlement_target,
            "generatedAt": self.generated_at,
            "expiresAt": self.expires_at,
            "executionCapsuleHash": self.execution_capsule_hash,
            "finalPayloadCommitment": self.final_payload_commitment,
        }

    @property
    def digest(self) -> str:
        # The binding digest intentionally excludes the capsule commitment to
        # avoid a circular hash. The complete signed quote document remains
        # available through full_digest and the signer must verify both.
        binding_payload = self.payload()
        binding_payload.pop("executionCapsuleHash", None)
        return canonical_hash("canonical-quote-binding-v1", binding_payload)

    @property
    def full_digest(self) -> str:
        return canonical_hash("canonical-quote-v1", self.payload())

    def verify(self, now: int, *, network: str, asset_id: str, account: str, amount: str) -> None:
        _strict_int(now, "quote verification time", minimum=0)
        identity_fields = {
            "quote id": self.quote_id,
            "provider id": self.provider_id,
            "route id": self.route_id,
            "network": self.network,
            "asset id": self.asset_id,
            "account": self.account,
            "fee asset": self.fee_asset,
            "settlement target": self.settlement_target,
            "execution capsule hash": self.execution_capsule_hash,
            "final payload commitment": self.final_payload_commitment,
        }
        for label, value in identity_fields.items():
            _bounded_text(value, label, maximum=512)
        _bounded_text(self.signature, "quote signature", maximum=MAX_SIGNATURE_FIELD)
        generated_at = _strict_int(self.generated_at, "quote generated-at", minimum=0)
        expires_at = _strict_int(self.expires_at, "quote expiry", minimum=0)
        _strict_bool(self.signature_valid, "quote signature validity")
        _strict_bool(self.provider_revoked, "quote provider revoked flag")
        _bounded_text(network, "expected quote network")
        _bounded_text(asset_id, "expected quote asset")
        _bounded_text(account, "expected quote account")
        if not isinstance(amount, str):
            raise DomainError("expected quote amount must be text")
        try:
            expected_amount = decimal_string(amount)
            quote_amount = decimal_string(self.amount)
            max_fee = decimal_string(self.max_fee)
        except CanonicalizationError as exc:
            raise DomainError("quote decimal field is invalid") from exc
        if generated_at >= expires_at:
            raise DomainError("quote validity interval is invalid")
        if not self.signature_valid:
            raise DomainError("quote signature is invalid")
        if self.provider_revoked:
            raise DomainError("quote provider is revoked")
        if now < generated_at or now >= expires_at:
            raise DomainError("quote is expired or not yet valid")
        if (self.network, self.asset_id, self.account, self.amount) != (network, asset_id, account, amount):
            raise DomainError("quote binding mismatch")
        if quote_amount <= 0 or expected_amount <= 0:
            raise DomainError("quote amount must be positive")
        if max_fee < 0:
            raise DomainError("quote maximum fee must be non-negative")
        _ = self.full_digest


@dataclass(frozen=True)
class ExecutionCapsule:
    operation_type: str
    account: str
    device_id: str
    intent_commitment: str
    network: str
    asset_id: str
    amount: str
    recipient: str | None
    ordered_actions: tuple[str, ...]
    registry_digest: str
    quote_id: str
    quote_digest: str
    final_payload: Mapping[str, Any]
    expires_at: int

    @property
    def material(self) -> dict[str, Any]:
        return {
            "operationType": self.operation_type,
            "account": self.account,
            "deviceId": self.device_id,
            "intentCommitment": self.intent_commitment,
            "network": self.network,
            "assetId": self.asset_id,
            "amount": self.amount,
            "recipient": self.recipient,
            "orderedActions": list(self.ordered_actions),
            "registryDigest": self.registry_digest,
            "quoteId": self.quote_id,
            "quoteDigest": self.quote_digest,
            "finalPayload": dict(self.final_payload),
            "expiresAt": self.expires_at,
        }

    @property
    def hash(self) -> str:
        return canonical_hash("execution-capsule-v1", self.material)

    def validate(self, now: int) -> None:
        _strict_int(now, "capsule verification time", minimum=0)
        identity_fields = {
            "operation type": self.operation_type,
            "account": self.account,
            "device id": self.device_id,
            "intent commitment": self.intent_commitment,
            "network": self.network,
            "asset id": self.asset_id,
            "registry digest": self.registry_digest,
            "quote id": self.quote_id,
            "quote digest": self.quote_digest,
        }
        for label, value in identity_fields.items():
            _bounded_text(value, f"capsule {label}")
        if not isinstance(self.amount, str):
            raise DomainError("capsule amount must be text")
        try:
            amount = decimal_string(self.amount)
        except CanonicalizationError as exc:
            raise DomainError("capsule amount is invalid") from exc
        if amount <= 0:
            raise DomainError("capsule amount must be positive")
        if self.recipient is not None:
            _bounded_text(self.recipient, "capsule recipient", maximum=512)
        if not isinstance(self.ordered_actions, tuple) or not 1 <= len(self.ordered_actions) <= 32:
            raise DomainError("capsule actions are missing or excessive")
        actions: list[str] = []
        for action in self.ordered_actions:
            actions.append(_bounded_text(action, "capsule action", maximum=128))
        if len(set(actions)) != len(actions):
            raise DomainError("capsule actions are duplicated")
        payload = _mapping(self.final_payload, "capsule final payload", maximum_fields=MAX_FINAL_PAYLOAD_FIELDS)
        expiry = _strict_int(self.expires_at, "capsule expiry", minimum=0)
        if now >= expiry:
            raise DomainError("capsule is expired")
        payload_amount = payload.get("amount")
        if payload_amount is not None and (not isinstance(payload_amount, str) or payload_amount != self.amount):
            raise DomainError("final payload amount differs from capsule")
        canonical_bytes(self.material)


_LIVE_STATE_REQUIRED = {
    "operationType",
    "account",
    "deviceId",
    "intentCommitment",
    "network",
    "assetId",
    "amount",
    "orderedActions",
    "finalPayload",
    "expiresAt",
}
_LIVE_STATE_ALLOWED = _LIVE_STATE_REQUIRED | {"recipient"}


def compile_capsule(
    draft: ActionPlanDraft,
    *,
    live_state: Mapping[str, Any],
    registry: SignedRegistry,
    quote: CanonicalQuote,
    now: int,
    production: bool = False,
) -> ExecutionCapsule:
    if not isinstance(draft, ActionPlanDraft):
        raise DomainError("draft has the wrong runtime type")
    if not isinstance(registry, SignedRegistry) or not isinstance(quote, CanonicalQuote):
        raise DomainError("registry and quote runtime types are required")
    _strict_int(now, "capsule compilation time", minimum=0)
    _strict_bool(production, "production mode")
    draft.validate()
    if not draft.executable:
        raise DomainError("user confirmation and ambiguity resolution are required")
    state = _mapping(live_state, "live state", maximum_fields=len(_LIVE_STATE_ALLOWED))
    missing = _LIVE_STATE_REQUIRED - set(state)
    unknown = set(state) - _LIVE_STATE_ALLOWED
    if missing or unknown:
        raise DomainError(f"live state keys mismatch; missing={sorted(missing)}, unknown={sorted(unknown)}")

    operation_type = _bounded_text(state["operationType"], "live operation type")
    account = _bounded_text(state["account"], "live account")
    device_id = _bounded_text(state["deviceId"], "live device id")
    network = _bounded_text(state["network"], "live network")
    asset_id = _bounded_text(state["assetId"], "live asset id")
    amount = state["amount"]
    if not isinstance(amount, str):
        raise DomainError("live amount must be text")
    try:
        decimal_string(amount)
    except CanonicalizationError as exc:
        raise DomainError("live amount is invalid") from exc
    if state["intentCommitment"] != draft.intent_commitment:
        raise DomainError("live state is not bound to the confirmed intent")

    proposed_amount = draft.proposed.get("amountCandidate")
    if proposed_amount is not None:
        if not isinstance(proposed_amount, str) or amount != proposed_amount:
            raise DomainError("live amount differs from confirmed intent")
    proposed_asset = draft.proposed.get("assetSymbolCandidate")
    if proposed_asset is not None:
        if not isinstance(proposed_asset, str):
            raise DomainError("confirmed asset candidate has the wrong type")
        base_asset = re.split(r"[-/:]", asset_id, maxsplit=1)[0]
        if base_asset.upper() != proposed_asset.upper():
            raise DomainError("live asset differs from confirmed intent")

    recipient = state.get("recipient")
    if recipient is not None and not isinstance(recipient, str):
        raise DomainError("live recipient must be text or null")
    actions_value = state["orderedActions"]
    if not isinstance(actions_value, (list, tuple)) or any(not isinstance(item, str) for item in actions_value):
        raise DomainError("live ordered actions must be a text array")
    ordered_actions = tuple(actions_value)
    payload = _mapping(state["finalPayload"], "live final payload", maximum_fields=MAX_FINAL_PAYLOAD_FIELDS)
    expires_at = _strict_int(state["expiresAt"], "live expiry", minimum=0)

    registry.resolve(asset_id, network, now, production=production)
    quote.verify(now, network=network, asset_id=asset_id, account=account, amount=amount)
    payload_commitment = canonical_hash("final-payload-v1", payload)
    if quote.final_payload_commitment != payload_commitment:
        raise DomainError("final payload commitment mismatch")
    capsule = ExecutionCapsule(
        operation_type=operation_type,
        account=account,
        device_id=device_id,
        intent_commitment=draft.intent_commitment,
        network=network,
        asset_id=asset_id,
        amount=amount,
        recipient=recipient,
        ordered_actions=ordered_actions,
        registry_digest=registry.digest,
        quote_id=quote.quote_id,
        quote_digest=quote.digest,
        final_payload=payload,
        expires_at=min(expires_at, quote.expires_at),
    )
    capsule.validate(now)
    if quote.execution_capsule_hash != capsule.hash:
        raise DomainError("quote is not bound to exact execution capsule")
    return capsule


@dataclass(frozen=True)
class PolicyInput:
    global_write_disabled: bool
    feature_enabled: bool
    account_model: str
    native_balance: str
    route_verified: bool
    route_expiry: int | None
    now: int


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason_code: str
    japanese_message: str


def evaluate_policy(value: PolicyInput) -> PolicyDecision:
    try:
        if not isinstance(value, PolicyInput):
            raise DomainError("policy input has the wrong runtime type")
        _strict_bool(value.global_write_disabled, "global write flag")
        _strict_bool(value.feature_enabled, "feature flag")
        _strict_bool(value.route_verified, "route verified flag")
        _bounded_text(value.account_model, "account model", maximum=32)
        _strict_int(value.now, "policy time", minimum=0)
        if value.route_expiry is not None:
            _strict_int(value.route_expiry, "route expiry", minimum=0)
        if not isinstance(value.native_balance, str):
            raise DomainError("native balance must be text")
        balance = decimal_string(value.native_balance)
    except (DomainError, CanonicalizationError):
        return PolicyDecision(False, "INVALID_POLICY_INPUT", "入力を確認できないため停止しました。")

    if value.global_write_disabled:
        return PolicyDecision(False, "GLOBAL_WRITE_DISABLED", "現在は送信を停止しています。")
    if not value.feature_enabled:
        return PolicyDecision(False, "FEATURE_DISABLED", "この機能はまだ利用できません。")
    if value.account_model not in {"EOA", "ERC4337", "SPONSORED", "RELAYER"}:
        return PolicyDecision(False, "UNKNOWN_ACCOUNT_MODEL", "アカウント方式を確認できません。")
    if balance == 0:
        if not value.route_verified:
            return PolicyDecision(False, "FEE_ROUTE_UNVERIFIED", "手数料ルートを確認できません。手動確認に戻ります。")
        if value.route_expiry is None:
            return PolicyDecision(False, "FEE_ROUTE_EXPIRY_MISSING", "手数料ルートの期限を確認できません。")
        if value.now >= value.route_expiry:
            return PolicyDecision(False, "FEE_ROUTE_EXPIRED", "手数料ルートの期限が切れています。")
    return PolicyDecision(True, "POLICY_ALLOWED", "確認画面へ進めます。")


@dataclass(frozen=True)
class AuthorizationEnvelope:
    authorization_id: str
    device_id: str
    account: str
    capsule_hash: str
    operation_type: str
    issued_at: int
    expires_at: int
    nonce: str
    user_review_digest: str
    proof_of_possession: str

    @property
    def expected_proof_of_possession(self) -> str:
        return canonical_hash(
            "dpop-proof-v1",
            {
                "authorizationId": self.authorization_id,
                "deviceId": self.device_id,
                "account": self.account,
                "capsuleHash": self.capsule_hash,
                "nonce": self.nonce,
            },
        )

    def validate(self, now: int, capsule: ExecutionCapsule) -> None:
        _strict_int(now, "authorization verification time", minimum=0)
        if not isinstance(capsule, ExecutionCapsule):
            raise DomainError("authorization capsule has the wrong runtime type")
        capsule.validate(now)
        fields = {
            "authorization id": self.authorization_id,
            "device id": self.device_id,
            "account": self.account,
            "capsule hash": self.capsule_hash,
            "operation type": self.operation_type,
            "nonce": self.nonce,
            "user review digest": self.user_review_digest,
        }
        for label, value in fields.items():
            _bounded_text(value, f"authorization {label}")
        _bounded_text(self.proof_of_possession, "authorization proof", maximum=MAX_SIGNATURE_FIELD)
        issued_at = _strict_int(self.issued_at, "authorization issued-at", minimum=0)
        expires_at = _strict_int(self.expires_at, "authorization expiry", minimum=0)
        lifetime = expires_at - issued_at
        if now < issued_at or now >= expires_at or not 0 < lifetime <= 120:
            raise DomainError("authorization is not current or lifetime exceeds 120 seconds")
        if expires_at > capsule.expires_at:
            raise DomainError("authorization outlives the execution capsule")
        if self.device_id != capsule.device_id or self.account != capsule.account:
            raise DomainError("authorization device/account mismatch")
        if self.capsule_hash != capsule.hash or self.operation_type != capsule.operation_type:
            raise DomainError("authorization capsule mismatch")
        if self.proof_of_possession != self.expected_proof_of_possession:
            raise DomainError("sender-constrained proof binding is invalid")


class DurableAuthorizationStore:
    """SQLite reference for atomic single-use reservation.

    Production still requires a separately administered durable store and
    rollback-resistant fencing; this local store is not production evidence.
    """

    persistent = True

    def __init__(self, path: str) -> None:
        if not isinstance(path, str) or not path:
            raise DomainError("authorization store path is required")
        self._connection = sqlite3.connect(path, timeout=5.0, isolation_level=None)
        self._closed = False
        try:
            self._connection.execute("PRAGMA trusted_schema=OFF")
            self._connection.execute("PRAGMA foreign_keys=ON")
            self._connection.execute("PRAGMA busy_timeout=5000")
            self._connection.execute("PRAGMA synchronous=FULL")
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS consumed_authorization "
                "(authorization_id TEXT PRIMARY KEY, nonce TEXT NOT NULL UNIQUE, "
                "operation_fingerprint TEXT NOT NULL UNIQUE)"
            )
            self._verify_schema()
        except Exception:
            self._connection.close()
            self._closed = True
            raise

    def _verify_schema(self) -> None:
        rows = list(self._connection.execute("PRAGMA table_info(consumed_authorization)"))
        if len(rows) != 3 or [row[1] for row in rows] != ["authorization_id", "nonce", "operation_fingerprint"]:
            raise DomainError("authorization store schema is unsafe or requires explicit migration")
        if any(str(row[2]).upper() != "TEXT" for row in rows) or rows[0][5] != 1 or any(row[3] != 1 for row in rows[1:]):
            raise DomainError("authorization store columns or primary key are unsafe")
        unique_columns: set[str] = set()
        for index in self._connection.execute("PRAGMA index_list(consumed_authorization)"):
            # seq, name, unique, origin, partial
            if index[2] != 1 or (len(index) > 4 and index[4] != 0):
                continue
            columns = [row[2] for row in self._connection.execute(f'PRAGMA index_info("{index[1]}")')]
            if len(columns) == 1:
                unique_columns.add(columns[0])
        if not {"nonce", "operation_fingerprint"}.issubset(unique_columns):
            raise DomainError("authorization store nonce or operation uniqueness is missing")
        triggers = list(
            self._connection.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='consumed_authorization'"
            )
        )
        if triggers:
            raise DomainError("authorization store must not contain triggers")
        integrity = self._connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            raise DomainError("authorization store integrity check failed")

    def reserve(self, authorization_id: str, nonce: str, operation_fingerprint: str) -> bool:
        _bounded_text(authorization_id, "authorization store id")
        _bounded_text(nonce, "authorization store nonce")
        _bounded_text(operation_fingerprint, "operation fingerprint")
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            self._connection.execute(
                "INSERT INTO consumed_authorization "
                "(authorization_id, nonce, operation_fingerprint) VALUES (?, ?, ?)",
                (authorization_id, nonce, operation_fingerprint),
            )
            self._connection.execute("COMMIT")
            return True
        except sqlite3.IntegrityError:
            self._connection.execute("ROLLBACK")
            return False
        except Exception:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise

    def close(self) -> None:
        if not self._closed:
            self._connection.close()
            self._closed = True

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass


class MemoryAuthorizationStore:
    persistent = False

    def __init__(self) -> None:
        self._authorization_ids: set[str] = set()
        self._nonces: set[str] = set()
        self._operation_fingerprints: set[str] = set()

    def reserve(self, authorization_id: str, nonce: str, operation_fingerprint: str) -> bool:
        _bounded_text(authorization_id, "authorization store id")
        _bounded_text(nonce, "authorization store nonce")
        _bounded_text(operation_fingerprint, "operation fingerprint")
        if (
            authorization_id in self._authorization_ids
            or nonce in self._nonces
            or operation_fingerprint in self._operation_fingerprints
        ):
            return False
        self._authorization_ids.add(authorization_id)
        self._nonces.add(nonce)
        self._operation_fingerprints.add(operation_fingerprint)
        return True


class SignerState(str, Enum):
    READY = "READY"
    SIGNED_BROADCAST_UNKNOWN = "SIGNED_BROADCAST_UNKNOWN"
    BROADCAST_ACCEPTED_UNCONFIRMED = "BROADCAST_ACCEPTED_UNCONFIRMED"
    CONFIRMED = "CONFIRMED"
    REJECTED_BEFORE_EFFECT = "REJECTED_BEFORE_EFFECT"
    PARTIAL = "PARTIAL"
    MANUAL_RESOLUTION_REQUIRED = "MANUAL_RESOLUTION_REQUIRED"


class SignerGate:
    """No-key reference signer: enforces authorization consumption and state."""

    _NEW_OPERATION_ALLOWED = {
        SignerState.READY,
        SignerState.CONFIRMED,
        SignerState.REJECTED_BEFORE_EFFECT,
    }

    def __init__(self, *, store: DurableAuthorizationStore | MemoryAuthorizationStore | None = None, require_durable_store: bool = False) -> None:
        self._store = store or MemoryAuthorizationStore()
        self._require_durable_store = _strict_bool(require_durable_store, "durable store requirement")
        self.state = SignerState.READY
        self.last_signed_hash: str | None = None

    def sign(
        self,
        capsule: ExecutionCapsule,
        authorization: AuthorizationEnvelope,
        *,
        release_go: bool,
        runtime_lease_valid: bool,
        now: int,
        fail_after_sign: bool = False,
    ) -> bytes:
        _strict_bool(release_go, "release GO")
        _strict_bool(runtime_lease_valid, "runtime lease validity")
        _strict_bool(fail_after_sign, "fail-after-sign test flag")
        _strict_int(now, "signer time", minimum=0)
        if not release_go:
            raise DomainError("current release GO is required")
        if not runtime_lease_valid:
            raise DomainError("current runtime lease is required")
        if self._require_durable_store and not self._store.persistent:
            raise DomainError("durable authorization store is required")
        if self.state not in self._NEW_OPERATION_ALLOWED:
            raise DomainError("prior signed operation requires authoritative reconciliation")
        if not isinstance(capsule, ExecutionCapsule) or not isinstance(authorization, AuthorizationEnvelope):
            raise DomainError("capsule and authorization runtime types are required")
        capsule.validate(now)
        authorization.validate(now, capsule)
        if not self._store.reserve(authorization.authorization_id, authorization.nonce, capsule.hash):
            raise DomainError("authorization, nonce, or operation replay")
        signed = canonical_bytes({"capsuleHash": capsule.hash, "authorizationId": authorization.authorization_id})
        self.last_signed_hash = canonical_hash("signed-operation-v1", {"bytes": signed.hex()})
        if fail_after_sign:
            self.state = SignerState.SIGNED_BROADCAST_UNKNOWN
            raise RuntimeError("crash after signing; broadcast state is unknown")
        self.state = SignerState.BROADCAST_ACCEPTED_UNCONFIRMED
        return signed

    def reconcile(self, outcome: str) -> SignerState:
        _bounded_text(outcome, "reconciliation outcome", maximum=32)
        allowed = {
            "confirmed": SignerState.CONFIRMED,
            "rejected": SignerState.REJECTED_BEFORE_EFFECT,
            "partial": SignerState.PARTIAL,
            "unknown": SignerState.MANUAL_RESOLUTION_REQUIRED,
        }
        if outcome not in allowed:
            raise DomainError("unknown reconciliation outcome")
        if self.state in self._NEW_OPERATION_ALLOWED:
            raise DomainError("there is no pending signed operation to reconcile")
        if self.state == SignerState.PARTIAL and outcome == "rejected":
            raise DomainError("a partially effective operation cannot be rejected before effect")
        self.state = allowed[outcome]
        return self.state


class SagaStepState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    FINALIZED = "FINALIZED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass
class SagaStep:
    step_id: str
    idempotency_key: str
    state: SagaStepState = SagaStepState.NOT_STARTED
    external_reference: str | None = None
    precondition_hash: str = ""


@dataclass
class DurableSaga:
    operation_id: str
    steps: list[SagaStep] = field(default_factory=list)

    def __post_init__(self) -> None:
        _bounded_text(self.operation_id, "saga operation id")
        if not isinstance(self.steps, list):
            raise DomainError("saga steps must be a list")
        seen_steps: set[str] = set()
        seen_keys: set[str] = set()
        for step in self.steps:
            if not isinstance(step, SagaStep):
                raise DomainError("saga step has the wrong runtime type")
            _bounded_text(step.step_id, "saga step id")
            _bounded_text(step.idempotency_key, "saga idempotency key")
            if step.step_id in seen_steps or step.idempotency_key in seen_keys:
                raise DomainError("saga contains duplicate step or idempotency key")
            seen_steps.add(step.step_id)
            seen_keys.add(step.idempotency_key)

    def submit(self, step_id: str, idempotency_key: str, external_reference: str) -> SagaStep:
        _bounded_text(step_id, "saga step id")
        _bounded_text(idempotency_key, "saga idempotency key")
        _bounded_text(external_reference, "saga external reference", maximum=512)
        for step in self.steps:
            if step.idempotency_key == idempotency_key:
                if step.step_id != step_id or step.external_reference != external_reference:
                    raise DomainError("idempotency key was reused with different material")
                return step
            if step.step_id == step_id:
                raise DomainError("saga step id was reused with a different idempotency key")
        step = SagaStep(
            step_id=step_id,
            idempotency_key=idempotency_key,
            state=SagaStepState.SUBMITTED,
            external_reference=external_reference,
        )
        step.precondition_hash = canonical_hash(
            "saga-precondition-v1",
            {
                "operationId": self.operation_id,
                "stepId": step_id,
                "idempotencyKey": idempotency_key,
                "externalReference": external_reference,
            },
        )
        self.steps.append(step)
        return step

    def reconcile(self, step_id: str, authoritative_state: SagaStepState) -> SagaStep:
        _bounded_text(step_id, "saga step id")
        if not isinstance(authoritative_state, SagaStepState):
            raise DomainError("authoritative saga state has the wrong runtime type")
        transitions = {
            SagaStepState.NOT_STARTED: {SagaStepState.SUBMITTED, SagaStepState.FAILED},
            SagaStepState.SUBMITTED: {SagaStepState.ACCEPTED, SagaStepState.FINALIZED, SagaStepState.FAILED, SagaStepState.UNKNOWN},
            SagaStepState.ACCEPTED: {SagaStepState.FINALIZED, SagaStepState.FAILED, SagaStepState.UNKNOWN},
            SagaStepState.UNKNOWN: {SagaStepState.ACCEPTED, SagaStepState.FINALIZED, SagaStepState.FAILED, SagaStepState.UNKNOWN},
            SagaStepState.FINALIZED: {SagaStepState.FINALIZED},
            SagaStepState.FAILED: {SagaStepState.FAILED},
        }
        for step in self.steps:
            if step.step_id == step_id:
                if authoritative_state not in transitions[step.state]:
                    raise DomainError("invalid or backward saga state transition")
                step.state = authoritative_state
                return step
        raise DomainError("unknown saga step")
