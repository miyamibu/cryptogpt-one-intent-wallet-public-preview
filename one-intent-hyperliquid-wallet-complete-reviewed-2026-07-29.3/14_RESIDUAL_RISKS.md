# 残余リスク

以下は設計で低減できるが、消せない。

1. Hyperliquid L1停止・consensus障害
2. Bridge contract／validator障害
3. HyperEVM contract exploit
4. oracle異常
5. market gap／liquidity不足
6. liquidation
7. Vault損失
8. Android zero-day
9. MPC implementation／vendor bug
10. recovery share紛失
11. user social engineering
12. support impersonation
13. 取引Intent Parser／独立非OpenAI modelの誤解析
14. API policy変更
15. Hyperliquid仕様変更
16. 日本法の解釈・改正
17. third-party RPC／relayer障害
18. cloud compromise
19. insider collusion
20. unknown unknowns

## 対応

- 資産上限
- trade account分離
- feature kill switch
- manual escape
- read-only fallback
- external audit
- insurance feasibility
- risk disclosure
- staged release
- change monitoring
- no safety guarantee marketing

## 禁止表示

- 「絶対安全」
- 「必ず儲かる」
- 「AIが最適に運用」
- 「元本保証」
- 「公式Hyperliquidアプリ」
- 「非カストディだから規制対象外」
- 「一回承認だから全処理が同時確定」

## iOS／Store残余リスク

- iOSに一般目的Trusted Displayがない前提によるUX制限
- App Attest非対応／障害／OS compromise
- App Review guidelineの変更・解釈・拒否
- TestFlight／Ad Hocとpublic availabilityの差
- Threshold ECDSA vendor／recovery risk
- platform間implementation drift
- screen captureを完全防止できないこと
