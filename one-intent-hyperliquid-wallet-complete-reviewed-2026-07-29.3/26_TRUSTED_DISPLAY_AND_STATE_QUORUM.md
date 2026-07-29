# Trusted Displayと状態Quorum

## 1. なぜ必要か

`semanticHash`は、承認後にpayloadが変わっていないことを検査できる。しかし、改変されたAndroidアプリが人間へ別の内容を見せ、正しいhashへ認証を求める可能性までは消せない。

BiometricPromptは「ユーザーが鍵利用を認証した」ことを示す。通常は「その取引内容をTrusted UIで確認した」ことまでは示さない。

## 2. リスク別の表示・認証

| Tier | 例 | 最低要件 |
|---|---|---|
| R0 | read-only | 通常UI |
| R1 | 上限内Perp／Spot | 完成済みExecution Card＋具体ボタン＋短時間認証セッション |
| R2 | 既知Vault、同一userへの公式Bridge入金、cancel-all等 | 具体ボタン＋per-use認証または厳格なpolicy。独立状態証拠 |
| R3 | 事前登録済み宛先への上限内送金／出金 | 原則protected／external display。例外はR4相当ceremonyで事前登録済み、cooling済み、hard cap、standing authorization、auth-per-use、device／app evidenceを全て満たす場合だけ |
| R4 | 新規宛先、高額／全額、recovery、鍵・policy変更、agent／builder承認 | external／hardware displayまたは事前登録ceremony＋cooldown＋追加factor |
| R5 | contract／Bridge／Vault allowlist追加、Mainnet全体解放 | 管理者二者承認、監査、release evidence |

## 3. Android Protected Confirmation

利用条件:

1. `ConfirmationPrompt.isSupported(context)`がtrue
2. 実際の`presentPrompt`が成功
3. attested confirmation keyをRelying Partyが検証
4. challenge nonceが一致
5. 返された`promptText`がサーバー側のcanonical generatorと完全一致
6. responseが未使用

重要:

- `promptText`だけが人間が確認した内容である。
- `extraData`へCapsule hashを入れても、人間がそれを読んだことにはならない。
- accessibility service等により、対応端末でもpromptを利用できない場合がある。
- Pixel 9aの対応可否を文書だけで断定しない。実機で確認する。

### canonical prompt例

```text
ARBITRUM WITHDRAW

200.00 USDC

TO 0xABCD...1234

MAX FEE 1.50 USDC

NETWORK ARBITRUM ONE

PLAN 7F3A2C91
```

文字数制限に合わせながら、最低でも次を可視化する。

- operation
- source／destination network
- asset
- amountまたは安全な上限
- destination識別子
- maximum fee
- short plan fingerprint

新規宛先の完全アドレスがpromptに収まらない場合、先にTrusted DisplayでAddress Book登録を行い、cooldown後にalias＋fingerprintを利用する。省略表示だけで新規宛先を承認しない。

## 4. Fallback

Protected Confirmationが使えない場合:

1. 外部hardware walletのTrusted Display
2. 外部walletがtyped fieldsを十分表示することを実機確認
3. それも不可ならR4と、standing-authorization例外を満たさないR3をブロック

「対応していないので通常BiometricPromptへ静かに降格」は禁止する。降格には、明示警告、低いhard cap、登録済み自分宛て限定等の別policyと法務・セキュリティ承認が必要。

### R3 standing-authorization例外

これはruntime downgradeではない。宛先登録時にR4相当のexternal／hardware／protected ceremonyを完了し、cooling期間後に別の限定権限を発行する事前承認モデルである。最低条件：

- exact chain＋full address＋alias fingerprintを登録
- registration evidenceとpolicy versionを署名
- cooling完了
- per-action／daily hard cap、self／allowlisted destination限定
- auth-per-use、device／app integrity evidence
- address／policy／device／risk changeで即失効
- high amount／ALL／new destinationへ拡張不可

これらのどれかが欠ける場合、R3はprotected／external displayへ戻すかブロックする。

## 5. 状態Quorum

CompilerとSignerが同じAPI応答を信じるだけでは、共通モード障害を防げない。

### StateEvidence

Execution Capsuleは、次を持つ。

- source ID
- source type
- observed block／time
- state digest
- source independence class
- divergence result
- maximum age

### 推奨policy

| Tier | 状態証拠 |
|---|---|
| R1 | 公式API＋厳格なfreshness。低hard cap |
| R2 | 独立二系統のAPI／indexer照合 |
| R3/R4 | 自前non-validating nodeまたはchain data＋別API、EVM receipt／contract state |

同じ会社・同じbackend・同じcacheを二つのsource名で呼んでも独立ではない。

### Fail closed条件

- price、balance、position、account mode、contract code、paused stateの許容外乖離
- block height／timestampの異常
- source digest不一致
- source independence不明
- stale source
- source pin不一致

## 6. Signer側の検査

Signerは、Capsuleの`stateEvidence`を独立に検査する。Compilerが出した`CONSISTENT`という文字列を信じるだけでは不十分である。最低限、署名対象に影響するcritical fieldを別経路で再取得または検証する。

## 7. iOS authenticated app UI

iOSでは、App Attest＋Secure Enclave P-256＋Face ID／Touch IDを組み合わせても、一般目的の取引内容Trusted Displayとは分類しない。

`IOS_APP_ATTESTED_AUTHENTICATED_UI`は次を保証対象とする。

- server challengeに対する正規app instanceのassertion
- exact Authorization Envelope hashへのdevice authorization signature
- user authenticationを要求した鍵利用

保証対象外：ユーザーが正しい宛先・金額を実際に読んだこと。

したがって、新規宛先、高額／全額出金、recovery／key policy変更はexternal／hardware display、または事前登録＋cooling ceremonyを要求する。
