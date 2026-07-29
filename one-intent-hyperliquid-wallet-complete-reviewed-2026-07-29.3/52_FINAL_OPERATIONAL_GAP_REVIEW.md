# Final Operational Gap Review

**版:** 2026-07-29.3  
**結論:** 現在のZIPは`BLOCKED_NOT_OPERATIONAL`。以下の不足を実装・証拠化し、37 gate・93 claimを満たした場合だけ`PRODUCTION_OPERATIONAL_GO`候補になる。

## 1. 複数視点による反対尋問

| 視点 | 最も厳しい問い | 現在の答え | 完了に必要な証拠 |
|---|---|---|---|
| 初心者利用者 | 難しい言葉や音声誤変換で別取引をしないか | offline copyとhard confirmationは設計済み、実機未証明 | 初心者task test、誤操作率、理解度、実機録画 |
| 経験者 | 清算価格、margin方式、funding、partial fillはlive状態と一致するか | fixtureのみ | Hyperliquid Testnet lifecycle、成立後position照合、stale/gap negative test |
| デザイナー | 320px、最大文字、IME、safe area、画面回転で重ならないか | browser logical pixelのみ | SwiftUI／Compose実機matrix、VoiceOver／TalkBack、スクリーン録画 |
| 1pxを疑うQA | CTAがfold・keyboard・overlay・screen readerで隠れないか | browser検査済み、native未証明 | target端末ごとのgeometry/hit/focus/a11y tree evidence |
| Mobile security | root/jailbreak/overlay/hook/deep link/clipboardで承認をすり替えられないか | 要件のみ | 実機negative test、attestation backend、protected storage、fail-closed log |
| Backend | DB commitとbroadcastの片方だけ成功しないか | contractのみ | transactional outbox、crash-point test、ledger zero-diff reconciliation |
| Custody/Signer | policyを迂回してgeneric署名できないか | interface設計のみ | HSM/MPC実装、key ceremony、独立crypto review、generic-sign rejection |
| Protocol | token、bridge、Hyperliquid API変更を誤って受理しないか | registry/schemaのみ | code hash、proxy、asset ID、nonce、WebSocket gap、finalityのlive evidence |
| 手数料 | JPYCだけ・native fee 0から本当に安全に一回目を開始できるか | simulationのみ | provider契約、zero-gas canary、operation-bound quote、二重回収negative test |
| AI/privacy | model updateやprompt injectionでwrite境界を越えないか | read-only contractと要件 | model/version gate、golden corpus、privacy redaction、network isolation evidence |
| 管理者/SRE | 事故中に停止でき、復旧時に二重実行しないか | runbook設計のみ | kill-switch、restore、provider outage、key compromise、break-glass drill |
| 供給網 | validator、build host、dependency、署名鍵が侵害されても検知できるか | package validatorのみ | hermetic native/service build、SBOM、SLSA、独立builder、managed signing |
| 法務/Store | 日本で対象機能を提供し、Apple/Googleで公開できるか | 未判断 | release subjectへ結合した法務書面、portal submission/approval証拠 |

## 2. 検証器そのものの抜け穴

前版では、検証工程が証拠画像、報告、hash、manifestを更新してからPASSする余地があった。これは「古い証拠を見つける」のではなく「古い証拠を正しいものに書き換える」危険である。

修正:

- `tools/prepare_release_artifacts.py`だけが派生物を生成する。
- `tools/run_full_validation.py`は全generatorを`--check`で実行する。
- secure snapshotを検証前後で比較し、追加・削除・mode・内容の差を許さない。
- release builderは同じimmutable treeから2回生成し、byte-for-byte一致を要求する。
- clean extraction後も同じnon-mutating validationを実行する。

## 3. Release readinessの抜け穴

単に`delivery/evidence/`へファイルを置くだけではGOにしない。

- package外のtrust policy hash
- checker hash
- release subject hash
- trusted-time attestation hash
- 署名済みevidence statement
- 独立review approval
- 署名済みevidence index
- exact required-claim set
- artifact digestとsubject binding

これらをすべて要求する。自己署名、自己承認、期限切れ、revoked key、別release流用、未知claimは拒否する。

## 4. Runtimeの抜け穴

releaseが承認済みでも、障害や攻撃は後から起きる。次を分離する。

```text
PRODUCTION_OPERATIONAL_GO
        + fresh runtime state
        + short-lived service lease
        + single-use per-operation user authorization
        + signer-side last-moment revalidation
        = その一操作だけを実行可能
```

どれかが欠ければ実行しない。runtime leaseを包括承認として使わない。

## 5. Codexが実装すべき技術的残作業

- Kotlin／Jetpack Compose Android appとrelease AAB/APK
- Swift／SwiftUI iPhone appとarchive/IPA
- shared deterministic coreとKotlin／Swift／backend byte vectors
- Control API、取引Intent Parser、任意の非取引Support Gateway、registry、fee-route service、Reconciler
- policy-enforcing Signer、HSM/MPC integration、key ceremony/recovery
- transactional ledger、outbox/inbox、idempotency、audit hash chain
- Hyperliquid metadata/nonce/WebSocket/order lifecycle/margin/liquidation adapter
- JPYC official data pin、JPYC EX handoff integration
- token/proxy/allowance/bridge/finality/fee readiness adapters
- native security、accessibility、privacy、deep-link/clipboard defenses
- CI、SBOM、provenance、independent builds、signed release
- staging、Testnet、極小Mainnet canary、zero-difference reconciliation
- monitoring、kill switch、backup/restore、incident drills

## 6. Codexだけでは完了できない可能性がある外部作業

- 法人・partner契約とproduction credential
- Apple Developer／App Store Connect、Google Play Console
- Mac/Xcode、対象iPhone/Android実機
- HSM/MPC vendorまたは運用施設
- JPYC EX接続承認、fee sponsor/relayer契約
- 日本その他の地域別法務意見
- 独立mobile/backend/cryptography/smart-contract監査
- Store審査結果
- Testnet/Mainnet資産とrelease board承認

Codexはこれらを捏造せず、`delivery/EXTERNAL_BLOCKERS.md`へ担当role、portal、menu、button、field、資料、callback、保存先、検証方法、再試験command、閉じるgateを記録する。

## 7. 完了判定

最終machine-readable結果は二択である。

```text
PRODUCTION_OPERATIONAL_GO
BLOCKED_NOT_OPERATIONAL
```

`implementation complete`、`mostly ready`、`ready except`、`production candidate`を運用可能の同義語にしない。93 claimのうち一つでも欠けるか、runtime条件が失効した場合は`BLOCKED_NOT_OPERATIONAL`である。

## 8. 最終Signer・rollback・結果不明stateの不足

設計packageには、運用実装が必ず満たす次の追加契約を収録した。実装証拠がない現在は引き続きBLOCKEDである。

- `quoteId`や`quoteHash`という文字列だけを信頼しない。Signer自身がcanonical quote本文をstrict parseし、domain、provider、account、deployment、source state、network、asset、全action、minimum receive、fee、expiry、nonceを再計算する。
- release時に署名されたregistry entryをexact hashで読み、CAIP-2、numeric chain ID、RPCから取得したchain ID、Hyperliquid market identity、contract／proxy／implementation／code hash／decimalsを一致させる。
- 最終EVM calldata／typed data／Hyperliquid actionを生成した後、そのcanonical commitmentをquoteとoperation authorizationへ結合し、宛先・金額・方向・network・fee・slippage・期限の一文字差も拒否する。
- trusted-time、evidence-index、registry、runtime-state、account-binding、lease、authorization sequenceは、rollback-resistantなpackage外storageのhigh-water markより必ず大きくする。
- authorization IDとnonceは署名前に原子的に予約し、署名済みpayloadとtransaction hash候補をdurable保存してからbroadcastする。
- broadcast応答が失われた場合は`SIGNED_BROADCAST_UNKNOWN`とし、chain／venue照合で既存効果を確認するまで同じ操作を再署名しない。
- crash、timeout、concurrent request、process restart、DB failoverの各境界で「最大一署名」と「二重効果なし」を否定テストで実証する。

正本は`54_CANONICAL_QUOTE_REGISTRY_AND_ATOMIC_SIGNER.md`と`codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md`である。
