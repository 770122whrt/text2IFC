# Phase 6.4 Supplemental Live Chain Coverage

- provider: `deepseek-openai-compatible`
- accepted_session_hash: `129e4e93ae4e4583`
- nonaccept_session_hash: `0768b6259f2aff83`
- all_required_links_passed: `True`
- passed_required_link_count: `8` / `8`

## Coverage Matrix

| Link | Status | Evidence | Route | Response IDs | Evidence Paths |
|---|---|---|---|---|---|
| `provider_smoke_json` | `passed` | `live_model_verified` | `-` | `d6e24adb-c725-4500-bafb-7cb346f180db` | `smoke-json.json` |
| `accepted_user_input_to_design_brief` | `passed` | `live_model_verified` | `-` | `6d009189-217c-458c-81be-bc98f908fe02` | `calls/01-design-brief/request.redacted.json`<br>`calls/01-design-brief/response.raw.json`<br>`calls/01-design-brief/metrics.json`<br>`design-brief/design-brief.json` |
| `accepted_design_brief_to_bim_json` | `passed` | `live_model_verified` | `-` | `140ad36c-7e57-4f58-ae9e-97dbcdecc779` | `generator/prompt-rendered.md`<br>`generator/trace/request.redacted.json`<br>`generator/trace/response.raw.json`<br>`generator/metrics.json`<br>`generator/candidate.json`<br>`generator/validation.json` |
| `accepted_bim_json_to_deterministic_gates` | `passed` | `deterministic_verified` | `accepted` | - | `gate-summary.json`<br>`geometry-feedback.json`<br>`ifc-verification.json`<br>`case-result.json` |
| `accepted_deterministic_gates_to_audit` | `passed` | `live_model_verified` | `accepted` | `1f6f7cf5-aae0-4b45-b89e-1aed9d22815d` | `audit/prompt-rendered.md`<br>`audit/trace/request.redacted.json`<br>`audit/trace/response.raw.json`<br>`audit/metrics.json`<br>`audit/audit-report.json` |
| `accepted_audit_to_ifc` | `passed` | `artifact_verified` | `accepted` | - | `route-decision.json`<br>`feedback-rounds.json`<br>`output.ifc`<br>`report.md` |
| `nonaccept_user_input_to_design_brief_draft` | `passed` | `live_model_verified` | `-` | `d56e538d-6f86-43f0-91fe-aeaf7c5b3cfe`, `866cd965-d981-4ee0-b965-0794154f3f62`, `a6cf881d-9eea-4b44-a78e-7568433a5ac4`, `ef216096-e6ce-4ade-8116-9dde38f15705`, `69bb3321-1f1d-4c7f-b255-621e7993cd1f` | `calls`<br>`design-brief.json`<br>`conversation.json` |
| `nonaccept_issues_to_ask_user` | `passed` | `artifact_verified` | `ask_user` | - | `issues.json`<br>`route-decision.json`<br>`feedback-rounds.json`<br>`case-result.json`<br>`report.md` |
