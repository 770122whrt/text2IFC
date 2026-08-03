# Phase 12: Beam and Column Operations — Specification

**Created:** 2026-08-03
**Ambiguity score:** 0.06 (gate: ≤ 0.20)
**Requirements:** 16 locked

## Goal

The existing IFC2X3 repair pipeline can create one or more straight
rectangular `IfcBeam` and `IfcColumn` occurrences from natural-language intent,
author only explicitly supported semantics, and publish the repaired IFC only
after independently verified L0/L1/L2 and full-model preservation pass.

## Background

The common ChangeSet envelope, two-stage RepairIntent workflow, deterministic
target resolution, semantic binder, transactional applicator, comparator,
preservation gate and real DeepSeek proof pipeline already support Window,
Opening, Door and generic occurrence-property operations.

The IFC2X3 property corpus is class-generic and already contains
`Pset_BeamCommon` and `Pset_ColumnCommon`, but the production path is incomplete:

- no `add_beam` or `add_column` operation is registered;
- the target index has no Beam or Column adapter;
- Type enumeration names only `IfcWallType`, `IfcWindowStyle` and
  `IfcDoorStyle`;
- `set_occurrence_properties` explicitly rejects `IfcBeam` and `IfcColumn`;
- no structural operation prompt/few-shot profile or real DeepSeek structural
  Proof exists.

A complete BIMNet IFC2X3 manifest scan found 11 files containing Beam or
Column. The primary test-split scene, `d7n.ifc`, contains 10 Beams and 15
Columns. The secondary scene, `vvo.ifc`, contains six Beams and five Columns
with swept Beam and mapped Column representations. They provide real
cross-scene evidence but not independent authoring-family evidence.

## Requirements

1. **OPS-03 registered Beam creation**: The production registry supports an
   `add_beam` operation that creates one straight horizontal rectangular
   `IfcBeam` from a selected Storey, center-axis endpoints and section
   dimensions.
   - Current: No Beam geometry operation or production Beam operation profile
     exists.
   - Target: `add_beam` participates in the same context, audit, bind, apply,
     compare and publication orchestration as existing registered operations.
   - Acceptance: A default-registry end-to-end test creates exactly one
     `IfcBeam` with the requested axis and rectangular section and requires no
     Beam-specific branch in the common orchestration.

2. **OPS-04 registered Column creation**: The production registry supports an
   `add_column` operation that creates one straight vertical rectangular
   `IfcColumn` from a selected Storey, center-axis base/top and section
   dimensions/orientation.
   - Current: No Column geometry operation or production Column operation
     profile exists.
   - Target: `add_column` uses the common operation lifecycle and declares its
     own bounded geometry, target, semantic and evaluation contracts.
   - Acceptance: A default-registry end-to-end test creates exactly one
     `IfcColumn` with the requested vertical axis and rectangular section and
     requires no Column-specific branch in the common orchestration.

3. **Canonical center-axis geometry**: Beam and Column public intent,
   ChangeSet parameters and evaluation share one unambiguous center-axis
   coordinate contract in millimetres.
   - Current: No structural coordinate contract exists; sampled IFC placements
     and representation origins are authoring-pattern-specific.
   - Target: Beam start/end identify its end-face centers; Beam width is
     horizontal and perpendicular to its axis and height is vertical. Column
     base/top identify its vertical center axis; width/depth and non-square
     section orientation are explicit.
   - Acceptance: Schema and resolver tests reject profile-corner/raw-placement
     coordinates, conflicting length/height fields, non-finite values and a
     non-square Column with unresolved orientation.

4. **Frozen structural capability boundary**: The first release accepts
   horizontal straight Beams in any Storey-local XY direction and vertical
   straight Columns with rectangular sections only.
   - Current: No structural capability checker exists.
   - Target: Inclined/curved members, round/I/H/arbitrary/variable profiles,
     arbitrary Beam-section rotation and formal Grid placement return stable
     deterministic unsupported outcomes.
   - Acceptance: Focused tests prove every excluded geometry class is rejected
     before IFC mutation and is never approximated as a supported rectangle.

5. **Deterministic containment and physical graph**: Each created structural
   occurrence has exactly one allowed spatial containment and the relationships
   authorized by its Type, material and requested property contract.
   - Current: No Beam/Column applicator creates or validates containment.
   - Target: Beam containment is the selected `IfcBuildingStorey`; Column
     containment is the Storey at its axis base. The operation does not
     auto-split Columns, author analysis members/loads/nodes/ports, create
     structural connectivity, or trim/join supporting elements.
   - Acceptance: Reopened IFC checks show exact containment cardinality and no
     unauthorized structural-analysis or connection relationship was created.

6. **Exact or generated Type binding**: Every created Beam/Column binds
   exactly one `IfcBeamType`/`IfcColumnType`.
   - Current: The shared Type binder can reuse existing Window/Door Types and
     create Window/Door system Types, but rejects structural Type generation.
   - Target: An explicit Type-reuse request resolves one exact Type and reuses
     it unchanged. With no reuse request, the compiler creates a dedicated,
     deterministic structural Type from authorized class/section facts without
     clarification. Existing mapped geometry is never silently scaled or
     rewritten.
   - Acceptance: Tests cover exact reuse, missing-reuse deterministic
     generation, zero/multiple reuse candidates, class mismatch, mapped-size
     conflict and unchanged shared-Type fingerprints.

7. **Optional material by explicit authority**: Missing material is neither an
   error nor permission to invent one.
   - Current: Structural occurrence material is not supported by a Phase 12
     operation, and sampled Beam/Column material presence is inconsistent.
   - Target: No material request produces no new material association. An
     explicit material request reuses one uniquely resolved `IfcMaterial` or
     creates one with the exact authorized label. Explicit exact Type reuse
     preserves inherited Type material semantics without copying
     occurrence-direct material. Conflicts clarify.
   - Acceptance: Separate tests prove omitted, explicitly reused, explicitly
     created, Type-inherited and conflicting material cases, including absence
     of inferred grade/strength properties.

8. **Beam/Column target and Type evidence index**: The compact IFC index
   exposes Beam/Column occurrences and their Types through the existing
   registry-driven record model.
   - Current: Default adapters cover Wall, Opening, Door, Window and Space;
     explicit Type enumeration omits `IfcBeamType` and `IfcColumnType`.
   - Target: `IfcBeam`/`IfcColumn` adapters emit stable identity, Storey,
     placement/geometry summaries, Type/material/property evidence and bounded
     diagnostics; structural Types are indexed separately from occurrences.
   - Acceptance: Frozen inventory tests on `d7n.ifc` report 10 Beams and 15
     Columns and on `vvo.ifc` report six Beams and five Columns, with resolvable
     Type records and no regression to existing indexed families.

9. **Class-applicable property retrieval and authoring**: The existing
   IFC2X3 PSD retrieval/resolution/semantic path formally supports Beam and
   Column.
   - Current: The corpus contains structural PSD records, but the occurrence
     operation whitelist rejects both target classes and no live structural
     property case exists.
   - Target: Natural-language property intent resolves to a canonical
     class-applicable Pset/property/value type/value; Stage 2 receives only the
     resolved fact; the common semantic author applies it atomically to an
     existing or newly created structural occurrence.
   - Acceptance: Beam and Column tests each map a natural-language
     `LoadBearing=true` request to the correct canonical Common Pset, write the
     IFC Boolean value and pass L2 after reopen.

10. **Non-authoritative retrieval recall**: Vector or keyword recall cannot
    authorize a structural property or normalize an unsupported Provider key.
    - Current: The knowledge layer already treats vector retrieval as recall,
      but Beam/Column prompts, tests and live evidence do not enforce the rule.
    - Target: Applicability-filtered canonical PSD records remain authority;
      Top-K candidates and embeddings stay outside Stage 2; unknown synonyms,
      wrong nesting and wrong class properties fail closed.
    - Acceptance: Negative tests prove vector-only matches, cross-class PSD
      matches and hallucinated synonyms cannot enter a Bound ChangeSet.

11. **Selected operation routing**: Stage 1 classifies Beam/Column family and
    action within each RepairIntent operation and selects only the registered
    structural profiles needed by later stages.
    - Current: The selected-profile path contains Window/Opening/Door/property
      profiles but no structural profiles.
    - Target: Beam/Column profiles include their canonical schema, slot policy,
      capability codes, constraints and complete/clarification/unsupported
      few-shots without an extra Provider classification call.
    - Acceptance: Prompt-contract tests show unrelated family schemas and
      few-shots are absent, all canonical structural fields are explicit and a
      mixed Beam+Column request yields two intents compiled into one
      ChangeSet.

12. **Fail-closed clarification and conflict policy**: Ambiguity or
    unsupported intent stops before publication without compatibility
    rewriting of LLM output.
    - Current: Existing families clarify ambiguous targets/Types and reject
      schema violations, but structural error codes and conflict footprints do
      not exist.
    - Target: Ambiguous Storey/axis/support/orientation/explicit Type/material
      produces structured clarification; unsupported geometry produces stable
      capability rejection; exact duplicate or overlapping same-axis
      structural operations fail the whole transaction. Legitimate
      Beam/Column support intersections remain allowed.
    - Acceptance: Tests distinguish clarification, unsupported and conflict
      outcomes and prove no rejected candidate becomes a success artifact.

13. **Atomic structural and mixed-family ChangeSets**: Beam/Column operations
    compose with each other and with Window/Door without partial publication.
    - Current: Atomic multi-operation application is proven for Window and
      Door but not structural families.
    - Target: One ChangeSet can contain Beam, Column, Window and Door
      operations. Any audit, apply, postcondition, reopen or evaluation failure
      prevents the complete transaction from publishing.
    - Acceptance: A real-model mixed-family success publishes all intended
      members; injected failure in each operation position publishes none and
      leaves the damaged input unchanged.

14. **Strict structural L0/L1/L2 evaluation**: Published structural results
    meet explicit topology, geometry and semantic thresholds after reopening.
    - Current: No structural comparison adapter or precision contract exists.
    - Target: L1 requires each axis endpoint/base/top within 5 mm, axis
      direction/horizontal-or-vertical tilt within 0.1 degree and every section
      plus member length/height dimension within 1 mm. Product, containment and
      Type cardinalities are exact. L2 validates requested Material/Pset
      canonical name, IFC value type, value and semantic scope exactly.
    - Acceptance: Threshold boundary tests pass at the stated limits and fail
      immediately beyond them; approximate volume agreement alone cannot
      produce L1 success.

15. **Real IFC2X3 benchmark and Ground Truth isolation**: Structural
    acceptance uses real source IFCs with deterministic damage and evaluator-
    only Gold.
    - Current: No structural damage manifest, public projection or benchmark
      report exists.
    - Target: `d7n.ifc` is the primary Beam+Column test-split case and
      `vvo.ifc` is the secondary compatibility/mixed case. Original identities,
      STEP IDs, complete geometry and Gold ChangeSets remain outside all
      Provider-shaped inputs.
    - Acceptance: Manifests bind source path/schema/hash and damage scope;
      leakage tests prove private mappings are unavailable to Stage 1, target
      resolution, Stage 2 and predicted ChangeSets; reports label the evidence
      cross-scene, not cross-authoring-family.

16. **Real DeepSeek and independently validated Proof**: Phase 12 closes only
    after a real complete structural request and a real clarification request
    are independently curated and verified.
    - Current: Real DeepSeek Proof covers Window/Door families; no structural
      live run or family-neutral strict Proof verifier exists.
    - Target: The complete live request creates Beam+Column and exercises
      class-applicable structural properties. The clarification request stops
      without publication. A family-neutral proof validator recomputes prompt
      hashes, Provider/model evidence, Bound ChangeSet audit, IFC reopen,
      L0/L1/L2, global preservation and private-Gold isolation.
    - Acceptance: Both live paths contain genuine network evidence and
      `synthetic_fallback=false`; only the complete path publishes an IFC, and
      that IFC independently reopens as IFC2X3 and passes every strict gate.

## Boundaries

**In scope:**

- `add_beam` and `add_column` registered operation contracts.
- Horizontal straight rectangular Beam and vertical straight rectangular
  Column geometry using Storey-local center axes.
- Exact Type reuse and dedicated deterministic `IfcBeamType`/`IfcColumnType`
  generation.
- Optional, explicitly authorized direct `IfcMaterial` semantics.
- Beam/Column occurrence and Type indexing.
- Class-applicable `Pset_BeamCommon`/`Pset_ColumnCommon` retrieval and generic
  semantic authoring.
- Structural prompt profiles, constraints and complete/clarification/
  unsupported few-shots.
- Structural L0/L1/L2 comparison, full-model preservation and atomic mixed-
  family application.
- Real `d7n`/`vvo` benchmark evidence and real DeepSeek complete/clarification
  Proof with independent validation.

**Out of scope:**

- Inclined or curved members and round/I/H/arbitrary/variable profiles —
  unsupported geometry needs separate contracts and evidence.
- Formal `IfcGrid`/`IfcGridAxis` placement — grid indexing, intersection and
  ambiguity policy require a future phase.
- Structural analysis models, loads, analytical nodes, ports and automatic
  connectivity — Phase 12 creates physical BIM products only.
- Existing Beam/Column deletion, replacement, movement, resizing and shared
  Type mutation — only additive geometry and generic occurrence-property
  authoring are introduced.
- Automatic material, strength, grade, Pset or Quantity inference — absence is
  not user authorization.
- Cross-authoring-family structural claims — the authorized acceptance scenes
  are different BIMNet scenes from one source family.
- Window/Opening/Door workflow, geometry thresholds, Ground Truth boundary or
  established Storey-policy redesign — these contracts remain frozen.
- L3 GUID, STEP ID, authoring-node, serialization or byte identity — L3
  remains deferred.
- Phase 13 128k/large-context experiments — active DeepSeek limits remain
  65,536 input/output tokens.

## Constraints

- Output remains IFC2X3 and must reopen through IfcOpenShell before evaluation.
- The existing two-stage RepairIntent → deterministic resolution → selected
  profile → Bound ChangeSet workflow is mandatory.
- The Provider receives damaged/public evidence only; private Gold is
  post-repair evaluator input only.
- All low-level IFC identity, placement, representation and relationship
  entities are created deterministically, never authored by the LLM.
- Retrieval may improve recall but cannot authorize values or expand the
  canonical property contract.
- Unknown Provider synonyms and wrong nesting are preserved as failures rather
  than added to a compatibility normalizer.
- Every failure path is fail-closed and produces no publishable repaired IFC.
- Real DeepSeek UAT cannot use synthetic, cached or prerecorded output as a
  fallback.
- Common orchestration remains family-neutral; family-specific fields and
  logic enter only through registered operation definitions/profiles.

## Acceptance Criteria

- [ ] The default production registry exposes `add_beam` and `add_column`.
- [ ] `d7n.ifc` deterministic inventory reports 10 Beams and 15 Columns;
      `vvo.ifc` reports six Beams and five Columns.
- [ ] A complete Beam request creates exactly one horizontal rectangular
      `IfcBeam` with exact Storey containment and Type relationship.
- [ ] A complete Column request creates exactly one vertical rectangular
      `IfcColumn` with exact base-Storey containment and Type relationship.
- [ ] Missing Type-reuse intent creates a dedicated deterministic structural
      Type and never selects a neighboring existing Type.
- [ ] Exact Type reuse leaves the reused Type fingerprint unchanged and rejects
      class, size or mapped-geometry conflicts.
- [ ] Omitted material creates no material association and does not clarify;
      explicitly authorized material paths pass L2.
- [ ] Beam and Column each resolve and author a natural-language
      `LoadBearing=true` request through their canonical applicable Common Pset.
- [ ] Vector-only, cross-class, unknown-synonym and wrong-nesting property
      candidates cannot enter Stage 2 or a Bound ChangeSet.
- [ ] Beam/Column Stage 1 routing selects only the relevant registered
      profiles/few-shots and adds no Provider classification call.
- [ ] Inclined/curved/non-rectangular/Grid/structural-analysis requests return
      stable unsupported outcomes without mutation.
- [ ] Ambiguous Storey, placement, non-square orientation and explicit
      Type/material requests return structured clarification without
      publication.
- [ ] Mixed Beam+Column+Window+Door success publishes atomically; an injected
      failure in any operation publishes none.
- [ ] Reopened structural geometry passes 5 mm axis-point, 0.1 degree
      direction/tilt and 1 mm section/member-dimension thresholds.
- [ ] Reopened outputs pass exact product, containment and Type cardinality plus
      exact requested Material/Pset L2 checks.
- [ ] Full-model preservation remains fail-closed and does not reduce entity,
      geometry, relationship or semantic scope to make a benchmark pass.
- [ ] Public live inputs contain no original structural GUID, STEP ID, private
      geometry snapshot or Gold ChangeSet leakage.
- [ ] A real DeepSeek complete Beam+Column request publishes an IFC2X3 result
      that independently reopens and passes strict L0/L1/L2/preservation.
- [ ] A real DeepSeek clarification request stops without a publishable IFC.
- [ ] Both live proofs record genuine Provider/model evidence and
      `synthetic_fallback=false`.
- [ ] A family-neutral proof validator independently verifies every claimed
      success artifact instead of trusting saved evaluation JSON.
- [ ] The final report states that `d7n` and `vvo` prove cross-scene BIMNet
      behavior, not independent authoring-family compatibility.
- [ ] Phase 12 implementation, Proof, validation report, summaries,
      REQUIREMENTS/ROADMAP/STATE updates are committed independently and Phase
      13 is not started.

## Ambiguity Report

| Dimension | Score | Min | Status | Notes |
|-----------|------:|----:|:------:|-------|
| Goal Clarity | 0.96 | 0.75 | ✓ | Both structural families, publication outcome and strict evidence are explicit |
| Boundary Clarity | 0.95 | 0.70 | ✓ | Geometry, mutation, analysis, Grid, L3 and Phase 13 exclusions are enumerated |
| Constraint Clarity | 0.91 | 0.65 | ✓ | Type fallback, optional material, retrieval authority, token/data boundaries and thresholds are locked |
| Acceptance Criteria | 0.92 | 0.70 | ✓ | Real scenes, numeric L1 limits, exact L2, atomicity and live Proof are pass/fail |
| **Ambiguity** | **0.06** | **≤ 0.20** | **✓** | All individual dimensions meet their gates |

## Interview Log

| Round | Perspective | Question summary | Decision locked |
|-------|-------------|------------------|-----------------|
| 1 | Researcher | Is property RAG Window-only and what structural evidence exists? | PSD corpus is generic; Beam/Column production indexing, Type, authoring and live evidence are missing. Eleven BIMNet IFC2X3 scenes contain structural products. |
| 2 | Simplifier | What is the minimum useful structural geometry? | Horizontal straight Beam and vertical straight Column with rectangular profiles only. |
| 3 | Boundary Keeper | What is the canonical placement and what stays out? | Storey-local center axes; no formal Grid, inclined/curved/profile expansion, analysis model or existing-member mutation. |
| 4 | Failure Analyst | How should material and LLM contract violations behave? | Material is optional and authority-bound; unknown synonyms/wrong nesting fail rather than creating compatibility. |
| 5 | Seed Closer | What happens without Type reuse intent, and what makes structural L1 pass? | Generate a dedicated deterministic Type; use 5 mm axis-point, 0.1 degree direction/tilt and 1 mm section/member-dimension thresholds. |

---

*Phase: 12-beam-and-column-operations*
*Spec created: 2026-08-03*
*Next step: $gsd-plan-phase 12 — research, validation architecture and executable planning*
