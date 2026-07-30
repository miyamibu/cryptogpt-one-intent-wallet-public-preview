# 最終監査報告 — 2026-07-29.3

> この報告は `tools/generate_reports.py` が検証証跡、登録簿、operational readiness reportから決定論的に生成する。件数を手入力しない。

## 最終判定

```text
status=BLOCKED_NOT_OPERATIONAL
releaseEligibleForRuntimeActivation=false
productionWritePermitted=false
mandatoryGates=37
passedGates=0
requiredClaims=93
acceptedClaims=0
```

このZIPへ高い信頼を置ける範囲は、設計、Schema、API契約、ChatGPT read-only境界、完全オフライン画面見本、敵対的回帰、非破壊検証、再現可能archive、運用証拠契約、Codexへの引継ぎである。今回、Androidのunsigned release APK/AAB build、debug-signed Pixel 9a local UI proofと、Team `PUBLICTEAM`のiPhone 12 signed debug／Appium-WDA local UI proofを別スコープで結合したが、実資金を動かすAndroid／iOS release binary、本番backend、Signer、JPYC EX本番連携、手数料提供者、Hyperliquid Testnet／Mainnet write、外部監査、法務、Store承認は収録していない。801 coverage rowsはper-ID executable evidence未結合、37 gate／93 claimは未承認であり、対応状態は`delivery/evidence/operationalization/EXECUTION_EVIDENCE_BINDING_20260729.json`に固定した。

現在の正しい判定は`BLOCKED_NOT_OPERATIONAL`である。文字どおりの100%安全や未知の脆弱性がないことは主張しない。将来の`PRODUCTION_OPERATIONAL_GO`は、exact release subjectへ結合された37 gate・93 claimがすべて有効であることだけを意味し、取引承認そのものではない。

## 今回ふさいだ運用判定の重大な穴

1. 検証工程が証拠、報告、hash、manifestを書き換える自己正当化経路を閉じた。生成は`prepare_release_artifacts.py`、検証は`--check`とtree前後一致へ分離した。
2. package内のtrust policy・gate profile・Schema・checkerを同時改ざんする攻撃に備え、検証器bundle全体とtrust policy、release subject、trusted timeのhashをpackage外へ固定する契約を追加した。
3. evidence statement、review approval、evidence indexを署名し、approvalをstatementIdだけでなくstatement SHA-256へ結合し、issuer／reviewer／index/time signerの鍵・principal・roleを分離した。
4. 証拠をsource、Android、iOS、backend、signer、configuration、policy、registry、SBOMのexact digestへ結合した。
5. 欠落、重複、未知、期限切れ、revoked、別release、相互矛盾をすべてfail closedにした。
6. release readinessとruntime activationとsingle-use操作別本人承認を分離した。release reportとruntime leaseはいずれも取引を承認しない。
7. kill switch、stale lease、queue済み操作、deployment epoch、provider／telemetry／ledger状態をsigner直前に再確認する要件を追加した。
8. Android／iOSのoverlay、root/jailbreak、hook、deep link、clipboard、backup、privacy snapshotを実機gateへ追加した。
9. DB migration、transactional outbox、double-entry ledger、append-only audit、restore drillを運用gateへ追加した。
10. token proxy／decimals／allowance、bridge finality、Hyperliquid nonce／WebSocket gap／asset ID／partial fillをprotocol gateへ追加した。
11. AI model update、indirect prompt injection、data minimization、ChatGPT read-only境界をproduction gateへ追加した。
12. 法務意見とApple／Google審査を対象法人、地域、機能、binaryへ結合する外部証拠にした。
13. `--check`が正本screenshotを削除する経路とvalidator import失敗を見逃す経路を閉じ、isolated copyで各stepの前後を比較するようにした。
14. trusted-time sequenceとevidence-index sequenceをpackage外の保護high-water markより必ず大きくし、readiness reportとruntime時刻のsequence一致も要求した。
15. canonical quote本文、signed registry entry、CAIP-2／numeric／RPC chain ID、最終payload commitmentをSignerが再計算して完全一致させる契約を追加した。
16. 署名後にbroadcast結果が不明な状態を`SIGNED_BROADCAST_UNKNOWN`として固定し、照合なしの再署名・再送を禁止した。

## 多視点の最終レビュー

| 視点 | 収録範囲で確認したこと | 運用GOまでに必要な実証 |
|---|---|---|
| 初心者 | やさしい日本語、原文と解釈、固定額を出さない復旧 | 初心者task successとrisk理解度 |
| 経験者 | 方向、期限、上限、清算情報のfreshness表示 | live account、fill、margin、funding、liquidation照合 |
| デザイナー | 情報階層、末尾CTA、明暗、大文字、狭幅 | SwiftUI／Composeと実機OSフォント |
| 1px QA | clip、重なり、中心点遮蔽、上下到達性 | IME、safe area、回転、VoiceOver／TalkBack実機 |
| Mobile security | fail-closed要件とattestation schema | root/jailbreak/overlay/hook/deep-link negative test |
| Backend／Signer | capsule binding、冪等性、証拠契約 | outbox、ledger、HSM/MPC、key ceremony、independent audit |
| Protocol | registry、quote、fee readiness、manual fallback | JPYC/bridge/Hyperliquid live/Testnet/Mainnet canary evidence |
| SRE／管理者 | kill switch、role分離、復旧・照合の仕様 | outage、restore、key compromise、break-glass drill |
| 法務／Store | 技術GOと公開GOの分離 | release-bound legal opinionとportal approval |
| 供給網攻撃者 | strict archive、secret scan、double build | native/service hermetic build、SBOM、SLSA、managed signing |

## 自動検査の有限な証拠

| 項目 | 証拠 |
|---|---:|
| manifest追跡対象 | 429ファイル |
| ZIP内の総ファイル予定 | 431ファイル |
| 登録済み抜け穴 | 436件 |
| Security Invariants | 268件、連番 |
| 敵対的な抜け穴回帰 | 97件 |
| validator self-test | 38 assertions |
| やさしい日本語辞書 | 20項目 |
| 音声／copyケース | 8件 |
| JSON Schema | 35件 |
| JSON例 | 22件 |
| operational gates | 37件 |
| operational claims | 93件 |
| accepted production claims | 0件 |
| prototype画面検査 | 288条件 |
| START_HERE検査 | 6条件 |
| 安定レビュー画像 | 10枚 |
| 実行locale | ja-JP |
| 収録browser検査の外部通信 | 0 |

## 運用GOへ残る主なblocker

- production Android／iOS source、signed AAB/APK/archive/IPAと実機matrix
- live backend、取引Intent Parser、任意の非取引Support Gateway、Reconciler、registry、fee route、policy-enforcing Signer
- HSM/MPC、鍵儀式、復旧、release signing、out-of-band trust anchors
- JPYC公式release pin、JPYC EX契約、production credential、end-to-end evidence
- zero-native-balance provider／route、監査、abuse、reserve、canary
- Hyperliquid Testnet lifecycle、bounded Mainnet canary、zero-difference reconciliation
- independent mobile/backend/protocol/cryptography auditでcritical/high 0
- 法務、Apple、Google、provider契約をexact releaseへ結合した証拠
- kill switch、backup restore、provider outage、key compromise、data breachの実地訓練

機能・安全要件の正本は`codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md`、外部環境で資格・実機・HSM／MPC・Testnet・法務・Store・監査を実行する契約は`codex/CODEX_EXTERNAL_OPERATIONALIZATION_PROMPT_2026-07-29.md`である。外部作業を捏造せず、`delivery/EXTERNAL_BLOCKERS.md`へ担当role、portal、menu、button、field、資料、callback、証拠path、再試験command、閉じるgateを残す。
