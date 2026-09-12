"""Generation-stage preflight for versioned optional appearance removal; offline."""
import datetime as dt
import hashlib
import importlib.util
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
BASE = OUT.parent
ROOT = BASE.parents[3]
PARENT = BASE / 'projection-retry-20260910'
ORIGINAL = BASE / 'rerun-20260910'
PRIOR_A = PARENT / 'A-revise/runtime/runs/25a7dcb4706b8bf4/generation-budget.json'


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    validation = OUT / 'validation'
    validation.mkdir(exist_ok=False)
    parent = read(PARENT / 'admission.json')
    for package, version in parent['dependencies'].items():
        assert metadata.version(package) == version
    spec = importlib.util.spec_from_file_location('prior_generation_stage_matrix', ORIGINAL / 'prepare_admission.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    groups = module.GROUPS
    groups['seams'] += ['agent/test_unrequested_appearance.py', 'agent/test_phase6_5_changeset_contract.py',
                       'agent/test_appearance_request_projection.py']
    groups['public-chain'] += ['agent/test_design_review_budget_retry.py']
    frozen = []
    for folder, name in [(BASE, 'LIVE-ATTEMPT-FILES.json'), (BASE/'continuation-20260910', 'FILES.json'),
                         (ORIGINAL, 'FILES.json'), (PARENT, 'FILES.json')]:
        rows = read(folder/name)['files']
        for row in rows:
            assert sha(folder/row['path']) == row['sha256'], row['path']
        frozen.append({'path': (folder/name).relative_to(ROOT).as_posix(), 'sha256': sha(folder/name), 'files':len(rows)})
    history = read(PRIOR_A)
    assert len(history['attempts']) == 6 and all(a['status']=='completed' for a in history['attempts'])
    confirmation = ORIGINAL / 'explicit-egress-confirmation.json'
    write(OUT/'authorization.json', {
        'confirmation_path': confirmation.relative_to(ROOT).as_posix(), 'confirmation_sha256': sha(confirmation),
        'approved_payload_preview': (ORIGINAL/'payload-preview.json').relative_to(ROOT).as_posix(),
        'approved_payload_sha256': sha(ORIGINAL/'payload-preview.json'),
        'destination':'https://api.deepseek.com', 'model':'deepseek-v4-flash',
        'scope':'Same authorized A/B complete task after offline defect fix; unchanged frozen input and approved dialogue, new Brief/candidate, subsequent own feedback and metadata.',
        'A_prior_calls_charged':6, 'B_prior_calls_charged':0, 'limits':history['limits'],
        'excluded':['original IFC bytes','private Gold','other-task data','credential text'],
        'github_push_authorized':False})
    for branch in ['A-revise','B-retain']:
        for p in (OUT/'inputs'/branch).iterdir():
            if p.is_file():
                assert sha(p) == sha(ORIGINAL/'inputs'/branch/p.name)
    paths = {ROOT/p for p in parent['files_sha256']}
    paths.update([OUT/'run_branches.py', Path(__file__), OUT/'authorization.json', OUT/'.gitattributes',
                  PRIOR_A, PARENT/'FILES.json', PARENT/'RUN-HOLD.json', PARENT/'admission.json', confirmation,
                  ROOT/'schemas/agent/bim-json-changeset-1.1.schema.json',
                  ROOT/'prompts/agent/bim-json-generator-v2.4.md', ROOT/'prompts/agent/bim-json-changeset-v1.7.md',
                  ROOT/'prompts/agent/registry.json'])
    paths.update(p for p in (OUT/'inputs').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.update(ROOT/'tests'/p for files in groups.values() for p in files)
    bound = {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
    checks = []
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    for label, files in groups.items():
        command = [sys.executable,'-m','pytest', *['tests/'+p for p in files], '-q','-p','no:cacheprovider',
                   '--basetemp', '.tmp/pytest-style-stage-'+label+'-20260910',
                   '--junitxml',str(validation/(label+'.xml'))]
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        print('Offline Generation stage:',label,flush=True)
        with (validation/(label+'.log')).open('xb') as log:
            result = subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
        suites = list(ET.parse(validation/(label+'.xml')).getroot().iter('testsuite'))
        counts = {k:sum(int(s.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']}
        checks.append({'group':label,'command':command,'started_at':started,
            'finished_at':dt.datetime.now(dt.timezone.utc).isoformat(),'timeout_seconds':900,
            'exit_code':result.returncode,'log_sha256':sha(validation/(label+'.log')),
            'xml_sha256':sha(validation/(label+'.xml')),**counts})
        write(validation/'checks.json',checks)
        print(label,counts,flush=True)
        assert result.returncode == 0 and counts['tests'] and not any(counts[k] for k in ['failures','errors','skipped'])
    for label,command in [('compileall',[sys.executable,'-m','compileall','-q',*[str(p) for p in paths if p.suffix=='.py']]),
            ('diff-check',['git','-c','core.whitespace=cr-at-eol','diff','--check','--','src','tests','schemas','prompts','docs',str(OUT.relative_to(ROOT))])]:
        result = subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=180)
        log = validation/(label+'.log'); log.write_bytes(result.stdout+result.stderr)
        checks.append({'group':label,'command':command,'exit_code':result.returncode,'log_sha256':sha(log)})
        write(validation/'checks.json',checks)
        assert result.returncode == 0
    assert all(sha(ROOT/p)==digest for p,digest in bound.items()), 'Bound files changed during validation'
    bound.update({p.relative_to(ROOT).as_posix():sha(p) for p in validation.iterdir()})
    write(OUT/'admission.json',{
        'status':'admitted','stage':'Generation with ChangeSet 1.1 optional appearance removal',
        'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'scope':'Fresh stage seams and complete offline public chain because schema and transaction permissions gained a versioned, request-bound optional-field removal. No repository-wide or Repair-stage preflight.',
        'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'python':sys.version,'platform':platform.platform(),'dependencies':parent['dependencies'],
        'checks':checks,'files_sha256':bound,'frozen_authority_checks':frozen,
        'supersedes_holds':[{'path':(PARENT/'RUN-HOLD.json').relative_to(ROOT).as_posix(),'sha256':sha(PARENT/'RUN-HOLD.json')}],
        'supersession_basis':'Request-owned whole-product appearance gate plus narrowly authorized ChangeSet 1.1 removal. Original A offline replay restores all290 frozen IFC checks; old live QA failure unchanged.',
        'budget_history':{'A-revise':PRIOR_A.relative_to(ROOT).as_posix()},
        'matrix':{'complete_publication_resume':'public-chain semantic ready-session Type/style/mixed loops and persistence',
                  'both_generation_strategies':'semantic_public_paths, staged generation and scoped style cleanup',
                  'versions_atomic_scope':'changeset1.0/1.1 contracts/application and unrequested_appearance family',
                  'provider_failure_budget':'adapter failure, response preservation, task budget and carry-forward tests',
                  'reopen_semantics_geometry':'reopened-ifc group and independent style/geometry family',
                  'truth_boundary':'Generation-only approved text payload; unchanged input and all old evidence hashes; no originalIFC/privateGold transport'},
        'full_preflight':False,'network_transport_attempted':False,
        'invalidation':'Bound-file/dependency drift, new deterministic failure or local RUN-HOLD blocks transport.',
        'limits':'Offline tests are not capability metrics. Real A/B are revealed same-task retries. Human review and Proof acceptance remain separate; B retains the frozen known issue.'})
    print('ADMITTED',sum(c.get('tests',0) for c in checks),flush=True)


if __name__ == '__main__':
    main()
