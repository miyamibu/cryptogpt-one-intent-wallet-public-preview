# Release Gate Evidence Checklist

## Release metadata

- Release ID:
- Git commit:
- Android version:
- Backend image digest:
- Signer image digest:
- Model snapshot:
- Prompt hash:
- Schema version:
- Policy version:
- Registry version:
- Source pin version:

## Evidence

- [ ] unit report
- [ ] integration report
- [ ] Testnet transaction list
- [ ] Pixel 9a device report
- [ ] AI eval report
- [ ] signing golden vectors
- [ ] chaos report
- [ ] external audit
- [ ] remediation
- [ ] recovery drill
- [ ] incident drill
- [ ] legal memo
- [ ] privacy review
- [ ] source change report
- [ ] feature gate signatures
- [ ] SBOM
- [ ] dependency vulnerability report
- [ ] secret scan
- [ ] log redaction
- [ ] backup restore evidence

## Decision

```text
DESIGN_GO
OFFLINE_PROTOTYPE_GO
CODEX_IMPLEMENTATION_GO
ANDROID_BUILD_NO_GO
IOS_BUILD_NO_GO
TESTNET_WRITE_NO_GO
PERSONAL_SMALL_MAINNET_NO_GO
CLOSED_ALPHA_NO_GO
PUBLIC_ANDROID_STORE_NO_GO
PUBLIC_IOS_APP_STORE_NO_GO
```

Approvers:
- Engineering:
- Security:
- Operations:
- Legal:
- Product:

## Additional mandatory evidence

- [ ] agent bearer-risk characterization report
- [ ] named／unnamed agent lifecycle report
- [ ] independent state source inventory
- [ ] state divergence chaos report
- [ ] Protected Confirmation capability report for Pixel 9a
- [ ] canonical promptText vectors
- [ ] trusted-display fallback report
- [ ] Bridge2 pinned fork/harness report
- [ ] HyperEVM pinned fork report
- [ ] Testnet faucet/address prerequisite record
- [ ] Google Play Financial features declaration
- [ ] Google Play crypto-policy eligibility evidence
- [ ] target-country/store distribution approval
