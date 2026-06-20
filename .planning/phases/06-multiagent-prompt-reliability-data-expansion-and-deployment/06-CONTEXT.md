# Phase 6: Multi-agent Prompt Reliability, Data Expansion, and Deployment - Context

**Gathered:** 2026-06-18
**Status:** Ready for planning
**Source:** Phase 6 user discussion, Phase 4 summary, Phase 5 Agent handoff,
and current prompt/provider implementation review.

<domain>
## Phase Boundary

Phase 6 starts by making the text2IFC Agent stack observable and controllable.
The immediate product problem is not only "can a model produce a JSON once?"
It is "can we repeatedly improve weak natural-language input into correct BIM
JSON and IFC while knowing what prompt, agent, validator, repair, and audit
step caused each outcome?"

Therefore Phase 6 begins with multi-agent design and prompt traceability before
data expansion, fine-tuning, or deployment claims. Model improvement comes only
after the project can measure prompt-only generation, conditional repair,
Draft, blocking-failure routes, audit findings, generated IFC quality, and data
split safety.
</domain>

<decisions>
## Implementation Decisions

### Worktree and Git boundary

- **D-01:** All Phase 6 work for this conversation happens in
  `C:\Users\rt do believe\.codex\worktrees\a542\bimnet`.
- **D-02:** Do not edit files in `E:\code for project\bimnet` during this
  conversation. Normal Git worktree metadata sharing through the E-drive
  `.git` directory is expected and must be explained if it matters.
- **D-03:** The active development branch is `multiagent-design`.

### Current artifact truth

- **D-04:** `dataset/processed/agent-demo/geometry-gate/two-room-suite` is a
  useful generated-IFC quality artifact, but it is not a live multi-turn Agent
  prompt trace. Its candidate is hard-coded by
  `scripts/agent/run_geometry_gate_demo.py`.
- **D-05:** `prompts/agent/mimo-bim-json-v3.md` is the strongest current live
  prompt contract, but it is not yet controlled by a registry or renderer.
- **D-06:** Phase 6 must make prompt inputs and outputs reproducible:
  template ID, template hash, rendered prompt, renderer inputs, raw response,
  parsed BIM JSON, diagnostics, repair attempts, metrics, and audit report.

### Agent purpose and responsibility

- **D-07:** Design Brief Agent converts raw user text into explicit known facts,
  missing facts, ambiguities, and clarification targets. It does not output BIM
  JSON or IFC.
- **D-08:** BIM JSON Generator Agent converts the Design Brief into formal BIM
  JSON 2.0 or Draft updates. It does not output raw IFC, STEP text, or low-level
  IFC helper objects.
- **D-09:** Repair is conditional. A successful first-pass generation records
  zero repair attempts. A failed generation routes to a safe repair attempt,
  Draft clarification, or blocking failure. If repair is attempted, it remains
  a `repair_mode` of the BIM JSON Generator and uses validation and geometry
  feedback under the same output contract as generation.
- **D-10:** Audit Agent is separate from generation. It checks semantic coverage
  against the user request and Design Brief, but it cannot overrule schema,
  compiler, reopen, geometry, or secret-scan failures.
- **D-11:** Observer Loop records experiments and may recommend prompt changes.
  A prompt change must be tied to a failure class, a test or experiment case,
  and metric evidence.

### Data and model policy

- **D-12:** Phase 6 data expansion uses only authorized or license-reviewed
  sources. Every record keeps provenance and split assignment.
- **D-13:** BIMNet scene-family split integrity from Phase 3 remains binding.
- **D-14:** Draft and loss sidecars remain linked to formal targets and are not
  silently converted into training truth.
- **D-15:** Fine-tuning is a decision, not an assumption. It must be compared
  against prompt-only, conditional repair, and optional RAG-assisted baselines.
- **D-16:** RAG is considered only for recurring schema/class/property
  knowledge failures. It is not a substitute for the official IFC2X3 registries
  and validators.

### the agent's Discretion

- Exact file names for registry implementation, provided prompt template ID,
  hash, rendered inputs, raw output, parsed output, diagnostics, and metrics are
  preserved.
- Exact Design Brief schema layout, provided it validates known facts, missing
  facts, ambiguities, provenance, and correction history.
- Exact deployment surface, provided it can be run repeatably as a local CLI or
  service and produces a real IFC file with trace artifacts.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 6 contracts

- `.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-SPEC.md`
  - locked Phase 6 boundaries, agent roles, and acceptance criteria.
- `.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-AI-SPEC.md`
  - AI system design contract for multi-agent prompt orchestration.
- `.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-ACCEPTANCE-TRACE-REPORT.md`
  - single-entry Phase 6 acceptance, trace, input/output, and supervision
    report for user review.
- `.planning/REQUIREMENTS.md` - Phase 6 requirements, including MODEL,
  DEPLOY, prompt traceability, repair, audit, and observer-loop requirements.
- `.planning/ROADMAP.md` - phase dependencies and wave ordering.
- `.planning/STATE.md` - current project decisions, risks, and Phase 6 entry
  state.

### Prior-phase evidence

- `docs/architecture/phase-4-summary.md` - generated IFC gate, fidelity
  accounting, and Phase 6 supported-scope boundary.
- `.planning/phases/04-high-fidelity-ifc-round-trip/04-SPEC.md` - generated
  IFC correctness and high-fidelity boundaries.
- `.planning/phases/05-multi-turn-clarification-agent/05-AI-SPEC.md` - current
  clarification Agent state machine and provider boundary.
- `.planning/phases/05-multi-turn-clarification-agent/05-SPEC.md` - Chinese
  interaction, Draft, validation, and IFC acceptance rules.

### Current implementation references

- `prompts/agent/mimo-bim-json-v3.md` - current geometry-aware Mimo prompt.
- `prompts/agent/mimo-bim-json-iterations.md` - prompt iteration history.
- `src/text2ifc_agent/providers.py` - fake/file/Mimo provider boundary and
  raw IFC guardrails.
- `src/text2ifc_agent/session.py` - Phase 5 Agent state transitions.
- `scripts/agent/run_geometry_gate_demo.py` - deterministic geometry-gate demo
  and hard-coded candidate evidence.
- `src/text2ifc_quality/generated_ifc.py` - current generated IFC quality gate.
- `schemas/bim-json/2.0/schema.json` - formal BIM JSON structural truth.
- `src/text2ifc_contract/validation_v2.py` - formal validation gate.
- `src/text2ifc_compiler/compiler.py` - deterministic IFC2X3 compiler.
</canonical_refs>

<specifics>
## Specific Ideas

- Add a prompt registry under `prompts/agent/registry.json` or an equivalent
  typed metadata file.
- Add a renderer that accepts structured inputs instead of ad hoc prompt
  strings.
- Add Design Brief schema and validator before changing live provider prompts.
- Add few-shot examples as named registry assets, not copied into one-off demo
  scripts.
- Add an audit report schema that clearly marks deterministic failures as
  blocking.
- Add an experiment ledger where each row links prompt ID, case ID, provider
  mode, repair count, metric deltas, and artifact paths.
- Add a project-local skill-like runbook for the Observer Loop after the first
  implementation proves the artifact structure.
</specifics>

<deferred>
## Deferred Ideas

- Standalone physical Repair Agent, unless conditional repair metrics show that
  a separate specialized prompt is better.
- Production LangGraph or workflow-framework migration, unless the in-repo
  orchestrator becomes too hard to observe or resume.
- Full browser-based IFC review UI.
- Full BIMNet source-equivalent geometry reconstruction beyond the Phase 4
  supported-scope boundary.
</deferred>

---
*Phase: 06-multiagent-prompt-reliability-data-expansion-and-deployment*
*Context gathered: 2026-06-18*
