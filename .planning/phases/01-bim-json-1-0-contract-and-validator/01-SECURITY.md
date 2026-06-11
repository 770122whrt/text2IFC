---
phase: 1
slug: bim-json-1-0-contract-and-validator
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-11
---

# Phase 1 - Security

## Trust Boundaries

| Boundary | Description | Data crossing |
|---|---|---|
| JSON file to validator | A local file may contain malformed or pathological JSON | Untrusted structured input |
| JSON Schema to validator | The checked-in schema controls validation behavior | Trusted local contract |
| Legacy source to migration output | Existing files are read and normalized into a separate output root | Project data and provenance |

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|---|---|---|---|---|---|
| T-01-01 | Denial of service | Validation CLI | mitigate | Bound input size and emitted error count; test both limits | closed |
| T-01-02 | Server-side request forgery | Schema resolution | mitigate | Forbid remote `$ref` and perform no network resolution | closed |
| T-01-03 | Tampering | Migration | mitigate | Fixed source/output roots, deterministic paths, source SHA-256 before/after | closed |
| T-01-04 | Data loss | Migration | mitigate | Never overwrite sources; reject incomplete models; record every intentional omission | closed |

## Accepted Risks Log

No accepted risks.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|---|---:|---:|---:|---|
| 2026-06-11 | 4 | 4 | 0 | Codex planning review |
| 2026-06-11 | 4 | 4 | 0 | Codex implementation verification |

## Implementation Evidence

- T-01-01: CLI tests enforce the 10 MiB input limit and 1000-error cap.
- T-01-02: schema and reference tests reject non-local `$ref` values and use
  no network resolution.
- T-01-03: migration outputs use fixed category/ordinal names, path containment
  checks, atomic writes, and deterministic audit bytes.
- T-01-04: source hashes remain unchanged; incomplete and conflicting source
  facts reject the whole model; omissions and source element counts are
  recorded.

## Sign-Off

- [x] All threats have a disposition.
- [x] No accepted risks require documentation.
- [x] `threats_open: 0` confirmed.
- [x] Re-verified mitigations after Phase 1 execution.

**Approval:** verified 2026-06-11
