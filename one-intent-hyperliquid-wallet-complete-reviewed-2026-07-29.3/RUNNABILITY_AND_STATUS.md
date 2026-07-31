# 実行可能範囲と現在の状態

**版:** 2026-07-29.3  
**ZIP内ローカル運用:** `LOCAL_SANDBOX_OPERATIONAL_GO`  
**本番の機械判定:** `BLOCKED_NOT_OPERATIONAL`  
**本番GOとして許可する唯一の名称:** `PRODUCTION_OPERATIONAL_GO`

## 結論

このZIPは、loopback限定の非取引ローカルサンドボックスとして起動でき、設計、Schema、API契約、完全オフライン画面見本、敵対的レビュー、非破壊検証、運用証拠契約、Codex引継ぎに利用できる。Kotlin／Swiftの本番アプリ、live backend、Signer、実資金接続、外部監査、法務・Store承認は含まれないため、**本番運用はまだ可能ではない**。

`delivery/OPERATIONAL_READINESS_REPORT.json`は、37の必須gateと93のclaimを0件承認として正しく停止する。

## 今すぐ確認できるもの

1. `python3 -B tools/run_local_sandbox.py self-test`を実行する。
2. `python3 -B tools/run_local_sandbox.py serve`を実行し、`http://127.0.0.1:8765/`を開く。
3. 12種類の画面をiPhone／Android表示、通常／大きな文字、明／暗で操作する。
4. `python3 -B tools/run_full_validation.py`で、packageを変更せずに全検査を実行する。
5. `python3 -B tools/check_operational_readiness.py`で、現在の状態が`BLOCKED_NOT_OPERATIONAL`であることを確認する。
6. 機能仕様として`codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md`、外部運用化・証拠取得として`codex/CODEX_EXTERNAL_OPERATIONALIZATION_PROMPT_2026-07-29.md`をCodexへ渡す。

派生証拠を更新する場合だけ、検証とは別に次を実行する。

```bash
python3 -B tools/prepare_release_artifacts.py
```

## 収録済み

- loopback以外へbindできず、Host／Origin／Sec-Fetch-Site不一致、request smuggling系header、圧縮request、未知のwrite routeを拒否するローカルHTTPサンドボックス
- やさしい日本語を優先した12画面の完全オフライン見本
- 先物の清算価格、口座方式、取得時刻、取得不能時停止の表示仕様
- 音声原文と解釈を並べ、重要な誤変換を本人確認するhard gate
- JPYC-only／native fee 0、operation-bound fee quote、固定量なしの手動復旧
- 期限、資産、network、宛先、金額、倍率、費用を限定するStanding Authorization
- canonical JSON／Decimalの入力資源制限、厳密型検証、循環・無効Unicode・prefix bypass拒否
- nonceのdurable一意制約、署名後未確定状態の再署名禁止、厳密なSaga遷移
- 複合操作の十進算数、部分成功、冪等性、残りだけの再構築
- 6 viewport×12 flow×2文字モード×2テーマ＝288条件のbrowser logical-pixel検査
- 10枚の安定スクリーンショット
- 436件の既知抜け穴、268件のSecurity Invariants、97件の敵対的回帰ケース
- 62件のPython単体テストと全Python sourceの構文検査をrelease gateへ組み込んだ検証基盤
- 37 gate・93 claimのoperational readiness profile
- 署名済み証拠、独立review、trusted time、out-of-band trust anchorsの契約
- release readiness、runtime lease、操作別本人承認を分離するSchemaとnegative test
- trusted-time／evidence-index sequenceのrollbackを拒否するhigh-water contract
- canonical quote、signed registry、CAIP-2／RPC chain ID、最終payload commitmentのSigner直前照合
- `SIGNED_BROADCAST_UNKNOWN`からの無条件再署名・再送を拒否するatomic state contract
- Android／iOS／backend／Signer／Testnet／Mainnet canaryの機能仕様と、外部環境で証拠を取得するCodex実行契約

## 収録していないもの

- Kotlin／Jetpack Composeの完成実装とsigned APK/AAB
- Swift／SwiftUIの完成実装とsigned archive/IPA
- 本番Control API、取引Intent Parser、任意の非取引Support Gateway、Reconciler、Signer、MPC/HSM
- JPYC EX本番契約、資格情報、審査、発行／償還の実動作
- 本番sponsor/paymaster/relayerまたは監査済みfee swap route
- Hyperliquid Testnet/Mainnetのrequest、fill、position、reconciliation証拠
- 実機safe area、IME、VoiceOver、TalkBack、生体認証、attestation証拠
- 独立mobile/backend/protocol/cryptography監査
- 日本その他の地域別法務意見、Apple／Googleのsubmission/approval
- 本番監視、backup restore、kill switch、key compromiseの実地訓練

## 正式な判定

```text
BLOCKED_NOT_OPERATIONAL
productionWritePermitted=false
mandatoryGates=37
passedGates=0
requiredClaims=93
acceptedClaims=0
```

現在の段階別判定は次の10個を正本とする。

```text
DESIGN_GO
OFFLINE_PROTOTYPE_GO
CODEX_IMPLEMENTATION_GO
ANDROID_RELEASE_SIGNING_NO_GO
IOS_DISTRIBUTION_ARCHIVE_NO_GO
TESTNET_WRITE_NO_GO
PERSONAL_SMALL_MAINNET_NO_GO
CLOSED_ALPHA_NO_GO
PUBLIC_ANDROID_STORE_NO_GO
PUBLIC_IOS_APP_STORE_NO_GO
```

将来`PRODUCTION_OPERATIONAL_GO`を得ても、それだけで一操作を実行してはならない。freshなruntime state、300秒以下のservice lease、120秒以下のsingle-use操作別本人承認、signer直前再検証が必要である。

詳細は次を参照する。

- `51_OPERATIONAL_READINESS_AND_RUNTIME_ACTIVATION.md`
- `52_FINAL_OPERATIONAL_GAP_REVIEW.md`
- `53_CODEX_OPERATIONAL_COMPLETION_CONTRACT.md`
- `CODEX_START_HERE.md`
