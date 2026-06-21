# 06-02 Summary: BIM JSON Generator and Conditional Failure Routing

**Completed:** 2026-06-21
**Plan:** `06-02-PLAN.md`
**Status:** Complete

## Objective

Implement registry-rendered BIM JSON generation through deterministic provider
adapters and evidence-backed routing for success, repair, Draft, and blocking
failure outcomes.

## Commits

| Type | Commit | Description |
|---|---|---|
| RED | `c4bdfeb` | Added failing Generator and failure-routing tests |
| GREEN | `efd108c` | Implemented Generator, registered prompt, and router |

## Implemented

- `prompts/agent/bim-json-generator-v1.md` consumes Design Brief, schema and
  capability context, named few-shots, and deterministic feedback.
- `src/text2ifc_agent/generator.py` validates Design Brief, renders the
  registered prompt, validates trace identity, invokes fake/file-compatible
  providers, rejects provider boundary violations, and classifies output as
  Formal, Draft, or invalid.
- `src/text2ifc_agent/failure_routing.py` records exactly one route:
  `no_repair_needed`, `repair_attempted`, `draft_required`, or
  `blocked_failure`.
- Repair requires all feedback-declared fact paths to exist in known facts.
  Missing paths route to Draft; completed repair must reduce issue count or
  return Draft, otherwise the run blocks.
- Successful first-pass output records zero repair attempts.

## Verification

- RED: 6 expected failures because Generator and Failure Router were missing.
- Focused GREEN/regression slice: 20 passed.
- Full Agent regression: `python -m pytest tests/agent -q` produced 52 passed.
- `python -m compileall src scripts -q`: passed.
- Artifact secret scan: 2 passed.
- `git diff --check`: passed.

## Requirement Coverage

- **PROMPT-01:** Generator calls now use registered prompt identity, hash,
  structured renderer inputs, and required trace paths. Persistent trace
  writing remains Wave 4 integration work.
- **REPAIR-01:** Four routes and bounded repair evidence are implemented and
  tested. Repair is conditional and cannot fill undeclared user facts.
- **AGENT-01:** Fake/file provider output can now become validated Formal BIM
  JSON 2.0 or explicit Draft. This plan does not claim a live provider run.

## Security Notes

- Raw IFC, STEP, and low-level helper output remains blocked by provider
  guardrails before parsing.
- No provider credentials, headers, or URLs are persisted by Generator.

## Deviations from Plan

- Generator and router RED behaviors were grouped in one test file and one
  RED commit because both modules share the same Formal/Draft trace contract.
- `gsd-sdk` remained unavailable on PATH; equivalent inline gates were used.

## Self-Check: PASSED

All Wave 2 acceptance criteria and plan-level verification commands pass.

## Next

Proceed to `06-03-PLAN.md`: Audit Agent and deterministic gate integration.
