# 06-00 Summary: Prompt Registry and Multi-agent Design Contract

**Completed:** 2026-06-21
**Plan:** `06-00-PLAN.md`
**Status:** Complete

## Objective

Create the Phase 6 control layer for prompt identity, structured rendering,
trace validation, and explicit multi-agent responsibility boundaries.

## Commits

| Type | Commit | Description |
|---|---|---|
| RED | `4f355bf` | Added the failing prompt trace identity test |
| RED | `3b69a9b` | Added failing registry loading and rendering behavior |
| GREEN | `cf64af1` | Implemented the versioned prompt registry and renderer |
| Documentation | `38937da` | Defined multi-agent responsibility and evidence boundaries |

## Implemented

- `prompts/agent/registry.json` registers `bim-json-generator.v3` with its
  role, mode, source path, SHA-256 identity, required inputs, and forbidden
  output classes.
- `src/text2ifc_agent/prompt_registry.py` loads and verifies registered prompt
  hashes, renders structured inputs, and rejects incomplete or inconsistent
  prompt traces.
- `tests/agent/test_prompt_registry.py` proves missing prompt identity is
  rejected and registered templates render with stable metadata.
- `docs/architecture/phase-6-multiagent-design.md` defines the Design Brief,
  Generator, conditional failure routing, Audit, and Observer responsibilities.
- The architecture document explicitly identifies `two-room-suite` as a
  deterministic hard-coded geometry gate rather than live provider evidence.

## Verification

Focused RED verification:

```powershell
python -m pytest tests/agent/test_prompt_registry.py -q
```

Result before implementation: 2 failed for the expected missing
`text2ifc_agent.prompt_registry` feature.

Focused GREEN and provider regression:

```powershell
python -m pytest tests/agent/test_prompt_registry.py tests/agent/test_agent_providers.py -q
```

Result: 11 passed.

Plan-level Agent regression:

```powershell
python -m pytest tests/agent -q
```

Result: 43 passed.

Additional checks:

- `python -m compileall src scripts -q`: passed.
- `python -m pytest tests/agent/test_artifact_scan.py -q`: 2 passed.
- `git diff --check`: passed.

## Requirement Coverage

- **PROMPT-01:** Partially implemented. Registry identity, hash verification,
  renderer inputs, and trace requirements exist; provider orchestration and
  full trace bundle integration continue in later plans.
- **OBS-01:** Foundation implemented. Prompt provenance can now be recorded;
  experiment metrics and generated run reports remain Wave 4 work.
- **DEPLOY-01:** Architectural foundation only. Deployable service packaging
  remains Wave 6 work.

## Security Notes

- Registry and renderer code introduce no network calls.
- Prompt traces require artifact paths but do not record provider tokens,
  headers, or private URLs.
- Provider output guardrails remain unchanged and passing.

## Deviations from Plan

- `gsd-sdk` was not available on the current PowerShell PATH. The plan was
  executed inline using the same RED/GREEN, verification, summary, state, and
  atomic commit gates. No product behavior was skipped.

## Self-Check: PASSED

All Wave 0 acceptance criteria and plan-level verification commands pass.

## Next

Proceed to `06-01-PLAN.md`: Design Brief Agent schema, validator, and registered
Chinese-first prompt.
