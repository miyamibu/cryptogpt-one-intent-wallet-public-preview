# Hyperliquid機能・署名・検証マトリクス

> `API Wallet可能`は「安全に限定権限」という意味ではない。Hyperliquid上の署名者として受理される可能性と、製品側で採用する署名経路は別である。

| 機能 | 代表action／経路 | 署名分類 | 推奨signer | 主な確認 |
|---|---|---|---|---|
| Perp注文 | `order` | L1 action | Trade Agent | asset、side、size、price、reduceOnly、cloid |
| Spot注文 | `order` + spot asset | L1 action | Trade Agent | token ID、pair、tick/lot、min received |
| 注文取消 | `cancel` / `cancelByCloid` | L1 action | Trade Agent | account、asset、oid/cloid |
| 注文変更 | `batchModify` | L1 action | Trade Agent | 元注文、変更差分 |
| TP/SL | trigger order | L1 action | Trade Agent | trigger basis、market/limit、reduceOnly |
| レバレッジ | `updateLeverage` | L1 action | Trade Agent、R2以上 | max leverage、account mode |
| isolated margin | `updateIsolatedMargin` | L1 action | Trade Agent、R2以上 | position、delta |
| 全注文取消予約 | `scheduleCancel` | L1 action | Trade Agent | 期限、trigger limit |
| Vault入出金 | `vaultTransfer` | L1 action | Root policy path推奨 | exact vault、lock、profit share |
| Subaccount USDC | `subAccountTransfer` | L1 action | Root policy path | master/subaccount |
| Subaccount Spot | `subAccountSpotTransfer` | L1 action | Root policy path | token、direction |
| USDC class移動 | `usdClassTransfer` | user-signed | Root signer | account mode、amount、direction |
| 汎用asset移動 | `sendAsset` | user-signed | Root signer | source/destination dex、token |
| HyperCore USDC送金 | `usdSend` | user-signed | Root signer | destination、amount、chain |
| HyperCore Spot送金 | `spotSend` | user-signed | Root signer | token、destination、amount |
| Arbitrum出金 | `withdraw3` | user-signed | Root signer | destination、fee、amount |
| API Wallet承認 | `approveAgent` | user-signed | Root signer、R4 | agent、name、replacement impact |
| Builder fee承認 | `approveBuilderFee` | user-signed | Root signer、R4 | builder、max rate、disclosure |
| Native multi-sig化 | `convertToMultiSigUser` | user-signed | 原則初期版対象外 | HyperEVM影響、不可逆性 |
| Bridge2 Permit入金 | EIP-2612 Permit + contract | EVM typed data | Root wallet | chain、spender、value、deadline |
| HyperEVM Vault | contract call | EVM tx | Root signer | code hash、selector、allowance |

## 重要な非対称性

### L1 action

- `action_hash`、nonce、vault address、`expiresAfter`等を含む
- phantom agent形式の署名
- API Walletが利用される主要領域
- `expiresAfter`を一部actionで利用可能

### user-signed action

- EIP-712 typed data
- `hyperliquidChain`でenvironmentを分離
- `signatureChainId`
- `expiresAfter`非対応のため、実行直前に署名
- root user identityとの結び付きが重要

## Account mode

| Mode | 初期扱い |
|---|---|
| Standard | 対応 |
| Unified | 対応、runtime stateに基づく |
| Portfolio Margin | Feature Gate、pre-alpha等の現状監視 |

`usdClassTransfer`の必要性、balance field、risk calculationはmode依存。modeを推測しない。

## サブアカウント

- 利用可否をruntime取得
- 全ユーザー前提にしない
- agent nonceはsigner単位
- agentは取引process／並列subaccount単位で分ける。UIセッションごとの無制限発行は禁止し、現行agent数上限を管理する
- subaccount利用不可の場合の単一account policyを実装

## Builder fee

初期Mainnetでは無効。実装する場合:

- fee rateの完全表示
- user approvalの有無
-利益相反表示
- 法務判定
- builder address allowlist
- feeの監査ログ

## API Wallet bearer risk

`Trade Agent`は製品側の推奨経路であり、Hyperliquid protocolがそのagentを表のactionだけへ制限していることを意味しない。agent keyがSigner外へ漏れた場合、product policyを迂回できる。

Mainnet解除前に、採用SDK／protocol versionで次を実施する。

- agent署名で受理される全L1 actionのcharacterization
- vault／subaccount／margin／leverage等の負の試験
- 想定外action検知
- agent replacement／pruning／replay試験
- named／unnamed agent数とreplacement impact試験

## 状態ソース

`Info`／WebSocket／API serverの一系統だけをCompilerとSignerの共通source of truthにしない。R2以上では独立read path、non-validating node、またはchain evidenceを併用する。
