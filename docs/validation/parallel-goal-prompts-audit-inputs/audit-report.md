# Parallel Goal Prompts Pre-Execution Audit — Report

Audit date: 2026-08-31
Inputs: `prompt-a.md`, `prompt-b.md` (verbatim archives in this directory)
Charter: `../parallel-goal-prompts-audit-charter.md`
Outputs: `final-prompt-a.md`, `final-prompt-b.md` (this directory)

Verdict on the ORIGINAL two prompts as submitted: **REVISION REQUIRED**.
The revised prompts in this directory incorporate all required fixes; with those
fixes the two tasks are safe to launch in parallel.

## Repository facts verified during audit (read-only)

- `refactor_workspace/` does not exist yet; it is NOT in `.gitignore`.
- `.gitignore` ignores `.pytest-tmp*`, `tmp_ifc_*`, `/dataset/processed/ifc-repair/*`
  (transient live-run output); `dataset/processed/proof/` is the committed evidence area.
- `docs/validation/repair-milestone-r1/` and `dataset/processed/proof/ifc-repair-success-cases`
  hold R1 evidence; `dataset/processed/ifc-repair-runs/` holds phase12 run output.
- Operation names in Prompt A §2 all exist in
  `src/text2ifc_ifc_repair/operations/` (`door.py`, `window.py`) and
  `resolution_flow.py`. `structural_analysis_node` is NOT registered → valid
  unsupported-operation choice for C5-N.
- `operation_id` already exists as a unique, semantic-manifest-bound identity in
  `src/text2ifc_ifc_repair/changesets.py` (lines 170–327) — Prompt A §8's
  requirement is implementable by reuse, no parallel identity needed.
- `prompts/agent/registry.json` is the single shared mutable production file a
  new composite prompt/profile would need to touch.
- Live Provider config lives in `.env` (gitignored); only Task A needs it.
- Repo uses a shared fixed temp convention (`.pytest-tmp`) per .gitignore and
  `tests/ifc_repair/test_phase12_live_uat.py:1766` — a real concurrent-run hazard.

## §3 Filesystem collision table

| Path / namespace | Task A access | Task B access | Collision risk | Required fix (implemented in final prompts) |
| --- | --- | --- | --- | --- |
| `src/`, `schemas/` | read-only | read (copy to mirror) | LOW — B copies early-state files | B inventories at start; A never writes |
| `prompts/agent/registry.json` | possible ONE additive edit | read (copy + hash compare) | MEDIUM — only shared mutable file | A: single atomic early edit + hash recorded; B: freeze at inventory, treat later diff as known difference |
| `scripts/ifc_repair/composite_evidence/` | WRITE (new) | must not copy | LOW | B: CONCURRENT_EXTERNAL_OUTPUT rule |
| `tests/ifc_repair/composite_evidence/` | WRITE (new) | must not copy | LOW | same |
| `docs/validation/repair-composite-milestone/` | WRITE (new) | must not copy | LOW | same |
| `dataset/processed/proof/repair-composite-milestone/` | WRITE (new) | must not copy; reference-only | LOW | same |
| `dataset/processed/proof/` existing (R1, phase11) | read-only | reference/copy small fixtures | LOW | A: never writes existing evidence dirs; B: no binary duplication |
| `refactor_workspace/**` | FORBIDDEN to read | WRITE (new root) | LOW | A: explicit do-not-read rule |
| `docs/` original tree | read-only except own namespace | NO writes (original had "one top-level handoff doc" exception) | MEDIUM in original B | Removed exception; handoff lives at `refactor_workspace/REFACTOR-HANDOFF.md` |
| `.planning/` | read-only (no STATE.md updates) | read-only | LOW | Explicit in both |
| `.git/` / staging area | no git mutations | no git mutations | MEDIUM in originals (neither prohibited explicitly) | Absolute git-prohibition lists in both |
| Shared temp (`.pytest-tmp`, `tmp_ifc_*`, `.pytest_cache`) | default writes | default writes | HIGH | Task prefixes `composite-evidence-*` / `refactor-audit-*`; `-p no:cacheprovider`; `--basetemp` into own namespace |
| Retrieval/index assets (Qdrant/SQLite under knowledge runtime) | read-only use | must not rebuild in shared location | MEDIUM | B builds indexes only inside mirror; A never rebuilds |
| `.env` / Provider | read-only use | forbidden to use | LOW | Explicit in B |

Write sets after revision: disjoint. The registry.json case is the single,
documented, hash-tracked exception (additive, atomic, early).

## §14 Risk matrix

| Risk | Prompt A | Prompt B | Severity | Current protection | Required revision |
| --- | --- | --- | --- | --- | --- |
| shared-file writes | registry.json additive edit | none | MEDIUM | none in originals | atomic early edit + hash (A); frozen inventory (B) |
| Git collision | not prohibited | not prohibited | HIGH | none | absolute git-prohibition lists in both; record SHAs not commits |
| moving production during evidence | forbidden broadly | forbidden broadly | LOW | present | kept + fingerprint drift detection |
| moving execution revision | SHA recorded once | SHA recorded once | HIGH | partial | A: per-file SHA-256 baseline + re-verify pre-batch AND between cases |
| prompt/schema drift | covered by revision rule | n/a | MEDIUM | partial | fingerprint includes prompts/, schemas/; registry edit hash-pinned |
| evidence namespace collision | new dirs | copies docs/dataset early | MEDIUM | partial | CONCURRENT_EXTERNAL_OUTPUT rule + closed copy source |
| temporary artifact collision | default shared temp | default shared temp | HIGH | none | task prefixes + pytest isolation flags in both |
| concurrent output absorbed by refactor | n/a | "classify before copying" (weak) | HIGH | weak wording | hard rule: post-start files never enter mirror/map/architecture/equivalence |
| production behavior change | forbidden | mirror-only edits | MEDIUM | present | kept + final re-hash verification (B item 17) |
| private truth leakage | forbidden | boundary section | LOW | present | kept |
| post-hoc testcase modification | freeze docs | n/a | MEDIUM | present | kept + reviewer checks frozen-vs-executed |

## §15 Conclusions

**A. Can A and B currently be launched in parallel safely?**
NOT as originally submitted. Three blockers: (1) neither prompt prohibits git
mutations or use of shared fixed temp paths (`.pytest-tmp`); (2) Prompt B's
"ONE top-level handoff document" exception is an original-tree write and its
"anything created after task start must be classified before copying" wording
still allows absorbing Task A's concurrent output; (3) Prompt A had no concrete
re-verification mechanism for the production revision before/during genuine
execution (only a one-time SHA record), and no handling for the already-dirty
working tree beyond prose. With the revised prompts: yes, conditionally safe.

**B. Does Task A remain bound to the original production implementation?**
In the original: intent yes, mechanism weak. Revised: per-file SHA-256
baseline fingerprint over the production path set, re-verified immediately
before the genuine batch and between cases; drift → STOP. The pre-existing
dirty tree is handled by baseline-hashing ("no change vs own baseline", never
"clean tree"), so A cannot be tempted to stash/clean other work.

**C. Can Task B create the mirror without modifying Task A's environment?**
Yes after revision: closed single-root allowlist (`refactor_workspace/` only),
handoff doc moved inside, git prohibition including no `git init`, no
`.gitignore` edit, temp isolation, no Provider use, no shared index rebuild,
and a final re-hash of the original tree proving zero modification.

**D. Are the write namespaces genuinely disjoint?**
After revision: yes, with one documented exception — Task A's possible single
additive `prompts/agent/registry.json` edit. It is made safe by: single atomic
early write, hash-pinned in A's baseline, B freezing registry state at its
start-time inventory and treating any later diff as a known difference.

**E. Git/worktree instructions to remove or tighten?**
Neither original prompt mentioned git at all (implicit risk). Both revised
prompts add absolute prohibition lists (add/commit/stash/checkout/restore/
clean/reset/branch/switch/rebase), forbid touching pre-existing dirty files,
and replace checkpointing with hash-based revision recording. B additionally
forbids `git init` in the mirror.

**F. Does Task A demonstrate large-scale model modification rather than mostly property edits?**
Yes. C1→C5 ladder is entity-creation-heavy (Beam/Column/Door/Window + openings,
types, containment); property intents capped at 1–2 in C5; the feasibility
STOP rule (`COMPOSITE_EVIDENCE_CAPABILITY_BLOCKED`) plus "do not reduce to
property edit" clauses prevent silent substitution; §8 operation_id-bound
predicates prevent counting one Column four times; §9 exact-delta preservation
prevents bookkeeping inflation. C5-N adds the fail-closed atomic negative twin.

**G. Does Task B produce a genuinely usable refactored project?**
Yes. The mirror must be a coherent runnable project (source, tests, assets,
tools, docs, configs, fixtures) with import/registry/prompt/schema loading
checks, focused then broad offline regression inside the mirror, a behavior
equivalence report separating path changes from behavior changes, an
independent read-only parity audit with re-hash verification, and deferred
adoption (§21 no-merge). Large data/evidence are pointer-referenced, not
duplicated — keeping it usable without ballooning.

**H. What MUST be revised before launch?** (all implemented in final prompts)
1. Both: absolute git-mutation prohibition; hash-recording instead of commits.
2. Both: temp namespace prefixes + pytest cache/basetemp isolation.
3. A: concrete baseline fingerprint + re-verify pre-batch and between cases.
4. A: registry.json exception made explicit, atomic, hash-pinned.
5. A: `.planning/` read-only; no reading `refactor_workspace/`.
6. B: remove top-level handoff-doc exception; handoff inside workspace.
7. B: hard CONCURRENT_EXTERNAL_OUTPUT rule with SOURCE-INVENTORY.json.
8. B: original-tree testing limited to non-mutating checks; no full original
   suite during the parallel window; no shared index rebuild; no `.gitignore`
   edit; no `git init`.
9. B: bounded analysis granularity to prevent context explosion.
10. B: final original-tree re-hash proving zero modification.

## §13 Overreach findings and reductions

- B §2's "11 attributes for every meaningful file" over the entire repo →
  bounded to per-module depth for `src/`+`scripts/`, per-directory for
  docs/dataset/evidence (kept value, cut enumeration cost).
- B §13 nine architecture docs → kept but capped with conciseness guidance
  (tables over prose, ~≤300 lines each).
- B §16 broad regression → restricted to the mirror; original-tree runs only
  non-mutating checks during the parallel window.
- A §2 health check → explicitly scoped to the six listed operations ("do not
  re-prove every earlier Phase capability") per charter §7.
- A model diversity ("different unit system where feasible") → kept but
  subordinated: never weakens a case.
- No reductions were made that weaken correctness, freeze semantics,
  provenance, or traceability.

## §6/§7/§8/§9/§10/§11/§12 charter checks

- §6 evidence validity: freeze chain complete (models→geometry→requests→
  expected terminal class→freeze JSON with hashes); genuine-only execution;
  failures preserved; no patch-and-continue. Present in original; retained.
- §7 capability honesty: three-state classification present; STOP keyword
  present; milestone-scope sentence ADDED in revision.
- §8 B isolation: strengthened as above.
- §9 moving evidence: strengthened from "classify before copying" to hard
  exclusion + observations appendix.
- §10 refactor quality: understand-before-move chain intact
  (CURRENT-ARCHITECTURE → FILE-OWNERSHIP → EXECUTION-PATHS → PROPOSED →
  MIGRATION → DEBT → EQUIVALENCE); anti-superficial and anti-abstraction
  clauses present.
- §11 resource pressure: addressed via temp prefixes, pytest isolation,
  no shared index rebuild, reference-not-copy for large assets.
- §12 internal cross-review: both prompts carry their own independent
  subagent audits; P0/P1 reconcile loops tightened (A: fixes only within its
  allowlist; B: fixes only inside mirror, reviewer recheck).

## Final status

`PARALLEL_GOAL_PROMPTS_REVISION_REQUIRED`
