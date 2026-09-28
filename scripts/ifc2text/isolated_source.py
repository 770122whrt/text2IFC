"""Create an explicitly standalone native source selection, never a reconstruction.

Clone the complete IFC first so inverse style/material/type associations survive.
Remove other products only from that clone. Source GUID is evaluator metadata;
only the resulting public architectural description enters generation.
"""
from pathlib import Path
import hashlib

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.util.element

from text2ifc_ifc2text.filling_compare_v12 import compare_filling_geometry


def isolate_filling(source, output, global_id):
    source,output=Path(source),Path(output)
    if source.resolve()==output.resolve():
        raise ValueError('SOURCE_OUTPUT_SAME')
    if output.exists():
        raise ValueError('OUTPUT_EXISTS')
    before=source.read_bytes()
    original=ifcopenshell.open(str(source));selected=original.by_guid(global_id)
    if selected.is_a() not in {'IfcDoor','IfcWindow'}:
        raise ValueError('SELECT_DOOR_OR_WINDOW')
    model=ifcopenshell.file.from_string(original.to_string())
    target=model.by_guid(global_id)
    keep={target.id()}
    container=ifcopenshell.util.element.get_container(target)
    while container is not None:
        if container.id() in keep:
            raise ValueError('CYCLIC_SPATIAL_HIERARCHY')
        keep.add(container.id())
        container=ifcopenshell.util.element.get_aggregate(container)
    if not any(model.by_id(i).is_a('IfcBuildingStorey') for i in keep):
        raise ValueError('EXPLICIT_STOREY_REQUIRED')
    # Snapshot IDs, not entity pointers: removing a host also removes openings.
    removal=[p.id() for p in model.by_type('IfcProduct') if p.id() not in keep]
    for identity in removal:
        try: product=model.by_id(identity)
        except RuntimeError: continue
        ifcopenshell.api.root.remove_product(model,product=product)
    target=model.by_guid(global_id)
    comparison=compare_filling_geometry(selected,target)
    if not comparison['pass']:
        raise ValueError('SELECTION_GEOMETRY_CHANGED_OR_UNASSESSED: '+str(comparison))
    if source.read_bytes()!=before:
        raise ValueError('SOURCE_CHANGED')
    output.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive creation avoids replacing an earlier input or experiment.
    with output.open('x',encoding='utf-8',newline='') as stream:
        stream.write(model.to_string())
    reopened=ifcopenshell.open(str(output))
    if len(reopened.by_type('IfcElement'))!=1 or reopened.by_guid(global_id).FillsVoids:
        raise ValueError('STANDALONE_SELECTION_INVALID')
    return {'scope':'Native standalone selection; host installation deliberately not assessed',
        'source_path':str(source),'source_sha256':hashlib.sha256(before).hexdigest(),
        'selected_global_id':global_id,'ifc_class':selected.is_a(),
        'output_path':str(output),'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'geometry_comparison':comparison,'source_bytes_unchanged':source.read_bytes()==before,
        'not_evaluated':['host installation','whole building','live text loop']}
