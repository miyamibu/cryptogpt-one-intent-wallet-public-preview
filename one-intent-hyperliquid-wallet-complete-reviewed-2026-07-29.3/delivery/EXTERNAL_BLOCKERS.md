# External blockers — `BLOCKED_NOT_OPERATIONAL`

この文書の `Owner` は役割名です。固有の担当者、契約番号、資格情報、秘密値は未登録です。各 blocker を埋めるまで、対応 gate と feature flag を `NO_GO` のままにします。

正本の機械的な対応表は `delivery/external-blocker-traceability.json` です。本文に残る `Cxxx`／`Gxx` は旧版からのlegacy aliasであり、release判定・証拠登録には使用しません。canonical `directGateIds`／`dependentGateIds`／`claimIds`、owner、reviewer、portal、証拠path、検証command、success criteria、feature flag、再検証期限を使います。

## Wallet dependency boundary

`delivery/external-blocker-traceability.json` のcoverageは、全37 gate／93 claimへ `walletDependency` と `personalWalletRequired` を機械的に結合します。`personalWalletRequired` は常に `false` です。`NONE` はブロックチェーンID不要、`CONTROLLED_TESTNET_OR_PROVIDER_IDENTITY` は個人ではない隔離Testnet／provider identity、`PRODUCTION_SIGNER_MAINNET_OR_PROTECTED_RUNTIME` はHSM／MPC等の保護された本番権限を意味します。分類はgate closure基準であり、個人ウォレット接続や本番書込みを許可するものではありません。

同JSONの`coverage`は、構成済みの37 gateと93 claimを各1回ずつ列挙します。各gate／claimは`EXTERNAL_BLOCKER`または`INTERNAL_IMPLEMENTATION`として分類され、外部blockerに未列挙の項目も未追跡にはなりません。`LOCAL_VALIDATION`は本番claimを満たさないため、独立したGO分類としては扱いません。

Claim ID は外部証跡が直接必要なものだけを記載します。ローカル実装の不足、validator／native project／admin plane の不足は外部 blocker に置き換えず、`BLOCKED_INTERNAL` として別途実装・検証します。fake／simulated claim は、外部証拠を取得するまで operational PASS へ昇格しません。

## EXT-001 — Python／Playwright／Chromium の再現環境

- Legacy aliases: C003, C062, C063, C064, C065
- Canonical claims: SCOPE_LOCKED, REQUIREMENTS_TRACED, SBOM_PROVENANCE_SIGNED, EVIDENCE_BOUND_TO_RELEASE
- Owner: Release engineer; reviewer: independent build reviewer
- Portal/service: 管理対象の macOS CI runner と Python package mirror
- Account/permission: runner 管理権限、依存キャッシュの read、署名 artifact の write
- Menu/field: runner image、Python version、Playwright version、Chromium revision、architecture を固定する CI job fields
- Prepare: `python3` executable、Playwright package、Chromium revision、immutable image digest、SBOM
- Verify: `python3 -B tools/run_full_validation.py`、`python3 -B tools/build_release.py /tmp/one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.3.zip`、clean extractで同じ結果
- Evidence: `delivery/evidence/core/build-environment.json` と image/package hashes
- Canonical gates: SCOPE_AND_TRACEABILITY / SUPPLY_CHAIN / RELEASE_APPROVAL

## EXT-002 — Android build and physical device evidence

- Legacy aliases: C045, C049, C050, C051, C076
- Canonical claims: ANDROID_BUILD_SIGNED, ANDROID_DEVICE_MATRIX, ANDROID_PLATFORM_SECURITY, ATTESTATION_VERIFIED_SERVER_SIDE, UNSUPPORTED_DEVICE_POLICY, WCAG_AND_NATIVE_A11Y, COGNITIVE_COMPREHENSION
- Owner: Android engineer; reviewer: mobile security reviewer
- Service/portal: Android SDK／Gradle CI、Google Play internal testing portal
- Account/permission: Android build service account、Pixel 9a／compact Android USB debugging、internal tester permission
- Menu/field: SDK Manager で SDK／Build Tools／emulator image を確認し、Gradle task `assembleDebug`、`test`、`connectedCheck` を実行。Play Console は `Testing > Internal testing > Create new release` を使うが、公開はしない
- Prepare: exact JDK/Gradle/AGP versions、package name、debug signing configuration、device OS/build、TalkBack settings
- Verify: source/tree/config digest と APK/AAB/SBOM/provenance が同一 release subject に bind。Pixel 9a、compact device、largest text、dark/light、IME、process death、overlay、backup、clipboard、screen capture を timestamp 付きで記録
- Evidence: `delivery/evidence/android/` に signed test report、screenshots、device matrix、artifact hashes。秘密鍵や keystore は置かない
- Canonical gates: ANDROID_RELEASE / DEVICE_ATTESTATION / ACCESSIBILITY / USER_ACCEPTANCE

## EXT-003 — iOS build and physical device evidence

- Legacy aliases: C048, C049, C050, C051, C077
- Canonical claims: IOS_BUILD_SIGNED, IOS_DEVICE_MATRIX, IOS_PLATFORM_SECURITY, ATTESTATION_VERIFIED_SERVER_SIDE, UNSUPPORTED_DEVICE_POLICY, WCAG_AND_NATIVE_A11Y, COGNITIVE_COMPREHENSION, APPLE_ORGANIZATION_ELIGIBLE, APPLE_REVIEW_APPROVED
- Owner: iOS engineer; reviewer: mobile security reviewer
- Service/portal: macOS Xcode CI、Apple Developer、TestFlight internal testing
- Account/permission: team member with build/test permission、iPhone 12、small supported iPhone、current Face ID iPhone
- Menu/field: Xcode scheme `Build`／`Test`、`Product > Archive`、TestFlight internal group. App Store submission is a separate closed gate
- Prepare: exact Xcode/Swift/SDK versions、bundle identifier、entitlements、privacy labels、App Attest environment、device OS/build
- Verify: SwiftUI rendering, VoiceOver Japanese labels, Dynamic Type, safe area, keyboard, rotation, process termination, Keychain access classes, pasteboard, screen recording/snapshot and App Attest server evidence
- Evidence: `delivery/evidence/ios/` with signed archive digest, device matrix, screenshots, logs, reviewer identity and timestamps. Do not store certificates or profiles containing secrets
- Canonical gates: IOS_RELEASE / DEVICE_ATTESTATION / ACCESSIBILITY / APPLE_DISTRIBUTION / USER_ACCEPTANCE

## EXT-004 — Official Hyperliquid protocol and Testnet access

- Legacy aliases: C034, C035, C036, C037, C038, C039
- Canonical claims: HL_API_VERSION_PINNED, HL_ORDER_LIFECYCLE_TESTED, HL_MARGIN_MODEL_VERIFIED, LIQUIDATION_PREVIEW_VALIDATED, STALE_OR_UNKNOWN_BLOCKED, TESTNET_ALL_FLOWS, TESTNET_NO_UNEXPLAINED_DIFF, ZERO_UNEXPLAINED_DIFFERENCE
- Owner: protocol integration engineer; reviewer: independent protocol reviewer
- Service/portal: official Hyperliquid documentation/source and Testnet account portal
- Account/permission: isolated Testnet account and test funds; no Mainnet key or production API wallet
- Menu/field: dated documentation revision, Testnet endpoint, API-wallet/agent lifecycle screen, rate-limit documentation
- Prepare: immutable docs/SDK source hashes, market metadata, chain/domain configuration, redacted request IDs
- Verify: place/cancel/replace, partial fill, reject, stale nonce, disconnect, delayed status, duplicate request, restart reconciliation, cross/isolated margin, liquidation field, fee arithmetic, emergency cancel
- Evidence: `delivery/evidence/hyperliquid-testnet/` with redacted receipts, exact endpoint/version, source hash, test account identity hash
- Canonical gates: HYPERLIQUID_INTEGRATION / LIQUIDATION_RISK / TESTNET_E2E / RECONCILIATION_LEDGER

## EXT-005 — JPYC product and JPYC EX partner agreement

- Legacy aliases: C027, C082
- Canonical claims: JPYC_OFFICIAL_DATA_PINNED, JPYC_EX_CONTRACTED_TESTED, REGISTRY_SIGNED_PINNED, TOKEN_BEHAVIOR_ALLOWLIST, VENDORS_CONTRACTED, JP_LEGAL_OPINION
- Owner: legal/operations owner; reviewer: separate legal reviewer and partner reviewer
- Service/portal: JPYC official issuer materials and contracted JPYC EX/partner onboarding portal
- Account/permission: registered business account with production/sandbox onboarding authority
- Menu/field: current product/version, network, official contract source, decimals, code hash, redirect/callback registration, webhook authentication, sandbox certification, go-live checklist
- Prepare: legal entity information, contact, domains, callback URLs, privacy/DPA materials, support route, issuer fake-token warnings
- Verify: two independent official observations, registry entry and revocation process, partner contract number, sandbox end-to-end application and on-chain receipt reconciliation
- Evidence: `delivery/evidence/asset-registry/` and `delivery/evidence/jpyc-ex/` with signed registry snapshot, contract/code hash, agreement ID, callback export, test receipts; never store KYC or bank secrets
- Canonical gates: JPYC_INTEGRATION / ASSET_REGISTRY / PROVIDER_CONTRACTS / LEGAL_JAPAN

## EXT-006 — Verified fee sponsor/paymaster/relayer route

- Legacy aliases: C083, C084, C085
- Canonical claims: ZERO_GAS_PATH_PROVEN, FEE_QUOTE_BOUND_CAPPED, FEE_BUDGET_CONCURRENT_SAFE, VENDORS_CONTRACTED, VENDOR_EXIT_AND_OUTAGE, ZERO_UNEXPLAINED_DIFFERENCE, NO_BLIND_RETRY
- Owner: fee-route operations owner; reviewer: independent risk/finance reviewer
- Service/portal: provider onboarding portal and contract/API documentation
- Account/permission: provider account with terms, support, jurisdiction, settlement and reserve visibility
- Menu/field: capability status, exact account model, supported network/token, allowance/permit bootstrap, quote API, expiry, maximum fee, failure charge, reimbursement terms, rate limit and revoke control
- Prepare: provider ID, route ID, settlement target, operation limits, monthly/daily/user budgets, support escalation
- Verify: operation-bound quote, nonce replay, provider revocation, expired quote, chain mismatch, failed-action charge, duplicate reimbursement, no silent fallback, zero-native-balance canary in sandbox
- Evidence: `delivery/evidence/fee-route/` with signed capability/quote, terms hash, reserve/health evidence, provider key identity and test receipts
- Canonical gates: FEE_READINESS / PROVIDER_CONTRACTS / RECONCILIATION_LEDGER / FAILURE_RECOVERY

## EXT-007 — Independent security, protocol, mobile, and cryptography reviews

- Legacy aliases: C061, C078, C079
- Canonical claims: MOBILE_BACKEND_PENTEST, CRYPTO_SMART_CONTRACT_AUDIT, NO_OPEN_CRITICAL_HIGH, SIGNER_ARCHITECTURE_AUDITED
- Owner: security owner; reviewer: external review firm with no implementation approval role
- Service/portal: contracted audit firm evidence portal
- Account/permission: audit project access, read-only frozen source and exact release subject
- Menu/field: scope, version, commit/tree digest, threat model, findings, severity, owner, due date, fix commit, retest, accepted-risk approver
- Prepare: frozen source, binaries, SBOM/provenance, test vectors, mobile artifacts, protocol docs, deployment diagrams
- Verify: no unresolved critical/high findings, signed final reports, independent reviewer identity and artifact hashes
- Evidence: `delivery/evidence/security/` and report signatures; draft/self-review is not audit evidence
- Canonical gates: SECURITY_ASSESSMENT / KEY_CUSTODY_SIGNER / SUPPLY_CHAIN

## EXT-008 — Legal, regional, privacy, and store decisions

- Legacy aliases: C072, C073, C074, C075, C087
- Canonical claims: JP_LEGAL_OPINION, REGISTRATIONS_PERMISSIONS, TERMS_DISCLOSURES_TAX, DATA_MAP_AND_MINIMIZATION, DSAR_BREACH_PROCESS, APPLE_ORGANIZATION_ELIGIBLE, APPLE_REVIEW_APPROVED, PLAY_DECLARATIONS_COMPLETE, PLAY_REVIEW_APPROVED, VENDORS_CONTRACTED
- Owner: legal counsel and release owner; reviewer: independent legal/store reviewer
- Service/portal: retained counsel, Apple Developer/App Store Connect, Google Play Console
- Account/permission: exact legal entity owner, regional distribution and store submission permissions
- Menu/field: written decisions for custody, exchange/derivatives, marketing, JPYC handoff, AML/KYC, privacy/cross-border, fee sponsorship, Apple/Google crypto declarations, country list, support/complaints
- Prepare: exact release binaries, bundle/package IDs, privacy labels, permissions, risk disclosures, terms, support URL, geofence config
- Verify: signed counsel memo, Apple submission ID/decision, Google review/declaration result, exact region and binary digest match
- Evidence: `delivery/evidence/legal-store/` with redacted written approvals and portal exports; no password/2FA in repository
- Canonical gates: LEGAL_JAPAN / PRIVACY_DATA_GOVERNANCE / APPLE_DISTRIBUTION / GOOGLE_DISTRIBUTION / PROVIDER_CONTRACTS

## EXT-009 — Production signer, HSM/MPC, release trust, and out-of-band anchors

- Legacy aliases: C066, C067, C068, C069, C070, C071, C088, C089, C090, C091
- Canonical claims: SIGNER_ARCHITECTURE_AUDITED, KEY_CEREMONY_COMPLETE, SIGNER_FAIL_CLOSED, CAPSULE_EXACT_BINDING, ONE_TIME_REPLAY_PROTECTION, TWO_PERSON_HIGH_RISK, BREAK_GLASS_AUDITED, SBOM_PROVENANCE_SIGNED, EVIDENCE_BOUND_TO_RELEASE, INDEPENDENT_GO_APPROVAL, TRUSTED_TIME_AVAILABLE, RUNTIME_STATE_HEALTHY, SHORT_LIVED_WRITE_LEASE, PER_OPERATION_USER_AUTH
- Owner: custody/release security owner; reviewer: separate key ceremony and operations reviewers
- Service/portal: approved HSM/MPC facility and protected release environment
- Account/permission: two-person ceremony roles, no AI process access, protected high-water mark admin
- Menu/field: key generation, attestation, backup/recovery, rotation/revocation, release signing, trusted time, evidence index, ONE_INTENT_* anchors
- Prepare: hardware, ceremony witnesses, policy IDs, signer image/config digests, rollback-resistant storage, restore drill
- Verify: signer recomputes registry/quote/final payload; release/runtime/per-operation gates are independent; older counters cannot be accepted after rollback
- Evidence: protected out-of-band record referenced by `delivery/evidence-index.json`; private keys never enter this repository
- Canonical gates: KEY_CUSTODY_SIGNER / TRANSACTION_AUTHORIZATION / ADMIN_CHANGE_CONTROL / SUPPLY_CHAIN / RELEASE_APPROVAL / RUNTIME_ACTIVATION

## 進行を再開する最小順序

1. EXT-001 で exact build environment を固定し、local double-build／clean-extract を再実行する。
2. EXT-002/003 で native shell を実機に載せ、Android/iOS evidence を release subject に bind する。
3. EXT-004〜006 の sandbox/Testnet／partner／fee evidence を fake と分けて登録する。
4. EXT-007〜009 の独立レビュー、法務・ストア、signer/HSM／out-of-band anchor を取得する。
5. `python3 -B tools/run_full_validation.py`、`python3 -B tools/check_operational_readiness.py --require-go ...` を clean independent environment で再実行する。

一つでも失敗、期限切れ、scope mismatch、replay、差分、unresolved high finding、ledger difference があれば `BLOCKED_NOT_OPERATIONAL` に戻します。
