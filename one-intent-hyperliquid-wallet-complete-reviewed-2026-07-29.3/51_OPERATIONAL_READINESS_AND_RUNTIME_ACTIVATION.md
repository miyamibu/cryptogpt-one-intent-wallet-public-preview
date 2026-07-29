# Operational Readiness and Runtime Activation

**版:** 2026-07-29.3  
**現在の機械判定:** `BLOCKED_NOT_OPERATIONAL`  
**将来の唯一の本番GO名:** `PRODUCTION_OPERATIONAL_GO`

## 1. この文書が閉じる誤解

このZIPの設計、Schema、オフライン画面、検証ツールがPASSしても、それだけで実資金を扱えるわけではない。運用可能という判定には、次の三層がすべて必要である。

1. **Release readiness** — 対象binary、backend、signer、configuration、policy、asset registry、SBOMへ結合された37 gate・93 claimの証拠。
2. **Runtime activation** — その時点の障害、停止スイッチ、provider、registry、時刻、deployment epochを反映した短期限の稼働許可。
3. **Per-operation authorization** — 利用者が最終的な送金・注文内容を確認した、操作ごとのsingle-use承認。

Release readinessがGOでも、runtime activationまたは操作別承認がなければsign／broadcastしてはならない。runtime leaseは利用者の取引承認ではない。

## 2. 現在のpackage状態

`delivery/OPERATIONAL_READINESS_REPORT.json`は次を正本とする。

```text
status: BLOCKED_NOT_OPERATIONAL
productionWritePermitted: false
mandatoryGates: 37
passedGates: 0
requiredClaims: 93
acceptedClaims: 0
```

これは失敗ではなく、Android／iOS本番binary、本番backend、signer、外部監査、法務意見、Store承認、Testnet／Mainnet証拠を収録していない設計packageに対する正しいfail-closed判定である。

## 3. Release subjectへの厳密な結合

本番証拠は、少なくとも次のsubject fieldへ結合する。

- source commitとsource tree SHA-256
- Android artifact SHA-256
- iOS artifact SHA-256
- backend image digest
- signer image digest
- configuration bundle SHA-256
- policy bundle SHA-256
- asset registry SHA-256
- SBOM SHA-256
- release IDとenvironment

一つでも別なら証拠を流用しない。スクリーンショット、口頭承認、ファイル名だけではsubject bindingの証拠にならない。

## 4. package外の信頼根

攻撃者がpackageと検証器を同時に書き換える場合に備え、次のhashをpackage外の保護された設定へ固定する。

- `ONE_INTENT_TRUST_POLICY_SHA256`
- `ONE_INTENT_READINESS_CHECKER_SHA256`
- `ONE_INTENT_RELEASE_SUBJECT_SHA256`
- `ONE_INTENT_TRUSTED_TIME_ATTESTATION_SHA256`

package内のtrust policy、公開鍵、checker、時刻証明が存在するだけでは信頼しない。out-of-band anchorとexact一致しなければ本番GOを生成しない。

## 5. 証拠と承認

各claimは以下を満たす。

- canonical payloadへの承認済み署名
- issuer roleとreviewer roleの分離
- policyで要求されたapproval threshold
- distinct key条件
- key validity、revocation、not-before、not-after
- claim固有の最大有効日数
- artifact hash、size、media type
- exact release subject
- evidence indexの署名
- required claim集合との完全一致

欠落、重複、未知claim、解析不能、相互矛盾はすべて`BLOCK`である。

## 6. 37 gateの範囲

37 gateは次を含む。

- 製品範囲と要求追跡
- Android、iOS、backend、共有決定論コア
- 認証、復旧、端末attestation、鍵保管、signer
- transaction authorization、asset registry、JPYC、Hyperliquid
- 清算リスク、手数料準備、交換・別network移動
- ledger、照合、失敗復旧
- AI、ChatGPT read-only境界、日本語UX、アクセシビリティ
- privacy、管理変更、SRE、供給網、外部security assessment
- 日本法務、Apple、Google、provider契約
- Testnet、極小Mainnet canary、incident drill、利用者受入
- 独立release approval、runtime activation、launch後監視

詳細な93 claimは`config/operational-readiness.json`を正本とする。文書の要約と構成ファイルが食い違う場合は、validatorが失敗する。

## 7. Runtime activation

本番writeの直前に、少なくとも次を要求する。

- 署名済みtrusted time
- freshでsequence付きのruntime state bundle
- kill switchが無効
- provider、registry、policy、deployment epochが健康
- 300秒以下の短期限control-plane lease
- 120秒以下の操作別本人承認
- 最終Execution Capsule hashとのexact一致
- nonce未使用、device proof一致
- signerによる直前の再検証

古いlease、古いstate、停止後のqueue、別端末、別宛先、別金額、別quote、別chain、別assetは拒否する。

## 8. 運用中の失効

`PRODUCTION_OPERATIONAL_GO`は永久資格ではない。証拠期限、鍵失効、protocol／法務／Store条件の変更、provider事故、監視stale、照合差異、未解決critical/high、kill switch発動で自動的に`BLOCKED_NOT_OPERATIONAL`へ戻す。

## 9. 正本コマンド

派生物を生成する明示工程:

```bash
python tools/prepare_release_artifacts.py
```

packageを1バイトも変更しない検証:

```bash
python tools/run_full_validation.py
```

現在の設計packageが正しく停止していることの確認:

```bash
python tools/check_operational_readiness.py
```

本番証拠がすべて揃ったreleaseでだけ使用する判定:

```bash
python tools/check_operational_readiness.py --require-go \
  --trust-policy /protected/operational-trust-policy.json \
  --evidence-index delivery/evidence-index.json
```

環境変数のout-of-band anchorを含め、すべての条件が一致しなければ終了コード0にしない。
