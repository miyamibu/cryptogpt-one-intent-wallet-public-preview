# ChatGPT-facing boundary

実装は `services/nontransactional_support_gateway/gateway.py` にあります。固定 read-only operation 以外の route／schema／context は公開しません。
