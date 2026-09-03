# Phase 11 Implementation Pattern Map

**Date:** 2026-07-28
**Purpose:** Map each Phase 11 artifact to the closest proven codebase pattern
**Constraint:** Extend registered capabilities; do not duplicate the Window
pipeline or introduce common Door/Window conditionals.

## 1. New artifact map

| New or changed artifact | Closest proven analog | Reuse | Required difference |
|---|---|---|---|
| RepairIntent 0.5 schemas | RepairIntent/body 0.4 | additive schema, parser compatibility, bounded fields | per-operation `routing_intent`; `door_occurrence` quantity scope |
| Prompt profile 0.1 schema/loader | prompt registry + operation registry | checked-in JSON, fingerprints, fail-closed validation | catalog/full projections and selected few-shots |
| Intent v0.5 prompt | intent v0.4 prompt | public-only Stage 1, correction feedback | compact routing catalog and profile cross-check |
| ChangeSet v0.4 prompt | ChangeSet v0.3 prompt | compact non-authoritative draft | only selected profiles/contracts |
| Semantic Manifest 0.3 | Semantic Manifest 0.2 | source kinds, provenance, derivation | Door scope and generated Type template derivation |
| Bound ChangeSet 0.4 | Bound ChangeSet 0.3 | deterministic binder, assignment embedding | new scope/version only; draft remains 0.2 |
| Opening index adapter | `FillingIndexAdapter` + `WallIndexAdapter` | relation extraction, geometry summary, diagnostics | targetable Opening, empty/filled state, host-relative position |
| TypeRecord formal facts | current `TypeRecord` and type tables | separate Type authority, exact identity | DoorStyle formal attributes and representation summary |
| `operations/hosted_opening.py` | reusable portions of `operations/window.py` | straight-wall geometry, overlap, IDs, Opening placement | filling-family neutral APIs |
| `operations/opening.py` | Window operation definition | Registry contract and L1 structure | no filling entity or Type |
| `operations/door.py` | Window operation definition | registry/apply/postcondition structure | DoorStyle, swing/viewpoint, fill-existing path |
| generated Door Type factory | `type_templates.ensure_bound_type()` | exact existing Type reuse | registered class-specific factory and derivation validation |
| Door semantic policy | Window evaluation policy | OperationEvaluationPolicy and SemanticFact | Door role/facts and formal operation |
| occurrence comparison 0.2 | Window occurrence comparison 0.1 | fact extraction/classification | family-neutral role/scope |
| Door mutation helpers | Window private mutation helpers | source-bound manifest, property/quantity snapshot | remove full chain or retain Opening |
| Phase 11 acceptance runner | Phase 10.3/10.5 runners | offline-first, proof packaging, performance record | Door/mixed matrices and selected-profile evidence |

## 2. Module responsibility boundaries

## 2.1 `registry.py`

Owns:

- operation capability declaration;
- prompt-profile linkage;
- conditional intent hook;
- deterministic parameter-resolution hook;
- semantic scope-to-role map;
- conflict domain;
- generated Type factory registration.

Does not own:

- Door slot semantics;
- Wall geometry formulas;
- IFC entity construction;
- family-specific evaluation facts.

Acceptance smell: adding Beam later must not require editing a central
Door/Window switch.

## 2.2 `prompt_profiles.py`

Recommended new module.

Owns:

- `PromptProfile` immutable model;
- checked-in JSON loading and schema validation;
- profile/few-shot SHA-256 verification;
- compact Stage 1 catalog projection;
- full selected profile projection;
- union and deterministic ordering;
- Registry cross-validation.

Does not own:

- Provider calls;
- target resolution;
- capability authorization beyond declared profile metadata.

## 2.3 `request_stage.py`

Keeps one Stage 1 Provider call.

Changes:

- render compact profile catalog;
- parse RepairIntent 0.5;
- cross-check routing against Registry/profile;
- replace Window-only created-occurrence folding with a registered generic
  fold policy or a family-neutral operation-link rule;
- write selected profile evidence.

Does not load full Door/Window few-shots before Stage 1 output.

## 2.4 `provider_stage.py`

Changes:

- calculate selected profile IDs from resolved operations;
- serialize only those operation contracts and full profile/few-shot payloads;
- record IDs, versions, hashes and estimated prompt size;
- bind Semantic Manifest 0.3 into ChangeSet 0.4.

The Provider still emits ChangeSet draft 0.2. It never emits IFC code,
semantic authority or generated Type derivation.

## 2.5 Index modules

`index_adapters.py` extracts IFC facts.
`index_models.py` defines immutable records/version.
`index_store.py` persists exact JSON fields.
`indexer.py` binds source hash, schema and extractor version.

DoorStyle formal fields belong to TypeRecord formal attributes, not aliases or
ordinary Psets. Opening fill/host state belongs to Opening facets and
relationships, not free-form property facts.

## 2.6 `operations/hosted_opening.py`

Recommended family-neutral API:

```text
canonical_footprint(operation) -> HostedOpeningFootprint
check_wall_footprint(model, wall, footprint) -> structured checks
check_footprint_conflict(previous, current) -> structured issues
create_opening(model, operation, wall, footprint) -> role map
inspect_opening_chain(opening) -> topology record
host_storey(wall) -> IfcBuildingStorey
contain_element(model, element, storey, operation) -> relation record
```

The footprint contains wall-local horizontal and vertical intervals in mm.
It does not contain Door swing or Window Type facts.

Extract behavior under characterization tests before changing Window to use
it. Existing Window application hashes need not be byte-identical, but all
public L1/L2, occurrence fidelity and preservation behavior must remain
identical.

## 2.7 `operations/opening.py`

Owns:

- operation and parameter schemas;
- target Wall contract;
- opening-only L1/L2 policy;
- application role authorization;
- comparison adapter.

Delegates Opening construction and footprint checks to hosted-opening code.
Must explicitly prove no `IfcRelFillsElement` was created.

## 2.8 `operations/door.py`

Owns:

- both Door operation definitions;
- Door intent policy and deterministic canonicalizer;
- exact/generated Type compatibility;
- Door entity/representation/fill authoring;
- Door L1/L2 policies;
- Door postcondition/comparison adapters;
- Door-specific occurrence derivations.

Both operations share one Door core:

- `add_door_with_opening_to_wall` creates Opening then Door;
- `fill_existing_opening_with_door` validates/reuses the exact Opening and
  creates only Door/fill/containment/Type relationships.

No operation replaces an already filled Door.

## 2.9 `type_templates.py`

Refactor into:

```text
ensure_bound_type(model, assignment, definition, operation, owner_history)
```

Behavior:

1. existing GUID → require allowed Type class, return unchanged;
2. missing existing GUID with non-deterministic source → fail;
3. deterministic generated source → validate derivation and call registered
   factory;
4. factory result → verify GUID/class/formal fields.

Keep Window template behavior compatible. Door factory reads only validated
compiler-owned template fields, not raw Provider output.

## 2.10 Common semantic/evaluation modules

Replace hard-coded scope tuples with:

```text
definition.semantic_scope_roles
```

Replace hard-coded application role mapping with registered operation role
metadata. Family-specific fact extraction stays in operation policy/builders.

Historical Window report 0.1 and public APIs remain available. New generic
occurrence report 0.2 should have `ifc_class`, `scope` and `role`, allowing
Door, Opening and later Beam/Column use.

## 3. Test pattern map

| New test | Closest analog |
|---|---|
| `test_repair_intent_v05.py` | `test_occurrence_semantic_intent.py`, `test_request_stage.py` |
| `test_operation_prompt_profiles.py` | prompt registry tests and `test_registry.py` |
| `test_selected_provider_profiles.py` | `test_provider_stage.py`, `test_general_changeset_stage.py` |
| `test_opening_index.py` | `test_indexer.py`, `test_index_store.py` |
| `test_door_resolution.py` | `test_resolution_flow.py`, `test_property_confirmation.py` |
| `test_hosted_opening_primitives.py` | `test_window_application.py`, `test_batch_mutation.py` |
| `test_opening_application.py` | `test_window_application.py` |
| `test_door_application.py` | `test_window_application.py`, `test_semantic_authoring.py` |
| `test_door_type_authoring.py` | `test_property_binding_security.py`, generated Window Type tests |
| `test_door_evaluation.py` | `test_l1_evaluator.py`, `test_requested_property_l2.py` |
| `test_door_occurrence_fidelity.py` | `test_occurrence_fidelity.py`, `test_phase10_5_window_fidelity_e2e.py` |
| `test_mixed_hosted_operation_atomicity.py` | `test_apply_transaction.py`, `test_phase10_3_vvo_batch_e2e.py` |
| `test_phase11_dataset_e2e.py` | Phase 10/10.3/10.5 dataset tests |
| `test_phase11_live_uat.py` | `test_phase9_live_uat.py` |

Use synthetic IFC fixtures for contract and application tests. Dataset tests
must use source-bound manifests and remain marked/invoked separately when
large. Real Provider tests are never part of default offline CI.

## 4. Contract evolution pattern

Historical contract files are immutable.

| Existing | New | Compatibility rule |
|---|---|---|
| RepairIntent 0.4 | 0.5 | parser accepts both; new Stage 1 defaults to 0.5 |
| Semantic Manifest 0.2 | 0.3 | parser accepts all; new Door path always uses 0.3 |
| Bound ChangeSet 0.3 | 0.4 | audit/apply accept both; new Door path uses 0.4 |
| ChangeSet draft 0.2 | unchanged | no authority change is needed in Provider draft |
| Index 0.3 | 0.4 | no migration; rebuild on mismatch |
| Window occurrence report 0.1 | generic 0.2 | old functions preserved; new dispatcher emits 0.2 |

Every new schema has:

- a version constant and exact path;
- cached validation;
- round-trip and negative tests;
- prompt registry hash update where applicable;
- no mutation of older schema bytes.

## 5. Error pattern

Return stable codes at the earliest deterministic layer:

| Layer | Examples |
|---|---|
| Stage 1/profile | `OPERATION_PROFILE_MISMATCH`, malformed routing |
| clarification | `DOOR_DIMENSION_MEANING_REQUIRED`, `DOOR_VIEWPOINT_REQUIRED`, `DOOR_OPERATION_REQUIRED` |
| capability | `DOOR_GENERATED_STYLE_UNSUPPORTED`, `DOOR_REQUESTED_FEATURE_UNSUPPORTED`, `DOOR_REPLACEMENT_UNSUPPORTED` |
| resolution | `OPENING_ALREADY_FILLED`, `OPENING_HOST_INVALID`, Type ambiguity/conflict |
| audit | overlap, scope, fingerprint, class mismatch |
| application | deterministic ID collision, invalid Type derivation, missing relationship |
| postcondition/evaluation | topology, geometry, semantic or preservation mismatch |

Unsupported capability does not consume Stage 2. Ambiguity does not mutate an
IFC. An application/evaluation failure never publishes a result.

## 6. Security and authority pattern

- Provider input is public request + public bounded current-model evidence.
- Private original IFC/mutation manifest/benchmark Gold remain outside both
  Provider stages.
- Exact Type selection requires exact identity or explicit confirmation.
- Similarity retrieval cannot authorize.
- Generated Type derivation is compiler-owned and binder-signed.
- User values retain request/clarification provenance.
- Derived values retain formula ID, inputs and digest.
- Shared Type and non-target occurrence fingerprints are compared before and
  after.

## 7. Anti-patterns to reject in review

- copying all of `window.py` into `door.py`;
- adding `if operation_type.startswith("door")` to orchestrator/apply/evaluator;
- treating DoorStyle Name as OperationType;
- scaling an exact reused Type;
- asking the LLM to emit placements, transformation matrices or IFC STEP;
- copying occurrence properties because Type reuse was requested;
- requiring optional material/transom/hardware facts;
- changing Semantic Manifest 0.2 or ChangeSet 0.3 enum values in place;
- sending all future operation few-shots to every Provider call;
- using Ground Truth during production resolution;
- publishing a repaired IFC before independent operation and global gates pass.
