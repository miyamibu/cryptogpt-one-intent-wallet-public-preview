# 再現可能なZIP・展開安全性

**版:** 2026-07-29.3  
**判定:** release toolingはGO、Mainnetアプリの安全性は別gate

## 1. 防ぐ問題

- `../`、絶対path、backslashによる展開先外への書き込み
- symlink、device、socket等の特殊member
- 大文字小文字、Unicode正規化、重複名による上書き
- Windows予約名、末尾の空白／`.`、過長path、Unicode lookalikeを含む非ASCII path
- 暗号化member、異常な非圧縮量、極端な圧縮率による検査回避
- 秘密鍵／資格情報fileの混入
- manifest／`SHA256SUMS.txt`と実fileの不一致
- ZIPで表現不能なtimestampや毎回異なるtimestampによる再現性喪失
- 二つのZIP生成実装が時間とともに別仕様になる問題

## 2. 正本となる役割分担

| tool | 役割 |
|---|---|
| `tools/run_full_validation.py` | 画面、Schema、copy、archive、secret、link、敵対監査、report、manifestを正しい順で実行 |
| `tools/build_reproducible_zip.py` | ソート済み、固定timestamp、単一root、固定commentのZIPを一回生成する低水準builder |
| `tools/verify_zip.py` | CRC、path、特殊member、衝突、size／ratio、timestamp、manifest、checksums、clean-extract static validation |
| `tools/build_release.py` | 唯一のrelease入口。full validation後に低水準builderを二回呼び、byte-for-byte一致を要求してverifyする |

`build_release.py`は独自の第三のZIP実装を持たない。生成責務を`build_reproducible_zip.py`へ一本化する。

## 3. 固定timestamp

`config/build-metadata.json`の`deterministicBuildTimestamp`をZIP entryとmanifestへ使う。これは実行時刻を偽るためではなく、同じ入力から同じartifactを得るためである。実際のTestnet、実機、監査、承認時刻は将来の`delivery/evidence`へ別に保存する。

## 4. 正本コマンド

```bash
python tools/build_release.py ../one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.3.zip
```

内部では次を行う。

1. `tools/run_full_validation.py`
2. 同一treeから一時ZIPを二回生成
3. SHA-256と全byteの一致を確認
4. 指定先へ一つだけコピー
5. 両方の一時ZIPを`tools/verify_zip.py`で検査
6. source tree digest不変を確認して最終ZIPへatomic replace
7. 最終ZIPをもう一度`tools/verify_zip.py`で検査

検証skip、visual skip、既存証跡を信頼するshortcutは存在しない。毎回full validationを実行し、同一source treeから二回buildしてbyte-for-byte一致を要求する。

## 5. 検査上限

`verify_zip.py`は展開前にentry数、単一fileの非圧縮size、総非圧縮size、圧縮率、暗号化flagを検査する。これは一般的な巨大archiveを安全に受け入れる万能unzipではなく、本パッケージのrelease検証器である。

## 6. 証明しないこと

ZIPの再現性、展開安全性、収録fileの一致は、nativeアプリ、Mainnet、外部API、署名方式、法務、Store適格性を証明しない。


## 生成工程と検証工程の分離

`tools/prepare_release_artifacts.py`だけがscreenshot、report、example hash、operational report、manifest、checksumsを生成する。`tools/run_full_validation.py`は全て`--check`で実行し、secure tree snapshotの前後一致を要求する。検証中の自動修復・自動更新は失敗を隠すため禁止する。

release builderは同一immutable treeから2回生成してbyte一致を要求し、clean extraction後に同じnon-mutating validationを実行する。readiness checker、trust policy、release subject、trusted timeのhashはpackage外の保護されたanchorへ固定する。
