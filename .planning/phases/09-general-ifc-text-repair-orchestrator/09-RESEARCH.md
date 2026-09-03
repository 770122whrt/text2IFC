# Phase 9: General IFC + Text Repair Orchestrator - Research

**Researched:** 2026-07-20
**Status:** Complete
**Question:** What must be understood to plan a safe, general IFC + text repair
orchestrator on top of Phases 7 and 8?

## Executive Summary

Phase 9 is primarily an integration and state-contract phase, not a new IFC
authoring phase. The repository already contains the hard deterministic pieces:

- Phase 7: fingerprinted SQLite index, `TargetQuery`, deterministic resolution,
  and bounded target context.
- Pre-application: ChangeSet schema/binding validation, Registry Audit, and
  transactional application.
- Phase 8: production/private evaluator separation, independent L1, semantic
  L2 policy, strict aggregation, public projection, and diagnostic retention.
- Provider/runtime: OpenAI-compatible/DeepSeek client, redacted live evidence,
  prompt registry, token guards, and deterministic fake Providers.

The missing product layer is a versioned, resumable state machine that connects
those pieces without inheriting the frozen Window benchmark's private mutation
setup. Planning should favor additive public contracts and a new general
orchestrator, while keeping `run_case.py` and its benchmark workflow as
compatibility/UAT fixtures until the new path is verified.

The highest-risk work is not calling the Provider. It is preserving authority
across stage boundaries: request facts versus model facts, resolved candidates
versus arbitrary IDs, user-selected Prototype versus similarity, production
versus Gold, diagnostic candidate versus successful IFC, and persisted state
versus tampered/stale resume input.

## Current-State Delta

| Needed by Phase 9 | Existing asset | Delta |
|---|---|---|
| IFC + text production start | `scripts/ifc_repair/run_case.py` | Current CLI is frozen to LargeBuilding IDs and manufactures damage. |
| Text -> structured target intent | Phase 7 `TargetQuery.from_dict` | No Provider-facing RepairIntent schema/prompt/stage exists. |
| Target resolution | `build_ifc_index`, `resolve_target`, `build_target_context` | Currently exposed through a separate structured index CLI, not orchestration. |
| Clarification/resume | Resolution statuses exist | No clarification contract, persisted answer, state transition, or continuation API. |
| Resolved context -> ChangeSet | `generate_repair_changeset` | Assumes a prebuilt public repair spec/context; must accept operation-scoped resolved inputs. |
| Atomic apply | `audit.py`, `apply.py`, Registry | Reusable; common flow must preserve unified all-or-nothing behavior. |
| Production L2 facts | `SemanticFact`, Phase 7 records, `evaluate_production` | No orchestrator constructs `expected_facts_by_operation`. |
| Publication/evidence | Phase 8 `workflow.py` helpers | Tied to one benchmark/private flow; needs general public run lifecycle. |
| Human/machine CLI | `argparse` CLIs and exit-code tests | No shared typed result or interactive repair adapter. |

## Recommended Public Contract Set

Use separate exact-versioned schemas instead of growing TargetQuery or
Evaluation documents into workflow state.

### RepairIntent 0.1

Recommended identity: `text2ifc/ifc-repair-intent/0.1`.

Required top-level fields:

- `schema_version`
- `request_id`
- `source_request_hash`
- `operations`
- `clarifications`

Each operation intent should contain:

- stable `operation_intent_id`
- Registry `operation_type`
- embedded schema-valid `target_query`
- operation-specific requested `parameters`
- typed `attribute_intents`
- `prototype_intent` restricted to absent, explicit GUID/type reference, or
  user-selection request
- evidence pointers into the public request/contract documents

The Stage 1 schema should permit an explicit clarification object instead of
forcing an invented value. Unsupported operation types remain a deterministic
classification after parse, not a free-form Provider refusal that later stages
must interpret.

### Clarification 0.1

Recommended identity: `text2ifc/ifc-repair-clarification/0.1`.

The question object should include:

- `clarification_id`, `run_id`, `run_revision`, and `operation_intent_id`
- reason enum: `ambiguous_target`, `selector_conflict`,
  `missing_required_parameter`, `prototype_selection`, or
  `additional_target_detail`
- safe Chinese-first `question`
- answer schema/mode
- projected candidates with opaque answer token plus readable GUID/class/name/
  storey/position/match evidence
- no private original, mutation mapping, Provider secret, or raw IFC fragment

Candidate answers must be checked against the persisted candidate set and run
revision. Never trust a caller-supplied GlobalId merely because it has valid IFC
syntax.

### Run State and Terminal Result 0.1

Keep private operational state separate from the public result.

Private run state needs:

- `run_id`, `revision`, state schema and orchestrator version
- source path/reference, SHA-256, size, IFC schema
- current stage/status and transition timestamps
- input/output contract versions
- per-operation intent/resolution/clarification status
- artifact paths and hashes
- retry/attempt counters
- no raw API secret

The public terminal result should remain compact:

- `schema_version`, `run_id`, terminal `status`, `reason_code`
- `complete_repair_success`, `successful_artifact_publishable`
- L1/L2/L3 summaries when Evaluation exists
- relative paths to run directory, ChangeSet, Evaluation, manifest, successful
  IFC, or diagnostic candidate
- optional current clarification reference

Do not put full candidate lists, Provider messages, or Evaluation evidence in
stdout JSON.

## State Machine Design

Recommended durable stages:

```text
CREATED
  -> SOURCE_VALIDATED
  -> INDEX_READY
  -> INTENT_READY
  -> TARGETS_RESOLVED
  -> CHANGESET_READY
  -> APPLICATION_READY
  -> EVALUATED
  -> SUCCEEDED | NOT_PUBLISHABLE
```

Any pre-terminal stage may move to:

```text
CLARIFICATION_REQUIRED
UNSUPPORTED
INVALID_INPUT
PROVIDER_FAILED
AUDIT_FAILED
APPLICATION_FAILED
CANCELLED
```

Only `CLARIFICATION_REQUIRED` is resumable by a user answer. Provider correction
attempts are internal bounded transitions, not human clarification. Terminal
success/failure states are read-only.

### Resume behavior

- Candidate selection can reuse the existing index, Stage 1 intent, and
  resolution evidence; it replaces only the unresolved target binding.
- A structured missing-parameter answer can be merged into the intent and
  schema-validated without repeating indexing.
- Free-form additional target detail should create a new Stage 1 attempt that
  includes the original request plus clarification; previous intent evidence is
  retained as superseded, while source validation/index are reused.
- Continuation must compare the submitted `run_revision` and
  `clarification_id` to stored state to prevent stale or replayed answers.
- Use an exclusive per-run mutation lock and atomic temp-file replacement for
  state transitions. Concurrent continuation should return a structured
  conflict rather than racing artifact writes.

For correctness-first Phase 9, store the SQLite index inside the run directory.
Phase 7 already requires full rebuild on changed source; cross-run index caching
can remain an internal optimization only if every version/fingerprint field is
checked. Phase 13, not Phase 9, owns performance justification.

## Two-Stage Provider Boundary

### Stage 1: request understanding

Inputs should be limited to:

- raw user repair text, clearly delimited as untrusted data
- request hash and public run/request ID
- Registry operation summaries: operation type, allowed target IFC classes,
  target/parameter schemas, capability constraints, semantic attribute intent
  vocabulary
- RepairIntent schema
- previous public clarification answer when this is a correction attempt

It should not receive candidate records or whole IFC JSON. Its job is to state
what the user asked and what evidence is missing, not to select an entity.

### Deterministic middle stage

For each operation intent:

1. Validate Registry operation and parameter/target-query compatibility.
2. Resolve through the Phase 7 repository.
3. Stop the entire unified transaction if any result is ambiguous, conflicting,
   not found, or unsupported.
4. Project only relevant candidates/properties/relationships/geometry within
   explicit bytes/tokens.
5. Bind every resolved operation to the same source fingerprint.

### Stage 2: ChangeSet generation

Refactor the current `provider_stage.py` renderer/binder rather than bypassing
it. Stage 2 should receive operation-scoped intent plus resolved context and
output one existing ChangeSet 0.1 envelope. Strengthen binding for multiple
operations:

- every intent ID maps to exactly one ChangeSet operation ID
- operation types match
- each target ID appears in its own resolved candidate set
- top-level scope is the union of per-operation authorized targets/effects
- operation evidence pointers remain operation-scoped
- no missing or extra operation may pass

One bounded correction retry per Agent stage is a reasonable initial default:
it contains schema/validation feedback only, retains both attempts, and never
changes deterministic authority. The exact count can remain configurable but
must be finite and tested.

## Production Semantic Evidence Construction

Phase 8 already defines the closed authority enum and precedence. Phase 9
should add a builder that returns:

```python
dict[operation_id, tuple[SemanticFact, ...]]
```

Recommended source mapping:

| Authority | Construction |
|---|---|
| `EXPLICIT_REQUEST` | Convert validated RepairIntent attribute/parameter intent to typed facts, preserving user-text span/evidence pointer and units. |
| `SURVIVING_TARGET` | Use Phase 7 `ElementRecord` or direct IFC extraction for the resolved existing target when that role survived. |
| `SURVIVING_HOST` | Follow Registry-declared host role and actual IFC relationship, then convert only policy-compatible facts. |
| `SURVIVING_TYPE` | Follow formal IFC type relationship (`type_global_id`/`IfcRelDefinesByType`), never a name-only match. |
| `APPROVED_PROTOTYPE` | Resolve the exact user-named/selected entity, confirm Registry compatibility, record clarification/request evidence, then convert facts. |
| `DETERMINISTIC_POLICY` | Emit only values the versioned operation policy explicitly defines; no project-specific guesses. |

Every fact must use the eventual ChangeSet `operation_id`. Build a stable
intent-ID to operation-ID map after ChangeSet binding; never create one shared
fact list for all operations.

Potential ambiguity in request values must be handled before Stage 2. For
example, `FireRating=60` requires value type/unit normalization evidence; it
must not silently become a string if the applicable policy expects a duration.

No production helper should accept `PRIVATE_ORIGINAL`. Retain the Phase 8
constructor rejection and whole-bundle canary scan as defense in depth.

## Evidence Directory Layout

A plan-ready layout is:

```text
<output-root>/<run-id>/
  run-state.json                 # private operational state; redacted secrets
  result.json                    # compact public current/terminal result
  source/
    fingerprint.json
  index/
    targets.sqlite
    build-report.json
  request/
    request.txt
    request-metadata.json
  intent/
    prompt-input.json
    attempt-001/...
    repair-intent.json
  resolution/
    <operation-intent-id>/query.json
    <operation-intent-id>/resolution.json
    <operation-intent-id>/context.json
  clarification/
    <clarification-id>.json
    <clarification-id>-answer.json
  changeset/
    attempt-001/...
    changeset.json
  application/
    audit-report.json
    application-report.json
  evaluation/
    public-evaluation.json
    report.md
  artifacts/
    repaired.ifc                # only if Evaluation 0.2 publishable
  diagnostic/
    repaired-candidate.ifc      # optional, never successful path
  manifest.json
```

Provider live request/response/events and raw output can live inside the
corresponding attempt directory using existing redaction helpers. The manifest
should exclude itself or use a clearly defined two-pass convention; all other
public artifacts need relative path, SHA-256, size, role, and publication class.

## CLI/API Recommendation

Recommended Python surface:

```python
start_repair(inputs: RepairStartInputs, *, provider, registry) -> RepairRunResult
continue_repair(run_dir, answer: ClarificationAnswer, *, provider, registry) -> RepairRunResult
read_repair_result(run_dir) -> RepairRunResult
```

The API should return at every durable pause/terminal point and never call
`input()` or print. A thin CLI may loop over `continue_repair` in TTY mode.

Recommended command family:

```text
repair start SOURCE --request TEXT --output-root DIR
repair continue RUN_DIR --answer ...
repair result RUN_DIR
repair check-config
```

Human mode prints concise progress and prompts. `--json` prints only canonical
`result.json`. `--non-interactive` returns when clarification is required.
`--quiet` suppresses progress, not structured errors written to stderr.

Exact exit code numbers are implementation discretion, but categories should
be stable: success; clarification; invalid/unsupported request; Provider;
Audit/application; evaluation non-publishable; state/tamper error; cancelled.

## Phase 10 Boundary and Success Testing

Phase 9 must not make the existing Window authoring L2-complete. Therefore its
test matrix needs two complementary forms of evidence:

1. A Registry test fixture with deterministic adapters/evaluator facts proves
   the generic orchestrator's full success publication path and atomic
   multi-operation behavior.
2. The real existing Window integration proves the honest current behavior:
   Stage 1 -> resolution -> Stage 2 -> application can reach L1 success, while
   known L2 gaps keep the candidate diagnostic/non-publishable until Phase 10.

An opt-in real DeepSeek UAT should exercise both Agent calls and record its true
terminal status. Phase 9 success means the orchestration and gates are correct,
not that the Window L2 authoring debt disappeared.

## Security and Failure Analysis

| Threat | Severity | Required mitigation |
|---|---|---|
| User prompt injection changes output protocol or requests hidden data | high | Treat request as untrusted delimited data; exact schemas; Registry allowlist; no tool authority in Provider. |
| Agent emits target/scope outside deterministic context | critical | Per-operation candidate/evidence binding and complete intent-to-operation cardinality checks. |
| Clarification answer substitutes an unoffered GUID/Prototype | high | Opaque clarification ID, run revision, answer schema, and candidate-set membership validation. |
| Stale/tampered state resumes against another IFC | critical | Source/index/request hashes, schema versions, artifact manifest, exclusive lock, and fail-closed reload. |
| Private Ground Truth enters either Provider/public bundle | critical | Type-separated production API, no Gold fields, public allowlists, semantic/private canary scan across both stages. |
| Partial multi-operation application is presented as success | critical | One ChangeSet transaction, Registry/Audit all-or-nothing, Evaluation 0.2 sole publication authority. |
| Similar entity silently authorizes wrong Type/Pset/Material | high | Formal binding or explicit user authorization; compatibility policy and provenance; similarity is recall only. |
| Run path overwrite/traversal or symlink escape | high | Server-generated stable IDs, resolved containment checks, exclusive create, relative manifest paths, no user path fragments as artifact names. |
| Provider trace leaks API key/base URL/private values | high | Existing redaction, secret canaries, error sanitization, and public/private artifact roles. |
| Unbounded retry/candidate/context exhausts cost/tokens | medium | Fixed candidate/byte/token budgets and finite evidenced retries. |

## Common Pitfalls

- Reusing the benchmark `_run_window_repair_case` and merely replacing its text
  parameter would preserve a hidden Gold/mutation dependency.
- Letting Stage 2 resolve targets repeats the old ambiguity and bypasses Phase 7.
- Treating all non-resolved target statuses as generic Provider failure loses
  user-actionable clarification semantics.
- Persisting only a final JSON result makes continuation unverifiable; persist
  each authoritative stage input/output and hashes.
- Copying all indexed Psets into prompts violates the bounded-context decision;
  project only properties named by attribute intent/policy.
- Using the same `expected_facts` tuple for multiple ChangeSet operations
  reintroduces the operation-evidence leak fixed in Phase 8 review.
- Marking a repaired candidate as `artifacts/repaired.ifc` before Evaluation
  creates a publication race. Keep it in staging/diagnostic until the final
  aggregate passes.
- Treating live UAT success as deterministic acceptance makes CI credential-
  dependent. Offline contracts/gates remain authoritative.

## Validation Architecture

### Test layers

1. **Schema/model tests:** RepairIntent, clarification answer, run state, result,
   exact versions, canonical JSON, size bounds, malformed/unknown fields.
2. **State-machine tests:** every legal transition, illegal/replayed/stale
   transition, atomic persistence, lock conflict, resume and tamper detection.
3. **Stage tests:** public-only Stage 1, target resolution stop conditions,
   Stage 2 multi-operation binding, bounded retry and trace preservation.
4. **Semantic-authority tests:** request precedence, surviving roles, formal
   Type, selected Prototype, cross-operation isolation, forbidden similarity/
   Gold, missing-fact behavior.
5. **Orchestrator integration:** fake Providers plus synthetic IFC/Registry
   fixtures cover clarification, unsupported, every failure stage, generic
   publishable success, and source/hash/manifest invariants.
6. **Real IFC integration:** LargeBuilding/current Window path proves bounded
   indexing, both Agent stages (fake in CI), honest L1/L2 publication status,
   and no source mutation.
7. **CLI tests:** TTY adapter, non-interactive, JSON, quiet, stdout/stderr,
   resume/cancel, config redaction, and stable exit classes.
8. **Opt-in UAT:** one DeepSeek command with config preflight and redacted
   two-stage evidence; excluded from deterministic pytest gate.

### Sampling and commands

- Per TDD feature: its focused file under 30 seconds where practical.
- Per plan: all completed Phase 9 focused tests plus direct Phase 7/8 regression
  files.
- Before verification: full `tests/ifc_repair`, compileall, four new JSON Schema
  checks, public/private canary scan, source hashes, and `git diff --check`.

### Required negative fixtures

- duplicate-name ambiguous Walls and conflicting exact GUID/class selectors
- invalid/missing GlobalId and unsupported curved/free-form Wall capability
- stale/tampered run state and index/source fingerprint mismatch
- invalid clarification candidate/prototype and replayed answer
- prompt-injected RepairIntent/ChangeSet, extra/missing operation, crossed
  operation targets/facts/evidence pointers
- Audit/application exception, unreadable repaired IFC, L1 pass + L2 fail,
  L1 fail + L2 pass, not-evaluable mandatory L2
- private original ID/path/value canaries in both Provider inputs and all public
  outputs

## Recommended Plan Decomposition

1. **09-01 - RepairIntent and request-understanding contract (TDD):** schemas,
   models, prompt/registry, public-only Stage 1, bounded correction evidence.
2. **09-02 - Durable run/clarification state machine (TDD):** start/continue/
   read contracts, atomic state, run layout, candidate/answer validation,
   resume/tamper/lock behavior.
3. **09-03 - Resolution and ChangeSet binding orchestration (TDD):** Phase 7
   integration, operation-scoped contexts, clarification routing, Stage 2
   multi-operation cardinality and binding.
4. **09-04 - Production semantic authority and terminal publication (TDD):**
   expected-fact builder, Audit/apply/evaluate_production, artifact promotion,
   manifest/private boundary, full terminal matrix.
5. **09-05 - Interactive CLI and acceptance evidence:** thin human/machine CLI,
   LargeBuilding offline flow, opt-in DeepSeek route, docs/report, full
   regressions and security checks.

The plans should be sequential because the durable state schema is consumed by
all later stages and the working tree contains shared untracked repair-baseline
files. Each plan should stage only its exact files.

## RESEARCH COMPLETE

The phase is ready for Nyquist validation strategy, pattern mapping, detailed
TDD plans, and goal-backward plan checking.
