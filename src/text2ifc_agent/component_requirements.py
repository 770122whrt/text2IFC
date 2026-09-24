"""Carry explicit component requests as parent-product requirements."""
import copy
import re

from jsonschema import Draft202012Validator
from text2ifc_contract.schema import load_schema_v26
from text2ifc_contract.component_geometry import validate_components


def project_component_request(brief, record, base):
    path=base['source_path']+'/component_geometry'
    def error(code,message): return [],[{'code':code,'path':path,'message':message}]
    if brief.get('schema_version') != 'text2ifc/design-brief/2.9':
        return error('COMPONENT_REQUEST_VERSION_UNSUPPORTED','Parameterized components require Design Brief 2.9; do not discard them or replace them with a template.')
    from .brief_semantic_roles import role_index
    identities,_=role_index(brief)
    cls=identities.get(base['entity_id'],{}).get('ifc_class')
    if cls not in {'IfcDoor','IfcWindow'} or base['scope']=='inherited':
        return error('COMPONENT_REQUEST_TARGET_INVALID','Components require an explicitly identified door/window occurrence; they are not inherited Type geometry.')
    value=record['component_geometry']
    schema=load_schema_v26()
    errors=list(Draft202012Validator({'$defs':schema['$defs'],'$ref':'#/$defs/componentGeometry'}).iter_errors(value))
    if errors:
        return error('COMPONENT_REQUEST_INCOMPLETE','Incomplete or unsupported component parameters: '+'; '.join(e.message for e in errors))
    invalid=validate_components(value,cls,path)
    if invalid:
        return [],[{'code':i.code,'path':i.path,'message':i.message} for i in invalid]
    return [{**base,'kind':'component_geometry','value':copy.deepcopy(value)}],[]


def component_request_conflicts(expectations):
    components={};templates=set();issues=[]
    for e in expectations:
        if e['kind']=='template': templates.add(e['entity_id'])
        if e['kind']!='component_geometry': continue
        identity=e['entity_id']
        if identity in components and components[identity]['value']!=e['value']:
            issues.append({'code':'COMPONENT_REQUEST_CONFLICT','path':e['source_path'],
                           'message':'The same door/window has different complete component descriptions; clarify which one applies.'})
        components[identity]=e
    for identity in components.keys() & templates:
        issues.append({'code':'COMPONENT_TEMPLATE_CONFLICT','path':components[identity]['source_path'],
                       'message':'A product cannot request both a template and explicit component geometry.'})
    return issues


def public_component_coverage(brief):
    """Check the explicit public catalog, never private IFC/facts or guessed prose.

    Numerical fidelity is still assessed against the source after reconstruction.
    This guard prevents a declared refusal or part from being silently dropped.
    """
    if brief.get('status') != 'ready':
        return []
    text=brief.get('original_request','')
    blocks=re.findall(r'^#### ([^\n]+) 部件几何\n(.*?)(?=^#{1,4} |\Z)',text,flags=re.M|re.S)
    if not blocks:
        return []
    from .brief_semantic_roles import role_index
    from text2ifc_contract.component_geometry import expanded_parts
    identities,_=role_index(brief)
    requests=brief.get('known_facts',{}).get('semantic_requirements',[])
    issues=[]
    for label,body in blocks:
        if '本构件不支持完整重建，需要人工确认' in body:
            issues.append({'code':'PUBLIC_COMPONENT_UNSUPPORTED','path':'/original_request',
                           'message':f'{label} 的公开说明明确报告不支持；必须讨论或修改请求，不能直接标记 ready。'})
            continue
        targets={identity for identity,row in identities.items()
                 if label in (identity, row.get('record',{}).get('label'),row.get('record',{}).get('name'))}
        relevant=[r for r in requests if r.get('entity_id') in targets and r.get('component_geometry')]
        required=set(re.findall(r'^- ([^：\n]+)：角色=',body,flags=re.M))
        observed=set()
        for record in relevant:
            observed.update(p['id'] for p in expanded_parts(record['component_geometry']))
        if not relevant or not required.issubset(observed):
            issues.append({'code':'PUBLIC_COMPONENT_DESCRIPTION_INCOMPLETE','path':'/known_facts/semantic_requirements',
                           'message':f'{label} 的公开部件说明未完整进入 Brief；缺失部件 {sorted(required-observed)}。'})
    return issues
