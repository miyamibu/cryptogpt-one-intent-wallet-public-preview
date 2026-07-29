"""A deliberately narrow, non-transactional support gateway."""

from __future__ import annotations

import re
from typing import Any, Mapping

from shared.canonical import ensure_nfc, strict_loads


OPERATION_IDS = frozenset({
    "getReadOnlyStatus",
    "getPlainJapaneseTerm",
    "explainNonTransactionalError",
    "getGenericSafetyHelp",
})

FIXED_TERMS = {
    "execution_capsule": "実行カプセル: 確認済みの内容を固定する内部情報です。",
    "reconciliation": "照合: 外部の結果と記録を比べて状態を確認することです。",
}
FIXED_ERRORS = {
    "stale_state": "情報が古いため、処理を止めています。時間を置いて再確認してください。",
    "manual_resolution": "結果を確認できないため、同じ操作を繰り返さず確認が必要です。",
}
FIXED_SAFETY = {
    "general": "この画面は説明と確認用です。送信や署名は行いません。",
    "self_custody": "秘密情報は誰にも渡さず、内容を確認できない操作は止めてください。",
}

_FORBIDDEN = re.compile(
    r"(transaction|order|payload|signature|signing|quote|approval|deep.?link|qr|handoff|recipient|address|amount|asset|network|calldata|0x[0-9a-f]+|送信|署名|注文|宛先|金額|資産|ネットワーク|承認|見積|QR|リンク)",
    re.IGNORECASE,
)
_ALLOWED_KEYS = {
    "getReadOnlyStatus": {"opaqueReference"},
    "getPlainJapaneseTerm": {"termId"},
    "explainNonTransactionalError": {"errorCode"},
    "getGenericSafetyHelp": {"topicId"},
}


class BoundaryViolation(ValueError):
    pass


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
    if set(request) - {"body", "query", "path", "headers", "metadata", "toolContext"}:
        raise BoundaryViolation("unknown request envelope property")
    if set(request) != {"body"}:
        raise BoundaryViolation("only the body location is accepted; other tool context is rejected")
    for location, value in request.items():
        if not isinstance(value, Mapping):
            raise BoundaryViolation(f"{location} must be an object")
        if set(value) != _ALLOWED_KEYS[operation_id]:
            raise BoundaryViolation("request properties are not exactly allowlisted")
        _scan_untrusted(value, location)


def handle(operation_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
    validate_request(operation_id, request)
    body = request["body"]
    if operation_id == "getReadOnlyStatus":
        if not re.fullmatch(r"status-[A-Za-z0-9_-]{8,64}", body["opaqueReference"]):
            raise BoundaryViolation("opaque status reference is invalid")
        return {"status": "information_unavailable", "reasonCode": "REDACTED_STATUS", "writeAvailableHere": False, "executable": False}
    if operation_id == "getPlainJapaneseTerm":
        if body["termId"] not in FIXED_TERMS:
            raise BoundaryViolation("term is not in fixed catalog")
        return {"text": FIXED_TERMS[body["termId"]], "writeAvailableHere": False, "executable": False}
    if operation_id == "explainNonTransactionalError":
        if body["errorCode"] not in FIXED_ERRORS:
            raise BoundaryViolation("error is not in fixed catalog")
        return {"text": FIXED_ERRORS[body["errorCode"]], "writeAvailableHere": False, "executable": False}
    if body["topicId"] not in FIXED_SAFETY:
        raise BoundaryViolation("safety topic is not in fixed catalog")
    return {"text": FIXED_SAFETY[body["topicId"]], "writeAvailableHere": False, "executable": False}


def handle_json(operation_id: str, raw_request: str) -> dict[str, Any]:
    """Parse the HTTP body with duplicate-key rejection before routing."""

    try:
        request = strict_loads(raw_request)
    except ValueError as exc:
        raise BoundaryViolation("request JSON is not strict canonical JSON") from exc
    if not isinstance(request, Mapping):
        raise BoundaryViolation("request envelope must be an object")
    return handle(operation_id, request)
