# 公式ソース・SNS・変更監視

## Hyperliquid公式として確認するもの

- Hyperliquid Docs
- `hyperliquid-dex` GitHub organization
- Hyper Foundation
- X: `@HyperliquidX`
- X: `@HyperFND`
- 公式Telegram announcements
- contract address／onchain bytecode

公式サポート資料は「App Store上に公式Hyperliquidアプリはない」と注意喚起している。製品は必ず「独立した非公式クライアント」と明記する。

公式Instagramは、基準日時点で公式サポート資料から確認できないため、存在を推測しない。

## 過去7日SNS監視

リリース前および日次で:

- protocol incident
- maintenance
- API change
- Bridge pause
- asset change
- account mode change
- exploit warning
- scam domain warning
- documentation update

を検索する。

X取得に失敗した場合は、公式Docs／GitHub／statusを優先し、未確認の投稿内容を推測しない。

## 自動差分

- docs page hash
- GitHub default branch commit
- SDK version
- exchange action types
- signing types
- Bridge2 address/code hash
- HyperEVM chain parameters
- OpenAI terms update date
- OpenAI usage policy update date
- Android security docs update
- FSA announcements

## 影響判定

| Change | Action |
|---|---|
| 署名形式 | 全write停止 |
| Bridge code/address | Bridge停止 |
| fee/minimum | Card compiler更新まで停止 |
| Vault lock | 対象Vault停止 |
| OpenAI policy | AI機能停止／法務確認 |
| model snapshot | eval未通過ならpin継続 |
| law/regulation | public signup／write停止 |

## 追加監視

- Android Protected Confirmation API／device support changes
- Google Play Financial features declaration／crypto policy
- Hyperliquid agent count／capability／nonce semantics
- Hyperliquid node／API server guidance
- Testnet faucet prerequisite
- Bridge2 deployed bytecode and testnet/mainnet addresses

2026-07-28の調査では、公式サポート文書から公式Xアカウントは確認できたが、Xの直近7日投稿を完全に取得・照合できなかった。推測で補完せず、social reviewは`INCOMPLETE`として扱う。

## Apple change monitoring

毎releaseで次を公式ソースから差分確認する。

- App Review Guidelines 3.1.5／3.2
- Secure Enclave／CryptoKit supported curves
- App Attest availability／validation guidance
- Keychain accessibility
- LocalAuthentication／biometry policies
- iOS screen capture APIs
- TestFlight／distribution requirements
- HIG accessibility／touch target guidance
