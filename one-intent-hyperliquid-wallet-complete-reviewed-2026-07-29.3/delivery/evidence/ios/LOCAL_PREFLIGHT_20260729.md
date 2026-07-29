# iPhone 12 physical UI evidence — 2026-07-29

status: LOCAL_PHYSICAL_UI_VERIFIED
physicalUiStatus: VERIFIED
targetBundleId: jp.offlinewallet.ios.review
teamIdentifier: 8R3B5675ZJ
signingStatus: APPLE_DEVELOPMENT_DEVICE_BUILD_VERIFIED
installStatus: INSTALLED_AND_LAUNCHED
backend: Appium/WebDriverAgent
screenshotSha256: 8a1e808d66fc9580e74c5ae90d4f34549986f87e05f3b4b0e3269fdbae7444ea
screenshotPath: delivery/evidence/ios/iphone12-final-20260729.png
appExecutableSha256: 2b8f37a9917211c0856096eab3d27b5bff86212ed08ee5e7f998446daca7eba4

## Device

- Model: iPhone 12
- CoreDevice identifier: `E9D5CA0F-0729-5DFD-94B9-EFE2AB589C0E`
- USB UDID: `[REDACTED_DEVICE_ID]`
- Pairing: paired
- Lock state: unlocked since boot
- Developer Mode: enabled
- RemoteXPC tunnel: connected
- DDI services: available

## Automation backend

- Appium: 3.5.0, responding on localhost
- XCUITest driver: 11.16.3
- WebDriverAgent: responding during the physical-device session, iOS 26.5.2

## Verified build and operations

- TeamIdentifier `8R3B5675ZJ` was embedded in the signed app profile.
- `xcodebuild` signed device build: `BUILD SUCCEEDED`.
- The signed app was installed and launched on the physical iPhone.
- The disabled `最終確認へ` CTA was tapped; the visible state did not change.
- Downward and upward gestures were performed and observed.
- Start, after-scroll, and final captures were collected. The canonical final
  capture is included at `screenshotPath`; all three recorded captures have the
  `screenshotSha256` above.

This is local physical-device proof only. It is not archive/IPA, App Store,
production release evidence, or production authorization.
