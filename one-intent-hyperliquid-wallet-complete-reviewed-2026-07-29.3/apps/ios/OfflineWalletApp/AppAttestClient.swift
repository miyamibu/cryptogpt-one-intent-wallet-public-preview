import CryptoKit
import DeviceCheck
import Foundation

/// iOS-side App Attest boundary.
///
/// This client only creates Apple-produced key/attestation/assertion material
/// and binds assertions to canonical request data. Apple signature and
/// certificate verification must happen on the protected backend. App Attest
/// is never a trusted-display claim and is never a wallet signing key.
final class AppAttestClient {
    private let service = DCAppAttestService.shared

    var isSupported: Bool {
        service.isSupported
    }

    func generateKey() async throws -> String {
        guard isSupported else {
            throw AppAttestClientError.unsupported
        }
        return try await withCheckedThrowingContinuation { continuation in
            service.generateKey { keyId, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                guard let keyId, !keyId.isEmpty else {
                    continuation.resume(throwing: AppAttestClientError.missingKeyId)
                    return
                }
                continuation.resume(returning: keyId)
            }
        }
    }

    func attest(keyId: String, clientDataHash: Data) async throws -> Data {
        guard isSupported else {
            throw AppAttestClientError.unsupported
        }
        guard !keyId.isEmpty, clientDataHash.count == 32 else {
            throw AppAttestClientError.invalidBinding
        }
        return try await withCheckedThrowingContinuation { continuation in
            service.attestKey(keyId, clientDataHash: clientDataHash) { attestation, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                guard let attestation, !attestation.isEmpty else {
                    continuation.resume(throwing: AppAttestClientError.missingEvidence)
                    return
                }
                continuation.resume(returning: attestation)
            }
        }
    }

    func generateAssertion(keyId: String, clientDataHash: Data) async throws -> Data {
        guard isSupported else {
            throw AppAttestClientError.unsupported
        }
        guard !keyId.isEmpty, clientDataHash.count == 32 else {
            throw AppAttestClientError.invalidBinding
        }
        return try await withCheckedThrowingContinuation { continuation in
            service.generateAssertion(keyId, clientDataHash: clientDataHash) { assertion, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                guard let assertion, !assertion.isEmpty else {
                    continuation.resume(throwing: AppAttestClientError.missingEvidence)
                    return
                }
                continuation.resume(returning: assertion)
            }
        }
    }

    /// Builds the request binding hash. The server must recompute this from
    /// the exact same fields and separately verify the Apple assertion.
    func clientDataHash(
        semanticHash: String,
        renderReceiptHash: String,
        sourceStateHash: String,
        challenge: String,
        sessionId: String,
        deviceRegistrationId: String,
        policyVersion: String,
        expiresAt: Int
    ) throws -> Data {
        let value: [String: Any] = [
            "semanticHash": semanticHash,
            "renderReceiptHash": renderReceiptHash,
            "sourceStateHash": sourceStateHash,
            "challenge": challenge,
            "sessionId": sessionId,
            "deviceRegistrationId": deviceRegistrationId,
            "policyVersion": policyVersion,
            "expiresAt": expiresAt,
        ]
        guard JSONSerialization.isValidJSONObject(value) else {
            throw AppAttestClientError.invalidBinding
        }
        let json = try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
        return Data(SHA256.hash(data: json))
    }
}

enum AppAttestClientError: Error {
    case unsupported
    case invalidBinding
    case missingKeyId
    case missingEvidence
}
