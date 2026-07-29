# Claim-to-Source Matrix

| Design claim | Primary source(s) | Product consequence |
|---|---|---|
| ChatGPT App cannot execute crypto/financial transactions | OpenAI App Developer Terms | ChatGPT write prohibited |
| High-stakes financial decisions require human review | OpenAI Usage Policies | concrete user action required |
| API wallet signs for account but query uses actual account | Hyperliquid Nonces/API Wallets | separate signer/account IDs |
| Agent nonce is signer-scoped and address reuse is risky | Hyperliquid Nonces/API Wallets | nonce coordinator; burn replaced address |
| approveAgent lacks fine-grained app scope | Exchange endpoint/action shape | never call agent `trade-only` protocol permission |
| order and user-signed actions differ | Signing docs/official SDK | separate typed builders/signers |
| subaccounts are not available to all | Sub-accounts docs | fallback single-account policy |
| account modes alter balance semantics | Account Abstraction Modes | mode-aware compiler |
| Portfolio Margin is pre-alpha | Portfolio Margin docs | off by default/small test |
| HyperCore multi-sig does not equivalently secure HyperEVM | Multi-sig docs | do not use as universal root security |
| Bridge minimum/flow exists and may change | Bridge2 docs/contract | runtime validation |
| HLP has lock period | Protocol Vault docs | exact lock warning |
| app stores have no official Hyperliquid app | Support Guide | unofficial branding |
| Android Keystore is hardware-backed but not a secp256k1 assumption | Android Keystore docs | P-256 auth/AES wrapping or audited threshold |
| Japan registration issues exist for derivatives and mediation | FSA | written legal gate |

| BiometricPrompt is not equivalent to transaction Trusted Display | Android ConfirmationPrompt design/API | R4／non-exempt R3 needs protected/external display; R3 standing exception is pre-authorized and capped |
| Only confirmation prompt text represents user-approved content | Android ConfirmationPrompt API | canonical critical fields and server string comparison |
| Protected Confirmation can be unsupported/unavailable | Android ConfirmationPrompt API | runtime capability and NO_GO fallback |
| A single best-effort node should not be sole authoritative trading source | Hyperliquid Foundation non-validating node docs | independent state evidence |
| Testnet faucet has a same-address Mainnet-deposit prerequisite | Hyperliquid Testnet faucet | test onboarding evidence |
| Mainnet security testing is prohibited by program rules | Hyperliquid bug bounty | testnet/fork only; controlled functional canary |
| Play requires financial-feature declaration | Google Play Help | distribution release gate |
| Play crypto apps face regulated-jurisdiction and documentation requirements | Google Play policy | geo/legal/store evidence |
| iOS Secure Enclave CryptoKit signing is P-256 | Apple SecureEnclave.P256.Signing | use as Authorization Key, not Hyperliquid root secp256k1 |
| App Attest isn't available on every device | Apple `DCAppAttestService.isSupported` | capability negotiation and fail-closed policy |
| App Attest keys don't survive reinstall/migration/restore | Apple App Attest integrity guide | re-enrollment and old-device revocation |
| App Attest validates app instance, not human-reviewed transaction meaning | Apple DeviceCheck/App Attest scope | `trustedDisplayClaim=false` |
| iOS wallet App Store submission requires organization developer | Apple App Review 3.1.5(i) | public iOS gate requires organization enrollment |
| Crypto exchange apps need region-appropriate license/permissions | Apple App Review 3.1.5(iii) | legal/region/store evidence |
| Crypto futures apps face stricter provider requirements | Apple App Review 3.1.5(iv) | public Perp App Store default NO_GO |
| iOS text should support large sizes and accessibility audits | Apple HIG Accessibility | Dynamic Type 200%, VoiceOver, no critical clipping |
| Ad Hoc distribution is for registered devices | Apple provisioning help | personal/closed testing separated from public App Store |
| iOS screen capture can be detected but not treated as a universal prevention guarantee | Apple UIScreen capture docs | background/capture mitigations are best-effort |
