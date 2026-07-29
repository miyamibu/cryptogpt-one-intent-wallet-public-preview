"""Named module boundary for fail-closed policy evaluation."""

from .domain import PolicyDecision, PolicyInput, evaluate_policy

__all__ = ["PolicyDecision", "PolicyInput", "evaluate_policy"]
