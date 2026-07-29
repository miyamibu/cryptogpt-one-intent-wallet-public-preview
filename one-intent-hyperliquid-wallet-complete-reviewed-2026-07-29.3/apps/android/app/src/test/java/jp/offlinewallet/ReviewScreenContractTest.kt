package jp.offlinewallet

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ReviewScreenContractTest {
    @Test fun ambiguousDraftCannotEnablePrimaryAction() {
        val draft = ReviewContractV1("原文", "候補", listOf("ネットワーク"))
        assertFalse(draft.primaryActionEnabled)
        assertEquals(ReviewContractV1.ReasonCode.BLOCKED_AMBIGUITIES, draft.reasonCode)
    }

    @Test fun resolvedDraftStillRequiresExplicitConfirmation() {
        val draft = ReviewContractV1("原文", "候補", emptyList())
        assertFalse(draft.primaryActionEnabled)
        assertEquals(ReviewContractV1.ReasonCode.BLOCKED_EXPLICIT_CONFIRMATION_REQUIRED, draft.reasonCode)
    }

    @Test fun confirmedResolvedDraftOnlyEnablesLocalFinalReview() {
        val draft = ReviewContractV1("原文", "候補", emptyList(), userConfirmed = true)
        assertTrue(draft.isValid)
        assertTrue(draft.primaryActionEnabled)
        assertEquals(ReviewContractV1.ReasonCode.READY_FOR_LOCAL_FINAL_REVIEW, draft.reasonCode)
    }

    @Test fun invalidContractCannotBeMadeExecutableByConfirmation() {
        val draft = ReviewContractV1("", "候補", emptyList(), userConfirmed = true)
        assertFalse(draft.isValid)
        assertFalse(draft.primaryActionEnabled)
        assertEquals(ReviewContractV1.ReasonCode.INVALID_CONTRACT, draft.reasonCode)
    }
}
