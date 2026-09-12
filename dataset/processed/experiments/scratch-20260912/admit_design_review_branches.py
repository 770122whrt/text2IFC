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
parent = root / 'dataset/processed/ifc-presentation-validation/three-storey-human-review-20260909/admission.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
previous = json.loads(parent.read_text(encoding='utf-8'))
assert previous['status'] == 'admitted'
changed = [p for p, h in previous['files_sha256'].items() if sha(root / p) != h]
allowed = {'src/text2ifc_agent/clarification.py', 'src/text2ifc_agent/interactive_cli_flow.py',
           'src/text2ifc_agent/live_pipeline.py', 'src/text2ifc_agent/run_report.py',
           'prompts/agent/registry.json', 'tests/agent/test_explicit_wall_fact_contract.py',
           'tests/agent/test_interactive_cli_flow.py'}
assert set(changed) <= allowed, changed
for package, version in previous['dependencies'].items():
    assert metadata.version(package) == version
for result in previous['tests']:
    assert sha(root / result['path']) == result['sha256']
results = []
for name in ['design-review-final-regression-20260910', 'design-review-followup-20260910']:
    source = root / '.tmp' / (name + '.xml')
    suites = list(ET.parse(source).iter('testsuite'))
    assert suites and all(int(s.get(k, 0)) == 0 for s in suites for k in ('failures', 'errors', 'skipped'))
    target = out / (name + '.xml')
    assert not target.exists()
    shutil.copyfile(source, target)
    results.append({'path': target.relative_to(root).as_posix(), 'sha256': sha(target),
                    'tests': sum(int(s.get('tests')) for s in suites)})
new = ['src/text2ifc_agent/design_review.py', 'src/text2ifc_agent/run_report.py',
       'src/text2ifc_agent/clarification.py', 'prompts/agent/design-brief-v2.4.md',
       'prompts/agent/audit-v3.md', 'tests/agent/test_design_review_audit.py',
       'tests/agent/test_clarification_answer_boundary.py']
files = {p: sha(root / p) for p in set(previous['files_sha256']) | set(new)}
for path in out.rglob('*'):
    if path.is_file() and path.suffix in {'.json', '.txt', '.py', '.xml'}:
        files[path.relative_to(root).as_posix()] = sha(path)
subprocess.run([str(root / '.venv/Scripts/python.exe'), '-m', 'compileall', '-q',
                'src/text2ifc_agent/design_review.py', 'src/text2ifc_agent/live_pipeline.py',
                'src/text2ifc_agent/interactive_cli_flow.py', 'src/text2ifc_agent/run_report.py',
                str(out / 'run_branch.py')], cwd=root, check=True)
subprocess.run(['git', 'diff', '--check', '--', 'src/text2ifc_agent', 'tests/agent', 'prompts/agent'], cwd=root, check=True)
record = {
    'status': 'admitted', 'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'scope': 'same public Generation execution stage; conditional Audit 3.0 on caller-bound decisions; two user-authorized scripted branches',
    'parent_admission': {'path': parent.relative_to(root).as_posix(), 'sha256': sha(parent)},
    'dependencies': previous['dependencies'], 'changed_scope': changed,
    'new_files': new, 'tests': results, 'files_sha256': files,
    'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
    'assessment': 'Prompt/version selection and additive design-review provenance require refreshed admission. Current checks cover public Brief/clarification/resume, two request-decision branches through real offline compile/reopen/final session report, malformed/forged/stale review input and output, final-context preservation, old Audit compatibility, hard-gate nonoverride, and related existing generation/changeset/strategy paths. Reuse intact parent transport/compiler/rollback/scale seams. New review cannot mutate IFC or override hard gates.',
    'limits': 'Not a repository-wide preflight, blind capability comparison, complete regulation audit, or demonstrated live success. Existing staged initial-generation fixture replacement remains scoped compatibility evidence; actual branch strategy is legacy_full. Quote matching proves provenance, not natural-language decision correctness. User-authorized branch scripts are not spontaneous human dialogues.',
    'full_preflight': False, 'network_transport_attempted': False,
    'invalidation': 'Any recorded file/dependency change or applicable failed check blocks transport; a current explicit payload authorization is also required.',
}
(out / 'admission.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': 'admitted', 'changed': changed, 'tests': [r['tests'] for r in results]}))
