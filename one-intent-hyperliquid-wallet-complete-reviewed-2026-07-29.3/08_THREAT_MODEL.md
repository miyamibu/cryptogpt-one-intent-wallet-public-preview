# 脅威モデル

## 保護対象

- root wallet資産
- trade account資産
- API Wallet
- root signer share
- recovery share
- Address Book
- Policy Profile
- Execution Capsule
- audit evidence
- user identity
- model input／output
- contract allowlist
- feature gates
- trusted prompt text／authorization evidence
- state evidence／source independence
- Google Play release evidence

## 攻撃者

1. 悪意あるWebコンテンツ
2. prompt injection
3. モデルの誤解・幻覚
4. 端末マルウェア
5. accessibility abuse／overlay
6. 改変アプリ
7. clipboard hijacker
8. SIM／account takeover
9. backend侵害者
10. signer service侵害者
11. insider
12. MPC vendor
13. supply-chain attacker
14. malicious dependency
15. compromised Hyperliquid agent
16. malicious Vault／Bridge
17. contract admin compromise
18. oracle／market manipulation
19. network／DNS attacker
20. social engineering／support impersonator
21. compromised or stale API server
22. malicious app-store clone／distribution pipeline
23. agent-key thief operating outside product signer
24. compromised device UI that lies about transaction semantics

## STRIDE＋金融固有脅威

| ID | 脅威 | 影響 | 必須対策 |
|---|---|---|---|
| T01 | AIが質問を注文と誤認 | 無断注文 | intent state、具体ボタン |
| T02 | prompt injectionが宛先を差替え | 資産損失 | LLMはaddressを解決しない |
| T03 | UIとpayload不一致 | 資産損失 | semanticHash、signer再検証 |
| T04 | agent key漏えい | 不正取引 | asset隔離、kill switch、agent失効 |
| T05 | root share漏えい | 送金・出金 | threshold／wallet confirmation |
| T06 | backend＋signer共謀 | 全資産 | independent user factor／recovery |
| T07 | nonce replay | 二重実行 | atomic nonce、agent address再利用禁止 |
| T08 | timeout blind retry | 二重注文 | cloid／state reconcile |
| T09 | stale price | 想定外slippage | state version、drift threshold |
| T10 | address poisoning | 誤送金 | source、full address、new destination gate |
| T11 | fake token | 無価値資産 | canonical token registry |
| T12 | malicious contract upgrade | 資産奪取 | bytecode/proxy monitor、gate stop |
| T13 | unlimited allowance | 将来流出 | exact allowance、revoke |
| T14 | Bridge paused | 資産滞留 | paused check、no execute |
| T15 | partial Saga | 不整合 | step ledger、recovery UI |
| T16 | model drift | 誤解率増加 | snapshot pin、eval gate |
| T17 | log secret leakage | 鍵流出 | structured redaction、secret scanner |
| T18 | backup copies share | 鍵複製 | Auto Backup除外、restore test |
| T19 | biometric enrollment change | 認証乗っ取り | key invalidation／re-enrollment flow |
| T20 | Play Integrity false confidence | bypass | signal only、cryptographic control retained |
| T21 | admin lowers limits | insider theft | two-person approval、cooldown |
| T22 | recovery takeover | 全資産 | recovery proof、delay、notification |
| T23 | support scam | seed theft | in-app support identity、never ask seed |
| T24 | official-app impersonation | phishing | unofficial branding、certificate pin evidence |
| T25 | open interest/oracle shock | liquidation | risk display、max leverage、kill switch |
| T26 | agent key thief bypasses product policy | unauthorized L1 actions | bearer-key assumption、bounded account、revoke、characterization |
| T27 | BiometricPrompt authenticates wrong semantics | asset theft | R4と非例外R3はTrusted Display。R3 standing例外は事前ceremony＋hard cap |
| T28 | Protected Confirmation unavailable | unsafe downgrade | explicit fallback or NO_GO |
| T29 | trusted prompt omits destination/fee | user approves incomplete action | canonical prompt critical fields |
| T30 | single API lies/stales | bad price/state/status | independent state quorum |
| T31 | compiler and signer share same compromised source | common-mode failure | signer independent recheck |
| T32 | Testnet parity assumed | untested Mainnet/Bridge defect | environment-specific gates |
| T33 | Google Play declaration/review failure | distribution block/removal | store gate/evidence |
| T34 | long Saga crosses policy/source changes | unauthorized later step | per-step revalidation/max duration |
| T35 | dynamic remainder uses forged prior output | excessive transfer | chain-confirmed actual output＋hard bounds |

## 最悪ケース

### Case A: AI完全侵害

AIが任意の悪意あるDraftを返しても、Compiler／Policy／Card／user action／Signerの全境界を通らなければ実行できない。AIはアドレス、payload、署名APIにアクセスできない。

### Case B: Backend侵害

Backendだけではuser factorまたはdevice shareを満たせない設計を目標とする。Existing Wallet Modeではwallet confirmationが防御。Managed modeはMPC構成に依存するため監査必須。

### Case C: 端末侵害

完全な防御は不可能。被害を抑えるため、root actionのauth-per-use、remote feature stop、agent失効、別安全wallet、low limits、integrity signalを組み合わせる。

### Case D: Hyperliquid／Bridge障害

新規書き込み停止、read-only継続、状態照合、資産位置表示、公式status／docs確認。勝手な再送をしない。

## 残余リスク

- protocol insolvency／consensus
- zero-day
- sophisticated device compromise
- social engineering
- market gap
- oracle failure
- legal reinterpretation
- vendor outage
- recovery loss

残余リスクはゼロにできないため、資産上限と明示的なリスク表示が必要。

## Trusted Displayの限界

通常UIのCardと`renderReceiptHash`は重要だが、compromised UI processに対する完全なTrusted Displayではない。高リスクroot actionは、Android Protected Confirmation／外部wallet／hardware wallet等の独立表示経路を要求する。

## State sourceの限界

公式APIであっても、可用性・遅延・完全性を無条件に保証するものではない。重要操作は独立sourceと照合し、sourceが共通依存していないことを記録する。

## iOS／cross-platform threat additions

- App Attest replay／counter rollback
- unsupported device silent fallback
- reinstall／migrationによるdevice identity混乱
- Keychain同期／backup leakage
- biometric enrollment変更
- Universal Link／wallet callback hijack
- screen capture／background snapshot
- Swift／Kotlin／Rust canonicalization drift
- platform間risk tier drift
- App Store review／region control bypass

詳細は`mobile/IOS_SECURITY_REQUIREMENTS.md`と`24_KNOWN_LOOPHOLE_REGISTER.md`を参照する。
