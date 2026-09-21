"""Offline compiler capability probe, not a text-generation or accepted IFC run.

Copies only wall solid geometry into independent minimal BIM JSON documents.
The source IFC and previous roundtrip artifacts remain immutable. No Provider,
Prompt changes, production patches or tolerance changes are involved.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit
from shapely.geometry import Polygon
from shapely.ops import unary_union
from text2ifc_compiler import compile_document, open_ifc


def save(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n',
                    encoding='utf-8', newline='\n')


def placement(origin, axis=(0, 0, 1), ref=(1, 0, 0), parent=None):
    value = {'origin': list(map(float, origin)), 'axis': list(map(float, axis)),
             'ref_direction': list(map(float, ref))}
    if parent is not None:
        value['relative_to'] = parent
    return value


def document(points, *, wall_placement, solid_position, direction, depth):
    template = json.loads((ROOT / 'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    value = copy.deepcopy(template)
    value['schema_version'] = 'bim-json/2.3'
    ids = {'project-1', 'site-1', 'building-1', 'storey-1', 'wall-1'}
    value['entities'] = [e for e in value['entities'] if e['id'] in ids]
    value['relationships'] = []
    for entity in value['entities']:
        attrs = entity['attributes']
        if entity['id'] != 'wall-1' and 'ObjectPlacement' in attrs:
            attrs['ObjectPlacement'] = placement((0, 0, 0), parent=attrs['ObjectPlacement']['relative_to'])
        if entity['id'] == 'storey-1':
            attrs['Elevation'] = 0.0
        if entity['id'] == 'wall-1':
            attrs['ObjectPlacement'] = {**wall_placement, 'relative_to': 'storey-1'}
            attrs['Representation'] = {'kind': 'extruded_profile',
                'profile': {'kind': 'polygon', 'points': points},
                'position': solid_position, 'direction': direction, 'depth': depth}
    return value


def measured_geometry(entity):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, True)
    shape = ifcopenshell.geom.create_shape(settings, entity)
    coords, faces = list(shape.geometry.verts), list(shape.geometry.faces)
    vertices = [[float(v) * 1000 for v in coords[i:i + 3]] for i in range(0, len(coords), 3)]
    triangles = [Polygon([vertices[faces[i + j]][:2] for j in range(3)])
                 for i in range(0, len(faces), 3)]
    footprint = unary_union([p for p in triangles if p.is_valid and p.area > 1e-8])
    bounds = {k: [min(v[i] for v in vertices), max(v[i] for v in vertices)] for i, k in enumerate('xyz')}
    return bounds, footprint


def probe_source_wall(source_entity, scale, target):
    bodies = [item for rep in source_entity.Representation.Representations
              if rep.RepresentationIdentifier == 'Body' for item in rep.Items]
    assert len(bodies) == 1 and bodies[0].is_a('IfcExtrudedAreaSolid'), 'PROBE_REQUIRES_SINGLE_EXTRUSION'
    solid = bodies[0]
    assert solid.SweptArea.is_a('IfcArbitraryClosedProfileDef')
    assert solid.SweptArea.OuterCurve.is_a('IfcPolyline')
    points = [[float(v) * scale for v in p.Coordinates] for p in solid.SweptArea.OuterCurve.Points]
    matrix = ifcopenshell.util.placement.get_local_placement(source_entity.ObjectPlacement)
    wall_pos = placement(matrix[:3, 3] * scale, matrix[:3, 2], matrix[:3, 0])
    matrix_solid = ifcopenshell.util.placement.get_axis2placement(solid.Position)
    solid_pos = placement(matrix_solid[:3, 3] * scale, matrix_solid[:3, 2], matrix_solid[:3, 0])
    value = document(points, wall_placement=wall_pos, solid_position=solid_pos,
                     direction=list(solid.ExtrudedDirection.DirectionRatios), depth=float(solid.Depth) * scale)
    save(target / 'input-diagnostic.json', value)
    result = compile_document(value, target / 'compiled-diagnostic.ifc')
    if not result.success:
        return {'compile_success': False, 'detail': str(result)}
    model = open_ifc(target / 'compiled-diagnostic.ifc')
    wall = model.by_type('IfcWall')[0]
    src_bounds, src_outline = measured_geometry(source_entity)
    dst_bounds, dst_outline = measured_geometry(wall)
    maximum = max(abs(a - b) for key in src_bounds for a, b in zip(src_bounds[key], dst_bounds[key]))
    hausdorff = src_outline.hausdorff_distance(dst_outline)
    return {'compile_success': True, 'ifc_schema': model.schema,
            'source_profile': solid.SweptArea.is_a(),
            'reconstructed_profile': wall.Representation.Representations[0].Items[0].SweptArea.is_a(),
            'profile_vertex_count': len(points), 'opening_subtraction': False,
            'max_bbox_coordinate_delta_mm': maximum, 'footprint_hausdorff_mm': hausdorff,
            'footprint_symmetric_difference_mm2': src_outline.symmetric_difference(dst_outline).area,
            'within_probe_precision': maximum < 0.01 and hausdorff < 0.01}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='dataset/processed/experiments/ifc2text-wall-backend-20260921-v01')
    args = parser.parse_args()
    target = ROOT / args.out
    target.mkdir(parents=True, exist_ok=False)
    source = ROOT / 'dataset/external/bimnet/hxp.ifc'
    trace_path = ROOT / 'dataset/processed/experiments/ifc2text-attribution-20260921-v01/attribution.json'
    before = source.read_bytes()
    trace = json.loads(trace_path.read_text(encoding='utf-8'))
    model = ifcopenshell.open(str(source))
    scale = ifcopenshell.util.unit.calculate_unit_scale(model) * 1000
    cases = {}
    for label in ('W011', 'W013', 'W015'):
        entity = model.by_guid(trace['traces'][label]['source_observation']['source_global_id'])
        cases[label] = probe_source_wall(entity, scale, target / label)
    assert source.read_bytes() == before, 'SOURCE_MUTATED'
    report = {'evidence_kind': 'offline_source_geometry_to_existing_compiler_probe',
              'production_changes': False, 'provider_calls': 0, 'text_pipeline_tested': False,
              'source_unchanged': True, 'cases': cases,
              'all_cases_passed': all(c.get('within_probe_precision') for c in cases.values()),
              'limitations': ['Known source profiles supplied directly; not LLM-generated JSON.',
                  'Wall solids only, with opening subtractions disabled on both sides.',
                  'No proof of whole-building acceptance, text completeness, or arbitrary curved/variable-height walls.',
                  '0.01 mm is a diagnostic numeric check; original roundtrip tolerances remain unchanged.']}
    save(target / 'report.json', report)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report['all_cases_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
