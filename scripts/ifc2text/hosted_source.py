"""Select a native filling and its complete host on an independent IFC copy.

Every opening of that host is retained, even when its other filling is outside
the selection. Thus selecting a test scene never heals an existing wall cut.
This is source preparation, not a reconstruction algorithm.
"""
from pathlib import Path
import hashlib

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.geom
import ifcopenshell.util.element
import numpy as np

from text2ifc_ifc2text.filling_compare_v12 import compare_filling_geometry


def _mesh(product):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    shape=ifcopenshell.geom.create_shape(settings,product)
    return np.asarray(shape.geometry.verts),np.asarray(shape.geometry.faces)


def _same_mesh(first,second):
    a,af=_mesh(first);b,bf=_mesh(second)
    # Identical native representations, transforms and cuts must tessellate the
    # same way; this strict copy check is not a reconstruction tolerance metric.
    return a.shape==b.shape and np.array_equal(af,bf) and np.allclose(a,b,atol=1e-10,rtol=0)


def isolate_hosted_filling(source,output,global_id):
    source,output=Path(source),Path(output)
    if source.resolve()==output.resolve():raise ValueError('SOURCE_OUTPUT_SAME')
    if output.exists():raise ValueError('OUTPUT_EXISTS')
    before=source.read_bytes()
    original=ifcopenshell.open(str(source));selected=original.by_guid(global_id)
    if selected.is_a() not in {'IfcDoor','IfcWindow'}:raise ValueError('SELECT_DOOR_OR_WINDOW')
    if len(selected.FillsVoids)!=1:raise ValueError('EXACTLY_ONE_OPENING_REQUIRED')
    opening=selected.FillsVoids[0].RelatingOpeningElement
    if len(opening.VoidsElements)!=1:raise ValueError('EXACTLY_ONE_HOST_REQUIRED')
    host=opening.VoidsElements[0].RelatingBuildingElement
    if not host.is_a('IfcWall'):raise ValueError('SUPPORTED_WALL_HOST_REQUIRED')
    cuts=[r.RelatedOpeningElement for r in host.HasOpenings]
    model=ifcopenshell.file.from_string(original.to_string())
    keep={selected.id(),host.id(),*(o.id() for o in cuts)}
    for product in (selected,host):
        container=ifcopenshell.util.element.get_container(product)
        visited=set()
        while container is not None:
            if container.id() in visited:raise ValueError('CYCLIC_SPATIAL_HIERARCHY')
            visited.add(container.id());keep.add(container.id())
            container=ifcopenshell.util.element.get_aggregate(container)
    if not any(model.by_id(i).is_a('IfcBuildingStorey') for i in keep):raise ValueError('EXPLICIT_STOREY_REQUIRED')
    removal=[p.id() for p in model.by_type('IfcProduct') if p.id() not in keep]
    for identity in removal:
        try: product=model.by_id(identity)
        except RuntimeError:continue
        ifcopenshell.api.root.remove_product(model,product=product)
    comparison=compare_filling_geometry(selected,model.by_guid(global_id))
    host_same=_same_mesh(host,model.by_guid(host.GlobalId))
    cuts_same=all(_same_mesh(c,model.by_guid(c.GlobalId)) for c in cuts)
    if not comparison['pass'] or not host_same or not cuts_same:
        raise ValueError('HOSTED_SELECTION_GEOMETRY_CHANGED_OR_UNASSESSED')
    if source.read_bytes()!=before:raise ValueError('SOURCE_CHANGED')
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8',newline='') as stream:stream.write(model.to_string())
    reopened=ifcopenshell.open(str(output));target=reopened.by_guid(global_id)
    if len(reopened.by_type('IfcElement'))!=2+len(cuts) or len(target.FillsVoids)!=1:
        raise ValueError('HOSTED_SELECTION_INVALID')
    return {'scope':'Native filling, complete host wall and all of its openings; other products excluded from this test selection',
        'source_path':str(source),'source_sha256':hashlib.sha256(before).hexdigest(),
        'selected_global_id':global_id,'host_global_id':host.GlobalId,
        'opening_global_ids':[o.GlobalId for o in cuts],
        'output_path':str(output),'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'filling_comparison':comparison,'host_mesh_unchanged':host_same,
        'opening_meshes_unchanged':cuts_same,'source_bytes_unchanged':source.read_bytes()==before,
        'not_evaluated':['whole building','live text loop']}
