# Phase 8: L1/L2 Evaluation Contract - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-07-19
**Phase:** 08-l1-l2-evaluation-contract
**Areas discussed:** success aggregation, report hierarchy, L1 authority, L2 policy, production evidence, benchmark privacy, failed artifacts, phase boundary

---

## Success aggregation and hierarchy

| Option | Description | Selected |
|---|---|---|
| Strict mandatory L1/L2 | Only `passed` satisfies a mandatory level; `partial`, `not_evaluable`, and `failed` prevent complete success | Yes |
| Lenient unknown handling | Permit partial or unknown semantic facts to count as success | No |
| Flat boolean report | Retain only one run-level boolean | No |
| Hierarchical report | Run and per-operation L1/L2/L3 checks with evidence | Yes |

**User's choice:** Recommended strict aggregation and operation-level hierarchy accepted.

## L1 authority

| Option | Description | Selected |
|---|---|---|
| Trust Applicator report | Treat self-reported changed IDs as the allowed scope | No |
| Three-way authority | Cross-check Registry capability, ChangeSet scope, and actual IFC changes | Yes |

**User's choice:** Three-way independent validation accepted.

## L2 semantic policy

| Option | Description | Selected |
|---|---|---|
| All Material/Classification always required | Missing source evidence produces universal failure | No |
| All semantic associations optional | Never gate repair success | No |
| Evidence-triggered conditional requirement | If original/request/surviving facts/approved Prototype establish it, repaired IFC must reproduce and L2 must verify it | Yes |

**User's choice:** Recommended policy accepted with explicit clarification that
existing Material/Pset content makes the corresponding repaired semantic fact
mandatory; when no Material evidence exists it is not a required check.

## Production evidence and benchmark privacy

| Option | Description | Selected |
|---|---|---|
| Allow heuristic neighboring-element copying | Infer missing values from nearby model entities | No |
| Provenance-bound evidence precedence | Request, surviving facts, approved Prototype, deterministic policy only | Yes |
| Single benchmark report | Public report may contain original Gold values | No |
| Private detailed plus public projection | Gold stays evaluator-only and public evidence is non-leaking | Yes |

**User's choice:** Recommended provenance and report-isolation design accepted.

## Failed artifacts and scope boundary

| Option | Description | Selected |
|---|---|---|
| Delete every non-passing artifact | Remove repaired candidate even from diagnostics | No |
| Preserve diagnostic candidate | Keep immutable evidence but never publish it as successful | Yes |
| Fix Window L2 in Phase 8 | Expand phase into semantic authoring | No |
| Contract plus first Window policy | Define evaluator now; semantic restoration remains Phase 10 | Yes |

**User's choice:** All recommended boundaries accepted.

## the agent's Discretion

- Internal module/class layout and exact new schema minor version.
- Normalized evidence serialization details that preserve the locked contract.

## Deferred Ideas

- Phase 9 general orchestration and artifact-publication enforcement.
- Phase 10 Window semantic restoration.
- Later Door/Opening/Beam/Column policies and L3 authoring exactness.
