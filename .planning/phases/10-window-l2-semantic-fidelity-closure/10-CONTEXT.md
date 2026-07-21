# Phase 10: Window L2 Semantic Fidelity Closure - Context

**Gathered:** 2026-07-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete the existing straight-wall Window repair pipeline from user IFC plus
natural-language request through two Agent stages, deterministic semantic
binding, one atomic ChangeSet, IFC2X3 application, mandatory Production L1/L2,
optional private benchmark comparison, and successful publication. Phase 10
proves this Window path before property RAG or additional entity families are
introduced.

</domain>

<spec_lock>
## Specification Lock

Requirements, boundaries, constraints, and acceptance criteria are locked by
`10-SPEC.md`. Planning may choose module/function names and task grouping but
must not move RAG into Phase 10, weaken L1/L2, expose Gold, or replace the one
bound ChangeSet with an unaudited side channel.

</spec_lock>

<decisions>
## Implementation Decisions

### Provider and semantic binding boundary

- **D-01:** Stage 2 receives a compact semantic summary plus an immutable
  manifest reference/hash, not the full Pset/quantity/material/classification
  assignment list.
- **D-02:** Stage 2 may receive the few semantic slots explicitly stated by the
  user. It cannot add or alter facts outside the authorized manifest.
- **D-03:** Provider output is a non-executable ChangeSet draft. A deterministic
  Binder validates it and produces the one canonical executable bound
  ChangeSet containing the expanded typed assignments.
- **D-04:** The bound ChangeSet is self-contained for audit on disk even though
  the expanded list was never sent through a Provider prompt.

### Window semantic authority and ownership

- **D-05:** Required Window facts are Type, Host, Storey, OverallWidth,
  OverallHeight, IsExternal, and normalized Base Quantities.
- **D-06:** Material, Classification, selected Psets, and explicit user facts
  are conditional: authority present means author and verify; verified absence
  means `not_required`; conflict means fail/clarify.
- **D-07:** Formal current-IFC relationships are preferred. Compatible evidence
  associated with the explicitly/formally authorized Window Type may support a
  Window policy rule only with recorded cohort/applicability evidence and no
  conflicting values. It remains occurrence/cohort evidence, never Type facts.
- **D-08:** Existing Material and Classification resources are reused; the new
  Window receives deterministic association relationships so unrelated shared
  relationships are not needlessly rewritten.
- **D-09:** Type-owned Psets remain on the Type and are observed through the
  formal type binding. The applicator does not duplicate them onto the Window.
- **D-10:** Name, Tag, Mark, original GUID and exporter identity are not L2
  requirements unless explicitly requested; authoring-exact restoration is L3.

### Policy and compatibility

- **D-11:** Window L2 policy 0.2 normalizes `BaseQuantities` and
  `Qto_WindowBaseQuantities`; source spelling remains visible in provenance.
- **D-12:** The abstract `window.instance -> instance:*` check is replaced by
  concrete facts. Historical policy/evaluation 0.1 remains versioned and is not
  relabelled.
- **D-13:** Explicit user values take precedence only for occurrence-overridable
  facts. A value incompatible with the authorized Type or operation contract
  requires clarification or fails closed.

### Pipeline acceptance

- **D-14:** Phase 10 is complete only when the LargeBuilding single-Window
  damaged IFC passes the public offline pipeline, Production L1/L2, and private
  benchmark L1/L2 without Gold reaching the public path.
- **D-15:** The four existing real DeepSeek paths remain the live UAT set:
  complete request, clarification-completed request, Type name without GUID,
  and dimensions followed by Type confirmation.
- **D-16:** Only application+reopen+L1+L2 all-pass may publish a successful IFC.
  Every other terminal state retains diagnostic evidence without false success.

### Deferred property retrieval

- **D-17:** IFC2X3 property knowledge ingestion, keyword/vector retrieval,
  confidence calibration, standard-property candidate clarification, and all
  custom-property confirmation belong to Phase 10.1.
- **D-18:** Phase 10 leaves generic semantic-slot and operation-registry seams
  that Phase 10.1 and later Door/Opening/Beam/Column operations can consume, but
  does not implement RAG or those operation families.

### the agent's Discretion

- Exact class/module names for the manifest, Binder, and generic authoring
  helpers, provided their public schemas and audit boundary match D-01..D-04.
- Exact deterministic relationship GlobalId namespace and internal sorting.
- Exact normalized quantity role name, provided both IFC2X3 source spellings
  are supported and provenance retains the original spelling.
- Exact plan/task split and fixture construction, provided acceptance runs use
  the real public API/CLI path and no Gold shortcut.

</decisions>

<specifics>
## Specific Ideas

- LargeBuilding source:
  `dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc`.
- Authorized Window Type: `IfcWindowStyle` GlobalId
  `2cXV28XOjE6f6irhu0CO_c`, Name `M_Fixed:0915 x 1830mm`.
- The original Type cohort has consistent `IsExternal=true`, Uniformat
  Classification, and Glass/Sash Material facts, while Level, StoreyName,
  Host, Name, Tag, and Mark remain occurrence-specific.
- CLI stdout stays compact; full manifest, bound ChangeSet, application,
  Production evaluation, optional private benchmark report, and Provider traces
  remain in the run directory.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Locked Phase 10 scope

- `.planning/phases/10-window-l2-semantic-fidelity-closure/10-SPEC.md` - locked
  requirements, boundaries, constraints, and acceptance criteria.
- `.planning/ROADMAP.md` - Phase 10 WIN-01/WIN-02 goal and milestone boundary.
- `.planning/REQUIREMENTS.md` - pending Window fidelity requirements and later
  OPS/SCALE separation.
- `.planning/PROJECT.md` - one IFC+text-to-ChangeSet+validated-IFC product goal.

### Upstream contracts

- `.planning/phases/08-l1-l2-evaluation-contract/08-SPEC.md` - mandatory L1/L2,
  conditional semantics, Production-vs-benchmark authority, and L3 boundary.
- `.planning/phases/08-l1-l2-evaluation-contract/08-CONTEXT.md` - source
  precedence and publication semantics.
- `.planning/phases/09-general-ifc-text-repair-orchestrator/09-CONTEXT.md` -
  two-stage Agent flow, one ChangeSet, clarification, and CLI/API artifacts.
- `.planning/phases/09.1-ifc-type-evidence-and-prototype-resolution-correction/09.1-CONTEXT.md`
  - first-class Type authority and no occurrence-to-Type aggregation.

### IFC repair evidence

- `docs/validation/ifc2x3-changeset/design.md` - Registry, transaction, public/
  private boundary, and evidence-bundle design.
- `docs/validation/ifc2x3-changeset/ground-truth-comparison.md` - concrete
  LargeBuilding L1 pass and L2 semantic differences.
- `docs/validation/ifc2x3-changeset/phase9.1-validation-report.md` - current
  four-path live UAT and exact Phase 10 handoff categories.

### Current machine seams

- `src/text2ifc_ifc_repair/operations/window.py` - Window operation schema,
  applicator, L1 adapter, and L2 policy 0.1.
- `src/text2ifc_ifc_repair/production_evidence.py` - authorized public semantic
  expectation construction.
- `src/text2ifc_ifc_repair/semantic_facts.py` - typed IFC semantic extraction
  and comparison.
- `src/text2ifc_ifc_repair/provider_stage.py` - Stage 2 prompt, draft parsing,
  fingerprint/scope/evidence binding.
- `src/text2ifc_ifc_repair/orchestrator.py` - application/evaluation/publication
  state machine.
- `schemas/agent/ifc-repair-changeset-0.1.schema.json` - historical geometry-only
  ChangeSet contract that must remain readable.
- `schemas/agent/ifc-repair-evaluation-0.2.schema.json` - current mandatory
  L1/L2 terminal contract.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `OperationDefinition` and `OperationRegistry` already isolate operation-owned
  schemas, application, comparison, Type classes, and evaluation policy.
- `ProductionEvidence` already resolves source precedence, applicability,
  conflicts, and per-operation facts without accepting Gold in its signature.
- `extract_ifc_semantic_facts` already reopens occurrences and extracts Psets,
  quantities, attributes, Host/Storey/Type, Material, and Classification.
- The Phase 9 Binder/Audit path already validates ChangeSet fingerprint, scope,
  request hash, evidence refs, and permitted conditions.
- The applicator already creates deterministic Window/Opening/Voids/Fills,
  Type binding, and Storey containment transactionally.

### Established Patterns

- JSON Schema-backed versioned public contracts precede behavior.
- RED/GREEN/REFACTOR freezes fail-closed behavior before implementation.
- Provider output is subordinate to deterministic Registry, Audit, application,
  reopen, Evaluation, and publication gates.
- Historical evidence is preserved by versioning rather than reinterpretation.

### Integration Points

- Add operation-scoped semantic manifest/binding hooks to the Registry instead
  of adding Window branches to the common orchestrator.
- Extend Stage 2 draft binding with manifest ref/hash and explicit slot refs;
  expand only after Provider validation.
- Apply semantic assignments inside the existing transaction before reopen and
  Evaluation 0.2.
- Feed the same authorized manifest to Production expected facts and the
  applicator, then independently re-extract repaired facts for L2.

</code_context>

<deferred>
## Deferred Ideas

- Phase 10.1: IFC2X3 property standard library, project property index,
  multilingual aliases, hybrid keyword/vector retrieval, confidence/margin
  calibration, candidate clarification, and mandatory confirmation for every
  custom property.
- Phases 11/12: opening-only, Door, Beam, and Column operations after the Window
  semantic-slot pipeline is proven.
- Phase 13 or later: scale benchmarks, 128k Provider input experiment, and any
  evidence-based vector authorization policy.
- Later: L3 exactness and curved/free-form wall mutation.

</deferred>

---

*Phase: 10-window-l2-semantic-fidelity-closure*
*Context gathered: 2026-07-21*
