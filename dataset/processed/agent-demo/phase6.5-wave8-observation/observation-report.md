# Phase 6.5 Wave 8 Observation Report

## Result

- Batch status: blocked
- Cases observed: 3
- Accepted: 0
- Pre-provider blocked: 3
- Provider calls: 0
- BIM JSON artifacts: 0
- IFC artifacts: 0
- Prompt registry mismatches: 10

## Cases

| Case | Difficulty | Session | Status | Provider call | BIM JSON | IFC |
|---|---|---|---|---:|---:|---:|
| STD-D-MUL-01 | difficult | a9fce5cce1a5f627 | pre_provider_blocked | false | false | false |
| STD-E-RES-01 | easy | b8b756800d9d23ac | pre_provider_blocked | false | false | false |
| STD-M-OFF-01 | medium | 55b6c26a170ce92d | pre_provider_blocked | false | false | false |

## Shared Finding

All three frozen inputs reached session creation and stopped before the first
provider call because the versioned Prompt registry did not match the prompt
files on disk. This batch does not compare model quality across difficulty
levels. It proves that the current checkout cannot start a trustworthy live
Text2IFC run until registry drift is separately approved for repair.

No prompt, registry, schema, Gate, few-shot, or production code was changed
during the observation batch.
