# Phase 7: IFC Retrieval Index and Target Resolution - Context

**Gathered:** 2026-07-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 builds a local, versioned IFC2X3 retrieval index and resolves a
structured `TargetQuery` into deterministic, explainable target candidates.
It publishes bounded target context for later Agent stages, but does not call
the Provider, generate a ChangeSet, modify IFC, or decide L1/L2 success.

Initial editable target coverage is limited to `IfcWall` (including registered
subtypes), `IfcDoor`, and `IfcWindow`. `IfcSpace` is indexed as spatial and
relationship context; making spaces editable and adding other element classes
belong to later operation-expansion work.

</domain>

<decisions>
## Implementation Decisions

### Initial class coverage and extensibility

- **D-01:** Phase 7's initial editable target records cover Wall, Door, and
  Window. The index and query contracts must not be hard-coded to Window or
  Wall-only field layouts.
- **D-02:** `IfcSpace` is the default representation of a room and is indexed
  for name, long name, storey, boundaries, adjacency, and containment evidence.
  A user may explicitly describe a different semantic interpretation; the
  query must preserve that wording and route it through a registered adapter
  rather than silently forcing it into the default room meaning.
- **D-03:** All indexed entities share an `ElementRecord` skeleton containing
  identity, aliases, spatial evidence, relationships, geometry summary,
  properties, provenance, and typed `facets`.
- **D-04:** New element families attach through registered index, query,
  evidence, and context-projection adapters. Adding Wall, Space, Opening,
  structural, or other facets must not require a parallel retrieval pipeline.

### Identity and damaged-model diagnostics

- **D-05:** Bare IFC `GlobalId` is the canonical binding when valid. Name,
  LongName, Tag, ObjectType, type name, storey, grid/space, direction,
  relationships, and geometry are complementary evidence, never universal
  keys individually.
- **D-06:** Missing, malformed, or duplicate GlobalIds may receive internal
  diagnostic record IDs so the problem can be reported, but those IDs cannot
  be treated as reliable IFC identities or silently authorized for mutation.
- **D-07:** The same structural and identity integrity checks apply to
  user-supplied IFC and IFC produced by this system. Invalid/damaged input is
  classified with structured diagnostics; invalid produced IFC cannot be
  published as a successful result.

### Property sets and attribute intent

- **D-08:** The database retains as many parseable property sets and quantities
  as practical, including original names, values, IFC value types, units,
  owning entity/type, and provenance. Phase 7 must not discard properties only
  because the first Window operation does not use them.
- **D-09:** Complete stored properties are not automatically sent to the
  Provider. The request-understanding Agent extracts property-related user
  intent into structured JSON; deterministic context projection then includes
  only relevant existing properties, definitions, and candidate evidence.
- **D-10:** A later ChangeSet/compiler path may apply requested attribute
  changes only after schema, IFC type, unit, applicability, scope, and operation
  validation. The LLM supplies semantic intent, not unchecked low-level IFC
  property objects.

### Database and index lifecycle

- **D-11:** Use an embedded SQLite database from the first Phase 7
  implementation rather than a JSON sidecar as the primary index store. It
  must require no external database service.
- **D-12:** Keep storage behind a repository/backend interface so SQLite can be
  replaced or supplemented later without changing `ElementRecord`,
  `TargetQuery`, or candidate contracts.
- **D-13:** Bind every index database to source IFC SHA-256, IFC schema,
  index-schema version, extractor version, and creation metadata. A changed IFC
  or incompatible index version triggers a deterministic full rebuild in
  Phase 7.
- **D-14:** Incremental ChangeSet-driven index updates are deferred until scale
  measurements justify them; the interface may reserve revision metadata but
  Phase 7 correctness relies on full rebuilds.

### TargetQuery and constraint semantics

- **D-15:** `TargetQuery` is versioned and records explicit selectors,
  normalized selectors, requested operation/capability, attribute intent, and
  provenance separately. Missing selectors are not synthesized.
- **D-16:** Full natural-language-to-`TargetQuery` Agent behavior belongs to
  Phase 9. Phase 7 remains Provider-independent and uses structured queries
  plus limited deterministic parsing fixtures.
- **D-17:** Explicit GUID, IFC class, storey, and host/containment requirements
  are hard constraints. Other fields normally contribute evidence, but an
  explicitly mandatory grid, space, direction, relationship, or geometry
  statement becomes a hard constraint.
- **D-18:** Conflicting selectors produce a structured conflict result. An
  exact GUID does not silently override a conflicting class, storey, name, or
  location statement.

### Retrieval, ranking, and ambiguity

- **D-19:** Retrieval order is deterministic: exact GUID; class/capability and
  other hard filters; identity aliases; storey/grid/space/relationship;
  direction and relative position; geometry compatibility; optional semantic
  retrieval last.
- **D-20:** Phase 7 uses frozen, versioned scoring rules with field-level
  evidence. Resolution requires all hard constraints to pass, a uniquely best
  candidate under a tested margin policy, and no conflict.
- **D-21:** Zero matches, ambiguous matches, selector conflicts, and unsupported
  geometry/capability are first-class results. The system never silently picks
  the first sorted candidate.
- **D-22:** Alias normalization may normalize case, whitespace, punctuation,
  and controlled vocabulary while preserving original values and provenance.
  Bilingual synonyms live behind an extensible normalizer rather than core
  hard-coded target rules.

### Engineering position evidence

- **D-23:** Position evidence may combine wall-axis offsets, relative length,
  grids, storey, nearby spaces, local/world coordinates, facade/side, and
  distances to corners or existing openings. Missing required position facts
  cause clarification rather than invention.
- **D-24:** Wall-local evidence includes axis start/end coordinates, direction
  vector, coordinate basis, and a readable orientation description. Human
  phrases such as "from the west end" are normalized to explicit local-axis
  parameters without relying on an unexplained `wall_local_start`.
- **D-25:** Existing `IfcOpeningElement` records preserve explicit host wall,
  filling element, and geometry relationships. The current IFC is the only
  authority for what opening exists; benchmark mutation ground truth remains
  private evaluator evidence.
- **D-26:** Curved, segmented, free-form, or otherwise unsupported wall
  geometry is indexed and classified as approximate/unsupported; it is never
  silently straightened or treated as having full straight-wall positioning
  capability.

### Vector retrieval boundary

- **D-27:** Phase 7 defines a pluggable vector-retriever interface but ships
  with it disabled and with no embedding or vector-database dependency.
- **D-28:** Future embeddings operate on compact `ElementSearchDocument`
  records, not raw IFC JSON. Vector results may add recall or soft ranking only
  after hard structural constraints and can never override exact conflicts.
- **D-29:** Candidate evidence reserves retriever name, model/index version,
  source score, fused score, and matched fields so later vector experiments are
  auditable.

### Bounded Agent context

- **D-30:** The local database may be comprehensive, but Provider context is an
  operation- and intent-aware projection. It contains the resolved entity or
  deterministic top candidates, relevant properties/relationships/geometry,
  provenance, coordinate basis, and explicit budget metadata.
- **D-31:** Default normal context is top-5; diagnostic evidence may retain
  top-10. Both candidate count and canonical UTF-8 byte/token estimates are
  bounded, and budget reduction cannot drop the best exact match silently.
- **D-32:** Every candidate includes positive, negative, and unavailable
  field-level evidence rather than only one opaque score.

### Acceptance behavior

- **D-33:** Deterministic tests cover exact GUID, combined selectors,
  duplicate-name disambiguation, conflicts, abstention, repeatable ranking,
  invalid identity diagnostics, property retention/projection, and context
  budgets.
- **D-34:** `LargeBuilding.ifc` is the primary realistic Phase 7 sample; small
  synthetic fixtures provide controlled ambiguity and corruption cases.
- **D-35:** At least one `IfcSpace` query proves that spatial context is not
  encoded as a Wall-only special case, without claiming Space mutation support.
- **D-36:** The baseline retrieval flow must pass completely with vector search
  disabled.

### the agent's Discretion

- Exact normalized SQLite table layout, migration mechanism, indexes, and
  transaction boundaries, provided the public contracts and version bindings
  above remain stable.
- Exact initial deterministic weights, tie margin, and geometry tolerances,
  provided they are versioned, evidenced, and frozen by tests rather than
  hidden heuristics.
- Exact adapter class names and module layout, provided future element families
  do not require duplication of the common indexing and retrieval pipeline.

</decisions>

<specifics>
## Specific Ideas

- The final product remains: existing/damaged IFC + user text -> local target
  resolution -> Agent semantic ChangeSet -> deterministic IFC -> L1/L2 evidence.
- A comprehensive local property index and a compact Provider prompt are not
  competing designs: the Agent's extracted property intent selects the narrow
  projection from the database.
- Engineering target language should retain GUID, model names/tags, storey,
  grid/space, readable direction, and relative geometry together rather than
  forcing users to know one technical identifier.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase and milestone contracts

- `.planning/PROJECT.md` - v1.1 product goal, mandatory L1/L2 boundary, and
  hybrid target-selector decision.
- `.planning/REQUIREMENTS.md` - TGT-01 through TGT-05 and traceability to
  Phase 7.
- `.planning/ROADMAP.md` - fixed Phase 7 goal, dependencies, and success
  criteria.

### IFC repair design authority

- `docs/validation/ifc2x3-changeset/target-retrieval-design.md` - target
  evidence, index, query, ranking, database, property projection, and vector
  extension contract.
- `docs/validation/ifc2x3-changeset/design.md` - public/private boundary,
  operation registry, compact context, straight-wall capability, and
  LargeBuilding fixture.
- `docs/validation/ifc2x3-changeset/ground-truth-comparison.md` - current
  Window repair pipeline and the L1/L2/L3 distinction exposed by direct ground
  truth comparison.

### Existing machine contracts

- `schemas/agent/ifc-repair-context-0.1.schema.json` - current public context
  schema that Phase 7 must version rather than mutate silently.
- `schemas/agent/ifc-repair-changeset-0.1.schema.json` - downstream semantic
  ChangeSet binding consumed after target resolution.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `src/text2ifc_ifc_repair/context.py`: current bounded context serializer,
  IFC fingerprint binding, straight-wall candidate projection, and explicit
  not-found/ambiguous failures.
- `src/text2ifc_ifc_repair/registry.py`: existing operation capability registry
  pattern that can be complemented by index/query/projection adapters.
- `src/text2ifc_ifc_repair/geometry.py`: straight-wall axis, dimensions, and
  opening-position evidence reusable by Wall facets.
- `src/text2ifc_ifc_repair/provider_stage.py`: validates that Provider target
  IDs and scope are drawn from public context.

### Established Patterns

- Context is canonicalized and measured before Provider use.
- Registry-owned operation schemas keep common orchestration independent of
  Window-specific parameters.
- Base IFC SHA-256 binds public context and ChangeSet application.
- Ambiguous same-name Wall candidates already fail deterministically instead
  of relying on sort order.

### Integration Points

- Replace the current storey-plus-exact-Name scan in `context.py` with the
  versioned index/query service while preserving context validation and budget
  behavior.
- Operation registry target classes and capability constraints inform hard
  candidate filters; retrieval evidence feeds the existing public context and
  Provider binding checks.
- Phase 9 request understanding will produce `TargetQuery`; later operation
  handlers consume only resolved GlobalIds and validated attribute intent.

</code_context>

<deferred>
## Deferred Ideas

- Implement and benchmark vector retrieval in Phase 13 only if structured and
  lexical retrieval exposes measured recall gaps.
- Full natural-language Agent orchestration is Phase 9.
- Space mutation and target families beyond Wall, Door, and Window are later
  operation-expansion work.
- Incremental index maintenance is deferred until scale evidence justifies it.
- Curved/free-form wall modification and L3 authoring/identity exactness remain
  outside the v1.1 Phase 7 capability claim.

</deferred>

---

*Phase: 07-ifc-retrieval-index-and-target-resolution*
*Context gathered: 2026-07-19*
