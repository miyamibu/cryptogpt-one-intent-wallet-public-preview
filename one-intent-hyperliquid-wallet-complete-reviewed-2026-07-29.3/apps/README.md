# Apps

Browser、Android、iOS の最小安全境界を同じ日本語・未信頼 draft 契約で揃えています。AndroidはGradle Wrapperによるunsigned release設定のbuild、AAB生成、unit testを確認済みで、Pixel 9a（serial `[REDACTED_FOR_PUBLIC_PREVIEW]`）にはdebug-signed APKをdata-preserving installして起動・画面・CTA・上下ジェスチャを確認済みです。iOSはTeam `PUBLICTEAM`のsigned device buildとiPhone 12のインストール・起動・Appium/WDA画面操作proofを確認済みです。release APK/AABの署名、iOS archive/IPAの配布署名、完全な実機matrix、production attestationは未確認で、release gateは`NO_GO`のままです。
