# 05-04 Summary: Provider Boundary and Secret Safety

**Completed:** 2026-06-15
**Plan:** `05-04-PLAN.md`
**Status:** Complete

## Objective

Add deterministic fake/file Agent providers and an optional Anthropic-compatible
Mimo adapter behind redacted runtime configuration.

## Commits

| Type | Commit | Description |
|---|---|---|
| RED | `0d14a22` | Added failing provider, Mimo config, redaction, and guardrail tests |
| GREEN | `e521c68` | Implemented fake/file providers, provider output diagnostics, Mimo config check, optional live adapter, and raw IFC/STEP guardrails |

## Implemented

- `src/text2ifc_agent/providers.py`
- `scripts/agent/run_mimo_smoke.py`
- `tests/agent/test_agent_providers.py`

The provider layer now provides:

- `ProviderOutput`
- `FakeAgentProvider`
- `FileAgentProvider`
- `MimoAgentProvider`
- `load_mimo_config_from_env()`
- `redact_provider_payload()`
- `validate_provider_output()`

## Provider Modes

| Mode | Purpose | Network required |
|---|---|---|
| fake | deterministic tests and scripted demos | no |
| file | replay saved provider responses | no |
| mimo | optional live smoke with Anthropic-compatible endpoint | yes, only for `--prompt-only` |

## Config Check

Command:

```powershell
python scripts/agent/run_mimo_smoke.py --check-config
```

Result in this environment:

```json
{
  "base_url_configured": false,
  "configured": false,
  "missing": [
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "TEXT2IFC_MIMO_MODEL"
  ],
  "model": null,
  "provider": "mimo",
  "required_env": [
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "TEXT2IFC_MIMO_MODEL"
  ],
  "token_configured": false
}
```

This is non-blocking for deterministic tests. It reports environment variable
names only and does not print credential values or provider URLs.

## Verification

Focused RED verification:

```powershell
python -m pytest tests/agent/test_agent_providers.py -q
```

Expected RED result:

- 8 failed
- failures were missing provider replay, diagnostics, redaction, guardrails,
  and config reporting behavior.

Focused GREEN verification:

```powershell
python -m pytest tests/agent/test_agent_providers.py -q
```

Result:

- 8 passed

Config check:

```powershell
python scripts/agent/run_mimo_smoke.py --check-config
```

Result:

- exit 0
- `configured: false` with missing env var names only

Agent regression:

```powershell
python -m pytest tests/agent -q
```

Result:

- 26 passed

## Security and Boundary Notes

- Provider output containing raw IFC/STEP or low-level helper entities is
  rejected before merge.
- Metadata redaction reuses the Agent state redaction path.
- Fake/file providers are deterministic and do not require credentials.
- Live Mimo behavior is optional and isolated behind runtime env vars.

## Deviations

The optional live smoke was not run because this verification path does not
require live credentials. `--check-config` is the deterministic gate for this
plan.

## Next

Proceed to `05-05-PLAN.md`: scripted Chinese clarification demo that writes
and reopens `dataset/processed/agent-demo/simple-room/output.ifc`.
