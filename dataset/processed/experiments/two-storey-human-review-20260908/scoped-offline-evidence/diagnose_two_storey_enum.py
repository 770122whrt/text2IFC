import json,hashlib,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
from text2ifc_agent.generator import validate_generation_document
base=root/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908'
p=base/'corrective-04/generator/parsed-output.json'
doc=json.loads(p.read_text(encoding='utf-8'))
result=validate_generation_document(doc)
expected=json.loads((p.parent/'validation.json').read_text(encoding='utf-8'))
assert result['diagnostics']==expected['issues']
bad=[{'id':e['id'],'ifc_class':e['ifc_class'],'ConstructionType':e['attributes'].get('ConstructionType')} for e in doc['entities'] if e['ifc_class']=='IfcWindowStyle']
record={'status':'blocked','evidence_class':'offline exact unmodified Provider response replay','network_transport_attempted':False,
        'candidate_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'diagnostics':result['diagnostics'],'window_styles':bad,
        'previous_three_error_kinds_absent':not any(i['code'] in ['INVALID_IFC_ATTRIBUTE','BASIC_FILLING_CONSTRAINT_CONFLICT'] for i in result['diagnostics']),
        'scope':'This validates schema rejection only. No IFC compiled, no output claimed, no accepted Proof, no general capability improvement.',
        'next_step':'Freeze enum-valid/invalid, no-explicit-Type/minimal-deterministic-Style, window/door family and public recovery cases before any production change. Do not convert invalid Provider values into accepted evidence by editing this candidate.'}
with (base/'offline-enum-diagnosis.json').open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
print(json.dumps({'reproduced_errors':len(result['diagnostics']),'invalid_values':sorted({s['ConstructionType'] for s in bad})}))
