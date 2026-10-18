"""Read-only IFC geometry extraction using the installed native IfcOpenShell kernel.
Produces native GLB plus lossless mesh arrays and per-product diagnostics. No LLM or repair.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import time
import numpy as np


def mesh_is_valid(vertices, faces):
    return bool(vertices.ndim==2 and vertices.shape[1]==3 and len(vertices)>0
                and faces.ndim==2 and faces.shape[1]==3 and len(faces)>0
                and np.isfinite(vertices).all() and faces.min()>=0 and faces.max()<len(vertices))


def extract(source: Path, output: Path) -> dict:
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.unit
    output.mkdir(parents=True, exist_ok=True)
    start=time.perf_counter()
    before=source.read_bytes()
    if before.startswith(b'version https://git-lfs'):raise ValueError('Source is still an LFS pointer')
    snapshot=output/'source.ifc'
    if snapshot.exists() and snapshot.read_bytes()!=before:
        raise ValueError('Output folder belongs to a different IFC; use another sample directory')
    snapshot.write_bytes(before)
    model=ifcopenshell.open(str(source))
    expected=[];excluded=[]
    for p in model.by_type('IfcProduct'):
        reps=list(getattr(getattr(p,'Representation',None),'Representations',[]) or [])
        has_body=any(r.RepresentationIdentifier=='Body' for r in reps)
        if has_body and not p.is_a('IfcSpace') and not p.is_a('IfcOpeningElement'):
            expected.append(p)
        else:excluded.append({'id':p.id(),'type':p.is_a(),'reason':'space/opening operand' if has_body else 'no Body'})
    settings=ifcopenshell.geom.settings()
    configured={'use-world-coords':True,'weld-vertices':True,'disable-opening-subtractions':False,'mesher-linear-deflection':0.0005}
    for key,value in configured.items():settings.set(key,value)
    settings.set('context-identifiers',['Body'])
    ifcopenshell.ifcopenshell_wrapper.set_log_format_json()
    materials=[];items=[];arrays={};failures=[];mins=[];maxs=[]
    serializer=None;export_error=None
    try:
        options=ifcopenshell.geom.serializer_settings();options.set('use-element-guids',True)
        serializer=ifcopenshell.geom.serializers.gltf(str(output/'model.glb'),settings,options)
        serializer.setFile(model);serializer.writeHeader()
    except Exception as e:export_error=str(e)
    for i,p in enumerate(expected):
        record={'id':p.id(),'guid':p.GlobalId,'type':p.is_a(),'name':p.Name}
        try:
            shape=ifcopenshell.geom.create_shape(settings,p)
            g=shape.geometry
            vertices=np.asarray(g.verts,dtype=np.float64).reshape(-1,3)
            faces=np.asarray(g.faces,dtype=np.int32).reshape(-1,3)
            if not mesh_is_valid(vertices,faces):raise ValueError('Empty, nonfinite or invalid-index triangle mesh')
            palette=[]
            for m in g.materials:
                rgb=[float(m.diffuse.r()),float(m.diffuse.g()),float(m.diffuse.b())]
                trans=float(m.transparency)
                if not np.isfinite(trans):trans=0.0
                palette.append({'name':m.name,'rgba':rgb+[1-trans]})
            mids=np.asarray(g.material_ids,dtype=np.int32)
            if len(mids)!=len(faces):raise ValueError('Face/material cardinality mismatch')
            record.update(vertices=len(vertices),triangles=len(faces),bounds=[vertices.min(0).tolist(),vertices.max(0).tolist()],materials=palette,material_face_counts=dict(Counter(map(int,mids))))
            key=str(p.id());arrays[key+'_v']=vertices;arrays[key+'_f']=faces;arrays[key+'_m']=mids
            mins.append(vertices.min(0));maxs.append(vertices.max(0));items.append(record)
            if serializer is not None:serializer.write(shape)
        except Exception as e:
            record['error']=str(e);failures.append(record)
        if (i+1)%25==0:print('Processed',i+1,'/',len(expected),flush=True)
    if serializer is not None:
        try:serializer.finalize()
        except Exception as e:export_error=str(e)
    # get_log returns native diagnostics, which must not be suppressed to manufacture success.
    native_log=ifcopenshell.get_log()
    (output/'native-geometry.log').write_text(native_log,encoding='utf8')
    np.savez_compressed(output/'meshes.npz',**arrays)
    unchanged=source.read_bytes()==before
    report={'source':{'path':source.as_posix(),'bytes':len(before),'schema':model.schema,'unchanged_byte_for_byte':unchanged,'metres_per_project_unit':ifcopenshell.util.unit.calculate_unit_scale(model)},'kernel':{'ifcopenshell':ifcopenshell.version,'settings':configured,'representation':'Body'},'expected_body_products':len(expected),'rendered_products':len(items),'missing':failures,'counts_by_type':dict(Counter(r['type'] for r in items)),'triangles':sum(x['triangles'] for x in items),'bounds_world_metres':[np.min(mins,axis=0).tolist(),np.max(maxs,axis=0).tolist()] if mins else None,'products':items,'excluded':excluded,'glb_error':export_error,'glb_bytes':(output/'model.glb').stat().st_size if (output/'model.glb').exists() else 0,'native_log_lines':len(native_log.splitlines()),'elapsed_seconds':round(time.perf_counter()-start,3),'ifc_validator_run':False,'repair_run':False}
    (output/'native-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['products','excluded']},ensure_ascii=False,indent=2),flush=True)
    if not unchanged:raise RuntimeError('Source changed during read-only extraction')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();report=extract(a.source,a.output)
    raise SystemExit(0 if not report['missing'] and report['rendered_products']>0 else 2)
