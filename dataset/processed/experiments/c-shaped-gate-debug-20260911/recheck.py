"""Offline public gate recheck of a frozen live candidate; no Provider call."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'src'))
SOURCE=OUT.parent/'c-shaped-clarified-entry-20260911/live-run/runs/9b00e53444a948e7'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    from text2ifc_agent.live_pipeline import run_candidate_gate_stage, run_repair_stage
    before={p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}
    case=OUT/'offline-recheck'
    shutil.copytree(SOURCE,case)
    def forbidden():raise AssertionError('offline: Provider must not be called')
    # These two deterministic stages create new evidence on the copy only.
    run_repair_stage(provider_factory=forbidden,output_dir=case/'repair',
        generator_source_dir=case/'generator',case_id='frozen-live-c-offline-recheck')
    result=run_candidate_gate_stage(case_dir=case,output_dir=case,case_id='frozen-live-c-offline-recheck')
    new=read(case/'geometry-feedback.json');old=read(SOURCE/'geometry-feedback.json')
    assert before=={p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}
    assert sha(case/'generator/candidate.json')==before['generator/candidate.json']
    summary={'evidence_class':'offline_recheck_of_frozen_live_candidate','network_calls':0,
        'source_hashes':before,'source_unchanged':True,'candidate_unchanged':True,
        'valid':result['valid'],'old_issues':old['issues'],'new_issues':new['issues'],
        'counts':{'old':len(old['issues']),'new':len(new['issues'])}}
    with (OUT/'recheck-result.json').open('x',encoding='utf-8') as f:json.dump(summary,f,ensure_ascii=False,indent=2)
    print(json.dumps({'valid':result['valid'],'counts':summary['counts'],'issues':[i['code'] for i in new['issues']]}))
if __name__=='__main__':main()
