# Codex実装指示への案内

**版:** 2026-07-29.3

Codexへ渡す指示は、役割の異なる次の2ファイルです。

```text
codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md
codex/CODEX_EXTERNAL_OPERATIONALIZATION_PROMPT_2026-07-29.md
```

1つ目は機能・安全要件の唯一の正本です。2つ目は、外部環境・資格情報・実機・HSM／MPC・Testnet・法務・Store・独立監査を実行し、証拠へ結合するための実行契約です。2つ目は1つ目を上書きできません。

このpointerを独立した実装指示として使わないでください。展開したrepository全体をCodexへ渡し、`CODEX_START_HERE.md`の順序で両ファイルを使用してください。

Mainnet、Testnet書き込み、Android／iOS本番ビルド、JPYC EX本番連携、手数料代理支払い、Store公開は、正本に列挙した証拠が揃うまで`NO_GO`です。
