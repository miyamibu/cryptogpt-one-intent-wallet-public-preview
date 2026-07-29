# Changelog — 2026-07-29.3

## Release boundary

- `.2` baseline is preserved as the input package and is not overwritten.
- This `.3` package is a new design/operationalization evidence subject.
- `productionWritePermitted=false` remains enforced.
- Mainnet, public stores, production activation, and real-funds operations remain disabled.

## Evidence and release work

- Added a secret-free `ACCESS_AND_AUTHORITY_INVENTORY` for local, repository, device, and external-service availability.
- Bound 37 gates and 93 claims to explicit wallet-dependency classes; personal wallet connection is never required.
- Added baseline ZIP/tree/manifest/checksum evidence and recorded baseline validation failures without weakening validators.
- Updated current iPhone 12 local proof and retained the physical screenshot hash.
- Rebuilt release metadata, SBOM/provenance design artifacts, traceability, reports, manifest, and deterministic ZIP for `.3`.

## Non-operational boundary

This package does not claim signed production artifacts, live backend, HSM/MPC custody, Testnet/Mainnet writes, provider contracts, legal approval, Store approval, or independent audit completion.
