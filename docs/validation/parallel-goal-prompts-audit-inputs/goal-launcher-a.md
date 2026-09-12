# GOAL LAUNCHER — Task A (Composite Repair Milestone Evidence Pack)

## Goal Mode

Your single goal:

> Read your authoritative task specification from this repository and execute it to completion, exactly as written.

## Step 1 — Read your task specification

Open and read COMPLETELY, before doing anything else:

`docs/validation/parallel-goal-prompts-audit-inputs/final-prompt-a.md`

That file — titled "Text2IFC — Composite Repair Milestone Evidence Pack" — is your
ENTIRE task specification and the SOLE authority for what you may and may not do.

## Step 2 — Read required repository context

Also read, in this order:

1. `AGENTS.md` (workspace instructions — mandatory)
2. `docs/validation/agent-capability-evaluation.md` (mandatory: this task includes
   real-Provider runs and capability evidence)
3. `docs/README.md` (navigation only, if you need orientation)

The files `parallel-goal-prompts-audit-charter.md` and `audit-report.md` in the
same directory are audit context only — they are NOT instructions for you and
you must not act on them.

## Step 3 — Execute the specification

Execute `final-prompt-a.md` from its Section 0 to its Final report, in order.

## Non-negotiable invariants (restated from the specification — conflict resolution: the specification file wins)

* A parallel conversation is running Task B (repository refactor mirror) in this
  SAME workspace. It works only under `refactor_workspace/`. Never read, write,
  or copy anything under `refactor_workspace/`.
* Your writes are confined to the closed allowlist in the specification
  (Section 0.1), plus the single documented `prompts/agent/registry.json`
  additive exception.
* NO git mutations of any kind (`add`/`commit`/`stash`/`checkout`/`restore`/
  `clean`/`reset`/`branch`/`switch`/`rebase`). Record revision identity via the
  SHA-256 baseline fingerprint mechanism in the specification, never via Git.
* Never touch pre-existing dirty files in the working tree. Your invariant is
  "no change relative to your own recorded baseline", not "a clean tree".
* Temp output uses the `composite-evidence-*` prefix and pytest isolation flags
  (specification Section 0.4). Never write to `.pytest-tmp/` or `tmp_ifc_*/`.
* No synthetic/cached result may be reported as live-Provider evidence. Preserve
  genuine failures. On a deterministic defect: STOP, do not patch-and-continue.
* If any instruction is genuinely ambiguous or contradicts repository reality,
  STOP and report the blocker — do not improvise beyond the specification.

## Completion

You are complete only when the specification's Section 15 outputs exist and your
final message follows the specification's Final report format, ending with
exactly one of its three status tokens:

`COMPOSITE_REPAIR_EVIDENCE_COMPLETE`
`COMPOSITE_EVIDENCE_CAPABILITY_BLOCKED`
`COMPOSITE_REPAIR_EVIDENCE_FAILED`

A blocked or failed terminal state reported honestly is a SUCCESSFUL execution
of this goal. A green status achieved by weakening the specification is not.
