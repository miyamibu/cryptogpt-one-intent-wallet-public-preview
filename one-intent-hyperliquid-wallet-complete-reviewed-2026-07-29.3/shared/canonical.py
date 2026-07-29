"""Strict canonical JSON and decimal primitives.

The reference implementation intentionally rejects inputs which common mobile,
server, and JavaScript JSON implementations can interpret differently.  The
limits in this module are part of the defensive contract: canonicalization must
also fail closed on excessive depth, size, precision, and cyclic structures.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any


MAX_SAFE_INTEGER = 9_007_199_254_740_991
MAX_DECIMAL_TEXT_LENGTH = 128
MAX_DECIMAL_FRACTION_DIGITS = 38
MAX_JSON_TEXT_BYTES = 1 * 1024 * 1024
MAX_CANONICAL_BYTES = 1 * 1024 * 1024
MAX_CONTAINER_DEPTH = 128
MAX_VALUE_NODES = 100_000
MAX_STRING_LENGTH = 256 * 1024
MAX_HASH_DOMAIN_LENGTH = 128
_DECIMAL_RE = re.compile(r"^(0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_CONFUSABLE_SCRIPT_NAMES = ("CYRILLIC", "GREEK")


class CanonicalizationError(ValueError):
    """Input cannot be represented by the shared canonical contract."""


class DuplicateKeyError(CanonicalizationError):
    pass


class NonNFCError(CanonicalizationError):
    pass


class UnsafeNumberError(CanonicalizationError):
    pass


class ResourceLimitError(CanonicalizationError):
    pass


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate key: {key}")
        result[key] = value
    return result


def _parse_int(raw: str) -> int:
    if raw == "-0":
        raise UnsafeNumberError("negative zero is not allowed")
    value = int(raw)
    if abs(value) > MAX_SAFE_INTEGER:
        raise UnsafeNumberError("integer exceeds cross-language safe range")
    return value


def _reject_float(raw: str) -> Any:
    raise UnsafeNumberError("binary floating point and exponent notation are not allowed")


def _reject_constant(raw: str) -> Any:
    raise UnsafeNumberError(f"non-finite JSON constant is not allowed: {raw}")


def strict_loads(text: str) -> Any:
    if not isinstance(text, str):
        raise TypeError("strict_loads expects text")
    try:
        encoded_length = len(text.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise CanonicalizationError("text contains an invalid Unicode scalar") from exc
    if encoded_length > MAX_JSON_TEXT_BYTES:
        raise ResourceLimitError("JSON text exceeds the canonical size limit")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_pairs,
            parse_int=_parse_int,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise CanonicalizationError(str(exc)) from exc
    except RecursionError as exc:
        raise ResourceLimitError("JSON nesting exceeds the canonical depth limit") from exc
    return ensure_nfc(value)


def _validate_string(value: str) -> str:
    if len(value) > MAX_STRING_LENGTH:
        raise ResourceLimitError("string exceeds the canonical length limit")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise CanonicalizationError("string contains an invalid Unicode scalar") from exc
    if unicodedata.normalize("NFC", value) != value:
        raise NonNFCError("string is not NFC normalized")
    return value


def ensure_nfc(value: Any) -> Any:
    """Validate canonical JSON-compatible values without rewriting user data.

    Tuples are accepted as immutable array inputs.  Non-string mapping keys,
    cycles, excessive nesting, floats, and implementation-specific objects are
    rejected before JSON serialization.
    """

    node_count = 0
    active_containers: set[int] = set()

    def visit(item: Any, depth: int) -> Any:
        nonlocal node_count
        node_count += 1
        if node_count > MAX_VALUE_NODES:
            raise ResourceLimitError("value exceeds the canonical node limit")
        if depth > MAX_CONTAINER_DEPTH:
            raise ResourceLimitError("value exceeds the canonical depth limit")

        if isinstance(item, str):
            return _validate_string(item)
        if item is None or isinstance(item, bool):
            return item
        if isinstance(item, int):
            if abs(item) > MAX_SAFE_INTEGER:
                raise UnsafeNumberError("integer exceeds cross-language safe range")
            return item
        if isinstance(item, float):
            raise UnsafeNumberError("float values are not allowed")
        if isinstance(item, (list, tuple, dict)):
            marker = id(item)
            if marker in active_containers:
                raise CanonicalizationError("cyclic values are not allowed")
            active_containers.add(marker)
            try:
                if isinstance(item, list):
                    return [visit(child, depth + 1) for child in item]
                if isinstance(item, tuple):
                    return tuple(visit(child, depth + 1) for child in item)
                for key, child in item.items():
                    if not isinstance(key, str):
                        raise CanonicalizationError("JSON object keys must be strings")
                    visit(key, depth + 1)
                    visit(child, depth + 1)
                return item
            finally:
                active_containers.remove(marker)
        raise CanonicalizationError(f"unsupported value type: {type(item).__name__}")

    try:
        return visit(value, 0)
    except RecursionError as exc:
        raise ResourceLimitError("value exceeds the canonical depth limit") from exc


def canonical_bytes(value: Any) -> bytes:
    ensure_nfc(value)
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise CanonicalizationError(str(exc)) from exc
    if len(encoded) > MAX_CANONICAL_BYTES:
        raise ResourceLimitError("canonical JSON exceeds the size limit")
    return encoded


def canonical_hash(domain: str, value: Any) -> str:
    if not isinstance(domain, str):
        raise CanonicalizationError("hash domain must be text")
    _validate_string(domain)
    if not domain or len(domain) > MAX_HASH_DOMAIN_LENGTH or "\x00" in domain:
        raise CanonicalizationError("invalid hash domain")
    data = domain.encode("utf-8") + b"\x00" + canonical_bytes(value)
    return hashlib.sha256(data).hexdigest()


def decimal_string(raw: str, *, scale: int | None = None) -> Decimal:
    """Parse a non-exponent decimal string and optionally enforce scale."""

    if not isinstance(raw, str) or not _DECIMAL_RE.fullmatch(raw):
        raise CanonicalizationError("amount must be a non-negative decimal string")
    if len(raw) > MAX_DECIMAL_TEXT_LENGTH:
        raise CanonicalizationError("decimal string is too long")
    if scale is not None and (not isinstance(scale, int) or isinstance(scale, bool) or not 0 <= scale <= MAX_DECIMAL_FRACTION_DIGITS):
        raise CanonicalizationError("decimal scale limit is invalid")
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise CanonicalizationError("invalid decimal amount") from exc
    fractional = len(raw.partition(".")[2]) if "." in raw else 0
    if fractional > MAX_DECIMAL_FRACTION_DIGITS:
        raise CanonicalizationError("decimal fractional precision exceeds the shared limit")
    if scale is not None and fractional > scale:
        raise CanonicalizationError("decimal scale mismatch")
    return value


def address_fingerprint(address: str) -> str:
    if not isinstance(address, str) or not address or len(address) > 512 or address != address.strip():
        raise CanonicalizationError("address is required and must be bounded text")
    _validate_string(address)
    if any(ord(char) < 32 or ord(char) == 127 for char in address):
        raise CanonicalizationError("address contains a control character")
    return canonical_hash("address-fingerprint-v1", {"address": address})[:12].upper()


def validate_alias(alias: str) -> str:
    """Reject mixed-script aliases that can visually replace a trusted name."""

    if not isinstance(alias, str) or not 1 <= len(alias) <= 128 or alias != alias.strip():
        raise CanonicalizationError("alias must be bounded non-empty text")
    _validate_string(alias)
    if any(ord(char) < 32 or ord(char) == 127 for char in alias):
        raise CanonicalizationError("alias contains a control character")
    has_ascii = any("a" <= char.lower() <= "z" for char in alias)
    has_confusable_script = any(
        any(script_name in unicodedata.name(char, "") for script_name in _CONFUSABLE_SCRIPT_NAMES)
        for char in alias
    )
    if has_ascii and has_confusable_script:
        raise CanonicalizationError("mixed-script confusable alias is not allowed")
    return alias
