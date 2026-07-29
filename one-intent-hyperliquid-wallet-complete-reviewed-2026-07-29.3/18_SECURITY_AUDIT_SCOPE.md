# 外部セキュリティ監査スコープ

## 対象

### Mobile

- Keystore
- biometric
- Android Protected Confirmation／attestation／promptText
- trusted-display fallback
- local encryption
- backup exclusions
- app links
- network security config
- certificate trust
- root／hooking resistance
- screen overlay
- clipboard
- deep links
- QR parsing
- wallet integration
- logs
- crash reports

### Backend

- auth
- session
- device binding
- compiler
- policy engine
- Address Book
- contract registry
- feature gates
- admin
- audit log
- Saga
- concurrency
- SSRF
- injection
- secrets
- IAM

### Signer

- no arbitrary payload
- typed builders
- policy binding
- semanticHash
- nonce
- key lifecycle
- threshold protocol
- HSM configuration
- mTLS
- insider access
- disaster recovery
- audit independence
- agent key exfiltration outside product policy
- bearer credential blast radius

### Hyperliquid

- signing parity
- action classification
- account binding
- agent behavior
- subaccount
- account modes
- rounding
- cloid
- timeouts
- WebSocket
- rate limits
- error handling
- agent-capable L1 action characterization
- named/unnamed agent limits and replacement

### Bridge／Vault

- chain ID
- contract address
- code hash
- proxy
- allowance
- Permit
- replay
- reorg
- deposit credit
- withdraw finalization
- malicious vault
- lock period
- partial Saga
- Testnet／fork／Mainnet parity assumptions
- independent state/RPC quorum

### AI

- false execution
- prompt injection
- address generation
- contract generation
- tool boundary
- model drift
- schema bypass
- data leakage

## 攻撃目標

1. UIと異なる注文を署名
2. 新規宛先へ無認証送金
3. Capsuleを別accountで再利用
4. mainnet/testnet replay
5. agent nonce replay
6. timeout二重注文
7. generic signing endpoint獲得
8. Feature Gate bypass
9. admin単独で上限解除
10. backupからshare回収
11. prompt injectionで宛先変更
12. Vault allowanceを無制限化
13. Bridge contract差替え
14. audit event削除
15. recovery takeover
16. crash後の誤再開
17. agent keyを持ち出してproduct policyを迂回
18. BiometricPromptで異なる取引内容を承認
19. Protected Confirmation非対応時のsilent downgrade
20. single API stateを改ざんして価格・残高・完了を偽装
21. Google Play／region gateを迂回して公開

## 重大度

- Critical: root asset theft、arbitrary signing、auth bypass
- High: unauthorized trade／transfer、duplicate execution、recovery takeover
- Medium: sensitive data leak、DoS、misleading status
- Low: hardening／best practice

Critical／HighはMainnet blocker。

## iOS audit scope

- Secure Enclave Authorization Key lifecycle
- Keychain access group、synchronization、accessibility class
- App Attest server validation、counter、challenge binding
- LocalAuthentication cancellation／fallback／enrollment change
- Universal Link／external wallet callback
- background snapshot／capture／pasteboard
- Swift／Rust FFI safety
- iOS release entitlement／provisioning review
- recovery after uninstall／device loss／service shutdown
