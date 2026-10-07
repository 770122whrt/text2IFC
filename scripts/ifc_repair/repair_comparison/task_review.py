"""Recompute technical task review; delegated acceptance never means human viewing."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import ifcopenshell
from ifcopenshell.api.root import remove_product
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

from text2ifc_ifc_repair.compare import normalized_model_diff
from text2ifc_ifc_repair.mutation import _element_volume_m3, _snapshot_owner_history, _restore_owner_history, _canonicalize_modified_relationship_sets
from .authoring import ROOT, measure_product, reference_derived_offset
from .contracts import read_json, safe_path, sha256, write_json
from .inspection import native_validation, relation_evidence
from .viewer import collect_meshes, compare_meshes
from .damage_geometry import effective_opening_volumes

NUMBER = r'[-+]?\d+(?:\.\d+)?'
FACT_ID = 'target-1.opening_bottom_world_m'
KEYWORDS = ['窗台', '下沿', '标高', '高度', 'height', 'sill']


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _binding(case, task):
    return {'G': sha256(case / 'private/reference.ifc'), 'D': sha256(case / 'private/mutation/damaged.ifc'),
        'public_ifc': sha256(case / 'public/model.ifc'), 'request': sha256(case / 'public/request.txt'),
        'answer_card': sha256(case / 'private/answer-card.json'),
        'contract': _digest({key: task.get(key) for key in ('source', 'damage', 'request', 'targets', 'author_expectations', 'public_numeric_spec', 'clarification', 'required_product_count', 'required_products', 'required_relation_count')})}


def _close(a, b, tolerance):
    try:
        x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        return x.shape == y.shape and bool(np.isfinite(x).all() and np.isfinite(y).all() and np.max(np.abs(x-y)) <= tolerance)
    except (ValueError, TypeError):
        return False


def _number_in(text, value, tolerance):
    return any(abs(float(number) - float(value)) <= tolerance for number in re.findall(NUMBER, text))


def _span_text(value):
    return value.get('text', '') if isinstance(value, dict) else value


def _coordinate_pairs(text):
    pairs = re.findall(r'X\s*[=:：]?\s*(' + NUMBER + r')\s*[、,，]\s*Y\s*[=:：]?\s*(' + NUMBER + r')', text)
    pairs += re.findall(r'[（(]\s*(' + NUMBER + r')\s*[,，、]\s*(' + NUMBER + r')\s*[）)]', text)
    # Natural requests can specify a shared wall Y followed by an X list.
    shared_y = re.search(r'Y\s*(?:约|为|=)?\s*(' + NUMBER + r')\s*米', text)
    xs = re.search(r'X\s*分别为\s*(' + NUMBER + r')\s*米\s*和\s*(' + NUMBER + r')\s*米', text)
    if shared_y and xs:
        pairs += [(xs[1], shared_y[1]), (xs[2], shared_y[1])]
    single_x = re.search(r'平面中心\s*X\s*为\s*(' + NUMBER + r')\s*米', text)
    if shared_y and single_x:
        pairs.append((single_x[1], shared_y[1]))
    return pairs


def _target_paragraph(request,index):
    match=re.search(r'(?ms)^' + str(index) + r'．(.*?)(?=^\d+．|\n\n请保留|\Z)',request)
    return match[1] if match else ''


def _public_facts(request, expected, ref, index, missing_bottom):
    """Check literal facts in author paragraphs or explicit legacy text spans."""
    spans = expected.get('public_fact_spans')
    errors = []
    if spans:
        dimensions = _span_text(spans.get('dimensions', ''))
        location = _span_text(spans.get('location', ''))
        reference = _span_text(spans.get('reference', ''))
        if not all(isinstance(s, str) and s and s in request for s in (dimensions, location, reference)):
            return ['PUBLIC_FACT_SPAN_MISSING']
        width = re.search(r'宽(?:度)?\s*(' + NUMBER + ')', dimensions)
        height = re.search(r'高(?:度)?\s*(' + NUMBER + ')', dimensions)
        if not width or not height or not _close([width[1], height[1]], [expected['width_mm'], expected['height_mm']], .1):
            errors.append('PUBLIC_DIMENSION_MISMATCH')
        if not any(_close(pair, expected['opening_center_xy_m'], .0006) for pair in _coordinate_pairs(location)):
            errors.append('PUBLIC_LOCATION_MISMATCH')
        ref_absolute = any(_close(pair, ref['opening_center_xy_m'], .0006) for pair in _coordinate_pairs(reference))
        # Legacy request 001 uses a concrete same-wall +X distance.
        relative = re.search(r'沿\s*([XY])\s*(正|负)方向\s*(' + NUMBER + r')\s*米', reference)
        ref_relative = False
        if relative and ('同一面墙' in reference or '同一面墙' in request):
            axis = 'XY'.index(relative[1])
            wanted = float(relative[3]) * (1 if relative[2] == '正' else -1)
            delta = np.array(ref['opening_center_xy_m']) - expected['opening_center_xy_m']
            ref_relative = abs(delta[axis]-wanted) <= .001 and abs(delta[1-axis]) <= .001 and ref['host_guid'] == expected['host_guid']
        if not ref_absolute and not ref_relative:
            errors.append('PUBLIC_REFERENCE_LOCATION_NOT_VERIFIABLE')
        if not missing_bottom:
            vertical = _span_text(spans.get('vertical', ''))
            if expected.get('preserve_opening') and '底' in request and ('对齐' in request or '不变' in request):
                pass  # The actual retained public opening supplies the bottom.
            elif not vertical or vertical not in request or not (_number_in(vertical, expected['opening_bottom_world_m'], .0006) or _number_in(vertical, expected.get('sill_mm', float('inf')), .1)):
                errors.append('PUBLIC_VERTICAL_FACT_MISSING')
        return errors
    match = re.search(r'(?ms)^' + str(index) + r'．(.*?)(?=^\d+．|\n\n请保留|\Z)', request)
    if not match:
        return ['PUBLIC_FACT_SPANS_REQUIRED_FOR_NONSTANDARD_REQUEST']
    paragraph = match[1]
    width = re.search(r'名义宽\s*(' + NUMBER + r')\s*毫米、高\s*(' + NUMBER + r')\s*毫米', paragraph)
    xy = re.findall(r'X=(' + NUMBER + r')、Y=(' + NUMBER + r')', paragraph)
    floors = re.findall(r'(?:在|外观参照)标高\s*(' + NUMBER + r')\s*米', paragraph)
    if not width or not _close([float(width[1]), float(width[2])], [expected['width_mm'], expected['height_mm']], .1):
        errors.append('PUBLIC_DIMENSION_MISMATCH')
    if len(xy) != 2 or not _close(xy[0], expected['opening_center_xy_m'], .0006) or not _close(xy[1], ref['opening_center_xy_m'], .0006):
        errors.append('PUBLIC_LOCATION_OR_REFERENCE_MISMATCH')
    if len(floors) != 2 or not _close(floors, [expected['storey_world_elevation_m'], ref['storey_world_elevation_m']], .0006):
        errors.append('PUBLIC_STOREY_MISMATCH')
    vertical = re.search(r'洞口下沿距该层标高\s*(' + NUMBER + r')\s*毫米（世界标高\s*(' + NUMBER + r')\s*米）', paragraph)
    if missing_bottom:
        if vertical:
            errors.append('REQUIRED_FACT_ALREADY_PUBLIC')
        if re.search(r'原高|原标高|同高|齐平|平齐|对齐|高度.*参照|参照.*高度', paragraph):
            errors.append('CLARIFICATION_IMPLIED_BY_PUBLIC_TEXT')
    elif not vertical or not _close(float(vertical[1]), expected['sill_mm'], .1) or not _close(float(vertical[2]), expected['opening_bottom_world_m'], .0006):
        errors.append('PUBLIC_VERTICAL_FACT_MISSING_OR_CHANGED')
    return errors


def _expected_damaged(original, damage):
    copied = ifcopenshell.file.from_string(original.to_string())
    history = _snapshot_owner_history(copied)
    for target in damage:
        remove_product(copied, product=copied.by_guid(target['target_guid']))
        if not target['preserve_opening']:
            remove_product(copied, product=copied.by_guid(target['opening_guid']))
    _restore_owner_history(copied, history)
    _canonicalize_modified_relationship_sets(copied)
    return copied


def alternative_sill_witness(original, damaged, damage, *, delta_m=.2):
    """Test another window bottom against the actual D host solid, in memory."""
    if damage['kind'] != 'window' or damage['preserve_opening']:
        return {'passed': False, 'reason': 'requires a window and removed opening'}
    source_opening = original.by_guid(damage['opening_guid'])
    original_transform = ifcopenshell.util.placement.get_local_placement(source_opening.ObjectPlacement)
    scale = ifcopenshell.util.unit.calculate_unit_scale(original)
    before_bottom = min(_vertices(source_opening)[:, 2])
    attempts = []
    baseline_removed = None
    host_bounds_z = _vertices(damaged.by_guid(damage['wall_guid']))[:, 2]
    source_z = _vertices(source_opening)[:, 2]
    for delta in (0., abs(delta_m), -abs(delta_m)):
        model = ifcopenshell.file.from_string(damaged.to_string())
        host = model.by_guid(damage['wall_guid'])
        before = _element_volume_m3(host)
        opening = model.add(source_opening)
        transform = original_transform.copy()
        transform[2, 3] += delta / scale
        point = model.create_entity('IfcCartesianPoint', Coordinates=tuple(float(v) for v in transform[:3, 3]))
        axis = model.create_entity('IfcAxis2Placement3D', Location=point,
            Axis=model.create_entity('IfcDirection', DirectionRatios=tuple(float(v) for v in transform[:3, 2])),
            RefDirection=model.create_entity('IfcDirection', DirectionRatios=tuple(float(v) for v in transform[:3, 0])))
        opening.ObjectPlacement = model.create_entity('IfcLocalPlacement', RelativePlacement=axis)
        model.create_entity('IfcRelVoidsElement', GlobalId=ifcopenshell.guid.new(), OwnerHistory=host.OwnerHistory,
            RelatingBuildingElement=host, RelatedOpeningElement=opening)
        aperture = _element_volume_m3(opening)
        removed = before - _element_volume_m3(host)
        if delta == 0:
            baseline_removed = removed
            continue
        vertical_fit = source_z.min()+delta >= host_bounds_z.min()-.001 and source_z.max()+delta <= host_bounds_z.max()+.001
        passed = baseline_removed > 1e-8 and vertical_fit and abs(baseline_removed-removed) <= min(1e-5, baseline_removed * 1e-4)
        attempts.append({'bottom_world_m': float(before_bottom+delta), 'shift_m': delta,
            'opening_volume_m3': aperture, 'removed_host_volume_m3': removed,
            'source_position_removed_host_volume_m3': baseline_removed,
            'vertical_bounds_fit': bool(vertical_fit), 'same_wall_aperture_volume': bool(passed),
            'same_aperture_fits_public_host': bool(passed)})
        if passed:
            break
    return {'passed': any(a['same_aperture_fits_public_host'] for a in attempts),
        'selected_bottom_world_m': float(before_bottom), 'attempts': attempts,
        'basis': 'Same positive wall-intersection cut volume at original and alternate bottom, with opening vertical bounds inside the public host. Cutting solids may legitimately extend through wall faces. Appearance-only reference does not impose vertical alignment.',
        'limitation': 'Geometric non-uniqueness under the public wording; not a statistical test of what any model will infer.'}


def _vertices(entity):
    from .authoring import _mesh
    return _mesh(entity)[0]


def _wall_thickness(model, measurement):
    points = _vertices(model.by_guid(measurement['host_guid']))
    transform = np.asarray(measurement['host_placement_world_m'])
    local = (np.linalg.inv(transform) @ np.column_stack([points, np.ones(len(points))]).T).T[:, :3]
    return float(np.ptp(local[:, 1]))


def allowed_center_offsets(target, reference, offset, author, request):
    """Derive optional wall-face adaptation exclusively from public geometry."""
    rotation = np.asarray(target['host_placement_world_m'])[:3, :3]
    local = rotation.T @ np.asarray(offset)
    rule = author.get('installation_rule')
    if rule:
        if (rule.get('kind') != 'public_wall_face_alignment'
                or not rule.get('public_text') or rule['public_text'] not in request
                or not _close(rule.get('reference_wall_thickness_m'), reference.get('host_thickness_m'), .001)
                or not _close(rule.get('target_wall_thickness_m'), target.get('host_thickness_m'), .001)):
            return [], ['PUBLIC_WALL_THICKNESS_RULE_INVALID']
        normal = abs(local[1]) + (target['host_thickness_m'] - reference['host_thickness_m']) / 2
        if normal < -.001:
            return [], ['PUBLIC_WALL_FACE_OFFSET_NEGATIVE']
        local[1] = max(0., normal)
    if target['kind'] == 'door':
        return [(rotation @ (local*np.array([x,y,1]))).tolist() for x in (1,-1) for y in (1,-1)], []
    return [(rotation @ local).tolist()], []


def enable_sill_clarification(row, *, repository_root=ROOT):
    """Pre-author one necessary fact and its answer; never recover it at runtime."""
    row = deepcopy(row)
    proposal = row['task_proposal']
    spec = proposal['author_expectations']['target-1']
    if spec['ifc_class'] != 'IfcWindow' or spec.get('preserve_opening'):
        raise ValueError('SILL_CLARIFICATION_REQUIRES_REMOVED_WINDOW_OPENING')
    original_path = Path(repository_root) / row['source_path']
    if sha256(original_path) != row['source_sha256']:
        raise ValueError('SOURCE_CHANGED')
    original = ifcopenshell.open(str(original_path))
    damage = {'kind': 'window', 'target_guid': spec['target_guid'], 'opening_guid': spec['opening_guid'],
        'wall_guid': spec['host_guid'], 'preserve_opening': False}
    damaged = _expected_damaged(original, [damage])
    witness = alternative_sill_witness(original, damaged, damage)
    if not witness['passed']:
        raise ValueError('NO_FEASIBLE_ALTERNATIVE_SILL')
    request = proposal.get('clarification_proposal', {}).get('public_request_with_full_facts', proposal['public_request']) if proposal.get('clarification_proposal') else proposal['public_request']
    pattern = r'洞口下沿距该层标高\s*' + NUMBER + r'\s*毫米（世界标高\s*' + NUMBER + r'\s*米）。'
    match = re.search(pattern, request)
    if not match:
        raise ValueError('AUTHOR_VERTICAL_SENTENCE_REQUIRED')
    omitted = match[0]
    public = request[:match.start()] + request[match.end():]
    answer = f'第 1 处窗洞下沿距该层标高 {spec["sill_mm"]:.1f} 毫米，世界标高 {spec["opening_bottom_world_m"]:.3f} 米。'
    fact = {'id': FACT_ID, 'target_id': 'target-1', 'field': 'opening_bottom_world_m',
        'answer': answer, 'keywords': KEYWORDS,
        'value': spec['opening_bottom_world_m'], 'sill_mm': spec['sill_mm'],
        'basis': 'Pre-authored user intent before task preparation, not facts retrieved from G during execution.',
        'omitted_public_sentence': omitted, 'alternative_feasibility': witness,
        'why_needed': '洞口已删除，公开只指定平面位置、尺寸和外观。外观参照没有约束竖向对齐；另一个洞底高度在同一墙上同样容纳完整开口。'}
    proposal['public_request'] = public
    proposal['clarification_required'] = True
    proposal['clarification'] = {'schema_version': 'repair-comparison-clarification/0.1',
        'required_user_facts': [FACT_ID], 'facts': {FACT_ID: fact},
        'out_of_card_policy': 'pending_user_decision',
        'reply_policy': 'Only answer the requested fact using this pre-authored card; never look up G at runtime.'}
    proposal['clarification_proposal'] = {'enabled': True, 'necessary_fact_candidate': FACT_ID,
        'omittable_text': omitted, 'answer_card': answer, 'public_request_with_full_facts': request,
        'automatic_clarification_admission': False, 'alternative_feasibility': witness}
    spec['bottom_fact_source'] = 'preauthored_answer_card'
    proposal['public_numeric_spec']['targets'][0]['bottom_fact_source'] = 'preauthored_answer_card'
    return row


def audit_case(case, *, authorization=None, accept=False):
    """Write evidence, and accept only an actually passing authorized review."""
    if accept and (not isinstance(authorization, dict) or not all(isinstance(authorization.get(k), str) and authorization[k].strip() for k in ('user_quote', 'at'))):
        raise ValueError('USER_AUTHORIZATION_REQUIRED')
    case = safe_path(Path(case))
    private = case / 'private'
    task = read_json(private / 'task.json')
    bindings = _binding(case, task)
    prior_path = private / 'technical-review.json'
    prior = read_json(prior_path) if prior_path.exists() else None
    errors, checks, target_rows = [], {}, []
    request = (case / 'public/request.txt').read_text(encoding='utf-8').strip()
    source = task['source']
    proposal = source['task_proposal']
    card = read_json(private / 'answer-card.json')
    expected = task.get('author_expectations', {})
    numeric = task.get('public_numeric_spec', {})
    def record(name, passed, error=None):
        checks[name] = bool(passed)
        if not passed:
            errors.append(error or name.upper())
    accepted_binding = task.get('review', {}).get('input_bindings')
    if accepted_binding is None and prior and prior.get('accepted'):
        accepted_binding = prior['input_bindings']
    if accepted_binding is not None and accepted_binding != bindings:
        errors.append('REVIEW_BINDING_STALE')
    record('input_hash_bindings', bindings['G'] == task['source_sha256'] == source['source_sha256'] and bindings['D'] == task['damaged_sha256'] == bindings['public_ifc'])
    record('public_request_bound', request == task['request'].strip() == proposal['public_request'].strip())
    record('author_contract_bound', bool(expected) and expected == proposal.get('author_expectations') and bool(numeric) and numeric == proposal.get('public_numeric_spec'), 'AUTHOR_CONTRACT_MISSING_OR_CHANGED')
    record('public_files_only', {p.name for p in (case / 'public').iterdir()} == {'model.ifc', 'request.txt'})
    original = ifcopenshell.open(str(private / 'reference.ifc'))
    damaged = ifcopenshell.open(str(private / 'mutation/damaged.ifc'))
    native = {'G': native_validation(original), 'D': native_validation(damaged)}
    record('native_recomputed', original.schema == damaged.schema == 'IFC2X3' and all(r['passed'] for r in native.values()))
    expected_model = _expected_damaged(original, task['damage'])
    diff = normalized_model_diff(expected_model, damaged)
    record('damage_and_preservation_recomputed', not any(diff[k] for k in ('created', 'removed', 'modified')))
    meshes_g = collect_meshes(private / 'reference.ifc')
    meshes_d = collect_meshes(private / 'mutation/damaged.ifc')
    removed = {x['target_guid'] for x in task['damage']} | {x['opening_guid'] for x in task['damage'] if not x['preserve_opening']}
    hosts = {x['wall_guid'] for x in task['damage'] if not x['preserve_opening']}
    retained = set(meshes_g['meshes']) - removed - hosts
    unchanged = compare_meshes(meshes_g, meshes_d, sorted(retained))
    record('retained_geometry_recomputed', not meshes_g['errors'] and not meshes_d['errors'] and all(x['unchanged'] for x in unchanged))
    record('removed_targets_not_visible', not (removed & meshes_d['meshes'].keys()))
    actual_products_g = {e.GlobalId for e in original.by_type('IfcProduct')}
    actual_products_d = {e.GlobalId for e in damaged.by_type('IfcProduct')}
    record('exact_removed_product_set', actual_products_g - actual_products_d == removed and not (actual_products_d - actual_products_g))
    required = card.get('required_user_facts', [])
    clarification = {'required': required, 'passed': True, 'witness': None}
    clarification_contract = task.get('clarification', {})
    clarification_bound = required == clarification_contract.get('required_user_facts', []) and bool(required) == bool(task.get('clarification_required', False))
    if required:
        clarification_bound = clarification_bound and card.get('facts') == clarification_contract.get('facts') == proposal.get('clarification', {}).get('facts') and required == [FACT_ID]
    record('clarification_contract_bound', clarification_bound)
    relations, closures, refs, public_errors = [], {}, [], []
    opening_ids = [t['opening_guid'] for t in task['damage'] if not t['preserve_opening']]
    effective = effective_opening_volumes(original, opening_ids) if opening_ids else {'openings': [], 'walls': {}}
    if set(expected) != {f'target-{i+1}' for i in range(len(task['damage']))}:
        public_errors.append('AUTHOR_TARGET_DENOMINATOR_MISMATCH')
    for index, target in enumerate(task['targets'], 1):
        key = f'target-{index}'
        author = expected.get(key)
        if not author:
            continue
        try:
            measured = measure_product(original, original.by_guid(target['target_guid']).id())
            reference_g = original.by_guid(author['reference_guid'])
            ref = measure_product(damaged, damaged.by_guid(author['reference_guid']).id())
            measured['host_thickness_m'] = _wall_thickness(original, measured)
            ref['host_thickness_m'] = _wall_thickness(damaged, ref)
            refs.append(author['reference_guid'])
            numeric_target = next((s for s in numeric.get('targets', []) if s.get('id', s.get('target_id')) == key), None)
            target_errors = []
            if numeric_target is None:
                target_errors.append('NUMERIC_TARGET_MISSING')
            else:
                for field in ('width_mm', 'height_mm', 'opening_center_xy_m', 'opening_bottom_world_m'):
                    tolerance = .1 if field.endswith('_mm') else .000001
                    if not _close(author.get(field), numeric_target.get(field), tolerance):
                        target_errors.append('AUTHOR_NUMERIC_CONTRACT_MISMATCH:' + field)
            for field in ('width_mm', 'height_mm', 'opening_height_mm', 'opening_center_xy_m', 'opening_bottom_world_m', 'storey_world_elevation_m', 'sill_mm'):
                if field in author and not _close(author[field], measured[field], 1 if field.endswith('_mm') else .001):
                    target_errors.append('SOURCE_MEASUREMENT_MISMATCH:' + field)
            for field, actual in (('target_guid', target['target_guid']), ('host_guid', measured['host_guid']), ('storey_guid', measured['storey_guid']), ('ifc_class', measured['ifc_class'])):
                if field in author and author[field] != actual:
                    target_errors.append('TARGET_IDENTITY_MISMATCH:' + field)
            offset = reference_derived_offset(measured, ref)
            offsets = author.get('target_center_offsets_from_opening_m', [author.get('target_center_offset_from_opening_m')])
            allowed, offset_errors = allowed_center_offsets(measured, ref, offset['offset_m'], author, request)
            target_errors += offset_errors
            if not offsets or not all(any(_close(value, valid, .001) for valid in allowed) for value in offsets):
                target_errors.append('OFFSET_NOT_DERIVABLE_FROM_PUBLIC_REFERENCE')
            if not any(_close(value, offset['actual_target_offset_world_m'], .001) for value in offsets):
                target_errors.append('PUBLIC_OFFSET_DOES_NOT_MATCH_REFERENCE_G_TARGET')
            missing = key == 'target-1' and FACT_ID in required
            check_author = {**measured, **author}
            target_errors += _public_facts(request, check_author, ref, index, missing)
            if not target['preserve_opening']:
                item = closures.setdefault(target['wall_guid'], {'before': _element_volume_m3(original.by_guid(target['wall_guid'])), 'after': _element_volume_m3(damaged.by_guid(target['wall_guid'])),
                    'expected_after': _element_volume_m3(expected_model.by_guid(target['wall_guid'])),
                    'effective_delta_m3':effective['walls'][target['wall_guid']]['group_delta_m3'], 'cutting_solid_volume_sum': 0})
                item['cutting_solid_volume_sum'] += _element_volume_m3(original.by_guid(target['opening_guid']))
            requirements = target['required_relations']
            relations += relation_evidence(original, damaged, {'damage': target, 'task': {'required_relations': requirements}}, target['opening_guid'])
            if missing:
                fact = card.get('facts', {}).get(FACT_ID, {})
                witness = alternative_sill_witness(original, damaged, target)
                fact_ok = _close(fact.get('value'), measured['opening_bottom_world_m'], .001) and _number_in(fact.get('answer', ''), measured['opening_bottom_world_m'], .0006)
                clarification.update({'witness': witness, 'passed': witness['passed'] and fact_ok
                    and fact.get('omitted_public_sentence', '') not in _target_paragraph(request,index)})
                if not clarification['passed']:
                    target_errors.append('CLARIFICATION_FACT_OR_ALTERNATIVE_INVALID')
            target_rows.append({'id': key, 'step_id': target['source_step_id'], 'requested_dimensions_mm': [author['width_mm'], author['height_mm']],
                'nominal_dimensions_mm': [measured['width_mm'], measured['height_mm']],
                'opening_dimensions_mm': [measured['opening_width_mm'], measured['opening_height_mm']],
                'opening_sill_mm': measured['sill_mm'], 'mesh_local_extents_mm': measured['mesh_local_extents_mm'],
                'reference_guid': author['reference_guid'], 'reference_nominal_dimensions_mm': [ref['width_mm'], ref['height_mm']],
                'measured': measured, 'reference_d': ref, 'offset_witness': offset, 'errors': target_errors})
            public_errors += [f'{key}:{error}' for error in target_errors]
        except (RuntimeError, ValueError, KeyError, TypeError, StopIteration) as error:
            public_errors.append(f'{key}:MEASUREMENT_FAILED:{error}')
    reference_comparisons = compare_meshes(meshes_g, meshes_d, refs)
    record('retained_reference_geometry_unchanged', bool(refs) and all(r['unchanged'] for r in reference_comparisons))
    record('public_facts_match_measurements', not public_errors and len(target_rows) == len(task['targets']))
    errors += public_errors
    record('relation_edges_recomputed', len(relations) == task['required_relation_count'] and all(r['verified'] for r in relations))
    record('wall_closure_recomputed', all(v['after'] > v['before'] and abs(v['after'] - v['expected_after']) <= 1e-5
        and abs((v['after']-v['before'])-v['effective_delta_m3']) <= 1e-5 for v in closures.values()))
    record('denominators_match', task['required_product_count'] == len(task['targets']) == len(task['damage']) and task['required_products'] == dict(Counter(t['target']['class'] for t in task['targets'])))
    report = {'schema_version': 'repair-comparison-technical-review/0.1', 'case_id': task['case_id'],
        'passed': not errors and all(checks.values()), 'accepted': False, 'human_viewed': False,
        'input_bindings': bindings, 'checks': checks, 'errors': sorted(set(errors)), 'native_validation': native,
        'clarification': clarification, 'targets': target_rows, 'reference_comparisons': reference_comparisons,
        'wall_closure': closures, 'effective_opening_evidence':effective, 'relationship_evidence': relations,
        'scope': 'Delegated technical task review; no usBIM visual confirmation or model capability result.'}
    if _binding(case, task) != bindings:
        report['passed'] = False
        report['errors'].append('INPUT_CHANGED_DURING_REVIEW')
    if accept and report['passed']:
        card.update({'status':'accepted_by_delegation','reviewer':'Codex',
                     'human_viewed':False,'authorization':deepcopy(authorization)})
        write_json(private/'answer-card.json',card)
        bindings = _binding(case,task)
        report['input_bindings'] = bindings
        task['review'] = {'status': 'accepted_by_delegation', 'kind': 'delegated_technical', 'human_viewed': False,
            'reviewer':'Codex',
            'technical_review_passed': True, 'authorization': deepcopy(authorization),
            'reviewed_at': datetime.now(timezone.utc).isoformat(), 'input_bindings': bindings}
        report['accepted'] = True
        report['authorization'] = deepcopy(authorization)
        write_json(private / 'task.json', task)
    elif task['review'].get('status') == 'accepted_by_delegation' and not report['passed']:
        task['review'] = {**task['review'], 'status': 'stale_review', 'technical_review_passed': False,
            'invalidated_by': report['errors']}
        write_json(private / 'task.json', task)
    write_json(private / 'technical-review.json', report)
    write_json(private / 'geometry-review.json', {'passed': report['passed'], 'request': task['request'],
        'source_sha256': task['source_sha256'], 'damaged_sha256': task['damaged_sha256'], 'targets': target_rows,
        'notes': ['尺寸来自实际单位和几何，不从 Name 猜测。名义宽高与带框网格外包尺寸分别记录。',
            '技术审题按实际 G/D 重算；未声称人工打开 usBIM。'], 'input_bindings': bindings})
    return report
