# Security Invariants

以下は実装・運用の全期間で常に真でなければならない。

1. LLMは署名・broadcast capabilityを持たない。
2. LLMはraw address／contractを決定しない。
3. 実行は有効なExecution Capsuleなしに開始しない。
4. CapsuleのsemanticHashは承認後に変化しない。
5. SignerはCapsuleを独立再検証する。
6. generic signing endpointは存在しない。
7. root actionとtrade actionのsigner roleは分離する。
8. mainnet writeはfeature gate default OFF。
9. feature gateの変更はtwo-person approval。
10. 金額はDecimal／integerで扱う。
11. timeoutは成功／失敗の証拠ではない。
12. unknown stateでblind retryしない。
13. Orderはcloidで冪等化する。
14. signer nonceはatomicかつ一意。
15. deregistered agent addressを再利用しない。
16. Address Book変更は未実行Capsuleを無効化する。
17. contract registry変更は未実行Capsuleを無効化する。
18. chain ID／environment mismatchはfail closed。
19. 新規宛先は高リスク認証を要求する。
20. root key materialはOpenAIへ送らない。
21. secretsはlogへ出ない。
22. backupはkey materialを含まない。
23. 複合操作は原子的と表示しない。
24. PARTIALはCOMPLETEと表示しない。
25. AI停止時も緊急操作が可能。
26. Bridge完了はdestination creditまで確認する。
27. Vaultはallowlistとruntime codeを検証する。
28. Legal gate未完でpublic Mainnetを許可しない。
29. Critical／High security finding未解決でMainnetを許可しない。
30. Hyperliquid公式アプリを名乗らない。
31. product policyをAPI Walletのprotocol scopeと表示しない。
32. agent key漏えい時にproduct signer外でpolicyを迂回できる前提で設計する。
33. agentが署名可能な全L1 actionのcharacterization未完でMainnetを許可しない。
34. BiometricPromptだけをtransaction semanticsのTrusted Displayと扱わない。
35. R4は承認済みprotected／external／hardware display経路がなければfail closed。R3のapp内例外は事前R4 ceremony、cooling、hard cap、standing authorization、auth-per-use、device／app evidenceが全て有効な場合だけ許可する。
36. Protected ConfirmationではpromptTextのcritical fieldとchallengeをRelying Partyが検証する。
37. Protected Confirmation非対応時にsilent downgradeしない。
38. R2以上のcritical stateは独立sourceで照合する。
39. 同じprovider／cacheを独立quorumと数えない。
40. state divergence時はwriteを停止する。
41. SignerはCompilerと独立してcritical stateを再検証する。
42. HyperCore Testnet成功をBridge／HyperEVM／Mainnetの同等性証明としない。
43. 長時間Sagaは各step前にpolicy／state／contractを再検証する。
44. dynamic remainderはchain-confirmed actual outputとhard boundから計算する。
45. Google Play／region／legal gateは互いの代替ではない。
46. public配布は正確なFinancial features declarationとstore evidenceを要求する。
47. emergency RTOはchain上の約定・着金時間を保証しない。
48. source pin／release evidenceが期限切れならMainnet writeを許可しない。
49. ChatGPT側から取引payloadを含むdeep link／QRを発行しない。
50. Existing Wallet Modeのroot action署名回数を隠さない。
51. Authorization Envelopeはsemantic、render、state、prompt、challengeを同時に束縛する。
52. Execution Capsule exampleの派生hashはCIで再計算し、一致しなければ失敗する。
53. 新規宛先のTrusted Displayはfull addressまたは事前登録alias＋検証済みfingerprintを表示する。
54. iOSのSecure Enclave P-256をHyperliquid root secp256k1 signerとして扱わない。
55. App Attestはapp instanceのrisk evidenceであり、取引内容のTrusted Displayではない。
56. iOS App Attest modeはtrustedDisplayClaim=falseを維持する。
57. App Attest unsupported時にR3/R4へsilent downgradeしない。
58. iOS再install／migration／restore後はdevice enrollmentをやり直す。
59. Keychainのroot-related materialはThisDeviceOnlyかつnon-synchronizableとする。
60. biometric enrollment変更で高リスクauthorization keyを無効化または再登録する。
61. 新規宛先、高額／全額出金、recoveryはiOS app UI認証だけで許可しない。
62. saved destinationの短縮UXはstanding authorization、hard cap、cooling evidenceを要求する。
63. AndroidとiOSのauthorization assurance差をUIとdomain modelで隠さない。
64. cross-platform canonical bytesはgolden vectorで一致しなければreleaseしない。
65. community Hyperliquid SDKを唯一の署名oracleとしない。
66. platform別実機evidenceなしに他platformのPASSを流用しない。
67. iOS public App Store gateはorganization／license／legal evidenceなしに有効化しない。
68. Store審査通過を法的適法性の証拠としない。
69. TestFlight／Ad Hoc配布をpublic Mainnet許可の代替としない。
70. UIのcritical fieldはDynamic Type／font scale 200%でもclipしない。
71. iOS tap targetは44pt以上、Androidは48dp以上を守る。
72. critical meaningを色だけで伝えない。
73. PARTIAL／UNKNOWNで成功表示を出さない。
74. visual regressionでcritical regionの意図しない差分を許可しない。
75. background snapshot、notification、crash reportにsecretを含めない。
76. clipboardへseed、private key、MPC shareを置かない。
77. write-capable Siri／Shortcuts／notification actionをMVPで提供しない。
78. deep linkは実行payloadを直接発火させない。
79. 管理consoleはuser appと別auth／別domainにする。
80. Mainnet enableはtwo-person approvalとexpiryを要求する。
81. kill switchはAIと主要control APIの障害から独立して利用可能にする。
82. release evidenceはplatform、device、OS、build hashを含む。
83. unsupported capability、unknown integrity、state divergenceはfail closedとする。
84. Managed Self-Custodyは外部暗号監査とrecovery drill完了までOFFとする。
85. full root private keyを通常運用中に一か所へ復元しない。
86. recovery後はold device shareとstanding authorizationを失効させる。
87. offline prototypeはsimulation watermarkを削除せず、network／wallet callを持たない。
88. package validation PASSをproduction safety PASSと表示しない。
89. ユーザー入力の各actionable clauseはoperation、missing field、warning、またはunsupported reasonへ対応し、silent omissionしない。
90. entry-fill連動protective orderはactual weighted fillと許可済みformulaだけから導出する。
91. protective orderがdeadline内に配置できない場合、事前開示・許可されたreduce-only closeを実行するか、明示的RECOVERY_REQUIREDへ移行し、裸のポジションを成功扱いしない。
92. OpenAI／AI provider credentialはserver-side secret managerだけに置き、mobile binary、remote config、client logへ含めない。
93. 取引Intent ParserはOpenAI providerへ接続しない。任意の非取引Supportだけが、認証・replay防止・固定schema・rate／budget limitを備えたfirst-party Support Gatewayを使用する。
94. 非取引Support Gatewayのnetwork identityはTransaction Intent、Address Book、quote、Compiler／Policy write、Signer、broadcast、wallet root action endpointへ到達できない。
95. AI request／response／error telemetryはallowlist型redactionを通し、address、残高、auth header、provider credential、signature materialを保持しない。
96. visual／geometry evidenceはprototype source hash、test script hash、Playwright／browser version、viewportを含み、toolchain driftを黙って同一PASSとして扱わない。
97. derived example／visual evidenceを更新した後にmanifestとchecksumsを最後に再生成し、clean extractで一致するまで配布しない。
98. R0–R5の意味は一つのcanonical decision tableから生成し、Android、iOS、backend、文書、UI badgeで独自再定義しない。
99. R3 standing-authorization例外をruntime fallback／silent downgradeとして発行せず、宛先・chain・cap・policy・deviceの変更時に即失効させる。
100. 利用者が最初に見る主要ラベルでは、`Perp`、`Spot`、`Bridge`、`Vault`、`Slippage`、`Gas`を説明なしの単独表示にせず、`config/user-facing-terms.ja.json`の日本語を使う。
101. 先物取引では、清算価格または取得不能であることを実行前に表示し、古い／欠損した値を0や安全値として補完しない。
102. 約定後の清算価格は、対象positionの最新`liquidationPx`と取得時刻から表示し、AI生成値を使わない。
103. ネットワーク手数料用資産が0の場合、通常のオンチェーン交換を手数料なしで開始できると仮定しない。
104. JPYCからの手数料準備は、正式コントラクト、ネットワーク、経路、価格、有効期限、1回／月間上限を検証できる場合だけ行う。
105. 代理支払い／立替は許可一覧、監査済みprovider、費用上限、operation hash、idempotency、悪用上限へ束縛し、失敗時に二重回収しない。
106. 手数料の定期補充量と実行可否は決定論ポリシーで判断し、LLMへ裁量決定させない。
107. ChatGPT App、Apps SDK、MCP、Action、GPT toolへ注文・送金・交換・出金・暗号資産移転のwrite capabilityを公開しない。
108. JPYC EX連携は画面遷移、アドレス登録補助、状態連携までとし、本人確認、審査、最終申込み、発行／償還確定をウォレットやAIが代行しない。
109. 自動化不能時は、現在画面、正確なボタン名、期待結果、安全確認、再試行、support codeを表示し、曖昧な案内だけで終了しない。
110. 最初の一度だけの承認は、期限、資産、ネットワーク、金額、取引倍率、送金先、手数料上限へ限定し、新規送金先、高額／全額、鍵・権限変更へ流用しない。
111. 利用者が依頼していない損切り、利確、証拠金方式、経路、宛先、全額指定、手数料準備量を暗黙に追加しない。
112. 音声入力の原文と正規化後の理解を同時に保持し、material correctionの確認完了前は実行確認を有効化しない。
113. 画面見本とsimulation fixtureは常にexample-onlyであり、production evidenceへ型変換だけで昇格できない。
114. 主要actionはcritical review contentの最後に置き、固定領域で明細を隠さない。
115. flow、theme、text size、platform切替時はreview scroll stateを同期的に初期化する。
116. 長いreviewには上端・途中・末尾・全表示の状態を文言で示し、色だけに依存しない。
117. primary actionは最小端末・大きな文字・両themeで末尾まで到達可能かつ他要素に遮蔽されない。
118. visual testは`scrollIntoView()`等で初期欠陥を消してからPASSにしない。
119. visual evidenceは6 viewport、12 flow、2文字mode、2themeの全288条件を同じ検査集合で実行する。
120. visual evidenceは実行locale、browser、Playwright、prototype source、test harnessのhashを記録する。
121. browser logical-pixel検査をnative point/dp、safe area、IME、screen reader、物理mmの証明として扱わない。
122. 複合操作の最低値・最大値・費用差引前後を型で分離し、表示数値から算数を再計算する。
123. 代理支払いproviderは法人名、連絡先、規約version/hash、provider IDを利用者と監査証跡へ開示する。
124. 手数料quoteはaccount、network、asset、operation、amount、nonce、期限、費用上限、fee asset cost、精算先へ暗号学的に束縛する。
125. 手数料quoteは予想JPYC額、最大JPYC額、失敗時請求、精算先、期限を同じ確認面へ表示する。
126. quote provider IDとprovider registry identityが一致しない場合は実行しない。
127. zero-gas capability evidenceが未検証、期限切れ、失効、network不一致なら自動経路を使用しない。
128. 手動の手数料補充量は対象操作に結び付いたlive estimateだけから取得し、固定量を案内しない。
129. 手動見積もりはestimate ID、operation digest、推奨量、上限、生成時刻、有効期限を持ち、欠損時は送金を案内しない。
130. 手動補充後は元の操作をそのまま再送せず、最新残高と新しい見積もりから新しいexecution planを作る。
131. Codex実装指示は`codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md`だけを正本とし、rootファイルへ複製しない。
132. test、evidence、documentation、manifestの順序driftを防ぐため、派生物更新後にadversarial auditを実行し、manifestを最後に生成する。
133. 配布ZIPは単一root、sorted member、固定timestamp、重複名なし、symlinkなし、path traversalなしで生成する。
134. ZIPはCRC検査とclean extraction後の全ファイルSHA-256一致を確認する。
135. package内に`.env`、private key container、`__pycache__`、`.pyc`を含めない。
136. case-insensitive filesystemで衝突するファイル名を配布しない。
137. screenshot evidenceは要求された10画像の完全な集合とmanifest hashを持つ。
138. evidence source hashまたはtest harness hashが変われば以前のPASSを無効化する。
139. validation PASSは列挙した静的・browser検査のPASSだけを意味し、native build、Testnet、Mainnet、法務、StoreのGOへ自動伝播しない。
140. gate変更は成果物の存在ではなく、該当gate固有の証拠path、実行環境、担当者、期限を要求する。
141. 操作部品のhit検査は、scroll／overflow祖先で切り取られた後の実描画領域を正しく算出し、完全に非表示の子孫を誤検知せず、描画領域の中心が自身または子要素へhitしなければ失敗とする。
142. 配布入口の`START_HERE.html`はprototype本体と独立に、狭幅・標準幅・desktop、明暗、横はみ出し、focus、中心点、table containment、外部通信0を検査する。
143. 利用者が入力していない期間、上限、許容価格差、手数料上限、address、fingerprint等を画面見本へ置く場合、値の直近に「画面例」「初期値ではない」「ダミー」の適切な表示を付ける。
144. レビュー用screenshotはsticky領域の直下で内容blockを途中から切らず、上端・途中・末尾の状態が判別でき、focus状態など偶発的な描画差を除いた再現可能証拠とする。
145. package identity、version、deterministic timestamp、ZIP root、manifest headerは`config/build-metadata.json`の同一値から導出し、別々にhard-codeしない。
146. 収録する全JSON SchemaはDraft 2020-12としてmeta-schema検査し、`$id`は一意、全local `$ref`は解決可能、各Schemaにはvalidator対象のexampleを1件以上持たせる。
147. release dataのYAMLはduplicate keyとaliasを拒否し、validator自身が悪性fixtureを拒否できることをnegative self-testで証明する。
148. 配布buildにはfull validationを迂回するflagを設けず、検証後、2回のZIP生成、clean extraction検証の前後でsource tree digestを不変に保つ。
149. first-party write APIはshort-lived tokenだけで承認せず、sender-constrained proof、idempotency、operation固有のcapsule／receipt／device evidence bindingを検証する。
150. ChatGPT向けcontractは独立したmachine-readable allowlistとし、read-only scope以外、execution schema、transaction payload、signing challenge、write endpoint、実行deep linkを含めない。
151. 配布ZIPはmember順序、timestamp、compression、UTF-8 flag、Unix mode、extra/comment、root名までexact policyへ一致し、ADS・control/bidi文字・case/NFC衝突を拒否する。
152. source pinのJSON/YAMLは意味的に同一でなければならず、`contentHash`やcommit pinがない`MONITOR`情報はproduction release evidenceとして扱わない。
153. canonical release JSONはnegative zeroとIEEE-754相互運用safe integer範囲外をparse時に拒否し、言語間で値が変わる入力をhash対象にしない。
154. `run_full_validation.py`はvisualを含む工程をskipするoptionを持たず、FULL VALIDATIONという名称の実行は常に全工程を通す。
155. source filesystemの危険mode判定はarchiveへ入るregular fileへ適用し、host継承のdirectory setgidを権限付与と誤認せず、ZIP内modeは全fileを0644へ固定する。
156. generated reportを作成した後にplain-language、archive safety、security hygiene、local link／markup検査を実行し、生成物も同じrelease gateへ含める。
157. ChatGPT read-only OpenAPIは文字列検索だけに依存せず、path、HTTP method、operationId、request property、response const、OAuth scopeのexact allowlistで検査する。
158. release YAMLはduplicate key、alias、non-finite number、implicit timestampを拒否し、日時は明示的なquoted stringとして扱う。
159. 配布packageとZIPのpath componentはportable ASCII、NFC、case-insensitive collisionなし、control／bidi／ADS／Windows予約名なしでなければならない。
160. deterministic build timestampはUTC Z、秒精度、ZIPで表現可能な1980..2107年、偶数秒でなければrelease metadataとして受理しない。
161. 配布pathはportable ASCIIへ限定しているため、ZIP general-purpose filename flagsは0を正本とし、builderとverifierは同じ定数を使ってdriftしない。
162. full validationはpackage treeを1バイトも変更せず、実行前後のsecure snapshotとtree digestが一致しなければ失敗する。
163. 派生証拠、report、screenshot、example hash、manifest、checksumsの生成は明示的なprepare工程だけで行う。
164. prepare工程後の検証は常にcheck-only modeであり、期待値不足を自動補完しない。
165. operational trust policyはrelease package内の存在だけでは信頼せず、保護されたout-of-band hash anchorと一致しなければならない。
166. operational readiness checker自身のhashをout-of-band anchorへ固定し、checker変更は独立審査を要求する。
167. production release subjectのhashをout-of-band anchorへ固定し、別binary、別config、別schema、別sourceの証拠を流用しない。
168. trusted time attestationのhashをout-of-band anchorへ固定し、端末時計だけで証拠期限・鍵期限を判断しない。
169. 全readiness evidence statementは承認済み鍵でcanonical payloadへ署名し、artifact digest、size、media type、release subjectを含む。
170. 全review approvalは対象statement hashとrelease subjectを署名対象に含める。
171. issuer、reviewer、evidence-index signerはpolicyのrole separationとdistinct-key条件を満たす。
172. revoked、expired、not-yet-valid、unknown role、未登録鍵の署名は常に拒否する。
173. required claim集合とevidence indexのclaim集合は欠落、重複、未知項目なしの完全一致でなければならない。
174. claim固有のmax ageを超えた証拠または承認は、署名が正しくても無効とする。
175. 現在の設計packageは常にBLOCKED_NOT_OPERATIONALであり、production binaryを含まない状態からPRODUCTION_OPERATIONAL_GOを生成しない。
176. PRODUCTION_OPERATIONAL_GOは未知の安全性保証ではなく、明示した37 gateと93 claimの証拠が全て有効であることだけを意味する。
177. release readiness GOだけではwriteを許可せず、runtime state bundle、短期限control-plane lease、操作別本人承認を別々に要求する。
178. runtime control-plane leaseは取引承認ではなく、単独でsignまたはbroadcast capabilityを与えない。
179. per-operation authorizationは最終Execution Capsule hash、chain、asset、recipient、amount、fee、quote、nonce、expiry、deviceへ結合する。
180. per-operation authorizationはsingle-useであり、消費済みnonceまたは別deviceからの再利用を拒否する。
181. runtime state bundleはsequence、freshness、source、kill-switch、provider health、policy version、deployment epochを署名対象に含む。
182. kill switchまたはemergency stopが有効なら、queue済みを含む全新規sign/broadcastをsigner直前で拒否する。
183. 古いruntime lease、古いstate sequence、deployment epoch不一致ではwriteを拒否する。
184. client、backend、signer、policy、schema、canonicalizerのversion互換集合をrelease単位で固定する。
185. unknown、conflict、parse error、missing evidence、ambiguous stateは警告継続せずwrite gateを閉じる。
186. Androidはoverlay、tapjacking、screen capture、root、debug、hook、accessibility abuseを脅威として実機negative testする。
187. iOSはjailbreak、debug、dynamic instrumentation、screen capture、App Attest failureを脅威として実機negative testする。
188. deep link、universal link、QR、clipboardは非信頼入力であり、直接Execution Capsuleまたは署名要求を作らない。
189. clipboard由来addressはverified address bookまたは全文確認なしに送信先へ確定しない。
190. device-bound secret、standing authorization、session tokenはOS backupへ含めず、端末移行時に再発行する。
191. 通知、app switcher、crash report、analytics、AI promptへ秘密鍵、seed、完全address、取引機密を不用意に記録しない。
192. CI action、compiler、SDK、dependency、container imageはcommitまたはdigestでpinし、SBOMとprovenanceを生成する。
193. release signing keyはHSMまたは同等の保護と二人承認を用い、単独管理者が任意binaryへ署名できない。
194. 同一immutable sourceから独立builderを用いたartifact比較とclean extraction検証をrelease gateに含める。
195. Store metadata、privacy label、entitlement、permission、support URLをbinary release subjectへ結合して審査する。
196. DB migrationはexpand-contract、互換epoch、write fencing、rollback rehearsalを満たすまでproduction writeを開始しない。
197. DB stateと外部broadcastの境界はtransactional outbox/inboxとidempotent reconciliationで保護する。
198. 監査logはappend-only hash chainと外部immutable storageへ保管し、管理者による無痕跡変更を許さない。
199. backupは暗号化だけでなく定期restore drill、RPO/RTO、鍵復旧分離の証拠を持つ。
200. token identityはchainId、contract、code hash、proxy implementation、decimals、capabilitiesへ結合する。
201. allowanceとPermitはexact amount、短期限、verified spenderへ限定し、無制限承認を既定にしない。
202. 同名tokenまたは未登録networkはverified registryなしにwrite対象へ選べない。
203. tokenのpause、blacklist、rebase、fee-on-transfer、proxy upgradeが未知なら取引を停止する。
204. bridge成功はsource transactionだけでなくdestination finalityとreceiptまで確認する。
205. bridge routeのcontract、guardian、upgrade、incident、finality ruleを継続監視し、drift時に停止する。
206. bridge前にdestination network fee readinessを検証し、受取後に操作不能となる経路を警告なしに使わない。
207. bridge message IDを冪等keyとし、reorg、replay、partial deliveryをblind retryしない。
208. Hyperliquid API wallet nonceは単一atomic authorityまたは安全なpartitionで管理する。
209. Hyperliquid WebSocketのsequence gap、再接続、out-of-orderを検知し、REST snapshot再同期までwriteを止める。
210. Hyperliquidのsymbol表示ではなく公式metadataのasset IDとmarket typeをExecution Capsuleへbindする。
211. partial fill、cancel race、reduce-only rejection、position driftを成功に丸めず利用者へ残余状態を表示する。
212. cross/isolated margin、funding、fee、liquidation fieldのlive stateと取得時刻を確認し、古いpreviewで実行しない。
213. Hyperliquid API、署名domain、rate limit、response schemaのdriftでfallbackせずcontract test失敗として停止する。
214. LLMはraw address、contract、asset ID、chain ID、nonce、fee route、signing payloadを権限的に決定しない。
215. LLM/model version変更はgolden corpus、shadow test、誤実行率評価、risk owner承認なしにproduction昇格しない。
216. 外部Web、QR、support message、tool responseはuntrusted dataとして利用者命令と分離する。
217. AI providerへ送る内容は最小化・redaction・retention policy・地域要件・契約をrelease gateで確認する。
218. 法務意見は法人、地域、機能、asset、custody model、release subject、期限へ結合する。
219. Apple/Google審査はsubmission ID、binary version、申告内容、承認状態のportal証拠がなければGOにしない。
220. 法規・Store規約・protocol仕様・JPYC公式情報のsource monitorにowner、確認日、expiry、緊急停止手順を持つ。
221. 監視telemetry自体のstalenessを検知し、dashboardが更新されない状態を正常と扱わない。
222. break-glass操作は二人承認、期限、command allowlist、完全audit、事後reviewを要求する。
223. provider残高、sponsor reserve、exposure、rate limit、daily loss limitを監視し、閾値超過で自動停止する。
224. 利用者確認画面は最悪受取、総費用、清算・取消不能点を最終操作直前に表示し、fold下へ隠さない。
225. エラー後の再実行は実状態照合が完了するまで禁止し、安全な次手とtrace IDを提示する。
226. 本番release前にTestnetだけでなく上限を極小化したMainnet canary、完全照合、rollback/kill-switch drillを実施する。
227. 本番運用開始後もreadiness claimのexpiry、鍵revocation、policy drift、provider incidentを継続評価し、失効時は自動BLOCKEDへ戻す。
228. Codexは実装不能な外部条件を完了扱いにせず、担当role、portal、menu、button、field、必要資料、callback、証拠path、再試験commandを記録する。
229. 最終成果物はPRODUCTION_OPERATIONAL_GOまたはBLOCKED_NOT_OPERATIONALのどちらか一つをmachine-readableに出力し、曖昧なready表現を使わない。
230. 運用GOを発行する鍵・policy・trusted time・checker anchorをrelease package内だけに保存せず、package侵害と同時に信頼根が置換されない構成にする。

231. readiness checkerのout-of-band hashは単一scriptではなく、evaluator、CLI、canonicalizer、gate profile、operational Schema、dependency lockを含むdeterministic bundleへ結合する。
232. review approvalはstatementIdだけでなくexact statement SHA-256とrelease subjectへ署名結合する。
233. 同一Ed25519 public key materialを複数keyIdへ登録してapproval thresholdを満たすことを禁止する。
234. issuer、reviewer、index signer、trusted-time signerの分離はkeyIdだけでなくprincipalIdでも検証する。
235. 署名鍵は評価時とdocument signing timeの両方で有効でなければならない。
236. production evidenceは実ファイルdigest、sizeBytes、canonical media type、採取時刻、statement発行時刻、claim max ageを同時に満たす。
237. production evidence indexは正のsequence、短期限のissuedAt/expiresAt、署名、trusted timeとのchronologyを持つ。
238. outcome=PASSのproduction statementに未解決limitationsが1件でもあればclaimを受理しない。
239. release-readiness reportはPRODUCTION_OPERATIONAL_GOでも直接transaction writeを許可せず、runtime activation eligibilityだけを示す。
240. production verifierはhermetic signed runtime、attestation、protected runner、外部root of trustなしに自己の完全性を証明したと扱わない。
241. operational evaluatorは93 claimすべてを満たすephemeral positive-path試験でGO到達可能性を検証し、その結果でもdirect writeがfalseであることを確認する。
242. trust policy、index、statement、approval、evidenceを読む際はsymlink、hardlink、unsafe mode、oversize、read中変更を拒否するsecure file snapshotを使う。


243. 署名payloadは文書種別ごとのdomain separationを持ち、statement・approval・time・index・runtime文書間で署名を再利用できない。
244. canonical JSONはlone Unicode surrogateを拒否し、全実装で同一byte vectorを検証する。
245. evidence indexはreport内digestだけでなくpackage外のexact SHA-256 anchorと一致しなければならない。
246. release readiness reportは短期限validUntilとtrust policy・verifier bundle・release subject・evidence index・trusted timeのexact digestを持つ。
247. PRODUCTION_OPERATIONAL_GOは全37 gate rowが正本inventoryと一致してPASSし、全93 claim acceptedの場合だけ成立する。
248. release readiness evaluatorもruntime evaluatorも直接transaction authorizationを返さない。
249. 本番accountはrelease、deployment、registry、user key、device key、device attestationへ署名済みbindingで結合する。
250. account binding、runtime state、leaseのsequenceはsigner保護領域のhigh-water markより大きい場合だけ受理する。
251. 価格を伴う操作はnon-zero quote hashと短期限quoteValidUntilを操作別署名へ結合する。
252. Execution Capsuleはsource network、destination network集合、chain ID、network registry digestをsemantic hashへ含める。
253. state evidenceはaggregate時刻だけでなく各sourceのID、digest、観測時刻、chronologyを検証する。
254. user、device、policy engineの操作別署名はdistinct key material、keyId、principalでなければならない。
255. atomic signerはruntime decisionを権限として盲信せず、全immutable inputを保護境界内で再読込・再評価する。
256. authorization IDとnonceの予約・消費・署名結果記録は一つの原子的状態遷移で行い、署名後は再利用しない。
257. runtime authorizerの信頼hashはevaluatorだけでなくpolicy、Schema、canonicalizer、CLI、positive/negative testsを含むbundleへ結合する。
258. step type capability mappingの全値はleaseとoperationの両allowlist内でなければならず、未知stepは拒否する。

259. `--check`またはverification modeの全toolは、成功・失敗・例外・timeoutのいずれでも正本treeを変更しない。
260. full validationはvalidatorのexact allowlist、順序、重複なしを自己検査し、一つでもimport/起動/終了に失敗すれば全体を失敗させる。
261. trusted timeとevidence indexのsequence high-water markはrelease package外のrollback-resistant storeに保存し、候補値が厳密に増加しない限り受理しない。
262. runtime authorizationは現在のtrusted-time sequenceとreadiness reportへ結合されたtrustedTimeSequenceをexact一致させ、evidenceIndexSequenceも保護high-waterより上であることを確認する。
263. 価格・交換率・手数料を伴う操作は、provider、route、account、network、asset、入力額、最低受取、最大fee、slippage/limit、source state、生成・失効時刻を含むdomain-separated canonical quote documentへ結合する。
264. protected signerはexact signed network/asset registryを読み、CAIP-2 networkId、numeric chainId、RPC報告chainId、contract、proxy implementation、code hash、decimalsの一致を最終payload生成時に再検証する。
265. protected signerはExecution Capsule、operation authorization、quote documentから最終order/transaction bytesを再構築し、そのcommitmentが利用者承認対象と一致しない限り署名しない。
266. `SIGNED_BROADCAST_UNKNOWN`、`BROADCAST_ACCEPTED_UNCONFIRMED`、`PARTIAL`はblind retry不能とし、既存operation ID/nonce/cloid/message IDの照合が完了するまで新規署名を禁止する。
267. validatorのimport error、依存欠落、signal終了、timeout、出力解析不能はskipやwarningではなくrelease blockerとする。
268. ChatGPT／OpenAI-facing surfaceは、抽象read-only状態、固定用語、固定非取引エラー、一般安全案内、固定中立handoffだけを返し、取引文・金額・宛先・asset／network・下書き・quote・ボタン手順・復旧手順・実行linkを受理または出力しない。取引固有の自然言語解析とManualFallbackは独立wallet内へ隔離する。
