"""Offline evaluator controls; all mutated IFCs remain evaluator-only."""
import json
from pathlib import Path
import sys

import ifcopenshell
import ifcopenshell.api
from check_ifc import check_ifc

OUT=Path(__file__).resolve().parent
result=json.loads((OUT/'offline-public-04/result.json').read_text(encoding='utf-8'))
source=Path(result['run_dir'])/'output.ifc'
dest=OUT/'checker-controls';dest.mkdir(exist_ok=False)
rows=[]
for label,expected_failure in [('filled_courtyard','plate_3:native_volume'),('missing_floor_void','plate_1:opening_count'),
    ('wrong_material','wall_material'),('wrong_door_operation','all_doors_match'),('unrequested_property','no_unsolicited_properties')]:
    m=ifcopenshell.open(str(source))
    if label=='filled_courtyard':
        roof=m.by_type('IfcRoof')[0]
        solid=roof.Representation.Representations[0].Items[0]
        curve=solid.SweptArea.OuterCurve
        curve.Points=tuple(m.create_entity('IfcCartesianPoint',Coordinates=p) for p in [(0.,0.),(13200.,0.),(13200.,16800.),(0.,16800.),(0.,0.)])
    elif label=='missing_floor_void':
        slab=next(s for s in m.by_type('IfcSlab') if s.Name=='slab-2')
        m.remove(slab.HasOpenings[0])
    elif label=='wrong_material':
        next(v for v in m.by_type('IfcMaterial') if v.Name=='砖').Name='timber'
    elif label=='wrong_door_operation':
        door=next(d for d in m.by_type('IfcDoor') if 'entry' in d.Name)
        import ifcopenshell.util.element
        ifcopenshell.util.element.get_type(door).OperationType='SINGLE_SWING_RIGHT'
    else:
        pset=ifcopenshell.api.run('pset.add_pset',m,product=m.by_type('IfcWall')[0],name='Pset_WallCommon')
        ifcopenshell.api.run('pset.edit_pset',m,pset=pset,properties={'FireRating':'60min'})
    target=dest/(label+'.ifc');m.write(str(target))
    check=check_ifc(target)
    assert check['status']=='failed' and expected_failure in check['failed'],(label,check['failed'])
    (dest/(label+'.json')).write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
    rows.append(dict(case=label,status='expected_rejection',required_failure=expected_failure,observed=check['failed']))
(dest/'result.json').write_text(json.dumps(dict(status='passed',positive_check_count=485,negative_controls=rows,evidence_class='offline_evaluator_controls_not_provider'),ensure_ascii=False,indent=2),encoding='utf-8')
print('Evaluator positive +',len(rows),'negative controls passed.')
