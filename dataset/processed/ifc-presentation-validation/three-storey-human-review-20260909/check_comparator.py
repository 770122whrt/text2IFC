"""Reproduce the evidence-table comparison fix without running a Provider."""
import ast,hashlib,json
from pathlib import Path

base=Path(__file__).parent
tree=ast.parse((base/'check_ifc_v2.py').read_text(encoding='utf-8'))
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='same_rows')
namespace={}
exec(compile(ast.Module(body=[function],type_ignores=[]),'<comparison>','exec'),namespace)
same=namespace['same_rows']
reference=[(0,'north',3.8,2400)]
cases=[('floating_noise',[(0.,'north',3800*.001,2400.)],True),
       ('one_mm_position',[(0,'north',3.801,2400)],False),
       ('different_side',[(0,'east',3.8,2400)],False),('missing_row',[],False),
       ('nonfinite',[(0,'north',float('nan'),2400)],False),
       ('different_size',[(0,'north',3.8,2400.001)],False)]
checks={name:same(actual,reference)==want for name,actual,want in cases}
assert all(checks.values()),checks
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'reason':'Mixed tuple exact equality rejected binary floating-point noise. Only table numeric comparison changed.',
 'old_failed_checks':json.loads((base/'independent-ifc-check.json').read_text(encoding='utf-8'))['failed'],
 'numeric_abs_tolerance':1e-9,'numeric_rel_tolerance':0,'boundary_checks':checks,
 'original_evaluator_sha256':sha(base/'check_ifc.py'),'new_evaluator_sha256':sha(base/'check_ifc_v2.py'),
 'request_and_ifc_changed':False,
 'new_result':json.loads((base/'independent-ifc-check-v2.json').read_text(encoding='utf-8'))['status'],
 'same_evaluator_negative_control':json.loads((base/'checker-negative-two-storey-v2.json').read_text(encoding='utf-8'))['status']}
with (base/'evaluator-correction.json').open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
print(json.dumps(checks))
