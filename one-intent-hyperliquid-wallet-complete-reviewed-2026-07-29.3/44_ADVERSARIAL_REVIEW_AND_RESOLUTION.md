# 敵対的・多視点レビューと修正記録

**版:** 2026-07-29.3  
**対象:** 文書、Schema、API契約、オフライン画面見本、検証コード、Codex引継ぎ  
**注意:** これはproductionアプリの外部監査報告ではない。現パッケージの内部整合と実装前設計を、意図的に疑って検査した記録である。

## 1. レビュー方法

同じ設計を、互いに優先順位が衝突する次の立場から評価した。

| 視点 | 最優先 | 意図的に疑ったこと |
|---|---|---|
| 初心者利用者 | 分かりやすさ、迷わなさ | 英語、暗黙の既定値、資産の現在位置、失敗後の行動 |
| 経験者利用者 | 正確さ、検証可能性 | 完全なアドレス、見積もり時刻、最低受取、清算価格の限界 |
| プロダクトデザイナー | 階層、読みやすさ、操作効率 | 警告過多、長文、画面末尾、端末差、ダーク表示 |
| 「1mmのずれを探す」QA | 重なり、切れ、再現性 | 320×568、200%相当文字、スクロール末尾、固定領域、フォーカス |
| セキュリティ | fail closed、最小権限 | AIの黙示補完、zero-gas、署名対象差替え、stale state、二重実行 |
| 管理者・SRE | 停止、照合、証拠 | feature gate、provider失効、監査証跡、部分成功、kill switch |
| 法務・Store審査 | 適格性、正確な申告 | OpenAI金融write、Apple提出主体、Google金融機能申告、地域制限 |
| 成長担当 | 離脱率、短い導線 | 安全確認が多すぎないか、初回承認で摩擦を減らせるか |
| 反対側の成長担当 | 事故後の信頼維持 | 「1タップ」を誇張していないか、危険な自動化が継続率を壊さないか |
| 実装者 | 一貫性、テスト容易性 | Swift/Kotlin/backendの仕様drift、重複プロンプト、例と本番値の混同 |

## 2. 重大指摘と解決

| ID | 指摘 | 危険 | 修正 | 再発防止 |
|---|---|---|---|---|
| AR-001 | 利用者が頼んでいない「損切り2%」を先物画面が追加していた | AIが取引条件を発明する | 画面見本では「損切りは未設定」と明示。音声誤認の確認が終わるまで次へ進めない | `tools/test_prototype.py`と`tools/adversarial_audit.py`で「損切り2%」の混入を拒否 |
| AR-002 | まとめ操作の「最低受取」と「残り最大額」の算数が矛盾していた | 到着額の過大表示 | 最低売却額948.50−預入300.00−手数料上限1.00＝最低到着647.50へ統一 | DOMの数値を再計算するdomain consistency test |
| AR-003 | 固定された実行ボタンの裏に重要明細が隠れ得た | 読まずに実行、または重要情報へ到達不能 | 実行ボタンを明細の最後へ移動。上端・途中・末尾の案内を固定表示 | 288条件で末尾到達、ボタン非遮蔽、スクロール位置リセットを検査 |
| AR-004 | 元のvisual testが`scrollIntoView()`を使い、検査自身が画面状態を変えていた | PASSなのに初期表示を検証していない | 自然な初期位置を検査し、末尾は明示的にスクロール。各画面切替時に上端へ同期リセット | source/test hash付き証跡とtop/middle/bottom cue検査 |
| AR-005 | 320×568かつ大きな文字で、固定領域が明細を圧迫した | ボタンが末尾で完全表示されない | 小高さcontainer queryで非本質説明を圧縮。依頼原文は残し、明細領域を確保 | iPhone SE stress viewportをP0へ追加 |
| AR-006 | 日本語glyphのはみ出しと実際のclipを同一視した | 誤検知を避けるため検査を弱める誘惑 | `scrollWidth`だけでなく、text rangeと実際のclip境界を比較 | clipping判定ロジック自体を監査対象化 |
| AR-007 | JPYC手数料代理支払いの提供者、精算先、見積もりIDが曖昧 | 偽provider、二重回収、規約不明 | 法人名・連絡先・規約、契約先識別子、operation-bound quote ID、失敗時請求、期限を必須表示 | Fee disclosure keyの存在とfail-closed文言を自動検査 |
| AR-008 | POLが0でも「JPYCを交換すればよい」と読める余地 | 最初のtransactionを開始できない | zero-gas開始能力を証明できる代理支払い経路だけ許可。証明不能時は外部入金手順 | `0 POL`、proof、route固定、automatic fallback禁止を検査 |
| AR-009 | 手動手順に固定の0.05 POLを出す案 | 混雑・最低出金額・価格変化に不適合 | 対象操作に結び付いた推奨量と期限を実行時取得。取得不能なら送らない | `0.05 POL`の利用者向け固定指示を拒否 |
| AR-010 | 画面例の価格・残高・手数料が現在値に見え得た | 誤認に基づく取引 | 常時simulation watermark、各値へ「画面例」、情報の新しさ、見積もり期限を表示 | 外部通信0、watermark、example markerを検査 |
| AR-011 | 「一度だけ承認」が30分のsessionと30日の保存設定で混同され得た | 無期限権限と思わせる | 保存期間、利用中時間、無操作停止、1回/日/月、資産、network、相手を別行で表示 | scope expansion、新規相手、高額・全額は再確認というinvariant |
| AR-012 | source utteranceが正規化後の文章に置換される可能性 | 誤変換の証拠が消える | 「聞き取った言葉」と「確認した理解」を同時表示 | 「生産価格」の原文保持とhard gateを検査 |
| AR-013 | 「Bridge」「Vault」等が画面切替名へ戻る | 初心者が機能を選べない | 「別ネットワークへ送る」「運用口座」へ統一。技術名は詳細だけ | copy lintとprototype test |
| AR-014 | 部分成功後の再試行で完了済みstepを重複実行し得る | 二重売却・二重預入 | 完了、未開始、資産の現在位置を分離。残りだけを新しい見積もりで作成 | Saga/idempotency acceptance testとUI timeline |
| AR-015 | 複数のCodexプロンプトが独立に存在し、内容がdriftする | 古い指示でMainnet gateを緩める | `codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md`を機能仕様の唯一の正本にし、外部実行契約は別役割として固定し、rootの2ファイルは両方への参照用pointerへ変更 | adversarial auditで正本とpointerを検査 |
| AR-016 | 前版の自動検査が古いスクリーンショット名・120条件を固定 | 新しい画面が未検証でもPASS | 6 viewport×12 flow×2文字×2theme＝288条件、10画像へ更新 | validatorがevidence schema 2.0とsource hashを照合 |
| AR-017 | disabled buttonへ進める理由が画面下にあり、誤変換確認との関係が弱い | 利用者が故障と判断 | 誤変換確認fieldset直下へ理由を表示し、確認後にlive regionへ通知 | disabled state、announcement、confirmed copyを検査 |
| AR-018 | ダーク表示でwarning、muted text、disabled controlのコントラストが不明 | 読めない、意味が色だけになる | 全288条件でlight/dark contrast proxy、色以外の文言・形状を併用 | contrast ratio proxyとforced-colors CSS |
| AR-019 | 物理「1mm」とCSS pixelを同一視する主張 | 実機でのずれを隠す | browserはlogical-pixel proxyと明記。実機point/dp、safe area、font rendererはNO_GO | evidence limitationsと実機gate |
| AR-020 | App Store/Google Play/OpenAI適格性を実装完成と同一視 | 規約違反、審査拒否、法的提供リスク | 実装、Testnet、Store、法務を独立gateへ分離 | `PROJECT_STATUS.yaml`とGO/NO-GO matrix |
| AR-021 | ChatGPTから実行deep linkを作ればread-onlyを形式的に回避できる | 実質的な金融write促進 | transaction payload、署名要求、実行可能URLをChatGPT側から禁止 | tool contract negative testをCodex DoDへ追加 |
| AR-022 | 先物の清算価格が単一の安全保証に見える | cross marginや他position変動を無視 | 口座方式、担保、他position、成立価格で変動すると同画面で明示。欠損/staleは停止 | liquidation evidence/Testnet matrixを外部gate化 |
| AR-023 | 保存済みaliasだけで送金先を確認 | Address Book乗っ取り | 完全アドレス、指紋、network、変更検知を併記 | destination fingerprint invariant |
| AR-024 | 検証PASSをproduction安全PASSと読める | 過信 | 各報告へ「証明するもの／しないもの」を明示 | status validatorとassurance case |

| AR-025 | `getBoundingClientRect()`がscroll clipを無視するのに、そのまま可視control判定へ使用 | 完全に非表示の部品をcomposer遮蔽と誤判定し、真の遮蔽との区別が崩れる | overflow祖先とscreenで切り取った実描画矩形を計算し、その中心が自身／子要素へhitしなければ失敗 | topとreview末尾の全painted controlにelementFromPoint検査 |
| AR-026 | `START_HERE.html`自体がprototype matrix外 | 最初の入口だけ狭幅・dark・tableで崩れる | 320×800、390×844、1440×1000を明暗双方で独立検査 | 6条件、外部通信0、focus・center hit・containment |
| AR-027 | 任意に置いた承認値・fee cap・address・fingerprintが既定値／本番値に見える | 利用者が例をそのまま採用・コピー | 値の直近へ「画面例・初期値ではない」「ダミー」を表示 | prototype static copyと12flow検査 |
| AR-028 | screenshotの上端が明細block途中を切る | レビュー証拠として欠落・誤読 | sticky要約直下へblock境界を整列し、偶発focusを除去 | screenshot review stateとpartial-top-block assertion |

| AR-029 | 監査者の構文確認が`__pycache__`／`.pyc`を生成 | manifest外の不要物がZIPへ混入、再現性低下 | full pipeline冒頭でPython生成物だけを除去し、後段のarchive safetyとvalidatorでも残存を失敗 | clean tree full validationとZIP clean-extract検証 |

## 3. 対立した要求と決定

### 3.1 「実行ボタンを常に見せる」対「明細を読んだ後だけ見せる」

- 成長・操作速度側: 固定ボタンは迷いが少ない。
- 安全・初心者側: 固定ボタンは重要な末尾情報を読まずに押せ、短い端末では明細を隠す。
- 決定: 実行ボタンは明細の最後。固定領域には「下に続く／ここが最後」の状態だけを表示する。頻用者の短縮は、将来の明示的なsummary modeで検討し、critical fieldを省略しない。

### 3.2 「自然言語を賢く補完」対「聞き返して停止」

- 利便性側: 「生産価格」を自動で清算価格と解釈したい。
- 安全側: 重要語の誤変換は取引意味を変える。
- 決定: 候補として正規化するが、原文と解釈を並べ、明示確認まで実行をhard blockする。低リスクの表記揺れと、金額・方向・相手などのmaterial ambiguityを区別する。

### 3.3 「最初の1回だけ承認」対「操作ごとの確認」

- 利便性側: 毎回署名では会話型の価値が薄い。
- セキュリティ側: 包括承認は被害半径が大きい。
- 決定: 期限、資産、network、宛先、1回/日/月上限、倍率、手数料を束縛したStanding Authorizationだけを許可。新規宛先、高額、全額、鍵・権限変更は毎回step-upする。

### 3.4 「JPYCだけで自動解決」対「zero-gasでは停止」

- 初心者体験側: JPYCしかなくても送れるべき。
- EVM現実側: native fee assetが0なら通常swap自体を開始できない。
- 決定: 検証済みaccount abstraction/代理支払いがある場合だけ自動。提供者・費用・期限・失敗請求を表示できなければ、固定量を推測せず手動入金へ切り替える。

## 4. 解決していないためNO-GOの事項

次は、このZIP内で「修正済み」とは扱わない。

- Kotlin/Compose、Swift/SwiftUI、backend、Signer、Adapterのproduction実装
- Pixel 9a、iPhone実機のsafe area、IME、VoiceOver/TalkBack、生体認証、鍵失効
- Hyperliquid Testnetのorder/fill/liquidation/partial/reorg evidence
- JPYC EX契約、production credential、正式registryのrelease pin
- sponsor/paymaster/relayerの選定、監査、資金、法務、abuse control
- Threshold ECDSA/MPC/HSM、recovery drill、外部暗号監査
- 日本その他の対象地域における法的提供可能性
- Apple/Googleの提出主体、金融機能申告、地域適格性、審査結果
- 未知の脆弱性、将来の規約・プロトコル・法令変更

## 5. 結論

前版に対する無条件の「100%自信」は撤回する。2026-07-29.1は、発見した重大な仕様矛盾、UI到達性、検証汚染、zero-gas説明、重複指示を修正し、合理的に予見できた問題をテストまたはNO-GO条件へ変換した版である。

この結論は、**実装前パッケージとして高い内部信頼性を持つ**という意味であり、実資金を扱うproduction walletが完成したという意味ではない。
## 2026-07-29.1 追加の独立監査

旧PASSを前提にせずvalidator自身を実行・破壊fixture・source reviewで再確認した。実際に、package identity drift、Markdown checkerのcompile failure、OAuth URLのfalse positive、visual skip、negative zero／巨大整数、YAML implicit type、host directory mode依存、ZIP timestamp表現差を発見した。各問題は実装修正、LR-025〜LR-032、Security Invariants 153〜160、validator self-testへ変換した。production／native／Testnet／MainnetのNO-GOは変更していない。
