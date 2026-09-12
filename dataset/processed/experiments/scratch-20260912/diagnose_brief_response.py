import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'dataset/processed/ifc-presentation-validation/c-shaped-brief-debug-20260910'
stage=out/'live-attempt/design-brief'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
response=read(stage/'response.raw.json');request=read(stage/'request.redacted.json')['request']
message=response['choices'][0]['message'];usage=response['usage']
brief=read(stage/'design-brief.json')
old=out.parent/'c-shaped-teaching-building-20260910/live-run/runs/41edcb4296d1b826'
result=dict(status='ready',raw_response_sha256=sha(stage/'response.raw.json'),
    prompt_identical_to_failed_attempt=sha(stage/'prompt-rendered.md')==sha(old/'calls/01-design-brief/prompt-rendered.md'),
    requested_model=request['model'],returned_model=response['model'],finish_reason=response['choices'][0]['finish_reason'],
    output_limit=request['max_tokens'],thinking=request['extra_body']['thinking'],usage=usage,
    json_content_chars=len(message['content']),reasoning_content_chars=len(message.get('reasoning_content') or ''),
    visible_output_tokens_inferred=usage['completion_tokens']-usage['completion_tokens_details']['reasoning_tokens'],
    prior_output_tokens_if_input_tokenization_unchanged=83996-usage['prompt_tokens'],
    cap_hit_inference='Strongly consistent with 65536 output cap; prior response/usage breakdown missing, so cutoff location and original reasoning share are unknown.',
    schema_version=brief['schema_version'],validation=read(stage/'validation.json'),
    missing_facts=brief.get('missing_facts'),ambiguities=brief.get('ambiguities'),unsupported_requests=brief.get('unsupported_requests'),
    spontaneous_design_issue_claim='No issues reported in missing_facts/ambiguities/unsupported_requests. No Audit or independent IFC check was run.',
    prompt_conflict=dict(ordinary_v2_7='Header/schema 2.3, final output instruction 2.0.',
        review_v2_8='Final instruction already 2.3; unaffected.',cause_of_truncation_proven=False),
    source='https://api-docs.deepseek.com/api/create-chat-completion/')
assert result['prompt_identical_to_failed_attempt'] and result['validation']['valid']
(out/'diagnosis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['prompt_identical_to_failed_attempt','requested_model','returned_model','output_limit','visible_output_tokens_inferred','prior_output_tokens_if_input_tokenization_unchanged','json_content_chars']},ensure_ascii=False))
