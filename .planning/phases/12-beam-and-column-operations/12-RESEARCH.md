# Phase 12 Research: Beam and Column Operations

**Date:** 2026-08-03
**Status:** Complete for planning
**Scope:** Local production code, checked-in IFC2X3 datasets, existing Phase
8-11 operation/RAG/evaluation contracts
**Requirements:** OPS-03, OPS-04

## 1. Recommendation

Add `IfcBeam` and `IfcColumn` creation as two registered operations on the
existing two-stage IFC repair pipeline. Reuse the shared Registry,
RepairIntent, deterministic resolution, semantic authoring, atomic ChangeSet,
publication and comparison boundaries. Do not add a structural orchestrator,
family switch in common code, new RAG authority model or compatibility aliases
for Provider output.

The implementation should proceed through five bounded changes:

1. add Beam/Column target adapters, structural Type indexing and occurrence
   property scopes;
2. register compiler-owned generated `IfcBeamType`/`IfcColumnType` factories
   and a family-neutral straight rectangular-member authoring primitive;
3. add versioned structural operation profiles/few-shots and registered
   Beam/Column definitions;
4. extend deterministic damage, L0/L1/L2 and independent success-case
   validation to structural products;
5. prove offline dataset cases before real DeepSeek complete and clarification
   UAT, with no synthetic fallback.

No new contract decision is required. The Phase 12 context and specification
already resolve the two material ambiguities:

- absence of Type-reuse intent creates a dedicated deterministic structural
  Type and never selects a neighboring existing Type;
- structural L1 uses the established precision grade: axis endpoint/base/top
  within 5 mm, direction or horizontal/vertical tilt within 0.1 degrees, and
  section/member dimensions within 1 mm.

## 2. Sources inspected

### 2.1 Planning and frozen contracts

- `.planning/STATE.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/phases/12-beam-and-column-operations/12-CONTEXT.md`
- `.planning/phases/12-beam-and-column-operations/12-DISCUSSION-LOG.md`
- `.planning/phases/12-beam-and-column-operations/12-SPEC.md`
- Phase 9-11 specifications, validation strategies and summaries

### 2.2 Production operation path

- `src/text2ifc_ifc_repair/registry.py`
- `src/text2ifc_ifc_repair/operations/__init__.py`
- `src/text2ifc_ifc_repair/apply.py`
- `src/text2ifc_ifc_repair/audit.py`
- `src/text2ifc_ifc_repair/semantic_authoring.py`
- `src/text2ifc_ifc_repair/evaluation_policy.py`
- `src/text2ifc_ifc_repair/evaluation_models.py`
- `src/text2ifc_ifc_repair/type_templates.py`
- `src/text2ifc_ifc_repair/prompt_profiles.py`
- `src/text2ifc_ifc_repair/operations/window.py`
- `src/text2ifc_ifc_repair/operations/door.py`
- `src/text2ifc_ifc_repair/operations/occurrence_property.py`

### 2.3 Index, geometry and proof seams

- `src/text2ifc_ifc_repair/index_adapters.py`
- `src/text2ifc_ifc_repair/indexer.py`
- `src/text2ifc_ifc_repair/index_models.py`
- `src/text2ifc_ifc_repair/index_store.py`
- `src/text2ifc_ifc_repair/mutation.py`
- `src/text2ifc_compiler/geometry.py`
- `src/text2ifc_compiler/bootstrap.py`
- `src/text2ifc_compiler/verification.py`
- `scripts/ifc_repair/run_phase11_live_uat.py`
- `scripts/ifc_repair/run_phase11_offline.py`
- `scripts/ifc_repair/validate_success_cases.py`

### 2.4 Dataset evidence

Eleven checked-in BIMNet IFC2X3 files contain an `IfcBeam` or `IfcColumn`.
Phase 12 uses two scenes from the same BIMNet source family and must therefore
claim cross-scene compatibility, not cross-dataset generalization.

| Scene | Role | Observed structural inventory |
|---|---|---|
| `dataset/ifc/test/d7n.ifc` | primary test-split scene | 10 Beams, 15 Columns; all sampled members typed, contained and carrying common Pset evidence; no direct sampled material |
| `dataset/ifc/train/vvo.ifc` | secondary compatibility/mixed scene | 6 Beams, 5 Columns; Beams are horizontal swept solids with rectangular dimensions and reinforced-concrete material; Columns are approximately 500 x 500 mm mapped members, mostly without material |

Other observed inventory includes 33 Beams and two Columns in `q9v`, and one
Beam and seven Columns in `1px`. These may support later regression breadth but
are not required Phase 12 Proof scenes.

## 3. Existing architecture to reuse

### 3.1 Registry-driven operation dispatch

`OperationDefinition` already owns the correct extension seams:

- parameter, target and intent schemas;
- context, precondition, applicator, postcondition and comparison callbacks;
- capability constraints and evaluation policy;
- semantic policy facts and editable occurrence classes;
- exact-Type evidence and generated-Type factory/template;
- prompt profile, semantic scopes and conflict domain;
- deterministic intent policy, parameter resolution and operation conflict
  checks.

Beam and Column should each be ordinary definitions. Common audit, bind,
application and evaluation code must not branch on `family == beam` or
`family == column`.

### 3.2 Selected operation profiles

The current profile registry provides immutable JSON profiles, compact Stage 1
projections, full selected Stage 2 projections and content-hash guards.
Existing limits are sufficient for two structural profiles and their bounded
few-shots.

The frozen routing contract remains:

- Stage 1 receives the compact catalog for all registered operations and
  classifies family/action while extracting public facts;
- deterministic code validates and resolves the selected operation;
- clarification sees only missing/conflicting public facts;
- Stage 2 receives only the full profiles/few-shots selected by Stage 1;
- no extra classification call and no full-registry Stage 2 prompt.

Structural few-shots must show canonical fields only. If real Provider output
violates an explicitly documented field, the result fails or clarifies; Phase
12 must not add aliases merely to accept that output.

### 3.3 Atomic semantic authoring

`apply_changeset()` dispatches the registered applicator, then applies bound
semantic assignments to declared created/modified roles. The generic
`apply_semantic_assignments()` path already supports Type, material, Pset and
quantity semantics.

This means Beam/Column creation and requested scalar properties can remain in
one transaction. There is no need for a second GUID-dependent property
operation or a structural-only semantic writer.

### 3.4 Exact and generated Type binding

`ensure_bound_type()` already protects exact reuse:

- the resolved entity must exist;
- its IFC class must equal the operation's expected Type class;
- a generated Type must carry compiler-owned deterministic derivation;
- arbitrary Provider templates are not authority.

Phase 12 should extend the generated-Type class allowlist and register bounded
factories for `IfcBeamType` and `IfcColumnType`. A generated structural Type
contains compiler policy identity/label plus authorized rectangular-section
facts. It does not infer material, copy an occurrence Pset or adopt a
neighboring Type by similarity.

### 3.5 Geometry primitives

The whole-model compiler already demonstrates IFC2X3 rectangular
`IfcRectangleProfileDef` + `IfcExtrudedAreaSolid` authoring and local placement.
Those low-level concepts are reusable; its whole-model bootstrap and
orchestration are not.

The repair implementation must preserve the opened model's:

- unit scale and geometric representation context;
- `OwnerHistory`;
- Building/Storey hierarchy;
- object placement chain;
- transaction, deterministic-ID and publication rules.

A family-neutral straight-member module should accept an already resolved
world/local axis and rectangular section, then produce:

- Beam: an extrusion along the resolved member axis;
- Column: an extrusion from resolved base to top;
- occurrence placement and body representation;
- exact containment and Type relationships;
- evidence measurements used by postconditions and L1.

## 4. Gaps requiring implementation

## 4.1 Structural target and Type indexing

The default target adapters currently cover Wall, Opening, Door, Window and
Space. Explicit Type enumeration covers Wall, Window and Door Type classes.

Add:

- `BeamIndexAdapter` and `ColumnIndexAdapter`;
- bounded axis/base/top, direction, rectangular section and representation
  capability summaries;
- Storey, exact Type, material and effective property relationship evidence;
- separate `IfcBeamType` and `IfcColumnType` records;
- SQLite round-trip and stale-schema behavior matching the current rebuildable
  cache contract.

The index may expose similarity candidates, but only exact public resolution
may authorize a target, Storey, Type, material or reference member.

## 4.2 Occurrence property scopes

`operations/occurrence_property.py` currently limits editable targets to Door,
Wall/WallStandardCase and Window; tests intentionally reject Column.

Add Beam and Column as explicit supported occurrence classes and prove:

- property-name retrieval is distinct from value authority;
- exact typed facts, not vector text alone, reach Stage 2;
- requested Psets/quantities are authored on the new occurrence;
- optional unrequested material/property fields remain absent;
- existing family behavior is unchanged.

This is the required RAG completion. The PSD corpus is generic; the missing
work is structural production integration and evidence, not a new
Window-derived corpus.

## 4.3 Structural operation definitions

Register one add operation per family. Each definition should own:

- public parameter and target schemas;
- compact/full prompt profile ID;
- supported capability contract;
- deterministic parameter resolver;
- generated-Type template/factory;
- semantic role mapping;
- applicator, postcondition and comparison;
- structural conflict domain for duplicate/overlapping requested members where
  the frozen contract defines a conflict.

Beam requires resolved start/end or supported-reference derivation. Column
requires resolved base/top or base plus height. Both require rectangular
section dimensions and one Storey under the frozen Storey policy. Missing
blocking facts are grouped into one clarification.

## 4.4 Deterministic Type policy

Two paths are valid:

1. explicit Type reuse resolves exactly one compatible Type and leaves its
   fingerprint unchanged;
2. no Type-reuse intent creates one dedicated deterministic structural Type
   from the operation's authorized family/section facts.

Zero/multiple explicit Type candidates, family mismatch, representation-map
conflict or requested-size conflict must clarify or reject. Generated Types
must not select a nearby Type or inherit material/property facts that the
request did not authorize.

## 4.5 Damage and private Ground Truth

Add deterministic damage cases that remove selected Beam/Column products and
their occurrence-specific relationships while retaining a private mutation
manifest for evaluation.

Production inputs may contain only damaged/public IFC evidence and the public
request. Original IFC, removed GlobalIds, private mappings and expected values
must be introduced only after publication by the private comparator.

## 4.6 Independent success validation

The Phase 11 validator already found a historical false-positive class:
reported success was not enough until artifacts were independently reopened
and recomputed.

Evolve the validator into a family-neutral strict checker that:

- verifies every manifest hash;
- reopens every published IFC as IFC2X3;
- independently counts required new products and exact relationships;
- recomputes structural dimensions, axes, orientation and requested semantics;
- checks preservation and private-Gold isolation;
- rejects missing evidence, diagnostic-only substitutes and stale aggregate
  success flags.

Historical Window/Door Proof must remain valid under its declared schema; new
structural Proof receives the stricter structural checks.

## 5. Canonical structural parameter model

The exact schema names are implementation detail within the frozen meanings,
but prompt, schemas, normalization and evidence must use one canonical shape.
A suitable resolved representation is:

```json
{
  "axis": {
    "start": {"x_mm": 0, "y_mm": 0, "z_mm": 3000},
    "end": {"x_mm": 5000, "y_mm": 0, "z_mm": 3000}
  },
  "section": {
    "shape": "rectangle",
    "width_mm": 300,
    "height_mm": 500
  },
  "storey": {"global_id": "..."},
  "type": {
    "mode": "generated"
  }
}
```

For Column, the resolved axis is base-to-top. Public shorthand may be accepted
only when the deterministic resolver can prove the same canonical facts from
authorized evidence. Provider-supplied synonyms are not silently normalized
after a canonical prompt/schema violation.

Program-derived fields such as unit transforms, placement matrices,
deterministic GUIDs, representation context and Type template identity stay
out of Stage 1.

## 6. Evaluation policy

### 6.1 L0 structural validity

Blocking:

- output exists, parses and reports IFC2X3;
- every requested operation creates exactly one correct occurrence;
- required placement, shape representation, containment and Type relationship
  exist exactly once;
- no undeclared Root creation/removal or unauthorized mutation;
- atomic mixed requests publish once or publish nothing.

### 6.2 L1 geometry and relationship fidelity

Blocking:

- each Beam axis start/end or Column base/top is within 5 mm;
- axis direction and Beam horizontal/Column vertical tilt are within 0.1
  degrees;
- rectangular section and requested member dimensions are within 1 mm;
- Storey containment and Type relationship cardinalities are exact;
- reopened IFC measurements, not approximate volume, establish success.

Mesh or volume estimates may remain diagnostic. They cannot substitute for
axis, section or relationship measurements.

### 6.3 L2 semantic fidelity

Blocking when requested or deterministically bound:

- exact/generated Type identity and derivation;
- exact authorized material semantics;
- exact Pset/quantity names, scopes, data types and values;
- no invented optional material/property fact;
- exact Type reuse fingerprint unchanged;
- global preservation and private-Gold isolation pass.

## Validation Architecture

Phase 12 follows test-driven implementation and an offline-before-live gate.

### Layer A: contracts, profiles and policy

Fast synthetic tests for structural profile hashes, Stage 1 compact versus
Stage 2 selected projection, schema-required fields, conditional
clarification, forbidden inference and generated-Type derivation.

Target: less than 30 seconds.

### Layer B: index and resolution

Synthetic IFC2X3 plus `d7n`/`vvo` inventory tests for target adapters, Type
records, Storey/axis/section facts, exact resolution, ambiguity and SQLite
round trips.

Target: less than 60 seconds for focused tests.

### Layer C: Type, geometry and application

Synthetic IFC2X3 tests for Beam/Column geometry, placement, containment,
generated/exact Type binding, optional material, semantic assignments,
serialization/reopen and rollback.

Target: less than 120 seconds for focused tests.

### Layer D: structural evaluation and datasets

Offline `d7n` primary, `vvo` compatibility and mixed atomic cases with strict
L0/L1/L2, preservation, Ground Truth isolation and independent artifact
validation.

Target: less than 180 seconds for focused cases; full preservation may use the
existing longer comparator budget.

### Layer E: changed-surface and full repair regression

Run focused changed-surface tests after each plan and the complete
`tests/ifc_repair` suite before live UAT. The latest Phase 11 full repair suite
required about 18 minutes, so it is a deliberate pre-live gate rather than a
per-task feedback command.

### Layer F: real DeepSeek UAT

Only after every offline gate is green:

1. one complete Beam+Column request;
2. one incomplete structural request that returns one grouped clarification
   and resumes;
3. any required program-side unsupported/conflict guard.

The accepted live run records actual Stage 1/Stage 2 call counts, model/token
metadata, rendered prompt/profile hashes, public artifacts, publication state
and `synthetic_fallback_used: false`. Published output is then reopened and
independently validated; the runner's own success flag is not authority.

## 8. Security and trust-boundary analysis

| Threat | Required mitigation and test |
|---|---|
| Provider invents Type/material/property/coordinates | JSON schema plus deterministic authority binding rejects unbound facts |
| Full structural few-shots leak into unrelated requests | selected-profile hash/absence tests prove only chosen full profiles enter Stage 2 |
| Private original IFC or mutation mapping reaches Provider | process/input boundary test runs production without access to private artifacts |
| Similarity candidate becomes execution authority | exact resolver tests reject vector-only or ambiguous candidates |
| Generated Type derivation is tampered | class/template/hash validation fails before mutation |
| Shared exact Type is mutated to fit occurrence | before/after Type fingerprint and mapped-representation checks block publication |
| Partial Beam+Column ChangeSet publishes | injected second-operation/postcondition/evaluation failures leave no output |
| Aggregate report lies about success | independent validator reopens and recomputes every blocking gate |
| Proof artifact is stale or edited | manifest SHA-256 verification rejects it |
| Resource-heavy IFC causes unbounded validation | existing comparator/process budget and explicit timeout report fail closed |

No network input should influence filesystem paths, executable commands,
schema locations or private artifact selection.

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Axis/local-placement errors look correct by bounding box | measure reopened endpoints and direction in world coordinates |
| Column storey is inferred from a nearby member | resolve from the frozen base-Storey policy and exact Building/Storey evidence |
| Generated Type accidentally absorbs occurrence facts | factory accepts only bounded compiler template plus authorized section facts |
| Existing Type map conflicts with requested size | preserve Type unchanged and clarify/reject; never rescale or rewrite |
| RAG is treated as value authority | typed retrieval fact must carry exact source/subject/value; vector recall remains discovery only |
| Structural aliases hide a bad prompt | canonical profile/few-shot/schema tests; reject noncanonical Provider paths |
| One scene overstates generality | report `d7n`/`vvo` as cross-scene BIMNet evidence only |
| Full regression delays feedback | focused tests per task, full repair suite once before live |
| Live Provider retry masks contract weakness | retain attempts/corrections and report call counts; no synthetic/cached replacement |

## 10. Planning implications

The implementation plans should be sequential where they share Registry,
schema, geometry and evaluator seams:

1. structural index, property target support and prompt-profile contracts;
2. shared straight-member geometry and deterministic structural Type binding;
3. registered Beam/Column operations plus atomic application/evaluation;
4. deterministic dataset damage, strict independent validator and offline
   Proof;
5. real DeepSeek UAT, curated live Proof, final regression and Phase 12
   closure.

Every plan must include OPS-03 and/or OPS-04 traceability, test-first tasks,
explicit private/public boundary tests and focused verification commands.
Plan 5 must depend on all offline plans and must prohibit live execution until
their blocking gates pass.

## 11. Conclusion

Phase 12 is ready for planning. The production architecture already provides
the correct operation, authority, transaction and evidence boundaries.
Implementation is additive: fill the Beam/Column adapters, Type factories,
profiles, operations and strict Proof coverage without changing the frozen
Door workflow, geometry policy, Ground Truth isolation, Storey policy or RAG
authority model.
