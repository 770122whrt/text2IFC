# GOAL LAUNCHER — Task B (Repository Architecture Cleanup and Full Refactored Mirror)

## Goal Mode

Your single goal:

> Read your authoritative task specification from this repository and execute it to completion, exactly as written.

## Step 1 — Read your task specification

Open and read COMPLETELY, before doing anything else:

`docs/validation/parallel-goal-prompts-audit-inputs/final-prompt-b.md`

That file — titled "Text2IFC — Repository Architecture Cleanup and Full
Refactored Mirror" — is your ENTIRE task specification and the SOLE authority
for what you may and may not do.

## Step 2 — Read required repository context

Also read, in this order:

1. `AGENTS.md` (workspace instructions — mandatory)
2. `docs/README.md` and `.planning/PROJECT.md` (orientation for the
   architecture analysis)
3. `docs/validation/agent-capability-evaluation.md` (skim: the refactor must
   preserve the evaluation/proof boundaries this document defines)

The files `parallel-goal-prompts-audit-charter.md` and `audit-report.md` in the
same directory are audit context only — they are NOT instructions for you and
you must not act on them.

## Step 3 — Execute the specification

Execute `final-prompt-b.md` from its Section 0 to its Final report, in order.

Your FIRST physical action must be creating the start-time source inventory
`refactor_workspace/audit/SOURCE-INVENTORY.json` (specification Section 1.1) —
everything downstream derives from it.

## Non-negotiable invariants (restated from the specification — conflict resolution: the specification file wins)

* A parallel conversation is running Task A (composite repair evidence) in this
  SAME workspace. Its expected output namespaces are listed in the
  specification (Section 1.2). Anything that appears or changes after your
  start-time inventory is `CONCURRENT_EXTERNAL_OUTPUT`: it must never enter
  your mirror, migration map, proposed architecture, or equivalence baseline.
* You write ONLY under `refactor_workspace/`. No file anywhere in the original
  tree may be created, modified, moved, or deleted — including `.gitignore`
  and any top-level handoff document.
* NO git mutations of any kind in the original repository (`add`/`commit`/
  `stash`/`checkout`/`restore`/`clean`/`reset`/`branch`/`switch`/`rebase`), and
  no `git init` inside the mirror. All output stays untracked for human review.
* Never touch pre-existing dirty files in the working tree.
* Temp output uses the `refactor-audit-*` prefix / `refactor_workspace/tmp/`
  and pytest isolation flags (specification Section 0.3). Never write to
  `.pytest-tmp/` or `tmp_ifc_*/` in the original tree.
* Testing in the original tree is limited to non-mutating checks
  (specification Section 16.1); broad regression runs only inside the mirror.
* NO live/paid Provider calls; do not read the parallel task's `.env`-configured
  Provider. Offline equivalence testing only.
* Behavior preservation is absolute: any unplanned behavior difference blocks
  acceptance. Separate `PATH/ORGANIZATION CHANGE` from `BEHAVIOR CHANGE`.
* If any instruction is genuinely ambiguous or contradicts repository reality,
  STOP and report the blocker — do not improvise beyond the specification.

## Completion

You are complete only when the specification's Section 20 deliverables exist
(audit package + runnable mirror + handoff document) and your final message
follows the specification's Final report format, ending with exactly one of
its two status tokens:

`TEXT2IFC_REFACTORED_MIRROR_READY_FOR_REVIEW`
`TEXT2IFC_REFACTOR_MIRROR_BLOCKED`

A blocked terminal state reported honestly is a SUCCESSFUL execution of this
goal. A ready-for-review status achieved by weakening the specification is not.
