# 05-03 Summary: Answer Merge and Draft/Formal Transitions

**Completed:** 2026-06-15
**Plan:** `05-03-PLAN.md`
**Status:** Complete

## Objective

Implement multi-turn answer merging, unknown-answer Draft behavior, explicit
correction recording, and validation-gated formal-ready session transitions.

## Commits

| Type | Commit | Description |
|---|---|---|
| RED | `114e735` | Added failing answer merge and session transition tests plus importable skeletons |
| GREEN | `97fce76` | Implemented answer parsing, merge behavior, unknown handling, corrections, and session validation |

## Implemented

- `src/text2ifc_agent/merge.py`
- `src/text2ifc_agent/session.py`
- `tests/agent/test_answer_merge.py`

The merge/session layer now provides:

- `parse_answer_bundle()`
- `merge_answers()`
- `AgentConfig`
- `AgentSession.start()`
- `AgentSession.next_questions()`
- `AgentSession.apply_answers()`
- `AgentSession.current_status()`

## Behavior

State transitions:

| Input condition | Result |
|---|---|
| user answers a missing fact | answer is appended to transcript and accepted facts |
| user says `不知道` or equivalent | missing fact is marked `unknown`; state stays Draft |
| user gives an explicit correction | new accepted fact records `correction_of`; old fact is preserved |
| all missing facts answered and candidate validates | session becomes `formal_ready` |
| candidate remains invalid after answers | validator issues become new open missing facts |

Unknown-answer examples currently handled:

- `不知道`
- `不清楚`
- `不确定`
- `我不知道`
- `暂时不知道`
- `I do not know`
- `I don't know`
- `unknown`

## Verification

Focused RED verification:

```powershell
python -m pytest tests/agent/test_answer_merge.py -q
```

Expected RED result:

- 6 failed
- failures were missing parse, merge, unknown, correction, and session
  transition behavior.

Focused GREEN verification:

```powershell
python -m pytest tests/agent/test_answer_merge.py -q
```

Result:

- 6 passed

Agent regression:

```powershell
python -m pytest tests/agent -q
```

Result:

- 18 passed

## Requirement Coverage

- **AGENT-01:** Partial. A session can become `formal_ready` only when a
  candidate document passes `validate_v2_document`.
- **AGENT-02:** Continued. Planned questions can be answered and tracked.
- **AGENT-03:** Covered for multi-turn state mechanics: transcript, accepted
  facts, unknown facts, corrections, and status transitions.

## Security and Boundary Notes

- No compiler call is introduced in this plan.
- Formal readiness is gated by `validate_v2_document`.
- Invalid candidates produce new open missing facts instead of defaults.
- Unknown required facts stay Draft and do not create accepted facts.

## Deviations

None.

## Next

Proceed to `05-04-PLAN.md`: add fake/file providers and optional
Anthropic-compatible Mimo adapter with redacted diagnostics.
