from __future__ import annotations

from dataclasses import dataclass

from shared.domain import DurableSaga, SagaStepState


@dataclass
class Reconciler:
    saga: DurableSaga

    def authoritative_update(self, step_id: str, state: str) -> str:
        return self.saga.reconcile(step_id, SagaStepState(state)).state.value

    def pending_states(self) -> list[str]:
        return [step.step_id for step in self.saga.steps if step.state in {SagaStepState.UNKNOWN, SagaStepState.SUBMITTED, SagaStepState.ACCEPTED}]
