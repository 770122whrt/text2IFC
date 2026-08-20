# Phase 12 Stage 1 Clause-Role Correction — Frozen Design

**Created:** 2026-08-20

**Status:** FROZEN after user approval of Scheme 2

**Applies to:** Phase 12 Plan 12-15 retry and Plan 12-16 closeout

**Authority:** This document supplements `12-SPEC.md`, `12-VALIDATION.md`,
`12-STAGE1-SCOPE-CORRECTION-SPEC.md`, and
`12-TYPE-INTENT-CORRECTION-SPEC.md`. It may only clarify how Stage 1 classifies
request clauses. It may not change registered repair operations, frozen
Door/Window behavior, structural geometry, Type/material authority, Storey
policy, Ground Truth isolation, evaluator thresholds, or publication
atomicity.

## 1. Trigger and retained evidence

The genuine DeepSeek run
`dataset/processed/ifc-repair-runs/phase12-live/uat-20260820T103415722873Z`
passed the required zero-skip offline preflight. Its clarification/resume and
program-guard cases passed. Its complete Beam+Column case did not reach Stage
2 because Stage 1 added this item beside two otherwise correct operations:

```json
{
  "kind": "unregistered_action",
  "operation_id": null,
  "capability_id": "unregistered_operation",
  "source": {"excerpt": "Create both in one atomic ChangeSet"}
}
```

The same response correctly selected `beam.add.v0.3` and
`column.add.v0.3`, emitted exact rectangle/Storey selectors, kept both
generated-Type `prototype_intent` values null, and preserved the two
LoadBearing property intents. The only violated invariant was classifying the
transaction clause as a third requested action.

The failed run remains append-only evidence. It is not overwritten, curated,
or re-labelled as success. No deterministic code may remove or reinterpret
the erroneous Provider item.

## 2. Root cause

`ifc-repair-intent.v0.7` says every requested action must become an
`operations` or `unsupported_requests` item, but it does not define an action.
It also tells Stage 1 to reject every request part outside the operation
registry or selected profile. A compatible transaction clause is not an IFC
operation capability, so the observed classification follows an ambiguous
Prompt boundary.

The Prompt's only inline shape example is a structural-analysis negative and
it contains the historical `beam.add.v0.2` profile ID. There is no positive
multi-operation transaction anchor. Existing offline tests use prepared
Provider JSON and therefore prove schema assembly and fail-closed behavior,
not natural-language clause classification.

## 3. Exact four-role clause contract

Stage 1 classifies request clauses by semantic role and semantic object, not
by the presence of an imperative verb.

### 3.1 Registered model operation

A clause is a separate `operations` item only when satisfying it changes IFC
entities, attributes, geometry, semantics, or relationships and the requested
change maps to one registered `operation_type`.

The current production registry contains:

- `add_beam`;
- `add_column`;
- `add_window_with_opening_to_wall`;
- `add_opening_to_wall`;
- `add_door_with_opening_to_wall`;
- `fill_existing_opening_with_door`;
- `set_occurrence_properties`.

This list documents the current release. The runtime compact operation catalog,
its checked-in profile hashes, and its exact schemas remain the executable
source of truth. A future registered operation does not require this Prompt to
enumerate a new negative list.

### 3.2 Operation content or modifier

A clause that supplies the target, geometry, Type intent, material, property,
quantity, or another registered field for an already extracted operation is
encoded inside that operation. It does not create another operation.

Examples include:

- `on Level 1` as the Beam/Column Storey target;
- center-axis points, rectangle dimensions, and Column orientation;
- generate a dedicated Type, reuse exact Type X, or request selection among
  existing Types;
- material and canonical or natural-language property intent;
- `state that the Beam is load bearing`, which requests an IFC property and is
  not a reporting task;
- `both` or `the same Storey` when those words refer to operations or targets
  already present in the request.

### 3.3 Compatible transaction or execution constraint

A clause is a compatible transaction constraint when it only states how
already requested operations are grouped, committed, rolled back, validated,
or published. Satisfying it alone changes no IFC entity, attribute, geometry,
semantic fact, or relationship.

The following semantic equivalents are frozen for this correction:

- in one atomic ChangeSet;
- in the same ChangeSet;
- in one transaction;
- together atomically;
- all-or-nothing;
- publish both/all or neither/none.

They create neither an operation nor an unsupported item. They are not
silently discarded: the exact public request remains bound by its request hash
and root provenance, while the existing applicator enforces one atomic
transaction for the whole request. No `transaction_constraints` field is
added to RepairIntent.

An anaphoric phrase such as `Create both in one atomic ChangeSet` refers to the
already extracted objects. The verb `Create` does not introduce a new semantic
object and therefore does not introduce a third action.

### 3.4 Unsupported requested result

A clause becomes `unsupported_requests` only when it asks for a distinct
result that is outside the registry or uses an exact capability listed as
unsupported by the selected compact profile.

- Registered-but-unsupported capability: retain the partial registered
  operation and bind the exact checked-in `capability_id` to that operation.
- Unregistered result or external task: use `unregistered_action`,
  `operation_id=null`, and `capability_id=unregistered_operation`.
- Any unsupported item still terminates the entire atomic request before
  completeness, Stage 2, mutation, or publication.

Representative unregistered tasks include rendering, reporting, export,
calculation, simulation, and unregistered delete/move/resize operations.
Representative registered negatives include structural-analysis objects and
profile-owned unsupported geometry.

These examples are intentionally not an exhaustive deny-list. The exact
runtime registry and each selected compact profile's
`unsupported_capabilities` are authoritative. A phrase absent from the examples
is classified by the four-role rule and then validated against that authority.

## 4. Compact Stage 1 teaching design

Stage 1 remains a single Provider call over all compact registered operation
profiles. It does not load full profiles or Stage 2 few-shots.

The append-only Prompt replaces the long, stale, negative-only inline JSON with:

1. one four-row clause-role decision table;
2. one explicit semantic-object rule;
3. three short output-shape examples, marked representative rather than
   exhaustive:

```text
Positive multi-operation transaction:
Beam + Column + one atomic ChangeSet
=> operations=[add_beam, add_column]
=> unsupported_requests=[]

Registered negative:
add Beam + attach structural analysis node
=> operations=[add_beam]
=> unsupported_requests=[registered_capability(add_beam,
   structural_analysis_node)]

Pure unregistered task:
render Level 1
=> operations=[]
=> unsupported_requests=[unregistered_action(unregistered_operation)]
```

The shapes teach category boundaries only. They do not replace the exact JSON
schema, compact operation catalog, or capability IDs, and their abbreviated
notation is never valid Provider output.

The Prompt must also distinguish natural-language input from canonical output:
the user may say `rectangular`, but Beam/Column Provider JSON must emit the
exact registered token `rectangle`. Likewise, user Storey wording is natural
language, while Stage 1 emits only the registered `names` or `global_id`
selector shape.

## 5. Append-only version contract

Historical registered Prompt and schema artifacts remain byte-for-byte
unchanged. Because the current implementation binds each RepairIntent contract
identity to one immutable Prompt template, add:

- `text2ifc/ifc-repair-intent-body/0.8`;
- `text2ifc/ifc-repair-intent/0.8`;
- Prompt template `ifc-repair-intent.v0.8`.

RepairIntent 0.8 has the same JSON shape and semantics as 0.7 except for the
clarified clause-role Prompt contract. It adds no field, alias, normalizer, or
Provider-output rewrite. Beam/Column remain bound to v0.3 profiles; all other
registered operations remain bound to their existing frozen profiles.

The production `RepairAPI`, Phase 12 live runner, curator, and independent
validator move to the exact 0.8 contract. Historical tests may request 0.1–0.7
explicitly.

## 6. Failure family and test seams

RED begins before production edits and uses independent expected literals.

### 6.1 Positive semantic classes

- single Beam and single Column complete requests;
- Beam+Column with each frozen transaction synonym;
- generated/exact-reuse/selection-required Type states as operation modifiers;
- LoadBearing wording as an IFC property modifier rather than reporting;
- missing supported geometry with empty unsupported list and downstream
  grouped clarification;
- one mixed Beam+Column+Window+Door atomic request whose four registered
  operations remain exactly four and whose unsupported list is empty;
- Window-only, Door-only, Opening-only, and occurrence-property historical
  public paths.

### 6.2 Negative semantic classes

- one representative exact capability from each structural unsupported family:
  geometry, Grid placement, and structural analysis;
- representative Door/Window unsupported cases are historical non-regressions,
  not redesigned contracts;
- pure unregistered render/report/export task;
- registered repair plus one unregistered task, preserving both evidence
  classes while rejecting the whole request;
- unknown capability, wrong nesting, extra key, `rectangular` Provider token,
  Storey selector alias, malformed and truncated Provider output.

The Prompt is not tested by asserting that every possible English negative is
listed. Instead tests assert the generic rule, representative shapes, complete
registry projection, exact capability authority, and behavior across sibling
phrases. The real DeepSeek UAT remains the only evidence that the actual model
applies the Prompt to natural language.

### 6.3 Full-chain and safety seams

- `generate_repair_intent` renders only compact profiles and v0.8 schema;
- `RepairAPI.start / continue_with_answer` proves complete,
  clarification/resume, registered negative, pure unregistered, and mixed
  rejection paths;
- Stage 2 loads only profiles selected by Stage 1;
- all current Door/Window request, resolution, application, reopen, L0/L1/L2,
  preservation, and mixed-transaction regressions pass;
- every rejected case proves Stage2=0, apply=0, publication=0, source
  immutability, and no private-Gold exposure;
- the fixed offline Phase 12 matrix, compile, diff, existing Proof validation,
  and full repository suite pass without skip, substitution, or timeout before
  another Provider call.

## 7. Real UAT and Proof policy

The next timestamped DeepSeek run uses the unchanged natural-language three-case
matrix through public `RepairAPI.start / continue_with_answer`. No test seam,
mock, replay, cache, prerecorded response, hand-authored response, or synthetic
fallback may enter live evidence.

If the complete, clarification/resume, and guard cases pass, the curator may
stage candidates and invoke the strict validator in a separate process. Only
independently reopened IFC2X3 artifacts that pass L0/L1/L2, global
preservation, private-Gold isolation, provenance, and IFCCompare may enter
accepted Proof.

If another semantic contract defect appears, retain the failed run and stop
before retry or curation for user discussion.

## 8. Explicit non-goals and unresolved clauses

This correction does not freeze new behavior for:

- negated external tasks such as `do not render`;
- user-specified execution ordering;
- conditional execution;
- count-only expansion such as three members without three axes;
- one global analytical request over multiple operations;
- a request to permit partial publication despite frozen atomicity.

If any such clause appears in required acceptance evidence, it is a new
contract ambiguity and the work stops for user discussion. This correction
also does not add a deterministic keyword router, split Stage 1, load full
few-shots into Stage 1, change Door/Window contracts, weaken geometry/Storey/
Type/material/Gold/evaluation policies, start Phase 13, or mix dataset/PDF/
documentation-organization work into Phase 12 commits.
