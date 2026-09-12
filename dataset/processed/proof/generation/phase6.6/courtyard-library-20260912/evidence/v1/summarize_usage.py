"""Actual per-stage usage; reservations remain separate from returned usage."""
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent

def main():
    execution=json.loads((OUT/'live-run/execution.json').read_text(encoding='utf8'))
    run=Path(execution['run_dir'])
    ledger=json.loads((run/'generation-budget.json').read_text(encoding='utf8'))
    responses={}
    for path in sorted(run.rglob('response-metadata.json')):
        value=json.loads(path.read_text(encoding='utf8'))
        if value.get('evidence_class')!='live':continue
        identity=value.get('response_id')
        assert identity,'Missing actual response identity'
        if identity in responses:
            assert responses[identity]['usage']==value.get('usage',{}),'Inconsistent duplicated response usage'
            responses[identity]['paths'].append(path.relative_to(run).as_posix())
            continue
        stage=path.parent
        prompt=stage/'prompt-rendered.md';output=stage/'model-text.txt'
        responses[identity]={'response_id':identity,'paths':[path.relative_to(run).as_posix()],
            'usage':value.get('usage',{}),'finish_reason':value.get('finish_reason'),'model':value.get('model'),
            'prompt_characters':len(prompt.read_text(encoding='utf8')) if prompt.exists() else None,
            'output_characters':len(output.read_text(encoding='utf8')) if output.exists() else None}
    rows=list(responses.values())
    actual_input=sum(r['usage'].get('prompt_tokens',0) or 0 for r in rows)
    actual_output=sum(r['usage'].get('completion_tokens',0) or 0 for r in rows)
    result={'run_id':execution['run_id'],'status':execution['status'],
        'actual_response_count':len(rows),'actual_input_tokens':actual_input,
        'actual_output_tokens_including_reasoning':actual_output,'actual_total_tokens':actual_input+actual_output,
        'calls_reserved_or_used':len(ledger['attempts']),
        'tokens_charged_or_reserved':sum(a['tokens_charged'] for a in ledger['attempts']),
        'active_seconds':sum(a['elapsed_seconds'] for a in ledger['attempts']),
        'attempts':ledger['attempts'],'responses':rows,
        'ledger_sha256':hashlib.sha256((run/'generation-budget.json').read_bytes()).hexdigest(),
        'unknown_usage_note':'No completed response is not zero consumption; unresolved attempts retain their budget reservation.'}
    (OUT/'usage-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k not in {'attempts','responses'}},ensure_ascii=False))

if __name__=='__main__':main()
