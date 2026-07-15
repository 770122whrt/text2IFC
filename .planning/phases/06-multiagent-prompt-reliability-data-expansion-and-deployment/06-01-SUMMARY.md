# 06-01 Summary: Design Brief Agent Contract

**Completed:** 2026-06-21
**Plan:** `06-01-PLAN.md`
**Status:** Complete

## Objective

Create a schema-backed Design Brief boundary that records Chinese user intent,
known facts, missing facts, ambiguities, corrections, questions, and provenance
without becoming BIM JSON or IFC.

## Commits

| Type | Commit | Description |
|---|---|---|
| RED | `ecaf6c2` | Added failing complete, weak-input, and boundary tests |
| RED refinement | `a5ed5b8` | Aligned extra-field diagnostics with the project contract |
| GREEN | `f80c2da` | Implemented Design Brief JSON Schema and validator |
| Prompt | `0e735a3` | Added and registered the Chinese Design Brief prompt |

## Implemented

- `schemas/agent/design-brief/1.0/schema.json` defines the Design Brief
  contract independently from BIM JSON.
- `src/text2ifc_agent/design_brief.py` validates briefs with stable field-level
  diagnostics and does not mutate input facts.
- `prompts/agent/design-brief-v1.md` instructs the model to preserve unknowns,
  output Design Brief JSON only, and ask at most 1-3 Chinese questions.
- `prompts/agent/registry.json` registers `design-brief.v1` with a verified
  SHA-256 identity and explicit forbidden output classes.
- `tests/agent/test_design_brief.py` proves complete facts validate, weak input
  stays incomplete, and BIM JSON root fields are rejected.

## Verification

- RED: `python -m pytest tests/agent/test_design_brief.py -q` produced 3
  expected failures because the Design Brief validator was missing.
- Focused GREEN: 5 tests passed across Design Brief and Prompt Registry.
- Full Agent regression: `python -m pytest tests/agent -q` produced 46 passed.
- `python -m compileall src scripts -q`: passed.
- Artifact secret scan: 2 passed.
- `git diff --check`: passed.

## Requirement Coverage

- **AGENT-04:** Contract, validation, and registered prompt are implemented.
  Live/replay orchestration continues in later waves.
- **AGENT-01:** Partial. Design Brief now supplies structured intent to the
  future BIM JSON Generator; BIM JSON generation remains Wave 2.
- **AGENT-02:** The prompt limits clarification to 1-3 Chinese questions and
  preserves missing facts instead of applying defaults.

## Security Notes

- The prompt and schema contain no provider configuration or secrets.
- Design Brief rejects BIM JSON root collections and forbids raw IFC/STEP at
  the prompt registry boundary.

## Deviations from Plan

- The project-wide diagnostic convention is `UNSUPPORTED_FIELD`, so the RED
  test was corrected before GREEN rather than introducing a second error code.
- `gsd-sdk` remained unavailable on PATH; equivalent inline gates were used.

## Self-Check: PASSED

All Wave 1 acceptance criteria and verification commands pass.

## Next

Proceed to `06-02-PLAN.md`: registry-rendered BIM JSON generation and
conditional failure routing.
