# MiMo Anthropic API Compatibility

Source: https://mimo.mi.com/docs/en-US/api/chat/anthropic-api  
Fetched: 2026-06-23  
Official page update time: 2026-06-03

This document records the MiMo Anthropic-compatible chat API details needed by
the text2IFC live multi-agent pipeline. It is a project-readable reference, not
an API secret store. Do not paste real API keys into this file, traces,
reports, prompts, commits, or terminal logs.

## Endpoint

The Anthropic-compatible Messages endpoint is:

```text
https://api.xiaomimimo.com/anthropic/v1/messages
```

For text2IFC, this means the configured base URL should resolve to the
`/anthropic/v1/messages` route used by the live provider. If the project stores
a base URL rather than the full message endpoint, the provider must append the
correct path exactly once.

## Authentication

The official page documents two accepted authentication styles.

### Method 1: `api-key`

```http
api-key: $MIMO_API_KEY
Content-Type: application/json
```

### Method 2: bearer token

```http
Authorization: Bearer $MIMO_API_KEY
Content-Type: application/json
```

Project implication:

- The user-local `.env` may expose the key as `API_KEY`.
- The provider should map `API_KEY` to the MiMo API key without writing the
  value to artifacts.
- `MIMO_API_KEY` is the name used in the official examples.
- Older project names such as `ANTHROPIC_AUTH_TOKEN` may be supported only as a
  compatibility fallback.
- The old Anthropic-style `x-api-key` header is not the header name shown on
  the MiMo page. Prefer `api-key` for MiMo unless a future official document
  states otherwise.

## Basic Request Shape

The page's default example is a non-streaming `POST` request with:

- `model`: for example `mimo-v2.5-pro`
- `max_tokens`: example value `1024`
- `system`: system prompt string
- `messages`: Anthropic-style message array
- `top_p`: example value `0.95`
- `stream`: `false` for non-streaming
- `temperature`: example value `1.0`
- `stop_sequences`: `null` when unused
- `thinking`: an object; the default example disables thinking

Adapted non-secret curl example:

```bash
curl --location --request POST \
  "https://api.xiaomimimo.com/anthropic/v1/messages" \
  --header "api-key: ${MIMO_API_KEY}" \
  --header "Content-Type: application/json" \
  --data-raw '{
    "model": "mimo-v2.5-pro",
    "max_tokens": 1024,
    "system": "You are a helpful assistant.",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "please introduce yourself"
          }
        ]
      }
    ],
    "top_p": 0.95,
    "stream": false,
    "temperature": 1.0,
    "stop_sequences": null,
    "thinking": {
      "type": "disabled"
    }
  }'
```

Equivalent Python sketch:

```python
import os
import requests

endpoint = "https://api.xiaomimimo.com/anthropic/v1/messages"
api_key = os.environ["MIMO_API_KEY"]

payload = {
    "model": "mimo-v2.5-pro",
    "max_tokens": 1024,
    "system": "You are a helpful assistant.",
    "messages": [
        {
            "role": "user",
            "content": [{"type": "text", "text": "please introduce yourself"}],
        }
    ],
    "top_p": 0.95,
    "stream": False,
    "temperature": 1.0,
    "stop_sequences": None,
    "thinking": {"type": "disabled"},
}

response = requests.post(
    endpoint,
    headers={"api-key": api_key, "Content-Type": "application/json"},
    json=payload,
    timeout=120,
)
response.raise_for_status()
message = response.json()
```

## Non-streaming Response Shape

The default response follows an Anthropic-like message envelope:

```json
{
  "id": "example-message-id",
  "type": "message",
  "role": "assistant",
  "model": "mimo-v2.5-pro",
  "stop_reason": "end_turn",
  "content": [
    {
      "type": "text",
      "text": "..."
    }
  ],
  "usage": {
    "input_tokens": 57,
    "output_tokens": 54
  }
}
```

Fields that matter for text2IFC live gates:

- `id`: provider response ID retained as evidence.
- `model`: provider model used for the call.
- `stop_reason`: must be read from the response. For accepted text2IFC
  semantic stages, `end_turn` is the expected successful terminal reason.
- `content[].type`: should contain text blocks for the current provider
  adapter.
- `content[].text`: model text to parse as the expected JSON contract.
- `usage.input_tokens` and `usage.output_tokens`: token accounting to retain in
  metrics.

## Supported Modes Mentioned by the Page

The page navigation lists these request examples or tabs:

- default
- streaming
- function call
- image input
- deep thinking

The static text captured for this project exposes the default non-streaming
example and its response. The other tabs are acknowledged here but not
reconstructed, because their full request/response bodies were not visible in
the captured page text. Do not infer missing fields for text2IFC from tab names
alone.

## Model Notice

The page banner says legacy `MiMo-V2-Flash` and TTS names are being routed or
deprecated in June 2026 and recommends migration to the V2.5 series. For
Phase 6.1, keep using the explicitly configured V2.5 model, such as
`mimo-v2.5-pro`, unless a newer project decision changes the model.

## text2IFC Adapter Requirements

For this repository, the MiMo adapter should:

1. Read the live key from `API_KEY` or `MIMO_API_KEY`, with any legacy
   Anthropic variable handled as a documented fallback only.
2. Use the official `api-key` header for MiMo requests.
3. Keep `Content-Type: application/json`.
4. Preserve exact response metadata: `id`, `model`, `stop_reason`, and
   `usage`.
5. Treat non-`end_turn` terminal reasons as blocked unless a plan explicitly
   defines a safe alternative.
6. Never persist key values, bearer headers, full `.env` contents, or private
   proxy URLs.
7. Redact request headers in trace artifacts.
8. Keep semantic Agent outputs constrained to Design Brief, Draft, Audit, or
   BIM JSON contracts; never ask MiMo to emit raw IFC/STEP text.

## Known Difference From Current Project History

Earlier Phase 5 and Phase 6 code used Anthropic-compatible environment names
such as `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_BASE_URL`. That was compatible
with the earlier local setup, but the official MiMo page documents
`MIMO_API_KEY` examples and the user has now provided `API_KEY` in `.env`.

The next implementation step should therefore be a TDD change that:

- accepts `API_KEY` in the config loader;
- sends `api-key` rather than `x-api-key` for MiMo;
- keeps secret redaction updated for `API_KEY`, `MIMO_API_KEY`, and legacy
  names;
- reruns the MiMo live smoke request before claiming provider connectivity.
