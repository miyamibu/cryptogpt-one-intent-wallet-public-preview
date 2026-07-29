# iOS local source build recheck — 2026-07-29

## Build

- Project: `apps/ios/OfflineWalletApp.xcodeproj`
- Scheme: `OfflineWalletApp`
- Command: `xcodebuild -project OfflineWalletApp.xcodeproj -scheme OfflineWalletApp -sdk iphoneos -configuration Debug -derivedDataPath /private/tmp/cryptogpt-ios-derived-20260729 CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO build`
- Result: `BUILD SUCCEEDED`
- Bundle ID: `jp.offlinewallet.ios.review`
- Version: `0.1.0`
- Derived data: `/private/tmp/cryptogpt-ios-derived-20260729` (outside the canonical package)
- Built executable SHA-256: `b43b704be34883d548e656747dfa1d5f989e9b89f13a63fdfc74de6e9bae5218`
- Built executable size: `145424` bytes

## Boundary

This is a current source compilation check with signing disabled. It is not an archive/IPA, distribution-signing, Store, App Attest server, backend, signer-custody, Testnet/Mainnet, or production-operation proof. The separate physical iPhone Appium/WDA recheck is recorded in `LOCAL_RECHECK_20260729.md`.
