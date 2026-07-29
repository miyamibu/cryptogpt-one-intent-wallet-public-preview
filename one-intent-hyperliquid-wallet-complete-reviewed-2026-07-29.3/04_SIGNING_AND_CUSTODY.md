# 署名・鍵管理・カストディ設計

## 結論

Testnetの最初の基準実装はExisting Wallet Mode。Managed Self-Custody Modeは、監査済み鍵方式、復旧試験、Trusted Display、法務判定が完了するまでMainnet無効。

## 鍵の分類

| 鍵 | 用途 | 保護 |
|---|---|---|
| Device Auth P-256 | Capsule／device認証 | Android Keystore |
| Confirmation P-256 | Protected Confirmation response署名 | 対応端末のKeyMint／attestation |
| Local Wrapping AES | local secret/share暗号化 | Android Keystore |
| Trade Agent secp256k1 | HyperCore L1 action | device-local encrypted blobを第一候補、または監査済みthreshold |
| Root EOA/MPC | user-signed action・EVM | external wallet／hardware wallet／threshold signer |
| Recovery share | サービス停止・端末紛失 | ユーザー管理、オンライン非保存 |
| Backend service key | mTLS／JWT | KMS/HSM |
| Admin key | release／policy | hardware security key |

## 禁止

- seed phrase入力フォーム
- clipboardへseed表示
- server logへprivate material
- generic `sign(bytes)` endpoint
- generic `eth_signTypedData` proxy
- generic EVM calldata signing
- developer consoleからproduction署名
- single adminによるpolicy relaxation
- Protected Confirmation非対応時のsilent downgrade
- agent keyを「アプリpolicyでscope済み」と表示

## API Walletに対する正しい脅威認識

- API Walletは署名代理であり、細粒度OAuth scopeではない
- product allowlistは、鍵がproduct signerを通る場合のsoftware controlにすぎない
- agent private keyを盗んだ攻撃者は、製品外でpolicyを迂回し得る
- agentが署名可能な全L1 actionをTestnetでcharacterizationする
- dedicated account／subaccount、hard balance cap、max leverageでblast radiusを抑える
- agent replacement時は古いaddressを焼却扱い
- agent private keyをroot action signerと同じprocessに置かない
- named agent数／replacement影響をruntime管理し、UI sessionごとに無制限発行しない
- anomalous L1 action monitorと即時revoke導線を持つ

## Trade Agentの配置

### 標準候補: device-local

- app内でagent keyを生成
- Android KeystoreのAES wrapping keyで暗号化
- session中だけmemoryへ展開
- background／timeout／risk eventでzeroize
- backup／D2Dから除外
- root walletで初回approve

利点: backend単独侵害でagent署名しにくい。  
限界: device compromiseやmemory extractionで鍵が漏れればproduct policyを迂回される。

### server／threshold候補

低遅延やmulti-device要件で採用する場合、custody、insider、availability、policy bypassを別監査し、法務書面意見を得る。server-side HSMだけで「非カストディ」と表示しない。

## Threshold ECDSA採用条件

- third-party audit
- secp256k1 compatibility
- deterministic ECDSA／low-s
- distributed key generation ceremony
- share refresh
- device replacement
- recovery from vendor outage
- recovery without vendor unilateral control
- malicious party／collusion model
- policy signer denial handling
- transaction intent binding
- Trusted Display binding
- Japanese custody legal opinion
- measurable latency／availability
- official SDK test vectors
- vendor exit／export／migration

## Existing Wallet Mode

初回にTrade Agentを承認した後、許可範囲内のPerp／Spotはagentで1タップ化できる。root actionは外部walletまたはhardware walletが原則都度署名する。Hyperliquidに一般的なroot-action session delegationが存在すると仮定しない。root actionを複数含むSagaでは、1つのIntentでも複数のwallet確認が発生し得る。typed fieldsを分解表示し、raw hashだけを見せない。walletがcritical fieldsを十分表示しない場合、高額操作のTrusted Displayとして採用しない。

「全機能を会話＋アプリ内1タップ」で完結させるUXは、Managed Self-Custody Modeが監査・復旧・法務ゲートを通過した場合に限る。UX要件のためにroot鍵を単一serverへ置くことは禁止する。

## Android認証

- P-256 auth keyはHyperliquid署名鍵そのものではない
- BiometricPromptはuser/key authorizationであり、transaction semanticsのTrusted Displayではない
- R4とstanding例外を満たさないR3はProtected Confirmation／external／hardware displayを使用
- Protected Confirmationの`promptText`とchallengeをRelying Partyが検証
- `extraData`だけを人間確認の証拠にしない
- AES-GCM nonce再利用禁止
- associated dataへuser/device/key versionを含める

## Recovery

- recovery shareの確認テストを初回に行う
- recovery資料をスクリーンショット保存させない
- recovery後は旧device share／agentを失効
- address migrationの手順を用意
- compromiseしたaddressを再利用しない
- service shutdown時のユーザー単独回収可能性を証明

## iOS鍵設計

| 鍵／証拠 | 用途 | iOS保護 |
|---|---|---|
| Device Authorization P-256 | Authorization Envelope署名 | Secure Enclave |
| App Attest key | 正規app instanceのassertion | App Attest service |
| Wrapped MPC device share | Threshold ECDSA | Keychain ThisDeviceOnly＋Secure Enclaveで利用制御 |
| Root secp256k1 | Hyperliquid user-signed／EVM | external walletまたは監査済みMPC |

App Attest、Face ID、Secure Enclave P-256をroot secp256k1署名やTrusted Displayの代わりにしない。再install／migration／restore時はdevice enrollmentをやり直す。
