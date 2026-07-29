"""Server-side attestation evidence contracts.

The package never verifies Apple signatures locally.  It only accepts an
evidence record produced by a separately protected Apple verifier and checks
that the record is bound to the exact operation before it can be considered
by a policy engine.
"""

from .ios_app_attest import AppAttestEvidence, AppAttestVerificationError, verify_server_evidence

__all__ = ["AppAttestEvidence", "AppAttestVerificationError", "verify_server_evidence"]
