# Operational Handoff — design-only

package=one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.3
status=BLOCKED_NOT_OPERATIONAL
localSandboxStatus=LOCAL_SANDBOX_OPERATIONAL_GO
productionWritePermitted=false
runtimeActivation=NOT_ISSUED
PRE_WALLET_GO=NOT_USED

## Canonical stage commands

```bash
python3 -B tools/prepare_release_artifacts.py
python3 -B tools/run_full_validation.py
python3 -B tools/check_operational_readiness.py
python3 -B tools/build_release.py ../one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.3.zip
```

The first command is the only mutating preparation step. The second and third
commands are non-mutating/readiness checks. The fourth command performs the
deterministic double-build and clean-extract verification outside the package.

## Handoff boundary

Do not connect a wallet, add a production key, enable a Testnet/Mainnet write,
publish to Apple/Google, or activate a runtime lease based on this package.
Before any wallet-connected work, external owners must complete the blockers in
`release/UNRESOLVED_EXTERNAL_BLOCKERS.md`, regenerate all evidence, bind it to
one exact signed release subject, and obtain independent two-person approval.
