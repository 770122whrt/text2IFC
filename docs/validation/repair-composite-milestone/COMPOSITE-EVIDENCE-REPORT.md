# COMPOSITE EVIDENCE REPORT — Text2IFC Composite Repair Milestone

**Task:** build a NEW, independently traceable evidence group demonstrating
that the current Text2IFC Repair system can execute increasingly large,
atomic, multi-family IFC modifications producing visually and structurally
meaningful BIM artifact changes (specification
`docs/validation/parallel-goal-prompts-audit-inputs/final-prompt-a.md`).

**Current state: COMPLETE.** Every offline gate is GREEN (48/48 composite
suite), and the genuine DeepSeek execution has been PERFORMED under explicit
user authorization: 12 real Provider calls (stage1 ×9, stage2 ×3) in frozen
order C1→C5-N. C1 succeeded end-to-end through the live chain (strict
L0/L1/L2 + operation-bound proof + exact-delta preservation all PASS); C5-N
proved the all-or-nothing guard against the real Provider (terminal
`unsupported`, zero mutation, no Stage 2); C2–C5 preserved genuine Provider
failures (clarifications ×3, provider output failure ×1). The proof pack is
organized per the repository convention (`01-original/02-input/03-repaired`
+ `input/agent/changeset/validation`) — see the pack `README.md` and
`WORK-SUMMARY.md`. Live results detail: `composite-evidence-matrix.md`.

---

## 1. Base revision and baseline fingerprint

* Branch `Zcode`, HEAD `8bfcfe075521ddb142f8608296dfbfea1fd385e4`.
* Baseline fingerprint `composite-baseline-fingerprint.json`: 508 production
  files, snapshot at task start. **CLEAN at every checkpoint**; the
  user-authorized production repair is recorded in the fingerprint itself
  with before/after SHA-256 per file and the authorization reference
  (`authorized_fixes`): `operations/window.py`,
  `semantic_authoring.py`, `operations/door.py` (the two defect fixes) and
  the two failure-family regression test files added under
  `tests/ifc_repair/`.
* **`COMPOSITE_EVIDENCE_BASE_REVISION=8bfcfe075521ddb142f8608296dfbfea1fd385e4`**
* The `prompts/agent/registry.json` exception was never needed (no new
  prompt/profile asset); it remains recorded as unused.

## 2. Capability health

All six required operations are `HEALTHY_FOR_COMPOSITE_EVIDENCE`, evidenced
by registry/schema/profile/binder/applicator/comparison citations plus
freshly-run focused tests (`composite-capability-feasibility.md`).

## 3. Selected BIMs

CM-TALL (BIM Whale TallBuilding), CM-S65 (IFC-Bench sixty5 str), CM-VVO
(BIMNet vvo) — three sources, scales, and storey layouts; all bindings are
public-fact-only and were re-validated after every rebind
(`composite-model-selection.md`, which also honestly records the pre-freeze
model and binding corrections).

## 4. Frozen composite cases

Six hash-bound cases in `composite-acceptance-freeze.json` (execution order
C1 → C2 → C3 → C4 → C5 → C5-N): 2/3/5/7/8 entity operations across up to 4
families plus 2 property intents on the hero case, and a negative twin
carrying one verified-absent unsupported operation. Every artifact predicate
binds to `operation_id` + `operation_type`.

## 5. Defects found, fixed, and frozen (the substantive outcome)

The offline full-chain preflight (specification Section 10.1) exposed two
latent production defects that no historical single-family case could reach:

1. **Mixed-manifest binding defect** — a changeset mixing structural
   operations with a window operation could never bind
   (`BOUND_CHANGESET_INVALID`): the window manifest stayed at v0.1 raw
   source kinds, the negotiation downgraded the envelope to 0.2, and
   structural vocabulary is illegal there. Root cause was two
   family-specific inconsistencies (window policy-facts gate +
   `use_v03` scope set). Fixed by aligning window with its siblings.
2. **Door semantic-role authorization defect** — any door operation carrying
   a property intent failed whole-model L1 scope authorization: the door's
   semantic authoring emits `semantic_door_pset` roles that its L1
   authorization map never contained (while beam/column/window authorize
   their equivalents). Fixed by mirroring the structural pattern.

Both were repaired at mechanism level (general, not point-fixes), frozen as
failure families (`test_mixed_manifest_binding.py` 14 tests,
`test_door_property_authorization.py` 7 tests), and passed full regression
gates. Full localization evidence and the honest correction of the first
(root-cause analysis is in `DEFECT-RECORD.md`).

## 6. Genuine Provider calls

**Zero so far.** All artifacts are labelled `offline_deterministic_apply` /
`negative_guard_zero_mutation`; nothing synthetic is claimed as live. The
live runner (`run_composite.py --execute-genuine`) is ready and reuses the
frozen cases, the operation-bound proof validator, and the exact-delta
preservation checks as-is.

## 7. Per-case results (offline, zero Provider)

| Case | Result |
| --- | --- |
| C1 (TALL, beam+column) | OFFLINE_PROVEN — full public API chain, 4 proof predicates, exact-delta + comparator preservation |
| C2 (S65, column×2+door-fill) | OFFLINE_PROVEN — genuine door-fill of a real pre-existing opening verified by reopening the IFC |
| C3 (TALL, beam×2+column×2+window) | OFFLINE_PROVEN — 5-op multi-family |
| C4 (S65, 4-family, 7 ops) | OFFLINE_PROVEN — after the solid-zone window rebinding (documented) |
| C5 HERO (VVO, 8 ops + 2 properties) | OFFLINE_PROVEN — Stage 1.5 property resolution chain included |
| C5-N negative twin | NEGATIVE_GUARD_PROVEN — real-API run ends `unsupported`, zero mutation, zero Stage 2 |

## 8. Scale ladder result

**33 of 33 requested operations proven** across 4 families (beam, column,
door add + fill, window) with atomic publication, IFC2X3 reopen, strict
L0/L1/L2, operation-bound proof, and exact authorized deltas on every
positive case; the negative twin proves all-or-nothing fail-closed safety.

## 9. Hero case artifact delta (C5)

`dataset/processed/proof/repair-composite-milestone/C5/ARTIFACT-DELTA.md`:
`IfcBeam 6→8`, `IfcColumn 5→9`, `IfcDoor 26→27`, `IfcWindow 21→22`,
`IfcOpeningElement 57→59`, +6 Types/Styles, +2 authored property sets
(`Pset_DoorCommon.FireRating=EI60`, `Pset_WindowCommon.IsExternal=true`),
with every added GlobalId listed per operation; atomic publication, reopen,
proof, and preservation all PASS.

## 10. Negative twin result

Zero mutation, terminal `unsupported`, no Stage 2, no published artifact —
proven through the real `RepairAPI` by a passing test and recorded as
`NEGATIVE-GUARD.json` + zero-delta `ARTIFACT-DELTA.md`.

## 11. Preservation / atomicity

Composed authorized deltas from ALL operations; EXACT per-class deltas
(off-by-one fails, negative-tested); production comparator zero unexpected
changed ids; `atomic_operation_set` predicate; strict L0/L1/L2 recompute;
source immutability for every case.

## 12. Independent subagent audit

The first audit (pre-fix) returned PASS with concerns; both P1 findings were
remediated in-namespace and re-verified. A post-fix re-audit is recorded in
`composite-independent-audit.md` (see its final section for the post-fix
recheck).

## 13. Offline verification gates (all green)

Composite suite 48/48; failure families 21/21; door regressions 41/41;
window/changeset/semantic-authoring regressions 105 passed; phase12 dataset
e2e + frozen proofs 53 passed; phase12 live-UAT production-path 11 passed;
R1 summary suites 69 passed. All runs used `-p no:cacheprovider` with fresh
`composite-evidence-*` system-temp basetemps.

## 14. Outputs

All Section 15 outputs exist under `docs/validation/repair-composite-milestone/`
and `dataset/processed/proof/repair-composite-milestone/` (per-case evidence
directories with `source-reference.json`, `changeset.json`,
`application.json`, `composite-proof.json`, `preservation.json`,
`ARTIFACT-DELTA.md`, `artifact-delta.json`, and `repaired.ifc` — or
`NEGATIVE-GUARD.json` for the twin). Nothing was committed; the user curates
and commits.

## 15. Next action

Genuine Provider execution of the frozen ladder (C1 → C5-N) via
`run_composite.py --execute-genuine` is unblocked by every offline gate and
awaits explicit user authorization.
