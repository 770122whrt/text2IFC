---
phase: 12-beam-and-column-operations
plan: "15B"
type: execute
wave: 15
depends_on: ["12-15A"]
autonomous: true
requirements: [OPS-03, OPS-04]
---

<objective>
Close the Type-intent contract defect exposed by the preserved Phase 12 live
run without compatibility logic, then requalify the unchanged Plan 12-15 live
and Plan 12-16 closeout paths.
</objective>

<context>
@.planning/phases/12-beam-and-column-operations/12-TYPE-INTENT-CORRECTION-SPEC.md
@.planning/phases/12-beam-and-column-operations/12-STAGE1-SCOPE-CORRECTION-SPEC.md
@docs/validation/agent-capability-evaluation.md
@.planning/phases/12-beam-and-column-operations/12-15-PLAN.md
@.planning/phases/12-beam-and-column-operations/12-16-PLAN.md
</context>

<tasks>

<task type="auto">
  <name>Task 12-15B-01: Freeze the Type-intent failure family as RED</name>
  <action>Add independent prompt/profile, RepairIntent, resolution, and public API cases for null generated-Type intent, exact reuse, bounded candidate selection, zero-candidate failure, the preserved mixed Beam/Column phrase, Stage boundaries, and historical Door/Window compatibility. Observe the focused suite fail before production edits.</action>
  <verify><automated>.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_repair_intent_v07.py tests/ifc_repair/test_structural_prompt_profiles.py tests/ifc_repair/test_resolution_flow.py -q --basetemp=.pytest-tmp/phase12-type-intent-red</automated></verify>
  <done>The complete Type-intent family is committed while production still lacks v0.7/v0.3.</done>
</task>

<task type="auto">
  <name>Task 12-15B-02: Implement append-only RepairIntent 0.7 and profiles 0.3</name>
  <action>Add the 0.7 body/envelope/prompt and 0.2 profile schema; add Beam/Column v0.3 profiles and bound few-shots; update exact registry hashes and production bindings. Keep Stage 1 compact, Stage 2 selected-only, and all historical registered files unchanged. Do not rewrite Provider output.</action>
  <verify><automated>.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_repair_intent_v07.py tests/ifc_repair/test_structural_prompt_profiles.py tests/ifc_repair/test_selected_provider_profiles.py -q --basetemp=.pytest-tmp/phase12-type-intent-contract</automated></verify>
  <done>The three states are explicit in Stage 1, profiles validate and hash-bind, and Stage 2 alone loads selected v0.3 few-shots.</done>
</task>

<task type="auto">
  <name>Task 12-15B-03: Requalify the public chain before DeepSeek</name>
  <action>Run the frozen failure family, complete/clarification/guard public chains, offline matrix, required Door/Window regressions, compile/diff/proof gates, and machine-readable zero-skip preflight. Preserve both prior live runs append-only.</action>
  <verify><automated>.\.venv\Scripts\python.exe scripts/ifc_repair/run_phase12_live_uat.py --preflight-only</automated></verify>
  <done>Every required offline gate is green with bounded timeouts and no Provider transport call.</done>
</task>

<task type="auto">
  <name>Task 12-15B-04: Retry live acceptance and close Phase 12</name>
  <action>Run the unchanged natural-language three-case DeepSeek matrix. If green, curate only accepted evidence, independently recompute strict Proof and IFC comparison, update reports/STATE/ROADMAP, create scoped Git checkpoints, push the branch, and perform the agreed branch closeout. If another contract defect appears, stop for user discussion before retry or curation.</action>
  <verify><automated>.\.venv\Scripts\python.exe scripts/ifc_repair/run_phase12_live_uat.py --live</automated></verify>
  <done>Plans 12-15 and 12-16 close with genuine live evidence and independently verified Proof, or the new failed evidence is preserved and reported without a false success claim.</done>
</task>

</tasks>

<success_criteria>
- Generated/new/dedicated Type requests produce null prototype intent.
- Existing-Type reuse is exact or bounded candidate clarification; zero candidates fail closed.
- No LLM-output compatibility, new analysis capability, Stage boundary drift, or frozen policy redesign is introduced.
- Dataset/PDF/document-organization work remains excluded from Phase 12 commits.
</success_criteria>
