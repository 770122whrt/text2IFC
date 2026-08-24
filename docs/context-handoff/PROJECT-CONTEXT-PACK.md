# Project Context Pack

- Last updated: 2026-08-23
- Repository: `text2ifc` / BIMNet workspace (`E:\code for project\bimnet`)
- Branch: `codex/workflow-dataset-links`
- Commit / HEAD: `46c4173803adf91176a37e5ea85d8512d6ea8cd9`
- Maintainer: Codex-assisted
- Purpose: cross-conversation technical handoff
- Worktree state: dirty; branch is one commit ahead of `origin/codex/workflow-dataset-links`

This pack is a current-state orientation document, not a specification, release
record, acceptance report, or replacement for repository authorities. Update it
when the current phase, contracts, production path, or completion evidence
materially changes.

## Evidence labels and authority order

- **Confirmed Repository Fact** — observed in the current branch, worktree,
  production code, schemas, tests, or authoritative planning artifacts.
- **User/Project Decision** — frozen by an active SPEC, VALIDATION, ROADMAP, or
  project guidance even if final acceptance is still pending.
- **Codex Hypothesis** — an interpretation that still requires evidence. This
  initial pack contains no hypothesis presented as implementation fact.

For current work, use this precedence:

1. the user's active, explicitly frozen scope;
2. the applicable phase SPEC and VALIDATION, then its ordered active PLAN;
3. versioned schemas, registries, prompt records, and production implementation;
4. focused tests and machine-readable run/Proof evidence;
5. `.planning/STATE.md`, `.planning/ROADMAP.md`, and
   `.planning/REQUIREMENTS.md` for execution and milestone status;
6. architecture documents and reports as orientation or historical evidence.

`docs/README.md` is the stable documentation index. `.planning/PROJECT.md`
still describes the project value and long-lived constraints, but its dated
"Current State" prose is older than `.planning/STATE.md` and must not be used to
override the active Phase 12.1 state.

## 1. Current Scope

### Product scope

**Confirmed Repository Fact:** The repository contains two related but distinct
flows:

1. the shipped text-to-new-IFC generation baseline, which turns a natural-
   language brief into structured BIM JSON and deterministically compiles
   IFC2X3; and
2. the v1.1 IFC ChangeSet Repair Pipeline, which accepts an existing IFC2X3
   model plus a repair request and produces a traceable semantic ChangeSet and
   an independently validated repaired IFC.

**Confirmed Repository Fact:** The active milestone is `v1.1 — IFC ChangeSet
Repair Pipeline`. The current focus is Phase 12.1, Property Resolution RAG and
Reranker Correction. Formal planning status is **Plan 5 of 7 complete** and
**Phase 12 live acceptance blocked**.

**Confirmed Repository Fact:** Current repair operation registration includes:

- `add_window_with_opening_to_wall`;
- `add_opening_to_wall`;
- `add_door_with_opening_to_wall`;
- `fill_existing_opening_with_door`;
- `add_beam`;
- `add_column`;
- `set_occurrence_properties` for existing `IfcWindow`, `IfcDoor`, `IfcWall`,
  `IfcWallStandardCase`, `IfcBeam`, and `IfcColumn` occurrences.

**User/Project Decision:** Wall support in Phase 12.1 is property-only. There is
no `add_wall` operation. Beam/Column scope remains straight rectangular members:
horizontal Beam, vertical Column, center-axis placement, frozen structural
geometry thresholds, exact or deterministic Type policy, and optional material
or properties only when explicitly requested or otherwise authorized by the
frozen contract.

### Current non-goals

**User/Project Decision:** Do not start Phase 13, add structural-analysis nodes,
add grids or connectivity analysis, expand Door/Window geometry, relax L1/L2,
change Storey or Type/material policy, expose private Gold, introduce
Provider-output compatibility aliases, or add arbitrary/curved structural
profiles as part of Phase 12.1.

## 2. Architecture

### Generation baseline

```text
natural-language design request
  -> Design Brief / expected facts
  -> generation agents and scoped revisions
  -> BIM JSON 2.0
  -> deterministic gates
  -> deterministic IfcOpenShell IFC2X3 compilation
  -> audit / issue normalization / reporting
```

The detailed generation baseline is documented in
`docs/architecture/current-workflow-and-data-flow.md`. That document's
"existing IFC editing unsupported" boundary describes the generation pipeline,
not the later repair subsystem.

### Current repair architecture

```text
existing IFC2X3 + public repair text
  -> RepairAPI / durable RunStore
  -> source validation + deterministic SQLite index
  -> Stage 1 Provider: compact classification and RepairIntent extraction
  -> deterministic target, Type, parameter, and property resolution
       exact canonical property -> exact no-RAG path
       natural-language property -> eligibility filter
                                  -> multilingual vector Top-K
                                  -> bounded Stage 1.5 Provider
                                  -> deterministic admissibility
                                  -> program-built ExactPropertyIntent
  -> Stage 2 Provider: selected full profiles/few-shots -> ChangeSet draft
  -> deterministic semantic authority + Binder + Audit
  -> transactional apply to a candidate copy
  -> reopen IFC2X3 + L0/L1/L2/preservation evaluation
  -> atomic terminal publication or diagnostic-only failure artifacts
```

**Confirmed Repository Fact:** `RepairAPI` is the public behavioral facade used
by Python callers and the repair CLI. It persists stage transitions, supports
clarification continuation and restart, rejects non-IFC2X3 sources, and keeps
private benchmark originals and mutation mappings outside its constructor and
`start` input.

**Confirmed Repository Fact:** The default operation registry owns target,
parameter, prompt-profile, apply, comparison, and evaluation behavior per
operation. The common orchestrator does not implement Window/Door/Beam/Column
semantics itself.

## 3. Runtime and Data Flow

### Stage 1 — request classification and extraction

**Confirmed Repository Fact:** `generate_repair_intent` uses RepairIntent 0.8
for the default public API. Its prompt receives only the public repair request,
the compact supported-operation catalog, the closed semantic-body schema, and
bounded validation feedback. The compact catalog contains routing information
and intent schemas; Stage 1 does not load the full operation few-shot bundle.

Stage 1 is responsible for:

- identifying supported operation types and routing profile IDs;
- extracting user-stated target, parameters, clauses, and provenance;
- emitting either exact canonical property claims or natural-language property
  claims (`property_phrase`, raw value/unit, scope, provenance);
- exposing unsupported requests rather than inventing executable facts.

It is not responsible for target authorization, vector retrieval, candidate
selection, canonical IFC property construction, ChangeSet binding, IFC writes,
or structural-analysis advice.

### Exact-property path

**Confirmed Repository Fact:** An explicit canonical `Pset.Property` claim uses
the deterministic exact resolver. It validates registry applicability,
single-value template, value type, unit, scope, and existing project facts. It
does not use fuzzy matching, vector search, or aliases.

### Natural-language property path and Stage 1.5

**Confirmed Repository Fact:** The current production modules implement this
bounded chain:

1. `PropertyKnowledgeRuntime` loads authorable public IFC2X3 PSD/current-project
   scalar records and filters by target class, template, value/unit, and
   occurrence scope.
2. Local BGE-M3 embeddings plus a versioned Qdrant collection retrieve at most
   the policy Top-K. The default policy's maximum is five.
3. `ifc-property-resolution.v0.1` receives one query, its persisted candidate
   set, the decision schema, and validation feedback only.
4. The Stage 1.5 Provider can return one offered candidate, clarification, or
   unsupported. It has at most two attempts and cannot return executable Pset,
   Property, value type, unit, scope, or authoring fields.
5. Deterministic admissibility reopens the authoritative record and checks
   offered membership, record equality, class applicability, scalar template,
   value/unit/scope compatibility, retrieval floor, and unresolved conflicts.
6. Program code constructs `ExactPropertyIntent`: canonical set/property/type
   come from the authoritative record; normalized value/unit and provenance
   remain bound to the original user claim.

**User/Project Decision:** Vector rank, Top-1, and score margin are retrieval
evidence only. The LLM makes a bounded semantic selection among offered
candidates; neither vector output nor LLM text is directly authorable.

**Confirmed Repository Fact:** Candidate, decision, admissibility, and exact-
intent artifacts are persisted as durable run checkpoints. Clarification
answers bind to one run, operation, claim, generation, and offered candidate.
Stage 2 does not run until property resolution is exact.

### Stage 2 — ChangeSet draft

**Confirmed Repository Fact:** `generate_bound_changeset` receives only resolved
operations. It selects the full operation prompt profiles and few-shots for the
operation types actually present, renders a closed ChangeSet-draft schema, and
allows at most two Provider attempts. Program code binds the draft to semantic
manifests and a versioned bound ChangeSet before application.

### Apply, evaluate, and publish

**Confirmed Repository Fact:** The orchestrator applies the entire ChangeSet
once to a candidate output, reopens it, evaluates mandatory L0/L1/L2 and
preservation evidence, then atomically promotes a successful artifact. A failed
mandatory operation or evaluation does not publish a partial successful IFC;
diagnostic artifacts remain available.

## 4. Major Components

| Component | Current responsibility | Primary paths |
|---|---|---|
| Generation agents | Design brief, BIM JSON generation/revision, Provider adapters | `src/text2ifc_agent/`, `scripts/agent/` |
| Deterministic generation | BIM JSON validation and IFC2X3 compilation | `scripts/bim_json/`, `scripts/bim_json_v2/`, `src/text2ifc_compiler/` |
| Repair facade and lifecycle | Public API/CLI, durable runs, clarification, restart, terminal artifacts | `src/text2ifc_ifc_repair/api.py`, `cli.py`, `run_store.py`, `run_models.py`, `run_artifacts.py` |
| Repair stages | Stage 1 intent, Stage 1.5 property decision, Stage 2 draft | `request_stage.py`, `property_resolution_stage.py`, `provider_stage.py` |
| Deterministic repair core | Index, target/type/property resolution, semantic authority, audit, apply, orchestration | `src/text2ifc_ifc_repair/` |
| Operation plugins | Window, Opening, Door, Beam, Column, occurrence properties | `src/text2ifc_ifc_repair/operations/` |
| IFC knowledge | IFC2X3 declaration/PSD registry, property records, vector runtime | `src/text2ifc_knowledge/`, `schemas/ifc/generated/IFC2X3/` |
| Prompt registry | Immutable template records and operation prompt profiles | `prompts/agent/registry.json`, `src/text2ifc_ifc_repair/prompt_profiles.py` |
| Machine contracts | Repair, property-resolution, evaluation, BIM JSON, IFC knowledge schemas | `schemas/agent/`, `schemas/bim-json/`, `schemas/ifc/` |
| Phase 12 runners | Offline, public structural, live UAT, curation, independent Proof validation | `scripts/ifc_repair/run_phase12_*.py`, `curate_phase12_*.py`, `validate_success_cases.py` |
| Tests and fixtures | Contract, seam, API/CLI, IFC, dataset, Proof, regression evidence | `tests/knowledge/`, `tests/ifc_repair/`, `tests/fixtures/` |

## 5. Authoritative Contracts

### Active repair contracts

| Contract | Current version / role | Authority |
|---|---|---|
| RepairIntent envelope/body | `text2ifc/ifc-repair-intent/0.8` and body `0.8` in the default API | `schemas/agent/ifc-repair-intent-0.8.schema.json`, `ifc-repair-intent-body-0.8.schema.json` |
| Provider ChangeSet draft | `text2ifc/ifc-repair-changeset-draft/0.2` | `schemas/agent/ifc-repair-changeset-draft-0.2.schema.json` |
| Bound ChangeSet | additive versions through `text2ifc/ifc-repair-changeset/0.4`; current Door/structural semantic path binds 0.4 | `schemas/agent/ifc-repair-changeset-0.4.schema.json`, `src/text2ifc_ifc_repair/changesets.py` |
| IFC index | `text2ifc/ifc-index/0.5` | `src/text2ifc_ifc_repair/index_models.py` |
| Prompt profile schema | versions `0.1` and `0.2`; operations bind explicit profile IDs | `schemas/agent/ifc-repair-prompt-profile-0.1.schema.json`, `ifc-repair-prompt-profile-0.2.schema.json` |
| Evaluation | private/full `text2ifc/ifc-repair-evaluation/0.2`; public projection `0.2` | `schemas/agent/ifc-repair-evaluation-0.2.schema.json`, `evaluation_models.py`, `evaluation_projection.py` |
| Durable run | run state `0.1`, clarification `0.2`, result `0.1` | `schemas/agent/ifc-repair-run-state-0.1.schema.json`, `ifc-repair-clarification-0.2.schema.json`, `ifc-repair-result-0.1.schema.json` |

### Phase 12.1 property-resolution contracts

| Contract | Version | Key boundary |
|---|---|---|
| Query | `text2ifc/ifc-property-resolution-query/0.2` | one run/operation/claim plus original phrase/value/unit/scope |
| Candidate set | `text2ifc/ifc-property-candidate-set/0.1` | bounded, versioned public records and retrieval evidence |
| Rerank decision | `text2ifc/ifc-property-rerank-decision/0.1` | offered candidate ID, clarification, or unsupported only |
| Admissibility | `text2ifc/ifc-property-admissibility/0.1` | deterministic execution checks; no natural-language semantic decision |
| Retrieval policy | `text2ifc/property-resolution-policy/0.2` | Top-K, retrieval floor, supported template/scope, runtime readiness |
| Stage 1.5 prompt | `ifc-property-resolution.v0.1` | repair-only, one bounded claim, no authoring fields |
| Proof validation | `text2ifc/ifc-repair-proof-validation/0.2` | minimal validator-to-curator property-authority boundary; historical 0.1 semantics remain historical |

**Confirmed Repository Fact:** Live transcript evidence is now stage-aware.
Stage 1 and Stage 2 retain operation prompt-profile identity; Stage 1.5 records
the immutable Property Resolution template identity and is counted separately
as `property_resolution`. Provider wrappers preserve the actual transport
identity only through the bounded `ProviderEvidenceDelegator` protocol; the
outer wrapper type alone cannot make an attempt live-eligible.

**Confirmed Repository Fact:** The production live-UAT path constructs the real
BGE-M3/Qdrant runtime and fails closed when it is unavailable. The offline
mocked-transport full-chain path accepts a deterministic alias-free runtime at a
narrow dependency-injection seam while retaining the real RepairAPI,
orchestration, admissibility, Stage 2, IFC apply, reopen, and publication path.

**Confirmed Repository Fact:** Released/registered older schemas and prompt
profiles remain present. New behavior is additive; older contract files are not
rewritten in place.

**User/Project Decision:** `schemas/ifc/knowledge/property_aliases.json` is
historical evidence only. It is not the active standard for new natural-
language resolution, cannot be loaded into the active runtime or current Proof
replay, and cannot justify executable authorization. Current `RepairAPI`
construction rejects a `PropertyKnowledgeResolver` carrying aliases.

**User/Project Decision:** Phase 12.1 introduces no new hash/fingerprint
authorization gate. Stable IDs, explicit versions, persisted offered-set
membership, and deterministic record checks connect its stages. Existing source
integrity and accepted-artifact mechanisms elsewhere in the repair system are
unchanged.

## 6. Test Taxonomy

| Layer | What it proves | Representative locations |
|---|---|---|
| Schema/contract tests | closed versions, required fields, canonical rejection | `tests/ifc_repair/test_property_resolution_contract_v02.py`, repair-intent/ChangeSet tests |
| Stage seam tests | Stage 1, vector runtime, Stage 1.5, admissibility, Stage 2 behavior in isolation | `tests/knowledge/`, `test_property_resolution_prompt.py`, `test_property_resolution_stage.py`, `test_property_admissibility.py` |
| Resolution and API tests | deterministic binding, clarification lineage, persistence/restart, fail-closed behavior | `test_resolution_flow.py`, `test_property_resolution_api.py`, API/run-store tests under `tests/ifc_repair/` |
| Operation tests | geometry, Type/material, relationships, Psets, L1/L2 per family | Window/Door/Opening/structural tests under `tests/ifc_repair/` |
| Full-chain offline tests | public API/CLI, mixed atomicity, rollback, source immutability, private-Gold isolation | Phase 11/12 runner and dataset E2E tests |
| Frozen capability evaluation | Baseline/Candidate denominator, family slices, negatives, false-authorization gates | `tests/fixtures/knowledge/phase12_1_property_resolution.json`, `test_property_retrieval_evaluation.py` |
| Live Provider UAT | genuine Provider viability only after offline admission | `scripts/ifc_repair/run_phase12_live_uat.py` and persisted live run artifacts |
| Independent Proof | reopens artifacts and recomputes L0/L1/L2/preservation without trusting runner aggregates | `scripts/ifc_repair/validate_success_cases.py`, curation scripts, IFCCompare tooling |

**Confirmed Repository Fact:** Pytest is configured for Python 3.12+, with
`tests` as the test root, `src` and `.deps/python312` on the import path, and a
repository-local `.pytest-tmp` base directory. Live knowledge extras are
`qdrant-client` and `sentence-transformers`.

**Evidence rule:** A focused or offline pass does not prove live success. A live
case does not replace seam/full-chain offline admission. A single revealed case
turning green proves only that failure was fixed unless a frozen
Baseline/Candidate evaluation supports a broader claim.

## 7. Acceptance and Release Gates

**Confirmed Repository Fact:** Most Plan 12.1-06 offline plumbing and preflight
work is implemented, but frozen R12 Candidate evaluation remains blocked.
Phase-level closeout still requires, in order:

1. contract, retrieval, reranker, admissibility, and exact-intent tests;
2. the frozen minimum 60-case evaluation with Window/Door/Wall/Beam/Column
   slices and zero false standard authorization;
3. complete public API/CLI and five-family regression, including historical
   Door/Window contracts;
4. zero active legacy alias imports, fallback, or current Proof replay;
5. a fresh machine-readable preflight with zero failure, skip, substitution,
   timeout, and network call;
6. genuine DeepSeek complete, clarification/resume, Window semantic-canary,
   and unsupported-program-guard cases with no synthetic/cached fallback;
7. independent Proof recomputation, IFC reopen, strict L0/L1/L2/preservation,
   and IFCCompare;
8. final reports and state/requirement closure.

**Confirmed Repository Fact:** Checkpoints `2a87020b` and `4d2cd7d3`
implemented the Stage 1.5 contracts and preflight 0.3. Independent follow-up
review then proved the apparent Candidate 60/60 was still Gold-equivalent: the
second replay fixture exactly mapped evaluation queries to Gold answers.
Checkpoint `b8cf328e` deletes that answer table and makes evaluation 0.2 fail
closed with `INDEPENDENT_STAGE15_CANDIDATE_OUTPUT_REQUIRED`. A fresh real local
BGE-M3/Qdrant run passes the five evaluator tests and reports supported Top-K
recall 1.0, but all 60 semantic Candidate rows remain intentionally unscored.
Five-family/full-chain fixtures remain valid plumbing evidence, not semantic
Candidate evidence. Preflight 0.3 itself correctly binds
commit/worktree/runtime/timestamps and derives network attempted from observed
calls; its recorded 1100-test suite passed, but the artifact cannot admit Plan
06 because its R12 evaluation was later invalidated.

## 8. Non-Negotiable Invariants

1. Never mutate the source IFC in place; apply to a candidate and publish only
   after mandatory validation.
2. Production Provider input contains the damaged/public IFC evidence and user
   request only. Pristine pre-damage IFC, private Gold, mutation recipes,
   deleted identities, and private-derived facts enter only post-repair
   evaluation.
3. Providers never author STEP or receive whole-IFC JSON. IfcOpenShell and
   deterministic code own IFC2X3 construction.
4. No synthetic, cached, prerecorded, hand-authored, or fallback result may be
   reported as genuine live Provider evidence.
5. Noncanonical LLM output fails closed; do not add compatibility mappings to
   accommodate it.
6. Exact canonical properties use deterministic registry authority. Natural-
   language properties use vector recall plus bounded Stage 1.5, followed by
   deterministic admissibility and program-built exact intent.
7. Retrieval is discovery, not authorization. Candidate score/rank/margin never
   directly authorizes an IFC property.
8. ChangeSets apply atomically; one invalid operation or mandatory evaluation
   failure suppresses a successful IFC publication.
9. Successful artifacts must reopen as IFC2X3 and pass the applicable L0/L1/L2
   and preservation contracts.
10. Accepted committed Proof is append-only. Genuine failed live attempts are
    preserved and are not relabeled as successes.
11. Door/Window workflow, geometry thresholds, Storey policy, Type/material
    authority, and private-Gold isolation remain frozen during Phase 12.1.
12. Phase 13 and the 128k default-budget experiment must not begin before Phase
    12/12.1 closes.

## 9. Current Roadmap and Phase State

| Phase | Current state | What is true now |
|---|---|---|
| v1.0 / Phases 1–6.5 | Shipped/archive baseline | New-model generation path remains available and separate from repair |
| Phases 7–10.5 | Complete in current milestone records | Index, evaluation, public repair API, Type/property contracts, Window reference path, dataset/preservation infrastructure |
| Phase 11 | Complete | Opening/Door implementation accepted with genuine DeepSeek and independently recomputed Proof; frozen contracts remain in force |
| Phase 12 | Live acceptance blocked | Plans 12-01 through 12-14 complete; Beam/Column implementation and offline/live infrastructure exist; genuine complete case failed before Stage 2 with `PROPERTY_NOT_RESOLVED`; no live structural success was curated |
| Phase 12.1 | In progress, formal 5/7 | Plans 01–05 complete; Plan 06 is blocked on Gold-independent Stage 1.5 Candidate evidence; Plan 07 remains blocked |
| Phase 13 | Not started | BIMNet-scale retrieval and 128k experiment remain blocked on Phase 12/12.1 closure |

Current requirement state:

- complete: `RAG-01..04`, `OPS-01..02`, and preceding mapped requirements;
- pending: `RAG-05..07`, `OPS-03`, `OPS-04`;
- future/blocked: `SCALE-01`, `SCALE-02`.

The next authoritative execution plan is
`.planning/phases/12.1-property-resolution-rag-reranker/12.1-06-PLAN.md`.

## 10. Entry Points

### Read first

1. `docs/README.md`
2. `.planning/STATE.md`
3. `.planning/ROADMAP.md`
4. `.planning/REQUIREMENTS.md`
5. `.planning/phases/12.1-property-resolution-rag-reranker/12.1-SPEC.md`
6. `.planning/phases/12.1-property-resolution-rag-reranker/12.1-VALIDATION.md`
7. the active blocked PLAN, currently `12.1-06-PLAN.md`
8. `docs/validation/agent-capability-evaluation.md` before any Agent/LLM
   behavior change, capability claim, or real Provider run

### Production interfaces

- Python repair facade: `src/text2ifc_ifc_repair/api.py` (`RepairAPI`)
- Thin repair CLI adapter: `src/text2ifc_ifc_repair/cli.py` (`main`)
- Operation registry: `src/text2ifc_ifc_repair/operations/__init__.py`
- Prompt registry: `prompts/agent/registry.json`
- IFC knowledge runtime: `src/text2ifc_knowledge/property_runtime.py`

### Active Phase 12/12.1 execution and verification

- offline matrix: `scripts/ifc_repair/run_phase12_offline.py`
- public structural path: `scripts/ifc_repair/run_phase12_public_structural_repair.py`
- live matrix: `scripts/ifc_repair/run_phase12_live_uat.py`
- live/structural curation: `scripts/ifc_repair/curate_phase12_live_proof.py`,
  `curate_phase12_structural_proof.py`
- independent Proof validator: `scripts/ifc_repair/validate_success_cases.py`
- direct IFC comparison: `scripts/ifc_repair/compare_ifc.py`

The active VALIDATION's final admission command family is: full
`tests/knowledge` plus `tests/ifc_repair`, Phase 12 offline runner, Python
`compileall`, `git diff --check`, and independent success-case validation. Use
fresh run-local output directories and the repository `.venv`.

## 11. Risks and Open Questions

### Confirmed current risks

1. **R12 evaluation blocked:** real BGE Top-K retrieval is green, but no
   Gold-independent frozen Stage 1.5 Candidate outputs exist. The removed
   answer-table replay cannot be used as semantic Candidate evidence, and this
   task forbids a genuine DeepSeek call. Plan 06 and Plan 07 remain blocked.
2. **Live acceptance remains red:** the preserved genuine Phase 12 complete
   case failed before Stage 2 with `PROPERTY_NOT_RESOLVED`; no structural live
   success is in accepted Proof.
3. **Architecture-doc drift:**
   `docs/architecture/ifc-repair-pipeline-status-and-roadmap.md` describes the
   established two-Provider repair baseline and an older exact-property path;
   it does not yet describe the current Stage 1.5 worktree. The Phase 12.1 SPEC,
   VALIDATION, schemas, and code are the current authority for that correction.
4. **Project-state drift:** `.planning/PROJECT.md` has an older current-state
   snapshot. Use it for core value/constraints, not active phase status.
5. **Dirty-worktree isolation:** the worktree also contains unrelated PDF,
   dataset/catalog, requirements, documentation, generated run, temp, and user
   changes. They must not be reset, cleaned, or silently included in a Phase
   12.1 or context-pack commit.
6. **Protocol file not yet tracked:** project guidance and `docs/README.md`
   route Agent/LLM changes to
   `docs/validation/agent-capability-evaluation.md`, but that file is currently
   untracked in this worktree. Its commit status must be resolved deliberately;
   do not silently omit or absorb it.
7. **Temporary-run visibility:** `git status` reports many historical untracked
   `.tmp-*` directories. Cleanup is authorized only for the explicit run-local
   roots created by the current Plan 06 closeout after evidence is recorded;
   unrelated or historical evidence roots remain outside scope.

### Open questions requiring later evidence, not assumptions

- How frozen R12 will obtain Gold-independent Stage 1.5 Candidate outputs
  without violating the current prohibition on genuine DeepSeek calls in Plan
  06. No valid pre-Gold frozen output exists in the repository.
- The real local BGE-M3/Qdrant runtime was ready for Plan 06, but Plan 07 must
  rerun its fresh preflight rather than treating one environment snapshot as
  permanent readiness.
- Whether genuine DeepSeek passes all four required live cases after offline
  admission, and whether independent Proof/IFCCompare accepts the results.

## 12. Recent Material Changes

**Confirmed Repository Fact:** The Phase 12.1-06 implementation sequence is:

- `b65b5c67d3af87bc34ece461d791f150eb3f0670` — freezes the 60-case property
  evaluation fixture and evaluator test;
- `b320de411c4eb0c8525d47dc02238e2630894b23` — adds the evaluated alias-free
  retrieval policy/runtime integration and runner wiring;
- `46c4173803adf91176a37e5ea85d8512d6ea8cd9` — adds the five-family
  alias-retirement E2E test and amends the Phase 12.1 contracts/plans.
- `87b6f7c5` — preserves the alias-free runner/validator authority work and the
  context-handoff evidence package before external resolution.
- `2a87020b` — completes the Stage 1.5 live-evidence, deterministic runtime
  injection, four-case matrix and proof-validation 0.2 contracts.
- `4d2cd7d3` — freezes non-vacuous semantic groups, tracks the pytest
  environment shim and upgrades the complete preflight to 0.3; its Stage 1.5
  replay was later rejected as an answer-equivalent oracle.
- `b8cf328e` — deletes the replay answer table and makes evaluation 0.2 block
  when independent Stage 1.5 Candidate outputs are unavailable.

**Confirmed Repository Fact:** Plan 06 production/test/schema changes and the
anti-oracle correction are isolated in the checkpoints above. The remaining
scoped documentation changes record the blocked state in the issue context,
project context, STATE and ROADMAP; there is no accepted Plan 06 summary.
Unrelated PDF, dataset, requirements, docs, generated-run, protocol and temp
changes remain excluded.

**Confirmed Repository Fact:** Earlier current-milestone material changes are:

- Phase 11 Door/Opening closure with genuine DeepSeek, strict reopen/L0/L1/L2,
  and independently recomputed Proof;
- Phase 12 Beam/Column Plans 01–14 implementation and offline/live harness;
- the preserved Phase 12 live failure that localized the natural-language
  property-resolution gap before Stage 2;
- Phase 12.1 Plans 01–05: additive contracts/prompt, vector runtime, bounded
  Stage 1.5, deterministic admissibility/program exact intent, and durable API
  clarification/restart integration.

## 13. Reviewer Handoff

Before changing or accepting the current branch, a reviewer should retain these
facts:

1. **Confirmed:** branch is `codex/workflow-dataset-links`; Plan 06
   implementation/correction checkpoints are `2a87020b`, `4d2cd7d3` and
   `b8cf328e`.
2. **Confirmed:** the worktree is intentionally dirty; preserve unrelated user
   files and all genuine run/failure evidence.
3. **Confirmed:** formal state is Phase 12.1 Plan 5/7; Plan 06 is blocked.
4. **Confirmed:** no accepted `12.1-06-SUMMARY.md` or Plan 06 completion
   checkpoint exists; Plan 07 genuine live evidence remains absent.
5. **Confirmed:** Phase 12 live acceptance is blocked; no live structural
   success has been curated.
6. **Confirmed:** Phase 11 is closed and its Door/Opening acceptance contracts
   are frozen.
7. **Confirmed:** default repair Stage 1 uses RepairIntent 0.8 and compact
   operation profiles; Stage 2 loads only selected full profiles/few-shots.
8. **Confirmed:** explicit canonical properties bypass RAG; natural-language
   properties use the separate Stage 1.5 chain.
9. **Project Decision:** historical aliases are not an active resolver,
   fallback, prompt input, authorization source, or current Proof replay.
10. **Project Decision:** vector results and LLM output cannot directly supply
    executable property fields; code constructs the exact intent from authority
    plus the original user claim.
11. **Confirmed:** the default registry has seven operation types and no
    `add_wall`; Wall is property-only.
12. **Confirmed:** source immutability, damaged/public input, post-repair-only
    private Gold, atomic application, reopen, and strict L0/L1/L2 remain release
    boundaries.
13. **Project Decision:** no synthetic/cached/prerecorded fallback can count as
    live evidence.
14. **Confirmed:** five-family regression and preflight 0.3 execution are green,
    but Plan 12.1-06 has not passed frozen R12 Candidate evaluation.
15. **Confirmed:** Plan 12.1-07 owns genuine DeepSeek, independent Proof,
    IFCCompare, report, requirements, and state closeout.
16. **Project Decision:** do not start Phase 13 or reopen frozen
    Door/Window/structural/Storey/Type/material/private-Gold contracts.
17. **Confirmed:** the valid Plan 06 evidence proves real-BGE Top-K retrieval
    readiness and deterministic offline plumbing only; it does not admit Plan
    06 or prove Stage 1.5 semantics.
