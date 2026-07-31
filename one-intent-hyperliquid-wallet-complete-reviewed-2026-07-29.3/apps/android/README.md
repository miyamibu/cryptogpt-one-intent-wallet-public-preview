# Android App Target

予定stack：Kotlin、Jetpack Compose、Coroutines、Credential Manager、BiometricPrompt、Android Keystore。

`ReviewContractV1`とComposeのオフライン確認shell、pure unit contract testを収録しています。`READY_FOR_LOCAL_FINAL_REVIEW`はローカル画面の状態だけで、署名・送信・deep link・network authorizationではありません。現行`.3`ソースではGradle Wrapper 9.3.1によるunit test、unsigned release APK、AAB buildが成功しています。Pixel 9a（serial `[REDACTED_FOR_PUBLIC_PREVIEW]`）にはdebug-signed APKをdata-preserving installし、起動・画面・無効CTA・上下ジェスチャを確認済みです。release signing、Play App Signing、instrumentation、全device matrix、release-bound signed screenshotは未完了です。

共通vectorは`shared/mobile-review-contract-v1.tsv`です。`bash ./gradlew --no-daemon :app:testDebugUnitTest :app:assembleDebug`で5件のunit testとunsigned debug buildをPASSしました。これはローカル確認であり、release signing・Testnet/Mainnet・wallet key accessの証拠ではありません。

P0 device：Pixel 9a。実機結果は `delivery/evidence/android/LOCAL_RECHECK_20260729.md`、2026-07-30の再build結果は `delivery/evidence/android/RELEASE_BUILD_RECHECK_20260730.md` を参照してください。
