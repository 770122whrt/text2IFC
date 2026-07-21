# Phase 10: Window L2 Semantic Fidelity Closure - Specification

**Created:** 2026-07-21
**Ambiguity score:** 0.05 (gate: <= 0.20)
**Requirements:** 10 locked
**Roadmap requirements:** WIN-01, WIN-02

## Goal

Given an existing or damaged IFC2X3 file and a natural-language Window request,
the public repair pipeline produces one audit-bound ChangeSet, deterministically
authors the Window and its required semantics, and publishes an IFC only when
both Production L1 and L2 pass; the LargeBuilding case must also pass private
benchmark L2 and real DeepSeek UAT.

## Background

Phases 7-09.1 already provide an IFC2X3 SQLite index, target and Type
resolution, two bounded Agent stages, resumable clarification, a unified
ChangeSet transaction, Evaluation 0.2, and fail-closed publication. The current
LargeBuilding repair reaches the evaluator and passes L1, but remains
non-publishable because the new `IfcWindow` does not have complete Production
authority or authoring for Base Quantities, Classification, Material, selected
occurrence Psets, and several required Window facts. The existing Window policy
also names `Qto_WindowBaseQuantities.*` while the IFC2X3 source exposes
`BaseQuantities.*`, and declares an abstract `instance:*` category with no
concrete extraction contract. Phase 10 closes these gaps before any RAG or
additional entity-family expansion begins.

## Requirements

1. **Window semantic authoring contract**: Window repair has a versioned,
   operation-scoped contract for every semantic fact that may be authored.
   - Current: Geometry parameters exist in the operation schema, while semantic
     facts are evaluated separately and are not an explicit compiler input.
   - Target: A typed Window authoring manifest records fact key, value, IFC
     value type, unit, occurrence-versus-Type ownership, source reference,
     provenance, applicability, and authoring action for each authorized fact.
   - Acceptance: Schema/model tests accept a complete manifest, reject missing
     provenance or an unsupported fact kind, and reject facts whose source is
     private Ground Truth, Provider invention, or an unauthorized neighbor.

2. **Compact Provider boundary and one bound ChangeSet**: Stage 2 uses an
   immutable semantic-manifest reference rather than receiving or reproducing
   the full semantic fact list.
   - Current: ChangeSet 0.1 carries geometry only; sending every Pset to Stage 2
     would make the Provider responsible for deterministic IFC fact copying.
   - Target: Stage 2 receives a bounded summary, manifest reference/hash, and
     only explicit user semantic slots; a deterministic Binder expands the
     manifest into the sole executable and auditable bound ChangeSet.
   - Acceptance: Prompt-capture tests prove the full assignment list and Gold
     are absent from Stage 2 input, while the bound ChangeSet contains every
     authored assignment and rejects stale hash, altered value, foreign
     operation reference, and Provider-added semantic fact.

3. **Versioned Window L2 policy**: A new policy version defines concrete Window
   L2 facts without reinterpreting historical policy/evidence.
   - Current: Policy 0.1 expects `Qto_WindowBaseQuantities.*` and an undefined
     `instance:*` fact family.
   - Target: Policy 0.2 normalizes IFC2X3 `BaseQuantities` and
     `Qto_WindowBaseQuantities` into one semantic quantity role, replaces the
     abstract instance wildcard with concrete facts, and preserves policy 0.1
     artifacts as historical evidence.
   - Acceptance: Frozen 0.1 evidence remains readable; parameterized tests show
     both quantity-set spellings resolve to the same 0.2 checks and no 0.2
     check depends on an unextractable `instance:*` key.

4. **Required core Window semantics**: Every supported Window operation authors
   and validates compatible Type, exact Host, Storey, `OverallWidth`,
   `OverallHeight`, `Pset_WindowCommon.IsExternal`, and normalized Window Base
   Quantities.
   - Current: Type and Storey relationships plus width/height attributes may be
     present, but Production expectations and occurrence semantics are
     incomplete and L2 remains non-passing.
   - Target: Required facts are derived from the request, resolved target,
     formal containment, approved Type, compatible surviving facts, and
     deterministic policy with per-fact provenance.
   - Acceptance: Reopened IFC tests extract matching facts from the new Window;
     removing or changing any required fact makes the corresponding L2 check
     non-passing and prevents publication.

5. **Conditional Pset, Material, and Classification semantics**: Authorized
   conditional semantics are restored; verified absence remains
   `not_required`.
   - Current: LargeBuilding's repaired Window has no Material or Classification
     association and does not restore selected occurrence Window Psets.
   - Target: Formal surviving relationships, approved Type facts, compatible
     same-Type evidence under Window policy, and explicit user facts may
     activate conditional authoring. Existing Material and Classification
     resources are reused through deterministic relationships. Type-owned
     Psets remain Type-owned instead of being duplicated onto the occurrence.
   - Acceptance: Fixtures cover matching, missing, conflicting, and absent
     authority for Pset/Material/Classification; matching authority passes,
     missing/mismatch fails, conflict blocks, and verified absence is
     `not_required`.

6. **Deterministic and atomic IFC authoring**: Semantic authoring is part of the
   same all-or-nothing Window transaction as geometry and relationships.
   - Current: The Window applicator creates the core Opening/Window chain but
     has no generic semantic-assignment application stage.
   - Target: The applicator writes attributes, occurrence Psets, quantities,
     Material and Classification associations only from the audited bound
     ChangeSet, reopens the result, and rolls back the entire operation on any
     failed precondition, authoring step, postcondition, or reopen check.
   - Acceptance: Transaction tests inject failures at each semantic authoring
     category and prove the source IFC is unchanged, no partial successful IFC
     is published, and diagnostic evidence names the failing assignment.

7. **Production authority remains Gold-free**: Production L2 facts are
   resolved solely from the request, current IFC, authorized Type/Prototype,
   formal relationships, and deterministic operation policy.
   - Current: The public/private boundary exists, but Phase 10 introduces new
     authoring evidence and relationship reuse paths that could leak Gold or
     copy arbitrary neighbors if left unconstrained.
   - Target: Every authored fact has an allowed public source; cohort-based
     evidence is operation-policy-scoped, compatible, conflict-checked, and
     never promoted to Type ownership. Ground Truth remains benchmark-only
     after production application completes.
   - Acceptance: Signature and canary tests prove original IFC and private
     mutation mapping cannot enter manifest, prompts, ChangeSet, production
     evaluation, or public artifacts; unauthorized similarity and conflicting
     cohorts cannot authorize a value.

8. **Strict publication and diagnostic behavior**: The public API/CLI publishes
   a successful IFC only after application, reopen, L1, and L2 all pass.
   - Current: Phase 9 already enforces this rule and retains the current Window
     result as a non-publishable diagnostic candidate.
   - Target: Phase 10 preserves the same terminal state machine while adding
     semantic-manifest and bound-ChangeSet artifacts; failures remain resumable
     or diagnostic and cannot be relabelled as successful.
   - Acceptance: A terminal truth-table test covers application/reopen/L1/L2
     failures and proves only the all-pass row exposes `successful_ifc` and
     `successful_artifact_publishable=true`.

9. **LargeBuilding offline full-chain acceptance**: The existing single-Window
   LargeBuilding mutation completes the public IFC-plus-text pipeline without
   Provider or Gold shortcuts.
   - Current: The offline path performs Stage 1, target/Type resolution, Stage
     2, application, and evaluation but ends L1 passed/L2 non-passing.
   - Target: The same damaged IFC and natural-language request produce a bound
     ChangeSet, repaired IFC, Production L1/L2 pass, and private benchmark L1/L2
     pass; Ground Truth enters only the post-application benchmark adapter.
   - Acceptance: A deterministic integration test runs from damaged IFC plus
     text, asserts both Agent stages were exercised, asserts Production and
     benchmark L1/L2 `passed`, and compares the reopened IFC's frozen Window
     semantic allowlist with the original.

10. **Real DeepSeek Window UAT**: The supported Window pipeline succeeds with
    the configured real Provider and retains honest failure evidence.
    - Current: Four Phase 09.1 DeepSeek paths reach Stage 2 and L2 but correctly
      remain non-publishable because semantic authoring is missing.
    - Target: The complete-request, clarification-completed, Type-name, and
      dimension-plus-Type-confirmation paths all reach one bound ChangeSet,
      produce an IFC, and pass Production L1/L2. Provider/network/schema
      failures remain recorded failures and are never rewritten as success.
    - Acceptance: The opt-in live UAT reports contract pass and L1/L2 pass for
      all four paths, writes real Provider traces, publishes successful IFCs,
      and separately preserves any failed attempt with its original status.

## Boundaries

**In scope:**

- Window-only semantic authoring manifest and deterministic binding contract.
- Versioned bound ChangeSet capable of carrying complete typed semantic
  assignments without putting the full list in a Provider prompt.
- Window L2 policy 0.2 and historical 0.1 compatibility.
- Required Window Host/Storey/Type/dimension/IsExternal/quantity authoring.
- Conditional selected Pset, Material, and Classification authoring from
  authorized non-Gold evidence.
- Atomic IFC2X3 application, reopen, L1/L2, publication, and diagnostics.
- LargeBuilding offline Production/benchmark acceptance and real DeepSeek UAT.
- Operation-registry interfaces that later families can implement without
  adding family branches to common orchestration.

**Out of scope:**

- IFC2X3 property knowledge-base ingestion, embeddings, vector database,
  hybrid RAG, confidence calibration, and unknown/custom-property
  clarification - deferred to Phase 10.1 after the Window pipeline is proven.
- Automatic creation of a previously unknown custom Pset - Phase 10.1 requires
  explicit user confirmation for every custom property.
- Door, opening-only, Beam, and Column authoring - Phases 11/12 consume the
  proven extension interfaces only after Phase 10/10.1 acceptance.
- Automatic similarity/vector authorization of a Type or Prototype - remains
  forbidden; explicit/formal authorization is required.
- Curved, segmented, or free-form wall mutation - deferred beyond the current
  straight-wall capability.
- L3 GlobalId, STEP ID, exact placement/representation, serialization, or
  byte-identical reconstruction - explicitly non-gating.
- 128k Provider input - retained for the dedicated later scale experiment.

## Constraints

- IFC schema remains IFC2X3 and every candidate/output is reopened with
  IfcOpenShell before evaluation or publication.
- Stage 1 and Stage 2 remain bounded by the current 65,536-token configuration;
  the full semantic assignment list is not sent to either Provider stage.
- One run owns one unified, all-or-nothing bound ChangeSet.
- Missing facts are never invented from LLM knowledge, an arbitrary neighbor,
  or private Ground Truth.
- Explicit user facts outrank lower authorities only when the registered Window
  contract permits an occurrence override; incompatible Type-defining facts
  require clarification or fail closed.
- Type-owned facts remain Type-owned; direct occurrence facts are never
  promoted to `TypeRecord` through voting, ignore lists, or LLM judgment.
- Name, Tag, Mark, original GUIDs, and exporter-specific identity are not L2
  requirements unless explicitly requested; exact restoration remains L3.
- New behavioral work follows RED/GREEN/REFACTOR where the behavior has stable
  inputs and outputs.

## Acceptance Criteria

- [ ] Window semantic manifests and bound ChangeSets validate against exact
  schema versions and reject unauthorized/private facts.
- [ ] Stage 2 prompt captures contain only the manifest reference/summary and
  explicit user slots, never the expanded semantic list or Ground Truth.
- [ ] Policy 0.2 accepts normalized IFC2X3 Base Quantities and contains no
  undefined `instance:*` success gate; policy 0.1 evidence remains readable.
- [ ] Reopened repaired Windows contain matching Type, Host, Storey,
  OverallWidth/Height, IsExternal, and required Base Quantities.
- [ ] Authorized selected Psets, Material, and Classification are present and
  L2-equivalent; verified absence is `not_required`.
- [ ] A semantic authoring failure rolls back atomically and cannot expose a
  successful IFC artifact.
- [ ] Production artifacts and Provider prompts pass private-Gold canary scans.
- [ ] LargeBuilding damaged-IFC-plus-text offline integration passes Production
  L1/L2 and private benchmark L1/L2.
- [ ] All four configured real DeepSeek Window UAT paths pass L1/L2 and publish
  successful IFCs, or retain honest provider/application failure evidence.
- [ ] Full `tests/ifc_repair`, provider compatibility tests, `compileall`, and
  `git diff --check` pass.

## Ambiguity Report

| Dimension | Score | Min | Status | Notes |
|---|---:|---:|---|---|
| Goal Clarity | 0.97 | 0.75 | met | Complete Window pipeline and publish gate are explicit. |
| Boundary Clarity | 0.96 | 0.70 | met | RAG, later families, L3, curved walls, and 128k are separated. |
| Constraint Clarity | 0.92 | 0.65 | met | IFC2X3, Gold boundary, bounded prompts, atomic ChangeSet, and authority rules are locked. |
| Acceptance Criteria | 0.93 | 0.70 | met | Offline, benchmark, live UAT, negative, and regression gates are falsifiable. |
| **Ambiguity** | **0.05** | **<= 0.20** | **met** | Ready for planning. |

## Interview Log

| Round | Perspective | Question summary | Decision locked |
|---|---|---|---|
| 1 | Researcher | What prevents Phase 9 publication? | L1 works; genuine Window semantic authoring and Production authority are missing. |
| 2 | Simplifier | What is the minimum useful Phase 10? | Prove one complete Window IFC+text-to-published-IFC chain before expanding scope. |
| 3 | Boundary Keeper | Should RAG and unknown attributes be included now? | No; property knowledge/vector retrieval becomes Phase 10.1 after the core pipeline passes. |
| 4 | Failure Analyst | What must never be treated as success? | Missing/conflicting authority, Gold leakage, Provider-added facts, partial application, or non-passing L1/L2. |
| 5 | Seed Closer | What evidence proves completion? | LargeBuilding offline Production+benchmark L1/L2 and four real DeepSeek paths. |

---

*Phase: 10-window-l2-semantic-fidelity-closure*
*Spec created: 2026-07-21*
*Next step: execute the Phase 10 plans after review*
