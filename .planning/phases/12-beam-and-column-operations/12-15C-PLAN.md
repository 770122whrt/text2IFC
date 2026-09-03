---
phase: 12-beam-and-column-operations
plan: "15C"
type: execute
wave: 15
depends_on: ["12-15B"]
autonomous: true
requirements: [OPS-03, OPS-04]
---

<objective>
Correct Stage 1 clause-role classification so compatible transaction wording
does not become an extra unsupported action, while retaining generic registry
authority, exact negative rejection, all historical Door/Window behavior, and
the unchanged Phase 12 live/Proof closeout requirements.
</objective>

<context>
@.planning/phases/12-beam-and-column-operations/12-TRANSACTION-CLAUSE-CORRECTION-SPEC.md
@.planning/phases/12-beam-and-column-operations/12-STAGE1-SCOPE-CORRECTION-SPEC.md
@.planning/phases/12-beam-and-column-operations/12-TYPE-INTENT-CORRECTION-SPEC.md
@docs/validation/agent-capability-evaluation.md
@.planning/phases/12-beam-and-column-operations/12-15-PLAN.md
@.planning/phases/12-beam-and-column-operations/12-16-PLAN.md
</context>

<tasks>

<task type="auto">
  <name>Task 12-15C-01: Freeze the clause-role failure family as RED</name>
  <action>Add independent natural-language fixtures and prompt/public-seam tests for the four clause roles, all frozen atomic synonyms, operation modifiers, the three representative micro-shapes, mixed registered/unregistered rejection, and the preserved live phrase. Add a four-family Beam+Column+Window+Door positive and explicit Window/Door historical non-regression. Expected values must be independent literals; do not derive them from implementation constants. Run RED against the current v0.7 Prompt and retain the exact failures.</action>
  <verify><automated>.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_repair_intent_v08.py tests/ifc_repair/test_request_stage.py tests/ifc_repair/test_operation_prompt_profiles.py -q --basetemp=.pytest-tmp/phase12-clause-role-red</automated></verify>
  <done>The new family fails only because append-only 0.8 and the clause-role contract do not yet exist; historical behavior remains visible.</done>
</task>

<task type="auto">
  <name>Task 12-15C-02: Implement append-only RepairIntent and Prompt 0.8</name>
  <action>Add body/envelope 0.8 with the unchanged 0.7 JSON shape; add and register Prompt v0.8 with the four-role table, semantic-object rule, three representative micro-shapes, natural-language-versus-canonical-output distinction, and explicit non-exhaustive capability authority. Move current production bindings to 0.8 without changing operation definitions or profiles. Do not add transaction fields, keyword routing, aliases, normalization, Provider rewrites, Stage calls, or Stage 1 full few-shots. Keep every prior registered artifact byte-identical.</action>
  <verify><automated>.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_repair_intent_v08.py tests/ifc_repair/test_repair_intent_v07.py tests/ifc_repair/test_operation_prompt_profiles.py tests/ifc_repair/test_request_stage.py -q --basetemp=.pytest-tmp/phase12-clause-role-contract</automated></verify>
  <done>The compact Stage 1 contract is registry-generic, positive atomic clauses produce no extra item, representative negatives remain exact, and Stage 2 responsibility is unchanged.</done>
</task>

<task type="auto">
  <name>Task 12-15C-03: Requalify every registered repair family offline</name>
  <action>Run Stage1/Stage2 seams and public complete/clarification/guard chains, then the fixed Phase 12 offline matrix. Run the full Window/Door request, resolution, application, reopen, semantic, preservation, and mixed-family suites, not merely Beam/Column tests. Run compiler checks, diff check, full repository pytest under the frozen two-hour timeout, existing independent Proof validation, and the machine-readable zero-skip preflight. A failure, skip, substitution, timeout, or missing artifact blocks live transport.</action>
  <verify><automated>.\.venv\Scripts\python.exe scripts/ifc_repair/run_phase12_live_uat.py --preflight-only</automated></verify>
  <done>Every required command is green, all registered-family coverage is present, synthetic transport calls remain zero, and the source/live fixtures are unchanged.</done>
</task>

<task type="auto">
  <name>Task 12-15C-04: Execute one new real UAT and finish Plans 12-15/12-16</name>
  <action>Run the unchanged three-case natural-language matrix through public RepairAPI with the approved real DeepSeek transport. Preserve every attempt. If green, curate only accepted cases, independently recompute prompt/provider/provenance, IFC reopen, strict L0/L1/L2, global preservation, private-Gold isolation and IFCCompare, then update reports, VALIDATION, STATE and ROADMAP, create isolated Phase 12 Git checkpoints, push the current branch, and perform the agreed branch closeout. If another contract ambiguity appears, stop before retry or curation and discuss it with the user.</action>
  <verify><automated>.\.venv\Scripts\python.exe scripts/ifc_repair/run_phase12_live_uat.py --provider deepseek --require-green-preflight</automated></verify>
  <done>Phase 12 closes only with genuine DeepSeek evidence, independently validated accepted Proof, IFCCompare evidence, exact project status, isolated commits and pushed branch; otherwise the new failed run is retained without a false success claim.</done>
</task>

</tasks>

<success_criteria>
- Atomic/same-transaction/together/all-or-nothing clauses never create a third operation or unsupported item.
- Registry/profile authority, rather than an enumerated Prompt deny-list, defines supported and unsupported repair content.
- Beam/Column, Window, Door, Opening, and occurrence-property historical behavior passes the applicable public and strict regression gates.
- RepairIntent 0.8 changes no JSON shape and production adds no LLM-output compatibility.
- Door/Window workflow, geometry thresholds, Storey policy, Type/material authority, Ground Truth isolation, Proof strictness and Phase 13 boundary remain unchanged.
- Dataset/PDF/document-organization work remains excluded from Phase 12 commits.
</success_criteria>
