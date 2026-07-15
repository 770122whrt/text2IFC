# MiMo OpenAI API Compatibility

Source: https://mimo.mi.com/docs/en-US/api/chat/openai-api
Fetched: 2026-06-23
Official page update time: 2026-06-03

This document records the MiMo OpenAI-compatible chat API details needed for
the Phase 6.2 interactive CLI and Agents SDK feasibility work. It is a
reference document, not a secret store. Do not paste real API keys, provider
URLs, bearer headers, or `.env` contents into prompts, traces, reports,
commits, or terminal logs.

## Endpoint

The documented chat-completions endpoint is:

```text
https://api.xiaomimimo.com/v1/chat/completions
```

For local development, the project may keep a base URL in `OpenAI_BASE_URL`.
If the configured value does not already end in `/v1`, OpenAI-compatible
client code should append `/v1` before calling `chat.completions`.

## Authentication

The page documents two supported authentication methods.

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

Phase 6.2 should support the user-local `API_KEY` name, and may also support
`MIMO_API_KEY` or `OPENAI_API_KEY` as compatibility names. Trace artifacts must
redact header values and must not persist the private base URL.

## Basic Chat Request Shape

The default request is a `POST` to `/v1/chat/completions` with fields such as:

- `model`: for example `mimo-v2.5-pro`
- `messages`: OpenAI-style chat messages
- `max_completion_tokens`: example value `1024`
- `temperature`: example value `1.0`
- `top_p`: example value `0.95`
- `stream`: `false` for non-streaming
- `stop`: `null` when unused
- `frequency_penalty` and `presence_penalty`
- `thinking`: for example `{ "type": "disabled" }`

Non-secret curl sketch:

```bash
curl --location --request POST \
  "https://api.xiaomimimo.com/v1/chat/completions" \
  --header "api-key: ${MIMO_API_KEY}" \
  --header "Content-Type: application/json" \
  --data-raw '{
    "model": "mimo-v2.5-pro",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "please introduce yourself"
      }
    ],
    "max_completion_tokens": 1024,
    "temperature": 1.0,
    "top_p": 0.95,
    "stream": false,
    "stop": null,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "thinking": {
      "type": "disabled"
    }
  }'
```

OpenAI Python SDK sketch:

```python
import os
from openai import OpenAI

base_url = os.environ["OpenAI_BASE_URL"].rstrip("/")
if not base_url.endswith("/v1"):
    base_url += "/v1"

client = OpenAI(
    base_url=base_url,
    api_key=os.environ["API_KEY"],
)

response = client.chat.completions.create(
    model=os.environ.get("TEXT2IFC_MIMO_MODEL", "mimo-v2.5-pro"),
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "please introduce yourself"},
    ],
    temperature=1.0,
    max_completion_tokens=1024,
)
```

## Non-streaming Response Shape

The page's response example follows the OpenAI chat-completion shape:

```json
{
  "id": "example-chat-completion-id",
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "message": {
        "content": "...",
        "role": "assistant",
        "tool_calls": null
      }
    }
  ],
  "created": 1776848906,
  "model": "mimo-v2.5-pro",
  "object": "chat.completion",
  "usage": {
    "completion_tokens": 72,
    "prompt_tokens": 57,
    "total_tokens": 129,
    "completion_tokens_details": {
      "reasoning_tokens": 0
    },
    "prompt_tokens_details": null
  }
}
```

Fields that matter for text2IFC live evidence:

- `id`: provider response ID retained as evidence.
- `object`: should be `chat.completion` for non-streaming chat completions.
- `model`: provider model used for the call.
- `choices[].finish_reason`: successful non-truncated calls should normally
  finish with `stop`; `length` indicates truncation and must block accepted
  semantic parsing.
- `choices[].message.content`: model text to parse as the expected JSON
  contract.
- `choices[].message.tool_calls`: relevant for future tool/handoff spikes.
- `usage`: token accounting to retain in metrics.

## Capabilities Mentioned by the Page

The page includes example tabs or sections for:

- default
- streaming
- function call
- web search
- image input
- audio input
- video input
- speech synthesis
- structured output
- deep thinking

The visible captured text contains the default request and response shape. The
tab names are not enough to assume complete compatibility with OpenAI Agents
SDK behavior; Phase 6.2 must verify each needed feature through live smoke
tests before relying on it.

## Local Smoke Findings

Verified from this worktree on 2026-06-23:

- Raw HTTP `POST /v1/chat/completions` succeeded with HTTP 200 and returned
  `id`, `object: chat.completion`, `model`, `choices[].finish_reason`, and
  `usage`.
- Raw HTTP `POST /v1/responses` returned 404. Do not assume Responses API
  support unless a later official document or live test proves otherwise.
- OpenAI Python SDK `OpenAI(base_url=..., api_key=...)` can call
  `client.chat.completions.create(...)` against MiMo.
- A too-small token limit produced `finish_reason: length`; Phase 6.2 must
  treat truncation as a blocked semantic result, not as a usable answer.

## OpenAI Agents SDK Implication

The OpenAI Agents SDK project says it is a framework for multi-agent workflows
and supports the OpenAI Responses and Chat Completions APIs.

Source: https://github.com/openai/openai-agents-python

The repository's quick-start install command is:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install openai-agents
```

For text2IFC, the SDK should be treated as a Phase 6.2 feasibility candidate,
not as an automatic replacement for the existing pipeline. The project must
retain its own:

- prompt registry and hashes;
- Design Brief and BIM JSON schema validation;
- deterministic generation gates;
- IFC compiler and reopen checks;
- geometry checks;
- generated `report.md`;
- artifact secret scan.

## Phase 6.2 Adapter Requirements

1. Prefer `OpenAI_BASE_URL` / `OPENAI_BASE_URL`-style configuration for the
   OpenAI-compatible path, while preserving existing Anthropic-compatible
   configuration for Phase 6.1 history.
2. Support `API_KEY` without writing the key value to artifacts.
3. Keep all raw responses, redacted requests, response IDs, model names,
   finish reasons, usage, and normalized model text in trace sidecars.
4. Reject `finish_reason: length` for semantic stage acceptance.
5. Verify streaming, function/tool calling, structured output, and Agents SDK
   compatibility through explicit live smoke tests before relying on them.
6. Never let an SDK agent bypass BIM JSON 2.0 validation, IFC reopen checks, or
   geometry gates.
