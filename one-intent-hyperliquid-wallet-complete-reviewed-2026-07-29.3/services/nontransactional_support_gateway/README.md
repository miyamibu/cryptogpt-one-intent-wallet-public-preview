# Non-transactional support gateway

このサービスは ChatGPT/OpenAI 向けに、固定カタログの説明と秘匿済み状態だけを返します。`shared.domain.parse_intent_locally`、Control API write、Signer、Broadcaster、Address Book、Quote、Transaction payload にはルートを持ちません。4 つの operation ID、固定 request property、`.read` scope、`writeAvailableHere=false`、`executable=false` は `gateway.py` と契約テストで固定しています。
