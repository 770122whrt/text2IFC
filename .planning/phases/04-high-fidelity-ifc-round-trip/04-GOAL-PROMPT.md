Create and continuously execute this Goal:

Continue advancing the text2IFC project in E:\code for project\bimnet through
Phase 4: High-fidelity IFC Round Trip.

Goal:
Improve the reliability of the full Natural Language -> BIM JSON 2.0 -> IFC2X3
path. First establish a generated-IFC correctness gate that catches spatial,
attribute, relationship, and IFC-structure errors in simple Agent demos. Then
expand source IFC fidelity for materials, type reuse, connection topology,
complex/mapped geometry, and broader product classes with explicit loss
accounting. The phase must continuously record quantitative metrics and
experiment results so prompt, Agent, schema, compiler, and fidelity changes can
be evaluated rather than guessed.

Read first:
.planning/PROJECT.md
.planning/REQUIREMENTS.md
.planning/ROADMAP.md
.planning/STATE.md
.planning/phases/04-high-fidelity-ifc-round-trip/04-SPEC.md
.planning/phases/04-high-fidelity-ifc-round-trip/04-CONTEXT.md
.planning/phases/04-high-fidelity-ifc-round-trip/04-VALIDATION.md
.planning/phases/04-high-fidelity-ifc-round-trip/04-00-PLAN.md
.planning/phases/04-high-fidelity-ifc-round-trip/04-01-PLAN.md
.planning/phases/04-high-fidelity-ifc-round-trip/04-02-PLAN.md
.planning/phases/04-high-fidelity-ifc-round-trip/04-03-PLAN.md
.planning/phases/04-high-fidelity-ifc-round-trip/04-04-PLAN.md
.planning/phases/04-high-fidelity-ifc-round-trip/04-05-PLAN.md
.planning/phases/04-high-fidelity-ifc-round-trip/04-06-PLAN.md

Execution rules:
1. Execute strictly by wave order:
   Wave 0: 04-00 generated IFC correctness gate
   Wave 1: 04-01 fidelity inventory and metric harness
   Wave 2: 04-02 material and layer fidelity
   Wave 3: 04-03 type reuse fidelity
   Wave 4: 04-04 connection topology fidelity
   Wave 5: 04-05 complex and mapped geometry fidelity
   Wave 6: 04-06 broader classes, all-25 audit, and Phase 6 readiness
2. Follow strict TDD. For every eligible behavior, write a correct failing RED
   test and commit it before implementing GREEN.
3. BIM JSON Schema remains the only structural truth. Quality gates may add
   semantic and geometric checks but must not define a competing model.
4. Do not silently add required data, overwrite source data, repair geometry
   without diagnostics, or discard unsupported facts.
5. Wave 0 must complete before any high-fidelity source expansion. Do not start
   materials, types, topology, complex geometry, or broader classes until both
   `simple-room-fixed` and `two-room-suite` pass the generated-IFC quality gate.
6. Every generated demo must preserve input text, provider prompt, raw provider
   output, candidate BIM JSON, diagnostics, report, expected facts, metrics,
   and compiled IFC.
7. Every generated demo report must include parse validity, BIM JSON validity,
   compile/reopen success, geometry gate result, attribute accuracy,
   relationship accuracy, IFC structure result, repair iteration count, and
   error classes.
8. The model/provider layer outputs semantic BIM JSON facts only. It must not
   output raw IFC, STEP text, low-level IFC helper objects, hidden defaults, or
   unsupported geometry claims.
9. Unsupported source material, type, topology, class, or geometry facts must
   remain explicit Draft/loss content. Never substitute unsupported geometry
   with boxes or proxies and call it high fidelity.
10. Preserve BIMNet scene-family split boundaries and provenance for every
    dataset or evaluation artifact.
11. After every plan, run focused tests and necessary regression tests, write a
    SUMMARY, and update STATE and ROADMAP only with verified facts.
12. Before completing Phase 4, run generated-IFC gates, fidelity tests, full
    regression, compileall, artifact secret scans, code review, security review,
    and requirement coverage checks.
13. Ask the user only for product decision conflicts, unclear licensing, live
    provider credential failures that cannot be diagnosed locally, or blockers
    that cannot be recovered automatically.
14. After verification passes, make atomic commits and push to origin/main.
    Follow docs/how-to/publish-to-github.md for GitHub publishing.
15. Do not stop after a single plan. Continue to the next executable Phase 4
    step and clearly record current state.
