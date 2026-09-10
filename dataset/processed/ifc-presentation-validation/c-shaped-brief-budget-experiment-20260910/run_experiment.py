"""Two single-response Brief arms; same current prompt, different output caps."""
import argparse
from dataclasses import replace
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import sys
from urllib.parse import urlparse

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
SOURCE=OUT.parent/'c-shaped-teaching-building-20260910'
PRIOR=OUT.parent/'c-shaped-brief-debug-20260910/live-attempt'
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from text2ifc_agent.generation_budget import GenerationBudget,BudgetLimits,BudgetedProvider
from text2ifc_agent.live_pipeline import run_design_brief_stage
from text2ifc_agent.providers import ProviderOutputError

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

class OneResponse:
    def __init__(self,provider):self.provider=provider;self.calls=0
    def generate_live(self,**kwargs):
        if self.calls:
            raise ProviderOutputError('Experiment stops before automatic semantic correction.',
                details={'failure_class':'experiment_single_response','transport_attempted':False})
        assert kwargs['prompt']==(OUT/'frozen-prompt.md').read_text(encoding='utf-8')
        self.calls+=1
        return self.provider.generate_live(**kwargs)

def execute(output,config,provider_factory,*,evidence_class):
    protocol=read(OUT/'protocol.json')
    output=Path(output);output.mkdir(exist_ok=False)
    original=PRIOR/'generation-budget.json'
    assert sha(original)==protocol['prior_budget_sha256']
    shutil.copyfile(original,output/'generation-budget.json')
    budget=GenerationBudget(output,BudgetLimits(**protocol['limits']))
    before=budget.snapshot()
    assert before['calls_used']==2 and before['tokens_used_or_reserved']==147630
    assert all(a['status']!='reserved' for a in before['attempts'])
    results=[]
    record=dict(status='running',evidence_class=evidence_class,budget_before=before,
        started_at=dt.datetime.now(dt.timezone.utc).isoformat(),arms=results)
    write(output/'execution.json',record)
    for cap in protocol['output_caps_in_order']:
        label=f'{cap//1024}k';arm=output/label;arm.mkdir(exist_ok=False)
        arm_config=replace(config,max_completion_tokens=cap)
        provider=OneResponse(BudgetedProvider(provider_factory(arm_config),budget))
        result=dict(label=label,output_cap=cap,started_at=dt.datetime.now(dt.timezone.utc).isoformat(),budget_before=budget.snapshot())
        try:
            brief=run_design_brief_stage(provider=provider,output_dir=arm/'design-brief',
                design_brief_schema_version='text2ifc/design-brief/2.3',design_review_enabled=False,
                case=dict(case_id=f'c-shaped-budget-{label}',call_index=1,
                    user_request=(SOURCE/'request.txt').read_text(encoding='utf-8'),
                    conversation=read(SOURCE/'live-run/runs/41edcb4296d1b826/calls/01-design-brief/conversation.json')))
            result.update(status=brief['status'],valid=brief['valid'],brief_result=brief)
        except Exception as error:
            details=getattr(error,'evidence',getattr(error,'details',{}))
            result.update(status='exception',valid=False,exception_type=type(error).__name__,failure_class=details.get('failure_class','unknown'))
        result.update(finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),budget_after=budget.snapshot())
        results.append(result);write(arm/'execution.json',result);write(output/'execution.json',record)
        assert result['budget_after']['calls_used']==result['budget_before']['calls_used']+1
        if result.get('failure_class') not in {None,'truncated','experiment_single_response'}:
            break
    record.update(status='completed' if len(results)==2 else 'stopped',budget_after=budget.snapshot(),
        finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),historical_budget_unchanged=sha(original)==protocol['prior_budget_sha256'])
    write(output/'execution.json',record)
    assert record['historical_budget_unchanged']
    return record

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
    admission=read(OUT/'admission.json')
    assert admission['status']=='admitted'
    for p,h in admission['files_sha256'].items():assert sha(ROOT/p)==h,p
    for p,v in admission['dependencies'].items():assert importlib.metadata.version(p)==v
    if not args.live:print('Admission passed; no credential access or transport.');return
    approval=read(OUT/'authorization.json');protocol=read(OUT/'protocol.json')
    assert approval['status']=='approved' and approval['protocol_sha256']==sha(OUT/'protocol.json')
    assert sha(SOURCE/'request.txt')==protocol['request_sha256']
    from scripts.agent.run_phase6_2_cli import load_env_file
    from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config,OpenAICompatibleLiveProvider
    load_env_file(ROOT/'.env');config=load_openai_compatible_runtime_config(dict(os.environ))
    assert config.model=='deepseek-v4-flash' and urlparse(config.base_url).hostname=='api.deepseek.com'
    result=execute(OUT/'live',config,lambda c:OpenAICompatibleLiveProvider(config=c),evidence_class='live')
    print(json.dumps({'status':result['status'],'arms':[{k:r.get(k) for k in ['label','status','valid','failure_class']} for r in result['arms']],
        'budget_after':result['budget_after']},ensure_ascii=False))

if __name__=='__main__':main()
