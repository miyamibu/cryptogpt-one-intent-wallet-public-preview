# Known-Loophole Register

**目的:** 既知の現実的な抜け穴を、実装・試験・公開停止条件へ変換する。

これは「宇宙に存在する全攻撃を列挙した」と主張する文書ではない。未知の脆弱性は残る。代わりに、未知を理由にGOへ進まないための監視・監査・資産上限も定義する。

登録件数: **436**

| ID | 抜け穴 | 影響 | 修正／検証 |
|---|---|---|---|
| AI-001 | 質問を注文と誤認 | 無断注文 | 実行分類と具体ボタン。質問ラベルはoperations=0 |
| AI-002 | 否定文を見落とす | 反対注文 | 否定・引用・伝聞の専用評価 |
| AI-003 | 条件文を即時命令化 | 早すぎる注文 | 条件をCapsuleのpreconditionにし、再承認 |
| AI-004 | 引用内の命令を実行 | 無断注文 | quoted spanを非実行文脈に固定 |
| AI-005 | Web prompt injection | 宛先差替え | Web/RAGとexecution parserを分離 |
| AI-006 | 同名asset幻覚 | 偽token | asset aliasは署名済みregistryで解決 |
| AI-007 | アドレス生成 | 誤送金 | LLM output schemaにaddress fieldを持たせない |
| AI-008 | contract生成 | malicious call | LLMはcontractを指定不可 |
| AI-009 | 金額の桁誤認 | 過大注文 | Decimal parser＋Card表示＋policy |
| AI-010 | 万・億・全角数字誤認 | 過大注文 | locale corpus＋deterministic normalization |
| AI-011 | 音声認識誤り | 誤注文 | 音声transcriptを表示し具体Cardで承認 |
| AI-012 | model update regression | 誤認率増加 | snapshot pin＋full eval gate |
| AI-013 | confidenceを許可と誤用 | 無断実行 | confidenceはpolicy inputに使わない |
| AI-014 | チャット履歴の古い指示混入 | 誤注文 | current turnとselected plan IDを固定 |
| AI-015 | 複数候補の勝手な選択 | 誤操作 | ambiguousならinline選択必須 |
| AI-016 | OpenAI／AI provider API keyをmobile binaryへ埋め込む | key抽出、費用悪用、直接呼出し | provider credentialはserver-side secret managerのみ。mobileからproviderへ直接接続禁止 |
| AI-017 | 任意の非取引Support Gatewayが未認証client／replay／botに開放 | 費用枯渇、abuse、DoS | user＋device auth、nonce、rate／budget limit、replay防止、abuse isolation |
| AI-018 | mobileがAI providerへ直接接続し非取引Support policyを迂回 | schema／privacy／model pinning不整合 | 取引Intent ParserはOpenAI egress禁止。任意の非取引Supportはfirst-party Gateway経由だけ |
| AI-019 | 非取引Support request／response／provider errorをobservabilityへ無加工送信 | 禁止された取引文・address・残高・credential漏えい | fixed-field allowlist、redaction、retention、support access audit、secret canary test |
| UI-001 | 曖昧な送信ボタン | 認識不足 | button labelに操作・asset・金額 |
| UI-002 | buy/sell色だけで表示 | 誤認 | text/icon併用 |
| UI-003 | アドレス省略でpoisoning | 誤送金 | full-view＋source＋checksum |
| UI-004 | chain表示欠落 | 誤chain | HyperCore/Arbitrum/HyperEVMを明示 |
| UI-005 | feeの古い値 | 不足/誤認 | runtime timestamp付き |
| UI-006 | slippage非表示 | 損失 | min output/max slippage必須 |
| UI-007 | Vault APYだけ強調 | リスク誤認 | lock/DD/positions/profit share併記 |
| UI-008 | partial successを完了表示 | 二重操作 | PARTIAL状態とasset location |
| UI-009 | undoと誤表示 | 新規反対売買 | 約定後は取消不可を明示 |
| UI-010 | アクセシビリティ読み上げ欠落 | 誤操作 | TalkBack test |
| AUTH-001 | セッションが長すぎる | 盗難悪用 | 短時間、background lock |
| AUTH-002 | 新規宛先もセッション認証だけ | 盗難送金 | auth-per-use＋cooldown |
| AUTH-003 | 高額閾値回避の分割 | 資産流出 | rolling daily/velocity limits |
| AUTH-004 | 生体追加後も旧鍵有効 | 乗っ取り | invalidation policy＋recovery |
| AUTH-005 | device credential reset | 鍵悪用/失効 | write stop＋re-enrollment |
| AUTH-006 | replayしたauthorization | 二重実行 | challenge＋capsule hash＋one-time use |
| AUTH-007 | Integrity token別planへ流用 | bypass | requestHashへsemanticHash |
| AUTH-008 | admin一人でgate解除 | insider | two-person approval |
| KEY-001 | seed入力 | 全資産流出 | 入力機能を作らない |
| KEY-002 | private key log | 漏えい | structured redaction＋CI secret test |
| KEY-003 | MPC vendor単独署名 | custody/theft | cryptographic/control review |
| KEY-004 | device share＋server share共謀 | 全資産 | user factor／limits／audit |
| KEY-005 | recovery share紛失 | 回収不能 | 初回recovery drill |
| KEY-006 | recovery takeover | 全資産 | delay＋multi-factor＋notification |
| KEY-007 | agentをtrade-onlyと誤認 | 被害拡大 | protocol scopeではないと扱う |
| KEY-008 | agent address再利用 | replay | replacement後burn扱い |
| KEY-009 | generic sign endpoint | 任意署名 | typed buildersのみ |
| KEY-010 | raw typed-data proxy | 任意action | action-specific builder＋policy |
| KEY-011 | root/trade signer同一process | 権限昇格 | service/network/IAM分離 |
| KEY-012 | backupにsecret含有 | 複製 | Auto Backup/D2D除外 |
| KEY-013 | AES-GCM nonce再利用 | key compromise | unique random nonce＋test |
| KEY-014 | secp256k1をKeystore保証と誤認 | 実装破綻 | P-256 auth/AES wrapping or audited MPC |
| HL-001 | account addressとagent address混同 | 空データ/誤state | queryはactual account |
| HL-002 | nonce衝突 | 拒否/unknown | signer単位atomic allocator |
| HL-003 | clock skew | nonce拒否 | trusted time＋window guard |
| HL-004 | timeout blind retry | 二重注文 | cloid/state reconcile |
| HL-005 | cloid重複 | 誤state | plan/step/generationで一意 |
| HL-006 | field order差 | 署名不一致 | official SDK golden vector |
| HL-007 | trailing zero差 | 署名不一致 | wire serializer固定 |
| HL-008 | address case差 | 署名不一致 | canonical serializer |
| HL-009 | mainnet/testnet replay | 資産操作 | environment/domain tests |
| HL-010 | Spot asset index固定 | 別asset | runtime metadata |
| HL-011 | tick/lot固定 | 拒否/丸め損 | runtime decimals |
| HL-012 | account mode推測 | 残高誤計算 | mode runtime取得 |
| HL-013 | Portfolio Margin通常扱い | 清算リスク | feature gate/small test |
| HL-014 | subaccount全員利用可と仮定 | onboarding破綻 | capability detection |
| HL-015 | rate limit無視 | 非常口不能 | budget/cancel reserve |
| HL-016 | WSだけでstate確定 | 欠落 | REST reconcile |
| HL-017 | partial fill無視 | 過剰再注文 | filled/remain tracking |
| HL-018 | cancel race | 誤表示 | fill/cancel order reconciliation |
| HL-019 | scheduleCancelを決済と誤認 | ポジション残存 | open order onlyと明示 |
| HL-020 | reduceOnly未設定 | 反転ポジション | close pathで強制 |
| HL-025 | ユーザー指定の損切りをActionPlan／Capsuleが黙って落とす | 裸のポジション | actionable-clause coverage＋schema/test |
| HL-026 | fill前の推定価格でSLを固定、またはSL配置失敗後もポジションを残す | 想定外損失 | actual weighted fill formula＋placement deadline＋pre-authorized reduce-only close |
| MARKET-001 | price stale | slippage | snapshot age/drift |
| MARKET-002 | oracle異常 | 清算 | oracle/mark divergence guard |
| MARKET-003 | 低流動性 | 価格損失 | depth-based impact cap |
| MARKET-004 | OI cap | 注文拒否 | specific error/再送しない |
| MARKET-005 | gapでSL滑る | 損失 | market/limit SL tradeoff表示 |
| MARKET-006 | ALLでmargin不足 | 清算/拒否 | SAFE_ALL reserve |
| BR-001 | 偽Bridge address | 全資産流出 | signed allowlist＋code hash |
| BR-002 | wrong chain | 資産損失 | chain ID固定 |
| BR-003 | wrong USDC | 未credit | token address検証 |
| BR-004 | 最低額未満 | 資産損失 | runtime minimum reject |
| BR-005 | paused contract | 資産滞留 | paused check |
| BR-006 | Permit spender差替え | allowance theft | typed field verify |
| BR-007 | Permit deadline過長 | replay窓 | short deadline |
| BR-008 | unlimited Permit | 将来流出 | exact value |
| BR-009 | tx成功=credit完了と誤認 | 二重入金 | HyperCore credit確認 |
| BR-010 | withdraw accepted=着金完了と誤認 | 状態誤認 | Arbitrum finalization/credit |
| BR-011 | fee/time固定 | 仕様差 | runtime source/timestamp |
| BR-012 | 外部Bridgeへ自動fallback | 新リスク | 再承認＋allowlist |
| VAULT-001 | HLPとuser vault混同 | lock/fee誤認 | adapter分離 |
| VAULT-002 | profit share非表示 | 収益誤認 | Cardに明示 |
| VAULT-003 | lock更新見落とし | 資金拘束 | runtime lock |
| VAULT-004 | withdraw slippage無視 | 損失 | open positions/impact表示 |
| VAULT-005 | malicious HyperEVM vault | 盗難 | code/ABI/selector allowlist |
| VAULT-006 | proxy upgrade | 後日盗難 | implementation monitor |
| VAULT-007 | admin key risk非表示 | リスク誤認 | metadata/risk tier |
| VAULT-008 | unlimited allowance | 後日流出 | exact allowance/revoke |
| VAULT-009 | oracle manipulation | 損失 | oracle registry/risk |
| VAULT-010 | APY extrapolation | 誤誘導 | past performance warning |
| SAGA-001 | 1承認を原子性と誤認 | 部分失敗 | NON_ATOMIC表示 |
| SAGA-002 | step dependency欠落 | 順序誤り | DAG validation |
| SAGA-003 | 成功step自動逆取引 | 追加損失 | manual recovery |
| SAGA-004 | restartで二重再開 | 二重処理 | event store/idempotency |
| SAGA-005 | unknown stateをfailed扱い | 二重処理 | UNKNOWN＋reconcile |
| SAGA-006 | 後続金額が推定のまま | 不足/過剰 | actual output reference |
| MOB-001 | repackaged app | 鍵窃取 | signing cert/Integrity |
| MOB-002 | overlay tapjacking | 誤承認 | risk signal/secure UI |
| MOB-003 | accessibility control | 誤操作 | high-risk restriction |
| MOB-004 | clipboard hijack | 誤address | Address Book/QR verified |
| MOB-005 | screenshotにrecovery | 漏えい | FLAG_SECURE |
| MOB-006 | notificationに残高/宛先 | 漏えい | redacted notification |
| MOB-007 | root detectionを絶対視 | bypass | defense-in-depth |
| MOB-008 | app updateでmigration破損 | 鍵喪失 | migration/recovery test |
| BE-001 | SSRFでmetadata差替え | malicious registry | fixed upstream/egress |
| BE-002 | DB改ざんでaddress変更 | 誤送金 | versioned signed entries |
| BE-003 | feature gate改ざん | Mainnet解放 | signed gate/two-person |
| BE-004 | audit log削除 | 証拠喪失 | append-only/hash chain |
| BE-005 | dependency compromise | 任意コード | lock/SBOM/signatures |
| BE-006 | CI secret leakage | 鍵流出 | OIDC/ephemeral secrets |
| BE-007 | admin session theft | 権限奪取 | hardware MFA/short session |
| BE-008 | log injection | 監査混乱 | structured events |
| PRIV-001 | OpenAIへfull address送信 | プライバシー | alias only |
| PRIV-002 | OpenAIへ全履歴送信 | 漏えい | minimum context |
| PRIV-003 | Responses保存設定誤り | 保持 | store:false/config test |
| PRIV-004 | supportが秘密閲覧 | 漏えい | RBAC/access logs |
| LEGAL-001 | 非カストディ表示で登録回避と誤認 | 違法リスク | written legal opinion |
| LEGAL-002 | Perp媒介の評価漏れ | 登録違反 | FIBO analysis |
| LEGAL-003 | Spot仲介制度を誤用 | 登録違反 | affiliated provider条件確認 |
| LEGAL-004 | USDC分類漏れ | 規制違反 | 電子決済手段評価 |
| LEGAL-005 | AI助言化 | 投資助言 | content boundaries/legal review |
| LEGAL-006 | builder fee利益相反 | 消費者/規制 | fee disclosure/legal gate |
| OPS-001 | kill switchがAI依存 | 停止不能 | manual deterministic path |
| OPS-002 | 公式情報監視なし | 仕様逸脱 | daily source diff |
| OPS-003 | 公式アプリを装う | 詐欺誤認 | unofficial branding |
| OPS-004 | support DM詐欺 | seed窃取 | in-app verified support |
| OPS-005 | 法務前提変更を見落とす | 違法提供 | assumption hash/expiry |
| AUTH-009 | BiometricPromptを取引内容のTrusted Displayと誤認 | 誤内容承認 | R4／non-exempt R3はprotected／external display |
| AUTH-010 | Protected ConfirmationのpromptTextが不完全 | 宛先/fee誤認 | canonical critical fields |
| AUTH-011 | Protected Confirmation非対応時にsilent downgrade | 誤送金 | external displayまたはNO_GO |
| KEY-015 | agent key漏えいでproduct signer policyを迂回 | 不正L1 action | bearer credential前提、隔離、revoke |
| KEY-016 | agentが署名可能なaction未把握 | 想定外権限 | Testnet characterization |
| CAP-001 | renderReceiptHashを人間確認の証拠と誤認 | UI欺瞞 | Trusted Displayを別管理 |
| CAP-002 | JSON duplicate key／Unicode／number曖昧性 | hash差替え | strict parser/JCS vectors |
| CAP-003 | 長い新規addressを省略promptだけで承認 | poisoning | trusted registration/full fingerprint |
| HL-021 | UI sessionごとにagentを発行し上限超過 | replacement/停止 | lifecycle manager/current limit |
| HL-022 | 単一APIがstale/侵害 | 誤state | independent source quorum |
| HL-023 | CompilerとSignerが同じsourceを盲信 | common-mode | signer independent recheck |
| HL-024 | agent product-policy外actionをprotocolが受理 | 資産/position影響 | characterization＋bounded account |
| MARKET-007 | 独立sourceに見える二系統が同一cache | false quorum | independence class inventory |
| BR-013 | HyperCore Testnet成功をBridge parityと誤認 | Mainnet不具合 | fork/harness/canary別gate |
| BR-014 | Testnet faucet前提を無視 | テスト不能/資金誤解 | address/deposit prerequisite管理 |
| BR-015 | Permit owner/user/credit先の意味を誤る | 誤入金 | typed owner/user/recipient test |
| SAGA-007 | forged prior outputでREMAINDER増額 | 過大出金 | chain-confirmed output＋hard bound |
| SAGA-008 | 長時間Saga中にpolicy/contract変更 | 旧許可実行 | per-step revalidation/max duration |
| MOB-009 | Pixel 9aのProtected Confirmation対応を推測 | 実装破綻 | `isSupported`＋実機evidence |
| MOB-010 | accessibilityでconfirmation unavailable | unsafe fallback | explicit block/fallback test |
| BE-009 | state quorum service自体が単一障害 | 誤state | source-independent signer check |
| BE-010 | release manifestのsource pinが古い | 仕様逸脱 | expiry/diff/no-go |
| PRIV-005 | 会話から取引戦略・資産状況が過送信 | プライバシー | minimization/redaction/retention |
| LEGAL-007 | Google Play金融機能を過少申告 | reject/removal | accurate declaration evidence |
| LEGAL-008 | Store通過を法的適法性と誤認 | 規制違反 | legal and store gates independent |
| OPS-006 | Google Play暗号資産ポリシー適格性を仮定 | 配布不能 | review/documents/region gate |
| OPS-007 | emergency RTOをchain完了保証と誤表示 | 誤期待 | request acceptanceとchain outcome分離 |
| OPS-008 | visual evidence更新後にmanifestを再生成しない | 古いchecksumで偽PASS／配布不整合 | ordered validation runner、manifest最終生成、clean-extract verification |
| TEST-001 | Testnet成功をMainnet同等性証明とする | 未検出欠陥 | own-wallet canary after gates |
| TEST-002 | local forkのcode/stateが実際と不一致 | 偽PASS | pinned bytecode/block/source |
| OPENAI-001 | ChatGPT read-only appから注文payload入りdeep link | 規約上のfacilitation／誤実行 | action-carrying link禁止、独立アプリで再入力 |
| OPENAI-002 | ChatGPTへ取引固有の下書き・ボタン手順・復旧手順を返す | 「実行しない」read-only表示でも金融取引を実質的に促進し得る | 固定read-only状態、固定用語・エラー、一般安全案内、中立handoffだけ。取引Intentと手動復旧は独立wallet内へ隔離 |
| UX-011 | 1 Intentを1署名と表示 | wallet確認回数の隠蔽 | mode別署名回数を事前表示 |
| AUTH-012 | AuthorizationがsemanticHashだけを束縛 | render／prompt差替え | 4 hash＋challengeのEnvelope |
| AUTH-013 | prompt内fingerprint生成がhashと循環 | 不一致／実装破綻 | semantic core先行hash＋promptを別束縛 |
| AUTH-014 | 新規宛先を省略addressだけでProtected Confirmation | address poisoning | full addressまたは登録alias＋fingerprint |
| AUTH-015 | R3 standing例外をProtected Confirmation失敗時の即席fallbackとして発行 | 認証downgrade／誤送金 | 事前R4 ceremony、cooling、hard cap、signed policy、変更時失効 |
| CAP-004 | example hashがダミーのまま | 実装者が誤採用 | canonical hash toolで再計算・CI検証 |
| CAP-005 | sourceStateHashとStateEvidenceが不一致 | stale／偽state | canonical evidence hash検証 |
| WALLET-001 | Existing Wallet root actionをセッション署名可能と仮定 | UX／権限設計破綻 | wallet方式ごとに個別検証、原則都度署名 |
| WALLET-002 | 複合Sagaの複数wallet promptを隠す | 誤認承認 | 実行前に予想署名回数とmodeを表示 |
| WALLET-003 | dynamic remainderのroot actionを事前署名 | 金額不一致／replay | actual output後にjust-in-time署名 |
| IOS-001 | Secure Enclave P-256をsecp256k1 root keyと誤認 | 署名不能／危険なsoftware fallback | P-256はAuthorization Keyのみ、rootはexternal/MPC |
| IOS-002 | App AttestをTrusted Displayと誤称 | 誤内容承認 | assuranceをNOT_TRUSTED_DISPLAYに固定 |
| IOS-003 | App Attest非対応端末をsilent allow | 偽app／risk増大 | capability negotiation＋signed fallback |
| IOS-004 | App Attest keyが再install後も残ると仮定 | lockout／誤device binding | re-enrollmentとrecovery test |
| IOS-005 | assertion counterを検証しない | replay | server monotonic counter |
| IOS-006 | App Attest challengeがCapsule hash未束縛 | 別操作流用 | 4 hash＋session＋policyをclientDataへ |
| IOS-007 | Keychain itemがiCloud同期 | secret拡散 | ThisDeviceOnly＋non-synchronizable |
| IOS-008 | biometric enrollment変更後も鍵利用可能 | 追加指紋／顔で不正認証 | biometryCurrentSet policy |
| IOS-009 | passcode removalを検知しない | device security低下 | key invalidation／re-enrollment |
| IOS-010 | background snapshotに資産／address | privacy leakage | scene phase blur |
| IOS-011 | screen recordingを完全防止可能と表示 | 誤安全感 | capture detectionはbest-effortと明示 |
| IOS-012 | screenshot通知を事前防止と誤認 | secret capture | recovery materialを表示しない |
| IOS-013 | general pasteboardへsecret | cross-app leakage | secret copy禁止 |
| IOS-014 | address clipboardが無期限 | poisoning／privacy | localOnly＋expiration＋paste recheck |
| IOS-015 | custom URL schemeを唯一のwallet callbackにする | callback hijack | Universal Links／correlation nonce |
| IOS-016 | deep link payloadを即実行 | 無断出金 | draftのみ、app内再compile |
| IOS-017 | Siri／Shortcutからwrite | 音声誤認／ロック画面操作 | MVP write App Intents禁止 |
| IOS-018 | push actionから決済 | 誤tap／locked device | notificationはread-only |
| IOS-019 | external wallet返却accountを未検証 | 別account署名 | expected account／chain／payload再検証 |
| IOS-020 | Face ID cancel後のAuthorization再利用 | 無承認実行 | challenge／capsule失効 |
| IOS-021 | device migration後にold deviceを有効のまま | 二重端末権限 | device registry revoke／risk gate |
| IOS-022 | Secure Enclave unavailableでsoftware keyへ自動降格 | root compromise | fail closed／external wallet |
| IOS-023 | Keychain accessibilityがbackgroundまで広すぎる | secret exposure | most restrictive class |
| IOS-024 | crash reportへattestation／signature material | privacy／replay surface | redaction／secret scanner |
| IOS-025 | TestFlight buildをproduction安全と誤認 | 未監査Mainnet | distributionとMainnet gate分離 |
| XPLAT-001 | SwiftとKotlinでhash canonicalization drift | 別payload署名 | shared vectors／byte equality |
| XPLAT-002 | localeごとにsemantic amountが変化 | 桁誤り | display localeとcanonical value分離 |
| XPLAT-003 | OS別risk tierが暗黙に異なる | 一方だけ弱い認証 | cross-platform decision table |
| XPLAT-004 | shared frameworkがplatform security差を隠す | silent downgrade | capability enumをdomainへ |
| XPLAT-005 | Rust FFI ownership bug | crash／memory corruption | safe wrappers／fuzz／sanitizers |
| XPLAT-006 | FFI DTO version mismatch | field欠落 | schema/version negotiation |
| XPLAT-007 | community SDKだけで署名実装 | protocol mismatch | official Python golden oracle |
| XPLAT-008 | AndroidだけTestnet PASSでiOSもGO | platform欠陥 | platform別release gate |
| XPLAT-009 | iOSだけUI PASSでAndroidもGO | platform欠陥 | device matrix別evidence |
| XPLAT-010 | 同じbuild numberを別commitで再利用 | 証拠混乱 | immutable build provenance |
| XPLAT-011 | shared registry cacheが全platform共通障害 | 誤asset／address | signed version＋independent recheck |
| XPLAT-012 | time zone差でexpiry不一致 | 拒否／期限外実行 | UTC monotonic／clock skew bound |
| XPLAT-013 | mobileとbackendのDecimal scale差 | 過大／過小注文 | scale vectors／integer units |
| XPLAT-014 | platform-specific warningが片方で欠落 | risk非表示 | critical disclosure conformance |
| XPLAT-015 | native navigationで同じplanを二重保持 | stale execution | single active capsule authority |
| XPLAT-016 | 文書／platform間でR2・R3・R4の意味がずれる | 一方だけ弱い認証／誤Feature Gate | canonical tier tableを一つに固定し、cross-doc／code parity test |
| A11Y-001 | VoiceOverが金額を桁ごと誤読 | 誤認 | semantic label＋locale speech test |
| A11Y-002 | TalkBack focus順がvisualと違う | 別button誤操作 | focus order test |
| A11Y-003 | 200% textでfeeがclip | 未開示実行 | critical clipping zero gate |
| A11Y-004 | 色だけでlong／short | 色覚で誤認 | text＋icon |
| A11Y-005 | warningをhapticだけで通知 | 情報欠落 | text＋icon＋optional haptic |
| A11Y-006 | reduce motionでstate changeが消える | 状態不明 | non-motion indicator |
| A11Y-007 | switch controlでdestructiveへ先にfocus | 誤操作 | logical navigation order |
| A11Y-008 | addressを一続きで読み上げ理解不能 | 検証不能 | chunk／fingerprint speech mode |
| A11Y-009 | large content viewer未対応icon | 意味不明 | accessible labels／larger hit area |
| A11Y-010 | dynamic typeでbutton tap area縮小 | 誤tap | min target independent of text |
| PIXEL-001 | 1px dividerがhalf-pixelでぼやける | 視認性低下 | pixel-aligned rendering |
| PIXEL-002 | spinner出現でamountが1px移動 | 誤比較 | fixed layout slot |
| PIXEL-003 | pressed stateでlabel位置が動く | 誤認／低品質 | transformなし／visual diff |
| PIXEL-004 | safe area不足でhome indicatorとbutton重複 | 誤tap | inset tests |
| PIXEL-005 | camera cutoutとnetwork badge重複 | 情報欠落 | safe area layout |
| PIXEL-006 | IMEでprimary actionが隠れる | 操作不能 | IME insets／scroll |
| PIXEL-007 | 長い英語labelがclip | 意味欠落 | multiline button／matrix |
| PIXEL-008 | 日本語glyphと数値baselineずれ | 可読性低下 | font metric review |
| PIXEL-009 | address末尾がcard外へoverflow | 宛先検証不能 | wrap／monospace component |
| PIXEL-010 | dark modeでwarning contrast不足 | 警告不可視 | contrast tests |
| PIXEL-011 | disabled stateとenabled stateが同じ | 誤tap | state contrast＋reason |
| PIXEL-012 | destructiveとnormal buttonのhit area重複 | 誤実行 | 8pt/dp gap＋hit map test |
| PIXEL-013 | partial stateにgreen check | 完了誤認 | state-specific icon/text |
| PIXEL-014 | rounded card内のnested radius逆転 | 階層混乱 | radius token hierarchy |
| PIXEL-015 | font fallbackで数字幅が変わる | 桁位置ずれ | tabular figures／font pin |
| PIXEL-016 | visual testのbrowser／Playwright versionが証跡と不一致 | 差分再現不能／偽PASS | toolchain version記録、requirements pin、source hash binding |
| STORE-IOS-001 | 個人developerでwallet公開可能と仮定 | 審査拒否 | organization gate |
| STORE-IOS-002 | 暗号資産取引の地域認可を未確認 | 審査／法的リスク | region/license evidence |
| STORE-IOS-003 | Perp提出主体要件を無視 | 審査拒否 | written App Review/legal memo |
| STORE-IOS-004 | TestFlightを規制回避の一般配布に使用 | program risk | closed testing policy |
| STORE-IOS-005 | review用に機能を隠す | removal／account termination | accurate review notes |
| STORE-IOS-006 | Hyperliquid公式を装うmetadata | impersonation | unofficial branding |
| STORE-IOS-007 | third-party SDK privacy disclosure漏れ | rejection／privacy | SDK inventory／nutrition labels |
| STORE-IOS-008 | demo modeが実機能と違う | review deception | same decision logic／mock transport |
| STORE-IOS-009 | App Store通過を日本法GOと扱う | 違法提供 | independent legal gate |
| STORE-IOS-010 | 地域変更後もfeatureが有効 | unauthorized service | server region gate＋recheck |
| ADMIN-001 | Mainnet enableをtoggle一つで実行 | 誤解放 | two-person signed approval |
| ADMIN-002 | 管理consoleがuser appと同じauth | privilege escalation | separate domain／hardware MFA |
| ADMIN-003 | kill switchが同一backend障害に依存 | 停止不能 | out-of-band control |
| ADMIN-004 | support roleがfull address／balance全件閲覧 | privacy | least privilege／purpose binding |
| ADMIN-005 | feature gate変更にexpiryなし | 恒久危険設定 | time-bound gate |
| ADMIN-006 | registry rollbackがold malicious entryを復活 | 誤送金 | monotonic version／revocation |
| ADMIN-007 | audit exportにsecret | leakage | field allowlist |
| ADMIN-008 | incident中にsource quorumを緩める | 誤state | emergency policy still fail closed |
| ADMIN-009 | 同一人物が全承認roleを代行 | separation破綻 | independent approver identity |
| ADMIN-010 | minimum app version blockでemergency readも不能 | 資産把握不能 | read/emergency compatibility path |
| REC-IOS-001 | recovery shareを写真で保存させる | cloud leakage | offline recovery ceremony |
| REC-IOS-002 | 端末紛失で旧device share未失効 | 不正署名 | revoke＋reshare |
| REC-IOS-003 | server停止でrecovery手順がserver依存 | 資産凍結 | independent recovery tool |
| REC-IOS-004 | biometric変更をaccount takeoverと誤検知し永久lock | 資産凍結 | graded recovery |
| REC-IOS-005 | recovery後にstanding destinationが残る | 旧設定悪用 | policy reset／cooling |
| REC-IOS-006 | new iPhone restoreでApp Attest identityを流用 | device binding破綻 | new enrollment |
| REC-IOS-007 | MPC vendor export不能 | vendor lock-in | exit test／documented format |
| REC-IOS-008 | recovery toolの署名供給chain未監査 | key theft | reproducible build／offline verify |
| COPY-001 | 主要画面へPerp／Spot／Bridge等の難しい語が戻る | 初心者の誤解・誤操作 | 表示語辞書、copy lint、画面検査、技術語は詳細表示だけ |
| VOICE-001 | 「生産価格」を別の項目として扱う | 清算危険を確認できない | 先物文脈では清算価格候補として明示し、読み取り結果を表示 |
| LIQ-001 | 古い口座状態で清算価格を表示 | 誤った安全余裕 | freshness、source quorum、取得時刻、stale時fail closed |
| LIQ-002 | cross marginで単一清算価格だけを安全保証に使う | 他position変動で突然清算 | 口座方式、担保使用率、全体影響を表示し、値が不適切なら非表示 |
| FEE-001 | JPYCしかなくnative balance 0でも通常swap可能と仮定 | swap開始不能・資金停止 | sponsor／paymaster検証または具体的な外部入金手順へ分岐 |
| FEE-002 | 手数料自動補充が小額を繰り返し月間上限を迂回 | JPYC過剰消費 | atomic monthly counter、concurrency test、per-action＋monthly cap |
| FEE-003 | sponsorを偽装したproviderが費用回収 | 資産損失 | provider／contract pin、operation hash、最大費用、署名付きreceipt |
| FEE-004 | 古いquoteや薄い流動性で高額交換 | 価格損失 | quote expiry、最低受取、価格ずれ上限、route allowlist、simulation |
| JPYC-001 | 旧前払式JPYCまたは偽contractを正式JPYCとして扱う | 受取資産誤認 | versioned registry、network／contract照合、複数source pin |
| JPYC-002 | JPYC EX連携APIを最終申込み代行と誤認 | 法務・本人確認回避 | handoff範囲を型で限定し、最終確認はJPYC EXと表示 |
| GPT-001 | ChatGPT toolへ送金・取引writeが追加される | OpenAI規約違反・無断実行面 | read-only tool allowlist、CI contract test、action carrying link禁止 |
| MANUAL-001 | アプリ更新後も古いボタン名の手順を表示 | 復旧不能・誤操作 | app version付きsigned catalog、UI test ID連携、expiry |
| STAUTH-001 | 「一度承認」を無期限・無制限として実装 | 広範な資産損失 | exact scope、expiry、hard caps、revocation、scope expansion再承認 |
| UI-REV-001 | 固定CTAが重要明細を覆う | 未確認実行・情報到達不能 | CTAをreview末尾へ置き、上端・途中・末尾案内と非遮蔽test |
| UI-REV-002 | CTAが末尾にあってもsticky領域と重なる | 押下不能・誤押下 | bottom hit-test、中心点elementFromPoint、最小端末stress |
| UI-REV-003 | 画面切替後に前画面のscroll位置が残る | 重要な上段情報を見落とす | render時同期reset、flow/theme/text切替test |
| UI-REV-004 | 大きな文字で依頼原文を隠す | 音声誤認の証拠消失 | source utteranceを全text modeで保持 |
| UI-REV-005 | 日本語glyphの光学的overhangをclipと誤判定 | 検査を無効化・誤った修正 | text rangeと実clip境界を分離して測定 |
| UI-REV-006 | 320×568で明細領域が極端に小さい | 確認不能 | iPhone SE stressをP0化し、非本質copyだけ圧縮 |
| UI-REV-007 | ボタンの見た目は離れていてもhit領域が重なる | 意図しない操作 | hit-test可能controlの矩形交差を検査 |
| UI-REV-008 | 色だけでwarning状態を示す | 色覚・高contrast環境で意味消失 | 文言・badge・borderを併用し全theme contrast proxy |
| UI-REV-009 | browser pxを物理1mmの保証として表現 | 実機ずれを隠す | logical-pixel proxyと明記しnative実機gateを分離 |
| UI-REV-010 | disabled理由がボタンから離れる | 故障と誤認 | 誤変換確認直下に理由とlive announcementを配置 |
| TEST-REV-001 | `scrollIntoView()`でtestが都合のよい状態を作る | 初期状態の欠陥を見逃す | 自然な初期状態と明示scrollを分離 |
| TEST-REV-002 | 古いmatrix件数をvalidatorが固定 | 新しい画面未検証でもPASS | evidence schema 2.0、288件、10画像を厳密照合 |
| TEST-REV-003 | source更新後も古いvisual evidenceを再利用 | 証跡偽装 | prototype/test harness SHA-256をevidenceへ束縛 |
| TEST-REV-004 | lightだけ詳細検査しdarkはsmokeのみ | dark固有の読不能を見逃す | light/darkを全288組合せで同等検査 |
| TEST-REV-005 | screenshot名だけ存在し内容が空・極小 | 見た目証拠がない | required set、最低size、manifest hashを検査 |
| TEST-REV-006 | test localeを記録しない | 日本語renderer条件が不明 | `localeExecuted: [ja-JP]`を証拠へ記録 |
| TEST-REV-007 | validation後にmanifest対象を変更 | checksumが古い | 派生物→敵対監査→manifest→validatorの順序固定 |
| TEST-REV-008 | package内にpycache／symlink／case衝突 | 配布差異・path攻撃 | adversarial auditとdeterministic ZIP builderで拒否 |
| MATH-REV-001 | 最低額と最大額を同じ「残り」と表示 | 到着額過大表示 | min/max型を分離し表示値を再計算 |
| MATH-REV-002 | 複合処理の手数料差引前後が不明 | 期待残高の誤認 | 各stepの入力・費用・最低出力を別行表示 |
| MATH-REV-003 | 小数丸め方向がplatformで異なる | 上限超過・最低額割れ | Decimalと資産別丸め規則のgolden vector |
| VOICE-REV-001 | 正規化後の文だけ残し原文を消す | 誤認を追跡不能 | 原文と理解を同時表示・hash保存 |
| VOICE-REV-002 | 「生産価格」を無確認で清算価格に確定 | 意図違い | 候補表示し明示確認までhard block |
| FEE-REV-001 | 代理支払いproviderの法人名・連絡先・規約がない | 偽提供者・救済不能 | provider identity/terms hashをSchema必須化 |
| FEE-REV-002 | quoteが操作・nonce・精算先へ未結合 | quote差替え・二重請求 | operation digestとmaterial fieldsを署名対象化 |
| FEE-REV-003 | 失敗時請求を表示しない | 失敗だけで資産減少 | expected/cap/failed chargeを同時表示 |
| FEE-REV-004 | zero-gas能力の証拠期限を見ない | 失効経路で開始 | capability evidence、quote expiry、revocationをfail closed |
| FEE-REV-005 | 手動補充量を固定値で案内 | 混雑・最低出金額に不適合 | live operation-bound estimateの推奨量・上限だけ使用 |
| FEE-REV-006 | 手動見積もりが対象操作と未結合 | 別操作の量を流用 | estimate ID、operation digest、生成/期限を必須化 |
| PROMPT-REV-001 | Codex promptを3か所へ複製 | 古い安全条件で実装 | `codex/`正本1件、rootは短いpointerのみ |
| DOC-REV-001 | 検証PASSをproduction-readyと表現 | 過信・Mainnet誤開放 | assurance caseとcanonical GO/NO-GOをvalidatorで要求 |
| REL-REV-001 | ZIPの時刻・順序が毎回変わる | 再現性とhash比較低下 | fixed timestamp・sorted memberのdeterministic builder |
| TEST-REV-009 | `getBoundingClientRect()`だけで操作部品の可視性を判定 | scroll領域で完全に切り取られた部品を「composerに隠れた」と誤判定、または実遮蔽を誤って除外 | overflow祖先で切り取った実描画領域を算出し、その中心の`elementFromPoint`が自身または子要素でなければ失敗 |
| TEST-REV-010 | `START_HERE.html`をprototype iframeだけで代替検査 | 入口ページの狭幅崩れ・暗色・リンク遮蔽を見逃す | 320/390/1440幅×明暗の独立6条件、外部通信0、中心点、table containmentを検査 |
| UI-REV-011 | 画面例の承認期間・上限・アドレス・指紋が既定値または本番値に見える | 意図しない権限設定・誤コピー | 各任意値へ「画面例・初期値ではない」、addressへ「ダミー」、fingerprintへ「画面例」を文言で表示 |
| TEST-REV-011 | sticky要約の直下で証拠画像が内容block途中から始まる | レビュー資料が欠落・誤解を誘発 | 画像生成時にblock境界を整列し、上端の部分表示を自動失敗。focus ringも除去して安定化 |
| REL-REV-002 | build metadataとmanifestのpackage名・version・timestampが別々にhard-codeされる | 異なる製品名で検証済みと誤認、root名・checksum drift | `config/build-metadata.json`を唯一の正本にし、manifest、ZIP root、証跡、報告を厳密一致検査 |
| TEST-REV-012 | Schemaは収録されているが対応exampleがvalidator対象外 | 壊れたSchema／fixtureを未検査で配布 | 全Schemaのmeta-schema検査、`$id`一意性、local `$ref`解決、1件以上のmapped exampleを必須化 |
| TEST-REV-013 | YAML duplicate key／aliasを`safe_load`が受理 | gate・source・policy値の上書き、alias膨張 | strict loaderでduplicate mapping keyとaliasを拒否し、negative self-test化 |
| REL-REV-003 | `--skip-full-validation`等で古い証跡のZIPを作る | 検査迂回・古いscreenshot／manifest | release orchestratorからbypassを除去し、毎回full validation、前後tree digest一致を要求 |
| API-REV-001 | authorize／execute／resume／emergencyがbearer tokenだけに依存 | replay、別capsule・別deviceへの流用 | DPoP等のsender constraint、idempotency、capsule／receipt／device challenge／evidence hashを操作別必須化 |
| GPT-REV-002 | ChatGPT境界が文章だけで、machine-readable contractがない | 後続実装でwrite toolが混入 | 固定operation allowlistと`.read` scopeだけの独立OpenAPI、`executable=false`、execution schema参照禁止 |
| ZIP-REV-001 | ZIP member順序・mode・flag・extra field・ADS・bidiを検査しない | OS別展開差、hidden stream、表示名偽装、再現性破壊 | sorted member、exact mode/flag/timestamp/compression、extraなし、portable path policy、clean extract immutability |
| DOC-REV-002 | source pin JSON/YAMLがdriftし、`contentHash:null`を固定済みと誤認 | 外部仕様変更を検知できず本番GO | JSON/YAML semantic equality、MONITOR状態、production evidenceとしての使用禁止をvalidatorとCodex gateへ追加 |
| TEST-REV-014 | strict JSONが`-0`や2^53超の整数を受理 | 言語間hash／金額解釈drift | negative zeroとsafe integer範囲外をparse時に拒否しnegative self-test化 |
| REL-REV-004 | `run_full_validation.py --skip-visual`でもFULL VALIDATIONと表示 | visual欠陥を未検査で成功扱い | canonical full validationから全skip optionを削除しrelease外でも全visual test必須 |
| ZIP-REV-002 | host継承のdirectory setgidをpackage危険bitと誤認 | 環境依存false failure | archiveへ入るregular fileのsetuid/setgidを拒否し、directory metadataはbuilderで正規化 |
| TEST-REV-015 | Markdown link checkerのregexがcompileせず、generated report前にだけ実行 | broken／unsafe linkを未検査で配布 | checker起動self-check、report生成後のmarkup/link検査、失敗時release停止 |
| GPT-REV-003 | OAuth `authorizationUrl`をwallet `/authorize`と文字列誤検知 | false failureと本物のpath drift見逃し | ChatGPT contractをexact path/method/operation/schema/scope allowlistで構造検査 |
| TEST-REV-016 | YAML暗黙timestamp／NaNをruntime固有型で受理 | parser間semantic drift | implicit timestampとnon-finite floatを拒否し、日時はquoted stringへ限定 |
| ZIP-REV-003 | Unicode lookalike filenameを許可 | review／filesystem名の混同 | package path componentをportable ASCIIへ限定しNFC／casefold／reserved名も検査 |
| REL-REV-005 | ZIP非表現timestampをmetadataで許可 | 2秒丸め・年範囲差による非再現 | UTC、秒精度、1980..2107、偶数秒をmetadata load時に必須化 |
| ZIP-REV-004 | ASCII filenameへUTF-8 flag `0x800`を強制できると仮定 | builderはflagを0へ正規化しverifierが全member拒否 | pathをASCIIへ限定し、builder／verifierが共有するexact flag値0を正本化 |

## 2026-07-29.1 運用化の敵対的再監査で追加

| OPR-001 | 検証器が証拠・報告・hashを検証中に書き換える | 古い証拠を自己更新してPASSにできる | 生成はprepare工程だけ、full validationは前後tree hash完全一致のread-only検証 |
| OPR-002 | repository内のtrust policyを攻撃者が証拠と同時に差し替える | 偽鍵・偽承認者を正規として受理 | trust policy hashをpackage外の保護設定へ固定し、実行時にexact一致を要求 |
| OPR-003 | readiness checker自体を弱めてから全証拠を通す | 検査を通ったように見える | checker hashをout-of-band anchorへ固定し、変更時は独立再承認 |
| OPR-004 | 証拠が別release binaryや別設定を対象としている | 未検証buildを本番投入 | 全証拠・承認をrelease subjectのbinary/config/schema/source digestへ厳密結合 |
| OPR-005 | 時刻を端末時計だけで判定する | 期限切れ証拠・失効鍵を有効化 | 署名済みtrusted-time attestationとローカルclock差上限を要求 |
| OPR-006 | 署名済みだがissuerとreviewerが同一人物・同一鍵 | 自己承認でgate突破 | role分離、鍵分離、threshold、revocation、組織境界をpolicyで強制 |
| OPR-007 | 一部claimが欠落・重複・未知でも総合GO | 未検査領域を黙認 | required claim集合とevidence indexをexact set equalityで照合 |
| OPR-008 | 設計packageのPASSをproduction GOへ昇格 | 未実装の実資金機能を公開 | 現在状態をBLOCKED_NOT_OPERATIONALへ固定し、production subject以外GO不可 |
| OPR-009 | 署名済み証拠artifactが後から差し替わる | 監査結果を別内容へ置換 | statement内のartifact digest・media type・sizeを照合しimmutable保管 |
| OPR-010 | 未知・不一致・解析不能を警告だけで継続 | fail-openで資金移動 | unknown/conflict/parse errorは全write gateを閉じる |
| RUN-001 | release GOだけで常時取引を許可 | 障害・攻撃中にも送信 | release readinessとruntime activationを分離し、fresh stateと短期限leaseを要求 |
| RUN-002 | runtime leaseを取引承認として流用 | 利用者確認なしの実行 | leaseはサービス稼働許可だけとし、操作別本人承認を別署名で要求 |
| RUN-003 | kill switch反映前にqueue済み操作を送信 | 停止後も資金移動 | signer直前で最新sequence付き停止状態を再確認し、古いleaseを拒否 |
| RUN-004 | 状態bundleが古い・部分的・相互矛盾 | 誤残高・誤nonce・誤価格で実行 | 複数sourceのfreshness・sequence・quorum・整合性をpolicy化 |
| RUN-005 | 承認後にquote・fee・recipient・calldataが変化 | 別内容へ署名 | per-operation authorizationを最終capsule hash、quote、chain、nonceへ結合 |
| RUN-006 | 承認tokenの再利用・別端末転用 | replay・権限横取り | single-use nonce、device-bound proof、短期限、server-side consumed state |
| RUN-007 | deploy途中の旧新version混在 | 異なるcanonicalizationで署名 | client/backend/signer/policy/schemaの互換集合とdeployment epochを固定 |
| RUN-008 | 障害復旧後に未確定operationをblind retry | 二重送金・二重注文 | chain/exchange照合、idempotency、manual resolutionまで再送禁止 |
| MOB-OPR-001 | Android overlay・tapjackingで承認内容を隠す | 利用者が別内容を承認 | FLAG_SECURE、overlay検知、trusted confirmation可能時利用、遮蔽時停止 |
| MOB-OPR-002 | root化・debugger・hook環境を正常端末として扱う | 鍵・承認情報の窃取 | 端末完全性信号をrisk inputにし、高リスクwriteを停止、単独信頼はしない |
| MOB-OPR-003 | iOS jailbreak・dynamic instrumentationを未検出 | Keychain外への漏えい・画面改ざん | App Attest、debug/hook検知、Secure Enclave、異常時fail closed |
| MOB-OPR-004 | deep link・universal linkを外部入力のまま実行 | recipientや金額注入 | linkは非実行draftのみ、厳格allowlist、表示・再確認、署名済みlinkでも直接送信禁止 |
| MOB-OPR-005 | clipboard address差し替え | 攻撃者宛送金 | clipboardを信頼せず、address book・checksum・先頭末尾だけでなく全文確認手段 |
| MOB-OPR-006 | IME・音声・アクセシビリティserviceが機密や金額を改変 | 誤入力・漏えい | sensitive field制御、原文併記、決定項目の明示確認、accessibility実機試験 |
| MOB-OPR-007 | backup・端末移行で権限tokenや秘密情報まで復元 | 別端末で権限継続 | device-bound secretをbackup除外し、移行時に権限再発行・旧端末失効 |
| MOB-OPR-008 | 通知内容やapp switcher snapshotに残高・宛先を表示 | 肩越し・端末共有で漏えい | privacy screen、通知redaction、background snapshot遮蔽、設定と試験 |
| SUP-001 | CI dependencyやGitHub Actionがfloating tag | 供給網乗っ取り | commit/digest pin、SBOM、provenance、署名検証、定期更新レビュー |
| SUP-002 | release signing keyへ単独管理者がアクセス | 不正binary配布 | HSM/managed signing、二人承認、role分離、緊急失効・rotation drill |
| SUP-003 | build hostが汚染されても同じartifactと誤認 | backdoor混入 | hermetic build、独立builder比較、SLSA provenance、binary transparency |
| SUP-004 | Store掲載情報・support URL・privacy labelがbinaryとdrift | 誤説明・審査違反 | 提出bundleをrelease subjectへ結合し、Store差分もgate証拠化 |
| DB-001 | schema migration途中に旧serverがwrite | ledger不整合・資金二重処理 | expand-contract migration、互換epoch、write fencing、rollback rehearsal |
| DB-002 | transactional outboxなしでDBとbroadcastが分離 | 送ったのに未記録または逆 | outbox/inbox、exactly-once効果のidempotency、reconciliation |
| DB-003 | 監査logを管理者が編集・削除 | 事故追跡不能 | append-only hash chain、外部WORM、時刻証明、access audit |
| DB-004 | backupはあるがrestore試験なし | 災害時に復旧不能 | 暗号化backup、定期restore drill、RPO/RTO証拠、鍵復旧分離 |
| TOK-001 | token proxy upgrade・decimals・fee-on-transfer変更を無視 | 受取額・承認対象を誤る | chainId/address/code hash/proxy implementation/decimalsをreleaseとruntimeで照合 |
| TOK-002 | 無制限allowance・Permit署名を便利機能として残す | spender侵害で全額流出 | exact amount・短期限・spender allowlist・revoke flow、typed-data全文表示 |
| TOK-003 | 同名偽token・偽networkをUIで区別できない | 偽資産へ交換・送金 | verified registry、chain-native identifier、contract表示、未登録資産はwrite禁止 |
| TOK-004 | rebase・blacklist・pause等のtoken特性を無視 | 残高や送金成否の誤認 | asset capability registryとlive contract stateを確認し、未知特性は停止 |
| BRG-001 | source tx成功だけでbridge完了扱い | destination未着を成功表示 | source finality、message relay、destination receipt、必要時challenge periodまで追跡 |
| BRG-002 | bridge route contract・guardian・upgrade変更を未監視 | 侵害routeで資金損失 | allowlist、code/config hash、TVL/incident monitor、上限、kill switch |
| BRG-003 | destination gas不足で受取後操作不能 | 資金が実質凍結 | destination fee readinessを事前検査し、不足時の安全な補充手順 |
| BRG-004 | reorg・message replay・partial bridgeをblind retry | 二重mint・二重送信 | message IDで冪等化、finality threshold、provider照合、manual recovery |
| HL-OPR-001 | Hyperliquid API wallet nonce管理を複数processで競合 | 注文拒否・replay・意図しない順序 | 単一atomic nonce authority、agent別partition、公式仕様version pin |
| HL-OPR-002 | WebSocket欠落・順序逆転・再接続gapを最新状態と誤認 | position・fill・清算価格を誤表示 | sequence/gap検知、REST snapshot再同期、同期完了までwrite停止 |
| HL-OPR-003 | asset indexやspot/perp識別をsymbol文字列だけで決定 | 別市場へ注文 | 公式metadata snapshotとasset IDをbindし、変更時再確認 |
| HL-OPR-004 | partial fill・cancel race・reduce-only拒否を成功扱い | 残存position・過剰exposure | order/fill/positionを照合し、部分結果を明示、残りを自動再注文しない |
| HL-OPR-005 | cross/isolated margin・funding・fees・liquidation model drift | 清算距離と損失を誤説明 | live account modeと公式fieldを取得し、preview/after-fillを分離、古ければ停止 |
| HL-OPR-006 | API仕様・署名domain・rate limit変更を静かにfallback | 誤署名・意図しない再試行 | version pin、contract tests、公式変更監視、未知responseでfail closed |
| AI-OPR-001 | LLM出力を直接policy入力・address入力に使う | prompt injectionで取引改変 | LLMは非権限draftのみ、strict compilerとallowlist、raw address決定禁止 |
| AI-OPR-002 | 会話履歴やtool結果へ秘密・個人情報を過剰送信 | privacy breach | 最小化・redaction・retention制御・model provider契約・監査 |
| AI-OPR-003 | model更新でintent分類が変化 | 以前安全だった発話が実行扱い | model/version pin、golden corpus、shadow test、再承認なしの自動昇格禁止 |
| AI-OPR-004 | 悪性Web・QR・support文面の指示を権限ある命令として採用 | 間接prompt injection | 外部contentをuntrusted dataとして隔離し、利用者の明示命令と分離 |
| LEG-001 | 法務意見が別機能・別地域・期限切れ | 無資格提供・規約違反 | release subject、対象地域、主体、機能、日付へ結合した署名済み意見を要求 |
| LEG-002 | Apple/Googleの申告・審査状態を口頭確認だけでGO | 公開停止・アカウント制裁 | portal export、submission ID、承認画面、binary versionを証拠化 |
| LEG-003 | 制裁・AML・消費者保護・税務要件変更を未監視 | 継続運用が不適法 | 法務owner、source monitor、期限、緊急地域停止、再審査gate |
| SRE-001 | 監視dashboardが緑でも実際の送金経路が壊れている | 障害を見逃す | synthetic read/canary、reconciliation、provider別SLO、stale telemetry検知 |
| SRE-002 | 障害時に管理者が直接DBやsignerを操作 | 監査不能・誤送信 | break-glass二人承認、期限付き権限、command allowlist、完全audit |
| SRE-003 | 資金上限・rate limit・provider残高の枯渇を未検知 | 高損失または停止 | exposure limits、reserve monitor、automatic pause、capacity drill |
| UX-OPR-001 | 確認画面で最悪時受取・総費用・取消不能点がfold下に隠れる | 理解せず承認 | 重要項目を操作直前に要約し、到達・読み上げ・重なりを実機検証 |
| UX-OPR-002 | エラー時に「もう一度」だけ表示 | 二重実行・利用者迷子 | 実状態照合後の安全な次手、押す場所、禁止事項、support用trace IDを提示 |

| OPR-011 | checkerのPython本体だけhash固定し、gate設定・Schema・canonicalizerを固定しない | 攻撃者が必須claimや検証規則を弱めてもchecker hashが一致 | evaluator、CLI、gate profile、全operational Schema、canonicalizer、lockfileをdeterministic verifier bundleとして一括anchor |
| OPR-012 | reviewer approvalがstatementIdだけへ結合 | 同じIDの別statementへ承認を流用 | approvalへexact statementSha256を含め、index記録・実ファイルdigestと三者一致 |
| OPR-013 | 同じ公開鍵を複数keyIdで登録 | distinct-key thresholdを見かけ上満たす | canonical Ed25519 public key fingerprintの重複を拒否 |
| OPR-014 | 同一人物が複数鍵を使い複数approval slotを埋める | key分離だけで自己承認 | trust policyのprincipalId・organizationを署名文書へ結合しprincipal単位で重複拒否 |
| OPR-015 | 鍵の有効性を評価時だけ確認 | 有効開始前・失効後の時刻へbackdateした署名を受理 | document signing timeとevaluation timeの両方でkey validityを検証 |
| OPR-016 | evidenceの実size・採取時刻・statement発行順を検証しない | 別内容、未来証拠、古すぎる証拠を受理 | digest、sizeBytes、MIME、max age、collectedAt <= issuedAtをexact検証 |
| OPR-017 | evidence indexにsequence・発行・失効時刻がない | 古いindexのreplayや長期固定 | signed positive sequence、短期限issuedAt/expiresAt、trusted evaluation timeとの順序を必須化 |
| OPR-018 | PASS statementに未解決limitationsが残る | 除外条件付き結果を完全合格として集計 | production PASSはlimitations空のみ受理し、残余条件はclaimをBLOCK |
| OPR-019 | release readiness reportが直接write許可を返す | runtime異常・本人未承認でも送信根拠に流用 | reportは常にproductionWritePermitted=false、GO時もruntime activation eligibilityだけを返す |
| OPR-020 | verifier runtime・OS・Python依存を信頼済みと暗黙仮定 | interpreter/library/root侵害で検査結果を偽装 | hermetic signed verifier image、attestation、protected runner、外部anchorをCodexのrelease gateへ要求 |
| TEST-REV-017 | negative testだけでGO経路を一度も通さない | 相互矛盾で永遠にGO不能、または未検査分岐が残る | throw-away鍵と93 claimのephemeral synthetic evidenceでGO到達とdirect-write=falseを毎回検証 |
| OPR-021 | trusted inputをhash後に再openし、symlink/hardlink/同時差替えを許す | 検査対象と使用対象が異なるTOCTOU | no-follow descriptor、regular/single-link/permission/size確認、read前後inode・mtime・size一致でsecure snapshot |
| OPR-022 | 異なる署名文書で同じcanonical JSON署名を再利用 | 別種の承認へ署名を横流し | 文書種別ごとのdomain-separated payloadとV2署名profileを必須化 |
| OPR-023 | lone Unicode surrogateをcanonicalizerが受理 | 言語間でhash・署名対象が不一致 | Unicode scalar value以外を拒否するnegative vectorを固定 |
| OPR-024 | evidence indexのhashをreport記載だけで信頼 | 別index・古いindexへ差替え | exact evidence-index SHA-256をpackage外anchorへ固定 |
| OPR-025 | GO reportに期限・入力hashがない | 別release・別checker・古いGOを再利用 | validUntilとtrust/checker/subject/index/timeのdigestをreportへ結合 |
| RT-AUTH-001 | 37/93 summaryだけPASSにして個別gate rowをBLOCKのまま残す | 未合格gateを隠してruntime起動 | 正本gate inventoryと全行ID・件数・PASS・blocking空をexact照合 |
| RT-AUTH-002 | release GOをそのままtransaction許可として扱う | 障害中・本人未承認でも署名 | runtime evaluatorはatomic signer finalization候補だけを返し直接許可は常にfalse |
| RT-AUTH-003 | wallet accountとuser/device public keyの結合がない | 別利用者・別端末の署名を流用 | release/deployment/account/key/device attestationへ署名済みbindingを要求 |
| RT-AUTH-004 | runtime state・lease・binding sequenceをrollback | 失効前の健康状態や権限を再利用 | signer保護領域のhigh-water markより大きいsequenceだけを受理 |
| RT-AUTH-005 | quote hashだけあり有効期限を検証しない | 古い価格・feeで署名 | non-zero quote hashとquoteValidUntilを操作署名へ結合し最短期限に採用 |
| RT-AUTH-006 | chain/network identityをExecution Capsuleへ含めない | 同一address・asset表記を別networkで実行 | source/destination network、chain ID、network registry digestをsemantic hashへ結合 |
| RT-AUTH-007 | aggregate observedAtだけ新しく個別sourceは古い | stale stateで取引 | 全source timestamp・digest・IDを個別検証しaggregate chronologyと一致させる |
| RT-AUTH-008 | user/device/policy engineが同一鍵・同一principal | 三者承認を一者で偽装 | distinct key fingerprint・keyId・principalとactive bindingを検証 |
| RT-AUTH-009 | runtime判定後にsignerが別transaction bytesを署名 | TOCTOUで宛先・金額・chain差替え | signer内でimmutable inputsを再読込し最終transactionを再構築・再hash |
| RT-AUTH-010 | authorization IDとnonce消費が署名と非atomic | crash・並行処理で二重署名 | 保護された一意制約とtransactionでreserve/consume/signを原子的に実行 |
| RT-AUTH-011 | runtime evaluator本体だけを信頼し依存Schema・policyを固定しない | 検査規則を弱めて同じchecker名を使用 | authorizer・CLI・tests・schemas・policy・canonicalizerのbundle hashを外部anchor |
| RT-AUTH-012 | step typeからcapabilityへのmapがallowlist外を返す | leaseにない権限を暗黙生成 | map値をlease/operation両allowlistへ包含検証し未知stepを停止 |

| TEST-REV-018 | `--check`検証が証拠画像や生成物を先に削除する | 検証だけのつもりで正本を破壊し、後続生成で欠落を隠す | check modeは一時領域だけへ出力し、各validator前後のtree snapshotで1 byteでも変化すれば失敗 |
| TEST-REV-019 | validatorのimport error・起動失敗をrunnerがskipまたは警告扱い | 最重要検査が一度も走らず全体PASS | validator allowlistをexact固定し、重複・欠落・非zero終了・signal・timeoutを全てrelease failureにする |
| OPR-026 | signed trusted timeまたはevidence indexの古いsequenceを再提示 | 失効・撤回前のGO証拠をrollback再利用 | package外のrollback-resistant high-water markを保持し、候補sequenceが厳密に大きい場合だけ受理 |
| RT-AUTH-013 | runtimeがreadiness report内のtime/index sequenceと現在入力のsequenceを照合しない | 別時点のGO reportとruntime状態を組み合わせる | readinessのtrustedTimeSequence/evidenceIndexSequenceを現在入力とexact一致させ、両方を保護high-waterより上に要求 |
| RT-AUTH-014 | 非zero `quoteHash`だけを確認し、見積もり本文と最終order/transactionを照合しない | 宛先・route・入力額・最低受取・fee・price条件の差替え | domain-separated canonical quote documentを必須化し、signerが本文digestと最終payload commitmentを再計算 |
| RT-AUTH-015 | network registry digestを文字列比較するだけで、実registryのCAIP-2とchainIdを解決しない | 正しいhash欄を持つ別chain payloadへ署名 | exact signed registryをsigner内でloadし、networkId、chainId、RPC chain ID、asset/contract/code hashを相互照合 |
| RT-AUTH-016 | 署名後にbroadcast応答が不明な操作を新しいnonceで再署名・再送 | 二重送金・二重注文 | `SIGNED_BROADCAST_UNKNOWN`を終端待機状態にし、chain/exchange照合と一意operation IDで既存結果を確定するまで再署名禁止 |
