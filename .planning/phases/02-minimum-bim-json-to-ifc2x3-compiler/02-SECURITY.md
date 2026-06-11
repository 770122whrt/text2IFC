---
phase: 2
slug: minimum-bim-json-to-ifc2x3-compiler
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-11
---

# Phase 2 Security

## Trust Boundaries

| Boundary | Data crossing |
|---|---|
| JSON file to strict parser and contract validator | Untrusted structured input |
| Validated BIM JSON to IfcOpenShell | Bounded values and user strings |
| Temporary IFC to reopened verifier | Generated artifact before publication |
| Verified temporary file to destination | Atomic local filesystem replacement |

## Threat Register

| ID | Threat | Mitigation | Status |
|---|---|---|---|
| T-02-01 | Invalid input overwrites valid IFC | Validate before output work; sentinel tests | closed |
| T-02-02 | Partial or invalid IFC is exposed | Verify sibling temporary file before `os.replace` | closed |
| T-02-03 | Path confusion or input/output collision | Resolve paths, reject conflicts, derive no path from BIM data | closed |
| T-02-04 | Duplicate or colliding identities | Unique source IDs plus domain-separated deterministic UUIDv5 | closed |
| T-02-05 | Millimetre/metre confusion | One conversion boundary and all-family reopened 1 mm tests | closed |
| T-02-06 | Arbitrary strings invalidate IFC enums | Allow compatible enums; preserve exact source string in pset | closed |
| T-02-07 | Resource exhaustion | CLI 10 MiB limit, 1000-issue cap, finite-number rejection | closed |
| T-02-08 | Diagnostics leak unstable internals | Stable codes, entity IDs, attributes, and deterministic sorting | closed |
| T-02-09 | Temporary files remain after failure | Exact-path cleanup in `finally` with failure tests | closed |
| T-02-10 | NaN, Infinity, or overflow reaches geometry | Strict JSON parsing plus recursive semantic finite-number check | closed |

## Accepted Risks

- The in-memory Python API does not impose transport-size limits. Phase 6
  deployment must enforce request quotas before calling it.
- Finite coordinates and dimensions currently have no product maximum.
  Schema-required positivity and deployment resource limits are sufficient for
  Phase 2; domain maxima require a later product decision.

## Implementation Evidence

- Destination sentinels survive validation, verifier, output, and path-conflict
  failures.
- Reopened temporary IFC receives schema and EXPRESS validation.
- Same-class invalid entities each retain a normalized diagnostic identity.
- Long elements receive extent-aware non-overlapping synthetic placement.
- `NaN`, `Infinity`, `1e400`, and unrepresentable huge integers are rejected
  before IFC generation.
- `python -m pytest tests -q` reports `142 passed`.

## Sign-Off

- [x] All High threats have automated evidence.
- [x] All threats have a disposition.
- [x] Accepted residual risks are documented with future ownership.
- [x] `threats_open: 0` confirmed.

**Approval:** verified 2026-06-11
