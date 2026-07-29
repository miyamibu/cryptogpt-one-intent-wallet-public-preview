import Foundation

public struct ReviewContract: Sendable, Equatable {
    public let sourceUtterance: String
    public let normalizedInterpretation: String
    public let materialAmbiguities: [String]
    public let userConfirmed: Bool

    public init(sourceUtterance: String, normalizedInterpretation: String, materialAmbiguities: [String], userConfirmed: Bool = false) {
        self.sourceUtterance = sourceUtterance
        self.normalizedInterpretation = normalizedInterpretation
        self.materialAmbiguities = materialAmbiguities
        self.userConfirmed = userConfirmed
    }

    public enum ReasonCode: String, Sendable {
        case invalidContract = "INVALID_CONTRACT"
        case blockedAmbiguities = "BLOCKED_AMBIGUITIES"
        case blockedExplicitConfirmationRequired = "BLOCKED_EXPLICIT_CONFIRMATION_REQUIRED"
        case readyForLocalFinalReview = "READY_FOR_LOCAL_FINAL_REVIEW"
    }

    public var reasonCode: ReasonCode {
        if sourceUtterance.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ||
            normalizedInterpretation.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ||
            materialAmbiguities.contains(where: { $0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }) ||
            materialAmbiguities.count != Set(materialAmbiguities).count ||
            (userConfirmed && !materialAmbiguities.isEmpty) {
            return .invalidContract
        }
        if !materialAmbiguities.isEmpty { return .blockedAmbiguities }
        if !userConfirmed { return .blockedExplicitConfirmationRequired }
        return .readyForLocalFinalReview
    }

    public var isValid: Bool { reasonCode != .invalidContract }

    public var primaryActionEnabled: Bool {
        reasonCode == .readyForLocalFinalReview
    }
}
