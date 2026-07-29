# Release Assurance Case

**版:** 2026-07-29.3  
**目的:** 「何に自信を持てるか」を、主張・証拠・反証条件へ分解する。

## 1. 許可される主張

| Claim ID | 主張 | 根拠 | 反証・失効条件 |
|---|---|---|---|
| AC-001 | ZIPは設計・Schema・API契約・オフライン画面見本・Codex指示を含む | manifest、SHA256SUMS、required-file validation | checksum不一致、欠落、symlink、secret-like file |
| AC-002 | オフライン画面見本は外部通信、署名、送金、取引を行わない | inline bundle test、request listener 0、forbidden API scan、watermark | `fetch`/WebSocket/wallet接続の追加、watermark削除 |
| AC-003 | 12画面を6 logical viewport、2文字モード、2テーマで検査した | `tests/prototype-visual-evidence.json`、source/test/browser hash | source/test/toolchain hash drift、evidence期限切れ |
| AC-004 | 音声の「生産価格」は勝手に確定せず、確認まで先物確認をblockする | source utterance保持、disabled state、live announcement test | hard gate削除、原文非表示 |
| AC-005 | 画面見本は依頼にない損切りを追加しない | flow data、domain consistency test、adversarial audit | UI/compilerが未依頼の条件を生成 |
| AC-006 | まとめ操作の表示算数は例示値の範囲で整合する | 948.50−300.00−1.00＝647.50の自動再計算 | 表示値の一部だけ変更、丸め規則drift |
| AC-007 | JPYC-only zero-gasは、開始能力の証明がなければ自動経路へ進まない設計 | fee flow、Schema、invariants、negative test requirement | provider/quote/operation bindingの省略、silent route fallback |
| AC-008 | ChatGPT／OpenAI側を固定の非取引supportだけへ限定する設計 | boundary docs、exact OpenAPI allowlist、固定handoff、Codex negative test | write tool、取引固有draft／manual steps、transaction payload、実行deep linkの追加 |
| AC-009 | Mainnet、Store公開、native build、Testnet writeはNO-GO | `PROJECT_STATUS.yaml`、GO/NO-GO matrix、validator | 証拠なしのgate変更 |

## 2. 禁止される主張

このパッケージを根拠に、次を言ってはならない。

- 「100%安全」
- 「資産を失わない」
- 「法的に必ず提供できる」
- 「App Store／Google Playへ必ず公開できる」
- 「Codexへ渡せば無人でMainnet productionになる」
- 「browser visual testがSwiftUI／Compose実機を証明した」
- 「清算価格は保証値」
- 「JPYCだけあれば、どのウォレットでも手数料なしで必ず送れる」

## 3. 証拠階層

1. **一次仕様:** Schema、OpenAPI、feature gate、security invariants
2. **決定論的例:** canonical hash、DAG、数値整合、negative fixtures
3. **実行証拠:** Playwright browser、toolchain/hash、screenshot
4. **内部監査:** loophole register、multi-perspective review、adversarial audit
5. **未取得の外部証拠:** native device、Testnet、external audit、legal/store approval

上位の内部証拠は、未取得の外部証拠を代替しない。

## 4. Confidence statement

- パッケージ内部整合: **HIGH, evidence-backed after clean-extract validation**
- オフライン画面見本のbrowser logical-pixel挙動: **HIGH within tested matrix**
- native mobile実装の正当性: **UNVERIFIED**
- Testnet互換性: **UNVERIFIED**
- Mainnet安全性: **UNVERIFIED / NO-GO**
- 法務・Store適格性: **UNVERIFIED / NO-GO**

「事実上100%」という表現を使う場合でも、その対象は**収録ファイルの同一性と、列挙した自動検査が同じ環境で再現すること**に限定する。未知の欠陥がないことを意味しない。

## 5. Release decision

```text
DESIGN_GO
OFFLINE_PROTOTYPE_GO
CODEX_IMPLEMENTATION_GO
ANDROID_BUILD_NO_GO
IOS_BUILD_NO_GO
TESTNET_WRITE_NO_GO
PERSONAL_SMALL_MAINNET_NO_GO
CLOSED_ALPHA_NO_GO
PUBLIC_ANDROID_STORE_NO_GO
PUBLIC_IOS_APP_STORE_NO_GO
```

## 6. Gate変更の条件

GOへ変える担当者は、最低でも次を提示する。

- artifact/build hash
- 実行コマンドと終了コード
- toolchain、OS、device model
- Testnet transaction/order/fill/receipt
- negative test evidence
- external security audit findings and closure
- legal/store written decision
- two-person signed gate change with expiry

証拠へのpathがない「確認済み」は証拠として扱わない。
## 2026-07-29.1 追加の独立監査

旧PASSを前提にせずvalidator自身を実行・破壊fixture・source reviewで再確認した。実際に、package identity drift、Markdown checkerのcompile failure、OAuth URLのfalse positive、visual skip、negative zero／巨大整数、YAML implicit type、host directory mode依存、ZIP timestamp表現差を発見した。各問題は実装修正、LR-025〜LR-032、Security Invariants 153〜160、validator self-testへ変換した。production／native／Testnet／MainnetのNO-GOは変更していない。


## Operational readinessの追加assurance

現在のpackageは`BLOCKED_NOT_OPERATIONAL`であり、`productionWritePermitted=false`である。`config/operational-readiness.json`の37 gate・93 claimが、exact production release subject、署名済み証拠、独立review、trusted time、out-of-band trust/checker/subject/time anchorsへ結合されるまで`PRODUCTION_OPERATIONAL_GO`を生成しない。

またrelease GOは取引承認ではない。fresh runtime state、300秒以下のcontrol-plane lease、120秒以下のsingle-use操作別本人承認、signer直前再検証が揃わなければwriteを拒否する。claim失効、鍵revocation、provider事故、監視stale、ledger差異、kill switchで自動的にBLOCKEDへ戻る。
