"""Logical acceptance matrix for the offline browser prototype."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path


@dataclass(frozen=True)
class BrowserCase:
    viewport: str
    flow: str
    text_mode: str
    theme: str


VIEWPORTS = ("compact", "baseline", "wide", "pixel9a", "iphone12", "current-face-id")
FLOWS = (
    "draft-review", "ambiguous-voice", "manual-fallback", "fee-readiness",
    "jpyc-handoff", "reconciliation", "stop-control", "read-only-status",
    "registry-stale", "quote-expired", "hyperliquid-review", "partial-success",
)
TEXT_MODES = ("default", "largest")
THEMES = ("light", "dark")


def cases() -> list[BrowserCase]:
    return [BrowserCase(*values) for values in product(VIEWPORTS, FLOWS, TEXT_MODES, THEMES)]


def validate_prototype() -> None:
    prototype = Path(__file__).parents[1] / "apps" / "browser-prototype" / "index.html"
    source = prototype.read_text(encoding="utf-8")
    required = (
        "sourceUtterance", "normalizedInterpretation", "primaryAction", "disabled",
        "stopAction", "ストップロス: 設定なし", "画面例・ライブ送信ではありません",
    )
    missing = [item for item in required if item not in source]
    if missing:
        raise AssertionError(f"browser safety semantics missing: {missing}")
    forbidden = ("/execute", "/authorize", "deepLink", "signature", "payload")
    present = [item for item in forbidden if item in source]
    if present:
        raise AssertionError(f"browser prototype exposes prohibited capability markers: {present}")
    if len(cases()) != 288:
        raise AssertionError("browser matrix must contain exactly 288 logical cases")


if __name__ == "__main__":
    validate_prototype()
    print("BROWSER_MATRIX_PASS 288")
