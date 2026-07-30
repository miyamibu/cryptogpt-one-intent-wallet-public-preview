# 残リスク

- Python 参照実装は Kotlin、Swift、実運用 backend の byte-for-byte 実装ではありません。クロス言語 vector の実行証跡が必要です。
- Android/iOS は安全境界のshellです。Pixel 9aのlocal UI proofと、Team `PUBLICTEAM`のiPhone 12 signed device build／インストール・起動・Appium/WDA画面取得・tap・上下gestureは確認済みですが、overlay、accessibility、backup、attestation、biometric lifecycle、完全な実機matrix、release-bound screen evidenceは未証明です。
- fake protocol adapter は Hyperliquid、EVM、JPYC EX、fee provider の公式仕様・現在値・障害動作を証明しません。
- registry の署名はローカルデータモデルだけで、production key、two-person approval、revocation、rollback-resistant storage は未導入です。
- quote の暗号署名検証、provider identity、release/runtime の protected deployment は参照境界だけで、外部の署名基盤へ接続していません。
- readiness model が 37 gates／93 claims を持つことは、claims が pass したことを意味しません。現在の status は明示的に `BLOCKED_NOT_OPERATIONAL` です。
