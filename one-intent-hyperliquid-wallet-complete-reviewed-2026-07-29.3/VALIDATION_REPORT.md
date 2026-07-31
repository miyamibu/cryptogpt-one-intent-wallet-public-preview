# Validation Report

**Package version:** 2026-07-29.3  
**Deterministic evidence timestamp:** 2026-07-29T00:00:00Z  
**Static／offline package result:** `PASS after full non-mutating pipeline`  
**Operational readiness:** `BLOCKED_NOT_OPERATIONAL`  
**Release eligible for runtime activation:** `false`  
**Direct production write permitted by this report:** `false`  
**Native release／Testnet／Mainnet:** `LOCAL_DEVICE_PROOF_ONLY / RELEASE_NOT_VERIFIED / BLOCKED`
**Recorded toolchain:** Playwright 1.57.0／Chromium 143.0.7499.4

## 正本コマンド

```bash
python -m pip install -r tools/requirements.txt
python -m pip install -r tools/requirements-visual.txt

# 明示的な派生物生成。packageを変更する唯一の正本工程。
python tools/prepare_release_artifacts.py

# packageを1バイトも変更しない完全検証。
python tools/run_full_validation.py

# 現在の設計packageが正しく停止していることを確認。
python tools/check_operational_readiness.py

# 再現可能な二重buildとclean-extract再検証。
python tools/build_release.py ../one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.3.zip
```

## Non-mutating full validation順序

```text
secure tree snapshot
  -> validator negative self-test
  -> all Python sources compiled in memory
  -> complete Python unittest suite
  -> loopback-only local sandbox HTTP self-test
  -> example hash --check
  -> prototype 288 cases and screenshots --check
  -> START_HERE 6 cases --check
  -> operational readiness report --check
  -> generated reports --check
  -> blocked readiness evaluation
  -> synthetic 37-gate/93-claim positive reachability test
  -> operational readiness negative tests
  -> blocked runtime authorization evaluation
  -> synthetic runtime authorization positive reachability test
  -> runtime authorization negative tests
  -> plain Japanese
  -> archive safety and secret hygiene
  -> local links and markup
  -> adversarial audit
  -> manifest/checksums --check
  -> package/schema/OpenAPI validation
  -> exact tree snapshot equality
```

検証中にscreenshot、report、hash、manifest、cache、timestampを更新しない。期待値が古ければ自動修復せず失敗する。

## 検査結果の規模

| 項目 | 値 |
|---|---:|
| 追跡対象 | 438ファイル |
| ZIP内予定 | 440ファイル |
| Known-Loophole | 436 |
| Security Invariants | 268 |
| Loophole regression | 97 |
| Validator self-test | 38 |
| JSON Schema | 35 |
| JSON examples | 22 |
| Operational gates | 37 |
| Required claims | 93 |
| Accepted claims | 0 |
| Browser visual cases | 288 |
| START_HERE cases | 6 |
| Screenshots | 10 |

## Browser prototype

対象寸法:

- iphone-se-stress: 320×568 (IOS)
- iphone-small: 375×667 (IOS)
- iphone-faceid: 390×844 (IOS)
- iphone-large: 430×932 (IOS)
- android-compact: 360×800 (ANDROID)
- pixel9a-logical: 412×915 (ANDROID)

主な検査:

- simulation-only境界と依頼原文の保持
- material voice ambiguityの本人確認完了まで実行無効
- light/dark、通常／大きな文字の全組合せ
- 横はみ出し、critical text clip、scroll/overflow ancestorによる実描画領域
- iOS 44pt／Android 48dp logical proxy、主操作54px
- 操作targetの重なり、中心点遮蔽、末尾到達
- focus-visible、text spacing、contrast proxy、forced colors
- ダミーaddress、画面例、初期値ではない制限値の表示
- compositeのDecimal算数、partial success、manual fallback

安定レビュー画像:

- `prototype/screenshots/iphone-perp-before-confirmation.png`
- `prototype/screenshots/iphone-perp-after-confirmation.png`
- `prototype/screenshots/pixel9a-fee-dark.png`
- `prototype/screenshots/iphone-large-withdraw.png`
- `prototype/screenshots/pixel9a-manual.png`
- `prototype/screenshots/iphone-limited-authorization.png`
- `prototype/screenshots/android-tall-partial-dark.png`
- `prototype/screenshots/iphone-jpyc-large.png`
- `prototype/screenshots/iphone-se-composite-top.png`
- `prototype/screenshots/android-compact-spot-large-dark.png`

## Operational readiness contract

現在の設計packageは次を厳密に返す。

```text
status=BLOCKED_NOT_OPERATIONAL
releaseEligibleForRuntimeActivation=false
productionWritePermitted=false
mandatoryGates=37
passedGates=0
requiredClaims=93
acceptedClaims=0
```

Production GOには、package外のtrust policy/checker/release subject/trusted time hash、署名済みevidence statements、独立review approvals、exact claim set、release subject bindingが必要である。release GOだけでは取引を許可せず、fresh runtime state、300秒以下のlease、120秒以下のsingle-use操作別本人承認を要求する。さらに、trusted-time／evidence-index／registry／runtime sequenceは保護high-water markを超え、Signerはcanonical quote、signed registry、実RPC chain ID、最終payloadを直前に再計算する。署名後の結果不明は再署名せず照合へ送る。

## Operationalization evidence binding

`delivery/evidence/operationalization/EXECUTION_EVIDENCE_BINDING_20260729.json`はcoverage 801行、37 gate、93 claimをID単位で展開する。現行のper-ID executable evidenceは0行、accepted gateは0件、accepted claimは0件で、ローカル／read-only証拠は本番承認へ昇格させない。

## PASSが証明しないもの

- Kotlin／ComposeとSwift／SwiftUIの本番実装、physical-device挙動
- live backend、database migration、outbox、ledger、Signer、HSM/MPC
- JPYC EX、fee provider、bridge、Hyperliquidのproduction挙動
- Testnet／Mainnet write、fill、finality、liquidation、reconciliation
- external security audit、法務意見、Apple／Google承認
- 未知の脆弱性が存在しないこと、資金損失が起きないこと

したがって、現在の唯一の正しい運用判定は`BLOCKED_NOT_OPERATIONAL`である。
