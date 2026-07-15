# Phase 6 Research: Multi-agent Prompt Reliability, Data Expansion, and Deployment

**Created:** 2026-06-18
**Scope:** Planning research from verified local project evidence. External
model-framework selection remains optional and must not block deterministic
Phase 6 work.

## Key Findings

### 1. Prompt control is the immediate bottleneck

Current evidence:

- `prompts/agent/mimo-bim-json-v3.md` contains useful generation constraints.
- `scripts/agent/run_geometry_gate_demo.py` writes a short `prompt-used.md`,
  but the candidate JSON is hard-coded.
- Provider classes accept a `prompt` argument, but fake/file providers ignore
  it and live Mimo calls receive one rendered string without a registry-backed
  trace.

Planning implication:

- Phase 6 must start with prompt registry and trace artifacts. Otherwise future
  prompt iterations cannot be compared or reproduced.

### 2. A Design Brief layer reduces role overload

Current evidence:

- Phase 5 handles missing facts through Agent state, questions, and answer
  merge.
- Phase 4 geometry failures show that a model can satisfy JSON structure while
  misunderstanding spatial intent.

Planning implication:

- A Design Brief Agent should capture intent and ambiguity before BIM JSON
  generation. This makes the generator narrower and gives audit a human-intent
  artifact.

### 3. Repair should be measured before being split out

Current evidence:

- Phase 4 prompt v3 already accepts validation and geometry feedback.
- Repair output must still be BIM JSON 2.0 or Draft.

Planning implication:

- Implement repair as a generator mode first. Record repair deltas. Split into
  a standalone Repair Agent only if specialized repair prompts improve measured
  outcomes.

### 4. Agent audit is useful but cannot be authoritative

Current evidence:

- Phase 4 generated IFC gates catch structural and geometry failures.
- Some semantic mismatches, such as whether the output reflects the user's
  intent, are better reviewed against the original request and Design Brief.

Planning implication:

- Audit Agent should produce evidence-linked reports and flag mismatches. It
  must not pass a run that deterministic gates fail.

### 5. Fine-tuning is not the first Phase 6 action

Current evidence:

- Phase 3 has a baseline and data split.
- Phase 4 has fidelity accounting and generated IFC gates.
- Phase 5 has a simple Agent demo.
- Prompt traces and repair metrics are not yet unified.

Planning implication:

- Compare prompt-only, conditional repair, optional RAG, and fine-tune only
  after traceable prompt runs and reliability metrics exist.

## Validation Architecture

Phase 6 needs layered validation:

1. Prompt trace validation: every run has template ID/hash and renderer inputs.
2. Design Brief validation: schema-valid brief with known/missing/ambiguous
   facts.
3. BIM JSON validation: `validate_v2_document` for Formal output.
4. Draft validation: incomplete output stays explicit Draft.
5. IFC validation: compile, reopen, and generated IFC quality gate.
6. Agent audit validation: report exists and deterministic failures remain
   blocking.
7. Data validation: split, license, provenance, and loss sidecar checks.
8. Secret validation: artifact scan excludes token values and private headers.

## Risks

- Prompt drift: ad hoc prompt text bypasses registry.
- Self-review bias: generator reviews its own output and misses mistakes.
- Repair invention: repair loop fills missing facts instead of returning Draft.
- Dataset leakage: expanded training data violates scene-family split.
- Metric optimism: fine-tune appears better because invalid/Draft records are
  excluded incorrectly.
- Secret leakage: provider diagnostics accidentally write token or URL values.

## Recommended Wave Order

1. Prompt registry and trace bundle.
2. Design Brief Agent.
3. BIM JSON Generator orchestration and conditional failure routing.
4. Audit Agent and deterministic gate integration.
5. Experiment harness and metrics.
6. Data expansion plus prompt/RAG/fine-tune decision.
7. Deployment package and final IFC demo.

---
*Phase: 06-multiagent-prompt-reliability-data-expansion-and-deployment*
