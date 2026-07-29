# 監査ループ記録

**版:** 2026-07-29.3

| 反復 | 疑った前提 | 発見 | 処置 | 再検査 |
|---:|---|---|---|---|
| 1 | 前版のPASSを信頼してよい | validatorが旧スクリーンショット名と120条件を期待 | evidence schema 2.0、6×12×2×2へ更新 | 288条件 |
| 2 | 大きな文字でも情報が残る | 依頼原文を省略する案があった | user bubbleを常時保持 | 全flow大文字 |
| 3 | 固定CTAは便利 | 短い端末で明細を隠す | CTAをreview末尾へ移動 | 320×568を追加 |
| 4 | 音声正規化は自動でよい | 「生産価格」を誤って確定できる | 原文＋候補＋明示確認のhard gate | before/afterテスト |
| 5 | JPYCがあれば手数料を作れる | 0 nativeでは通常swap開始不能 | 口座方式・経路能力証明を分離 | zero-gas回帰 |
| 6 | 手動手順に例示量を出せる | 固定POL量が将来不適切 | operation-bound見積もりまでnull | fixed amount拒否 |
| 7 | JPYC addressを例に入れてよい | 例が本番値と誤認される | 明示的dummy、SIMULATION_ONLY | registry semantic check |
| 8 | 画面証跡だけで十分 | test自身のscroll操作や時刻drift | source/test/toolchain hash、固定時刻 | evidence照合 |
| 9 | ZIPは普通に圧縮すればよい | path traversal、symlink、Unicode衝突 | archive safetyとclean-extract検証 | ZIP verifier |
| 10 | promptの複製は便利 | 指示drift | 正本1つ＋pointer | adversarial audit |
| 11 | UIの見た目が整えばよい | dark contrast、focus、text spacing | light/dark、focus、spacing proxy | matrix test |
| 12 | 100%と表現できる | 未知の外部依存は消せない | finite assurance scopeとNO-GO | assurance case |
| 13 | `getBoundingClientRect()`の交差が可視性を表す | scroll領域で完全に切り取られた部品までcomposerと重なったと誤判定 | overflow祖先を含む実描画矩形を算出し、その中心をhit検査 | top/bottom全control |
| 14 | 入口は簡単なので崩れない | `START_HERE.html`自体がvisual matrix外 | 狭幅・標準・desktop×明暗の独立検査 | 6条件＋通信0 |
| 15 | 画面例と書けば任意値も伝わる | 30日・上限・address等が既定／本番値に見える | 値の直近へ初期値ではない／ダミー表示 | static copy回帰 |
| 16 | screenshotは存在すれば証拠 | sticky直下でblock途中が切れる | block境界へ整列、focus除去、部分上端を失敗 | 10画像境界検査 |
| 17 | 検証を通せば生成物は残らない | 手動構文確認の`__pycache__`／`.pyc`が最終検査で混入候補になった | pipeline開始時に限定cleanup、archive safetyとvalidatorで残存を再拒否 | clean treeからfull validation |
| 18 | manifest名とpackage identityは一致する | 旧generatorが別product名をhard-code | metadataを唯一の正本に統合 | manifest／ZIP root／report exact一致 |
| 19 | strict parserは通常入力だけ通ればよい | JSON `-0`／巨大整数、YAML NaN／暗黙timestampで言語間drift | parse時に拒否しnegative fixture化 | validator self-test 32 assertions |
| 20 | full validationのvisual skipは便利 | FULL VALIDATION名のままvisual未実行にできる | skip optionを完全削除 | canonical entry point source scan＋実行 |
| 21 | directory setgidは全て危険 | `/mnt/data`継承bitで安全なtreeが環境依存失敗 | regular fileの危険bitだけ拒否しZIP modeを0644固定 | archive safety再実行 |
| 22 | link checkerは単純regexで十分 | regex自体の括弧欠落、reference/raw HTML未検査 | parserを修正しself-test、生成後reportも検査 | local link／markup PASS |
| 23 | `/authorize`文字列を禁止すればChatGPT writeを防げる | OAuth authorizationUrlを誤検知し、path driftは構造未検査 | exact path/method/operation/schema/scope allowlistへ変更 | OpenAPI negative review |
| 24 | NFCだけでarchive名は十分 | Unicode lookalikeがreviewとOS表示を混同 | package pathをportable ASCIIへ限定 | path negative fixtures |
| 25 | UTC timestampならZIPで再現可能 | odd second／年範囲外はDOS時刻で丸め・失敗 | UTC Z・秒精度・1980..2107・偶数秒を必須化 | metadata self-test |
| 26 | `ZipInfo.flag_bits=0x800`はそのまま保存される | ASCII memberでzipfileがflagを0へ正規化し全検証失敗 | ASCII path policyに合わせexact flags 0を共有定数化 | double-build＋ZIP verifier |
| 27 | `--check`なら証拠を変えない | prototype checkerが正本screenshotを削除できた | check出力をtemporary directoryへ隔離 | source tree前後hash＋失敗path |
| 28 | validator一覧にあれば実行される | runtime checkerのimport失敗で検査不能 | import修正、exact allowlist、失敗即停止 | self-test 36 assertions |
| 29 | 署名済みtrusted timeなら新しい | 古いsequenceを再利用できる | package外high-waterよりstrictly greaterを要求 | readiness/runtime rollback negatives |
| 30 | quote hashが一致すれば同じ取引 | quote本文・route・final payloadを差し替え得る | strict canonical quoteとfinal-payload commitment | field-by-field mutation rejection |
| 31 | network名が同じなら同じchain | CAIP-2、numeric ID、RPC chain ID、registry entryがずれる | signed registryを実解決し全identityを照合 | chain/contract/code-hash negatives |
| 32 | timeout後は同じ操作を再送できる | 署名済みbroadcast結果不明で二重効果 | `SIGNED_BROADCAST_UNKNOWN`、durable state、照合優先、再署名禁止 | crash/concurrency/unknown-receipt tests |
