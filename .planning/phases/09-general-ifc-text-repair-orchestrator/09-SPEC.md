# Phase 9: General IFC + Text Repair Orchestrator - Specification

**Created:** 2026-07-20
**Ambiguity score:** 0.06 (gate: <= 0.20)
**Requirements:** 12 locked

## Goal

One supported Python API and CLI must accept a user-supplied existing or
damaged IFC2X3 file plus natural-language repair text, persist a resumable
two-stage Agent run, deterministically resolve and apply one unified ChangeSet,
and publish an IFC only when Evaluation 0.2 authorizes it.

## Background

Phase 7 already supplies a fingerprint/version-bound SQLite IFC index,
`TargetQuery`, deterministic target resolution, and bounded target context.
Phase 8 supplies Evaluation 0.2, strict mandatory L1/L2 aggregation,
production/private benchmark separation, diagnostic retention, and public
projection.

The current executable path is not a general product entrypoint:
`scripts/ifc_repair/run_case.py` requires frozen LargeBuilding Wall/Opening/
Window GUIDs, while `workflow.py` manufactures a damaged IFC from a private
original and routes the result through benchmark evaluation. The index CLI
accepts pre-authored TargetQuery JSON instead of natural language, and the
Provider stage only generates a ChangeSet after public spec/context already
exist. There is no versioned RepairIntent, persistent clarification state,
general production orchestrator, or shared human/machine terminal contract.

### Stage 1 contract repair addendum (2026-07-20)

The Provider owns only the semantic RepairIntent body. Request ID, source
request hash, prompt fingerprint, and Provider-model fingerprint are
deterministically attached by the runtime. A structurally valid operation may
carry partial parameters; the Operation Registry validates supplied values,
injects only schema-declared constants, and derives missing executable paths.
Missing facts produce `clarification_required/missing_required_parameter`
before target resolution and do not consume a Provider correction retry.

## Requirements

1. **General production start contract**: A public API and CLI accept a source
   IFC path, natural-language request, output root, Provider configuration, and
   bounded runtime options without requiring benchmark GUIDs or a private
   original.
   - Current: `run_case.py` defaults to one LargeBuilding Window case and
     requires Wall/Opening/Window identifiers; `workflow.py` creates its own
     damaged IFC.
   - Target: A caller can start a run from an arbitrary supplied IFC2X3 and
     request. The source is fingerprinted, checked, indexed, copied or read
     without in-place mutation, and bound to a unique non-overwriting run.
   - Acceptance: A CLI/API integration test starts from a caller-owned fixture,
     passes no benchmark IDs/original, leaves the source SHA-256 unchanged, and
     creates a versioned run result and evidence directory.

2. **Versioned RepairIntent stage**: The first Agent stage converts user text
   into one versioned structured intent containing one or more operation
   intents, `TargetQuery` selectors, requested parameters, attribute intents,
   and provenance.
   - Current: Phase 7 accepts structured TargetQuery JSON, but no production
     natural-language request-understanding contract exists.
   - Target: Provider semantic-body output is parsed against an exact JSON
     Schema and Registry capabilities before any target is resolved. Unsupported
     operation types and malformed supplied values are Provider-output errors;
     absent executable facts are a valid partial intent and request user
     clarification. The runtime, not the Provider, attaches all binding hashes.
   - Acceptance: Contract and Provider-stage tests cover valid complete and
     partial single/multiple operation intent, invalid schema, unsupported
     operation, target selectors, parameters, attribute intent, deterministic
     request/model/prompt bindings, and public-only trace evidence.

3. **Deterministic target resolution before ChangeSet**: Every operation intent
   is resolved through the Phase 7 index/query/context contracts before the
   ChangeSet Agent is called.
   - Current: The frozen repair workflow uses a bespoke repair context and
     preselected Wall identity; Phase 7 resolution is a separate CLI.
   - Target: Each operation receives a fingerprint-bound resolution and bounded
     public context. Resolved IFC identities and evidence pointers are the only
     target authority passed to ChangeSet generation.
   - Acceptance: Tests prove exact resolution reaches Stage 2, while
     `not_found`, `ambiguous`, `conflict`, `unsupported`, stale index, and
     context-budget failure do not call the ChangeSet Agent or apply IFC edits.

4. **Structured interactive clarification**: Ambiguous targets, conflicting
   selectors, missing required parameters, and optional user-authorized
   Prototype selection produce one resumable `clarification_required` state.
   - Current: Index query exits with a non-resolved status; there is no general
     interactive continuation contract.
   - Target: The state contains a reason code, safe human question, candidate
     identity/evidence, allowed answer schema, run/stage identity, and no private
     facts. The terminal adapter can ask and continue the same run; API and
     non-interactive CLI return the same state for later continuation.
   - Acceptance: Tests select a candidate, add natural-language detail, reject
     an invalid/out-of-list selection, cancel safely, persist/reload the run,
     and prove completed immutable stages are not repeated after continuation.

5. **Bound ChangeSet stage**: The second Agent stage receives only the public
   request, Registry operation contract, resolved target context, and approved
   semantic authority, then returns one unified ChangeSet.
   - Current: `provider_stage.py` validates one Window Changeset against a
     public spec/context, but the upstream target was not produced by a general
     RepairIntent/resolution workflow.
   - Target: Every operation target/scope ID, evidence pointer, operation type,
     request hash, and model fingerprint is validated. No unresolved, absent,
     stale, cross-operation, or private identifier can enter application.
   - Acceptance: Positive and adversarial tests cover valid multi-operation
     binding and reject out-of-context targets/scope, stale fingerprint/hash,
     missing/foreign evidence pointers, unsupported operation, and partial
     operation binding.

6. **Atomic Audit and application**: A valid unified ChangeSet is audited and
   applied through the Registry as one transaction; no subset is published.
   - Current: `audit.py` and `apply.py` provide deterministic checks and
     transaction staging for the frozen workflow.
   - Target: The general orchestrator invokes those existing authorities once,
     preserves source bytes, records per-operation outcomes, and fails the whole
     run on any precondition, Audit, application, reopen, or postcondition
     failure.
   - Acceptance: An integration fixture with multiple Registry operations
     proves all-or-nothing behavior, source immutability, IFC2X3 reopen, and no
     canonical output when one mandatory operation fails.

7. **Production L2 evidence construction**: The orchestrator builds
   operation-scoped expected semantic facts only from authorized production
   sources and passes them to `evaluate_production`.
   - Current: Phase 8 validates supplied production facts, but its verification
     explicitly leaves Phase 9 responsible for populating them.
   - Target: Precedence is explicit request; surviving target/Host/Type/
     relationship facts; user-approved or formally bound Type/Prototype; then
     deterministic operation policy. Each fact retains source kind/reference,
     applicability, operation ID, and provenance.
   - Acceptance: Tests prove request facts override lower authority, formally
     bound/user-selected Prototype facts are accepted, cross-operation facts
     stay isolated, arbitrary nearby/name/vector/LLM facts are rejected, and
     missing mandatory evidence becomes `not_evaluable`.

8. **Ground Truth isolation**: Production orchestration has no parameter,
   object field, prompt artifact, or evaluation input through which private
   original IFC or mutation mapping can influence generation.
   - Current: The frozen workflow directly combines mutation and benchmark
     evaluation in `_run_window_repair_case`.
   - Target: Benchmark evaluation remains a separate post-production adapter;
     public production start/continue inputs are type-separated and the final
     Provider/public bundle remains canary-scanned.
   - Acceptance: Constructor/signature tests reject Gold inputs; a private
     canary fixture is absent from RepairIntent, both Provider requests,
     TargetQuery/context, ChangeSet, production evaluation, terminal result,
     human output, and public evidence files.

9. **Evaluation-authoritative publication**: Every run ends with a public
   Evaluation 0.2 terminal report, and only
   `successful_artifact_publishable=true` creates the canonical successful IFC
   artifact reference.
   - Current: The Phase 8 Window workflow enforces this for its frozen case,
     but no general start/continue orchestrator consumes that contract.
   - Target: Success publishes the ChangeSet, repaired IFC, public L1/L2 report,
     Provider trace, and manifest. All other states omit a successful IFC path
     and retain any candidate only under diagnostic evidence.
   - Acceptance: Parameterized tests cover clarification, unsupported,
     Provider-invalid, Audit-failed, application-failed, L1-failed,
     L2-failed/not-evaluable, and full-pass terminal states; only the full-pass
     case exposes the canonical IFC path.

10. **Immutable evidence and resumable run lifecycle**: Each run uses a unique
    directory, schema-versioned stage records, atomic transitions, and a final
    hash manifest.
    - Current: `workflow.py` atomically stages one immutable evidence directory,
      but it is not resumable and is tied to a frozen Window benchmark.
    - Target: Start never overwrites an existing run; continue validates the
      stored schema, source fingerprint, last state, and answer before appending
      a transition. Completed artifact hashes remain stable across resume and
      process restart.
    - Acceptance: Tests cover duplicate run/output rejection, interrupted-state
      reload, tampered state/artifact/hash rejection, idempotent terminal reads,
      and manifest coverage for every public artifact.

11. **One API with human and machine CLI adapters**: Python is the behavior
    authority; CLI modes render the same typed results without duplicating
    pipeline logic.
    - Current: `run_case.py` owns frozen-case argument handling and always prints
      the full result JSON.
    - Target: Default TTY mode shows concise stage progress and interactive
      questions; `--non-interactive` never waits for input; `--json` prints a
      compact versioned terminal envelope; `--quiet` suppresses normal progress.
      Full payloads remain referenced files in the run directory.
    - Acceptance: CLI tests cover TTY clarification/continuation, EOF/cancel,
      non-interactive clarification, compact JSON parseability, quiet mode,
      stdout/stderr separation, stable terminal classes/exit codes, and equality
      of CLI artifact references with the Python API result.

12. **Deterministic and live evidence**: Phase 9 acceptance is offline-first
    but retains one real OpenAI-compatible/DeepSeek orchestration UAT path.
    - Current: Fake/live Provider paths exist only for the frozen Window case;
      Phase 8 acceptance made zero Provider calls.
    - Target: Offline fixtures cover every state and enter automated tests. A
      configuration-checked live run exercises both Agent stages and records
      public/redacted trace evidence; its terminal L2 result is reported
      honestly and is not required to pass before Phase 10 authoring closure.
    - Acceptance: Automated tests prove zero network dependency and fake
      Provider call counts; an opt-in live command either produces complete
      redacted UAT evidence or returns a structured configuration/Provider
      failure without being presented as deterministic test success.

## Boundaries

**In scope:**

- Versioned RepairIntent, clarification, persisted run-state, and compact
  terminal-result contracts.
- One Python start/continue/result API and one thin interactive/non-interactive
  CLI.
- Two public Agent stages: request understanding and resolved-context ChangeSet
  generation.
- Phase 7 index/resolution/context integration for each operation intent.
- Production semantic evidence construction for the Phase 8 evaluator.
- Registry-driven Audit/application, Evaluation 0.2 publication enforcement,
  immutable evidence bundle, hashes, and diagnostic retention.
- Deterministic offline state-matrix tests and one opt-in real DeepSeek UAT
  route.

**Out of scope:**

- Manufacturing `damaged.ifc` from a private original in the production API -
  mutation remains benchmark/test setup.
- Using Ground Truth to generate RepairIntent, resolve targets, create a
  ChangeSet, or supply production L2 facts - Gold stays evaluator-only.
- Restoring the known Window Pset/Quantity/Material/Classification/
  `IsExternal` authoring gaps - Phase 10.
- Implementing Opening-only, Door, Beam, or Column operations - Phases 11/12;
  Phase 9 only dispatches operations already registered.
- Automatically selecting a similar Prototype - requires later
  operation-specific deterministic applicability policy.
- Vector retrieval implementation, 128k default input, L3 authoring exactness,
  and curved/free-form wall mutation - later/deferred scope.
- Web UI, server deployment, account/authentication, or a general always-on
  chat REPL - the first interface is one repair-scoped terminal/API session.

## Constraints

- IFC outputs remain IFC2X3 and are created through IfcOpenShell; neither Agent
  may author STEP text.
- The existing source IFC is read-only and must retain its SHA-256 for every
  terminal state.
- SQLite remains the embedded index backend; index reuse requires exact source,
  schema, index/extractor version, and capability compatibility.
- Provider inputs contain only bounded public request/spec/context/contracts;
  the current 65,536-token DeepSeek guard remains unchanged in Phase 9.
- Every public contract is exact-versioned, canonical JSON, schema-validated,
  and size-bounded before Provider or persistence use.
- Agent correction retries are finite, redacted, and evidence-bearing;
  deterministic checks remain authoritative over all Agent output.
- CLI/API status must be locale-independent machine data even when human
  messages are Chinese-first.
- Deterministic acceptance cannot depend on network credentials; live UAT is
  additive evidence.

## Acceptance Criteria

- [ ] One API/CLI starts from a caller-owned IFC plus text, requires no private
  original/GUID fixture arguments, preserves the source hash, and creates an
  immutable run directory.
- [ ] Request understanding emits a schema-valid RepairIntent; deterministic
  Phase 7 resolution and bounded context run before ChangeSet generation.
- [ ] Interactive CLI resolves a candidate/missing-parameter clarification in
  the same run; non-interactive CLI/API return and later resume the identical
  versioned state.
- [ ] The ChangeSet Agent cannot reference any target, scope, evidence pointer,
  operation, request hash, or model fingerprint outside its public authority.
- [ ] Unified multi-operation application is all-or-nothing and leaves the
  caller's source IFC unchanged.
- [ ] Production L2 expected facts retain per-operation authorized provenance;
  unapproved similar/nearby/vector/LLM facts cannot produce a pass.
- [ ] Ground Truth/private canaries are absent from both Provider calls and all
  production/public artifacts.
- [ ] Every terminal path writes Evaluation 0.2; only a full application +
  preservation + mandatory L1 + mandatory L2 pass exposes a successful IFC.
- [ ] Human CLI output is concise; `--json` is a compact stable envelope;
  `--quiet` is silent on normal progress; detailed evidence remains on disk.
- [ ] Resume rejects tampered state, stale source/index, invalid answers, and
  terminal-state mutation while preserving completed artifact hashes.
- [ ] Offline automated tests cover the full terminal matrix with zero Provider
  network calls; an opt-in DeepSeek route records both Agent stages and reports
  its actual L1/L2 outcome without weakening deterministic gates.
- [ ] Phase 7 and Phase 8 regression suites remain green, and the general
  orchestrator contains no hard-coded Window/LargeBuilding IDs or private
  mutation dependency.

## Ambiguity Report

| Dimension | Score | Min | Status | Notes |
|---|---:|---:|---|---|
| Goal Clarity | 0.95 | 0.75 | Met | One input/output workflow and publication authority are explicit. |
| Boundary Clarity | 0.95 | 0.70 | Met | Phase 10-13, Gold, UI, L3, and unsupported operations are separated. |
| Constraint Clarity | 0.90 | 0.65 | Met | IFC2X3, public context, state, Provider, privacy, and offline constraints are locked. |
| Acceptance Criteria | 0.94 | 0.70 | Met | Twelve falsifiable requirements and twelve terminal/integration checks. |
| **Ambiguity** | **0.06** | **<= 0.20** | **Passed** | All dimensions exceed their minimum. |

## Interview Log

| Round | Perspective | Question summary | Decision locked |
|---:|---|---|---|
| 1 | Researcher | Should target understanding and ChangeSet generation be one or two Agent stages? | Two stages with deterministic target resolution between them. |
| 2 | Simplifier | How should ambiguity appear across terminal and API use? | One resumable clarification state; interactive CLI is included in v1. |
| 3 | Boundary Keeper | What belongs on stdout versus the evidence directory? | Concise human output; compact optional JSON; complete immutable artifacts on disk. |
| 4 | Failure Analyst | Can Production L2 use Ground Truth or damaged IFC facts? | Gold is benchmark-only; production uses request and authorized surviving/current evidence. |
| 5 | Seed Closer | When may an existing Type/Prototype supply semantic facts? | Formal binding or explicit user authorization only; similarity can retrieve but not authorize. |

---

*Phase: 09-general-ifc-text-repair-orchestrator*
*Spec created: 2026-07-20*
*Next step: Phase 9 research and executable planning*
