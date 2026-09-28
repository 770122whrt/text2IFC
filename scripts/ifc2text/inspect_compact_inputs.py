"""Read-only size/coverage survey for compact IFC2Text development."""
from pathlib import Path
import json
import re
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
import ifcopenshell

def main():
    records=[]
    for path in sorted((ROOT/'dataset/external/bimnet').glob('*.ifc')):
        model=ifcopenshell.open(str(path))
        counts={c:len(model.by_type(c)) for c in ['IfcBuildingStorey','IfcSpace','IfcWall','IfcDoor','IfcWindow','IfcOpeningElement','IfcStair']}
        records.append({'name':path.name,'bytes':path.stat().st_size,'schema':model.schema,
                        'variant_name':bool(re.search(r'_\d+$',path.stem)),'counts':counts})
    old=ROOT/'dataset/processed/experiments/ifc2text-phase1-20260917/hxp-goal-v03-01/writing/design-description.md'
    text=old.read_text(encoding='utf-8')
    print(json.dumps({'pool':records,'old_description':{'characters':len(text),'han_characters':len(re.findall(r'[\u4e00-\u9fff]',text)),
         'bbox_mentions':text.count('包围盒'),'unconfirmed_mentions':text.count('未确认'),'material_section_characters':sum(len(x.split('\n## ')[0]) for x in text.split('### 材料')[1:])}},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
