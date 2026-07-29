# Codex Remaining Work — Canonical Master Prompt

**Package release:** 2026-07-29.2  
**Canonical path:** `codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md`  
**Language for user-visible copy:** やさしい日本語  
**Initial release decision:** native build / Testnet write / Mainnet / public stores are all `NO_GO`

---

## 0. Your role and non-negotiable truthfulness

You are the implementation lead for a high-risk, self-custody-oriented wallet client that may eventually interact with Hyperliquid, Arbitrum, HyperEVM, JPYC EX handoff screens, and a verified fee-payment route. Work in the extracted repository that contains this prompt.

Do **not** interpret this package as a production application. It is a specification, contracts, deterministic examples, an offline browser prototype, validation tooling, and a handoff plan. You must build the missing native applications and services, produce evidence, and keep every write gate closed until its explicit exit criteria are satisfied.

Never state any of the following without corresponding artifact paths and reproducible evidence:

- production-ready
- 100% safe
- funds cannot be lost
- Mainnet-ready
- legally approved
- App Store or Google Play approved
- JPYC EX production integration complete
- zero-native-balance fee route verified
- independent security audit complete

A missing credential, contract, licensed entity, provider agreement, hardware facility, legal opinion, or store decision is not a coding failure. Record it in `delivery/EXTERNAL_BLOCKERS.md`, leave the affected gate `NO_GO`, and give exact human steps for obtaining and validating it. Do not invent a substitute.

---

## 1. Start with a forensic baseline

Before editing any source:

1. Run, from a clean extract:

   ```bash
   python -m pip install -r tools/requirements.txt
   python -m pip install -r tools/requirements-visual.txt
   python tools/run_full_validation.py
   ```

2. Record:
   - repository tree hash;
   - `manifest.json` hash;
   - `SHA256SUMS.txt` hash;
   - Python, Playwright, Chromium, OS, architecture;
   - every command, exit code, stdout/stderr;
   - dirty working tree status.

3. Create `delivery/BASELINE_EVIDENCE.json` and `delivery/BASELINE_REPORT.md`.

4. Do not “fix” a failing baseline by deleting assertions, weakening limits, altering expected evidence, or regenerating screenshots without explaining the cause. A validator is part of the attack surface. Every change to a validator requires a regression case that would fail under the old loophole.

5. Enforce **no validation bypass**: release creation must always run the full validation pipeline, freeze the source-tree digest, build twice from the same immutable tree, require byte-for-byte equality, verify a clean extraction, and prove the source tree was not changed by validation or packaging. Do not add a skip flag, environment-variable escape hatch, permissive fallback, or “trusted CI” shortcut.

6. Treat `codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md` as the only source of functional and safety requirements. Use `codex/CODEX_EXTERNAL_OPERATIONALIZATION_PROMPT_2026-07-29.md` only as the non-overriding execution contract for credentials, physical devices, HSM/MPC, Testnet, legal/store work, independent audits, and evidence capture. Root files `17_CODEX_IMPLEMENTATION_MASTER_PROMPT.md` and `34_CODEX_REMAINING_WORK_MASTER_PROMPT.md` are pointers, not independent copies.

---

## 2. Required repository structure

Implement a maintainable monorepo. A concrete acceptable layout is:

```text
apps/
  android/                 Kotlin, Jetpack Compose
  ios/                     Swift, SwiftUI
services/
  control-api/
  reconciler/
  nontransactional-support-gateway/
  registry-service/
  fee-route-service/
  signer-interface/
crates/                    or shared/
  domain/
  canonicalization/
  policy-engine/
  intent-compiler/
  state-machine/
  test-vectors/
adapters/
  hyperliquid/
  arbitrum/
  hyperevm/
  jpyc-ex-handoff/
  fee-route/
infra/
  local/
  staging/
  observability/
security/
  threat-tests/
  key-ceremony/
delivery/
  evidence/
  reports/
```

Equivalent structures are acceptable only when module boundaries, ownership, build commands, and evidence paths remain explicit.

---

## 3. Shared deterministic core

Build one shared deterministic domain core used by Android, iOS, backend compilation, and test fixtures. Rust with stable FFI is preferred; another language is acceptable only with byte-for-byte cross-platform vectors.

### 3.1 Core responsibilities

- strict JSON parsing with duplicate-key rejection;
- NFC normalization rules;
- decimal-string arithmetic with no binary floating-point for money;
- canonical serialization and domain-separated hashes;
- `ActionPlanDraft` validation;
- live-state compilation into `ExecutionCapsule`;
- policy evaluation;
- authorization scope evaluation;
- state machine and Saga transitions;
- idempotency and replay protection;
- quote/registry expiry;
- address/network/asset identity binding;
- partial-success reconciliation;
- user-visible Japanese status codes, while preserving machine reason codes.

### 3.2 Mandatory cross-language vectors

Generate and check the same bytes and hashes in:

- shared core;
- Kotlin;
- Swift;
- backend runtime.

Include positive and negative vectors for:

- duplicate keys;
- non-NFC strings;
- exponent notation;
- integer overflow;
- decimal scale mismatch;
- negative zero;
- Unicode confusables in aliases;
- altered address/network/amount after authorization;
- expired state/quote/registry;
- nonce reuse;
- partially completed Saga.

Do not proceed to Testnet writes until all implementations are byte-for-byte consistent.

---

## 4. Natural-language boundary

The AI component is an untrusted parser and explainer. It never becomes the policy authority, signer, broadcaster, price source, address source, or feature-gate administrator.

### 4.1 Standalone-wallet transaction-intent component may do

- convert utterance into an untrusted draft;
- identify ambiguity;
- provide plain-Japanese explanations;
- summarize read-only balances and reconciled states;
- select a pre-authored, versioned, signed manual-fallback catalog entry for rendering inside the standalone wallet only; it must not freely generate transaction-specific instructions.


The transaction-intent component must use deterministic local parsing first. Any fallback component must be independently operated and non-OpenAI. Do not send transaction intent, recipient, amount, asset/network selection, authorization material, transaction payload, signing material, or transaction-specific recovery context to an OpenAI Service. Keep any optional OpenAI-backed support gateway in a separate non-transactional service, credential, schema, and network segment.

### 4.2 Transaction-intent component must never do

- hold or receive a private key, seed phrase, MPC share, signing handle, or raw credential;
- create a new destination address from free text;
- decide that a similar asset is “close enough”;
- modify a compiled capsule;
- sign, broadcast, call the execution endpoint, or expose an executable deep link;
- return a transaction payload, signer request, WalletConnect request, or approval calldata through ChatGPT;
- enable a feature gate;
- silently choose another route after failure;
- invent a stop-loss, leverage, amount, recipient, network, fee cap, or liquidation value.

### 4.3 Voice normalization hard gate

Preserve both:

- `sourceUtterance`: exact recognized text;
- `normalizedInterpretation`: proposed meaning.

Material ambiguity includes at least amount, asset, direction, leverage, recipient, network, “all”, liquidation/production-price confusion, and unknown alias. A material ambiguity blocks execution until the user explicitly confirms or corrects it.

Required regression:

```text
BTCを500 USDC、ペイパチャルで3倍。生産価格も見せて。
```

The UI may propose:

- ペイパチャル → 先物取引（期限なし）
- 生産価格 → 清算価格

It must retain the original words and keep the primary action disabled until explicit confirmation. Do not add a stop-loss.

---

## 5. ChatGPT integration boundary

Implement any ChatGPT-facing App, MCP server, or Action as **read-only and explanatory only**. Treat this as an architectural invariant, not a wording preference. The machine-readable boundary is `contracts/chatgpt-readonly-openapi.yaml`; it is separate from the first-party control contract in `contracts/openapi.yaml`. The ChatGPT surface must expose exactly the allowlisted read-only operations in that contract and no hidden, undocumented, dynamically discovered, or proxy write capability.

Do not send transaction intent, recipient, amount, asset/network selection, authorization material, transaction payload, or signing material to an OpenAI Service for compilation or execution. A transaction-capable independent wallet may use a deterministic local parser or an independently operated non-OpenAI component, but the OpenAI-facing feature must remain disabled for transaction-intent compilation. A neutral, non-executable handoff may only tell the user to open the independent wallet; it must not pre-populate, encode, deep-link, queue, or otherwise facilitate a write.

Allowed outputs are limited to the exact fixed-catalog support surface:

- a redacted reconciled status for an opaque reference created previously inside the standalone wallet, without recipient, amount, asset quantity, network route, quote, or order details;
- a fixed plain-Japanese glossary entry;
- a fixed non-transactional error explanation;
- generic safety guidance selected only by an allowlisted topic ID;
- one fixed neutral handoff telling the user to open the independent wallet app, without screen location, prefill data, operation reference, deep link, token, or step sequence.

Prohibited outputs:

- transaction or order payloads;
- signatures or signing challenges;
- executable URLs or deep links that pre-populate a write;
- write-capable tools;
- direct invocation of `/execute`, `/authorize`, `/resume`, emergency writes, or signer endpoints;
- transaction-specific button names, screen sequences, recovery steps, copyable values, drafts, quotes, or instructions whose practical effect is initiating or facilitating the financial write inside ChatGPT;
- any indirect mechanism whose practical effect is initiating or facilitating the financial write inside ChatGPT.

Required ChatGPT/OpenAI boundary tests:

- the published operation ID set is exactly `getReadOnlyStatus`, `getPlainJapaneseTerm`, `explainNonTransactionalError`, and `getGenericSafetyHelp`;
- request validation rejects transaction utterances, recipient/address, amount, asset/network selection, order, approval, quote, payload, signature, step list, button list, executable URL, deep link, QR content, handoff token, and arbitrary additional properties in body, query, path, header, metadata, and tool context;
- responses cannot contain transaction-specific values, screen/button sequences, draft plans, payloads, or executable links, including inside free-text fields;
- the neutral handoff is a fixed catalog string and opens no transaction-specific route;
- the OpenAI-facing service has no network route, credential, service identity, queue producer, database permission, or proxy path to transaction intent, Address Book, quote, Compiler, Policy write, Control API write, Signer, or broadcast;
- source, binary, API gateway, service mesh, IAM, egress, logs, traces, analytics, and support consoles are tested for accidental transaction-context leakage;
- transaction-specific manual fallback remains available only inside the standalone wallet and is unreachable from the ChatGPT/OpenAI contract;
- every negative case fails closed and is bound to the released server/config/policy digests.

Add contract and integration negative tests that enumerate every tool, route, schema, OAuth scope, callback, redirect, deep link, plugin resource, and proxy path and prove no write-capable schema or endpoint is reachable. Verify the exact operation allowlist, exact request-property allowlists, `.read`-only scopes, `writeAvailableHere=false`, and `executable=false`. Treat any drift as a release-blocking failure.

---

## 6. Signed asset registry

Implement `schemas/asset-registry.schema.json` as a signed asset registry snapshot service.

### 6.1 Production requirements

- Two independent official-source observations where feasible.
- Content hashes and retrieval timestamps.
- Network ID in CAIP-2 form.
- chain ID, native fee asset, token address, decimals, code hash where obtainable.
- signer key ID, signature, validity interval.
- two-person approval for production publication.
- append-only audit record of additions, removals, conflicts, and emergency revocation.
- client pinning to registry ID and entry hash inside every compiled operation.
- fail closed when missing, stale, conflicting, revoked, or unsigned.
- reads may display “information unavailable”; writes must not guess.

### 6.2 JPYC-specific rule

Never copy a production JPYC contract address from the simulation example. The example intentionally uses a dummy address and `productionEligible=false`.

A production registry entry must be created only after legal/operations staff confirm:

- intended JPYC product/version;
- intended network;
- official contract source;
- decimals and bytecode/code hash;
- issuer warnings about fake tokens;
- validity and revocation process.

Record the exact evidence in `delivery/evidence/asset-registry/`.

---

## 7. JPYC EX handoff

Implement JPYC issuance/redemption as a controlled handoff, not as a fabricated public API.

### 7.1 Required behavior

- The wallet may prepare amount, destination network, and receiving address.
- Before handoff, show full address, fingerprint, network, amount, and expiry.
- The user completes identity verification, additional authentication, bank/payment steps, and final application on JPYC EX or an officially contracted partner flow.
- The wallet must not claim to approve, bypass, or perform those steps.
- On return, independently reconcile on-chain receipt and application state where supported.
- Expired or changed destination data invalidates the handoff.
- Never log identity documents, bank secrets, or full KYC payloads.

### 7.2 External blocker handling

When production partner credentials or an integration agreement are absent:

- implement a fake adapter and a contract test;
- keep production handoff disabled;
- document the partner onboarding contact, required documents, callback URLs, key exchange, sandbox access, certification, and go-live checklist in `delivery/EXTERNAL_BLOCKERS.md`;
- do not reverse-engineer or automate a consumer-only flow.

---

## 8. Fee readiness and zero-native-balance paradox

Implement `asset-registry`, `fee-route-capability`, `fee-readiness-plan`, and `manual-fallback` as separate trust objects.

A token balance does not prove that the account can initiate the transaction needed to exchange that token for native gas. The compiler must first identify the account execution model.

### 8.1 Required account models

- EOA;
- ERC-4337 smart account;
- protocol-native sponsored operation;
- relayer-mediated operation.

### 8.2 A zero-native-balance path is eligible only when all are true

- `supportsZeroNativeBalance=true` for the exact account model;
- provider identity, terms, support route, jurisdiction, and settlement target are present;
- capability evidence is `VERIFIED`, unexpired, not revoked, and independently reviewed for production;
- network, token, account, operation, amount, nonce, expiry, fee estimate, JPYC cap, and settlement target are bound to a signed quote;
- any required permit/allowance can itself be created without native gas, or already exists within a bounded policy;
- failure charging behavior is disclosed and capped;
- route abuse/rate limits and provider liquidity are checked;
- no silent provider or route fallback occurs;
- the user sees expected cost, maximum cost, failure cost, provider, settlement target, quote ID, and expiry before authorization.

### 8.3 Fail-closed outcomes

- Native balance sufficient: do nothing.
- Native balance low but a normal transaction is possible: quote only the minimum operation-bound swap plus bounded reserve.
- Native balance zero and verified route exists: use only that bound route.
- Capability missing/stale/conflicting: manual fallback.
- Live operation-bound recommended top-up unavailable: show no fixed amount and do not advise sending a guessed quantity.

Add tests for allowance bootstrap, permit replay, quote substitution, provider revocation, expired quote, chain mismatch, failed action charging, duplicate reimbursement, and forced silent fallback.

---

## 9. Hyperliquid adapter

Use official protocol documentation and live read-only queries as the primary behavior reference. A community SDK may be a transport convenience, never the sole source of truth for signing or semantics.

### 9.1 Capabilities

Implement and separately gate:

- account/read-only state;
- spot orders;
- perpetual/期限なし先物 orders;
- internal transfers where supported;
- Arbitrum deposits and withdrawals;
- HLP/運用口座 deposits and withdrawals;
- cancel-all and emergency write-disable;
- order/fill/status reconciliation.

### 9.2 Perpetual safeguards

The confirmation screen must show, when reliably available:

- buy/sell direction;
- margin amount;
- notional;
- leverage;
- margin mode;
- current reference price and age;
- estimated liquidation price and distance;
- fee estimate;
- price-deviation/slippage cap;
- stop-loss status, including explicitly “not set”.

Liquidation price is not a guarantee. Re-fetch immediately before authorization and again after fill. Stop when it is missing, stale, non-finite, inconsistent with account state, or based on a different margin mode. Do not locally invent a definitive liquidation price when the authoritative account state is unavailable.

### 9.3 Testnet evidence

Before any Mainnet consideration, produce evidence for:

- place, cancel, replace;
- partial fill;
- rejected order;
- stale nonce;
- connection interruption;
- delayed status;
- duplicate client request;
- reconciliation after restart;
- cross/isolated margin if supported;
- liquidation field presence/absence;
- fee and fill arithmetic;
- emergency cancel independent of AI.

Store request IDs and redacted receipts. Do not store signing secrets.

---

## 10. Execution, signer, and custody architecture

Keep these components separate:

1. untrusted AI draft;
2. deterministic compiler;
3. policy engine;
4. native review UI;
5. authorization envelope;
6. signer interface;
7. broadcaster/adapter;
8. reconciler.

### 10.1 Signer invariants

- Sign only a recognized operation type and an authorized capsule hash.
- Require operation-bound, sender-constrained authorization for every first-party write API call. Use DPoP or an equivalently reviewed proof-of-possession mechanism, rotate and revoke tokens, bind device/session/account/capsule/idempotency/challenge/evidence/receipt hashes, enforce narrow clock-skew and replay windows, and use PKCE or an equivalently safe pairing flow where OAuth-style authorization is involved. A bearer token by itself must never authorize a financial write.
- Recompute all critical fields server-side or inside the signer boundary.
- Load and verify the exact signed network/asset registry; compare CAIP-2, numeric/RPC chain ID, market/asset ID, contract, proxy implementation, code hash and decimals.
- Load the exact canonical quote document; recompute its digest and final order/transaction commitment instead of trusting a non-zero `quoteHash` field.
- Reject unknown contract calls by default.
- Enforce nonce, expiry, per-operation, daily, monthly, asset, network, recipient, leverage, and fee limits.
- Make key access independent of the AI process.
- Redact payloads in logs.
- Support immediate revocation and global write-disable.
- Root/recovery operations require step-up and a separate policy.

### 10.2 iOS

Do not claim that a Secure Enclave P-256 key directly signs secp256k1/Ethereum/Hyperliquid root operations. Use Secure Enclave for device authorization, local share encryption/access control, and attestable app/device signals. Implement secp256k1 with an independently reviewed custody design such as an external wallet or audited threshold-signing system. App Attest proves app integrity signals, not that the user saw the correct amount or destination.

### 10.3 Android

Use Android Keystore and biometric authorization appropriately. Protected Confirmation is conditional by device/API/hardware support and is not universally available. Detect capability at runtime; never label an unsupported software prompt as hardware-protected confirmation.

### 10.4 Managed self-custody

Do not implement an improvised MPC or threshold ECDSA protocol. Use a reviewed implementation/provider, complete a key ceremony, backup/recovery design, share-loss drill, compromise drill, and independent cryptographic audit before enabling managed custody.

---

## 11. Limited standing authorization

“Approve once” means a bounded standing authorization, never an unlimited token approval or unrestricted signer session.

Bind at least:

- policy ID/version;
- account/device;
- issue and expiry time;
- active-session maximum;
- inactivity timeout;
- permitted operation types;
- assets;
- networks;
- exact saved recipients and address fingerprints;
- per-operation/day/month limits;
- leverage cap;
- fee-preparation monthly cap;
- price-deviation cap;
- quote age;
- revocation counter.

Always require fresh step-up for:

- new or changed recipient;
- new network;
- all-balance action;
- high-value action;
- recovery or key change;
- policy/permission change;
- suspicious session/device;
- stale or sharply changed price/fee;
- missing liquidation data;
- scope expansion.

Make revoke/stop available from every main screen and from an out-of-band server path.

---

## 12. Native Android implementation

Implement Kotlin + Jetpack Compose with:

- offline-first read model;
- tapjacking/overlay resistance on critical confirmation and recovery screens, with explicit tests for obscured-touch and malicious accessibility-service scenarios;
- root/instrumentation/debugger risk handling that never silently weakens policy and that fails closed for protected write paths according to the approved threat model;
- biometric-enrollment-change, device-migration, backup/restore, clipboard, screenshot, notification-preview, and task-switcher leakage tests;
- strict navigation and state restoration;
- no secret in logs, clipboard, screenshots, backups, analytics, crash reports, or accessibility labels;
- secure screen policy for secret/recovery views;
- TalkBack labels and focus order;
- font scaling and Japanese line wrapping;
- 48dp minimum logical targets;
- IME-safe composer;
- screenshot/golden tests for all critical screens;
- process death and rotation tests;
- network-loss and stale-state banners;
- runtime capability labels for Keystore/biometric/Protected Confirmation;
- clear distinction between “request accepted”, “network confirmed”, and “destination arrived”.

Do not reproduce the browser prototype mechanically. Use its information hierarchy and safety invariants, then validate native rendering on physical devices.

---

## 13. Native iOS implementation

Implement Swift + SwiftUI with:

- strict state model shared with the deterministic core;
- overlay/screen-capture/accessibility-abuse resistance appropriate to iOS, with critical-flow tests and a documented residual-risk decision where the platform cannot provide a hard block;
- jailbreak/instrumentation/debugger risk handling that never silently weakens policy and that fails closed for protected write paths according to the approved threat model;
- biometric-enrollment-change, device-migration, iCloud/device-backup restore, pasteboard, screenshot/recording, notification-preview, and app-switcher leakage tests;
- Keychain access classes appropriate to the threat model;
- Secure Enclave P-256 authorization key where supported;
- App Attest as an integrity signal with fallback and revocation behavior;
- VoiceOver labels, rotor order, and focus restoration;
- Dynamic Type including accessibility sizes;
- 44pt minimum logical targets;
- safe-area/keyboard handling;
- screen-capture protections for secret/recovery views where platform behavior permits;
- localizable Japanese source strings with no concatenated grammar;
- process termination and state restoration tests;
- physical-device screenshots for small, baseline, and current Face ID devices.

Do not call App Attest or Face ID a trusted display. The review receipt must bind the exact rendered critical data through the application protocol, and the signer must still validate the semantic capsule.

---

## 14. UI and accessibility acceptance

Preserve the user’s original request at all text sizes. Critical screens must display:

- exact source utterance;
- interpreted meaning;
- full amount, asset, direction, network, recipient;
- full address plus short fingerprint;
- all caps and expiry;
- “screen example” markers for non-live data;
- data age;
- clear final-review boundary;
- explicit stop/revoke control.

### 14.1 Browser prototype

Keep all 288 logical proxy cases passing:

```text
6 viewports × 12 flows × 2 text modes × 2 themes = 288
```

### 14.2 Native matrix

Add at minimum:

- Pixel 9a physical device;
- compact Android physical device;
- iPhone 12 physical device;
- small supported iPhone;
- current Face ID iPhone;
- default and largest supported text sizes;
- light/dark/high-contrast settings;
- Japanese VoiceOver/TalkBack;
- keyboard/IME open and closed;
- slow network/offline/stale state;
- screen reader focus after error and modal dismissal.

A CSS pixel is not a physical millimetre. Do not claim “1 mm exact”. Record point/dp geometry, OS scale, screenshot dimensions, and diff tolerances.

---

## 15. Manual fallback generator

Generate manual guidance only inside the standalone wallet from deterministic structured data and a versioned signed catalog, not free-form AI memory. Never expose transaction-specific manual guidance through ChatGPT, an OpenAI-facing App, MCP, Action, or support endpoint.

Every guide must include:

- current stop reason;
- current app/screen;
- exact button/control label;
- source network and destination network;
- asset;
- full receive address and fingerprint;
- operation-bound recommended amount or a clear “not available” state;
- estimate generation and expiry time;
- source platform minimum withdrawal and fee caveat;
- expected result;
- how to return and refresh;
- idempotency warning;
- support code.

Never hardcode a POL amount. If the operation-bound amount cannot be obtained, instruct the user not to send yet and show how to refresh or contact support.

---

## 16. Reconciliation and partial success

Implement a durable Saga. Each step has:

- deterministic step ID;
- precondition hash;
- authorization scope;
- idempotency key;
- submitted/accepted/finalized/failed/unknown state;
- external reference;
- reconciliation checkpoints;
- compensating or safe-stop rule.

On restart or ambiguous response, query authoritative state before retrying. Never repeat a completed sale, deposit, transfer, approval, or withdrawal merely because the client timed out.

The UI must distinguish:

- completed;
- in progress;
- accepted but not finalized;
- not started;
- failed;
- unknown/reconciliation required;
- asset currently located at X.

---

## 17. Admin and SRE controls

Build a separate, least-privilege administration plane. It must not expose raw keys or arbitrary signing.

Required controls:

- global write kill switch;
- per-user/account write disable;
- per-capability disable;
- provider/asset/network revocation;
- quote source disable;
- read-only fallback;
- reconciliation queue visibility;
- stuck Saga handling;
- signed registry publication;
- release-gate state;
- incident timeline;
- immutable audit export.

Sensitive changes require two-person approval, reason, ticket, scope, expiry, and rollback. “Emergency” bypasses must be narrower, logged, time-limited, and reviewed afterward.

Operational alerts include:

- duplicate execution attempts;
- authorization/hash mismatch;
- provider quote anomaly;
- registry conflict/staleness;
- unexpected fee increase;
- reconciliation lag;
- signer denial spike;
- withdrawal destination change;
- unusual scope expansion;
- AI-to-write boundary violation attempt.

---

## 18. Privacy and logging

Classify and minimize data. Never log:

- seed phrase;
- private key or MPC share;
- full signing payload where it leaks sensitive details;
- authentication token;
- KYC document;
- bank secret;
- full clipboard content;
- full address together with personal alias in broad analytics.

Use structured redaction. Security audit logs may use hashed/pseudonymous account IDs, short fingerprints, reason codes, capsule hashes, and external references. Define retention, deletion, access review, breach response, and data-subject handling with counsel.

---

## 19. Security testing

Implement automated negative tests and arrange independent review.

Minimum threat tests:

- prompt injection and indirect injection;
- malicious overlay/tapjacking and obscured-touch confirmation;
- accessibility-service or assistive-technology abuse without breaking legitimate accessibility;
- biometric enrollment change, device migration, backup restore, and session re-binding;
- alias poisoning;
- Unicode confusable recipient/asset;
- address-book replacement;
- stale price and stale account state;
- amount/decimal confusion;
- quote substitution/replay;
- registry rollback/conflict;
- malicious fee provider;
- partial-success duplicate execution;
- signer confused deputy;
- SSRF and callback spoofing;
- app attestation replay;
- rooted/jailbroken device risk handling;
- clipboard and screenshot leakage;
- log/analytics leakage;
- dependency compromise and lockfile drift;
- unsafe ZIP/path traversal;
- feature-gate escalation;
- admin-session compromise;
- recovery abuse.

Run SAST, dependency/license scan, secret scan, fuzzing of canonicalization/compiler/state machine, API authorization tests, mobile static/dynamic analysis, and penetration testing. Findings must have severity, owner, due date, fix commit, retest evidence, and accepted-risk approver.

---

## 20. Legal, regional, and store gates

Do not encode legal conclusions in code. Implement configurable regional gates and produce a counsel questionnaire/evidence bundle.

Before public release, obtain written decisions on:

- custody/self-custody characterization;
- exchange/broker/derivatives implications;
- marketing and risk disclosure;
- JPYC issuance/redemption handoff;
- sanctions/AML/KYC responsibilities;
- privacy and cross-border data;
- fee sponsorship/relaying/reimbursement;
- Apple submitting-entity and crypto/derivatives rules;
- Google Play financial features and crypto declaration;
- supported countries and geofencing;
- customer support and complaints.

Store approval and legal eligibility are independent from technical completion. Keep public distribution gates closed until written evidence exists.

---

## 21. Build, CI, supply chain, and reproducibility

Required CI stages:

1. formatting/lint;
2. unit tests;
3. strict JSON/Schema/OpenAPI validation;
4. canonical vectors across all languages;
5. loophole regression tests;
6. browser prototype 288-case test;
7. Android unit/UI/static analysis;
8. iOS unit/UI/static analysis on macOS runners;
9. backend integration tests;
10. fake-adapter end-to-end tests;
11. Testnet tests behind manual protected gate;
12. secret/dependency/license/SBOM scan;
13. signed artifact build and provenance;
14. clean-extract package verification.

Pin toolchains, lockfiles, base images, action versions, package-manager registries, and dependencies by immutable version/hash where supported. Generate both CycloneDX or SPDX **SBOM** artifacts and signed **SLSA** provenance for every releasable binary and archive. Verify dependency checksums/signatures and provenance, reject lockfile drift, scan build scripts and transitive dependencies, and test malicious-package and dependency-confusion scenarios. Sign release artifacts and verify signatures in a clean environment. Protect branches and release environments. Require code-owner review for signer, canonicalization, policy, registry, fee route, build/release tooling, validators, and gate changes.

The release orchestrator must preserve **no validation bypass**. It must run full validation on every release, compare source-tree digests before and after validation and packaging, build twice from the same tree, require byte-for-byte equality, and reject any mutation, stale generated evidence, altered archive metadata, untracked output inside the source tree, or unverified clean extraction.

Treat `config/source-pins.example.yaml` and `source-pins.json` as semantically identical representations of one source-pin set. Reject duplicate YAML keys and aliases. A source with no immutable content hash remains `MONITOR` and can never be used as production eligibility evidence; retrieved text, screenshots, URLs, or dates alone do not upgrade it.

---

## 22. Implementation phases and gate exits

### Phase A — deterministic local system

Deliver:

- shared core;
- API contracts;
- fake Hyperliquid/JPYC/fee adapters;
- Android/iOS shells;
- local Control API/Reconciler;
- complete unit/negative tests;
- no live credentials.

Exit only when deterministic vectors and fake end-to-end tests pass.

### Phase B — staging/read-only

Deliver:

- live read-only adapters;
- signed staging registry;
- observable reconciliation;
- no write capability exposed to ChatGPT;
- no Mainnet writes.

Exit only with source-pinning, stale-data, outage, and privacy evidence.

### Phase C — Testnet write

Deliver:

- protected manual Testnet gate;
- signer test keys isolated from production;
- Hyperliquid Testnet scenarios;
- operation-bound fee route sandbox where available;
- physical-device native evidence.

Exit only after security owner and engineering owner sign the evidence bundle.

### Phase D — personal small-value Mainnet candidate

Still `NO_GO` until:

- independent security audit closed;
- custody/signing review closed;
- production registry and source monitor operational;
- fee provider and JPYC partner evidence complete;
- legal written approval for a precisely defined region/user set;
- incident/recovery drills passed;
- hard asset and daily limits configured;
- two-person gate change recorded.

### Phase E — closed alpha and public stores

Treat closed alpha, Google Play, and iOS App Store as three independent gates. Each requires its own legal, operational, support, privacy, store, device, and monitoring evidence.

---

## 23. Required evidence bundle

Create `delivery/evidence/` with machine-readable indexes. Every claim must point to files.

Minimum outputs:

```text
delivery/
  BASELINE_EVIDENCE.json
  BASELINE_REPORT.md
  IMPLEMENTATION_STATUS.yaml
  EXTERNAL_BLOCKERS.md
  TEST_COMMANDS.jsonl
  GATE_DECISIONS.yaml
  evidence/
    core/
    android/
    ios/
    api/
    hyperliquid-testnet/
    asset-registry/
    fee-route/
    jpyc-ex/
    security/
    privacy/
    operations/
    legal-store/
  reports/
    FINAL_ENGINEERING_REPORT.md
    RESIDUAL_RISKS.md
    MANUAL_OPERATOR_STEPS.md
```

For each test or review record:

- timestamp;
- commit;
- environment;
- toolchain;
- exact command;
- exit code;
- artifact hashes;
- pass/fail;
- limitations;
- reviewer/approver where applicable.

Screenshots alone are not sufficient evidence for protocol semantics. Logs alone are not sufficient evidence for user-visible rendering. Both are required for critical flows.

---

## 24. Exact stop conditions

Stop and leave the gate closed when any of these occur:

- current official source cannot be verified;
- asset registry is stale, unsigned, conflicted, or revoked;
- fee route capability or quote is stale/unverified;
- destination/network/amount differs from authorized capsule;
- liquidation field is unavailable or inconsistent for a required display;
- signer cannot recompute and recognize the operation;
- reconciliation cannot determine whether a write occurred;
- native physical-device evidence is missing;
- external audit has unresolved critical/high findings;
- legal/store eligibility is unknown;
- provider or partner credential/agreement is absent;
- test coverage was reduced to make CI pass;
- a requested feature would violate the ChatGPT read-only boundary.

Do not replace a hard failure with a warning when funds or authority could be affected.

---

## 25. Human-action instructions for blockers

For every blocker that cannot be completed in the coding environment, write exact instructions containing:

1. responsible role;
2. service/portal/vendor to open;
3. account type needed;
4. exact menu/screen;
5. exact button or field labels where known;
6. documents/values to prepare;
7. callback/domain/network configuration;
8. how to verify the result;
9. where to store the credential or evidence;
10. which automated test to rerun;
11. which gate remains closed until completion.

Do not write “configure credentials” or “ask legal” without these details.

---

## 26. Definition of done for this Codex assignment

The assignment is complete only when all of the following are true:

- repository builds locally with documented commands;
- Android debug application runs with fake adapters;
- iOS simulator application runs with fake adapters;
- shared deterministic vectors pass across core/Kotlin/Swift/backend;
- fake end-to-end flows cover all 12 prototype flows and negative cases;
- browser prototype remains unchanged in safety semantics and all 288 cases pass;
- read-only live state works in staging where credentials are available;
- Testnet evidence is produced only where access exists;
- every unavailable external dependency is in `EXTERNAL_BLOCKERS.md` with exact operator steps;
- all Mainnet and public-store gates remain `NO_GO` unless every required independent artifact exists;
- `python3 -B tools/build_release.py /tmp/one-intent-hyperliquid-wallet-complete-reviewed-<new-version>.zip` passes deterministic double-build and clean-extract verification, using the exact root/version filename required by the new release metadata;
- a clean extract passes package validation;
- final reports accurately separate implemented, tested, simulated, externally blocked, and unverified items.

At the end, print a concise gate table. Never collapse `SIMULATED`, `IMPLEMENTED`, `TESTED`, `AUDITED`, `LEGAL_APPROVED`, and `PRODUCTION_ENABLED` into one status.

---

## 27. Final response format

Return:

1. commit/tree hash;
2. files changed and architecture summary;
3. commands run and results;
4. artifact paths;
5. Testnet/physical-device/external evidence actually obtained;
6. unresolved blockers with exact human steps;
7. residual risks;
8. gate table;
9. explicit statement that Mainnet remains disabled unless all required evidence is present.

Do not provide a confident narrative without evidence paths. Evidence first, claims second.

---

## 28. Operational completion is an evidence decision, not a narrative

The only two final operational statuses are:

```text
PRODUCTION_OPERATIONAL_GO
BLOCKED_NOT_OPERATIONAL
```

The repository currently **must** evaluate to `BLOCKED_NOT_OPERATIONAL`. Do not rename a design package, simulator, successful build, Testnet run, release candidate, closed alpha, or Store submission as operational.

Treat `config/operational-readiness.json` as the machine-readable source of truth. It currently contains exactly **37 mandatory gates and 93 required claims** for the profile `JAPAN_PUBLIC_CROSS_PLATFORM_MAINNET_V1`. You must implement, test, and evidence every claim. A single missing, duplicate, unknown, stale, revoked, conflicting, unsigned, incorrectly reviewed, or release-mismatched claim keeps the result `BLOCKED_NOT_OPERATIONAL`.

Use the following commands as hard acceptance contracts:

```bash
# Explicitly generates derived design-package evidence. This is the only package mutation stage.
python tools/prepare_release_artifacts.py

# Must be byte-for-byte non-mutating.
python tools/run_full_validation.py

# This design package must remain blocked.
python tools/check_operational_readiness.py

# A production release may use this only after all external and implementation evidence exists.
python tools/check_operational_readiness.py --require-go \
  --trust-policy /protected/operational-trust-policy.json \
  --evidence-index delivery/evidence-index.json
```

Do not alter the production evaluator merely to obtain GO. A change to the readiness model, checker, trust policy, canonicalization, claim count, role separation, or signature verification is itself a high-risk release change requiring independent review, new regression tests, and new out-of-band anchors.

## 29. Non-mutating validation and independent roots of trust

The validator is part of the attack surface. Enforce all of the following:

1. `tools/run_full_validation.py` never writes screenshots, reports, hashes, manifests, caches, lockfiles, timestamps, or any other repository content.
2. It records a secure tree snapshot before testing and requires exact equality afterward, including path, type, mode, size, and SHA-256.
3. Derived artifacts are created only by `tools/prepare_release_artifacts.py`, followed by check-only validation.
4. Release building uses one immutable source tree, builds twice independently, requires byte-for-byte identity, safely extracts each archive, and reruns non-mutating validation.
5. Symlinks, hardlinks, device files, FIFOs, unsafe permissions, path traversal, ADS, control/bidi characters, Unicode/case collisions, untracked generated files, secret material, and archive bombs are rejected.
6. Do not trust a policy or checker merely because it is in the same repository as the evidence it validates.

Production evaluation requires protected, out-of-band values for:

```text
ONE_INTENT_TRUST_POLICY_SHA256
ONE_INTENT_READINESS_CHECKER_SHA256
ONE_INTENT_RELEASE_SUBJECT_SHA256
ONE_INTENT_TRUSTED_TIME_ATTESTATION_SHA256
```

Store those anchors in a separately administered protected release environment, not in source control, mobile remote config, the production database being evaluated, or the same writable bucket as the evidence. Document administrator separation, rotation, emergency revocation, audit logging, and recovery.

## 30. Signed evidence model and exact release binding

Implement the schemas and evaluator in this package as a minimum, not a maximum. Every production evidence statement must:

- use strict canonical JSON with no floats, duplicate keys, non-NFC ambiguity, unsafe integers, or alternate serialization;
- be signed by a currently valid, non-revoked key with an allowed issuer role;
- identify the exact claim and gate;
- bind to the exact production release subject;
- list evidence artifacts with SHA-256, exact byte size, media type, and immutable storage identifier;
- state environment, command/tool, timestamp, limitations, and result;
- have the required number of independent reviewer approvals;
- keep issuer, reviewer, evidence-index signer, and release approver separated as required by policy;
- expire according to the claim-specific `maxAgeDays`;
- be indexed by a separately signed evidence index containing the exact required-claim set.

The production release subject must bind at least:

- source commit and source-tree digest;
- Android artifact digest;
- iOS artifact digest;
- backend image digest;
- signer image digest;
- configuration bundle digest;
- policy bundle digest;
- signed asset-registry digest;
- SBOM digest;
- release ID and production environment.

Reject evidence from a different binary, build flavor, region, account model, custody model, policy, token registry, provider configuration, signer deployment, or Store submission.

Use signed trusted-time evidence. Validate local verifier clock skew, key validity, evidence age, approval age, and revocation status. A manipulated device or CI clock must not make expired evidence valid.

## 31. Release GO, runtime activation, and user authorization are three separate gates

Even a valid `PRODUCTION_OPERATIONAL_GO` report must never authorize a transaction by itself. The signer must require all three layers:

### 31.1 Release layer

A current, signed, independently approved readiness report for the exact release subject.

### 31.2 Runtime layer

A fresh, signed `runtime-state-bundle` and a short-lived `runtime-control-plane-lease` with:

- maximum lifetime 300 seconds;
- monotonic sequence and deployment epoch;
- current kill-switch and emergency-stop state;
- provider, registry, policy, signer, reconciler, and telemetry health;
- no unresolved ledger difference;
- no stale or conflicting source;
- current exposure, fee-reserve, rate-limit, incident, and legal/region state;
- explicit statement that the lease does not authorize any transaction.

Recheck runtime state at the signer immediately before signing and immediately before broadcast when these are separate steps. Stop queued and retried operations when a newer sequence enables a kill switch.

### 31.3 Per-operation layer

A single-use, device-bound, maximum-120-second user authorization that binds:

- final Execution Capsule hash;
- operation type and ordered actions;
- account and device;
- chain/network and market;
- asset/contract/asset ID;
- recipient or verified saved destination;
- exact input amount, minimum receive, maximum fee, slippage/price-deviation limit;
- quote ID, quote digest, provider, generation and expiry;
- leverage, side, reduce-only, margin mode, and risk details where applicable;
- nonce/idempotency/cloid/message ID;
- policy and registry versions;
- user-visible Japanese review digest.

The runtime lease can never substitute for this authorization. Consume the authorization atomically. Reject replay, another device, another recipient, another amount, another quote, another market, a changed transaction payload, or an already consumed nonce.

### 31.4 Canonical quote and final-payload commitment

A non-zero hash field is not sufficient evidence that the quote has the approved meaning. Implement a strict, domain-separated canonical quote document and bind it to the operation authorization. At minimum it must contain:

- quote ID, provider ID, provider key/certificate identity, route ID and environment;
- exact account and deployment;
- source and destination CAIP-2 network IDs, numeric chain IDs and signed network-registry digest;
- exact asset IDs, contract addresses, decimals and signed asset-registry digest;
- operation type, ordered step IDs, side, position effect, margin mode and leverage where relevant;
- exact input amount or maximum input, expected output, minimum output, limit/trigger condition, maximum slippage and maximum total fee;
- fee asset, provider reimbursement/failed-action charge and settlement target for fee-readiness routes;
- source-state hash, market/account metadata versions, generated time, expiry and one-time quote nonce;
- exact Execution Capsule hash;
- a final-payload commitment covering the canonical Hyperliquid wire action or EVM transaction fields that the signer will produce.

Use decimal strings, strict NFC canonical JSON, no floats, no duplicate keys and a dedicated signature/hash domain. Verify the provider signature or an equivalently reviewed authenticated first-party quote channel inside the signer trust boundary. The protected signer must re-read the quote, recompute its digest, reconstruct the final order/transaction, recompute the final-payload commitment and compare every material field. Any route, provider, chain, asset, amount, recipient, calldata, order wire value, minimum receive, maximum fee, slippage, limit, trigger, expiry or state difference is a hard stop and requires a fresh quote and fresh user authorization.

### 31.5 Signed registry resolution and chain identity

Do not accept a registry digest as an uninterpreted string. The protected signer must load the exact signed registry bytes whose digest is bound to the release, account binding, runtime state, Execution Capsule, quote and operation authorization. It must then:

1. verify registry signature, signer role, validity interval, positive monotonic sequence and revocation state;
2. resolve each CAIP-2 network ID to the one allowed numeric chain ID and environment;
3. compare that value with the RPC/provider-reported chain ID and the transaction/order domain actually being signed;
4. resolve every asset to chain, contract, proxy implementation, runtime bytecode hash, decimals, capability flags and market/asset ID;
5. reject aliases, symbols, stale entries, production-ineligible entries, proxy/code drift, decimals drift, an unknown chain or any source disagreement;
6. keep the affected feature gate closed until a newly approved registry is distributed and activated.

Persist network-registry and asset-registry sequence high-water marks outside the release bundle in rollback-resistant storage.

### 31.6 Rollback-resistant release/runtime counters

Persist the highest accepted values for trusted-time sequence, evidence-index sequence, registry sequences, account-binding sequence, runtime-state sequence, runtime-lease sequence, deployment epoch, authorization revocation counter and signer policy epoch in a separately administered rollback-resistant store. A candidate must be strictly newer where the contract requires monotonicity. Equality is stale/replay, not current.

The readiness report must include the exact trusted-time and evidence-index sequences used for the decision. Runtime authorization must compare those values with the current signed inputs and protected high-water marks. Advance high-water values atomically with accepting the corresponding decision; do not advance them for a rejected candidate. Restore, failover and disaster-recovery drills must prove that older values cannot become valid after database or infrastructure rollback.

### 31.7 Atomic signing and ambiguous broadcast state

Implement one durable state machine with a unique constraint over authorization ID, operation ID, nonce/idempotency key and provider-specific identifier (`cloid`, transaction nonce/hash or bridge message ID). The signer-side transaction must atomically:

1. reserve the unused authorization and nonce;
2. verify all release, runtime, registry, quote, capsule and user-authorization inputs again;
3. construct and persist the exact final-payload commitment;
4. obtain the signature;
5. mark the authorization permanently consumed and persist the signed bytes/hash before any network call.

If the process fails after signing, enter `SIGNED_BROADCAST_UNKNOWN`; never create a fresh signature or nonce for the same intended effect. If broadcast acknowledgement is ambiguous, enter `BROADCAST_ACCEPTED_UNCONFIRMED`. Reconcile by exact transaction hash, Hyperliquid `cloid`/order/fill state, bridge message ID and account-state change. Only deterministic evidence may transition to `CONFIRMED`, `REJECTED_BEFORE_EFFECT`, `PARTIAL` or `MANUAL_RESOLUTION_REQUIRED`. A timeout is not proof of failure. Include crash-point, concurrency, failover and replay tests for every transition.

## 32. Mandatory implementation and adversarial test expansion

In addition to earlier sections, implement and evidence the following.

### 32.1 Android

- hardware-backed Keystore where supported, key attestation validation, biometric policy, secure backup exclusions;
- overlay/tapjacking detection, obscured-touch rejection, screenshot/app-switcher protection, debugger/hook/root risk handling;
- Protected Confirmation capability probe where appropriate, with no silent downgrade;
- Play Integrity as one risk signal, never the sole authorization factor;
- strict App Links/deep-link parsing that creates a non-executable draft only;
- clipboard replacement detection and full-address verification path;
- TalkBack, large text, switch access, IME, locale, rotation, multi-window, low-memory and process-death tests.

### 32.2 iOS

- Keychain/Secure Enclave policy, access-control flags, backup/restore exclusions and device migration behavior;
- App Attest server verification, counter/reinstall behavior, jailbreak/debug/hook risk handling;
- Universal Link parsing into non-executable drafts only;
- screen recording/snapshot privacy behavior;
- VoiceOver, Dynamic Type, keyboard, safe-area, rotation, background/foreground and process-termination tests.

### 32.3 Backend and data

- strict authentication, sender-constrained tokens, device proof, rate limits, abuse and cost budgets;
- transactional outbox/inbox around every external side effect;
- append-only double-entry ledger and zero-unexplained-difference reconciliation;
- expand/contract database migration, version compatibility, write fencing, rollback rehearsal;
- append-only tamper-evident audit chain replicated to independently administered immutable storage;
- encrypted backup plus real restore drills proving RPO/RTO;
- redaction of secrets, recovery material, complete addresses where not necessary, authorization payloads, and sensitive conversation data.

### 32.4 Supply chain

- immutable dependency/action/container/compiler pins;
- lockfile integrity, dependency-confusion and malicious-build-script tests;
- signed SBOM and SLSA provenance for every binary/image/archive;
- hermetic builds and at least one independently administered builder comparison;
- HSM/managed release signing with two-person approval, revocation, rotation, and anti-rollback controls;
- Store metadata, entitlements, permissions and privacy labels bound to the exact release subject.

### 32.5 Tokens, approvals, swaps, and cross-network movement

- bind token identity to chain ID, contract, code hash, proxy implementation, decimals, and capability flags;
- detect upgrades, pause, blacklist, rebase, fee-on-transfer and unknown behavior;
- use exact-amount, short-expiry, verified-spender approvals; no default unlimited allowance;
- display and verify typed data before Permit signatures; provide revoke and stale-approval inventory;
- audit and pin routers, bridges, guardians, upgrade authorities, finality and challenge rules;
- do not call a bridge complete until destination finality and destination receipt are proven;
- use message-ID idempotency and explicit in-transit/partial/failed states;
- prove destination fee readiness before movement.

### 32.6 Hyperliquid

Recheck current official Hyperliquid documentation and SDK sources on the execution date. Pin the exact API/SDK/document versions used. Implement and test:

- a single atomic API-wallet nonce authority or a formally safe partitioning design;
- API wallet/agent lifecycle, authorization and revocation;
- exact signature domain and canonical action vectors;
- official metadata asset IDs and explicit spot/perpetual market identity, never symbol-only routing;
- WebSocket sequence/gap/out-of-order/reconnect detection and REST snapshot resynchronization;
- order acknowledgements, fills, partial fills, cancel races, reduce-only rejection, open orders and position reconciliation;
- cross/isolated margin, funding, fees, leverage and liquidation fields;
- pre-order liquidation preview separated from post-fill official account state;
- stale/null/conflicting liquidation data as a hard stop;
- rate limits, timeouts, ambiguous responses and unknown schema as fail-closed states;
- Testnet lifecycle and bounded Mainnet canary evidence.

### 32.7 JPYC and network-fee readiness

Recheck current official JPYC and JPYC EX materials on the execution date. Do not treat this package's examples as production contract data. Require:

- officially sourced network, chain ID, contract, decimals, proxy/code hash and product-era distinction;
- two-person registry approval and runtime drift monitoring;
- JPYC EX partner agreement, production credentials, registered redirect/callback values and end-to-end contractual tests;
- a verified sponsor/paymaster/relayer or swap route for zero-native-balance cases;
- operation-bound quotes, exact maximum fee, provider identity, expiry, reimbursement terms and failure-charge behavior;
- concurrency-safe monthly/daily/user/operation budgets and double-charge prevention;
- provider-reserve and abuse monitoring;
- Testnet/sandbox and extremely bounded Mainnet zero-gas canaries;
- a no-fixed-amount manual fallback when no verified route is available.

Never assume that JPYC can pay the first gas transaction merely because the wallet owns JPYC.

### 32.8 AI, natural language, and ChatGPT boundary

- The LLM produces an untrusted, non-authoritative draft only.
- It never chooses a raw address, contract, asset ID, chain ID, nonce, fee route, signature payload or final transaction.
- Material ambiguity, negation, quoted speech, voice-recognition uncertainty and conflicting instructions block execution.
- External webpages, QR data, support messages and tool output are untrusted content, not user authority.
- Pin model/provider/version/config; run a versioned golden corpus and shadow evaluation before promotion.
- Test prompt injection, tool injection, data exfiltration, model fallback and provider outage.
- Minimize/redact data and evidence retention; enforce gateway-to-signer network isolation.
- Keep ChatGPT/App/MCP/Action integrations strictly non-transactional: redacted read-only status, fixed glossary, fixed non-transactional error explanation, generic safety guidance, and a fixed neutral handoff only. Do not expose transaction-specific planning, drafts, quotes, button-by-button steps, recovery instructions, values, links, tokens, or context. They must not initiate, execute, or otherwise facilitate money, crypto, or investment transactions under the current OpenAI terms. Recheck the official terms on the implementation and release dates; a policy change never automatically enables writes.

## 33. Operational exercises required before GO

Unit and integration tests are insufficient. Produce immutable, release-bound evidence for:

1. all fake-provider flows and failure injection;
2. staging read-only operation;
3. Testnet writes for every supported transaction class;
4. physical Android and iPhone device matrices;
5. zero-native-balance fee-readiness scenarios;
6. Hyperliquid gap, nonce, partial-fill, liquidation and reconciliation scenarios;
7. DB crash points and migration rollback;
8. kill-switch propagation, including queued operations and stale leases;
9. key compromise, device loss, provider outage, API drift and data-breach drills;
10. backup restore meeting RPO/RTO;
11. independent mobile/backend/protocol/cryptography reviews;
12. legal and Store evidence for the exact entity, region, feature set and binaries;
13. an explicitly approved, extremely small Mainnet canary with hard per-operation, daily and total exposure limits;
14. zero unexplained reconciliation difference after the canary;
15. rollback, user notice and postmortem review.

A canary failure, ledger difference, stale telemetry, unresolved critical/high issue, legal uncertainty, Store rejection, provider contract gap, or unknown protocol state immediately returns the release to `BLOCKED_NOT_OPERATIONAL`.

## 34. External blockers must be executable human instructions

When the coding environment lacks an account, credential, contract, licensed entity, device, HSM/MPC facility, audit firm, legal decision, Store decision, Testnet asset or Mainnet approval, create or update `delivery/EXTERNAL_BLOCKERS.md`.

Each blocker must contain:

- blocker ID and affected readiness claim IDs;
- responsible role and independent reviewer;
- exact service, vendor or portal;
- required account type and permissions;
- exact menu/screen and button/field labels, or a dated note that the current UI must be re-observed;
- documents, identifiers and values to prepare;
- callback/domain/bundle/package/network configuration;
- secret-storage location and prohibited storage locations;
- success screen/export/submission ID/contract number required as evidence;
- evidence artifact path and required hash/signature;
- exact automated and manual tests to rerun;
- the gate and feature flag that remain closed;
- expiry/revalidation date and escalation contact.

Do not write vague instructions such as “obtain credentials,” “confirm with legal,” “test on a phone,” or “submit to the Store.”

## 35. Required final repository outputs

In addition to earlier deliverables, create production-capable equivalents of:

```text
config/operational-readiness.json
config/operational-trust-policy.production.json         # public keys/roles only; no secrets
config/runtime-policy.production.json
release/release-subject.json
delivery/evidence-index.json
delivery/OPERATIONAL_READINESS_REPORT.json
delivery/RUNTIME_ACTIVATION_REPORT.json
delivery/GATE_DECISIONS.json
delivery/EXTERNAL_BLOCKERS.md
delivery/reports/FINAL_ENGINEERING_REPORT.md
delivery/reports/FINAL_SECURITY_REPORT.md
delivery/reports/FINAL_OPERATIONS_REPORT.md
delivery/reports/FINAL_LEGAL_STORE_REPORT.md
```

Private signing keys, recovery phrases, API secrets and HSM material must never enter the repository or evidence archive.

Add a single command that verifies a frozen production release without mutating it. It must output only one machine status, a complete blocker list and artifact hashes. Add a second signer-side policy check that independently proves a transaction cannot be signed without current release GO, runtime state, lease and per-operation authorization.

## 36. Final completion protocol

Before reporting completion:

1. freeze the exact source and all release inputs;
2. run full non-mutating validation;
3. perform independent deterministic builds and verify provenance;
4. verify every evidence signature, review threshold, expiry, revocation and release binding;
5. require all 37 gates and 93 claims to pass;
6. verify protected out-of-band anchors;
7. obtain fresh trusted time and prove trusted-time/evidence-index/registry/runtime counters are strictly above protected high-water marks;
8. verify the runtime state and issue a short-lived lease;
9. prove the lease alone cannot authorize a transaction;
10. run a denied-operation test without per-operation authorization;
11. run negative tests that mutate one field at a time in the signed registry, canonical quote, final-payload commitment, chain ID, recipient, amount, fee, expiry and source state;
12. run crash/concurrency tests at every reserve/sign/persist/broadcast transition and prove `SIGNED_BROADCAST_UNKNOWN` never causes a second signature;
13. run an approved bounded operation and reconcile it to zero difference only when every prior gate permits;
14. immediately test kill-switch revocation, sequence rollback and stale-lease rejection;
15. generate final reports without changing the frozen artifacts;
16. rerun verification from a clean, independently administered environment.

Then return exactly one operational status:

- `PRODUCTION_OPERATIONAL_GO` only when every required artifact and external decision actually exists and verifies; or
- `BLOCKED_NOT_OPERATIONAL` with exact blockers and human steps.

Do not claim literal 100% safety or absence of unknown vulnerabilities. The defensible completion claim is: all explicitly defined release and runtime gates for the exact subject have valid evidence, fail-closed controls are active, and no known blocker remains.
