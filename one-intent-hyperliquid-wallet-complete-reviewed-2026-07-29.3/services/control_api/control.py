from __future__ import annotations

from dataclasses import dataclass, field

from shared.domain import ActionPlanDraft, AuthorizationEnvelope, CanonicalQuote, DomainError, ExecutionCapsule, PolicyDecision, SignedRegistry
from services.signer_interface.signer import SignerInterface


@dataclass
class ControlApi:
    """In-process facade. Network routing and authentication remain deployment concerns."""

    write_enabled: bool = False
    signer: SignerInterface = field(default_factory=SignerInterface)

    def __post_init__(self) -> None:
        if type(self.write_enabled) is not bool:
            raise DomainError("control API write gate must be a boolean")
        if not isinstance(self.signer, SignerInterface):
            raise DomainError("control API signer has the wrong runtime type")

    def execute(
        self,
        capsule: ExecutionCapsule,
        *,
        authorization: AuthorizationEnvelope | None = None,
        policy_decision: PolicyDecision | None = None,
        release: dict[str, object] | None = None,
        runtime: dict[str, object] | None = None,
        registry: SignedRegistry | None = None,
        quote: CanonicalQuote | None = None,
        now: int,
    ) -> str:
        if not self.write_enabled:
            raise DomainError("control API write gate is disabled")
        if not isinstance(capsule, ExecutionCapsule):
            raise DomainError("execution capsule has the wrong runtime type")
        capsule.validate(now)
        if not isinstance(authorization, AuthorizationEnvelope) or not isinstance(policy_decision, PolicyDecision):
            raise DomainError("authorization and policy decision are required")
        if not isinstance(release, dict) or not isinstance(runtime, dict):
            raise DomainError("release and runtime inputs are required")
        if type(policy_decision.allowed) is not bool or not policy_decision.allowed:
            reason = policy_decision.reason_code if isinstance(policy_decision.reason_code, str) else "INVALID_POLICY"
            raise DomainError(f"policy denied: {reason}")
        self.signer.sign_if_all_gates_pass(
            capsule,
            authorization,
            release=release,
            runtime=runtime,
            registry=registry,
            quote=quote,
            now=now,
        )
        return "signing_gate_passed_no_broadcast"

    def create_draft(self, draft: ActionPlanDraft) -> dict[str, object]:
        if not isinstance(draft, ActionPlanDraft):
            raise DomainError("draft has the wrong runtime type")
        draft.validate()
        return {
            "sourceUtterance": draft.source_utterance,
            "normalizedInterpretation": draft.normalized_interpretation,
            "materialAmbiguities": list(draft.material_ambiguities),
            "primaryActionEnabled": draft.executable,
        }
