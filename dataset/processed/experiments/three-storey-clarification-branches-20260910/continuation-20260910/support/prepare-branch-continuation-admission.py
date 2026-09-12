import datetime as dt
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
base = root / 'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910'
out = base / 'continuation-20260910'
out.mkdir(exist_ok=True)
validation = out / 'validation'
validation.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
parent = json.loads((base / 'admission.json').read_text(encoding='utf-8'))
changed = {p for p, digest in parent['files_sha256'].items() if sha(root / p) != digest}
assert changed == {'src/text2ifc_agent/dynamic_gates.py', 'src/text2ifc_agent/change_scope.py',
                   'src/text2ifc_agent/semantic_requirements.py', 'src/text2ifc_agent/issue_normalizers.py'}, changed
for package, version in parent['dependencies'].items():
    assert metadata.version(package) == version
tests = []
for name, description in [
    ('type-scope-integration-green-20260910', '27 semantic/Type cases plus existing scope and ChangeSet rounds'),
    ('type-scope-public-regression-20260910', 'semantic public paths, staged generation, CLI/REPL and Audit'),
    ('cross-storey-name-green-20260910', 'name boundary, dynamic gates, revision and package gates'),
    ('branch-continuation-offline-20260910', 'new continuation harness through actual public IFC compilation/reopen; budget stop'),
    ('branch-continuation-public-20260910', 'semantic public paths, gate/audit bundle, geometry loop and scoped loop'),
]:
    source = root / '.tmp' / (name + '.xml')
    tree = ET.parse(source)
    suites = list(tree.getroot().iter('testsuite'))
    counts = {k: sum(int(s.attrib.get(k, 0)) for s in suites) for k in ['tests', 'failures', 'errors', 'skipped']}
    assert counts['tests'] and not any(counts[k] for k in ['failures', 'errors', 'skipped']), (name, counts)
    target = validation / source.name
    if target.exists():
        assert target.read_bytes() == source.read_bytes()
    else:
        shutil.copyfile(source, target)
    tests.append({'path': target.relative_to(root).as_posix(), 'sha256': sha(target), **counts,
                  'scope': description, 'timestamp': suites[0].get('timestamp'),
                  'duration_seconds': sum(float(s.get('time', 0)) for s in suites)})
commands = [
    [sys.executable, '-m', 'compileall', '-q', 'src/text2ifc_agent/dynamic_gates.py',
     'tests/agent/test_cross_storey_name_boundary.py', 'tests/agent/test_design_review_continuation.py',
     str((base / 'continue_branches.py').relative_to(root))],
    ['git', 'diff', '--check', '--', 'src/text2ifc_agent/dynamic_gates.py',
     'docs/architecture/semantic-appearance-plan.md'],
]
checks = []
for command in commands:
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    result = subprocess.run(command, cwd=root, capture_output=True)
    assert result.returncode == 0, result.stderr.decode(errors='replace')
    checks.append({'command': command, 'exit_code': result.returncode, 'started_at': started,
        'finished_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'output_sha256': hashlib.sha256(result.stdout + result.stderr).hexdigest()})
authorization = {'user_reply': '继续进行案例A和B的真实运行 有问题与我沟通',
    'destination': 'https://api.deepseek.com', 'model': 'deepseek-v4-flash',
    'payload_preview_sha256': sha(base / 'payload-preview.json'),
    'scope': 'same frozen branch inputs; A reuses preserved real Brief, cumulative remaining 2 calls; B up to 6 calls',
    'per_branch_total_limits': {'max_calls': 6, 'max_tokens': 800000, 'max_active_seconds': 1800},
    'prior_A_calls': 4, 'prior_B_calls': 0, 'github_push_authorized': False}
(out / 'authorization.json').write_text(json.dumps(authorization, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
files = {p: sha(root / p) for p in parent['files_sha256']}
new = [root / 'tests/agent/test_semantic_scope_and_type_policy.py',
       root / 'tests/agent/test_cross_storey_name_boundary.py', root / 'tests/agent/test_design_review_continuation.py',
       base / 'continue_branches.py', out / 'authorization.json', base / 'RUN-HOLD.json',
       base / 'admission.json', root / '.tmp/prepare-branch-continuation-admission.py',
       base.parent / 'three-storey-human-review-20260909/generated.ifc']
prior_run = base / 'A-revise/runtime/runs/48dcf264b1a6df16'
new += [prior_run / 'generation-budget.json']
new += [p for p in (prior_run / 'calls/01-design-brief').rglob('*') if p.is_file()]
new += [root / t['path'] for t in tests]
for path in new:
    files[path.relative_to(root).as_posix()] = sha(path)
admission = {
    'status': 'admitted', 'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'scope': 'same Generation public execution stage; scoped revalidation after issue mapping/Type policy/stair-name fix; new append-only runner',
    'parent_admission': {'path': (base/'admission.json').relative_to(root).as_posix(), 'sha256': sha(base/'admission.json')},
    'supersedes_hold': {'path': (base/'RUN-HOLD.json').relative_to(root).as_posix(), 'sha256': sha(base/'RUN-HOLD.json'),
        'basis': 'Both reported deterministic defects fixed offline; preserved candidate dynamic gates pass; refreshed affected public-path checks. New Type gate remains blocking, without automatic deletion.'},
    'head': subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
    'python': sys.version, 'dependencies': parent['dependencies'], 'changed_scope': sorted(changed),
    'tests': tests, 'checks': checks, 'files_sha256': files,
    'full_preflight': False, 'network_transport_attempted': False,
    'assessment': 'Reuse 551 unchanged parent hash bindings, transport/compiler/transaction/persistence/scale coverage. New runner has offline public success for A/B, parent immutability, cumulative budget exhaustion before transport, and duplicate-output guard. Related semantic/strategy/CLI/Audit/ChangeSet regressions remain green; extra Type policy remains fail closed.',
    'limits': 'A is a disclosed retry from reused real Brief, not blind improvement. B retains acknowledged usability defect. Neither branch is construction approval, full regulation review or registered Proof. No Type graph cleanup or prompt/schema changes. No repository-wide success claim.',
    'invalidation': 'Any bound file/dependency drift, failed applicable check, exhausted unsettled budget or further unresolved deterministic defect blocks transport.'}
(out / 'admission.json').write_text(json.dumps(admission, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'status': admission['status'], 'changed_scope': sorted(changed), 'test_counts': [t['tests'] for t in tests], 'bound_files': len(files)}))
