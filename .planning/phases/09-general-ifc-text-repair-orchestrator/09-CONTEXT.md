# Phase 9: General IFC + Text Repair Orchestrator - Context

**Gathered:** 2026-07-20
**Status:** Ready for specification and planning

<domain>
## Phase Boundary

Phase 9 turns the Phase 7 target-index/resolution contracts and Phase 8
Evaluation 0.2 contract into one supported production entrypoint. Given a
user-supplied existing or damaged IFC2X3 file plus natural-language repair or
modification text, it produces a bound semantic ChangeSet, deterministically
applies it, evaluates the result, and either publishes a successful IFC with
evidence or returns an honest clarification/unsupported/failure state.

The phase generalizes orchestration; it does not manufacture damage, consume
private Ground Truth during generation, close the known Window L2 authoring
gaps, or add Opening/Door/Beam/Column operations.

</domain>

<decisions>
## Implementation Decisions

### Two-stage Agent contract

- **D-01:** Use two explicit Agent stages. Stage 1 converts user text into a
  versioned `RepairIntent` containing operation intent, `TargetQuery`, requested
  parameters, and attribute intents. Deterministic Phase 7 resolution runs
  before Stage 2 receives bounded resolved context and generates the unified
  ChangeSet.
- **D-02:** The ChangeSet Agent must never search raw IFC or bind an unresolved
  target. Every target ID, scope ID, evidence pointer, and base fingerprint is
  validated against the public resolved context before Audit/application.
- **D-03:** One run owns one unified ChangeSet transaction. It may contain one
  or more Registry-supported operation intents, but ambiguity, unsupported
  capability, or invalidity in any mandatory operation prevents partial
  application/publication.

### Clarification and resumable state

- **D-04:** Target ambiguity, selector conflict, missing required parameters,
  and user-selectable Prototype choice use one structured
  `clarification_required` state with reason code, question, candidate evidence,
  and allowed answer shape. No path silently selects the first candidate.
- **D-05:** The default terminal experience is an interactive repair session.
  It renders concise candidate identity, GUID, class, storey, position, and
  match evidence; the user can select a candidate, add natural-language detail,
  or cancel, after which the same run continues.
- **D-06:** Non-interactive CLI and Python callers receive the same structured
  clarification state instead of a prompt. A `run_id` plus a validated answer
  resumes the same persisted run without repeating already completed immutable
  stages.
- **D-07:** Interaction is scoped to one repair run and exits at a terminal
  result; Phase 9 does not introduce an unrelated always-on chat/REPL product.

### Public API, CLI, and artifacts

- **D-08:** A Python orchestration API/state machine is the single behavior
  authority. The CLI is a thin adapter for start, interactive continuation,
  non-interactive continuation, and result rendering; it must not contain a
  second repair pipeline.
- **D-09:** Human CLI mode displays short stage progress and a compact final
  summary. `--json` emits a stable, compact terminal result with status and
  artifact paths, not full Provider/context/evaluation payloads. `--quiet`
  suppresses non-error human progress.
- **D-10:** Detailed `RepairIntent`, `TargetQuery`, resolution, bounded public
  context, Provider attempts, ChangeSet, Audit/application, public Evaluation
  0.2, hashes, and diagnostics live in a non-overwriting run directory. The
  input IFC is never modified in place.
- **D-11:** Only Evaluation 0.2
  `successful_artifact_publishable=true` produces the canonical successful IFC
  path. Every other terminal state retains evidence and may retain a diagnostic
  candidate, but exposes no misleading successful-output path.

### Production L2 authority and Ground Truth

- **D-12:** Production L2 expected facts use this authority order: explicit
  user request; surviving target/Host/Type/relationship facts in the supplied
  current/damaged IFC; a user-approved or already formally bound Type/
  Prototype; then deterministic operation policy. Provenance is retained per
  fact.
- **D-13:** Private original IFC and mutation mapping are benchmark evaluator
  inputs only after the production pipeline has completed. They never enter
  request understanding, target resolution, Provider prompts, ChangeSet
  generation, production evaluation, or public evidence.
- **D-14:** Missing project-specific semantics are not filled from LLM common
  knowledge or an arbitrary nearby/similar entity. A mandatory fact without
  authorized evidence is `not_evaluable`; a conditional Material/Pset/etc.
  with verified absence of authority is `not_required` under its versioned
  Phase 8 policy.

### Type and Prototype authorization

- **D-15:** An existing IFC `IfcRelDefinesByType` or equivalent registered
  formal binding may authorize the bound Type automatically for the current
  target.
- **D-16:** A user may authorize a Type/Prototype by naming its GUID/type in
  text or selecting it from an evidence-bearing clarification list. The
  selection and inherited facts become auditable request evidence.
- **D-17:** Phase 9 may retrieve and display plausible Prototype candidates but
  cannot automatically adopt the nearest, name-similar, same-storey, or
  vector-similar entity. Future operation-specific policy may automate a
  prototype only after deterministic applicability rules and tests are added.

### the agent's Discretion

- Exact Python class/function names, internal stage enum layout, persistence
  serialization, and module split, provided API/CLI share one state machine and
  every persisted transition is schema-versioned and atomic.
- Exact bounded retry policy for invalid Agent output, provided retries are
  finite, all attempts remain evidenced, and no retry can bypass deterministic
  validation.
- Exact human progress phrasing, exit-code numbers, and run-id format, provided
  machine JSON and status semantics are stable and tests cover every terminal
  class.
- Index reuse/cache implementation, provided the index is fingerprint/version
  bound as required by Phase 7 and a changed IFC cannot reuse stale records.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone and Phase 9 scope

- `.planning/PROJECT.md` - v1.1 product goal, deterministic compiler boundary,
  mandatory L1/L2 commitment, and deferred capabilities.
- `.planning/REQUIREMENTS.md` - PIPE-01 through PIPE-04 and the adjacent
  VAL/WIN/OPS/SCALE boundaries.
- `.planning/ROADMAP.md` - fixed Phase 9 goal, dependencies, and success
  criteria.

### Upstream locked decisions

- `.planning/phases/07-ifc-retrieval-index-and-target-resolution/07-CONTEXT.md`
  - TargetQuery, SQLite index, ambiguity, property intent, bounded context, and
  Prototype/vector boundaries.
- `.planning/phases/08-l1-l2-evaluation-contract/08-SPEC.md` - Evaluation 0.2
  requirements, production-vs-benchmark authority, and publication contract.
- `.planning/phases/08-l1-l2-evaluation-contract/08-CONTEXT.md` - mandatory
  L1/L2 aggregation, conditional semantics, and private Gold decisions.
- `.planning/phases/08-l1-l2-evaluation-contract/08-VERIFICATION.md` - verified
  integration seams and carried Phase 9 evidence-construction debt.

### IFC repair design and evidence

- `docs/validation/ifc2x3-changeset/design.md` - unified ChangeSet, Registry,
  public/private boundary, transaction, and evidence bundle design.
- `docs/validation/ifc2x3-changeset/target-retrieval-design.md` - natural
  language target evidence, bounded projection, and Prototype/vector policy.
- `docs/validation/ifc2x3-changeset/ground-truth-comparison.md` - L1/L2/L3
  distinction and concrete LargeBuilding semantic gaps.
- `docs/validation/ifc2x3-changeset/phase8-validation-report.md` - current
  Evaluation 0.2 behavior and the honest L1-pass/L2-fail baseline.

### Machine contracts

- `schemas/agent/ifc-target-query-0.1.schema.json` - Phase 7 structured target
  request.
- `schemas/agent/ifc-target-resolution-0.1.schema.json` - deterministic
  resolved/ambiguous/conflict/unsupported outcome.
- `schemas/agent/ifc-target-context-0.1.schema.json` - bounded public target
  context.
- `schemas/agent/ifc-repair-changeset-0.1.schema.json` - unified semantic
  ChangeSet envelope.
- `schemas/agent/ifc-repair-evaluation-0.2.schema.json` - mandatory L1/L2
  terminal evaluation.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `src/text2ifc_ifc_repair/indexer.py`, `index_store.py`, `target_query.py`, and
  `target_context.py`: fingerprint-bound local indexing, structured resolution,
  and bounded context projection already exist.
- `src/text2ifc_ifc_repair/provider_stage.py`: prompt rendering, Provider trace,
  ChangeSet schema parsing, context/fingerprint/scope/evidence binding checks.
- `src/text2ifc_ifc_repair/apply.py` and `audit.py`: deterministic preflight,
  transactional operation dispatch, source preservation, and candidate publish.
- `src/text2ifc_ifc_repair/benchmark_evaluation.py`, `evaluation.py`, and
  `evaluation_projection.py`: production/private evaluation split, strict
  aggregate, diagnostic retention, and public allowlist/canary boundary.
- `src/text2ifc_ifc_repair/workflow.py`: atomic evidence-directory staging and
  terminal report generation can be extracted from the frozen Window case.

### Established Patterns

- JSON Schema-backed versioned contracts are parsed before behavior.
- Registry adapters own operation-specific target, parameter, Audit, apply,
  L1, and L2 behavior; common orchestration stays operation-neutral.
- Source hashes, request hashes, target evidence pointers, and operation scope
  bind every Agent-produced artifact.
- Invalid, ambiguous, unsupported, and non-publishable outcomes fail closed
  while retaining structured evidence.

### Integration Points

- Replace the hard-coded LargeBuilding IDs and benchmark mutation setup in
  `scripts/ifc_repair/run_case.py` / `workflow.py` with a public start/continue
  orchestration API that consumes the user's IFC directly.
- Add request-understanding before `resolve_target`; feed the resulting
  `TargetQuery` and relevant attribute intents into `build_target_context`.
- Reuse `generate_repair_changeset`, `apply_changeset`, and
  `evaluate_production`; keep `evaluate_benchmark` behind a separate test/UAT
  adapter.
- Reuse existing OpenAI-compatible/DeepSeek configuration and Provider trace
  code rather than creating a Phase 9-specific client.

</code_context>

<specifics>
## Specific Ideas

- Default CLI example: `bimnet repair Building.ifc`, followed by one request
  prompt and only the clarification questions required for that repair.
- Candidate clarification should show readable engineering identity plus GUID,
  class, storey, position/geometry, and why each candidate matched.
- Human success output should be short: status, L1/L2, repaired IFC path,
  ChangeSet path, Evaluation path, and run directory.
- Machine `--json` output should be a compact terminal envelope containing
  stable statuses and artifact references; complete evidence remains on disk.
- The system may help the user find a Prototype, but cannot quietly decide one
  for the user.

</specifics>

<deferred>
## Deferred Ideas

- Restoring Window Psets, quantities, Material, Classification,
  `IsExternal`, and other missing authoring semantics - Phase 10.
- Opening-only, Door, Beam, and Column operation implementation - Phases 11
  and 12.
- Automated vector matching and any vector-authorized Prototype policy - Phase
  13 or later, after measured recall evidence.
- 128k Provider input change - Phase 13 near-limit experiment.
- L3 authoring/identity exactness and curved/free-form wall mutation - outside
  the Phase 9/v1.1 supported boundary.

</deferred>

---

*Phase: 09-general-ifc-text-repair-orchestrator*
*Context gathered: 2026-07-20*
