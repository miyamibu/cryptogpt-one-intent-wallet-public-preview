# Android release build recheck — 2026-07-30

- Command: `bash ./gradlew --no-daemon test assembleRelease bundleRelease`
- Gradle: 9.3.1
- Java: Homebrew OpenJDK 17.0.18
- Result: `BUILD SUCCESSFUL`
- Unit tests: debug and release unit test tasks PASS
- Release lint: PASS
- Unsigned APK SHA-256: `38e4550fde7bcf9b4515c65e12649e1ec13ed07ec25f81381a7afdbf1c47a1d5`
- AAB SHA-256: `630bde068cb932a6b78092f53fb1ba6ccea0c77d9486af8afb48c63db7b28fda`
- APK signature verification: failed as expected because the artifact is unsigned
- AAB `jarsigner -verify`: reports that the bundle is unsigned
- Pixel 9a: not attached during this recheck

The output hashes match the 2026-07-29 local build evidence. No release
keystore, Play App Signing key, Play Console upload, Play Integrity verdict,
or Store action was used. `ANDROID_BUILD_SIGNED` remains blocked.
