"""Compile explicit public placement clauses and independently check their effects.

This bounded grammar covers an explicitly located rectangular Beam/Column and
an exactly referenced Window or Door with a copied opening. Free-form requests retain
the existing grounding path. Once an explicit placement anchor is recognized,
missing, ambiguous or unsupported facts fail closed instead of becoming guesses.
Only the original request and the current public IFC are inputs.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from itertools import product
import math
import re
from typing import Any, Mapping

import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

from .evaluation_models import CheckResult, EvidenceFact, EvaluationStatus
from .scene_context import SceneError


LEGACY_VERSION = "text2ifc/public-request-geometry/0.1"
REFERENCE_VERSION = "text2ifc/public-request-geometry/0.2"
VERSION = "text2ifc/public-request-geometry/0.3"
TOLERANCE_MM = 1.0
REFERENCE_YAW_DEGREES = (0, 180, -180)
_NUMBER = r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
_VECTOR = rf"[（(]\s*({_NUMBER})\s*[，,]\s*({_NUMBER})\s*[，,]\s*({_NUMBER})\s*[）)]"
_FAMILIES = {"add_column": "柱", "add_beam": "梁", "add_window_with_opening_to_wall": "窗",
             "fill_existing_opening_with_door": "门", "add_door_with_opening_to_wall": "门"}


class PublicGeometryError(ValueError):
    pass


def public_geometry_capability(operation_type: str) -> dict | None:
    """Describe the installed exact-reference path, not case admission or authority.

    The scene catalog adds this only to operations present in its registry.
    Literal request parsing and public IFC binding still independently decide
    whether an individual request is admissible.
    """
    if operation_type == 'add_beam':
        return {'compiler_version': VERSION, 'exact_reference_copy_supported': True,
                'product_geometry': 'copy_exact_public_reference_body',
                'required_representation': 'single_body_single_rectangular_extruded_area_solid',
                'binding_roles': {'target_id': 'public_storey', 'reference_id': 'public_reference_beam'},
                'required_authority': ['explicit_original_request_clause', 'offered_reference',
                                       'unique_reference_world_placement_origin'],
                'derived_by_program': ['axis_end_face_centres', 'horizontal_width_vertical_height',
                                       'placement_world_mm'],
                'limits': ['horizontal_straight_rectangular_beam', 'same_orientation',
                           'preserve_all_internal_body_offsets_and_transforms',
                           'no_missing_multiple_or_private_reference']}
    if operation_type not in {'add_window_with_opening_to_wall', 'fill_existing_opening_with_door',
                              'add_door_with_opening_to_wall'}:
        return None
    retained = operation_type == 'fill_existing_opening_with_door'
    door = operation_type != 'add_window_with_opening_to_wall'
    return {
        'compiler_version': VERSION, 'exact_reference_copy_supported': True,
        'product_geometry': 'copy_exact_public_reference_body',
        'required_representation': ('mapped_type_or_supported_direct_body_reuse' if door
                                    else 'mapped_type_representation_required'),
        'representation_check': ('The program verifies representation compatibility. An omitted summary '
                                 'field is not evidence of unsupported geometry; query public geometry '
                                 'detail when needed and retain deterministic validation.'),
        'opening_geometry': ('retain_existing_opening_unchanged' if retained
                             else 'copy_reference_opening_preserving_relative_pose'),
        'binding_roles': {'target_id': 'public_existing_opening' if retained else 'public_host_wall',
                          'reference_id': 'public_reference_occurrence'},
        'relative_rotation_degrees': {'height_axis': list(REFERENCE_YAW_DEGREES),
                                     'thickness_axis': [0], 'width_axis': [0]},
        'required_authority': ['explicit_original_request_clause', 'offered_target_and_reference',
                               'verified_public_geometry_and_compatible_host'],
        'request_clause_requirements': ['补建一扇门：' if door else '补建一扇窗：',
            '归属楼层', '放置基点', '完整形状复制参照',
            '朝向与参照相同 or 朝向相对参照，按自身高、厚、宽轴依次旋转',
            '保留现有洞口' if retained else '洞口复制参照构件所填洞口'],
        'limits': ['bounded_literal_request_grammar', 'upright_product_and_opening',
                   'reference_axes_parallel_to_straight_host', 'opening_within_host',
                   'no_missing_or_private_reference_authority'],
        'derived_by_program': ['product_installation', 'opening_installation',
                               'opening_dimensions_and_host_local_position'],
    }


def _error(detail: str) -> PublicGeometryError:
    return PublicGeometryError("PUBLIC_GEOMETRY_" + detail)


def _vector(pattern: str, text: str) -> np.ndarray:
    matches = list(re.finditer(pattern, text))
    if len(matches) != 1:
        raise _error("CLAUSE_INCOMPLETE_OR_AMBIGUOUS")
    values = np.array([float(v) for v in matches[0].groups()])
    if not np.isfinite(values).all():
        raise _error("NUMBER_INVALID")
    return values


def _frame(value: Any) -> np.ndarray:
    m = np.array(value, dtype=float)
    if (m.shape != (4, 4) or not np.isfinite(m).all()
            or not np.allclose(m[3], [0, 0, 0, 1], atol=1e-8)
            or not np.allclose(m[:3, :3].T @ m[:3, :3], np.eye(3), atol=1e-7)
            or not np.isclose(np.linalg.det(m[:3, :3]), 1, atol=1e-7)):
        raise _error("FRAME_UNAVAILABLE_OR_UNSUPPORTED")
    return m


def _bounds(value: Any) -> np.ndarray:
    try:
        b = np.array([value[a] for a in 'xyz'], dtype=float).T
    except (KeyError, TypeError, ValueError) as error:
        raise _error("BODY_UNAVAILABLE") from error
    if b.shape != (2, 3) or not np.isfinite(b).all() or np.any(b[1] <= b[0]):
        raise _error("BODY_UNAVAILABLE")
    return b


def _transformed_bounds(local: np.ndarray, frame: np.ndarray) -> dict:
    vv = np.array([frame @ [*xyz, 1] for xyz in product(*zip(local[0], local[1]))])[:, :3]
    return {a: [round(float(vv[:, i].min()), 6), round(float(vv[:, i].max()), 6)]
            for i, a in enumerate('xyz')}


def _public_world_bounds(scene: Any, identity: str, local: np.ndarray, frame: np.ndarray,
                         *, opening: bool = False, uncut: bool = False) -> dict:
    if not hasattr(scene, 'body_vertices_mm'):
        if uncut:
            raise _error('UNCUT_HOST_GEOMETRY_UNAVAILABLE')
        return _transformed_bounds(local, frame)
    points = np.asarray(scene.body_vertices_mm(identity, opening=opening,
        **({'uncut': True} if uncut else {})), dtype=float)
    transformed = points @ frame[:3, :3].T + frame[:3, 3]
    return {a: [round(float(transformed[:, i].min()), 6), round(float(transformed[:, i].max()), 6)]
            for i, a in enumerate('xyz')}


def _explicit_clauses(request: str) -> list[tuple[str, str]]:
    starts = list(re.finditer(r"(?m)^\s*(?:\d+[.．、]\s*)?补建(?:一[根扇]?)?([柱梁窗门])[:：]", request))
    clauses = []
    for i, start in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(request)
        text = re.split(r"\n\s*属性更改|\n\s*除以上", request[start.start():end], maxsplit=1)[0].strip()
        if '放置基点' in text:
            clauses.append((start[1], text))
    return clauses


def _clause(operation: Mapping[str, Any], request: str) -> str | None:
    family = _FAMILIES.get(operation['operation_type'])
    if not family:
        return None
    clauses = [text for kind, text in _explicit_clauses(request) if kind == family]
    if not clauses:
        return None
    if len(clauses) > 1:
        quotes = [s.get('excerpt', '') for s in operation.get('provenance', ())
                  if s.get('source_kind') == 'user_request' and s.get('reference') == 'request:/text']
        exact = [c for c in clauses if any(q and (q in c or c in q) for q in quotes)]
        if len(exact) != 1:
            raise _error("OPERATION_CLAUSE_AMBIGUOUS")
        clauses = exact
    return clauses[0]


def validate_geometry_coverage(body: dict, evidence: list[dict], request: str) -> None:
    unsupported = [u.get('source', {}).get('excerpt', '') for u in body.get('unsupported_requests', ())]
    requested = Counter(text for kind, text in _explicit_clauses(request)
                        if kind in _FAMILIES.values() and not any(text in q for q in unsupported))
    covered = Counter(e['public_geometry_requirement']['source_excerpt'] for e in evidence
                      if e.get('public_geometry_requirement'))
    if requested != covered:
        raise _error('CLAUSE_CARDINALITY_MISMATCH')


def public_geometry_required(operation_type: str, request: str) -> bool:
    family = _FAMILIES.get(operation_type)
    return family is not None and any(kind == family for kind, _ in _explicit_clauses(request))


def calibrate_request_geometry(operation: dict, binding: dict, scene: Any, request: str,
                               *, version: str = VERSION) -> dict | None:
    """Bind literal anchors before Intent freezes; never infer a missing number."""
    clause = _clause(operation, request)
    if clause is None:
        return None
    if version not in (LEGACY_VERSION, REFERENCE_VERSION, VERSION):
        raise _error('VERSION_UNSUPPORTED')
    target = scene.offered_record(binding['target_id'])
    host = scene.offered_record(target['host_id']) if target['ifc_class'] == 'IfcOpeningElement' else target
    floor = re.findall(r"归属楼层[「\"]([^」\"]+)[」\"]", clause)
    actual_floor = target.get('name') if target['ifc_class'] == 'IfcBuildingStorey' else host.get('storey_name')
    if len(floor) != 1 or floor[0] != actual_floor:
        raise _error("STOREY_BINDING_MISMATCH")
    try:
        target_detail = scene.geometry_detail(host['id'])
        target_frame = _frame(target_detail['placement_world_mm'])
        world = list(re.finditer(r"放置基点世界坐标为" + _VECTOR + r"\s*米", clause))
        if world:
            point = _vector(r"放置基点世界坐标为" + _VECTOR + r"\s*米", clause) * 1000
        else:
            relative = _vector(rf"放置基点距墙长度起端\s*({_NUMBER})\s*毫米，\s*距墙厚度负向侧\s*({_NUMBER})\s*毫米，\s*高出墙底\s*({_NUMBER})\s*毫米", clause)
            point = (target_frame @ [*(_bounds(target_detail['body_bounds_local_mm'])[0] + relative), 1])[:3]
        result = {'schema_version': version, 'operation_id': operation['operation_id'],
                  'operation_type': operation['operation_type'], 'target_id': target['id'],
                  'request_sha256': hashlib.sha256(request.encode('utf-8')).hexdigest(),
                  'source_excerpt': clause}
        if (operation['operation_type'] == 'add_beam' and '完整形状复制参照' in clause
                and version == VERSION):
            _reference_beam(operation, binding, clause, point, target_frame, scene, result)
        elif operation['operation_type'] in {'add_column', 'add_beam'}:
            _structural(operation, clause, point, target_frame, result)
        else:
            _window(operation, binding, clause, point, scene, host, target_detail, result)
    except (SceneError, KeyError, TypeError, ValueError) as error:
        if isinstance(error, PublicGeometryError):
            raise
        raise _error("PUBLIC_FACTS_UNAVAILABLE") from error
    return result


def _reference_beam(operation: dict, binding: dict, clause: str, point: np.ndarray,
                    storey: np.ndarray, scene: Any, result: dict) -> None:
    from .public_beam_copy import measure_beam, body_signature
    if not binding.get('reference_id') or clause.count('朝向与参照相同') != 1 or '朝向相对参照' in clause:
        raise _error('EXACT_REFERENCE_REQUIRED')
    peer = scene.offered_record(binding['reference_id'])
    if peer['ifc_class'] != 'IfcBeam':
        raise _error('REFERENCE_CLASS_MISMATCH')
    floors = re.findall(r'完整形状复制参照：楼层「([^」]+)」', clause)
    if floors and floors != [peer.get('storey_name')]:
        raise _error('REFERENCE_OR_HOST_BINDING_MISMATCH')
    anchor = _vector('现存IfcBeam世界基点' + _VECTOR + r'\s*米', clause) * 1000.
    model = getattr(scene, '_geometry_model', None)
    if model is None:
        model = getattr(scene, 'model', None)
    if model is None:
        raise _error('PUBLIC_FACTS_UNAVAILABLE')
    reference = model.by_guid(peer['id'])
    measure_beam(reference)
    placement = _frame(scene.geometry_detail(peer['id'])['placement_world_mm'])
    if not np.allclose(placement[:3, 3], anchor, atol=.5, rtol=0):
        raise _error('REFERENCE_OR_HOST_BINDING_MISMATCH')
    # Literal point authority must select exactly one public occurrence, including
    # peers that were not offered in this Provider page. No private source exists.
    scale = ifcopenshell.util.unit.calculate_unit_scale(model) * 1000.
    matches = []
    for beam in model.by_type('IfcBeam'):
        floor = ifcopenshell.util.element.get_container(beam)
        if floors and getattr(floor, 'Name', None) != floors[0]:
            continue
        if beam.ObjectPlacement is None:
            raise _error('REFERENCE_PLACEMENT_UNAVAILABLE')
        origin = ifcopenshell.util.placement.get_local_placement(beam.ObjectPlacement)[:3, 3] * scale
        if np.allclose(origin, anchor, atol=.5, rtol=0):
            matches.append(str(beam.GlobalId))
    if matches != [peer['id']]:
        raise _error('REFERENCE_AMBIGUOUS')
    placement[:3, 3] = point
    target_entity = model.by_guid(result['target_id'])
    measured = measure_beam(reference, relative_to=target_entity, placement_world_mm=placement)
    relative = np.linalg.inv(storey) @ placement
    if not np.allclose(relative[:3, 2], [0, 0, 1], atol=1e-7, rtol=0):
        raise _error('STRUCTURAL_ORIENTATION_UNSUPPORTED')
    operation['parameters'] = {'axis': {key: {a + '_mm': float(v[i]) for i, a in enumerate('xyz')}
        for key, v in [('start', measured['axis_start_mm']), ('end', measured['axis_end_mm'])]},
        'section': measured['section']}
    result.update(reference_id=peer['id'], placement_world_mm=placement.round(9).tolist(),
        bounds_world_mm=_public_world_bounds(scene, peer['id'],
            _bounds(scene.geometry_detail(peer['id'])['body_bounds_local_mm']), placement),
        exact_beam_body=True, body_signature_sha256=hashlib.sha256(
            json.dumps(body_signature(reference), ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest())


def _structural(operation: dict, clause: str, point: np.ndarray, storey: np.ndarray, result: dict) -> None:
    if '形状为单一长方体' not in clause:
        raise _error("BOX_REQUIRED")
    dims = _vector(r"沿自身三个轴方向的尺寸为" + _VECTOR + r"毫米", clause)
    offset = _vector(r"基点距对应负向面的距离为" + _VECTOR + r"毫米", clause)
    angles = _vector(rf"朝向相对项目坐标系，按高、厚、宽轴依次旋转\s*({_NUMBER})\s*度、\s*({_NUMBER})\s*度、\s*({_NUMBER})\s*度", clause)
    if np.any(dims <= 0):
        raise _error("BOX_DIMENSIONS_INVALID")
    yaw, pitch, roll = np.radians(angles)
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    rotation = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]]) @ np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]]) @ np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    placement = np.eye(4)
    placement[:3, :3], placement[:3, 3] = rotation, point
    column = operation['operation_type'] == 'add_column'
    local_start = -offset + (np.array([dims[0] / 2, dims[1] / 2, 0]) if column else np.array([0, dims[1] / 2, dims[2] / 2]))
    local_end = local_start + (np.array([0, 0, dims[2]]) if column else np.array([dims[0], 0, 0]))
    to_storey = np.linalg.inv(storey) @ placement
    a, b = ((to_storey @ [*v, 1])[:3] for v in (local_start, local_end))
    # The existing operation contract supports vertical columns/horizontal beams.
    delta = b - a
    if (column and (np.linalg.norm(delta[:2]) > .000001 or delta[2] <= 0)
            or not column and (abs(delta[2]) > .000001
                               or not np.isclose(abs(to_storey[2, 2]), 1, atol=1e-8))):
        raise _error("STRUCTURAL_ORIENTATION_UNSUPPORTED")
    section = {'shape': 'rectangle', 'width_mm': float(dims[0] if column else dims[1]),
               'depth_mm' if column else 'height_mm': float(dims[1] if column else dims[2])}
    if column:
        direction = to_storey[:3, 0]
        section['orientation'] = {'x': float(direction[0]), 'y': float(direction[1])}
    keys = ('base', 'top') if column else ('start', 'end')
    operation['parameters']['axis'] = {key: {axis + '_mm': round(float(v[i]), 6) for i, axis in enumerate('xyz')}
                                       for key, v in zip(keys, (a, b))}
    operation['parameters']['section'] = section
    result['bounds_world_mm'] = _transformed_bounds(np.array([-offset, dims - offset]), placement)


def _window(operation: dict, binding: dict, clause: str, point: np.ndarray, scene: Any,
            wall: dict, wall_detail: dict, result: dict) -> None:
    legacy = result['schema_version'] == LEGACY_VERSION
    retained = operation['operation_type'] == 'fill_existing_opening_with_door'
    if ('完整形状复制参照' not in clause
            or (legacy and '朝向与参照相同' not in clause)
            or ('保留现有洞口' if retained else '洞口复制参照构件所填洞口') not in clause
            or not binding.get('reference_id')):
        raise _error("EXACT_REFERENCE_REQUIRED")
    peer = scene.offered_record(binding['reference_id'])
    expected_class = 'IfcWindow' if operation['operation_type'] == 'add_window_with_opening_to_wall' else 'IfcDoor'
    if peer['ifc_class'] != expected_class:
        raise _error("REFERENCE_CLASS_MISMATCH")
    names = re.findall(r"宿主墙「([^」]+)」", clause)
    peer_names = re.findall(rf"现存{expected_class}「([^」]+)」", clause)
    peer_floors = re.findall(r"完整形状复制参照：楼层「([^」]+)」", clause)
    if (names and names != [wall.get('name')]
            or peer_names and peer_names != [peer.get('name')]
            or peer_floors and peer_floors != [peer.get('storey_name')]):
        raise _error("REFERENCE_OR_HOST_BINDING_MISMATCH")
    ref = scene.geometry_detail(peer['id'])
    placement = _frame(ref['placement_world_mm'])
    reference_prefix = f'现存{expected_class}世界基点'
    if reference_prefix in clause:
        reference_point = _vector(reference_prefix + _VECTOR + r'\s*米', clause) * 1000.
        if not np.allclose(placement[:3, 3], reference_point, atol=TOLERANCE_MM, rtol=0):
            raise _error('REFERENCE_OR_HOST_BINDING_MISMATCH')
    if '宿主墙未扣洞口的整体范围' in clause:
        matches = list(re.finditer(r'宿主墙未扣洞口的整体范围为\s*' + _VECTOR + r'\s*至\s*' + _VECTOR + r'\s*米', clause))
        if len(matches) != 1:
            raise _error('CLAUSE_INCOMPLETE_OR_AMBIGUOUS')
        expected = np.array([float(v) * 1000. for v in matches[0].groups()]).reshape(2, 3)
        actual = _bounds(_public_world_bounds(scene, wall['id'], _bounds(wall_detail['body_bounds_local_mm']),
                                               _frame(wall_detail['placement_world_mm']), uncut=True))
        if not np.isfinite(expected).all() or not np.allclose(actual, expected, atol=TOLERANCE_MM, rtol=0):
            raise _error('REFERENCE_OR_HOST_BINDING_MISMATCH')
    if not legacy:
        placement[:3, :3] = placement[:3, :3] @ _reference_rotation(clause)
    placement[:3, 3] = point
    opening = ref['opening']
    if retained:
        opening = scene.geometry_detail(binding['target_id'])
        opening_frame = _frame(opening['placement_world_mm'])
        offset = _vector(rf"保留现有洞口：距墙长度起端\s*({_NUMBER})\s*毫米，\s*距墙厚度负向侧\s*({_NUMBER})\s*毫米，\s*高出墙底\s*({_NUMBER})\s*毫米", clause)
        anchor = (_frame(wall_detail['placement_world_mm']) @ [*(_bounds(wall_detail['body_bounds_local_mm'])[0] + offset), 1])[:3]
        if not np.allclose(opening_frame[:3, 3], anchor, atol=TOLERANCE_MM, rtol=0):
            raise _error('RETAINED_OPENING_BINDING_MISMATCH')
    else:
        opening_frame = placement @ _frame(opening['placement_in_product_mm'])
    opened = (_transformed_bounds(_bounds(opening['body_bounds_local_mm']), opening_frame) if legacy
              else _public_world_bounds(scene, binding['target_id'] if retained else peer['id'],
                  _bounds(opening['body_bounds_local_mm']), opening_frame, opening=not retained))
    axis = wall.get('wall_axis')
    if not axis:
        raise _error("WALL_AXIS_UNAVAILABLE")
    direction = np.array(axis['direction_world'], dtype=float)
    if abs(direction[2]) > 1e-8 or not np.isclose(np.linalg.norm(direction), 1, atol=1e-7):
        raise _error("WALL_ORIENTATION_UNSUPPORTED")
    if not legacy and (not np.allclose(placement[:3, 2], [0, 0, 1], atol=1e-7)
            or not np.isclose(abs(placement[:3, 0] @ direction), 1, atol=1e-7)
            or not np.allclose(opening_frame[:3, 2], [0, 0, 1], atol=1e-7)
            or not np.isclose(abs(opening_frame[:3, 0] @ direction), 1, atol=1e-7)):
        raise _error('REFERENCE_HOST_ORIENTATION_UNSUPPORTED')
    # Project all opening corners, since the host axis may point west or rotate.
    local = _bounds(opening['body_bounds_local_mm'])
    corners = np.array([(opening_frame @ [*v, 1])[:3] for v in product(*zip(local[0], local[1]))])
    positions = (corners - np.array(axis['start_world_mm'])) @ direction
    low, high = float(positions.min()), float(positions.max())
    if low < -.001 or high > axis['length_mm'] + .001:
        raise _error("OPENING_OUTSIDE_HOST")
    if not retained:
        params = operation['parameters']
        params['position'] = {'reference': 'wall_local_start', 'center_offset_mm': round((low + high) / 2, 6)}
        params['opening'] = {'width_mm': round(high - low, 6), 'height_mm': round(opened['z'][1] - opened['z'][0], 6),
                             'sill_height_mm': round(opened['z'][0] - axis['start_world_mm'][2], 6)}
        if operation['operation_type'] == 'add_door_with_opening_to_wall':
            # The copied public cutter defines the opening envelope, never a
            # guessed leaf/clear-passage dimension supplied by the Provider.
            params['opening']['dimension_meaning'] = 'overall_opening'
    body_bounds = (_transformed_bounds(_bounds(ref['body_bounds_local_mm']), placement) if legacy
                   else _public_world_bounds(scene, peer['id'], _bounds(ref['body_bounds_local_mm']), placement))
    result.update(reference_id=peer['id'], bounds_world_mm=body_bounds,
                  opening_bounds_world_mm=opened)
    if not legacy:
        result.update(host_id=wall['id'], placement_world_mm=placement.round(9).tolist(),
                      opening_placement_world_mm=opening_frame.round(9).tolist(),
                      reference_opening_id=ref['opening']['id'], retained_opening=retained)


def _reference_rotation(clause: str) -> np.ndarray:
    same = clause.count('朝向与参照相同')
    explicit = '朝向相对参照' in clause
    if same == 1 and not explicit:
        return np.eye(3)
    if same or not explicit:
        raise _error('REFERENCE_ROTATION_INCOMPLETE_OR_AMBIGUOUS')
    angles = _vector(rf"朝向相对参照，按自身高、厚、宽轴依次旋转\s*({_NUMBER})\s*度、\s*({_NUMBER})\s*度、\s*({_NUMBER})\s*度", clause)
    if not np.allclose(angles[1:], 0, atol=1e-8) or not any(np.isclose(angles[0], v, atol=1e-8) for v in REFERENCE_YAW_DEGREES):
        raise _error('REFERENCE_ROTATION_UNSUPPORTED')
    sign = 1. if abs(angles[0]) < 1e-8 else -1.
    return np.diag([sign, sign, 1.])


class _CurrentIfcFacts:
    """Evaluation reads only the already-bound public identities in D."""
    def __init__(self, model: Any, identities: tuple[str, ...]):
        self.model, self.identities = model, identities

    def offered_record(self, identity: str) -> dict:
        if identity not in self.identities:
            raise _error('IDENTITY_UNBOUND')
        entity = self.model.by_guid(identity)
        floor = entity if entity.is_a('IfcBuildingStorey') else ifcopenshell.util.element.get_container(entity)
        if entity.is_a('IfcOpeningElement'):
            if len(entity.VoidsElements) != 1:
                raise _error('HOST_AMBIGUOUS')
            host = entity.VoidsElements[0].RelatingBuildingElement
            floor = ifcopenshell.util.element.get_container(host)
        row = {'id': identity, 'ifc_class': entity.is_a(), 'name': entity.Name,
               'storey_name': getattr(floor, 'Name', None)}
        if entity.is_a('IfcOpeningElement'):
            row['host_id'] = str(host.GlobalId)
        if entity.is_a('IfcWall'):
            from .geometry import straight_wall_axis, wall_dimensions_mm
            from .scene_context import public_geometry_detail
            detail = public_geometry_detail(self.model, identity)
            m = _frame(detail['placement_world_mm'])
            scale = ifcopenshell.util.unit.calculate_unit_scale(self.model) * 1000
            a, b = straight_wall_axis(entity)
            aa, bb = ((m @ [*(np.array(v) * scale), 1])[:3] for v in (a, b))
            row['wall_axis'] = {'start_world_mm': aa.tolist(), 'direction_world': ((bb - aa) / np.linalg.norm(bb - aa)).tolist(),
                                'length_mm': wall_dimensions_mm(entity)['length']}
        return row

    def geometry_detail(self, identity: str) -> dict:
        self.offered_record(identity)
        from .scene_context import public_geometry_detail
        return public_geometry_detail(self.model, identity)

    def body_vertices_mm(self, identity: str, *, opening: bool = False,
                         uncut: bool = False) -> list[list[float]]:
        self.offered_record(identity)
        from .scene_context import public_body_vertices_mm
        product = self.model.by_guid(identity)
        if opening:
            if len(product.FillsVoids) != 1:
                raise _error('REFERENCE_OPENING_AMBIGUOUS')
            product = product.FillsVoids[0].RelatingOpeningElement
        return public_body_vertices_mm(product, uncut=uncut)


def public_geometry_check(*, requirement: Mapping[str, Any], repair_request: str,
                          damaged_model: Any, repaired_model: Any, roles: Mapping[str, str]) -> CheckResult:
    """C recomputes A's original public requirement, then measures actual R."""
    from .run_models import thaw_json
    requirement = thaw_json(requirement)
    expected, actual = {}, {}
    status = EvaluationStatus.NOT_EVALUABLE
    reason = 'Original public placement requirements could not be verified.'
    try:
        rebuilt = verify_public_geometry_requirement(requirement, repair_request, damaged_model)
        expected = {k: rebuilt[k] for k in ('bounds_world_mm', 'opening_bounds_world_mm') if k in rebuilt}
        family = _FAMILIES[requirement['operation_type']]
        role = {'柱': 'column', '梁': 'beam', '窗': 'window', '门': 'door'}[family]
        for key, entity_role in [('bounds_world_mm', role), ('opening_bounds_world_mm', 'opening')]:
            if key not in expected:
                continue
            entity = repaired_model.by_guid(roles[entity_role])
            settings = ifcopenshell.geom.settings()
            settings.set(settings.USE_WORLD_COORDS, True)
            settings.set('context-identifiers', ['Body'])
            shape = ifcopenshell.geom.create_shape(settings, entity)
            verts = shape.geometry.verts
            if not verts:
                raise _error('RESULT_GEOMETRY_UNAVAILABLE')
            actual[key] = {a: [min(verts[i::3]) * 1000, max(verts[i::3]) * 1000] for i, a in enumerate('xyz')}
        passed = all(abs(v - actual[key][a][i]) <= TOLERANCE_MM
                     for key, box in expected.items() for a, values in box.items() for i, v in enumerate(values))
        if rebuilt.get('placement_world_mm'):
            if rebuilt.get('exact_beam_body'):
                from .public_beam_copy import measure_beam_installation
                pose_check = measure_beam_installation(repaired_model.by_guid(roles[role]), rebuilt,
                                                       reference_model=damaged_model)
            else:
                pose_check = measure_public_installation(repaired_model.by_guid(roles[role]),
                    repaired_model.by_guid(roles['opening']), rebuilt, reference_model=damaged_model)
            expected['installation'] = 'exact public reference geometry and placement'
            actual['installation'] = pose_check
            passed = passed and pose_check['valid']
        status = EvaluationStatus.PASSED if passed else EvaluationStatus.FAILED
        reason = 'Actual world geometry matches the original public placement.' if passed else 'Actual world geometry differs from the original public placement.'
    except (PublicGeometryError, SceneError, RuntimeError, KeyError, ValueError, TypeError, AttributeError):
        pass
    return CheckResult(check_id='l2.public-request-geometry', policy_id='public-request-geometry.v0.3',
        applicability='required', mandatory=True, status=status, reason=reason,
        evidence=(EvidenceFact(fact_id='l2.public-request-geometry', source_kind='explicit_request',
            source_ref='request:/text', expected_state='available' if expected else 'unavailable',
            actual_state='available' if actual else 'unavailable', expected_value=expected, actual_value=actual,
            provenance=(VERSION, 'request:/text', 'current_public_ifc')),))


def verify_public_geometry_requirement(requirement: Mapping[str, Any], request: str, model: Any) -> dict:
    """Recompile trusted metadata from the original public request and source."""
    from .run_models import thaw_json
    requirement = thaw_json(requirement)
    binding = {k: requirement[k] for k in ('operation_id', 'target_id')}
    if requirement.get('reference_id'):
        binding['reference_id'] = requirement['reference_id']
    operation = {'operation_id': requirement['operation_id'], 'operation_type': requirement['operation_type'],
                 'parameters': {}, 'provenance': [{'source_kind': 'user_request', 'reference': 'request:/text',
                                                  'excerpt': requirement['source_excerpt']}]}
    identities = tuple(requirement[k] for k in ('target_id', 'reference_id', 'host_id') if k in requirement)
    source = _CurrentIfcFacts(model, identities)
    rebuilt = calibrate_request_geometry(operation, binding, source, request, version=requirement['schema_version'])
    if rebuilt != requirement:
        raise _error('REQUIREMENT_BINDING_MISMATCH')
    return rebuilt


def place_public_product(product: Any, parent: Any, placement_world_mm: Any) -> None:
    """Author a complete rigid pose in the parent's frame, in project units."""
    from .operations.hosted_opening import local_placement
    frame = _frame(placement_world_mm)
    scale = ifcopenshell.util.unit.calculate_unit_scale(product.file) * 1000.
    frame[:3, 3] /= scale
    relative = np.linalg.inv(ifcopenshell.util.placement.get_local_placement(parent.ObjectPlacement)) @ frame
    if not np.allclose(relative[:3, 2], [0, 0, 1], atol=1e-7):
        raise _error('INSTALLATION_TILT_UNSUPPORTED')
    product.ObjectPlacement = local_placement(product.file, relative_to=parent.ObjectPlacement,
        location=tuple(float(v) for v in relative[:3, 3]),
        ref_direction=tuple(float(v) for v in relative[:3, 0]))


def _local_mesh(product: Any) -> np.ndarray:
    settings = ifcopenshell.geom.settings()
    settings.set('context-identifiers', ['Body'])
    shape = ifcopenshell.geom.create_shape(settings, product)
    points = np.array(shape.geometry.verts).reshape((-1, 3)) * 1000.
    if not len(points):
        raise _error('RESULT_GEOMETRY_UNAVAILABLE')
    # Compare actual local geometry, so a symmetric envelope cannot hide a
    # missing board, hardware component, or a different mapped representation.
    return np.array(sorted(map(tuple, np.round(points, 4))))


def measure_public_installation(product: Any, opening: Any, requirement: Mapping[str, Any],
                                *, reference_model: Any | None = None) -> dict:
    """Independently measure complete poses and public-reference Body meshes."""
    source = product.file if reference_model is None else reference_model
    scale = ifcopenshell.util.unit.calculate_unit_scale(product.file) * 1000.
    pose_errors = []
    geometry_matches = []
    for entity, key, reference_id in (
        (product, 'placement_world_mm', requirement['reference_id']),
        (opening, 'opening_placement_world_mm', requirement['target_id'] if requirement['retained_opening']
         else requirement['reference_opening_id']),
    ):
        actual = ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement).copy()
        actual[:3, 3] *= scale
        expected = _frame(requirement[key])
        pose_errors.append({'translation_mm': float(np.max(np.abs(actual[:3, 3] - expected[:3, 3]))),
                            'rotation_matrix': float(np.max(np.abs(actual[:3, :3] - expected[:3, :3])))})
        a, b = _local_mesh(entity), _local_mesh(source.by_guid(reference_id))
        geometry_matches.append(a.shape == b.shape and bool(np.allclose(a, b, atol=.001, rtol=0)))
    return {'valid': all(geometry_matches) and all(e['translation_mm'] <= TOLERANCE_MM
                 and e['rotation_matrix'] <= 1e-7 for e in pose_errors),
            'pose_errors': pose_errors, 'reference_body_mesh_matches': geometry_matches}
