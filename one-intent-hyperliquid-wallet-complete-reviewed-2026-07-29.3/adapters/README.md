# Adapters

これらはネットワークへ接続しない fake／contract adapter です。`FakeHyperliquidAdapter` の書き込みは明示的な fake Testnet gate が必要で、既定では拒否します。JPYC EX は controlled handoff のデータ整合性だけを扱い、公式パートナー API を推測しません。手数料ルートは検証済み capability と operation-bound quote が全条件を満たす場合だけ eligible です。
