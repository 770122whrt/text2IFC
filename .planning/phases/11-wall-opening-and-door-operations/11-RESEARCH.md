# Phase 11 Research: Wall Opening and Door Operations

**Date:** 2026-07-28
**Status:** Complete for planning
**Scope:** Local codebase, installed IfcOpenShell 0.8.5, and checked-in IFC2X3 datasets
**Requirements:** OPS-01, OPS-02

## 1. Recommendation

Implement Door and opening-only behavior as registered operation families on
top of a shared hosted-opening primitive. Do not duplicate
`operations/window.py`, and do not put Door/Window branches into common
orchestration.

The implementation should make five additive changes:

1. add RepairIntent routing and versioned prompt profiles;
2. extend the rebuildable SQLite index with Opening and formal DoorStyle facts;
3. extract shared Wall–Opening geometry/topology and register three operations;
4. generalize semantic scope, L1/L2 and occurrence-fidelity dispatch through
   Registry metadata;
5. prove single, batch, mixed, large-model and real DeepSeek paths.

The critical contract consequence is that Phase 11 needs Semantic Manifest
0.3 and Bound ChangeSet 0.4. Existing 0.2/0.3 schemas enumerate only
`window_occurrence` and `opening_occurrence`; changing them in place would
silently alter immutable historical contracts.

## 2. Sources inspected

### 2.1 Current production path

- `src/text2ifc_ifc_repair/request_stage.py`
- `src/text2ifc_ifc_repair/provider_stage.py`
- `src/text2ifc_ifc_repair/repair_intent.py`
- `src/text2ifc_ifc_repair/resolution_flow.py`
- `src/text2ifc_ifc_repair/registry.py`
- `src/text2ifc_ifc_repair/audit.py`
- `src/text2ifc_ifc_repair/apply.py`
- `src/text2ifc_ifc_repair/production_evidence.py`
- `src/text2ifc_ifc_repair/semantic_authoring.py`
- `src/text2ifc_ifc_repair/occurrence_fidelity.py`
- `src/text2ifc_ifc_repair/benchmark_evaluation.py`

### 2.2 Existing Window operation and index

- `src/text2ifc_ifc_repair/operations/window.py`
- `src/text2ifc_ifc_repair/operations/occurrence_property.py`
- `src/text2ifc_ifc_repair/type_templates.py`
- `src/text2ifc_ifc_repair/index_models.py`
- `src/text2ifc_ifc_repair/index_adapters.py`
- `src/text2ifc_ifc_repair/indexer.py`
- `src/text2ifc_ifc_repair/index_store.py`
- `src/text2ifc_ifc_repair/target_query.py`
- `src/text2ifc_ifc_repair/target_context.py`

### 2.3 Contracts

- RepairIntent 0.1 through 0.4 and body schemas;
- Semantic Manifest 0.1 and 0.2;
- Bound ChangeSet 0.2 and 0.3;
- ChangeSet draft 0.2;
- intent and ChangeSet prompts through v0.4/v0.3;
- prompt registry fingerprints.

### 2.4 Dataset evidence

| Model | Path | Door evidence relevant to Phase 11 |
|---|---|---|
| LargeBuilding | `dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc` | 18 Doors, three styles, right-swing and double-door formal operations |
| vvo | `dataset/ifc/train/vvo.ifc` | 26 Doors, 23 styles, left/right/double/`NOTDEFINED` variation |
| AdvancedProject | `dataset/external/bim-whale-ifc-samples/AdvancedProject/IFC/AdvancedProject.ifc` | 126 Doors, 14 styles, large-model preservation target |
| px4 | `dataset/ifc/test/px4.ifc` | 12 Doors, ten styles, compact secondary regression model |

All sampled Doors fill an Opening, every sampled Opening voids a host, sampled
Doors are contained in a Storey, and sampled Doors have a formal Type binding.
These are dataset observations, not universal IFC assumptions.

## 3. What can be reused unchanged

### 3.1 Public orchestration

`api.py`, `cli.py`, `orchestrator.py`, run state, terminal publication and
artifact layout already treat one request as a resumable transaction. They
should receive new operation capabilities without a Door-specific public
entrypoint.

### 3.2 Unified ChangeSet transaction

`audit_changeset()` and `apply_changeset()` already:

- bind source/request fingerprints;
- audit before mutation;
- apply all operations in memory;
- suppress publication on audit, application or postcondition failure;
- serialize to a temporary file;
- reopen as IFC2X3 before atomic publication.

The transaction model is correct. Phase 11 extends dispatch metadata and
cross-operation conflict grouping; it does not add a second Door ChangeSet.

### 3.3 Target and Type authorization

The Phase 7/09.1 SQLite path already supports exact GUID, aliases, Storey,
Space, host, grid, direction, geometry capability and exact Type
authorization. Door should use the same deterministic resolver. Similarity can
offer candidates, but it cannot authorize a Type.

### 3.4 Property knowledge and occurrence semantics

Phase 10.1/10.2/10.5 already separate:

- understanding a property name;
- authorizing its value;
- deciding occurrence versus Type ownership;
- binding provenance;
- authoring isolated scalar Psets/quantities;
- evaluating effective occurrence facts.

Door scalar Psets and quantities should enter this path by adding a
`door_occurrence` scope, not by introducing a Door-only property subsystem.

### 3.5 Full-model preservation

Comparator 0.2 and validation caching already meet the large-model
preservation requirement. AdvancedProject acceptance must reuse the complete
gate and its current 180-second / 4-GiB budget rather than introduce a reduced
“fast Door gate.”

## 4. Gaps found in the current implementation

## 4.1 Prompt selection is not operation-bounded

`request_stage._supported_operations()` serializes every operation contract
into Stage 1. `provider_stage.generate_bound_changeset()` also serializes all
registered operation contracts into Stage 2. As Beam and Column are added,
token usage and cross-family confusion grow.

The selected-profile design must therefore be real runtime behavior:

- Stage 1 receives all compact routing/slot projections, but not every full
  few-shot;
- each RepairIntent operation names one profile;
- the program validates profile ↔ operation ↔ target-class consistency;
- clarification, resolution and Stage 2 receive only the referenced profiles;
- prompt artifacts record exactly which profile/few-shot hashes were loaded.

There is no extra Provider call. Stage 1 performs routing and partial
extraction in one response.

## 4.2 RepairIntent has no family/action routing

RepairIntent 0.4 has operation type, query, parameters and semantic intent, but
no explicit component family/action/profile record. A new version is required
because routing must be schema-bound and provenance-bearing.

The new field belongs to each operation. A mixed request can therefore carry,
for example:

```text
door.add-with-opening
window.add-with-opening
occurrence.set-properties
```

in one RepairIntent and later one ChangeSet.

## 4.3 Required-parameter logic cannot express conditional Door rules

`OperationRegistry.missing_required_parameters()` derives missing paths only
from JSON Schema `required`. Door requirements are conditional:

- width/height meaning may be known or unknown;
- an existing Opening may supply overall dimensions;
- a reused Type may supply formal operation;
- a generated Type needs resolved swing or explicit `NOTDEFINED`;
- left/right needs a viewpoint, while an exact reused Type may not.

Add an operation-level intent policy checker and deterministic parameter
resolver. JSON Schema continues to reject malformed supplied values; the
checker returns stable missing/unsupported/conflict diagnostics based on
target/Type evidence.

## 4.4 Index lacks Opening records and DoorStyle formal facts

The default adapter registry indexes Wall, Door, Window and Space, not
`IfcOpeningElement`. Current Door/Window records expose filling and host IDs,
but a surviving empty Opening is not queryable as a first-class target.

`TypeRecord` stores common Type labels and properties but not the formal
IfcDoorStyle fields:

- `OperationType`;
- `ConstructionType`;
- `ParameterTakesPrecedence`;
- `Sizeable`;
- representation-map availability/fingerprint.

Index 0.4 should add:

- `OpeningIndexAdapter`;
- opening host, filling IDs, empty/filled state, Storey, dimensions and
  wall-relative placement evidence;
- a bounded formal-attributes map on TypeRecord;
- bounded representation summary/fingerprint;
- exact SQLite persistence and round-trip tests.

The index is a derived cache. A 0.3 database opened by 0.4 code must fail with
`INDEX_SCHEMA_VERSION_MISMATCH` and be rebuilt.

## 4.5 Window operation contains reusable hosted-opening primitives

`operations/window.py` currently combines:

- parameter schemas and evaluation policy;
- wall-region preconditions;
- overlap checks;
- deterministic IDs;
- Opening geometry and placement;
- voids/fills/containment authoring;
- Type binding;
- Window geometry;
- postconditions and comparison.

Copying this file for Door would duplicate Wall placement, overlap and
relationship behavior. Extract only family-neutral behavior into
`operations/hosted_opening.py`:

- canonical rectangular footprint;
- wall bounds and sibling-opening conflict checks;
- deterministic role IDs;
- Opening representation/placement;
- void relationship;
- Storey lookup and containment helper;
- common topology inspection;
- common geometric measurements.

Window remains responsible for Window schema, entity, Type, semantic policy
and comparison. Door remains responsible for Door schema, swing, Type,
representation and Door checks.

## 4.6 Cross-family overlap checking is currently incomplete

`audit.py` groups prior operations by `(operation_type, target_id)`. A Door and
a Window on the same Wall are therefore not compared even if their openings
overlap.

Operation definitions need a conflict domain such as `hosted_opening`.
Operations in the same domain and host must compare canonical 2D wall-local
footprints regardless of filling class. Opening-only, Door and Window then use
one conflict checker; unrelated operation families keep their existing
behavior.

## 4.7 Semantic application hard-codes Window scopes

`apply.py` currently iterates:

```text
window_occurrence → policy.semantic_role
opening_occurrence → opening
```

Semantic Manifest 0.2 and Bound ChangeSet 0.3 also enumerate only these two
scopes. Door cannot be added safely by mapping it to
`window_occurrence`.

Add Registry metadata:

```text
semantic_scope_roles:
  door_occurrence: door
  opening_occurrence: opening
```

and publish additive Semantic Manifest 0.3 / Bound ChangeSet 0.4 schemas with
`door_occurrence`. Common application and evaluation must iterate the
registered mapping.

## 4.8 Generated Type template evidence is currently discarded

`resolution_flow.generated_type_authority()` creates an authority payload with
`template_version`, `ifc_class` and `template`. In
`production_evidence.py`, the resulting `relationship:type` fact preserves
only the GlobalId, class and template version in provenance.
`type_templates.ensure_bound_type()` then hard-codes `IfcWindowStyle` and
cannot reconstruct Door `OperationType`.

For Phase 11:

1. generated-Type template builders receive the resolved operation;
2. the canonical template is hashed and included in the generated authority;
3. the binder preserves the bounded template in the assignment `derivation`;
4. the registered Type factory checks class, template ID/version and allowed
   enum values before creating an IFC entity;
5. the applicator never accepts arbitrary Provider-supplied template content.

This is why Bound ChangeSet 0.4 is required even though Provider draft 0.2 can
remain unchanged.

## 4.9 Type factory is Window-only

`ensure_bound_type()` creates only `IfcWindowStyle`. It should become a
generic dispatcher using the current operation definition:

- exact existing Type: require the expected IFC Type class and return it
  unchanged;
- deterministic generated Type: validate the compiler-owned derivation and
  call the registered factory;
- missing exact Type: fail;
- Provider-defined Type template: reject.

Generated Door factory output is limited to:

- `SINGLE_SWING_LEFT`;
- `SINGLE_SWING_RIGHT`;
- explicit `NOTDEFINED`.

The first release does not generate double/sliding/folding/revolving/rolling
styles and does not scale an existing Type.

## 4.10 Fidelity and benchmark code still names Window

`occurrence_fidelity.py` exposes Window-specific schema/function names, and
benchmark role mapping contains Window assumptions. Preserve the historical
Window 0.1 report but add a family-neutral occurrence comparison 0.2 contract
and Registry-driven role mapping. Door and Opening use the new contract;
Window regressions must continue to pass.

## 4.11 Damage generation is Window-only

`mutation.py` supports one Window chain and Window batches. Phase 11 needs two
Door damage modes:

- remove Door, fill relationship and Opening/void relationship;
- remove Door and fill relationship while retaining a valid empty Opening.

The private mutation manifest must capture removed Door name, ID, Type,
formal operation, occurrence property/quantity facts, Opening, Wall, Storey
and damage scope. It remains evaluator-only and never enters Provider input.

## 5. IFC2X3 semantic findings

The installed IfcOpenShell schema reports:

### IfcDoor occurrence

Relevant occurrence attributes include:

- `GlobalId`, `OwnerHistory`, `Name`, `Description`, `ObjectType`, `Tag`;
- `ObjectPlacement`, `Representation`;
- `OverallHeight`, `OverallWidth`.

An `IfcDoor` fills an `IfcOpeningElement` through `IfcRelFillsElement`. The
Opening voids a host through `IfcRelVoidsElement`. Door spatial containment
uses the host Storey in the sampled models.

### IfcDoorStyle

Relevant formal fields are:

- `OperationType`;
- `ConstructionType`;
- `ParameterTakesPrecedence`;
- `Sizeable`;
- inherited `HasPropertySets` and `RepresentationMaps`.

`Name` is not formal swing authority. A name containing “left” or “right”
cannot repair an `OperationType=NOTDEFINED` fact.

### Panel and lining properties

`IfcDoorPanelProperties` and `IfcDoorLiningProperties` can describe panel,
lining, threshold and transom details. These are not all mandatory for an
ordinary repair. Phase 11 treats them as optional supported/unsupported
features, not blanket clarification requirements.

The deterministic generated visual template may use internal panel/frame
display parameters, but those parameters are compiler policy unless the user
explicitly supplies a supported construction fact.

## 6. Canonical public parameter model

Use one normalized operation parameter model after clarification/resolution.
Provider input remains closer to user wording; the deterministic resolver
produces the executable form.

### 6.1 Opening dimensions

```json
{
  "overall_width_mm": 900,
  "overall_height_mm": 2100,
  "source_meanings": {
    "width": "overall_opening",
    "height": "overall_opening"
  }
}
```

Accepted source meanings:

- `overall_opening`;
- `clear_passage`;
- `door_leaf`;
- `rough_opening`;
- `unknown`.

Only `overall_opening` is directly executable for a new opening. Other
meanings are preserved and clarified unless a future registered deterministic
formula has every authorized input. For an existing Opening,
`fit_existing_opening=true` derives executable dimensions from current IFC
evidence.

### 6.2 Position

Public forms:

- center offset from a named Wall end;
- nearest-edge offset from a named Wall end;
- Wall midpoint;
- exact existing Opening.

Canonical executable form:

```json
{
  "reference": "wall_local_start",
  "center_offset_mm": 1050,
  "derivation": {
    "source_anchor": "south_end",
    "source_measure": "nearest_edge",
    "formula_id": "edge-to-center/0.1"
  }
}
```

Project coordinates are rejected. Grid remains a target selector.

### 6.3 Swing

Generated Door canonical form:

```json
{
  "operation_type": "SINGLE_SWING_RIGHT",
  "viewpoint": {
    "from_space_global_id": "...",
    "toward_space_global_id": "..."
  },
  "swing_destination_space_global_id": "..."
}
```

The resolver proves viewpoint sides through reliable space evidence or a
deterministic geometry side test. It records evidence and never asks the
Provider to compute transforms.

## 7. Prompt-profile architecture

Add one checked-in profile schema and these initial profiles:

| Profile ID | Operation |
|---|---|
| `window.add-with-opening` | existing Window operation |
| `opening.add-to-wall` | opening-only |
| `door.add-with-opening` | Door + new Opening |
| `door.fill-existing-opening` | Door + existing empty Opening |
| `occurrence.set-properties` | generic occurrence scalar authoring |

Each profile contains:

- `profile_id`, version, family and action;
- linked operation type and target classes;
- compact Stage 1 classification terms and slot summary;
- required, conditional, optional and program-derived slots;
- forbidden inference rules;
- supported and unsupported feature codes;
- Stage 2 projection contract;
- few-shot IDs and content hashes.

Few-shots are stored separately from the compact catalog. Every Door geometry
profile has complete, clarification, exact-Type-reuse and unsupported-feature
examples. Sentinel identities may never be treated as public project facts.

## 8. Recommended Registry seams

Extend `OperationDefinition` with bounded declarative metadata and hooks:

| Field/hook | Purpose |
|---|---|
| `prompt_profile_id` | links operation to one checked-in profile |
| `semantic_scope_roles` | maps manifest scopes to applicator result roles |
| `conflict_domain` | enables mixed-family hosted-opening overlap checks |
| `intent_policy_checker` | conditional missing/unsupported/conflict checks |
| `parameter_resolver` | canonicalizes public parameters with index evidence |
| `generated_type_factory` | creates a validated compiler-owned Type |

Keep the existing operation callbacks for context, precondition, application,
postcondition and comparison. Avoid a growing central `if family == ...`
dispatcher.

The default Registry must validate at construction time:

- profile exists and names the same operation;
- target classes agree;
- semantic scopes are non-empty and unique;
- generated Type template/factory are paired;
- conflict-domain operations expose canonical footprints.

## 9. Evaluation design

### 9.1 Opening-only

Blocking:

- Opening exists and IFC reopens;
- exactly one voids relation to the selected Wall;
- requested dimensions/position;
- region within Wall and no overlap;
- no filling element;
- full-model preservation.

Opening Psets/quantities are conditional on bound authority.

### 9.2 Door

Blocking L1:

- correct new/existing Opening;
- one voids relationship and one fills relationship;
- Door Storey containment;
- dimensions, placement and orientation;
- Type binding;
- formal operation semantics when required;
- compatible generated/mapped geometry;
- no overlap or unauthorized mutation.

Blocking L2:

- type, host and Storey relationships;
- `OverallWidth`, `OverallHeight`;
- generated/reused formal operation evidence;
- Width, Height and Area quantities;
- every explicit or deterministic semantic assignment.

Occurrence fidelity uses the existing five classifications. L3 identity,
STEP, byte order and representation-node equality remain diagnostic.

### 9.3 Mixed atomicity

At least two Door and two Window operations must:

- route to the correct selected profiles;
- share one source/request fingerprint;
- bind into one ChangeSet;
- perform cross-family footprint checks;
- publish once only after every independent L1/L2 result passes;
- publish nothing after one injected failure.

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Prompt token growth returns when more families are added | Stage 1 compact catalog; selected full profiles only after routing; record token/profile evidence |
| Door handedness is geometrically reversed | require viewpoint; formal Type operation or deterministic side evidence; orientation tests from both Wall directions |
| Shared Type is modified | exact reuse is reference-only; generated Type gets a new deterministic identity; fingerprint existing Type before/after |
| Existing Type geometry is scaled silently | compare size/operation evidence; clarify on conflict; no Sizeable shortcut |
| Door-specific branches spread through common code | Registry scope/conflict/profile/factory metadata; plan acceptance rejects central family branches |
| Generated template becomes semantic invention | distinguish compiler visual parameters from authored facts; only bound facts enter L2 |
| Private Ground Truth leaks into Provider input | retain canaries; mutation manifest stays evaluator-only; assert provider payload paths/hashes |
| Large model regresses | reuse complete preservation gate; retain 180 s / 4 GiB limits; cold/warm evidence |
| Old success cases break | preserve all historical schemas and Window tests; run full IFC repair suite before live UAT |

## 11. Implementation sequence

1. **Contracts and prompt routing** — freeze additive versions and selected
   profile behavior first.
2. **Index and deterministic resolution** — make Opening and DoorStyle facts
   queryable before application.
3. **Hosted-opening and Door authoring** — extract shared primitives and add
   three registered operations.
4. **Evaluation and mixed atomicity** — remove Window-only semantic/fidelity
   assumptions and prove rollback.
5. **Dataset and DeepSeek acceptance** — only after the offline matrix is
   green.

This sequence prevents Provider behavior from masking deterministic
application or evaluation defects.

## 12. Planning conclusion

No unresolved product decision remains from the design discussion. The
implementation can proceed with these fixed policies:

1. additive contract versions: RepairIntent 0.5, Index 0.4, Semantic Manifest
   0.3 and Bound ChangeSet 0.4;
2. simplified deterministic generated Door representation, not
   manufacturer-level reconstruction;
3. real DeepSeek UAT runs only after all offline gates pass and reports honest
   failure without fallback.
