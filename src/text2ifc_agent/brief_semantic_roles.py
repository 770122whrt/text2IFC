"""Executable roles for explicit Brief identities; never infer roles from ID text."""
from collections.abc import Mapping
from text2ifc_contract.materials import (
    LAYER_OCCURRENCES, LAYER_TYPES, SINGLE_OCCURRENCES, TYPE_OCCURRENCE,
)

COLLECTION_CLASSES = {'walls':'IfcWall','doors':'IfcDoor','windows':'IfcWindow',
    'columns':'IfcColumn','beams':'IfcBeam',
    'spaces':'IfcSpace','floor_slabs':'IfcSlab','slabs':'IfcSlab','roof_slab':'IfcSlab',
    'roof':'IfcRoof','railings':'IfcRailing','stairs':'IfcStair','storeys':'IfcBuildingStorey'}

def role_index(brief):
    """Only actual identity records, not semantic references or narrative maps."""
    from .semantic_requirements import SEMANTIC_FIELDS
    identities={};issues=[];duplicates={};referenced=set()
    def references(value):
        if not isinstance(value,Mapping) or not SEMANTIC_FIELDS.intersection(value):return
        for identity in (value.get('entity_id',value.get('id')),value.get('type_id')):
            if isinstance(identity,str):referenced.add(identity)
    known=brief.get('known_facts',{})
    if not isinstance(known,Mapping):return {},[]
    requirements=known.get('semantic_requirements',[])
    for row in requirements if isinstance(requirements,list) else []:references(row)
    def visit(value,path,expected=None):
        if isinstance(value,list):
            for i,item in enumerate(value): visit(item,f'{path}/{i}',expected)
        elif isinstance(value,Mapping):
            references(value)
            identity=value.get('id');declared=value.get('ifc_class',expected)
            if isinstance(identity,str) and identity and isinstance(declared,str):
                if identity in identities:
                    duplicates[identity]=(path,declared)
                else:identities[identity]={'ifc_class':declared,'path':path,'record':value}
                # A product's nested style/material data cannot introduce identities.
                if declared!='IfcBuildingStorey':return
            for key,child in value.items():
                if key in {'semantic_requirements','semantic_review','appearance','fact_sources'}:continue
                visit(child,f'{path}/{key}',COLLECTION_CLASSES.get(key,expected if key in {'exterior','interior'} else None))
    visit(known,'/known_facts')
    for identity,(path,declared) in duplicates.items():
        if identity in referenced or declared in TYPE_OCCURRENCE or identities[identity]['ifc_class'] in TYPE_OCCURRENCE:
            issues.append({'code':'SEMANTIC_ROLE_IDENTITY_AMBIGUOUS','path':path,
                'message':'A semantic identity has multiple defining records; resolve the target before recovery.'})
        # Storey-local geometry names remain legal in the geometry contract.
        # Never arbitrarily use their first definition as a semantic target.
        identities.pop(identity)
    return identities,issues

def role_issue(row,identities,*,railing_enabled=False):
    identity=row['entity_id'];definition=identities.get(identity,{})
    cls=definition.get('ifc_class');kind=row['kind'];value=row['value'];code=None
    if kind=='type':
        other=identities.get(value,{}) if isinstance(value,str) else {}
        target=other.get('ifc_class')
        if value==identity or cls in TYPE_OCCURRENCE:code='SEMANTIC_TYPE_TARGET_ROLE'
        elif cls and target and TYPE_OCCURRENCE.get(target)!=('IfcWall' if cls=='IfcWallStandardCase' else cls):
            code='SEMANTIC_TYPE_FAMILY_MISMATCH'
    elif kind=='template' and cls:
        template=value.get('template_id') if isinstance(value,Mapping) else None
        family={'door-left':'IfcDoor','door-right':'IfcDoor','window-single':'IfcWindow',
                'window-double-vertical':'IfcWindow'}.get(template)
        if railing_enabled and template=='metal-picket':family='IfcRailing'
        if cls!=family or row.get('scope')=='inherited':code='SEMANTIC_TEMPLATE_TARGET_ROLE'
    elif kind=='material' and cls and isinstance(value,Mapping):
        material_kind=value.get('kind');scope=row.get('scope','effective')
        if material_kind=='single_material':
            if cls not in SINGLE_OCCURRENCES | TYPE_OCCURRENCE.keys():code='SEMANTIC_MATERIAL_SCOPE_MISMATCH'
        elif material_kind=='material_list':
            if cls == 'IfcWallStandardCase' or cls not in SINGLE_OCCURRENCES | TYPE_OCCURRENCE.keys():
                code='SEMANTIC_MATERIAL_SCOPE_MISMATCH'
        elif material_kind=='material_layer_set':
            # An inherited layer set is a Type value, not a direct instance usage.
            if cls not in LAYER_TYPES and not (scope=='inherited' and cls in LAYER_OCCURRENCES):
                code='SEMANTIC_MATERIAL_SCOPE_MISMATCH'
        elif material_kind=='material_layer_set_usage':
            if cls not in LAYER_OCCURRENCES or scope=='inherited':code='SEMANTIC_MATERIAL_SCOPE_MISMATCH'
            elif value.get('direction')!=LAYER_OCCURRENCES[cls]:code='SEMANTIC_MATERIAL_AXIS_MISMATCH'
        if cls in TYPE_OCCURRENCE and scope=='inherited':code='SEMANTIC_MATERIAL_SCOPE_MISMATCH'
    if code:return {'code':code,'path':row['source_path'],
        'message':f'{kind} requirement for {identity!r} does not match its explicit IFC role/scope; correct semantics without changing the identity or geometry.'}
    return None

def filter_roles(brief,expectations):
    if brief.get('schema_version') not in {'text2ifc/design-brief/2.4', 'text2ifc/design-brief/2.5', 'text2ifc/design-brief/2.6', 'text2ifc/design-brief/2.7', 'text2ifc/design-brief/2.8', 'text2ifc/design-brief/2.9'}:return expectations,[]
    identities,issues=role_index(brief);valid=[]
    bindings={}
    for row in expectations:
        issue=role_issue(row,identities,railing_enabled=brief.get('schema_version')in {'text2ifc/design-brief/2.6', 'text2ifc/design-brief/2.7', 'text2ifc/design-brief/2.8', 'text2ifc/design-brief/2.9'})
        if brief.get('schema_version') in {'text2ifc/design-brief/2.7', 'text2ifc/design-brief/2.8', 'text2ifc/design-brief/2.9'} and row['kind'] == 'appearance' and identities.get(row['entity_id'], {}).get('ifc_class') == 'IfcStair':
            from .cross_storey_identity import stair_flight_ids
            flights = stair_flight_ids(identities[row['entity_id']]['record'], row['entity_id'])
            issue = {'code': 'SEMANTIC_APPEARANCE_TARGET_ROLE', 'path': row['source_path'],
                'message': f'IfcStair is the assembly, not the visible flight body. Preserve the requested appearance on its flight identities {flights!r}; keep assembly material and all geometry unchanged.'}
        if issue:issues.append(issue)
        else:
            valid.append(row)
            if row['kind']=='type':bindings.setdefault(row['entity_id'],set()).add(str(row['value']))
    for identity,targets in bindings.items():
        if len(targets)>1:
            rows=[r for r in valid if r['entity_id']==identity and r['kind']=='type']
            issues.append({'code':'SEMANTIC_TYPE_MULTIPLE','path':rows[0]['source_path'],
                'message':'An occurrence has multiple requested effective Types; do not select one silently.'})
            valid=[r for r in valid if r not in rows]
    declared={}
    for row in valid:
        if row['kind'] not in {'material','property'}:continue
        key=(row['entity_id'],row['scope'],row['kind'],row.get('pset'),row.get('property'))
        if key in declared and declared[key]!=row['value']:
            issues.append({'code':'SEMANTIC_VALUE_CONFLICT','path':row['source_path'],
                'message':'The same target/scope has incompatible values; resolve the request rather than silently selecting one.'})
        else:declared[key]=row['value']
    return valid,issues

def removable_semantic_paths(brief):
    """Explicit products/types may lose semantic leaves only, never identity data."""
    if brief.get('schema_version') not in {'text2ifc/design-brief/2.4', 'text2ifc/design-brief/2.5', 'text2ifc/design-brief/2.6', 'text2ifc/design-brief/2.7', 'text2ifc/design-brief/2.8', 'text2ifc/design-brief/2.9'}:return []
    from .semantic_requirements import SEMANTIC_FIELDS
    identities,issues=role_index(brief)
    if issues:return []
    return sorted(f"{d['path']}/{key}" for d in identities.values()
        for key in SEMANTIC_FIELDS if key in d['record'])

def strip_paths(document,paths):
    import copy
    fixed=copy.deepcopy(document)
    for path in paths:
        parts=path.split('/')[1:];parent=fixed
        try:
            for part in parts[:-1]:parent=parent[int(part)] if isinstance(parent,list) else parent[part]
            if isinstance(parent,dict):parent.pop(parts[-1],None)
        except (KeyError,IndexError,TypeError,ValueError):
            # Leave altered/missing ancestors in place for the frozen-part
            # comparison to reject, rather than crashing before a failure trace.
            continue
    return fixed

def recoverable_value_loss(before,after):
    """Invalid format cannot justify losing its concrete material/template intent."""
    from .semantic_requirements import project_semantic_requirements,SEMANTIC_FIELDS
    identities,_=role_index(before)
    values=project_semantic_requirements(after)['expectations']
    records=[r for r in before.get('known_facts',{}).get('semantic_requirements',[]) if isinstance(r,Mapping)]
    records += [d['record'] for d in identities.values() if SEMANTIC_FIELDS.intersection(d['record'])]
    assignments={}
    for row in records:
        identity=row.get('entity_id',row.get('id'));target=row.get('type_id')
        if isinstance(target,str) and identity!=target and identities.get(identity,{}).get('ifc_class') not in TYPE_OCCURRENCE:
            assignments.setdefault(target,set()).add(identity)
    def material_content(value):
        if isinstance(value,str) and value.strip():return ('single',value)
        if not isinstance(value,Mapping):return None
        if value.get('kind')=='single_material' and value.get('name'):return ('single',value['name'])
        if value.get('kind')=='material_list' and isinstance(value.get('materials'),list) and value['materials'] and all(isinstance(x,Mapping) and isinstance(x.get('name'),str) and x['name'].strip() for x in value['materials']):
            return ('list',[x['name'] for x in value['materials']])
        layers=value.get('layers')
        if value.get('kind') in {'material_layer_set','material_layer_set_usage'} and isinstance(layers,list) and layers and all(isinstance(x,Mapping) and x.get('name') and isinstance(x.get('thickness'),(int,float)) and x['thickness']>0 for x in layers):
            return ('layers',[(x['name'],x['thickness']) for x in layers])
        return None
    for record in records:
        identity=record.get('entity_id',record.get('id'))
        if before.get('schema_version') in {'text2ifc/design-brief/2.7', 'text2ifc/design-brief/2.8', 'text2ifc/design-brief/2.9'} and 'appearance' in record and identities.get(identity, {}).get('ifc_class') == 'IfcStair':
            from .cross_storey_identity import stair_flight_ids
            flights = stair_flight_ids(identities[identity]['record'], identity)
            if any(not any(r['entity_id'] == flight and r['kind'] == 'appearance' and r['value'] == record['appearance'] and r['scope'] == record.get('scope', 'effective') for r in values) for flight in flights):
                return True
        material=record.get('material')
        if material is None and isinstance(record.get('materials'),list) and len(record['materials'])==1:material=record['materials'][0]
        content=material_content(material)
        if content and not any(r['entity_id']==identity and r['kind']=='material' and material_content(r['value'])==content for r in values):return True
        template=record.get('template')
        if isinstance(template,Mapping):
            targets=assignments.get(identity,{identity}) if identities.get(identity,{}).get('ifc_class') in TYPE_OCCURRENCE else {identity}
            if not targets or any(not any(r['entity_id']==target and r['kind']=='template' and r['value']==template for r in values) for target in targets):return True
    return False
