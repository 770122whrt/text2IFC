# Phase 12 Stage 1 Scope Correction — Frozen Contract

**Created:** 2026-08-18
**Status:** FROZEN after user approval of the generic `unsupported_requests`
design
**Applies to:** Phase 12 correction checkpoint before Plan 12-15 is retried
**Authority:** This document supplements `12-SPEC.md`, `12-CONTEXT.md` and
`12-VALIDATION.md`. It may make Stage 1 stricter but may not weaken or redesign
their frozen Door/Window, geometry, Storey, Ground Truth, transaction or Proof
contracts. Any conflict is a hard stop for user discussion.

## 1. Trigger and allowed claim

The first genuine Phase 12 DeepSeek run passed its zero-skip offline preflight
but did not produce a publishable case:

- a complete Beam/Column request emitted the noncanonical section token
  `rectangular` and stopped as `STRUCTURAL_SECTION_UNSUPPORTED`;
- a clarification/resume request used `target_query.storey_name` to name the
  target `IfcBuildingStorey`, so deterministic target resolution returned no
  candidate;
- a request to add a physical Beam and also attach a structural-analysis node
  omitted the only existing reject marker, fell into missing-geometry
  clarification and did not return the expected
  `STRUCTURAL_ANALYSIS_UNSUPPORTED` guard.

All raw attempts remain failed live evidence. They may not be relabelled,
overwritten or curated as success. A later same-case pass is reliability and
Phase-closure viability evidence, not blind capability-improvement evidence.
The largest allowed claim from this checkpoint is **bug fixed** unless the
separately frozen Baseline/Candidate protocol proves more.

## 2. Root cause and invariant

Stage 1 is not a pure classifier. Its one Provider response both selects an
operation profile and extracts target, geometry, semantics and unsupported
intent. Stage 2 receives selected full profiles and few-shots only after Stage
1, completeness, capability and target-resolution gates have succeeded.
Therefore Stage 2 cannot repair an underspecified Stage 1 contract.

The violated invariant is:

> The compact Stage 1 contract must be self-contained and exact for every
> value that Stage 1 must emit or reject. The repair Agent must preserve and
> explicitly reject every requested action outside registered IFC repair
> operations; it may never silently drop it, turn it into a clarification, or
> approximate it as supported work.

Structural-analysis members, nodes, loads, ports and analytical connectivity
have never been Phase 12 authoring features. They are out-of-scope requests
used only to prove the repair Agent fails closed.

## 3. Frozen architecture

The existing call graph remains:

```text
public repair request
  -> Stage 1: one call, compact profiles, route + extract RepairIntent
  -> deterministic scope/completeness/capability/target/semantic resolution
  -> Stage 2: selected full profiles + selected few-shots only
  -> deterministic bind/apply/reopen/L0/L1/L2/preservation/publication
```

This checkpoint does not add a Stage 1A/1B call, a deterministic keyword
router, all-profile Stage 1 few-shot injection, an LLM alias normalizer, or a
retry that treats an unsupported request as supported.

## 4. RepairIntent 0.6 scope channel

Add new, append-only contracts:

- `text2ifc/ifc-repair-intent-body/0.6`;
- `text2ifc/ifc-repair-intent/0.6`;
- prompt template `ifc-repair-intent.v0.6`.

Existing 0.1–0.5 files and registry records remain byte-for-byte historical
contracts. The current public `RepairAPI` moves to 0.6; tests may explicitly
request earlier versions for compatibility regression only.

The 0.6 Stage 1 body has a required root array `unsupported_requests`. It is
empty for an in-scope request. At least one of `operations` or
`unsupported_requests` must be non-empty.

Each item has exactly this semantic shape:

```json
{
  "unsupported_id": "unsupported-1",
  "kind": "registered_capability",
  "operation_id": "beam-1",
  "capability_id": "structural_analysis_node",
  "source": {
    "source_kind": "user_request",
    "reference": "request:/text",
    "excerpt": "attach a structural analysis node"
  }
}
```

Fields are closed and canonical:

- `kind` is exactly `registered_capability` or `unregistered_action`;
- `registered_capability` requires an `operation_id` that exists in the same
  body and a `capability_id` listed by that operation's selected checked-in
  profile;
- `unregistered_action` requires `operation_id=null` and
  `capability_id="unregistered_operation"`;
- `source` is one public provenance object quoting only the user request;
- unknown kinds, capability synonyms, invented operation IDs, wrong nesting
  and extra keys fail Stage 1 validation. They are not normalized.

For Phase 12 structural profiles, the exact registered capability IDs are:

- `structural_analysis_member`;
- `structural_analysis_node`;
- `structural_analysis_load`;
- `structural_analysis_port`;
- `structural_analysis_connection`.

They all map deterministically to `STRUCTURAL_ANALYSIS_UNSUPPORTED`. One or
more items from only that family retain that reason code. Multiple unsupported
families return `REPAIR_REQUEST_CONTAINS_UNSUPPORTED_ACTIONS` with the complete
validated item list. A sole `unregistered_action` returns
`REPAIR_REQUEST_OUT_OF_SCOPE`.

## 5. Scope-gate priority and atomicity

After Stage 1 JSON/schema/profile binding succeeds, the runtime checks
`unsupported_requests` before:

1. required-parameter completeness;
2. clarification generation;
3. target or Type resolution;
4. property retrieval;
5. Stage 2;
6. compiler/applicator mutation.

Any non-empty `unsupported_requests` array terminates the whole public request.
A mixed request such as “add a Beam and attach an analysis node” may preserve
the Beam operation for evidence, but no supported subset is executed. Required
Beam geometry may be omitted because scope rejection intentionally precedes
completeness. The source IFC hash and bytes remain unchanged; Stage 2 and
publication counts are zero.

A pure unrelated request may have `operations=[]` and one or more
`unregistered_action` records. It terminates with
`REPAIR_REQUEST_OUT_OF_SCOPE`; it does not fabricate an IFC operation.

## 6. Versioned Beam/Column compact profiles

Do not rewrite `beam.add` or `column.add` profile 0.1 or their few-shots. Add
new checked-in profile IDs `beam.add.v0.2` and `column.add.v0.2`, new bound
few-shot IDs/files, new prompt-registry hashes, and bind production
`add_beam`/`add_column` definitions to the v0.2 profiles.

Stage 1 still receives only their compact projections. Stage 2 still receives
only the full profiles and few-shots selected by the validated RepairIntent.

### 6.1 Canonical section intent

The Stage 1 section-shape schema accepts only these exact tokens:

- `rectangle` — the only executable Phase 12 shape;
- `round_section`;
- `i_section`;
- `h_section`;
- `arbitrary_section`;
- `variable_section`.

The latter five are preserved only so deterministic capability checking can
reject them before mutation. `rectangular`, case variants, aliases and
explanatory strings are schema-invalid and receive bounded schema feedback;
they are never converted to `rectangle` by program code.

The final executable parameter schema remains `shape == "rectangle"`.

### 6.2 Canonical Storey target intent

For `add_beam` and `add_column`, the target object is the
`IfcBuildingStorey` itself. Their new registry-bound Stage 1 target schema:

- fixes `allowed_ifc_classes` to `['IfcBuildingStorey']`;
- permits the target Storey's own `global_id` or `names` selectors;
- requires at least one of those two selectors;
- forbids `storey_name` and `storey_global_id` for this target operation;
- permits no synonym or relocated selector.

Thus “on Level 1” is represented as `names: ["Level 1"]`.
`storey_name` retains its existing global meaning as a containment filter for
an element target; no resolver compatibility special case is added and the
frozen Storey policy is unchanged.

The generic operation registry gains an optional `intent_target_schema`
parallel to `intent_parameter_schema`. Request-stage rendering and validation
consume it without Beam/Column branches in common orchestration.

## 7. Stage 1 prompt boundary

`ifc-repair-intent.v0.6` must state plainly:

- this Agent interprets only operation types present in
  `SUPPORTED_OPERATIONS` for IFC repair;
- it does not perform structural analysis, calculation, export, messaging,
  document generation or any other unregistered task;
- it must not silently omit an extra requested action;
- registered but unsupported capabilities use the exact selected profile's
  capability ID in `unsupported_requests`;
- wholly unregistered actions use `unregistered_action`;
- any unsupported item stops the whole atomic request before Stage 2;
- missing facts in an otherwise in-scope repair clarify, while out-of-scope
  actions reject. These states must never be conflated.

The Prompt must not include project identities, source STEP, mutation recipes,
private Gold or expected target answers.

## 8. Frozen public seams and failure family

No production change begins until RED tests prove the following through the
agreed public seams.

### 8.1 Stage seam: `generate_repair_intent`

- complete Beam and Column bodies use `rectangle`, Storey `names`, and empty
  `unsupported_requests`;
- the rendered compact contract contains the v0.2 profile IDs, exact shape
  tokens, exact Storey selector rule and structural-analysis capability IDs;
- no Beam/Column full few-shot body appears in Stage 1;
- `rectangular`, `storey_name` on a Storey target, unknown capability IDs,
  wrong nesting and extra fields fail closed;
- a registered structural-analysis request and a wholly unrelated request both
  produce valid, auditable 0.6 bodies rather than missing-parameter
  clarification.

### 8.2 Public full-chain seam: `RepairAPI.start` / resume

- repair-only complete requests can reach Stage 2 and publish only after the
  existing strict gates;
- repair-only incomplete requests retain grouped clarification/resume;
- Beam/Column plus analysis member/node/load/port/connection each terminates
  before completeness and Stage 2 with
  `STRUCTURAL_ANALYSIS_UNSUPPORTED`;
- supported plus unrelated action rejects atomically;
- a pure unrelated request rejects without a fabricated operation;
- malformed Provider output follows the existing bounded correction/failure
  policy and never becomes an unsupported success;
- every rejected case proves Stage2=0, apply=0, publication=0 and exact source
  immutability.

### 8.3 Failure-family slices frozen before GREEN

The pre-fix family includes:

- positive: Beam, Column and mixed Beam+Column complete requests;
- clarification: missing axis/section only, with no unsupported action;
- registered negative: analysis member, node, load, port and connection;
- geometry negative: round/I/H/arbitrary/variable section and curved/Grid
  placement remain deterministic capability rejections;
- boundary: pure unsupported, supported+unsupported, multiple unsupported
  families and unknown capability token;
- cross-scene: d7n and vvo public-path execution with group-isolated evidence;
- Provider failures: malformed, truncated and schema-invalid Stage 1 output;
- safety: source immutability, private-Gold isolation, no Stage 2 and no partial
  publication for every unsupported request.

Tests must use independent expected literals and public behavior, not derive
expected values from the implementation under test.

## 9. Validation and live retry policy

Before another real Provider call, all applicable Stage seams, the complete
public fake/replay chain, Phase 12 offline matrix, relevant historical
Door/Window regressions, complete reached repair tests, `compileall` and
`git diff --check` must pass with zero failure, skip, timeout or substitution.
The machine-readable preflight must remain in the new run lineage.

The prior failed live directory remains append-only failure evidence. A new
timestamped DeepSeek run uses the frozen Plan 12-15 matrix and actual transport;
synthetic, cached, prerecorded and hand-authored fallback remain prohibited.
If another canonical or scope-contract defect appears, stop before retry or
curation and discuss it with the user.

Only a new run whose complete and clarification/resume cases publish, reopen
as IFC2X3 and independently pass L0/L1/L2/preservation/isolation may enter
Proof. The unsupported guard must retain Stage1=1, Stage2=0, no mutation and
the exact deterministic reason. Plan 12-16 remains conditional on those
results.

## 10. Explicit non-goals

This checkpoint does not:

- implement structural analysis nodes, members, loads, ports or connections;
- add a structural-analysis operation or ChangeSet authoring path;
- accept aliases from observed LLM output;
- move fields or normalize wrong nesting;
- split Stage 1 into extra Provider calls;
- load every full profile/few-shot into Stage 1;
- change Door/Window workflow, geometry thresholds, Type/material policy,
  Ground Truth isolation, Storey containment policy, evaluator tolerances or
  Proof acceptance;
- begin Phase 13.

## 11. Git and evidence boundary

Contract, RED, GREEN, Prompt/Profile/schema, live evidence, Proof curation and
Phase closure use separate scoped checkpoints where practical. Unrelated
dataset-source organization, PDFs and documentation cleanup already present in
the dirty worktree are excluded. Failed live evidence is preserved and never
mixed into an accepted Proof directory.
