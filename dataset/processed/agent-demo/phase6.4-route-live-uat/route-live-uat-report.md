# Phase 6.4 Route-Level Live UAT

- all_required_routes_live_checked: `True`
- passed_case_count: `8` / `8`
- missing_required_routes: `[]`

## Route Classes

- auto_resolved_routes: `['regenerate_json', 'repair_json', 'revise_design_brief']`
- correct_terminal_routes: `['ask_user', 'blocked_as_unsupported', 'gate_issue', 'runtime_blocked']`
- retry_control_routes: `['provider_retry']`

## Boundary

Routes with auto_resolved_live prove a live model correction action. Routes with correct_terminal_live prove the workflow should stop, ask the user, or require human/developer review instead of fabricating a fix. provider_retry proves retry-control evidence, not model self-repair.

## Cases

| Case | Route | Status | Response ID | Evidence |
|---|---|---|---|---|
| `ask_user` | `ask_user` | `correct_terminal_live` | `65393a90-7d15-4762-8549-0d9ae5c5acf7` | `cases/ask_user/request.redacted.json`<br>`cases/ask_user/response.raw.json`<br>`cases/ask_user/parsed-output.json` |
| `blocked_as_unsupported` | `blocked_as_unsupported` | `correct_terminal_live` | `02661331-a39d-47b5-b2a6-e09729c12c10` | `cases/blocked_as_unsupported/request.redacted.json`<br>`cases/blocked_as_unsupported/response.raw.json`<br>`cases/blocked_as_unsupported/parsed-output.json` |
| `gate_issue` | `gate_issue` | `correct_terminal_live` | `6a8e2a74-5d01-47ff-9af9-349f71a6d90a` | `cases/gate_issue/request.redacted.json`<br>`cases/gate_issue/response.raw.json`<br>`cases/gate_issue/parsed-output.json` |
| `provider_retry` | `provider_retry` | `retry_control_live` | `0b068773-0c12-4a4d-9c59-fcf1b4d3244f` | `cases/provider_retry/request.redacted.json`<br>`cases/provider_retry/response.raw.json`<br>`cases/provider_retry/parsed-output.json` |
| `regenerate_json` | `regenerate_json` | `auto_resolved_live` | `983935af-ecd6-4728-86f1-41db8013dbc1` | `cases/regenerate_json/request.redacted.json`<br>`cases/regenerate_json/response.raw.json`<br>`cases/regenerate_json/parsed-output.json` |
| `repair_json` | `repair_json` | `auto_resolved_live` | `31befec5-8d76-42d1-99d4-15292c029a98` | `cases/repair_json/request.redacted.json`<br>`cases/repair_json/response.raw.json`<br>`cases/repair_json/parsed-output.json` |
| `revise_design_brief` | `revise_design_brief` | `auto_resolved_live` | `7cd3b3f9-db27-4da1-8ddb-b308ba57242a` | `cases/revise_design_brief/request.redacted.json`<br>`cases/revise_design_brief/response.raw.json`<br>`cases/revise_design_brief/parsed-output.json` |
| `runtime_blocked` | `runtime_blocked` | `correct_terminal_live` | `e28e5bec-6c96-442a-be5c-65fc0ee2924c` | `cases/runtime_blocked/request.redacted.json`<br>`cases/runtime_blocked/response.raw.json`<br>`cases/runtime_blocked/parsed-output.json` |
