# Phase 11 Validation Strategy

**Date:** 2026-07-28
**Status:** Complete — deterministic, real DeepSeek and independent Proof gates passed on 2026-07-31
**Requirements:** OPS-01, OPS-02
**Policy:** Offline deterministic closure first; real DeepSeek only after all
offline blocking gates pass.

## 1. Quality claims

Phase 11 must prove six independent claims:

1. **Routing correctness** — natural-language actions are classified into the
   registered operation/profile without loading unrelated full few-shots.
2. **Authority correctness** — no target, Type, occurrence value or generated
   Type fact is used without exact public authority or deterministic policy.
3. **IFC authoring correctness** — Opening/Door geometry and relationships are
   valid IFC2X3 and survive serialization/reopen.
4. **Atomicity** — single, batch and mixed requests publish all operations or
   none.
5. **Fidelity/preservation** — every required L1/L2/occurrence fact passes and
   unrelated model content is preserved.
6. **Provider viability** — real DeepSeek can complete one full path and one
   bounded clarification path without synthetic fallback.

One aggregate “success” flag is insufficient. Reports retain:

- `geometry_relationship_success`;
- `semantic_fidelity_success`;
- `occurrence_fidelity_success`;
- `global_preservation_success`;
- optional diagnostic `authoring_exactness`.

Publication requires the first four.

## 2. Test layers

## 2.1 Layer A — schema and pure policy tests

Fast, synthetic, no IFC file and no Provider network.

Coverage:

- RepairIntent 0.5/body 0.5 round trip;
- routing/profile schema and hash validation;
- profile-operation-target cross-check;
- compact versus full profile projections;
- conditional missing slot logic;
- dimension meaning;
- viewpoint/swing rules;
- supported/unsupported feature classification;
- Semantic Manifest 0.3 and ChangeSet 0.4;
- compatibility parsing for all historical versions.

Target runtime: under 15 seconds.

Example command:

```powershell
python -m pytest `
  tests/ifc_repair/test_repair_intent_v05.py `
  tests/ifc_repair/test_operation_prompt_profiles.py `
  tests/ifc_repair/test_selected_provider_profiles.py `
  tests/ifc_repair/test_changesets.py -q
```

## 2.2 Layer B — index and deterministic resolution

Synthetic IFC2X3 fixtures plus small checked-in models; no Provider.

Coverage:

- Opening extraction and SQLite round trip;
- empty versus filled Opening;
- host and Storey traversal;
- Opening dimensions and wall-relative position;
- DoorStyle formal attributes and representation summary;
- stale 0.3 index rejection/rebuild;
- exact GUID/name Wall, Opening and DoorStyle resolution;
- ambiguous target/Type clarification;
- every supported position form;
- viewpoint side resolution;
- generated/exact Type compatibility;
- unsupported replacement/complex generation rejection.

Target runtime: under 45 seconds.

Example command:

```powershell
python -m pytest `
  tests/ifc_repair/test_opening_index.py `
  tests/ifc_repair/test_door_resolution.py `
  tests/ifc_repair/test_indexer.py `
  tests/ifc_repair/test_index_store.py `
  tests/ifc_repair/test_resolution_flow.py -q
```

## 2.3 Layer C — operation application

Synthetic IFC2X3 models; no Provider.

Coverage:

- extracted Window hosted-opening behavior remains green;
- opening-only operation;
- Door + new Opening;
- Door + surviving Opening;
- exact Type reuse unchanged;
- generated left/right/explicit `NOTDEFINED` Type;
- deterministic visual representation;
- Storey containment;
- Type/fill/void relationships;
- requested scalar Pset/quantity authoring;
- serialization and reopen;
- stable failure and zero publication.

Target runtime: under 90 seconds.

Example command:

```powershell
python -m pytest `
  tests/ifc_repair/test_hosted_opening_primitives.py `
  tests/ifc_repair/test_opening_application.py `
  tests/ifc_repair/test_door_application.py `
  tests/ifc_repair/test_door_type_authoring.py `
  tests/ifc_repair/test_window_application.py `
  tests/ifc_repair/test_apply_transaction.py -q
```

## 2.4 Layer D — L1/L2/fidelity and atomic integration

Synthetic and compact dataset fixtures; no Provider.

Coverage:

- Opening-only L1/L2;
- Door L1/L2;
- occurrence comparison 0.2;
- exact occurrence properties/quantities;
- Type-only versus occurrence-reuse authority;
- mixed Door/Window non-overlap;
- mixed Door/Window overlap failure;
- five-Door batch success;
- one injected operation failure rolls back all;
- private benchmark difference never changes production publication;
- full-model preservation.

Target runtime: under 180 seconds for compact suite.

Example command:

```powershell
python -m pytest `
  tests/ifc_repair/test_door_evaluation.py `
  tests/ifc_repair/test_door_occurrence_fidelity.py `
  tests/ifc_repair/test_mixed_hosted_operation_atomicity.py `
  tests/ifc_repair/test_phase11_dataset_e2e.py -q
```

## 2.5 Layer E — full repository regression

Run after each implementation plan and again before live UAT:

```powershell
python -m pytest tests/ifc_repair -q
python -m compileall -q src tests scripts
git diff --check
```

No live Provider call may begin while any command is red.

## 2.6 Layer F — real DeepSeek UAT

Explicitly network/provider-backed and executed only after Layer E passes.

Required cases:

1. complete Door + Opening request;
2. incomplete Door request → one bounded clarification → completed request;
3. unsupported complex generated style rejected by program logic before
   Stage 2.

The complete case should use one successful Stage 1 and one successful Stage
2 call. The clarified case may use Stage 1, one user/fixture clarification
answer and the resumed Stage 1/Stage 2 path. Schema-correction retries are
reported and cannot be hidden.

UAT evidence must include:

- redacted request/response transport;
- model, token and attempt metadata;
- rendered prompt and renderer input;
- selected profile/few-shot IDs, versions and hashes;
- RepairIntent, clarification state and answer;
- resolved operations;
- Semantic Manifests and bound ChangeSet;
- application, reopen, L1/L2/fidelity/preservation results;
- final status and reason code;
- explicit `synthetic_fallback_used: false`.

## 3. Requirement-to-test traceability

| Requirement | Blocking tests/evidence |
|---|---|
| OPS-01 | opening profile/routing; Wall target resolution; opening-only apply; void/no-fill postcondition; L1/L2; mixed atomic case |
| OPS-02 | Door profiles/routing; exact/generated Type; viewpoint/dimension clarification; new/surviving Opening apply; Door L1/L2; occurrence fidelity; batch/mixed; live UAT |

## 4. Contract acceptance matrix

| Case | Expected |
|---|---|
| valid RepairIntent 0.5 | parses, preserves routing provenance |
| RepairIntent 0.4 fixture | still parses unchanged |
| routing profile names another operation | `OPERATION_PROFILE_MISMATCH` |
| profile/few-shot hash mismatch | fail closed before Provider |
| Door quantity uses `door_occurrence` | Manifest 0.3 / ChangeSet 0.4 valid |
| same scope in Manifest 0.2 | rejected without modifying 0.2 schema |
| generated Door Type derivation | preserved and validated by factory |
| Provider attempts to supply template | rejected/ignored as non-authoritative |
| ChangeSet 0.3 Window proof | still validates/applies |
| Draft 0.2 Door geometry | binder upgrades to bound ChangeSet 0.4 |

## 5. Clarification and capability matrix

| Input condition | Expected terminal behavior before Stage 2 |
|---|---|
| “add a 900 × 2100 door” with no dimension meaning | one clarification containing width/height meaning |
| explicit “900 × 2100 opening” | no dimension clarification |
| new generated left/right Door without viewpoint | `DOOR_VIEWPOINT_REQUIRED` clarification |
| exact reused valid DoorStyle, no extra swing request | no swing clarification |
| exact Type operation conflicts with explicit swing | one preserve-Type/cancel-reuse clarification |
| no Type and no operation, user did not accept unknown | `DOOR_OPERATION_REQUIRED` clarification |
| user explicitly accepts unspecified operation | generated `NOTDEFINED` |
| asks for generated sliding/double Door | `DOOR_GENERATED_STYLE_UNSUPPORTED`, no Stage 2 |
| asks for unimplemented transom/hardware authoring | `DOOR_REQUESTED_FEATURE_UNSUPPORTED`, no Stage 2 |
| optional material/transom/hardware omitted | proceed without asking |
| existing Opening is already filled | `OPENING_ALREADY_FILLED`, no mutation |
| request is replacement/deletion/reposition | `DOOR_REPLACEMENT_UNSUPPORTED`, no mutation |

All missing blocking slots for one operation should be grouped into one
clarification. Unstated optional slots must not appear.

## 6. Geometry/topology matrix

| Operation | Required created/modified topology |
|---|---|
| `add_opening_to_wall` | one Opening, one void relation, host reference; no filling |
| `add_door_with_opening_to_wall` | one Opening, one Door, one void, one fill, Storey containment, Type binding |
| `fill_existing_opening_with_door` | one Door, one fill, Storey containment, Type binding; existing Opening/void retained |

For every applicable case:

- exactly one host Wall;
- exactly one fill relation for a Door;
- Door geometry projected into Opening-local coordinates overlaps the Opening
  by at least `0.95`;
- authorized nominal Door-envelope/Opening center deviation is at most
  `5 mm`, axis deviation at most `0.1°`, and nominal width/height deviation at
  most `1 mm`; the actual Type geometry is reported separately because valid
  frames may extend beyond the nominal opening envelope;
- Door Storey is resolved from the Opening world-base elevation within the
  same Building, not copied from a multi-storey Wall's direct containment;
- wall-local 2D region within the Wall;
- sibling regions do not overlap;
- local placement/orientation survives reopen;
- no duplicate deterministic GUID;
- no unauthorized removal.

## 7. Type and semantic matrix

## 7.1 Exact Type reuse

Verify:

- exact object GlobalId reused;
- Type STEP content/fingerprint unchanged;
- existing `OperationType` reported honestly;
- RepresentationMaps referenced without mutation;
- Type Psets/materials/classifications inherited as effective facts;
- no occurrence Pset copied unless separately authorized.

## 7.2 Generated Type

Verify:

- deterministic GlobalId for same source/request/operation/template;
- different operation produces a distinct Type;
- allowed `IfcDoorStyle.OperationType` only;
- template ID/version/hash present in bound derivation;
- simplified representation reopens and is associated with the Door;
- internal visual parameters do not appear as user-authorized L2 facts;
- unsupported enum or tampered derivation fails before creation.

## 7.3 Occurrence facts

Verify:

- explicit Door Pset/Quantity values are authored on the Door occurrence;
- exact/natural property resolution does not invent a value;
- explicit authorized occurrence reuse produces isolated new relations;
- Type reuse wording alone does not copy occurrence facts;
- Wall/Opening/Storey/placement/identity facts are derived or omitted;
- any wrong required value blocks semantic/occurrence success.

## 8. Atomicity and failure injection

Required injections:

1. second Door overlaps first Door;
2. Door overlaps Window on same Wall;
3. one target fingerprint or Type identity is stale;
4. one generated Type derivation is tampered;
5. one existing Opening becomes filled after resolution;
6. one semantic assignment has unsupported value type;
7. one postcondition deliberately fails;
8. one evaluation check deliberately reports mismatch.

For each:

- `published=false`;
- no output IFC path exists;
- damaged/source SHA-256 is unchanged;
- no partial success file is copied to Proof;
- terminal reason identifies the first stable blocking layer;
- per-operation evidence shows which operations had not been committed.

## 9. Dataset acceptance

## 9.1 LargeBuilding single Door

Damage: remove one Door/Opening chain.
Request: natural-language complete dimensions/position plus exact Type reuse
and explicit occurrence package where full replication is being tested.

Required:

- original, damaged and repaired IFC reopen;
- report lists removed Door name, GlobalId and Type;
- topology, Type and requested occurrence facts pass;
- production L1/L2/fidelity/preservation pass;
- private Ground Truth comparator explains every remaining difference.

## 9.2 vvo surviving Opening

Damage: remove Door and fill relation, preserve valid Opening and void.
Request: identify the surviving Opening and restore one Door.

Required:

- original Opening GlobalId retained;
- no second Opening/void created;
- Door operation/viewpoint correct;
- exact/generated Type policy honored;
- production and private comparison pass or report precise unsupported facts.

Authority addendum (2026-07-30):

- production executes in a separate process that cannot accept original IFC,
  mutation manifest or deleted-object identity;
- the public request and RepairIntent may identify an empty Opening through a
  bounded width/height/depth/wall-local-center/sill geometry signature;
- five retained Openings resolve without GlobalId, object Name, Storey Name or
  host GUID and receive exactly one Door/fill each;
- original IFC and private mutation mapping are introduced only after the
  repaired IFC exists, for the private comparator;
- any undeclared added IFC Root is a blocking preservation failure.

## 9.3 Generated Type case

No Type intent. Use complete operation/viewpoint and overall Opening
dimensions.

Required:

- dedicated deterministic system DoorStyle;
- no project Type chosen by similarity;
- correct formal enum;
- deterministic visual representation;
- all blocking gates pass.

## 9.4 Five-Door batch

Damage five independent Door targets and restore through one request.

Required:

- one RepairIntent, one bound ChangeSet, five operation results;
- one publication;
- five independent L1/L2/fidelity results;
- injected failure proves rollback;
- report lists all removed Door names/IDs/Types.

## 9.5 Mixed Door/Window

At least two Door and two Window additions/repairs in one request.

Required:

- selected profile union contains only used families;
- one unified ChangeSet;
- cross-family non-overlap;
- all independent gates pass;
- one cross-family overlap fixture fails atomically.

## 9.6 AdvancedProject

One Door operation on the 44-MB source.

Required:

- complete production preservation, not sampling;
- cold and warm request-to-publication runs;
- each at or below 180 seconds;
- process-tree peak RSS at or below 4 GiB;
- cache hit/miss evidence;
- no reduced validation scope.

## 10. Token-efficiency evidence

For one Door-only, one Window-only and one mixed request, record:

- compact Stage 1 catalog bytes/tokens;
- selected full profile/few-shot bytes/tokens;
- Stage 2 total input tokens;
- names/hashes of profiles excluded from each prompt;
- full-registry baseline estimate.

Blocking correctness does not depend on a fixed percentage saving, but Phase
11 must prove unrelated full few-shots are absent. A report should state the
measured token difference rather than claim an estimated innovation.

## 11. Proof package layout

Curated accepted cases:

```text
dataset/processed/proof/ifc-repair-success-cases/door/
  single/
  surviving-opening/
  generated-type/
  batch/
  mixed/
  large-model/
```

Each case contains:

```text
README.md
manifest.json
original.ifc
damaged.ifc
repaired.ifc
request.txt
repair-intent.json
resolved-operations.json
semantic-manifest*.json
bound-changeset.json
application.json
evaluation.json
occurrence-comparison.json
global-comparison.json
ifc-validation.json
provider-evidence/        # only for live cases, redacted
private-evaluation/       # never referenced by provider inputs
```

`manifest.json` binds every artifact by SHA-256 and records source path/hash,
operation count, publication status, removed Door names/IDs/Types and tool
versions.

Ephemeral retries remain under ignored
`dataset/processed/ifc-repair/`. Only accepted, source-bound, redacted evidence
is copied to Proof.

## 12. Completion gate

Phase 11 may be marked complete only when:

- all five implementation-plan summaries exist;
- OPS-01 and OPS-02 traceability is complete;
- all offline layers are green;
- historical Window proofs and ChangeSet 0.3 remain green;
- all six dataset cases are accepted or an honest blocker is recorded;
- real DeepSeek complete and clarified requests publish valid IFC without
  fallback;
- unsupported complex generation is rejected before Stage 2;
- full test, compile and diff checks pass from a clean worktree;
- Phase 11 changes are committed in a scoped Git checkpoint.

### 12.1 Executed closure evidence

| Gate | Result |
|---|---|
| Real Provider | PASS — `deepseek-openai-compatible` / `deepseek-v4-flash`; `synthetic_fallback_used=false` |
| Complete Door | PASS — Stage 1/2 = 1/1; published IFC reopened as IFC2X3; strict L0/L1/L2 |
| Clarification/resume | PASS — total Stage 1/2 = 2/1; one public `missing_required_parameter` clarification; strict L0/L1/L2 |
| Unsupported capability | PASS — Stage 1/2 = 1/0; exact `DOOR_OPERATION_TYPE_UNSUPPORTED` |
| Accepted live run | `dataset/processed/proof/phase11-live-uat/uat-20260731T224900289758Z/` |
| Curated live success Proof | Two `provider_evidence_mode=live` surviving-Opening Door cases |
| Collection verifier | PASS — 16 cases, 45 operations, 247 files, 48 IFC2X3 reopens |
| Independent audit coverage | 11 cases strictly recomputed; 5 historical Window cases explicitly `legacy_artifact_only` |
| Changed-surface regression | PASS — 78 tests |
| Proof collection tests | PASS — 5 tests |
| Complete IFC repair regression | PASS — 688 passed, 1 expected skip in 1099.76 seconds |
| Repository-wide attempt | 1599 tests collected; no failure before the 1204-second command timeout. This is recorded as timeout, not as a full-suite pass. |

The accepted live run followed three earlier rejected runs. Those failures were
used to correct exact prompt/schema guidance and two deterministic evidence
boundaries. No compatibility aliases were added for
`center_offset_from_wall_start_mm`, relocated `opening.center_offset_mm`, or
`door.threshold_height_mm`; the active Door v0.2 profiles instead require the
frozen canonical paths and omit program-derived fields from Stage 1.

## 13. Pre-execution plan review

Planning self-check completed on 2026-07-28:

| Check | Result |
|---|---|
| GSD frontmatter validation | PASS for 11-01 through 11-05 |
| GSD plan-structure validation | PASS; five plans, 15 executable tasks, zero warnings |
| Requirements | OPS-01 and OPS-02 appear in every plan and remain pending until evidence |
| Dependency order | 11-01 → 11-02 → 11-03 → 11-04 → 11-05 |
| Historical compatibility | Explicit tests in 11-01, 11-03, 11-04 and 11-05 |
| Offline-before-live | Enforced by 11-05 dependency and live task preconditions |
| Private/public boundary | Threat and test coverage in all five plans |
| Dataset coverage | LargeBuilding, vvo, generated Type, five-Door, mixed and AdvancedProject |
| Product decisions | No unresolved product blocker; fixed in 11-CONTEXT and 11-SPEC |

The sequential dependency is deliberate for the first Door expansion: it
avoids parallel edits to Registry, schemas, authoring and evaluation while the
common Window path is being extracted. Later component families may parallelize
once these extension seams are proven.
