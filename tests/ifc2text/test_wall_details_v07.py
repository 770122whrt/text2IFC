"""Frozen wall-description family: geometry, rounding, omissions and immutable sources."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import ifcopenshell
import numpy as np
import pytest
from shapely.geometry import Polygon
from text2ifc_compiler import compile_document
from text2ifc_ifc2text.wall_details_v07 import read_wall_solid, enrich_wall_details, detailed_description
from text2ifc_ifc2text.observation import extract_description_facts

FIXTURE = Path('tests/contract_v2/fixtures/complete.json')


def make_wall(tmp_path, points=None, angle=False):
    doc = json.loads(FIXTURE.read_text(encoding='utf-8'))
    doc['schema_version'] = 'bim-json/2.3'
    doc['entities'] = [e for e in doc['entities'] if e['id'] in {'project-1','site-1','building-1','storey-1','wall-1'}]
    doc['relationships'] = []
    wall = next(e for e in doc['entities'] if e['id']=='wall-1')
    if points is not None:
        wall['attributes']['Representation']['profile'] = {'kind':'polygon','points':points}
    if angle:
        wall['attributes']['ObjectPlacement']['ref_direction']=[1.,1.,0.]
    path=tmp_path/'source.ifc'
    assert compile_document(doc,path).success
    return path


@pytest.mark.parametrize('points', [
    [[0,-100],[4000,-100],[4000,100],[200,100],[0,-100]],
    [[0,0],[4000,0],[4000,200],[2100,200],[2100,100],[1900,100],[1900,200],[0,200],[0,0]],
])
def test_nonrectangular_outline_is_preserved_in_description(tmp_path,points):
    path=make_wall(tmp_path,points,angle=True); original=path.read_bytes()
    facts=enrich_wall_details(path,extract_description_facts(path))
    wall=facts['storeys'][0]['walls'][0]
    detail=wall['solid_detail']
    assert detail['status']=='supported_vertical_extrusion'
    assert detail['requires_explicit_outline']
    assert detail['height_mm']==pytest.approx(3000.)
    assert Polygon(detail['bottom_outline_xy_mm']).area==pytest.approx(Polygon(points).area,abs=.01)
    text=detailed_description(facts)
    assert '底面外轮廓' in text and '扣除洞口之前' in text
    assert text.count('**墙 W001 的实体轮廓**')==1
    assert wall['source_global_id'] not in text
    assert path.read_bytes()==original


def test_rectangle_keeps_compact_text(tmp_path):
    path=make_wall(tmp_path)
    facts=enrich_wall_details(path,extract_description_facts(path))
    detail=facts['storeys'][0]['walls'][0]['solid_detail']
    assert not detail['requires_explicit_outline']
    assert '底面外轮廓' not in detailed_description(facts)


def test_unsupported_solid_is_not_replaced_by_a_bbox_profile(tmp_path):
    path=make_wall(tmp_path)
    model=ifcopenshell.open(str(path)); wall=model.by_type('IfcWall')[0]
    solid=wall.Representation.Representations[0].Items[0]
    solid.ExtrudedDirection.DirectionRatios=(1.,0.,1.)
    result=read_wall_solid(wall,1.)
    assert result['status']=='unsupported'
    assert 'outline' not in result
    assert result['reason']=='NON_VERTICAL_EXTRUSION'


def test_description_extension_does_not_mutate_facts(tmp_path):
    path=make_wall(tmp_path,[[0,0],[4000,0],[4000,200],[100,200],[0,0]])
    facts=extract_description_facts(path); frozen=copy.deepcopy(facts)
    enriched=enrich_wall_details(path,facts)
    assert facts==frozen and enriched is not facts
    detail=enriched['storeys'][0]['walls'][0]['solid_detail']
    from text2ifc_ifc2text.compact import mm1
    assert max(abs(x-float(mm1(x))) for p in detail['bottom_outline_xy_mm'] for x in p)<=.0500001
