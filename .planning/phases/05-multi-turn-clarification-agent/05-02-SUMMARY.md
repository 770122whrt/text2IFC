# 05-02 Summary: Missing Facts to Chinese Questions

**Completed:** 2026-06-15
**Plan:** `05-02-PLAN.md`
**Status:** Complete

## Objective

Map validator and Draft missing-fact diagnostics into bounded, user-facing
Chinese clarification questions.

## Commits

| Type | Commit | Description |
|---|---|---|
| RED | `ba69e37` | Added failing question planner tests and importable skeleton |
| GREEN | `0b9fc84` | Implemented validator/Draft missing-fact normalization, ranking, and 1-3 question planning |

## Implemented

- `src/text2ifc_agent/questions.py`
- `tests/agent/test_question_planner.py`

The planner now provides:

- `missing_facts_from_validator_issues()`
- `missing_facts_from_draft()`
- `rank_missing_facts()`
- `plan_questions()`

## Behavior

Representative mappings:

| Missing fact source | User-facing Chinese question |
|---|---|
| missing room/space representation | `房间的长、宽、高分别是多少？` |
| missing storey/floor reference | `这个构件属于哪一个楼层？请提供楼层名称或标高。` |
| missing door placement | `这扇门位于哪面墙上？门洞在墙上的水平位置和底部高度是多少？` |
| missing window placement | `这扇窗位于哪面墙上？窗在墙上的水平位置、窗台高度和尺寸是多少？` |

Question planning:

- filters to open missing facts;
- ranks storey/floor, room size, wall facts, door placement, then window
  placement;
- returns at most 3 questions per turn;
- keeps unasked facts open in state for later turns.

## Verification

Focused RED verification:

```powershell
python -m pytest tests/agent/test_question_planner.py -q
```

Expected RED result:

- 4 failed, 1 passed
- failures were missing validator/Draft question generation behavior.

Focused GREEN verification:

```powershell
python -m pytest tests/agent/test_question_planner.py -q
```

Result:

- 5 passed

Agent regression:

```powershell
python -m pytest tests/agent -q
```

Result:

- 12 passed

## Requirement Coverage

- **AGENT-02:** Covered for foundational missing-fact to question mapping and
  1-3 batching.
- **AGENT-03:** Extended. Open missing facts remain in Agent state across
  bounded question planning.

## Security and Boundary Notes

- User-facing questions avoid low-level IFC terms such as `IfcCartesianPoint`,
  `IfcDirection`, `IfcOwnerHistory`, STEP IDs, raw JSON paths, and schema
  wording.
- The planner does not infer or fill missing facts; it only asks questions.
- No provider, network, or compiler behavior was introduced in this plan.

## Deviations

None.

## Next

Proceed to `05-03-PLAN.md`: merge user answers, preserve transcript/facts, and
keep unknown required facts as Draft.
