# Text2IFC Repair Milestone R1 — Final Acceptance Handoff

## 0. Persist this specification before doing any work

Before inspecting capabilities, selecting BIM models, preparing cases, or modifying any repository artifact:

1. Save this entire task specification **verbatim** to:

   `docs/handoffs/repair-milestone-r1-final-acceptance.md`

2. Do not summarize, rewrite, normalize, shorten, or restructure the specification while saving it.

3. Reopen and read the saved handoff from disk.

4. Treat that saved file as the authoritative task specification for the rest of this work.

5. All subsequent analysis, generated artifacts, testcase preparation, BIM selection, capability declarations, coverage matrices, and final reporting must be traceable back to this handoff.

6. Do not silently modify the handoff during execution.

If you discover that the specification itself needs revision:

* do not edit it;
* record the issue in the final report;
* stop at the relevant boundary if the issue prevents faithful execution;
* wait for explicit user approval before creating a revised handoff version.

The handoff is a specification artifact, not an execution log.

After saving and rereading it, proceed with the task below.

---

# Text2IFC Repair Milestone R1 — Capability Declaration, Diverse Acceptance Set, and Proof-Matrix Preparation

Treat this document as the authoritative specification for preparing the final acceptance evaluation of the current IFC repair milestone.

The current Beam + Column Stage 2 authority path has already passed its focused genuine E2E after the Stage 2 / Binder contract correction.

Do not use this task to continue feature development.

The purpose now is to define exactly what the current repair system can claim, construct a diverse genuine acceptance set for those claims, bind the predefined semantic test intents to real BIM models, and prepare the final capability/proof matrix.

The intended milestone is approximately:

`Repair Milestone R1 — IFC2X3 Bounded Semantic Repair Closed Loop`

This milestone does NOT claim universal IFC editing capability.

---

## 1. Global rules

### 1.1 Production / evaluation isolation

The production repair path must never use:

* pristine/original IFC;
* deleted GUIDs;
* mutation recipes;
* mutation ground truth;
* private Gold;
* benchmark expected answers;
* pre-existing Proof;
* hidden original values.

These may only be used by private post-repair evaluation where explicitly permitted.

BIM/model selection and testcase binding must use only public/current model evidence available to the production-side setup.

### 1.2 Do not weaken the system for the evaluation

Do not:

* add aliases;
* add fallback behavior;
* loosen schemas;
* weaken gates;
* change semantic thresholds;
* modify Stage 1/1.5 prompts to fit the cases;
* modify retrieval ranking to fit the cases;
* modify Gold after execution;
* change a testcase after seeing its result;
* replace a failed testcase with an easier one.

The evaluation must test the current system, not reshape the system around the evaluation.

### 1.3 Separate testcase semantics from BIM binding

The semantic intent of each testcase is frozen by this specification.

Codex may adapt only model-dependent facts such as:

* actual IFC file;
* Storey name / GlobalId;
* occurrence GlobalId / exact public target identity;
* safe geometry coordinates;
* dimensions when a template explicitly marks them model-dependent;
* opening/host location;
* other fixture-specific facts required to instantiate the same semantic testcase.

Codex must NOT change:

* tested capability;
* property semantic;
* positive / clarification / inadmissible / unsupported outcome class;
* Easy / Medium / Hard difficulty;
* single-operation vs multi-operation structure;
* atomicity requirement;
* required family combination;
* acceptance semantics.

For example:

`Door FireRating = true`

must not become:

`Door IsExternal = true`

just because the latter is easier.

---

# 2. First produce a formal current Capability Declaration

Before selecting BIM models or binding testcases, inspect the CURRENT repository implementation and declare the repair capabilities that are actually supported now.

Do not derive capability claims from old plans or aspirations.

Use active:

* operation registry;
* prompt profiles;
* schemas;
* resolution code;
* property authority;
* Stage 1.5 contracts;
* semantic manifest;
* Stage 2 contract;
* Binder;
* Audit;
* applicators;
* focused/current tests.

Produce:

`repair-capability-manifest.md`

and, if useful, a machine-readable equivalent.

## 2.1 Component capability table

For every currently supported repair family, record:

| Family | Operation | Supported target | Geometry / operation capability | Important constraints | Type support | Property support | Unsupported boundary |
| ------ | --------- | ---------------- | ------------------------------- | --------------------- | ------------ | ---------------- | -------------------- |

At minimum inspect:

* Beam;
* Column;
* Window;
* Door;
* Wall;
* Opening;
* occurrence property editing;

and any other operation currently registered.

Do not claim a capability merely because an IFC class exists in code.

## 2.2 System-level capability declaration

Explicitly declare whether the current implementation supports each of the following and cite the implementation path:

* deterministic target resolution;
* exact target identity;
* generated Type;
* exact existing Type reuse;
* unspecified Type reuse with clarification;
* property semantic retrieval;
* Stage 1.5 candidate selection;
* clarification;
* clarification/resume;
* unsupported-operation rejection;
* unsupported-property handling;
* invalid/incompatible property value handling;
* ExactPropertyIntent construction;
* multi-operation ChangeSet;
* cross-family multi-operation ChangeSet;
* atomic execution;
* fail-closed rollback / zero mutation;
* Binder deterministic-authority equality;
* IFC2X3 reopen;
* L0 evaluation;
* L1 evaluation;
* L2 evaluation;
* preservation / unintended-mutation evaluation;
* private-evidence isolation.

For each capability classify it as:

* `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE`
* `SUPPORTED_BUT_NOT_FINAL_ACCEPTANCE_ELIGIBLE`
* `NOT_SUPPORTED`

Give a concrete reason.

## 2.3 Property capability declaration

Inspect the current authoritative IFC2X3 property corpus and current production authorability filters.

Produce a table of representative currently authorable scalar properties for the supported families.

At minimum inspect whether the following are genuinely available and authorable:

* `LoadBearing`
* `IsExternal`
* `FireRating`
* `AcousticRating`
* `Reference`

Also identify additional useful properties if they provide value-type or semantic diversity.

For each record:

| IFC class/family | Pset | Property | Value type | Scope | Authorable now? | Suitable for acceptance? |
| ---------------- | ---- | -------- | ---------- | ----- | --------------- | ------------------------ |

Do not force a requested property into the test set if the current authority legitimately does not support it.

If one of the predefined property testcase semantics below is genuinely unsupported, report that BEFORE binding tests. Do not silently substitute another property.

---

# 3. Build the Capability Coverage Requirements

The final acceptance set should test every capability that the system intends to claim for Milestone R1.

This is capability coverage, not combinatorial exhaustive testing.

Every claimed core capability must have at least one genuine acceptance case.

High-value capabilities should appear in more than one context where reasonable.

Property semantic resolution should receive broader coverage than the previous frozen E2E matrix.

The final acceptance set should normally contain approximately:

* 4 diverse BIM models;
* 10–12 genuine cases;
* Easy / Medium / Hard levels;
* single-operation and multi-operation cases;
* successful repair;
* clarification/resume;
* deterministic value rejection/correction;
* unsupported/fail-closed behavior.

If complete capability coverage requires slightly fewer or slightly more cases, justify the difference.

Do not inflate the case count without gaining additional capability coverage.

---

# 4. Select diverse BIM models

Codex is responsible for selecting real IFC2X3 BIM files available in the current local/public datasets.

Prefer models that differ from fixtures repeatedly used during Phase 12 development.

Candidate sources may include existing local datasets such as:

* BIMNet;
* IFCBench;
* IFC-Whale;
* other public/local IFC2X3 collections already available to the repository.

Do not require one particular dataset if another model is more suitable.

## 4.1 Selection criteria

Prefer approximately four models satisfying:

1. valid IFC2X3;
2. opens successfully with IfcOpenShell;
3. contains the families required by assigned tests;
4. substantially differs in building structure, scale, element distribution, or source;
5. preferably was not a primary fixture repeatedly used during the recent Beam/Column/Window E2E development;
6. provides sufficient public evidence to bind targets;
7. allows safe model-dependent geometry placement for add operations;
8. is not selected using hidden mutation truth.

Prefer diversity such as:

* different source datasets;
* different building sizes;
* single-storey vs multi-storey where available;
* different family distributions;
* different occurrence counts;
* different existing property content.

## 4.2 Model diversity report

Produce:

`repair-acceptance-model-selection.md`

including:

| Model ID | Dataset/source | IFC schema | Storeys | Approx. relevant element counts | Assigned cases | Diversity reason | Previously heavily used? |
| -------- | -------------- | ---------- | ------- | ------------------------------- | -------------- | ---------------- | ------------------------ |

Also include IfcOpenShell reopen evidence.

Do not execute repair cases yet.

---

# 5. Bind the predefined semantic testcase templates

The testcase semantics below are predefined.

Codex should instantiate them against the selected BIM models.

Where placeholders appear, choose real model-specific values.

Do not change the capability being tested.

## EASY

### E1 — Existing Window / IsExternal

Difficulty: `Easy`

Capabilities:

* existing-occurrence target resolution;
* natural-language property intent;
* BGE-M3/Qdrant retrieval;
* Stage 1.5 selection;
* Boolean property;
* deterministic admissibility;
* occurrence property editing;
* preservation.

Semantic request template:

> 将 `<WINDOW_TARGET>` 设置为外窗。

Expected semantic target:

`Pset_WindowCommon.IsExternal = true`

Use a real existing Window.

Prefer Chinese natural-language input.

Expected terminal class:

`SUCCESS`

### E2 — Existing Door / FireRating

Difficulty: `Easy`

Capabilities:

* Door occurrence property edit;
* Chinese natural-language property retrieval;
* non-Boolean property;
* Stage 1.5;
* deterministic value typing;
* artifact preservation.

Semantic request template:

> 将 `<DOOR_TARGET>` 的防火等级设置为 `EI60`。

Expected semantic target, if supported:

`Pset_DoorCommon.FireRating = "EI60"`

Expected terminal class:

`SUCCESS`

Do not substitute another property if FireRating is unsupported.

### E3 — Existing Beam / Reference

Difficulty: `Easy`

Semantic request template:

> 将 `<BEAM_TARGET>` 的构件编号设置为 `B-204`。

Expected semantic target, if authoritative:

`Pset_BeamCommon.Reference = "B-204"`

Expected terminal class:

`SUCCESS`

### E4 — Existing Wall / AcousticRating

Difficulty: `Easy`

Semantic request template:

> 将 `<WALL_TARGET>` 的隔声等级设置为 `Rw 50`。

Expected semantic target, if authoritative:

`Pset_WallCommon.AcousticRating = "Rw 50"`

Expected terminal class:

`SUCCESS`

---

## MEDIUM

### M1 — Existing Door / FireRating with incompatible value

Difficulty: `Medium`

Semantic request template:

> 将 `<DOOR_TARGET>` 的防火等级设置为 `true`。

Expected behavior:

1. resolve FireRating first;
2. do not reinterpret it as another Boolean property;
3. deterministic validation rejects Boolean `true`;
4. request correction/clarification according to the current frozen taxonomy;
5. no IFC mutation occurs before correction.

Expected terminal class before correction:

`INADMISSIBLE_VALUE_OR_CLARIFICATION`

If supported, prepare correction:

> 改为 `EI60`。

### M2 — Beam Add + Generated Type + Reference

Difficulty: `Medium`

Semantic request template:

> 在 `<STOREY>` 添加一根新的水平直线矩形梁，中心轴从 `<BEAM_START>` 到 `<BEAM_END>`，截面宽 `<WIDTH>` mm、高 `<HEIGHT>` mm。为它创建独立的 Beam Type，并将构件编号设置为 `B-NEW-01`。

Codex may bind only model-dependent Storey, coordinates and valid dimensions.

Expected terminal class:

`SUCCESS`

### M3 — Column Add + Generated Type + LoadBearing

Difficulty: `Medium`

Semantic request template:

> 在 `<STOREY>` 添加一根新的竖直矩形柱，中心轴底点为 `<COLUMN_BASE>`，顶点为 `<COLUMN_TOP>`，截面宽 `<WIDTH>` mm、深 `<DEPTH>` mm，局部宽度方向为 `<ORIENTATION>`。为它创建独立的 Column Type，并将其设置为承重构件。

Expected semantic property:

`Pset_ColumnCommon.LoadBearing = true`

Expected terminal class:

`SUCCESS`

---

## HARD

### H1 — Cross-family Beam Add + Existing Window Property Edit

Difficulty: `Hard`

Semantic request template:

> 在 `<STOREY>` 添加一根新的水平矩形梁，中心轴从 `<BEAM_START>` 到 `<BEAM_END>`，截面尺寸为 `<WIDTH>` × `<HEIGHT>` mm，并为它创建独立 Beam Type。同时，将 `<WINDOW_TARGET>` 的防火等级设置为 `EI60`。两项修改必须在同一个原子事务中完成，全部成功才发布。

Expected terminal class:

`SUCCESS`

### H2 — Existing Door + Existing Wall, two independent properties

Difficulty: `Hard`

Semantic request template:

> 将 `<DOOR_TARGET>` 的防火等级设置为 `EI60`，同时将 `<WALL_TARGET>` 的隔声等级设置为 `Rw 50`。两项修改在同一个原子事务中执行。

Expected terminal class:

`SUCCESS`

### H3 — Natural clarification / resume

Difficulty: `Hard`

Do NOT use the artificial phrase:

`load bearing status or external status`

Find a genuine ambiguity using:

* multiple real target candidates;
* ambiguous existing Type reuse;
* or a naturally underspecified property request.

Freeze:

* initial request;
* public candidates;
* stable semantic identity of the intended answer.

Never freeze a dynamic `candidate:N` rank/token.

Expected sequence:

`clarification_required`
→ public answer
→ same lineage resume
→ successful repair

Expected terminal class:

`CLARIFICATION_THEN_SUCCESS`

### H4 — Mixed supported + unsupported atomic guard

Difficulty: `Hard`

Semantic request template:

> 在 `<STOREY>` 添加一根受支持的水平矩形梁 `<VALID_BEAM_GEOMETRY>`，并同时为该梁创建一个 structural analysis node。两项必须作为同一个事务完成。

Expected behavior:

* supported Beam operation recognized;
* structural analysis node recognized as unsupported;
* whole request terminates before mutation;
* source IFC remains unchanged.

Expected terminal class:

`UNSUPPORTED_ATOMIC_GUARD`

---

# 6. Add capability-driven cases only if required

After mapping the capability manifest to E1–H4, identify any claimed core capability that remains uncovered.

Add only the smallest number of cases necessary.

Candidate uncovered capabilities may include:

* exact existing Type reuse;
* unspecified Type reuse clarification;
* Door fill-existing-opening;
* opening-only operation;
* another registered family;
* another genuinely useful property value type.

Each additional case must explicitly name the uncovered capability that justifies it.

Target total remains approximately 10–12 cases.

---

# 7. Model-bind every testcase

For every testcase produce a bound specification containing:

* case ID;
* difficulty;
* BIM model ID/path;
* dataset/source;
* IFC schema;
* exact frozen public request;
* operation families;
* capabilities covered;
* public target identities;
* Storey;
* model-dependent geometry;
* expected terminal class;
* expected canonical property identity if applicable;
* expected value type;
* whether Stage 1.5 is expected;
* whether clarification is expected;
* whether Stage 2 is expected;
* whether IFC mutation is expected;
* whether L0/L1/L2 applies;
* preservation expectation;
* atomicity expectation.

Do not execute cases yet.

---

# 8. Build the Capability Coverage Matrix

Produce:

`repair-capability-coverage-matrix.md`

Use declared capabilities as rows and cases as columns.

Include at least:

* target resolution;
* property RAG;
* Stage 1.5;
* Boolean property;
* Label property;
* Identifier property;
* generated Type;
* exact Type reuse if claimed;
* Beam add;
* Column add;
* Window edit;
* Door edit;
* Wall edit;
* Opening operation if claimed;
* Door fill if claimed;
* multi-operation;
* cross-family operation;
* clarification;
* resume;
* invalid-value handling;
* unsupported guard;
* atomicity;
* Binder exact authority;
* IFC reopen;
* L0;
* L1;
* L2;
* preservation.

Every core `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` capability must have genuine testcase coverage.

Otherwise flag:

`CAPABILITY_COVERAGE_GAP`

---

# 9. Prepare the final Proof Matrix using the existing project convention

The project already has a prior Proof / Proof Matrix implementation and convention.

Locate and reuse it.

Do not invent a new Proof architecture.

Prepare the future matrix for the frozen cases using the existing repository schema, curation logic and evidence conventions.

At minimum the final executed Proof must capture:

* case;
* BIM model;
* difficulty;
* exact request;
* request hash;
* Stage 1;
* target resolution;
* retrieval Top-K;
* Stage 1.5;
* clarification/resume;
* admissibility;
* Type authority;
* Stage 2;
* Binder authority equality;
* semantic assignments;
* Audit;
* transaction;
* IFC apply;
* reopen;
* L0;
* L1;
* L2;
* preservation;
* zero-mutation evidence;
* Provider provenance;
* fallback status;
* private-evidence leakage status;
* final outcome.

Use explicit N/A states where execution correctly terminates before downstream stages.

---

# 10. Preserve the existing frozen four-case Phase 12.1 matrix

The original four Plan 07 cases remain separate.

They are Phase 12.1 closure evidence.

The new diverse acceptance set is Repair Milestone R1 capability/generalization evidence.

Do not overwrite, replace or rewrite the original four.

Because shared Stage 2/Binder production code changed, the later execution phase must rerun the full frozen four-case genuine matrix once on the final code version.

Do not run it during this preparation task.

---

# 11. IFCCompare planning

Identify which cases legitimately support private:

`01-original.ifc`
vs
`02-damaged.ifc`
vs
`03-repaired.ifc`

comparison.

Private pristine/mutation evidence must remain strictly post-repair evaluation only.

Do not manufacture Ground Truth for diversity cases that lack legitimate pristine repair truth.

---

# 12. Produce the freeze package

Before any genuine execution, produce:

1. `repair-capability-manifest.md`
2. `repair-acceptance-model-selection.md`
3. bound testcase specifications
4. `repair-capability-coverage-matrix.md`
5. planned Proof Matrix using the previous project convention
6. model diversity rationale
7. capability gaps
8. exact genuine execution list

Also summarize:

* BIM model count;
* testcase count;
* Easy / Medium / Hard counts;
* family coverage;
* terminal outcome coverage;
* properties covered;
* IFC value types covered;
* single vs multi-operation distribution.

---

# 13. Mandatory human freeze point

STOP after preparing the freeze package.

Do not:

* call DeepSeek;
* execute genuine E2E;
* change a testcase after Provider behavior is known;
* run final IFCCompare;
* curate final Proof results;
* close Phase 12.1;
* close Repair Milestone R1;
* begin the next Phase.

The user will review the proposed capability claims, BIM models, bound cases, expected outcomes and matrices.

Only explicit approval allows genuine execution.

---

# Final report

Return:

## A. Handoff persistence

Confirm that the authoritative specification was saved and reread from:

`docs/handoffs/repair-milestone-r1-final-acceptance.md`

## B. Current capability declaration

## C. BIM diversity selection

## D. Proposed Easy / Medium / Hard testcase set

## E. Property and value-type coverage

## F. Capability Coverage Matrix

## G. Existing Proof convention reused

## H. Freeze readiness

Finish with exactly one:

`REPAIR_MILESTONE_R1_FREEZE_READY`

or

`REPAIR_MILESTONE_R1_FREEZE_BLOCKED`
