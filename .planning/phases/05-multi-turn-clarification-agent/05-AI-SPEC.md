# Phase 5: Multi-turn Clarification Agent - AI Design Contract

**Created:** 2026-06-15
**Status:** Ready for planning

## 1. System Classification

Phase 5 is a structured conversational extraction and clarification system.
It is not a free-form design chatbot and not a raw IFC generator.

The Agent has one job: collect enough explicit user facts to produce valid BIM
JSON 2.0, then pass that JSON to the deterministic IFC2X3 compiler.

### Domain Context

Good behavior:

- asks short Chinese questions about missing building facts;
- asks at most 1-3 questions per turn;
- preserves what the user already said;
- says the state is Draft when required facts are unknown;
- compiles only after formal BIM JSON 2.0 validation passes;
- writes an IFC file only from formal BIM JSON.

Bad behavior:

- invents dimensions, storeys, placements, openings, or relationships;
- asks the user for low-level IFC implementation objects;
- outputs raw IFC/STEP text;
- overwrites previous user facts without explicit correction;
- hides missing facts behind a default template;
- leaks provider tokens, headers, or URLs into artifacts.

Stakes:

- A plausible but fabricated building model is worse than an explicit Draft.
- A valid-looking IFC file must still be traceable to user-provided facts.
- Provider failures must not block deterministic local tests.

## 2. Selected Framework

Selected approach: lightweight in-repo state machine plus provider adapter.

Rationale:

- The first Phase 5 goal is narrow and testable: missing-fact detection,
  Chinese question planning, answer merging, validation, and IFC compilation.
- Existing Phase 3 code already has provider abstraction, fake/file modes, and
  evaluation harnesses.
- A heavyweight agent framework would add persistence and orchestration before
  the domain contract is stable.
- The state machine can later be wrapped by LangGraph or another workflow
  framework if production persistence, branching, or observability needs grow.

Alternative considered: LangGraph.

LangGraph is a good future option for durable, branching, audited production
workflows. It is not the right first implementation because Phase 5 can prove
the product behavior with simpler code and deterministic tests.

## 3. Implementation Pattern

Suggested entry points:

```python
from text2ifc_agent.session import AgentSession, AgentConfig

session = AgentSession.start(
    user_text=request_text,
    config=AgentConfig(language="zh-CN", max_questions=3),
    provider=provider,
)

while session.state.status == "needs_clarification":
    questions = session.next_questions()
    answers = answer_source.answer(questions)
    session = session.apply_answers(answers)

result = session.finalize(output_ifc_path)
```

Provider boundary:

```python
class AgentProvider(Protocol):
    def generate_candidate(
        self,
        *,
        prompt: str,
        schema: dict[str, Any],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """Return raw model text and metadata; never write secrets."""
```

The implementation should prefer standard library HTTP for the first Mimo
adapter unless an installed SDK is already available. Fake/file providers stay
the default for tests.

## 4. Structured Output Contract

The model-facing output target is semantic BIM JSON 2.0 or a Draft update. It
must not include raw IFC, STEP lines, compiler-only objects, or low-level IFC
resource entities.

Pydantic-style shape for Agent state validation:

```python
class MissingFact(BaseModel):
    id: str
    code: str
    path: str
    question_zh: str
    status: Literal["open", "answered", "unknown", "deferred"]
    source: Literal["schema", "validator", "draft", "agent"]

class AgentTurn(BaseModel):
    role: Literal["user", "agent", "system"]
    content: str
    question_ids: list[str] = []

class AgentState(BaseModel):
    schema_version: Literal["text2ifc/agent-state-v1"]
    language: Literal["zh-CN"]
    status: Literal["draft", "needs_clarification", "formal_ready", "compiled"]
    original_request: str
    transcript: list[AgentTurn]
    missing_facts: list[MissingFact]
    accepted_facts: list[dict[str, Any]]
    candidate_document: dict[str, Any] | None
```

JSON Schema remains the source of truth for BIM JSON itself. Pydantic, if used,
is only for Agent state and provider input/output hygiene.

## 5. Evaluation Strategy

| Dimension | Metric | Gate |
|---|---|---|
| Chinese interaction | question language and no schema jargon | required |
| Question batching | 1-3 questions per turn | required |
| Missing-fact handling | no defaults; unknown stays Draft | required |
| Merge correctness | prior facts preserved; corrections explicit | required |
| Formal validation | `validate_v2_document` passes before compile | required |
| IFC compilation | output IFC exists and reopens | required |
| Provider safety | fake/file tests pass without network | required |
| Secret safety | artifact scan finds env var names only, no values | required |
| Live smoke | Mimo adapter either succeeds or fails diagnostically | non-blocking unless credentials are explicitly required |

Reference cases should start with:

- incomplete simple-room request missing dimensions and openings;
- request with more than 3 missing facts;
- user answers "I do not know";
- two-turn successful simple-room completion;
- invalid provider JSON;
- Draft provider response;
- successful scripted IFC demo.

## 6. Guardrails

- Online guardrail: reject raw IFC/STEP or low-level IFC helper entities from
  provider output.
- Online guardrail: refuse compilation unless formal BIM JSON 2.0 validation
  passes.
- Online guardrail: redact provider metadata before writing transcripts.
- Offline gate: scan generated Agent artifacts for credential-like strings.
- Offline gate: compile/reopen the final IFC demo output.

## 7. Tracing and Artifacts

The first tracing mechanism is deterministic local artifact logging:

- `transcript.json`
- `state.json`
- `candidate.json`
- `diagnostics.json`
- `metrics.json`
- `report.md`
- `output.ifc`

External tracing tools are deferred until provider behavior and interaction
metrics stabilize.

## 8. Checklist

- [x] Framework selected with rationale.
- [x] Domain good/bad/stakes rubric defined.
- [x] Provider boundary selected.
- [x] Structured Agent state shape sketched.
- [x] Evaluation dimensions defined.
- [x] Guardrails defined.
- [x] Final IFC artifact required.

---

*Phase: 05-multi-turn-clarification-agent*
