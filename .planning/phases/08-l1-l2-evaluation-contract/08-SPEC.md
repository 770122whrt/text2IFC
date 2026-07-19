# Phase 8: L1/L2 Evaluation Contract - Specification

**Created:** 2026-07-19
**Ambiguity score:** 0.07 (gate: <= 0.20)
**Requirements:** 11 locked

## Goal

Every applied IFC repair receives a versioned, evidence-bearing evaluation in
which mandatory L1 geometry/relationship correctness and mandatory L2 semantic
fidelity are independently decided, privately benchmarkable, and both required
for complete repair success while L3 exactness remains non-gating.

## Background

`evaluate_repair_application` currently publishes
`text2ifc/ifc-repair-evaluation/0.1` and collapses application validity,
postconditions, preservation, and operation comparison into one boolean. The
Window comparison adapter independently verifies substantial L1 geometry and
topology, but no common level/status model or operation-owned L2 policy exists.
Direct LargeBuilding original-vs-repaired comparison proved that the current
case passes geometry/relationship checks while losing or changing instance
Psets, quantities, `IsExternal`, material, and classification semantics. The
current boolean therefore cannot represent the v1.1 definition of success.

## Requirements

1. **Versioned hierarchical report**: A new evaluation contract reports run,
   application/preservation, operation, L1, L2, L3, check, and evidence levels.
   - Current: Evaluation 0.1 exposes a run boolean, common comparison, and
     operation-specific dictionaries without formal level contracts.
   - Target: New reports have a distinct schema version and deterministic
     hierarchy while 0.1 reports remain readable without reinterpretation.
   - Acceptance: JSON Schema validation accepts a complete new report, rejects
     missing required hierarchy/status/evidence, and a compatibility test reads
     a frozen 0.1 fixture without treating it as the new version.

2. **Five-state level semantics**: Every level/check uses `passed`, `failed`,
   `partial`, `not_required`, or `not_evaluable` with a reason and evidence.
   - Current: Most checks are booleans and unavailable facts cannot be
     distinguished from failure or omission.
   - Target: Unknown, inapplicable, incomplete, and failed outcomes are
     distinct machine states; no unavailable fact is silently passed.
   - Acceptance: Parameterized tests exercise all five states and reject an
     unknown state or a state lacking its required reason/evidence.

3. **Strict success aggregation**: Complete success requires application
   success and `passed` L1/L2 for every mandatory operation.
   - Current: One boolean mixes application, preservation, and the existing
     Window comparison adapter; there is no L2 gate.
   - Target: `partial`, `not_evaluable`, or `failed` mandatory L1/L2 makes the
     run unsuccessful; `not_required` is allowed only by explicit policy.
   - Acceptance: A truth-table test proves that L1 pass/L2 failure, L1 pass/L2
     partial, and L1 pass/L2 not-evaluable all yield incomplete repair, while
     application pass plus required L1/L2 pass yields complete success.

4. **Independent L1 scope and preservation**: L1 validates physical result,
   topology, containment, scope, preservation, readability, and tolerances
   independently from the authoring path.
   - Current: The comparator uses Applicator-reported changed IDs as the
     complete allowed-change set and Window-specific checks cover only one
     operation.
   - Target: Allowed effects cross-check Registry capability, ChangeSet scope,
     and actual IFC changes; unexpected changes and missing/duplicate relations
     are structured failures.
   - Acceptance: Controlled fixtures prove expected Window geometry passes,
     while one undeclared wall drift, extra relationship, missing relation,
     duplicate chain, containment mismatch, and tolerance violation each fail
     the corresponding L1 check.

5. **Operation-owned L2 policy**: Each supported operation supplies a
   versioned policy of `required`, `conditional`, and `informational` semantic
   checks through the common registry/evaluator contract.
   - Current: `OperationDefinition` has application/comparison adapters but no
     common L2 allowlist or applicability contract.
   - Target: Window is the first concrete policy; a fixture operation proves a
     later family can register policy without modifying common aggregation.
   - Acceptance: Registry tests reject missing/duplicate policy IDs and prove
     both Window and a fixture operation dispatch through the same evaluator.

6. **Evidence-triggered semantic requirements**: Material, Classification,
   Psets, quantities, and instance semantics become mandatory when authorized
   evidence establishes their presence or requested value.
   - Current: Repaired Window may omit original instance semantics while the
     current evaluation still succeeds.
   - Target: Private original facts in benchmark mode, explicit request facts,
     surviving current IFC facts, or compatible approved Prototype/Type facts
     activate the corresponding conditional check; repaired IFC must contain a
     matching typed value/Pset/association.
   - Acceptance: For each source kind, a present fact plus missing/mismatched
     repaired fact fails L2 and a matching repaired fact passes; when no source
     establishes the fact, the check is `not_required`.

7. **Production evidence authority**: Production evaluation uses only public,
   provenance-bound facts and discloses mandatory facts it cannot evaluate.
   - Current: There is no formal production L2 evidence resolver or source
     precedence.
   - Target: Precedence is explicit request, surviving target/Host/Type facts,
     compatible approved Prototype/Type, then deterministic policy; arbitrary
     neighbors, names, and model knowledge are forbidden sources.
   - Acceptance: Tests prove source precedence, incompatible Prototype
     rejection, neighbor-copy rejection, per-fact provenance, and
     `not_evaluable` for a mandatory fact with no reliable source.

8. **Private benchmark evaluator**: Synthetic benchmark evaluation may compare
   repaired IFC with private original Ground Truth without exposing Gold to any
   Provider/public stage.
   - Current: Direct original-vs-repaired analysis exists as documentation but
     not as an isolated machine evaluator contract.
   - Target: Private original IFC and mutation role mapping enter only the
     evaluator after application and support semantic equivalence without
     requiring original GUID reuse.
   - Acceptance: A benchmark fixture resolves recreated roles through the
     private mapping and detects known L2 differences; an artifact-flow test
     proves Provider input, TargetQuery, public context, and ChangeSet contain
     no private original values or IDs.

9. **Private/public report separation**: Benchmark evaluation produces a
   detailed private report and a non-leaking public projection.
   - Current: The evidence workflow has one evaluation report and no Gold-aware
     projection boundary.
   - Target: Private evidence may contain original values; public evidence
     contains statuses, difference categories, safe provenance, and remediation
     needs but not Gold-only values/IDs.
   - Acceptance: A secret/canary fixture appears in the private report, is
     absent from every public/Provider artifact, and the public report still
     exposes the correct failed L2 category.

10. **L3 and diagnostic artifact semantics**: L3 observations and non-passing
    repaired candidates remain auditable without becoming successful outputs.
    - Current: L3 has no machine level, and publication semantics are inferred
      from the aggregate boolean.
    - Target: L3 is `not_required` for v1.1; failed/partial/not-evaluable runs
      may retain an immutable diagnostic IFC/evidence directory but terminal
      success is false and the report marks it non-publishable as success.
    - Acceptance: Tests show L3 differences do not change a passing L1/L2 run,
      while every non-passing L1/L2 state sets success false and
      `successful_artifact_publishable` false without deleting diagnostic data.

11. **LargeBuilding honest baseline**: The current frozen Window repair is
    evaluated as L1-correct but not L2-complete under the new contract.
    - Current: The same case is accepted by evaluation 0.1 despite documented
      Pset/quantity, `IsExternal`, material, and classification differences.
    - Target: Benchmark evaluation reports L1 `passed`, L2 non-passing with the
      verified difference categories, L3 `not_required`, and complete success
      false; no Provider call is needed.
    - Acceptance: A deterministic LargeBuilding test reproduces those statuses
      and categories from frozen artifacts or a controlled equivalent fixture,
      with Provider calls fixed at zero.

## Boundaries

**In scope:**

- New versioned L1/L2/L3 evaluation schema and immutable domain model.
- Deterministic run/operation/check aggregation and compatibility reading of
  existing evaluation 0.1 artifacts.
- Independent common L1 scope/preservation checks plus Window L1 integration.
- Operation-owned L2 policy registry with Window as the first concrete policy.
- Production evidence selection with typed values and provenance.
- Benchmark-private original/manifest comparison and public report projection.
- Diagnostic artifact/publication status contract.
- Controlled fixtures and LargeBuilding offline acceptance for VAL-01..VAL-05.

**Out of scope:**

- Natural-language-to-TargetQuery and general repair orchestration - Phase 9.
- Restoring missing Window Psets, quantities, Material, Classification, or
  `IsExternal` in the Applicator - Phase 10 uses this evaluator to drive fixes.
- Real Provider calls - Phase 8 is deterministic and Provider-independent.
- Concrete Door, Opening-only, Beam, or Column semantic authoring/policies -
  later operation phases; only registry extensibility fixtures are needed now.
- L3 identity/authoring exact restoration or compatibility claims - explicitly
  excluded from v1.1.
- Scale/performance and 128k context experiments - Phase 13.

## Constraints

- IFC schema remains IFC2X3 and outputs are reopened through IfcOpenShell.
- Ground Truth and private mutation mappings are evaluator-only and cannot
  cross into Provider/public artifacts.
- Evaluation is deterministic, JSON-Schema-backed, source-hash-bound, and
  operation-policy-versioned.
- No missing semantic value may be invented from nearby entities or LLM/BIM
  common knowledge.
- Existing Window L1 behavior and Phase 7 index/evidence contracts must remain
  backward compatible.
- Phase implementation follows TDD; no new external service or Provider
  dependency is allowed.

## Acceptance Criteria

- [ ] New hierarchical evaluation reports validate against their exact schema
  version and frozen 0.1 artifacts remain readable.
- [ ] All five statuses have tested semantics, reason, and evidence contracts.
- [ ] Strict aggregation truth table requires mandatory L1 and L2 to pass.
- [ ] L1 independently detects scope, preservation, geometry, topology,
  containment, duplicate-chain, and tolerance failures.
- [ ] Window and a fixture operation register evaluation policies through the
  same common registry boundary.
- [ ] Material/Pset/Classification checks activate when authorized evidence is
  present and become `not_required` when no such evidence exists.
- [ ] Production evidence precedence and prohibited inference sources are
  enforced with per-fact provenance.
- [ ] Benchmark Gold is consumed only after application by the private
  evaluator and is absent from all public/Provider artifacts.
- [ ] Public benchmark reports preserve useful categories/statuses without
  leaking Gold-only values or identifiers.
- [ ] L3 remains `not_required`; diagnostic IFCs may be retained but cannot be
  marked publishable as successful.
- [ ] LargeBuilding/current equivalent evaluation reports L1 pass, honest L2
  gaps, complete success false, and zero Provider calls.
- [ ] Full `tests/ifc_repair` regression and `compileall` pass.

## Ambiguity Report

| Dimension | Score | Min | Status | Notes |
|---|---:|---:|---|---|
| Goal Clarity | 0.95 | 0.75 | met | Required L1/L2 success outcome is explicit. |
| Boundary Clarity | 0.95 | 0.70 | met | Phase 9/10/later operations and L3 are separated. |
| Constraint Clarity | 0.90 | 0.65 | met | Evidence precedence, privacy, compatibility, and determinism are locked. |
| Acceptance Criteria | 0.90 | 0.70 | met | Eleven falsifiable requirements and twelve final gates. |
| **Ambiguity** | **0.07** | **<= 0.20** | **met** | Weighted clarity 0.93. |

## Interview Log

| Round | Perspective | Question summary | Decision locked |
|---|---|---|---|
| 1 | Researcher | Is the current roadmap enough, and what gaps exist in evaluation 0.1? | A new hierarchical evaluation contract and operation-owned L2 policy are required. |
| 2 | Simplifier | What is the irreducible Phase 8 result? | Deterministic schema, strict L1/L2 gate, two evidence modes, and Window first policy. |
| 3 | Boundary Keeper | Does Phase 8 fix Window semantics or orchestrate the full repair? | No; Phase 9 orchestrates and Phase 10 restores Window semantics. |
| 4 | Failure Analyst | How are unknown facts, self-reported changes, and Gold leakage prevented? | Five states, three-way L1 scope, evidence provenance, and private/public reports. |
| 5 | Seed Closer | When are Material and Psets mandatory? | Authorized evidence activates mandatory L2 checks; no evidence means `not_required`. |

---

*Phase: 08-l1-l2-evaluation-contract*
*Spec created: 2026-07-19*
*Next step: $gsd-plan-phase 8 - executable implementation planning*
