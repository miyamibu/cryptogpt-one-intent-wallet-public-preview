# UI Adversarial Review

## 攻撃者の視点

### Address poisoning

- aliasは同じ、addressは末尾だけ似せる
- clipboardを置換
- QRを差し替える
- ENS等の解決結果を変更

対策：full address、fingerprint、chain、registration source、cooling period。貼付直後の即送信禁止。

### Visual substitution

- cardは200 USDC、backendは2,000 USDC
- fee fieldをscroll外へ押す
- loading overlayでbutton labelを隠す
- dark modeでwarningを消す

対策：renderReceiptHash、semanticHash、critical region screenshot tests、signer再構築表示モデル。

### Interaction confusion

- double tap
- back gesture中のtap
- Face ID cancel後のstale authorization
- keyboard submitとorder submit混同

対策：one-shot challenge、UI state machine、button debounceではなくidempotency、auth cancellationでcapsule invalidation。

## デザイナーの意地悪レビュー

- 1px dividerがRetinaでぼやけていないか
- cardのradiusとbutton radiusの階層が逆転していないか
- number columnの右端が揃っているか
- spinnerでlayoutが1px跳ねないか
- warning iconだけ2px下がっていないか
- pressed stateでtextが移動しないか
- Japanese glyphのbaselineがLatin numberとずれていないか
- multiline buttonのline-heightが窮屈でないか

## 小型画面

- 375×667でExecution Card＋keyboard
- iPhone landscape
- Android compact 360幅
- 200% text

critical fieldsを折り畳まない。画面遷移を増やさず、card内部をscroll可能にしてaction buttonはsafe areaへ固定する。ただしbuttonとcard内容の間に「見ていないまま押せる」距離を作らないため、未読critical fieldがある間はbuttonに要約を残す。

## Admin UI

- Mainnet ONをtoggle一つで変更しない
- target environment、feature、region、expiryを同時表示
- second approverを同一sessionで代行できない
- revokeとdeleteを混同しない
- audit exportにsecretを含めない
