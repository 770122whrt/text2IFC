---
phase: 12
slug: beam-and-column-operations
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-03
---

# Phase 12 - Validation Strategy

> Per-phase validation contract for Beam/Column TDD feedback, offline closure,
> real DeepSeek UAT and independent Proof acceptance.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest on the project `.venv`; deterministic IFC2X3 fixtures plus checked-in BIMNet scenes |
| **Config file** | `pyproject.toml` and existing `tests/ifc_repair/conftest.py` infrastructure |
| **Quick run command** | `.\.venv\Scripts\python.exe -m pytest <task-specific test files> -q` |
| **Changed-surface command** | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair -q` |
| **Compile command** | `.\.venv\Scripts\python.exe -m compileall -q src tests scripts` |
| **Full pre-live command** | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair -q` followed by compile and `git diff --check` |
| **Estimated runtime** | focused task: 15-180 seconds; complete IFC repair suite: approximately 18-20 minutes |

Real DeepSeek calls are not a normal automated feedback command. They run
once, after every offline blocking gate is green, and their published output
is independently reopened and recomputed.

---

## Quality Claims

Phase 12 must prove seven claims independently:

1. **Routing:** Stage 1 selects registered Beam/Column operation profiles and
   Stage 2 loads no unrelated full profile or few-shot.
2. **Authority:** exact public/derived evidence authorizes every target,
   Storey, Type, material, property and geometric fact.
3. **IFC authoring:** straight rectangular Beam/Column geometry, placement,
   containment and Type relationships survive IFC2X3 serialization/reopen.
4. **Atomicity:** single and mixed ChangeSets publish all requested operations
   once or publish nothing.
5. **Structural fidelity:** reopened products pass strict L0/L1/L2 with
   explicit axis, direction, section, relationship and semantic evidence.
6. **Preservation and isolation:** unrelated model content is preserved and
   private original/mutation Gold cannot influence production.
7. **Provider viability:** real DeepSeek completes one structural request and
   one clarification/resume path with `synthetic_fallback_used: false`.

No aggregate `success=true` field is sufficient. Publication and curated Proof
acceptance require all applicable blocking claims.

---

## Sampling Rate

- **After every TDD red/green task:** run that task's focused command.
- **After every implementation plan:** run its focused suite plus the named
  historical regression files.
- **Before real DeepSeek UAT:** complete `tests/ifc_repair` suite, compile and
  `git diff --check` must be green.
- **After live publication:** run the independent Phase 12 Proof validator in
  a separate invocation over the accepted artifact directory.
- **Maximum focused feedback latency:** 180 seconds.
- **Full repair regression budget:** 1,500 seconds; a timeout is reported as a
  timeout, never as a pass.

No watch-mode command is permitted.

---

## Per-Task Verification Map

The planner must preserve these task identifiers or update this table before
execution. `W0` means the task creates the named test first under TDD.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure behavior | Test type | Automated command | File exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | OPS-03, OPS-04 | T12-01, T12-02 | only selected full structural profiles reach Stage 2; noncanonical fields fail | unit | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_structural_prompt_profiles.py tests/ifc_repair/test_operation_prompt_profiles.py tests/ifc_repair/test_selected_provider_profiles.py -q` | W0 | pending |
| 12-01-02 | 01 | 1 | OPS-03, OPS-04 | T12-03 | Beam/Column occurrence and Type facts round-trip without becoming authority | unit/integration | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_structural_index.py tests/ifc_repair/test_indexer.py tests/ifc_repair/test_index_store.py -q` | W0 | pending |
| 12-01-03 | 01 | 1 | OPS-03, OPS-04 | T12-04 | property retrieval requires exact typed value authority and supported scope | unit | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_structural_property_authoring.py tests/ifc_repair/test_occurrence_property_operation.py tests/ifc_repair/test_property_binding_security.py -q` | W0 | pending |
| 12-02-01 | 02 | 2 | OPS-03, OPS-04 | T12-05 | generated structural Type derivation/class/hash are compiler-owned | unit | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_structural_type_authoring.py tests/ifc_repair/test_generated_type_authority.py -q` | W0 | pending |
| 12-02-02 | 02 | 2 | OPS-03, OPS-04 | T12-06 | reopened straight-member axes and rectangular sections equal authorized inputs | unit/integration | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_structural_geometry.py -q` | W0 | pending |
| 12-02-03 | 02 | 2 | OPS-03, OPS-04 | T12-07 | exact Type is unchanged; generated Type cannot invent material/Pset facts | integration | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_structural_type_authoring.py tests/ifc_repair/test_property_authoring.py tests/ifc_repair/test_apply_transaction.py -q` | W0 | pending |
| 12-03-01 | 03 | 3 | OPS-03 | T12-01, T12-08 | Beam missing/ambiguous facts clarify; complete facts create one valid Beam | integration | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_beam_resolution.py tests/ifc_repair/test_beam_application.py -q` | W0 | pending |
| 12-03-02 | 03 | 3 | OPS-04 | T12-01, T12-08 | Column missing/ambiguous facts clarify; base-Storey policy creates one valid Column | integration | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_column_resolution.py tests/ifc_repair/test_column_application.py -q` | W0 | pending |
| 12-03-03 | 03 | 3 | OPS-03, OPS-04 | T12-09 | mixed structural application and semantic assignments publish all or none | integration | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_structural_atomicity.py tests/ifc_repair/test_apply_transaction.py -q` | W0 | pending |
| 12-04-01 | 04 | 4 | OPS-03, OPS-04 | T12-10 | deterministic damage keeps original/mapping private from production | integration/security | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_structural_mutation.py tests/ifc_repair/test_phase12_ground_truth_isolation.py -q` | W0 | pending |
| 12-04-02 | 04 | 4 | OPS-03, OPS-04 | T12-11 | reopened L0/L1/L2 uses exact axis/section/cardinality/semantic checks | integration | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_structural_evaluation.py tests/ifc_repair/test_evaluation_policy.py tests/ifc_repair/test_requested_property_l2.py -q` | W0 | pending |
| 12-04-03 | 04 | 4 | OPS-03, OPS-04 | T12-12, T12-13 | d7n/vvo offline artifacts pass preservation and independent strict validation | dataset E2E | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_phase12_dataset_e2e.py tests/ifc_repair/test_phase12_success_cases.py tests/ifc_repair/test_success_case_collection.py -q` | W0 | pending |
| 12-05-01 | 05 | 5 | OPS-03, OPS-04 | T12-02, T12-14 | live runner exposes actual calls/retries and forbids synthetic/cached fallback | integration | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_phase12_live_uat.py -q` | W0 | pending |
| 12-05-02 | 05 | 5 | OPS-03, OPS-04 | T12-11, T12-12 | live IFC and manifest are independently reopened, hashed and recomputed | live + independent | `.\.venv\Scripts\python.exe scripts/ifc_repair/validate_success_cases.py --help` plus the Phase 12 strict-validator command frozen by Plan 04 | existing/evolved | pending |
| 12-05-03 | 05 | 5 | OPS-03, OPS-04 | all | complete regression and curated report match raw evidence | regression/report | `.\.venv\Scripts\python.exe -m pytest tests/ifc_repair -q` | existing | pending |

*Status: pending - green - red - flaky*

---

## Wave 0 Requirements

Existing pytest infrastructure is sufficient. Each implementation task must
create or extend its test file before production code.

- [ ] `tests/ifc_repair/test_structural_prompt_profiles.py`
- [ ] `tests/ifc_repair/test_structural_index.py`
- [ ] `tests/ifc_repair/test_structural_property_authoring.py`
- [ ] `tests/ifc_repair/test_structural_type_authoring.py`
- [ ] `tests/ifc_repair/test_structural_geometry.py`
- [ ] `tests/ifc_repair/test_beam_resolution.py`
- [ ] `tests/ifc_repair/test_beam_application.py`
- [ ] `tests/ifc_repair/test_column_resolution.py`
- [ ] `tests/ifc_repair/test_column_application.py`
- [ ] `tests/ifc_repair/test_structural_atomicity.py`
- [ ] `tests/ifc_repair/test_structural_mutation.py`
- [ ] `tests/ifc_repair/test_phase12_ground_truth_isolation.py`
- [ ] `tests/ifc_repair/test_structural_evaluation.py`
- [ ] `tests/ifc_repair/test_phase12_dataset_e2e.py`
- [ ] `tests/ifc_repair/test_phase12_success_cases.py`
- [ ] `tests/ifc_repair/test_phase12_live_uat.py`

No dependency installation or new test framework is required.

---

## Contract and Routing Matrix

| Case | Expected blocking result |
|------|--------------------------|
| Stage 1 classifies Beam add | exactly the Beam operation/profile selected |
| Stage 1 classifies Column add | exactly the Column operation/profile selected |
| one Beam + one Column request | both compact routes, then only two full selected profiles |
| unrelated Door/Window request | no structural full profile/few-shot in Stage 2 |
| profile hash/path/operation mismatch | fail closed before Provider execution |
| Provider emits a documented noncanonical structural key | schema/contract failure; no compatibility alias |
| missing axis/base/top/section/Storey fact | one grouped clarification, no Stage 2 publication |
| no Type-reuse intent | dedicated deterministic matching structural Type |
| explicit Type resolves zero or multiple candidates | clarification, no mutation |
| exact Type conflicts with requested family/section/map | clarification or rejection; Type unchanged |
| no material request and no authorized inherited Type material | no material authored |
| optional Pset omitted | no clarification and no invented Pset |
| vector recall has plausible value but no exact typed source fact | discovery only; cannot authorize value |

---

## Structural Geometry and Relationship Matrix

| Operation | Required topology and geometry |
|-----------|--------------------------------|
| Beam add | one `IfcBeam`; straight center axis; rectangular section; one body representation; exact requested Storey containment; exactly one `IfcRelDefinesByType` |
| Column add | one `IfcColumn`; base-to-top center axis; rectangular section; one body representation; base-Storey containment under frozen policy; exactly one `IfcRelDefinesByType` |
| mixed Beam+Column | both occurrences and semantic assignments in one bound ChangeSet and one publication |

For every reopened product:

- correct IFC occurrence class;
- one local placement chain rooted in the authorized spatial structure;
- one compatible body representation;
- no duplicate deterministic GlobalId;
- no unauthorized existing Root removal or modification;
- exact material/Pset relationship only when authorized.

---

## L0/L1/L2 Acceptance

### L0

- output exists and parses as IFC2X3;
- expected product count and classes are exact;
- containment and Type relationships exist exactly once;
- all postconditions and publication state are successful;
- injected failure creates no published IFC.

### L1

- Beam start/end or Column base/top deviation: at most 5 mm per point;
- member direction or horizontal/vertical tilt deviation: at most 0.1 degrees;
- rectangular width/height and any explicitly requested member dimension:
  at most 1 mm;
- containment and Type relationship cardinality: exact;
- values are measured from reopened IFC geometry/placement;
- approximate volume, mesh bounds or visual resemblance are diagnostic only.

### L2

- exact or generated structural Type binding and derivation;
- exact Type fingerprint unchanged after reuse;
- requested/inherited material follows the frozen authorization rules;
- requested Pset/quantity names, data types, scopes and values are exact;
- optional omitted semantics remain absent;
- global preservation and private-Gold isolation pass.

---

## Atomicity and Failure Injection

Required failures:

1. second structural operation has an ambiguous Storey;
2. exact Type identity becomes stale after resolution;
3. exact Type section or representation map conflicts with request;
4. generated Type derivation hash/class is tampered;
5. semantic assignment has an unsupported value type or scope;
6. second operation applicator or postcondition is injected to fail;
7. strict L1 endpoint/section check is injected to mismatch;
8. preservation detects one undeclared Root mutation;
9. independent Proof validator sees a stale hash or missing artifact.

Each case must prove:

- `published=false`;
- no publishable output path exists;
- source/damaged IFC SHA-256 is unchanged;
- no partial case is copied into accepted Proof;
- terminal reason identifies the first stable blocking layer.

---

## Dataset Acceptance

### `d7n.ifc` primary

- frozen inventory reports 10 Beams and 15 Columns;
- at least one Beam and one Column deterministic damage/repair path;
- one mixed Beam+Column ChangeSet;
- exact Type/containment/property facts and strict reopened L0/L1/L2;
- private original/mutation mapping unavailable to production;
- unrelated source identities, relationships, geometry and semantics preserved.

### `vvo.ifc` secondary

- frozen inventory reports six Beams and five Columns;
- proves compatibility with horizontal swept Beam and mapped Column evidence;
- material-present and material-absent policies both covered;
- same-family source limitation stated honestly in the report.

The accepted report must not claim cross-dataset generalization.

---

## Real DeepSeek UAT

The live gate starts only after all offline layers and the full repair
regression pass.

Required cases:

1. **Complete:** one public request creates both a Beam and a Column in one
   atomic ChangeSet and publishes a reopened IFC2X3 result.
2. **Clarification/resume:** one incomplete structural request produces one
   grouped public clarification, accepts the bounded answer and then completes.
3. **Program guard:** one unsupported/conflicting request is rejected at its
   deterministic boundary without an unauthorized mutation.

Raw evidence must include:

- redacted request/response transport;
- Provider/model/token/attempt metadata;
- actual Stage 1 and Stage 2 call counts;
- rendered prompt and selected profile/few-shot IDs, versions and hashes;
- RepairIntent, clarification state/answer and resolved operations;
- semantic manifests and bound ChangeSet;
- application, reopen, L0/L1/L2/preservation results;
- terminal publication status/reason;
- explicit `synthetic_fallback_used: false`.

Synthetic, cached, prerecorded or hand-authored Provider output cannot
substitute for this gate. Schema correction retries remain visible.

---

## Independent Proof Validation

The validator must distrust runner summaries and recompute from bound
artifacts:

- manifest completeness and every SHA-256;
- IFC existence, schema and reopen;
- exact requested product and relationship counts;
- world-space axis/base/top, direction and rectangular dimensions;
- requested material/Pset/quantity semantics;
- Type identity/derivation and exact-reuse fingerprint;
- atomic publication, preservation and private-Gold isolation;
- Provider evidence mode and absence of fallback.

The final report distinguishes:

- live strict structural cases;
- offline strict structural cases;
- historical Window/Door cases retained under their declared schemas;
- any legacy artifact that cannot be independently recomputed.

---

## Threat References

| Ref | Threat |
|-----|--------|
| T12-01 | family/action or operation profile misrouting |
| T12-02 | unrelated full profile/few-shot prompt leakage |
| T12-03 | derived index/similarity evidence promoted to authority |
| T12-04 | RAG property suggestion invents a value or scope |
| T12-05 | generated Type template/class/hash tampering |
| T12-06 | bounding-box/volume proxy hides wrong axis or section |
| T12-07 | exact shared Type is mutated or occurrence facts copied |
| T12-08 | missing structural fact is inferred instead of clarified |
| T12-09 | mixed ChangeSet partially publishes |
| T12-10 | private original/mutation Gold leaks into production |
| T12-11 | aggregate success flag masks failed strict gate |
| T12-12 | Proof artifact is missing, stale or edited |
| T12-13 | same-family scenes are reported as cross-dataset evidence |
| T12-14 | synthetic/cached output substitutes for real Provider UAT |

---

## Manual-Only Verifications

All product and evidence claims are automated. Human review is limited to
confirming that the final narrative matches machine evidence and does not
overclaim the dataset scope; this review cannot turn a failed automated gate
green.

---

## Validation Sign-Off

- [ ] All plan tasks have focused automated verification or a Wave 0 test
      created first.
- [ ] No three consecutive tasks lack an automated command.
- [ ] Every Wave 0 file is created by its owning TDD task.
- [ ] No watch-mode flag exists.
- [ ] Focused feedback latency is at most 180 seconds.
- [ ] OPS-03 and OPS-04 trace through plans, tests and Proof.
- [ ] Offline gates precede the real DeepSeek gate.
- [ ] Independent Proof validation distrusts runner aggregate success.
- [ ] `nyquist_compliant: true` is set after the final plan/task map is
      reconciled.

**Approval:** pending plan-checker convergence
