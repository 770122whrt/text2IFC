"""Offline diagnostic probes only: no Provider and no candidate/IFC publication."""
import copy,hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
from text2ifc_agent.live_pipeline import _repair_allowed_change_paths,_repair_evidence_by_path
from text2ifc_agent.fact_delta import evaluate_repair_fact_delta
from text2ifc_agent.failure_routing import assess_repair_eligibility
from text2ifc_agent.generator import validate_generation_document
base=root/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908'
first=base/'runtime-02/runs/45743eb8eb1e77b0/generator'
last=base/'corrective-04/generator'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
original=read(first/'parsed-output.json');latest=read(last/'parsed-output.json')
issue=next(i for i in read(first/'validation.json')['issues'] if i['code']=='INVALID_IFC_ATTRIBUTE')
idx=int(issue['path'].split('/')[2]); changed=copy.deepcopy(original)
attrs=changed['entities'][idx]['attributes'];attrs['NumberOfRiser']=attrs.pop('NumberOfRisers')
allowed=_repair_allowed_change_paths([issue],candidate=original)
delta=evaluate_repair_fact_delta(before=original,after=changed,allowed_change_paths=allowed,evidence_by_path=_repair_evidence_by_path([issue],allowed))
assert not delta['valid'] and any(i['path'].endswith('/NumberOfRiser') for i in delta['issues'])
positive=copy.deepcopy(original);positive['entities'][idx]['attributes']['NumberOfRisers']=19
positive_delta=evaluate_repair_fact_delta(before=original,after=positive,allowed_change_paths=allowed,evidence_by_path=_repair_evidence_by_path([issue],allowed))
assert positive_delta['valid'] # permission seam only, not a valid IFC assertion
unrelated=copy.deepcopy(positive);unrelated['entities'][0]['attributes']['Name']='UNAUTHORIZED'
negative_delta=evaluate_repair_fact_delta(before=original,after=unrelated,allowed_change_paths=allowed,evidence_by_path=_repair_evidence_by_path([issue],allowed))
assert not negative_delta['valid']
last_issues=read(last/'validation.json')['issues'];brief=read(last/'design-brief.json')
route=assess_repair_eligibility(issues=last_issues,known_facts=brief['known_facts'])
assert route['route']=='blocked_failure'
single=copy.deepcopy(latest);j=int(last_issues[0]['path'].split('/')[2]);single['entities'][j]['attributes']['ConstructionType']='NOTDEFINED'
remaining=validate_generation_document(single)
assert len(remaining['diagnostics'])==9
render=read(last/'prompt-render-input.json')
context={key:{token:json.dumps(render[key],ensure_ascii=False).count(token) for token in ['ConstructionType','IfcWindowStyleConstructionEnum','OTHER_CONSTRUCTION']} for key in ['FORMAL_SCHEMA','CAPABILITY_PROFILE','FEW_SHOTS','GENERATION_FEEDBACK']}
record={'evidence_class':'offline diagnostic only','network_transport_attempted':False,'production_changes':False,
 'sources_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [first/'parsed-output.json',last/'parsed-output.json',last/'prompt-render-input.json']},
 'rename_permission_probe':{'allowed_paths':allowed,'delta':delta,'same_path_permission_positive':positive_delta['valid'],'unrelated_change_rejected':not negative_delta['valid'],'limits':'Permission checks alone do not validate candidate semantics; all mutations stayed in memory.'},
 'early_error_route_probe':route,'one_of_ten_correction_probe':{'remaining_contract_errors':len(remaining['diagnostics']),'classification':remaining['status'],'limits':'No mutated candidate saved or compiled. Existing apply_changeset rejects any remaining Formal validation issue, so connecting independent early-error patches needs an explicit partial-workspace contract or a complete bounded repair group.'},
 'actual_context_token_occurrences':context,
 'recommendation_boundaries':'Preserve IFC2X3, default legacy_full, explicit staged, immutable raw attempts, no material/property invention, local Type and final reopen verification.'}
out=root/'.tmp/pipeline-stability-inspection-01.json'
with out.open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
print(json.dumps({'rename_permission':delta['valid'],'enum_route':route['route'],'one_style_corrected_remaining_errors':len(remaining['diagnostics']),'provider_calls':0}))
