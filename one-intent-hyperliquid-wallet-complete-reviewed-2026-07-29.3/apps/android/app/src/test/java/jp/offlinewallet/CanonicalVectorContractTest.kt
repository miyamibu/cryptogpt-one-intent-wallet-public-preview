package jp.offlinewallet

import java.io.File
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The Android test entry is intentionally file-backed: it must consume the
 * same canonical vector document as the Python and Swift checks. Gradle/SDK
 * availability and execution remain separate release gates.
 */
class CanonicalVectorContractTest {
    @Test fun sharedCanonicalVectorDocumentIsBoundToCurrentContract() {
        val vectorPath = System.getProperty("offlineWallet.sharedCanonicalVector")
        val vector = vectorPath?.let { path ->
            File(path).takeIf { it.isFile }?.readText()
        }
        assertTrue("shared/canonical-vectors-v1.json must be available to Android tests", vector != null)
        assertTrue(vector!!.contains("EXECUTABLE_CROSS_LANGUAGE_VECTOR"))
        assertTrue(vector.contains("stable-object-with-nfc-text"))
        assertTrue(vector.contains("stable-nested-array-and-object"))
    }
}
