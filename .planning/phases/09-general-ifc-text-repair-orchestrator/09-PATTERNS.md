# Phase 9 Pattern Map

**Mapped:** 2026-07-20
**Purpose:** Reuse the closest existing contracts and runtime patterns while
keeping the new production orchestrator independent of the frozen benchmark.

## New Contract and Module Map

| Planned role | Recommended file | Closest analogs | Pattern to preserve |
|---|---|---|---|
| RepairIntent schema/model | `schemas/agent/ifc-repair-intent-0.1.schema.json`, `src/text2ifc_ifc_repair/repair_intent.py` | `ifc-target-query-0.1.schema.json`, `target_query.py`, `text2ifc_agent/design_brief.py` | Draft 2020-12 exact schema, frozen dataclass, canonical JSON, stable machine error codes. |
| Request-understanding prompt/stage | `prompts/agent/ifc-repair-intent-v0.1.md`, `request_stage.py` | `prompt_registry.py`, `clarification.py`, `provider_stage.py` | Registered hash-bound prompt, explicit required inputs, untrusted user delimiter, raw/parsed/validation/metrics evidence per attempt. |
| Run/clarification contracts | `schemas/agent/ifc-repair-run-state-0.1.schema.json`, `ifc-repair-clarification-0.1.schema.json`, `run_models.py` | `clarification.py`, `session_store.py`, `evaluation_models.py` | Immutable typed transitions, monotonic revisions/call indices, pending question IDs, deep-detached JSON state. |
| Durable run store | `run_store.py` | `session_store.py`, `index_store.py`, `workflow.py` staging | Exclusive create, SQLite/atomic transaction pattern, relative artifact paths, non-overwrite, reopen validation. |
| Production evidence builder | `production_evidence.py` | `semantic_facts.py`, `index_models.py`, `evaluation_policy.py` | Closed `EvidenceSourceKind`, typed units/values, provenance, formal relationship compatibility, per-operation mapping. |
| General orchestration | `orchestrator.py` | `workflow.py`, `interactive_cli_flow.py` | API returns typed results, progress callback is optional, every failure becomes structured evidence, common code owns stages. |
| Evidence finalization | `run_artifacts.py` or extracted workflow helper | `_finalize_evidence_bundle`, `evaluation_projection.py`, `artifact_scan.py` | Temp staging, relative hashes, public allowlist, canary scan, diagnostic versus success promotion. |
| CLI | `scripts/ifc_repair/repair.py` | `scripts/ifc_repair/index.py`, `run_case.py`, `scripts/agent/run_phase6_2_cli.py` | `argparse`, callable `main(argv)`, stable exit codes, no import-time I/O, human and JSON renderers over one API. |

## Reusable Assets

### Phase 7 retrieval

- `build_ifc_index(source, database)` already fingerprints/reopens the source,
  emits diagnostics, and atomically publishes SQLite.
- `TargetQuery.from_dict` and `resolve_target` already implement exact schema,
  hard constraints, evidence scoring, and resolved/ambiguous/not-found/conflict/
  unsupported results.
- `build_target_context` already caps candidates and UTF-8 bytes/tokens and
  projects only attribute-intent-relevant properties.

The orchestrator should call these APIs directly. Do not parse the stdout of
`scripts/ifc_repair/index.py` and do not reimplement candidate ranking.

### Agent clarification and trace

- `ClarificationController` demonstrates immutable turn/call records,
  monotonic call indices, pending-question validation, source-turn provenance,
  and explicit rerun.
- `SessionStore` demonstrates unique session/run directories, SQLite events,
  turns, artifacts, and reproducible export.
- `make_openai_design_brief_invoker` and `provider_stage.py` demonstrate
  registered prompt rendering, response parsing, live trace capture, metrics,
  and schema/semantic validation.

Reuse these shapes, but do not reuse Phase 6 Design Brief schemas/statuses as
the Phase 9 public contract. IFC target candidates and run-revision binding are
new requirements.

### ChangeSet/Audit/apply

- `provider_stage._binding_issues` already validates model/request binding,
  candidate scope, Registry target/parameter schemas, allowed conditions, and
  evidence pointers.
- `audit.py` is the deterministic pre-application authority.
- `apply.py` already uses a staged output and publishes only after application
  validation/reopen.
- `OperationRegistry` centralizes operation-specific behavior and L2 policy.

Extend binding to intent-to-operation cardinality and per-operation context;
do not add Window conditions to the general orchestrator.

### Evaluation/publication

- `ProductionEvaluationInputs` structurally excludes Ground Truth and already
  accepts `expected_facts_by_operation`.
- `semantic_facts_from_element_record` lifts Phase 7 records without losing
  provenance.
- `evaluate_production` and `evaluation_to_dict` are the production terminal
  authority.
- `project_public_evaluation` and final bundle canary scanning protect the
  public boundary.

The new production flow must call `evaluate_production`, not
`evaluate_benchmark`. Keep benchmark wrapping outside the public API.

## Established Patterns

1. **Contracts before behavior:** all Agent/state documents have an exact
   schema version and reject unknown fields before orchestration.
2. **Deterministic Gates outrank Agents:** Provider output may propose intent or
   ChangeSet but cannot authorize capability, identity, scope, evidence, Audit,
   or publication.
3. **Hash binding:** source, request, prompt template, candidate/context, and
   ChangeSet identity are reproducible and checked at stage boundaries.
4. **Immutable evidence:** raw/parsed/validation artifacts are retained; later
   attempts supersede rather than rewrite earlier evidence.
5. **Adapter-owned specialization:** Registry definitions own target classes,
   schemas, constraints, apply and evaluation; orchestration is family-neutral.
6. **Fail closed with diagnostics:** invalid/unavailable behavior becomes a
   structured terminal or clarification state and never a guessed success.

## Integration Landmines

- `workflow.py` imports `remove_window_and_opening`, reads
  `mutation_manifest.private.json`, and invokes `evaluate_benchmark`; it is an
  evidence fixture, not the base class for the production API.
- The current ChangeSet prompt still asks the model to match candidates by
  name. Phase 9 Stage 2 must receive a resolved binding and forbid reselection.
- `TargetQuery.resolved_target_id` is an internal record ID; ChangeSet target
  fields need the candidate's bare reliable IFC GlobalId.
- `ElementRecord.properties` may be comprehensive, but `build_target_context`
  intentionally projects only requested property terms.
- `SOURCE_PRECEDENCE` contains `PRIVATE_ORIGINAL` for benchmark use. The
  production builder must use the existing production allowlist and never
  construct that source kind.
- `apply_changeset` may call its output a published application candidate; the
  orchestrator must not promote it to the user-visible success path until
  Evaluation 0.2 passes.
- The worktree contains pre-existing untracked IFC repair baseline files.
  Execution plans must list/stage exact owned paths and never use `git add -A`.

## Recommended Test Analogs

| New test area | Closest tests to copy structurally |
|---|---|
| RepairIntent schema and status | `tests/agent/test_design_brief.py`, `tests/ifc_repair/test_target_query.py` |
| Provider attempt evidence | `tests/ifc_repair/test_provider_stage.py`, `tests/agent/test_live_clarification.py` |
| Clarification/resume | `tests/agent/test_interactive_cli_flow.py`, `test_interactive_cli_session.py` |
| Run store/tamper | `tests/ifc_repair/test_index_store.py`, `test_apply_transaction.py` |
| Multi-operation binding | `tests/ifc_repair/test_changesets.py`, `test_benchmark_evaluation.py` |
| Production semantic authority | `tests/ifc_repair/test_evaluation_policy.py`, `test_benchmark_evaluation.py` |
| Terminal publication matrix | `tests/ifc_repair/test_offline_e2e.py`, `test_evaluation_contract.py` |
| CLI modes | `tests/ifc_repair/test_index_cli.py`, `test_run_case_cli.py` |

## Plan Sequencing Constraint

The closest analogs confirm a strict dependency chain:

```text
RepairIntent contract
-> durable clarification/run state
-> Phase 7 resolution + Stage 2 binding
-> production facts + Audit/apply/evaluation/publication
-> CLI and realistic acceptance
```

These plans should not run concurrently against shared orchestrator files. The
later CLI plan may depend on every prior plan while still keeping its own
acceptance/report changes isolated.
