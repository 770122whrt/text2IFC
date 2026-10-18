"""Read back grounded identities before any IFC mutation; never retarget an operation."""
from pathlib import Path
from functools import partial
import json
import ifcopenshell


def _host_ids(model, identity):
    if model is None or not identity:
        return set()
    try:
        obj=model.by_guid(identity)
        fills=tuple(getattr(obj,'FillsVoids',()))
        opening=fills[0].RelatingOpeningElement if len(fills)==1 else obj
        return {r.RelatingBuildingElement.GlobalId for r in getattr(opening,'VoidsElements',())}
    except (RuntimeError,AttributeError):
        return set()


def check_selection(references, context):
    if references.get('targets'):
        return _check_targets(references,context)
    selected={k:v for k,v in references.items() if v and k in ('primary','auxiliary')}
    if not selected:
        return {'valid':True,'issues':[],'checks':[]}
    model=ifcopenshell.open(str(context['source_ifc_path'])) if context.get('source_ifc_path') else None
    operations=context.get('resolution',{}).get('operations',[])
    installation=context.get('installation_references') or {}
    derivations=context.get('derivations') or []
    targets=set();references_seen=set();spatial_references=set()
    for operation in operations:
        target=operation.get('target_global_id')
        if target:targets.add(target);targets.update(_host_ids(model,target))
        record=installation.get(operation.get('operation_id'),{})
        if record.get('reference_global_id'):references_seen.add(record['reference_global_id'])
        for d in derivations:
            if d.get('operation_id')!=operation.get('operation_id'):continue
            for key in ('reference_occurrence_id','reference_id'):
                if d.get(key):references_seen.add(d[key]);spatial_references.add(d[key])
            spatial_references.update(d.get('reference_ids',[]))
    checks=[];issues=[]
    for role,ref in selected.items():
        guid=ref['global_id']
        allowed=(targets|spatial_references) if role=='primary' else references_seen
        valid=guid in allowed
        checks.append({'role':role,'selected_global_id':guid,'matched':valid})
        if not valid:issues.append({'code':'PICKED_TARGET_MISMATCH' if role=='primary' else 'PICKED_REFERENCE_UNVERIFIED',
                                   'role':role,'selected_global_id':guid,'observed_ids':sorted(allowed)})
    return {'valid':not issues,'issues':issues,'checks':checks}


def _check_targets(references,context):
    """Per-operation readback. References cannot stand in for missing modification targets."""
    expected={r['global_id'] for r in references['targets']}
    model=ifcopenshell.open(str(context['source_ifc_path'])) if context.get('source_ifc_path') else None
    operations=context.get('resolution',{}).get('operations',[])
    intents={o.get('operation_id'):o for o in context.get('intent',{}).get('operations',[])}
    matched=set();checks=[];issues=[];signatures=set()
    auxiliary=references.get('auxiliary')
    for operation in operations:
        oid=operation.get('operation_id');target=operation.get('target_global_id')
        target_scope=({target} if target else set())|_host_ids(model,target)
        selected=expected & target_scope
        valid=bool(selected)
        if not valid:
            issues.append({'code':'UNSELECTED_TARGET','operation_id':oid,'observed_target':target})
        matched.update(selected)
        normalized=intents.get(oid,operation)
        signature=json.dumps([operation.get('operation_type'),target,normalized.get('parameters'),normalized.get('attribute_intents'),normalized.get('prototype_intent')],sort_keys=True,ensure_ascii=False,default=str)
        if signature in signatures:
            issues.append({'code':'DUPLICATE_TARGET_OPERATION','operation_id':oid,'observed_target':target});valid=False
        signatures.add(signature)
        used=set()
        installation=(context.get('installation_references') or {}).get(oid,{})
        if installation.get('reference_global_id'):used.add(installation['reference_global_id'])
        for derivation in context.get('derivations',[]):
            if derivation.get('operation_id')==oid:
                used.update(derivation.get('reference_ids',[]))
                used.update(derivation[k] for k in ('reference_id','reference_occurrence_id') if derivation.get(k))
        if auxiliary and auxiliary['global_id'] not in used:
            issues.append({'code':'PICKED_REFERENCE_UNVERIFIED','operation_id':oid,'selected_global_id':auxiliary['global_id']});valid=False
        checks.append({'operation_id':oid,'target_global_id':target,'selected_targets':sorted(selected),'matched':valid})
    for guid in sorted(expected-matched):
        issues.append({'code':'PICKED_TARGET_MISSING','selected_global_id':guid})
    return {'valid':not issues,'issues':issues,'checks':checks,'target_count':len(expected),'covered_target_count':len(matched),'scope':'explicit_targets'}


def guard_for_request(request):
    """Build a Python-only guard from server-verified picks, not model-provided instructions."""
    references=request.get('references') or {}
    def guard(context):
        data=dict(context)
        # Only the grounding file corresponding to this exact current Intent is eligible.
        run_dir=Path(context['run_directory'])
        wanted=context['intent']
        derivations=[]
        for path in (run_dir/'intent').glob('**/repair-intent.json'):
            if path.is_symlink():continue
            if json.loads(path.read_text(encoding='utf-8'))!=wanted:continue
            evidence=path.parent/'grounding-evidence.json'
            if evidence.is_file() and not evidence.is_symlink():
                derivations.extend(json.loads(evidence.read_text(encoding='utf-8')).get('derivations',[]))
        data['derivations']=derivations
        return check_selection(references,data)
    return guard
