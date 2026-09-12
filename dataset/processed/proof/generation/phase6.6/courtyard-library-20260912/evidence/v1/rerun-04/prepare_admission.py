"""Stage admission for additive part appearance; no network or credential load."""
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
ROOT = OUT.parents[4]
sys.path.insert(0, str(ROOT/'src'))
from text2ifc_agent.artifact_scan import scan_path
from text2ifc_agent.prompt_registry import load_prompt_registry
from text2ifc_agent.design_brief import load_design_brief_schema
from text2ifc_contract.schema import load_schema_v22, _load_schema_path

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, value):
    with p.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')

parent = read(SOURCE/'rerun-03/admission.json')
changed = set(read(OUT/'implementation-paths.json'))
assert parent['status'] == 'admitted'
for path, expected in parent['files_sha256'].items():
    if path not in changed:
        assert sha(ROOT/path) == expected, path
for package, version in parent['dependencies'].items():
    assert importlib.metadata.version(package) == version, package
checks = {}
for p in [SOURCE/'part-public-final.xml', *(OUT/n for n in (
        'stage-seams-final.xml', 'stage-public.xml', 'repair-regression-final.xml', 'legacy.xml', 'recovery-final.xml'))]:
    cases = list(ET.parse(p).getroot().iter('testcase'))
    assert cases and not any(n.tag in {'failure', 'error', 'skipped'} for case in cases for n in case), p
    checks[p.relative_to(ROOT).as_posix()] = {'passed':len(cases), 'sha256':sha(p)}
load_prompt_registry(); load_design_brief_schema('text2ifc/design-brief/2.5'); load_schema_v22()
_load_schema_path(ROOT/'schemas/bim-json/draft/1.2/schema.json')
_load_schema_path(ROOT/'schemas/agent/bim-json-changeset-1.2.schema.json')
assert subprocess.run([sys.executable,'-m','compileall','-q',
    'src/text2ifc_agent','src/text2ifc_compiler','src/text2ifc_contract','src/text2ifc_presentation'],cwd=ROOT).returncode == 0
assert subprocess.run(['git','diff','--check','HEAD','--',*sorted(changed)],cwd=ROOT).returncode == 0
ledger = SOURCE/'rerun-03/live-run/runs/58a394a71cf278c4/generation-budget.json'
attempts = read(ledger)['attempts']
assert len(attempts) == 5 and sum(a['tokens_charged'] for a in attempts) == 375754
assert not any(a['status'] == 'reserved' for a in attempts)
preview = read(SOURCE/'rerun-03/payload-preview.json')
preview.update(purpose='Same frozen courtyard design through newly approved explicit part-appearance contracts, full Generation/Audit loop.',
    previous_budget_sha256=sha(ledger), inherited_calls=5, inherited_tokens=375754,
    design_brief_version='text2ifc/design-brief/2.5', generation_schema_version='bim-json/2.2',
    excluded=['IFC bytes','independent evaluators','private Gold','other-case data','credential values'])
write(OUT/'payload-preview.json', preview)
approval = read(SOURCE/'rerun-03/authorization.json')
approval.update(payload_preview_sha256=sha(OUT/'payload-preview.json'), previous_budget_sha256=sha(ledger),
    basis='User explicitly approved real Provider generation and GitHub evidence push, then approved adding versioned part appearance while retaining the original design. Same destination, frozen input, exclusions and cumulative limits.')
assert approval['limits'] == read(ledger)['limits']
write(OUT/'authorization.json', approval)
bound = dict(parent['files_sha256'])
for p in [*(ROOT/n for n in changed), SOURCE/'check_part_colours.py', ledger,
          SOURCE/'rerun-03/admission.json', *(OUT/n for n in (
              'run_case.py','test_runner.py','prepare_admission.py','implementation-paths.json',
              'payload-preview.json','authorization.json')), *(ROOT/n for n in checks)]:
    bound[p.relative_to(ROOT).as_posix()] = sha(p)
scan = scan_path(OUT); assert scan['finding_count'] == 0, scan
write(OUT/'admission.json', {'status':'admitted', 'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
    'stage':'Generation explicit basic filling part appearance 2.5/2.2',
    'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'scope':'Occurrence channels, authoring/semantic projection, compile/reopen, both strategies, bounded correction and clarification/resume; unchanged shared Provider adapter and safety boundaries inherited.',
    'changed_scope':sorted(changed), 'parent_admission':str((SOURCE/'rerun-03/admission.json').relative_to(ROOT)),
    'files_sha256':bound, 'dependencies':parent['dependencies'], 'checks':checks, 'scan':scan,
    'matrix': {'complete':'part-public-final.xml + stage-public.xml; two public strategies',
        'clarification_resume':'stage-seams-final.xml/recovery-final.xml; real invoker and persisted SessionStore, fake transport',
        'ambiguous_unsupported':'part request family; Type/role, inherited/whole conflict, unknown parts, malformed values',
        'malformed_truncated':'source boundary tests + unchanged admitted adapter malformed/truncation/configuration evidence',
        'binding_atomic_preservation':'part recovery/semantic request tests, final stages, old semantic and enum regression',
        'publication_reopen':'actual IFC semantics and styles verified before atomic replace; no geometry or material invention',
        'source_private_isolation':'source request/prior ledger unchanged; no source IFC/Gold/evaluator transported; Repair in-place mutation not applicable'},
    'full_preflight':False, 'network_transport_attempted':False,
    'limitations':['Offline regressions overlap and do not measure capability improvement.',
        'All failed tests and genuine attempts retained; successful checks do not change historical verdicts.',
        'Source scanner flags two pre-existing api_key=config.api_key keyword expressions; inspected variable references, not embedded secrets. Artifact scan has zero findings.',
        'Courtyard final IFC and human visual acceptance still pending.']})
print(json.dumps({'status':'admitted','check_groups':len(checks),'inherited_tokens':375754}))
