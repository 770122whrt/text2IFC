"""Freeze local C evidence and an explicit staging list; never calls git/provider."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'src'))
from text2ifc_agent.artifact_scan import scan_path
BASE=OUT.parent
FIRST=BASE/'c-shaped-integrated-20260911'
LIVE=BASE/'c-shaped-clarified-entry-20260911'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)

def main():
    run=LIVE/'live-run/runs/9b00e53444a948e7'
    ledger=read(run/'generation-budget.json')
    rows=[]
    for p in [FIRST/'live-run/runs/cf0a6e858a2a74a8/calls/01-design-brief',
              run/'calls/01-design-brief',run/'generator',run/'audit']:
        m=read(p/'response-metadata.json');u=m['usage']
        rows.append({'metadata_path':p.relative_to(ROOT).as_posix()+'/response-metadata.json',
            'metadata_sha256':sha(p/'response-metadata.json'),'response_id':m['response_id'],
            'response_model':m['model'],'input':u['prompt_tokens'],'output':u['completion_tokens'],
            'reasoning_included_in_output':u['completion_tokens_details']['reasoning_tokens'],
            'cache_hit':u.get('prompt_cache_hit_tokens'),'cache_miss':u.get('prompt_cache_miss_tokens'),
            'total':u['total_tokens']})
    total=sum(a['tokens_charged'] for a in ledger['attempts']);active=sum(a['elapsed_seconds'] for a in ledger['attempts'])
    assert total==583435 and len(ledger['attempts'])==8
    write(OUT/'usage-summary.json',{'new_real_responses':rows,'new_total':sum(r['total'] for r in rows),
        'cumulative_calls':8,'cumulative_tokens_charged':total,'cumulative_active_seconds':active,
        'limits':ledger['limits'],'ledger_path':(run/'generation-budget.json').relative_to(ROOT).as_posix(),
        'ledger_sha256':sha(run/'generation-budget.json'),'all_attempts':ledger['attempts'],
        'provider_call_during_closeout':False})
    validation=OUT/'validation';validation.mkdir(exist_ok=True)
    for name in ['outline-red','assessment-red','c-gates-green','c-gates-final','c-scope-final','c-gates-public']:
        shutil.copyfile(ROOT/'.tmp'/(name+'.xml'),validation/(name+'.xml'))
    for name,count in [('c-gates-final',108),('c-scope-final',6),('c-gates-public',4)]:
        tests=list(ET.parse(validation/(name+'.xml')).getroot().iter('testcase'))
        assert len(tests)==count and not any(n.tag in {'error','failure','skipped'} for t in tests for n in t)
    files=[]
    for base in [FIRST,LIVE]:
        files.extend(p for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='FILES.json')
    # Recheck copy retains old runtime locally. Curate only new deterministic
    # outputs; original live traces are already preserved in the live bundle.
    files.extend(p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts
        and p.name!='FILES.json' and 'offline-recheck' not in p.parts)
    for name in ['repair/route.json','repair/metrics.json','geometry-feedback.json',
                 'semantic-geometry-expectation.json','gate-summary.json','ifc-verification.json',
                 'semantic-verification.json','request-semantics.json']:
        files.append(OUT/'offline-recheck'/name)
    scan={str(b.name):scan_path(b) for b in [FIRST,LIVE,OUT]}
    assert all(v['finding_count']==0 for v in scan.values())
    write(OUT/'artifact-validation.json',{'status':'passed','secret_finding_count':0,
        'scanned_collections':list(scan),'evidence_class':'scoped_offline_artifact_checks',
        'full_preflight':False,'human_accepted':False,'ifc_delivery_accepted':False})
    files.append(OUT/'artifact-validation.json')
    # Every local link in new human reports must resolve, without accessing the
    # unrelated accepted Repair Proof paths affected by sandbox permissions.
    for report in [FIRST/'REPORT-RESULT.md',LIVE/'REPORT.md',OUT/'REPORT.md']:
        for target in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
            assert (report.parent/target.split('#')[0]).exists(),target
    for base in [FIRST,LIVE,OUT]:
        owned=[p for p in files if p.is_relative_to(base)]
        manifest=base/'FILES.json'
        write(manifest,{'schema_version':'text2ifc/local-file-inventory/1.0',
            'status':'diagnostic_not_accepted_proof','files':[
                {'path':p.relative_to(base).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
                for p in sorted(owned)],'manifest_excludes_itself':True})
        files.append(manifest)
    extra=[ROOT/p for p in ['.planning/STATE.md','docs/architecture/semantic-appearance-plan.md',
        'docs/architecture/token-efficiency-plan.md','tests/agent/test_c_clarified_entry_run.py']]
    allpaths=sorted({p.relative_to(ROOT).as_posix() for p in [*files,*extra]})
    (ROOT/'.tmp/c-evidence-paths.txt').write_text('\n'.join(allpaths)+'\n',encoding='utf-8')
    print(json.dumps({'files':len(files),'bytes':sum(p.stat().st_size for p in files),
        'staging_list_count':len(allpaths),'scan_findings':0,'cumulative_tokens':total}))
if __name__=='__main__':main()
