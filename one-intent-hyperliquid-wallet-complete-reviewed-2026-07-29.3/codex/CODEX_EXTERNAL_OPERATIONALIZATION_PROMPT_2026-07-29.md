# Codex外部運用化・本番証拠取得プロンプト

**対象baseline:** `one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.2`  
**作成日:** 2026-07-29  
**目的:** このbaselineを改ざんせず、外部サービス、native build、実機、HSM/MPC、Testnet、法務・Store審査、独立監査、運用基盤まで実際に完了し、証拠で裏付けられた運用候補releaseを作る。

---

## 0. あなたの役割

あなたは、このrepositoryの実装・インフラ・mobile・security・protocol・release engineeringを横断して作業するCodex実行担当です。説明だけで終えず、現在の実行環境、接続済みrepository、CI、cloud、developer portal、Testnet、実機、secret managerで権限のある作業を最後まで実行してください。

ただし、権限・資格情報・契約・法務判断・実機・外部審査・二者承認がない作業を成功したことにしてはいけません。実行できない外部作業は、後述のblocker形式で、担当role、公式portal、具体的な画面・field、必要資料、期待結果、証拠path、再試験commandまで記録してください。

機能仕様の唯一の正本は次です。

```text
codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md
```

本ファイルは、上記正本を外部環境で実行し、運用証拠を取得するための実行契約です。矛盾時は、よりfail-closedで、資金・鍵・個人情報・release integrityを保護する方を採用し、矛盾と判断をdecision logへ残してください。

---

## 1. 現在の事実を変更せず受け入れる

このbaselineについて、開始時点の正しい状態は次です。

```text
localSandboxStatus=LOCAL_SANDBOX_OPERATIONAL_GO
productionStatus=BLOCKED_NOT_OPERATIONAL
productionWritePermitted=false
mandatoryGates=37
passedGates=0
requiredClaims=93
acceptedClaims=0
```

収録済みなのは、決定論的Python参照コア、Schema、OpenAPI、fake adapter、browser prototype、loopback限定・非取引local sandbox、非変異validation、再現可能ZIP、evidence contractです。収録されていないのは、完成Android/iOS app、live backend、production signer、鍵、JPYC EX資格情報、fee provider契約、Hyperliquid write資格、実機証拠、独立監査、法務意見、Store承認です。

このbaselineの`config/build-metadata.json`と`tools/package_metadata.py`は、設計releaseについてnative/live/mainnet/production claimをすべてfalseに固定しています。これを単純に反転してGOを捏造してはいけません。baselineをimmutable inputとして保存し、運用実装は新しいversion、明示的なproduction profile、別release subject、独立したtrust policy、署名済み証拠を持つ新releaseとして作成してください。

---

## 2. 絶対ルール

1. **証拠なしでgateを開かない。** screenshot、log、receipt、artifact digest、signed statement、review approvalのない「実施済み」は不合格です。
2. **秘密をrepository、prompt、chat、log、artifact、screenshotへ入れない。** API key、wallet secret、seed、private key、2FA recovery code、App Store/Play credential、HSM shareはsecret managerまたはhardware boundaryだけで扱います。
3. **production keyをAI processへ渡さない。** Codexが参照できるのはsecret reference、public key ID、attestation、redacted resultだけです。
4. **Testnet before Mainnet。** Hyperliquid、bridge、fee route、JPYC関連のwriteは、fake→local integration→sandbox/Testnet→bounded canaryの順で進めます。
5. **Mainnet canaryは明示的な人間承認、上限、対象account、期限、kill switch、照合手順が揃う場合だけ。** 権限が曖昧なら実行せずblockerにします。
6. **blind retry禁止。** 署名後やbroadcast後の結果不明は`SIGNED_BROADCAST_UNKNOWN`としてauthoritative reconciliationまで再署名・再送しません。
7. **exact release binding。** code、native binary、container、configuration、policy、asset registry、SBOM、evidence、legal/store decisionを同じrelease subject digestへ結合します。
8. **rollback禁止。** trusted time、evidence index、registry、runtime bundle、lease sequenceはpackage外の保護high-water markより必ず大きくします。
9. **readinessと取引承認を分離。** `PRODUCTION_OPERATIONAL_GO`だけで取引を実行せず、fresh runtime state、300秒以下のlease、120秒以下のsingle-use操作別本人承認、signer直前再検証を要求します。
10. **外部仕様は実行日に公式一次資料で再確認。** blog、検索snippet、第三者記事を正本にしません。取得日時、URL、document version、commit/release、SHA-256をsource pinへ保存します。
11. **法的結論を推測しない。** 対象法人、custody model、asset flow、derivatives機能、対象地域、fee sponsorship、KYC/AML、privacy、marketing、store distributionに結合した書面判断を資格ある専門家から取得します。
12. **未知・欠落・期限切れ・revoked・scope mismatchはすべてNO-GO。** 一部成功を全体成功に丸めません。

---

## 3. 開始時のbaseline検証

作業開始前に、受領ZIPのhashを別記録へ固定し、clean directoryへ展開してください。macOS metadata、symlink、path traversal、重複Unicode pathを持ち込まないでください。

```bash
set -euo pipefail
sha256sum one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.2.zip
unzip -q one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.2.zip -d baseline-clean
cd baseline-clean/one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.2

python3 -B tools/check_python_sources.py
python3 -B tools/test_python_unit_suite.py
python3 -B tools/run_local_sandbox.py self-test
python3 -B tools/test_validation_harness.py
python3 -B tools/run_full_validation.py
python3 -B tools/check_operational_readiness.py
```

期待値:

- 全Python source compile PASS
- 全Python unit tests PASS
- local sandbox self-test PASS
- full validation PASS
- readiness checkerは、設計releaseが`BLOCKED_NOT_OPERATIONAL`であることをPASSとして確認
- source treeがvalidation前後でbyte-for-byte不変

一つでも違えば運用実装を開始せず、baseline破損として記録してください。

---

## 4. 作業repositoryとrelease分離

1. baseline ZIPと展開treeをread-only archiveへ保存する。
2. baseline tree digest、ZIP SHA-256、受領日時、受領者を署名可能な記録へ固定する。
3. 新しいprivate repositoryまたは保護branchへimportし、branch protection、required review、signed commit/tag、secret scanning、dependency scanningを有効化する。
4. 運用実装versionを新しく採番する。`2026-07-29.2`を上書きせず、さらに新しいversionへ進める。
5. design profileとproduction profileを分離し、production profileは実証済みartifactだけを参照する。
6. generated evidenceと手入力approvalを混同しない。generatorは外部証拠を生成したことにできない。
7. CI identity、release identity、evidence issuer、independent reviewer、runtime authorizer、signer keyのroleとkeyを分離する。

最低限、次を新releaseで作成してください。

```text
release/RELEASE_SUBJECT.json
release/SOURCE_PINS.json
release/SBOM.spdx.json
release/PROVENANCE.json
release/ARTIFACT_HASHES.txt
release/BUILD_ENVIRONMENT.md
release/REPRODUCIBILITY_REPORT.md
release/CODEX_EXECUTION_REPORT.md
release/UNRESOLVED_EXTERNAL_BLOCKERS.md
release/OPERATIONAL_HANDOFF.md
```

---

## 5. 実行順序

次の順序を崩さないでください。上流identityやpolicyが未確定のまま下流binaryやMainnet canaryを作り直す無駄と、誤ったrelease bindingを防ぐためです。

1. source control、CI、hermetic build、artifact signing
2. deterministic shared core、cross-language vectors
3. backend、database、outbox、ledger、reconciler、admin control plane
4. signer、HSM/MPC、key ceremony、release/runtime authorization
5. Android native appと実機
6. iOS native appと実機
7. signed asset registry、JPYC identity、network/RPC identity
8. Hyperliquid fake/local/Testnet integration
9. JPYC EX controlled handoff
10. zero-native-balance fee route
11. observability、SRE、backup/restore、incident drills
12. privacy、legal、regional controls、Apple/Google submission
13. independent mobile/backend/protocol/cryptography audit
14. exact release evidence、readiness、runtime activation、bounded canary

---

## 6. Workstream A — managed source、CI、reproducible supply chain

### 実装

- protected repository、required two-person review、signed tag、CODEOWNERS、branch protection
- pinned toolchain: Python、Node、Playwright/Chromium、JDK、Gradle、Android SDK/NDK、Xcode/Swift、container builder
- lockfile、dependency hash、container digest、base image digest
- hermetic buildまたはnetwork accessを記録したcontrolled build
- SAST、dependency audit、secret scan、license scan、SBOM、provenance、artifact signing
- Android/iOS/backend/signer/config/policy/registryを同じrelease IDへ結合
- clean builderを二つ使った再現性または、非再現部分を明示したequivalence evidence

### 外部作業

- managed CI runner、artifact registry、code signing service、Apple signing、Google Play signingを設定
- CI secretはOIDC/workload identityとsecret managerで取得し、長期credentialを置かない
- production deploymentはprotected environmentと二者承認を要求

### 証拠

```text
delivery/evidence/supply-chain/
  source-tag.json
  build-environment.json
  dependency-lock-hashes.txt
  sbom.spdx.json
  provenance.intoto.jsonl
  artifact-signatures/
  clean-build-a.log
  clean-build-b.log
  reproducibility-report.md
  secret-scan.json
  dependency-scan.json
```

### 合格条件

- source commit/tree、全artifact、config/policy/registry/SBOM hashがrelease subjectと一致
- unpinned dependency、mutable tag、unreviewed production change、secret findingが0
- release artifactをclean extract/deployして同じ検証結果を再現

---

## 7. Workstream B — backend、data、ledger、reconciliation

### 実装

- authenticated Control API、transaction intent parser、fixed-catalog nontransactional support gateway
- strict schema、duplicate-key rejection、NFC、decimal string、payload size/depth limits
- database migration、transactional outbox、idempotency table、nonce uniqueness、operation state machine
- double-entry ledger、provider charge/reimbursement、external receipt、reconciliation difference
- signed registry/quote/runtime bundle cacheとexpiry/revocation
- append-only audit、PII/secret redaction、retention、DSAR/deletion workflow
- admin role separation、two-person high-risk change、break-glass audit
- kill switchをsigner直前とqueue drain時にも再確認

### 必須negative tests

- same idempotency key with changed material
- duplicate nonce with changed authorization ID
- crash after reserve、after sign、before/after broadcast
- DB rollback、outbox duplicate、stale read、WebSocket gap、provider timeout
- partial fill、partial bridge、fee charged but action failed
- stale registry/quote/runtime lease、revoked provider、wrong chain ID
- log injection、oversized JSON、deep nesting、mixed Unicode、unknown properties

### 証拠

```text
delivery/evidence/backend/
delivery/evidence/database/
delivery/evidence/ledger/
delivery/evidence/reconciliation/
delivery/evidence/admin-change-control/
```

### 合格条件

- blind retry 0
- unexplained ledger difference 0
- restore後もnonce/idempotency/reconciliation invariantを維持
- signerへの入力はexact capsule hashとrelease/runtime bindingsを含む

---

## 8. Workstream C — deterministic coreとcross-platform一致

Python参照実装と、Kotlin、Swift、backend languageで次を同一test vectorから一致させてください。

- canonical JSON byte sequence
- duplicate key、float、exponent、NaN/Infinity、negative zero拒否
- NFC、非string key、depth/size/node limit
- Decimal parsing、scale、rounding、overflow
- intent commitment
- asset registry digest
- canonical quote binding/full digest
- final payload commitment
- execution capsule hash
- DPoP/sender-constrained proof
- authorization、runtime lease、release subject hash

全languageのhash outputを1つのmachine-readable reportへ集約し、1件でも差があればNO-GOです。

---

## 9. Workstream D — signer、HSM/MPC、key ceremony

### 実装

- signerはnetwork edge、AI、mobile client、general backendから分離
- HSM/MPCまたは承認済みhardware-backed key custody
- key generation、backup/recovery、rotation、revocation、compromise response
- two-person ceremonyとseparate witness
- release readiness、runtime lease、per-operation authorizationを独立検証
- capsule、quote、registry、RPC chain ID、final payload、account/device、nonceをsigner内で再計算
- authorizationをdurable atomic reserveしてから一度だけ署名
- signed bytesとbroadcast outcomeをdurable stateへpersist
- `SIGNED_BROADCAST_UNKNOWN`はreconciliationまで再署名禁止
- stale kill switch/runtime state/provider/telemetry/ledgerなら署名拒否
- signer processへraw user text、OpenAI output、browser payloadを直接渡さない

### 外部作業

- HSM/MPC tenant、roles、policy、attestation、audit exportを設定
- ceremonyを実施し、private materialを出力せずpublic key IDとattestationを保存
- protected high-water markをpackage外に配置
- disaster recoveryとkey compromise drillを実施

### 証拠

```text
delivery/evidence/signer/
delivery/evidence/key-ceremony/
delivery/evidence/runtime-authorization/
delivery/evidence/trusted-time/
delivery/evidence/high-water-marks/
```

### 合格条件

- private key/seed/shareがrepo・CI log・Codex contextに0
- replay、rollback、scope mismatch、stale lease、wrong releaseをすべて拒否
- independent cryptography/security reviewerがexact signer artifactを承認

---

## 10. Workstream E — Android

### 実装

- Kotlin/Jetpack Composeで12 flowと全fail-closed stateを実装
- Android Keystore hardware-backed key、biometric/user-presence policy
- Play Integrityまたは選定attestationをserver-side検証
- root/hook/overlay/tapjacking/debugger/backup/clipboard/deep-link/screenshot privacy policy
- network security config、certificate strategy、no cleartext、strict domain allowlist
- accessibility: TalkBack、font scale、320px相当、IME、rotation、safe insets
- lifecycle/process death/offline/retry/reconciliation
- signed AAB/APK、mapping、SBOM、provenance

### 外部作業

- exact legal entityのGoogle Play Console
- app signing、internal testing、closed testing、financial features declaration
- 対象地域のcrypto wallet/exchange policyと必要license/formを実行日時点で公式Google Play policyから再確認
- walletがnon-custodialでも、対象機能、地域、derivatives、fiat/JPYC handoff、marketingについて法務判断を取得
- physical devicesでmatrixを実行

### 証拠

```text
delivery/evidence/android/
  signed-artifact-hashes.txt
  play-integrity/
  device-matrix/
  accessibility/
  security-negative-tests/
  play-console/
```

### 合格条件

- exact signed AAB/APK hashがrelease subjectと一致
- required device/security/accessibility matrixが全PASS
- Play submission ID、declaration、review resultが対象binary/regionへ結合

---

## 11. Workstream F — iOS

### 実装

- Swift/SwiftUIで12 flowと全fail-closed stateを実装
- Keychain/Secure Enclave、LocalAuthentication、App Attest server verification
- jailbreak/hook/debugger、universal link、pasteboard、backup、privacy snapshot対策
- VoiceOver、Dynamic Type、small device、rotation、safe area、IME相当入力
- process suspension/termination、offline、reconciliation
- signed archive/IPA、dSYM、SBOM、provenance

### 外部作業

- Apple Developer Programはexact legal entity/organization enrollmentで実施
- Apple App Review Guidelinesのcrypto wallet、financial service、privacy、account deletion、sign-in、payments該当箇所を実行日に再確認
- App Attest key/environmentとserver verificationを構成
- TestFlight internal/external testing、App Store Connect submission、privacy labels、export/compliance、support/termsを登録
- 物理iPhoneでsecurity/accessibility matrixを実施

### 証拠

```text
delivery/evidence/ios/
  signed-artifact-hashes.txt
  app-attest/
  device-matrix/
  accessibility/
  security-negative-tests/
  app-store-connect/
```

### 合格条件

- exact signed archive/IPA hashがrelease subjectと一致
- App Attest server-side validationとnegative tests PASS
- Apple submission/decisionが対象法人、bundle ID、version、binary hash、regionへ結合

---

## 12. Workstream G — Hyperliquid

### source pin

実行日時点で、Hyperliquid公式documentationと公式SDK repositoryだけを一次資料として確認してください。公式Python SDKを使う場合も、branch名ではなくexact commit/releaseとdependency hashを固定します。Mainnet URLをTestnetと取り違えないよう、environment identityをconfig、UI、receipt、evidenceへ明示します。

### credential

- Hyperliquid UI/公式手順で生成・承認されたAPI walletを使う
- account public addressとAPI wallet secretを分離
- secretはsecret manager/HSM referenceからruntime注入
- withdrawal、agent admin、builder fee adminなど不要capabilityを付与しない
- credential rotation/revocationとincident procedureを作る

### 実装・試験

- official metadata/asset identity pin
- account state、positions、orders、margin、funding、liquidation inputs
- client order ID/idempotency、nonce、request signing、clock handling
- WebSocket sequence/gap/reconnect、REST reconciliation
- accepted、partial、filled、cancelled、rejected、unknown
- stale or missing liquidation/reference priceならreview/executeを停止
- emergency cancel/closeは独立control、二者承認、rate limit、audit
- fake adapterとlive/Testnet adapterを別module・別credential・別evidence labelにする

### Testnet順序

1. read-only metadata/account smoke
2. intentionally invalid order negative test
3. minimum bounded order
4. partial fill/cancel
5. disconnect and WebSocket gap
6. crash after sign/broadcast unknown
7. restart and reconciliation
8. emergency cancel
9. zero unexplained ledger difference

### Mainnet canary

次が全部揃う場合だけ、人間が明示承認した極小上限・対象account・market・期限で実施します。

- Testnet lifecycle全PASS
- independent protocol/security review
- legal/region/store scope approval
- signer/HSM、kill switch、monitoring、reconciliation operational
- canary budget、stop condition、rollback owner、real-time observer

### 証拠

```text
delivery/evidence/hyperliquid/
  source-pins.json
  sdk-lock.json
  credential-public-metadata.json
  testnet-requests-redacted/
  testnet-receipts/
  websocket-gap-tests/
  lifecycle-report.json
  reconciliation-report.json
  mainnet-canary/   # 実施した場合のみ
```

---

## 13. Workstream H — JPYCとJPYC EX

### identityの固定

- 現行の資金移動業型JPYCと、旧Prepaid型JPYCを混同しない
- JPYC公式website、公式GitHub organization、公式contract list、金融庁等の一次資料を実行日に確認
- networkごとにcontract、proxy implementation、decimals、code hash、chain IDをRPCで再確認
- symbol/nameだけでassetを認識しない
- production eligibilityはsigned registryとindependent reviewが揃うまでfalse

### JPYC EX handoff

- JPYC EXの正式なpartner/API/redirect/return contract、KYC/AML、supported region、support/escalation、SLAを契約で確認
- handoff ID、amount、network、receiving address、fingerprint、created/expiry、return stateを固定
- amount > 0、短期限、destination不変、deep-link allowlist、state/nonce、replay protection
- appはJPYC EXの完了を自己申告せず、authoritative receiptとon-chain stateを照合
- incomplete/partial/timeoutはmanual reconciliationへ送る
- 本番credentialや個人情報をevidenceへ入れない

### 証拠

```text
delivery/evidence/jpyc/
delivery/evidence/jpyc-ex/
delivery/evidence/asset-registry/
```

### 合格条件

- exact contract/network/code identityをsigned registryへ固定
- partner契約、technical test、legal review、support procedureが対象release/regionへ結合
- old/prepaid asset、wrong network、proxy change、decimals changeをnegative testで拒否

---

## 14. Workstream I — zero-native-balance fee route

provider/paymaster/relayer/swap routeを採用する場合、marketing claimではなく次を契約・技術・runtimeの三層で証明してください。

- legal entity、provider ID、contact、terms version/hash、jurisdiction
- account model、network、token asset、settlement target
- zero-native-balance bootstrapが本当に成立するか
- operation-bound signed quote: account、operation ID、amount、nonce、expiry
- estimated fee、maximum fee、failure charge、fee asset cost
- reserve/budget、concurrency、rate limit、liquidity、revocation、kill switch
- failed action charge、reimbursement、duplicate reimbursement
- provider outage/abuse/support/escalation

generic quote、期限なしquote、caller binding欠落、fixed manual top-up amountは拒否します。verified routeがなければ、具体量を作らず「まだ送らない」manual fallbackにします。

証拠:

```text
delivery/evidence/fee-route/
```

---

## 15. Workstream J — ChatGPT/OpenAI境界

実行日時点でOpenAI公式Apps/Actions/Developer Terms/usage requirementsを再確認してください。OpenAI-facing surfaceは固定4操作のread-only contractから拡張しません。

- `readOnlyHint`等のtool annotationsを正確に設定
- write、open-world transaction、payload、signature、address、amount、asset/network、transaction-specific instructionを公開しない
- OpenAIへwallet raw utterance、transaction draft、balance/address、personal dataを送らない
- responseは固定用語、固定error、一般安全案内、中立handoffだけ
- CSP、OAuth/token scope、rate limit、prompt/tool injection test
- digital token/financial transactionに関するcurrent platform ruleと矛盾するsurfaceを作らない

OpenAI側は独立walletを実行する入口ではなく、非取引説明boundaryです。取引解析、confirmation、signing、broadcastは独立app/control planeだけで行います。

証拠:

```text
delivery/evidence/openai-boundary/
```

---

## 16. Workstream K — observability、SRE、DR

- metrics/log/traceをtransaction、signer、provider、ledger、reconciliation、attestation、kill switchへ実装
- address、authorization、token、secret、raw utterance、PIIのredaction test
- SLO、capacity、rate limit、DDoS/WAF、dependency outage
- backup encryption、restore、RTO/RPO、data integrity
- deployment rollback。ただしtrusted sequence/high-water markはrollbackしない
- kill switch、provider revoke、key compromise、data breach、store removal、market volatility drills
- on-call、escalation、customer support、complaint handling
- production dashboardとalert receiptをrelease evidenceへ結合

証拠:

```text
delivery/evidence/sre/
delivery/evidence/incident-drills/
delivery/evidence/backup-restore/
delivery/evidence/observability/
```

合格条件:

- restore後のledger/replay/high-water invariants PASS
- simulated outage中にsignerがfail closed
- critical alertsが担当者へ届き、ack/escalation evidenceがある

---

## 17. Workstream L — privacy、法務、地域、Store

資格ある外部専門家とexact legal entity ownerが実施してください。Codex自身の推測を法務証拠にしません。

### 書面判断のscope

- custody/non-custody model
- exchange、perpetual/derivatives、order routing、agent/API wallet
- JPYC/JPYC EX handoff、funds transfer、fiat/crypto boundaries
- KYC/AML/sanctions、travel rule該当性
- fee sponsorship/paymaster/relayer
- consumer disclosure、liquidation risk、marketing
- privacy、cross-border transfer、retention、breach、DSAR
- target countries/regions、geofence、age restrictions
- Apple/Google crypto/financial declarations
- support、complaint、dispute、account deletion

### 必要資料

- exact binary/container/config/policy digest
- data flow、asset flow、custody/key flow
- terms、privacy policy、risk disclosures、support URL
- permissions、privacy labels/data safety form
- target region listとgeofence test
- business registration/license/partner contract

### 証拠

```text
delivery/evidence/legal-store/
  counsel-opinion-redacted.pdf
  scope-and-release-binding.json
  apple-submission/
  google-play-submission/
  regional-approval-matrix.json
```

password、2FA、unredacted identity documentをrepositoryへ保存しないでください。

---

## 18. Workstream M — independent audits

実装担当・内部承認者と独立したreviewerを使い、少なくとも次を実施してください。

- mobile security: Android/iOS、attestation、deep link、overlay、root/jailbreak、storage
- backend/API/data/ledger/reconciliation
- signer/key custody/cryptography/canonicalization
- protocol: Hyperliquid、JPYC identity、fee route、bridge/swapを採用する場合はそのroute
- privacy/data governance
- supply chain/release process

scopeはexact source commit、artifact digest、config/policy/registryへ結合します。draft report、self-review、automated scanだけをindependent auditと呼ばないでください。

合格条件:

- unresolved critical/high = 0
- medium/lowはowner、deadline、risk acceptance、retest evidenceがある
- final reportがreviewer署名または検証可能なportal exportを持つ

---

## 19. Workstream N — evidence、trust anchors、readiness、runtime activation

### evidence statement

各claimについて、次を持つ署名済みstatementを作ります。

- claim ID
- exact release subject digest
- evidence artifact path/hash
- issuer role/principal/key ID
- issued/expiry
- environment/region/device/provider scope
- test command/result
- limitations
- signature profile/signature

### independent approval

approvalはstatement IDだけでなくstatement SHA-256へ結合します。issuerとreviewerのprincipal、role、keyを分離します。

### out-of-band anchors

package外の保護場所へ次を固定します。

- operational trust policy SHA-256
- readiness verifier bundle SHA-256
- runtime authorizer bundle SHA-256
- release subject SHA-256
- trusted-time signer/key
- evidence-index signer/key
- protected trusted-time/evidence/registry/runtime high-water marks

### readiness

37 gate・93 claimをexact setとして評価し、missing、duplicate、unknown、expired、revoked、wrong release、wrong scope、wrong signer、insufficient independent approvalをすべて拒否します。

### runtime activation

release GO後も、次を同一atomic signer decisionで確認します。

- exact release subject
- fresh trusted time
- fresh signed runtime state bundle
- 300秒以下のlease
- kill switch false
- deployment/config/policy/registry/provider/telemetry/ledger healthy
- account/device binding
- 120秒以下のsingle-use operation authorization
- exact capsule/quote/registry/RPC/final payload recomputation
- durable nonce reservation

---

## 20. 外部一次資料の再確認リスト

実行日ごとに、少なくとも次の公式domain/documentを再確認し、`release/SOURCE_PINS.json`へURL、取得時刻、version/commit、content SHA-256を保存してください。

- Hyperliquid official developer/API documentation
- `hyperliquid-dex` official SDK repository and exact commit/release
- JPYC official website and `jpycoin` official GitHub organization/contract list
- JPYC EX official service/partner documentation
- Japan Financial Services Agency official materials relevant to the exact service model
- Apple App Review Guidelines and App Attest documentation
- Google Play cryptocurrency/financial services and financial features declaration policies
- OpenAI official Apps/Actions documentation and Developer Terms
- adopted cloud/HSM/paymaster/relayer/provider official documentation and contract

sourceがJavaScript portalやPDFなら、official exportまたはcontent hashを保存し、third-party cacheを正本にしないでください。

---

## 21. 検証command

実装中はfast suiteとfull suiteを分けてもよいですが、release判定はclean environmentのfull suiteだけです。

```bash
set -euo pipefail

# baseline/reference
python3 -B tools/check_python_sources.py
python3 -B tools/test_python_unit_suite.py
python3 -B tools/run_local_sandbox.py self-test
python3 -B tools/test_validation_harness.py

# generated artifactsを明示的に準備
python3 -B tools/prepare_release_artifacts.py

# non-mutating validation
python3 -B tools/run_full_validation.py

# production profileではpackage外の保護anchorsを明示して実行
python3 -B tools/check_operational_readiness.py --require-go \
  --trust-policy /protected/operational-trust-policy.json \
  --trust-policy-sha256 "$ONE_INTENT_OPERATIONAL_TRUST_POLICY_SHA256" \
  --verifier-bundle-sha256 "$ONE_INTENT_READINESS_VERIFIER_BUNDLE_SHA256" \
  --release-subject /protected/release-subject.json \
  --release-subject-sha256 "$ONE_INTENT_RELEASE_SUBJECT_SHA256" \
  --trusted-time /protected/trusted-time-attestation.json \
  --trusted-time-high-water-mark /protected/trusted-time-high-water.json \
  --evidence-index-high-water-mark /protected/evidence-index-high-water.json

# runtime authorizerもprotected inputsでpositive/negative suiteを実行
python3 -B tools/test_runtime_authorization_positive.py
python3 -B tools/test_runtime_authorization_negative.py
```

実際のCLIが正本で変更された場合は、`--help`とcurrent sourceを確認して正しい引数へ更新し、command transcriptを証拠化してください。検証器を変更して失敗を隠すことは禁止です。検証器変更は別review、negative self-test、bundle hash更新、out-of-band anchor更新を必要とします。

---

## 22. Blocker記録形式

実行できない外部作業は、`release/UNRESOLVED_EXTERNAL_BLOCKERS.md`へ次のexact形式で追記してください。

```markdown
## BLOCKER-<連番> — <短い名称>

- status: BLOCKED
- affected gates/claims: <gate IDs / claim IDs>
- owner role: <個人名ではなく責任role。必要なら別の保護台帳で割当>
- independent reviewer role: <role>
- official service/portal: <名称と公式URL>
- required account/permission: <権限>
- exact navigation: <menu → page → button → field>
- required inputs/documents: <資料>
- irreversible or financial effect: <none / exact effect and limit>
- action to perform: <曖昧語なし>
- expected success result: <portal status、receipt、artifact>
- evidence destination: <delivery/evidence/...>
- evidence redaction: <除去する秘密/PII>
- revalidation command: `<command>`
- closes only when: <期限、scope、hash、review条件>
- current reason not executed: <credential/contract/device/human approval等>
```

「Apple対応」「法務確認」「API設定」のような抽象語だけは禁止です。

---

## 23. 最終成果物

権限内の作業をすべて実行した後、次を提出してください。

1. 新しいsource repository/commit/tag
2. Android signed artifactとhash、または明示blocker
3. iOS signed artifactとhash、または明示blocker
4. backend/signer/container/config/policy/registry artifactsとdigest
5. SBOM、provenance、source pins、artifact signatures
6. Testnet/live read-only/partner integration evidence
7. ledger/reconciliation/restore/incident drill reports
8. legal/store/audit evidenceまたは明示blocker
9. signed evidence indexとindependent approvals
10. readiness reportとruntime authorization negative/positive results
11. deterministic release ZIPとSHA-256
12. `release/CODEX_EXECUTION_REPORT.md`
13. `release/UNRESOLVED_EXTERNAL_BLOCKERS.md`
14. `release/OPERATIONAL_HANDOFF.md`

`CODEX_EXECUTION_REPORT.md`には、少なくとも次を含めます。

```text
baselineZipSha256=
baselineTreeSha256=
sourceCommit=
sourceTreeSha256=
androidArtifactSha256=
iosArtifactSha256=
backendImageDigest=
signerImageDigest=
configurationBundleSha256=
policyBundleSha256=
assetRegistrySha256=
sbomSha256=
unitTestsPassed=
fullValidationStatus=
mandatoryGates=
passedGates=
requiredClaims=
acceptedClaims=
operationalStatus=
productionWritePermitted=false
mainnetCanaryPerformed=<true|false>
unresolvedBlockerCount=
```

`productionWritePermitted`はreadiness report単体では常にfalseです。取引ごとのruntime/per-operation authorizationを省略してtrueにしないでください。

---

## 24. 最終判定

最終行は、次のどちらか一つだけにしてください。

```text
PRODUCTION_OPERATIONAL_GO
```

または

```text
BLOCKED_NOT_OPERATIONAL
```

`PRODUCTION_OPERATIONAL_GO`を出せるのは、37 gate・93 claimがexact release subjectへ結合され、期限内・非revokedの証拠と独立approvalを持ち、package外trust anchorsで検証され、native/backend/signer/protocol/legal/store/SREの対象scopeが一致し、clean independent environmentでreadiness `--require-go`がPASSした場合だけです。

一つでも未実装、未検証、期限切れ、scope mismatch、unresolved critical/high、ledger差分、rollback、secret exposure、Store/法務の必須blockerがあれば、正しい最終判定は`BLOCKED_NOT_OPERATIONAL`です。部分的に完成したworkstreamと、その時点で安全に利用できる非取引/Testnet範囲は、判定とは別に正確に報告してください。
