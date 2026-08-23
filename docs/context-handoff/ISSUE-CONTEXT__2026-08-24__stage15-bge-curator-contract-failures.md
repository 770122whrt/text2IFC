# Issue Context: Stage 1.5 BGE, Live Transcript, and Curator Contract Failures

**Created:** 2026-08-24  
**Last updated:** 2026-08-24  
**Status:** Investigation complete; external resolution review pending  
**Scope:** Phase 12.1 Plan 06 candidate work only; no production-code or test fix is applied by this investigation

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
