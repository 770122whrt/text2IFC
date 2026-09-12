# Text2IFC — Repository Architecture Cleanup and Full Refactored Mirror

## Goal Mode

Work toward one explicit goal:

> Understand the current Text2IFC repository as an engineering and research system, clarify its conceptual architecture and code ownership, and produce a cleaner, runnable, behavior-preserving REFACTORED MIRROR of the project together with authoritative Markdown architecture documentation.

This is NOT a feature-development task.

The objective is clarity:

* clear ideas;
* clear module ownership;
* clear execution paths;
* clear contracts;
* clear evidence boundaries;
* clear documentation hierarchy;
* clear separation of source, tests, research evidence, datasets, scripts, schemas, prompts, and historical artifacts.

---

# 0. Critical parallel-work isolation

Another conversation is simultaneously building a new Composite Repair evidence group in the SAME repository.

Therefore:

## DO NOT reorganize the active repository in place.

Do NOT move, rename, delete, or modify ANY active project file.

Do NOT modify the production tree being used by the evidence conversation.

## 0.1 Closed write allowlist

Everything you create or modify must live under EXACTLY ONE root:

`refactor_workspace/`

No exceptions. No top-level handoff document in the original tree: the handoff document is `refactor_workspace/REFACTOR-HANDOFF.md`.

If an existing repository convention absolutely requires a different isolated root, document the choice; the allowlist stays CLOSED: one isolated root, nothing outside it.

The active original repository remains the reference implementation.

The refactored mirror is the proposed future repository.

No file in the original production tree may be created, overwritten, moved, or deleted.

## 0.2 Git rules — absolute

In the ORIGINAL repository do NOT run: `git add`, `git commit`, `git stash`, `git checkout`, `git restore`, `git clean`, `git reset`, `git branch`, `git switch`, `git rebase`.

Do NOT modify `.gitignore` or any dotfile in the original tree (adding `refactor_workspace/` to it would itself be an original-tree write; the directory simply stays untracked).

Do NOT run `git init` inside the mirror. The mirror is a plain directory tree; whether it becomes a repository is decided by the adoption conversation.

The working tree already contains pre-existing dirty files belonging to other work (including the parallel evidence task). NEVER revert, clean, or overwrite them.

## 0.3 Temporary output rules

* Never write to shared fixed temp paths such as `.pytest-tmp/` or `tmp_ifc_*/` in the original tree.
* Temp/scratch output uses prefix `refactor-audit-*` under the system temp location or under `refactor_workspace/tmp/`.
* When running pytest for this task, use `-p no:cacheprovider` and `--basetemp` pointing inside `refactor_workspace/`.

---

# 1. Establish source revision — with a start-time inventory

Record:

* current branch;
* current HEAD SHA;
* full `git status` output;
* files clearly belonging to the parallel evidence task;
* unrelated pre-existing dirty files.

Define:

`REFACTOR_SOURCE_REVISION=<SHA>`

## 1.1 Source inventory — mandatory mechanism

FIRST ACTION of the task: create

`refactor_workspace/audit/SOURCE-INVENTORY.json`

containing:

* HEAD SHA and branch;
* the list of ALL tracked files (`git ls-files`) with per-file SHA-256 (blob content hash);
* the list of untracked-but-present files at start (from `git status --porcelain`), each marked `UNTRACKED_AT_START`;
* timestamps.

Validate the inventory is internally complete (every listed file readable; `registry.json`-style JSON files parse).

## 1.2 CONCURRENT_EXTERNAL_OUTPUT rule

Any file that appears (or changes) after this inventory is `CONCURRENT_EXTERNAL_OUTPUT` by default — most likely the parallel evidence task's output (expected namespaces include `docs/validation/repair-composite-milestone/`, `dataset/processed/proof/repair-composite-milestone/`, `scripts/ifc_repair/composite_evidence/`, `tests/ifc_repair/composite_evidence/`, and a possible additive `prompts/agent/registry.json` change).

`CONCURRENT_EXTERNAL_OUTPUT` must NOT enter:

* the refactored mirror;
* the migration map;
* the proposed architecture;
* the behavioral equivalence baseline.

You MAY note its existence in `refactor_workspace/audit/CONCURRENT-OBSERVATIONS.md` (one line per observed path), but never adopt it automatically.

The mirror must identify exactly which source revision it was derived from: ONLY inventory-listed file states.

---

# 2. First understand the repository

Before reorganizing anything, perform a repository inventory using `SOURCE-INVENTORY.json` as the file universe.

Inspect at minimum:

* top-level directories;
* `src/`;
* `scripts/`;
* `tests/`;
* `prompts/`;
* `schemas/`;
* `docs/`;
* `.planning/`;
* dataset/data directories;
* proof/evidence directories;
* evaluation tools;
* runner entrypoints;
* configs;
* environment/dependency files;
* generated artifacts;
* historical research materials.

## 2.1 Bounded analysis granularity

Apply per-file depth ONLY where ownership genuinely lives:

* `src/` and `scripts/`: per-module analysis (purpose, owner concept, dependencies);
* `tests/`: per-test-file mapping to the module it covers;
* `prompts/`, `schemas/`, configs: per-asset registration/ownership;
* `docs/`, `.planning/`, `dataset/`, evidence dirs: per-directory purpose plus flagged anomalies only.

For each analyzed item identify:

* purpose;
* owner concept;
* production or non-production;
* runtime dependency;
* test dependency;
* authoritative vs historical;
* generated vs source-controlled;
* public evidence vs private benchmark truth;
* whether other files import/reference it;
* whether it appears obsolete/duplicate.

Do not guess from filenames only.

Read actual imports, registry references, CLI entrypoints, schemas and documentation links.

---

# 3. Build a conceptual architecture first

Before writing the refactored mirror, produce:

`refactor_workspace/audit/CURRENT-ARCHITECTURE.md`

Describe the CURRENT system as it actually exists.

At minimum identify layers such as:

1. User/API boundary
2. Agent/Provider layer
3. Repair Intent
4. deterministic target resolution
5. property knowledge / retrieval
6. Stage 1.5 semantic resolution
7. admissibility/authority
8. Stage 2 ChangeSet drafting
9. Binder / Audit
10. IFC operation registry/applicators
11. evaluation
12. Proof / validation / curation
13. datasets/benchmarks
14. runners/tooling
15. research/planning/documentation

Use repository evidence (cite files).

Do not invent an architecture the code does not actually have.

---

# 4. Build a file ownership map

Produce:

`refactor_workspace/audit/FILE-OWNERSHIP-MAP.md`

For every significant module/directory answer:

> Why does this exist and which conceptual layer owns it?

Use tables, one row per module (per Section 2.1 granularity). Highlight:

* misplaced files;
* duplicate responsibilities;
* files with ambiguous ownership;
* scripts that are effectively production modules;
* production code hiding inside validation scripts;
* historical code still imported by current production;
* obsolete compatibility code;
* prompt/schema/profile coupling;
* evidence-specific code mixed into general runtime.

Do not delete based solely on suspicion.

---

# 5. Dependency and execution map

Produce:

`refactor_workspace/audit/EXECUTION-PATHS.md`

Trace the actual important flows.

At minimum:

### Production Repair

Natural language
→ API
→ Stage 1
→ resolution
→ property retrieval/Stage 1.5 when applicable
→ deterministic admissibility
→ Stage 2
→ Binder/Audit
→ applicator
→ repaired IFC
→ evaluator.

### Clarification/resume

### Unsupported/fail-closed

### Offline semantic evaluation

### Genuine Provider UAT

### Proof curation/validation

### Benchmark/private comparison

For every flow list actual files/functions/modules.

---

# 6. Define refactor principles

The refactor must prioritize:

1. behavior preservation;
2. conceptual clarity;
3. module cohesion;
4. minimal circular dependencies;
5. stable public contracts;
6. clear production/evaluation isolation;
7. clear source/generated artifact boundary;
8. removal of unnecessary path ambiguity;
9. predictable naming;
10. maintainability for future researchers/agents.

Do NOT introduce abstraction merely for architectural aesthetics.

Do NOT create unnecessary framework layers.

Do NOT rewrite working algorithms.

Do NOT change research semantics.

---

# 7. Proposed repository structure

After the audit, design the target structure.

Document it first in:

`refactor_workspace/audit/PROPOSED-STRUCTURE.md`

Include a full tree and rationale.

The exact structure must be derived from the repository rather than blindly imposed.

However the resulting organization should make these concerns visually distinct:

* production Python packages;
* Agent/provider integration;
* IFC repair domain;
* knowledge/retrieval;
* contracts/schemas;
* prompt assets;
* CLI/runners/tools;
* tests;
* benchmarks;
* validation/evaluation;
* proof artifacts;
* datasets/data references;
* research/planning;
* user/developer documentation;
* generated artifacts.

Avoid top-level dumping grounds.

---

# 8. Important architectural boundaries

The refactored mirror must preserve these boundaries explicitly.

## Production vs benchmark truth

Production must not depend on:

* pristine original IFC;
* deleted GUIDs;
* mutation truth;
* private Gold;
* post-repair benchmark comparator.

These belong only to private evaluation/benchmark layers.

## Prompt/schema/profile assets

Make their relationships clear.

Avoid scattered assets whose owning runtime cannot be determined.

## Runners vs reusable implementation

A `scripts/` file that contains reusable domain logic should be evaluated for migration into a proper package.

CLI orchestration may remain in tooling/entrypoint directories.

## Proof/evidence

Proof validators, curators and immutable generated evidence must not be confused with production execution.

## Research history

Historical plans and research notes should remain accessible but clearly separated from authoritative current architecture.

---

# 9. Create the refactored mirror

After the proposed structure is documented, create:

`refactor_workspace/text2ifc-refactored/`

This should be a coherent proposed repository, not merely a diagram.

Migrate/copy/reorganize the code and project files into this mirror, sourcing EXCLUSIVELY from `SOURCE-INVENTORY.json` states (Section 1).

## Do not copy

* `.git/`;
* caches (`__pycache__/`, `.pytest_cache/`, `.cache/`), virtual environments, `.deps/`;
* `.env` or any secrets/credentials;
* transient pytest temp directories;
* `dataset/processed/ifc-repair/` transient live-run outputs (gitignored);
* large generated execution artifacts — proof/evidence binaries are REFERENCED, not duplicated (see below);
* irrelevant local PDFs/binaries;
* `refactor_workspace/` itself;
* the parallel-audit artifacts under `docs/validation/parallel-goal-prompts-audit-*` (reference-only);
* anything classified `CONCURRENT_EXTERNAL_OUTPUT`.

For large datasets/evidence that should not be duplicated, create explicit documented external/reference locations (pointer files with expected SHA-256) rather than silently omitting them. Small fixtures required for tests may be copied.

The mirror should remain understandable and runnable.

---

# 10. Preserve functionality

Update inside the mirror as necessary:

* imports;
* relative paths;
* package initialization;
* CLI entrypoints;
* registry paths;
* schema paths;
* prompt paths;
* test paths;
* documentation links;
* fixture locations.

Do not modify behavior unless relocation absolutely requires a compatibility change.

Every behavior-affecting difference must be reported.

Prefer deterministic path resolution from project/package roots over fragile current-working-directory assumptions.

---

# 11. Avoid giant modules

Identify oversized modules or files combining unrelated responsibilities.

For each, decide whether it should:

* remain intact;
* be split;
* have helpers extracted;
* move to a more appropriate owner package.

Do not split merely because a file is long.

Split only when responsibilities are genuinely separable.

Pay special attention to:

* large validators;
* large runners;
* operation registries;
* Provider glue;
* Proof tooling.

---

# 12. Naming cleanup

Normalize confusing naming only where it materially improves understanding.

Examples to inspect:

* `phaseXX` names that are now production-generic;
* old version-specific helpers still used generally;
* `live`, `offline`, `success_case`, `proof`, `validation` naming overlap;
* repair vs evaluation vocabulary;
* historical aliases.

Do not casually rename public schema IDs or frozen evidence contracts.

Historical version identifiers remain immutable.

---

# 13. Documentation hierarchy

The mirror must include a clear documentation entrance.

Produce at minimum (inside the MIRROR):

`docs/README.md`

`docs/architecture/SYSTEM-OVERVIEW.md`

`docs/architecture/REPAIR-PIPELINE.md`

`docs/architecture/MODULE-MAP.md`

`docs/architecture/CONTRACTS-AND-AUTHORITY.md`

`docs/architecture/EVALUATION-AND-PROOF.md`

`docs/development/REPOSITORY-GUIDE.md`

`docs/development/ADDING-AN-OPERATION.md`

`docs/development/TESTING-GUIDE.md`

Exact names may be adjusted coherently.

These documents must reflect the refactored mirror, not the historical repository.

Prefer tables and precise pointers over long prose; each document should stay concise (roughly ≤ 300 lines) unless the content genuinely justifies more.

---

# 14. Migration map

Produce:

`refactor_workspace/audit/MIGRATION-MAP.md`

Use a table:

| Original path | Refactored path | Action | Reason | Behavior impact |
| ------------- | --------------- | ------ | ------ | --------------- |

Every moved/renamed/merged/deferred significant file must appear.

Also list:

### intentionally retained unchanged

### intentionally not copied

### likely obsolete but not deleted

### requires human decision

Do not hide uncertain files.

---

# 15. Architectural debt report

Produce:

`refactor_workspace/audit/ARCHITECTURAL-DEBT.md`

Classify findings:

* P0 correctness/dependency problems;
* P1 serious maintainability issues;
* P2 cleanup;
* historical debt;
* intentionally retained compatibility.

Examples:

* circular imports;
* duplicate schemas;
* scripts importing scripts;
* hard-coded phase identifiers in generic production code;
* evaluation logic mixed into production;
* duplicated path constants;
* stale documentation;
* obsolete entrypoints.

Do not fix unrelated P2 issues merely because they exist.

---

# 16. Tests in the mirror

## 16.1 Where tests run

All execution happens INSIDE the mirror (or with outputs directed into `refactor_workspace/`), using Section 0.3 temp isolation (`-p no:cacheprovider`, `--basetemp` inside `refactor_workspace/`).

Testing in the ORIGINAL tree is limited to non-mutating checks: `--collect-only`, import/compile checks, and a focused offline selection — never a full suite, never anything that writes outside `refactor_workspace/`. Full original-tree baseline runs belong to the post-adoption audit, after the parallel evidence task finishes.

## 16.2 What to run in the mirror

Start with:

* import/compile checks;
* registry loading;
* prompt/schema loading;
* representative unit tests;
* repair API;
* target resolution;
* Stage 1.5;
* Beam/Column operations;
* Door/Window operations;
* Binder/Audit;
* evaluator;
* Proof validator.

Because this is a repository-wide refactor, a broad regression IN THE MIRROR is justified once focused failures are resolved.

Do NOT call paid/live Providers. Do not read the parallel task's `.env`-configured Provider at all.

Use zero-network/offline tests for refactor equivalence.

Do not regenerate genuine evidence.

Do not rebuild retrieval indexes into any shared original-tree location; if an index is needed, build it inside the mirror from the mirror's own assets.

---

# 17. Behavioral equivalence report

Produce:

`refactor_workspace/audit/BEHAVIOR-EQUIVALENCE.md`

Report:

* tests run (command + result, separated mirror vs original-tree);
* pass/fail;
* imports;
* registries (operation registry parity; `prompts/agent/registry.json` hash comparison against SOURCE-INVENTORY version — a mid-run additive change by the parallel task is a known, documented difference, not a defect);
* prompt/profile hashes if preserved;
* schema identities;
* operation types;
* major CLI entrypoints;
* known differences.

Separate:

`PATH/ORGANIZATION CHANGE`

from:

`BEHAVIOR CHANGE`

Any unplanned behavior change blocks acceptance of the refactor.

---

# 18. Independent subagent cross-audit

After implementation appears complete, launch an independent reviewer subagent.

The reviewer must be read-only.

It should compare:

`original repository`

vs

`refactor_workspace/text2ifc-refactored/`

Audit at minimum:

1. missing production modules;
2. missing tests;
3. broken imports;
4. broken prompt/schema/profile paths;
5. operation registry parity;
6. API parity;
7. Stage 1/1.5/2 flow parity;
8. production/private-evidence isolation;
9. evaluation parity;
10. Proof tooling parity;
11. important docs/evidence accidentally omitted;
12. duplicate or orphan files;
13. circular dependencies;
14. new architecture actually clearer;
15. unnecessary abstractions introduced;
16. no CONCURRENT_EXTERNAL_OUTPUT leaked into the mirror;
17. original project was not modified by this task.

For item 17 the reviewer must re-hash a sample (at minimum: every file under `src/`, `schemas/`, `prompts/`, `pyproject.toml`) and compare against `SOURCE-INVENTORY.json`.

Require concrete evidence, not a generic code review.

Save:

`refactor_workspace/audit/INDEPENDENT-REFACTOR-AUDIT.md`

---

# 19. Reconcile review findings

After the independent review:

* fix issues only inside the refactored mirror;
* rerun relevant focused tests;
* have the reviewer recheck material P0/P1 findings.

Do not modify the active original repository.

---

# 20. Final deliverables

The task must leave two major outputs.

## A. Refactor analysis package

Under:

`refactor_workspace/audit/`

At minimum:

1. `SOURCE-INVENTORY.json`
2. `CONCURRENT-OBSERVATIONS.md` (may be empty)
3. `CURRENT-ARCHITECTURE.md`
4. `FILE-OWNERSHIP-MAP.md`
5. `EXECUTION-PATHS.md`
6. `PROPOSED-STRUCTURE.md`
7. `MIGRATION-MAP.md`
8. `ARCHITECTURAL-DEBT.md`
9. `BEHAVIOR-EQUIVALENCE.md`
10. `INDEPENDENT-REFACTOR-AUDIT.md`
11. `REFACTOR-SUMMARY.md`

## B. Refactored full project

Under:

`refactor_workspace/text2ifc-refactored/`

It must be a coherent project folder with:

* source;
* tests;
* contracts/assets;
* tools;
* documentation;
* configs;
* necessary fixtures;
* clear external data/evidence references.

Plus:

`refactor_workspace/REFACTOR-HANDOFF.md` — the single entry document explaining what was produced, where, and what decisions remain for the human.

---

# 21. Do not merge

This task is NOT authorized to replace the existing repository with the mirror.

Do not:

* delete the original tree;
* mass-move original files;
* merge the refactor into production;
* rewrite Git history;
* commit over the active production architecture;
* commit anything at all — all output remains untracked under `refactor_workspace/` for the user to review.

A separate human/independent audit conversation will decide whether and how this mirror is adopted.

---

# 22. Final report

Report:

## Source revision

(inventory mechanism status, concurrent-output observations summary)

## Original architecture findings

## Major architecture problems

## Proposed structure

## Refactored mirror location

## File migration summary

## Test/equivalence result

## Independent audit result

## Remaining human decisions

## Explicit confirmation that original active tree was not reorganized

(backed by the final fingerprint comparison against SOURCE-INVENTORY.json)

End exactly with one:

`TEXT2IFC_REFACTORED_MIRROR_READY_FOR_REVIEW`

or

`TEXT2IFC_REFACTOR_MIRROR_BLOCKED`
