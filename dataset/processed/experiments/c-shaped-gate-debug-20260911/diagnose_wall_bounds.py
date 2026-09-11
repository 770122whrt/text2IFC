"""Development diagnosis: rectangular wall footprints, not a general code audit."""
import hashlib
import itertools
import json
from pathlib import Path
import ifcopenshell
import ifcopenshell.geom
import numpy as np

OUT=Path(__file__).resolve().parent
SOURCE=OUT.parent/'c-shaped-clarified-entry-20260911/live-run/runs/9b00e53444a948e7'
def main():
    p=SOURCE/'output.ifc';before=hashlib.sha256(p.read_bytes()).hexdigest()
    model=ifcopenshell.open(str(p));settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
    native=[]
    for wall in model.by_type('IfcWall'):
        shape=ifcopenshell.geom.create_shape(settings,wall)
        v=np.array(shape.geometry.verts).reshape(-1,3);f=np.array(shape.geometry.faces).reshape(-1,3)
        if abs(v[:,2].min())>1e-6:continue
        t=v[f];volume=abs(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)
        native.append({'name':wall.Name,'bbox_m':np.array([v.min(axis=0),v.max(axis=0)]).T.tolist(),'volume_m3':float(volume)})
    expectation=json.loads((OUT/'offline-recheck/semantic-geometry-expectation.json').read_text(encoding='utf-8'))
    walls={k:v for k,v in expectation['walls'].items() if v['bbox']['z'][0]==0}
    overlaps=[]
    for (a,x),(b,y) in itertools.combinations(walls.items(),2):
        lengths=[min(x['bbox'][axis][1],y['bbox'][axis][1])-max(x['bbox'][axis][0],y['bbox'][axis][0]) for axis in ['x','y']]
        if min(lengths)>1e-8:overlaps.append({'a':a,'b':b,'area_m2':lengths[0]*lengths[1]})
    # At the southwest corner both centreline wall segments start 100mm away
    # from the outer corner, leaving the exterior corner square uncovered.
    point=[.05,.05]
    covered=any(all(v['bbox'][axis][0]<=point[i]<=v['bbox'][axis][1] for i,axis in enumerate(['x','y'])) for v in walls.values())
    assert not covered and overlaps
    assert hashlib.sha256(p.read_bytes()).hexdigest()==before
    result={'evidence_class':'offline_diagnostic','provider_calls':0,'source_ifc_sha256':before,
        'source_unchanged':True,'native_ground_walls':native,
        'native_ground_wall_total_volume_m3':sum(w['volume_m3'] for w in native),
        'brief_derived_ground_wall_overlap_pairs':overlaps,
        'southwest_corner_test_point_m':point,'brief_derived_wall_covers_point':covered,
        'conclusion':'Fixing the 500mm candidate shift cannot fix the Brief-derived rectangular wall joins. The Brief expectation itself has positive overlapping wall footprints and an uncovered outer corner. Original input requests joined, nonoverlapping walls within the outline. No candidate or user fact was edited.',
        'limits':'Axis-aligned wall footprints at a fixed ground plane. These probes do not constitute full topology, structural, access or building-code verification.'}
    with (OUT/'wall-boundary-diagnosis.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'overlap_pairs':len(overlaps),'corner_covered':covered,'native_ground_wall_volume_m3':result['native_ground_wall_total_volume_m3']}))
if __name__=='__main__':main()
