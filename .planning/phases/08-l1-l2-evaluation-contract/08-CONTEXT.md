# Phase 8: L1/L2 Evaluation Contract - Context

**Gathered:** 2026-07-19
**Status:** Ready for specification and planning

<domain>
## Phase Boundary

Phase 8 defines and implements the versioned evaluation contract that decides
whether an applied IFC repair has achieved mandatory L1 physical/relationship
correctness and mandatory L2 BIM semantic fidelity. It supports evaluator-only
private Ground Truth in benchmark runs and non-Gold evidence in production
runs. It does not add natural-language orchestration, repair missing Window
semantics, call a Provider, or add Door/Beam/Column mutation operations.

</domain>

<decisions>
## Implementation Decisions

### Success statuses and aggregation

- **D-01:** Every level and check uses one of `passed`, `failed`, `partial`,
  `not_required`, or `not_evaluable`; unknown or unavailable facts never become
  implicit passes.
- **D-02:** `complete_repair_success` requires application success and every
  mandatory operation's L1 and L2 status to be `passed`. `not_required` may
  pass only where the versioned policy explicitly marks that check optional.
  `partial`, `not_evaluable`, and `failed` make the complete result false.
- **D-03:** Reports are hierarchical: run -> application/preservation -> each
  operation -> L1/L2/L3 -> checks and evidence. One mandatory operation failure
  fails the run; the unified ChangeSet remains the evaluation unit.
- **D-04:** L3 authoring/identity exactness is emitted as observations with
  level status `not_required` for v1.1 and never contributes to success.

### Contract versioning

- **D-05:** Introduce a new evaluation schema version rather than silently
  changing `text2ifc/ifc-repair-evaluation/0.1`. Existing 0.1 evidence remains
  readable; new runs use the new L1/L2-aware version.
- **D-06:** Policies, check IDs, tolerances, evidence source kinds, and
  aggregation semantics are versioned and machine-readable.

### L1 authority and preservation

- **D-07:** L1 independently validates geometry, Host/Opening/Filling topology,
  containment, requested scope, preservation, IFC readability/schema, and
  absence of duplicate or unexpected chains.
- **D-08:** Allowed changes are derived by cross-checking three sources:
  Operation Registry capability, ChangeSet-declared scope, and Applicator
  actual changes. The Evaluator does not trust the Applicator's self-reported
  changed IDs as sole authority.
- **D-09:** Unexpected deletion, creation, modification, relationship drift, or
  tolerance violation is a structured L1 failure with before/after evidence.

### L2 policy and conditional semantic facts

- **D-10:** Each operation registers an L2 policy whose checks are classified
  as `required`, `conditional`, or `informational`; operation-specific policies
  extend a common evaluator instead of creating parallel report pipelines.
- **D-11:** Initial Window required semantics include compatible type,
  Host/Storey, `IsExternal`, and key dimensions/quantities. Explicitly requested
  semantic attributes are required.
- **D-12:** Material, Classification, Psets, and other instance semantics are
  conditionally mandatory. If the private original in benchmark mode, explicit
  user text, surviving damaged/current IFC facts, or an approved Prototype/Type
  establishes that a fact exists, the repair output must contain the
  corresponding semantic value/Pset and L2 must check it.
- **D-13:** If no authorized evidence source establishes Material/Pset/
  Classification presence, that check is `not_required`, not `failed` or
  `not_evaluable`. Absence must be disclosed through source evidence.
- **D-14:** Name, Tag, and other authoring labels are conditional L2 facts only
  when requested or semantically established; exact original identity,
  GlobalId, STEP ID, representation, placement construction, and bytes remain
  L3 observations.

### Production evidence authority

- **D-15:** Production L2 evidence precedence is: explicit user request;
  surviving target/Host/Type/relationship facts; approved Prototype/Type;
  versioned deterministic operation policy. Provenance is retained per fact.
- **D-16:** An approved same-type Prototype may support `passed` only through
  an explicit policy rule with compatible applicability. Arbitrary nearby
  entities, names, or LLM/BIM common knowledge cannot supply missing facts.
- **D-17:** A mandatory fact with no reliable source is `not_evaluable`, makes
  complete success false, and states what evidence is missing.

### Benchmark Ground Truth isolation

- **D-18:** Benchmark mode may use the private mutation manifest and original
  IFC after Provider/application stages to map deleted/recreated semantic roles
  and evaluate equivalence. Gold GUID reuse is not an L1/L2 requirement.
- **D-19:** Provider input, public context, TargetQuery, ChangeSet generation,
  and production evaluation never receive original Ground Truth or private
  mutation mappings.
- **D-20:** Benchmark evaluation produces a private detailed report that may
  contain original values and a public projection containing statuses,
  difference categories, and non-leaking evidence. Leakage tests scan the full
  Provider/public artifact boundary.

### Failed and non-evaluable artifacts

- **D-21:** A repaired IFC from `failed`, `partial`, or `not_evaluable` L1/L2
  may remain inside an immutable diagnostic evidence directory, but its
  terminal result is not successful and it cannot be presented or published as
  a successful repaired IFC.
- **D-22:** Phase 8 defines this status/publication contract; Phase 9 enforces
  it in the general IFC + text orchestrator.

### Phase acceptance scope

- **D-23:** Phase 8 delivers the common evaluation schema/model, aggregation,
  policy registry, production and benchmark evaluators, private/public report
  projection, Window as the first policy adapter, and deterministic tests.
- **D-24:** LargeBuilding must honestly reproduce the current outcome: L1
  passes, while L2 reports known instance Pset/quantity, `IsExternal`, material,
  and classification differences instead of allowing L1 to hide them.
- **D-25:** No real Provider call is required for Phase 8 acceptance. Frozen
  offline/current evidence and controlled fixtures are sufficient.

### the agent's Discretion

- Exact module names and normalized in-memory data structures, provided the
  public JSON contracts and check/status semantics remain stable.
- Exact new schema minor version and migration helper shape, provided 0.1 is
  not silently reinterpreted.
- Exact check grouping and evidence serialization, provided each result retains
  source, expected/actual state, provenance, applicability, and reason.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone and Phase 8 contracts

- `.planning/PROJECT.md` - mandatory L1/L2 boundary, private Ground Truth rule,
  and deferred L3 commitment.
- `.planning/REQUIREMENTS.md` - VAL-01 through VAL-05 and later WIN/PIPE scope.
- `.planning/ROADMAP.md` - fixed Phase 8 goal, dependency, and success criteria.

### Current evaluation evidence and design authority

- `docs/validation/ifc2x3-changeset/ground-truth-comparison.md` - verified L1
  successes, concrete L2 gaps, and L3 differences in the LargeBuilding Window
  case.
- `docs/validation/ifc2x3-changeset/design.md` - public/private boundary,
  registry design, transactional application, and validation expectations.
- `docs/validation/ifc2x3-changeset/target-retrieval-design.md` - Phase 7
  identity/property provenance that production evaluation may consume.
- `docs/validation/ifc2x3-changeset/phase7-validation-report.md` - verified
  target/index boundary inherited by Phase 8.

### Existing machine contracts

- `src/text2ifc_ifc_repair/compare.py` - current evaluation 0.1 aggregation and
  normalized damaged-vs-repaired preservation comparator.
- `src/text2ifc_ifc_repair/operations/window.py` - current independent Window
  L1 comparison adapter and tolerances.
- `src/text2ifc_ifc_repair/audit.py` - pre-application deterministic audit;
  must remain distinct from post-application evaluation.
- `src/text2ifc_ifc_repair/registry.py` - operation registration/dispatch
  extension pattern.
- `src/text2ifc_ifc_repair/workflow.py` - evidence bundle and terminal success
  integration point.
- `.planning/phases/07-ifc-retrieval-index-and-target-resolution/07-CONTEXT.md`
  - locked evidence, provenance, property, and damaged-identity decisions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `compare_ifc_models`: normalized GlobalId-based before/after preservation and
  representation snapshots reusable by L1 and L2 evidence builders.
- Window `comparison_adapter`: independently measures opening dimensions,
  placement, wall volume, void/fill topology, containment, and duplicates.
- `OperationRegistry`: already isolates Window-specific schemas and adapters;
  it can own evaluation policy adapters without changing common aggregation.
- Phase 7 index records: retain typed Psets, quantities, type, storey,
  relationships, and provenance for production evidence selection.
- Workflow evidence bundle: already writes evaluation JSON/report and immutable
  artifacts, so versioned private/public evaluation can attach here.

### Established Patterns

- Deterministic checks are authoritative; Provider/Audit cannot override them.
- IFC outputs are reopened and independently measured after application.
- Registry adapters keep the common pipeline independent of Window details.
- Source IFC hashes and structured evidence bind all stages.

### Integration Points

- Replace the current boolean aggregation in `evaluate_repair_application`
  with the versioned hierarchical result while retaining a compatibility
  projection for existing callers.
- Extend operation definitions with L1/L2 policy/evaluator hooks rather than
  hard-coding Window semantics in the common evaluator.
- Separate benchmark-private Ground Truth inputs from production inputs at the
  workflow boundary before writing public artifacts.
- Phase 9 consumes Phase 8 terminal status; Phase 10 uses the Window L2 report
  to implement missing semantic restoration.

</code_context>

<specifics>
## Specific Ideas

- User clarification: when the original or another authorized input establishes
  Material/Pset content, both the semantic request/generation path and repaired
  IFC must preserve the corresponding Pset/value and L2 must verify it. When no
  Material evidence exists, it is not a required check.
- L1 success must never be presented as complete BIM repair when L2 is partial,
  failed, or not evaluable.

</specifics>

<deferred>
## Deferred Ideas

- General natural-language repair orchestration and publication enforcement -
  Phase 9.
- Restoring the missing Window Psets, quantities, Material, Classification, and
  `IsExternal` semantics - Phase 10.
- Door, Opening-only, Beam, and Column semantic policies beyond contract-level
  extension fixtures - Phases 11 and 12.
- L3 authoring/identity exact restoration - outside v1.1.

</deferred>

---

*Phase: 08-l1-l2-evaluation-contract*
*Context gathered: 2026-07-19*
