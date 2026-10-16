"""Independently reopen downloaded live-UAT IFCs and inspect geometry and IFC relationships.
No model calls and no private benchmark/Gold inputs. Does not rewrite input or result IFCs.
"""
from pathlib import Path
from collections import Counter
import argparse
import json
import sys
import time
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.validate

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'ui/ifc-viewer/.artifacts/live-ui-20261011'

def main(label):
    directory=OUT/label
    record=json.loads((directory/'task.json').read_text(encoding='utf-8'))
    task=json.loads((directory/'last-task.json').read_text(encoding='utf-8'))
    source_path=directory/'input.ifc';result_path=directory/'repaired.ifc'
    source_bytes=source_path.read_bytes();result_bytes=result_path.read_bytes()
    source=ifcopenshell.open(str(source_path));result=ifcopenshell.open(str(result_path))
    old_ids={o.GlobalId for o in source.by_type('IfcProduct')}
    new_ids={o.GlobalId for o in result.by_type('IfcProduct')}
    kind='IfcDoor' if record['case']=='door' else 'IfcWindow'
    added=[o for o in result.by_type(kind) if o.GlobalId not in old_ids]
    original_path=ROOT/record['source_file'] if record.get('source_file') else ROOT/'dataset/processed/ifc-repair/repair-comparison/development'/record['input_case']/'public/model.ifc'
    if not original_path.resolve().is_relative_to(ROOT):raise ValueError('Source outside this workspace')
    original=original_path.read_bytes()
    expected_added=record.get('expected_added',1)
    geometry=[];settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
    for obj in added:
        shape=ifcopenshell.geom.create_shape(settings,obj)
        vertices=tuple(shape.geometry.verts);faces=tuple(shape.geometry.faces)
        fillings=list(obj.FillsVoids)
        opening=fillings[0].RelatingOpeningElement if len(fillings)==1 else None
        voids=list(opening.VoidsElements) if opening else []
        geometry.append({'global_id':obj.GlobalId,'name':obj.Name,'ifc_class':obj.is_a(),'triangles':len(faces)//3,
            'world_bounds_m':[[min(vertices[i::3]),max(vertices[i::3])] for i in range(3)],
            'nominal_width':obj.OverallWidth,'nominal_height':obj.OverallHeight,
            'filling_relationships':len(fillings),'host_relationships':len(voids),
            'host_global_id':voids[0].RelatingBuildingElement.GlobalId if len(voids)==1 else None})
    logger=ifcopenshell.validate.json_logger();started=time.monotonic()
    ifcopenshell.validate.validate(result,logger,express_rules=True)
    (directory/'independent-validation-diagnostics.json').write_text(json.dumps(logger.statements,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    source_logger=ifcopenshell.validate.json_logger()
    if logger.statements:ifcopenshell.validate.validate(source,source_logger,express_rules=True)
    (directory/'source-validation-diagnostics.json').write_text(json.dumps(source_logger.statements,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    def issue_key(row):return (row.get('type'),row.get('attribute'),str(row.get('instance')),row.get('message'))
    introduced=[row for row in logger.statements if issue_key(row) not in {issue_key(x) for x in source_logger.statements}]
    checks={
        'both_ifc2x3':source.schema==result.schema=='IFC2X3',
        'downloaded_input_matches_public_source':source_bytes==original,
        'source_and_output_not_rewritten':source_path.read_bytes()==source_bytes and result_path.read_bytes()==result_bytes,
        'requested_added_occurrence_count':len(added)==expected_added,
        'existing_product_ids_preserved':old_ids.issubset(new_ids),
        'new_geometry_and_single_hosted_filling':all(r['triangles']>0 and r['filling_relationships']==r['host_relationships']==1 for r in geometry),
        'express_and_schema_no_diagnostics':not logger.statements,
        'native_published_result':task['successful_artifact_publishable'] is True and task['status']=='succeeded'}
    picked_path=directory/'selected-objects.json'
    if picked_path.is_file():
        picked=json.loads(picked_path.read_text(encoding='utf-8'))
        checks['each_selected_wall_hosts_exactly_one_new_window']=Counter(r['host_global_id'] for r in geometry)==Counter(r['guid'] for r in picked['targets'])
        reference=source.by_guid(picked['reference']['guid'])
        def type_ids(obj):return {r.RelatingType.GlobalId for r in obj.IsDefinedBy if r.is_a('IfcRelDefinesByType')}
        checks['shared_reference_type_preserved']=bool(type_ids(reference)) and all(type_ids(obj)==type_ids(reference) for obj in added)
    run=ROOT/'.tmp/repair-ui-api/data/native/runs'/task['run_id']
    labels=[]
    for path in (run/'intent').glob('**/live-attempt-*.json'):
        data=json.loads(path.read_text(encoding='utf-8'));response=data.get('response',{})
        if response.get('model'):labels.append(response['model'])
    report={'task_id':task['task_id'],'run_id':task['run_id'],'checks':checks,'passed':all(checks.values()),
        'added_geometry':geometry,'count_before':len(source.by_type(kind)),'count_after':len(result.by_type(kind)),
        'validation_diagnostics':len(logger.statements),'source_diagnostics_checked_because_output_has_issues':bool(logger.statements),'source_diagnostics':len(source_logger.statements),'introduced_diagnostics':len(introduced),'validation_seconds':round(time.monotonic()-started,2),
        'response_model_labels':sorted(set(labels)),'basis':'Downloaded input/output; source identities, native geometry and EXPRESS independently checked. No pristine pre-damage IFC.'}
    (directory/'independent-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not report['passed']:raise SystemExit(1)

def summarize_suite():
    cases=[]
    for label in ('door-1','window-2','multi-3'):
        folder=OUT/label
        task=json.loads((folder/'last-task.json').read_text(encoding='utf-8'))
        check=json.loads((folder/'independent-checks.json').read_text(encoding='utf-8'))
        events=json.loads((folder/'events.json').read_text(encoding='utf-8'))
        calls=[e for e in events['activity'] if e.get('kind')=='provider_call' and e['action']=='completed']
        missing=[e for e in calls if not isinstance(e.get('usage',{}).get('total_tokens'),int)]
        total=sum(e.get('usage',{}).get('total_tokens',0) for e in calls)
        cases.append({'label':label,'task_id':task['task_id'],'run_id':task['run_id'],'native_status':task['status'],
            'provider_calls':len(calls),'returned_total_tokens':total,'missing_usage_calls':len(missing),
            'independent_full_check_passed':check['passed'],'output_diagnostics':check['validation_diagnostics'],
            'source_diagnostics':check.get('source_diagnostics'),'introduced_diagnostics':check.get('introduced_diagnostics'),
            'added_objects':len(check['added_geometry']),
            'task_url':'http://127.0.0.1:4178/ifc-viewer/?task='+task['task_id']})
    ledger=json.loads((ROOT/'.tmp/repair-ui-api/data/live-budget/ui-live-20261011-first/generation-budget.json').read_text(encoding='utf-8'))
    total=sum(a['tokens_charged'] for a in ledger['attempts'])
    assert total==sum(c['returned_total_tokens'] for c in cases)
    assert len(ledger['attempts'])==sum(c['provider_calls'] for c in cases)
    report={'scope':'local live integration, not a model-quality benchmark','cases':cases,
        'actual_model_calls':len(ledger['attempts']),'actual_returned_tokens':total,'limits':ledger['limits'],
        'active_provider_seconds':sum(a['elapsed_seconds'] for a in ledger['attempts']),
        'unsettled_calls':sum(a['status']=='reserved' for a in ledger['attempts']),
        'all_cost_records_match':True,'new_live_tasks':len(cases),'task_limit':3,
        'fully_verified_cases':sum(c['independent_full_check_passed'] for c in cases),
        'multi_case_note':'Two test walls reused a generated public-input fixture. Its three pre-existing IFC rule errors are retained in the live result. Fixture builder repaired and checked offline; this live run was not repeated or relabelled.'}
    (OUT/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--label');parser.add_argument('--summarize',action='store_true');a=parser.parse_args()
    if a.summarize:summarize_suite()
    else:
        if not a.label or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in a.label):parser.error('Invalid label')
        main(a.label)
