# ChatGPT-facing boundary

実装は `services/nontransactional_support_gateway/gateway.py` にあります。固定 read-only operation 以外の route／schema／context は公開しません。

status／error／safety operationはtrusted subject／tenant context、reference ownership、24文字以上のopaque ID、in-process rate limit、固定response field allowlistを要求します。`LOCAL_DEMO_CONTEXT`はloopback sandbox専用の非本番fixtureです。
