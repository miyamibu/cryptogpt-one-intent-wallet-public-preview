"""OpenAPI-aligned, deliberately non-transactional support gateway."""

from __future__ import annotations

import re
import threading
import time
from typing import Any, Mapping

from shared.canonical import ensure_nfc, strict_loads


OPERATION_IDS = frozenset(
    {
        "getReadOnlyStatus",
        "getPlainJapaneseTerm",
        "explainNonTransactionalError",
        "getGenericSafetyHelp",
    }
)

CATALOG_VERSION = "2026-07-31.1"
OPAQUE_ID_PATTERN = r"[A-Za-z0-9_-]{24,128}"
LOCAL_DEMO_CONTEXT = {
    "subjectId": "sub_7f3a9c1e6b4d2a8f0c5e9d1b",
    "tenantId": "ten_4c8e2a1f6d9b3e7c5a0f2d8b",
    "referenceOwnerSubjectId": "sub_7f3a9c1e6b4d2a8f0c5e9d1b",
    "referenceOwnerTenantId": "ten_4c8e2a1f6d9b3e7c5a0f2d8b",
}
NEUTRAL_HANDOFF = "独立したウォレットアプリを開いて、内容を確認してください。"
FIXED_TERMS = {
    "execution-capsule": ("実行カプセル", "確認済みの内容を固定する内部情報です。"),
    "reconciliation": ("照合", "外部の結果と記録を比べて状態を確認することです。"),
}
FIXED_ERRORS = {
    "SUPPORT_UNAVAILABLE": ("サポート情報を表示できません", "時間を置いて再確認してください。"),
    "STATUS_DELAYED": ("状態の更新に時間がかかっています", "同じ操作を繰り返さず、状態を再確認してください。"),
    "STATUS_UNKNOWN": ("状態を確認できません", "結果が確定するまで新しい操作を始めないでください。"),
    "AUTHENTICATION_REQUIRED": ("認証が必要です", "独立したウォレットアプリで認証状態を確認してください。"),
    "REFERENCE_NOT_FOUND": ("参照情報が見つかりません", "参照番号を確認してください。"),
}
FIXED_SAFETY = {
    "CHECK_RECIPIENT_SAFELY": ("宛先の安全な確認", "独立したウォレットアプリで宛先全体を確認してください。"),
    "RECOGNIZE_FAKE_TOKEN": ("偽トークンへの注意", "名称だけで判断せず、独立したウォレットアプリの登録情報を確認してください。"),
    "PROTECT_RECOVERY_SECRET": ("復旧秘密の保護", "復旧秘密は誰にも渡さず、画面共有や入力依頼を拒否してください。"),
    "UNDERSTAND_NETWORK_FEE": ("ネットワーク手数料", "確定前に独立したウォレットアプリで総額を確認してください。"),
    "CONTACT_SUPPORT": ("サポートへの連絡", "秘密情報を添付せず、公式窓口から問い合わせてください。"),
}

_FORBIDDEN = re.compile(
    r"(transaction|order|payload|signature|signing|quote|approval|deep.?link|qr|handoff|"
    r"recipient|address|amount|asset|network|calldata|0x[0-9a-f]+|送信|署名|注文|宛先|"
    r"金額|資産|ネットワーク|承認|見積|QR|リンク)",
    re.IGNORECASE,
)
_EXPECTED_LOCATIONS = {
    "getReadOnlyStatus": {"path"},
    "getPlainJapaneseTerm": {"path"},
    "explainNonTransactionalError": {"body"},
    "getGenericSafetyHelp": {"body"},
}
_ALLOWED_KEYS = {
    "getReadOnlyStatus": {"referenceId"},
    "getPlainJapaneseTerm": {"termId"},
    "explainNonTransactionalError": {"errorCode", "locale", "supportReference"},
    "getGenericSafetyHelp": {"topic", "locale"},
}
_REQUIRED_KEYS = {
    "getReadOnlyStatus": {"referenceId"},
    "getPlainJapaneseTerm": {"termId"},
    "explainNonTransactionalError": {"errorCode", "locale"},
    "getGenericSafetyHelp": {"topic", "locale"},
}
_RESPONSE_KEYS = {
    "getReadOnlyStatus": {"referenceId", "status", "updatedAt", "messageCode", "supportCode", "writeAvailableHere"},
    "getPlainJapaneseTerm": {"termId", "labelJa", "explanationJa"},
    "explainNonTransactionalError": {"catalogEntryId", "catalogVersion", "titleJa", "explanationJa", "neutralHandoffJa", "executable"},
    "getGenericSafetyHelp": {"catalogEntryId", "catalogVersion", "titleJa", "explanationJa", "neutralHandoffJa", "executable"},
}
_CONTEXT_REQUIRED = frozenset({"getReadOnlyStatus", "explainNonTransactionalError", "getGenericSafetyHelp"})
_CONTEXT_KEYS = frozenset({"subjectId", "tenantId", "referenceOwnerSubjectId", "referenceOwnerTenantId"})
_ID_RE = re.compile(OPAQUE_ID_PATTERN)


class FixedWindowRateLimiter:
    """Small in-process limiter for the non-transactional boundary only."""

    def __init__(
        self,
        *,
        limit: int = 60,
        window_seconds: float = 60.0,
        max_subjects: int = 1024,
    ) -> None:
        if limit <= 0 or window_seconds <= 0 or max_subjects <= 0:
            raise ValueError("rate-limit parameters must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_subjects = max_subjects
        self._lock = threading.Lock()
        self._windows: dict[tuple[str, str], list[float]] = {}

    def allow(self, context: Mapping[str, Any], *, now: float | None = None) -> bool:
        key = (str(context["subjectId"]), str(context["tenantId"]))
        current = time.monotonic() if now is None else now
        cutoff = current - self.window_seconds
        with self._lock:
            active_windows = {
                subject_key: [value for value in timestamps if value > cutoff]
                for subject_key, timestamps in self._windows.items()
            }
            active_windows = {
                subject_key: timestamps
                for subject_key, timestamps in active_windows.items()
                if timestamps
            }
            if key not in active_windows and len(active_windows) >= self.max_subjects:
                oldest_key = min(active_windows, key=lambda subject_key: active_windows[subject_key][-1])
                del active_windows[oldest_key]
            timestamps = active_windows.get(key, [])
            if len(timestamps) >= self.limit:
                active_windows[key] = timestamps
                self._windows = active_windows
                return False
            timestamps.append(current)
            active_windows[key] = timestamps
            self._windows = active_windows
            return True


_RATE_LIMITER = FixedWindowRateLimiter()


class BoundaryViolation(ValueError):
    pass


def _validate_trusted_context(operation_id: str, trusted_context: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if operation_id not in _CONTEXT_REQUIRED:
        if trusted_context is not None:
            if not isinstance(trusted_context, Mapping):
                raise BoundaryViolation("trusted context must be an object")
            if set(trusted_context) != _CONTEXT_KEYS:
                raise BoundaryViolation("trusted context properties do not match the contract")
        return trusted_context
    if not isinstance(trusted_context, Mapping) or set(trusted_context) != _CONTEXT_KEYS:
        raise BoundaryViolation("authenticated subject and tenant context are required")
    for key in _CONTEXT_KEYS:
        value = trusted_context[key]
        if not isinstance(value, str) or not _ID_RE.fullmatch(value):
            raise BoundaryViolation("subject and tenant identifiers must be high-entropy opaque IDs")
    if trusted_context["subjectId"] != trusted_context["referenceOwnerSubjectId"]:
        raise BoundaryViolation("reference does not belong to the authenticated subject")
    if trusted_context["tenantId"] != trusted_context["referenceOwnerTenantId"]:
        raise BoundaryViolation("reference does not belong to the authenticated tenant")
    if not _RATE_LIMITER.allow(trusted_context):
        raise BoundaryViolation("read-only support rate limit exceeded")
    return trusted_context


def _allowlisted_response(operation_id: str, response: dict[str, Any]) -> dict[str, Any]:
    if set(response) != _RESPONSE_KEYS[operation_id]:
        raise BoundaryViolation("response properties do not match the read-only contract")
    return response


def _scan_untrusted(value: Any, path: str = "root") -> None:
    if isinstance(value, str):
        if _FORBIDDEN.search(value):
            raise BoundaryViolation(f"transaction context rejected at {path}")
        ensure_nfc(value)
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str) or key.startswith("_"):
                raise BoundaryViolation(f"invalid property at {path}")
            _scan_untrusted(key, f"{path}.{key}")
            _scan_untrusted(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _scan_untrusted(item, f"{path}[{index}]")
    elif value is not None and not isinstance(value, (bool, int)):
        raise BoundaryViolation(f"unsupported value at {path}")


def validate_request(operation_id: str, request: Mapping[str, Any]) -> None:
    if operation_id not in OPERATION_IDS:
        raise BoundaryViolation("operation is not allowlisted")
    if set(request) != _EXPECTED_LOCATIONS[operation_id]:
        raise BoundaryViolation("request locations do not match the OpenAPI operation")
    location = next(iter(_EXPECTED_LOCATIONS[operation_id]))
    value = request[location]
    if not isinstance(value, Mapping):
        raise BoundaryViolation(f"{location} must be an object")
    keys = set(value)
    if not _REQUIRED_KEYS[operation_id].issubset(keys) or not keys.issubset(_ALLOWED_KEYS[operation_id]):
        raise BoundaryViolation("request properties do not match the OpenAPI schema")
    # All accepted values are validated against fixed catalogs or opaque-ID
    # patterns in ``handle``.  Free text is never accepted by this contract.


def _explanation(entry_id: str, title: str, explanation: str) -> dict[str, Any]:
    return {
        "catalogEntryId": entry_id,
        "catalogVersion": CATALOG_VERSION,
        "titleJa": title,
        "explanationJa": explanation,
        "neutralHandoffJa": NEUTRAL_HANDOFF,
        "executable": False,
    }


def handle(
    operation_id: str,
    request: Mapping[str, Any],
    *,
    trusted_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    validate_request(operation_id, request)
    _validate_trusted_context(operation_id, trusted_context)
    if operation_id == "getReadOnlyStatus":
        reference = request["path"]["referenceId"]
        if not isinstance(reference, str) or not re.fullmatch(OPAQUE_ID_PATTERN, reference):
            raise BoundaryViolation("opaque status reference is invalid")
        return _allowlisted_response(operation_id, {
            "referenceId": reference,
            "status": "INFORMATION_ONLY",
            "updatedAt": "1970-01-01T00:00:00Z",
            "messageCode": "STATUS_INFORMATION_ONLY",
            "supportCode": None,
            "writeAvailableHere": False,
        })
    if operation_id == "getPlainJapaneseTerm":
        term_id = request["path"]["termId"]
        if term_id not in FIXED_TERMS:
            raise BoundaryViolation("term is not in the fixed catalog")
        label, explanation = FIXED_TERMS[term_id]
        return _allowlisted_response(operation_id, {"termId": term_id, "labelJa": label, "explanationJa": explanation})
    body = request["body"]
    if body.get("locale") != "ja-JP":
        raise BoundaryViolation("only the contract locale is accepted")
    if operation_id == "explainNonTransactionalError":
        error_code = body["errorCode"]
        if error_code not in FIXED_ERRORS:
            raise BoundaryViolation("error is not in the fixed catalog")
        reference = body.get("supportReference")
        if reference is not None and (not isinstance(reference, str) or not re.fullmatch(OPAQUE_ID_PATTERN, reference)):
            raise BoundaryViolation("support reference is invalid")
        title, explanation = FIXED_ERRORS[error_code]
        return _allowlisted_response(operation_id, _explanation(error_code, title, explanation))
    topic = body["topic"]
    if topic not in FIXED_SAFETY:
        raise BoundaryViolation("safety topic is not in the fixed catalog")
    title, explanation = FIXED_SAFETY[topic]
    return _allowlisted_response(operation_id, _explanation(topic, title, explanation))


def handle_json(
    operation_id: str,
    raw_request: str,
    *,
    trusted_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse the request with duplicate-key rejection before routing."""

    try:
        request = strict_loads(raw_request)
    except ValueError as exc:
        raise BoundaryViolation("request JSON is not strict canonical JSON") from exc
    if not isinstance(request, Mapping):
        raise BoundaryViolation("request envelope must be an object")
    return handle(operation_id, request, trusted_context=trusted_context)
