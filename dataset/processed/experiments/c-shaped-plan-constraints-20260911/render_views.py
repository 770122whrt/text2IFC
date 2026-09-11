"""Read-only actual IFC meshes; no generated geometry or decorative retouching."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from scripts.presentation.render_ifc_review import render

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('ifc',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--image-python',required=True)
    args=parser.parse_args()
    args.output.mkdir(exist_ok=False)
    render(args.ifc,args.output/'viewer.html')
    page=(args.output/'viewer.html').read_text(encoding='utf-8')
    payload=json.loads(page.split('<script>const data=',1)[1].split(';const canvas=',1)[0])
    assert not payload['mesh_failures']
    products=payload['products']
    selections={'overall':(products,'All represented physical products; source IFC unchanged.'),
                'ground-floor':([p for p in products if min(p['verts'][2::3])<.01 and p['kind']!='IfcStairFlight'],
                                'Only elements starting at the ground floor shown; upper elements and stair flights hidden in this view only.')}
    for kind in ['IfcWindow','IfcDoor']:
        matches=[p for p in products if p['kind']==kind]
        if matches:selections[kind]=(matches[:1],'One actual filling isolated; original IFC component colors.')
    renderer=ROOT/'dataset/processed/ifc-presentation-validation/three-storey-human-review-20260909/render_png.py'
    for name,(items,note) in selections.items():
        mesh=args.output/(name+'-mesh.json')
        mesh.write_text(json.dumps({**payload,'products':items,'view_note':note},ensure_ascii=False),encoding='utf-8')
        extra=['--pitch','1.57079632679','--yaw','0'] if name=='ground-floor' else []
        subprocess.run([args.image_python,str(renderer),str(mesh),str(args.output/(name+'.png')),*extra],check=True)

if __name__=='__main__':main()
