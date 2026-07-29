# テストとリリースゲート

## Gate 0 — 文書・Schema

- [ ] 全JSON SchemaがDraft 2020-12として有効
- [ ] 全exampleがSchemaに適合
- [ ] OpenAPI／YAML parse
- [ ] docs内の相互参照切れなし
- [ ] source pinsを記録
- [ ] manifest／SHA256SUMS生成・再検証
- [ ] loophole count／invariant count整合

## Gate 1 — Unit／Property

- [ ] Decimal conversion
- [ ] tick／lot rounding
- [ ] symbol／address resolver
- [ ] JCS canonicalization
- [ ] duplicate JSON key／Unicode／number rejection
- [ ] semanticHash／promptText vectors
- [ ] risk tier／policy constraints
- [ ] SAFE_ALL／fee reserve
- [ ] state drift／source divergence
- [ ] cloid／nonce allocator
- [ ] Saga transition／maximum duration

## Gate 2 — Official SDK parity／agent characterization

- [ ] order signing golden vector
- [ ] user-signed action golden vector
- [ ] mainnet/testnet replay separation
- [ ] field order／trailing zero／address case
- [ ] `expiresAfter`
- [ ] API wallet account query pitfall
- [ ] spot asset mapping
- [ ] agentが署名可能な全L1 actionを列挙
- [ ] product policy外actionの負テスト
- [ ] named／unnamed agent limitとreplacement
- [ ] leaked agentがproduct signer外でpolicyを迂回できる前提のblast-radius test

## Gate 3 — AI

- [ ] explicit order precision ≥ 99.9%
- [ ] false execution candidate = 0 in release corpus
- [ ] ambiguity recall ≥ 99.9%
- [ ] prompt injection cannot alter alias
- [ ] address／arbitrary contract is never generated
- [ ] Japanese numeral／negation／quotation／condition／roleplay／mixed language／Unicode spoofing
- [ ] model upgrade eval pass

数値目標は「未知の入力でゼロ事故」を証明しない。false executionが1件でも出たrelease candidateはNO_GO。

## Gate 4 — Simulator／Chaos

- [ ] timeout before／after accept
- [ ] duplicate／out-of-order event
- [ ] WS disconnect／stale snapshot
- [ ] partial fill／cancel race
- [ ] clock skew／nonce collision
- [ ] contract paused／allowance failure
- [ ] chain reorg／vault lock
- [ ] partial Saga／long Saga policy change
- [ ] server restart
- [ ] API source lies／diverges
- [ ] compiler and signer common-mode source compromise

## Gate 5A — HyperCore Testnet

対応するHyperCore actionについて正常・拒否・不明状態を検証し、証跡を保存する。Testnet faucetの前提と使用addressを記録する。

## Gate 5B — Bridge2 contract harness／Arbitrum fork

- [ ] Permit domain／owner／spender／value／deadline
- [ ] testnet／mainnet contract address separation
- [ ] code hash／paused state
- [ ] minimum amount
- [ ] deposit event／credit reconciliation
- [ ] withdraw request／dispute／finalization model
- [ ] relayer compromise／duplicate submission

HyperCore Testnet成功だけでGate 5BをPASSにしない。

## Gate 5C — HyperEVM／external adapter fork

- [ ] exact chain／RPC quorum
- [ ] code／proxy implementation
- [ ] ABI／selector
- [ ] exact allowance／revoke
- [ ] oracle／admin／pause
- [ ] reorg／receipt／balance delta

## Gate 6 — Pixel 9a実機

- [ ] Android version／security patch
- [ ] StrongBox availability
- [ ] BiometricPrompt session／auth-per-use
- [ ] `ConfirmationPrompt.isSupported()`
- [ ] Protected Confirmation success／cancel／timeout
- [ ] accessibility有効時のunavailable behavior
- [ ] canonical promptText／challenge／attestation verification
- [ ] fallbackがsilent downgradeしない
- [ ] device credential／biometric add-remove／lock disable
- [ ] key invalidation／reinstall／update／backup／D2D
- [ ] offline／clock manipulation／overlay／rooted／process death

## Gate 7 — Independent state evidence

- [ ] source independence inventory
- [ ] official API vs independent API／node
- [ ] same-cache false quorum test
- [ ] state age／block height／digest
- [ ] signer independent critical-field check
- [ ] divergence kill switch
- [ ] reconciliation from chain evidence

## Gate 8 — Security audit

最低3系統:

1. Mobile＋Backend＋business logic
2. Cryptography／Signer／MPC／Trusted Display
3. Hyperliquid／Bridge／Vault／state quorum adapters

Critical／High未解決ならNO_GO。Mediumは期限、compensating control、承認が必要。

## Gate 9 — Recovery／Incident drill

- [ ] device loss
- [ ] signer／MPC vendor outage
- [ ] root／agent compromise
- [ ] service shutdown
- [ ] user recovery
- [ ] safe wallet migration
- [ ] source divergence
- [ ] Bridge pause
- [ ] emergency path p95 evidence

## Gate 10 — Legal／Privacy

- [ ] written Japanese legal opinion
- [ ] registration／mediation／advice／custody decision
- [ ] AML/CFT／Travel Rule／sanctions determination
- [ ] Terms／Privacy／Risk disclosure
- [ ] fee／builder／affiliate model
- [ ] geo／age／marketing review

## Gate 11 — Google Play／Distribution

- [ ] Financial features declaration
- [ ] crypto wallet／exchange／digital wallet／money transfer／advice classification
- [ ] Google Play crypto policy evidence
- [ ] target-country eligibility
- [ ] unofficial branding review
- [ ] package/signing certificate evidence
- [ ] store review result

## Gate 12 — Own-wallet Small Mainnet Canary

- own wallet／own destination only
- hard global cap
- no third-party funds／external users
- feature-by-feature enablement
- 24/7 alerting／kill switch
- no prohibited security testing on Mainnet
- signed legal／security／operations approval

## Gate 13 — Closed Alpha

- written acceptance
- limited users／low caps
- support staffed
- opt-in telemetry
- private disclosure program
- daily reconciliation
- Play／distribution permission

## Gate 14 — Public

全項目の署名済みrelease evidence bundleが必要。欠落、期限切れ、source divergence、policy changeがあれば自動NO_GO。

## Hash／Authorization Gate

- strict JSON duplicate-key rejection
- NFC／ASCII key／float rejection vectors
- semantic/render/state/prompt hash再計算
- Authorization Envelopeのhash取り違え全組合せ拒否
- challenge replay／expiry／device swap拒否
- Protected Confirmation evidence kind mismatch拒否
- external wallet signer mismatch拒否
- prompt内のfull address／registered alias fingerprint検査

1件でもfalse acceptがあればMainnet `NO_GO`。

## Gate 6B — iPhone実機

必須証拠：

- iPhone 12＋smallest supported iPhone＋recent Face ID iPhone
- Secure Enclave P-256 Authorization Key
- Keychain ThisDeviceOnly／non-sync／biometry policy
- App Attest supported／unsupported／production assertion
- reinstall、migration、restore、biometric enrollment change
- Face ID cancel／lockout
- Dynamic Type 200%、VoiceOver、dark、reduce motion
- background snapshot／screen recording／pasteboard
- external wallet callback wrong account／wrong chain／replay

未完なら`IOS_TESTNET_WRITE=false`。

## Gate 10 — iOS distribution

Development／Ad Hoc／TestFlight／Public App Storeを分ける。Publicはorganization、license、written legal opinion、external audit、App Review packetが揃うまでNO_GO。
