# Goal Mode Prompt: Execute Phase 5

Use this prompt to start a persistent Goal for Phase 5 execution.

```text
Create and continuously execute this Goal:

Continue advancing the text2IFC project in E:\code for project\bimnet through
Phase 5: Multi-turn Clarification Agent.

Goal:
Build the first Chinese-first multi-turn Agent that converts incomplete natural
language into either an explicit Draft clarification state or valid formal BIM
JSON 2.0, then compiles the completed result to IFC2X3. The final acceptance
artifact is a real IFC file:
dataset/processed/agent-demo/simple-room/output.ifc

Read first:
.planning/PROJECT.md
.planning/REQUIREMENTS.md
.planning/ROADMAP.md
.planning/STATE.md
.planning/phases/05-multi-turn-clarification-agent/05-SPEC.md
.planning/phases/05-multi-turn-clarification-agent/05-CONTEXT.md
.planning/phases/05-multi-turn-clarification-agent/05-AI-SPEC.md
.planning/phases/05-multi-turn-clarification-agent/05-RESEARCH.md
.planning/phases/05-multi-turn-clarification-agent/05-VALIDATION.md
.planning/phases/05-multi-turn-clarification-agent/05-01-PLAN.md
.planning/phases/05-multi-turn-clarification-agent/05-02-PLAN.md
.planning/phases/05-multi-turn-clarification-agent/05-03-PLAN.md
.planning/phases/05-multi-turn-clarification-agent/05-04-PLAN.md
.planning/phases/05-multi-turn-clarification-agent/05-05-PLAN.md
.planning/phases/05-multi-turn-clarification-agent/05-06-PLAN.md

Execution rules:
1. Execute strictly by wave order:
   Wave 1: 05-01 Agent state contract
   Wave 2: 05-02 missing-fact diagnostics to Chinese questions
   Wave 3: 05-03 answer merge and Draft/Formal transitions
   Wave 4: 05-04 fake/file providers plus optional Mimo adapter
   Wave 5: 05-05 scripted Chinese clarification demo to IFC
   Wave 6: 05-06 final verification, summary, security review, and roadmap/state update
2. Follow strict TDD. For every eligible behavior, write a correct failing RED
   test and commit it before implementing GREEN. Refactor only after GREEN.
3. JSON Schema remains the only BIM JSON structural truth. Agent state may
   track missing facts and transcripts, but it must not define a second BIM
   JSON model.
4. User-facing interaction is Chinese-first. Every clarification turn asks 1-3
   key questions.
5. If required facts are missing or the user says they do not know, keep the
   conversation in Draft. Do not apply a default template in Phase 5.
6. Do not silently invent dimensions, placements, openings, relationships,
   storeys, rooms, or properties.
7. The model/provider layer outputs semantic BIM JSON facts or Draft updates
   only. It must not output raw IFC, STEP text, IfcCartesianPoint,
   IfcDirection, IfcOwnerHistory, STEP IDs, or compiler-only objects.
8. Compile IFC only after the candidate passes formal BIM JSON 2.0 validation
   through validate_v2_document.
9. The final Phase 5 demo must run:
   python scripts/agent/run_clarification_demo.py --check
   and must write and reopen:
   dataset/processed/agent-demo/simple-room/output.ifc
10. Fake/file providers are required for deterministic tests. Mimo live smoke
    is optional and must be configured only through environment variables and
    CLI flags. Never write token values, headers, or provider URLs to files,
    transcripts, diagnostics, reports, commits, or final answers.
11. After every plan, run focused tests and necessary regression tests, write a
    SUMMARY, and update STATE/ROADMAP only with verified facts.
12. Before completing Phase 5, run Agent tests, full regression, compileall,
    the simple-room demo, Mimo config check, artifact secret scan, focused code
    review, and requirement coverage checks for AGENT-01, AGENT-02, and
    AGENT-03.
13. Ask the user only for product decision conflicts, unclear licensing, live
    provider credential failures that cannot be diagnosed locally, or blockers
    that cannot be recovered automatically.
14. After verification passes, make atomic commits and push to origin/main.
    Follow docs/how-to/publish-to-github.md for GitHub publishing.
15. Do not stop after a single plan. Continue to the next executable Phase 5
    step and clearly record current state.
```
