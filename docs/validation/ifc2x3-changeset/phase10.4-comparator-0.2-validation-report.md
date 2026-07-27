# Phase 10.4 Comparator 0.2 Validation Report

**Date:** 2026-07-24; follow-ups through 2026-07-26
**Outcome:** Comparator gate passed. A narrowly scoped evaluator-alignment
follow-up then made the saved AdvancedProject five-Window repair publishable
without another Provider call or any ChangeSet modification. The later
IfcOpenShell validation-delta gate also passed correctness, while exposing a
large-model latency regression that remains open.

## What was fixed

The former comparator expanded and serialized large representation trees once
per product. On `AdvancedProject.ifc` this kept Production evaluation running
for more than 15 minutes.

Comparator 0.2 now uses two safe layers:

1. Equal aligned STEP records are used only as a fast certificate for locating
   potentially affected graph regions.
2. Every candidate root is confirmed with a typed, schema-aware semantic
   fingerprint. STEP identifiers are never used as cross-file identity.

Non-root entity hashes are memoized within one immutable model, so shared
`IfcRepresentationMap` and other shared resources are calculated once.
Ordered IFC aggregates retain order; SET/BAG aggregates are normalized.

## Fail-closed behavior

The comparator returns no preservation pass when it encounters:

- an empty or duplicate root `GlobalId`;
- a non-finite or unsupported canonical value;
- an incomplete comparison or 120-second timeout.

Production L1 converts these integrity failures to mandatory
`not_evaluable` scope checks. The legacy file-comparison entry point also
returns `complete_preservation_success: false` rather than raising and being
mistaken for success.

## Measured AdvancedProject result

Input scale:

- damaged IFC: 769,814 entities and 47,072 roots;
- repaired IFC: 770,044 entities and 47,114 roots.

The five original Windows removed by the deterministic Damage step were:

| # | Original `IfcWindow.Name` |
|---:|---|
| 1 | `BALANS Fixed Single Window:BALANS 10M FLOOR (SH = 0):916922` |
| 2 | `BALANS Fixed Single Window:BALANS 10M FLOOR (SH = 0):919838` |
| 3 | `BALANS Fixed Single Window:BALANS 10M BATHROOM:960189` |
| 4 | `BALANS Fixed Single Window:BALANS 20M FLOOR (SH = 0):773593` |
| 5 | `BALANS Fixed Single Window:BALANS 30M FLOOR (SH = 0):781498` |

Batch mutation reports now expose these names as
`removed_windows[].name`, ordered by `target_id`.

| Run | Comparator | Open + compare | Peak RSS | Result |
|---:|---:|---:|---:|---|
| 1 | 40.097 s | 51.764 s | 1.083 GB | 42 created / 5 modified / 0 removed |
| 2 | 39.638 s | 50.878 s | 1.081 GB | 42 created / 5 modified / 0 removed |
| 3 | 39.234 s | 50.683 s | 1.082 GB | 42 created / 5 modified / 0 removed |

The median comparator time is 39.638 seconds; the maximum peak RSS is
1,082,695,680 bytes. The agreed budgets were 120 seconds and 4 GiB.

All detected root effects were accepted by the existing ChangeSet/Registry
scope policy. In particular, the optimized comparator did not weaken the
global preservation gate.

## Ground-Truth authoring-gap audit

The root-count differences are attributable to the five damaged
Window/Opening chains, not unrelated model loss:

- the five original Windows owned 65 occurrence-direct `IfcPropertySet`
  objects; the repaired Windows owned four, one `Pset_WindowCommon` for each of
  operations 2-5, hence the repaired file has 61 fewer PropertySets;
- the originals owned five Window and five Opening `BaseQuantities` objects;
  the repair recreated the five Window quantities but no Opening quantities,
  hence the repaired file has five fewer `IfcElementQuantity` objects;
- approved Type reuse still supplies many effective Type properties, so root
  ownership counts must not be treated as the number of missing semantic
  values. The remaining effective occurrence gap is 28-30 properties per
  repaired Window.

The saved natural-language request does not authorize full Ground-Truth
replication. Operation 1 declares no properties; operations 2-5 declare only
`Pset_WindowCommon.IsExternal` and `Pset_WindowCommon.Reference`. Therefore,
the current case proves functional geometry/relationship repair and authorized
L2 semantics, not complete occurrence authoring.

The stronger target remains:

```text
complete authorized natural-language description + damaged IFC
  -> geometry/relationships/effective occurrence semantics equivalent to original IFC
```

Byte-for-byte STEP identity and an identical internal authoring graph remain
deferred authoring-exactness concerns. Future Ground-Truth debugging should
classify each difference as missing from the user text, unsupported authoring,
wrong value, or ownership-only, rather than silently ignoring it.

## Initial Full Production replay (2026-07-24)

A fresh replay reused the saved real DeepSeek ChangeSet without another
Provider call. Application passed and produced a reopened IFC. The complete
command finished in approximately 117.6 seconds, below the 180-second budget.

The final Production result is nevertheless **failed**, not publishable:

- all five Window operations failed their distinct L1 geometry-fit check;
- operations 3-5 each missed 14 inherited material facts;
- operations 1-2 passed L2;
- global created/modified/removed/relationship scope checks all passed.

This distinction matters: Phase 10.4 removes the evaluation scalability
blocker. It does not relabel a geometrically or semantically failing repair as
successful.

## Minimal evaluator-alignment replay (2026-07-25)

The two remaining failures were confirmed as evaluator/evidence-model
false negatives rather than IFC application failures:

1. The approved mapped Window Type represents its physical frame 10 mm inside
   the opening boundary. L1 previously required the Window body and opening to
   have identical bounding-box edges. L1 now accepts this existing authored
   pattern only when the mapped body is contained, centred, and its nominal
   `OverallWidth`/`OverallHeight` still match the requested opening. The
   generated non-mapped template continues to require exact edges.
2. Operations 3-5 have occurrence-direct material associations. IFC effective
   material resolution gives those associations precedence over materials on
   the bound Type. Production evidence and saved-manifest replay now use the
   same precedence. When no direct association exists, the Type material
   remains effective, preserving the operations 1-2 behavior.

The same saved real DeepSeek ChangeSet was reapplied to a freshly regenerated
damaged fixture. Its damaged-source SHA-256 matched the original live
transition. No Provider output was regenerated and no expected evidence was
copied from Ground Truth.

The follow-up command completed in approximately 94 seconds:

- deterministic application: passed and wrote a reopened IFC;
- global preservation/scope gate: passed;
- operations 1-5: each passed L1 and L2;
- final Production status: `passed`;
- publication: `true`.

This follow-up changes only how existing valid mapped geometry and IFC material
precedence are evaluated. It does not broaden target authorization, ChangeSet
scope, or semantic write permissions.

## Regression evidence

The complete IFC repair suite finished with:

```text
517 passed, 1 skipped in 219.27s
```

It includes the existing LargeBuilding and vvo batch end-to-end cases plus the
new fingerprint, shared-geometry, identity-integrity, timeout and STEP-shift
contracts.

## IFC schema-validation follow-up (2026-07-26)

IfcOpenShell validation is now available through one shared implementation:

- standalone mode requires an IFC with zero diagnostics;
- repair mode compares the damaged/source baseline with the repaired candidate
  and fails only when the candidate introduces a new diagnostic;
- the same delta check is a mandatory common L1 check named
  `l1.output.validation`;
- `scripts/ifc_repair/validate_ifc.py` exposes the check for debugging without
  running the Provider or applying a ChangeSet.

Baseline-aware comparison is required for real third-party IFCs. The saved
AdvancedProject five-Window ChangeSet was reapplied and evaluated without
another Provider call:

| Evidence | Result |
|---|---:|
| damaged baseline diagnostics | 286 |
| repaired candidate diagnostics | 286 |
| new diagnostics | 0 |
| resolved diagnostics | 0 |
| five operations L1/L2 | passed |
| global preservation | passed |
| publishable | true |

The end-to-end run took approximately 356 seconds, including about 46 seconds
for deterministic application and about 310 seconds for Production evaluation.
This is a correctness pass but a performance regression against the former
180-second full-run budget. Baseline diagnostic caching or a separately
budgeted validation pass is therefore required before claiming that validation
and Comparator 0.2 together meet the large-model latency target.

Example commands:

```powershell
# A newly authored standalone IFC must be intrinsically valid.
.venv\Scripts\python scripts\ifc_repair\validate_ifc.py candidate.ifc

# A repair of a pre-existing IFC must not introduce new diagnostics.
.venv\Scripts\python scripts\ifc_repair\validate_ifc.py repaired.ifc `
  --baseline damaged.ifc `
  --output validation-delta.json
```

## Artifacts

- `dataset/processed/ifc-repair/phase10.4-comparator-0.2/advanced-project-comparator-benchmark.json`
- `dataset/processed/ifc-repair/phase10.4-comparator-0.2/preflight-production-003/repaired.ifc`
- `dataset/processed/ifc-repair/phase10.4-comparator-0.2/preflight-production-003/application.json`
- `dataset/processed/ifc-repair/phase10.4-comparator-0.2/preflight-production-003/production-evaluation.json`
- `dataset/processed/ifc-repair/phase10.4-comparator-0.2/preflight-production-006-minimal-fix/repaired.ifc`
- `dataset/processed/ifc-repair/phase10.4-comparator-0.2/preflight-production-006-minimal-fix/application.json`
- `dataset/processed/ifc-repair/phase10.4-comparator-0.2/preflight-production-006-minimal-fix/production-evaluation.json`
- `dataset/processed/ifc-repair/phase10.4-comparator-0.2/preflight-production-007-validation-delta/repaired.ifc`
- `dataset/processed/ifc-repair/phase10.4-comparator-0.2/preflight-production-007-validation-delta/application.json`
- `dataset/processed/ifc-repair/phase10.4-comparator-0.2/preflight-production-007-validation-delta/production-evaluation.json`

## Handoff

The AdvancedProject five-Window case now closes the large-model Window path:
saved Provider output, deterministic ChangeSet application, scalable global
preservation, per-operation L1/L2 evaluation, and publication all complete.
Phase 11 operation-family expansion can be discussed next. L3 authoring
exactness remains explicitly deferred and is not implied by this L1/L2 pass.
