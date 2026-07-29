from __future__ import annotations

import sqlite3
import stat
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from services.ledger_store import (
    LedgerConflictError,
    LedgerLine,
    LedgerNotFoundError,
    LedgerStore,
    LedgerStoreIntegrityError,
    LedgerValidationError,
    OperationState,
    OutboxMessage,
    OutboxState,
    ReconciliationResult,
)
from services.ledger_store.store import LOCAL_ONLY, NETWORK_IO_ENABLED


class LedgerStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.database = str(Path(self.directory.name) / "ledger.sqlite")
        self.store = LedgerStore(self.database)
        self.store.register_account("wallet-cash", "USDC", now=1)
        self.store.register_account("settlement-clearing", "USDC", now=1)

    def tearDown(self) -> None:
        self.store.close()
        self.directory.cleanup()

    @staticmethod
    def message(event_id: str = "event-1", dedupe_key: str = "dedupe-1") -> OutboxMessage:
        return OutboxMessage(
            event_id=event_id,
            topic="local.settlement.requested",
            dedupe_key=dedupe_key,
            payload={"operationId": "operation-1", "amountMinor": 500, "assetId": "USDC"},
        )

    @staticmethod
    def lines(amount: int = 500) -> tuple[LedgerLine, LedgerLine]:
        return (
            LedgerLine("wallet-cash", "USDC", -amount),
            LedgerLine("settlement-clearing", "USDC", amount),
        )

    def post(self):
        return self.store.post_operation(
            operation_id="operation-1",
            idempotency_key="idempotency-1",
            transaction_id="transaction-1",
            lines=self.lines(),
            outbox=self.message(),
            now=10,
        )

    def test_module_is_explicitly_local_only(self) -> None:
        self.assertTrue(LOCAL_ONLY)
        self.assertFalse(NETWORK_IO_ENABLED)
        with self.assertRaises(LedgerValidationError):
            LedgerStore(":memory:")
        with self.assertRaises(LedgerValidationError):
            LedgerStore("relative.sqlite")

    def test_owner_only_permissions_and_time_rollback_fence(self) -> None:
        self.assertEqual(stat.S_IMODE(Path(self.database).stat().st_mode) & 0o077, 0)
        self.post()
        health = self.store.monitor_health(now=9)
        self.assertEqual(health.status, "UNHEALTHY")
        self.assertTrue(any("high-water" in issue for issue in health.issues))
        with self.assertRaises(LedgerStoreIntegrityError):
            self.store.claim_outbox("worker-a", now=9)

    def test_balanced_ledger_and_outbox_commit_atomically(self) -> None:
        snapshot = self.post()
        self.assertEqual(snapshot.state, OperationState.PENDING)
        self.assertEqual(snapshot.outbox_state, OutboxState.PENDING)
        self.assertEqual(self.store.account_balance("wallet-cash"), -500)
        self.assertEqual(self.store.account_balance("settlement-clearing"), 500)
        health = self.store.monitor_health(now=10)
        self.assertEqual(health.status, "HEALTHY")
        self.assertEqual(health.pending_outbox, 1)

    def test_unbalanced_post_rolls_back_operation_and_outbox(self) -> None:
        with self.assertRaises(LedgerValidationError):
            self.store.post_operation(
                operation_id="operation-1",
                idempotency_key="idempotency-1",
                transaction_id="transaction-1",
                lines=(
                    LedgerLine("wallet-cash", "USDC", -500),
                    LedgerLine("settlement-clearing", "USDC", 499),
                ),
                outbox=self.message(),
                now=10,
            )
        with self.assertRaises(LedgerNotFoundError):
            self.store.get_operation("operation-1")
        self.assertEqual(self.store.monitor_health(now=10).pending_outbox, 0)

    def test_outbox_identity_conflict_rolls_back_the_entire_second_post(self) -> None:
        self.post()
        with self.assertRaises(LedgerConflictError):
            self.store.post_operation(
                operation_id="operation-2",
                idempotency_key="idempotency-2",
                transaction_id="transaction-2",
                lines=self.lines(200),
                outbox=self.message(event_id="event-1", dedupe_key="dedupe-2"),
                now=11,
            )
        with self.assertRaises(LedgerNotFoundError):
            self.store.get_operation("operation-2")
        self.assertEqual(self.store.account_balance("wallet-cash"), -500)

    def test_account_asset_identity_is_immutable(self) -> None:
        self.assertFalse(self.store.register_account("wallet-cash", "USDC", now=2))
        with self.assertRaises(LedgerConflictError):
            self.store.register_account("wallet-cash", "JPYC", now=2)
        with self.assertRaises(LedgerNotFoundError):
            self.store.post_operation(
                operation_id="missing-account-operation",
                idempotency_key="missing-account-key",
                transaction_id="missing-account-transaction",
                lines=(
                    LedgerLine("wallet-cash", "USDC", -1),
                    LedgerLine("unregistered", "USDC", 1),
                ),
                outbox=self.message("missing-account-event", "missing-account-dedupe"),
                now=3,
            )

    def test_exact_idempotent_replay_and_material_conflict(self) -> None:
        first = self.post()
        replay = self.post()
        self.assertEqual(first, replay)
        with self.assertRaises(LedgerConflictError):
            self.store.post_operation(
                operation_id="operation-1",
                idempotency_key="idempotency-1",
                transaction_id="transaction-1",
                lines=self.lines(600),
                outbox=self.message(),
                now=11,
            )
        self.assertEqual(self.store.account_balance("wallet-cash"), -500)

    def test_outbox_lease_is_exclusive_and_requires_owner(self) -> None:
        self.post()
        claimed = self.store.claim_outbox("worker-a", now=20, lease_seconds=10)
        self.assertEqual(len(claimed), 1)
        self.assertEqual(claimed[0].attempts, 1)
        self.assertEqual(claimed[0].lease_until, 30)
        self.assertEqual(self.store.claim_outbox("worker-b", now=21), ())
        with self.assertRaises(LedgerConflictError):
            self.store.mark_outbox_delivered("event-1", "worker-b", now=22)
        self.assertTrue(self.store.mark_outbox_delivered("event-1", "worker-a", now=22))
        self.assertFalse(self.store.mark_outbox_delivered("event-1", "worker-a", now=23))
        snapshot = self.store.get_operation("operation-1")
        self.assertEqual(snapshot.state, OperationState.RECONCILIATION_REQUIRED)
        self.assertEqual(snapshot.outbox_state, OutboxState.DELIVERED)

    def test_expired_lease_recovery_requeues_without_inventing_delivery(self) -> None:
        self.post()
        self.store.claim_outbox("worker-a", now=20, lease_seconds=5)
        degraded = self.store.monitor_health(now=25)
        self.assertEqual(degraded.status, "DEGRADED")
        self.assertEqual(degraded.expired_leases, 1)
        recovery = self.store.recover(now=25)
        self.assertEqual(recovery.requeued_expired_leases, 1)
        self.assertEqual(recovery.operations_flagged_for_reconciliation, 0)
        self.assertEqual(recovery.health.status, "HEALTHY")
        claimed_again = self.store.claim_outbox("worker-b", now=25, lease_seconds=5)
        self.assertEqual(claimed_again[0].attempts, 2)

    def test_confirmed_observation_resolves_send_acknowledgement_gap(self) -> None:
        self.post()
        report = self.store.reconcile_operation(
            "operation-1",
            observation_id="observation-confirmed-1",
            result=ReconciliationResult.CONFIRMED,
            observed_at=30,
            now=30,
            external_reference="external-effect-1",
        )
        self.assertFalse(report.conflicting_observation)
        self.assertEqual(report.operation.state, OperationState.CONFIRMED)
        self.assertEqual(report.operation.outbox_state, OutboxState.DELIVERED)
        self.store.claim_outbox("no-events-worker", now=40)
        duplicate = self.store.reconcile_operation(
            "operation-1",
            observation_id="observation-confirmed-1",
            result=ReconciliationResult.CONFIRMED,
            observed_at=30,
            now=41,
            external_reference="external-effect-1",
        )
        self.assertTrue(duplicate.duplicate_observation)
        self.assertEqual(self.store.monitor_health(now=41).status, "HEALTHY")

    def test_not_applied_observation_creates_exact_reversal_once(self) -> None:
        self.post()
        report = self.store.reconcile_operation(
            "operation-1",
            observation_id="observation-not-applied-1",
            result=ReconciliationResult.NOT_APPLIED,
            observed_at=30,
            now=30,
        )
        self.assertTrue(report.reversal_created)
        self.assertEqual(report.operation.state, OperationState.REVERSED)
        self.assertEqual(report.operation.outbox_state, OutboxState.CANCELLED)
        self.assertIsNotNone(report.operation.reversal_transaction_id)
        self.assertEqual(self.store.account_balance("wallet-cash"), 0)
        self.assertEqual(self.store.account_balance("settlement-clearing"), 0)
        second = self.store.reconcile_operation(
            "operation-1",
            observation_id="observation-not-applied-2",
            result=ReconciliationResult.NOT_APPLIED,
            observed_at=31,
            now=31,
        )
        self.assertFalse(second.reversal_created)
        self.assertEqual(self.store.monitor_health(now=31).status, "HEALTHY")

    def test_unknown_and_conflicting_observations_fail_closed(self) -> None:
        self.post()
        unknown = self.store.reconcile_operation(
            "operation-1",
            observation_id="observation-unknown",
            result=ReconciliationResult.UNKNOWN,
            observed_at=20,
            now=20,
        )
        self.assertEqual(unknown.operation.state, OperationState.RECONCILIATION_REQUIRED)
        self.assertEqual(self.store.monitor_health(now=20).status, "DEGRADED")
        recovered = self.store.recover(now=20)
        self.assertEqual(recovered.operations_flagged_for_reconciliation, 0)
        self.assertEqual(
            self.store.get_operation("operation-1").state,
            OperationState.RECONCILIATION_REQUIRED,
        )
        confirmed = self.store.reconcile_operation(
            "operation-1",
            observation_id="observation-confirmed",
            result=ReconciliationResult.CONFIRMED,
            observed_at=21,
            now=21,
            external_reference="external-effect-1",
        )
        self.assertEqual(confirmed.operation.state, OperationState.CONFIRMED)
        conflict = self.store.reconcile_operation(
            "operation-1",
            observation_id="observation-conflict",
            result=ReconciliationResult.NOT_APPLIED,
            observed_at=22,
            now=22,
        )
        self.assertTrue(conflict.conflicting_observation)
        self.assertFalse(conflict.reversal_created)
        self.assertEqual(conflict.operation.state, OperationState.RECONCILIATION_REQUIRED)
        self.assertTrue(conflict.operation.reconciliation_conflict)
        self.assertEqual(self.store.account_balance("wallet-cash"), -500)
        still_locked = self.store.reconcile_operation(
            "operation-1",
            observation_id="observation-conflict-repeat",
            result=ReconciliationResult.NOT_APPLIED,
            observed_at=23,
            now=23,
        )
        self.assertTrue(still_locked.conflicting_observation)
        self.assertFalse(still_locked.reversal_created)
        self.assertEqual(still_locked.operation.state, OperationState.RECONCILIATION_REQUIRED)
        self.assertEqual(self.store.account_balance("wallet-cash"), -500)

    def test_external_reference_cannot_confirm_two_operations(self) -> None:
        self.post()
        self.store.reconcile_operation(
            "operation-1",
            observation_id="observation-operation-1",
            result=ReconciliationResult.CONFIRMED,
            observed_at=20,
            now=20,
            external_reference="external-effect-shared",
        )
        self.store.post_operation(
            operation_id="operation-2",
            idempotency_key="idempotency-2",
            transaction_id="transaction-2",
            lines=self.lines(200),
            outbox=self.message("event-2", "dedupe-2"),
            now=21,
        )
        conflict = self.store.reconcile_operation(
            "operation-2",
            observation_id="observation-operation-2",
            result=ReconciliationResult.CONFIRMED,
            observed_at=22,
            now=22,
            external_reference="external-effect-shared",
        )
        self.assertTrue(conflict.conflicting_observation)
        self.assertTrue(conflict.operation.reconciliation_conflict)
        self.assertEqual(conflict.operation.state, OperationState.RECONCILIATION_REQUIRED)
        self.assertEqual(conflict.operation.outbox_state, OutboxState.PENDING)

    def test_retry_is_delayed_and_does_not_duplicate_event(self) -> None:
        self.post()
        self.store.claim_outbox("worker-a", now=20, lease_seconds=10)
        with self.assertRaises(LedgerValidationError):
            self.store.mark_outbox_retry(
                "event-1", "worker-a", now=21, retry_at=40, error_code="token=secret"
            )
        self.store.mark_outbox_retry(
            "event-1", "worker-a", now=21, retry_at=40, error_code="LOCAL_DISPATCHER_UNAVAILABLE"
        )
        self.assertEqual(self.store.claim_outbox("worker-b", now=39), ())
        claimed = self.store.claim_outbox("worker-b", now=40)
        self.assertEqual([event.event_id for event in claimed], ["event-1"])
        self.assertEqual(claimed[0].attempts, 2)

    def test_reconciliation_rejects_future_or_pre_operation_observations(self) -> None:
        self.post()
        with self.assertRaises(LedgerValidationError):
            self.store.reconcile_operation(
                "operation-1",
                observation_id="future-observation",
                result=ReconciliationResult.UNKNOWN,
                observed_at=31,
                now=30,
            )
        with self.assertRaises(LedgerValidationError):
            self.store.reconcile_operation(
                "operation-1",
                observation_id="pre-operation-observation",
                result=ReconciliationResult.UNKNOWN,
                observed_at=9,
                now=30,
            )

    def test_two_connections_share_the_durable_lease(self) -> None:
        self.post()
        second = LedgerStore(self.database)
        try:
            first_claim = self.store.claim_outbox("worker-a", now=20, lease_seconds=10)
            second_claim = second.claim_outbox("worker-b", now=20, lease_seconds=10)
            self.assertEqual([event.event_id for event in first_claim], ["event-1"])
            self.assertEqual(second_claim, ())
        finally:
            second.close()

    def test_state_survives_close_and_reopen(self) -> None:
        self.post()
        self.store.close()
        self.store = LedgerStore(self.database)
        snapshot = self.store.get_operation("operation-1")
        self.assertEqual(snapshot.state, OperationState.PENDING)
        self.assertEqual(self.store.account_balance("wallet-cash"), -500)

    def test_health_detects_tampered_unbalanced_entries_and_blocks_writes(self) -> None:
        self.post()
        tamper = sqlite3.connect(self.database)
        tamper.execute(
            "UPDATE ledger_entries SET amount_minor = 499 "
            "WHERE transaction_id = 'transaction-1' AND account_id = 'settlement-clearing'"
        )
        tamper.commit()
        tamper.close()
        health = self.store.monitor_health(now=20)
        self.assertEqual(health.status, "UNHEALTHY")
        self.assertTrue(any("unbalanced" in issue for issue in health.issues))
        with self.assertRaises(LedgerStoreIntegrityError):
            self.store.claim_outbox("worker-a", now=20)

    def test_non_json_financial_payload_is_rejected(self) -> None:
        message = OutboxMessage("event-float", "local.topic", "dedupe-float", {"amount": 0.1})
        with self.assertRaises(LedgerValidationError):
            self.store.post_operation(
                operation_id="operation-float",
                idempotency_key="idempotency-float",
                transaction_id="transaction-float",
                lines=self.lines(),
                outbox=message,
                now=10,
            )


if __name__ == "__main__":
    unittest.main()
