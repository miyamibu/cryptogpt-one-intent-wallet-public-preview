# 障害・復旧・インシデント

## 実行状態

各stepとplanをappend-only eventで記録する。

```text
PLAN_CREATED
PLAN_COMPILED
STATE_EVIDENCE_COLLECTED
CARD_RENDERED
TRUSTED_PROMPT_PRESENTED
USER_AUTHORIZED
SIGN_REQUESTED
SIGNED
SUBMITTED
REMOTE_ACCEPTED
OBSERVED
RECONCILED
COMPLETED
FAILED
RECOVERY_REQUIRED
```

## タイムアウト

### Order

1. HTTP timeout
2. 同一cloidでstatus照会
3. open／filled／rejectedを確認
4. independent state sourceで補助照合
5. unknownなら新規注文禁止
6. manual reviewまたは一定時間後再照合

### Transfer／Withdraw

1. nonceとsignature hash保存
2. response timeout
3. user action history／balance delta／destination／chain eventを照合
4. 証拠なしに新nonceで再送しない

### EVM

1. tx hash取得済みか
2. mempool／receipt
3. replacement policy
4. reorg confirmation
5. token balance delta
6. RPC quorum divergence

## Crash recovery

起動時に、incomplete Saga、last event、remote state、signer state、feature gate、source evidence、expiry、safe next actionを再構築する。

## 端末紛失

- remote session revoke
- trade agent revoke／replace
- device share disable
- recovery flow
- root address migration必要性
- old device notification
- no silent recovery

## 鍵失効／Protected Confirmation障害

- write操作停止
- read-only表示
- capability再評価
- recovery authentication
- old device key revoke
- new auth／confirmation key enrollment
- Address Book／policy integrity verification
- high-risk cooldown

対応端末でProtected Confirmationが一時利用不能でも、R4またはstanding例外を満たさないR3を通常BiometricPromptへ自動降格しない。

## API Wallet漏えい

1. write kill switch
2. open orders cancel
3. agent replacement／deregister
4. affected account state snapshot
5. product外から実行された全L1 action調査
6. safe walletへ資産移動
7. compromised address再利用禁止
8. incident disclosure

## State-source incident

- divergent sourceを隔離
- R2以上のwrite停止
- local node／chain evidence／別providerで再照合
- stale compiler outputと未実行Capsuleを失効
-誤った完了表示を訂正
- source ownerとroot causeを監査

## Root key疑い

- 全署名停止
- agentは状況により取消専用
- safe walletへmigration
- HyperEVM資産も確認
- Bridge pending withdrawal確認
- legal／users対応

## Bridge incident

- deposits／withdrawals gate停止
- contract paused／events／official notice確認
- pending state分類
- 「失敗」「遅延」「争議期間」「finalized」を区別
- third-party bridgeへ自動迂回しない

## Vault incident

- new deposits停止
- withdrawal可否確認
- contract upgrade／oracle／position risk
- ユーザーへ現在のlock・withdraw risk表示
- 自動で損失確定取引をしない

## RTO/RPO目標

目標はアプリ／サービス側の応答であり、chain上の約定・着金時間を保証しない。

| 系統 | 目標 | RPO |
|---|---:|---:|
| emergency request受付 | p95 2秒以内（依存先利用可能時） | 0 |
| cancel／write kill path復旧 | 1分以内 | 0 |
| read-only account state | 5分以内 | 1分 |
| normal order service | 15分以内 | 0 |
| AI chat | 4時間以内 | 会話は許容 |
| audit event | 15分以内 | 0 |
| signer | 15分以内、または安全停止 | 0 |

非常口はAI、通常チャット、分析機能より優先する。
