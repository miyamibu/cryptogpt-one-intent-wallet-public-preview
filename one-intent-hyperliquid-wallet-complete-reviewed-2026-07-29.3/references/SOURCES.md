# Primary Sources

**Retrieved/checked:** 2026-07-29 JST  
These links must be rechecked before every release. A source entry is not a permanent guarantee.

## OpenAI

1. App Developer Terms  
   https://openai.com/policies/developer-apps-terms/  
   Key point: updated 2026-07-09; applies to Apps SDK apps, connectors, plugins, custom GPT actions and related apps within OpenAI Services; section 1.6(h) prohibits initiating, executing, or facilitating money transfers, cryptocurrency transfers, or other financial/investment transactions through the Services.

2. Usage Policies  
   https://openai.com/ja-JP/policies/usage-policies/  
   Key point: effective 2025-10-29; prohibits automation without human review of high-stakes decisions in sensitive domains including financial activities/credit.

3. API Data Controls  
   https://platform.openai.com/docs/models/default-usage-policies-by-endpoint  
   Key point: API data is not used to train by default unless opted in; abuse monitoring and application-state retention depend on endpoint/settings; evaluate `store:false`, ZDR/MAM and endpoint eligibility.

## Hyperliquid Documentation

4. Nonces and API Wallets  
   https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets  
   Key points: API/agent wallet signs on behalf of master/subaccounts; queries use actual account address; nonces are signer-scoped; top 100; time window; do not reuse deregistered agent addresses.

5. Exchange Endpoint  
   https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint  
   Key points: action shapes; approveAgent; order/cancel; transfers; withdraw; `cloid`; builder fee; signing inputs.

6. Signing  
   https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/signing  
   Key points: two signing schemes; field order, trailing zeros and address formatting matter; official SDK is the comparison oracle.

7. Tick and Lot Size  
   https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/tick-and-lot-size

8. Rate Limits and User Limits  
   https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits

9. WebSocket  
   https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket

10. Bridge2  
    https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/bridge2  
    Key points at check time: official Arbitrum bridge, native USDC, minimum 5 USDC, deposit with permit support, withdrawal process. Do not hardcode volatile values.

11. Bridge overview  
    https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/bridge  
    Key points at check time: validator process, dispute period, withdrawal gas fee description.

12. Sub-accounts  
    https://hyperliquid.gitbook.io/hyperliquid-docs/trading/sub-accounts  
    Key point at check time: up to 10 after $100,000 volume; therefore not universal.

13. Account Abstraction Modes  
    https://hyperliquid.gitbook.io/hyperliquid-docs/trading/account-abstraction-modes  
    Key points: Standard, Unified, Portfolio Margin; mode changes API state semantics; Portfolio Margin status must be monitored.

14. Portfolio Margin  
    https://hyperliquid.gitbook.io/hyperliquid-docs/trading/portfolio-margin  
    Key point at check time: pre-alpha and explicitly recommends very small test accounts.

15. Multi-sig  
    https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/multi-sig  
    Key point: HyperCore native multi-sig does not make HyperEVM controlled in the same manner; original wallet still controls HyperEVM and CoreWriter does not work for multi-sig users.

16. HLP Protocol Vault  
    https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/protocol-vaults  
    Key point at check time: 4-day deposit lock.

17. HyperCore Vaults  
    https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults  
    https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/hypercore-vaults-legacy  
    Key points: vault risk; owner profit share; protocol vault distinction.

18. HyperEVM  
    https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm  
    https://hyperliquid.gitbook.io/hyperliquid-docs/hyperevm  
    Key points: chain parameters and alpha-stage caveats.

19. Risks  
    https://hyperliquid.gitbook.io/hyperliquid-docs/risks  
    Key points: smart contract, L1, liquidity and oracle risks; list is not exhaustive.

20. Support Guide  
    https://hyperliquid.gitbook.io/hyperliquid-docs/support  
    Key points: no official Hyperliquid app in app stores; official X accounts listed as `@HyperliquidX` and `@HyperFND`; never share seed/private key.

## Hyperliquid GitHub

21. Python SDK  
    https://github.com/hyperliquid-dex/hyperliquid-python-sdk  
    Observed `pyproject.toml` version at check time: 0.24.0. Pin an exact commit in implementation.

22. Bridge2 Contract  
    https://github.com/hyperliquid-dex/contracts/blob/master/Bridge2.sol  
    Key points: Permit deposit implementation; validator withdrawal/finalization; contract code must be pinned and runtime-verified.

## Android

23. Hardware-backed Keystore  
    https://source.android.com/docs/security/features/keystore  
    Key point: Android Keystore/KeyMint supports hardware-backed access-controlled keys, but product design must not assume native secp256k1 support.

24. KeyGenParameterSpec.Builder  
    https://developer.android.com/reference/android/security/keystore/KeyGenParameterSpec.Builder

25. Biometric Authentication  
    https://developer.android.com/identity/sign-in/biometric-auth  
    Key point: auth-per-use keys are appropriate for high-value actions.

26. Play Integrity  
    https://developer.android.com/google/play/integrity  
    Key point: use `requestHash` and environment signals as additional evidence, not as the sole authorization boundary.

## Japan Financial Services Agency

27. Crypto Assets and Electronic Payment Instruments  
    https://www.fsa.go.jp/policy/virtual_currency02/index.html  
    Key point: registration frameworks, including the electronic payment instrument/crypto-asset service intermediary regime effective 2026-06-01.

28. Crypto-asset business transitional notice  
    https://www.fsa.go.jp/news/r1/virtualcurrency/20200403-2.html  
    Key point: crypto-asset derivatives businesses require Financial Instruments Business registration under the described regime.

29. Service intermediary information  
    https://www.fsa.go.jp/common/shinsei/denanchuukai/index.html  
    Key point: intermediary framework assumes commission from a registered affiliated provider and limited mediation activities.

30. FATF virtual assets update  
    https://www.fsa.go.jp/inter/fatf/20260716/20260716.html  
    Key point: current attention to Travel Rule, fraud, stablecoins, unhosted wallets, P2P and DeFi risks.

## Official social-account check

The Hyperliquid official support page explicitly lists X accounts and Telegram. It did not establish an official Instagram account at the check date. Do not infer one from lookalike profiles. Review the official X accounts’ prior seven days before each release or incident response; if X cannot be retrieved, rely on Docs, GitHub and official announcements and mark social review incomplete.

## Source use rules

- Prefer primary sources.
- Record retrieval time.
- Pin Git commit/contract bytecode when used by code.
- Treat examples and time/fee estimates as volatile.
- If official sources conflict, stop the affected feature and obtain clarification.
- Never use a social post alone to change a signing format or contract allowlist.

## Additional Android／Distribution／Node sources

31. Android `ConfirmationPrompt` API  
    https://developer.android.com/reference/android/security/ConfirmationPrompt  
    Key points: runtime `isSupported`; prompt may be unavailable even on supported devices; Relying Party must validate the attested key, returned `promptText` and challenge; `promptText` is the user-approved content.

32. Google Play Financial features declaration  
    https://support.google.com/googleplay/android-developer/answer/13849271  
    Key points: categories include mobile payments/digital wallets, money transfer, cryptocurrency wallet, cryptocurrency exchange, and financial advice.

33. Google Play blockchain-based content／cryptocurrency policy  
    https://support.google.com/googleplay/android-developer/answer/17190352  
    Key points: crypto exchange/wallet activity should use certified services in regulated jurisdictions; regional rules apply; Google may request licensing/compliance documents.

34. Hyperliquid nodes／API servers  
    https://hyperliquid.gitbook.io/hyperliquid-docs/validators/running-a-validator  
    https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/api-servers  
    https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/nodes/foundation-non-validating-node  
    Key points: permissionless non-validating nodes; API servers derive state from nodes; a best-effort Foundation node is not a sole authoritative source for trading.

35. Hyperliquid Testnet faucet  
    https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/testnet-faucet  
    Key point at check time: the same address must have deposited on Mainnet before claiming mock Testnet USDC.

36. Hyperliquid bug bounty  
    https://hyperliquid.gitbook.io/hyperliquid-docs/bug-bounty-program  
    Key point: prohibited testing includes Mainnet; use Testnet or local forks.

## Git blob observations

The following are Git object/blob observations from the repository at the check time, not repository commit pins:

- SDK `pyproject.toml`: `30656a819ba812d5df37759f637202a8db80ba2b`
- SDK `exchange.py`: `41a2f66b568451208770517d5afd58af724edded`
- SDK `signing.py`: `560414711218560a8aa48b6adee311361a3a4029`
- `Bridge2.sol`: `2f2e98e3be5e6eccc3a24e5a8317105e220e7ccb`

Implementation must pin an actual repository commit and deployed contract bytecode; a blob hash alone is not a release pin.

## Apple／iOS／App Store

37. App Review Guidelines  
    https://developer.apple.com/app-store/review/guidelines/  
    Key points at check time: last updated 2026-06-08; crypto wallets must be offered by organization developers; crypto exchange functionality requires appropriate licensing/permissions in offered regions; cryptocurrency futures and similar products have stricter provider requirements; app completeness and accurate review disclosure are required.

38. Secure Enclave P-256 Signing  
    https://developer.apple.com/documentation/cryptokit/secureenclave/p256/signing  
    Key point: Secure Enclave CryptoKit signing uses NIST P-256. Do not treat it as Hyperliquid/Ethereum secp256k1 root signing.

39. Secure Enclave  
    https://developer.apple.com/documentation/cryptokit/secureenclave  
    Key points: hardware-based key manager; check availability; supported cryptographic operations must be verified against current docs.

40. Establishing your app's integrity／App Attest  
    https://developer.apple.com/documentation/devicecheck/establishing-your-app-s-integrity  
    Key points: check `isSupported`; keys survive updates but not reinstall, migration, or restore; App Attest validates app instances, not transaction semantics.

41. App Attest `isSupported`  
    https://developer.apple.com/documentation/devicecheck/dcappattestservice/issupported  
    Key point: not all device types support App Attest.

42. DeviceCheck overview  
    https://developer.apple.com/documentation/devicecheck  
    Key point: no single anti-fraud policy eliminates all fraud; App Attest is one risk input.

43. Keychain accessibility  
    https://developer.apple.com/documentation/security/ksecattraccessible  
    Key point: choose the most restrictive accessibility; `ThisDeviceOnly` items are non-synchronizable.

44. Screen capture state  
    https://developer.apple.com/documentation/uikit/uiscreen/iscaptured  
    Key point: capture/mirroring can be observed; deprecated API points to scene capture state. This is not a universal screenshot-prevention guarantee.

45. Human Interface Guidelines — Accessibility  
    https://developer.apple.com/design/human-interface-guidelines/accessibility/  
    Key points: support text enlargement ideally to 200%; iOS default 17 pt, minimum 11 pt for custom type guidance; audit with Accessibility Inspector.

46. Ad Hoc provisioning  
    https://developer.apple.com/help/account/provisioning-profiles/create-an-ad-hoc-provisioning-profile  
    Key point: Ad Hoc distribution uses registered devices and a distribution profile; it is not public distribution.

47. App Store provisioning  
    https://developer.apple.com/help/account/provisioning-profiles/create-an-app-store-provisioning-profile  
    Key point: public distribution requires App Store Connect provisioning and Apple review workflow.

## Cross-platform source rule

Android and iOS security features must never be represented as equivalent merely because both return a boolean or signature. Each platform must publish its capability evidence, assurance label, unsupported fallback, device matrix, and release gate separately.

## 2026-07-29.1追加確認

48. OpenAI App Developer Terms  
    https://openai.com/policies/developer-apps-terms/  
    Checked 2026-07-29. Section 1.6(h) prohibits an App, API, or App Response from initiating, executing, or otherwise facilitating money transfers, cryptocurrency transfers, or other financial or investment transactions through OpenAI Services. This package therefore limits ChatGPT/App/MCP integration to redacted read-only status, a fixed glossary, fixed non-transactional error explanations, generic safety guidance, and a neutral non-executable handoff. Transaction-specific drafts or manual steps are not exposed.

49. OpenAI Usage Policies  
    https://openai.com/policies/usage-policies/  
    Checked 2026-07-29. High-stakes decisions in financial activities may not be automated without human review. The wallet keeps AI at draft generation and uses deterministic policy plus explicit/scoped authorization.

50. JPYC official GitHub organization  
    https://github.com/jpycoin  
    Checked 2026-07-29. The current funds-transfer-business JPYC is described as an electronic payment instrument, issued/redeemed via JPYC EX, with official contracts listed for Ethereum, Avalanche C-Chain, and Polygon. It is distinct from the old prepaid JPYC.

51. JPYC EX integration API announcement  
    https://prtimes.jp/main/html/rd/p/000000324.000054018.html  
    Published 2026-07-13. The integration covers login/account linkage, navigation to issuance/redemption procedures, wallet-address registration assistance, and status linkage. Final review, additional authentication, acceptance, and confirmation remain with JPYC.

52. Hyperliquid official Python SDK — user state  
    https://github.com/hyperliquid-dex/hyperliquid-python-sdk/blob/master/hyperliquid/info.py  
    Checked 2026-07-29. The `clearinghouseState` response documentation includes per-position `liquidationPx`; `metaAndAssetCtxs` includes `markPx`. Production implementation must pin a commit and test current protocol responses rather than depend on a moving branch.
