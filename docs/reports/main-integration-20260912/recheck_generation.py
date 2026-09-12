from pathlib import Path
import hashlib,json,shutil,traceback
from text2ifc_agent.live_pipeline import run_final_acceptance_stage
ROOT=Path.cwd(); REPORT=ROOT/'docs/reports/main-integration-20260912'; scratch=ROOT/'.tmp/generation-recheck-01'; scratch.mkdir(exist_ok=False)
collections=[('AB','three-storey-clarification-ab-20260910'),('C','c-shaped-teaching-20260911')]
results=[]
for _,collection in collections:
    base=ROOT/'dataset/processed/proof/generation/phase6.6'/collection
    manifest=json.loads((base/'manifest.json').read_text(encoding='utf-8'))
    for case in manifest['cases']:
        source=(base/case['authority']).parent
        before={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
        local=scratch/case['case_id']; shutil.copytree(source,local)
        output=REPORT/'generation-recheck-01'/case['case_id']; output.mkdir(parents=True,exist_ok=False)
        record={'case_id':case['case_id'],'source':source.relative_to(ROOT).as_posix(),'mode':'offline_revalidation_existing_accepted_proof','provider_calls':0}
        try:record['result']=run_final_acceptance_stage(case_dir=local,output_dir=output,case_id=case['case_id'])
        except Exception as exc:record.update(error=repr(exc),traceback=traceback.format_exc())
        after={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
        record['frozen_sources_unchanged']=before==after
        results.append(record); print(json.dumps(record,ensure_ascii=False),flush=True)
        (REPORT/'generation-recheck-01.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert all(r.get('result',{}).get('valid') and r['frozen_sources_unchanged'] for r in results)
