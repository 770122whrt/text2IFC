import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element as element
import ifcopenshell.util.unit as unit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01/generation'
source = Path(sys.argv[1])
destination = Path(sys.argv[2])
expected = json.loads((OUT / 'frozen-expectations.json').read_text(encoding='utf-8'))
model = ifcopenshell.open(str(source))
scale = unit.calculate_unit_scale(model)
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)
def bbox(product):
    shape = ifcopenshell.geom.create_shape(settings, product)
    vertices = list(shape.geometry.verts)
    return [[min(vertices[k::3]), max(vertices[k::3])] for k in range(3)]
def near(actual, value):
    if isinstance(value, (list, tuple)):
        return len(actual) == len(value) and all(near(a, b) for a, b in zip(actual, value))
    return abs(actual - value) < 1e-6
def material_names(product):
    material = element.get_material(product)
    if material is None:
        return []
    if material.is_a('IfcMaterial'):
        return [material.Name]
    if material.is_a('IfcMaterialLayerSetUsage'):
        return [layer.Material.Name for layer in material.ForLayerSet.MaterialLayers]
    return [material.is_a()]
def styles(product):
    output = []
    for representation in product.Representation.Representations:
        if representation.RepresentationIdentifier != 'Body':
            continue
        for item in representation.Items:
            for styled in item.StyledByItem:
                for assignment in styled.Styles:
                    assigned = assignment.Styles if assignment.is_a('IfcPresentationStyleAssignment') else [assignment]
                    for style in assigned:
                        if style.is_a('IfcSurfaceStyle'):
                            for shading in style.Styles:
                                if shading.is_a('IfcSurfaceStyleShading'):
                                    output.append({'name': style.Name, 'rgb': [shading.SurfaceColour.Red, shading.SurfaceColour.Green, shading.SurfaceColour.Blue],
                                                   'transparency': getattr(shading, 'Transparency', 0.0) or 0.0})
    return output
checks = {'schema': model.schema == expected['schema'], 'units_mm': near(scale, .001)}
counts = {kind: len(model.by_type(kind)) for kind in expected['counts']}
checks['requested_counts'] = counts == expected['counts']
checks['no_roof_or_ceiling'] = not model.by_type('IfcRoof') and not model.by_type('IfcCovering')
observations = []
walls = model.by_type('IfcWall')
boxes = [bbox(wall) for wall in walls]
target_boxes = [[[-3.2, 3.2], [-2.2, -2.0], [0, 3]], [[-3.2, 3.2], [2.0, 2.2], [0, 3]],
                [[-3.2, -3.0], [-2.2, 2.2], [0, 3]], [[3.0, 3.2], [-2.2, 2.2], [0, 3]]]
checks['wall_outer_bounds_thickness_height'] = all(any(near(box, target) for box in boxes) for target in target_boxes)
checks['room_clear_bounds'] = near(bbox(model.by_type('IfcSpace')[0]), [[-3, 3], [-2, 2], [0, 3]])
checks['floor_bounds_and_top'] = near(bbox(model.by_type('IfcSlab')[0]), [[-3.2, 3.2], [-2.2, 2.2], [-.15, 0]])
checks['wall_materials'] = all(material_names(wall) == ['砖'] for wall in walls)
checks['floor_material'] = material_names(model.by_type('IfcSlab')[0]) == ['混凝土']
allowed_metadata = {'Pset_text2IFCIdentity', 'Pset_text2IFCBasicFilling', 'Pset_text2IFCAppearance'}
checks['no_unrequested_properties'] = all(pset.Name in allowed_metadata for pset in model.by_type('IfcPropertySet'))
checks['no_unrequested_materials'] = all(not material_names(p) for p in model.by_type('IfcElement')
                                      if not p.is_a('IfcWall') and not p.is_a('IfcSlab'))
for filling in [*model.by_type('IfcDoor'), *model.by_type('IfcWindow')]:
    box = bbox(filling)
    psets = element.get_psets(filling)
    template = psets['Pset_text2IFCBasicFilling']['TemplateId']
    is_door = filling.is_a('IfcDoor')
    side = 'south' if is_door else 'east' if sum(box[0]) > 0 else 'west'
    expected_template = 'door-left' if is_door else 'window-double-vertical' if side == 'east' else 'window-single'
    nominal = [1000, 2100] if is_door else [1600, 1200]
    actual_styles = styles(filling)
    glass = [s for s in actual_styles if s['name'] == 'warm-residential:glazing']
    checks[f'{side}_template'] = template == expected_template
    checks[f'{side}_nominal_dimensions'] = near([filling.OverallWidth, filling.OverallHeight], nominal)
    checks[f'{side}_mesh_width_height_sill'] = near([box[0 if is_door else 1][1] - box[0 if is_door else 1][0],
                                                box[2][1] - box[2][0], box[2][0]], [1.0, 2.1, 0] if is_door else [1.6, 1.2, .9])
    checks[f'{side}_centered'] = near(sum(box[0 if is_door else 1]), 0) and near(
        sum(box[1 if is_door else 0]) / 2, -2.1 if is_door else 3.1 if side == 'east' else -3.1)
    checks[f'{side}_depth_within_wall'] = box[1 if is_door else 0][1] - box[1 if is_door else 0][0] <= .2 + 1e-6
    checks[f'{side}_component_colors'] = len({tuple(s['rgb']) for s in actual_styles}) >= 2
    checks[f'{side}_transparent_panel_count'] = len(glass) == (0 if is_door else 2 if side == 'east' else 1) and all(0 < s['transparency'] < 1 for s in glass)
    checks[f'{side}_appearance_profile'] = psets['Pset_text2IFCAppearance']['Profile'] == 'warm-residential'
    checks[f'{side}_parameter_sources'] = bool(json.loads(psets['Pset_text2IFCBasicFilling']['ParameterSourcesJson']))
    opening = filling.FillsVoids[0].RelatingOpeningElement
    host = opening.VoidsElements[0].RelatingBuildingElement
    opening_box, host_box = bbox(opening), bbox(host)
    width_axis, depth_axis = (0, 1) if is_door else (1, 0)
    checks[f'{side}_opening_exact_size'] = near([opening_box[width_axis][1] - opening_box[width_axis][0],
                                                opening_box[2][1] - opening_box[2][0]], [v * .001 for v in nominal])
    checks[f'{side}_opening_through_host'] = opening_box[depth_axis][0] <= host_box[depth_axis][0] + 1e-6 and opening_box[depth_axis][1] >= host_box[depth_axis][1] - 1e-6
    if is_door:
        checks['door_left_operation'] = element.get_type(filling).OperationType == 'SINGLE_SWING_LEFT'
    observations.append({'guid': filling.GlobalId, 'side': side, 'template': template, 'bbox_m': box,
                         'styles_read_from_representation_items': actual_styles, 'opening_guid': opening.GlobalId, 'host_guid': host.GlobalId})
report = {'status': 'passed' if all(checks.values()) else 'failed', 'source': str(source),
          'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'frozen_request_sha256': hashlib.sha256((OUT / 'frozen-expectations.json').read_bytes()).hexdigest(),
          'checks': checks, 'counts': counts, 'fillings': observations,
          'basis': 'Independent reopened IFC compared to pre-Provider human request, actual mesh bounds, typed material relationships and StyledItem colors; Agent represented labels not used.',
          'limitations': 'One development viability case; no capability improvement claim. Small internal provenance property sets and minimal legal door style are intentional deterministic attachments.'}
destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'failed': [k for k, v in checks.items() if not v], 'checks': len(checks)}))
