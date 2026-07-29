# iPhone 12 physical UI recheck — 2026-07-29

## Device and backend

- Device: iPhone 12
- UDID: `[REDACTED_DEVICE_ID]`
- Connection: USB, trusted and unlocked
- Appium: 3.5.0
- Backend: Appium/XCUITest/WebDriverAgent
- Bundle ID: `jp.offlinewallet.ios.review`
- Session mode: `noReset=true`; no uninstall, erase, reset, or reinstall performed

## Operations actually performed

1. Started an Appium session against the installed app and captured the starting screen.
2. Located the disabled button `最終確認へ` from the accessibility tree and issued a tap.
3. Captured the post-tap screen and compared the accessibility source.
4. Issued one upward and one downward swipe and captured both results.
5. Deleted the Appium session normally.

## Results

- Appium session: PASS
- Disabled CTA tap: executed; no visible or accessibility-source state change
- Starting screen SHA-256: `5c87b7bd369c0c91dc03cc7f13ca7edfd595f0a31bf2ff7f30398e8f58ea29c0`
- After disabled CTA SHA-256: `5c87b7bd369c0c91dc03cc7f13ca7edfd595f0a31bf2ff7f30398e8f58ea29c0`
- Up-swipe: executed; no visual change because all current content was already visible
- Down-swipe: executed; no visual change because all current content was already visible
- Screenshot artifact: `delivery/evidence/ios/iphone12-appium-recheck-20260729.png`
- Screenshot artifact SHA-256: `5c87b7bd369c0c91dc03cc7f13ca7edfd595f0a31bf2ff7f30398e8f58ea29c0`

## Boundary

This is physical-device UI evidence only. It does not prove archive/IPA distribution signing, App Attest server verification, Store approval, backend operation, signer custody, Testnet/Mainnet, or production readiness. The earlier canonical screenshot with SHA-256 `8a1e808d66fc9580e74c5ae90d4f34549986f87e05f3b4b0e3269fdbae7444ea` remains preserved and was not overwritten.
