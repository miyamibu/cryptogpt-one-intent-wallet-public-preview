# Operational evidence directory

This directory contains design metadata and historical/non-release review records only. `delivery/evidence/core/reference-tests-current.json` records the current local validation scope; it is unsigned and cannot satisfy a production claim. `reference-tests.json` is explicitly marked historical. Files placed here do not become trusted merely by existing.

Release-facing evidence must be placed under `delivery/evidence/artifacts/`, referenced by the canonical semantic `gateId`/`claimId` in `delivery/evidence-index.json`, and bound to the exact subject in `release/release-subject.json`. Numeric `Gxx`/`Cxxx` aliases are never authoritative; external blocker mapping is in `delivery/external-blocker-traceability.json`.

A production evidence artifact must be generated from the exact immutable release subject, hashed, referenced by a signed evidence statement, independently reviewed, and included in a signed evidence index. The production verifier must also receive the trust-policy hash, verifier hash, and release-subject hash through protected out-of-band configuration.

Never place private keys, seed phrases, access tokens, full unredacted identity documents, production database exports, or unrestricted legal/customer records in a release package. Store sensitive originals in the approved controlled evidence repository and include a signed redacted decision record plus immutable digest as allowed by counsel and policy.
