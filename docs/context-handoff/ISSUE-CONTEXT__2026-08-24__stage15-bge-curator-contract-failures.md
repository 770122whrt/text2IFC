# Issue Context: Stage 1.5 BGE, Live Transcript, and Curator Contract Failures

**Created:** 2026-08-24  
**Last updated:** 2026-08-24  
**Status:** Partially resolved; Plan 12.1-06 blocked on Gold-independent R12 Candidate evidence
**Scope:** Phase 12.1 Plan 06 investigation/correction only; no genuine DeepSeek call, Proof curation, final IFCCompare or Plan 07

## 1. Problem Statement

A focused Phase 12 contract run reported `108 passed / 3 failed`. The failures
touch the alias-free Stage 1.5 property path and the live Proof curator:

1. the production-path live-executor test stops at `BGE_M3_UNAVAILABLE` instead
   of publishing the Beam/Column repair;
2. two curator tests reject a mocked successful validator payload because it
   does not contain `property_authority_coverage` and
   `current_property_acceptance_eligible`.

The question is not merely how to turn the tests green. An external reviewer
must determine which parts are stale fixtures, production integration defects,
contract/specification drift, test-architecture defects, runtime/environment
dependencies, or another cause. Reintroducing alias authority is explicitly not
an admissible resolution.

## 2. Current Observed Failure

### Fresh focused reproduction

**Confirmed Repository Fact:** On 2026-08-24 the three known failing tests were
rerun without network access:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/ifc_repair/test_phase12_live_uat.py::test_complete_transport_drives_the_real_repair_api_and_reopens_ifc2x3 `
  tests/ifc_repair/test_phase12_success_cases.py::test_public_curate_installs_only_two_strict_success_cases_after_validation `
  tests/ifc_repair/test_phase12_success_cases.py::test_public_curate_resolves_the_latest_timestamped_runner_directory `
  -q -p no:cacheprovider `
  --basetemp=.tmp-issue-context-stage15-20260824
```

Result:

```text
3 failed in 101.79s (0:01:41)
```

This narrow rerun confirms the same three failures but does not reproduce the
full `108 passed / 3 failed` denominator. The earlier focused two-file run was:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/ifc_repair/test_phase12_live_uat.py `
  tests/ifc_repair/test_phase12_success_cases.py `
  -q --basetemp=.tmp-phase12-1-live-proof-contract-regression
```

and reported `108 passed, 3 failed in 282.19s`.

### Failure A: real RepairAPI path stops before Stage 1.5 Provider transport

The assertion at `tests/ifc_repair/test_phase12_live_uat.py:817` expected
`status == "succeeded"`. The actual result was:

```text
status = clarification_required
reason_code = BGE_M3_UNAVAILABLE
clarification.reason_code = property_resolution
clarification.question = Property retrieval is unavailable for this request.
```

The fresh durable state is retained at:

```text
.tmp-issue-context-stage15-20260824/
  test_complete_transport_drives0/complete/runtime/runs/
  repair-16f0ca40896947f6a5a714454d78f8ba/state.json
```

It reached `intent_ready`, persisted the natural-language Beam property query,
then transitioned to `clarification_required` with
`BGE_M3_UNAVAILABLE`. The Provider mock was never asked to handle Stage 1.5.

### Failures B and C: curator rejects mocked validator output

Both failures raise:

```text
ValueError: LIVE_CANDIDATE_VALIDATION_FAILED
```

The mocked validator returns exit code `0`, `status == "passed"`, two recomputed
live cases, and no errors. The curator now additionally requires every case to
contain:

```text
property_authority_coverage in {
  "strict_stage_1_5_recomputed",
  "not_applicable"
}
current_property_acceptance_eligible is True
```

The shared test fixture `_strict_validator_payload()` does not emit either
field.

## 3. Runtime and Data Flow

The frozen natural-language property flow is:

```text
Live UAT runner
  -> TranscriptProvider
  -> RepairAPI
  -> Stage 1 intent extraction
  -> alias-free eligibility + BGE-M3/Qdrant Top-K
  -> Stage 1.5 Provider decision (ifc_property_resolution)
  -> deterministic admissibility
  -> program-constructed ExactPropertyIntent
  -> Stage 2 bound ChangeSet
  -> apply / reopen / validation / publication

Persisted successful case
  -> independent validator replays current Stage 1.5 evidence
  -> validator emits per-case authority eligibility
  -> curator admits exactly the required live cases
```

The current first failure occurs at the BGE-M3/Qdrant retrieval-runtime step.
However, repository inspection shows additional failures would occur after that
step because the live transcript wrapper and mock transport have not yet been
updated for `ifc_property_resolution`.

## 4. Authoritative Contract

### Alias retirement and runtime readiness

**User/Project Decision:** Phase 12.1 SPEC R1 and VALIDATION prohibit reviewed
aliases from active API/runners/current Proof replay. Historical alias artifacts
may remain only as history or an explicitly isolated evaluation baseline.

**User/Project Decision:** SPEC R4 requires the production path to prepare or
reuse a versioned alias-free BGE-M3/Qdrant collection, expose health, and block
natural-language resolution if vector evidence is unavailable or stale
(`12.1-SPEC.md:86-98`).

**User/Project Decision:** Fail-closed `BGE_M3_UNAVAILABLE` behavior is therefore
contract-conforming for a genuinely unavailable production runtime. Falling
back to the prior reviewed-alias resolver would violate the frozen contract.

### Separate Stage 1.5 and live evidence

**User/Project Decision:** Stage 1.5 is a separate bounded Provider call, not a
Stage 1 or Stage 2 compatibility mode. The live run must record exact Stage 1,
property-resolution, and Stage 2 call/attempt counts
(`12.1-VALIDATION.md:137-154`; `12.1-SPEC.md:209-222`).

**User/Project Decision:** The Stage 1.5 prompt identity is
`ifc-property-resolution.v0.1`, and its execution evidence is a template
identity, not an operation prompt-profile identity
(`property_resolution_stage.py:28`, `:494-527`).

### Current Proof authority

**User/Project Decision:** Every current property claim must retain query,
candidate set, rendered prompt and Provider attempt, parsed Stage 1.5 decision,
admissibility, program-constructed exact intent, and authored IFC fact. Missing
evidence or `REVIEWED_ALIAS_EXACT` makes a case current-ineligible; the validator
must not call a Provider or legacy alias resolver
(`12.1-VALIDATION.md:80-101`; `12.1-SPEC.md:224-239`).

### Required live matrix

**User/Project Decision:** The frozen live matrix includes:

1. Beam + Column complete with natural-language `load bearing=true`;
2. property clarification/resume at Stage 1.5;
3. Window `外窗=true` semantic canary through Vector + Stage 1.5;
4. unsupported program guard before property/Stage 2 mutation.

The current runner's default case matrix does not yet implement items 2 and 3.

## 5. Production Implementation Evidence

### 5.1 Alias-free runtime switch is present only in the dirty candidate

**Confirmed Repository Fact:** The worktree diff changes
`_production_case_executor()` from:

```python
property_knowledge_resolver=create_default_property_resolver()
```

to:

```python
property_knowledge_runtime=create_default_property_runtime()
```

at `scripts/ifc_repair/run_phase12_live_uat.py:920-925`.

This change is directionally required by the frozen alias-retirement contract.
At HEAD, before the dirty change, the runner still used the reviewed-alias
resolver.

### 5.2 Default runtime has a real local BGE/Qdrant dependency

**Confirmed Repository Fact:** `create_default_property_runtime()` defaults to:

- model ID/path `BAAI/bge-m3`;
- `local_files_only=True`;
- local Qdrant storage at `.cache/property-resolution/qdrant` when no URL/path is
  supplied;
- `runtime_mode="production"`.

Provider/model construction exceptions become `BGE_M3_UNAVAILABLE`; Qdrant
construction exceptions become `QDRANT_UNAVAILABLE`
(`property_runtime.py:244-349`). The runtime does not silently use aliases.

**Confirmed Repository Fact:** Dedicated runtime seam tests already cover the
distinct BGE and Qdrant unavailable reasons
(`tests/knowledge/test_property_vector_runtime.py:361-393`).

### 5.3 Live transcript wrapper does not recognize Stage 1.5

**Confirmed Repository Fact:** Stage 1.5 sends
`state["stage"] == "ifc_property_resolution"`
(`property_resolution_stage.py:105-124`).

**Confirmed Repository Fact:** `TranscriptProvider._stage_name()` recognizes
only strings containing `intent` and `changeset`; all other stages raise
`LIVE_TRANSCRIPT_STAGE_UNSUPPORTED`
(`run_phase12_live_uat.py:355-361`).

This defect is currently masked by the earlier BGE failure.

### 5.4 Live call counts omit property resolution

**Confirmed Repository Fact:** `_counts()` initializes only `stage1` and
`stage2`, and `_case_contract_pass()` checks only those keys
(`run_phase12_live_uat.py:991-997`, `:1056-1115`). This conflicts with the
frozen Stage 1/property-resolution/Stage 2 evidence requirement.

### 5.5 Live attempt identity validation assumes operation profiles

**Confirmed Repository Fact:** `_prompt_identities()` extracts only
`profile_id`, `profile_version`, `profile_hash`, and few-shot identities from
the rendered prompt. `_live_attempt_evidence_pass()` requires nonempty profile
IDs/versions/hashes for every attempt (`run_phase12_live_uat.py:315-345`,
`:1000-1053`).

**Confirmed Repository Fact:** Stage 1.5 persists `template_id` and
`template_hash`, not operation profile identities
(`property_resolution_stage.py:494-527`, `:570-575`). Its prompt contains no
operation-profile identity block. Therefore a correctly recorded Stage 1.5
attempt would still fail the current general live-attempt evidence predicate.

### 5.6 Transcript wrapping breaks Stage 1.5 live-eligibility typing

**Confirmed Repository Fact:** The runner creates a real
`OpenAICompatibleLiveProvider`, wraps it in `TranscriptProvider`, and passes the
wrapper into `RepairAPI` (`run_phase12_live_uat.py:1278-1299`, `:1467-1475`).

**Confirmed Repository Fact:** Stage 1.5 marks evidence live-eligible only when
the provider object it receives is directly an `OpenAICompatibleLiveProvider`
using the default SDK client, or a supported `MimoAgentProvider`
(`property_resolution_stage.py:476-491`). A `TranscriptProvider` wrapper is
classified as `injected_offline`, even if it returned a genuine live transport
result. No explicit wrapper-delegation contract currently bridges this.

This defect is also masked by the BGE failure and the unsupported transcript
stage name.

### 5.7 Current live matrix is still the pre-12.1 matrix

**Confirmed Repository Fact:** `DEFAULT_CASES` currently contains only:

- Beam/Column complete with load-bearing claims;
- a geometry-completeness Column clarification/resume;
- unsupported structural-analysis program guard.

There is no Window `外窗` case. The clarification request has no natural-language
property claim and therefore is not the frozen Stage 1.5 property clarification
case (`run_phase12_live_uat.py:95-148`).

### 5.8 Validator and curator current-property fields are dirty additions

**Confirmed Repository Fact:** The dirty validator recomputes current Stage 1.5
evidence and emits:

- `property_authority_coverage`:
  `strict_stage_1_5_recomputed`, `historical_property_artifact_only`, or
  `not_applicable`;
- `property_claim_count`;
- `property_reason_codes`;
- `historical_alias_present`;
- `current_property_acceptance_eligible`.

The positive current path emits `current_property_acceptance_eligible=True`;
historical property artifacts emit `False`
(`validate_success_cases.py:1417-1500`, `:1560-1589`).

**Confirmed Repository Fact:** The dirty curator now consumes two of those
fields at `curate_phase12_live_proof.py:1005-1020`.

**Confirmed Repository Fact:** The validator output still declares
`text2ifc/ifc-repair-proof-validation/0.1`. Repository search found no separate
JSON Schema for this report; the producer, consumer, and test fake currently
form an implicit Python-level interface.

## 6. Current Test Expectation

### Live-executor test

**Confirmed Repository Fact:** `_ProductionPathTransport` says it mocks only
the external Provider transport and exercises the real API. It supports only:

```text
ifc_repair_intent
ifc_repair_bound_changeset
```

and raises `AssertionError(stage)` for any other stage
(`test_phase12_live_uat.py:224-251`).

**Confirmed Repository Fact:** The complete test expects exactly:

```python
[item["stage"] for item in provider.attempts] == ["stage1", "stage2"]
```

at `test_phase12_live_uat.py:833-836`. It has no Stage 1.5 response fixture,
template-identity expectation, or property-resolution call count.

**Confirmed Repository Fact:** The test has no seam for injecting a controlled
alias-free runtime into `_production_case_executor`; the executor constructs the
production default BGE/Qdrant runtime internally. Consequently this nominally
offline mock-transport test is environment-sensitive and takes about 102
seconds in the current failing environment.

### Curator tests

**Confirmed Repository Fact:** `_strict_validator_payload()` uses validation
report version `0.1` and emits only provider mode and live transcript status per
case (`test_phase12_success_cases.py:1484-1509`). It omits both newly required
property-authority fields.

**Confirmed Repository Fact:** The two failing curator tests mock the entire
validator subprocess by returning that fixture. They do not execute
`validate_success_cases.py`, so they test the curator/validator response
interface rather than proof recomputation itself.

## 7. Three-Way Comparison

| Concern | Frozen contract | Current production/worktree | Current test expectation | Assessment |
|---|---|---|---|---|
| Alias authority | No active alias resolver/fallback | Dirty live runner switches to alias-free runtime; `RepairAPI` rejects alias-bearing resolver | Complete live test was authored for the old alias-backed two-stage path | Test is stale on this boundary; reverting production would violate contract |
| Vector unavailable | Fail closed and record health | Returns `BGE_M3_UNAVAILABLE` | Expects success without preparing/injecting a ready alias-free runtime | Runtime dependency plus test-architecture mismatch |
| Stage 1.5 Provider call | Separate bounded call | Property stage emits `ifc_property_resolution` | Mock transport supports Stage 1 and Stage 2 only | Stale/incomplete mock fixture |
| Transcript routing | Record Stage 1/1.5/2 | Wrapper rejects `ifc_property_resolution` | Expects only Stage 1/2 | Confirmed production integration defect and stale test expectation |
| Attempt counts | Exact Stage 1/property-resolution/Stage 2 counts | Counter has Stage 1/2 only | Expects Stage 1/2 only | Confirmed implementation/test drift from SPEC |
| Prompt identity | Stage 1.5 immutable template ID/hash | Stage 1.5 persists template identity; general live gate requires profiles | No Stage 1.5 identity assertion | Confirmed production evidence-gate mismatch; test gap |
| Live eligibility | Genuine default SDK transport must remain provable through Stage 1.5 | Wrapper causes Stage 1.5 type check to classify it offline | Mocked transport is not designed to exercise this distinction | Confirmed production wrapper/evidence mismatch; not reached by current failure |
| Live matrix | Complete, property clarification, Window canary, guard | Current default matrix has complete, geometry clarification, guard | Tests freeze current three-case matrix | Confirmed SPEC/runner/test drift; Plan 06 is incomplete |
| Proof current-property authority | Current Stage 1.5 evidence must be recomputed; aliases ineligible | Dirty validator emits coverage/eligibility; dirty curator requires them | Mock validator fixture omits both | Fixture is stale relative to dirty producer/consumer |
| Proof report interface | Semantics are frozen; machine fields should be independently judgeable | New fields added under report version `0.1`, with no separate schema found | Fixture also claims version `0.1` with older shape | Contract-interface ambiguity; reviewer must decide version/schema policy |
| Required curated cases | Both required Phase 12.1 success cases are property cases under frozen matrix | Curator accepts `not_applicable` for either required case | Fixture supplies no coverage at all | Potential acceptance looseness beyond the immediate fixture failure |

## 8. Fixtures, Mocks, and Runtime Dependencies

### REAL

- `RepairAPI`, durable run store, IFC indexing, resolution, apply/reopen path in
  the failing live-executor test.
- The worktree's `create_default_property_runtime()` construction.
- The local source/damaged IFC used by `_production_case_executor`.
- Curator staging/install logic up to its independent-validator gate.

### MOCKED

- External Provider transport in `_ProductionPathTransport`.
- Entire validator subprocess result in the two curator tests.
- Provider outputs for Stage 1 and Stage 2 in the live-executor test.

### PATCHED

- No BGE provider, vector index, property runtime, or Stage 1.5 Provider seam is
  patched in the failing live-executor test.
- The curator tests replace `validator_runner` through the public injection seam;
  they do not monkeypatch validator internals.

### EXTERNAL / ENVIRONMENT-DEPENDENT

- Locally available `BAAI/bge-m3` SentenceTransformer assets because the
  production constructor uses `local_files_only=True`.
- Torch/SentenceTransformers native runtime readiness.
- Qdrant client and local collection storage/version readiness.
- Genuine DeepSeek HTTPS/default-SDK transport for later live acceptance; it is
  not used by these tests.

### NOT COVERED BY THESE THREE TESTS

- A real ready BGE-M3/Qdrant production lifecycle.
- Stage 1.5 transport through `TranscriptProvider` (blocked earlier by BGE).
- Stage 1.5 live acceptance eligibility through the wrapper.
- Stage-aware template identity acceptance in the live runner.
- Frozen property clarification/resume and Window semantic-canary live cases.
- Actual independent validator execution in the two curator tests.
- Genuine DeepSeek, IFCCompare, or accepted Proof curation.

### Existing controlled alias-free test seam

**Confirmed Repository Fact:** Other tests already construct an alias-free
`PropertyKnowledgeRuntime` using authoritative IFC2X3 records,
`InMemoryVectorIndex`, and deterministic fixture embeddings, with
`runtime_mode="offline_test"` (for example
`test_property_vector_runtime.py:100-115` and
`test_property_resolution_family_e2e.py:128-151`). This proves that a
hermetic, alias-free offline full-chain seam is technically available without
turning the old alias resolver back on.

## 9. Git and Change History

**Confirmed Repository Fact:** At investigation time:

```text
branch: codex/workflow-dataset-links
HEAD:   46c4173803adf91176a37e5ea85d8512d6ea8cd9
```

The worktree is intentionally dirty and contains unrelated PDF, dataset,
documentation, generated-run, temporary, and user changes. None were reset,
cleaned, or modified during this investigation.

**Confirmed Repository Fact:** Phase 12.1 is formally 5/7 complete. Plan 06 is
pending; three partial Plan 06 commits exist and more candidate work is dirty.
There is no `12.1-06-SUMMARY.md`. The project context pack explicitly warns not
to treat this worktree as accepted Plan 06 evidence.

Relevant current diffs:

```text
M scripts/ifc_repair/curate_phase12_live_proof.py       +3/-0
M scripts/ifc_repair/run_phase12_live_uat.py            +3/-3
M scripts/ifc_repair/validate_success_cases.py         +352/-15
M src/text2ifc_ifc_repair/api.py                        +5/-0
  tests/ifc_repair/test_phase12_live_uat.py              unchanged
  tests/ifc_repair/test_phase12_success_cases.py         unchanged
```

The unmodified tests are being run against uncommitted producer/consumer
changes. That is evidence of fixture lag, but it does not negate the independent
production integration defects listed above.

Material partial commits:

- `b65b5c67` — frozen 60-case property evaluation fixture/evaluator;
- `b320de41` — alias-free retrieval evaluation/policy integration and partial
  runner wiring;
- `46c41738` — five-family alias-retirement E2E and amended Phase 12.1
  contracts/plans.

## 10. Confirmed Facts

1. The three focused failures reproduce on 2026-08-24 without network access.
2. The live-executor failure is a persisted fail-closed
   `BGE_M3_UNAVAILABLE`, not an LLM output or Stage 2 authoring failure.
3. The frozen contract requires alias-free BGE-M3/Qdrant readiness for natural
   property claims.
4. Reverting the runner to the reviewed-alias resolver is contract-invalid.
5. The live-executor test does not prepare or inject a controlled alias-free
   runtime.
6. Its Provider transport has no Stage 1.5 response branch.
7. Its attempt assertion explicitly expects Stage 1 followed directly by Stage
   2.
8. The production transcript wrapper rejects the actual Stage 1.5 stage name.
9. The production live counter has no property-resolution bucket.
10. The production live-attempt gate requires operation profile identities for
    every stage, while Stage 1.5 has a template identity.
11. The Stage 1.5 evidence classifier sees the transcript wrapper rather than
    the underlying approved live provider and marks it offline.
12. These three production integration issues are masked by the earlier BGE
    failure.
13. The current default live matrix lacks the frozen Window semantic canary.
14. Its clarification case is geometry clarification, not property
    clarification at Stage 1.5.
15. The dirty validator emits per-case current-property coverage and eligibility.
16. The dirty curator requires those fields, but the two curator test fakes do
    not emit them.
17. The curator tests mock the validator result; they do not prove the validator
    itself succeeds or fails.
18. The proof-validation report retains version `0.1` despite the additive
    fields, and no standalone report schema was found.
19. Plan 06 remains formally incomplete and no new live call is admissible.
20. No production code, tests, Proof, Git state, or historical failure evidence
    was modified by this investigation.

## 11. Current Hypotheses

### H1. Composite incomplete Plan 06 integration — high confidence

**Codex Hypothesis:** The most accurate top-level classification is a composite
work-in-progress integration failure, not a single regression. The alias-free
runtime was introduced into the real live executor before its hermetic test
seam, Stage 1.5 transport recording, stage-aware identity rules, and live matrix
were updated together.

Evidence supporting H1: Sections 5.1 through 5.7 and the fact that Plan 06 is
formally pending.

### H2. Stale fixtures account for part, but not all, of the red state — high confidence

**Codex Hypothesis:** The two curator failures are directly caused by a stale
mock validator payload. The live test also has stale Stage 1/2-only mock and
assertion fixtures. Updating only those fixtures would expose, not resolve, the
production transcript/evidence defects.

### H3. Runtime/environment dependency is real and contract-intended — high confidence

**Codex Hypothesis:** `BGE_M3_UNAVAILABLE` is valid production behavior in the
current environment. The defect is not that production fails closed; the
architecture question is whether this particular offline test should exercise
the actual model cache or inject a controlled alias-free runtime while a
separate preflight proves the real BGE lifecycle.

### H4. Live transcript/evidence code is a production regression relative to the frozen contract — high confidence

**Codex Hypothesis:** `_stage_name`, `_counts`, the universal profile-identity
gate, and wrapper-based live-eligibility classification are genuine production
integration defects. They prevent a valid Stage 1.5 live attempt from being
recorded and admitted even in a fully ready environment.

### H5. Curator output fields express the right safety intent but have an under-specified interface — medium-high confidence

**Codex Hypothesis:** Requiring current Stage 1.5 authority is aligned with the
SPEC. The exact Python field names and report-version evolution are not frozen
in a standalone schema, so the producer/consumer/test interface needs an
explicit decision rather than an automatic fixture-only edit.

### H6. Allowing `not_applicable` for either required curated case may be too permissive — medium-high confidence

**Codex Hypothesis:** Under the frozen live matrix, both curated success cases
are property-bearing cases. Accepting `not_applicable` for either case could
allow a non-Stage-1.5 result into Phase 12.1 Proof. This is not the cause of the
current red tests, but it is a nearby acceptance-contract risk that external
review should resolve before fixture updates.

## 12. Unresolved Ambiguities

1. Should `TranscriptProvider` expose/delegate the underlying approved Provider
   identity to Stage 1.5, or should Stage 1.5 acceptance use transport evidence
   plus an explicit wrapper protocol instead of concrete-type checks?
2. What is the exact live transcript label for Stage 1.5:
   `property_resolution`, `stage1.5`, or the raw
   `ifc_property_resolution`? The frozen docs require the semantic stage but do
   not freeze this internal string.
3. Should the live runner's evidence predicate become stage-aware, accepting
   operation profile identities for Stage 1/2 and template identity for Stage
   1.5?
4. Should `_production_case_executor` accept a runtime factory/injected runtime
   for offline tests while production CLI always uses a preflight-proven default
   runtime?
5. Should production construct/reindex the default BGE/Qdrant runtime once per
   live invocation or once per case? The current executor constructs it per
   case.
6. Is `text2ifc/ifc-repair-proof-validation/0.1` intentionally open to additive
   fields, or should the report gain a formal schema/new version before curator
   makes fields mandatory?
7. For the two fixed curated case IDs, should
   `property_authority_coverage` be required to equal
   `strict_stage_1_5_recomputed`, with `not_applicable` allowed only for other
   collections/cases?
8. Should `current_property_acceptance_eligible` remain a producer-supplied
   summary consumed by curator, or should curator derive it from more specific
   recomputed fields? The curator must still rely on the separate validator,
   not runner aggregates.
9. How should the frozen property clarification and Window canary be represented
   in `DEFAULT_CASES` and its case-matrix digest without conflating Plan 06
   offline admission with Plan 07 genuine live execution?

## 13. Candidate Fix Directions

These are review directions, not approved or applied fixes.

### Direction A: Complete the production Stage 1.5 live contract first

- Add an explicit Stage 1.5 transcript stage and separate attempt counts.
- Make prompt evidence validation stage-aware: profile identity for Stage 1/2,
  template identity for Stage 1.5.
- Establish an explicit approved-provider delegation/evidence protocol through
  `TranscriptProvider`; do not infer live eligibility solely from an unwrapped
  concrete type.
- Update the default live matrix to the frozen four-case contract.

This direction addresses confirmed production/spec gaps. It must be tested
offline before any genuine Provider call.

### Direction B: Split hermetic full-chain testing from real BGE readiness

- Keep the real API, durable store, resolver coordinator, admissibility, Stage 2,
  IFC authoring, reopen, and publication path in the full-chain test.
- Inject a deterministic alias-free `PropertyKnowledgeRuntime` and a Stage
  1.5-capable Provider double for that offline test.
- Separately retain production-construction and preflight tests that prove real
  local BGE-M3/Qdrant readiness, version consistency, reuse, and fail-closed
  behavior.

This direction avoids environment-sensitive unit/full-chain tests without using
aliases or weakening production readiness.

### Direction C: Formalize the validator-to-curator report contract

- Decide whether the report remains `0.1` with documented additive fields or
  receives a new version/formal JSON Schema.
- Make the mock validator fixture match that decided interface.
- Add rejection tests for historical alias authority, missing current Stage 1.5
  evidence, false eligibility, and case-specific coverage.
- Resolve whether the two fixed candidate Proof cases may ever be
  `not_applicable`; under the current frozen matrix they appear to require
  `strict_stage_1_5_recomputed`.

### Direction explicitly rejected by contract

- Do not restore `create_default_property_resolver()` in active live execution.
- Do not add new reviewed aliases, alias replay, keyword authorization, cached
  answers, synthetic fallback, or compatibility handling for erroneous LLM
  output.

## 14. Final Resolution

**Pending external review.**

No production code or test changes have been applied. The reviewer should first
resolve the ambiguities in Section 12 and select compatible directions from
Section 13. A fixture-only patch is insufficient because it would leave the
confirmed Stage 1.5 live transcript, count, identity, wrapper-eligibility, and
matrix defects in production.

## 15. Regression Evidence

### Fresh evidence produced for this issue

- Three known failures reproduced: `3 failed in 101.79s`.
- Fresh durable failure state preserves `BGE_M3_UNAVAILABLE` at the property
  retrieval boundary.
- No network transport was used.
- No production, test, Proof, planning, or Git files were modified by the test
  run; only the untracked `.tmp-issue-context-stage15-20260824/` evidence root
  was created.

### Existing relevant evidence inspected, not rerun here

- Alias-free runtime seam tests include ready-runtime and separate
  BGE/Qdrant-unavailable coverage.
- Five-family property-resolution E2E tests have a deterministic alias-free
  runtime seam.
- The broader two-file run reported `108 passed / 3 failed` and retained its
  artifacts at `.tmp-phase12-1-live-proof-contract-regression/`.
- Formal Plan 06 zero-skip preflight is not accepted; no live-readiness claim is
  made.

## 16. Reviewer Handoff

1. **Confirmed:** This is a dirty, incomplete Plan 12.1-06 candidate, not an
   accepted Phase checkpoint.
2. **Confirmed:** The focused state is reproducibly red on exactly the three
   named tests.
3. **Confirmed:** The first failure is caused immediately by unavailable local
   BGE-M3 in the production default runtime.
4. **Project Decision:** That runtime must fail closed and must not fall back to
   reviewed aliases.
5. **Confirmed:** The live test is environment-sensitive because the executor
   constructs the real default runtime internally.
6. **Confirmed:** The live Provider mock cannot answer Stage 1.5.
7. **Confirmed:** The live transcript wrapper cannot label Stage 1.5.
8. **Confirmed:** Live attempt counts omit Stage 1.5.
9. **Confirmed:** The live evidence predicate expects profile identities that
   Stage 1.5 does not use.
10. **Confirmed:** The wrapper causes Stage 1.5 live evidence to be classified
    as offline by concrete-type logic.
11. **Confirmed:** Those production issues are masked by the earlier BGE
    failure.
12. **Confirmed:** The default live matrix still lacks property clarification
    and Window canary required by frozen VALIDATION.
13. **Confirmed:** The two curator failures are directly caused by an older mock
    validator payload.
14. **Project Decision:** Current Proof must recompute complete Stage 1.5
    evidence and reject historical alias authority.
15. **Confirmed:** The new curator fields are not backed by a standalone report
    schema found in this repository and retain report version `0.1`.
16. **Hypothesis:** The best overall diagnosis is composite incomplete
    integration plus stale fixtures and a real environment dependency.
17. **Hypothesis:** A test-only fixture update would be incomplete and would
    expose additional production failures.
18. **Hypothesis:** `not_applicable` may be too permissive for the two fixed
    property-bearing Proof cases.
19. **Open:** Decide the provider-wrapper evidence protocol, stage-aware prompt
    identity contract, and validator report version before implementation.
20. **Confirmed:** No fix, DeepSeek call, Proof curation, Phase 12 closeout, or
    Phase 13 work is authorized or performed by this issue package.

## Sources Inspected

- `docs/context-handoff/PROJECT-CONTEXT-PACK.md`
- `docs/context-handoff/CONTEXT-HANDOFF-RULES.md`
- `.planning/STATE.md`
- `.planning/ROADMAP.md`
- `.planning/phases/12.1-property-resolution-rag-reranker/12.1-SPEC.md`
- `.planning/phases/12.1-property-resolution-rag-reranker/12.1-VALIDATION.md`
- `.planning/phases/12.1-property-resolution-rag-reranker/12.1-06-PLAN.md`
- `docs/validation/agent-capability-evaluation.md`
- `src/text2ifc_knowledge/property_runtime.py`
- `src/text2ifc_ifc_repair/api.py`
- `src/text2ifc_ifc_repair/property_resolution_stage.py`
- `scripts/ifc_repair/run_phase12_live_uat.py`
- `scripts/ifc_repair/validate_success_cases.py`
- `scripts/ifc_repair/curate_phase12_live_proof.py`
- `tests/ifc_repair/test_phase12_live_uat.py`
- `tests/ifc_repair/test_phase12_success_cases.py`
- `tests/knowledge/test_property_vector_runtime.py`
- `tests/ifc_repair/test_property_resolution_family_e2e.py`
- current Git status/diff/log and the two repository-local failure artifact roots

## 17. Implementation Addendum — 2026-08-24

This addendum preserves the original investigation above. It supersedes only
the pending execution state recorded in Section 14; it does not rewrite the
earlier observations or hypotheses as if they had been known initially.

### Implemented root causes

The issue was a composite incomplete integration, not one property phrase or a
reason to restore an alias:

1. `BGE_M3_UNAVAILABLE` was correct production fail-closed behavior. The
   mocked-transport full-chain test was environment-sensitive because the live
   executor constructed the default production BGE-M3/Qdrant runtime internally
   instead of accepting a deterministic alias-free runtime at the test seam.
2. Stage 1.5 had not been integrated into the live evidence path as a first-
   class semantic stage. `TranscriptProvider` could not label
   `ifc_property_resolution`, attempt counts omitted it, identity validation
   treated every attempt as an operation-profile attempt, and wrapper-based
   live eligibility was lost at the outer Python type.
3. The frozen live matrix and mocked transport still represented a Stage 1/2-
   only three-case workflow. They did not execute property clarification/resume
   or the Window `外窗=true` semantic canary through Stage 1.5.
4. Validator and curator had acquired mandatory property-authority fields
   without a formal versioned boundary. Updating only mock payloads would have
   hidden the production integration defects and silently changed report 0.1.
5. Historical property-bearing Proof cases needed an explicit ineligible
   classification. `not_applicable` is valid only for a genuinely non-property
   case; it cannot make an unrecomputed alias-era property artifact current.
6. The first 60-case Candidate evaluator was not admissible evidence: it
   selected an expected candidate and authorization outcome from Gold fixture
   fields, and its added group IDs made group isolation vacuous.
7. Preflight 0.2 was incomplete: its full-suite command omitted
   `tests/knowledge`, it did not bind execution identity/timestamps/network
   attempt state, and an untracked auto-loaded pytest conftest affected the run.

### Implemented fix

Implementation checkpoints:

- `2a87020b` (`fix(12.1-06): complete stage 1.5 offline contracts`);
- `4d2cd7d3` (`fix(12.1-06): make offline admission non-oracular`).

- Added a bounded, cycle-safe provider-evidence delegation protocol. A wrapper
  may expose the actual transport identity without a `TranscriptProvider`-
  specific compatibility branch; injected transports remain non-live.
- Added a `property_resolution` transcript stage, separate Stage 1 / Stage 1.5 /
  Stage 2 counts, immutable Stage 1.5 template identity, exact operation-profile
  identity for Stage 1/2, and exact zero-few-shot handling where the registered
  profile has no examples.
- Added narrow dependency injection to the mocked full-chain executor and the
  private offline public-repair helper. The public production function retains
  its three-input signature and the default live/CLI path still constructs the
  real BGE-M3/Qdrant runtime.
- Extended the fixed matrix to Beam+Column natural-language properties,
  property clarification/user candidate selection, Window `外窗=true`, and the
  unsupported-program guard. The mocked transport now traverses the real
  RepairAPI, persistence/orchestration, admissibility, Stage 2, IFC application,
  reopen, and publication path.
- Added `text2ifc/ifc-repair-proof-validation/0.2` as the minimal validator-to-
  curator schema. The two fixed live property success IDs require
  `strict_stage_1_5_recomputed`, at least one property claim, and current
  eligibility. Unrecomputed property artifacts are
  `historical_property_artifact_only` and ineligible; zero-property cases may
  remain `not_applicable`.
- Added deterministic replay for a public user candidate selection without a
  Provider call or legacy alias resolver. Forged selection, wrong transition,
  missing Stage 1.5 evidence, unoffered selection, and alias authority fail
  closed.
- Replaced the oracle-capable Candidate evaluator with deterministic frozen
  Stage 1.5 prompt replay. The replay sees only the rendered query and offered
  candidates; expected/authorization/case-ID fields are rejected. Empty
  candidate sets follow the production clarification route without a replay
  Provider call. The 60 cases now form 40 non-vacuous semantic groups.
- Upgraded preflight to 0.3. It runs the exact
  `tests/knowledge tests/ifc_repair` suite, records commit/branch/dirty-worktree
  state, runtime/dependency identity and check timestamps, and derives
  `network_transport_attempted` from observed calls. The pytest environment
  shim is now tracked instead of silently auto-loading from an untracked file.

No reviewed alias, phrase table, compatibility normalization, production test
fallback, retrieval/admissibility relaxation, L0/L1/L2 weakening, property hash
gate, genuine DeepSeek call, Proof curation, or Phase 13 work was added.

## 18. Interim Regression Evidence

### Focused and family gates

- Stage 1.5 runner/success focus: `124 passed in 556.68s`, zero skip.
- Frozen 60-case evaluation: `5 passed in 183.73s`. Baseline passed 46/60;
  Candidate passed 60/60 with 14 failures retained in the denominator.
  Supported Top-K recall and confirmed-standard precision were 1.0. False
  standard authorization, wrong class/type/unit/scope, alias runtime authority,
  unoffered selection, and private leakage were all zero. The replay recorded 58
  attempts plus two no-candidate routes and could not read Gold labels.
- Five-family and alias-retirement regression: `8 passed in 18.99s`, covering
  Window, Door, Wall, Beam, and Column through the public Stage 1.5 path.
- Dataset real-IFC full chain: `12 passed in 461.44s`, including six successes
  and two expected atomic rollbacks.

### Fresh machine-readable preflight 0.3

Preflight evidence ID:
`sha256:70725e29ee3761be682967f51d00277fdfef9d126bbb0ce4f2fff0cd33b6cdbf`.

- execution commit:
  `4d2cd7d37d0e00953b6a1774bff71955410eab5b`;
- focused: passed, exit 0, `86 passed in 147.98s`;
- offline matrix: passed, six accepted cases, two expected atomic rollbacks,
  `provider_network_calls=0`;
- complete `tests/knowledge tests/ifc_repair`:
  `1100 passed in 3149.34s`, zero skip;
- compileall: passed;
- `git diff --check`: passed;
- existing accepted Proof validator: passed under report 0.2.

The manifest reports exactly zero failures, skips, substitutions, timeouts, and
network calls. It also binds branch, intentionally dirty worktree, Python/
platform/dependency identity, per-check timestamps, and a network-attempt flag
derived from observed calls. The enclosing preflight-only result reports
`transport_calls=0` and `evidence_mode=not_run`; it is not live evidence.

### Rejected interim admission record

- Exact combined preflight command `tests/knowledge tests/ifc_repair`:
  `1100 passed in 3149.34s (52:29)`; JUnit independently records 1100 tests,
  zero failures, zero errors, and zero skipped.
- Existing accepted Proof recomputation report 0.2: 22 cases, 57 operations,
  361 checked files, 66 IFC reopens, 17 independently recomputed cases, five
  legacy limitations, zero current strict Stage 1.5 cases, and two historical
  property artifacts explicitly ineligible. This run did not add or curate
  Phase 12.1 Proof.
- Final IFCCompare was not executed as Plan 06 admission. It remains a Plan 07
  responsibility over genuine live results.

### Runtime boundary

Both runtime classes were exercised and must not be conflated:

- the 60-case evaluation and offline-matrix readiness used the real local
  production BGE-M3/Qdrant runtime (`BAAI/bge-m3`, 472 records, ready);
- the mocked Provider full-chain executor used the deterministic alias-free
  runtime injection seam while executing real product orchestration and IFC
  application.

No genuine DeepSeek transport was called. Plan 12.1-07 remains responsible for
the four-case live matrix, independent live Proof curation/recomputation, final
IFCCompare, and Phase 12/12.1 closeout.

## 19. Independent Re-review Rejection and Fail-Closed Correction

The follow-up independent review rejected the Candidate result recorded in
Section 18. That rejection supersedes the earlier Candidate 60/60 and Plan 06
admission language; the raw preflight 0.3 artifact remains useful execution
evidence but is not an accepted Plan 06 gate.

### Remaining root cause

The removed helper no longer received fields named `expected` or `authorize`,
but `phase12_1_stage15_transcript_replay.json` was an answer-equivalent table:
all 31 replay keys matched evaluation inputs and all 31 replay decisions matched
Gold. The Provider performed an exact query lookup and selected the stored
canonical path. Therefore the reported Candidate 60/60 measured fixture
conformance, not Gold-independent Stage 1.5 semantics. The shallow helper-
signature test did not detect this indirect leakage.

### Corrective implementation

Checkpoint `b8cf328e` (`fix(12.1-06): reject replay-oracle evaluation`):

- deletes the answer-equivalent Stage 1.5 replay fixture and its evaluation
  provider/helper;
- preserves deterministic Stage 1.5 fakes only for offline prompt/parser/
  orchestration/full-chain plumbing, where they are valid and explicitly
  non-live;
- upgrades the evaluation report to
  `text2ifc/phase12.1-property-resolution-evaluation/0.2`;
- runs real BGE-M3/Qdrant retrieval for all 60 cases but reports semantic
  Candidate rows as unscored;
- returns `status=blocked` with
  `INDEPENDENT_STAGE15_CANDIDATE_OUTPUT_REQUIRED` and never converts missing
  semantic evidence into zero false authorization or perfect precision;
- adds a regression that rejects any reintroduction of the replay fixture,
  helper or oracle model ID into the 60-case Candidate evaluator.

Fresh focused evidence:

- anti-oracle RED: one expected failure on the answer-table evaluator;
- anti-oracle GREEN: one pass after removal;
- complete real-BGE evaluation file: `5 passed in 125.06s`;
- supported canonical Top-K recall remains 1.0;
- semantic Candidate scored count is 0 and unscored count is 60;
- Provider/network calls remain 0.

### Admission consequence

Plan 12.1-06 is **not complete**. Frozen R12 requires Candidate semantic outputs
that can be scored by the same evaluator without Gold leakage. This task also
forbids a genuine DeepSeek call, and no pre-Gold frozen Candidate output exists
in the repository. Consequently the remaining evidence cannot be manufactured
by another fixture, alias, deterministic auto-authorization rule, subagent
opinion or relaxed gate.

Preflight 0.3 implementation/provenance remains valid, and its recorded
`tests/knowledge tests/ifc_repair` execution did pass 1100 tests with zero
failure/error/skip/network. It cannot admit Plan 06 because the evaluation
included in that run was later proven invalid. No Plan 06 summary or completion
checkpoint is created, and Plan 07 remains blocked.

## 20. Local Temporary Artifact Cleanup

On 2026-08-24, repository-root cleanup identified 175 untracked `.tmp-*`
items totaling 11,172,528,170 bytes. They were pytest base directories, test
caches, repeated generated IFC/JSON outputs, JUnit files, and superseded
Phase 11/12/12.1 preflight workspaces. No matching pytest or Python process was
running at cleanup time.

The first cleanup batch removed 161 reproducible pytest/preflight directories
totaling 10,785,621,982 bytes with zero failures. It deliberately retained the
two diagnostic roots named earlier in this issue,
`.tmp-issue-context-stage15-20260824` and
`.tmp-phase12-1-live-proof-contract-regression`, plus 12 small JUnit XML result
files, until their evidence boundary was checked. Their durable findings are
already distilled in Sections 2, 15, 16, 18, and 19; retaining complete test
workspaces would duplicate generated data without strengthening the evidence.

Before deleting the remaining temporary carriers, their exact boundary was
recorded. `.tmp-issue-context-stage15-20260824` contained 139 files / 22,625,930
bytes; `.tmp-phase12-1-live-proof-contract-regression` contained 1,466 files /
363,675,394 bytes. The 12 JUnit XML files totaled 604,864 bytes and recorded:

| Run label | Tests | Failures | Errors | Skipped | Pytest time (s) |
|---|---:|---:|---:|---:|---:|
| admission-focused3 | 152 | 0 | 0 | 0 | 492.010 |
| admission-full | 1,094 | 4 | 3 | 0 | 1,492.453 |
| admission-full2 | 1,094 | 0 | 0 | 0 | 3,004.886 |
| diagnose-acceleration | 3 | 0 | 0 | 0 | 6.891 |
| final-full | 1,098 | 0 | 0 | 0 | 3,267.542 |
| fix-contracts-focused | 38 | 0 | 0 | 0 | 169.988 |
| fix-dataset-e2e | 3 | 0 | 0 | 0 | 381.164 |
| preflight-v02-green | 11 | 0 | 0 | 0 | 5.306 |
| preflight-v02-live-full | 86 | 0 | 0 | 0 | 165.937 |
| proof-nonproperty-green | 3 | 0 | 0 | 0 | 46.567 |
| specialty-eval60 | 3 | 0 | 0 | 0 | 243.447 |
| specialty-five-family | 8 | 0 | 0 | 0 | 19.642 |

These JUnit rows are historical intermediate executions only. In particular,
the green intermediate runs do not supersede the anti-oracle rejection in
Section 19 and do not admit Plan 06.

Durable change and regression history remains in Git checkpoints `87b6f7c5`,
`2a87020b`, `4d2cd7d3`, `b8cf328e`, and `8f83cca9`, together with this issue,
`.planning/STATE.md`, `.planning/ROADMAP.md`, and
`PROJECT-CONTEXT-PACK.md`. Genuine run/failure evidence and accepted Proof under
`dataset/processed/ifc-repair-runs` and `dataset/processed/proof` are explicitly
outside the cleanup scope. Dataset sources, PDFs, requirements, and unrelated
dirty-worktree changes are also untouched.

Removing these temporary paths does not change the evidence classification:
Plan 12.1-06 remains blocked on Gold-independent Stage 1.5 Candidate output,
Plan 07 remains blocked, and no live evidence or Proof has been promoted.
