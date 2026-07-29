#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from artifact_io import text_bytes, write_or_check
from canonical_hashes import strict_load_json
from package_metadata import ROOT, load_package_metadata
from test_validation_harness import EXPECTED_ASSERTIONS

METADATA = load_package_metadata()
EXCLUDED_FROM_MANIFEST = {"manifest.json", "SHA256SUMS.txt"}


def load_json(rel: str) -> dict:
    return strict_load_json(ROOT / rel)


def tracked_files() -> list[Path]:
    return sorted(
        p
        for p in ROOT.rglob("*")
        if p.is_file()
        and p.relative_to(ROOT).as_posix() not in EXCLUDED_FROM_MANIFEST
        and "__pycache__" not in p.parts
        and p.suffix != ".pyc"
    )


def metrics() -> dict[str, object]:
    visual = load_json("tests/prototype-visual-evidence.json")
    entry = load_json("tests/start-here-layout-evidence.json")
    terms = load_json("config/user-facing-terms.ja.json")
    copy_cases = load_json("tests/plain-japanese-copy-cases.json")
    regression_cases = load_json("tests/loophole-regression-cases.json")
    readiness = load_json("delivery/OPERATIONAL_READINESS_REPORT.json")
    readiness_profile = load_json("config/operational-readiness.json")
    loophole_text = (ROOT / "24_KNOWN_LOOPHOLE_REGISTER.md").read_text(encoding="utf-8")
    loophole_ids = re.findall(r"^\|\s*([A-Z][A-Z0-9-]*-\d{3})\s*\|", loophole_text, re.MULTILINE)
    invariant_text = (ROOT / "25_SECURITY_INVARIANTS.md").read_text(encoding="utf-8")
    invariant_numbers = [int(x) for x in re.findall(r"^(\d+)\.\s", invariant_text, re.MULTILINE)]
    return {
        "tracked": len(tracked_files()),
        "archive_total": len(tracked_files()) + 2,
        "loopholes": len(loophole_ids),
        "invariants": len(invariant_numbers),
        "terms": len(terms.get("entries", [])),
        "copy_cases": len(copy_cases.get("cases", [])),
        "regression_cases": len(regression_cases.get("cases", [])),
        "schemas": len(list((ROOT / "schemas").glob("*.json"))),
        "examples": len(list((ROOT / "examples").glob("*.json"))),
        "visual": visual,
        "entry": entry,
        "readiness": readiness,
        "readiness_profile": readiness_profile,
        "validator_selftest_assertions": EXPECTED_ASSERTIONS,
    }


def write_final_audit(m: dict[str, object], *, check: bool) -> None:
    v = m["visual"]
    e = m["entry"]
    r = m["readiness"]
    s = r["summary"]
    text = f"""# 最終監査報告 — {METADATA.version}

> この報告は `tools/generate_reports.py` が検証証跡、登録簿、operational readiness reportから決定論的に生成する。件数を手入力しない。

## 最終判定

```text
status={r['status']}
releaseEligibleForRuntimeActivation={str(r['releaseEligibleForRuntimeActivation']).lower()}
productionWritePermitted={str(r['productionWritePermitted']).lower()}
mandatoryGates={s['mandatoryGates']}
passedGates={s['passedGates']}
requiredClaims={s['requiredClaims']}
acceptedClaims={s['acceptedClaims']}
```

このZIPへ高い信頼を置ける範囲は、設計、Schema、API契約、ChatGPT read-only境界、完全オフライン画面見本、敵対的回帰、非破壊検証、再現可能archive、運用証拠契約、Codexへの引継ぎである。今回、Androidのunsigned release APK/AAB build、debug-signed Pixel 9a local UI proofと、Team `8R3B5675ZJ`のiPhone 12 signed debug／Appium-WDA local UI proofを別スコープで結合したが、実資金を動かすAndroid／iOS release binary、本番backend、Signer、JPYC EX本番連携、手数料提供者、Hyperliquid Testnet／Mainnet write、外部監査、法務、Store承認は収録していない。801 coverage rowsはper-ID executable evidence未結合、37 gate／93 claimは未承認であり、対応状態は`delivery/evidence/operationalization/EXECUTION_EVIDENCE_BINDING_20260729.json`に固定した。

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
| manifest追跡対象 | {m['tracked']}ファイル |
| ZIP内の総ファイル予定 | {m['archive_total']}ファイル |
| 登録済み抜け穴 | {m['loopholes']}件 |
| Security Invariants | {m['invariants']}件、連番 |
| 敵対的な抜け穴回帰 | {m['regression_cases']}件 |
| validator self-test | {m['validator_selftest_assertions']} assertions |
| やさしい日本語辞書 | {m['terms']}項目 |
| 音声／copyケース | {m['copy_cases']}件 |
| JSON Schema | {m['schemas']}件 |
| JSON例 | {m['examples']}件 |
| operational gates | {s['mandatoryGates']}件 |
| operational claims | {s['requiredClaims']}件 |
| accepted production claims | {s['acceptedClaims']}件 |
| prototype画面検査 | {v['geometryAndContrastCases']}条件 |
| START_HERE検査 | {len(e['cases'])}条件 |
| 安定レビュー画像 | {len(v['screenshots'])}枚 |
| 実行locale | {', '.join(v['localeExecuted'])} |
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
"""
    write_or_check(ROOT / "FINAL_AUDIT_REPORT.md", text_bytes(text), check=check, label="FINAL_AUDIT_REPORT.md")


def write_validation_report(m: dict[str, object], *, check: bool) -> None:
    v = m["visual"]
    e = m["entry"]
    r = m["readiness"]
    s = r["summary"]
    screenshots = "\n".join(f"- `{path}`" for path in v["screenshots"])
    viewports = "\n".join(f"- {x['id']}: {x['width']}×{x['height']} ({x['platform']})" for x in v["viewports"])
    text = f"""# Validation Report

**Package version:** {METADATA.version}  
**Deterministic evidence timestamp:** {v['generatedAt']}  
**Static／offline package result:** `PASS after full non-mutating pipeline`  
**Operational readiness:** `{r['status']}`  
**Release eligible for runtime activation:** `{str(r['releaseEligibleForRuntimeActivation']).lower()}`  
**Direct production write permitted by this report:** `{str(r['productionWritePermitted']).lower()}`  
**Native release／Testnet／Mainnet:** `LOCAL_DEVICE_PROOF_ONLY / RELEASE_NOT_VERIFIED / BLOCKED`
**Recorded toolchain:** Playwright {v['toolchain']['playwrightPython']}／Chromium {v['toolchain']['browser']}

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
python tools/build_release.py ../{METADATA.root_name}.zip
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
| 追跡対象 | {m['tracked']}ファイル |
| ZIP内予定 | {m['archive_total']}ファイル |
| Known-Loophole | {m['loopholes']} |
| Security Invariants | {m['invariants']} |
| Loophole regression | {m['regression_cases']} |
| Validator self-test | {m['validator_selftest_assertions']} |
| JSON Schema | {m['schemas']} |
| JSON examples | {m['examples']} |
| Operational gates | {s['mandatoryGates']} |
| Required claims | {s['requiredClaims']} |
| Accepted claims | {s['acceptedClaims']} |
| Browser visual cases | {v['geometryAndContrastCases']} |
| START_HERE cases | {len(e['cases'])} |
| Screenshots | {len(v['screenshots'])} |

## Browser prototype

対象寸法:

{viewports}

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

{screenshots}

## Operational readiness contract

現在の設計packageは次を厳密に返す。

```text
status={r['status']}
releaseEligibleForRuntimeActivation={str(r['releaseEligibleForRuntimeActivation']).lower()}
productionWritePermitted={str(r['productionWritePermitted']).lower()}
mandatoryGates={s['mandatoryGates']}
passedGates={s['passedGates']}
requiredClaims={s['requiredClaims']}
acceptedClaims={s['acceptedClaims']}
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
"""
    write_or_check(ROOT / "VALIDATION_REPORT.md", text_bytes(text), check=check, label="VALIDATION_REPORT.md")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or verify generated audit reports.")
    parser.add_argument("--check", action="store_true", help="compare reports and do not modify the package")
    args = parser.parse_args()
    m = metrics()
    write_final_audit(m, check=args.check)
    write_validation_report(m, check=args.check)
    print(("VERIFIED" if args.check else "GENERATED") + " FINAL_AUDIT_REPORT.md AND VALIDATION_REPORT.md")
    print(f"Tracked files before manifest: {m['tracked']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
