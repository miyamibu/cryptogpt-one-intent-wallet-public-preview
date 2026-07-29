# Release Evidence Bundle Contract

各release candidateは次のdirectoryを生成する。

```text
evidence/<release-id>/
  release.json
  source-pins.json
  manifest.json
  sbom/
  builds/
    android/
    ios/
    backend/
  tests/
    unit/
    integration/
    conformance/
    device/
    visual/
    attack/
  security/
    findings.json
    audit-summary.pdf-or-reference
  legal/
    gate-status.json
  store/
    apple-status.json
    google-status.json
  operations/
    rollback-test.json
    recovery-drill.json
    incident-tabletop.json
  approvals/
    security.sig
    operations.sig
    legal.sig
```

## release.json required fields

- releaseId
- git commit
- source date epoch
- compiler versions
- schema versions
- app build numbers
- bundle／application IDs
- environment
- enabled feature gates
- supported regions
- signer policy version
- asset／contract／address registry versions
- test evidence digests
- unresolved findings
- expiry

## Signature rule

Mainnet write releaseは、security、operations、legalの独立署名が必要。署名者が同一人物でも役割を切り替えて一人で完了できる運用は禁止する。

## Evidence freshness

- market／contract source pins：release時点
- OS／Store policy：提出直前に再確認
- legal opinion：前提変更時に失効
- pentest：material architecture changeで失効
- device evidence：OS major upgradeで再実施


## 本ZIPのオフライン証跡

現在の設計パッケージでは、将来のproduction evidenceと混同しない次の有限な証跡を収録する。

- `tests/prototype-visual-evidence.json`: 6寸法×12flow×2文字設定×2theme、source hash、test harness hash、toolchain、locale、10画像、各画像の`TOP`／`BOTTOM_ACTION`取得状態、限界
- `tests/start-here-layout-evidence.json`: 320／390／1440幅×明暗、入口page source／harness hash、外部通信なし、限界
- `manifest.json`: 固定timestamp、file size、SHA-256
- `SHA256SUMS.txt`: manifestを含む全収録fileのSHA-256
- `config/build-metadata.json`: production claim禁止、Mainnet無効、再現可能timestamp

これらはnative build、Testnet、Mainnet、外部監査、法務、Store evidenceの代用品ではない。
