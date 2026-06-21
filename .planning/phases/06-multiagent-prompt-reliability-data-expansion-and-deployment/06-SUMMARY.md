# Phase 6 Summary: Multi-agent Prompt Reliability and Deployment

**Completed:** 2026-06-21
**Status:** Complete
**Branch:** `multiagent-design`

## Result

Phase 6 now provides a traceable Chinese-first multi-agent text2IFC path:

Chinese request -> Design Brief -> registered Generator prompt -> BIM JSON 2.0
or Draft -> deterministic validation -> IFC2X3 compile/reopen -> geometry gate
-> semantic audit -> generated Markdown report.

The final acceptance directory is:

`dataset/processed/agent-demo/phase6-multiagent/`

It contains a real 16,014-byte IFC2X3 file, a generated `report.md`, and the
complete supporting trace bundle.

## Delivered Waves

| Wave | Delivery |
|---|---|
| 06-00 | Versioned prompt registry, hash-verified rendering, trace contract, and multi-agent role boundaries |
| 06-01 | Validated Chinese-first Design Brief contract and prompt |
| 06-02 | Registry-backed BIM JSON Generator and four-route conditional failure handling |
| 06-03 | Evidence-linked Audit Agent subordinate to deterministic gates |
| 06-04 | Experiment harness, five controlled outcome classes, metrics, and generated reports |
| 06-05 | License/provenance/split-safe 100-record manifest and evidence-based model decision |
| 06-06 | Repeatable service CLI, final IFC demo, complete report, and deployment boundary |

## Final Acceptance Evidence

The final service demo records:

- BIM JSON status: `formal`
- provider mode: `fake`
- compile/reopen: passed
- geometry gate: passed
- Audit Agent: passed
- failure route: `no_repair_needed`
- repair attempts: `0`
- secret findings: `0`

IfcOpenShell reopened the final artifact as IFC2X3 and found four `IfcWall`
objects, one `IfcSpace`, one `IfcDoor`, and one `IfcWindow`.

`report.md` is generated from persisted sidecars and includes the original
Chinese input, Design Brief, rendered prompt, raw output, parsed BIM JSON,
validation feedback, geometry feedback, failure route, audit result, metrics,
and final artifact paths.

## Data and Model Decision

The Phase 6 manifest contains 100 records linked to 25 authorized IFC2X3
sources and 19 isolated scene families:

- train: 68, training-eligible;
- validation: 20, evaluation-only;
- test: 12, evaluation-only.

Prompt-only multi-agent generation plus deterministic gates is the selected
deployment baseline. Conditional repair remains available only after failure.
RAG and fine-tuning are deferred until Chinese-first reviewed data and a real
provider validation/test benchmark show measurable need.

## Verification

- Phase 6 Agent, service, and dataset suite: 72 passed.
- Full repository regression after LFS fixture materialization: 368 passed in
  827.09 seconds.
- Service tests: 4 passed.
- Training-manifest tests: 6 passed.
- `python -m compileall src scripts -q`: passed.
- `python scripts/service/run_text2ifc_service_demo.py --check`: passed.
- `python scripts/dataset/build_phase6_training_manifest.py --check`: passed.
- Final artifact secret scan: 0 findings across 17 files.
- Final IFC compile, reopen, and geometry quality gates: passed.
- Git diff whitespace check: passed.

The first full regression run exposed unmaterialized Git LFS IFC fixtures.
After pulling only the required BIMNet and buildingSMART IFC objects into the
C-drive worktree, the remaining Windows-only schema hash failure revealed a
missing LF rule. `.gitattributes` now fixes BIM JSON schema files to LF, and
the full regression passes.

## Provider Status

The deterministic acceptance path uses the fake provider. The final
`--check-config` run reported that `ANTHROPIC_AUTH_TOKEN`,
`ANTHROPIC_BASE_URL`, and `TEXT2IFC_MIMO_MODEL` were absent from the executing
process. No live Mimo Phase 6 quality claim is made, and no secret or private
provider URL was written to artifacts or documentation.

## Deployment Boundary

`scripts/service/run_text2ifc_service_demo.py` is a repeatable CLI service
boundary for complete, Draft, and blocked scenarios. It reuses the shared
prompt registry, Generator, routing, validation, compilation, geometry, Audit,
reporting, and secret-scan path.

It is not yet an HTTP production service or evidence of live model accuracy.
Those are later deployment increments built on the now measurable and
traceable boundary.

## Requirement Coverage

- **PROMPT-01:** Complete.
- **AGENT-04:** Complete.
- **AGENT-05:** Complete.
- **REPAIR-01:** Complete.
- **OBS-01:** Complete.
- **MODEL-01:** Complete through measured comparison and decision.
- **MODEL-02:** Complete through license/split-safe expansion and explicit
  fine-tuning deferral criteria.
- **DEPLOY-01:** Complete for the supported CLI service boundary and final
  trace-backed IFC demo.

## Final Review

Focused code review found no blocking correctness, security, or traceability
issues. Deterministic gates remain authoritative, Draft cannot compile,
successful first-pass generation records zero repairs, reports are generated
from sidecars, and secrets remain excluded.
