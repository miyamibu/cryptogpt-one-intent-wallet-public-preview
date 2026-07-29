import SwiftUI

@main
struct OfflineWalletApp: App {
    private let draft = ReviewContract(
        sourceUtterance: "BTCを500 USDC、ペイパチャルで3倍。生産価格も見せて。",
        normalizedInterpretation: "候補を表示しています。",
        materialAmbiguities: ["方向", "ネットワーク"],
    )

    var body: some Scene {
        WindowGroup {
            ReviewScreen(draft: draft)
        }
    }
}
