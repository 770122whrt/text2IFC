"""Offline native IFC -> component JSON -> IFC diagnostic, NOT a text/LLM loop.

Select every door/window before reading outcomes. Compare complete product meshes,
including all source Body items; refused products remain in the denominator.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'src'),str(ROOT/'.deps/python312')]

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.shape
import ifcopenshell.util.unit
import numpy as np
from scipy.spatial import cKDTree

from text2ifc_compiler.compiler import compile_document
from text2ifc_ifc2text.component_details_v10 import read_component_geometry


def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')


def isolated_document(product, representation):
    def pos(parent, matrix=None):
        m = np.eye(4) if matrix is None else matrix
        return {'relative_to':parent,'origin':m[:3,3].tolist(),'axis':m[:3,2].tolist(),'ref_direction':m[:3,0].tolist()}
    def record(identity, cls, attributes):
        return {'id':identity,'ifc_class':cls,'attributes':attributes,'property_sets':{},'provenance':{'source':'native-component-diagnostic'}}
    entities = [record('project','IfcProject',{'Name':'Native component diagnostic'})]
    for identity,cls,parent in [('site','IfcSite','project'),('building','IfcBuilding','site'),('storey','IfcBuildingStorey','building')]:
        entities.append(record(identity,cls,{'Name':identity,'ObjectPlacement':pos(parent)}))
    scale = ifcopenshell.util.unit.calculate_unit_scale(product.file)*1000
    frame = ifcopenshell.util.placement.get_local_placement(product.ObjectPlacement).copy()
    frame[:3,3] *= scale
    attributes = {'Name':product.Name or product.GlobalId,'ObjectPlacement':pos('storey',frame),'Representation':representation}
    for name in ('OverallWidth','OverallHeight'):
        value = getattr(product,name,None)
        if value is not None: attributes[name] = float(value)*scale
    entities.append(record('filling',product.is_a(),attributes))
    return {'schema_version':'bim-json/2.6','ifc_schema':'IFC2X3','units':{'length':'MILLIMETRE'},'entities':entities,'relationships':[],
            'provenance':{'source':'native-component-diagnostic'}}


def mesh_measure(product):
    settings = ifcopenshell.geom.settings()
    settings.set('use-world-coords',True)
    settings.set('mesher-linear-deflection',0.0001)
    shape = ifcopenshell.geom.create_shape(settings,product)
    mesh = shape.geometry
    vertices = np.asarray(mesh.verts).reshape(-1,3)*1000
    return vertices, {'volume_mm3':ifcopenshell.util.shape.get_volume(mesh)*1e9,
                      'area_mm2':ifcopenshell.util.shape.get_area(mesh)*1e6,
                      'mesh_vertices':len(vertices),'mesh_triangles':len(mesh.faces)//3}


def compare(source, rebuilt):
    a,am = mesh_measure(source); b,bm = mesh_measure(rebuilt)
    distance = max(float(cKDTree(a).query(b)[0].max()),float(cKDTree(b).query(a)[0].max()))
    volume_error = abs(am['volume_mm3']-bm['volume_mm3'])/max(am['volume_mm3'],1e-12)
    area_error = abs(am['area_mm2']-bm['area_mm2'])/max(am['area_mm2'],1e-12)
    return {'source_geometry':am,'rebuilt_geometry':bm,'symmetric_vertex_distance_mm':distance,
            'volume_relative_error':volume_error,'area_relative_error':area_error,
            'passed_native_diagnostic':distance<=1. and volume_error<=1e-6 and area_error<=1e-6,
            'limits':'Full-product tessellated vertices/area/volume, not exact surface Hausdorff or installation validation.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,action='append',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    sources = []
    for source in args.source:
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        model = ifcopenshell.open(str(source))
        selected = [*model.by_type('IfcWindow'),*model.by_type('IfcDoor')]
        sources.append((source,digest,model,selected))
    write(args.output/'selection.json',{'scope':'native deterministic single-product diagnostic; zero Provider calls',
        'sources':[{'path':str(p),'sha256':d,'ifc_schema':m.schema,'selection':[e.GlobalId for e in s]} for p,d,m,s in sources],
        'linear_tolerance_mm':1.,'volume_relative_tolerance':1e-6,'area_relative_tolerance':1e-6,
        'not_evaluated':['public text chain','Brief','LLM','host installation','whole-building','materials','physical part materials']})
    rows = []
    for source,digest,model,selected in sources:
        for index,product in enumerate(selected):
            case = args.output/f'{digest[:10]}-{index+1:03d}'
            case.mkdir()
            row = {'source':str(source),'source_sha256':digest,'global_id':product.GlobalId,'name':product.Name,
                   'ifc_class':product.is_a(),'case':case.name}
            detail = read_component_geometry(product)
            write(case/'source-components.json',detail)
            if detail['status'] != 'supported':
                rows.append({**row,'status':'unsupported','reasons':detail['unsupported']}); continue
            doc = isolated_document(product,detail['representation'])
            write(case/'bim.json',doc)
            compiled = compile_document(doc,case/'rebuilt.ifc')
            if not compiled.success:
                write(case/'compilation.json',asdict(compiled))
                rows.append({**row,'status':'compile_failed','issues':asdict(compiled)}); continue
            try:
                rebuilt = ifcopenshell.open(str(compiled.output_path)).by_type(product.is_a())[0]
                metrics = compare(product,rebuilt)
                write(case/'compare.json',metrics)
                rows.append({**row,'status':'passed' if metrics['passed_native_diagnostic'] else 'geometry_failed',**metrics})
            except Exception as exc:
                rows.append({**row,'status':'measurement_failed','error':f'{type(exc).__name__}: {exc}'})
            print(row['ifc_class'],row['global_id'],rows[-1]['status'],flush=True)
    unchanged = all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest,_,_ in sources)
    summary = {'scope':'offline native component diagnostic, not IFC->text->IFC','source_bytes_unchanged':unchanged,
               'counts':{status:sum(r['status']==status for r in rows) for status in sorted({r['status'] for r in rows})},'cases':rows}
    write(args.output/'summary.json',summary)
    print(json.dumps(summary['counts']),flush=True)


if __name__ == '__main__':
    main()
