# Repair Milestone R1 planned Proof Matrix

## 1. Existing proof convention

Future curation reuses the current Phase 12 validators, operation registry, L0/L1/L2 adapters and
artifact conventions. The R1 terminal diversity requires a versioned successor instead of silently
changing the released Plan 07 contracts:

- historical Plan 07 proof validation remains `ifc-repair-proof-validation/0.2` and its success
  collection remains `0.1`;
- R1 proof validation is `ifc-repair-proof-validation/0.3`;
- R1 collection is `ifc-repair-proof-collection/0.2`;
- R1 no-output/initial-stop evidence is `ifc-repair-proof-terminal/0.1`;
- frozen, case-specific admission metadata is `ifc-repair-proof-profiles/0.1`;
- current validators/curators:
  `scripts/ifc_repair/validate_success_cases.py`,
  `scripts/ifc_repair/curate_phase12_live_proof.py`, and
  `scripts/ifc_repair/curate_phase12_structural_proof.py`;
- R1 curation entry point:
  `scripts/ifc_repair/curate_repair_milestone_r1_proof.py`.

This file plans evidence only. No Proof was curated while preparing the freeze package.

## 2. Per-case evidence record

For each case, the eventual Proof Matrix row must link immutable case-local artifacts for:

1. frozen request and model SHA-256;
2. Stage 1 parsed intent and prompt-profile identity;
3. target/Storey resolution and offered-set evidence;
4. property authority query, BGE/Qdrant offered Top-K, and Stage 1.5 raw/parsed decision;
5. clarification/resume lineage when applicable;
6. deterministic admissibility and ExactPropertyIntent, or explicit N/A reason;
7. Stage 2 raw response, parsed ChangeSet and immutable template/profile identity;
8. Binder equality and operation-registry authorization;
9. transactional IFC apply/publication status;
10. IfcOpenShell reopen;
11. L0, L1, L2;
12. source/repaired preservation and no-unintended-mutation results;
13. Provider attempts, per-stage call/attempt counts, model/thinking/request metadata, latency and
    token usage when returned;
14. private-Gold/mutation-truth leakage audit;
15. independent validation report and final semantic, deterministic, artifact and evidence outcomes.

`M1` and `H3` require both initial-stop and resume evidence. `H4` requires the full unsupported
decision, zero Provider/apply leakage after the stop boundary, unchanged source hash and absence of
a published repaired IFC; it must not receive fabricated L0/L1/L2 PASS values.

## 3. Planned matrix

| Case | Semantic/model outcome | Deterministic execution outcome | Artifact outcome | Evidence/contract outcome | Truth-based IFCCompare |
|---|---|---|---|---|---|
| E1 | IsExternal selected | accepted + executed | repaired IFC/reopen | full R1 0.3 validation | ineligible |
| E2 | Door FireRating selected | accepted + executed | repaired IFC/reopen | full R1 0.3 validation | ineligible |
| E3 | Beam Reference selected | accepted + executed | repaired IFC/reopen | full R1 0.3 validation | ineligible |
| E4 | Wall AcousticRating selected | accepted + executed | repaired IFC/reopen | full R1 0.3 validation | ineligible |
| M1 | FireRating selected; value correction | initial rejection; resume executed | no initial artifact; resumed repaired IFC | both turns + lineage | ineligible |
| M2 | Beam/property intent | accepted + executed | repaired IFC/reopen | structural + property evidence | ineligible |
| M3 | Column/property intent | accepted + executed | repaired IFC/reopen | geometry/orientation/property evidence | ineligible |
| H1 | two requested operations | atomic execution | one repaired IFC/reopen | cross-family atomic evidence | ineligible |
| H2 | two exact properties | atomic execution | one repaired IFC/reopen | multi-target atomic evidence | ineligible |
| H3 | target clarification; IsExternal | initial stop; resume executed | no initial artifact; resumed repaired IFC | offered-set + stable identity lineage | ineligible |
| H4 | unsupported-program recognized | transaction rejected | no repaired IFC | zero-mutation terminal evidence | ineligible |
| A1 | exact existing Type intent | accepted + executed | repaired IFC/reopen | reuse/no-duplicate-Type evidence | ineligible |

Each future result must preserve four separate verdicts. A semantic success followed by execution or
evidence failure is reported explicitly as such; it may not be collapsed into or hidden behind a
generic PASS/FAIL label.

## 4. Curation admission

A case is eligible for current Proof only after:

- genuine Provider evidence is immutable and stage-aware;
- required deterministic execution and artifact checks completed with zero skip/substitution;
- current R1 validation 0.3 report passes its applicable property-authority and terminal contract;
- source immutability and leakage checks pass;
- the independent validator recomputes, rather than trusts, claimed results.

Property-bearing success cases require the current strict Stage 1.5 recomputation/acceptance fields
defined by the existing curator boundary. `not_applicable` is allowed only for genuine non-property
cases such as A1/H4 and cannot admit a property-bearing success case.

## 5. Exact future genuine execution list

After explicit freeze approval, and not before:

1. rerun the original Plan 07 four genuine cases on the same final code version;
2. run R1 cases in exact order
   `E1,E2,E3,E4,M1,M2,M3,H1,H2,H3,H4,A1`;
3. stop on the first new deterministic/infrastructure defect, preserve the run, and return to the
   offline protocol before any separate rerun;
4. independently validate and curate only completed eligible evidence;
5. run final IFCCompare only on a separately authorized truth-bearing set; none of the 12 R1
   diversity cases qualifies.

No genuine execution command, credential, or Provider payload is frozen here; those belong to the
post-approval execution manifest and must preserve the current public-input/private-evaluation
boundary.
