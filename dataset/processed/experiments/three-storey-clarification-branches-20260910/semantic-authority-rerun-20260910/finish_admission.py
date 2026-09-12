"""Finish a stage preflight after one test-only fixture correction.

Keep the failed suite, verify every production/input byte is unchanged, and
replace only the affected test file's outcomes with a full-file revalidation.
"""
import datetime as dt
import importlib.util
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
BASE = OUT.parent
ROOT = BASE.parents[3]
PARENT = BASE/'appearance-guard-rerun-20260910'
CHANGED_TEST = 'tests/agent/test_phase6_2_fix_repl_cli.py'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def outcomes(path):
    return {(t.get('classname'), t.get('name')): not any(t.find(k) is not None for k in ('failure','error','skipped'))
            for t in ET.parse(path).getroot().iter('testcase')}


def main():
    prior = OUT/'validation-02'
    old_bound = read(prior/'bound-inputs.json')
    drift = [p for p, digest in old_bound.items() if sha(ROOT/p) != digest]
    assert drift == [CHANGED_TEST], drift
    parent = read(PARENT/'admission.json')
    for package, version in parent['dependencies'].items():
        assert metadata.version(package) == version
    checks = read(prior/'checks.json')
    assert [c['group'] for c in checks] == ['seams','public-chain']
    assert checks[0]['exit_code'] == 0
    for check in checks:
        assert sha(prior/(check['group']+'.xml')) == check['xml_sha256']
        assert sha(prior/(check['group']+'.log')) == check['log_sha256']
    effective = {**outcomes(prior/'seams.xml'), **outcomes(prior/'public-chain.xml')}
    failed = [key for key, passed in effective.items() if not passed]
    assert failed == [('tests.agent.test_phase6_2_fix_repl_cli', 'test_default_live_repl_design_brief_trace_is_session_scoped')], failed
    validation = OUT/'validation-completion'
    validation.mkdir(exist_ok=False)
    spec = importlib.util.spec_from_file_location('frozen_generation_matrix', BASE/'rerun-20260910/prepare_admission.py')
    matrix = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(matrix)
    groups = {'cli-fixture-revalidation': [CHANGED_TEST],
              'reopened-ifc': ['tests/'+p for p in matrix.GROUPS['reopened-ifc']]}
    bound = {p:sha(ROOT/p) for p in old_bound}
    bound[Path(__file__).relative_to(ROOT).as_posix()] = sha(Path(__file__))
    bound[(OUT/'inspect_branch.py').relative_to(ROOT).as_posix()] = sha(OUT/'inspect_branch.py')
    supplemental = []
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    for label, files in groups.items():
        command = [sys.executable, '-m', 'pytest', *files, '-q', '-p', 'no:cacheprovider',
            '--basetemp', '.tmp/pytest-semantic-completion-'+label+'-20260910',
            '--junitxml', str(validation/(label+'.xml'))]
        print('Offline Generation stage completion:', label, flush=True)
        with (validation/(label+'.log')).open('xb') as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=900)
        rows = outcomes(validation/(label+'.xml'))
        record = {'group': label, 'command': command, 'exit_code':result.returncode,
                  'tests':len(rows), 'passed':sum(rows.values()),
                  'xml_sha256':sha(validation/(label+'.xml')), 'log_sha256':sha(validation/(label+'.log'))}
        supplemental.append(record)
        print(record['group'], record['tests'], record['passed'], flush=True)
        assert result.returncode == 0 and rows and all(rows.values()), record
        if label == 'cli-fixture-revalidation':
            expected_keys = {key for key in effective if key[0] == 'tests.agent.test_phase6_2_fix_repl_cli'}
            assert set(rows) == expected_keys, 'Full affected test file must be revalidated'
        else:
            assert not set(rows).intersection(effective)
        effective.update(rows)
    assert all(effective.values())
    for label, command in [('compileall', [sys.executable,'-m','compileall','-q','src','tests/agent',str(OUT)]),
        ('diff-check',['git','-c','core.whitespace=cr-at-eol','diff','--check','--','src','tests','schemas','prompts','scripts/agent/run_phase6_2_cli.py','docs/architecture/semantic-appearance-plan.md'])]:
        result = subprocess.run(command,cwd=ROOT,capture_output=True,timeout=180)
        (validation/(label+'.log')).write_bytes(result.stdout+result.stderr)
        assert result.returncode == 0, result.stderr.decode(errors='replace')
    assert all(sha(ROOT/p)==digest for p,digest in bound.items()), 'Inputs changed during completion'
    frozen = []
    for folder, name in [(BASE,'LIVE-ATTEMPT-FILES.json'), (BASE/'continuation-20260910','FILES.json'),
            (BASE/'rerun-20260910','FILES.json'),(BASE/'projection-retry-20260910','FILES.json'), (PARENT,'FILES.json')]:
        manifest = read(folder/name)
        assert all(sha(folder/r['path'])==r['sha256'] for r in manifest['files'])
        frozen.append({'path':(folder/name).relative_to(ROOT).as_posix(),'sha256':sha(folder/name),'files':len(manifest['files'])})
    write(validation/'checks.json', supplemental)
    write(validation/'effective-results.json', [{'classname':k[0],'name':k[1],'passed':v} for k,v in sorted(effective.items())])
    for directory in [OUT/'validation',prior,validation]:
        bound.update({p.relative_to(ROOT).as_posix():sha(p) for p in directory.iterdir() if p.is_file()})
    history = PARENT/'A-revise/runtime/runs/4927c3df4028e515/generation-budget.json'
    assert len(read(history)['attempts']) == 11
    write(OUT/'admission.json', {'status':'admitted', 'stage':'Generation with explicit semantic authority and bounded Brief2.2 repair',
        'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'scope':'Generation-stage offline seams, complete public API/CLI and both strategies, clarification/resume, atomic cleanup, budget and provider failures, reopened IFC; not Full Preflight.',
        'checks':checks,'supplemental_checks':supplemental, 'effective_unique_tests':len(effective),
        'resolved_fixture_failure':{'original':list(failed[0]),'file':CHANGED_TEST,
            'before_sha256':old_bound[CHANGED_TEST],'after_sha256':bound[CHANGED_TEST],
            'reason':'Test-only explicit empty semantic list; production bytes and all other bound inputs unchanged. Failed suite retained, affected whole file revalidated.'},
        'dependencies':parent['dependencies'], 'files_sha256':bound,'frozen_authority_checks':frozen,
        'supersedes_holds':[{'path':(PARENT/'RUN-HOLD.json').relative_to(ROOT).as_posix(),'sha256':sha(PARENT/'RUN-HOLD.json')}],
        'supersession_basis':'Missing extraction cannot authorize semantic deletion or publication. Required categorized review, real user turn sources, one budgeted semantic-only correction, preservation of all nonsemantic facts and already structured values. Frozen20-case failure family now passes.',
        'budget_history':{'A-revise':history.relative_to(ROOT).as_posix()},
        'full_preflight':False,'network_transport_attempted':False,
        'invalidation':'Bound bytes/dependencies drift, new deterministic defect or local RUN-HOLD blocks transport.',
        'limits':'Offline regression evidence, not capability improvement or natural-language completeness proof. Human review and B acknowledged clearance issue remain separate.'})
    print('ADMITTED',len(effective),'unique tests; old failures preserved',flush=True)


if __name__ == '__main__':
    main()
