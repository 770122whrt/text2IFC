"""Author private repair candidates from measured, licensed source selections.

This module creates review drafts, never damage, approval, or Provider input
directories. Only ``task_proposal.public_request`` is intended to be public.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

from .contracts import damage_profile

ROOT = Path(__file__).resolve().parents[3]

# Proposal index, number of targets. Source selections are private and immutable
# during this authoring operation. Mixed tasks keep explicit per-target refs.
DEFAULT_PLANS = {
    'formal-014': [(1, 1)], 'formal-015': [(1, 2)],
    'formal-017': [(0, 2), (1, 1)], 'formal-018': [(1, 2)],
    'formal-019': [(1, 1)], 'formal-020': [(0, 2), (1, 1)],
    'formal-012': [(0, 3)],
    'formal-010': [(1, 3)],
}
CLOSED_DOOR_SLOTS = {'formal-015', 'formal-018'}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _placement_m(entity, scale):
    if not entity.ObjectPlacement:
        raise ValueError('PLACEMENT_REQUIRED')
    transform = ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement).copy()
    transform[:3, 3] *= scale
    return transform


def _mesh(entity):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    shape = ifcopenshell.geom.create_shape(settings, entity)
    points = np.asarray(shape.geometry.verts).reshape(-1, 3)
    faces = np.asarray(shape.geometry.faces).reshape(-1, 3)
    if not len(points) or not len(faces) or not np.isfinite(points).all():
        raise ValueError('MESH_REQUIRED')
    return points, faces


def _bounds(points):
    return [[float(points[:, a].min()), float(points[:, a].max())] for a in range(3)]


def _local(points, transform):
    return (np.linalg.inv(transform) @ np.column_stack([points, np.ones(len(points))]).T).T[:, :3]


def _mesh_digest(points, faces):
    # Translation and triangle/vertex ordering do not define a different shape.
    # Do not normalize scale or reflect axes: those could hide wrong geometry.
    quantized = np.rint((points - points.min(axis=0)) * 100000).astype(np.int64)
    triangles = sorted(tuple(sorted(tuple(int(v) for v in quantized[i]) for i in face)) for face in faces)
    return hashlib.sha256(json.dumps(triangles, separators=(',', ':')).encode()).hexdigest()


def measure_product(model, step_id):
    """Read nominal values, actual meshes and actual placement in SI units."""
    entity = model.by_id(step_id)
    if entity.is_a() not in {'IfcDoor', 'IfcWindow'} or len(entity.FillsVoids) != 1:
        raise ValueError('TARGET_MUST_HAVE_UNIQUE_OPENING')
    opening = entity.FillsVoids[0].RelatingOpeningElement
    if len(opening.VoidsElements) != 1 or len(opening.HasFillings) != 1:
        raise ValueError('OPENING_MUST_HAVE_UNIQUE_WALL_AND_FILL')
    wall = opening.VoidsElements[0].RelatingBuildingElement
    if not wall.is_a('IfcWall'):
        raise ValueError('WALL_HOST_REQUIRED')
    storey = ifcopenshell.util.element.get_container(entity, ifc_class='IfcBuildingStorey')
    if storey is None:
        raise ValueError('STOREY_REQUIRED')
    scale = ifcopenshell.util.unit.calculate_unit_scale(model)
    width = float(entity.OverallWidth or 0) * scale * 1000
    height = float(entity.OverallHeight or 0) * scale * 1000
    if width <= 0 or height <= 0:
        raise ValueError('POSITIVE_NOMINAL_DIMENSIONS_REQUIRED')
    transform = _placement_m(entity, scale)
    if not np.allclose(np.abs(transform[:3, 2]), [0, 0, 1], atol=1e-7):
        raise ValueError('UPRIGHT_TARGET_REQUIRED')
    points, faces = _mesh(entity)
    local = _local(points, transform)
    opening_points, _ = _mesh(opening)
    opening_local = _local(opening_points, transform)
    wall_points, _ = _mesh(wall)
    opening_bounds = _bounds(opening_points)
    opening_span = np.ptp(opening_local, axis=0) * 1000
    if abs(width - height) > 1 and np.allclose([width, height], opening_span[[2, 0]], atol=1, rtol=0):
        raise ValueError('NOMINAL_OPENING_DIMENSIONS_SWAPPED')
    floor = float(_placement_m(storey, scale)[2, 3])
    nominal_floor = float(storey.Elevation) * scale if storey.Elevation is not None else None
    type_entity = ifcopenshell.util.element.get_type(entity)
    operation = getattr(type_entity, 'OperationType', None) if type_entity else None
    return {
        'source_step_id': step_id, 'target_guid': entity.GlobalId,
        'ifc_class': entity.is_a(), 'kind': 'door' if entity.is_a('IfcDoor') else 'window',
        'host_guid': wall.GlobalId, 'opening_guid': opening.GlobalId,
        'storey_guid': storey.GlobalId, 'storey_world_elevation_m': floor,
        'storey_attribute_elevation_m': nominal_floor,
        'width_mm': width, 'height_mm': height,
        'opening_width_mm': float(opening_span[0]), 'opening_height_mm': float(opening_span[2]),
        'opening_center_xy_m': [sum(b) / 2 for b in opening_bounds[:2]],
        'opening_bottom_world_m': opening_bounds[2][0],
        'sill_mm': (opening_bounds[2][0] - floor) * 1000,
        'bounds_world_m': _bounds(points), 'opening_bounds_world_m': opening_bounds,
        'host_bounds_world_m': _bounds(wall_points),
        'host_placement_world_m': _placement_m(wall, scale).tolist(),
        'mesh_center_world_m': [sum(b) / 2 for b in _bounds(points)],
        'opening_center_world_m': [sum(b) / 2 for b in opening_bounds],
        'mesh_local_extents_mm': (np.ptp(local, axis=0) * 1000).tolist(),
        'mesh_sha256': _mesh_digest(local, faces), 'mesh_triangles': len(faces),
        'operation_type': operation, 'type_guid': type_entity.GlobalId if type_entity else None,
        'unit_to_mm': scale * 1000,
        'placement_world_m': transform.tolist(),
    }


def reference_derived_offset(target, reference):
    """Infer product-to-opening offset using only public ref and host rotations.

    G's measured target offset is solely an independent admission check. It does
    not provide any component of the inferred value returned for scoring.
    """
    target_rotation = np.array(target['host_placement_world_m'])[:3, :3]
    ref_rotation = np.array(reference['host_placement_world_m'])[:3, :3]
    ref_offset = np.array(reference['mesh_center_world_m']) - reference['opening_center_world_m']
    inferred = target_rotation @ ref_rotation.T @ ref_offset
    actual = np.array(target['mesh_center_world_m']) - target['opening_center_world_m']
    delta = float(np.linalg.norm(inferred - actual))
    return {'basis': 'retained_public_reference_geometry', 'offset_m': inferred.tolist(),
        'reference_offset_world_m': ref_offset.tolist(),
        'actual_target_offset_world_m': actual.tolist(),
        'target_validation_delta_m': delta,
        'matches_target_within_1mm': delta <= .001}


def _number(value):
    # Public millimetre precision, with exact unrounded evidence kept privately.
    value = round(float(value), 1)
    return f'{value:g}'


def _xy(values):
    return f'X={values[0]:.3f}、Y={values[1]:.3f}'


def _request_item(spec, reference, index):
    name = '门' if spec['kind'] == 'door' else '窗'
    prefix = f'{index}．在标高 {spec["storey_world_elevation_m"]:.3f} 米的楼层，'
    where = f'平面中心位于（{_xy(spec["opening_center_xy_m"])} 米）的墙面位置，'
    if spec['preserve_opening']:
        where = f'为平面中心位于（{_xy(spec["opening_center_xy_m"])} 米）的现有空门洞'
    dimensions = f'补一扇{name}，名义宽 {_number(spec["width_mm"])} 毫米、高 {_number(spec["height_mm"])} 毫米；'
    dimensions += f'墙洞宽 {_number(spec["opening_width_mm"])} 毫米、高 {_number(spec["opening_height_mm"])} 毫米，'
    vertical = f'洞口下沿距该层标高 {_number(spec["sill_mm"])} 毫米（世界标高 {spec["opening_bottom_world_m"]:.3f} 米）。'
    ref = f'外观参照标高 {reference["storey_world_elevation_m"]:.3f} 米楼层、平面中心（{_xy(reference["opening_center_xy_m"])} 米）处保留的{name}：'
    ref += '保持相同的框、扇和玻璃分格。' if name == '窗' else '保持相同的框、门扇形状及开启形式；在目标墙面按该参照门相对于所在墙面的方式设置开向。'
    return prefix + where + dimensions + vertical + ref, vertical


def _clarification_draft(slot, request, specs, vertical_facts):
    if slot not in {'formal-013', 'formal-019', 'formal-020'}:
        return None
    if slot == 'formal-019':
        # A surviving opening constrains dimensions, but not desired handing.
        clause = '在目标墙面按该参照门相对于所在墙面的方式设置开向。'
        return {'enabled': False, 'necessary_fact_candidate': 'door_handing_relative_to_public_reference',
            'omittable_text': clause,
            'answer_card': '请按请求中那扇参照门相对于其墙面的开向设置目标门。',
            'needs_review': '删去此句仍可能被“开启形式”暗示；启用前须同时把外观参照限制为门框与门扇样式，独立验证两种开向均可行。',
            'public_request_with_full_facts': request,
            'automatic_clarification_admission': False}
    first = specs[0]
    return {'enabled': False, 'necessary_fact_candidate': 'target-1.opening_bottom_world_m',
        'omittable_text': vertical_facts[0],
        'answer_card': f'第 1 处窗洞下沿距该层标高 {_number(first["sill_mm"])} 毫米，世界标高 {first["opening_bottom_world_m"]:.3f} 米。',
        'needs_review': '启用前确认删除整句后，公共参照仅约束外观，不含恢复原高度或窗底与参照齐平的暗示；另验证至少一个不同高度仍可容纳同尺寸洞口。',
        'public_request_with_full_facts': request,
        'automatic_clarification_admission': False}


def author_candidate(selection, *, repository_root, plan=None):
    """Return a measured private draft compatible with formal_batch preparation."""
    root = Path(repository_root).resolve()
    source = (root / selection['assessment_path']).resolve()
    if not source.is_relative_to(root):
        raise ValueError('SOURCE_OUTSIDE_REPOSITORY')
    if _sha(source) != selection['assessment_sha256']:
        raise ValueError('SOURCE_CHANGED')
    rights = selection['rights']
    if rights.get('public_release_policy') not in {'open_modification_with_notice', 'open_modification_with_copyleft'}:
        raise ValueError('RIGHTS_NOT_CLEAR')
    if not selection.get('native_pass_registered'):
        raise ValueError('REGISTERED_NATIVE_PASS_REQUIRED')
    model = ifcopenshell.open(str(source))
    if model.schema != 'IFC2X3':
        raise ValueError('UNSUPPORTED_SCHEMA')
    slot = selection['proposed_slot']
    plan = plan if plan is not None else DEFAULT_PLANS.get(slot, [(0, selection['recommended_target_count'])])
    bindings = []
    for proposal_index, count in plan:
        proposal = selection['proposals'][proposal_index]
        if count < 1 or len(proposal['targets']) < count:
            raise ValueError('TARGET_COUNT_UNAVAILABLE')
        bindings.extend((target['step_id'], proposal['reference']['step_id']) for target in proposal['targets'][:count])
    targets = [binding[0] for binding in bindings]
    if not 1 <= len(targets) <= 3 or len(set(targets)) != len(targets):
        raise ValueError('ONE_TO_THREE_DISTINCT_TARGETS_REQUIRED')
    if any(reference in targets for _, reference in bindings):
        raise ValueError('REFERENCE_IS_TARGET')
    measurements = {step: measure_product(model, step) for step in set(sum(([t, r] for t, r in bindings), []))}
    specs, paragraphs, vertical_facts = [], [], []
    for index, (target, reference) in enumerate(bindings, 1):
        measured, ref = measurements[target], measurements[reference]
        if measured['ifc_class'] != ref['ifc_class'] or not np.allclose([measured['width_mm'], measured['height_mm']], [ref['width_mm'], ref['height_mm']], atol=1):
            raise ValueError(f'REFERENCE_DIMENSION_MISMATCH:{target}:{reference}')
        if measured['mesh_sha256'] != ref['mesh_sha256']:
            raise ValueError(f'REFERENCE_MESH_MISMATCH:{target}:{reference}')
        spec = dict(measured)
        offset = reference_derived_offset(measured, ref)
        spec.update({'id': f'target-{index}', 'basis': 'public_author_intent',
            'basis_detail': 'Task-author requested facts are authored before damage. Source measurements independently verify feasibility; they are not silently added during scoring.',
            'reference_guid': ref['target_guid'], 'reference_step_id': reference,
            'reference_center_xy_m': ref['opening_center_xy_m'],
            'reference_storey_world_elevation_m': ref['storey_world_elevation_m'],
            'preserve_opening': measured['kind'] == 'door' and slot not in CLOSED_DOOR_SLOTS,
            'match_center_world_m': measured['opening_center_xy_m'] + [measured['opening_bottom_world_m'] + measured['opening_height_mm'] / 2000],
            'coarse_match_m': 0.35,
            'geometry_checks': {'reference_mesh_equal': True, 'mesh_tolerance_mm': .01,
                'nominal_mesh_width_delta_mm': measured['mesh_local_extents_mm'][0] - measured['width_mm'],
                'nominal_mesh_height_delta_mm': measured['mesh_local_extents_mm'][2] - measured['height_mm'],
                'storey_elevation_attribute_agrees': measured['storey_attribute_elevation_m'] is not None and abs(measured['storey_attribute_elevation_m'] - measured['storey_world_elevation_m']) <= .001}})
        spec['geometry_checks']['reference_derived_center_offset_matches_target'] = offset['matches_target_within_1mm']
        spec['center_offset_evidence'] = offset
        if offset['matches_target_within_1mm']:
            spec['target_center_offset_from_opening_m'] = offset['offset_m']
            spec['target_center_offset_basis'] = offset['basis']
        else:
            spec['author_warning'] = 'Public reference/host rotations do not predict target centre within 1mm; do not infer this value from G. Select another reference or revise public author intent before scoring.'
        paragraph, vertical = _request_item(spec, ref, index)
        specs.append(spec)
        paragraphs.append(paragraph)
        vertical_facts.append(vertical)
    # Avoid an overlapping coarse-matching region for close targets.
    for spec in specs:
        distances = [float(np.linalg.norm(np.array(spec['match_center_world_m']) - other['match_center_world_m'])) for other in specs if other is not spec]
        if distances:
            spec['coarse_match_m'] = min(.35, min(distances) * .4)
            if spec['coarse_match_m'] < .002:
                raise ValueError('TARGET_POSITIONS_NOT_DISTINCT')
    request = '请完成以下门窗补全。下面的位置均按模型世界坐标描述，X、Y 和楼层标高的单位是米，尺寸的单位是毫米。\n\n' + '\n\n'.join(paragraphs) + '\n\n请保留其余墙体、门窗和其他构件及其位置；只在上述位置补全，使门窗、墙洞和所在墙体的关系完整。'
    if re.search(r'(?<![A-Za-z0-9_$])[0-3][A-Za-z0-9_$]{21}(?![A-Za-z0-9_$])|IfcOpenShell|ChangeSet|run_python|Python|STEP|GlobalId', request, re.I):
        raise ValueError('PRIVATE_IDENTIFIER_OR_METHOD_IN_PUBLIC_REQUEST')
    if _sha(source) != selection['assessment_sha256']:
        raise ValueError('SOURCE_CHANGED_DURING_AUTHORING')
    counts = dict(Counter(spec['ifc_class'] for spec in specs))
    repaired = bool(rights.get('repair_evidence')) or rights.get('original_sha256', selection['assessment_sha256']) != selection['assessment_sha256']
    proposal = {'damage_scale': damage_profile(counts)['level'],
        'description': '按实际几何核对后的门窗补全草案；独立目标与公共参照逐一绑定。',
        'provisional_source_step_ids': targets,
        'retained_reference_step_ids': list(dict.fromkeys(reference for _, reference in bindings)),
        'frozen': False, 'public_request': request, 'clarification_required': False,
        'public_basis': ['预先编写的用户修复意图；公开给出目标位置、名义尺寸、墙洞尺寸、竖向位置以及仍可见的外观参照。'],
        'door_damage': 'remove_door_and_opening' if slot in CLOSED_DOOR_SLOTS else 'remove_door_keep_opening',
        # Opening width is measured in the product frame for authoring, while
        # the independent scorer cannot safely infer width from a world AABB.
        'author_expectations': {spec['id']: {key: value for key, value in spec.items() if key != 'opening_width_mm'} for spec in specs},
        'public_numeric_spec': {'coordinate_system': 'IFC world', 'position_unit': 'metres', 'length_unit': 'millimetres',
            'private_bindings': True, 'targets': specs},
        'clarification_proposal': _clarification_draft(slot, request, specs, vertical_facts),
        'damage_profile': damage_profile(counts)}
    return {'candidate_slot': slot, 'status': 'authored_draft_pending_technical_review',
        'human_review': 'not_performed', 'human_viewed': False,
        'asset_id': selection['asset_id'], 'source_path': selection['assessment_path'],
        'source_sha256': selection['assessment_sha256'], 'source_bytes': source.stat().st_size,
        'schema': model.schema, 'source_register': 'dataset/external/ifc-asset-register.jsonl',
        'scene_family': selection['source_family'],
        'family_basis': selection.get('building_identity_basis', 'Retain registered coarse family; file uniqueness does not prove independent real buildings.'),
        'building_identity': selection.get('building_identity'),
        'independent_building_verified': selection.get('independent_building_verified', False),
        'source_rvt_path': selection.get('source_rvt_path'),
        'source_role': 'preselected_reference_from_registered_repair_copy' if repaired else 'preselected_reference_from_registered_original',
        'historical_repair_evidence': rights.get('repair_evidence', []),
        'license': selection['license'], 'rights_record': rights.get('record'),
        'rights_policy': rights['public_release_policy'], 'rights_source_url': rights.get('model_url') or rights.get('source_url'),
        'rights_conditions': rights.get('conditions'), 'rights_evidence': rights,
        'schema_validation': {'evidence': selection.get('assessment_native_evidence'), 'registered_native_pass': True,
            'rerun_during_authoring': False, 'prior_summary': selection.get('prior_native_summary')},
        'current_read_only_checks': {'source_hash_matches': True, 'target_reference_meshes_match': True,
            'source_modified': False, 'actual_world_storey_placement_checked': True,
            'viewer_status': 'not_verified_in_usBIM', 'purpose': 'Source measurement and authored intent, not damaged-model validation or capability evidence'},
        'task_proposal': proposal}


def author_selection(selection_path, output, *, repository_root=ROOT, slots=None):
    selection_path, output = Path(selection_path).resolve(), Path(output).resolve()
    selection = json.loads(selection_path.read_text(encoding='utf-8'))
    sources = {(Path(repository_root) / row['assessment_path']).resolve() for row in selection['candidates']}
    if output == selection_path or output in sources or output.suffix.lower() != '.json' or 'public' in [part.lower() for part in output.parts]:
        raise ValueError('PRIVATE_JSON_OUTPUT_REQUIRED')
    candidates, errors, seen = [], [], set()
    for source in selection['candidates']:
        if slots and source['proposed_slot'] not in slots:
            continue
        try:
            if source['assessment_sha256'] in seen:
                raise ValueError('DUPLICATE_SOURCE_FILE')
            seen.add(source['assessment_sha256'])
            candidates.append(author_candidate(source, repository_root=repository_root))
        except (ValueError, RuntimeError, IndexError, KeyError) as error:
            errors.append({'candidate_slot': source['proposed_slot'], 'error': str(error)})
    result = {'purpose': 'Private authored draft inventory; never mount or send to tested systems.',
        'selection_sha256': _sha(selection_path), 'candidates': candidates, 'errors': errors,
        'claims': ['Different source IFC files are not a claim of 20 independent real buildings.',
            'Shared coarse families and synthetic layouts remain explicit.',
            'No human visual approval, usBIM validation, damaged-input validation, or model call is claimed.']}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--slot', action='append')
    args = parser.parse_args()
    result = author_selection(args.selection, args.output, slots=args.slot)
    print(json.dumps({'authored': len(result['candidates']), 'errors': result['errors']}, ensure_ascii=False))
    return bool(result['errors'])


if __name__ == '__main__':
    raise SystemExit(main())
