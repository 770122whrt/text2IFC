"""Bind a configuration-only retry to unchanged admitted production and budget."""
import datetime as dt
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent
PRIOR = SOURCE / 'rerun-02'
ROOT = OUT.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from text2ifc_agent.artifact_scan import scan_path

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, value):
    with p.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

parent = read(PRIOR / 'admission.json')
assert parent['status'] == 'admitted'
for p, expected in parent['files_sha256'].items():
    assert sha(ROOT / p) == expected, p
for package, version in parent['dependencies'].items():
    assert importlib.metadata.version(package) == version, package
cases = list(ET.parse(OUT / 'configuration.xml').getroot().iter('testcase'))
assert cases and not any(n.tag in {'failure', 'error', 'skipped'} for c in cases for n in c)
ledger = PRIOR / 'live-run/runs/5e0a62ff38ef73c1/generation-budget.json'
attempts = read(ledger)['attempts']
assert len(attempts) == 4 and sum(a['tokens_charged'] for a in attempts) == 310268
assert not any(a['status'] == 'reserved' for a in attempts)
preview = read(PRIOR / 'payload-preview.json')
preview.update(purpose='One bounded same-case retry after a confirmed 65536-token truncation; only per-response output cap raised, no cumulative budget increase.',
    previous_budget_sha256=sha(ledger), inherited_calls=4, inherited_tokens=310268,
    max_completion_tokens=98304, previous_max_completion_tokens=65536,
    provider_limit_source='https://api-docs.deepseek.com/quick_start/pricing')
write(OUT / 'payload-preview.json', preview)
approval = read(PRIOR / 'authorization.json')
approval.update(payload_preview_sha256=sha(OUT / 'payload-preview.json'),
    previous_budget_sha256=sha(ledger),
    basis=approval['basis'] + ' User also authorized addressing excessive input/output. This retry only raises a local response cap inside the unchanged explicitly approved cumulative limits; destination and public payload scope unchanged.')
assert approval['limits'] == read(ledger)['limits']
write(OUT / 'authorization.json', approval)
assert subprocess.run([sys.executable, '-m', 'compileall', '-q', str(OUT)], cwd=ROOT).returncode == 0
bound = dict(parent['files_sha256'])
for p in [PRIOR / 'admission.json', ledger, *(OUT / n for n in (
    'run_case.py', 'test_configuration.py', 'prepare_admission.py', 'configuration.xml',
    'payload-preview.json', 'authorization.json'))]:
    bound[p.relative_to(ROOT).as_posix()] = sha(p)
scan = scan_path(OUT)
assert scan['finding_count'] == 0, scan
write(OUT / 'admission.json', {'status': 'admitted',
    'scope': 'Configuration-only output cap retry; unchanged production and exact execute function. Inherits prior public-chain admission; adapter and cumulative-budget regressions rechecked.',
    'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'parent_admission': (PRIOR / 'admission.json').relative_to(ROOT).as_posix(),
    'parent_sha256': sha(PRIOR / 'admission.json'), 'files_sha256': bound,
    'dependencies': parent['dependencies'], 'scan': scan,
    'checks': {'configuration.xml': {'passed': len(cases), 'sha256': sha(OUT / 'configuration.xml')}},
    'full_preflight': False, 'network_transport_attempted': False,
    'limitations': ['Same-case development retry, not a capability or token-saving benchmark.',
        'All prior failures remain charged. No raw IFC or independent evaluator goes to Provider.']})
print(json.dumps({'status': 'admitted', 'passed': len(cases), 'prior_tokens': 310268, 'max_completion_tokens': 98304}))
