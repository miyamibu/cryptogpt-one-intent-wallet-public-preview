# iOS archive/export recheck — 2026-07-29

- Command: `xcodebuild -project OfflineWalletApp.xcodeproj -scheme OfflineWalletApp -sdk iphoneos -configuration Release -archivePath <temporary>.xcarchive CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO archive`
- Archive result: `ARCHIVE SUCCEEDED`
- Archive app bundle ID: `jp.offlinewallet.ios.review`
- Archive executable SHA-256: `04c0a640613235b6e2d5e65ceb0cbc30b71a99417a0dad87764eb20f1f266ab1`
- Code-sign inspection: `code object is not signed at all`
- Export attempt: `xcodebuild -exportArchive` with an ad-hoc export options plist
- Export result: `FAILED — No Team Found in Archive`

This closes only the unsigned local archive compilation path. It does not
produce an IPA, distribution signature, provisioning-profile evidence, Apple
portal approval, App Attest server evidence, or Store submission. The archive
was written to a temporary path outside the package and no device app was
reinstalled for this step.
