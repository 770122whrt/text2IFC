# Phase 10 Discussion Log

**Date:** 2026-07-21
**Purpose:** Human-readable record of the decisions captured in `10-CONTEXT.md`.

## Window completion level

- L1 geometry/relationship and L2 semantic fidelity are mandatory.
- L3 authoring/identity exactness is recorded but not required.
- LargeBuilding must move from honest L1-pass/L2-non-passing evidence to a real
  offline and DeepSeek L1/L2 pass.

## Stage 2 and ChangeSet

- Rejected: sending the full semantic fact/Pset list to Stage 2.
- Selected: Stage 2 receives a compact manifest summary/reference and explicit
  user slots only.
- Selected: a deterministic Binder expands authorized facts into one final,
  self-contained bound ChangeSet; Provider output remains a draft.

## Open attributes and RAG

- The long-term model is a small structural Operation Registry plus open
  semantic slots and a property resolver, not one operation per property.
- Standard-property retrieval searches IFC2X3 knowledge first.
- Low-confidence or ambiguous results require user clarification.
- Every custom property requires explicit user confirmation.
- Knowledge-base/vector/RAG implementation is deferred to Phase 10.1 so Phase
  10 can first prove the complete Window repair pipeline.

## Scope order

1. Complete and test Window end to end in Phase 10.
2. Add and validate property RAG/custom confirmation on Window in Phase 10.1.
3. Only then expand the proven interfaces to Opening, Door, Beam, and Column.

---

*Canonical machine-consumed decisions live in `10-CONTEXT.md`.*
