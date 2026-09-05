# Plan 07 and Repair Milestone R1 Genuine Execution Matrix

- Date: 2026-09-01
- Branch: `codex/workflow-dataset-links`
- Implementation checkpoint: `223e46e7`
- Provider: `deepseek-v4-flash`, thinking enabled
- Retrieval: production BGE-M3/Qdrant; no alias or synthetic fallback
- Overall status at this checkpoint: Plan 07 case contracts PASS; R1 partial at 9/12

This document keeps semantic/model outcome, deterministic execution, artifact
outcome, and evidence/contract outcome separate. `NOT_EXECUTED` is not PASS or
FAIL. At this historical checkpoint R1 was not closed.

## Closure update — 2026-09-03

This checkpoint has been superseded by a new uninterrupted 12/12 run and
independent Proof 0.3. The historical rows and false/pending eligibility fields
below remain unchanged. Current closure evidence is the
[final R1 Proof Matrix](repair-proof-matrix-2026-09-03.md), accepted run
`r1-20260902T152701658266Z` and curated Proof root
`dataset/processed/proof/repair-milestone-r1/r1-20260902T152701658266Z-curated/`.
The original Plan 07 four cases were also rerun once on the final code as
`uat-20260902T180900748385Z`: 4/4 PASS with 11 genuine calls. Its changed-scope
curator packaging limitation is recorded in the final matrix and is not
represented as a second independently curated Proof.

## 1. Plan 07 frozen four-case genuine matrix

Evidence:
[live-uat-result.json](../../../dataset/processed/proof/ifc-repair-success-cases/structural/live/phase12-live-deepseek-complete/provider-evidence/live-uat-result.json)

| Case | Request / intended path | Calls S1/S1.5/S2 | Semantic/model | Deterministic execution | IFC artifact and L0/L1/L2 | Evidence/contract |
|---|---|---:|---|---|---|---|
| `complete` | Beam + Column complete natural-language properties | 1/2/1 | two property decisions confirmed | apply and reopen succeeded | [repaired IFC](../../../dataset/processed/proof/ifc-repair-success-cases/structural/live/phase12-live-deepseek-complete/runtime/runs/repair-233cb4e15aad442fbcf00fbc10584f83/.terminal-bundles/6af48e15b81842aaac434bf8a1a07c1d/successful/repaired.ifc); L0/L1/L2 PASS | case contract PASS |
| `clarification-resume` | property clarification then stable-identity resume | 1/1/1 | clarification and selected property confirmed | resume, apply and reopen succeeded | result records repaired IFC and L0/L1/L2 PASS; only the complete-case IFC remains under the current curated root | case contract PASS |
| `window-semantic-canary` | Window `外窗=true` through Vector + Stage 1.5 | 1/1/1 | `Pset_WindowCommon.IsExternal` confirmed | apply and reopen succeeded | result records repaired IFC and L0/L1/L2 PASS; raw IFC path is no longer present under the current curated root | case contract PASS |
| `program-guard` | supported Beam request plus unsupported analysis program | 1/0/0 | unsupported program recognized | stopped before Stage 1.5/Stage 2/apply | no repaired IFC; L0/L1/L2 N/A by contract | guard contract PASS |

Aggregate: 11 genuine calls (`stage1=4`, `property_resolution=4`, `stage2=3`).
The top-level result still records `acceptance_eligible=false`,
`proof_acceptance_eligible=false`, and
`proof_validation_status=pending_plan_12_14`; therefore the matrix is not final
Phase closure.

## 2. R1 frozen 12-case ordered genuine run

Evidence root:
`dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260901T055419268779Z/`

[r1-execution-result.json](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260901T055419268779Z/r1-execution-result.json)

| Case | Frozen capability | Calls S1/S1.5/S2 | Semantic/model | Deterministic execution | IFC artifact / L0-L2 | Evidence/contract |
|---|---|---:|---|---|---|---|
| `E1` | existing Window `IsExternal=true` | 1/1/1 | confirmed | succeeded | [repaired.ifc](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260901T055419268779Z/cases/E1/runtime/runs/repair-cee46fdb9e8f4ea2b786f63e1258771b/.terminal-bundles/c9e0716105774a0eba3c2076e10291ab/successful/repaired.ifc); L0/L1/L2 PASS | PASS |
| `E2` | existing Door `FireRating="EI60"` | 1/1/1 | confirmed | succeeded | [repaired.ifc](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260901T055419268779Z/cases/E2/runtime/runs/repair-eee9ce9b4ea947b2a4753a2bb5977de3/.terminal-bundles/c9450bb510054741a488d7bb4b849732/successful/repaired.ifc); L0/L1/L2 PASS | PASS |
| `E3` | existing Beam `Reference="B-204"` | 1/1/1 | confirmed | succeeded | [repaired.ifc](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260901T055419268779Z/cases/E3/runtime/runs/repair-ce9877bef9a44d619856362082fa2c4f/.terminal-bundles/1cd6f6701bb245e7aaa2c61c2ae203d7/successful/repaired.ifc); L0/L1/L2 PASS | PASS |
| `E4` | existing Wall `AcousticRating="Rw 50"` | 1/1/1 | confirmed | succeeded | [repaired.ifc](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260901T055419268779Z/cases/E4/runtime/runs/repair-be713dd432b1484d9f56bb22a171c8dc/.terminal-bundles/740dcffce60d463bac6df56802ee719d/successful/repaired.ifc); L0/L1/L2 PASS | PASS |
| `M1` | Door FireRating invalid Boolean, `add_detail` correction to `EI60` | 3/2/1 | property identity retained through correction | initial no-mutation stop, resume succeeded | [repaired.ifc](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260901T055419268779Z/cases/M1/runtime/runs/repair-239f7e8cce564ed1844daa711b838a16/.terminal-bundles/f15f9fa02d774a949b0dceb37c919c86/successful/repaired.ifc); L0/L1/L2 PASS | PASS, 6 calls |
| `M2` | Beam add + generated Type + Reference | 1/1/1 | confirmed | succeeded | [repaired.ifc](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260901T055419268779Z/cases/M2/runtime/runs/repair-f460dfd4cfc24b97a3c15dd93ebb32ac/.terminal-bundles/b172ced0c5cf4b13865553288da404f0/successful/repaired.ifc); L0/L1/L2 PASS | PASS |
| `M3` | Column add + generated Type + LoadBearing | 1/1/1 | confirmed | succeeded | [repaired.ifc](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260901T055419268779Z/cases/M3/runtime/runs/repair-1ccaefb80f784d0f9d6e18e85d04d7f9/.terminal-bundles/a1d1ea6ed33f470e89cd9cba7d81991b/successful/repaired.ifc); L0/L1/L2 PASS | PASS |
| `H1` | atomic Beam add + existing Window FireRating | 1/1/1 | two-operation intent confirmed | mixed ChangeSet 0.5 applied atomically | [repaired.ifc](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260901T055419268779Z/cases/H1/runtime/runs/repair-503a6d3a9a554815966f353fce013c05/.terminal-bundles/a691d7bfb981424daa8c7270311e9e83/successful/repaired.ifc); L0/L1/L2 PASS | PASS |
| `H2` | atomic Door FireRating + Wall AcousticRating | 1/2/2 | both properties confirmed | two target operations applied atomically | [repaired.ifc](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260901T055419268779Z/cases/H2/runtime/runs/repair-22023759c6d34feeb677f730cceca79b/.terminal-bundles/bea3584b8149440081237826b95c32f4/successful/repaired.ifc); L0/L1/L2 PASS | PASS, 5 calls |
| `H3` | natural target clarification + resume | 1/0/0 | Stage 1 property intent valid; no target candidate offered | fail-closed before Stage 1.5/Stage 2 | no repaired IFC; L0/L1/L2 N/A | FAIL: `LIVE_CASE_PROPERTY_IDENTITY_NOT_OFFERED` |
| `H4` | supported Beam + unsupported analysis-node atomic guard | 0/0/0 | NOT_EXECUTED | NOT_EXECUTED | no artifact because run stopped earlier | NOT_EXECUTED |
| `A1` | exact existing Type reuse | 0/0/0 | NOT_EXECUTED | NOT_EXECUTED | no artifact because run stopped earlier | NOT_EXECUTED |

Aggregate before stop: 33 genuine calls (`stage1=12`,
`property_resolution=11`, `stage2=10`). Production property runtime readiness
was PASS with 472 records. No synthetic fallback or private-evidence leakage was
reported.

## 3. Focused regression and diagnostic evidence

| Check | Result | Meaning |
|---|---:|---|
| Stage 1 internal-ID retry + prompt registry + mocked public full chain | `5 passed` | the E2 internal-ID repair is locally admitted; does not prove live behavior alone |
| E2 single genuine diagnostic | PASS, 1/1/1 calls | Prompt v0.10 avoided invalid internal ID; full IFC path passed |
| H1 single genuine diagnostic | PASS, 1/1/1 calls | mixed ChangeSet contract passed the real path |
| Fresh R1 ordered run | 9 PASS, H3 stop | partial live evidence only |

## 4. Closure boundary

Still required before any R1/Phase closure claim:

1. H3 focused offline diagnosis and regression;
2. H3 genuine single-case pass;
3. a new uninterrupted fresh R1 12-case run;
4. independent Proof 0.3 recomputation and curation;
5. remaining frozen final gates and planning/summary closure.

Do not splice successful rows from different genuine runs into a synthetic
12/12 result.
