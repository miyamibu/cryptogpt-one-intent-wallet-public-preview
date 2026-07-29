# Local sandbox runtime

This service is the ZIP-contained runnable mode. It binds only to literal loopback addresses or `localhost` and exposes:

- `GET /` and `/prototype/` for the reviewed offline screens;
- `GET /healthz` and fail-closed `/readiness`;
- `POST /v1/draft` for deterministic local untrusted-draft parsing;
- `POST /v1/support/{operationId}` for the fixed-catalog, read-only support boundary.

It intentionally contains **no signer, broadcaster, wallet key, provider credential, external-network client, transaction endpoint, executable deep link, or Mainnet/Testnet write**. Any `/v1/*` route outside the allowlist is rejected.

The HTTP boundary rejects non-loopback or mismatched `Host`, cross-origin and cross-site requests, `Transfer-Encoding`, duplicate `Content-Length`, `Expect`, compressed request bodies, URL query/fragment context, oversized bodies, malformed paths, and unsupported content types. Responses use no-store, CSP, frame-denial, referrer, MIME-sniffing, cross-origin isolation, and restrictive permissions headers. Parser and filesystem exception details are never returned to the client.

```bash
python3 -B tools/run_local_sandbox.py self-test
python3 -B tools/run_local_sandbox.py serve
```

Open `http://127.0.0.1:8765/`. Production remains `BLOCKED_NOT_OPERATIONAL` until the external gates and Codex completion contract are satisfied.
