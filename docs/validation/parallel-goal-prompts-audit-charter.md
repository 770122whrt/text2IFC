# Text2IFC — Parallel Goal Prompts Pre-Execution Audit (Charter)

> Status: charter received, audit NOT started. Waiting for Prompt A and Prompt B,
> and for the user's explicit "开始审核" signal.
> This file is the audit working charter only. It is not evidence and not a task artifact.

## Role

The auditor is NOT executing either Text2IFC task. The auditor performs a
PRE-EXECUTION AUDIT of TWO prompts that will later be launched in two separate
Goal Mode conversations against the SAME repository/workspace:

1. `Text2IFC — Composite Repair Milestone Evidence Pack` (Prompt A / Task A)
2. `Text2IFC — Repository Architecture Cleanup and Full Refactored Mirror` (Prompt B / Task B)

Responsibility: audit and improve the PROMPTS THEMSELVES before either task begins.

Forbidden during audit: executing their tasks, modifying the repository (except
this charter file), running tests, calling Providers, creating evidence,
performing the refactor.

Final result: TWO hardened prompts that are safe to launch in parallel.

## 1. Primary objective

Determine whether the two prompts can safely run in parallel against the same
Text2IFC repository without:

- modifying the same production files;
- moving files while the other task is executing them;
- invalidating execution revision provenance;
- mixing evidence with refactor artifacts;
- overwriting historical R1 evidence;
- creating ambiguous Git state;
- racing on shared generated directories;
- changing prompts/schemas/profiles used by genuine execution;
- creating inconsistent checkpoints;
- allowing one task to consume artifacts produced by the other task during the run.

## 2. Treat the two tasks as fundamentally different

### Task A — Composite Repair Evidence

Primary purpose: demonstrate large-scale, atomic, multi-family IFC repair
capability using the CURRENT production implementation.

May: inspect current production; perform focused health checks; create new
evidence-specific files; create dedicated proof/evidence support if explicitly
scoped; execute genuine frozen composite cases only after freeze conditions are
satisfied.

Must NOT: reorganize the repository; broadly modify production; move modules;
tune implementation to pass showcase cases; consume a refactored mirror as
production authority. Evidence must remain bound to the original production
revision.

### Task B — Repository Refactor Mirror

Primary purpose: understand and reorganize the Text2IFC repository into a
clearer behavior-preserving proposed project structure.

Must work in an ISOLATED mirror/staging directory.

Must NOT: reorganize the active original repository; alter production files used
by Task A; alter Task A evidence; replace current production while Task A is
running; change the authoritative execution revision.

The refactored mirror is a PROPOSAL / candidate repository, not the production
authority for Task A.

## 3. Audit filesystem collision risks

Produce a table: Path/namespace × Task A access × Task B access × Collision
risk × Required fix. At minimum inspect planned writes involving: `src/`,
`scripts/`, `tests/`, `prompts/`, `schemas/`, `docs/`, `docs/validation/`,
`dataset/processed/`, proof/evidence directories, `.planning/`, temporary test
directories, refactor workspace, generated reports, Git staging/checkpoint
behavior. Goal: WRITE SETS disjoint except unavoidable read-only access.

## 4. Audit production-version integrity

Task A's genuine evidence must correspond to one stable production
implementation. Check protection against: Task B modifying original production;
HEAD changing during execution; production-affecting uncommitted changes; Task A
starting on SHA X and finishing on SHA Y; schemas/prompts/profiles changing
midway. Task A should record at least: initial branch; initial HEAD SHA;
production working-tree fingerprint/state; prompt/schema/profile relevant state.
Immediately before genuine Provider execution, re-check the authoritative
production implementation has not changed. If changed: STOP; do not continue
genuine execution.

## 5. Audit Git interaction

The two Goal conversations must not create conflicting Git operations. Review
whether either prompt permits: staging the entire repository; committing
unrelated files; cleaning/resetting shared worktree; deleting untracked files;
switching branches; rebasing; checking out paths belonging to the other task.
These should normally be prohibited. Prefer artifact-level revision recording
over broad shared-worktree Git manipulation during parallel execution.

## 6. Audit Task A — evidence scientific validity

- Evidence freeze: models chosen before genuine execution; exact requests
  frozen; geometry frozen; operation composition frozen; expected terminal
  class frozen; no changing cases after observing Provider behavior.
- Production isolation: no pristine/original private truth in production; no
  mutation truth; no deleted GUIDs; no private Gold; no benchmark answer leakage.
- Genuine execution: real Provider evidence only; no synthetic fallback counted
  as success; failures preserved; no patch-and-continue.
- Composite complexity: cases must genuinely show increasing repair complexity,
  especially: repeated same-family operations; multiple Beams; multiple Columns;
  Door; Window; atomic ChangeSet; Hero Case; negative atomic twin.
- Proof identity: repeated operations must be proven by stable operation
  identity (`operation_id + operation_type` or equivalent), not by
  `operation_type` alone (insufficient for Column ×4, Beam ×3).

## 7. Audit Task A — capability honesty

Task A must NOT silently develop a missing feature. Health-check rules must
distinguish: inherited healthy capability; registered but currently broken
capability; unsupported capability. If Door/Window entity authoring is not
currently healthy: STOP and report the capability gap rather than replacing the
intended entity-level modification with an easier property edit. Do not force
Task A to re-prove every previous Phase capability — milestone
integration/showcase, not another exhaustive capability benchmark.

## 8. Audit Task B — refactor isolation

Confirm the refactor prompt creates a full mirror such as
`refactor_workspace/text2ifc-refactored/` and leaves the active project
untouched. Task B may READ the current repository broadly; WRITE only inside its
isolated workspace. It must NOT: move original files; rename original modules;
edit original docs; change original imports; clean the original project; write
tests into active `tests/`; modify active schemas/prompts; commit changes into
original production. Required modifications for refactor functionality occur
inside the mirror.

## 9. Audit Task B — avoid copying moving evidence

Task B must establish a start-time source inventory. Files appearing after that
baseline are classified `CONCURRENT_EXTERNAL_OUTPUT` unless explicitly part of
the original source revision; they must not silently enter the migration map,
proposed architecture, refactored mirror, or behavioral equivalence baseline.
Task B may document that concurrent evidence exists but should not adopt it
automatically.

## 10. Audit Task B — refactor quality

The refactor must include: current architecture; module ownership; execution
paths; dependency relationships; production/evaluation/private-truth
boundaries; proposed structure; migration mapping; architectural debt; behavior
equivalence. Prevent superficial refactors based only on folder names;
unnecessary abstraction and framework creation; rewriting algorithms merely to
make architecture appear cleaner.

## 11. Audit cross-task resource pressure

Review risks involving: large IFC files; pytest temp files; SQLite indexes;
Qdrant/local retrieval assets; evidence output directories; generated
filenames; Provider logs. Require task-specific temporary namespaces, e.g.
Task A prefix `composite-evidence-*`, Task B prefix `refactor-audit-*`. No reuse
of generic mutable temp/evidence paths that could collide.

## 12. Audit internal cross-review requirements

Both execution prompts must contain their OWN independent subagent audit
(separate from this prompt audit).

- Task A internal reviewer inspects: frozen-vs-executed semantics; operation
  count; artifact delta; atomicity; Provider provenance; private evidence
  isolation.
- Task B internal reviewer inspects: missing modules; broken imports; registry
  parity; production behavior parity; missing tests; accidental original-tree
  modification; whether the proposed architecture is genuinely clearer.

Executing agent addresses material P0/P1 findings within its own allowed
workspace before declaring completion.

## 13. Identify overreach

For BOTH prompts identify instructions that are unnecessarily expensive;
excessively broad; redundant; likely to cause context drift; likely to trigger
unrelated cleanup; likely to produce huge documentation without decision value.
Recommend reductions without weakening correctness or traceability.

## 14. Required risk matrix

| Risk                                   | Prompt A | Prompt B | Severity | Current protection | Required revision |
| -------------------------------------- | -------: | -------: | -------- | ------------------ | ----------------- |
| shared-file writes                     |          |          |          |                    |                   |
| Git collision                          |          |          |          |                    |                   |
| moving production during evidence      |          |          |          |                    |                   |
| moving execution revision              |          |          |          |                    |                   |
| prompt/schema drift                    |          |          |          |                    |                   |
| evidence namespace collision           |          |          |          |                    |                   |
| temporary artifact collision           |          |          |          |                    |                   |
| concurrent output absorbed by refactor |          |          |          |                    |                   |
| production behavior change             |          |          |          |                    |                   |
| private truth leakage                  |          |          |          |                    |                   |
| post-hoc testcase modification         |          |          |          |                    |                   |

## 15. Required conclusions

Answer explicitly: A. parallel-safe now? B. Task A bound to original production
throughout genuine execution? C. Task B mirror without modifying Task A's
environment? D. write namespaces genuinely disjoint? E. Git/worktree
instructions to remove or tighten? F. does Task A actually demonstrate
large-scale model modification rather than mostly property changes? G. does Task
B produce a genuinely usable refactored project rather than only documentation?
H. what MUST be revised before launch?

## 16–17. Final deliverables

Output complete sections:

- `# FINAL PROMPT A — COMPOSITE REPAIR EVIDENCE` — entire corrected Prompt A,
  directly copyable into a fresh Goal Mode conversation.
- `# FINAL PROMPT B — REPOSITORY REFACTOR MIRROR` — entire corrected Prompt B,
  directly usable in a separate Goal Mode conversation.

Not patches/diffs only — the ENTIRE corrected prompts.

## 18. Do not execute either prompt

Task ends after reviewing and rewriting the two prompts. Do not invoke either
workflow; modify Text2IFC; create evidence; create the refactored mirror; run
Provider calls; run repository tests; commit anything. The user reviews the two
final prompts and launches them manually.

## Final status

End with exactly one of:

`PARALLEL_GOAL_PROMPTS_APPROVED`

`PARALLEL_GOAL_PROMPTS_REVISION_REQUIRED`
