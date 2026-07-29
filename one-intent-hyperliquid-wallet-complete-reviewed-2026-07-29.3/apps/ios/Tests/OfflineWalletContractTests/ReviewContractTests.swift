import XCTest
@testable import OfflineWalletContract

final class ReviewContractTests: XCTestCase {
    func testOriginalUtteranceIsPreservedAndAmbiguityDisablesAction() {
        let draft = ReviewContract(
            sourceUtterance: "BTCを500 USDC、ペイパチャルで3倍。生産価格も見せて。",
            normalizedInterpretation: "候補を表示しています。",
            materialAmbiguities: ["方向", "ネットワーク"]
        )
        XCTAssertFalse(draft.primaryActionEnabled)
        XCTAssertEqual(draft.sourceUtterance, "BTCを500 USDC、ペイパチャルで3倍。生産価格も見せて。")
        XCTAssertEqual(draft.reasonCode, .blockedAmbiguities)
    }

    func testResolvedDraftRequiresExplicitConfirmation() {
        let draft = ReviewContract(sourceUtterance: "原文", normalizedInterpretation: "候補", materialAmbiguities: [])
        XCTAssertFalse(draft.primaryActionEnabled)
        XCTAssertEqual(draft.reasonCode, .blockedExplicitConfirmationRequired)
    }

    func testConfirmedResolvedDraftEnablesLocalFinalReviewOnly() {
        let draft = ReviewContract(sourceUtterance: "原文", normalizedInterpretation: "候補", materialAmbiguities: [], userConfirmed: true)
        XCTAssertTrue(draft.isValid)
        XCTAssertTrue(draft.primaryActionEnabled)
        XCTAssertEqual(draft.reasonCode, .readyForLocalFinalReview)
    }

    func testInvalidContractCannotBeEnabledByConfirmation() {
        let draft = ReviewContract(sourceUtterance: "", normalizedInterpretation: "候補", materialAmbiguities: [], userConfirmed: true)
        XCTAssertFalse(draft.isValid)
        XCTAssertFalse(draft.primaryActionEnabled)
        XCTAssertEqual(draft.reasonCode, .invalidContract)
    }
}
