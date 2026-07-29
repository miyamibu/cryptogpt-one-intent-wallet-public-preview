# Android Pixel 9a local recheck — 2026-07-29

- Device model: `Pixel 9a`
- ADB serial: `55211JEBF16639`
- Android: `16`
- Package: `jp.offlinewallet`
- Build command: `bash ./gradlew assembleDebug --no-daemon`
- Build result: `BUILD SUCCESSFUL`
- APK: `apps/android/app/build/outputs/apk/debug/app-debug.apk`
- APK SHA-256: `81f1b45646f2f2319bd0fb02dc27848430de8d39472297d0ed9d28f49d1a5951`
- APK signer: Android Debug certificate, APK Signature Scheme v2 verified
- Data-preserving install: `adb install -r` → `Success`
- Launch: `jp.offlinewallet/.MainActivity` visible and resumed
- Screen capture: `delivery/evidence/android/PIXEL9A_LOCAL_RECHECK_20260729.png`
- Screen capture SHA-256: `74c7d8e0ffbe34c181c1a2f35ee584b1c76b102163281ccd90b3c381555ec56b`
- UI hierarchy: `uiautomator dump` succeeded

## Interaction results

- Disabled `最終確認へ` CTA remained disabled and the screen digest was unchanged.
- Downward and upward swipe gestures completed; the screen digest was unchanged
  because all reviewed content was already visible.
- The UI hierarchy exposed `オフライン確認`, `未確認: 方向、ネットワーク`,
  `判定: BLOCKED_AMBIGUITIES`, and the disabled CTA.

## Boundary

This is physical-device UI evidence for a debug-signed build. It is not a
release-signed APK/AAB, Play App Signing/Play Integrity evidence, production
attestation, Testnet/Mainnet evidence, or store approval. No uninstall, data
clear, factory reset, wallet connection, or transaction was performed.
