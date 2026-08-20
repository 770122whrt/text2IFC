# Phase 12 Type Intent Correction — Frozen Contract

**Created:** 2026-08-20  
**Status:** FROZEN after user approval of Option A  
**Applies to:** Phase 12 Plan 12-15 retry and Plan 12-16 closeout  
**Authority:** This document supplements `12-SPEC.md`, `12-VALIDATION.md`,
`12-STAGE1-SCOPE-CORRECTION-SPEC.md`, and `12-15A-PLAN.md`. It may only make
the Beam/Column Type-intent boundary more explicit. Any conflict is a hard stop
for user discussion.

## 1. Trigger and retained evidence

The genuine DeepSeek run
`dataset/processed/ifc-repair-runs/phase12-live/uat-20260818T133409954828Z`
passed its zero-skip offline preflight. Its clarification/resume and
structural-analysis guard cases passed, but its complete Beam/Column case did
not publish. Stage 1 represented the request to **generate dedicated structural
Types** as two `prototype_intent.reference_kind == "selection_required"`
claims. Deterministic resolution correctly treated those claims as requests to
reuse existing Types and stopped with `missing_evidence` before Stage 2.

That run remains append-only failed live evidence. It is not relabelled,
overwritten, curated, or counted as success. A later pass of the same case may
prove only that this frozen bug is fixed and that the Phase 12 acceptance path
is viable; it is not a class-level capability-improvement claim.

## 2. Root cause and invariant

The RepairIntent 0.6 schema allowed the three existing representation states,
but neither the Stage 1 prompt nor its compact Beam/Column profiles stated the
semantic distinction between generating a new Type and reusing an existing
Type plainly enough. The full Stage 2 few-shots did state that generated Type
identity is program-derived, but Stage 1 correctly does not load those
few-shots. Stage 2 therefore cannot repair the wrong Stage 1 Type intent.

The frozen invariant is:

> `prototype_intent` describes only an explicitly requested reuse of an
> existing IFC Type. A request to create, generate, dedicate, or otherwise
> produce a new Type is not prototype reuse and must leave
> `prototype_intent` null so deterministic code can create the Type.

No runtime synonym map, alias normalizer, Provider-output rewrite, or observed
response special case may enforce this invariant.

## 3. Exact three-state contract

For `add_beam` and `add_column`, Stage 1 emits exactly one of these states:

1. **No Type instruction, or new/generated/dedicated Type requested**
   - `prototype_intent` is exactly `null`.
   - Deterministic resolution issues the registered generated-Type authority,
     identity, label, and relationship.
2. **Exact existing Type identity requested**
   - `prototype_intent.reference_kind` is exactly `global_id` or `type_name`.
   - `reference` contains only the exact public identity supplied by the user.
   - Deterministic resolution must bind that existing Type or fail closed.
3. **Reuse of an existing Type requested without exact identity**
   - `prototype_intent.reference_kind` is exactly `selection_required`.
   - Resolution searches the bounded public Type catalog for the registered
     Beam/Column Type classes.
   - If one or more public candidates exist, the run enters
     `prototype_selection` clarification and accepts only a returned candidate
     token through the existing authorization path.
   - If no public candidate exists, the run terminates with
     `missing_evidence`.

Option A is frozen: zero-candidate selection does **not** add a free-form
clarification answer, does not accept a newly supplied Type name or GlobalId on
resume, and does not silently fall back to generated Type creation.

## 4. Append-only prompt and profile versions

Add, without modifying registered historical artifacts:

- `text2ifc/ifc-repair-intent-body/0.7`;
- `text2ifc/ifc-repair-intent/0.7`;
- prompt template `ifc-repair-intent.v0.7`;
- prompt-profile schema `text2ifc/ifc-repair-prompt-profile/0.2`;
- profiles `beam.add.v0.3` and `column.add.v0.3`;
- profile-bound v0.3 Stage 2 few-shots and prompt-registry records.

RepairIntent 0.7 retains the 0.6 JSON shape and unsupported-request behavior;
only its contract identity and prompt binding advance. The new profile schema
adds an explicit compact `type_intent_rules` object so Stage 1 receives the
three-state rule without receiving full Stage 2 few-shots. Existing RepairIntent
0.1–0.6 prompts/schemas and Beam/Column profile 0.1–0.2 files remain historical
contracts.

The production `RepairAPI`, Beam/Column operation definitions, Phase 12 live
runner, curator, and independent validator move to the new exact versions.
Historical tests may explicitly request older versions.

## 5. Frozen Stage boundaries

- Stage 1 remains one Provider call over the public request, exact RepairIntent
  0.7 schema, and compact registered operation projections.
- Stage 1 receives `type_intent_rules` but no Beam/Column full profile document
  and no Stage 2 few-shot body.
- Deterministic completeness, capability, target, Type, property, and semantic
  resolution remain between the stages.
- Stage 2 alone receives the selected full v0.3 profiles and their selected
  few-shots. It produces only the bound ChangeSet draft.
- The existing clarification/resume and structural-analysis guard contracts do
  not change.

## 6. Failure family and acceptance seams

RED tests must freeze independent expected literals for:

- Beam/Column with no Type instruction -> `prototype_intent: null`;
- Beam/Column requesting a new, generated, or dedicated Type -> null;
- the failed live mixed Beam+Column phrase "generate dedicated structural
  Types" -> both null and successful deterministic generated-Type authority;
- exact Type name and exact GlobalId reuse -> exact reference kinds;
- unspecified existing-Type reuse with candidates -> bounded
  `prototype_selection` clarification;
- unspecified existing-Type reuse without candidates -> `missing_evidence`;
- incorrect `selection_required` for a generated-Type request remains an
  invalid semantic Provider result for the purpose of prompt/failure-family
  evidence; production code does not rewrite it;
- Stage 1 prompt contains the exact three states and compact v0.3 rules but no
  selected few-shot body;
- Stage 2 loads only the selected v0.3 full profiles/few-shots;
- Door/Window prompt/profile behavior and earlier RepairIntent versions remain
  unchanged.

The relevant public seams are `generate_repair_intent`, deterministic
resolution, and `RepairAPI.start / continue_with_answer`. Tests must not derive
their expected values from implementation constants under test.

## 7. Validation and retry policy

Before another real DeepSeek call, the new failure family, Stage 1 seam,
selected-profile Stage 2 seam, public complete/clarification/guard chains,
Phase 12 offline matrix, applicable Door/Window regressions, compile check,
diff check, independent Proof validator, and the live runner's zero-skip
preflight must pass. No failure, skip, substitution, timeout, mock, cached,
prerecorded, hand-authored, or synthetic result authorizes a live call.

A new timestamped run must use natural-language user requests through the
public `RepairAPI.start / continue_with_answer` path and the approved DeepSeek
transport. If it exposes another prompt/schema/contract defect, stop before a
retry or Proof curation and discuss it with the user.

Only a run whose complete and clarification/resume cases publish and reopen as
IFC2X3, whose guard remains Stage1=1/Stage2=0 with exact source immutability,
and whose independently reopened artifacts pass strict L0/L1/L2,
preservation, private-Gold isolation, provenance, and IFC comparison may enter
the accepted Phase 12 Proof.

## 8. Non-goals and Git boundary

This correction does not implement structural analysis, add a Stage call,
load Stage 2 few-shots into Stage 1, add aliases, normalize malformed Provider
output, redesign Door/Window operations, change geometry thresholds, weaken
Type/material/Storey/private-Gold policy, start Phase 13, or mix dataset/PDF/
documentation-organization work into Phase 12 checkpoints.

