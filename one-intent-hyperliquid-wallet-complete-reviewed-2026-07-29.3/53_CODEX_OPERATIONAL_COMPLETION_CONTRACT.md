# Codex Operational Completion Contract

**正本プロンプト:** `codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md`  
**現在の状態:** `BLOCKED_NOT_OPERATIONAL`

## 成果物契約

Codexは文書だけを増やして完了としてはならない。実装可能な範囲では、実際にbuild・起動・試験できるAndroid、iOS、shared core、backend、signer interface、reconciler、registry、fee route、CI、deployment、observabilityを作る。

最終成果物には次を含める。

1. native/service source、lockfile、migration、infra、runbook。
2. fake adapterで12 flowを端から端まで実行する再現可能テスト。
3. physical device、Testnet、Mainnet canary、監査、法務、Store等の実際に取得した証拠。
4. `config/operational-readiness.json`の37 gate・93 claimを対象とする署名済みevidence bundle。
5. package外のtrust/checker/subject/time anchorを設定する運用手順。
6. release readinessとruntime activationを分離した実装。
7. 未完了外部条件のボタン単位手順を含む`delivery/EXTERNAL_BLOCKERS.md`。
8. 最終machine-readable判定。
9. canonical quote、signed registry、actual RPC chain ID、final payload commitmentをSignerが再計算する実装とmutation negative tests。
10. package外high-water storage、strictly increasing sequence、atomic authorization/nonce consumption、`SIGNED_BROADCAST_UNKNOWN`照合のcrash/concurrency evidence。

## 禁止

- mock、fixture、screenshot、存在するだけのfileをproduction evidenceと呼ばない。
- credential、契約、法務意見、監査、Store承認を捏造しない。
- testを削除・弱体化してPASSにしない。
- Mainnet、public Store、signer write、ChatGPT financial writeを証拠なしに開かない。
- runtime leaseを利用者の取引承認として扱わない。
- unresolved critical/high、ledger差異、unknown stateをwarningで通さない。
- quote hash、network label、client-side previewだけを信頼して署名しない。
- signed/broadcast結果不明の操作を新しいnonceまたは新しい署名で自動再試行しない。
- sequence high-water、registry hash、chain ID、final payloadの一つでも不一致ならsigner writeを許可しない。

## 正式終了条件

すべてを完璧に実行した場合、次の一つだけを出す。

- `PRODUCTION_OPERATIONAL_GO`: 37 gate・93 claimがexact release subjectへ有効に結合され、独立承認、out-of-band anchors、trusted time、runtime activation、操作別承認が検証可能。
- `BLOCKED_NOT_OPERATIONAL`: それ以外のすべて。

詳細な実装順序、試験、証拠、外部作業、最終回答形式は正本プロンプトに従う。
