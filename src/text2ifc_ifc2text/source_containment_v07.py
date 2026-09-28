"""Audit and explicitly normalize filling containment in a NEW source-work copy.

Different host/recorded containers are not by themselves an IFC schema defect.
Normalization is a modeling policy; the original remains the archival baseline.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import os
import uuid
import ifcopenshell
import ifcopenshell.util.placement
import ifcopenshell.util.unit

POLICY='host_storey_for_selected_fillings'


def _container(entity):
    relations=list(getattr(entity,'ContainedInStructure',()) or ())
    if len(relations)!=1:return None
    return relations[0].RelatingStructure


def _host(entity):
    fills=list(getattr(entity,'FillsVoids',()) or ())
    if len(fills)!=1:return None,None
    opening=fills[0].RelatingOpeningElement
    voids=list(getattr(opening,'VoidsElements',()) or ())
    return (opening,voids[0].RelatingBuildingElement) if len(voids)==1 else (opening,None)


def _ref(entity):
    if entity is None:return None
    return {'global_id':entity.GlobalId,'name':entity.Name,'class':entity.is_a()}


def inspect_containment(source: str | Path) -> dict:
    source=Path(source); before=source.read_bytes()
    model=ifcopenshell.open(str(source))
    scale=ifcopenshell.util.unit.calculate_unit_scale(model)*1000
    floors=[]
    for s in model.by_type('IfcBuildingStorey'):
        contents=[e for rel in s.ContainsElements for e in rel.RelatedElements]
        floors.append({**_ref(s),'elevation_mm':None if s.Elevation is None else float(s.Elevation)*scale,
            'composition_type':getattr(s,'CompositionType',None),
            'contained_counts':dict(Counter(e.is_a() for e in contents)),
            'space_count':sum(e.is_a('IfcSpace') for r in s.IsDecomposedBy for e in r.RelatedObjects)})
    records=[]
    for entity in [*model.by_type('IfcDoor'),*model.by_type('IfcWindow')]:
        opening,host=_host(entity); container=_container(entity); hc=_container(host) if host else None
        mismatch=container is not None and hc is not None and container!=hc
        row={**_ref(entity),'recorded_container':_ref(container),'host':_ref(host),'host_container':_ref(hc),
            'opening':_ref(opening),'recorded_vs_host_different':mismatch,
            'containment_cardinality':len(entity.ContainedInStructure),
            'difference_alone_proves_source_error':False,
            'eligible_for_explicit_host_policy':bool(mismatch and container.is_a('IfcBuildingStorey') and hc.is_a('IfcBuildingStorey'))}
        if entity.ObjectPlacement:
            row['world_placement_origin_mm']=(ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement)[:3,3]*scale).tolist()
            row['placement_relative_to_opening']=bool(opening and entity.ObjectPlacement.PlacementRelTo==opening.ObjectPlacement)
        records.append(row)
    assert source.read_bytes()==before
    return {'schema_version':'text2ifc/source-containment-review/0.7','source':str(source),'ifc_schema':model.schema,
        'normalization_applied':False,'source_unchanged':True,'storeys':floors,'fillings':records,
        'conclusion':'Mixed recording/hosting conventions are observed; architectural intent is not proved by containment alone.',
        'validation_scope':'targeted relationship and placement inspection, not full IFC validation'}


def normalize_copy(source: str | Path, destination: str | Path, *, selected_global_ids: list[str], policy: str) -> dict:
    source,destination=Path(source),Path(destination)
    if source.resolve()==destination.resolve() or destination.exists():raise ValueError('SOURCE_OR_EXISTING_OUTPUT_OVERWRITE_FORBIDDEN')
    if policy!=POLICY:raise ValueError('EXPLICIT_HOST_POLICY_REQUIRED')
    if not selected_global_ids or len(set(selected_global_ids))!=len(selected_global_ids):raise ValueError('EXPLICIT_UNIQUE_SELECTION_REQUIRED')
    before=source.read_bytes(); audit=inspect_containment(source)
    eligible={x['global_id']:x for x in audit['fillings'] if x['eligible_for_explicit_host_policy']}
    if not set(selected_global_ids)<=eligible.keys():raise ValueError('SELECTION_NOT_ELIGIBLE')
    model=ifcopenshell.open(str(source))
    untouched={e.id():str(e) for e in model if not e.is_a('IfcRelContainedInSpatialStructure')}
    original_containment={e.GlobalId:getattr(_container(e),'GlobalId',None) for e in model.by_type('IfcElement')}
    changed=[]
    for gid in selected_global_ids:
        entity=model.by_guid(gid); old=entity.ContainedInStructure[0]
        _,host=_host(entity); target=_container(host)
        target_rel=host.ContainedInStructure[0]
        source_container=old.RelatingStructure
        remaining=tuple(x for x in old.RelatedElements if x!=entity)
        if remaining:old.RelatedElements=remaining
        else:model.remove(old)
        target_rel.RelatedElements=tuple(target_rel.RelatedElements)+(entity,)
        changed.append({'global_id':gid,'from':_ref(source_container),'to':_ref(target),'host':_ref(host)})
    assert untouched=={e.id():str(e) for e in model if not e.is_a('IfcRelContainedInSpatialStructure')},'UNEXPECTED_ENTITY_CHANGE'
    destination.parent.mkdir(parents=True,exist_ok=True)
    temp=destination.with_name(destination.stem+'.pending-'+uuid.uuid4().hex+'.ifc')
    try:
        model.write(str(temp)); reopened=ifcopenshell.open(str(temp))
        assert untouched=={e.id():str(e) for e in reopened if not e.is_a('IfcRelContainedInSpatialStructure')},'ROUNDTRIP_CHANGED_NONCONTAINMENT'
        for entity in reopened.by_type('IfcElement'):
            if entity.GlobalId in selected_global_ids:
                assert _container(entity)==_container(_host(entity)[1])
            else:
                assert getattr(_container(entity),'GlobalId',None)==original_containment[entity.GlobalId]
        assert all(len(r.RelatedElements)>0 for r in reopened.by_type('IfcRelContainedInSpatialStructure'))
        assert source.read_bytes()==before,'SOURCE_MUTATED'
        with destination.open('xb') as stream:stream.write(temp.read_bytes())
    finally:
        if temp.exists():temp.unlink()
    return {'schema_version':'text2ifc/source-normalization/0.7','policy':policy,'source':str(source),'destination':str(destination),
        'role':'policy_normalized_working_copy_not_proof_of_source_defect','moved_count':len(changed),'changes':changed,
        'geometry_and_noncontainment_entities_unchanged':True,'source_unchanged':True,
        'reference_storeys_preserved':True,'original_roundtrip_evidence_replaced':False}
