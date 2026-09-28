"""Current roundtrip evaluator: global matching and a uniform strict 0.1 mm policy.

Historical evaluators remain replayable. Only source expectations are normalized
to the agreed host-storey convention; candidate containment is always inspected.
"""
from __future__ import annotations

import copy
import math
from pathlib import Path

from .diagnostic_review import compare_observations as _legacy_compare
from .observation import all_items, extract_description_facts

VERSION = 'text2ifc/ifc2text-roundtrip-compare/1.0'
LINEAR_TOLERANCE_MM = .1
NUMERIC_EPSILON_MM = 1e-9


def outside_linear_tolerance(value):
    """Boundary equality fails, allowing only 1e-9 mm numerical uncertainty."""
    return not math.isfinite(value) or value >= LINEAR_TOLERANCE_MM - NUMERIC_EPSILON_MM


def _source_host_policy(source):
    expected = copy.deepcopy(source)
    items = dict((i['label'], i) for _, i in all_items(expected))
    changes = []
    for category, item in all_items(expected):
        if category not in ('doors', 'windows'):
            continue
        host = items.get(item.get('host_wall'), {})
        if host.get('storey') and host['storey'] != item.get('storey'):
            changes.append({'category': category, 'source': item['label'],
                            'host': host['label'], 'from': item.get('storey'), 'to': host['storey']})
            item['storey'] = host['storey']
    return expected, changes


def _material_content(item):
    content = []
    for material in item.get('materials', []):
        kind = material['kind']
        if kind in ('material_layer_set', 'material_layer_set_usage'):
            content.append({'kind': 'layers', 'layers': [
                {'name': None if l.get('name') is None else str(l['name']).strip(),
                 'thickness_mm': l.get('thickness_mm')} for l in material['layers']]})
        elif kind == 'material_list':
            content.append({'kind': 'list', 'names': sorted(
                [None if v is None else str(v).strip() for v in material['names']], key=str)})
        elif kind == 'single_material':
            content.append({'kind': 'single', 'name': None if material.get('name') is None else str(material['name']).strip()})
        else:
            content.append({'kind': 'unsupported', 'ifc_class': material.get('ifc_class')})
    return content


def _material_equal(a, b):
    if type(a) is not type(b) and not isinstance(a, (int, float)):
        return False
    if isinstance(a, dict):
        if not isinstance(b, dict) or a.keys() != b.keys():
            return False
        return all((x is None and b[k] is None) or
                   (x is not None and b[k] is not None and not outside_linear_tolerance(abs(x-b[k])))
                   if k == 'thickness_mm' else _material_equal(x, b[k]) for k, x in a.items())
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(_material_equal(x, y) for x, y in zip(a, b))
    return a == b


def _summarize(report):
    rows = [r for category in report['categories'].values() for r in category['matched']]
    summary = report['summary']
    summary['geometric_deviations'] = sum(r['geometry_outside_tolerance'] for r in rows)
    summary['storey_elevation_deviations'] = sum(r['outside_tolerance'] for r in report['storeys']['matched'])
    summary['material_content_differences'] = sum(r['material_content_difference'] for r in rows)
    summary['missing_storeys'] = len(report['storeys']['missing'])
    summary['extra_storeys'] = len(report['storeys']['extra'])
    failed = any(summary[k] for k in ('missing', 'extra', 'geometric_deviations',
        'storey_elevation_deviations', 'material_content_differences', 'relation_differences',
        'missing_storeys', 'extra_storeys'))
    measured = bool(rows) and not report['unassessed'] and not report['matching_ambiguities']
    report['status'] = {'files_readable': None, 'geometry_processable': None,
        'evaluated_scope_consistent': False if failed else (True if measured else None),
        'reconstruction_consistent': False if failed else None}
    # Keep public report rendering compatible while exposing the fuller categories.
    report['components'] = report['categories']
    for row in rows:
        row['outside_tolerance'] = row['geometry_outside_tolerance'] or row['material_content_difference']


def compare_observations(source, candidate, *, matching_mm=2000.):
    expected, changes = _source_host_policy(source)
    report = _legacy_compare(expected, candidate, position_mm=.1, dimension_mm=.1, matching_mm=matching_mm)
    report['schema_version'] = VERSION
    report['tolerances'] = {'linear_mm': .1, 'position_mm': .1, 'dimension_mm': .1,
        'storey_elevation_mm': .1, 'outline_mm': .1, 'material_layer_thickness_mm': .1,
        'angle_deg': 2., 'boundary': 'error >= 0.1 mm fails', 'numeric_epsilon_mm': NUMERIC_EPSILON_MM,
        'area_and_volume': 'report only; no linear threshold applied'}
    report['containment_policy'] = {'name': 'source_fillings_follow_host_storey',
        'source_adjustments': changes, 'candidate_normalized': False, 'source_ifc_modified': False}
    report['original_source_relation_differences'] = (
        _legacy_compare(source, candidate, matching_mm=matching_mm)['relation_differences']
        if changes else copy.deepcopy(report['relation_differences']))
    left = {i['label']: i for _, i in all_items(source)}
    right = {i['label']: i for _, i in all_items(candidate)}
    for row in report['storeys']['matched']:
        row['outside_tolerance'] = outside_linear_tolerance(row['elevation_delta_mm'])
    for category in report['categories'].values():
        for row in category['matched']:
            a, b = left[row['source']], right[row['candidate']]
            coordinates = [abs(x-y) for k in ('x', 'y', 'z') for x, y in zip(a['bounds_mm'][k], b['bounds_mm'][k])]
            row['bbox_coordinate_max_delta_mm'] = max(coordinates)
            values = [row['center_delta_mm'], *coordinates, *row['bbox_size_deltas_mm'].values(),
                      *row['nominal_dimension_deltas_mm'].values()]
            if row['outline_hausdorff_mm'] is not None:
                values.append(row['outline_hausdorff_mm'])
            row['geometry_outside_tolerance'] = any(outside_linear_tolerance(v) for v in values) or (
                row['angle_delta_deg'] is not None and row['angle_delta_deg'] > 2.)
            row['source_material_content'], row['candidate_material_content'] = _material_content(a), _material_content(b)
            row['material_content_difference'] = not _material_equal(row['source_material_content'], row['candidate_material_content'])
    _summarize(report)
    return report


def _wall_result(source, candidate):
    from .wall_compare_v09 import compare_wall_entities
    report = compare_wall_entities(source, candidate)
    report['schema_version'] = 'text2ifc/wall-compare/1.0'
    report['boundary'] = 'error >= 0.1 mm fails'
    for key in ('before_openings', 'with_openings'):
        part = report[key]
        if part.get('unassessed'):
            continue
        values = [part['bbox_coordinate_max_delta_mm'], part['bbox_center_delta_mm'],
                  *part['bbox_size_deltas_mm'].values(), part['projected_boundary_distance_mm']]
        for section in part['sections']:
            if section.get('distance_mm') is not None:
                section['pass'] = not outside_linear_tolerance(section['distance_mm'])
        part['pass'] = not any(outside_linear_tolerance(v) for v in values) and all(
            s.get('pass', False) for s in part['sections'])
    report['pass'] = all(report[k]['pass'] for k in ('before_openings', 'with_openings'))
    return report


def _precise_facts(path, model):
    """Do not score rounded presentation facts at a submillimetre boundary."""
    from .facts import _world_vertices_mm
    from text2ifc_ifc_repair.geometry import opening_dimensions_mm
    from text2ifc_ifc_repair.index_adapters import WallIndexAdapter
    import ifcopenshell.util.unit
    facts = extract_description_facts(path)
    scale = ifcopenshell.util.unit.calculate_unit_scale(model) * 1000.
    for category, item in all_items(facts):
        entity = model.by_guid(item['source_global_id'])
        try:
            points = _world_vertices_mm(entity)
            item['bounds_mm'] = {k: [min(p[j] for p in points), max(p[j] for p in points)]
                                 for j, k in enumerate(('x', 'y', 'z'))}
        except (RuntimeError, ValueError, TypeError):
            item.pop('bounds_mm', None)
        if category in ('doors', 'windows'):
            for field, attribute in (('overall_width_mm', 'OverallWidth'), ('overall_height_mm', 'OverallHeight')):
                value = getattr(entity, attribute, None)
                item[field] = None if value is None else float(value) * scale
        if category == 'openings':
            try:
                item['dimensions_mm'] = opening_dimensions_mm(entity)
            except (RuntimeError, ValueError, TypeError):
                item['dimensions_mm'] = {}
        if category == 'walls':
            # PCA extents depend on tessellation and are not reliable intrinsic
            # dimensions of polygon walls; precise body checks cover those walls.
            for key in ('length_mm', 'thickness_mm', 'height_mm'):
                item.pop(key, None)
            if item.get('measurement_method') == 'explicit_ifc_axis_plus_geometry':
                try:
                    dimensions = WallIndexAdapter().extract(entity).geometry_summary.get('dimensions_mm', {})
                    for key in ('length', 'thickness', 'height'):
                        if dimensions.get(key) is not None:
                            item[key + '_mm'] = float(dimensions[key])
                except (RuntimeError, ValueError, TypeError):
                    pass
    return facts


def compare_roundtrip(source_path, candidate_path, *, original_source_path=None):
    """Read-only file comparison; optional original is an archival diagnostic only."""
    import ifcopenshell
    try:
        source_model = ifcopenshell.open(str(source_path))
        candidate_model = ifcopenshell.open(str(candidate_path))
    except Exception as error:
        return {'schema_version': VERSION, 'status': {'files_readable': False,
            'geometry_processable': None, 'reconstruction_consistent': None}, 'error_type': type(error).__name__}
    try:
        source = _precise_facts(source_path, source_model)
        candidate = _precise_facts(candidate_path, candidate_model)
    except Exception as error:
        return {'schema_version': VERSION, 'status': {'files_readable': True,
            'geometry_processable': False, 'reconstruction_consistent': None}, 'error_type': type(error).__name__}
    report = compare_observations(source, candidate)
    report['source'], report['candidate'] = source['source'], candidate['source']
    left = {i['label']: i for _, i in all_items(source)}
    right = {i['label']: i for _, i in all_items(candidate)}
    for row in report['categories']['walls']['matched']:
        detail = _wall_result(source_model.by_guid(left[row['source']]['source_global_id']),
                              candidate_model.by_guid(right[row['candidate']]['source_global_id']))
        row['wall_geometry'] = detail
        unknown = any(detail[k].get('unassessed') for k in ('before_openings', 'with_openings'))
        if unknown:
            report['unassessed'].append({'category': 'walls', 'source': row['source'], 'fields': ['wall_mesh_comparison']})
        else:
            row['geometry_outside_tolerance'] |= not detail['pass']
    _summarize(report)
    report['status']['files_readable'] = True
    report['status']['geometry_processable'] = bool(left) and all(
        i.get('bounds_mm') for i in [*left.values(), *right.values()])
    report['source_role'] = 'comparison_source'
    if original_source_path is not None:
        if Path(original_source_path).resolve() == Path(source_path).resolve():
            raise ValueError('ORIGINAL_AND_NORMALIZED_SOURCE_MUST_DIFFER')
        original = extract_description_facts(original_source_path)
        report['source_role'] = 'host_policy_normalized_source_working_copy'
        report['original_source_diagnostic'] = {
            'source': original['source'], 'role': 'archival_baseline_not_replaced',
            'relation_differences': _legacy_compare(original, candidate)['relation_differences']}
    return report
