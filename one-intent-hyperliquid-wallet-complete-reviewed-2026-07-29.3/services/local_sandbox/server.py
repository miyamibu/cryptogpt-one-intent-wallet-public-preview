"""Loopback-only operational sandbox for the reviewed offline package.

The sandbox intentionally has no signer, broadcaster, wallet key, provider
credential, or external-network client.  It serves only the offline prototype,
the fail-closed readiness summary, the deterministic untrusted draft parser,
and the fixed-catalog read-only support boundary.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
import ipaddress
import mimetypes
import re
import socket
import threading
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import unquote, urlsplit

from services.nontransactional_support_gateway.gateway import BoundaryViolation, LOCAL_DEMO_CONTEXT, handle
from shared.canonical import CanonicalizationError, canonical_bytes, strict_loads
from shared.domain import DomainError, parse_intent_locally


ROOT = Path(__file__).resolve().parents[2]
MAX_REQUEST_BYTES = 16 * 1024
MAX_STATIC_BYTES = 2 * 1024 * 1024
MAX_CONCURRENT_REQUESTS = 16
RATE_LIMIT_WINDOW_SECONDS = 1.0
RATE_LIMIT_REQUESTS_PER_WINDOW = 60
MAX_RATE_LIMIT_SOURCES = 1024
LOCAL_STATUS = "LOCAL_SANDBOX_OPERATIONAL_GO"
PRODUCTION_STATUS = "BLOCKED_NOT_OPERATIONAL"
_PERCENT_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")

_STATIC_ROUTES: dict[str, Path] = {
    "/": ROOT / "START_HERE.html",
    "/START_HERE.html": ROOT / "START_HERE.html",
    "/START_HERE.css": ROOT / "START_HERE.css",
    "/prototype": ROOT / "prototype/index.html",
    "/prototype/": ROOT / "prototype/index.html",
    "/prototype/index.html": ROOT / "prototype/index.html",
    "/prototype/app.js": ROOT / "prototype/app.js",
    "/prototype/styles.css": ROOT / "prototype/styles.css",
    "/docs/final-delivery-index": ROOT / "FINAL_DELIVERY_INDEX.md",
    "/docs/fee-route-and-asset-registry": ROOT / "47_FEE_ROUTE_AND_ASSET_REGISTRY_SPEC.md",
    "/FINAL_DELIVERY_INDEX.md": ROOT / "FINAL_DELIVERY_INDEX.md",
    "/47_FEE_ROUTE_AND_ASSET_REGISTRY_SPEC.md": ROOT / "47_FEE_ROUTE_AND_ASSET_REGISTRY_SPEC.md",
}


def _json_safe(value: Any) -> bytes:
    """Emit stable UTF-8 JSON after the shared canonical type/NFC checks."""
    return canonical_bytes(value)


def _is_loopback_host(host: str) -> bool:
    if not isinstance(host, str):
        return False
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _authority(authority: str, *, default_port: int) -> tuple[str, int] | None:
    """Parse an HTTP authority without resolving DNS or accepting credentials."""
    if not isinstance(authority, str) or not authority or any(char.isspace() for char in authority):
        return None
    try:
        parsed = urlsplit("//" + authority)
        if parsed.username is not None or parsed.password is not None or parsed.path or parsed.query or parsed.fragment:
            return None
        hostname = parsed.hostname
        port = parsed.port if parsed.port is not None else default_port
    except ValueError:
        return None
    if hostname is None or not _is_loopback_host(hostname):
        return None
    return hostname.lower(), port


def _same_loopback_origin(origin: str, host_header: str, *, server_port: int) -> bool:
    try:
        parsed = urlsplit(origin)
        if parsed.scheme != "http" or not parsed.netloc or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            return False
        if parsed.username is not None or parsed.password is not None:
            return False
        origin_host = parsed.hostname
        origin_port = parsed.port if parsed.port is not None else 80
    except ValueError:
        return False
    host = _authority(host_header, default_port=80)
    if origin_host is None or host is None or not _is_loopback_host(origin_host):
        return False
    return origin_host.lower() == host[0] and origin_port == host[1] == server_port


@dataclass(frozen=True)
class AppResponse:
    status: int
    content_type: str
    body: bytes


class LocalSandboxApp:
    """Pure request router used by both the HTTP handler and unit tests."""

    def __init__(self, root: Path = ROOT) -> None:
        self.root = root.resolve()

    def _read_static(self, path: str) -> AppResponse:
        configured = _STATIC_ROUTES.get(path)
        if configured is None:
            return self.json_error(HTTPStatus.NOT_FOUND, "NOT_FOUND", "そのページはありません。")
        try:
            relative = configured.relative_to(ROOT)
            unresolved = self.root / relative
            if unresolved.is_symlink():
                raise OSError("static symlink is not permitted")
            target = unresolved.resolve(strict=True)
            target.relative_to(self.root)
            if not target.is_file():
                raise OSError("static target is not a regular file")
            with target.open("rb") as handle:
                body = handle.read(MAX_STATIC_BYTES + 1)
            if len(body) > MAX_STATIC_BYTES:
                raise OSError("static file exceeds limit")
        except (OSError, RuntimeError, ValueError):
            return self.json_error(HTTPStatus.INTERNAL_SERVER_ERROR, "STATIC_FILE_INVALID", "表示を停止しました。")
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
            content_type += "; charset=utf-8"
        return AppResponse(HTTPStatus.OK, content_type, body)

    @staticmethod
    def json_error(status: int, code: str, message: str) -> AppResponse:
        return AppResponse(
            int(status),
            "application/json; charset=utf-8",
            _json_safe({"error": {"code": code, "message": message}, "productionWritePermitted": False}),
        )

    def _readiness(self) -> AppResponse:
        try:
            raw = (self.root / "delivery/OPERATIONAL_READINESS_REPORT.json").read_text(encoding="utf-8")
            report = strict_loads(raw)
            if not isinstance(report, Mapping) or report.get("status") != PRODUCTION_STATUS:
                raise ValueError("unexpected readiness status")
            if report.get("productionWritePermitted") is not False or report.get("releaseEligibleForRuntimeActivation") is not False:
                raise ValueError("readiness unexpectedly permits production")
            summary = report.get("summary")
            if not isinstance(summary, Mapping):
                raise ValueError("readiness summary is missing")
            names = ("mandatoryGates", "passedGates", "requiredClaims", "acceptedClaims")
            values: dict[str, int] = {}
            for name in names:
                value = summary.get(name)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    raise ValueError("readiness count is invalid")
                values[name] = value
            if values["mandatoryGates"] != 37 or values["requiredClaims"] != 93:
                raise ValueError("readiness profile count differs from this reviewed release")
            if values["passedGates"] != 0 or values["acceptedClaims"] != 0:
                raise ValueError("design package unexpectedly contains accepted production evidence")
            response = {
                "status": LOCAL_STATUS,
                "productionReadiness": PRODUCTION_STATUS,
                "productionWritePermitted": False,
                "releaseEligibleForRuntimeActivation": False,
                **values,
            }
            return AppResponse(HTTPStatus.OK, "application/json; charset=utf-8", _json_safe(response))
        except (OSError, UnicodeError, CanonicalizationError, KeyError, TypeError, ValueError):
            return self.json_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "READINESS_UNAVAILABLE",
                "運用判定を確認できないため停止しました。",
            )

    def route(self, method: str, raw_path: str, body: bytes = b"", content_type: str = "") -> AppResponse:
        if not isinstance(method, str) or not isinstance(raw_path, str) or not isinstance(body, bytes):
            return self.json_error(HTTPStatus.BAD_REQUEST, "INVALID_REQUEST", "要求を確認できません。")
        parsed = urlsplit(raw_path)
        if parsed.query or parsed.fragment or _PERCENT_ESCAPE.search(parsed.path):
            return self.json_error(HTTPStatus.BAD_REQUEST, "URL_CONTEXT_REJECTED", "URLに追加情報を含めないでください。")
        try:
            path = unquote(parsed.path, encoding="utf-8", errors="strict")
        except UnicodeError:
            return self.json_error(HTTPStatus.BAD_REQUEST, "INVALID_PATH", "URLを確認できません。")
        if not path.startswith("/") or "\x00" in path or any(ord(char) < 32 or ord(char) == 127 for char in path):
            return self.json_error(HTTPStatus.BAD_REQUEST, "INVALID_PATH", "URLを確認できません。")

        if method == "GET" and path in _STATIC_ROUTES:
            return self._read_static(path)
        if method == "GET" and path == "/healthz":
            return AppResponse(
                HTTPStatus.OK,
                "application/json; charset=utf-8",
                _json_safe(
                    {
                        "status": LOCAL_STATUS,
                        "mode": "LOOPBACK_OFFLINE_NON_TRANSACTIONAL",
                        "productionReadiness": PRODUCTION_STATUS,
                        "productionWritePermitted": False,
                        "signerAvailable": False,
                        "externalNetworkClientAvailable": False,
                    }
                ),
            )
        if method == "GET" and path == "/readiness":
            return self._readiness()
        if method == "POST" and path == "/v1/draft":
            if content_type.split(";", 1)[0].strip().lower() != "application/json":
                return self.json_error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "JSON_REQUIRED", "JSON形式だけを受け付けます。")
            if len(body) > MAX_REQUEST_BYTES:
                return self.json_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "REQUEST_TOO_LARGE", "入力が長すぎます。")
            try:
                data = strict_loads(body.decode("utf-8", errors="strict"))
                if not isinstance(data, Mapping) or set(data) != {"utterance"} or not isinstance(data["utterance"], str):
                    raise ValueError("invalid draft shape")
                utterance = data["utterance"]
                if not 1 <= len(utterance) <= 2048:
                    raise ValueError("invalid utterance length")
                draft = parse_intent_locally(utterance)
                response = {
                    "sourceUtterance": draft.source_utterance,
                    "normalizedInterpretation": draft.normalized_interpretation,
                    "proposed": dict(draft.proposed),
                    "materialAmbiguities": list(draft.material_ambiguities),
                    "primaryActionEnabled": draft.executable,
                    "intentCommitment": draft.intent_commitment,
                    "productionWritePermitted": False,
                }
                return AppResponse(HTTPStatus.OK, "application/json; charset=utf-8", _json_safe(response))
            except (UnicodeDecodeError, ValueError, CanonicalizationError, DomainError):
                return self.json_error(HTTPStatus.BAD_REQUEST, "INVALID_DRAFT_REQUEST", "入力を確認できません。")
        status_match = re.fullmatch(r"/v1/support/status/([A-Za-z0-9_-]{24,128})", path)
        glossary_match = re.fullmatch(r"/v1/support/glossary/([a-z0-9-]{2,64})", path)
        if method == "GET" and status_match:
            try:
                response = handle(
                    "getReadOnlyStatus",
                    {"path": {"referenceId": status_match.group(1)}},
                    trusted_context=LOCAL_DEMO_CONTEXT,
                )
                return AppResponse(HTTPStatus.OK, "application/json; charset=utf-8", _json_safe(response))
            except BoundaryViolation:
                return self.json_error(HTTPStatus.BAD_REQUEST, "BOUNDARY_REJECTED", "この境界では処理できない入力です。")
        if method == "GET" and glossary_match:
            try:
                response = handle("getPlainJapaneseTerm", {"path": {"termId": glossary_match.group(1)}})
                return AppResponse(HTTPStatus.OK, "application/json; charset=utf-8", _json_safe(response))
            except BoundaryViolation:
                return self.json_error(HTTPStatus.NOT_FOUND, "NOT_FOUND", "その用語はありません。")
        support_operations = {
            "/v1/support/explain-error": "explainNonTransactionalError",
            "/v1/support/safety-help": "getGenericSafetyHelp",
        }
        if method == "POST" and path in support_operations:
            if content_type.split(";", 1)[0].strip().lower() != "application/json":
                return self.json_error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "JSON_REQUIRED", "JSON形式だけを受け付けます。")
            if len(body) > MAX_REQUEST_BYTES:
                return self.json_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "REQUEST_TOO_LARGE", "入力が長すぎます。")
            try:
                value = strict_loads(body.decode("utf-8", errors="strict"))
                if not isinstance(value, Mapping):
                    raise BoundaryViolation("request body must be an object")
                response = handle(support_operations[path], {"body": value}, trusted_context=LOCAL_DEMO_CONTEXT)
                return AppResponse(HTTPStatus.OK, "application/json; charset=utf-8", _json_safe(response))
            except (UnicodeDecodeError, BoundaryViolation, ValueError):
                return self.json_error(HTTPStatus.BAD_REQUEST, "BOUNDARY_REJECTED", "この境界では処理できない入力です。")
        if path.startswith("/v1/"):
            return self.json_error(
                HTTPStatus.METHOD_NOT_ALLOWED,
                "WRITE_SURFACE_UNAVAILABLE",
                "このローカル画面には署名・送信機能がありません。",
            )
        return self.json_error(HTTPStatus.NOT_FOUND, "NOT_FOUND", "そのページはありません。")


class _Handler(BaseHTTPRequestHandler):
    server_version = "OneIntentLocalSandbox"
    sys_version = ""
    protocol_version = "HTTP/1.1"

    @property
    def app(self) -> LocalSandboxApp:
        return self.server.app  # type: ignore[attr-defined]

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(5.0)

    def _guard_headers(self) -> AppResponse | None:
        host_values = self.headers.get_all("Host", failobj=[])
        server_port = int(self.server.server_address[1])
        if len(host_values) != 1:
            return self.app.json_error(HTTPStatus.MISDIRECTED_REQUEST, "LOOPBACK_HOST_REQUIRED", "loopbackのHostだけを受け付けます。")
        host = _authority(host_values[0], default_port=80)
        if host is None or host[1] != server_port:
            return self.app.json_error(HTTPStatus.MISDIRECTED_REQUEST, "LOOPBACK_HOST_REQUIRED", "loopbackのHostだけを受け付けます。")

        origins = self.headers.get_all("Origin", failobj=[])
        if len(origins) > 1 or (origins and not _same_loopback_origin(origins[0], host_values[0], server_port=server_port)):
            return self.app.json_error(HTTPStatus.FORBIDDEN, "CROSS_ORIGIN_REJECTED", "別のoriginからは利用できません。")
        fetch_site = self.headers.get("Sec-Fetch-Site")
        if fetch_site is not None and fetch_site not in {"same-origin", "none"}:
            return self.app.json_error(HTTPStatus.FORBIDDEN, "CROSS_SITE_REJECTED", "別のsiteからは利用できません。")
        if self.headers.get_all("Transfer-Encoding", failobj=[]):
            return self.app.json_error(HTTPStatus.BAD_REQUEST, "TRANSFER_ENCODING_REJECTED", "要求形式を確認できません。")
        if self.headers.get("Expect") is not None:
            return self.app.json_error(HTTPStatus.EXPECTATION_FAILED, "EXPECT_REJECTED", "要求形式を確認できません。")
        content_encoding = self.headers.get("Content-Encoding")
        if content_encoding is not None and content_encoding.strip().lower() != "identity":
            return self.app.json_error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "CONTENT_ENCODING_REJECTED", "圧縮した要求は受け付けません。")
        lengths = self.headers.get_all("Content-Length", failobj=[])
        if len(lengths) > 1:
            return self.app.json_error(HTTPStatus.BAD_REQUEST, "CONTENT_LENGTH_REJECTED", "要求形式を確認できません。")
        return None

    def _read_body(self) -> tuple[bytes | None, AppResponse | None]:
        lengths = self.headers.get_all("Content-Length", failobj=[])
        if not lengths:
            return b"", None
        raw = lengths[0]
        if not re.fullmatch(r"[0-9]+", raw):
            return None, self.app.json_error(HTTPStatus.BAD_REQUEST, "CONTENT_LENGTH_REJECTED", "要求形式を確認できません。")
        length = int(raw, 10)
        if length > MAX_REQUEST_BYTES:
            return None, self.app.json_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "REQUEST_TOO_LARGE", "入力が長すぎます。")
        if length and self.command in {"GET", "HEAD", "OPTIONS"}:
            return None, self.app.json_error(HTTPStatus.BAD_REQUEST, "UNEXPECTED_BODY", "この要求には本文を含めないでください。")
        try:
            body = self.rfile.read(length)
        except (OSError, TimeoutError):
            return None, self.app.json_error(HTTPStatus.BAD_REQUEST, "BODY_READ_FAILED", "要求本文を確認できません。")
        if len(body) != length:
            return None, self.app.json_error(HTTPStatus.BAD_REQUEST, "BODY_TRUNCATED", "要求本文を確認できません。")
        return body, None

    def _send(self, response: AppResponse) -> None:
        self.send_response(int(response.status))
        self.send_header("Content-Type", response.content_type)
        self.send_header("Content-Length", str(len(response.body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Permissions-Policy", "accelerometer=(), camera=(), geolocation=(), microphone=(), payment=(), usb=()")
        self.send_header("X-Permitted-Cross-Domain-Policies", "none")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'; object-src 'none'",
        )
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(response.body)
        self.close_connection = True

    def _dispatch(self) -> None:
        guard = self._guard_headers()
        if guard is not None:
            self._send(guard)
            return
        body, error = self._read_body()
        if error is not None:
            self._send(error)
            return
        assert body is not None
        response = self.app.route(self.command, self.path, body, self.headers.get("Content-Type", ""))
        self._send(response)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        self._dispatch()

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        self._dispatch()

    def do_PUT(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        self._dispatch()

    def do_PATCH(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        self._dispatch()

    def do_DELETE(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        self._dispatch()

    def do_HEAD(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        self._dispatch()

    def do_OPTIONS(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        self._dispatch()

    def log_message(self, format: str, *args: object) -> None:
        # Request paths, bodies, headers, addresses, and transaction context are
        # deliberately excluded so an accidental secret in a URL is not logged.
        status = args[1] if len(args) > 1 else "-"
        print(f"local-sandbox method={self.command} status={status}")


class LocalSandboxServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address: tuple[str, int], app: LocalSandboxApp) -> None:
        self.app = app
        self._worker_slots = threading.BoundedSemaphore(MAX_CONCURRENT_REQUESTS)
        self._rate_lock = threading.Lock()
        self._rate_windows: dict[str, deque[float]] = defaultdict(deque)
        super().__init__(address, _Handler)

    @staticmethod
    def _reject_connection(request: socket.socket, status: int, reason: str, code: str) -> None:
        body = _json_safe({"error": {"code": code, "message": reason}, "productionWritePermitted": False})
        phrase = HTTPStatus(status).phrase
        header = (
            f"HTTP/1.1 {status} {phrase}\r\n"
            "Content-Type: application/json; charset=utf-8\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Cache-Control: no-store\r\n"
            "Connection: close\r\n\r\n"
        ).encode("ascii")
        try:
            request.sendall(header + body)
        except OSError:
            pass
        finally:
            request.close()

    def _allow_rate(self, client_address: tuple[object, ...]) -> bool:
        source = str(client_address[0]) if client_address else "unknown"
        now = time.monotonic()
        with self._rate_lock:
            cutoff = now - RATE_LIMIT_WINDOW_SECONDS
            active_windows = {
                key: window
                for key, window in self._rate_windows.items()
                if window and window[-1] > cutoff
            }
            if source not in active_windows and len(active_windows) >= MAX_RATE_LIMIT_SOURCES:
                oldest_source = min(active_windows, key=lambda key: active_windows[key][-1])
                del active_windows[oldest_source]
            window = active_windows.setdefault(source, deque())
            while window and window[0] <= cutoff:
                window.popleft()
            if len(window) >= RATE_LIMIT_REQUESTS_PER_WINDOW:
                self._rate_windows = active_windows
                return False
            window.append(now)
            self._rate_windows = active_windows
            return True

    def process_request(self, request: socket.socket, client_address: tuple[object, ...]) -> None:
        if not self._worker_slots.acquire(blocking=False):
            self._reject_connection(request, HTTPStatus.SERVICE_UNAVAILABLE, "処理量の上限に達したため停止しました。", "CONCURRENCY_LIMIT")
            return
        if not self._allow_rate(client_address):
            self._worker_slots.release()
            self._reject_connection(request, HTTPStatus.TOO_MANY_REQUESTS, "短時間の要求回数が上限に達しました。", "RATE_LIMITED")
            return
        super().process_request(request, client_address)

    def process_request_thread(self, request: socket.socket, client_address: tuple[object, ...]) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._worker_slots.release()


class IPv6LocalSandboxServer(LocalSandboxServer):
    address_family = socket.AF_INET6


def create_server(host: str = "127.0.0.1", port: int = 8765, *, root: Path = ROOT) -> LocalSandboxServer:
    if not _is_loopback_host(host):
        raise ValueError("local sandbox may bind only to a loopback address")
    if not isinstance(port, int) or isinstance(port, bool) or not 0 <= port <= 65535:
        raise ValueError("port must be an integer in 0..65535")
    bind_host = "127.0.0.1" if host.lower() == "localhost" else host
    server_type: type[LocalSandboxServer]
    try:
        server_type = IPv6LocalSandboxServer if ipaddress.ip_address(bind_host).version == 6 else LocalSandboxServer
    except ValueError as exc:
        raise ValueError("loopback host must be localhost or a literal loopback address") from exc
    return server_type((bind_host, port), LocalSandboxApp(root))


def serve(host: str, port: int) -> int:
    server = create_server(host, port)
    actual_host, actual_port = server.server_address[:2]
    display_host = f"[{actual_host}]" if ":" in str(actual_host) else actual_host
    print(f"LOCAL SANDBOX: http://{display_host}:{actual_port}/")
    print("Production readiness: BLOCKED_NOT_OPERATIONAL; signer/broadcast/external network: unavailable")
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the loopback-only non-transactional local sandbox.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    return serve(args.host, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
