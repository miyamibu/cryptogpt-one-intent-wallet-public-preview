'use strict';

const flows = {
  perp: {
    user: 'BTCを500 USDC、ペイパチャルで3倍。生産価格も見せて。',
    interpretation: '「ペイパチャル」は先物取引（期限なし）、「生産価格」は清算価格の候補として読み取りました。意味の確認が終わるまで注文確認へ進みません。',
    title: 'BTCを3倍で買う',
    badge: '先物取引（期限なし）',
    badgeTone: 'warning',
    summary: '元手500 USDC・損切りは未設定',
    requiresCorrectionConfirmation: true,
    rows: [
      ['売買方向', '買い'],
      ['取引の種類', '先物取引（期限なし）'],
      ['元手', '500 USDC'],
      ['取引の大きさ', '約1,500 USDC'],
      ['取引倍率', '3倍'],
      ['現在の参考価格', '100,000 USDC（画面例）'],
      ['清算価格の目安', '67,300 USDC（画面例）'],
      ['清算までの距離', '約32.7%（画面例）'],
      ['証拠金の方式', '口座全体で共有（画面例）'],
      ['損切り価格', '未設定'],
      ['予定価格と成立価格のずれの上限', '0.30%（画面例・利用者設定ではない）'],
      ['取引手数料の目安', '0.53 USDC（画面例）'],
      ['情報の新しさ', '10秒以内（画面例）']
    ],
    notice: '清算価格は保証値ではありません。口座の他の取引、担保残高、資金調整料、未成立注文、成立価格で変わります。送信直前と成立後に取得し直し、値を取得できない・古い・口座状態と合わない場合は停止します。損切り注文も必ず成立するとは限りません。',
    button: 'この注文内容を確認する',
    sub: '聞き間違いの確認後も、署名前の最終画面で金額・方向・倍率・清算価格を再表示します。'
  },
  spot: {
    user: 'スポットでHYPEを300 USDC分買って。',
    interpretation: '「スポット」は現物取引として読み取りました。HYPEを、保有する300 USDCを使って買う下書きです。',
    title: 'HYPEを現物で買う',
    badge: '現物取引',
    summary: '300 USDC・最低5.914 HYPE（画面例）',
    rows: [
      ['売買方向', '買い'],
      ['取引の種類', '現物取引'],
      ['使う金額', '300 USDC'],
      ['受取見込み', '約5.940 HYPE（画面例）'],
      ['最低受取', '5.914 HYPE（画面例）'],
      ['予定価格と成立価格のずれの上限', '0.40%（画面例・利用者設定ではない）'],
      ['成立方法', 'すぐ成立する数量だけ'],
      ['取引手数料の目安', '0.21 USDC（画面例）'],
      ['情報の新しさ', '10秒以内（画面例）']
    ],
    notice: '最低受取額を下回る場合は停止します。似た名前の資産、桁数の違い、古い価格を検出しても、別の資産や経路へ勝手に切り替えません。',
    button: 'この購入内容を確認する',
    sub: '本番では最新の価格・最低受取額・手数料を取得し直してから署名します。'
  },
  send: {
    user: '友人Aに50 USDC送って。',
    interpretation: '保存済みの「友人A」へ、Hyperliquid内で50 USDCを送る下書きです。名前だけでなく、完全なアドレスと指紋も確認します。',
    title: '友人Aへ送る',
    badge: '保存済みの相手',
    summary: '50 USDC・Hyperliquid内',
    rows: [
      ['送る相手', '友人A'],
      ['送る金額', '50 USDC'],
      ['送金元ネットワーク', 'Hyperliquid'],
      ['送金先ネットワーク', 'Hyperliquid'],
      ['送金先アドレス', '0x2222222222222222222222222222222222222222（画面例のダミー）'],
      ['照合用の指紋', '2222・2222・2222（画面例）'],
      ['送金手数料の上限', '0.10 USDC（画面例）'],
      ['見積もりの有効期限', '画面例・あと60秒']
    ],
    notice: '保存名が同じでもアドレスが変われば新しい相手として扱います。全額、高額、新しい相手、ネットワーク不一致では必ず停止して再確認します。',
    button: '送金内容を確認する',
    sub: 'これはHyperliquidからArbitrumへ出す操作ではありません。'
  },
  withdraw: {
    user: '自分のArbitrumへ200 USDC移して。',
    interpretation: 'Hyperliquidから、保存済みの自分のArbitrum受取先へ200 USDCを出す下書きです。',
    title: 'HyperliquidからArbitrumへ移す',
    badge: '向き：Hyperliquid → Arbitrum',
    summary: '200 USDC・自分の保存済み口座',
    rows: [
      ['送金元', 'Hyperliquid'],
      ['受取ネットワーク', 'Arbitrum'],
      ['送る金額', '200 USDC'],
      ['送金先アドレス', '0x2222222222222222222222222222222222222222（画面例のダミー）'],
      ['照合用の指紋', '2222・2222・2222（画面例）'],
      ['手数料の上限', '1 USDC（画面例）'],
      ['受付の確認', 'Hyperliquid側で追跡'],
      ['到着の確認', 'Arbitrum側で別に追跡'],
      ['見積もりの有効期限', '画面例・あと60秒']
    ],
    notice: '「受付済み」と「Arbitrumへ到着済み」は別の状態です。到着確認まで完了扱いにせず、実行直前に正式な出金経路・停止状態・手数料を再確認します。',
    button: '別ネットワークへの送金を確認する',
    sub: '新しい送金先・全額・高額・ネットワーク変更は毎回確認します。'
  },
  bridge: {
    user: 'Arbitrumから500 USDCを入れて。',
    interpretation: 'ArbitrumからHyperliquidへ、正式なUSDCを500 USDC移す下書きです。',
    title: 'ArbitrumからHyperliquidへ入れる',
    badge: '向き：Arbitrum → Hyperliquid',
    summary: '500 USDC・正式な経路だけ',
    rows: [
      ['送金元ネットワーク', 'Arbitrum'],
      ['受取先', 'Hyperliquid'],
      ['資産', '正式なUSDCを実行時に照合'],
      ['金額', '500 USDC'],
      ['受取先アドレス', '0x1111111111111111111111111111111111111111（画面例のダミー）'],
      ['照合用の指紋', '1111・1111・1111（画面例）'],
      ['ネットワーク手数料の上限', '2 USDC相当（画面例）'],
      ['経路', '正式な経路を実行時に照合']
    ],
    notice: '正式な資産、受取先、一時停止状態を実行直前に確認します。似た名前の資産や外部サービスへ勝手に切り替えず、送金元側でもネットワーク名を一致させます。',
    button: '受取手順と費用を確認する',
    sub: '画面見本のため、実際の資金移動や外部接続はありません。'
  },
  vault: {
    user: 'HLPの運用口座に300 USDC入れて。',
    interpretation: 'HLPの運用口座へ300 USDCを預ける下書きです。銀行預金ではなく、元本割れや引き出し制限の可能性があります。',
    title: 'HLPの運用口座へ預ける',
    badge: '元本保証なし',
    badgeTone: 'danger',
    summary: '300 USDC・損失と制限を先に確認',
    rows: [
      ['預ける金額', '300 USDC'],
      ['引き出せない期間', '4日（画面例・実行前に再確認）'],
      ['元本保証', 'なし'],
      ['損失の可能性', 'あり'],
      ['過去の成績', '取得時刻つきの最新値だけ'],
      ['過去の最大下落', '取得できる場合に表示'],
      ['現在の運用総額', '取得時刻つきで表示'],
      ['資金の使われ方', '実行前に説明'],
      ['費用', '内訳と上限を表示']
    ],
    notice: '利益だけを強調しません。損失、引き出せない期間、資金の使われ方、情報の取得時刻を同じ画面で示し、取得できない値を推測で埋めません。',
    button: 'リスクと預入内容を確認する',
    sub: '本番では最新情報を再取得し、元本保証がないことを署名前に再表示します。'
  },
  jpyc: {
    user: '日本円から1万円分のJPYCを受け取りたい。',
    interpretation: 'JPYC EXの本人確認と申込み画面へ移り、正式なJPYCをこのウォレットで受け取る流れです。このウォレットは発行や審査を代行しません。',
    title: '日本円からJPYCを受け取る',
    badge: 'JPYC EXで最終手続き',
    summary: '申込額10,000円・受取先は実行時に選択',
    rows: [
      ['申込額', '10,000円'],
      ['受取予定', '10,000 JPYC（申込画面で再確認）'],
      ['受取ネットワーク', 'Polygon（画面例）'],
      ['受取先アドレス', '0x1111111111111111111111111111111111111111（画面例のダミー）'],
      ['照合用の指紋', '1111・1111・1111（画面例）'],
      ['正式なJPYCの確認', '有効期限内の公式登録情報と照合'],
      ['本人確認と最終申込み', 'JPYC EXで本人が行う'],
      ['銀行などの費用', 'JPYC EXの画面で確認'],
      ['完了後', 'このウォレットで入金を確認']
    ],
    notice: 'このウォレットやChatGPTが、JPYC EXの審査・本人確認・追加認証・最終申込みを代行または迂回することはありません。ネットワークと正式な登録情報を実行時に照合し、期限切れなら停止します。',
    button: '移動前の内容を確認する',
    sub: 'この画面見本は外部サイトを開きません。本番でも受取先・ネットワーク・金額を移動前に再表示します。'
  },
  fee: {
    user: 'JPYCしかないけど、3,000 JPYCを友人Aへ送って。',
    interpretation: 'Polygonの手数料用資産POLが0です。この画面例では、口座方式と代理支払い経路の両方が確認済みの場合だけ、必要最小限の費用をJPYCで精算する想定です。',
    title: 'ネットワーク手数料を準備する',
    badge: '口座と経路の証明が必要',
    badgeTone: 'warning',
    summary: 'JPYCだけ保有・POL残高0',
    rows: [
      ['JPYC残高', '10,000 JPYC（画面例）'],
      ['送る金額', '3,000 JPYC'],
      ['現在のPOL残高', '0 POL（不足）'],
      ['この画面例の口座方式', '代理支払い対応のスマート口座'],
      ['代理支払いの提供者', '本番では法人名・連絡先・規約を表示'],
      ['精算先', '本番では契約先と完全な識別子を表示'],
      ['対応確認', '口座・ネットワーク・資産・操作が一致（画面例）'],
      ['POLが0でも開始できる根拠', '一括代理支払いの有効な証明あり（画面例）'],
      ['今回の手数料見積もり', '0.012 POL（画面例）'],
      ['JPYCで精算する見込み', '18 JPYC（画面例）'],
      ['JPYCで精算する上限', '25 JPYC（画面例・利用者設定ではない）'],
      ['失敗時の請求', '0 JPYC（画面例・条件を表示）'],
      ['見積もりID', '本番では署名対象と結び付けて表示'],
      ['見積もりの有効期限', '画面例・あと60秒'],
      ['失敗した場合', '別経路へ自動変更せず停止']
    ],
    notice: '通常のウォレットでは、POLが0だとJPYCの交換自体を始められない場合があります。口座方式、代理支払い能力、必要な許可、失敗時の請求、見積もりの結び付きを証明できなければ、この処理は行わず手動手順へ切り替えます。',
    button: '費用と送金内容を確認する',
    sub: '手数料が足りていれば準備しません。提供者・回収上限・期限を表示できない場合も進めません。'
  },
  setup: {
    user: '最初の一回だけ承認して、あとは会話で進めたい。',
    interpretation: '秘密鍵の共有や無期限の包括承認ではなく、保存期間、利用中の時間、金額、資産、ネットワーク、相手、費用、取引倍率を限定した設定を作ります。',
    title: '会話操作の範囲を設定する',
    badge: '制限付き・いつでも停止',
    summary: '表示中の制限値は画面例・初期値ではありません',
    rows: [
      ['設定の保存期間', '30日（画面例・初期値ではない）'],
      ['1回の利用時間', '最大30分（画面例）'],
      ['無操作で停止', '10分（画面例）'],
      ['1回あたりの上限', '30,000円相当（画面例）'],
      ['1日あたりの上限', '60,000円相当（画面例）'],
      ['1か月あたりの上限', '300,000円相当（画面例）'],
      ['対応する資産', 'USDC・JPYC・HYPEだけ（画面例）'],
      ['対応するネットワーク', '保存済みの範囲だけ（画面例）'],
      ['保存済みの送金先', '友人A・自分の口座（画面例）'],
      ['取引倍率', '最大3倍（画面例）'],
      ['手数料の自動準備', '月500 JPYCまで（画面例）'],
      ['無制限の資産利用許可', '禁止'],
      ['毎回確認する操作', '新規相手・高額・全額・鍵・権限変更'],
      ['停止と取消し', 'この画面の「確認・停止」から']
    ],
    notice: '表示中の期間・金額・資産・送金先はすべて画面例で、既定値ではありません。利用者が一項目ずつ選びます。「最初の一回だけ」は、秘密鍵を渡すことでも、無期限・無制限に資産を使わせることでもありません。範囲外、期限切れ、不審な端末、急な費用上昇、古い価格では必ず停止します。',
    button: '限定した設定内容を確認する',
    sub: 'ChatGPT内では実取引を行わず、独立したウォレット内だけで使う設定です。'
  },
  composite: {
    user: 'HYPEを全部売って、300 USDCをHLPの運用口座へ、残りをArbitrumへ。',
    interpretation: '3つの操作を順番に進める下書きです。「全部」は直前の残高で確定し、各段階の最低額・費用・送金先を別々に示します。',
    title: '3つの操作を順番に進める',
    badge: '途中停止を前提に確認',
    badgeTone: 'warning',
    summary: '売却 → 300 USDCを運用 → 残りを送る',
    rows: [
      ['1．売却後の最低受取', '948.50 USDC（費用差引後・画面例）'],
      ['2．HLPの運用口座へ', '300.00 USDC（依頼額）'],
      ['3．送金前に残る最低額', '648.50 USDC（画面例）'],
      ['Arbitrumへの送金手数料上限', '1.00 USDC（画面例）'],
      ['Arbitrum到着の最低見込み', '647.50 USDC（画面例）'],
      ['送金先アドレス', '0x2222222222222222222222222222222222222222（画面例のダミー）'],
      ['照合用の指紋', '2222・2222・2222（画面例）'],
      ['処理順', '1の確定後に2、2の確定後に3'],
      ['途中で止まった場合', '完了済みを繰り返さず、残りだけ作り直す']
    ],
    notice: '一度の確認でも、ネットワーク上では一段ずつ処理します。最低額を下回る、運用口座への預入に失敗する、送金費用が上限を超える場合は次へ進みません。',
    button: '3段階の内容と順番を確認する',
    sub: '最低到着額は 948.50 − 300.00 − 1.00 ＝ 647.50 USDC です。'
  },
  partial: {
    user: '前のまとめ操作はどうなった？',
    interpretation: '完了した操作、まだ始めていない操作、現在資産がある場所を分けて表示します。',
    title: '途中で止まった操作',
    badge: '残りだけ確認',
    badgeTone: 'warning',
    type: 'partial'
  },
  manual: {
    user: '手数料の自動準備ができない時は、どうすればいい？',
    interpretation: '確認済みの代理支払いも、POLが0のまま始められる正式な経路も使えない想定です。固定の金額を案内せず、その時点の見積もりと有効期限を取得してから手順を示します。',
    title: '自動で準備できない場合',
    badge: '固定金額では案内しない',
    badgeTone: 'danger',
    type: 'manual'
  }
};

const card = document.getElementById('executionCard');
const timeline = document.getElementById('timeline');
const userBubble = document.getElementById('userBubble');
const phone = document.getElementById('phone');
const assurance = document.getElementById('assuranceText');
const liveStatus = document.getElementById('liveStatus');
const themeToggle = document.getElementById('themeToggle');
const largeTextToggle = document.getElementById('largeTextToggle');
let currentFlow = 'perp';
let currentPlatform = 'ios';
let interpretationConfirmed = false;

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[character]));
}

function setStatus(message) {
  liveStatus.textContent = message;
  assurance.textContent = message;
}

function rowHtml([label, value]) {
  const address = /^0x[0-9a-f]{40}$/i.test(String(value)) || label.includes('アドレス');
  return `<div class="row ${address ? 'address-row' : ''}">
    <span class="label">${escapeHtml(label)}</span>
    <span class="value ${address ? 'address' : ''}">${escapeHtml(value)}</span>
  </div>`;
}

function understandingHtml(flow) {
  return `<div class="understanding ${flow.requiresCorrectionConfirmation && !interpretationConfirmed ? 'requires-check' : ''}">
    <strong>聞き取った言葉と確認した理解</strong>
    <span class="heard"><b>聞き取った言葉：</b>${escapeHtml(flow.user)}</span>
    <span class="normalized"><b>確認した理解：</b>${escapeHtml(flow.interpretation)}</span>
  </div>`;
}

function correctionHtml(flow) {
  if (!flow.requiresCorrectionConfirmation) return '';
  const confirmedText = interpretationConfirmed
    ? '<p class="correction-help">確認済みです。注文確認へ進めます。最終署名の前にも再表示します。</p>'
    : '<p class="correction-help">確認するまで下の注文確認ボタンは使えません。</p>';
  return `<fieldset class="correction-check">
    <legend>聞き間違いの確認</legend>
    <div class="correction-actions">
      <button id="confirmInterpretation" class="secondary" type="button" ${interpretationConfirmed ? 'disabled' : ''}>「清算価格」の意味で合っています</button>
      <button id="editInterpretation" class="text-action" type="button">読み取りを直す</button>
    </div>
    ${confirmedText}
  </fieldset>`;
}

function actionHtml(flow, buttonId = 'executeButton') {
  const disabled = flow.requiresCorrectionConfirmation && !interpretationConfirmed;
  return `<div class="action-footer">
    <p class="final-check-label">明細の最後です。金額・相手・ネットワーク・上限をもう一度確認してください。</p>
    ${flow.sub ? `<p class="subline pre-action">${escapeHtml(flow.sub)}</p>` : ''}
    <button id="${buttonId}" class="primary" type="button" ${disabled ? 'disabled aria-disabled="true"' : ''}>${escapeHtml(flow.button)}</button>
  </div>`;
}

function getActiveScroller() {
  return document.getElementById('reviewScroll');
}

function updateScrollStatus(scroller = getActiveScroller()) {
  if (!scroller) return;
  const status = document.getElementById('scrollStatus');
  if (!status) return;
  const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight);
  const atTop = scroller.scrollTop <= 2;
  const scrollerRect = scroller.getBoundingClientRect();
  const activeCard = document.querySelector('.execution-card:not(.hidden), .timeline:not(.hidden)');
  const lastBlock = activeCard ? activeCard.lastElementChild : null;
  const lastBlockFullyVisible = Boolean(lastBlock) && lastBlock.getBoundingClientRect().bottom <= scrollerRect.bottom + 2;
  const atBottom = scroller.scrollTop >= max - 2 || lastBlockFullyVisible;
  let position = 'middle';
  let icon = '↕';
  let text = '上下に続きがあります';
  if (max <= 2) {
    position = 'all'; icon = '✓'; text = 'すべて表示しています';
  } else if (atTop) {
    position = 'top'; icon = '↓'; text = '下に続きがあります';
  } else if (atBottom) {
    position = 'bottom'; icon = '✓'; text = 'ここが最後です';
  }
  status.dataset.position = position;
  status.querySelector('.scroll-status-icon').textContent = icon;
  status.querySelector('.scroll-status-text').textContent = text;
}

function resetScrollAndStatus() {
  const scroller = getActiveScroller();
  if (!scroller) return;
  scroller.scrollTop = 0;
  updateScrollStatus(scroller);
}

function wireScroller() {
  const scroller = getActiveScroller();
  if (!scroller) return;
  if (scroller.dataset.scrollBound !== 'true') {
    scroller.addEventListener('scroll', () => updateScrollStatus(scroller), {passive: true});
    scroller.dataset.scrollBound = 'true';
  }
  resetScrollAndStatus();
}

function renderStandard(flow) {
  timeline.classList.add('hidden');
  card.classList.remove('hidden');
  card.innerHTML = `
    <header class="card-head">
      <h3>${escapeHtml(flow.title)}</h3>
      <span class="badge ${escapeHtml(flow.badgeTone || '')}">${escapeHtml(flow.badge)}</span>
    </header>
    <div class="card-content">
      <p class="sticky-summary">${escapeHtml(flow.summary)}</p>
      ${understandingHtml(flow)}
      ${correctionHtml(flow)}
      <div class="rows">${flow.rows.map(rowHtml).join('')}</div>
      <p class="notice">${escapeHtml(flow.notice)}</p>
      ${actionHtml(flow)}
    </div>
  `;
  wireCardActions(flow);
  wireScroller();
}

function renderPartial(flow) {
  card.classList.add('hidden');
  timeline.classList.remove('hidden');
  timeline.innerHTML = `
    <header class="card-head">
      <h3>${escapeHtml(flow.title)}</h3>
      <span class="badge warning">${escapeHtml(flow.badge)}</span>
    </header>
    <div class="card-content timeline-content">
      ${understandingHtml(flow)}
      <div class="step"><span class="step-number">1</span><div><strong>HYPEの売却は完了</strong><small>948.72 USDC（画面例）を受け取り済み。取引番号と成立価格を照合済みの画面例です。</small></div></div>
      <div class="step"><span class="step-number">2</span><div><strong>HLPの運用口座への300 USDCは完了</strong><small>預入済み。完了済みの操作は再実行しません。</small></div></div>
      <div class="step"><span class="step-number">3</span><div><strong>Arbitrumへの送金は開始していません</strong><small>648.72 USDC（画面例）はHyperliquidに残っています。手数料が上限を超えたため、安全に停止した画面例です。</small></div></div>
      <p class="notice danger">再開時は現在残高、送金先アドレス、Arbitrum、最新手数料を取得し直し、残りの送金だけを新しい確認として作ります。</p>
      <div class="action-footer">
        <p class="final-check-label">完了済みと未開始を区別し、残りだけを再作成します。</p>
        <p class="subline pre-action">画面見本のため、実際の再開や送金は行いません。</p>
        <button id="resumeButton" class="primary" type="button">残りの送金だけを作り直す</button>
      </div>
    </div>
  `;
  document.getElementById('resumeButton').addEventListener('click', () => setStatus('画面見本：残りの操作だけを再見積もりする想定です。実処理はありません。'));
  wireScroller();
}

function renderManual(flow) {
  timeline.classList.add('hidden');
  card.classList.remove('hidden');
  card.innerHTML = `
    <header class="card-head">
      <h3>${escapeHtml(flow.title)}</h3>
      <span class="badge danger">${escapeHtml(flow.badge)}</span>
    </header>
    <div class="card-content">
      <p class="sticky-summary">必要量は、その時点の見積もりから表示</p>
      ${understandingHtml(flow)}
      <div class="manual-step"><span class="step-number">1</span><div><strong>「手数料見積もりを更新」を押す</strong><small>対象操作、Polygon、POLの現在残高、混雑状況を取得します。取得できない場合は送らないでください。</small></div></div>
      <div class="manual-step"><span class="step-number">2</span><div><strong>画面に表示された推奨量と有効期限を確認する</strong><small>固定値ではありません。「必要量＋小さな予備」と根拠を表示し、期限切れなら再見積もりします。</small></div></div>
      <div class="manual-step"><span class="step-number">3</span><div><strong>下の「資産」→「受け取る」→「Polygon」を選ぶ</strong><small>別のネットワークを選ばないでください。手数料用資産がPOLであることも照合します。</small></div></div>
      <div class="manual-step"><span class="step-number">4</span><div><strong>完全な受取アドレスと照合用の指紋を確認してコピーする</strong><small>画面例のダミー：0x1111111111111111111111111111111111111111／指紋 1111・1111・1111。</small></div></div>
      <div class="manual-step"><span class="step-number">5</span><div><strong>別のウォレットまたは取引所から、表示された推奨量だけPOLを送る</strong><small>送金元でもPolygonを選びます。推奨量を取得できない、最低出金額が大きすぎる、ネットワークが一致しない場合は中止します。</small></div></div>
      <div class="manual-step"><span class="step-number">6</span><div><strong>このアプリへ戻り「残高を更新」を押す</strong><small>POLの着金と必要残高を確認してから、元のJPYC送金を新しく見積もります。</small></div></div>
      <p class="notice danger">少額でも誤ったネットワークやアドレスへ送ると戻せない場合があります。推奨量を取得できない場合、固定のPOL量を推測して送らないでください。</p>
      <div class="action-footer">
        <p class="final-check-label">固定量を案内せず、対象操作に結び付いた最新見積もりを先に取得します。</p>
        <p class="subline pre-action">画面見本では「実行時に取得」と表示するだけで、価格・手数料・残高を取得しません。</p>
        <button id="estimateButton" class="primary" type="button">手数料見積もりを更新する</button>
      </div>
    </div>
  `;
  document.getElementById('estimateButton').addEventListener('click', () => setStatus('画面見本：本番では最新の推奨量と有効期限を取得します。ここでは取得しません。'));
  wireScroller();
}

function wireCardActions(flow) {
  const confirm = document.getElementById('confirmInterpretation');
  const edit = document.getElementById('editInterpretation');
  const execute = document.getElementById('executeButton');

  if (confirm) {
    confirm.addEventListener('click', () => {
      interpretationConfirmed = true;
      render();
      setStatus('「生産価格」は「清算価格」の意味であると確認しました。注文確認へ進めます。');
      const enabled = document.getElementById('executeButton');
      if (enabled) enabled.focus({preventScroll: true});
    });
  }
  if (edit) {
    edit.addEventListener('click', () => setStatus('読み取りを直す入力欄を開く想定です。この画面見本では実入力を行いません。'));
  }
  if (execute) {
    execute.addEventListener('click', () => {
      if (execute.disabled) return;
      setStatus('画面見本：独立したウォレットの最終確認と署名画面へ進む想定です。実処理はありません。');
    });
  }
}

function render() {
  const flow = flows[currentFlow];
  userBubble.textContent = flow.user;
  if (flow.type === 'partial') renderPartial(flow);
  else if (flow.type === 'manual') renderManual(flow);
  else renderStandard(flow);
  assurance.textContent = '画面見本・外部通信なし・秘密鍵や復旧情報を入力しないでください';
  resetScrollAndStatus();
}


function setPressed(selector, active) {
  document.querySelectorAll(selector).forEach(button => {
    const isActive = button === active;
    button.classList.toggle('active', isActive);
    button.setAttribute('aria-pressed', String(isActive));
  });
}

document.querySelectorAll('[data-flow]').forEach(button => {
  button.addEventListener('click', () => {
    currentFlow = button.dataset.flow;
    interpretationConfirmed = false;
    setPressed('[data-flow]', button);
    render();
    setStatus(`${button.textContent.trim().replace(/\s+/g, ' ')}の画面見本を表示しました。`);
  });
});

document.querySelectorAll('[data-platform]').forEach(button => {
  button.addEventListener('click', () => {
    currentPlatform = button.dataset.platform;
    phone.classList.toggle('android', currentPlatform === 'android');
    phone.classList.toggle('ios', currentPlatform === 'ios');
    setPressed('[data-platform]', button);
    setStatus(`${currentPlatform === 'ios' ? 'iPhone' : 'Pixel 9a'}の表示へ切り替えました。`);
  });
});

themeToggle.addEventListener('change', () => {
  phone.dataset.theme = themeToggle.checked ? 'dark' : 'light';
  setStatus(`${themeToggle.checked ? '暗い表示' : '明るい表示'}へ切り替えました。`);
});

largeTextToggle.addEventListener('change', () => {
  phone.classList.toggle('large-text', largeTextToggle.checked);
  setStatus(`${largeTextToggle.checked ? '大きな文字' : '通常の文字'}へ切り替えました。依頼内容は残ります。`);
});

document.getElementById('permissionButton').addEventListener('click', () => {
  setStatus('会話操作の期限・上限・相手・停止・取消しを確認する画面を開く想定です。');
});

document.querySelector('.account').addEventListener('click', () => {
  setStatus('完全な口座アドレス、照合用の指紋、利用ネットワークを確認する画面を開く想定です。');
});

window.__WALLET_PROTOTYPE__ = Object.freeze({
  flows,
  getState: () => Object.freeze({
    currentFlow,
    currentPlatform,
    interpretationConfirmed,
    largeText: largeTextToggle.checked,
    theme: phone.dataset.theme
  }),
  resetScrollAndStatus,
  updateScrollStatus
});

render();
