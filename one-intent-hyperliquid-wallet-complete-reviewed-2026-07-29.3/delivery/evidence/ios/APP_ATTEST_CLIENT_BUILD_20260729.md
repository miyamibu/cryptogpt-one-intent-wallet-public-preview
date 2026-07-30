# iOS App Attest client build evidence — 2026-07-29

- Target: `apps/ios/OfflineWalletApp.xcodeproj` / `OfflineWalletApp`
- Bundle ID: `jp.offlinewallet.ios.review`
- Build command: `xcodebuild -project OfflineWalletApp.xcodeproj -scheme OfflineWalletApp -sdk iphoneos -configuration Debug -derivedDataPath /private/tmp/<redacted> CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO build`
- Result: `BUILD SUCCEEDED`
- App executable SHA-256: `130ee0f0c466e639ed5c1b966fae8d0a7d717ea53b684590f2498ce4abbb0200`
- Linked platform frameworks observed: `DeviceCheck.framework`, `CryptoKit.framework`, `SwiftUI.framework`, `UIKit.framework`

## Boundary

`AppAttestClient.swift` now exposes the iOS-side `isSupported`, key generation,
attestation, assertion, and request-binding hash boundary. The build was made
with signing disabled and did not access a certificate, provisioning profile,
Apple account secret, App Attest key, attestation, or assertion.

This is source/build evidence only. It does not prove an Apple production
entitlement, Apple server verification, counter persistence, unsupported-device
fallback, reinstall/migration re-enrollment, or Store eligibility. The backend
must verify the Apple evidence and exact bundle/team/environment binding before
any authorization policy can consider it.
