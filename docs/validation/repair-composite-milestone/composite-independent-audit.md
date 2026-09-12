# Composite Independent Audit — Text2IFC Composite Repair Milestone

**Auditor:** independent read-only subagent (general-purpose), dispatched per
specification Section 14. The auditor did not modify anything, never read
`refactor_workspace/`, and re-ran read-only verification commands (including
re-opening the repaired IFC files with ifcopenshell, `git status`, the
fingerprint `verify`, and the focused test suite) itself.

**Audit date:** 2026-08-31 (after evidence generation, before this report).

## Per-item verdicts (spec Section 14 items 1–14)

| # | Audit item | Verdict | Evidence summary |
| --- | --- | --- | --- |
| 1 | Case composition matches frozen semantics | **PASS** | Freeze `composite-acceptance-freeze.json`: C1 2 ops / C2 3 / C3 5 / C4 7 / C5 8 / C5-N 8 + 1 unsupported; family sets match; all 6 `request_sha256` recompute correctly |
| 2 | Operation counts not inflated by bookkeeping | **PASS** | C5's 8 operations are 4×add_column + 2×add_beam + 1×add_door + 1×add_window; the 2 property intents are counted separately (`property_intent_count: 2`); `expected_entity_delta` demands real entity deltas |
| 3 | Same-family repeated ops independently proven via operation_id | **PASS** | `composite_proof.py:236-246` binds by operation_id (exactly one match) + operation_type; `test_composite_proof.py:155-165` proves C4's 4 columns with 4 distinct operation_ids/occurrence GUIDs/type GUIDs; duplicate-id tamper test fails closed |
| 4 | Door/Window entity modifications genuine | **PASS** | Auditor re-opened the IFCs: source opening `0dkujmS9z4NwYsuEau8iwB` empty with host wall `2$GiA0FALCKuqNnxjNZITr`; repaired IFC has exactly one filling `IfcDoor 2mdSQmCfDG4918u8b5wOds` (1170×2490, IfcDoorStyle SINGLE_SWING_LEFT), same host, `IfcDoor 0→1`, `IfcRelFillsElement 0→1` |
| 5 | Geometry frozen before Provider execution | **PASS** | Freeze carries exact axis/section/wall/opening constraints with tolerances; `DEFECT-RECORD.md` records that genuine Provider execution never ran; no live-attempt artifacts exist anywhere |
| 6 | Provider evidence genuine (no synthetic-as-live) | **PASS** | Matrix states live calls = 0; every artifact is `offline_deterministic_apply`; blocked cases carry honest `DEFECT-RECORD.json` with `offline_repaired_ifc_produced: false`; no counter-example found |
| 7 | No private truth entered production | **PASS** | All bindings use public facts (wall L/H/T/direction/storey-elevation, opening 5-tuple, storey GlobalIds); grep over the composite scripts shows zero reads of Gold/mutation-recipe/deleted-identity/comparator paths; the three model hashes re-verified |
| 8 | Atomicity independently proven | **PASS** | `atomic_operation_set` requires changeset ids == applied ids == frozen ids AND valid+published; exact-delta preservation + comparator check with off-by-one and shrink-allowed-set negative tests |
| 9 | Artifact Delta matches actual IFC | **PASS** | Auditor re-opened C1/C2 repaired IFCs and re-counted: C1 IfcBeam 0→1, IfcColumn 0→1, +Types, IfcRelDefinesByType 15→17; C2 IfcColumn 387→389, IfcDoor 0→1, openings/walls unchanged — all match the delta files; source SHA-256 matches the freeze |
| 10 | No unrelated mutation | **PASS** | C1/C2 `preservation.json`: `unexpected_changed_ids: []`, `complete_preservation_success: true` (allowed sets of 7 and 13 ids) |
| 11 | Negative twin zero mutation | **PASS** | `test_offline_full_chain.py::test_offline_full_chain_negative_twin_fails_closed` drives the real `RepairAPI`, asserts `unsupported`, identical source SHA-256 before/after, zero stage-2 attempts, no successful artifact; test executed and passed |
| 12 | Original R1 evidence not altered | **PASS** | `git status` shows no tracked-file modifications under `docs/validation/repair-milestone-r1/` or `dataset/processed/proof/ifc-repair-success-cases/` (411 tracked files clean); the four modified `src/` files are exactly the pre-existing dirty set; the baseline fingerprint snapshot (taken at task start) still verifies CLEAN, proving none of them changed during the task |
| 13 | All writes inside the Section 0.1 allowlist | **PASS** | Bounded mtime scan (newer than task start, excluding allowlist dirs and `refactor_workspace/`) found zero files outside the allowlist modified during the task; untracked entries outside the allowlist all predate the task window |
| 14 | Final fingerprint check confirms zero production drift | **PASS** | `baseline_fingerprint.py verify` → exit 0, "verify: CLEAN (508 production files match baseline)" |

## DEFECT-RECORD code-claim verification

| Claim | Verdict | Evidence |
| --- | --- | --- |
| (a) window.py gates `canonical_source_kind` on `authorized_occurrence_assignment` | **PASS** | `window.py:461-464` computes the gate; `window.py:510-514` sets the kind conditionally |
| (b) live-path window facts end with all-None canonical kinds | **PASS** (effect) with a wording correction | `api.py:542-553` passes `to_dict()` which DOES include `authorized_semantics`; the accurate mechanism is that resolved window operations carry no `authorized_occurrence_assignment` entries, so the gate stays closed. The blocking behavior is proven end-to-end by the red tests through the real `RepairAPI`. The DEFECT-RECORD wording has been corrected accordingly (fix applied inside this task's namespace) |
| (c) 0.4 schema rejects the raw source kinds | **PASS** | `schemas/agent/ifc-repair-changeset-0.4.schema.json:33` enum lacks `deterministic_policy`/`surviving_target`; `changesets.py:218-220` raises `BOUND_CHANGESET_INVALID` |
| (d) sibling hooks set the kind unconditionally | **PASS** | `beam.py:606`, `column.py:631`, `door.py:827` |

## Overall verdict

**PASS with concerns.** The evidence chain is internally consistent and
honest: freeze ↔ bound-testcases ↔ evidence matrix ↔ per-case artifacts ↔
tests all agree; the 5 of 33 offline-proven operations (C1, C2) were
independently re-verified by re-opening the repaired IFC files; no
live-Provider claim exists anywhere; no private truth enters any production
path; the R1 evidence and the whole production tree are byte-identical to the
pre-task fingerprint; all writes stayed inside the allowlist; and the full
focused suite (48 tests) passes under the auditor's own run.

## Material findings and remediation (per specification Section 14)

**P0:** none.

**P1 (both remediated inside this task's own namespaces after the audit):**

1. `composite-model-selection.md` was stale: it still described the WRH-based
   pre-freeze draft (C2/C4 on West Riverside Hospital) while the regenerated
   freeze had already rebound C2/C4 to S65 (`sixty5/str.ifc`) after WRH was
   measured to exceed the frozen 180 s production evaluation deadline. The
   frozen evidence itself was self-consistent; the documentation was not.
   **Remediated:** the model-selection document now records CM-S65 facts and
   bindings for C2/C4, an honest-record note explaining why WRH was dropped
   (evaluation-deadline constraint, measured ~209 s vs the frozen 180 s), and
   the rejected-model list was corrected.
2. `DEFECT-RECORD.md` root-cause item (b) was imprecise (it implied
   `api.py` drops `authorized_semantics`; in fact the field is passed but
   window operations simply never carry an
   `authorized_occurrence_assignment`). **Remediated:** the record now states
   the mechanism accurately; the defect's blocking behavior was never in
   doubt (proven by the frozen red tests through the real `RepairAPI`).

**Minor nits (non-blocking):** `freeze_sha256` hashes the hash-less payload
rather than the file bytes (reproducible via `freeze_cases.py`, documented
here); the dead `target_kind` branch in `generate_case_evidence.py` was
replaced with a correct per-operation mapping and the per-case evidence was
regenerated (C1/C2 binding-integrity labels now read `opening`/`wall`
correctly).

## Post-fix recheck

After the two P1 remediations, the auditor's decisive checks were re-run by
the task agent and remain green: the focused test suite (48 tests) passes,
the regenerated per-case artifacts still show C1/C2 OFFLINE_PROVEN with
identical entity deltas, and `baseline_fingerprint.py verify` is CLEAN — zero
production drift. No evidence content was silently edited: the only changes
were the two documentation corrections and the regenerated (equivalent)
per-case artifacts described above.
