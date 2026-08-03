# Phase 12: Beam and Column Operations - Context

**Gathered:** 2026-08-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 12 proves that the common IFC2X3 ChangeSet architecture can create
non-opening structural elements. It registers `add_beam` and `add_column`,
extends the existing generic property-knowledge and semantic-authoring path to
`IfcBeam` and `IfcColumn`, and closes both operations with deterministic and
real DeepSeek L0/L1/L2 evidence.

The phase reuses the frozen two-stage RepairIntent-to-Bound-ChangeSet workflow,
private Ground Truth isolation, Storey policy, preservation gate and operation
Registry. It does not redesign the Window, Opening or Door families and does
not start the Phase 13 large-context experiment.

</domain>

<decisions>
## Implementation Decisions

### Structural geometry

- **G-01:** The first release supports rectangular sections only.
- **G-02:** A member center axis is the only canonical placement reference.
  Profile corners, support faces and raw IFC placement nodes are not public
  placement authorities.
- **G-03:** `add_beam` supports a straight horizontal Beam in any direction in
  the selected Storey's XY plane. It is not restricted to global or Storey X/Y
  alignment.
- **G-04:** `add_column` supports a straight vertical Column only. Inclined
  Columns are unsupported in this release.
- **G-05:** A Beam axis start and end are the centers of its two end faces.
  `width_mm` is horizontal and perpendicular to the axis; `height_mm` is
  vertical. Section rotation about the Beam axis is unsupported.
- **G-06:** A Column uses vertical axis base and top points plus
  `width_mm`/`depth_mm`. A non-square Column needs an explicit orientation or
  uniquely resolved orientation evidence. Missing orientation is clarified,
  not defaulted.
- **G-07:** All public and ChangeSet dimensions use millimetres. Axis extent is
  the sole length/height authority; a conflicting scalar length or height is
  rejected.
- **G-08:** Beam/Column contact and intersection at legitimate support
  locations is allowed. The system does not auto-trim, extend, join or avoid
  clashes. Exact duplicate and overlapping same-axis creation requests are
  deterministically rejected.
- **G-09:** Inclined or curved members, round/I/H/arbitrary/variable profiles
  and arbitrary section rotation are explicit capability rejections.

### Placement, containment and physical relationships

- **P-01:** Public placement is expressed in the selected Storey's local
  coordinate system. The Provider never authors low-level IFC placement
  entities.
- **P-02:** The first release accepts either explicit Storey-local coordinates
  or a uniquely resolved existing Beam/Column center-axis reference.
- **P-03:** Formal `IfcGrid`/`IfcGridAxis` indexing, intersection resolution
  and placement are deferred. Grid labels are not silently treated as
  coordinates.
- **P-04:** A Beam is contained in the explicitly selected
  `IfcBuildingStorey`.
- **P-05:** A Column is contained in the Storey containing its axis base. A
  Column that reaches another Storey is not automatically split or multiply
  contained.
- **P-06:** Ambiguous Storey, support, member, endpoint or orientation evidence
  produces structured clarification.
- **P-07:** Phase 12 creates physical BIM relationships only: spatial
  containment, exact Type binding, authorized material association and
  explicitly requested property relationships.
- **P-08:** It does not create structural analysis members, loads, nodes,
  ports, `IfcRelConnectsStructuralMember`, automatic Beam-to-Column
  connectivity or member openings.

### Type, material and semantic authoring

- **T-01:** Every created Beam or Column binds an `IfcBeamType` or
  `IfcColumnType`.
- **T-02:** A Type is either an explicitly authorized, uniquely resolved exact
  existing Type or a dedicated deterministic Type generated from authorized
  parameters. When no Type reuse is requested, the compiler creates the
  dedicated deterministic Type without asking for clarification; the generated
  Type identity and label are compiler policy, not inferred user facts.
- **T-03:** Exact Type reuse preserves the Type unchanged. A mapped
  representation or size conflict is clarified or rejected; existing Type
  geometry is never silently scaled, rewritten or cloned into a guessed
  corrected Type.
- **T-04:** Material is optional. If the request supplies no material and does
  not explicitly authorize exact reuse of a Type that already carries
  inherited material semantics, the operation creates no material association
  and does not clarify merely because material is absent.
- **T-05:** Explicit material requests are resolved deterministically.
  Explicit exact Type reuse preserves material semantics already inherited
  through that exact Type but does not copy an occurrence-direct material
  association. A conflict between an explicit material and the exact reused
  Type is clarified.
- **T-06:** The first release authors a direct `IfcMaterial` only. It may reuse
  a uniquely resolved existing material or create one with the exact
  user-authorized label. Names such as `C30` or `steel` do not authorize
  inferred strength, grade or other properties.
- **T-07:** Optional Psets and quantities are not generated just because they
  commonly occur on structural members. Supported properties explicitly
  requested by the user are authored and validated.
- **T-08:** Properties on newly created members use the existing
  operation-neutral `semantic_assignments` path and are applied atomically to
  the created semantic role. There is no Beam/Column-specific compatibility
  layer.

### Property knowledge and RAG completion

- **R-01:** The existing IFC2X3 PSD corpus remains the only property-schema
  authority. Phase 12 does not create a separate structural RAG architecture.
- **R-02:** Add `IfcBeam` and `IfcColumn` target index adapters and include
  `IfcBeamType` and `IfcColumnType` in Type indexing.
- **R-03:** Extend the generic occurrence-property and semantic-authoring
  support to Beam and Column, including class-specific applicability checks.
- **R-04:** Exact names, formally recorded aliases and canonical PSD
  definitions are authoritative. Keyword/vector retrieval is recall only and
  cannot independently authorize a property.
- **R-05:** Stage 2 receives only the resolved canonical Pset name, property
  name, IFC value type and exact value. Top-K results, embeddings and unresolved
  aliases never enter Stage 2.
- **R-06:** Operation prompts and few-shots explicitly cover
  `Pset_BeamCommon`, `Pset_ColumnCommon`, their canonical field shapes and
  invalid-key rejection.
- **R-07:** LLM feedback is not a compatibility contract. If a live model emits
  an unknown synonym or incorrect nesting, preserve the failure, audit whether
  the prompt/few-shot contract was sufficient, and only then discuss a
  deterministic program change. Do not add aliases merely to accept that
  output.
- **R-08:** Formal acceptance exercises at least one natural-language
  `LoadBearing=true` request for each of Beam and Column.

### Stage routing and operation boundaries

- **O-01:** The only new geometry operations are `add_beam` and `add_column`.
  Existing generic property authoring remains generic.
- **O-02:** Stage 1 classifies the family and action inside every
  RepairIntent operation. The runtime then selects only the relevant operation
  profiles, schemas, constraints and few-shots for resolution and Stage 2.
  Classification does not add another Provider call.
- **O-03:** A request that creates both families yields explicit Beam and
  Column intents compiled into one atomic ChangeSet.
- **O-04:** Common orchestration remains free of Beam-, Column-, Window- and
  Door-specific fields. Family fields exist only inside registered operation
  contracts.
- **O-05:** Existing member deletion, replacement, movement, resizing and
  Type mutation are out of scope.
- **O-06:** Frozen Window/Opening/Door workflows, geometry thresholds, Ground
  Truth isolation and Storey policy remain unchanged.

### Failure and clarification policy

- **F-01:** Missing or ambiguous Storey, axis, rectangular dimensions or
  non-square Column orientation produces a structured clarification. An
  explicit Type-reuse request that resolves to zero/multiple candidates or
  conflicts with requested geometry also clarifies. Absence of Type-reuse
  intent selects a dedicated deterministic Type; missing optional material
  alone does not clarify.
- **F-02:** Unsupported profiles, inclined/curved members, Grid placement and
  structural-connection requests return stable deterministic capability codes.
- **F-03:** Unknown keys, synonymous keys and incorrect nesting fail the
  canonical schema. The normalizer does not absorb them.
- **F-04:** Multiple matching Types, materials, Storeys or reference members
  stop for clarification rather than selecting by ranking.
- **F-05:** Failed audit, application, reopen, L0, L1, L2 or preservation
  leaves no publishable repaired IFC. Diagnostic candidates and the original
  input remain available.

### Validation and live proof

- **V-01:** The primary real IFC2X3 acceptance model is
  `dataset/ifc/test/d7n.ifc`, which contains 10 Beams and 15 Columns. A
  deterministic damage case removes one member of each family and keeps
  original identities and Gold facts private.
- **V-02:** `dataset/ifc/train/vvo.ifc` is the secondary compatibility scene.
  It exercises six Beams, five Columns, Beam swept-solid geometry, Column
  mapped representations and mixed material presence. These two scenes are
  both BIMNet and must not be described as independent authoring families.
- **V-03:** Acceptance includes a mixed Window/Door/Beam/Column atomic
  ChangeSet on a suitable real model. Injected failure in any operation must
  prevent publication of the whole transaction.
- **V-04:** RAG/semantic acceptance covers a natural-language Beam property and
  Column property and proves their canonical PSD applicability and IFC value
  types.
- **V-05:** Real DeepSeek UAT includes one complete Beam+Column request and one
  clarification request. Synthetic or prerecorded output cannot replace
  either path.
- **V-06:** Live output must be reopened and independently pass strict L0, L1,
  L2 and global preservation. The result is not successful merely because the
  Provider returned valid JSON or the applicator wrote a file.
- **V-06A:** Structural L1 uses the established precision grade adapted to
  center-axis members: each axis endpoint/base/top is within 5 mm, axis
  direction/horizontal-or-vertical tilt is within 0.1 degree, and section plus
  member length/height dimensions are within 1 mm. Product, containment and
  Type relationship cardinalities are exact. Requested Material/Pset facts
  must match canonical name, IFC value type, value and semantic scope exactly.
  Approximate volume agreement cannot substitute for these checks.
- **V-07:** The Phase 11 proof curator/validator is evolved into a
  family-neutral validator that checks raw response, canonical intent, Bound
  ChangeSet, audit, repaired IFC, evaluation, prompt hashes, Provider/model
  evidence, private-Gold isolation and non-target preservation.
- **V-08:** Synthetic fixtures may cover deterministic schema, geometry and
  rejection tests but are never an acceptance or live-proof fallback.
- **V-09:** Completion updates the Phase 12 validation report, Summary,
  ROADMAP/REQUIREMENTS status and STATE in an independent Git checkpoint.
  Phase 13 does not begin.

### the agent's Discretion

- Internal module/file boundaries for the two handlers, provided all new
  family behavior enters through the existing registries and operation-neutral
  semantic authoring.
- Deterministic entity naming and GUID seed details, provided they are stable,
  do not leak private Gold and remain subordinate to the frozen semantic
  contracts.
- The exact implementation layout of the family-neutral proof validator and
  focused test files.

</decisions>

<specifics>
## Specific Ideas

- The governing rule is: do not make the program compatible with arbitrary LLM
  feedback. First prove that the selected prompt, constraints and few-shots
  state the canonical contract clearly; preserve any violation as evidence.
  Programmatic normalization is discussed only after the prompt contract is
  shown to be sufficient.
- Property retrieval is already class-generic at the IFC2X3 PSD corpus layer.
  Phase 12 completes the missing Beam/Column index, Type, authoring and live
  evidence path instead of rebuilding RAG.
- The user explicitly chose rectangular sections and center-axis placement,
  and made material optional unless it is explicitly requested or inherited
  through explicitly authorized exact Type reuse.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project status and phase requirements

- `.planning/ROADMAP.md` - Phase 12 goal, dependencies and success criteria.
- `.planning/REQUIREMENTS.md` - `OPS-03` Beam and `OPS-04` Column
  requirements.
- `.planning/STATE.md` - Current checkpoint, frozen system constraints and
  Phase 11 handoff.

### Property knowledge and semantic authority

- `.planning/phases/10.2-ifc2x3-property-knowledge-retrieval-and-resolution/10.2-SPEC.md`
  - IFC2X3 PSD registry, applicability-filtered retrieval, typed resolution
  and non-authoritative vector recall.
- `.planning/phases/10.2-ifc2x3-property-knowledge-retrieval-and-resolution/10.2-VALIDATION.md`
  - Deterministic and live property-knowledge evidence and the existing
  family-support boundary.
- `.planning/phases/10.5-window-occurrence-fidelity-and-validation-acceleration/10.5-CONTEXT.md`
  - Exact Type/occurrence authority, semantic bundles, atomicity and L2
  preservation decisions that remain common.

### Operation architecture and frozen workflow

- `.planning/phases/11-wall-opening-and-door-operations/11-SPEC.md` - Frozen
  two-stage routing, operation profile, clarification, Type and proof
  contracts.
- `.planning/phases/11-wall-opening-and-door-operations/11-CONTEXT.md` -
  Confirmed Window/Opening/Door boundaries that Phase 12 cannot redesign.
- `.planning/phases/11-wall-opening-and-door-operations/11-VALIDATION.md` -
  Strict L0/L1/L2 and real-Provider validation rules.
- `docs/validation/ifc2x3-changeset/design.md` - Common ChangeSet envelope,
  Registry seam, transaction application, comparator and the planned
  `add_beam`/`add_column` capability boundary.
- `docs/validation/ifc2x3-changeset/phase11-door-validation-report.md` - Most
  recent real DeepSeek proof, independent strict reopen validation and known
  proof-quality failure modes.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `src/text2ifc_ifc_repair/registry.py`: `OperationDefinition` and
  `OperationRegistry` already isolate target schema, parameter schema,
  context, audit, application, comparison, prompt profile, conflict domain and
  semantic roles.
- `src/text2ifc_ifc_repair/semantic_authoring.py`: generic bound Type,
  occurrence Pset, quantity, material and relationship authoring already
  targets roles created by a geometry operation.
- `src/text2ifc_knowledge/property_search.py`: class-filtered IFC2X3 PSD
  retrieval is generic and should be extended through registrations, not
  forked.
- `src/text2ifc_ifc_repair/index_adapters.py` and
  `src/text2ifc_ifc_repair/indexer.py`: the current adapter and Type-index
  seams are the direct Beam/Column integration points.
- `scripts/ifc_repair/curate_phase11_live_proof.py`: starting point for the
  family-neutral strict live-proof validator.

### Established Patterns

- Operation applicators create low-level IFC placement, representation,
  identity and relationships deterministically after the Provider supplies
  bounded semantic parameters.
- Exact Type reuse is unchanged and fail-closed; generated Types are dedicated
  and deterministic.
- Requested semantics are bound before apply and written through declared
  operation semantic roles.
- Benchmark Gold is available only to post-repair comparison and never to
  RepairIntent, Provider prompts, Stage 2 or predicted ChangeSets.

### Integration Points

- Register Beam/Column handlers in
  `src/text2ifc_ifc_repair/operations/__init__.py` without adding central
  routing branches.
- Extend the default target adapter registry and Type enumeration currently
  limited to Wall, Opening, Door, Window, Space and their current Type classes.
- Extend the supported class list of
  `src/text2ifc_ifc_repair/operations/occurrence_property.py`; its current
  contract deliberately rejects `IfcBeam` and `IfcColumn`.
- Add structural operation profiles, prompt constraints and few-shots through
  the same selected-profile path used by Door.

</code_context>

<deferred>
## Deferred Ideas

- Inclined, curved, round, I/H, arbitrary and variable-section members.
- Formal `IfcGrid`/`IfcGridAxis` indexing and grid-intersection placement.
- Structural analysis models, loads, ports, automatic joints and analytical
  connectivity.
- Existing Beam/Column deletion, replacement, movement, resizing and Type
  mutation.
- Independent non-BIMNet authoring-family acceptance when an authorized real
  IFC2X3 source is available.
- Phase 13's 128k/large-context experiment.

</deferred>

---

*Phase: 12-beam-and-column-operations*
*Context gathered: 2026-08-03*
