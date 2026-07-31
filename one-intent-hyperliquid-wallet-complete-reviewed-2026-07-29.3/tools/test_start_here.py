#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from playwright.async_api import async_playwright

from artifact_io import json_bytes, write_or_check
from canonical_hashes import strict_load_json
from package_metadata import ROOT, load_package_metadata

METADATA = load_package_metadata()
SOURCE = ROOT / "START_HERE.html"
EVIDENCE = ROOT / "tests/start-here-layout-evidence.json"
BUILD_TIMESTAMP = METADATA.deterministic_build_timestamp
VIEWPORTS = (
    ("mobile-narrow", 320, 800),
    ("mobile-standard", 390, 844),
    ("desktop", 1440, 1000),
)
THEMES = ("light", "dark")
REGRESSION_COUNT = len(strict_load_json(ROOT / "tests/loophole-regression-cases.json").get("cases", []))


def test_html() -> str:
    html = SOURCE.read_text(encoding="utf-8")
    css = (ROOT / "START_HERE.css").read_text(encoding="utf-8")
    regression_metric = f'<div class="metric">{REGRESSION_COUNT}</div>'
    if regression_metric not in html:
        raise RuntimeError(f"START_HERE regression metric is stale; expected {REGRESSION_COUNT}")
    exact = '<a class="button primary" href="prototype/index.html">'
    if exact not in html:
        raise RuntimeError("START_HERE prototype link marker changed; update the deterministic test fixture")
    return html.replace('<link rel="stylesheet" href="START_HERE.css" />', f"<style>{css}</style>")


LAYOUT_CHECK = r"""
() => {
  const errors = [];
  const visible = (el) => {
    if (!el) return false;
    const s = getComputedStyle(el), r = el.getBoundingClientRect();
    return s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity) !== 0 && r.width > .5 && r.height > .5;
  };
  const parse = (value) => {
    const m = String(value).match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number);
    return {r:p[0], g:p[1], b:p[2], a:p.length > 3 ? p[3] : 1};
  };
  const blend = (fg,bg) => ({r:fg.r*fg.a+bg.r*(1-fg.a),g:fg.g*fg.a+bg.g*(1-fg.a),b:fg.b*fg.a+bg.b*(1-fg.a),a:1});
  const background = (el) => {
    const chain=[];let n=el;while(n&&n.nodeType===1){chain.push(n);n=n.parentElement;}
    let out={r:255,g:255,b:255,a:1};
    for(const item of chain.reverse()){const c=parse(getComputedStyle(item).backgroundColor);if(c&&c.a>0)out=blend(c,out);}
    return out;
  };
  const linear = (x) => {x/=255;return x<=.04045?x/12.92:Math.pow((x+.055)/1.055,2.4);};
  const lum = (c) => .2126*linear(c.r)+.7152*linear(c.g)+.0722*linear(c.b);
  const contrast = (a,b) => (Math.max(lum(a),lum(b))+.05)/(Math.min(lum(a),lum(b))+.05);
  const body = document.body;
  if (!document.documentElement.lang.startsWith('ja')) errors.push('document language is not Japanese');
  if (document.documentElement.scrollWidth > innerWidth + 2 || body.scrollWidth > innerWidth + 2) errors.push(`page horizontal overflow ${document.documentElement.scrollWidth}/${innerWidth}`);
  const text = body.innerText;
  for (const phrase of ['288','10','NO-GO','実際の送金・取引・署名・外部通信は行いません','codex/CODEX_REMAINING_WORK_MASTER_PROMPT.md']) {
    if (!text.includes(phrase)) errors.push(`required entry-page text missing: ${phrase}`);
  }
  const top = document.querySelector('.top');
  if (!visible(top) || top.getBoundingClientRect().top > 1) errors.push('persistent simulation banner missing');
  for (const el of [...document.querySelectorAll('.card')].filter(visible)) {
    const r=el.getBoundingClientRect();
    if(r.left < -2 || r.right > innerWidth + 2) errors.push(`card escapes viewport: ${el.className}`);
  }
  const prototypeLink=document.querySelector('a[href="prototype/index.html"]');
  if(!visible(prototypeLink)) errors.push('top-level prototype link missing');
  const controls=[...document.querySelectorAll('a.button')].filter(visible);
  document.documentElement.style.scrollBehavior='auto';
  for(const el of controls){
    const r=el.getBoundingClientRect();
    if(r.height<44)errors.push(`entry action below 44px: ${(el.textContent||'').trim()}`);
    const max=Math.max(0,document.documentElement.scrollHeight-innerHeight);
    const target=Math.min(max,Math.max(0,el.offsetTop-innerHeight/2));window.scrollTo(0,target);void el.offsetHeight;
    el.focus({preventScroll:true});const s=getComputedStyle(el),rr=el.getBoundingClientRect();
    if(parseFloat(s.outlineWidth)<2||s.outlineStyle==='none')errors.push(`focus indicator missing: ${(el.textContent||'').trim()}`);
    const x=rr.left+rr.width/2,y=rr.top+rr.height/2,hit=document.elementFromPoint(x,y);
    if(!hit||!(hit===el||el.contains(hit)))errors.push(`entry action center obscured: ${(el.textContent||'').trim()}`);
  }
  window.scrollTo(0,0);document.activeElement?.blur();
  for(const selector of ['.lead','.button.primary','.boundary','.status strong','.small']){
    for(const el of [...document.querySelectorAll(selector)].filter(visible)){
      if(!(el.textContent||'').trim())continue;const s=getComputedStyle(el),bg=background(el);let fg=parse(s.color);if(!fg)continue;fg=blend(fg,bg);
      const px=parseFloat(s.fontSize),weight=parseInt(s.fontWeight,10)||400,large=px>=24||(px>=18.66&&weight>=700),minimum=large?3:4.5,actual=contrast(fg,bg);
      if(actual+.02<minimum)errors.push(`${selector} contrast ${actual.toFixed(2)} < ${minimum}`);
    }
  }
  const tableWrap=document.querySelector('.table-wrap');
  if(!tableWrap)errors.push('reading-order table wrapper missing');
  else if(innerWidth<=520&&tableWrap.scrollWidth<=tableWrap.clientWidth)errors.push('reading-order table no longer has a contained narrow-screen fallback');
  return errors;
}
"""


async def main(*, check: bool = False) -> None:
    html = test_html()
    results: list[dict[str, object]] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--force-color-profile=srgb"],
        )
        browser_version = browser.version
        for name, width, height in VIEWPORTS:
            for theme in THEMES:
                context = await browser.new_context(
                    viewport={"width": width, "height": height},
                    color_scheme=theme,
                    locale="ja-JP",
                    device_scale_factor=1,
                )
                page = await context.new_page()
                unexpected: list[str] = []
                console_errors: list[str] = []
                page.on("request", lambda req: unexpected.append(req.url) if not req.url.startswith("about:") else None)
                page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
                await page.set_content(html, wait_until="load")
                errors = await page.evaluate(LAYOUT_CHECK)
                errors.extend(f"unexpected request: {url}" for url in unexpected)
                errors.extend(f"console error: {msg}" for msg in console_errors)
                if errors:
                    raise AssertionError(f"{name}/{theme}: " + " | ".join(errors))
                results.append({"viewport": name, "width": width, "height": height, "theme": theme.upper(), "result": "PASS"})
                await context.close()
        evidence = {
            "schemaVersion": "1.0",
            "release": METADATA.version,
            "generatedAt": BUILD_TIMESTAMP,
            "result": "PASS",
            "localeExecuted": ["ja-JP"],
            "source": {"path": "START_HERE.html", "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest()},
            "testHarness": {"path": "tools/test_start_here.py", "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
            "toolchain": {
                "playwrightPython": importlib.metadata.version("playwright"),
                "browser": browser_version,
                "browserSource": "playwright-managed",
            },
            "cases": results,
            "checks": [
                "entry_page_no_horizontal_overflow",
                "persistent_simulation_boundary",
                "44px_entry_actions",
                "focus_and_center_hit_testing",
                "light_dark_contrast_proxy",
                "contained_table_overflow",
                "top_level_prototype_link",
                "no_external_requests_or_console_errors",
            ],
            "limitations": [
                "Browser logical-pixel proxy only; browser and OS font/rendering differences remain.",
                "The prototype is opened as a top-level page; the entry page deliberately does not embed it in an iframe.",
            ],
        }
        write_or_check(
            EVIDENCE,
            json_bytes(evidence),
            check=check,
            label="tests/start-here-layout-evidence.json",
        )
        await browser.close()
    print("START_HERE LAYOUT VALIDATION PASSED" + (" (NON-MUTATING CHECK)" if check else " (EVIDENCE PREPARED)"))
    print(f"Cases: {len(results)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare or verify START_HERE browser evidence.")
    parser.add_argument("--check", action="store_true", help="compare evidence and do not modify the package")
    args = parser.parse_args()
    asyncio.run(main(check=args.check))
