---
phase: 08-l1-l2-evaluation-contract
status: complete
created: 2026-07-19
---

# Phase 8 Existing Pattern Map

| Planned role | New/modified file | Closest existing analog | Pattern to preserve |
|---|---|---|---|
| Evaluation domain records | `src/text2ifc_ifc_repair/evaluation_models.py` | `src/text2ifc_ifc_repair/index_models.py` | Frozen dataclasses, explicit schema-version constant, JSON-safe values |
| Canonical report/schema validation | `src/text2ifc_ifc_repair/evaluation.py`, `schemas/agent/ifc-repair-evaluation-0.2.schema.json` | `src/text2ifc_ifc_repair/target_query.py`, `schemas/agent/ifc-target-resolution-0.1.schema.json` | Exact version constants, canonical sorted JSON, Draft 2020-12 validation |
| Operation evaluation policy | `src/text2ifc_ifc_repair/evaluation_policy.py`, `src/text2ifc_ifc_repair/registry.py` | `src/text2ifc_ifc_repair/registry.py` | Immutable operation-owned contract, duplicate/unknown stable errors, common dispatch |
| Typed semantic extraction | `src/text2ifc_ifc_repair/semantic_facts.py` | `src/text2ifc_ifc_repair/indexer.py` | IfcOpenShell `get_psets` flattening, typed values, deterministic ordering, provenance |
| L1 model comparison | `src/text2ifc_ifc_repair/compare.py` | Existing `compare_ifc_models` and Window `_comparison_adapter` | Reopen IFC, compare by GlobalId not STEP order, independent geometry measurement |
| Window L2 policy | `src/text2ifc_ifc_repair/operations/window.py` | Existing `window_operation_definition` | Window-specific facts remain behind registry definition, not common evaluator |
| Benchmark/public projection | `src/text2ifc_ifc_repair/benchmark_evaluation.py` | `src/text2ifc_ifc_repair/projection.py` | Private input allowlist, public output allowlist, stable diagnostics for loss |
| Evidence workflow | `src/text2ifc_ifc_repair/workflow.py` | Existing atomic evidence staging/finalization | Immutable output directory, provider/private separation, artifact SHA-256 manifest |

## Data Flow

```text
Registry policy + ChangeSet + before/after diff
  -> L1 evidence/checks

request/surviving/prototype/(private gold) expectations
  + repaired IFC typed facts
  -> L2 evidence/checks

L1 + L2 + L3 observations + application state
  -> evaluation 0.2 strict aggregation
  -> private detailed report (benchmark only)
  -> allowlisted public report
  -> workflow terminal/publication status
```

## Reuse Constraints

- Do not merge Audit and Evaluation; Audit occurs before application.
- Do not place benchmark-original arguments on production evaluator functions.
- Do not reimplement Pset parsing differently from Phase 7 without a shared
  helper or parity tests.
- Do not make common evaluation aware of Window field names; policies and
  adapters own those details.
- Do not change evaluation 0.1 meaning in place.
