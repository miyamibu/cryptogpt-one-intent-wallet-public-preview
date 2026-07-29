# Admin and Operations Console Specification

## 分離

管理者consoleはmobile user appと別deploy、別auth、別domain、別feature gateにする。

## Roles

- Security Owner
- Operations Owner
- Legal／Compliance Owner
- Release Manager
- Support Read-only
- Incident Commander

一人がMainnet write enableを完結できない。

## High-risk operations

- feature gate enable
- signer policy change
- contract registry update
- address registry root update
- source quorum change
- region enable
- recovery share policy change
- emergency freeze／unfreeze

必須：hardware MFA、fresh auth、reason、ticket、expiry、second approval、append-only event。

## Dashboards

- plan compile／reject rate
- signer allow／deny
- nonce lag／conflict
- WebSocket gap
- reconciliation UNKNOWN／PARTIAL
- state source divergence
- App Attest／integrity failure
- device enrollment anomaly
- agent lifecycle／revocation
- Bridge pending age
- user support fraud reports

## Incident actions

- all writes off
- root actions off
- trade actions off
- per-region off
- per-asset off
- agent revoke queue
- compromised build blocklist
- minimum app version
- forced re-enrollment

## Support boundary

Supportは以下を要求しない。

- seed phrase
- private key
- MPC share
- full recovery material
- screen share of secret

support responseにはverified in-app case IDを使う。
