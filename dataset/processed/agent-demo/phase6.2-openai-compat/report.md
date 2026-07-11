# Phase 6.2 OpenAI Compatibility Report

- Decision: `limited_sdk`
- Implementation route: `native_orchestrator_with_openai_sdk_provider`
- Provider: `deepseek-openai-compatible`

## openai_sdk

```json
{
  "content_text": "{\"ok\": true}",
  "evidence_class": "sdk_smoke",
  "finish_reason": "stop",
  "model": "deepseek-v4-flash",
  "object": "chat.completion",
  "parse_eligible": true,
  "provider": "deepseek-openai-compatible",
  "request": {
    "max_tokens": 131072,
    "messages": [
      {
        "content": "Return exactly this JSON object: {\"ok\": true}",
        "role": "user"
      }
    ],
    "model": "deepseek-v4-flash",
    "response_format": {
      "type": "json_object"
    },
    "temperature": 0
  },
  "response_id": "7034109e-e447-499c-bbdd-1f898a91f611",
  "status": "passed",
  "usage": {
    "completion_tokens": 25,
    "completion_tokens_details": "[REDACTED]",
    "prompt_cache_hit_tokens": "[REDACTED]",
    "prompt_cache_miss_tokens": "[REDACTED]",
    "prompt_tokens": 35,
    "prompt_tokens_details": "[REDACTED]",
    "total_tokens": 60
  }
}
```

## agents_sdk

```json
{
  "evidence_class": "sdk_smoke",
  "final_output": "{\"ok\": true}",
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
  "error_type": "NotFoundError",
  "evidence_class": "sdk_smoke",
  "http_status": 404,
  "status": "unavailable"
}
```
