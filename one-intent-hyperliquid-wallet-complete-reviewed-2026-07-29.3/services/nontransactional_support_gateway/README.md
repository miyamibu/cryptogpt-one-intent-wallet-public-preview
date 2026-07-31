# Non-transactional support gateway

このサービスは ChatGPT/OpenAI 向けに、固定カタログの説明と秘匿済み状態だけを返します。`shared.domain.parse_intent_locally`、Control API write、Signer、Broadcaster、Address Book、Quote、Transaction payload にはルートを持ちません。4 つの operation ID、固定 request property、`.read` scope、`writeAvailableHere=false`、`executable=false` は `gateway.py` と契約テストで固定しています。

status／error／safety operationはtrusted subject／tenant context、reference ownership、24文字以上のopaque ID、in-process rate limit、固定response field allowlistを要求します。`LOCAL_DEMO_CONTEXT`はloopback sandbox専用の非本番fixtureです。
