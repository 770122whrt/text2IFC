"""Read-only evaluation of the frozen A/B branch output; never edits runtime."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
base = root / 'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910'
reference = root / 'dataset/processed/ifc-presentation-validation/three-storey-human-review-20260909'
branch = sys.argv[1]
assert branch in {'A-revise', 'B-retain'}
case = base / branch
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
execution = load(case / 'execution.json')
assert execution['status'] == 'compiled', execution['status']
runtime = root / execution['run_dir']
assert runtime.resolve().is_relative_to(case.resolve())
acceptance = load(runtime / 'acceptance-metrics.json')
assert acceptance['valid'] and acceptance['compile_reopen_success']
for source, name in [(runtime / 'output.ifc', 'generated.ifc'), (runtime / 'candidate.json', 'model.json')]:
    target = case / name
    assert not target.exists()
    shutil.copyfile(source, target)
    assert sha(source) == sha(target)
python = str(root / '.venv/Scripts/python.exe')
subprocess.run([python, str(case / 'check_ifc.py'), str(case / 'generated.ifc'), str(case / 'independent-ifc-check.json')], check=True, cwd=root)
subprocess.run([python, str(base / 'measure_clearance.py'), str(case / 'generated.ifc'), str(case / 'clearance-check.json')], check=True, cwd=root)
subprocess.run([python, str(reference / 'export_mesh.py'), str(case / 'generated.ifc'), str(case / 'views')], check=True, cwd=root)
for name in ['overall', 'cutaway', 'window-double', 'door']:
    subprocess.run([python, str(reference / 'render_png.py'), str(case / 'views' / (name + '-mesh.json')),
                    str(case / 'views' / (name + '.png'))], check=True, cwd=root)
mesh = load(case / 'views/overall-mesh.json')
stairs = [p for p in mesh['products'] if p['kind'] == 'IfcStairFlight']
assert len(stairs) == 2
mesh['products'] = stairs
mesh['view_note'] = 'Only actual IFC stair flights isolated; other elements hidden, IFC unchanged.'
with (case / 'views/stairs-mesh.json').open('x', encoding='utf-8') as f:
    json.dump(mesh, f, ensure_ascii=False)
subprocess.run([python, str(reference / 'render_png.py'), str(case / 'views/stairs-mesh.json'),
                str(case / 'views/stairs.png')], check=True, cwd=root)
budget = load(runtime / 'generation-budget.json')
report = {'branch': branch, 'runtime': execution['run_dir'], 'machine_status': execution['status'],
          'acceptance': acceptance, 'ifc_sha256': sha(case / 'generated.ifc'),
          'ifc_bytes': (case / 'generated.ifc').stat().st_size,
          'independent_check': {k: load(case / 'independent-ifc-check.json')[k] for k in ['status', 'failed']},
          'clearance': {k: load(case / 'clearance-check.json')[k] for k in ['sample_count', 'minimum_sampled_gap_m', 'zero_gap_count']},
          'attempts': budget['attempts'], 'human_review_status': 'pending', 'proof_registered': False,
          'original_ifc_unchanged': sha(reference / 'generated.ifc') == '756cf1ad4b8175ecb2571ce09483bd6ab83edfd562ae2f66c33a650b9e610d63',
          'original_request_unchanged': sha(reference / 'request.txt') == '2046a23ec544596aead827abe9ef734aa118694f9af6c8bc20c2649b9a2f818e'}
assert report['original_ifc_unchanged'] and report['original_request_unchanged']
with (case / 'evaluation-summary.json').open('x', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(json.dumps({k: report[k] for k in ['branch', 'machine_status', 'independent_check', 'clearance']}))
