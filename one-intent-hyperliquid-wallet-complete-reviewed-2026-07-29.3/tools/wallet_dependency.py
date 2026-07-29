"""Machine-readable wallet/account dependency classes for readiness gates.

This module distinguishes a user's personal wallet from controlled identities
needed for sandbox/provider testing or protected production signing. The
classification is a gate-closure contract; it does not grant write permission.
"""
from __future__ import annotations

from typing import Final

WALLET_DEPENDENCY_VERSION: Final = "1.0"
NO_BLOCKCHAIN_IDENTITY: Final = "NONE"
CONTROLLED_TESTNET_OR_PROVIDER_IDENTITY: Final = "CONTROLLED_TESTNET_OR_PROVIDER_IDENTITY"
PRODUCTION_SIGNER_MAINNET_OR_PROTECTED_RUNTIME: Final = "PRODUCTION_SIGNER_MAINNET_OR_PROTECTED_RUNTIME"

WALLET_DEPENDENCY_CLASSES: Final = frozenset(
    {
        NO_BLOCKCHAIN_IDENTITY,
        CONTROLLED_TESTNET_OR_PROVIDER_IDENTITY,
        PRODUCTION_SIGNER_MAINNET_OR_PROTECTED_RUNTIME,
    }
)

GATES_BY_WALLET_DEPENDENCY: Final = {
    NO_BLOCKCHAIN_IDENTITY: frozenset(
        {
            "ACCESSIBILITY",
            "AI_NATURAL_LANGUAGE",
            "ANDROID_RELEASE",
            "APPLE_DISTRIBUTION",
            "ASSET_REGISTRY",
            "AUTH_SESSION_RECOVERY",
            "BACKEND_RELEASE",
            "CHATGPT_BOUNDARY",
            "DETERMINISTIC_CORE",
            "DEVICE_ATTESTATION",
            "GOOGLE_DISTRIBUTION",
            "INCIDENT_DRILLS",
            "IOS_RELEASE",
            "LEGAL_JAPAN",
            "POST_LAUNCH_MONITORING",
            "PRIVACY_DATA_GOVERNANCE",
            "PROVIDER_CONTRACTS",
            "RELEASE_APPROVAL",
            "SCOPE_AND_TRACEABILITY",
            "SECURITY_ASSESSMENT",
            "SRE_RESILIENCE",
            "SUPPLY_CHAIN",
            "USER_ACCEPTANCE",
            "UX_PLAIN_JAPANESE",
        }
    ),
    CONTROLLED_TESTNET_OR_PROVIDER_IDENTITY: frozenset(
        {
            "FAILURE_RECOVERY",
            "FEE_READINESS",
            "HYPERLIQUID_INTEGRATION",
            "JPYC_INTEGRATION",
            "LIQUIDATION_RISK",
            "RECONCILIATION_LEDGER",
            "SWAP_AND_CROSS_NETWORK",
            "TESTNET_E2E",
        }
    ),
    PRODUCTION_SIGNER_MAINNET_OR_PROTECTED_RUNTIME: frozenset(
        {
            "ADMIN_CHANGE_CONTROL",
            "KEY_CUSTODY_SIGNER",
            "MAINNET_CANARY",
            "RUNTIME_ACTIVATION",
            "TRANSACTION_AUTHORIZATION",
        }
    ),
}


def wallet_dependency_for_gate(gate_id: str) -> str:
    """Return exactly one conservative dependency class for a canonical gate."""
    matches = [dependency for dependency, gate_ids in GATES_BY_WALLET_DEPENDENCY.items() if gate_id in gate_ids]
    if len(matches) != 1:
        raise ValueError(f"wallet dependency classification must cover exactly one class: {gate_id}")
    return matches[0]


def validate_gate_partition(gate_ids: set[str]) -> None:
    """Reject stale, duplicated, or missing gate classifications."""
    classified = set().union(*GATES_BY_WALLET_DEPENDENCY.values())
    if classified != gate_ids:
        raise ValueError(
            "wallet dependency gate partition drift: "
            f"missing={sorted(gate_ids - classified)}, unexpected={sorted(classified - gate_ids)}"
        )
    if sum(len(gates) for gates in GATES_BY_WALLET_DEPENDENCY.values()) != len(classified):
        raise ValueError("wallet dependency gate partition contains duplicate gate IDs")
