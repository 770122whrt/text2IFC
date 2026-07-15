# Phase 6 Model Decision

**Date:** 2026-06-21
**Decision scope:** Chinese-first text to Design Brief to BIM JSON 2.0 or
Draft, followed by deterministic IFC2X3 compilation and audit.

## Decision

Use the **Prompt-only** multi-agent path as the Phase 6 deployable baseline:

1. Design Brief Agent separates known, missing, and ambiguous facts.
2. BIM JSON Generator produces only BIM JSON 2.0 or Draft.
3. Deterministic schema, compiler, reopen, and geometry gates decide whether
   IFC may be accepted.
4. Audit Agent compares intent and output but cannot override deterministic
   failures.
5. **Repair-mode** is conditional and is invoked only for a model-produced
   error that can be corrected from already known facts.

Do not fine-tune in Phase 6. Do not add RAG to the default path yet. The current
evidence is sufficient to deploy and measure the orchestration boundary, but
it is not sufficient to claim a fine-tuned or retrieval-augmented model would
improve held-out Chinese text2IFC quality.

## Evidence

| Evidence | Verified result | What it proves |
| --- | ---: | --- |
| Authorized BIMNet IFC2X3 sources | 25 | Local extraction, dataset construction, evaluation, and local training are authorized for these sources |
| Scene families | 19 | Source-family isolation can be enforced |
| Text/BIM JSON pairs | 100 | A small supervised/evaluation seed set exists |
| Train / validation / test pairs | 68 / 20 / 12 | Evaluation records can remain outside training |
| Pair review status | 100 generated, 0 human-reviewed | Current pairs are not a reviewed production corpus |
| Pair styles | 25 each for concise, enumerated, property-focused, spatial | Template diversity exists, but linguistic diversity is limited |
| Records containing CJK characters | 39 | Some source names are Chinese; the instruction templates remain English-first |
| Phase 3 fake validation semantic-valid rate | 1.00 | Storage, parsing, and evaluation plumbing work; this is target echo and does not measure model quality |
| Phase 6 controlled experiment cases | 5 | Success, Draft, repair, blocked, and audit routes are persisted and reportable |
| Phase 6 default run | Formal, compile/reopen pass, geometry pass, audit pass, 0 repairs | The deterministic orchestration path works with the fake provider |
| Historical Mimo simple-room run | Parse, validation, and compile succeeded | A live provider has produced compilable structured output |
| Historical Mimo geometry review | Wall rotation/connectivity defect was observed | Compile success alone is not semantic or geometric success |

All Phase 6 experiment evidence currently uses `provider_mode: fake`. It must
not be used to claim live Mimo accuracy or to rank language models.

## Prompt-only

Prompt-only is the current deployment choice because it has the strongest
traceability and the lowest data risk:

- every prompt has an ID, content hash, renderer inputs, and persisted rendered
  text;
- original input, Design Brief, raw response, parsed output, validation,
  geometry, audit, and metrics are stored together;
- missing user facts remain Draft instead of being invented;
- a Formal result is compiled only after BIM JSON 2.0 validation;
- deterministic IFC gates remain blocking even if the Audit Agent approves.

This choice is a measurable baseline, not a claim that prompting alone is the
final modeling solution. A real provider benchmark must reuse the same
validation and reporting path before prompt quality can be judged.

## Repair-mode

Repair is a mode of the BIM JSON Generator, not a mandatory separate agent in
the first deployment.

The current routing contract is:

- `no_repair_needed`: first-pass Formal output passes required gates;
- `repair_attempted`: supplied facts are sufficient, but the candidate has a
  repairable structural or geometric defect;
- `draft_required`: required user facts are absent or the user does not know;
- `blocked_failure`: provider, parsing, compiler, or another system failure
  cannot be safely repaired.

The controlled matrix proves these routes are recorded. It does not yet prove
that a second model call improves a failed candidate. A standalone Repair
Agent is justified only when a benchmark shows that a specialized repair
prompt improves pass rate without increasing invented facts.

## Optional RAG

RAG is not selected for the default path because no real held-out benchmark
currently identifies recurring knowledge-retrieval failures.

RAG should be tested only when failures repeatedly involve facts that can be
retrieved from approved IFC2X3 knowledge, such as:

- choosing between related IFC product classes;
- valid standard property-set and property names;
- relationship endpoint rules;
- whether a class is generate, extract-only, compiler-generated, or
  unsupported.

If triggered, retrieval must use project-local IFC2X3 registries generated
from the official schema and PSD sources. Retrieval must not provide missing
project dimensions, placements, openings, or relationships that the user did
not state.

## Fine-tuning decision

**Fine-tuning is not justified by the current evidence.**

Only 68 records are training-eligible. All 100 pairs are deterministic
generated templates and have `review_status: generated`. The prompts are
English-first, even when source element names contain Chinese. There is no
current real-provider validation/test benchmark under the Phase 6 prompt
registry, and the fake target-echo baseline cannot rank a fine-tuned model
against prompt-only generation.

Fine-tuning may be reconsidered after all of the following exist:

1. Chinese-first, human-reviewed or controlled-review paraphrases.
2. A real Mimo prompt-only run over the fixed validation and test scene
   families.
3. Metrics that include Formal validity, Draft correctness, class and
   relationship accuracy, compile/reopen, geometry gate pass, semantic audit,
   invented-fact rate, and repair count.
4. A repair benchmark that records before/after errors rather than only a
   routing decision.
5. Stable results across repeated runs with prompt ID and model configuration
   recorded without secrets.

Any future fine-tune export must include only records marked
`training_eligible: true` in
`dataset/processed/phase6/training-manifest.json`. Validation and test records
remain evaluation-only.

## Supported and Unsupported Scope

The current system can generate supported BIM JSON 2.0 semantic entities,
parent-relative placement, supported extrusion geometry, properties, and
relationships, then compile them to IFC2X3.

Phase 4 source-fidelity accounting reports:

| Dimension | Supported rate |
| --- | ---: |
| Entities | 83.72% |
| Relationships | 88.89% |
| Properties | 93.86% |
| Representations | 70.65% |
| Materials | 60.02% |
| Types | 15.22% |
| Connections | 100% |

These are source-fidelity measurements, not model accuracy. Mapped geometry,
faceted BRep, tessellation, boolean results, surface models, broad material
systems, and type reuse remain incomplete or loss-explicit. A model must not
invent substitutes for those unsupported source facts.

## Wave 6 Deployment Boundary

Wave 6 should package the prompt-only multi-agent pipeline with conditional
failure routing. The deterministic fake/file providers remain the required
test path. A live provider is optional and must be labelled honestly.

The service acceptance result is a generated trace bundle with:

- original Chinese input;
- Design Brief;
- prompt metadata and rendered prompt;
- raw and parsed provider output;
- BIM JSON 2.0 or Draft;
- validation, geometry, and audit evidence;
- failure route and repair attempts;
- metrics;
- generated `report.md`;
- `output.ifc` only when every blocking Formal gate passes.

This boundary creates a reliable deployment and evaluation platform now,
while preserving the evidence needed to decide later whether RAG, repair
specialization, or fine-tuning actually improves the system.
