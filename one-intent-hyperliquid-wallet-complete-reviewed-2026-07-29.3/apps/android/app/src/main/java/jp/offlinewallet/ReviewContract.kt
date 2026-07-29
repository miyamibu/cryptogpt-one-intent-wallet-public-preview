package jp.offlinewallet

/**
 * Pure offline review contract. READY only means local final-review UI; it
 * never authorizes signing, broadcasting, a deep link, or a network request.
 */
data class ReviewContractV1(
    val sourceUtterance: String,
    val normalizedInterpretation: String,
    val materialAmbiguities: List<String>,
    val userConfirmed: Boolean = false,
) {
    enum class ReasonCode {
        INVALID_CONTRACT,
        BLOCKED_AMBIGUITIES,
        BLOCKED_EXPLICIT_CONFIRMATION_REQUIRED,
        READY_FOR_LOCAL_FINAL_REVIEW,
    }

    val reasonCode: ReasonCode
        get() = when {
            sourceUtterance.isBlank() ||
                normalizedInterpretation.isBlank() ||
                materialAmbiguities.any { it.isBlank() } ||
                materialAmbiguities.size != materialAmbiguities.distinct().size ||
                (userConfirmed && materialAmbiguities.isNotEmpty()) -> ReasonCode.INVALID_CONTRACT
            materialAmbiguities.isNotEmpty() -> ReasonCode.BLOCKED_AMBIGUITIES
            !userConfirmed -> ReasonCode.BLOCKED_EXPLICIT_CONFIRMATION_REQUIRED
            else -> ReasonCode.READY_FOR_LOCAL_FINAL_REVIEW
        }

    val isValid: Boolean
        get() = reasonCode != ReasonCode.INVALID_CONTRACT

    val primaryActionEnabled: Boolean
        get() = reasonCode == ReasonCode.READY_FOR_LOCAL_FINAL_REVIEW
}
