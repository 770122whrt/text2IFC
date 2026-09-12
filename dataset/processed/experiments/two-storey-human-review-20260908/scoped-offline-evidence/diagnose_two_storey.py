import json, sys, hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))
from text2ifc_agent.generator import validate_generation_document
import ifcopenshell
base=root/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908'
run=base/'runtime-02/runs/45743eb8eb1e77b0'
path=run/'generator/parsed-output.json'
candidate=json.loads(path.read_text(encoding='utf-8'))
validation=validate_generation_document(candidate)
expected=json.loads((run/'generator/validation.json').read_text(encoding='utf-8'))
assert validation['diagnostics']==expected['issues']
entity=ifcopenshell.file(schema='IFC2X3').create_entity('IfcStairFlight')
report={'evidence_class':'offline_exact_replay','candidate_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'validation':validation,'ifc2x3_stair_attributes':list(entity.get_info()),
        'diagnosis':'Unchanged validator reproduces the 10 real Generator output errors. No product defect or silent normalization established. Existing contract requires IFC2X3 NumberOfRiser (singular), matching door OperationType, and local axes inherited once from each host. No candidate edits and no compiler bypass.',
        'affected_entities':{str(i):candidate['entities'][i] for i in [24,29,31,33,51,53,61,63]}}
(base/'offline-contract-diagnosis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'reproduced':len(validation['diagnostics']),'stair_attributes':list(entity.get_info())}))
