# Phase 9: General IFC + Text Repair Orchestrator - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution
> agents. Decisions are captured in `09-CONTEXT.md`; this log preserves the
> alternatives considered.

**Date:** 2026-07-20
**Phase:** 09-general-ifc-text-repair-orchestrator
**Areas discussed:** Agent call architecture, clarification modes, CLI/API and artifacts, Production L2 authority, Type/Prototype authorization

---

## Agent call architecture

| Option | Description | Selected |
|---|---|---|
| Two-stage Agent | Text first becomes RepairIntent/TargetQuery; deterministic resolution precedes ChangeSet generation | Yes |
| One combined call | Agent emits unresolved target query and ChangeSet together | No |

**User's choice:** Two-stage Agent architecture accepted.

**Notes:** Phase 7 deliberately deferred natural-language-to-TargetQuery to
Phase 9. The second call receives resolved, bounded public context rather than
raw IFC.

---

## Clarification modes

| Option | Description | Selected |
|---|---|---|
| Interactive CLI | One repair session asks for target/parameter clarification and continues the same run | Yes |
| Non-interactive CLI | Returns structured `clarification_required` for scripts/CI | Yes |
| Python API | Returns the same state for an upper layer to render and resume | Yes |

**User's choice:** All three presentations are valid once clarified as adapters
over one shared state machine; interactive behavior is required in the first
version.

**Notes:** This is not three repair pipelines and not an always-on chat REPL.
The default terminal adapter interacts within one run; automation and APIs
receive the same persisted state and can continue by `run_id`.

---

## CLI output and run artifacts

| Option | Description | Selected |
|---|---|---|
| Full JSON on stdout | Print complete context, traces, ChangeSet and evaluation to the terminal | No |
| Human summary by default | Concise progress/status and artifact paths; detailed evidence remains in the run directory | Yes |
| Compact `--json` | Stable machine terminal envelope with status and artifact references | Yes |

**User's choice:** Human-readable interactive output by default, compact JSON
only when explicitly requested, and detailed immutable artifacts on disk.

**Notes:** A non-passing candidate is clearly diagnostic and never appears at
the successful IFC path.

---

## Production L2 authority

| Option | Description | Selected |
|---|---|---|
| Ground Truth-assisted production | Use private original facts to help the Agent repair the model | No |
| Authorized current evidence | Request, surviving current/damaged IFC facts, approved Type/Prototype, then deterministic policy | Yes |
| Similarity/LLM inference | Copy nearby semantics or use common knowledge when facts are missing | No |

**User's choice:** Production and Benchmark are strictly separated. Ground
Truth is private post-application benchmark evidence; real production uses only
authorized non-Gold evidence and discloses missing facts.

**Notes:** Required unknowns become `not_evaluable`; conditionally absent
Material/Pset facts follow the Phase 8 `not_required` policy.

---

## Type and Prototype authorization

| Option | Description | Selected |
|---|---|---|
| Formal existing binding | Reuse a Type already bound to the current target through IFC relationships | Yes |
| User-authorized Prototype | User names or selects an evidence-bearing Type/existing instance | Yes |
| Automatic similar entity | Silently select nearest/name-similar/same-storey/vector-similar entity | No |

**User's choice:** The system may retrieve and display Prototype candidates but
cannot choose one for the user unless a future operation-specific deterministic
policy explicitly authorizes it.

**Notes:** Vector retrieval can improve recall later, but similarity alone is
never semantic authority.

## the agent's Discretion

- Internal state-machine class names and persisted representation.
- Finite Agent correction/retry count and exact retry prompts.
- Stable exit-code values, progress wording, run-id format, and fingerprint-safe
  index cache layout.

## Deferred Ideas

- Window semantic authoring closure belongs to Phase 10.
- Opening/Door and Beam/Column operations belong to Phases 11/12.
- Vector matching and 128k experiments belong to Phase 13 or later.
- L3 exactness and curved/free-form wall mutation remain deferred.
