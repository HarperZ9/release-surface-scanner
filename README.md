# Release Surface Scanner

Release Surface Scanner is a public-safe scanner for turning a repository into a reviewable release packet.

It checks required release files, skips private environment files, detects secret-shaped values without echoing them, hashes included files, emits a machine-readable release report, and builds a compact proof index.

## Commands

```powershell
release-scan scan . --json-out out/release-report.json --md-out out/release-report.md --fail-on-fail
release-scan proof-index . --json-out out/proof-index.json
```

## Boundary

This package publishes generic release assurance mechanics only. It does not publish private operator data, private evidence, client data, credentials, or `.env` files.
