# iOS Security Requirements

## 1. セキュリティ境界

iPhone実装は、次の5つを混同しない。

1. **ユーザー認証** — Face ID／Touch ID／端末パスコード
2. **アプリ正当性** — App Attest
3. **端末認証鍵** — Secure Enclave P-256
4. **Hyperliquid署名権限** — secp256k1 API WalletまたはThreshold ECDSA root wallet
5. **画面内容の人間確認** — 実行カード、外部ウォレット、ハードウェア表示

Face IDに成功しただけで、画面の宛先・金額が正しいことは証明されない。App Attestに成功しても同じである。

## 2. Secure Enclaveの役割

採用する用途：

- P-256 Authorization Keyの生成・署名
- Keychain／MPC device shareを開くための鍵利用認証
- `biometryCurrentSet`相当のアクセス制御
- 端末登録・Authorization Envelope・server challengeへの署名

採用しない用途：

- Hyperliquid root EOAのraw secp256k1 private keyをSecure Enclaveへ直接入れる
- Secure Enclave署名だけでHyperliquid user-signed actionを生成する
- P-256をsecp256k1と同一視する

## 3. Keychain

端末側秘密データは以下を満たす。

- `ThisDeviceOnly`
- iCloud Keychain同期OFF
- アプリグループ共有OFF（必要性を証明した場合のみ例外）
- background access不要ならWhenUnlocked
- 高リスク鍵はbiometry current setに束縛
- uninstall／device migration／restore後は再登録
- secretsをNSUserDefaults、SQLite平文、ログ、crash reportへ書かない
- backupに復旧shareを含めない

## 4. App Attest

### 目的

- 正規bundle ID／team IDのアプリ实例からの要求である可能性を高める
- Authorization Envelopeのchallengeとapp instanceを関連付ける
- repackaged client、単純bot、replayの検知材料にする

### 限界

- compromised OSを完全には排除しない
- すべての端末が対応するわけではない
- reinstall、migration、restoreで鍵が失われる
- ユーザーが画面内容を理解した証拠ではない
- 単独でMainnet許可条件にしない

### Assertion clientData

以下をcanonical encodeしてSHA-256する。

```text
semanticHash
renderReceiptHash
sourceStateHash
challenge
sessionId
deviceRegistrationId
policyVersion
expiresAt
```

serverはcounter monotonicity、challenge one-time use、team ID、bundle ID、environment、key stateを検証する。

## 5. iOS Authorization Mode

`IOS_APP_ATTESTED_AUTHENTICATED_UI`は、次を意味する。

- 正規アプリの可能性をApp Attestで確認
- Face ID／Touch ID等でAuthorization Key利用を許可
- exact hashへP-256署名
- **Trusted Displayとは呼ばない**

利用可能範囲：

- R1：通常のPerp／Spot
- R2：既知Vault、上限内操作
- R3：事前登録済み宛先＋standing authorization＋金額上限＋都度認証

利用禁止（R4へ分類）：

- 新規宛先
- 宛先変更直後
- 高額／全額出金
- recovery share変更
- 新端末追加
- MPC policy変更
- 未知contract

上記は外部ウォレット／ハードウェアウォレット、または別日に完了した宛先登録ceremonyとcooling periodを要求する。

## 6. Existing Wallet Mode

- Universal LinkまたはWalletConnect系の正式連携を利用する
- generic custom URL schemeだけへ依存しない
- external walletが表示・署名したpayloadを再検証する
- expected signature countを事前表示する
- root actionで追加wallet confirmationが出る事実を隠さない
- external wallet capability evidenceがなければTrusted Displayと分類しない

## 7. Managed Self-Custody Mode

以下が揃うまで実装をMainnet有効化しない。

- 監査済みThreshold ECDSA／secp256k1実装
- device share＋HSM/server share＋independent recovery share
- full keyが平文復元されないことの証拠
- DKG／reshare／recovery／rotation／backupの外部監査
- vendor exit plan
- policy signer compromise test
- device loss／server loss／service shutdown drill
- legal analysis of custody/control

自作MPCは禁止する。

## 8. 画面・capture・pasteboard

- background移行時に金額・宛先・QR・seed関連画面をblur
- recording／mirroring状態を検出し、高リスク画面を停止または警告
- screenshotは完全防止できると表示しない
- screenshot通知は事後検知にすぎない
- recovery dataを画面に同時表示しない
- clipboardへ秘密鍵・seed・MPC shareを入れない
- address copy時はlocal-only／expirationを使い、貼付時に再確認
- notificationへ残高、full address、position sizeを標準表示しない

## 9. Deep Link／App Intents／Siri

MVPでは以下を禁止する。

- URLからamount、destination、sideを直接実行
- Siri／Shortcuts／App Intentsからwrite action
- notification actionから取引・出金
- QR scan後の即実行

linkは閲覧画面やplan draftまでに限定し、アプリ内で再コンパイルする。

## 10. iOS release evidence

- iPhone 12実機をP0基準として含める
- device model／OS version／build hash
- App Attest production environment test
- unsupported fallback test
- reinstall／restore／migration test
- Face ID enrollment change test
- passcode removal test
- locked／background／low power／offline test
- VoiceOver／Dynamic Type 200% test
- screen recording／AirPlay test
- crash log secret scan
- Keychain backup and migration behavior evidence
- root action external confirmation evidence
