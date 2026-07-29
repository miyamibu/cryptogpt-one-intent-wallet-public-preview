"""Crash-safe, local-only SQLite reference for accounting state.

This module deliberately performs no network I/O and contains no provider,
wallet, signing, or secret-management integration.  It demonstrates four
local durability boundaries:

* a balanced double-entry transaction and its outbox event commit atomically;
* outbox delivery is leased and retryable, with explicit lease recovery;
* reconciliation changes state only from caller-supplied observations;
* health checks fail closed on schema, foreign-key, or balance corruption.

The store is a reference implementation, not production custody evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import stat
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterator, Mapping, Sequence


LOCAL_ONLY = True
NETWORK_IO_ENABLED = False

_APPLICATION_ID = 0x43575054  # "CWPT"
_SCHEMA_VERSION = 1
_MAX_TEXT = 512
_MAX_PAYLOAD_BYTES = 64 * 1024
_MAX_JSON_DEPTH = 32
_MAX_JSON_NODES = 4096
_MAX_LINES = 128
_MAX_MINOR_UNITS = 10**15
_MAX_SQLITE_INTEGER = 2**63 - 1
_ERROR_CODE_PATTERN = re.compile(r"[A-Z][A-Z0-9_.:-]{0,127}\Z")


class LedgerStoreError(RuntimeError):
    """Base exception for the local ledger store."""


class LedgerValidationError(LedgerStoreError):
    """Input is malformed, unsafe, or not balanced."""


class LedgerConflictError(LedgerStoreError):
    """An idempotency key, lease, or authoritative result conflicts."""


class LedgerNotFoundError(LedgerStoreError):
    """A requested local account, operation, or event does not exist."""


class LedgerStoreIntegrityError(LedgerStoreError):
    """SQLite schema or ledger invariants are not safe for further writes."""


class OperationState(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REVERSED = "REVERSED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class OutboxState(str, Enum):
    PENDING = "PENDING"
    LEASED = "LEASED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class ReconciliationResult(str, Enum):
    CONFIRMED = "CONFIRMED"
    NOT_APPLIED = "NOT_APPLIED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class LedgerLine:
    """A signed minor-unit posting; positive is debit and negative is credit."""

    account_id: str
    asset_id: str
    amount_minor: int


@dataclass(frozen=True)
class OutboxMessage:
    event_id: str
    topic: str
    dedupe_key: str
    payload: Mapping[str, object]


@dataclass(frozen=True)
class OutboxEvent:
    event_id: str
    operation_id: str
    topic: str
    dedupe_key: str
    payload: dict[str, object]
    state: OutboxState
    attempts: int
    available_at: int
    lease_until: int | None


@dataclass(frozen=True)
class OperationSnapshot:
    operation_id: str
    idempotency_key: str
    state: OperationState
    original_transaction_id: str
    reversal_transaction_id: str | None
    external_reference: str | None
    reconciliation_conflict: bool
    outbox_state: OutboxState


@dataclass(frozen=True)
class ReconciliationReport:
    operation: OperationSnapshot
    result: ReconciliationResult
    duplicate_observation: bool
    conflicting_observation: bool
    reversal_created: bool


@dataclass(frozen=True)
class HealthReport:
    status: str
    integrity_check: str
    pending_outbox: int
    leased_outbox: int
    expired_leases: int
    reconciliation_required: int
    issues: tuple[str, ...]


@dataclass(frozen=True)
class RecoveryReport:
    requeued_expired_leases: int
    operations_flagged_for_reconciliation: int
    health: HealthReport


_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE schema_metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE ledger_accounts (
        account_id TEXT PRIMARY KEY,
        asset_id TEXT NOT NULL,
        created_at INTEGER NOT NULL CHECK (created_at >= 0),
        UNIQUE (account_id, asset_id)
    )
    """,
    """
    CREATE TABLE operations (
        operation_id TEXT PRIMARY KEY,
        idempotency_key TEXT NOT NULL UNIQUE,
        request_fingerprint TEXT NOT NULL CHECK (length(request_fingerprint) = 64),
        state TEXT NOT NULL CHECK (
            state IN ('PENDING', 'CONFIRMED', 'REVERSED', 'RECONCILIATION_REQUIRED')
        ),
        original_transaction_id TEXT NOT NULL UNIQUE,
        reversal_transaction_id TEXT UNIQUE,
        external_reference TEXT,
        reconciliation_conflict INTEGER NOT NULL DEFAULT 0 CHECK (reconciliation_conflict IN (0, 1)),
        created_at INTEGER NOT NULL CHECK (created_at >= 0),
        updated_at INTEGER NOT NULL CHECK (updated_at >= created_at)
    )
    """,
    """
    CREATE TABLE ledger_transactions (
        transaction_id TEXT PRIMARY KEY,
        operation_id TEXT NOT NULL,
        kind TEXT NOT NULL CHECK (kind IN ('ORIGINAL', 'REVERSAL')),
        reverses_transaction_id TEXT,
        created_at INTEGER NOT NULL CHECK (created_at >= 0),
        UNIQUE (operation_id, kind),
        CHECK (
            (kind = 'ORIGINAL' AND reverses_transaction_id IS NULL) OR
            (kind = 'REVERSAL' AND reverses_transaction_id IS NOT NULL)
        ),
        FOREIGN KEY (operation_id) REFERENCES operations(operation_id) ON DELETE RESTRICT,
        FOREIGN KEY (reverses_transaction_id) REFERENCES ledger_transactions(transaction_id) ON DELETE RESTRICT
    )
    """,
    f"""
    CREATE TABLE ledger_entries (
        transaction_id TEXT NOT NULL,
        line_number INTEGER NOT NULL CHECK (line_number >= 0 AND line_number < {_MAX_LINES}),
        account_id TEXT NOT NULL,
        asset_id TEXT NOT NULL,
        amount_minor INTEGER NOT NULL CHECK (
            amount_minor != 0 AND
            amount_minor >= -{_MAX_MINOR_UNITS} AND
            amount_minor <= {_MAX_MINOR_UNITS}
        ),
        PRIMARY KEY (transaction_id, line_number),
        UNIQUE (transaction_id, account_id),
        FOREIGN KEY (transaction_id) REFERENCES ledger_transactions(transaction_id) ON DELETE RESTRICT,
        FOREIGN KEY (account_id, asset_id) REFERENCES ledger_accounts(account_id, asset_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE outbox_events (
        event_id TEXT PRIMARY KEY,
        operation_id TEXT NOT NULL UNIQUE,
        topic TEXT NOT NULL,
        dedupe_key TEXT NOT NULL UNIQUE,
        payload_json TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('PENDING', 'LEASED', 'DELIVERED', 'CANCELLED')),
        attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
        available_at INTEGER NOT NULL CHECK (available_at >= 0),
        worker_id TEXT,
        lease_until INTEGER,
        delivered_at INTEGER,
        last_error_code TEXT,
        created_at INTEGER NOT NULL CHECK (created_at >= 0),
        updated_at INTEGER NOT NULL CHECK (updated_at >= created_at),
        CHECK (
            (state = 'LEASED' AND worker_id IS NOT NULL AND lease_until IS NOT NULL) OR
            (state != 'LEASED' AND worker_id IS NULL AND lease_until IS NULL)
        ),
        CHECK (
            (state = 'DELIVERED' AND delivered_at IS NOT NULL) OR
            (state != 'DELIVERED' AND delivered_at IS NULL)
        ),
        FOREIGN KEY (operation_id) REFERENCES operations(operation_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE reconciliation_observations (
        observation_id TEXT PRIMARY KEY,
        operation_id TEXT NOT NULL,
        result TEXT NOT NULL CHECK (result IN ('CONFIRMED', 'NOT_APPLIED', 'UNKNOWN')),
        external_reference TEXT,
        observation_fingerprint TEXT NOT NULL CHECK (length(observation_fingerprint) = 64),
        conflicting INTEGER NOT NULL DEFAULT 0 CHECK (conflicting IN (0, 1)),
        observed_at INTEGER NOT NULL CHECK (observed_at >= 0),
        FOREIGN KEY (operation_id) REFERENCES operations(operation_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE UNIQUE INDEX operations_external_reference_uq
    ON operations(external_reference)
    WHERE external_reference IS NOT NULL
    """,
    """
    CREATE INDEX outbox_ready_idx
    ON outbox_events(state, available_at, created_at, event_id)
    """,
)

_EXPECTED_TABLES = {
    "schema_metadata",
    "ledger_accounts",
    "operations",
    "ledger_transactions",
    "ledger_entries",
    "outbox_events",
    "reconciliation_observations",
}
_EXPECTED_INDEXES = {"operations_external_reference_uq", "outbox_ready_idx"}


def _validate_text(value: object, label: str, *, maximum: int = _MAX_TEXT) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise LedgerValidationError(f"{label} must be a non-empty trimmed string")
    if len(value) > maximum or any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise LedgerValidationError(f"{label} exceeds the safe text boundary")
    return value


def _validate_time(value: object, label: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        or value > _MAX_SQLITE_INTEGER
    ):
        raise LedgerValidationError(f"{label} must be a non-negative signed 64-bit integer")
    return value


def _validate_positive_int(value: object, label: str, *, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0 or value > maximum:
        raise LedgerValidationError(f"{label} must be an integer from 1 through {maximum}")
    return value


def _canonical_json(value: Mapping[str, object]) -> str:
    if not isinstance(value, Mapping):
        raise LedgerValidationError("outbox payload must be a JSON object")
    node_count = 0

    def validate(node: object, depth: int) -> None:
        nonlocal node_count
        node_count += 1
        if node_count > _MAX_JSON_NODES or depth > _MAX_JSON_DEPTH:
            raise LedgerValidationError("outbox payload exceeds the structural limit")
        if node is None or isinstance(node, bool):
            return
        if isinstance(node, str):
            if len(node) > _MAX_PAYLOAD_BYTES:
                raise LedgerValidationError("outbox payload string exceeds the size limit")
            return
        if isinstance(node, int) and not isinstance(node, bool):
            if abs(node) > _MAX_SQLITE_INTEGER:
                raise LedgerValidationError("outbox payload integer exceeds the signed 64-bit limit")
            return
        if isinstance(node, float):
            raise LedgerValidationError("outbox payload must not contain floating-point values")
        if isinstance(node, Mapping):
            for key, child in node.items():
                _validate_text(key, "outbox payload key")
                validate(child, depth + 1)
            return
        if isinstance(node, (list, tuple)):
            for child in node:
                validate(child, depth + 1)
            return
        raise LedgerValidationError("outbox payload contains a non-JSON value")

    validate(value, 0)
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise LedgerValidationError("outbox payload is not canonical JSON") from exc
    if len(encoded.encode("utf-8")) > _MAX_PAYLOAD_BYTES:
        raise LedgerValidationError("outbox payload exceeds 64 KiB")
    return encoded


def _hash_json(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _coerce_result(value: ReconciliationResult | str) -> ReconciliationResult:
    try:
        return value if isinstance(value, ReconciliationResult) else ReconciliationResult(value)
    except (TypeError, ValueError) as exc:
        raise LedgerValidationError("unsupported reconciliation result") from exc


class LedgerStore:
    """A single-file, local SQLite accounting boundary.

    All mutating methods are serialized per instance and use ``BEGIN
    IMMEDIATE``. Multiple processes remain coordinated by SQLite locking.
    """

    def __init__(self, path: str) -> None:
        if not isinstance(path, str) or not path or path.startswith("file:") or path == ":memory:":
            raise LedgerValidationError("ledger store requires a non-URI filesystem path")
        database_path = Path(path)
        if not database_path.is_absolute():
            raise LedgerValidationError("ledger store path must be absolute")
        if not database_path.parent.is_dir():
            raise LedgerValidationError("ledger store parent directory must already exist")
        if database_path.is_symlink() or (database_path.exists() and not database_path.is_file()):
            raise LedgerValidationError("ledger store path must be a regular non-symlink file")
        existed_before_open = database_path.exists()
        if existed_before_open and stat.S_IMODE(database_path.stat().st_mode) & 0o077:
            raise LedgerValidationError("existing ledger store must be readable and writable only by its owner")

        self.path = database_path
        self._lock = threading.RLock()
        self._closed = False
        self._connection = sqlite3.connect(
            str(database_path),
            timeout=5.0,
            isolation_level=None,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        try:
            if not existed_before_open:
                database_path.chmod(0o600)
            self._connection.execute("PRAGMA trusted_schema=OFF")
            self._connection.execute("PRAGMA foreign_keys=ON")
            self._connection.execute("PRAGMA busy_timeout=5000")
            self._connection.execute("PRAGMA synchronous=FULL")
            journal_mode = str(self._connection.execute("PRAGMA journal_mode=WAL").fetchone()[0]).lower()
            if journal_mode != "wal":
                raise LedgerStoreIntegrityError("ledger store requires SQLite WAL mode")
            self._initialize_or_verify_schema()
            initial_health = self._collect_health(now=self._clock_high_water())
            if initial_health.status == "UNHEALTHY":
                raise LedgerStoreIntegrityError("; ".join(initial_health.issues))
        except Exception:
            self._connection.close()
            self._closed = True
            raise

    def _initialize_or_verify_schema(self) -> None:
        objects = list(
            self._connection.execute(
                "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
            )
        )
        application_id = int(self._connection.execute("PRAGMA application_id").fetchone()[0])
        user_version = int(self._connection.execute("PRAGMA user_version").fetchone()[0])
        if not objects and application_id == 0 and user_version == 0:
            with self._write_transaction():
                for statement in _SCHEMA_STATEMENTS:
                    self._connection.execute(statement)
                self._connection.execute(
                    "INSERT INTO schema_metadata (key, value) VALUES ('schema_version', ?)",
                    (str(_SCHEMA_VERSION),),
                )
                self._connection.execute(
                    "INSERT INTO schema_metadata (key, value) VALUES ('schema_digest', ?)",
                    (self._schema_digest(),),
                )
                self._connection.execute(
                    "INSERT INTO schema_metadata (key, value) VALUES ('clock_high_water', '0')"
                )
                self._connection.execute(f"PRAGMA application_id={_APPLICATION_ID}")
                self._connection.execute(f"PRAGMA user_version={_SCHEMA_VERSION}")
        self._verify_schema()

    def _schema_digest(self) -> str:
        records = [
            dict(row)
            for row in self._connection.execute(
                "SELECT type, name, tbl_name, sql FROM sqlite_master "
                "WHERE name NOT LIKE 'sqlite_%' AND type IN ('table', 'index', 'trigger', 'view') "
                "ORDER BY type, name"
            )
        ]
        return _hash_json(records)

    def _verify_schema(self) -> None:
        application_id = int(self._connection.execute("PRAGMA application_id").fetchone()[0])
        user_version = int(self._connection.execute("PRAGMA user_version").fetchone()[0])
        if application_id != _APPLICATION_ID or user_version != _SCHEMA_VERSION:
            raise LedgerStoreIntegrityError("ledger store application id or schema version is unsafe")

        rows = list(
            self._connection.execute(
                "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
            )
        )
        tables = {str(row["name"]) for row in rows if row["type"] == "table"}
        indexes = {str(row["name"]) for row in rows if row["type"] == "index"}
        unsafe_objects = [str(row["name"]) for row in rows if row["type"] in {"trigger", "view"}]
        if tables != _EXPECTED_TABLES or indexes != _EXPECTED_INDEXES or unsafe_objects:
            raise LedgerStoreIntegrityError("ledger store schema contains missing or unexpected objects")

        metadata = dict(self._connection.execute("SELECT key, value FROM schema_metadata"))
        if set(metadata) != {"schema_version", "schema_digest", "clock_high_water"}:
            raise LedgerStoreIntegrityError("ledger store metadata keys are unsafe")
        if metadata.get("schema_version") != str(_SCHEMA_VERSION):
            raise LedgerStoreIntegrityError("ledger store metadata version is unsafe")
        if metadata.get("schema_digest") != self._schema_digest():
            raise LedgerStoreIntegrityError("ledger store schema digest mismatch")
        if int(self._connection.execute("PRAGMA foreign_keys").fetchone()[0]) != 1:
            raise LedgerStoreIntegrityError("ledger store foreign keys are disabled")
        if int(self._connection.execute("PRAGMA trusted_schema").fetchone()[0]) != 0:
            raise LedgerStoreIntegrityError("ledger store trusted schema must remain disabled")
        if str(self._connection.execute("PRAGMA journal_mode").fetchone()[0]).lower() != "wal":
            raise LedgerStoreIntegrityError("ledger store WAL mode is disabled")
        if int(self._connection.execute("PRAGMA synchronous").fetchone()[0]) != 2:
            raise LedgerStoreIntegrityError("ledger store synchronous mode is not FULL")

    @contextmanager
    def _write_transaction(self, *, now: int | None = None) -> Iterator[None]:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            if now is not None:
                self._advance_clock(now)
            yield
        except Exception:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise
        else:
            self._connection.execute("COMMIT")

    def _clock_high_water(self) -> int:
        row = self._connection.execute(
            "SELECT value FROM schema_metadata WHERE key = 'clock_high_water'"
        ).fetchone()
        if row is None:
            raise LedgerStoreIntegrityError("ledger store clock high-water mark is missing")
        try:
            value = int(row["value"])
        except (TypeError, ValueError) as exc:
            raise LedgerStoreIntegrityError("ledger store clock high-water mark is invalid") from exc
        if value < 0:
            raise LedgerStoreIntegrityError("ledger store clock high-water mark is negative")
        return value

    def _advance_clock(self, now: int) -> None:
        high_water = self._clock_high_water()
        if now < high_water:
            raise LedgerStoreIntegrityError("caller time moved behind the durable high-water mark")
        if now > high_water:
            self._connection.execute(
                "UPDATE schema_metadata SET value = ? WHERE key = 'clock_high_water'", (str(now),)
            )

    def _ensure_open(self) -> None:
        if self._closed:
            raise LedgerStoreError("ledger store is closed")

    def _require_structural_health(self, now: int) -> None:
        report = self._collect_health(now)
        if report.status == "UNHEALTHY":
            raise LedgerStoreIntegrityError("; ".join(report.issues))

    def register_account(self, account_id: str, asset_id: str, *, now: int) -> bool:
        account_id = _validate_text(account_id, "account id")
        asset_id = _validate_text(asset_id, "asset id")
        now = _validate_time(now, "account creation time")
        with self._lock:
            self._ensure_open()
            self._require_structural_health(now)
            with self._write_transaction(now=now):
                existing = self._connection.execute(
                    "SELECT asset_id FROM ledger_accounts WHERE account_id = ?", (account_id,)
                ).fetchone()
                if existing is not None:
                    if existing["asset_id"] != asset_id:
                        raise LedgerConflictError("ledger account cannot change asset identity")
                    return False
                self._connection.execute(
                    "INSERT INTO ledger_accounts (account_id, asset_id, created_at) VALUES (?, ?, ?)",
                    (account_id, asset_id, now),
                )
                return True

    def post_operation(
        self,
        *,
        operation_id: str,
        idempotency_key: str,
        transaction_id: str,
        lines: Sequence[LedgerLine],
        outbox: OutboxMessage,
        now: int,
    ) -> OperationSnapshot:
        operation_id = _validate_text(operation_id, "operation id")
        idempotency_key = _validate_text(idempotency_key, "idempotency key")
        transaction_id = _validate_text(transaction_id, "transaction id")
        now = _validate_time(now, "operation time")
        if not isinstance(outbox, OutboxMessage):
            raise LedgerValidationError("outbox message has the wrong runtime type")
        event_id = _validate_text(outbox.event_id, "outbox event id")
        topic = _validate_text(outbox.topic, "outbox topic")
        dedupe_key = _validate_text(outbox.dedupe_key, "outbox dedupe key")
        payload_json = _canonical_json(outbox.payload)
        normalized_lines = self._normalize_lines(lines)
        fingerprint = _hash_json(
            {
                "operationId": operation_id,
                "idempotencyKey": idempotency_key,
                "transactionId": transaction_id,
                "lines": [
                    {"accountId": line.account_id, "assetId": line.asset_id, "amountMinor": line.amount_minor}
                    for line in normalized_lines
                ],
                "outbox": {
                    "eventId": event_id,
                    "topic": topic,
                    "dedupeKey": dedupe_key,
                    "payload": json.loads(payload_json),
                },
            }
        )

        with self._lock:
            self._ensure_open()
            self._require_structural_health(now)
            try:
                with self._write_transaction(now=now):
                    by_operation = self._connection.execute(
                        "SELECT operation_id, request_fingerprint FROM operations WHERE operation_id = ?",
                        (operation_id,),
                    ).fetchone()
                    by_key = self._connection.execute(
                        "SELECT operation_id, request_fingerprint FROM operations WHERE idempotency_key = ?",
                        (idempotency_key,),
                    ).fetchone()
                    if by_operation is not None or by_key is not None:
                        rows = [row for row in (by_operation, by_key) if row is not None]
                        if all(row["operation_id"] == operation_id and row["request_fingerprint"] == fingerprint for row in rows):
                            return self._operation_snapshot(operation_id)
                        raise LedgerConflictError("operation or idempotency key was reused with different material")

                    for line in normalized_lines:
                        account = self._connection.execute(
                            "SELECT asset_id FROM ledger_accounts WHERE account_id = ?", (line.account_id,)
                        ).fetchone()
                        if account is None:
                            raise LedgerNotFoundError(f"ledger account is not registered: {line.account_id}")
                        if account["asset_id"] != line.asset_id:
                            raise LedgerConflictError("ledger line asset does not match the registered account")

                    self._connection.execute(
                        "INSERT INTO operations "
                        "(operation_id, idempotency_key, request_fingerprint, state, original_transaction_id, "
                        "reversal_transaction_id, external_reference, reconciliation_conflict, created_at, updated_at) "
                        "VALUES (?, ?, ?, 'PENDING', ?, NULL, NULL, 0, ?, ?)",
                        (operation_id, idempotency_key, fingerprint, transaction_id, now, now),
                    )
                    self._connection.execute(
                        "INSERT INTO ledger_transactions "
                        "(transaction_id, operation_id, kind, reverses_transaction_id, created_at) "
                        "VALUES (?, ?, 'ORIGINAL', NULL, ?)",
                        (transaction_id, operation_id, now),
                    )
                    self._connection.executemany(
                        "INSERT INTO ledger_entries "
                        "(transaction_id, line_number, account_id, asset_id, amount_minor) VALUES (?, ?, ?, ?, ?)",
                        [
                            (transaction_id, index, line.account_id, line.asset_id, line.amount_minor)
                            for index, line in enumerate(normalized_lines)
                        ],
                    )
                    self._connection.execute(
                        "INSERT INTO outbox_events "
                        "(event_id, operation_id, topic, dedupe_key, payload_json, state, attempts, available_at, "
                        "worker_id, lease_until, delivered_at, last_error_code, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, 'PENDING', 0, ?, NULL, NULL, NULL, NULL, ?, ?)",
                        (event_id, operation_id, topic, dedupe_key, payload_json, now, now, now),
                    )
                    return self._operation_snapshot(operation_id)
            except sqlite3.IntegrityError as exc:
                raise LedgerConflictError("operation conflicts with an existing durable identity") from exc

    def _normalize_lines(self, lines: Sequence[LedgerLine]) -> tuple[LedgerLine, ...]:
        if isinstance(lines, (str, bytes)) or not isinstance(lines, Sequence):
            raise LedgerValidationError("ledger lines must be a sequence")
        if len(lines) < 2 or len(lines) > _MAX_LINES:
            raise LedgerValidationError("a transaction requires 2 through 128 ledger lines")
        normalized: list[LedgerLine] = []
        account_ids: set[str] = set()
        asset_totals: dict[str, int] = {}
        asset_signs: dict[str, set[int]] = {}
        for line in lines:
            if not isinstance(line, LedgerLine):
                raise LedgerValidationError("ledger line has the wrong runtime type")
            account_id = _validate_text(line.account_id, "ledger account id")
            asset_id = _validate_text(line.asset_id, "ledger asset id")
            amount = line.amount_minor
            if isinstance(amount, bool) or not isinstance(amount, int) or amount == 0 or abs(amount) > _MAX_MINOR_UNITS:
                raise LedgerValidationError("ledger amount must be a bounded non-zero integer")
            if account_id in account_ids:
                raise LedgerValidationError("an account may appear only once in a transaction")
            account_ids.add(account_id)
            asset_totals[asset_id] = asset_totals.get(asset_id, 0) + amount
            asset_signs.setdefault(asset_id, set()).add(1 if amount > 0 else -1)
            normalized.append(LedgerLine(account_id, asset_id, amount))
        for asset_id, total in asset_totals.items():
            if total != 0 or asset_signs[asset_id] != {-1, 1}:
                raise LedgerValidationError(f"double-entry transaction is not balanced for asset {asset_id}")
        return tuple(sorted(normalized, key=lambda item: (item.asset_id, item.account_id)))

    def claim_outbox(
        self,
        worker_id: str,
        *,
        now: int,
        lease_seconds: int = 30,
        limit: int = 10,
    ) -> tuple[OutboxEvent, ...]:
        worker_id = _validate_text(worker_id, "outbox worker id")
        now = _validate_time(now, "outbox claim time")
        lease_seconds = _validate_positive_int(lease_seconds, "outbox lease", maximum=3600)
        limit = _validate_positive_int(limit, "outbox claim limit", maximum=100)
        lease_until = _validate_time(now + lease_seconds, "outbox lease expiry")
        with self._lock:
            self._ensure_open()
            self._require_structural_health(now)
            with self._write_transaction(now=now):
                event_ids = [
                    str(row["event_id"])
                    for row in self._connection.execute(
                        "SELECT event_id FROM outbox_events "
                        "WHERE state = 'PENDING' AND available_at <= ? "
                        "ORDER BY created_at, event_id LIMIT ?",
                        (now, limit),
                    )
                ]
                for event_id in event_ids:
                    self._connection.execute(
                        "UPDATE outbox_events SET state = 'LEASED', worker_id = ?, lease_until = ?, "
                        "attempts = attempts + 1, updated_at = ? WHERE event_id = ? AND state = 'PENDING'",
                        (worker_id, lease_until, now, event_id),
                    )
                return tuple(self._outbox_event(event_id) for event_id in event_ids)

    def mark_outbox_delivered(self, event_id: str, worker_id: str, *, now: int) -> bool:
        event_id = _validate_text(event_id, "outbox event id")
        worker_id = _validate_text(worker_id, "outbox worker id")
        now = _validate_time(now, "outbox delivery time")
        with self._lock:
            self._ensure_open()
            self._require_structural_health(now)
            with self._write_transaction(now=now):
                row = self._connection.execute(
                    "SELECT operation_id, state, worker_id, lease_until FROM outbox_events WHERE event_id = ?",
                    (event_id,),
                ).fetchone()
                if row is None:
                    raise LedgerNotFoundError("outbox event does not exist")
                if row["state"] == OutboxState.DELIVERED.value:
                    return False
                if row["state"] != OutboxState.LEASED.value or row["worker_id"] != worker_id:
                    raise LedgerConflictError("outbox delivery requires the current lease owner")
                if int(row["lease_until"]) <= now:
                    raise LedgerConflictError("outbox lease expired before delivery acknowledgement")
                self._connection.execute(
                    "UPDATE outbox_events SET state = 'DELIVERED', worker_id = NULL, lease_until = NULL, "
                    "delivered_at = ?, last_error_code = NULL, updated_at = ? WHERE event_id = ?",
                    (now, now, event_id),
                )
                self._connection.execute(
                    "UPDATE operations SET state = 'RECONCILIATION_REQUIRED', updated_at = ? "
                    "WHERE operation_id = ? AND state = 'PENDING'",
                    (now, row["operation_id"]),
                )
                return True

    def mark_outbox_retry(
        self,
        event_id: str,
        worker_id: str,
        *,
        now: int,
        retry_at: int,
        error_code: str,
    ) -> None:
        event_id = _validate_text(event_id, "outbox event id")
        worker_id = _validate_text(worker_id, "outbox worker id")
        now = _validate_time(now, "outbox retry time")
        retry_at = _validate_time(retry_at, "outbox next attempt time")
        if retry_at < now:
            raise LedgerValidationError("outbox retry time must not be in the past")
        error_code = _validate_text(error_code, "outbox retry error code", maximum=128)
        if _ERROR_CODE_PATTERN.fullmatch(error_code) is None:
            raise LedgerValidationError("outbox retry error must be a sanitized uppercase code")
        with self._lock:
            self._ensure_open()
            self._require_structural_health(now)
            with self._write_transaction(now=now):
                row = self._connection.execute(
                    "SELECT state, worker_id, lease_until FROM outbox_events WHERE event_id = ?", (event_id,)
                ).fetchone()
                if row is None:
                    raise LedgerNotFoundError("outbox event does not exist")
                if row["state"] != OutboxState.LEASED.value or row["worker_id"] != worker_id:
                    raise LedgerConflictError("outbox retry requires the current lease owner")
                if int(row["lease_until"]) <= now:
                    raise LedgerConflictError("expired outbox leases must be recovered before retry")
                self._connection.execute(
                    "UPDATE outbox_events SET state = 'PENDING', available_at = ?, worker_id = NULL, "
                    "lease_until = NULL, last_error_code = ?, updated_at = ? WHERE event_id = ?",
                    (retry_at, error_code, now, event_id),
                )

    def reconcile_operation(
        self,
        operation_id: str,
        *,
        observation_id: str,
        result: ReconciliationResult | str,
        observed_at: int,
        now: int,
        external_reference: str | None = None,
    ) -> ReconciliationReport:
        operation_id = _validate_text(operation_id, "operation id")
        observation_id = _validate_text(observation_id, "reconciliation observation id")
        result = _coerce_result(result)
        observed_at = _validate_time(observed_at, "reconciliation observation time")
        now = _validate_time(now, "reconciliation receipt time")
        if observed_at > now:
            raise LedgerValidationError("reconciliation observation must not be from the future")
        if external_reference is not None:
            external_reference = _validate_text(external_reference, "external reference")
        if result is ReconciliationResult.CONFIRMED and external_reference is None:
            raise LedgerValidationError("confirmed reconciliation requires an external reference")
        observation_fingerprint = _hash_json(
            {
                "operationId": operation_id,
                "observationId": observation_id,
                "result": result.value,
                "observedAt": observed_at,
                "externalReference": external_reference,
            }
        )

        with self._lock:
            self._ensure_open()
            self._require_structural_health(now)
            try:
                with self._write_transaction(now=now):
                    operation = self._connection.execute(
                        "SELECT * FROM operations WHERE operation_id = ?", (operation_id,)
                    ).fetchone()
                    if operation is None:
                        raise LedgerNotFoundError("operation does not exist")
                    if observed_at < int(operation["created_at"]):
                        raise LedgerValidationError("reconciliation observation predates the operation")
                    existing_observation = self._connection.execute(
                        "SELECT observation_fingerprint, conflicting FROM reconciliation_observations "
                        "WHERE observation_id = ?",
                        (observation_id,),
                    ).fetchone()
                    if existing_observation is not None:
                        if existing_observation["observation_fingerprint"] != observation_fingerprint:
                            raise LedgerConflictError("observation id was reused with different material")
                        return ReconciliationReport(
                            operation=self._operation_snapshot(operation_id),
                            result=result,
                            duplicate_observation=True,
                            conflicting_observation=bool(existing_observation["conflicting"]),
                            reversal_created=False,
                        )

                    self._connection.execute(
                        "INSERT INTO reconciliation_observations "
                        "(observation_id, operation_id, result, external_reference, observation_fingerprint, "
                        "conflicting, observed_at) VALUES (?, ?, ?, ?, ?, 0, ?)",
                        (observation_id, operation_id, result.value, external_reference, observation_fingerprint, observed_at),
                    )
                    state = OperationState(str(operation["state"]))
                    existing_external_reference = operation["external_reference"]
                    reversal_transaction_id = operation["reversal_transaction_id"]
                    conflict_locked = bool(operation["reconciliation_conflict"])
                    conflicting = False
                    reversal_created = False

                    if result is ReconciliationResult.UNKNOWN:
                        if conflict_locked:
                            conflicting = True
                        elif state not in {OperationState.CONFIRMED, OperationState.REVERSED}:
                            self._set_operation_state(
                                operation_id,
                                OperationState.RECONCILIATION_REQUIRED,
                                now,
                                conflict=False,
                            )
                    elif result is ReconciliationResult.CONFIRMED:
                        reference_owner = self._connection.execute(
                            "SELECT operation_id FROM operations WHERE external_reference = ? AND operation_id != ?",
                            (external_reference, operation_id),
                        ).fetchone()
                        if conflict_locked or reference_owner is not None:
                            conflicting = True
                            self._set_operation_state(
                                operation_id,
                                OperationState.RECONCILIATION_REQUIRED,
                                now,
                                conflict=True,
                            )
                        elif reversal_transaction_id is not None or state is OperationState.REVERSED:
                            conflicting = True
                            self._set_operation_state(
                                operation_id,
                                OperationState.RECONCILIATION_REQUIRED,
                                now,
                                conflict=True,
                            )
                        elif (
                            existing_external_reference is not None
                            and existing_external_reference != external_reference
                        ):
                            conflicting = True
                            self._set_operation_state(
                                operation_id,
                                OperationState.RECONCILIATION_REQUIRED,
                                now,
                                conflict=True,
                            )
                        else:
                            self._connection.execute(
                                "UPDATE operations SET state = 'CONFIRMED', external_reference = ?, "
                                "reconciliation_conflict = 0, updated_at = ? "
                                "WHERE operation_id = ?",
                                (external_reference, now, operation_id),
                            )
                            self._connection.execute(
                                "UPDATE outbox_events SET state = 'DELIVERED', worker_id = NULL, lease_until = NULL, "
                                "delivered_at = COALESCE(delivered_at, ?), last_error_code = NULL, updated_at = ? "
                                "WHERE operation_id = ? AND state != 'CANCELLED'",
                                (now, now, operation_id),
                            )
                    else:
                        if conflict_locked:
                            conflicting = True
                        elif state is OperationState.CONFIRMED and reversal_transaction_id is None:
                            conflicting = True
                            self._set_operation_state(
                                operation_id,
                                OperationState.RECONCILIATION_REQUIRED,
                                now,
                                conflict=True,
                            )
                        else:
                            if reversal_transaction_id is None:
                                reversal_transaction_id = self._create_reversal(operation_id, now)
                                reversal_created = True
                            self._set_operation_state(
                                operation_id, OperationState.REVERSED, now, conflict=False
                            )
                            self._connection.execute(
                                "UPDATE outbox_events SET state = 'CANCELLED', worker_id = NULL, lease_until = NULL, "
                                "delivered_at = NULL, updated_at = ? WHERE operation_id = ?",
                                (now, operation_id),
                            )

                    if conflicting:
                        self._connection.execute(
                            "UPDATE reconciliation_observations SET conflicting = 1 WHERE observation_id = ?",
                            (observation_id,),
                        )

                    return ReconciliationReport(
                        operation=self._operation_snapshot(operation_id),
                        result=result,
                        duplicate_observation=False,
                        conflicting_observation=conflicting,
                        reversal_created=reversal_created,
                    )
            except sqlite3.IntegrityError as exc:
                raise LedgerConflictError("reconciliation conflicts with an existing durable identity") from exc

    def _set_operation_state(
        self,
        operation_id: str,
        state: OperationState,
        now: int,
        *,
        conflict: bool | None = None,
    ) -> None:
        if conflict is None:
            self._connection.execute(
                "UPDATE operations SET state = ?, updated_at = ? WHERE operation_id = ?",
                (state.value, now, operation_id),
            )
            return
        self._connection.execute(
            "UPDATE operations SET state = ?, reconciliation_conflict = ?, updated_at = ? "
            "WHERE operation_id = ?",
            (state.value, int(conflict), now, operation_id),
        )

    def _create_reversal(self, operation_id: str, now: int) -> str:
        operation = self._connection.execute(
            "SELECT original_transaction_id FROM operations WHERE operation_id = ?", (operation_id,)
        ).fetchone()
        if operation is None:
            raise LedgerNotFoundError("operation does not exist")
        original_transaction_id = str(operation["original_transaction_id"])
        digest = hashlib.sha256(f"{operation_id}\x00{original_transaction_id}".encode("utf-8")).hexdigest()
        reversal_transaction_id = f"reversal-{digest[:32]}"
        entries = list(
            self._connection.execute(
                "SELECT line_number, account_id, asset_id, amount_minor FROM ledger_entries "
                "WHERE transaction_id = ? ORDER BY line_number",
                (original_transaction_id,),
            )
        )
        if len(entries) < 2:
            raise LedgerStoreIntegrityError("original transaction has insufficient ledger entries")
        self._connection.execute(
            "INSERT INTO ledger_transactions "
            "(transaction_id, operation_id, kind, reverses_transaction_id, created_at) "
            "VALUES (?, ?, 'REVERSAL', ?, ?)",
            (reversal_transaction_id, operation_id, original_transaction_id, now),
        )
        self._connection.executemany(
            "INSERT INTO ledger_entries "
            "(transaction_id, line_number, account_id, asset_id, amount_minor) VALUES (?, ?, ?, ?, ?)",
            [
                (
                    reversal_transaction_id,
                    int(row["line_number"]),
                    str(row["account_id"]),
                    str(row["asset_id"]),
                    -int(row["amount_minor"]),
                )
                for row in entries
            ],
        )
        self._connection.execute(
            "UPDATE operations SET reversal_transaction_id = ? WHERE operation_id = ?",
            (reversal_transaction_id, operation_id),
        )
        return reversal_transaction_id

    def recover(self, *, now: int) -> RecoveryReport:
        now = _validate_time(now, "recovery time")
        with self._lock:
            self._ensure_open()
            self._require_structural_health(now)
            with self._write_transaction(now=now):
                requeued = self._connection.execute(
                    "UPDATE outbox_events SET state = 'PENDING', worker_id = NULL, lease_until = NULL, "
                    "available_at = ?, last_error_code = 'LEASE_EXPIRED', updated_at = ? "
                    "WHERE state = 'LEASED' AND lease_until <= ?",
                    (now, now, now),
                ).rowcount
                flagged = self._connection.execute(
                    "UPDATE operations SET state = 'RECONCILIATION_REQUIRED', "
                    "reconciliation_conflict = 0, updated_at = ? "
                    "WHERE state = 'PENDING' AND operation_id IN "
                    "(SELECT operation_id FROM outbox_events WHERE state IN ('DELIVERED', 'CANCELLED'))",
                    (now,),
                ).rowcount
            health = self._collect_health(now)
            if health.status == "UNHEALTHY":
                raise LedgerStoreIntegrityError("recovery left the ledger structurally unhealthy")
            return RecoveryReport(int(requeued), int(flagged), health)

    def get_operation(self, operation_id: str) -> OperationSnapshot:
        operation_id = _validate_text(operation_id, "operation id")
        with self._lock:
            self._ensure_open()
            return self._operation_snapshot(operation_id)

    def _operation_snapshot(self, operation_id: str) -> OperationSnapshot:
        row = self._connection.execute(
            "SELECT o.operation_id, o.idempotency_key, o.state, o.original_transaction_id, "
            "o.reversal_transaction_id, o.external_reference, o.reconciliation_conflict, "
            "e.state AS outbox_state "
            "FROM operations o JOIN outbox_events e ON e.operation_id = o.operation_id "
            "WHERE o.operation_id = ?",
            (operation_id,),
        ).fetchone()
        if row is None:
            raise LedgerNotFoundError("operation does not exist")
        return OperationSnapshot(
            operation_id=str(row["operation_id"]),
            idempotency_key=str(row["idempotency_key"]),
            state=OperationState(str(row["state"])),
            original_transaction_id=str(row["original_transaction_id"]),
            reversal_transaction_id=(
                str(row["reversal_transaction_id"]) if row["reversal_transaction_id"] is not None else None
            ),
            external_reference=(str(row["external_reference"]) if row["external_reference"] is not None else None),
            reconciliation_conflict=bool(row["reconciliation_conflict"]),
            outbox_state=OutboxState(str(row["outbox_state"])),
        )

    def _outbox_event(self, event_id: str) -> OutboxEvent:
        row = self._connection.execute(
            "SELECT event_id, operation_id, topic, dedupe_key, payload_json, state, attempts, "
            "available_at, lease_until FROM outbox_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if row is None:
            raise LedgerNotFoundError("outbox event does not exist")
        payload = json.loads(str(row["payload_json"]))
        if not isinstance(payload, dict):
            raise LedgerStoreIntegrityError("outbox payload root is not an object")
        return OutboxEvent(
            event_id=str(row["event_id"]),
            operation_id=str(row["operation_id"]),
            topic=str(row["topic"]),
            dedupe_key=str(row["dedupe_key"]),
            payload=payload,
            state=OutboxState(str(row["state"])),
            attempts=int(row["attempts"]),
            available_at=int(row["available_at"]),
            lease_until=(int(row["lease_until"]) if row["lease_until"] is not None else None),
        )

    def account_balance(self, account_id: str) -> int:
        account_id = _validate_text(account_id, "account id")
        with self._lock:
            self._ensure_open()
            exists = self._connection.execute(
                "SELECT 1 FROM ledger_accounts WHERE account_id = ?", (account_id,)
            ).fetchone()
            if exists is None:
                raise LedgerNotFoundError("ledger account does not exist")
            total = 0
            for row in self._connection.execute(
                "SELECT amount_minor FROM ledger_entries WHERE account_id = ?", (account_id,)
            ):
                total += int(row["amount_minor"])
            return total

    def monitor_health(self, *, now: int) -> HealthReport:
        now = _validate_time(now, "health check time")
        with self._lock:
            self._ensure_open()
            return self._collect_health(now)

    def _collect_health(self, now: int) -> HealthReport:
        issues: list[str] = []
        integrity_check = "unknown"
        pending_outbox = 0
        leased_outbox = 0
        expired_leases = 0
        reconciliation_required = 0
        try:
            self._verify_schema()
            integrity_rows = [str(row[0]) for row in self._connection.execute("PRAGMA quick_check")]
            integrity_check = "; ".join(integrity_rows)
            if integrity_rows != ["ok"]:
                issues.append("sqlite quick_check failed")
            if list(self._connection.execute("PRAGMA foreign_key_check")):
                issues.append("sqlite foreign-key check failed")
            issues.extend(self._ledger_invariant_issues())
            issues.extend(self._state_invariant_issues())
            pending_outbox = int(
                self._connection.execute("SELECT COUNT(*) FROM outbox_events WHERE state = 'PENDING'").fetchone()[0]
            )
            leased_outbox = int(
                self._connection.execute("SELECT COUNT(*) FROM outbox_events WHERE state = 'LEASED'").fetchone()[0]
            )
            expired_leases = int(
                self._connection.execute(
                    "SELECT COUNT(*) FROM outbox_events WHERE state = 'LEASED' AND lease_until <= ?", (now,)
                ).fetchone()[0]
            )
            reconciliation_required = int(
                self._connection.execute(
                    "SELECT COUNT(*) FROM operations WHERE state = 'RECONCILIATION_REQUIRED'"
                ).fetchone()[0]
            )
            if now < self._clock_high_water():
                issues.append("caller time is behind the durable high-water mark")
        except (sqlite3.DatabaseError, LedgerStoreIntegrityError, ValueError, TypeError) as exc:
            issues.append(f"health inspection failed: {exc}")

        unique_issues = tuple(dict.fromkeys(issues))
        if unique_issues:
            status = "UNHEALTHY"
        elif expired_leases or reconciliation_required:
            status = "DEGRADED"
        else:
            status = "HEALTHY"
        return HealthReport(
            status=status,
            integrity_check=integrity_check,
            pending_outbox=pending_outbox,
            leased_outbox=leased_outbox,
            expired_leases=expired_leases,
            reconciliation_required=reconciliation_required,
            issues=unique_issues,
        )

    def _ledger_invariant_issues(self) -> list[str]:
        issues: list[str] = []
        transactions = list(
            self._connection.execute(
                "SELECT transaction_id, operation_id, kind, reverses_transaction_id FROM ledger_transactions "
                "ORDER BY transaction_id"
            )
        )
        entries_by_transaction: dict[str, list[sqlite3.Row]] = {}
        for transaction in transactions:
            transaction_id = str(transaction["transaction_id"])
            entries = list(
                self._connection.execute(
                    "SELECT account_id, asset_id, amount_minor FROM ledger_entries "
                    "WHERE transaction_id = ? ORDER BY line_number",
                    (transaction_id,),
                )
            )
            entries_by_transaction[transaction_id] = entries
            if len(entries) < 2:
                issues.append(f"transaction {transaction_id} has fewer than two entries")
                continue
            totals: dict[str, int] = {}
            signs: dict[str, set[int]] = {}
            for entry in entries:
                asset_id = str(entry["asset_id"])
                amount = int(entry["amount_minor"])
                totals[asset_id] = totals.get(asset_id, 0) + amount
                signs.setdefault(asset_id, set()).add(1 if amount > 0 else -1)
            for asset_id, total in totals.items():
                if total != 0 or signs[asset_id] != {-1, 1}:
                    issues.append(f"transaction {transaction_id} is unbalanced for {asset_id}")

        for transaction in transactions:
            if transaction["kind"] != "REVERSAL":
                continue
            transaction_id = str(transaction["transaction_id"])
            original_id = str(transaction["reverses_transaction_id"])
            original = entries_by_transaction.get(original_id)
            reversal = entries_by_transaction.get(transaction_id)
            if original is None or reversal is None:
                issues.append(f"reversal {transaction_id} has no local original")
                continue
            original_map = {
                (str(row["account_id"]), str(row["asset_id"])): int(row["amount_minor"])
                for row in original
            }
            reversal_map = {
                (str(row["account_id"]), str(row["asset_id"])): int(row["amount_minor"])
                for row in reversal
            }
            if {key: -value for key, value in original_map.items()} != reversal_map:
                issues.append(f"reversal {transaction_id} is not the exact inverse")
        return issues

    def _state_invariant_issues(self) -> list[str]:
        issues: list[str] = []
        for row in self._connection.execute(
            "SELECT o.operation_id, o.state, o.original_transaction_id, o.reversal_transaction_id, "
            "o.reconciliation_conflict, "
            "e.state AS outbox_state FROM operations o "
            "LEFT JOIN outbox_events e ON e.operation_id = o.operation_id ORDER BY o.operation_id"
        ):
            operation_id = str(row["operation_id"])
            original_count = int(
                self._connection.execute(
                    "SELECT COUNT(*) FROM ledger_transactions "
                    "WHERE operation_id = ? AND kind = 'ORIGINAL' AND transaction_id = ?",
                    (operation_id, row["original_transaction_id"]),
                ).fetchone()[0]
            )
            if original_count != 1:
                issues.append(f"operation {operation_id} does not bind exactly one original transaction")
            reversal_transaction_id = row["reversal_transaction_id"]
            if reversal_transaction_id is not None:
                reversal_count = int(
                    self._connection.execute(
                        "SELECT COUNT(*) FROM ledger_transactions WHERE operation_id = ? AND kind = 'REVERSAL' "
                        "AND transaction_id = ? AND reverses_transaction_id = ?",
                        (operation_id, reversal_transaction_id, row["original_transaction_id"]),
                    ).fetchone()[0]
                )
                if reversal_count != 1:
                    issues.append(f"operation {operation_id} does not bind its exact reversal transaction")
            if row["outbox_state"] is None:
                issues.append(f"operation {operation_id} has no outbox event")
                continue
            state = str(row["state"])
            outbox_state = str(row["outbox_state"])
            if bool(row["reconciliation_conflict"]) and state != OperationState.RECONCILIATION_REQUIRED.value:
                issues.append(f"operation {operation_id} has an unsafe reconciliation conflict state")
            if state == OperationState.CONFIRMED.value and outbox_state != OutboxState.DELIVERED.value:
                issues.append(f"confirmed operation {operation_id} is not delivered")
            if state == OperationState.REVERSED.value:
                if outbox_state != OutboxState.CANCELLED.value or row["reversal_transaction_id"] is None:
                    issues.append(f"reversed operation {operation_id} is not fully reversed")
            if state == OperationState.PENDING.value and outbox_state in {
                OutboxState.DELIVERED.value,
                OutboxState.CANCELLED.value,
            }:
                issues.append(f"pending operation {operation_id} has a terminal outbox state")
        return issues

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._connection.close()
                self._closed = True

    def __enter__(self) -> "LedgerStore":
        self._ensure_open()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
