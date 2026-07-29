# Platform Security Capability Matrix

| Capability | Android | iPhone | 共通判断 |
|---|---|---|---|
| 生体認証 | BiometricPrompt | Face ID／Touch ID via LocalAuthentication | user presence、内容保証ではない |
| authorization key | Android Keystore | Secure Enclave P-256 | capsule hash署名用 |
| app integrity | Play Integrity／key attestation等 | App Attest | risk signal、単独許可不可 |
| trusted confirmation | 対応端末のConfirmationPrompt | 一般目的の同等APIを前提にしない | silent parity禁止 |
| root secp256k1 | software/MPC/external wallet | software/MPC/external wallet | raw keyをOS storeへ雑に置かない |
| screen capture | FLAG_SECURE等 | capture state検出、blur | iOSで完全防止を主張しない |
| device migration | key policy依存 | App Attest keyは再install/migrationで失効 | recovery ceremony必須 |
| passkey | Credential Manager | AuthenticationServices | account loginに使用、root keyそのものではない |
| app distribution | internal／Play testing／Play | development／Ad Hoc／TestFlight／App Store | Store gateを法務gateの代替にしない |
| min tap target | 48dp | 44pt | critical actionはより大きくする |
| large text | font scale | Dynamic Type | 200%でcritical fields欠落禁止 |

## Risk tier別許可

Risk tierの意味は`26_TRUSTED_DISPLAY_AND_STATE_QUORUM.md`を正本とし、platform列は同じTierに対する利用可能な認証経路だけを示す。

| Tier | 例 | Android | iOS |
|---|---|---|---|
| R0 | 閲覧 | app UI | app UI |
| R1 | 上限内Perp／Spot | session auth | authenticated app UI |
| R2 | 既知Vault／cancel all | per-use or policy | per-use + App Attest |
| R3 | 保存済み自分宛出金 | protected confirmation推奨 | standing policy＋per-use auth、またはexternal wallet |
| R4 | 新規宛先／鍵変更／recovery | external／hardware | external／hardware／cooling ceremony |

## Capability negotiation

アプリ起動時に、機能を推測で有効化しない。

```text
capabilities = detect()
policy = fetchSignedPolicy()
releaseGate = fetchSignedGate()
allowed = intersection(capabilities, policy, releaseGate)
```

unknown、unsupported、attestation failureはfail closed。R4／non-exempt R3を低い認証へ自動降格しない。R3 standing例外は事前に独立発行された限定policyでありfallbackとして生成しない。
