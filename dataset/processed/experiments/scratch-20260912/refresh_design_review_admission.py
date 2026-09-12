import datetime as dt
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
from xml.etree import ElementTree as ET

root = Path(__file__).resolve().parents[1]
out = root / 'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
current = out / 'admission.json'
initial = out / 'admission-initial.json'
record = json.loads(current.read_text(encoding='utf-8'))
assert not initial.exists()
changed = [p for p, h in record['files_sha256'].items() if sha(root / p) != h]
allowed = {'src/text2ifc_agent/interactive_cli_flow.py', 'src/text2ifc_agent/live_pipeline.py',
           'tests/agent/test_design_review_audit.py', 'tests/agent/test_interactive_cli_flow.py',
           'tests/agent/test_explicit_wall_fact_contract.py',
           (out / 'run_branch.py').relative_to(root).as_posix()}
assert set(changed) <= allowed, changed
parent = root / record['parent_admission']['path']
assert sha(parent) == record['parent_admission']['sha256']
for package, version in record['dependencies'].items():
    assert metadata.version(package) == version
for result in record['tests']:
    assert sha(root / result['path']) == result['sha256']
for name in ['design-review-selection-green-20260910', 'design-review-boundary-final-20260910',
             'design-review-public-final-20260910']:
    source = root / '.tmp' / (name + '.xml')
    suites = list(ET.parse(source).iter('testsuite'))
    assert suites and all(int(s.get(k, 0)) == 0 for s in suites for k in ('failures', 'errors', 'skipped'))
    target = out / source.name
    assert not target.exists()
    shutil.copyfile(source, target)
    record['tests'].append({'path': target.relative_to(root).as_posix(), 'sha256': sha(target),
                            'tests': sum(int(s.get('tests')) for s in suites)})
subprocess.run([str(root / '.venv/Scripts/python.exe'), '-m', 'compileall', '-q',
                'src/text2ifc_agent/design_review.py', 'src/text2ifc_agent/live_pipeline.py',
                'src/text2ifc_agent/interactive_cli_flow.py', 'src/text2ifc_agent/run_report.py',
                str(out / 'run_branch.py')], cwd=root, check=True)
shutil.copyfile(current, initial)
record['supersedes_preliminary_admission'] = {'path': initial.relative_to(root).as_posix(), 'sha256': sha(initial)}
record['created_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
record['head'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
record['final_scoped_changes'] = changed
record['assessment'] += ' Final opt-in selection preserves ordinary Brief 2.3. New Brief 2.4 without bound context stops before Generator transport. Added 46/22/19 passing overlapping scoped checks cover final version selection, A/B public compile/reopen, absent-context and ordinary/staged/REPL compatibility. No cumulative success-rate claim.'
record['files_sha256'] = {p: sha(root / p) for p in record['files_sha256']}
for path in out.rglob('*'):
    if path.is_file() and path.suffix in {'.json', '.txt', '.py', '.xml'} and path not in {current, initial}:
        record['files_sha256'][path.relative_to(root).as_posix()] = sha(path)
current.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': record['status'], 'head': record['head'], 'changed': changed,
                  'overlapping_test_results': [r['tests'] for r in record['tests']]}))
