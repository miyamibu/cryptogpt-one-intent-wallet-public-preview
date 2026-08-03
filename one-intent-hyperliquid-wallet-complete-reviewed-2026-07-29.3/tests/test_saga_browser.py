from __future__ import annotations

import unittest
import tempfile

from shared.domain import DurableSaga, DurableSagaStore, DomainError, SagaStepState
from tools.test_browser_matrix import cases, validate_prototype


class SagaBrowserTests(unittest.TestCase):
    def test_saga_is_idempotent_and_does_not_move_finalized_backwards(self) -> None:
        saga = DurableSaga("op-1")
        first = saga.submit("step-1", "idem-1", "external-1")
        duplicate = saga.submit("step-1", "idem-1", "external-1")
        self.assertIs(first, duplicate)
        saga.reconcile("step-1", SagaStepState.FINALIZED)
        with self.assertRaises(DomainError):
            saga.reconcile("step-1", SagaStepState.FAILED)

    def test_saga_state_survives_restart_and_keeps_atomic_idempotency(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = f"{directory}/saga.sqlite"
            store = DurableSagaStore(path)
            first = DurableSaga("op-durable", store=store)
            created = first.submit("step-1", "idem-1", "external-1")
            store.close()

            restarted_store = DurableSagaStore(path)
            restarted = DurableSaga("op-durable", store=restarted_store)
            duplicate = restarted.submit("step-1", "idem-1", "external-1")
            self.assertEqual(duplicate.precondition_hash, created.precondition_hash)
            restarted.reconcile("step-1", SagaStepState.UNKNOWN)
            restarted_store.close()

            final_store = DurableSagaStore(path)
            final = DurableSaga("op-durable", store=final_store)
            self.assertEqual(final.steps[0].state, SagaStepState.UNKNOWN)
            with self.assertRaises(DomainError):
                final.submit("step-1", "idem-1", "different-external")
            final_store.close()

    def test_browser_matrix_is_exactly_288(self) -> None:
        validate_prototype()
        self.assertEqual(len(cases()), 288)
