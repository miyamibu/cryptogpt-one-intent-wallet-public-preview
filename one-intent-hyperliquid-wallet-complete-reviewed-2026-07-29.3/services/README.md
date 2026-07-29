# Services

`control_api`、`signer_interface`、`reconciler` は first-party 内部境界です。ChatGPT/OpenAI の `nontransactional_support_gateway` からは、契約・ネットワーク・権限・キュー・DB のルートを持たせない方針を証跡にしています。ここに外部資格情報や署名鍵を追加してはいけません。
