"""Reuse unchanged Generation stage and add bounded C-footprint validation."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
PARENT=ROOT/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
parent=read(PARENT/'admission.json')
drift=[p for p,h in parent['files_sha256'].items() if sha(ROOT/p)!=h]
assert set(drift)<={'docs/architecture/semantic-appearance-plan.md'},drift
for name,version in parent['dependencies'].items():assert importlib.metadata.version(name)==version
testcase=list(ET.parse(OUT/'geometry-tests.xml').getroot().iter('testcase'))
assert len(testcase)==11 and all(not any(n.tag in ('failure','error','skipped') for n in row) for row in testcase)
positive=read(OUT/'offline-runner/execution.json');checks=read(OUT/'offline-runner/independent-checks.json')
assert positive['status']=='compiled' and positive['budget_after']['calls_used']==3
assert checks['status']=='passed' and checks['check_count']==485
negative=read(OUT/'checker-controls/result.json')
assert negative['status']=='passed' and len(negative['negative_controls'])==5
validation=OUT/'validation';validation.mkdir(exist_ok=False)
for label in ['cshape-geometry-tests','cshape-offline-public','cshape-offline-public-02','cshape-offline-public-03','cshape-offline-public-04','cshape-offline-runner','cshape-checker-controls']:
    source=ROOT/'.tmp'/(label+'-20260910.log')
    shutil.copyfile(source,validation/(label+'.log'))
result=subprocess.run([sys.executable,'-m','compileall','-q',str(OUT),str(ROOT/'tests/compiler/test_concave_footprints.py')],cwd=ROOT,capture_output=True)
assert result.returncode==0
(validation/'compileall.log').write_bytes(result.stdout+result.stderr)
bound={p:sha(ROOT/p) for p in parent['files_sha256']}
bound.update({p.relative_to(ROOT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ('admission.json','authorization.json')})
bound['tests/compiler/test_concave_footprints.py']=sha(ROOT/'tests/compiler/test_concave_footprints.py')
admission=dict(status='admitted',stage='Existing Generation stage; new C-shaped scene without preseeded concern',
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    parent_admission=PARENT.relative_to(ROOT).as_posix()+'/admission.json',parent_admission_sha256=sha(PARENT/'admission.json'),
    inherited_effective_unique_tests=parent['effective_unique_tests'],scope='No product/Prompt/Schema changes. Reuse unchanged admitted public paths, add concave footprint compile/mesh controls and exact new runner offline full chain.',
    changed_bindings=drift,changed_binding_reason='Documentation-only A/B human acceptance and next-scene scope update; production bytes unchanged.',
    additional_geometry_tests=11,public_offline=dict(evidence_class='hand_authored_fake_offline',status='compiled',provider_seam_responses=3,independent_ifc_checks=485),
    evaluator_negative_controls=5,dependencies=parent['dependencies'],files_sha256=bound,
    provider_transport_attempted=False,authorization='Separate case-specific approval required before live; A/B authorization is not reused.',
    full_preflight=False,limitations='New-scene single-run observation. No statistical stability or code-compliance claim. Independent checker is evaluator-only.',
    invalidate_on='Bound production, contract, dependency or input drift; failed applicable checks; a newly exposed deterministic defect.')
with (OUT/'admission.json').open('x',encoding='utf-8') as f:json.dump(admission,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':'admitted','bound_files':len(bound),'production_drift':False,'geometry_tests':11,'offline_ifc_checks':485,'negative_controls':5}))
