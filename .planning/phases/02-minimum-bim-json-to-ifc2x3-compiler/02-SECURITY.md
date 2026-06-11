# Phase 2 Security Design

**Created:** 2026-06-11
**Status:** Design complete; implementation pending

## Assets and Trust Boundaries

Assets:

- canonical BIM JSON input,
- existing destination IFC files,
- generated IFC artifacts,
- deterministic BIM-ID-to-GlobalId mapping,
- local filesystem paths and temporary files.

Trust boundaries:

- JSON enters through the Phase 1 validator,
- IfcOpenShell receives validated but still untrusted values,
- the compiler writes a temporary artifact before replacing a destination,
- verifier output is normalized before reaching users or tests.

## Threat Register

| ID | Threat | Severity | Required mitigation | Planned evidence |
|---|---|---:|---|---|
| T-02-01 | Invalid input overwrites a valid IFC | High | Validate before output work; sibling temp plus `os.replace` only after verification | Sentinel output tests |
| T-02-02 | Partial or invalid IFC is exposed after compiler failure | High | Reopen and schema-verify temp artifact; always clean temp on failure | Injected verification failure |
| T-02-03 | Path confusion writes outside the requested destination | Medium | Resolve destination parent; create temp only in that parent; never derive paths from BIM IDs | CLI path tests |
| T-02-04 | Duplicate or colliding identities corrupt traceability | High | Phase 1 uniqueness gate plus deterministic domain-separated UUIDv5; assert generated uniqueness | Repeat compile identity tests |
| T-02-05 | Unit confusion creates unsafe 1000x geometry | High | One reviewed mm-to-m boundary and reopened dimension tests for every family | Parameterized 1 mm tests |
| T-02-06 | Arbitrary predefined strings cause invalid IFC enums | Medium | Allowlist compatible enums; use `NOTDEFINED` where mandatory; preserve source in pset | Custom value tests plus schema validation |
| T-02-07 | Resource exhaustion from huge inputs or geometry | Medium | Retain 10 MiB file input limit; schema requires finite explicit arrays; document deployment limits | Existing CLI limit regression |
| T-02-08 | Validator diagnostics leak unstable internals | Low | Stable issue codes, paths, entity IDs, deterministic sort; omit memory addresses | Negative verifier snapshot tests |
| T-02-09 | Temporary files remain after failure | Medium | `try/finally` cleanup using exact resolved temp path | Failure-path filesystem tests |

## Security Invariants

1. No output path is touched before canonical validation succeeds.
2. Destination replacement occurs only after in-memory and reopened validation
   both succeed.
3. Required hierarchy, references, dimensions, and properties are never
   synthesized from defaults.
4. Mandatory IFC bookkeeping values such as `NOTDEFINED` are used only where
   the IFC2X3 schema requires them and do not replace source properties.
5. Original BIM JSON IDs remain recoverable even when IFC enums cannot encode
   source vocabulary.
6. No BIM JSON string is interpreted as a filesystem path, Python expression,
   or IfcOpenShell class name.

## Phase Exit Gate

Phase 2 cannot be marked complete while any High threat lacks an automated
test. The final security verification must rerun the complete compiler suite
and inspect atomic-output, unit, identity, and enum handling directly.

