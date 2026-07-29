# Android release-configuration build recheck — 2026-07-29

- Command: `env ANDROID_SDK_ROOT=/Users/<local-user>/Library/Android/sdk ANDROID_HOME=/Users/<local-user>/Library/Android/sdk bash ./gradlew test assembleRelease bundleRelease --no-daemon`
- Result: `BUILD SUCCESSFUL`
- Unit tests: `:app:testDebugUnitTest` and `:app:testReleaseUnitTest` passed
- Unsigned APK: `apps/android/app/build/outputs/apk/release/app-release-unsigned.apk`
- Unsigned APK SHA-256: `38e4550fde7bcf9b4515c65e12649e1ec13ed07ec25f81381a7afdbf1c47a1d5`
- AAB: `apps/android/app/build/outputs/bundle/release/app-release.aab`
- AAB SHA-256: `630bde068cb932a6b78092f53fb1ba6ccea0c77d9486af8afb48c63db7b28fda`
- APK verification: release APK is explicitly unsigned (`apksigner verify` reports missing manifest/signature)

The release configuration compiles and packages locally, but no release
keystore, Play App Signing, artifact signature, provenance signature, or
Play Console upload was available. These hashes are local build evidence and
do not close `ANDROID_BUILD_SIGNED`.
