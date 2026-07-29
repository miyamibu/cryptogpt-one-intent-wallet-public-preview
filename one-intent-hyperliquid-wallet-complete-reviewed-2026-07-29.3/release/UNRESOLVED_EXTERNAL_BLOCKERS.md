# Unresolved External Blockers — 2026-07-29.3

status=BLOCKED_EXTERNAL
productionWritePermitted=false
releaseEvidenceStatus=NOT_RELEASE_EVIDENCE

The following items cannot be completed from an offline design package:

| blocker | owner/authority | missing evidence | closes |
|---|---|---|---|
| native Android build | Android release owner / Android SDK portal | release signing, signed APK/AAB, instrumentation, compact/recent device matrix and release-bound evidence | ANDROID_BUILD |
| native iOS release | Apple release owner / Apple Developer portal | archive/IPA, distribution signing, App Store provisioning, full physical-device matrix and release-bound evidence | IOS_BUILD |
| custody and signer | Security owner / HSM-MPC provider | real key ceremony, rotation, revocation, recovery, break-glass and independent audit | SIGNER_CUSTODY |
| backend and ledger | Backend/SRE owner | deployed auth, DB migration, outbox, double-entry ledger, reconciliation and restore drill | BACKEND_OPERATIONAL |
| protocol/provider | Protocol and provider owners | official source pins, JPYC/fee route contract, Hyperliquid Testnet lifecycle and reconciliation | PROTOCOL_LIVE |
| legal/store | Legal counsel / Apple / Google | jurisdictional opinion, provider contracts, app review and store approval | LEGAL_STORE |
| operations | SRE and security owners | monitoring, on-call, incident/key-compromise/kill-switch drills | OPERATIONS |
| independent assurance | independent security/mobile/protocol reviewers | critical/high findings closed and exact release subject approval | INDEPENDENT_GO |

Each blocker requires owner, portal, evidence path, callback, retest command and gate decision in the external operationalization contract. No blocker is closed by this file's existence.
