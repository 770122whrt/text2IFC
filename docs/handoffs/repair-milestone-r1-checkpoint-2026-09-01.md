# Phase 12.1 / Repair Milestone R1 Checkpoint Handoff

- Date: 2026-09-01
- Repository: `E:\code for project\bimnet`
- Branch: `codex/workflow-dataset-links`
- Implementation checkpoint: `223e46e7`
- Status: partial; safe checkpoint for a new conversation
- Canonical state: `.planning/STATE.md`
- Evidence matrix: [Plan 07 and R1 genuine execution matrix](../validation/repair-milestone-r1/plan07-r1-genuine-execution-matrix-2026-09-01.md)

## 1. Purpose and audience

This handoff is for the next engineer or Codex conversation taking over Phase
12.1 / Repair Milestone R1. It records what is implemented and genuinely
verified, what stopped the latest run, where the IFC artifacts are retained,
and the exact order for resuming work. It is not a Phase-closure or final Proof
claim.

## 2. Upstream baseline

The frozen repair pipeline is:

```text
public repair request
-> Stage 1 RepairIntent
-> deterministic target resolution
-> BGE-M3/Qdrant authoritative Top-K
-> Stage 1.5 property_resolution Provider decision
-> deterministic admissibility + ExactPropertyIntent
-> Stage 2 bound ChangeSet
-> atomic IFC apply
-> IfcOpenShell reopen
-> L0/L1/L2 and preservation evaluation
-> terminal publication
```

The production path remains alias-free and fail-closed. It does not use a
synthetic, cached, reviewed-alias, or test-runtime fallback. Private pristine
IFC, Gold, mutation/deletion truth, benchmark expected labels, and existing
Proof remain outside Provider input.

## 3. Implemented delta at checkpoint `223e46e7`

The checkpoint groups already-tested R1/Phase 12.1 work by responsibility:

- production BGE-M3/Qdrant configuration and lifecycle reuse;
- Stage 1.5 retrieval/admissibility boundary corrections;
- Stage 1/1.5/2 live attempt provenance and thinking-mode evidence;
- Stage 2 mixed-manifest authority through versioned ChangeSet 0.5;
- H1 mixed structural/property semantic binding and atomic preservation;
- copy-on-write occurrence-property authoring for shared property objects;
- R1 evaluator budget/RSS accounting and production source binding;
- a manifest-bound R1 genuine runner that stops on the first deterministic or
  infrastructure defect;
- immutable Stage 1 prompts v0.9/v0.10. Prompt v0.10 makes internal IDs distinct
  from IFC GlobalId/Tag/Name, and Stage 1 rejects invalid internal IDs rather
  than normalizing Provider output;
- focused regression coverage for the above boundaries.

The commit deliberately excludes PDF/dataset catalog work, `.tmp-*`, raw live
runs, uncurated Proof, root `AGENTS.md`, and unrelated user deletions.

## 4. Current end-to-end state

### Plan 07 four-case matrix

The frozen four-case genuine run completed all four case contracts with 11
DeepSeek calls (`stage1=4`, `property_resolution=4`, `stage2=3`). Three success
cases reached apply/reopen and L0/L1/L2; the unsupported-program guard correctly
stopped after Stage 1 with no artifact.

The result is genuine case-contract PASS, but its top-level final Proof fields
remain non-final: `acceptance_eligible=false`,
`proof_acceptance_eligible=false`, and
`proof_validation_status=pending_plan_12_14`. Therefore it does not by itself
close Phase 12/12.1.

Evidence:
[live-uat-result.json](../../dataset/processed/proof/ifc-repair-success-cases/structural/live/phase12-live-deepseek-complete/provider-evidence/live-uat-result.json)

### R1 fresh 12-case run

The append-only run
`r1-20260901T055419268779Z` used production BGE-M3/Qdrant and genuine
`deepseek-v4-flash` with thinking enabled. It stopped fail-closed at H3:

- E1-E4, M1-M3, H1, H2: 9 cases passed;
- H3: deterministic stop `LIVE_CASE_PROPERTY_IDENTITY_NOT_OFFERED`;
- H4 and A1: not executed because the ordered runner stopped at H3;
- calls before stop: 33 (`stage1=12`, `property_resolution=11`, `stage2=10`);
- every successful case has a retained repaired IFC and L0/L1/L2 PASS.

Evidence:
[r1-execution-result.json](../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260901T055419268779Z/r1-execution-result.json)

## 5. H3 blocker: confirmed facts and unresolved cause

### Confirmed repository/runtime facts

- Frozen H3 request: set the `Level 2` 819 mm x 759 mm Window as external.
- Stage 1 produced a valid property operation with stable internal ID
  `set-window-external-1`, natural-language property phrase `外窗`, and
  `raw_value=true`.
- Target resolution returned `status=clarification_required`,
  `reason_code=not_found`, and an empty candidate list.
- The R1 fixture carries a stable semantic/authoritative answer identity, but
  the runtime had no currently offered target candidate against which it could
  bind the frozen resume answer.
- The runner stopped before Stage 1.5 and Stage 2. No repaired IFC was published.

Evidence:

- [H3 case result](../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260901T055419268779Z/cases/H3/case-result.json)
- `dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260901T055419268779Z/cases/H3/runtime/runs/repair-b258ab308dd74731a8fde7ebc981a49a/`

### Unresolved

Why the frozen H3 geometry/storey target selector produced zero public target
candidates has not been diagnosed in this conversation. Do not infer that the
property is unsupported, do not weaken offered-set validation, and do not patch
the fixture or Prompt before tracing source IFC -> resolver -> offered target
set.

## 6. Evidence ledger and strongest layer

| Evidence | Result | Highest supported layer |
|---|---|---|
| Focused Stage 1 ID/prompt plus mocked full chain | `5 passed` | L1 deterministic/offline integration |
| H1 single genuine diagnostic | PASS, 3 calls | L3 live case viability |
| E2 single genuine diagnostic | PASS, 3 calls | L3 live case viability |
| Plan 07 frozen four cases | 4/4 case contracts PASS | L3 live + case L0/L1/L2; final Proof pending |
| R1 fresh ordered run | 9 PASS, H3 stop, 2 not executed | Partial L3 live; not R1 acceptance |
| R1 Proof 0.3 curation | not run for this fresh partial run | not reached |
| Final IFCCompare / Phase closure | not run | not reached |

Focused E2 diagnostic:
`dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-e2-genuine-diagnostic-20260901T054811235740Z/`

Focused H1 diagnostic:
`dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-h1-genuine-diagnostic-20260901T052645933962Z/`

## 7. Claim boundary

Supported claims:

- the committed implementation checkpoint is runnable and its focused Stage 1
  and public full-chain regressions pass;
- Plan 07 four genuine cases passed their case contracts;
- nine R1 cases genuinely passed apply/reopen/L0/L1/L2 in the fresh run;
- no alias or synthetic fallback was used in those runs.

Not supported:

- R1 12/12 acceptance;
- independent R1 Proof 0.3 success;
- final IFCCompare success;
- Phase 12 or 12.1 closure;
- Phase 13 readiness.

## 8. Local artifact and remote state

- Provider endpoint used by the retained live evidence:
  `https://api.deepseek.com/chat/completions`.
- Model: `deepseek-v4-flash`; requested thinking mode: enabled.
- Retrieval runtime: production `BAAI/bge-m3` + Qdrant, 472 authority records,
  collection `ifc2x3-property-vector/0.2`.
- Raw genuine evidence and repaired IFC files are retained locally under
  `dataset/processed/`; they are intentionally not part of the code checkpoint.
- No server-side deployment or artifact synchronization is claimed.

## 9. Remaining work in dependency order

1. Diagnose H3 target resolution read-only and freeze a focused offline
   reproduction.
2. If a deterministic defect is confirmed, fix it generally and run the
   focused offline target/resume family.
3. Run H3 alone genuinely. Stop again on any new deterministic/model failure.
4. Only after H3 passes, start a new fresh ordered R1 12-case run; do not splice
   old and new runs into one uninterrupted experiment.
5. Independently recompute and curate eligible R1 Proof 0.3 evidence.
6. Complete the frozen final gates, summaries, STATE/ROADMAP closure, and only
   then consider Phase 13.

## 10. Git recovery and reproduction entry points

- Repository root: `E:\code for project\bimnet`
- Branch: `codex/workflow-dataset-links`
- Implementation checkpoint: `223e46e7`
- The worktree remains dirty because unrelated user changes, temporary test
  directories, and raw live evidence are deliberately preserved.
- Never use `reset`, `clean`, or `add -A` when resuming.

Read first in the new conversation:

1. this handoff;
2. [execution matrix](../validation/repair-milestone-r1/plan07-r1-genuine-execution-matrix-2026-09-01.md);
3. `.planning/STATE.md`;
4. `.planning/phases/12.1-property-resolution-rag-reranker/12.1-SPEC.md`;
5. `.planning/phases/12.1-property-resolution-rag-reranker/12.1-VALIDATION.md`;
6. `.planning/phases/12.1-property-resolution-rag-reranker/12.1-07-PLAN.md`;
7. the H3 case result and runtime directory listed above.
