---
phase: 10-window-l2-semantic-fidelity-closure
plan: 02
status: complete
completed: 2026-07-21
commits:
  - c334b946
  - ea885357
---

# Plan 10-02 Summary

Implemented IFC index 0.3 association evidence and a single Gold-free semantic
authority result shared by authoring and Production L2.

- Material and Classification associations now round-trip with relationship,
  resource, occurrence, Type, inheritance, and STEP/GUID provenance.
- Same-Type occurrence evidence is isolated as `authorized_type_cohort`; only
  policy-allowlisted direct facts may enter it, and conflicting values fail with
  `AUTHORIZED_TYPE_COHORT_CONFLICT`.
- `build_semantic_manifest` deterministically projects the selected Production
  facts into typed, operation-scoped authoring assignments.
- Registry exposes an operation-neutral manifest-builder hook. Orchestration
  constructs and hashes the public manifest before application.
- Private original, mutation mapping, similarity, embedding, and Provider facts
  remain outside the builder signature.

Verification: 63 focused tests passed using an isolated pytest temp root;
compileall and `git diff --check` passed. The repository's shared `.pytest-tmp`
was locked by another process, so it was not deleted or reused.
