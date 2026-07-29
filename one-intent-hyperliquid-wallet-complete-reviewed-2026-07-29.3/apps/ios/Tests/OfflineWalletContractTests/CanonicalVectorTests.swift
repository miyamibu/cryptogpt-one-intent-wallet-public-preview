import CoreFoundation
import CryptoKit
import Foundation
import XCTest

final class CanonicalVectorTests: XCTestCase {
    private struct Document: Decodable {
        let schemaVersion: String
        let status: String
        let cases: [Vector]
    }

    private struct Vector: Decodable {
        let id: String
        let domain: String
        let input: String
        let canonicalBytesHex: String?
        let sha256: String?
        let expectedError: String?
    }

    private func vectorDocument() throws -> Document {
        var packageRoot = URL(fileURLWithPath: #filePath)
        for _ in 0..<5 { packageRoot.deleteLastPathComponent() }
        let path = packageRoot.appendingPathComponent("shared/canonical-vectors-v1.json")
        return try JSONDecoder().decode(Document.self, from: Data(contentsOf: path))
    }

    private func escaped(_ value: String) throws -> String {
        let data = try JSONSerialization.data(withJSONObject: [value])
        guard let text = String(data: data, encoding: .utf8), text.count >= 2 else {
            throw NSError(domain: "CanonicalVectorTests", code: 1)
        }
        return String(text.dropFirst().dropLast())
    }

    private func canonicalJSON(_ value: Any) throws -> Data {
        if value is NSNull { return Data("null".utf8) }
        if let string = value as? String { return Data(try escaped(string).utf8) }
        if let array = value as? [Any] {
            let parts = try array.map { try String(data: canonicalJSON($0), encoding: .utf8)! }
            return Data(("[" + parts.joined(separator: ",") + "]").utf8)
        }
        if let object = value as? [String: Any] {
            let parts = try object.keys.sorted().map { key in
                let encodedKey = try escaped(key)
                let encodedValue = try String(data: canonicalJSON(object[key]!), encoding: .utf8)!
                return encodedKey + ":" + encodedValue
            }
            return Data(("{" + parts.joined(separator: ",") + "}").utf8)
        }
        if let number = value as? NSNumber {
            if CFGetTypeID(number) == CFBooleanGetTypeID() {
                return Data((number.boolValue ? "true" : "false").utf8)
            }
            let integer = number.int64Value
            guard number.doubleValue == Double(integer) else {
                throw NSError(domain: "CanonicalVectorTests", code: 2)
            }
            return Data(String(integer).utf8)
        }
        throw NSError(domain: "CanonicalVectorTests", code: 3)
    }

    private func hex(_ data: Data) -> String {
        data.map { String(format: "%02x", $0) }.joined()
    }

    private func digest(domain: String, bytes: Data) -> String {
        var payload = Data(domain.utf8)
        payload.append(0)
        payload.append(bytes)
        return SHA256.hash(data: payload).map { String(format: "%02x", $0) }.joined()
    }

    func testValidCasesMatchSharedCanonicalBytesAndHash() throws {
        let document = try vectorDocument()
        XCTAssertEqual(document.schemaVersion, "shared-canonical-v1")
        XCTAssertEqual(document.status, "EXECUTABLE_CROSS_LANGUAGE_VECTOR")
        let valid = document.cases.filter { $0.expectedError == nil }
        XCTAssertEqual(valid.count, 2)
        for vector in valid {
            let object = try JSONSerialization.jsonObject(with: Data(vector.input.utf8), options: [.fragmentsAllowed])
            let bytes = try canonicalJSON(object)
            XCTAssertEqual(hex(bytes), vector.canonicalBytesHex, vector.id)
            XCTAssertEqual(digest(domain: vector.domain, bytes: bytes), vector.sha256, vector.id)
        }
    }
}
