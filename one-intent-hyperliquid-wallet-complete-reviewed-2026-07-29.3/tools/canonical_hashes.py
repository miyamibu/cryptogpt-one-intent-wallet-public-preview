#!/usr/bin/env python3
"""Deterministic canonical hashing for package examples.

This is a deliberately small RFC 8785-compatible subset for project-owned data:
- object keys must be ASCII and are lexicographically sorted;
- strings must already be NFC;
- JSON floats are rejected; financial values are decimal strings;
- duplicate keys are rejected by strict_load_json.

Production implementations must either use a reviewed RFC 8785 implementation or
prove byte-for-byte compatibility with the vectors generated here.
"""
from __future__ import annotations

import copy
import hashlib
import sys
import unicodedata
from pathlib import Path
from typing import Any

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))
from shared.canonical import canonical_bytes as _shared_canonical_bytes
from shared.canonical import canonical_hash as _shared_canonical_hash
from shared.canonical import strict_loads as _shared_strict_loads

SEMANTIC_DOMAIN = "ONE_INTENT_EXECUTION_CAPSULE_V1"
RENDER_DOMAIN = "ONE_INTENT_RENDER_RECEIPT_V1"
STATE_DOMAIN = "ONE_INTENT_STATE_EVIDENCE_V1"
PROMPT_DOMAIN = "ONE_INTENT_TRUSTED_PROMPT_V1"
SOURCE_TEXT_DOMAIN = "ONE_INTENT_SOURCE_TEXT_V1"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class CanonicalizationError(ValueError):
    pass


def strict_load_json_text(text: str) -> Any:
    try:
        return _shared_strict_loads(text)
    except Exception as exc:
        raise CanonicalizationError(str(exc)) from exc


def strict_load_json_bytes(data: bytes) -> Any:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CanonicalizationError("JSON is not valid UTF-8") from exc
    return strict_load_json_text(text)


def strict_load_json(path: Path) -> Any:
    return strict_load_json_text(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> bytes:
    try:
        return _shared_canonical_bytes(value)
    except Exception as exc:
        raise CanonicalizationError(str(exc)) from exc


def domain_hash(domain: str, value: Any) -> str:
    try:
        return "0x" + _shared_canonical_hash(domain, value)
    except Exception as exc:
        raise CanonicalizationError(str(exc)) from exc


def prompt_hash(prompt_text: str | None) -> str | None:
    if prompt_text is None:
        return None
    if unicodedata.normalize("NFC", prompt_text) != prompt_text:
        raise CanonicalizationError("promptText is not NFC-normalized")
    payload = PROMPT_DOMAIN.encode("utf-8") + b"\x00" + prompt_text.encode("utf-8")
    return "0x" + hashlib.sha256(payload).hexdigest()




def source_text_hash(source_text: str) -> str:
    if unicodedata.normalize("NFC", source_text) != source_text:
        raise CanonicalizationError("source text is not NFC-normalized")
    payload = SOURCE_TEXT_DOMAIN.encode("utf-8") + b"\x00" + source_text.encode("utf-8")
    return "0x" + hashlib.sha256(payload).hexdigest()


def semantic_projection(capsule: dict[str, Any]) -> dict[str, Any]:
    """Return the semantic core, excluding presentation/self-derived fields.

    Authorization binds the resulting semanticHash together with renderReceiptHash,
    sourceStateHash, promptTextHash and a fresh challenge. Therefore these derived
    fields are intentionally excluded from the semantic core to avoid circularity.
    """
    out = copy.deepcopy(capsule)
    for key in ("semanticHash", "renderReceiptHash", "sourceStateHash", "renderReceipt"):
        out.pop(key, None)
    presentation = out.get("authorizationPresentation")
    if isinstance(presentation, dict):
        presentation.pop("promptText", None)
        presentation.pop("promptTextHash", None)
    return out


def expected_hashes(capsule: dict[str, Any]) -> dict[str, str | None]:
    if capsule.get("hashProfile") != "ONE_INTENT_HASH_PROFILE_V1":
        raise CanonicalizationError("unsupported or missing hashProfile")
    state_evidence = capsule.get("stateEvidence")
    render_receipt = capsule.get("renderReceipt")
    presentation = capsule.get("authorizationPresentation", {})
    if not isinstance(state_evidence, dict) or not isinstance(render_receipt, dict):
        raise CanonicalizationError("stateEvidence and renderReceipt are required")
    return {
        "sourceStateHash": domain_hash(STATE_DOMAIN, state_evidence),
        "renderReceiptHash": domain_hash(RENDER_DOMAIN, render_receipt),
        "semanticHash": domain_hash(SEMANTIC_DOMAIN, semantic_projection(capsule)),
        "promptTextHash": prompt_hash(presentation.get("promptText")),
    }
