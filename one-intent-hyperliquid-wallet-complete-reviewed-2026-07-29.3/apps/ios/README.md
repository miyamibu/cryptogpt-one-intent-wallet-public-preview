# iOS App Target

予定stack：Swift、SwiftUI、Swift Concurrency、AuthenticationServices、LocalAuthentication、CryptoKit Secure Enclave、DeviceCheck App Attest、Security Keychain。

`OfflineWalletContract`にpure review contract、`OfflineWalletUI`にUI-only shellを収録しています。`READY_FOR_LOCAL_FINAL_REVIEW`はローカル最終確認画面だけを示し、署名・送信・deep link・network authorizationではありません。`OfflineWalletApp.xcodeproj`、bundle ID、Info.plist、SwiftUI app entrypointを追加し、Team `8R3B5675ZJ` のApple Development iPhoneOS build、iPhone 12実機インストール・起動・UI証跡をPASSしました。archive/IPA、配布署名、Store公開は未完了です。

`OfflineWalletApp/AppAttestClient.swift`は、対応端末でAppleが発行するkey／attestation／assertionを、semantic hash等へ束縛したclient-data hashとともに生成する境界です。Appleの証明書・署名・counterのサーバー検証はこのローカルパッケージには含まれず、App AttestはTrusted Displayやwallet root signing keyとして扱いません。現在のApp Attest証跡は未取得で、production entitlement、server verification、unsupported／再インストール再登録の実機証拠が揃うまで`NO_GO`です。

共通vectorは`shared/mobile-review-contract-v1.tsv`です。Swift PackageのmacOS contract test 5件、`OfflineWalletApp`のiPhoneOS／Simulator compileを実行しました。Appium 3.5.0／XCUITest 11.16.3／WDAで、iPhone 12の画面取得、無効CTAタップ、上下ジェスチャを確認済みです。iOS archive/IPA、配布署名、Store、完全な実機matrixは別gateとして扱います。

P0：iPhone 12実機、smallest supported iPhone、recent Face ID iPhone。
