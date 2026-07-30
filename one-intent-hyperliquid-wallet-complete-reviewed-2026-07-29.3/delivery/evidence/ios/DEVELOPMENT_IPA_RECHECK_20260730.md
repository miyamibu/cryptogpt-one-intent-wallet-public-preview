# iOS development IPA and physical-device recheck — 2026-07-30

- Project: `apps/ios/OfflineWalletApp.xcodeproj`
- Scheme: `OfflineWalletApp`
- Bundle ID: `jp.offlinewallet.ios.review`
- Requested Team: `PUBLICTEAM`
- Archive: signed Release archive succeeded with automatic signing
- Export: development IPA succeeded; this was not an App Store or distribution export
- IPA SHA-256: `7f2ad7e8f3ec59a7bda470c525d1ff5af64ada7cfb4d479cd804e535a9080a6d`
- Embedded provisioning TeamIdentifier: `PUBLICTEAM`
- Embedded application identifier: `PUBLICTEAM.*`
- `codesign --verify --deep --strict`: PASS
- Signing certificate display name: `Apple Development: [REDACTED_SIGNING_IDENTITY]`
- Device: physical iPhone 12, UDID `[REDACTED_DEVICE_ID]`
- Install: existing app was overwritten without uninstall/reset; install succeeded
- Launch: succeeded
- Verification backend: Appium 3.5.0 / XCUITest / WebDriverAgent
- UI state: `BLOCKED_AMBIGUITIES`
- Primary CTA: `最終確認へ`, `enabled=false`
- Disabled CTA tap: no state change
- Up/down gestures: completed
- Screenshot SHA-256 before actions: `91c9c5a0058ce54a499ef66edf37c5ab67ae7840aa83042679d8672ea8735512`
- Screenshot SHA-256 after actions: `91c9c5a0058ce54a499ef66edf37c5ab67ae7840aa83042679d8672ea8735512`

The generated archive, IPA, and current screenshots remained outside the
canonical package under a temporary validation directory. No Store upload,
TestFlight submission, production entitlement, secret extraction, or app-data
reset was performed.

## Fail-closed conclusion

This closes the local development-IPA and physical-device reinstall path only.
The certificate display name still contains the old `PUBLICTEAM` label even
though the embedded profile reports Team `PUBLICTEAM`; therefore it is not
accepted as independent distribution-identity proof. App Store distribution
profile/export, release certificate chain review, App Attest production
environment/server verification, and Store review remain blocked.
