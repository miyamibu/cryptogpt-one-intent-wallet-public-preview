# Final security report

## 現在の結論

ローカル負のテストは実装済みですが、独立セキュリティ監査済みではありません。したがって `G21`、`G30` および関連 claim は `BLOCKED_EXTERNAL` です。

## 確認した境界

- OpenAI-facing service は 4 操作以外を拒否し、body/query/path/header/metadata/tool context の追加キーと取引文脈を拒否します。
- signer は release GO、runtime lease、120秒以内の single-use authorization、capsule hash、device/account、proof of possession を要求します。
- authorization の proof は device/account/capsule/authorization/nonce に束縛し、durable store を要求する production facade は store 未設定時に fail closed します。
- 署名後のプロセス障害は `SIGNED_BROADCAST_UNKNOWN` となり、同一 authorization の再署名を拒否します。
- ログやリポジトリには秘密鍵・回復情報を置いていません。SBOM／provenanceの設計ファイルは生成済みですが、署名・透明性ログ・独立検証は未完了です。

## 未検証

fuzzing、SAST、依存関係／ライセンス／SBOM／SLSA、mobile dynamic analysis、penetration test、HSM/MPC key ceremony、独立 cryptography/protocol review は未実施です。
