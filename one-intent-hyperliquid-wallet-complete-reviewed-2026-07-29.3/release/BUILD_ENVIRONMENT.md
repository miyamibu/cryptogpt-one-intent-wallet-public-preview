# Build Environment — design-only

package=one-intent-hyperliquid-wallet-complete-reviewed-2026-07-29.3
recordedAt=2026-07-29T00:00:00Z
status=PARTIAL_DESIGN_LOCK_NOT_RELEASE_LOCK
complete=false

## Recorded tools

- Python: 3.14.6 (/opt/homebrew/opt/python@3.14/bin/python3.14)
- Python dependencies: jsonschema 4.26.0, PyYAML 6.0.3, cryptography 46.0.4, Playwright 1.57.0
- Browser: Playwright 1.57.0 / Chromium 143.0.7499.4
- Swift: 6.3.3; Xcode 26.6; iPhoneOS SDK 26.5
- Java: OpenJDK 17.0.18

## Native build boundary

- Android Gradle Wrapper: `GRADLE_WRAPPER_9.3.1_PRESENT_LOCAL_ONLY`
- Android Gradle CLI: `GRADLE_9.3.1_PRESENT_LOCAL_ONLY`
- Android SDK/sdkmanager: `ANDROID_SDK_API_35_36_PRESENT_LOCAL_ONLY` / `SDKMANAGER_PRESENT_LOCAL_ONLY`
- iOS target: `OfflineWalletApp` Xcode app target plus Swift Package on `macOS 13`; local Team `8R3B5675ZJ` signed iPhoneOS device proof and unsigned Simulator compile, with no archive/IPA.

## Safety controls

- networkAccessForValidation: `false`
- productionWritePermitted: `false`
- nativeSignedArtifactsAvailable: `false`
- artifactSigningAvailable: `false`
- twoPersonApprovalProvisioned: `false`

`BUILD_ENVIRONMENT.md` is a recorded local design environment, not a hermetic builder attestation. Local Android debug/device proof and the Team `8R3B5675ZJ` iPhone 12 signed debug/device proof do not close release archive/IPA, distribution signing, custody, or production gates.
