# Phase 6.2 OpenAI Compatibility Report

- Decision: `limited_sdk`
- Implementation route: `native_orchestrator_with_openai_sdk_provider`
- Provider: `mimo-openai-compatible`

## openai_sdk

```json
{
  "content_text": "{\"ok\": true}",
  "evidence_class": "sdk_smoke",
  "finish_reason": "stop",
  "model": "mimo-v2.5-pro",
  "object": "chat.completion",
  "parse_eligible": true,
  "provider": "mimo-openai-compatible",
  "request": {
    "max_completion_tokens": 1024,
    "messages": [
      {
        "content": "Return exactly this JSON object: {\"ok\": true}",
        "role": "user"
      }
    ],
    "model": "mimo-v2.5-pro",
    "temperature": 0
  },
  "response_id": "10a218e773654eda9637e7a0ff7e3a29",
  "status": "passed",
  "usage": {
    "completion_tokens": 29,
    "completion_tokens_details": "[REDACTED]",
    "prompt_tokens": 262,
    "prompt_tokens_details": "[REDACTED]",
    "total_tokens": 291
  }
}
```

## agents_sdk

```json
{
  "evidence_class": "sdk_smoke",
  "final_output": "```json\n{\"ok\": true}\n```",
  "metadata_gaps": [
    "response_id_not_first_class",
    "finish_reason_not_first_class"
  ],
  "response_id": null,
  "status": "limited",
  "usage": {}
}
```

## responses_api

```json
{
  "evidence_class": "sdk_smoke",
  "model": "mimo-v2.5-pro",
  "object": "response",
  "response_id": "resp_c8801db9341046769fa9a28f3b88eaca",
  "status": "passed"
}
```
