---
phase: 12-beam-and-column-operations
plan: "15A"
type: execute
wave: 15
depends_on: ["12-14"]
files_modified:
  - schemas/agent/ifc-repair-intent-body-0.6.schema.json
  - schemas/agent/ifc-repair-intent-0.6.schema.json
  - prompts/agent/ifc-repair-intent-v0.6.md
  - prompts/agent/ifc-repair-profiles/beam.add.v0.2.json
  - prompts/agent/ifc-repair-profiles/column.add.v0.2.json
  - prompts/agent/ifc-repair-few-shots
  - prompts/agent/registry.json
  - src/text2ifc_ifc_repair
  - tests/ifc_repair
autonomous: true
requirements: [OPS-03, OPS-04]
must_haves:
  truths:
    - "Stage 1 classifies and extracts registered IFC repair intent with compact profile metadata only; Stage 2 alone loads selected full profiles and few-shots."
    - "Unsupported registered capabilities and unregistered actions are explicit 0.6 unsupported_requests and terminate before clarification, Stage 2, or mutation."
    - "Beam/Column Stage 1 accepts only the exact rectangle geometry token and Storey target selector contract; malformed aliases are rejected, not normalized."
    - "Existing 0.1-0.5 schemas, prompts and profile artifacts remain byte-for-byte historical contracts."
  artifacts:
    - path: ".planning/phases/12-beam-and-column-operations/12-STAGE1-SCOPE-CORRECTION-SPEC.md"
      provides: "Frozen correction contract and decision authority."
    - path: "tests/ifc_repair/fixtures/phase12_stage1_scope_cases.json"
      provides: "Frozen sibling positive, negative, boundary and cross-scene failure family."
    - path: "schemas/agent/ifc-repair-intent-body-0.6.schema.json"
      provides: "Provider body contract with explicit unsupported_requests."
    - path: "schemas/agent/ifc-repair-intent-0.6.schema.json"
      provides: "Bound RepairIntent envelope contract."
---

<objective>
Close the deterministic Stage 1 contract defects exposed by the preserved
Phase 12 live run before retrying Plan 12-15.

Purpose: Correct prompt/schema/registry sufficiency without accepting aliases,
implementing structural analysis, or weakening Storey and private-Gold policy.

Output: A versioned 0.6 public contract, frozen failure-family tests, all-green
offline public-chain preflight, then the unchanged real-Provider acceptance path.
</objective>

<context>
@.planning/phases/12-beam-and-column-operations/12-STAGE1-SCOPE-CORRECTION-SPEC.md
@docs/validation/agent-capability-evaluation.md
@.planning/phases/12-beam-and-column-operations/12-15-PLAN.md
@.planning/phases/12-beam-and-column-operations/12-16-PLAN.md
</context>

<tasks>

<task type="auto">
  <name>Task 12-15A-01: Freeze the Stage 1 failure family as RED tests</name>
  <action>Add one immutable case matrix covering Beam/Column complete, grouped clarification, structural analysis member/node/load/port/connection, other unsupported geometry, pure unregistered and mixed repair-plus-unregistered requests, malformed/truncated output, exact rectangle, forbidden rectangular alias, exact Storey names selector, forbidden storey_name selector, and d7n/vvo scene labels. Test the public generate_repair_intent and RepairAPI seams, prompt/profile selection, call counts, source immutability and private-input isolation. Observe the focused suite fail before production edits.</action>
  <verify><automated>.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_repair_intent_v06.py tests/ifc_repair/test_phase12_stage1_scope.py -q --basetemp=.pytest-tmp/phase12-stage1-red</automated></verify>
  <done>The complete frozen family is committed while production still fails the new contract.</done>
</task>

<task type="auto">
  <name>Task 12-15A-02: Implement the versioned schema, prompt, profile and domain contract</name>
  <action>Add 0.6 RepairIntent/body schemas and prompt registry entry; add Beam/Column v0.2 profiles and bound few-shots; add unsupported_requests to the immutable domain model; add generic OperationDefinition.intent_target_schema validation; bind Beam/Column to exact rectangle and Storey target intent schemas. Keep Stage 1 compact and Stage 2 selected-profile loading unchanged in responsibility. Do not edit released artifacts.</action>
  <verify><automated>.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_repair_intent_v06.py tests/ifc_repair/test_structural_prompt_profiles.py tests/ifc_repair/test_selected_provider_profiles.py -q --basetemp=.pytest-tmp/phase12-stage1-contract</automated></verify>
  <done>0.6 round-trips exactly, old versions remain valid, prompt/profile hashes bind, and aliases/wrong target fields fail closed.</done>
</task>

<task type="auto">
  <name>Task 12-15A-03: Enforce unsupported scope before clarification and Stage 2</name>
  <action>Validate each unsupported item against registered operation/profile capability metadata, derive only the frozen reason codes, and terminate any pure or mixed unsupported request before completeness and all later stages. Update RepairAPI and Phase 12 live runner to 0.6. Never normalize provider keys or infer an omitted unsupported item.</action>
  <verify><automated>.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_phase12_stage1_scope.py tests/ifc_repair/test_phase12_live_uat.py -q --basetemp=.pytest-tmp/phase12-stage1-api</automated></verify>
  <done>Every frozen scope case has exact classification, reason and Stage1/Stage2/mutation counts through the public API seam.</done>
</task>

<task type="auto">
  <name>Task 12-15A-04: Requalify offline before returning to Plan 12-15</name>
  <action>Run focused suites, complete Phase 12 offline matrix, required regressions, compileall, diff check and the live runner's zero-skip machine-readable preflight. Any failure, skip, substitution or timeout blocks the Provider call. Preserve the existing failed live run append-only.</action>
  <verify><automated>.\.venv\Scripts\python.exe scripts/ifc_repair/run_phase12_live_uat.py --preflight-only</automated></verify>
  <done>All required offline gates are genuinely green and a new immutable preflight authorizes the unchanged Plan 12-15 real DeepSeek path.</done>
</task>

</tasks>

<success_criteria>
- No released schema/prompt/profile is rewritten.
- Stage 1 remains compact and Stage 2 remains the sole full-profile/few-shot consumer.
- Unsupported work cannot become clarification or reach Stage 2/mutation.
- No alias, synthetic/cached fallback, structural-analysis implementation, or frozen Door/Window/Storey/Gold-policy redesign is introduced.
</success_criteria>

<output>
Create `12-15A-SUMMARY.md`, then resume the unchanged Plan 12-15 and Plan 12-16.
</output>
