# Text2IFC — Composite Repair Milestone Evidence Pack

## Goal Mode

Work toward one explicit goal:

> Build a NEW, independently traceable evidence group demonstrating that the current Text2IFC Repair system can execute increasingly large, atomic, multi-family IFC modifications that produce visually and structurally meaningful BIM artifact changes.

This task is NOT a property benchmark.

The existing Phase 12.1 / Repair Milestone R1 evidence remains authoritative and MUST NOT be overwritten, renamed, rewritten, or repurposed.

The new evidence group is additive.

---

# 0. Parallel-work isolation — mandatory

Another Codex conversation is simultaneously performing a project reorganization in the SAME repository directory.

Therefore this task MUST NOT perform broad repository restructuring.

## You may write only to

Create a dedicated namespace such as:

`docs/validation/repair-composite-milestone/`

and:

`dataset/processed/proof/repair-composite-milestone/`

plus narrowly required composite-evidence-only tests/scripts if they do not modify current production behavior.

Recommended dedicated implementation namespace:

`scripts/ifc_repair/composite_evidence/`

and dedicated tests:

`tests/ifc_repair/composite_evidence/`

If existing repository conventions strongly suggest a better equivalent namespace, use it and document the choice.

## You MUST NOT

* move existing production files;
* rename existing modules;
* reorganize directories;
* change existing R1 frozen cases;
* change Phase 12.1 evidence;
* alter property semantics;
* modify Stage 1 / Stage 1.5 / Stage 2 behavior to make a showcase case pass;
* weaken gates;
* add fallback execution;
* use private Gold during production;
* use deleted GUIDs/mutation truth during production;
* tune prompts after observing failures;
* replace a failed case with an easier case.

If a required current capability is not actually healthy, report the blocker.

Do not repair production capability as part of this evidence task unless the user explicitly authorizes a separate repair task.

---

# 1. Freeze the execution revision

Before designing or running evidence:

Record:

* branch;
* HEAD SHA;
* production-affecting working-tree state;
* prompt/schema/profile state.

If production-affecting files are dirty because of the parallel refactor conversation, determine whether those edits are confined to that conversation's isolated refactor mirror.

The original production tree used for execution must remain unchanged.

Record:

`COMPOSITE_EVIDENCE_BASE_REVISION=<SHA>`

Every genuine evidence artifact must bind back to this revision.

If the original production execution path changes while this task is running:

STOP genuine execution.

Do not continue against a moving implementation.

---

# 2. Current-operation health check

Perform a focused, zero-provider inspection of current registered operations.

At minimum inspect:

* `add_beam`
* `add_column`
* `add_window_with_opening_to_wall`
* `add_door_with_opening_to_wall`
* `fill_existing_opening_with_door`
* `set_occurrence_properties`

Classify each:

* `HEALTHY_FOR_COMPOSITE_EVIDENCE`
* `REGISTERED_BUT_NOT_EVIDENCE_READY`
* `NOT_CURRENTLY_SUPPORTED`

The health check must inspect actual:

* registry entry;
* intent schema;
* prompt profile;
* Stage 2 contract;
* Binder;
* applicator;
* comparison/evaluation adapter;
* focused tests.

Do not infer health merely because historical tests once passed.

Door and Window are inherited capabilities.

They do not need to be claimed as newly introduced by the current Phase.

They are being used here as integrated milestone capabilities.

If Door or Window entity-level authoring is not currently healthy, do NOT silently replace it with a property-only case.

Report the exact capability blocker.

---

# 3. Evidence objective

This evidence group must emphasize:

* actual IFC entity creation;
* geometry change;
* multiple component families;
* increasing operation count;
* atomic multi-operation transactions;
* Type creation/reuse where applicable;
* visible Before → After BIM change;
* fail-closed behavior for a large unsupported atomic request.

Property edits are secondary.

Do not build another property-heavy matrix.

---

# 4. Composite Scale Ladder

Build approximately FIVE positive composite cases plus ONE negative twin.

Use current healthy capabilities only.

All cases must be new evidence cases and must not overwrite the previous R1 12-case freeze.

Select real IFC2X3 models from the existing local/public corpus.

Prefer models different in source, scale, discipline, Storey layout, and unit system where feasible.

Use approximately 2–4 models total.

## C1 — Small Composite

Required semantic composition:

* Beam ×1
* Column ×1
* same atomic transaction

Target operation count:

`2`

Required result:

* new Beam;
* new Column;
* correct geometry;
* correct Storey;
* correct Type authority;
* one atomic publication.

This is the minimum composite baseline.

---

## C2 — Medium Composite

Preferred semantic composition:

* Column ×2
* Door ×1

Target operation count:

`3`

Door must preferably be an entity-level modification:

* fill an existing opening with a Door; or
* add Door + Opening to a Wall,

depending on the currently healthy registered operation.

Do NOT reduce this case to a simple Door property edit merely to make it pass.

Required result:

* two new Columns;
* one Door-level artifact repair;
* all operations committed atomically.

---

## C3 — Multi-family Composite

Required target composition if current capabilities permit:

* Beam ×2
* Column ×2
* Window ×1

Target operation count:

`5`

Window should preferably be entity-level:

* Window + Opening on an existing valid Wall.

Required result:

* visibly changed BIM;
* five independently bound requested operations;
* correct containment/host/opening relationships;
* no partial publication.

---

## C4 — Large Composite

Required target composition if current capabilities permit:

* Column ×4
* Beam ×1
* Door ×1
* Window ×1

Target operation count:

`7`

This case should create a visually obvious local building modification.

Choose geometry that is valid, spatially separated enough to avoid accidental overlap, and publicly bindable from the selected IFC.

Do not optimize geometry after observing Provider output.

Geometry must be frozen first.

---

## C5 — HERO CASE

This is the primary qualitative showcase.

Target composition:

* Beam ×2–3
* Column ×4–5
* Door ×1
* Window ×1

Target entity-level operations:

approximately `8–10`

The Hero request must be ONE coherent natural-language repair request.

It should describe one local renovation / structural modification task rather than a mechanically concatenated list of unrelated test instructions.

Example conceptual structure:

> Modify a defined region of one Storey by adding several Columns and Beams, adding/filling one Door, and adding one Window. All modifications are mandatory and must be published as one atomic transaction.

The final exact request must be frozen before Provider execution.

### Property usage in C5

At most 1–2 property intents may be included if they integrate naturally, for example:

* Door FireRating;
* Window IsExternal.

However property semantics must remain secondary.

Do not increase property count merely to inflate complexity.

The primary evidence is IFC artifact modification.

---

## C5-N — Negative Twin

Create one negative twin of the Hero Case.

Keep its overall large composite structure substantially the same, but add exactly one required unsupported operation such as:

`structural_analysis_node`

Expected behavior:

* supported Beam/Column/Door/Window portions may be recognized;
* unsupported capability must be recognized;
* because the request is atomic, Stage 2/apply/publication must not produce a partial repaired IFC;
* zero model mutation.

This is an all-or-nothing safety demonstration.

Do NOT weaken the positive C5 to construct this case.

---

# 5. Do not force unsupported compositions

The semantic scale above is the target.

Before binding cases, create:

`composite-capability-feasibility.md`

For every requested family/operation report whether the exact desired composition is executable using the current frozen production path.

If a requested entity-level Door or Window operation is genuinely unavailable:

STOP before genuine execution and return:

`COMPOSITE_EVIDENCE_CAPABILITY_BLOCKED`

Do not silently substitute property modification.

We want to know what the system actually supports.

---

# 6. Model and geometry binding

Produce:

`composite-model-selection.md`

For every selected IFC record:

* source;
* path;
* SHA-256;
* IFC schema;
* project units;
* Storeys;
* relevant family counts;
* candidate Walls/Openings;
* available existing Types;
* why the model is suitable;
* prior Text2IFC evidence usage if known.

All BIM bindings must use public information.

No private damaged/original truth may enter the production path.

For every add operation freeze:

* Storey GlobalId;
* public host GlobalId where applicable;
* start/end axis or placement;
* dimensions;
* orientation;
* Type policy;
* host/opening relationship target.

Check geometry feasibility before genuine execution.

Do not change geometry after Provider behavior is observed.

---

# 7. Freeze specification

Before any genuine Provider call, create:

`composite-bound-testcases.md`

and machine-readable:

`composite-acceptance-freeze.json`

For every case record:

* case ID;
* model;
* exact request;
* request hash;
* difficulty/scale;
* operation count;
* operation families;
* exact public bindings;
* expected terminal class;
* required atomicity;
* expected entity delta;
* Type policy;
* expected artifact predicates;
* whether property resolution is involved;
* provider stages expected;
* reopen requirement;
* preservation requirement.

The case meaning must not change after execution begins.

---

# 8. Composite Proof must be operation-bound

The previous R1 Proof implementation may identify a structural predicate only by operation type.

That is insufficient for:

* Beam ×2;
* Column ×4;
* repeated same-family operations.

For THIS NEW evidence namespace, every expected artifact predicate must bind to a stable:

`operation_id`

plus:

`operation_type`

Do not rely only on operation type.

Example concept:

```json
{
  "predicate_id": "C5-column-03",
  "operation_id": "op-column-03",
  "operation_type": "add_column"
}
```

The Proof must independently verify every requested occurrence.

Do not alter historical R1 Proof semantics merely to support this new evidence group.

Use the smallest versioned composite-proof extension necessary.

---

# 9. Composite preservation semantics

Whole-model preservation must compose the authorized deltas from ALL operations in the atomic ChangeSet.

Conceptually:

# `allowed whole-model delta`

union of independently authorized deltas of every requested operation.

For example a composite transaction may authorize:

* N Beam occurrences;
* N Column occurrences;
* generated/reused Types;
* containment relationships;
* Door/Window/Opening entities;
* fills/voids relationships;
* exact authorized property mutation.

Anything outside the composed authorized delta must fail validation.

Do NOT implement preservation by skipping unknown operation types.

---

# 10. Genuine execution

Only proceed if:

* execution revision remains fixed;
* production-affecting working tree remains unchanged;
* all required operation health checks pass;
* cases are frozen;
* composite Proof validator is ready;
* zero-provider focused tests pass.

Then run the genuine cases exactly once in frozen order:

`C1 → C2 → C3 → C4 → C5 → C5-N`

Use the currently authoritative live Provider configuration.

Record full provenance:

* model;
* thinking mode;
* stage calls;
* retry/attempt count;
* token usage;
* latency;
* prompt/profile/few-shot identity;
* Stage 1;
* Stage 1.5 when applicable;
* Stage 2;
* Binder;
* Audit;
* apply;
* reopen.

No synthetic/cached fallback may count as genuine success.

On the first new deterministic/infrastructure defect:

* preserve the failure;
* STOP;
* do not patch-and-continue;
* do not replace the case.

---

# 11. Artifact Delta Evidence

Every successful positive case must produce a human-readable:

`ARTIFACT-DELTA.md`

and machine-readable equivalent.

At minimum show:

### Before

* relevant entity counts;
* selected region/families;
* relevant existing Type/host/opening state.

### After

* added GlobalIds;
* added IFC classes;
* added Types;
* containment;
* geometry;
* host/opening/fill relationships;
* property differences if applicable.

Example:

```text
IfcBeam:   52 → 55
IfcColumn: 88 → 92
IfcDoor:   41 → 42
IfcWindow: 73 → 74

Added:
Beam B1 ...
Beam B2 ...
Column C1 ...
...

Atomic publication: PASS
IFC2X3 reopen: PASS
Preservation: PASS
```

The evidence must make the model change understandable without reading internal Agent traces.

---

# 12. Before / After IFC artifacts

Retain:

* immutable source IFC reference/hash;
* repaired IFC;
* case-specific artifact delta;
* Proof artifacts.

Do not require or manufacture private pristine Ground Truth for this showcase pack.

If legitimate private comparator truth already exists independently, it may be used only post-repair and must be clearly marked private.

---

# 13. Composite summary matrix

Produce:

`composite-evidence-matrix.md`

Required columns:

| Case | BIM | Families | Entity Ops | Property Intents | Total Intents | Atomic | Visible Artifact Change | Outcome |
| ---- | --- | -------: | ---------: | ---------------: | ------------: | -----: | ----------------------: | ------- |

Also report:

* total successful operations;
* total requested operations;
* number of families;
* number of created entities;
* number of created Types;
* model reopen result;
* preservation result.

For an atomic positive case:

`9/10 operations successful`

is NOT a successful case.

Case success requires all required operations and all artifact predicates to pass.

---

# 14. Cross-audit with independent subagent

After the task appears complete, launch an independent review subagent.

The reviewer must NOT modify implementation.

Ask it to audit:

1. case composition really matches frozen semantics;
2. operation counts are not inflated by bookkeeping;
3. same-family repeated operations are independently proven;
4. Door/Window entity modifications are genuine;
5. geometry was frozen before Provider execution;
6. Provider evidence is genuine;
7. no private truth entered production;
8. atomicity is independently proven;
9. Artifact Delta matches actual IFC;
10. no unrelated mutation occurred;
11. negative twin produced zero mutation;
12. original R1 evidence was not altered.

If reviewer finds a material issue:

* report it;
* do not silently edit historical evidence;
* mark the case/evidence group failed or blocked as appropriate.

Save the review as:

`composite-independent-audit.md`

---

# 15. Final outputs

At minimum produce:

1. `composite-capability-feasibility.md`
2. `composite-model-selection.md`
3. `composite-bound-testcases.md`
4. `composite-acceptance-freeze.json`
5. composite Proof contract/profile if needed
6. per-case evidence directories
7. per-case `ARTIFACT-DELTA.md`
8. `composite-evidence-matrix.md`
9. `composite-independent-audit.md`
10. `COMPOSITE-EVIDENCE-REPORT.md`

Do not modify the old R1 12-case evidence.

---

# Final report

Report:

## Base revision

## Capability health

## Selected BIMs

## Frozen composite cases

## Genuine Provider calls

## Per-case result

## Scale ladder result

## Hero Case artifact delta

## Negative twin result

## Preservation / atomicity

## Independent subagent audit

## Any blockers

End exactly with one:

`COMPOSITE_REPAIR_EVIDENCE_COMPLETE`

or

`COMPOSITE_EVIDENCE_CAPABILITY_BLOCKED`

or

`COMPOSITE_REPAIR_EVIDENCE_FAILED`
