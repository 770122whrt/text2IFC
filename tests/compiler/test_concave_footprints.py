"""Concave slab support: native mesh volume cannot be inferred from its bbox."""
import json
from pathlib import Path

import ifcopenshell.geom
import ifcopenshell.util.element
import numpy as np
import pytest

from text2ifc_compiler import compile_document, open_ifc

ROOT=Path(__file__).resolve().parents[2]

@pytest.mark.parametrize('points,area',[
    ([(0,0),(8,0),(8,2),(3,2),(3,6),(8,6),(8,8),(0,8)],44),
    ([(0,0),(8,0),(8,8),(6,8),(6,3),(2,3),(2,8),(0,8)],44),
    ([(0,0),(8,0),(8,3),(3,3),(3,8),(0,8)],39),
])
@pytest.mark.parametrize('scale,mirror',[(1,1),(0.5,-1),(1.7,1)])
def test_concave_footprint_survives_compile_reopen_and_native_mesh(tmp_path,points,area,scale,mirror):
    document=json.loads((ROOT/'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    slab=next(e for e in document['entities'] if e['id']=='slab-1')
    polygon=[[x*1000*scale*mirror,y*1000*scale] for x,y in points]
    slab['attributes']['Representation']['profile']['points']=[*polygon,polygon[0]]
    output=tmp_path/'concave.ifc'
    result=compile_document(document,output)
    assert result.success,result
    model=open_ifc(output)
    target=next(e for e in model.by_type('IfcSlab') if ifcopenshell.util.element.get_psets(e).get('Pset_text2IFCIdentity',{}).get('BimJsonId')=='slab-1')
    settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
    shape=ifcopenshell.geom.create_shape(settings,target)
    vertices=np.array(shape.geometry.verts).reshape(-1,3)
    triangles=vertices[np.array(shape.geometry.faces).reshape(-1,3)]
    volume=abs(np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6)
    assert volume==pytest.approx(area*scale**2*.2,abs=1e-8)
    bbox_volume=np.prod(vertices.max(axis=0)-vertices.min(axis=0))
    assert volume<bbox_volume*.8  # C/U/L must not become a solid rectangle.
