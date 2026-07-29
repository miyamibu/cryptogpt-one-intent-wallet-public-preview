// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "OfflineWalletContract",
    platforms: [.macOS(.v13)],
    products: [
        .library(name: "OfflineWalletContract", targets: ["OfflineWalletContract"]),
        .library(name: "OfflineWalletUI", targets: ["OfflineWalletUI"]),
    ],
    targets: [
        .target(name: "OfflineWalletContract", path: "Sources/OfflineWalletContract"),
        .target(name: "OfflineWalletUI", dependencies: ["OfflineWalletContract"], path: "Sources/OfflineWalletUI"),
        .testTarget(name: "OfflineWalletContractTests", dependencies: ["OfflineWalletContract"], path: "Tests/OfflineWalletContractTests"),
    ]
)
