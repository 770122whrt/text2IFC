# Phase 12 Pattern Map: Beam and Column Operations

**Date:** 2026-08-03
**Status:** Complete for planning
**Purpose:** Map each Phase 12 implementation surface to the closest proven
local analog. This is a reuse guide, not authorization to reopen frozen
contracts.

## 1. Pattern summary

Phase 12 should look like a new pair of registered operations inside the
existing repair system, not like a second compiler. The most important reuse
chain is:

```text
OperationDefinition metadata
  -> compact Stage 1 profile
  -> deterministic resolution/authority
  -> selected Stage 2 profile
  -> bound semantic ChangeSet
  -> registered applicator
  -> reopen + Registry-driven L0/L1/L2
  -> full-model preservation
  -> independent Proof validation
```

Door is the closest complete operation-definition analog. Window provides
stable geometry/type/postcondition examples. The whole-model compiler provides
only low-level rectangular swept-solid ideas.

## 2. File-to-pattern map

| Phase 12 surface | Closest existing analog | Reuse | Do not copy |
|---|---|---|---|
| Beam/Column operation registration | `src/text2ifc_ifc_repair/operations/door.py` and `operations/__init__.py` | one declarative `OperationDefinition` per operation; resolver, policy, factory, profile, semantic roles and evaluator callbacks live on the definition | Door swing/opening/host fields or central family branches |
| Structural parameter schemas | Door/Window parameter schemas in `operations/door.py` and `operations/window.py` | strict JSON Schema, required public facts, stable missing/conflict diagnostics | compatibility aliases for noncanonical Provider paths |
| Prompt profiles and few-shots | `src/text2ifc_ifc_repair/prompt_profiles.py`, `prompts/agent/ifc-repair-profiles/`, `prompts/agent/ifc-repair-few-shots/` | compact Stage 1 projection, selected full Stage 2 projection, exact file/hash guards and sentinels | loading every full profile or teaching program-derived placement/GUID/template fields |
| Target adapters | `src/text2ifc_ifc_repair/index_adapters.py` | one adapter per occurrence class; bounded geometry, relationships, facets and warnings | treating an adapter summary as execution authority |
| Type records | explicit Type enumeration in `src/text2ifc_ifc_repair/indexer.py` | separate occurrence and Type records with deterministic SQLite round trip | embedding Type candidates into occurrence records only |
| Property target support | `operations/occurrence_property.py`, `semantic_authoring.py` | explicit editable class allowlist and generic bound semantic assignment | new structural RAG subsystem or vector-only value authority |
| Generated structural Types | `src/text2ifc_ifc_repair/type_templates.py` and Door factory in `operations/door.py` | validate expected class, compiler template/version/hash and deterministic identity before entity creation | selecting a neighboring Type when reuse was not requested; mutating a reused Type |
| Straight rectangular geometry | `src/text2ifc_compiler/geometry.py` `_v2_profile`, `add_v2_geometry`, `assign_v2_placement`; placement/reopen patterns in Door/Window applicators | `IfcRectangleProfileDef`, `IfcExtrudedAreaSolid`, local placement and representation context concepts | whole-model bootstrap, unit assumptions, OwnerHistory replacement or compiler orchestration |
| Semantic assignments | `src/text2ifc_ifc_repair/apply.py`, `semantic_authoring.py` | applicator returns created roles; common layer applies Type/material/Pset/quantity assignments atomically | a second property operation depending on newly created GUIDs |
| Evaluation | Door evaluation policy in `operations/door.py`, `evaluation_policy.py`, `evaluation_models.py` | Registry-driven blocking claims and evidence-backed results | aggregate success, approximate volume or visual bounds as strict L1 |
| Mutation and private Gold | `src/text2ifc_ifc_repair/mutation.py`, Phase 11 door mutation/tests | deterministic damage plus evaluator-only manifest | original IFC/deleted identity/mutation mapping in Provider input |
| Offline/live runner | `scripts/ifc_repair/run_phase11_offline.py`, `run_phase11_live_uat.py` | offline-before-live, raw attempts, profile hashes, actual Stage call counts and no-fallback field | synthetic, cached or hand-authored fallback |
| Proof curation and validation | Phase 11 curation scripts and `scripts/ifc_repair/validate_success_cases.py` | immutable case manifests, artifact hashes, reopen and independent recomputation | trusting the runner's reported `success` boolean |

## 3. Registered operation pattern

### Reference

`src/text2ifc_ifc_repair/operations/door.py` demonstrates the full local
pattern:

- schemas live beside the implementation;
- semantic policy declares required bound facts;
- intent policy and parameter resolver produce deterministic clarification;
- generated-Type factory accepts compiler-owned derivation;
- applicator returns stable created roles;
- postcondition and comparison callbacks measure the result;
- the definition declares profile, semantic roles and conflict domain.

### Phase 12 application

Create two definitions with distinct operation type/profile/target class:

```text
beam.add
  occurrence: IfcBeam
  type: IfcBeamType

column.add
  occurrence: IfcColumn
  type: IfcColumnType
```

Exact final operation identifiers should follow the repository naming
convention frozen by the checked-in profile schema. Once introduced, every
profile, few-shot, RepairIntent, registry definition, test and report must use
the same identifier.

Both definitions share a structural parameter resolver and straight-member
primitive where behavior is truly family-neutral. Beam/Column-specific
required facts and L1 checks remain on their definitions.

### Required invariant

Common `audit.py`, `apply.py`, orchestration and publication code discover the
new capability from Registry metadata. A new `if target_class == "IfcBeam"`
branch in common dispatch is a plan failure.

## 4. Prompt and canonical-field pattern

### Reference

`prompt_profiles.py` already validates:

- immutable JSON files;
- schema and content hashes;
- profile-operation-target agreement;
- compact versus full projection;
- selected union ordering and byte/count limits.

Door v0.2 correction provides the governing lesson: the prompt/few-shot/schema
must explicitly require the canonical path, and incorrect Provider output must
fail. The code must not accumulate synonyms to accommodate model feedback.

### Phase 12 application

Add one Beam and one Column profile with:

- compact classification terms and public slot summary;
- required, conditional, optional and program-derived slot lists;
- forbidden inference rules;
- complete, grouped-clarification, generated-Type and exact-Type-conflict
  examples;
- exact few-shot hashes.

Use one canonical resolved model:

- Beam: start/end center-axis, rectangular width/height, Storey;
- Column: base/top center-axis, rectangular width/depth, base Storey;
- optional explicit exact Type reuse;
- optional authorized material and Psets.

Do not include unit transforms, local-placement matrices, representation
context, deterministic IDs or generated-Type template identity in Stage 1.

## 5. Index and RAG pattern

### Reference

`index_adapters.py` builds bounded occurrence facts; `indexer.py` persists
occurrences and separately enumerated Types. The current default adapter and
Type lists simply omit structural families.

`operations/occurrence_property.py` is the production property-authoring
allowlist. Its current rejection of `IfcColumn` proves that a generic PSD
corpus alone is not structural support.

### Phase 12 application

Add:

- Beam/Column occurrence adapters;
- `IfcBeamType`/`IfcColumnType` enumeration;
- section/axis/placement capability evidence;
- containment, Type, material and effective property relationships;
- Beam/Column occurrence property scopes and tests;
- exact typed property evidence reaching the existing binder.

Keep the authority layers separate:

```text
vector recall -> candidate/property-name discovery
exact public/type/index fact -> deterministic authorization
bound manifest/ChangeSet -> executable fact
```

No plan may describe vector similarity as authorization for a value, Type,
material, target or Storey.

## 6. Type factory pattern

### Reference

`type_templates.ensure_bound_type()` handles exact and generated paths, while
Door registers a bounded generated factory/template. Exact reuse validates
class and returns the existing entity unchanged.

### Phase 12 application

Extend the supported generated value types to `IfcBeamType` and
`IfcColumnType`. Register deterministic factories that validate:

- expected IFC class;
- template ID and version;
- canonical derivation hash;
- rectangular section facts authorized by the resolved operation;
- absence of arbitrary Provider-owned template content.

When Type reuse is not requested, always create a dedicated deterministic
Type. Never clarify merely because nearby Types exist. Clarify/reject only an
explicit reuse request that resolves zero/multiple Types or conflicts with
family/section/representation evidence.

Generated Type policy must not invent material or copy occurrence facts.
Exact reuse preserves Type-inherited material but does not copy a direct
occurrence material/Pset.

## 7. Structural geometry pattern

### Reference

`text2ifc_compiler/geometry.py` shows the schema-level rectangular swept-solid
construction. Door/Window repair applicators show how an opened model supplies
units, representation context, `OwnerHistory`, placements, deterministic IDs
and reopen postconditions.

### Phase 12 application

Extract or implement a small repair-local straight-member primitive with a
function boundary equivalent to:

```text
create_straight_rectangular_member(
  model,
  occurrence_class,
  resolved_world_axis,
  section_width_mm,
  section_height_mm,
  storey,
  owner_history,
  representation_context,
  deterministic_ids
) -> created occurrence/representation/measurement evidence
```

The exact signature may adapt to local types, but the inputs and authority
boundary must remain explicit.

Beam uses start-to-end axis and horizontal acceptance. Column uses base-to-top
axis and vertical acceptance. Both use center-axis semantics and the frozen
Storey policy. Serialization/reopen measurements must be produced from the
created IFC, not carried forward from inputs as assumed success.

## 8. Semantic application pattern

### Reference

`apply.py` calls the registered applicator and then
`apply_semantic_assignments()` using the definition's declared role mapping.
This supports created entities without exposing their compiler-generated IDs
to Stage 2.

### Phase 12 application

Applicators return stable roles such as:

```text
beam
column
structural_type
```

The exact roles must match the semantic manifest scopes chosen by the existing
contract/version. Requested material/Pset/quantity assignments then use the
generic authoring layer in the same atomic transaction.

Do not add a follow-up occurrence-property ChangeSet that requires a newly
created Beam/Column GUID.

## 9. Evaluation pattern

### Reference

`evaluation_policy.py` and `evaluation_models.py` separate policy from
evidence. Door definitions show per-operation L0/L1/L2 callbacks and exact
relationship checks.

### Phase 12 application

Each operation records reopened evidence for:

- occurrence class and product count;
- axis endpoints or base/top;
- direction or horizontal/vertical tilt;
- rectangular section and member dimensions;
- Storey containment and Type relationship cardinalities;
- exact/generated Type evidence;
- applicable material/Pset/quantity facts;
- preservation.

Strict L1 thresholds:

```text
axis endpoint/base/top: <= 5 mm
direction/horizontal/vertical tilt: <= 0.1 degree
section/member dimension: <= 1 mm
```

Approximate volume and mesh bounds remain diagnostic. They cannot turn a
failed strict measurement green.

## 10. Dataset, isolation and Proof pattern

### Reference

Phase 11 separates:

1. deterministic damage and private mutation manifest;
2. production repair process with damaged/public evidence only;
3. post-publication private comparison;
4. immutable Proof curation;
5. independent collection validation.

### Phase 12 application

Use `d7n.ifc` as primary test-split evidence and `vvo.ifc` as secondary
same-family compatibility evidence. Required matrix:

- Beam-only;
- Column-only;
- mixed Beam+Column atomic success;
- injected mixed rollback;
- material-present and material-absent;
- requested property path;
- real DeepSeek complete;
- real DeepSeek clarification/resume.

The independent validator must reopen the result, recompute structural
measurements and verify hashes. It must not infer success from an application
or evaluation summary.

## 11. Test-first ownership map

| Plan area | Tests created first | Production surfaces after RED |
|---|---|---|
| Profiles/index/property | `test_structural_prompt_profiles.py`, `test_structural_index.py`, `test_structural_property_authoring.py` | profiles/few-shots, adapters/indexer, occurrence property allowlist |
| Type/geometry | `test_structural_type_authoring.py`, `test_structural_geometry.py` | type templates/factories and repair-local geometry module |
| Beam/Column operations | Beam/Column resolution/application tests plus `test_structural_atomicity.py` | operation modules, registration and evaluator hooks |
| Dataset/Proof | mutation, isolation, evaluation, dataset and success-case tests | mutation runner, offline runner and strict validator |
| Live closure | `test_phase12_live_uat.py` | live runner/curator/reporting, then actual Provider execution |

Historical regression files named in `12-VALIDATION.md` run beside the new
tests at each seam.

## 12. Anti-patterns to reject during plan review

- a second Beam/Column orchestration pipeline;
- a common dispatcher with structural family switches;
- copying whole-model bootstrap into IFC repair;
- Provider-owned placement matrices, GUIDs or Type templates;
- Type similarity selection without explicit reuse intent;
- material or Pset invention when omitted;
- vector retrieval promoted to semantic value authority;
- aliases added after noncanonical model output;
- bounding-box, mesh or volume proxy reported as strict L1;
- private original/mutation Gold visible before publication;
- live UAT before complete offline regression;
- synthetic/cached fallback presented as real DeepSeek evidence;
- runner `success=true` accepted without independent reopen/recomputation;
- `d7n` and `vvo` described as independent datasets.

## 13. Planning conclusion

The local analogs cover every Phase 12 implementation surface. No new
architecture or product decision is needed. Plans can remain sequential across
the five seams defined in `12-RESEARCH.md`, with TDD ownership and validation
commands taken from `12-VALIDATION.md`.
