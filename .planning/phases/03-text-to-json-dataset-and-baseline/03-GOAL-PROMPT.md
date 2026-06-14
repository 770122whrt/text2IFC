# Goal Mode Prompt: Execute Phase 3

Use this prompt to start a persistent Goal for Phase 3 execution.

```text
Create and continuously execute this Goal:

Continue advancing the text2IFC project in E:\code for project\bimnet through
Phase 3: Text-to-JSON Dataset and Baseline.

Goal:
Build a leak-free, provenance-linked Text-to-BIM-JSON dataset from authorized
BIMNet IFC2X3 sources, establish a structured-output Text-to-JSON baseline,
complete an evaluation harness, and run at least one Natural Language ->
BIM JSON 2.0 -> IFC2X3 end-to-end demo.

Read first:
.planning/PROJECT.md
.planning/REQUIREMENTS.md
.planning/ROADMAP.md
.planning/STATE.md
.planning/phases/03-text-to-json-dataset-and-baseline/03-SPEC.md
.planning/phases/03-text-to-json-dataset-and-baseline/03-CONTEXT.md
.planning/phases/03-text-to-json-dataset-and-baseline/03-RESEARCH.md
.planning/phases/03-text-to-json-dataset-and-baseline/03-VALIDATION.md
.planning/phases/03-text-to-json-dataset-and-baseline/03-01-PLAN.md
.planning/phases/03-text-to-json-dataset-and-baseline/03-02-PLAN.md
.planning/phases/03-text-to-json-dataset-and-baseline/03-03-PLAN.md
.planning/phases/03-text-to-json-dataset-and-baseline/03-04-PLAN.md
.planning/phases/03-text-to-json-dataset-and-baseline/03-05-PLAN.md
.planning/phases/03-text-to-json-dataset-and-baseline/03-06-PLAN.md

Execution rules:
1. Execute strictly by wave order:
   Wave 1: 03-01 scene-family split and provenance gate
   Wave 2: 03-02 Draft triage and formal supported-scope gold set
   Wave 3: 03-03 Text/JSON pair generation
   Wave 4: 03-04 evaluation harness
   Wave 5: 03-05 structured-output baseline
   Wave 6: 03-06 E2E demo, summary, and RAG/fine-tune decision report
2. Follow strict TDD. For every eligible behavior, write a correct failing RED
   test and commit it before implementing GREEN. Refactor only after GREEN.
3. JSON Schema remains the only BIM JSON structural truth.
4. Do not silently add required data, overwrite source data, or discard source
   facts that cannot be migrated or supported.
5. Scene-family split must complete before text generation, augmentation,
   baseline runs, or fine-tune exports.
6. Formal gold targets may only come from Phase 2.5 supported-scope BIM JSON
   2.0 that passes validate_v2_document. All omitted/loss source facts must be
   retained in sidecars.
7. Draft/clarification records must remain separate from formal baseline
   records. Do not score Draft records as Formal predictions.
8. The structured-output baseline outputs BIM JSON 2.0 only. It must not output
   raw IFC, STEP text, IfcCartesianPoint, IfcDirection, IfcOwnerHistory, or
   compiler-level implementation objects.
9. The evaluation harness must exist before any baseline quality conclusion
   and must output machine-readable metrics plus a markdown report.
10. After every plan, run focused tests and necessary regression tests, write a
    SUMMARY, and update STATE and ROADMAP.
11. Before completing Phase 3, run GSD verification, code review, data-leakage
    checks, security checks, and requirement coverage checks.
12. Ask the user only for product decision conflicts, unclear licensing, live
    provider credentials, or blockers that cannot be recovered automatically.
13. After verification passes, make atomic commits and push to origin/main.
    Follow docs/how-to/publish-to-github.md for GitHub publishing.
14. Do not stop the Goal after a single plan. Continue to the next executable
    Phase 3 step and clearly record current state.
```
