# Multi-storey Prompt and Input Hardening Implementation Plan

> **For agentic workers:** Execute the tasks in order. Use TDD: record the RED
> result before changing a production asset, then verify GREEN.

**Goal:** Make the controlled two-storey input geometrically self-consistent
and teach the Design Brief and Generator the placement facts required to keep
multi-storey doors, windows, and openings on their intended host walls.

**Architecture:** This is an asset-only hardening patch. The diagnosis CLI
continues to send a Chinese natural-language request, but that request includes
a compact, named coordinate contract. Prompt assets turn invalid layout facts
into Draft/clarification rather than a ready Design Brief. The generator few
shot demonstrates parent-relative placement on a rotated host wall.

**Tech Stack:** Python/pytest, versioned Markdown prompts, JSON few-shot asset.

---

### Task 1: Lock the controlled input contract

**Files:**
- Modify: `scripts/agent/run_phase6_4_multistorey_diagnosis.py`
- Modify: `tests/agent/test_phase6_4_multistorey_diagnosis.py`

- [ ] Add a failing test that requires a `CONTROL_LAYOUT_V2` block with
  non-overlapping named space rectangles, an explicit stair opening, and door
  centers on shared wall segments.
- [ ] Run the focused test and record the expected RED failure.
- [ ] Replace the contradictory two-storey prompt with the controlled V2 input.
- [ ] Re-run the focused test and record GREEN.

### Task 2: Preserve and validate layout facts in the Design Brief prompt

**Files:**
- Modify: `prompts/agent/design-brief-v2.1.md`
- Modify: `tests/agent/test_mimo_prompt_assets.py`
- Modify: `prompts/agent/registry.json`

- [ ] Add a failing prompt-asset test for explicit coordinate preservation and
  the three invalid-layout outcomes: overlap, no shared host segment, and
  stair-opening/space collision.
- [ ] Run the focused test and record RED.
- [ ] Add only those explicit rules to the Design Brief prompt; require
  clarification/Draft rather than silently deriving a replacement layout.
- [ ] Refresh the prompt registry SHA-256 and verify GREEN.

### Task 3: Teach rotated-host local placement in the generator few shot

**Files:**
- Modify: `prompts/agent/bim-json-generator-v2.md`
- Modify: `prompts/agent/few-shots/bim-json-generator-v2-two-storey-standard.json`
- Modify: `tests/agent/test_mimo_prompt_assets.py`
- Modify: `prompts/agent/registry.json`

- [ ] Add a failing test requiring a rotated wall, a non-zero host-local
  opening offset, and a filling with zero local offset/identity direction.
- [ ] Run the focused test and record RED.
- [ ] Add the narrow Generator contract and extend the existing two-storey
  few-shot with a rotated host-wall example and paired void/fill relations.
- [ ] Refresh the registry SHA-256 and verify GREEN.

### Task 4: Verify asset rendering and regressions

**Files:**
- Test: `tests/agent/test_phase6_4_multistorey_diagnosis.py`
- Test: `tests/agent/test_mimo_prompt_assets.py`
- Test: `tests/agent/test_prompt_registry.py`

- [ ] Run the focused asset tests.
- [ ] Run the Phase 6.4 prompt/route regression subset and `compileall`.
- [ ] Do not run DeepSeek live until the local contract tests pass; report the
  exact live command as the next verification checkpoint.
