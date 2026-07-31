#!/usr/bin/env python3
"""Actual HTTP E2E for the loopback-only preview in three browser engines."""
from __future__ import annotations

import asyncio
import http.client
import sys
import threading
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from playwright.async_api import async_playwright

from services.local_sandbox.server import create_server


def _request(port: int, path: str, *, host: str | None = None) -> tuple[int, dict[str, str], bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request("GET", path, headers={"Host": host or f"127.0.0.1:{port}"})
    response = connection.getresponse()
    result = response.status, {key.lower(): value for key, value in response.getheaders()}, response.read()
    connection.close()
    return result


async def _browser_matrix(base_url: str) -> None:
    async with async_playwright() as playwright:
        for name in ("chromium", "firefox", "webkit"):
            browser = await getattr(playwright, name).launch(headless=True)
            context = await browser.new_context(locale="ja-JP")
            page = await context.new_page()
            console_errors: list[str] = []
            page_errors: list[str] = []
            failed_requests: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on("requestfailed", lambda request: failed_requests.append(request.url))

            response = await page.goto(base_url + "/", wait_until="networkidle")
            assert response is not None and response.status == 200, f"{name}: entry response"
            assert await page.locator("iframe").count() == 0, f"{name}: iframe must not exist"
            assert await page.locator('a[href="prototype/index.html"]').count() >= 1, f"{name}: prototype link"
            for path in (
                "/docs/final-delivery-index",
                "/docs/fee-route-and-asset-registry",
                "/FINAL_DELIVERY_INDEX.md",
                "/47_FEE_ROUTE_AND_ASSET_REGISTRY_SPEC.md",
            ):
                linked = await page.request.get(base_url + path)
                assert linked.status == 200, f"{name}: {path} returned {linked.status}"

            await page.locator('a[href="prototype/index.html"]').first.click()
            await page.wait_for_load_state("networkidle")
            assert page.url.endswith("/prototype/index.html"), f"{name}: prototype not top-level"
            flow_buttons = page.locator("[data-flow]")
            assert await flow_buttons.count() == 12, f"{name}: expected 12 flows"
            for index in range(12):
                button = flow_buttons.nth(index)
                await button.click()
                assert await button.get_attribute("aria-pressed") == "true", f"{name}: flow {index}"

            assert not console_errors, f"{name}: console errors: {console_errors}"
            assert not page_errors, f"{name}: page errors: {page_errors}"
            assert not failed_requests, f"{name}: failed requests: {failed_requests}"
            await context.close()
            await browser.close()


def main() -> int:
    server = create_server("127.0.0.1", 0, root=ROOT)
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    try:
        paths = (
            "/", "/START_HERE.html", "/START_HERE.css", "/prototype/index.html", "/prototype/app.js", "/prototype/styles.css",
            "/docs/final-delivery-index", "/docs/fee-route-and-asset-registry",
            "/FINAL_DELIVERY_INDEX.md", "/47_FEE_ROUTE_AND_ASSET_REGISTRY_SPEC.md",
        )
        for path in paths:
            status, headers, body = _request(port, path)
            assert status == 200 and body, f"{path}: expected 200"
            assert headers.get("x-content-type-options") == "nosniff", f"{path}: security headers"
            assert "frame-ancestors 'none'" in headers.get("content-security-policy", ""), f"{path}: CSP"
        assert _request(port, "/missing")[0] == 404
        assert _request(port, "/%2e%2e/PROJECT_STATUS.yaml")[0] != 200
        assert _request(port, "/", host="example.com")[0] == 421
        asyncio.run(_browser_matrix(f"http://127.0.0.1:{port}"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    print("LOCAL PREVIEW ACTUAL HTTP E2E PASSED (chromium, firefox, webkit)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
