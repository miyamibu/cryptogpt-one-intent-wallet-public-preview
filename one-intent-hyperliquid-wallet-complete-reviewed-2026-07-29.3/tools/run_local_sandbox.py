#!/usr/bin/env python3
"""Operator entry point for the loopback-only local sandbox."""
from __future__ import annotations

import argparse
import json
import socket
import sys
import threading
import urllib.error
import urllib.request

sys.dont_write_bytecode = True
from package_metadata import ROOT, load_package_metadata
sys.path.insert(0, str(ROOT))
from services.local_sandbox.server import LOCAL_STATUS, create_server, serve


def _request(
    url: str, *, body: dict[str, object] | None = None
) -> tuple[int, dict[str, str], dict[str, object]]:
    data = None if body is None else json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            headers = {key.lower(): value for key, value in response.headers.items()}
            return response.status, headers, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        headers = {key.lower(): value for key, value in exc.headers.items()}
        return exc.code, headers, json.loads(exc.read().decode("utf-8"))


def _raw_status(port: int, request: bytes) -> int:
    with socket.create_connection(("127.0.0.1", port), timeout=5) as connection:
        connection.sendall(request)
        response = connection.recv(4096)
    status_line = response.split(b"\r\n", 1)[0].split()
    if len(status_line) < 2 or not status_line[1].isdigit():
        raise RuntimeError(f"invalid HTTP response: {response[:200]!r}")
    return int(status_line[1])


def self_test() -> int:
    load_package_metadata()
    server = create_server("127.0.0.1", 0, root=ROOT)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        status, headers, health = _request(base + "/healthz")
        required_headers = {
            "cache-control": "no-store",
            "x-frame-options": "DENY",
            "x-content-type-options": "nosniff",
            "cross-origin-opener-policy": "same-origin",
        }
        if status != 200 or health.get("status") != LOCAL_STATUS or health.get("productionWritePermitted") is not False:
            raise RuntimeError(f"health contract failed: {status} {health}")
        for name, expected in required_headers.items():
            if headers.get(name) != expected:
                raise RuntimeError(f"security header failed: {name}={headers.get(name)!r}")
        if "frame-ancestors 'none'" not in headers.get("content-security-policy", ""):
            raise RuntimeError("content security policy does not deny framing")

        status, _, readiness = _request(base + "/readiness")
        if (
            status != 200
            or readiness.get("status") != LOCAL_STATUS
            or readiness.get("productionReadiness") != "BLOCKED_NOT_OPERATIONAL"
            or readiness.get("productionWritePermitted") is not False
            or readiness.get("passedGates") != 0
            or readiness.get("acceptedClaims") != 0
        ):
            raise RuntimeError(f"readiness fail-closed contract failed: {status} {readiness}")

        status, _, draft = _request(base + "/v1/draft", body={"utterance": "BTCを500 USDC、ペイパチャルで3倍。生産価格も見せて。"})
        if status != 200 or draft.get("primaryActionEnabled") is not False or not draft.get("materialAmbiguities"):
            raise RuntimeError(f"draft fail-closed contract failed: {status} {draft}")
        status, _, support = _request(
            base + "/v1/support/safety-help",
            body={"topic": "PROTECT_RECOVERY_SECRET", "locale": "ja-JP"},
        )
        if status != 200 or support.get("executable") is not False or any(
            key in support for key in ("transaction", "payload", "signature", "deepLink", "handoff")
        ):
            raise RuntimeError(f"support boundary failed: {status} {support}")
        status, _, blocked = _request(base + "/v1/execute", body={})
        if status != 405 or blocked.get("productionWritePermitted") is not False:
            raise RuntimeError(f"write surface was not rejected: {status} {blocked}")
        status, _, queried = _request(base + "/healthz?token=must-not-be-accepted")
        if status != 400 or queried.get("productionWritePermitted") is not False:
            raise RuntimeError(f"query context was not rejected: {status} {queried}")

        port = int(server.server_address[1])
        invalid_host = b"GET /healthz HTTP/1.1\r\nHost: attacker.example\r\nConnection: close\r\n\r\n"
        if _raw_status(port, invalid_host) != 421:
            raise RuntimeError("non-loopback Host was not rejected")
        invalid_origin = (
            f"GET /healthz HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n"
            "Origin: http://attacker.example\r\nConnection: close\r\n\r\n"
        ).encode("ascii")
        if _raw_status(port, invalid_origin) != 403:
            raise RuntimeError("cross-origin request was not rejected")
        transfer_encoding = (
            f"POST /v1/draft HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n"
            "Transfer-Encoding: chunked\r\nContent-Type: application/json\r\n"
            "Connection: close\r\n\r\n0\r\n\r\n"
        ).encode("ascii")
        if _raw_status(port, transfer_encoding) != 400:
            raise RuntimeError("Transfer-Encoding request was not rejected")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    print("LOCAL SANDBOX SELF-TEST PASSED")
    print("Loopback/offline/read-only/security-header/anti-rebinding boundary: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Operate the loopback-only local sandbox.")
    sub = parser.add_subparsers(dest="command", required=True)
    serve_parser = sub.add_parser("serve", help="serve START_HERE, the prototype, and local read-only APIs")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    sub.add_parser("self-test", help="start an ephemeral server and verify every exposed boundary")
    args = parser.parse_args()
    if args.command == "self-test":
        return self_test()
    return serve(args.host, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
