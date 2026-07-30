from __future__ import annotations

import unittest

from services.attestation.ios_app_attest import AppAttestVerificationError, verify_server_evidence


def evidence(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "keyId": "ios-key-001",
        "bundleId": "jp.offlinewallet.ios.review",
        "teamId": "PUBLICTEAM",
        "environment": "development",
        "challengeSha256": "a" * 64,
        "capsuleSha256": "b" * 64,
        "assertionSha256": "c" * 64,
        "attestationChainSha256": "d" * 64,
        "counter": 7,
        "serverVerified": True,
        "supported": True,
        "reinstallReenrolled": True,
        "trustedDisplayClaim": False,
    }
    value.update(changes)
    return value


class IOSAppAttestContractTests(unittest.TestCase):
    def test_accepts_exact_server_verified_binding(self) -> None:
        digest = verify_server_evidence(
            evidence(),
            expected_bundle_id="jp.offlinewallet.ios.review",
            expected_team_id="PUBLICTEAM",
            expected_environment="development",
            expected_challenge_sha256="a" * 64,
            expected_capsule_sha256="b" * 64,
            minimum_counter=6,
        )
        self.assertEqual(len(digest), 64)

    def test_rejects_unverified_or_trusted_display_claim(self) -> None:
        for changes in ({"serverVerified": False}, {"trustedDisplayClaim": True}, {"supported": False}):
            with self.subTest(changes=changes):
                with self.assertRaises(AppAttestVerificationError):
                    verify_server_evidence(
                        evidence(**changes),
                        expected_bundle_id="jp.offlinewallet.ios.review",
                        expected_team_id="PUBLICTEAM",
                        expected_environment="development",
                        expected_challenge_sha256="a" * 64,
                        expected_capsule_sha256="b" * 64,
                    )

    def test_rejects_binding_mismatch_counter_replay_and_reinstall_reuse(self) -> None:
        cases = (
            {"bundleId": "other.bundle"},
            {"challengeSha256": "e" * 64},
            {"counter": 6},
            {"reinstallReenrolled": False},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                with self.assertRaises(AppAttestVerificationError):
                    verify_server_evidence(
                        evidence(**changes),
                        expected_bundle_id="jp.offlinewallet.ios.review",
                        expected_team_id="PUBLICTEAM",
                        expected_environment="development",
                        expected_challenge_sha256="a" * 64,
                        expected_capsule_sha256="b" * 64,
                        minimum_counter=6 if changes.get("counter") == 6 else None,
                    )

    def test_rejects_ambiguous_shape_and_unsafe_counter(self) -> None:
        cases = (
            {"unexpectedAuthorization": True},
            {"counter": True},
            {"counter": 2**63},
            {"assertionSha256": "A" * 64},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                with self.assertRaises(AppAttestVerificationError):
                    verify_server_evidence(
                        evidence(**changes),
                        expected_bundle_id="jp.offlinewallet.ios.review",
                        expected_team_id="PUBLICTEAM",
                        expected_environment="development",
                        expected_challenge_sha256="a" * 64,
                        expected_capsule_sha256="b" * 64,
                    )


if __name__ == "__main__":
    unittest.main()
