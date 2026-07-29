# Security Control Catalog

| ID | Control | Evidence |
|---|---|---|
| SC-001 | AI/Signer network isolation | network policy test |
| SC-002 | strict ActionPlan schema | schema validation |
| SC-003 | deterministic address resolver | unit test |
| SC-004 | contract allowlist | signed registry |
| SC-005 | canonical Capsule hash | golden vectors |
| SC-006 | UI button binding | instrumentation test |
| SC-007 | auth-per-use for R3/R4; standing R3 requires preregistration/cooling/cap | Pixel 9a test |
| SC-008 | decimal-safe arithmetic | property tests |
| SC-009 | cloid idempotency | chaos test |
| SC-010 | signer nonce allocator | concurrency test |
| SC-011 | no blind retry | fault injection |
| SC-012 | WS + REST reconcile | disconnect test |
| SC-013 | Bridge code hash | runtime evidence |
| SC-014 | Vault proxy monitor | change alert |
| SC-015 | exact allowance | EVM test |
| SC-016 | log redaction | automated scan |
| SC-017 | backup exclusions | restore test |
| SC-018 | feature gate signed config | signature test |
| SC-019 | admin two-person approval | audit evidence |
| SC-020 | kill switch | drill |
| SC-021 | recovery | drill |
| SC-022 | dependency pinning | lockfiles/SBOM |
| SC-023 | secret scanning | CI report |
| SC-024 | model eval gate | eval report |
| SC-025 | policy/source monitoring | diff report |
| SC-026 | legal release gate | counsel memo |
| SC-027 | unofficial branding | review |
| SC-028 | destination cooldown | integration test |
| SC-029 | SAFE_ALL reserve | property test |
| SC-030 | partial Saga receipt | UX test |
