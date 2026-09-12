"""Read actual mesh/IFC; produce disclosed isolated views without model edits."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[4]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--image-python',required=True)
    parser.add_argument('--views', type=Path, default=OUT/'review-views')
    parser.add_argument('--output', type=Path, default=OUT/'design-recheck');args=parser.parse_args()
    source=args.views/'overall-mesh.json'
    payload=json.loads(source.read_text(encoding='utf-8'));products=payload['products']
    out=args.output;out.mkdir(exist_ok=False)
    def bounds(p): return [[min(p['verts'][i::3]),max(p['verts'][i::3])] for i in range(3)]
    selected=[p for p in products if p['kind'] in {'IfcRailing','IfcStairFlight'}]
    report={'source_ifc_sha256':payload['sha256'],'mesh_failures':payload['mesh_failures'],
        'actual_components':[{'guid':p['id'],'name':p['name'],'ifc_class':p['kind'],
            'world_bounds_metres':bounds(p),'render_material_rgba':p['materials'],
            'triangles':len(p['faces'])//3} for p in selected],
        'court_area_m2':48,'footprint_area_m2':432,'court_fraction':48/432,
        'limits':'Geometric presence is not proof of concept fidelity, support connections, graspable handrails or complete usable circulation.'}
    views={
        'railings-isolated':([p for p in products if p['kind']=='IfcRailing'],
            '只显示原IFC四块栏板，隐藏其余构件；不改变RGB或透明度。'),
        'stairs-isolated':([p for p in products if p['kind']=='IfcStairFlight'],
            '只显示原IFC梯段，隐藏围护墙和楼板；不代表原方案采用开放楼梯。'),
        'structure-cutaway':([p for p in products if p['kind'] in {'IfcRailing','IfcStairFlight'} or
            (p['kind']=='IfcSlab' and bounds(p)[2][0]<6.99)],
            '隐藏所有墙、门窗和屋面，仅显示实际地板、二层楼板、梯段、玻璃栏板；暴露构件关系，不新增构件。'),
    }
    for name,(items,note) in views.items():
        mesh=out/(name+'.json');mesh.write_text(json.dumps({**payload,'products':items,'view_note':note},ensure_ascii=False),encoding='utf-8')
        renderer=ROOT/'dataset/processed/ifc-presentation-validation/three-storey-human-review-20260909/render_png.py'
        subprocess.run([args.image_python,str(renderer),str(mesh),str(out/(name+'.png'))],check=True)
    report['views']={k:v[1] for k,v in views.items()}
    (out/'geometry-presence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'components':len(selected),'views':len(views)}))

if __name__=='__main__':main()
