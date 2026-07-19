---
phase: 08-l1-l2-evaluation-contract
status: complete
created: 2026-07-19
requirements:
  - VAL-01
  - VAL-02
  - VAL-03
  - VAL-04
  - VAL-05
---

# Phase 8 Research: L1/L2 Evaluation Contract

## Recommendation

Evolve evaluation as a new versioned domain contract rather than adding more
booleans to `compare.py`. Keep `compare_ifc_models` and the Window geometry
measurement as reusable evidence producers, but normalize their output through
one status/check/level/run model. Register an immutable operation evaluation
policy beside the existing operation capabilities. Make production and
benchmark modes share policy and comparison code while accepting different
authorized evidence sources.

## Current State and Delta

Current `text2ifc/ifc-repair-evaluation/0.1` computes
`complete_repair_success` from application validity, postconditions,
damaged-vs-repaired preservation, and each operation adapter's `valid` boolean.
This already provides strong L1 ingredients:

- normalized before/after snapshots independent of STEP order;
- unexpected GlobalId change detection;
- Window geometry, placement, void/fill, containment, volume, duplicate-chain,
  and tolerance checks;
- immutable evidence packaging and Provider-private manifest exclusion.

The missing delta is structural, not merely additional checks:

- no five-state outcome algebra;
- no explicit L1/L2/L3 hierarchy;
- no independent three-source authorization of changed scope;
- no operation-owned L2 policy or applicability classification;
- no typed evidence precedence for production;
- no evaluator-only Ground Truth interface or public/private report projection;
- no honest aggregate failure when L1 passes but L2 does not.

## Proposed Contract Architecture

### 1. Immutable evaluation domain

Add frozen records for `EvaluationStatus`, `EvidenceFact`, `CheckResult`,
`LevelResult`, `OperationEvaluation`, and `RepairEvaluation`. Serialize only
through a canonical schema-backed function. Recommended new version:
`text2ifc/ifc-repair-evaluation/0.2`.

Status aggregation must be a small pure function with a frozen truth table:

| Child result | Mandatory | Parent effect |
|---|---:|---|
| passed | yes/no | satisfied |
| not_required | no, policy-declared | satisfied but disclosed |
| failed | yes/no | failed |
| partial | yes/no | partial/non-passing |
| not_evaluable | yes/no | non-passing for mandatory facts |

L3 is constructed with `not_required` at the level boundary; observations can
still contain matched/different/unavailable evidence.

### 2. Operation evaluation policy

Extend `OperationDefinition` with an optional typed `evaluation_policy` field
and expose a stable `require_evaluation_policy` failure for operations that are
evaluated under 0.2. Keep it out of the callable capability list: policy is
immutable data, while the existing `comparison_adapter` remains the
operation-specific measurement hook.

An `OperationEvaluationPolicy` should bind:

- policy ID/version and operation type;
- allowed created/modified/removed roles and IFC classes for L1;
- L1 check IDs and tolerance references;
- L2 semantic fact specifications with `required`, `conditional`, or
  `informational` applicability;
- permitted evidence source kinds and value comparison rules;
- public projection/redaction behavior.

### 3. L1 three-way authorization

Do not use `application_result.changes` as the sole allowed-change authority.
Build three sets and report each:

1. policy-authorized effects from Registry roles/classes/relations;
2. ChangeSet-declared target/scope and operation intent;
3. actual before/after changes plus Applicator role mapping.

The actual set must be explainable by both policy and declared intent. The role
mapping proves which newly generated GUID represents opening/window/relations;
the independent model diff proves what really changed. Mismatches become named
L1 checks rather than exceptions or hidden list differences.

### 4. Typed L2 evidence resolution

Reuse Phase 7's extraction semantics and IfcOpenShell utilities:

- `ifcopenshell.util.element.get_psets(..., should_inherit=True, verbose=True)`
  for typed Psets and quantities;
- `get_material` / `get_materials` for inherited and instance material facts;
- `get_type` and `get_container` for Type/Storey;
- IFC associations for classifications, retaining referenced source/name/
  identification and relationship provenance.

Resolve one `SemanticExpectation` per policy fact. Every expectation includes
source kind, source path/entity, expected typed value, applicability, and
provenance. Compare it with a separately extracted repaired fact.

Evidence precedence is deterministic:

1. explicit request;
2. surviving target/Host/Type facts;
3. compatible approved Prototype/Type;
4. deterministic operation policy;
5. private original only in benchmark mode.

Private original is not a production fallback. Nearby elements and name-based
guessing are never authorized.

### 5. Material/Pset conditional rule

The user's clarification is best represented as applicability computation, not
a loose best-effort check:

```text
if authorized source contains Material/Pset/Classification fact:
    applicability = conditional_activated
    repaired missing -> failed
    repaired mismatched -> failed
    repaired equivalent -> passed
else:
    status = not_required
```

If an always-required fact lacks any reliable expected value, its status is
`not_evaluable`, not `not_required`. This distinction prevents the conditional
rule from weakening Type/Host/Storey or explicit user requirements.

### 6. Benchmark privacy boundary

Introduce separate input types:

- `ProductionEvaluationInputs`: request facts, damaged/current IFC, changeset,
  application result, repaired IFC, policy registry;
- `BenchmarkEvaluationInputs`: production inputs plus private original IFC and
  private mutation role mapping.

Only the benchmark evaluator can import/read the private mapping. It emits a
private detailed report first, then a deterministic public projection that
removes Gold-only expected/actual values, IDs, paths, and canary strings while
retaining check IDs, statuses, categories, and remediation needs.

The public report should be built from an allowlist, not by recursively deleting
known private keys. Tests should seed unique canary IDs/values and scan every
Provider/public artifact.

## Compatibility and Integration

- Keep evaluation 0.1 parsing as a compatibility adapter; do not label old
  booleans as proven L2 outcomes.
- `audit.py` remains pre-application validation. Phase 8 evaluation remains
  post-application and independently reopens IFC.
- `workflow.py` should call the new evaluator only after successful application
  and write public/private files into separate evidence locations.
- Preserve existing callers that inspect `complete_repair_success`, but derive
  it from the new strict aggregation.
- Phase 9 consumes `terminal_status` and `successful_artifact_publishable`;
  Phase 10 changes authoring until Window L2 passes.

## Key Pitfalls

1. **Gold leakage through reports:** Provider exclusion alone is insufficient;
   public evaluation/report/manifest artifacts can also leak original IDs or
   values. Use allowlist projection and whole-bundle canary scans.
2. **Treating missing conditional facts as pass:** `not_required` must include
   evidence that no activating source existed.
3. **Treating mandatory unknowns as optional:** missing expected value for an
   always-required check is `not_evaluable` and non-passing.
4. **Trusting the Applicator:** actual IFC diff remains authoritative for what
   changed; Applicator output is role evidence only.
5. **Overloading L2 with L3:** exact GUID, STEP order, representation tree, and
   authoring placement construction must stay observational.
6. **Breaking 0.1 evidence:** add a new schema/reader rather than mutating old
   semantics in place.
7. **Accidentally fixing Phase 10:** Phase 8 must report current Window semantic
   loss honestly, not add Pset/material authoring to make its test green.

## Validation Architecture

### Test layers

1. **Contract unit tests:** schema versions, five statuses, canonical
   serialization, aggregation truth table, 0.1 compatibility.
2. **Policy/evidence unit tests:** policy validation, conditional activation,
   typed comparison, source precedence, Prototype compatibility, prohibited
   inference.
3. **L1 integration fixtures:** controlled extra/missing/modified roots,
   topology/containment errors, duplicate chain, and tolerance boundaries.
4. **Privacy integration fixtures:** private canary original/manifest values,
   detailed private report, allowlisted public projection, full artifact scan.
5. **LargeBuilding acceptance:** existing Window case produces L1 pass, honest
   L2 non-pass, L3 not-required, complete false, zero Provider calls.
6. **Regression:** all `tests/ifc_repair`, compileall, schema checks, and source
   IFC immutability.

### Sampling strategy

- Each TDD plan starts with a focused RED file and runs it after every commit.
- Each wave runs all Phase 8 focused files.
- Final acceptance runs the complete IFC repair suite and compileall.
- LargeBuilding is not in the fastest feedback loop; controlled fixtures keep
  unit feedback under 15 seconds.

## Planning Implications

Use four sequential TDD plans:

1. evaluation 0.2 domain/schema/status aggregation;
2. operation L2 policy and typed evidence resolution;
3. independent L1 authorization/preservation integration;
4. benchmark privacy, workflow projection, LargeBuilding acceptance, and docs.

Plans 2 and 3 both depend on Plan 1. They should remain sequential because both
touch operation definitions/aggregation boundaries and parallel edits would
create avoidable registry conflicts. Plan 4 depends on all preceding contracts.
