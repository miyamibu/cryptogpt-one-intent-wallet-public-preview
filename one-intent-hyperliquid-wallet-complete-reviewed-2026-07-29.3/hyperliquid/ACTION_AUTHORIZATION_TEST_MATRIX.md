# Hyperliquid Action Authorization Test Matrix

> `Trade Agent expected`はproduct policyであり、protocol-level scopeの主張ではない。agent keyを持つ攻撃者がproduct signer外で何を実行できるかを別途characterizationする。

| Action | Product Trade Agent path | Product Root path | Negative |
|---|---:|---:|---|
| order | yes | optional | wrong account/asset |
| cancel | yes | optional | unknown oid |
| modify | yes | optional | size increase over policy |
| trigger | yes | optional | wrong tpsl |
| updateLeverage | policy | optional | over max |
| scheduleCancel | yes | optional | invalid time |
| vaultTransfer | no in product policy | yes | unknown vault |
| subAccountTransfer | no in product policy | yes | wrong account |
| usdClassTransfer | no | yes | wrong direction |
| sendAsset | no | yes | unknown dex/token |
| usdSend | no | yes | new destination |
| spotSend | no | yes | token mismatch |
| withdraw3 | no | yes | chain/destination mismatch |
| approveAgent | no | yes R4 | replacement without warning |
| approveBuilderFee | no | yes R4 | fee too high |
| EVM Permit | no | yes | spender mismatch |
| EVM Vault call | no | yes | selector/code mismatch |

## Required tests

### Product boundary

- mainnet payload cannot execute on testnet and vice versa
- agent signer service cannot reach root typed builder
- root signer rejects wrong role
- Capsule account／policy／registry／expiry mismatch
- manipulated amount／destination／fee
- duplicate nonce／reused agent address
- concurrent subaccounts／clock skew／`expiresAfter`

### Bearer-key characterization

- export a disposable Testnet agent key in a controlled harness
- bypass the product signer and attempt every documented L1 action type
- record accepted／rejected behavior and affected account／vault／subaccount
- verify product documentation does not claim stronger protocol scope
- verify dedicated account hard cap limits blast radius
- verify monitor detects out-of-band action
- verify revoke／replace blocks future action
- verify old address is never reused after pruning/replacement

### Agent lifecycle

- named／unnamed agent current limits
- replacement semantics
- expiry／zero balance pruning
- nonce set pruning and replay risk
- one agent per trading process／parallel subaccount within protocol limits
- no UI-session agent proliferation
