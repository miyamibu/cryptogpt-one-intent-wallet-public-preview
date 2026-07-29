from __future__ import annotations

import unittest

from shared.domain import DurableSaga, DomainError, SagaStepState
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

    def test_browser_matrix_is_exactly_288(self) -> None:
        validate_prototype()
        self.assertEqual(len(cases()), 288)
