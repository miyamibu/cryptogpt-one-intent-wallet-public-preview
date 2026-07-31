"""Protected V2 atomic-signer validation and durable authorization journal.

This module deliberately contains no private key, signing implementation,
broadcaster, provider client, or network connection.  It is the final
pre-signing boundary: exact canonical bytes are decoded, pinned schemas and
signatures are verified, signer-owned context is enforced, and replay claims
are durably reserved before a caller may proceed to a separately implemented
signer.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Protocol

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .canonical import (
    CANONICAL_PROFILE_VERSION,
    canonical_bytes,
    canonical_decimal_string,
    canonical_hash,
    canonical_network_address,
    ensure_nfc,
    strict_loads_bytes,
)
from .signature_trust_store import SignatureTrustStore, VerifierRole


SCHEMA_VERSION = "2.1"
_SCHEMA_ROOT = Path(__file__).resolve().parents[1] / "schemas"
_SCHEMA_FILES = (
    "atomic-signer-request-v2.schema.json",
    "operation-spec-v2.schema.json",
    "user-review-receipt-v2.schema.json",
    "runtime-decision-envelope-v2.schema.json",
)
PINNED_V2_1_SCHEMA_SHA256: Mapping[str, str] = MappingProxyType(
    {
        "atomic-signer-request-v2.schema.json": "24fd0c1adf87ce0f84266a422a7dd9041d4eb4202e64a449e1e988f99000e2eb",
        "operation-spec-v2.schema.json": "36810a0b178e5e0c792efaeea2d22b03ab938d14a24ef2098ff458e4c9d1c979",
        "user-review-receipt-v2.schema.json": "d90ad287e061ff9c19b73990c120d4b06f54032e6d743fd2dc452e3e11fc74c2",
        "runtime-decision-envelope-v2.schema.json": "e531ed703d56faff4937b94aee658632c7bbc6aece6aa455764dd6d28107b11a",
    }
)

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_TRUST_BOOLEAN_KEYS = frozenset(
    {
        "allowed",
        "release_go",
        "runtime_lease_valid",
        "server_verified",
        "signature_valid",
        "trust_valid",
        "verified",
    }
)
_SIGNED_FIELDS = frozenset({"canonicalDigest", "signature"})


class AtomicSignerContractError(ValueError):
    """The request cannot cross the protected signer boundary."""


class ReplayDetectedError(AtomicSignerContractError):
    """A durable one-time claim was already consumed."""


class ClockRollbackError(AtomicSignerContractError):
    """The signer clock moved behind its durable high-water mark."""


class UnresolvedOperationError(AtomicSignerContractError):
    """A prior signing operation requires reconciliation before proceeding."""


class OperationType(str, Enum):
    TRANSFER = "TRANSFER"
    SWAP = "SWAP"
    PERP_OPEN = "PERP_OPEN"
    PERP_CLOSE = "PERP_CLOSE"
    VAULT_DEPOSIT = "VAULT_DEPOSIT"
    VAULT_WITHDRAW = "VAULT_WITHDRAW"
    CANCEL = "CANCEL"
    REVOKE_AUTHORIZATION = "REVOKE_AUTHORIZATION"


class OperationAction(str, Enum):
    TRANSFER = "TRANSFER"
    SWAP = "SWAP"
    PERP_OPEN = "PERP_OPEN"
    PERP_CLOSE = "PERP_CLOSE"
    VAULT_DEPOSIT = "VAULT_DEPOSIT"
    VAULT_WITHDRAW = "VAULT_WITHDRAW"
    CANCEL = "CANCEL"
    REVOKE_AUTHORIZATION = "REVOKE_AUTHORIZATION"


class JournalState(str, Enum):
    AUTHORIZATION_RESERVED = "AUTHORIZATION_RESERVED"
    SIGNING_INTENT_RECORDED = "SIGNING_INTENT_RECORDED"
    SIGNED_BROADCAST_UNKNOWN = "SIGNED_BROADCAST_UNKNOWN"
    BROADCAST_INTENT_RECORDED = "BROADCAST_INTENT_RECORDED"
    BROADCAST_CONFIRMED = "BROADCAST_CONFIRMED"
    FINALIZED = "FINALIZED"
    ABORTED_BEFORE_SIGNING = "ABORTED_BEFORE_SIGNING"


_TERMINAL_STATES = frozenset(
    {JournalState.FINALIZED.value, JournalState.ABORTED_BEFORE_SIGNING.value}
)
_ALLOWED_TRANSITIONS: Mapping[JournalState, frozenset[JournalState]] = MappingProxyType(
    {
        JournalState.AUTHORIZATION_RESERVED: frozenset(
            {JournalState.SIGNING_INTENT_RECORDED, JournalState.ABORTED_BEFORE_SIGNING}
        ),
        JournalState.SIGNING_INTENT_RECORDED: frozenset(
            {JournalState.SIGNED_BROADCAST_UNKNOWN}
        ),
        JournalState.SIGNED_BROADCAST_UNKNOWN: frozenset(
            {JournalState.BROADCAST_INTENT_RECORDED}
        ),
        JournalState.BROADCAST_INTENT_RECORDED: frozenset(
            {JournalState.BROADCAST_CONFIRMED}
        ),
        JournalState.BROADCAST_CONFIRMED: frozenset({JournalState.FINALIZED}),
    }
)


class SignerClock(Protocol):
    """Clock installed when the signer boundary starts."""

    def wall_time(self) -> int: ...

    def monotonic_ns(self) -> int: ...


@dataclass(frozen=True)
class SystemSignerClock:
    def wall_time(self) -> int:
        return int(time.time())

    def monotonic_ns(self) -> int:
        return time.monotonic_ns()


@dataclass(frozen=True)
class AssetRule:
    asset_id: str
    decimals: int
    allowed_networks: frozenset[str]
    token_contract: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.asset_id, str) or not self.asset_id:
            raise ValueError("asset rule id is required")
        if (
            not isinstance(self.decimals, int)
            or isinstance(self.decimals, bool)
            or not 0 <= self.decimals <= 38
        ):
            raise ValueError("asset decimals must be between 0 and 38")
        networks = frozenset(self.allowed_networks)
        if not networks or any(not isinstance(value, str) or not value for value in networks):
            raise ValueError("asset rule must contain allowed network identifiers")
        object.__setattr__(self, "allowed_networks", networks)
        if self.token_contract is not None:
            for network in networks:
                canonical_network_address(network, self.token_contract)


@dataclass(frozen=True)
class AtomicSignerConfiguration:
    expected_audience: str
    expected_environment: str
    expected_deployment: str
    expected_release_subject_digest: str
    expected_policy_bundle_digest: str
    asset_registry: Mapping[str, AssetRule]
    schema_sha256: Mapping[str, str] = field(
        default_factory=lambda: PINNED_V2_1_SCHEMA_SHA256
    )
    maximum_request_ttl_seconds: int = 120
    maximum_review_ttl_seconds: int = 300
    maximum_decision_ttl_seconds: int = 300
    maximum_operation_ttl_seconds: int = 300
    allowed_clock_skew_seconds: int = 5
    maximum_clock_rollback_seconds: int = 5

    def __post_init__(self) -> None:
        for name in (
            "expected_audience",
            "expected_environment",
            "expected_deployment",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} is required")
        if self.expected_environment not in {"STAGING", "TESTNET", "PRODUCTION"}:
            raise ValueError("expected environment is unsupported")
        for name in (
            "expected_release_subject_digest",
            "expected_policy_bundle_digest",
        ):
            if not _DIGEST_RE.fullmatch(getattr(self, name)):
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")
        limits = (
            self.maximum_request_ttl_seconds,
            self.maximum_review_ttl_seconds,
            self.maximum_decision_ttl_seconds,
            self.maximum_operation_ttl_seconds,
        )
        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 1 <= value <= 300
            for value in limits
        ):
            raise ValueError("signer TTL limits must be between 1 and 300 seconds")
        for name in ("allowed_clock_skew_seconds", "maximum_clock_rollback_seconds"):
            value = getattr(self, name)
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 30
            ):
                raise ValueError(f"{name} must be between 0 and 30 seconds")
        schema_hashes = dict(self.schema_sha256)
        if schema_hashes != dict(PINNED_V2_1_SCHEMA_SHA256):
            raise ValueError("signer schema pin set does not match V2.1")
        object.__setattr__(self, "schema_sha256", MappingProxyType(schema_hashes))
        assets: dict[str, AssetRule] = {}
        for key, rule in self.asset_registry.items():
            if not isinstance(rule, AssetRule) or key != rule.asset_id or key in assets:
                raise ValueError("asset registry entries must be keyed by their asset id")
            assets[key] = rule
        if not assets:
            raise ValueError("signer asset registry must not be empty")
        object.__setattr__(self, "asset_registry", MappingProxyType(assets))


@dataclass(frozen=True)
class TransferDetails:
    amount: Decimal
    recipient: bytes
    token_contract: bytes
    fee: Decimal
    fee_recipient: bytes


@dataclass(frozen=True)
class SwapDetails:
    amount: Decimal
    output_asset_id: str
    minimum_output: Decimal
    maximum_slippage_bps: int
    fee: Decimal
    fee_recipient: bytes


@dataclass(frozen=True)
class PerpOpenDetails:
    amount: Decimal
    side: str
    leverage: int
    margin_mode: str
    maximum_slippage_bps: int
    reduce_only: bool


@dataclass(frozen=True)
class PerpCloseDetails:
    amount: Decimal
    side: str
    position_id: str
    maximum_slippage_bps: int
    reduce_only: bool


@dataclass(frozen=True)
class VaultDepositDetails:
    amount: Decimal
    vault_id: str


@dataclass(frozen=True)
class VaultWithdrawDetails:
    amount: Decimal
    vault_id: str
    recipient: bytes


@dataclass(frozen=True)
class CancelDetails:
    target_operation_id: str
    market_id: str


@dataclass(frozen=True)
class RevokeAuthorizationDetails:
    authorization_id: str
    authorization_key_id: str


OperationDetails = (
    TransferDetails
    | SwapDetails
    | PerpOpenDetails
    | PerpCloseDetails
    | VaultDepositDetails
    | VaultWithdrawDetails
    | CancelDetails
    | RevokeAuthorizationDetails
)


@dataclass(frozen=True)
class TypedOperationSpec:
    operation_id: str
    operation_type: OperationType
    account: bytes
    network: str
    asset_id: str
    ordered_actions: tuple[OperationAction, ...]
    details: OperationDetails
    payload_commitment: str
    expires_at: int


@dataclass(frozen=True)
class JournalReservation:
    operation_id: str
    operation_sequence: int
    fencing_token: int
    state: JournalState


@dataclass(frozen=True)
class JournalOperation:
    operation_id: str
    request_id: str
    authorization_id: str
    nonce: str
    payload_digest: str
    operation_sequence: int
    fencing_token: int
    state: JournalState
    updated_at: int


@dataclass(frozen=True)
class VerifiedAtomicSignerRequest:
    request_id: str
    authorization_id: str
    nonce: str
    operation_spec_digest: str
    review_receipt_digest: str
    runtime_decision_digest: str
    canonical_digest: str
    operation: TypedOperationSpec
    reservation: JournalReservation
    request: Mapping[str, Any]


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AtomicSignerContractError(f"{label} must be an object")
    ensure_nfc(value)
    return value


def _integer(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise AtomicSignerContractError(f"{label} must be a non-negative integer")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise AtomicSignerContractError(f"{label} must be non-empty text")
    ensure_nfc(value)
    return value


def _reject_trust_booleans(value: Any, path: str = "request") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise AtomicSignerContractError(f"{path} contains a non-text key")
            if key.lower() in _TRUST_BOOLEAN_KEYS:
                raise AtomicSignerContractError(
                    f"caller-supplied trust field is prohibited: {path}.{key}"
                )
            _reject_trust_booleans(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_trust_booleans(child, f"{path}[{index}]")


def _signed_material(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in envelope.items() if key not in _SIGNED_FIELDS}


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(child) for child in value)
    return value


def _load_pinned_validator(
    expected_hashes: Mapping[str, str],
) -> Draft202012Validator:
    schemas: dict[str, Mapping[str, Any]] = {}
    resources: list[tuple[str, Resource[Any]]] = []
    for filename in _SCHEMA_FILES:
        path = _SCHEMA_ROOT / filename
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise AtomicSignerContractError(f"pinned schema cannot be read: {filename}") from exc
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected_hashes.get(filename):
            raise AtomicSignerContractError(f"pinned schema digest mismatch: {filename}")
        try:
            schema = json.loads(raw.decode("utf-8", errors="strict"))
            Draft202012Validator.check_schema(schema)
            resource = Resource.from_contents(schema)
        except Exception as exc:
            raise AtomicSignerContractError(f"pinned schema is invalid: {filename}") from exc
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise AtomicSignerContractError(f"pinned schema has no id: {filename}")
        schemas[filename] = schema
        resources.append((schema_id, resource))
    registry = Registry().with_resources(resources)
    return Draft202012Validator(
        schemas["atomic-signer-request-v2.schema.json"],
        registry=registry,
    )


def _validate_schema(validator: Draft202012Validator, request: Mapping[str, Any]) -> None:
    errors = sorted(
        validator.iter_errors(request),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if not errors:
        return
    error = errors[0]
    location = ".".join(str(part) for part in error.absolute_path) or "request"
    raise AtomicSignerContractError(f"V2.1 schema rejected {location}: {error.message}")


def _asset_rule(
    configuration: AtomicSignerConfiguration,
    asset_id: str,
    network: str,
) -> AssetRule:
    rule = configuration.asset_registry.get(asset_id)
    if rule is None or network not in rule.allowed_networks:
        raise AtomicSignerContractError("operation asset is not allowed on the selected network")
    return rule


def _positive_decimal(value: Any, label: str, *, scale: int) -> Decimal:
    try:
        parsed = canonical_decimal_string(value, scale=scale)
    except (TypeError, ValueError) as exc:
        raise AtomicSignerContractError(f"{label} is not canonical") from exc
    if parsed <= 0:
        raise AtomicSignerContractError(f"{label} must be greater than zero")
    return parsed


def _nonnegative_decimal(value: Any, label: str, *, scale: int) -> Decimal:
    try:
        return canonical_decimal_string(value, scale=scale)
    except (TypeError, ValueError) as exc:
        raise AtomicSignerContractError(f"{label} is not canonical") from exc


def _typed_operation(
    value: Mapping[str, Any],
    configuration: AtomicSignerConfiguration,
) -> TypedOperationSpec:
    try:
        operation_type = OperationType(value["operationType"])
        actions = tuple(OperationAction(item) for item in value["orderedActions"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AtomicSignerContractError("operation type or ordered actions are unsupported") from exc
    if actions != (OperationAction(operation_type.value),):
        raise AtomicSignerContractError("ordered actions do not match the typed operation")
    network = _text(value.get("network"), "operation network")
    account = canonical_network_address(
        network,
        _text(value.get("account"), "operation account"),
    )
    asset_id = _text(value.get("assetId"), "operation asset id")
    asset = _asset_rule(configuration, asset_id, network)
    details = _mapping(value.get("operationDetails"), "operation details")

    if operation_type is OperationType.TRANSFER:
        token_contract_text = _text(details.get("tokenContract"), "transfer token contract")
        if asset.token_contract is not None and token_contract_text != asset.token_contract:
            raise AtomicSignerContractError("transfer token contract does not match the asset registry")
        typed_details: OperationDetails = TransferDetails(
            amount=_positive_decimal(details.get("amount"), "transfer amount", scale=asset.decimals),
            recipient=canonical_network_address(
                network, _text(details.get("recipient"), "transfer recipient")
            ),
            token_contract=canonical_network_address(network, token_contract_text),
            fee=_nonnegative_decimal(details.get("fee"), "transfer fee", scale=asset.decimals),
            fee_recipient=canonical_network_address(
                network, _text(details.get("feeRecipient"), "transfer fee recipient")
            ),
        )
    elif operation_type is OperationType.SWAP:
        output_asset_id = _text(details.get("outputAssetId"), "swap output asset")
        output_asset = _asset_rule(configuration, output_asset_id, network)
        typed_details = SwapDetails(
            amount=_positive_decimal(details.get("amount"), "swap amount", scale=asset.decimals),
            output_asset_id=output_asset_id,
            minimum_output=_positive_decimal(
                details.get("minimumOutput"),
                "swap minimum output",
                scale=output_asset.decimals,
            ),
            maximum_slippage_bps=_integer(
                details.get("maximumSlippageBps"), "swap maximum slippage"
            ),
            fee=_nonnegative_decimal(details.get("fee"), "swap fee", scale=asset.decimals),
            fee_recipient=canonical_network_address(
                network, _text(details.get("feeRecipient"), "swap fee recipient")
            ),
        )
    elif operation_type is OperationType.PERP_OPEN:
        typed_details = PerpOpenDetails(
            amount=_positive_decimal(details.get("amount"), "perp open amount", scale=asset.decimals),
            side=_text(details.get("side"), "perp open side"),
            leverage=_integer(details.get("leverage"), "perp open leverage"),
            margin_mode=_text(details.get("marginMode"), "perp open margin mode"),
            maximum_slippage_bps=_integer(
                details.get("maximumSlippageBps"), "perp open maximum slippage"
            ),
            reduce_only=False,
        )
    elif operation_type is OperationType.PERP_CLOSE:
        typed_details = PerpCloseDetails(
            amount=_positive_decimal(details.get("amount"), "perp close amount", scale=asset.decimals),
            side=_text(details.get("side"), "perp close side"),
            position_id=_text(details.get("positionId"), "perp position id"),
            maximum_slippage_bps=_integer(
                details.get("maximumSlippageBps"), "perp close maximum slippage"
            ),
            reduce_only=True,
        )
    elif operation_type is OperationType.VAULT_DEPOSIT:
        typed_details = VaultDepositDetails(
            amount=_positive_decimal(details.get("amount"), "vault deposit amount", scale=asset.decimals),
            vault_id=_text(details.get("vaultId"), "vault id"),
        )
    elif operation_type is OperationType.VAULT_WITHDRAW:
        typed_details = VaultWithdrawDetails(
            amount=_positive_decimal(details.get("amount"), "vault withdrawal amount", scale=asset.decimals),
            vault_id=_text(details.get("vaultId"), "vault id"),
            recipient=canonical_network_address(
                network, _text(details.get("recipient"), "vault withdrawal recipient")
            ),
        )
    elif operation_type is OperationType.CANCEL:
        typed_details = CancelDetails(
            target_operation_id=_text(
                details.get("targetOperationId"), "cancel target operation id"
            ),
            market_id=_text(details.get("marketId"), "cancel market id"),
        )
    else:
        typed_details = RevokeAuthorizationDetails(
            authorization_id=_text(
                details.get("authorizationId"), "revoked authorization id"
            ),
            authorization_key_id=_text(
                details.get("authorizationKeyId"), "revoked authorization key id"
            ),
        )

    return TypedOperationSpec(
        operation_id=_text(value.get("operationId"), "operation id"),
        operation_type=operation_type,
        account=account,
        network=network,
        asset_id=asset_id,
        ordered_actions=actions,
        details=typed_details,
        payload_commitment=_text(value.get("payloadCommitment"), "payload commitment"),
        expires_at=_integer(value.get("expiresAt"), "operation expiresAt"),
    )


def _validate_window(
    label: str,
    *,
    issued_at: int,
    not_before: int,
    expires_at: int,
    now: int,
    maximum_ttl: int,
    allowed_skew: int,
) -> None:
    if issued_at >= expires_at or not_before >= expires_at:
        raise AtomicSignerContractError(f"{label} time ordering is invalid")
    if expires_at - issued_at > maximum_ttl:
        raise AtomicSignerContractError(f"{label} TTL exceeds signer policy")
    if issued_at > now + allowed_skew or not_before > now + allowed_skew:
        raise AtomicSignerContractError(f"{label} is future-dated")
    if expires_at <= now - allowed_skew:
        raise AtomicSignerContractError(f"{label} is expired")


class SQLiteOperationJournal:
    """SQLite-backed replay reservation and crash-recovery state machine."""

    def __init__(self, path: str | Path) -> None:
        if isinstance(path, Path):
            path = str(path)
        if not isinstance(path, str) or not path:
            raise ValueError("journal path is required")
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(
            path,
            timeout=5.0,
            isolation_level=None,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        with self._lock:
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA synchronous = FULL")
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS journal_meta (
                    key TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS operations (
                    operation_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL UNIQUE,
                    authorization_id TEXT NOT NULL UNIQUE,
                    nonce TEXT NOT NULL UNIQUE,
                    payload_digest TEXT NOT NULL,
                    operation_sequence INTEGER NOT NULL UNIQUE,
                    fencing_token INTEGER NOT NULL UNIQUE,
                    state TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS replay_claims (
                    claim_type TEXT NOT NULL,
                    claim_value TEXT NOT NULL,
                    operation_id TEXT NOT NULL,
                    PRIMARY KEY (claim_type, claim_value),
                    FOREIGN KEY (operation_id) REFERENCES operations(operation_id)
                );
                CREATE TABLE IF NOT EXISTS operation_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT NOT NULL,
                    operation_sequence INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    state TEXT NOT NULL,
                    payload_digest TEXT NOT NULL,
                    observed_at INTEGER NOT NULL,
                    UNIQUE (operation_id, operation_sequence),
                    FOREIGN KEY (operation_id) REFERENCES operations(operation_id)
                );
                """
            )

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def _meta(self, key: str, default: int) -> int:
        row = self._connection.execute(
            "SELECT value FROM journal_meta WHERE key = ?",
            (key,),
        ).fetchone()
        return default if row is None else int(row["value"])

    def _set_meta(self, key: str, value: int) -> None:
        self._connection.execute(
            """
            INSERT INTO journal_meta(key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )

    def assert_clock(self, observed_at: int, maximum_clock_rollback_seconds: int) -> None:
        with self._lock:
            high_water = self._meta("high_water_wall_time", observed_at)
        if observed_at + maximum_clock_rollback_seconds < high_water:
            raise ClockRollbackError(
                "signer wall clock is behind the durable high-water mark"
            )

    def reserve(
        self,
        verified: "_VerifiedWithoutReservation",
        *,
        observed_at: int,
        maximum_clock_rollback_seconds: int,
    ) -> JournalReservation:
        with self._lock:
            try:
                self._connection.execute("BEGIN IMMEDIATE")
                high_water = self._meta("high_water_wall_time", observed_at)
                if observed_at + maximum_clock_rollback_seconds < high_water:
                    raise ClockRollbackError(
                        "signer wall clock is behind the durable high-water mark"
                    )
                self._set_meta("high_water_wall_time", max(observed_at, high_water))

                claims = {
                    "requestId": verified.request_id,
                    "authorizationId": verified.authorization_id,
                    "nonce": verified.nonce,
                    "operationId": verified.operation.operation_id,
                    "operationSpecDigest": verified.operation_spec_digest,
                }
                for claim_type, claim_value in claims.items():
                    row = self._connection.execute(
                        """
                        SELECT operation_id FROM replay_claims
                        WHERE claim_type = ? AND claim_value = ?
                        """,
                        (claim_type, claim_value),
                    ).fetchone()
                    if row is not None:
                        raise ReplayDetectedError(
                            f"durable replay claim already consumed: {claim_type}"
                        )

                unresolved = self._connection.execute(
                    f"""
                    SELECT operation_id FROM operations
                    WHERE state NOT IN ({",".join("?" for _ in _TERMINAL_STATES)})
                    LIMIT 1
                    """,
                    tuple(sorted(_TERMINAL_STATES)),
                ).fetchone()
                if unresolved is not None:
                    raise UnresolvedOperationError(
                        "an unresolved signer operation requires reconciliation"
                    )

                sequence = self._meta("next_operation_sequence", 1)
                fencing_token = self._meta("next_fencing_token", 1)
                self._set_meta("next_operation_sequence", sequence + 1)
                self._set_meta("next_fencing_token", fencing_token + 1)
                state = JournalState.AUTHORIZATION_RESERVED
                self._connection.execute(
                    """
                    INSERT INTO operations(
                        operation_id, request_id, authorization_id, nonce,
                        payload_digest, operation_sequence, fencing_token,
                        state, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        verified.operation.operation_id,
                        verified.request_id,
                        verified.authorization_id,
                        verified.nonce,
                        verified.operation.payload_commitment,
                        sequence,
                        fencing_token,
                        state.value,
                        observed_at,
                        observed_at,
                    ),
                )
                self._connection.executemany(
                    """
                    INSERT INTO replay_claims(claim_type, claim_value, operation_id)
                    VALUES (?, ?, ?)
                    """,
                    (
                        (claim_type, claim_value, verified.operation.operation_id)
                        for claim_type, claim_value in claims.items()
                    ),
                )
                self._connection.execute(
                    """
                    INSERT INTO operation_events(
                        operation_id, operation_sequence, event_type, state,
                        payload_digest, observed_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        verified.operation.operation_id,
                        1,
                        "AUTHORIZATION_RESERVED",
                        state.value,
                        verified.operation.payload_commitment,
                        observed_at,
                    ),
                )
                self._connection.execute("COMMIT")
                return JournalReservation(
                    operation_id=verified.operation.operation_id,
                    operation_sequence=sequence,
                    fencing_token=fencing_token,
                    state=state,
                )
            except Exception:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                raise

    def transition(
        self,
        operation_id: str,
        *,
        fencing_token: int,
        expected_state: JournalState,
        new_state: JournalState,
        event_type: str,
        payload_digest: str,
        observed_at: int,
    ) -> JournalOperation:
        allowed = _ALLOWED_TRANSITIONS.get(expected_state, frozenset())
        if new_state not in allowed:
            raise ValueError("journal state transition is not allowed")
        if not _DIGEST_RE.fullmatch(payload_digest):
            raise ValueError("journal payload digest must be a lowercase SHA-256 digest")
        with self._lock:
            try:
                self._connection.execute("BEGIN IMMEDIATE")
                row = self._connection.execute(
                    "SELECT * FROM operations WHERE operation_id = ?",
                    (operation_id,),
                ).fetchone()
                if (
                    row is None
                    or int(row["fencing_token"]) != fencing_token
                    or row["state"] != expected_state.value
                ):
                    raise AtomicSignerContractError(
                        "journal operation, fencing token, or expected state mismatch"
                    )
                event_sequence = int(
                    self._connection.execute(
                        """
                        SELECT COALESCE(MAX(operation_sequence), 0) + 1 AS next
                        FROM operation_events WHERE operation_id = ?
                        """,
                        (operation_id,),
                    ).fetchone()["next"]
                )
                self._connection.execute(
                    """
                    UPDATE operations
                    SET state = ?, payload_digest = ?, updated_at = ?
                    WHERE operation_id = ?
                    """,
                    (new_state.value, payload_digest, observed_at, operation_id),
                )
                self._connection.execute(
                    """
                    INSERT INTO operation_events(
                        operation_id, operation_sequence, event_type, state,
                        payload_digest, observed_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        operation_id,
                        event_sequence,
                        event_type,
                        new_state.value,
                        payload_digest,
                        observed_at,
                    ),
                )
                self._connection.execute("COMMIT")
            except Exception:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                raise
        return self.operation(operation_id)

    def operation(self, operation_id: str) -> JournalOperation:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM operations WHERE operation_id = ?",
                (operation_id,),
            ).fetchone()
        if row is None:
            raise KeyError(operation_id)
        return JournalOperation(
            operation_id=str(row["operation_id"]),
            request_id=str(row["request_id"]),
            authorization_id=str(row["authorization_id"]),
            nonce=str(row["nonce"]),
            payload_digest=str(row["payload_digest"]),
            operation_sequence=int(row["operation_sequence"]),
            fencing_token=int(row["fencing_token"]),
            state=JournalState(str(row["state"])),
            updated_at=int(row["updated_at"]),
        )

    def unresolved_operations(self) -> tuple[JournalOperation, ...]:
        placeholders = ",".join("?" for _ in _TERMINAL_STATES)
        with self._lock:
            rows = self._connection.execute(
                f"""
                SELECT operation_id FROM operations
                WHERE state NOT IN ({placeholders})
                ORDER BY operation_sequence
                """,
                tuple(sorted(_TERMINAL_STATES)),
            ).fetchall()
        return tuple(self.operation(str(row["operation_id"])) for row in rows)


@dataclass(frozen=True)
class _VerifiedWithoutReservation:
    request_id: str
    authorization_id: str
    nonce: str
    operation_spec_digest: str
    review_receipt_digest: str
    runtime_decision_digest: str
    canonical_digest: str
    operation: TypedOperationSpec
    request: Mapping[str, Any]


class AtomicSignerBoundary:
    """Signer-owned validation context; callers supply only request bytes."""

    def __init__(
        self,
        *,
        configuration: AtomicSignerConfiguration,
        trust_store: SignatureTrustStore,
        journal: SQLiteOperationJournal,
        clock: SignerClock | None = None,
    ) -> None:
        if not isinstance(configuration, AtomicSignerConfiguration):
            raise ValueError("protected signer configuration is required")
        if not isinstance(trust_store, SignatureTrustStore):
            raise ValueError("protected signature trust store is required")
        if not isinstance(journal, SQLiteOperationJournal):
            raise ValueError("durable signer journal is required")
        installed_clock = SystemSignerClock() if clock is None else clock
        if not callable(getattr(installed_clock, "wall_time", None)) or not callable(
            getattr(installed_clock, "monotonic_ns", None)
        ):
            raise ValueError("signer-owned clock is invalid")
        self._configuration = configuration
        self._trust_store = trust_store
        self._journal = journal
        self._clock = installed_clock
        self._schema_validator = _load_pinned_validator(configuration.schema_sha256)
        self._clock_lock = threading.Lock()
        self._last_monotonic_ns: int | None = None

    def _read_clock(self) -> tuple[int, int]:
        wall = self._clock.wall_time()
        monotonic = self._clock.monotonic_ns()
        if (
            not isinstance(wall, int)
            or isinstance(wall, bool)
            or wall < 0
            or not isinstance(monotonic, int)
            or isinstance(monotonic, bool)
            or monotonic < 0
        ):
            raise ClockRollbackError("signer clock returned an invalid reading")
        with self._clock_lock:
            if self._last_monotonic_ns is not None and monotonic < self._last_monotonic_ns:
                raise ClockRollbackError("signer monotonic clock moved backwards")
            self._last_monotonic_ns = monotonic
        return wall, monotonic

    def validate_and_reserve(self, raw_request: bytes) -> VerifiedAtomicSignerRequest:
        try:
            parsed = strict_loads_bytes(raw_request, require_canonical=True)
        except (TypeError, ValueError) as exc:
            raise AtomicSignerContractError(
                "atomic signer request is not exact canonical UTF-8 JSON"
            ) from exc
        request = _mapping(parsed, "atomic signer request")
        _reject_trust_booleans(request)
        _validate_schema(self._schema_validator, request)
        if request.get("schemaVersion") != SCHEMA_VERSION:
            raise AtomicSignerContractError("unknown atomic signer schema version")
        if request.get("canonicalProfile") != CANONICAL_PROFILE_VERSION:
            raise AtomicSignerContractError("unknown atomic signer canonical profile")

        wall_now, _ = self._read_clock()
        configuration = self._configuration
        self._journal.assert_clock(
            wall_now,
            configuration.maximum_clock_rollback_seconds,
        )
        operation = _mapping(request.get("operationSpec"), "operation spec")
        review = _mapping(request.get("reviewReceipt"), "review receipt")
        decision = _mapping(request.get("runtimeDecision"), "runtime decision")
        typed_operation = _typed_operation(operation, configuration)

        operation_digest = canonical_hash("operation-spec-v2", operation)
        review_digest = canonical_hash("user-review-receipt-v2", review)
        decision_digest = canonical_hash("runtime-decision-envelope-v2", decision)
        digest_bindings = (
            (request.get("operationSpecDigest"), operation_digest, "operation spec"),
            (request.get("reviewReceiptDigest"), review_digest, "review receipt"),
            (request.get("runtimeDecisionDigest"), decision_digest, "runtime decision"),
            (review.get("operationSpecDigest"), operation_digest, "review operation"),
            (decision.get("operationSpecDigest"), operation_digest, "decision operation"),
            (decision.get("reviewReceiptDigest"), review_digest, "decision review"),
        )
        for actual, expected, label in digest_bindings:
            if actual != expected:
                raise AtomicSignerContractError(f"{label} digest binding mismatch")

        account_text = _text(operation.get("account"), "operation account")
        for label, envelope in (
            ("request", request),
            ("review", review),
            ("runtime decision", decision),
        ):
            if envelope.get("subject") != account_text:
                raise AtomicSignerContractError(f"{label} subject is not the operation account")

        for review_field, operation_field in (
            ("displayDigest", "displayManifestDigest"),
            ("quoteDigest", "quoteDigest"),
            ("sourceStateDigest", "sourceStateDigest"),
            ("finalPayloadDigest", "payloadCommitment"),
        ):
            if review.get(review_field) != operation.get(operation_field):
                raise AtomicSignerContractError(
                    f"review {review_field} is not bound to operation {operation_field}"
                )

        expected_context = {
            "audience": configuration.expected_audience,
            "environment": configuration.expected_environment,
            "deployment": configuration.expected_deployment,
        }
        for field_name, expected in expected_context.items():
            for label, envelope in (
                ("request", request),
                ("review", review),
                ("runtime decision", decision),
            ):
                if envelope.get(field_name) != expected:
                    raise AtomicSignerContractError(
                        f"{label} {field_name} does not match signer configuration"
                    )
        if (
            decision.get("releaseSubjectDigest")
            != configuration.expected_release_subject_digest
        ):
            raise AtomicSignerContractError("release subject does not match signer configuration")
        if decision.get("policyBundleDigest") != configuration.expected_policy_bundle_digest:
            raise AtomicSignerContractError("policy bundle does not match signer configuration")

        requested_at = _integer(request.get("requestedAt"), "requestedAt")
        request_not_before = _integer(request.get("notBefore"), "request notBefore")
        request_expires_at = _integer(request.get("expiresAt"), "request expiresAt")
        reviewed_at = _integer(review.get("reviewedAt"), "reviewedAt")
        review_not_before = _integer(review.get("notBefore"), "review notBefore")
        review_expires_at = _integer(review.get("expiresAt"), "review expiresAt")
        issued_at = _integer(decision.get("issuedAt"), "decision issuedAt")
        decision_not_before = _integer(decision.get("notBefore"), "decision notBefore")
        evaluated_at = _integer(decision.get("evaluatedAt"), "decision evaluatedAt")
        decision_expires_at = _integer(decision.get("expiresAt"), "decision expiresAt")
        _validate_window(
            "atomic signer request",
            issued_at=requested_at,
            not_before=request_not_before,
            expires_at=request_expires_at,
            now=wall_now,
            maximum_ttl=configuration.maximum_request_ttl_seconds,
            allowed_skew=configuration.allowed_clock_skew_seconds,
        )
        _validate_window(
            "review receipt",
            issued_at=reviewed_at,
            not_before=review_not_before,
            expires_at=review_expires_at,
            now=wall_now,
            maximum_ttl=configuration.maximum_review_ttl_seconds,
            allowed_skew=configuration.allowed_clock_skew_seconds,
        )
        if not issued_at <= decision_not_before <= evaluated_at:
            raise AtomicSignerContractError("runtime decision evaluation ordering is invalid")
        _validate_window(
            "runtime decision",
            issued_at=issued_at,
            not_before=decision_not_before,
            expires_at=decision_expires_at,
            now=wall_now,
            maximum_ttl=configuration.maximum_decision_ttl_seconds,
            allowed_skew=configuration.allowed_clock_skew_seconds,
        )
        if typed_operation.expires_at - requested_at > configuration.maximum_operation_ttl_seconds:
            raise AtomicSignerContractError("operation TTL exceeds signer policy")
        if min(
            typed_operation.expires_at,
            review_expires_at,
            decision_expires_at,
        ) < request_expires_at:
            raise AtomicSignerContractError(
                "request outlives an embedded authorization object"
            )

        status = decision.get("status")
        reasons = decision.get("blockingReasons")
        if status != "ELIGIBLE_FOR_ATOMIC_SIGNER_FINALIZATION" or reasons != []:
            raise AtomicSignerContractError("runtime decision is not eligible for finalization")

        common_scope = {
            "audience": configuration.expected_audience,
            "environment": configuration.expected_environment,
            "deployment": configuration.expected_deployment,
            "now": wall_now,
        }
        self._verify_envelope_signature(
            review,
            domain="user-review-receipt-v2",
            required_role=VerifierRole.HUMAN_REVIEW,
            **common_scope,
        )
        self._verify_envelope_signature(
            decision,
            domain="runtime-decision-envelope-v2",
            required_role=VerifierRole.RUNTIME_POLICY,
            policy_bundle_digest=configuration.expected_policy_bundle_digest,
            release_subject_digest=configuration.expected_release_subject_digest,
            **common_scope,
        )
        request_digest = self._verify_envelope_signature(
            request,
            domain="atomic-signer-request-v2",
            required_role=VerifierRole.ORCHESTRATION,
            policy_bundle_digest=configuration.expected_policy_bundle_digest,
            release_subject_digest=configuration.expected_release_subject_digest,
            **common_scope,
        )

        verified = _VerifiedWithoutReservation(
            request_id=_text(request.get("requestId"), "request ID"),
            authorization_id=_text(request.get("authorizationId"), "authorization ID"),
            nonce=_text(request.get("nonce"), "nonce"),
            operation_spec_digest=operation_digest,
            review_receipt_digest=review_digest,
            runtime_decision_digest=decision_digest,
            canonical_digest=request_digest,
            operation=typed_operation,
            request=_freeze(request),
        )
        reservation = self._journal.reserve(
            verified,
            observed_at=wall_now,
            maximum_clock_rollback_seconds=configuration.maximum_clock_rollback_seconds,
        )
        return VerifiedAtomicSignerRequest(
            request_id=verified.request_id,
            authorization_id=verified.authorization_id,
            nonce=verified.nonce,
            operation_spec_digest=verified.operation_spec_digest,
            review_receipt_digest=verified.review_receipt_digest,
            runtime_decision_digest=verified.runtime_decision_digest,
            canonical_digest=verified.canonical_digest,
            operation=verified.operation,
            reservation=reservation,
            request=verified.request,
        )

    def _verify_envelope_signature(
        self,
        envelope: Mapping[str, Any],
        *,
        domain: str,
        required_role: VerifierRole,
        audience: str,
        environment: str,
        deployment: str,
        now: int,
        policy_bundle_digest: str | None = None,
        release_subject_digest: str | None = None,
    ) -> str:
        material = _signed_material(envelope)
        expected = canonical_hash(domain, material)
        if envelope.get("canonicalDigest") != expected:
            raise AtomicSignerContractError(f"{domain} canonical digest mismatch")
        try:
            verified = self._trust_store.verify(
                _text(envelope.get("issuer"), f"{domain} issuer"),
                _text(envelope.get("keyId"), f"{domain} key ID"),
                _text(
                    envelope.get("signatureAlgorithm"),
                    f"{domain} signature algorithm",
                ),
                domain.encode("utf-8") + b"\x00" + canonical_bytes(material),
                _text(envelope.get("signature"), f"{domain} signature"),
                _integer(
                    envelope.get("revocationEpoch"),
                    f"{domain} revocation epoch",
                ),
                domain=domain,
                required_role=required_role,
                audience=audience,
                environment=environment,
                deployment=deployment,
                policy_bundle_digest=policy_bundle_digest,
                release_subject_digest=release_subject_digest,
                now=now,
            )
        except Exception as exc:
            raise AtomicSignerContractError(
                f"{domain} signature verifier failed closed"
            ) from exc
        if verified is not True:
            raise AtomicSignerContractError(
                f"{domain} signature or trust scope is not valid"
            )
        return expected


def validate_atomic_signer_request(
    raw_request: bytes,
    *,
    boundary: AtomicSignerBoundary,
) -> VerifiedAtomicSignerRequest:
    """Final boundary entry point; no caller-owned time or prevalidated dict."""

    if not isinstance(boundary, AtomicSignerBoundary):
        raise AtomicSignerContractError("protected atomic signer boundary is required")
    return boundary.validate_and_reserve(raw_request)


def parse_and_validate_atomic_signer_request(
    raw_request: bytes,
    *,
    boundary: AtomicSignerBoundary,
) -> VerifiedAtomicSignerRequest:
    """Compatibility name for the same exact canonical-bytes boundary."""

    return validate_atomic_signer_request(raw_request, boundary=boundary)
