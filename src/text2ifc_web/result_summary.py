"""Readable projection from actual application/publication evidence, not LLM self-report."""
from pathlib import Path
import json
import ifcopenshell
from .store import write_json


def summarize_operations(source,result,intent,application,publishable):
    actual={o['operation_id']:o for o in application.get('operations',[])}
    def products(changes,category):
        rows=[];seen=set()
        for item in changes.get(category,[]):
            guid=item.get('global_id')
            if not guid or guid in seen:continue
            obj=None
            for model in (result,source):
                if model is None:continue
                try:obj=model.by_guid(guid)
                except RuntimeError:continue
                if obj is not None:break
            if obj is None or not obj.is_a('IfcProduct') or obj.is_a() in ('IfcOpeningElement','IfcSpace','IfcAnnotation'):continue
            seen.add(guid);rows.append({'global_id':guid,'step_id':obj.id(),'ifc_class':obj.is_a(),'name':obj.Name,'category':category})
        return rows
    rows=[]
    for operation in intent.get('operations',[]):
        oid=operation['operation_id'];applied=actual.get(oid);changes=(applied or {}).get('changes',{})
        rows.append({'operation_id':oid,'operation_type':operation['operation_type'],
                     'status':'published' if applied and publishable else 'applied_not_published' if applied else 'not_completed',
                     'created':products(changes,'created'),'modified':products(changes,'modified'),
                     'target_query':operation.get('target_query',{}),'parameters':operation.get('parameters',{})})
    return {'operation_total':len(rows),'published_operations':sum(r['status']=='published' for r in rows),
            'successful_artifact_publishable':bool(publishable),'rows':rows,
            'basis':'native application evidence and matching IFC identities; not a new evaluation'}


def write_result_summary(store,task_id,result):
    task=store.task(task_id);request=store.prepared(task['prepared_id'])
    run=store.root/'native'/'runs'/task['run_id']
    def read(path):return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
    intent=read(run/'intent.json')
    application={};output=None
    artifacts=result.artifacts
    manifest=artifacts.get('manifest')
    if manifest:
        base=(run/manifest).parent
        evidence=read(base/'terminal/evidence.json')
        application=evidence.get('evidence',{}).get('application',{})
    file=artifacts.get('successful_ifc') or artifacts.get('diagnostic_candidate')
    if file:
        path=(run/file).resolve()
        if path.is_relative_to(run.resolve()):output=ifcopenshell.open(str(path))
    source=ifcopenshell.open(str(store.source(request['input_id'])))
    summary=summarize_operations(source,output,intent,application,result.successful_artifact_publishable)
    summary.update(task_id=task_id,run_id=task['run_id'],reason_code=result.reason_code)
    write_json(store.root/'summaries'/(task_id+'.json'),summary)
    return summary
