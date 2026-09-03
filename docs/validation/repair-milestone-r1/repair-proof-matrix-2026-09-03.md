# Repair Milestone R1 Final Proof Matrix

- Closure date: 2026-09-03
- Branch: `codex/workflow-dataset-links`
- Accepted genuine run: `r1-20260902T152701658266Z`
- Final-code Plan 07 compatibility run: `uat-20260902T180900748385Z`
- Provider: `deepseek-v4-flash`, thinking enabled
- Ordered result: 12/12 frozen case contracts passed
- Calls: 40 (`stage1=17`, `property_resolution=12`, `stage2=11`)
- Curated Proof: validation 0.3 / terminal 0.1 / collection 0.2 / profile 0.1
- Closure status: PASS

This matrix keeps semantic/model outcome, deterministic execution outcome,
artifact outcome and evidence/contract outcome separate. The historical
Plan 07 result remains immutable with its original `false/pending` eligibility
fields; this additive R1 Proof and closeout record supply the final closure
evidence rather than rewriting the historical result.

## Accepted evidence roots

- [ordered execution result](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260902T152701658266Z/r1-execution-result.json)
- [curated Proof root](../../../dataset/processed/proof/repair-milestone-r1/r1-20260902T152701658266Z-curated/)
- [Proof validation 0.3](../../../dataset/processed/proof/repair-milestone-r1/r1-20260902T152701658266Z-curated/PROOF-VALIDATION.json)
- [curation binding](../../../dataset/processed/proof/repair-milestone-r1/r1-20260902T152701658266Z-curated/CURATION.json)
- [final IFCCompare/collection summary](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-final-ifccompare-20260903/validation-summary.json)
- [final-code Plan 07 live result](../../../dataset/processed/ifc-repair-runs/phase12-live/uat-20260902T180900748385Z/live-uat-result.json)
- [final-code Plan 07 zero-network admission](../../../dataset/processed/ifc-repair-runs/phase12-live/admission-20260903-r1-final-code/changed-scope-admission.json)

The curated `PROOF-VALIDATION.json` has SHA-256
`7ed2a0131e8461e91604b796febdcd387d9fb858580ec9d107634feb1d873c4c`,
matching `CURATION.json`. It reports 12 cases, 13 operations, 785 checked
files, 23 IFC reopens, 12 independently recomputed cases, one valid no-output
case, zero errors and zero limitations.

## Final-code Plan 07 compatibility matrix

The original Plan 07 four-case run and its accepted validation 0.2 evidence
remain the independent Proof authority for this matrix. After the final R1
repairs, the same four frozen cases were run once more on the final code as
`uat-20260902T180900748385Z`. It passed 4/4 with 11 genuine calls
(`stage1=4`, `property_resolution=4`, `stage2=3`) and no fallback.

| Case | Calls S1/S1.5/S2 | Final-code result | Artifact result |
|---|---:|---|---|
| `complete` | 1/2/1 | PASS; atomic Beam + Column path | [repaired IFC](../../../dataset/processed/ifc-repair-runs/phase12-live/uat-20260902T180900748385Z/cases/complete/runtime/runs/repair-2c2d4be0aa8240488448b826efc0dab4/.terminal-bundles/59df2d59c1e845d28d91baf52a1c358c/successful/repaired.ifc); reopen and L0/L1/L2 PASS |
| `clarification-resume` | 1/1/1 | PASS; stable property identity resumed | [repaired IFC](../../../dataset/processed/ifc-repair-runs/phase12-live/uat-20260902T180900748385Z/cases/clarification-resume/runtime/runs/repair-392a149cc545470085ee1bce5176a108/.terminal-bundles/13d95f2497bc4699ad188281c940c1fe/successful/repaired.ifc); reopen and L0/L1/L2 PASS |
| `window-semantic-canary` | 1/1/1 | PASS; offered `IsExternal` authority selected | [repaired IFC](../../../dataset/processed/ifc-repair-runs/phase12-live/uat-20260902T180900748385Z/cases/window-semantic-canary/runtime/runs/repair-1ee9e411b9fc44308dfb2f9c17c002f8/.terminal-bundles/31eab6f6a4374d3faf0687a70b8a3bac/successful/repaired.ifc); reopen and L0/L1/L2 PASS |
| `program-guard` | 1/0/0 | PASS; `STRUCTURAL_ANALYSIS_UNSUPPORTED` | no mutation, no publish, no repaired IFC; L0/L1/L2 N/A by contract |

One evidence-packaging limitation is retained explicitly: the current Plan 07
curator only copies a run-local full `preflight/` tree, while this final-code run
used the runner-accepted changed-scope admission reference. A post-run curation
attempt therefore stopped at `LIVE_PREFLIGHT_EVIDENCE_MISSING`. This is not
reported as a second independently curated Proof. It did not invalidate the
four live case contracts, their retained repaired IFC/reopen checks, the
original Plan 07 Proof, or the separately curated R1 Proof 0.3. The curator
layout compatibility can be addressed later without another Provider run.

## H3 root cause and general repair

The original H3 failure was deterministic target filtering, not a missing
Provider intent. Stage 1 correctly emitted an `IfcWindow` query on Level 2 with
opening width/height constraints. Two general defects then emptied the offered
candidate set:

1. Window/Door filling records store size as `overall_width` and
   `overall_height`, while the geometry predicate read only the hosted-opening
   keys `width` and `height`.
2. Exact zero-tolerance comparisons saw unit-conversion noise such as
   `819.0000000000001` because filling dimensions had not passed through the
   existing millimetre cleaner.

The production repair makes opening-width/height predicates read the filling
overall-dimension keys when hosted-opening keys are absent, and normalizes
filling millimetres with the common `_clean_mm` rule. Wrong dimensions remain
excluded, hosted openings retain their old behavior, and the currently-offered
candidate identity check remains unchanged. Production code contains no H3
GlobalId, frozen dimension, case id or phrase special case.

## Final 12-case matrix

`S1/S1.5/S2` counts are genuine HTTPS transport calls. All success artifacts
were independently reopened by Proof 0.3; L0/L1/L2, source immutability,
property authority, atomicity and preservation were recomputed rather than
accepted from terminal self-report.

| Case | Calls S1/S1.5/S2 | Semantic/model outcome | Deterministic execution outcome | Artifact outcome | Evidence/contract outcome | IFCCompare |
|---|---:|---|---|---|---|---|
| `E1` | 1/1/1 | `IsExternal=true` selected from offered authority | occurrence property applied; source unchanged | [repaired IFC](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260902T152701658266Z/cases/E1/runtime/runs/repair-b86897cf5de942b8a12be6c012a3ed7a/.terminal-bundles/1955cfe7022d4f7a930aae57660293fe/successful/repaired.ifc); L0/L1/L2 PASS | Proof PASS; property and preservation predicates PASS | N/A: no legal R1 private triplet |
| `E2` | 2/1/1 | corrected Stage 1 output then `FireRating=EI60` selected | occurrence property applied; source unchanged | [repaired IFC](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260902T152701658266Z/cases/E2/runtime/runs/repair-7ffe3c5e21e24bfc80e01690320fbfa7/.terminal-bundles/fad7684d445e45d79dddc15e0a9d6cbe/successful/repaired.ifc); L0/L1/L2 PASS | Proof PASS; correction attempt retained | N/A |
| `E3` | 1/1/1 | Beam occurrence `Reference=B-204` selected | exact occurrence property applied | [repaired IFC](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260902T152701658266Z/cases/E3/runtime/runs/repair-f930e1b7bdf64579a246beede1bc4c87/.terminal-bundles/94556f6ba9554957902fffb840384b4d/successful/repaired.ifc); L0/L1/L2 PASS | Proof PASS; occurrence scope verified | N/A |
| `E4` | 1/1/1 | Wall `AcousticRating=Rw 50` selected | occurrence property applied | [repaired IFC](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260902T152701658266Z/cases/E4/runtime/runs/repair-83fc4d551d9c488196f846a7aebaf78e/.terminal-bundles/72f3314937ac42678eefccc3f3375d2b/successful/repaired.ifc); L0/L1/L2 PASS | Proof PASS; preservation PASS | N/A |
| `M1` | 3/2/1 | invalid Boolean stopped; user detail resumed as `EI60` with stable property identity | first path did not mutate; resumed path applied | [repaired IFC](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260902T152701658266Z/cases/M1/runtime/runs/repair-7e0a896445a24d42b29a72b28a191b10/.terminal-bundles/003936332c2f48b2a4de0f22891c5ed9/successful/repaired.ifc); L0/L1/L2 PASS | Proof PASS; clarification lineage retained | N/A |
| `M2` | 1/1/1 | generated Beam Type plus occurrence `Pset_BeamCommon.Reference` | Beam and requested property applied | [repaired IFC](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260902T152701658266Z/cases/M2/runtime/runs/repair-7988ad21f9a54fa9b7400b7f8ce10c51/.terminal-bundles/776136b479644cb185204585bfc9f238/successful/repaired.ifc); L0/L1/L2 PASS | Proof PASS; root `Tag` was not substituted | N/A |
| `M3` | 2/1/1 | corrected Stage 1 output; Column `LoadBearing` authority selected | Column/Type/property applied | [repaired IFC](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260902T152701658266Z/cases/M3/runtime/runs/repair-f12def4310484e858169f78b1b5429cc/.terminal-bundles/5d1181db5f10453eb3b327d9cd4c4a2f/successful/repaired.ifc); L0/L1/L2 PASS | Proof PASS; correction retained | N/A |
| `H1` | 1/1/1 | mixed Beam add plus Window property intent confirmed | two-operation ChangeSet applied atomically | [repaired IFC](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260902T152701658266Z/cases/H1/runtime/runs/repair-ced900798d8c479da01c5d903cc7d061/.terminal-bundles/3ccdee3857664c7597a9a686aa9e8552/successful/repaired.ifc); L0/L1/L2 PASS | Proof PASS; both predicates and atomic set PASS | N/A |
| `H2` | 1/2/1 | Door and Wall properties independently selected | two target operations applied atomically | [repaired IFC](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260902T152701658266Z/cases/H2/runtime/runs/repair-de5a7bd04fb44cd59e8188fd2675b050/.terminal-bundles/7fb9a33c90814184b9150308d6f12b49/successful/repaired.ifc); L0/L1/L2 PASS | Proof PASS; two authority and preservation checks PASS | N/A |
| `H3` | 1/1/1 | offered Window candidates restored; frozen stable identity resumed; `IsExternal=true` selected | clarification/resume applied to currently offered identity | [repaired IFC](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260902T152701658266Z/cases/H3/runtime/runs/repair-c29c5e7113c9410fb80277c383232a11/.terminal-bundles/36116cb0488b4a8d9e61682e1fec3d1a/successful/repaired.ifc); L0/L1/L2 PASS | Proof PASS; terminal class `CLARIFICATION_THEN_SUCCESS` | N/A |
| `H4` | 1/0/0 | Stage 1 recognized unsupported structural-analysis work inside an atomic request | whole transaction stopped before Stage 1.5, Stage 2 or apply | no repaired IFC by contract; source SHA before=after; zero candidate output | Proof PASS; `UNSUPPORTED_ATOMIC_GUARD`, one valid no-output case | N/A by design |
| `A1` | 2/0/1 | corrected Stage 1 output; exact existing Type reuse requested | Beam added with existing Type; no property stage applicable | [repaired IFC](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260902T152701658266Z/cases/A1/runtime/runs/repair-6ddc28933f2b4c27a9920a7cd99bf048/.terminal-bundles/1d0f3be436984b6aa1103924fd25399a/successful/repaired.ifc); L0/L1/L2 PASS | Proof PASS; exact-Type relation verified | N/A |

## Why H4 has no repair artifact

H4 is not a missing repair. Its frozen expected behavior is an atomic guard: the
request combines a supported Beam edit with unsupported structural-analysis
work. Applying only the supported half would violate atomicity. The correct
result is therefore `STRUCTURAL_ANALYSIS_UNSUPPORTED`, with one Stage 1 call,
zero Property Resolution calls, zero Stage 2 calls, `mutation_attempted=false`,
`candidate_output_paths=[]`, `successful_artifact_publishable=false`, and equal
source hashes before and after. L0/L1/L2 are N/A because there is deliberately
no repaired output to score; Proof 0.3 instead reopens the source and verifies
the no-output contract.

## IFCCompare and preservation boundary

R1 diversity cases deliberately contain no legitimate private
pristine/damaged/repaired Ground Truth, so their IFCCompare eligibility is
0/12. Creating truth for them after seeing repairs would invalidate the frozen
evaluation. Their artifact evidence is source/repaired preservation plus strict
L0/L1/L2 and predicate recomputation.

The existing accepted collection, which does contain pre-existing legitimate
private triplets, was revalidated with proof-collection 0.2 and IFCCompare. The
validator passed 24 cases, 60 operations, 588 files and 72 IFC reopens; 19 cases
were independently recomputed and all 12 truth-bearing triplet audits were
publishable. Five older Window cases retain explicit
`legacy_unverifiable` limitations because their historical manifests lack
current role mappings; those cases are not used to manufacture or strengthen
R1 acceptance.

## Genuine run ledger

Every preserved R1 genuine attempt is retained. Counts below come from the
top-level result where present; for interrupted workspaces without a top-level
result, counts are reconstructed from retained Stage 1 live attempts and
Property/Stage 2 provider metadata and are marked `interrupted`.

| Run/evidence id | Calls S1/S1.5/S2 | Outcome |
|---|---:|---|
| `phase12-live-deepseek-complete` | 4/4/3 (11) | historical Plan 07 four-case contracts PASS; original top-level eligibility remains false/pending |
| `uat-20260902T180900748385Z` | 4/4/3 (11) | PASS: final-code Plan 07 compatibility run, 4/4; changed-scope curator packaging limitation recorded separately |
| `r1-20260831T032507331224Z` | 0/0/0 | BLOCKED preflight/Plan 07 evidence invalid |
| `r1-20260831T034907322238Z` | 2/2/2 (6) | interrupted; no top-level result |
| `r1-20260831T040334441512Z` | 2/2/2 (6) | interrupted; no top-level result |
| `r1-20260831T151326967970Z` | 3/3/3 (9) | FAIL, preserved case-contract stop |
| `r1-20260831T155141193325Z` | 9/8/9 (26) | FAIL, preserved case-contract stop |
| `r1-20260901T034310928815Z` | 9/8/9 (26) | FAIL, preserved case-contract stop |
| `r1-20260901T052919004905Z` | 2/1/1 (4) | FAIL, preserved case-contract stop |
| `r1-20260901T055419268779Z` | 12/11/10 (33) | FAIL at H3, deterministic stop after 9/12 |
| `r1-20260901T134510430440Z` | 10/8/8 (26) | FAIL, preserved case-contract stop |
| `r1-20260901T145817303105Z` | 12/11/10 (33) | interrupted; no top-level result |
| `r1-20260901T154532207844Z` | 14/11/12 (37) | FAIL, preserved case-contract stop |
| `r1-20260902T053023885207Z` | 14/11/11 (36) | runtime PASS but rejected by Proof: M2 wrote root `Tag`, not frozen Pset authority |
| `r1-20260902T141632454789Z` | 2/0/0 (2) | FAIL, preserved model/case stop |
| `r1-20260902T142055280724Z` | 1/0/0 (1) | FAIL, preserved native-runtime defect |
| `r1-20260902T142600567859Z` | 1/0/0 (1) | FAIL, preserved native-runtime defect |
| `r1-20260902T145705953728Z` | 0/0/0 | BLOCKED before Provider: runtime warmup |
| `r1-20260902T145900991242Z` | 0/0/0 | BLOCKED before Provider: runtime warmup |
| `r1-20260902T150201099674Z` | 0/0/0 | BLOCKED before Provider: runtime warmup |
| `r1-20260902T150620324506Z` | 0/0/0 | BLOCKED before Provider: authorization intentionally absent |
| `r1-20260902T150713117380Z` | 1/1/0 (2) | FAIL, preserved scope-mismatch diagnostic |
| `r1-20260902T152701658266Z` | 17/12/11 (40) | ACCEPTED: uninterrupted 12/12 and curated Proof PASS |
| `r1-e2-genuine-diagnostic-20260901T054811235740Z` | 1/1/1 (3) | PASS diagnostic |
| `r1-h1-genuine-diagnostic-20260901T052645933962Z` | 1/1/1 (3) | PASS diagnostic |
| `r1-h3-genuine-diagnostic-20260901T122853444723Z` | 1/0/0 (1) | FAIL, zero-tolerance dimension-noise defect retained |
| `r1-h3-genuine-diagnostic-20260901T133321521853Z` | 1/1/1 (3) | PASS after both general H3 fixes |
| `r1-a1-genuine-diagnostic-20260902T044307233890Z` | 1/0/1 (2) | interrupted after retained calls; no top-level result |
| `r1-a1-genuine-diagnostic-20260902T044750131045Z` | 1/0/1 (2) | PASS diagnostic |
| `r1-m2-genuine-diagnostic-20260902T141119863111Z` | 1/1/1 (3) | PASS after general property-vs-root-field prompt correction |

Zero-call blocked runs are retained because they prove fail-closed admission;
they are not counted as Provider evidence. No successful rows from different
runs are spliced into the accepted 12/12 result.

## Focused and necessary regression evidence

- H3 mechanism admission retained 1,250 IFC-repair passes and 111 knowledge
  passes, with zero failure/skip.
- Scope-normalization focused set: 57 passed.
- Final changed-scope admission group: 208 passed with no
  failure/skip/timeout/network.
- Final closure-focused rerun across H3 geometry, scope, Prompt v0.11, R1
  runner/assembler/re-audit and vector runtime: 104 passed in 67.46 seconds.
- Final-code Plan 07 admission binding rerun: 104 passed in 70.03 seconds;
  zero Provider calls during admission, followed by the single 4/4 genuine run.
- Modified Python packages/scripts passed compileall; Git diff integrity check
  passed.

The final step did not rerun an unrelated repository-wide 1,100+ suite. The
recorded full H3 mechanism suites and the 208/104 changed-scope gates are the
applicable regression evidence; no timeout or skipped suite is presented as a
pass.

## Final decision

All frozen R1 gates have passed without changing requests, Gold, taxonomy,
thresholds, offered-set/admissibility checks or preservation/Proof thresholds.
The original Plan 07 Proof plus its final-code 4/4 compatibility run, and the
independently curated R1 Proof 0.3, support Phase 12 and Phase 12.1 closure and
completion of RAG-05..07 and OPS-03/04. The changed-scope curator packaging
limitation is non-semantic and remains documented rather than hidden. Phase 13
remains unstarted.
