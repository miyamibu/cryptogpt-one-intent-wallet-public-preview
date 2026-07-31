#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import platform
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
from playwright.async_api import async_playwright

from artifact_io import json_bytes, write_or_check
from package_metadata import ROOT, load_package_metadata

METADATA = load_package_metadata()
SHOTS = ROOT / "prototype/screenshots"
EVIDENCE = ROOT / "tests/prototype-visual-evidence.json"
BUILD_TIMESTAMP = METADATA.deterministic_build_timestamp
FLOWS = ("perp", "spot", "send", "withdraw", "bridge", "vault", "jpyc", "fee", "setup", "composite", "partial", "manual")
VIEWPORTS = (
    ("iphone-se-stress", "ios", 320, 568),
    ("iphone-small", "ios", 375, 667),
    ("iphone-faceid", "ios", 390, 844),
    ("iphone-large", "ios", 430, 932),
    ("android-compact", "android", 360, 800),
    ("pixel9a-logical", "android", 412, 915),
)


def render_profile() -> dict[str, str]:
    return {
        "platform": sys.platform,
        "osRelease": platform.release(),
        "machine": platform.machine(),
    }


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise RuntimeError(f"invalid PNG screenshot: {path.relative_to(ROOT)}")
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def bundled_html() -> str:
    html = (ROOT / "prototype/index.html").read_text(encoding="utf-8")
    css = (ROOT / "prototype/styles.css").read_text(encoding="utf-8")
    js = (ROOT / "prototype/app.js").read_text(encoding="utf-8")
    return html.replace('<link rel="stylesheet" href="styles.css" />', f"<style>{css}</style>").replace(
        '<script src="app.js"></script>', f"<script>{js}</script>"
    )


MATRIX_JS = r"""
(cfg) => {
  const errors = [];
  let scrollCases = 0;
  const by = (selector) => document.querySelector(selector);
  const visible = (e) => {
    if (!e) return false;
    const s = getComputedStyle(e), r = e.getBoundingClientRect();
    return s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity) !== 0 && r.width > .5 && r.height > .5;
  };
  const rect = (e) => e.getBoundingClientRect();
  const clippedRect = (e, boundary) => {
    const r = rect(e), limit = boundary ? rect(boundary) : {left:-Infinity,top:-Infinity,right:Infinity,bottom:Infinity};
    let left = Math.max(r.left, limit.left), top = Math.max(r.top, limit.top);
    let right = Math.min(r.right, limit.right), bottom = Math.min(r.bottom, limit.bottom);
    let n = e.parentElement;
    const clips = (v) => ['hidden','auto','scroll','clip'].includes(v);
    while (n && n !== document.documentElement) {
      const s = getComputedStyle(n), nr = rect(n);
      if (clips(s.overflowX)) { left = Math.max(left, nr.left); right = Math.min(right, nr.right); }
      if (clips(s.overflowY)) { top = Math.max(top, nr.top); bottom = Math.min(bottom, nr.bottom); }
      n = n.parentElement;
    }
    return {left,top,right,bottom,width:Math.max(0,right-left),height:Math.max(0,bottom-top)};
  };
  const inside = (a, b, tolerance = 1.75) => {
    const x = rect(a), y = rect(b);
    return x.left >= y.left - tolerance && x.top >= y.top - tolerance && x.right <= y.right + tolerance && x.bottom <= y.bottom + tolerance;
  };
  const intersects = (a, b) => {
    const x = rect(a), y = rect(b);
    return x.right > y.left && x.left < y.right && x.bottom > y.top && x.top < y.bottom;
  };
  // Chromium can report up to ~5 CSS px of glyph overhang for Japanese punctuation.
  const overflowX = (e) => e.scrollWidth > e.clientWidth + 6;
  const overflowY = (e) => e.scrollHeight > e.clientHeight + 2;
  const parse = (value) => {
    const m = String(value).match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number);
    return {r:p[0], g:p[1], b:p[2], a:p.length > 3 ? p[3] : 1};
  };
  const blend = (fg, bg) => ({
    r: fg.r * fg.a + bg.r * (1 - fg.a),
    g: fg.g * fg.a + bg.g * (1 - fg.a),
    b: fg.b * fg.a + bg.b * (1 - fg.a), a: 1
  });
  const background = (el) => {
    const chain = []; let n = el;
    while (n && n.nodeType === 1) { chain.push(n); n = n.parentElement; }
    let out = {r:255,g:255,b:255,a:1};
    for (const item of chain.reverse()) {
      const c = parse(getComputedStyle(item).backgroundColor);
      if (c && c.a > 0) out = blend(c, out);
    }
    return out;
  };
  const linear = (x) => { x /= 255; return x <= .04045 ? x / 12.92 : Math.pow((x + .055) / 1.055, 2.4); };
  const luminance = (c) => .2126 * linear(c.r) + .7152 * linear(c.g) + .0722 * linear(c.b);
  const ratio = (a, b) => (Math.max(luminance(a), luminance(b)) + .05) / (Math.min(luminance(a), luminance(b)) + .05);
  const contrastSelectors = [
    '.muted','.seg','.flow','.review-box','.eyebrow','.account','.simulation-strip',
    '.permission-rail strong','.permission-rail small','.rail-button','.bubble.assistant','.bubble.user',
    '.card-head h3','.sticky-summary','.badge','.understanding','.correction-help','.secondary','.text-action',
    '.label','.value','.notice','.primary','.subline','.final-check-label','.scroll-status',
    '.step strong','.step small','.manual-step strong','.manual-step small','.fake-input','.assurance'
  ];
  const criticalSelectors = [
    '.eyebrow','.simulation-strip','.permission-rail strong','.permission-rail small','.bubble',
    '.card-head h3','.sticky-summary','.badge','.understanding','.correction-help','.label','.value',
    '.notice','.primary','.subline','.final-check-label','.scroll-status','.step strong','.step small',
    '.manual-step strong','.manual-step small','.fake-input','.assurance','.rail-button','.secondary','.text-action'
  ];

  const apply = (platform, flow, width, height, large, dark) => {
    by(`[data-platform="${platform}"]`).click();
    by(`[data-flow="${flow}"]`).click();
    const largeToggle = by('#largeTextToggle');
    if (largeToggle.checked !== large) {
      largeToggle.checked = large;
      largeToggle.dispatchEvent(new Event('change', {bubbles:true}));
    }
    const themeToggle = by('#themeToggle');
    if (themeToggle.checked !== dark) {
      themeToggle.checked = dark;
      themeToggle.dispatchEvent(new Event('change', {bubbles:true}));
    }
    const phone = by('#phone');
    phone.style.width = `${width}px`;
    phone.style.height = `${height}px`;
    window.__WALLET_PROTOTYPE__.resetScrollAndStatus();
    void phone.offsetHeight;
  };

  for (const vp of cfg.viewports) {
    for (const flow of cfg.flows) {
      for (const large of [false, true]) {
        for (const dark of [false, true]) {
          apply(vp.platform, flow, vp.width, vp.height, large, dark);
          const label = `${vp.id}/${flow}/${large?'large':'default'}/${dark?'dark':'light'}`;
          const fail = (message) => errors.push(`${label}: ${message}`);
          const phone = by('#phone'), screen = by('.screen');
          const active = by('.execution-card:not(.hidden),.timeline:not(.hidden)');
          const scroller = by('#reviewScroll');
          const primary = active?.querySelector('.primary');
          const status = by('#scrollStatus');
          const activeContent = active?.querySelector('.card-content');
          if (!phone || !screen || !active || !scroller || !primary || !status) { fail('active structure incomplete'); continue; }
          if (!inside(screen, phone, 11)) fail('screen outside phone');
          for (const e of [...document.querySelectorAll('.app-header,.simulation-strip,.permission-rail,.conversation,.execution-card:not(.hidden),.timeline:not(.hidden),.composer')].filter(visible)) {
            const scrollableSection = e.matches('.execution-card,.timeline');
            const er = rect(e), sr = rect(screen);
            if (scrollableSection) {
              if (er.left < sr.left - 2 || er.right > sr.right + 2) fail(`section outside screen horizontally: ${e.className}`);
            } else if (!inside(e, screen, 2)) {
              fail(`section outside screen: ${e.className}`);
            }
            if (overflowX(e)) fail(`section horizontal overflow: ${e.className}`);
          }
          const source = by('.bubble.user');
          if (!visible(source) || !intersects(source, screen)) fail('source request is hidden');
          if (large && getComputedStyle(source).display === 'none') fail('large text hides source request');
          if (!visible(by('.simulation-strip'))) fail('simulation marker missing');
          if (scroller.clientHeight < 44) fail(`detail viewport too short: ${scroller.clientHeight}`);
          if (Math.abs(scroller.scrollTop) > 1) fail('scroll state leaked');
          if (!scroller.contains(primary)) fail('primary is outside review scroller');
          if (!activeContent?.lastElementChild?.classList.contains('action-footer')) fail('final review block is not last');
          if (!inside(status, screen, 2)) fail('scroll status outside screen');

          const required = vp.platform === 'ios' ? 44 : 48;
          for (const e of [...document.querySelectorAll('#phone button')].filter(visible)) {
            const r = rect(e);
            if (r.height < required - .2) fail(`target below ${required}: ${e.className} ${r.height.toFixed(1)}`);
            if ((e.classList.contains('plus') || e.classList.contains('mic')) && r.width < required - .2) fail(`round target width below ${required}: ${e.className}`);
          }
          if (rect(primary).height < 54 - .2) fail(`primary below 54: ${rect(primary).height.toFixed(1)}`);

          for (const selector of criticalSelectors) {
            for (const e of [...document.querySelectorAll(selector)].filter(visible)) {
              if (overflowX(e)) fail(`critical horizontal clipping ${selector}: ${(e.textContent||'').trim().slice(0,55)}`);
              if (overflowY(e)) fail(`critical vertical clipping ${selector}: ${(e.textContent||'').trim().slice(0,55)}`);
            }
          }
          for (const e of [...document.querySelectorAll('.address')].filter(visible)) if (overflowX(e)) fail('address does not wrap');

          const verifyVisibleControls = (phase) => {
            // getBoundingClientRect() ignores clipping by scroll/overflow ancestors. Only the
            // actually painted intersection is eligible for hit/overlap testing; a fully
            // clipped descendant must never be mistaken for a control hidden by the composer.
            const controls = [...document.querySelectorAll('#phone button')]
              .filter(visible)
              .map((e) => ({e, painted: clippedRect(e, screen)}))
              .filter(({painted}) => painted.width > 1 && painted.height > 1);
            for (const {e, painted} of controls) {
              const x = painted.left + painted.width / 2, y = painted.top + painted.height / 2;
              const hit = document.elementFromPoint(x, y);
              if (!hit || !(hit === e || e.contains(hit))) fail(`${phase} painted control center is obscured: ${e.className}`);
            }
            for (let i = 0; i < controls.length; i++) for (let j = i + 1; j < controls.length; j++) {
              const a = controls[i].painted, b = controls[j].painted;
              if (Math.min(a.right,b.right)-Math.max(a.left,b.left)>1 && Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1) {
                fail(`${phase} overlapping painted controls ${controls[i].e.className}/${controls[j].e.className}`);
              }
            }
          };
          verifyVisibleControls('top');

          const selectedPlatforms = document.querySelectorAll('[data-platform][aria-pressed="true"]');
          const selectedFlows = document.querySelectorAll('[data-flow][aria-pressed="true"]');
          if (selectedPlatforms.length !== 1 || selectedPlatforms[0].dataset.platform !== vp.platform) fail('platform aria-pressed mismatch');
          if (selectedFlows.length !== 1 || selectedFlows[0].dataset.flow !== flow) fail('flow aria-pressed mismatch');

          const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight);
          if (max > 2) scrollCases++;
          if (status.dataset.position !== (max > 2 ? 'top' : 'all')) fail(`initial scroll cue ${status.dataset.position}`);
          if (max > 2) {
            scroller.scrollTop = max / 2;
            window.__WALLET_PROTOTYPE__.updateScrollStatus(scroller);
            if (status.dataset.position !== 'middle') fail(`middle scroll cue ${status.dataset.position}`);
          }
          scroller.scrollTop = max;
          window.__WALLET_PROTOTYPE__.updateScrollStatus(scroller);
          const sr = rect(scroller), pr = rect(primary);
          if (Math.abs(scroller.scrollTop - max) > 2) fail('details bottom unreachable');
          if (pr.top < sr.top - 2 || pr.bottom > sr.bottom + 2) fail('primary not fully visible at bottom');
          if (!primary.disabled) {
            const hit = document.elementFromPoint(pr.left + pr.width/2, pr.top + pr.height/2);
            if (!hit || !(hit === primary || primary.contains(hit))) fail('primary occluded at bottom');
          }
          if (status.dataset.position !== (max > 2 ? 'bottom' : 'all')) fail(`bottom scroll cue ${status.dataset.position}`);
          verifyVisibleControls('bottom');
          scroller.scrollTop = 0;
          window.__WALLET_PROTOTYPE__.updateScrollStatus(scroller);

          for (const selector of contrastSelectors) {
            for (const el of [...document.querySelectorAll(selector)].filter(visible)) {
              if (!(el.textContent || '').trim()) continue;
              const style = getComputedStyle(el), bg = background(el);
              let fg = parse(style.color); if (!fg) continue; fg = blend(fg, bg);
              const actual = ratio(fg, bg), px = parseFloat(style.fontSize), weight = parseInt(style.fontWeight,10) || 400;
              const largeText = px >= 24 || (px >= 18.66 && weight >= 700);
              const minimum = largeText ? 3 : 4.5;
              if (actual + .02 < minimum) fail(`${selector} contrast ${actual.toFixed(2)} < ${minimum}: ${(el.textContent||'').trim().slice(0,45)}`);
            }
          }
        }
      }
    }
  }
  return {errors, scrollCases};
}
"""


async def main(*, check: bool = False) -> None:
    stored_evidence = None
    if check:
        if not EVIDENCE.is_file():
            raise RuntimeError(f"missing stored evidence: {EVIDENCE.relative_to(ROOT)}")
        stored_evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    temporary = tempfile.TemporaryDirectory(prefix="wallet-prototype-check-") if check else None
    output_shots = Path(temporary.name) if temporary is not None else SHOTS
    output_shots.mkdir(parents=True, exist_ok=True)
    # In --check mode, render only into the temporary directory. Never delete or
    # rewrite stored evidence; the package tree must remain byte-for-byte unchanged.
    for stale in output_shots.glob("*.png"):
        stale.unlink()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--force-color-profile=srgb"],
        )
        runtime_toolchain = {
            "playwrightPython": importlib.metadata.version("playwright"),
            "browser": browser.version,
            "browserSource": "playwright-managed",
            "renderProfile": render_profile(),
        }
        evidence_toolchain = runtime_toolchain
        render_profile_matches = True
        if stored_evidence is not None:
            canonical_toolchain = stored_evidence.get("toolchain")
            if not isinstance(canonical_toolchain, dict):
                raise RuntimeError("stored prototype evidence has no toolchain object")
            for key in ("playwrightPython", "browser"):
                if canonical_toolchain.get(key) != runtime_toolchain[key]:
                    raise RuntimeError(
                        f"prototype toolchain mismatch for {key}: "
                        f"stored={canonical_toolchain.get(key)!r} runtime={runtime_toolchain[key]!r}"
                    )
            render_profile_matches = canonical_toolchain.get("renderProfile") == runtime_toolchain["renderProfile"]
            evidence_toolchain = canonical_toolchain
        page = await browser.new_page(viewport={"width": 1360, "height": 1200}, device_scale_factor=1, locale="ja-JP")
        unexpected: list[str] = []
        console_errors: list[str] = []
        page.on("request", lambda req: unexpected.append(req.url))
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        await page.set_content(bundled_html(), wait_until="load")

        banner = await page.locator(".prototype-banner").inner_text()
        assert banner == "画面見本です — 実際の送金・取引・署名・外部通信は行いません"
        static_errors = await page.evaluate(
            """() => {
              const f=window.__WALLET_PROTOTYPE__?.flows, errors=[];
              if(!f)return ['inspection interface missing'];
              const text=JSON.stringify(f);
              if(text.includes('0.05 POL'))errors.push('fixed POL amount remains');
              if(text.includes('損切り2%'))errors.push('invented stop-loss remains');
              if(!f.perp.requiresCorrectionConfirmation || !f.perp.summary.includes('損切りは未設定'))errors.push('perp safety state incomplete');
              const map=Object.fromEntries(f.composite.rows), num=v=>Number(String(v).replace(/[^0-9.]/g,''));
              if(Math.abs(num(map['1．売却後の最低受取'])-num(map['2．HLPの運用口座へ'])-num(map['3．送金前に残る最低額']))>.001)errors.push('composite remaining arithmetic');
              if(Math.abs(num(map['3．送金前に残る最低額'])-num(map['Arbitrumへの送金手数料上限'])-num(map['Arbitrum到着の最低見込み']))>.001)errors.push('composite arrival arithmetic');
              const fee=Object.fromEntries(f.fee.rows);
              for(const key of ['代理支払いの提供者','精算先','失敗時の請求','見積もりID','見積もりの有効期限','失敗した場合'])if(!fee[key])errors.push(`fee disclosure missing ${key}`);
              if(!f.fee.notice.includes('証明できなければ'))errors.push('zero-gas route is not fail-closed');
              if(!f.manual.interpretation.includes('固定の金額を案内せず'))errors.push('manual fallback permits fixed amount');
              if(!f.setup.notice.includes('無期限・無制限')||!f.setup.summary.includes('初期値ではありません'))errors.push('limited-authority example/default warning missing');
              if(!f.spot.user.includes('スポット')||!f.spot.interpretation.includes('現物取引'))errors.push('plain-Japanese normalization missing');
              if(!f.spot.summary.includes('画面例'))errors.push('spot derived quote is not marked as example');
              if(!Object.fromEntries(f.fee.rows)['JPYCで精算する上限'].includes('画面例'))errors.push('fee cap is not marked as example');
              for(const key of ['send','withdraw','bridge','jpyc','composite']){
                const rows=Object.fromEntries(f[key].rows||[]);
                if(!rows['照合用の指紋']?.includes('画面例'))errors.push(`${key} example fingerprint marker missing`);
                const address=rows['送金先アドレス']||rows['受取先アドレス'];
                if(address&&!address.includes('画面例のダミー'))errors.push(`${key} dummy address marker missing`);
              }
              if(!document.documentElement.lang.startsWith('ja'))errors.push('document language missing');
              for(const b of document.querySelectorAll('button'))if(!(b.getAttribute('aria-label')||b.textContent||'').trim())errors.push(`button label missing ${b.className}`);
              return errors;
            }"""
        )
        assert not static_errors, "static/domain: " + " | ".join(static_errors)

        correction = await page.evaluate(
            """() => {
              document.querySelector('[data-flow="perp"]').click();
              const before=document.querySelector('#executeButton').disabled;
              document.querySelector('#confirmInterpretation').click();
              return {before,after:document.querySelector('#executeButton').disabled,live:document.querySelector('#liveStatus').textContent,source:document.querySelector('.bubble.user').textContent};
            }"""
        )
        assert correction["before"] is True and correction["after"] is False
        assert "確認" in correction["live"] and "生産価格" in correction["source"]

        cfg = {
            "viewports": [{"id": n, "platform": p_, "width": w, "height": h} for n, p_, w, h in VIEWPORTS],
            "flows": list(FLOWS),
        }
        matrix = await page.evaluate(MATRIX_JS, cfg)
        assert not matrix["errors"], "\n".join(matrix["errors"][:80])
        geometry_cases = len(VIEWPORTS) * len(FLOWS) * 2 * 2
        print(f"prototype matrix passed: {geometry_cases} cases", flush=True)

        # Focus visibility proxy: every current control is scrolled into view before programmatic focus.
        focus_errors = await page.evaluate(
            """() => {
              document.querySelector('[data-platform="ios"]').click();document.querySelector('[data-flow="setup"]').click();
              const l=document.querySelector('#largeTextToggle');if(!l.checked){l.checked=true;l.dispatchEvent(new Event('change',{bubbles:true}));}
              const t=document.querySelector('#themeToggle');if(!t.checked){t.checked=true;t.dispatchEvent(new Event('change',{bubbles:true}));}
              const phone=document.querySelector('#phone');phone.style.width='390px';phone.style.height='844px';
              const active=document.querySelector('.execution-card:not(.hidden)'),s=document.querySelector('#reviewScroll');
              const screen=document.querySelector('.screen').getBoundingClientRect(),errors=[];
              for(const e of [...document.querySelectorAll('#phone button')].filter(x=>{const st=getComputedStyle(x),r=x.getBoundingClientRect();return !x.disabled&&st.display!=='none'&&st.visibility!=='hidden'&&r.width>.5&&r.height>.5;})){
                if(s.contains(e)){
                  if(e.classList.contains('primary')) s.scrollTop=s.scrollHeight;
                  else {const er=e.getBoundingClientRect(),sr=s.getBoundingClientRect();s.scrollTop+=er.top-sr.top-(sr.height-er.height)/2;}
                  window.__WALLET_PROTOTYPE__.updateScrollStatus(s);void s.offsetHeight;
                }
                e.focus({preventScroll:true});const st=getComputedStyle(e),r=e.getBoundingClientRect();
                if(parseFloat(st.outlineWidth)<2||st.outlineStyle==='none')errors.push(`focus missing ${e.className}`);
                if(r.right<screen.left||r.left>screen.right||r.bottom<screen.top||r.top>screen.bottom)errors.push(`focused offscreen ${e.className}`);
                const hit=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);if(!hit||!(hit===e||e.contains(hit)))errors.push(`focus obscured ${e.className}`);
              }
              return errors;
            }"""
        )
        assert not focus_errors, "focus: " + " | ".join(focus_errors)

        spacing_style = await page.add_style_tag(content="""
          #phone .bubble,#phone .understanding,#phone .row,#phone .notice,#phone .subline,#phone .step div,#phone .manual-step div {
            line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important;
          }
          #phone p { margin-bottom:2em!important; }
        """)
        spacing_errors = await page.evaluate(
            """flows => {
              const errors=[];for(const flow of flows){document.querySelector(`[data-flow="${flow}"]`).click();const a=document.querySelector('.execution-card:not(.hidden),.timeline:not(.hidden)'),s=document.querySelector('#reviewScroll');
                for(const e of a.querySelectorAll('.understanding,.row,.notice,.subline,.step,.manual-step'))if(e.scrollWidth>e.clientWidth+8)errors.push(`${flow} spacing clip ${e.className}`);
                const max=Math.max(0,s.scrollHeight-s.clientHeight);s.scrollTop=max;if(Math.abs(s.scrollTop-max)>2)errors.push(`${flow} spacing bottom unreachable`);
              }return errors;
            }""",
            list(FLOWS),
        )
        assert not spacing_errors, "text spacing: " + " | ".join(spacing_errors)
        await spacing_style.evaluate("e=>e.remove()")

        screenshot_plan = [
            ("ios","perp",390,844,False,False,"iphone-perp-before-confirmation.png",False,False),
            # The bottom-action evidence frame is taller than the device matrix
            # viewport so the screenshot starts on a complete disclosure block.
            # Real 390/375px device behavior remains enforced by the 288-case
            # matrix above; this frame is a review artifact, not device proof.
            ("ios","perp",430,1000,False,False,"iphone-perp-after-confirmation.png",True,True),
            ("android","fee",412,915,False,True,"pixel9a-fee-dark.png",False,False),
            ("ios","withdraw",375,667,True,False,"iphone-large-withdraw.png",False,False),
            ("android","manual",412,915,False,False,"pixel9a-manual.png",False,False),
            ("ios","setup",390,844,False,False,"iphone-limited-authorization.png",False,False),
            ("android","partial",412,932,False,True,"android-tall-partial-dark.png",True,False),
            # The large-text JPYC review frame uses a widened logical viewport so
            # every 15px line and the final CTA remain bounded without shrinking
            # the accessibility stress text. This is prototype evidence only;
            # physical iPhone evidence remains a separate gate.
            ("ios","jpyc",520,1200,True,False,"iphone-jpyc-large.png",True,False),
            ("ios","composite",320,568,False,False,"iphone-se-composite-top.png",False,False),
            # Compact 360/412px behavior remains covered by the 288-case matrix;
            # this taller review frame keeps a complete disclosure block above
            # the bottom action instead of presenting a visually cut paragraph.
            ("android","spot",430,1000,True,True,"android-compact-spot-large-dark.png",True,False),
        ]
        screenshot_states: dict[str, dict[str, object]] = {}
        for platform, flow, width, height, large, dark, filename, bottom, confirm in screenshot_plan:
            state = await page.evaluate(
                """d => {
                  document.querySelector(`[data-platform="${d.platform}"]`).click();
                  document.querySelector(`[data-flow="${d.flow}"]`).click();
                  const l=document.querySelector('#largeTextToggle');
                  if(l.checked!==d.large){l.checked=d.large;l.dispatchEvent(new Event('change',{bubbles:true}));}
                  const t=document.querySelector('#themeToggle');
                  if(t.checked!==d.dark){t.checked=d.dark;t.dispatchEvent(new Event('change',{bubbles:true}));}
                  const p=document.querySelector('#phone');p.style.width=`${d.width}px`;p.style.height=`${d.height}px`;
                  if(d.confirm)document.querySelector('#confirmInterpretation')?.click();
                  const active=document.querySelector('.execution-card:not(.hidden),.timeline:not(.hidden)');
                  const s=document.querySelector('#reviewScroll');
                  const action=active.querySelector('.action-footer');
                  const blocks=[...active.querySelectorAll('.understanding,.correction-check,.row,.notice,.step,.manual-step,.action-footer')];
                  const max=Math.max(0,s.scrollHeight-s.clientHeight);
                  let chosen=0;
                  let partialTopBlocks=0;
                  let actionVisible=false;
                  if(d.bottom){
                    s.scrollTop=max;void s.offsetHeight;
                    const initialRect=s.getBoundingClientRect();
                    const sticky=s.querySelector('.sticky-summary');
                    const inset=sticky?sticky.getBoundingClientRect().height:0;
                    const contentTop=(el)=>el.getBoundingClientRect().top-initialRect.top+s.scrollTop;
                    const actionBottom=contentTop(action)+action.getBoundingClientRect().height;
                    const minimum=Math.max(0,actionBottom-s.clientHeight);
                    const candidates=[...new Set(blocks.map(el=>Math.max(0,contentTop(el)-inset)).filter(v=>v>=minimum-1&&v<=max+1).map(v=>Math.round(v*100)/100))].sort((a,b)=>a-b);
                    if(!candidates.some(v=>Math.abs(v-max)<.5))candidates.push(max);
                    for(const candidate of candidates){
                      s.scrollTop=candidate;window.__WALLET_PROTOTYPE__.updateScrollStatus(s);void s.offsetHeight;
                      const sr=s.getBoundingClientRect(),ar=action.getBoundingClientRect(),safeTop=sr.top+inset;
                      const partial=blocks.filter(el=>{const r=el.getBoundingClientRect();return r.top<safeTop-1&&r.bottom>safeTop+1&&r.bottom>sr.top&&r.top<sr.bottom;}).length;
                      const actionIsVisible=ar.top>=safeTop-2&&ar.bottom<=sr.bottom+2;
                      if(actionIsVisible&&partial===0){chosen=s.scrollTop;partialTopBlocks=partial;actionVisible=true;break;}
                    }
                    if(!actionVisible){
                      s.scrollTop=max;window.__WALLET_PROTOTYPE__.updateScrollStatus(s);void s.offsetHeight;
                      const sr=s.getBoundingClientRect(),ar=action.getBoundingClientRect(),safeTop=sr.top+inset;
                      partialTopBlocks=blocks.filter(el=>{const r=el.getBoundingClientRect();return r.top<safeTop-1&&r.bottom>safeTop+1&&r.bottom>sr.top&&r.top<sr.bottom;}).length;
                      actionVisible=ar.top>=safeTop-2&&ar.bottom<=sr.bottom+2;chosen=s.scrollTop;
                    }
                  }else{
                    s.scrollTop=0;window.__WALLET_PROTOTYPE__.updateScrollStatus(s);void s.offsetHeight;
                    const sr=s.getBoundingClientRect(),ar=action.getBoundingClientRect();
                    actionVisible=ar.top>=sr.top-2&&ar.bottom<=sr.bottom+2;chosen=0;
                  }
                  document.activeElement?.blur();
                  return {captureMode:d.bottom?'BOTTOM_ACTION':'TOP',scrollTop:chosen,maxScroll:max,actionVisible,partialTopBlocks,scrollCue:document.querySelector('#scrollStatus')?.dataset.position||null};
                }""",
                {"platform":platform,"flow":flow,"width":width,"height":height,"large":large,"dark":dark,"bottom":bottom,"confirm":confirm},
            )
            if bottom:
                assert state["actionVisible"] is True, f"evidence screenshot action is not visible: {filename}: {state}"
                assert state["partialTopBlocks"] == 0, f"evidence screenshot cuts a content block at the top: {filename}: {state}"
            screenshot_states[filename] = state
            await page.locator("#phone").screenshot(path=str(output_shots / filename))

        assert not unexpected, f"unexpected network requests: {unexpected}"
        assert not console_errors, f"console errors: {console_errors}"

        evidence_screenshot_states = screenshot_states
        if stored_evidence is not None and not render_profile_matches:
            canonical_states = stored_evidence.get("screenshotReviewStates")
            if not isinstance(canonical_states, dict) or set(canonical_states) != set(screenshot_states):
                raise RuntimeError("stored cross-profile screenshot state set does not match the screenshot plan")
            stable_state_keys = ("captureMode", "actionVisible", "partialTopBlocks", "scrollCue")
            for filename, state in screenshot_states.items():
                canonical_state = canonical_states.get(filename)
                if not isinstance(canonical_state, dict):
                    raise RuntimeError(f"stored screenshot state is invalid: {filename}")
                for key in stable_state_keys:
                    if canonical_state.get(key) != state.get(key):
                        raise RuntimeError(
                            f"cross-profile screenshot state changed: "
                            f"{filename} {key} stored={canonical_state.get(key)!r} runtime={state.get(key)!r}"
                        )
            evidence_screenshot_states = canonical_states

        evidence = {
            "schemaVersion": "2.0",
            "release": METADATA.version,
            "generatedAt": BUILD_TIMESTAMP,
            "result": "PASS",
            "script": "tools/test_prototype.py",
            "localeExecuted": ["ja-JP"],
            "toolchain": evidence_toolchain,
            "testHarness": {
                "path": "tools/test_prototype.py",
                "sha256": hashlib.sha256((ROOT / "tools/test_prototype.py").read_bytes()).hexdigest(),
            },
            "prototypeFiles": {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in ("prototype/index.html","prototype/styles.css","prototype/app.js")},
            "viewports": [{"id":n,"platform":p_.upper(),"width":w,"height":h} for n,p_,w,h in VIEWPORTS],
            "flows": list(FLOWS),
            "textModes": ["DEFAULT","LARGE_TEXT_STRESS"],
            "themes": ["LIGHT","DARK"],
            "geometryAndContrastCases": geometry_cases,
            "overflowingCasesWithReachableReviewEnd": matrix["scrollCases"],
            "screenshots": [f"prototype/screenshots/{x[6]}" for x in screenshot_plan],
            "screenshotReviewStates": evidence_screenshot_states,
            "checks": [
                "persistent_simulation_marker","source_request_preserved_in_large_text","voice_correction_hard_gate",
                "no_network_or_console_error","all_light_dark_flow_viewport_combinations","WCAG_contrast_proxy",
                "44pt_48dp_logical_target_proxy","review_end_and_primary_reachability","scroll_state_cues",
                "control_overlap_and_center_hit_testing","address_wrapping","focus_visibility_proxy","WCAG_text_spacing_proxy",
                "no_fixed_manual_POL_amount","fee_route_disclosure","limited_authority_disclosure",
                "evidence_screenshot_boundary_alignment","invented_value_example_markers"
            ],
            "limitations": [
                "Browser logical-pixel proxy only; native SwiftUI and Jetpack Compose rendering are not proven.",
                "No real-device safe area, VoiceOver, TalkBack, IME, biometric prompt, secure element, GPU, or OS font renderer is proven.",
                "One CSS pixel is not one physical millimetre; real-device screenshot comparison remains mandatory.",
                "Screenshot bytes are compared exactly only on the recorded render profile; cross-profile validation permits at most one device pixel of border-rounding variance and requires the complete browser matrix.",
                "Static values are examples; no live price, balance, fee, contract, JPYC EX, or Hyperliquid lookup occurs."
            ],
        }
        if check:
            for item in screenshot_plan:
                filename = item[6]
                expected_dimensions = (item[2], item[3])
                stored = SHOTS / filename
                generated = output_shots / filename
                if not stored.is_file():
                    raise RuntimeError(f"missing stored screenshot: {stored.relative_to(ROOT)}")
                if render_profile_matches and stored.read_bytes() != generated.read_bytes():
                    raise RuntimeError(f"stale or non-reproducible screenshot: {stored.relative_to(ROOT)}")
                if not render_profile_matches:
                    stored_dimensions = png_dimensions(stored)
                    generated_dimensions = png_dimensions(generated)
                    for dimensions in (stored_dimensions, generated_dimensions):
                        if any(abs(actual - expected) > 1 for actual, expected in zip(dimensions, expected_dimensions)):
                            raise RuntimeError(
                                f"cross-profile screenshot dimensions exceed viewport tolerance: "
                                f"{stored.relative_to(ROOT)} expected={expected_dimensions} actual={dimensions}"
                            )
                    if any(abs(a - b) > 1 for a, b in zip(stored_dimensions, generated_dimensions)):
                        raise RuntimeError(
                            f"cross-profile screenshot dimensions changed by more than one pixel: "
                            f"{stored.relative_to(ROOT)} stored={stored_dimensions} generated={generated_dimensions}"
                        )
            if not render_profile_matches:
                print(
                    "CROSS-PROFILE SCREENSHOT CHECK PASSED "
                    "(stored bytes protected by manifest; generated dimensions and browser matrix verified)",
                    flush=True,
                )
        write_or_check(
            EVIDENCE,
            json_bytes(evidence),
            check=check,
            label="tests/prototype-visual-evidence.json",
        )
        await browser.close()
    if temporary is not None:
        temporary.cleanup()
    print("PROTOTYPE VALIDATION PASSED" + (" (NON-MUTATING CHECK)" if check else " (EVIDENCE PREPARED)"), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare or verify deterministic offline prototype evidence.")
    parser.add_argument("--check", action="store_true", help="render to a temporary directory and compare without modifying the package")
    args = parser.parse_args()
    asyncio.run(main(check=args.check))
