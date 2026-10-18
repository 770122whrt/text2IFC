"""Method-independent candidate scorer; draft policy is never formal admission.

The caller supplies the unique submission and task state, never ChangeSet or an
application record. Candidate snapshots are diagnostic fallbacks, not approved
expectations. Explicit ``policy['targets']`` carries pre-run task expectations;
this module neither parses model claims nor freezes a task on the caller's behalf.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from itertools import product
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.unit
import ifcopenshell.util.placement
import numpy as np

from .contracts import read_json, sha256
from .inspection import native_validation
from .ledger import TERMINAL
from .scoring import _bounds, _center, _mesh, _mesh_signature, _preservation, clarification_score


SCHEMA = 'repair-comparison-formal-score/0.1'
DEFAULT_POLICY = {
    'version': 'formal-candidate-draft-0.1', 'frozen': False,
    'length_mm': 1.0, 'coarse_match_m': 0.5, 'angle_degrees': 0.1,
    'appearance_method': 'public-host-local-centered-triangle-style-multiset-fixed-eight-grids',
    'appearance_vertex_round_m': 1e-6, 'appearance_style_decimals': 5,
    'appearance_grid_offsets_m': [0.0, 0.5e-6],
    'appearance_max_axis_quantization_m': 1e-6,
    'appearance_equivalence': 'unproven differences require review',
    'position_method': 'public opening center/bottom and predeclared target offset alternatives',
    'targets': {},
}
RELATIONS = {'IfcRelFillsElement', 'IfcRelVoidsElement', 'IfcRelContainedInSpatialStructure'}


def _metric(numerator, denominator, status='scored'):
    return {'numerator': numerator, 'denominator': denominator,
            'value': numerator / denominator if numerator is not None and denominator else None,
            'status': status if denominator else 'not_applicable'}


def _flag(value, status='scored'):
    return {'value': value, 'status': status}


def _policy(value):
    result = deepcopy(DEFAULT_POLICY)
    if value is not None:
        if set(value) - set(result):
            raise ValueError('UNKNOWN_POLICY_FIELDS')
        result.update(deepcopy(value))
    for key in ('length_mm', 'coarse_match_m', 'angle_degrees'):
        if type(result[key]) not in (int, float) or not math.isfinite(result[key]) or result[key] <= 0:
            raise ValueError('INVALID_POLICY_TOLERANCE:' + key)
    # These are descriptions of the inherited witness, not tuning knobs.
    for key in ('appearance_method', 'appearance_vertex_round_m', 'appearance_style_decimals',
                'appearance_grid_offsets_m', 'appearance_max_axis_quantization_m',
                'appearance_equivalence', 'position_method'):
        if result[key] != DEFAULT_POLICY[key]:
            raise ValueError('UNSUPPORTED_GEOMETRY_POLICY:' + key)
    if type(result['frozen']) is not bool or not isinstance(result['targets'], dict):
        raise ValueError('INVALID_POLICY')
    result['angle_check'] = 'not independently measured; appearance witness only; angle_degrees is reserved'
    return result


def _task(case):
    spec = read_json(case / 'private/task.json')
    evidence = read_json(case / 'private/checks.json')
    if spec['schema_version'] != 'repair-comparison-task-candidate/0.1':
        raise ValueError('UNSUPPORTED_TASK_SCHEMA')
    targets = spec['targets']
    expected = Counter()
    edge_ids = []
    for index, row in enumerate(targets):
        if row['kind'] not in {'window', 'door'}:
            raise ValueError('UNSUPPORTED_TARGET_FAMILY')
        if type(row['preserve_opening']) is not bool:
            raise ValueError('INVALID_OPENING_CONTRACT')
        row['target_id'] = f'target-{index+1}'
        expected['IfcWindow' if row['kind'] == 'window' else 'IfcDoor'] += 1
        for edge in row['required_relations']:
            if edge['ifc_class'] not in RELATIONS:
                raise ValueError('UNSUPPORTED_RELATION_OBLIGATION')
            edge_ids.append(edge['id'])
        if len({edge['ifc_class'] for edge in row['required_relations']}) != len(row['required_relations']):
            raise ValueError('DUPLICATE_SEMANTIC_EDGE')
    if (not targets or dict(expected) != spec['required_products']
            or len(targets) != spec['required_product_count']
            or len(edge_ids) != spec['required_relation_count']
            or len(set(edge_ids)) != len(edge_ids)):
        raise ValueError('TASK_DENOMINATOR_MISMATCH')
    if not evidence.get('checks') or not all(v is True for v in evidence['checks'].values()):
        raise ValueError('PREPARATION_EVIDENCE_FAILED')
    return spec, evidence


def _by_guid(model, guid):
    try:
        return model.by_guid(guid)
    except RuntimeError:
        return None


def _safe_center(entity):
    try:
        value = _center(entity)
        return value if np.isfinite(value).all() else None
    except (RuntimeError, ValueError, AttributeError, TypeError):
        return None


def _matching(candidates, center, radius):
    matches = []
    for entity in candidates:
        actual = _safe_center(entity)
        if actual is not None:
            distance = float(np.max(np.abs(actual - center)))
            if distance <= radius:
                matches.append((entity, distance))
    return {'status': 'matched' if len(matches) == 1 else 'ambiguous' if matches else 'missing',
            'candidates': [e.GlobalId for e, _ in matches],
            'distances_m': [d for _, d in matches],
            'guid': matches[0][0].GlobalId if len(matches) == 1 else None}


def _bounds_match(entity, expected, tolerance):
    bounds = _bounds(entity)
    return bounds is not None and bool(np.all(np.abs(bounds - np.asarray(expected)) <= tolerance / 1000))


def _appearance(candidate, reference, kind):
    """Actual world meshes in their bound public host-wall coordinates.

    Product placement cannot normalize away a wrongly rotated occurrence. A
    missing/nonunique host prevents confirmation; it never invokes best fit.
    """
    def mesh(entity):
        fills = list(entity.FillsVoids)
        if len(fills) != 1:
            return None
        voids = list(fills[0].RelatingOpeningElement.VoidsElements)
        if len(voids) != 1:
            return None
        host = voids[0].RelatingBuildingElement
        rotation = ifcopenshell.util.placement.get_local_placement(host.ObjectPlacement)[:3, :3]
        if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-9):
            return None
        vertices, faces, styles, material_ids = _mesh(entity)
        styles = [tuple(value if math.isfinite(value) else None for value in style) for style in styles]
        return vertices @ rotation, faces, styles, material_ids
    reference_mesh, actual = mesh(reference), mesh(candidate)
    if reference_mesh is None or actual is None:
        return None
    return True if _same_centered_surface(actual,reference_mesh,kind) else None


def _same_centered_surface(actual, reference, kind):
    """Sufficient triangle-and-style witness with fixed quantization phases.

    A shared cell bounds every corresponding centered coordinate by <1 µm per
    axis; the complete triangle/style multiset must match on one common grid.
    Faces, multiplicity and material assignment are never replaced by point-set
    distance. Eight fixed phases prevent a nanometre crossing of one rounding
    boundary from being the only reason identical geometry remains unproven.
    """
    signs = [(1,1,1)] if kind == 'window' else [(1,1,1),(-1,-1,1),(-1,1,1),(1,-1,1)]
    wanted = _mesh_signature(reference)
    if any(_mesh_signature(actual,sign)==wanted for sign in signs):
        return True
    def signature(mesh,sign,offset):
        vertices,faces,styles,material_ids=mesh
        center=(vertices.min(axis=0)+vertices.max(axis=0))/2
        bins=np.floor(((vertices-center)*sign+offset)/1e-6).astype(np.int64)
        triangles=[]
        for index,face in enumerate(faces):
            material=material_ids[index]
            style=styles[material] if 0<=material<len(styles) else None
            triangles.append((tuple(sorted(tuple(bins[v]) for v in face)),style))
        return Counter(triangles)
    for offset in product((0.,.5e-6),repeat=3):
        wanted=signature(reference,(1,1,1),offset)
        if any(signature(actual,sign,offset)==wanted for sign in signs):
            return True
    return False


def _preservation_with_additions(damaged, result, new_guids):
    evidence = _preservation(damaged, result, new_guids)
    old = {entity.GlobalId for entity in damaged.by_type('IfcRoot')}
    new_guids = set(new_guids)
    allowed = set(new_guids)
    # Authorised occurrence support may introduce types/properties. An unrelated
    # root is not excused merely because it was absent from D.
    support = []
    for guid in new_guids:
        product = result.by_guid(guid)
        support.extend(result.traverse(product))
        for inverse in result.get_inverse(product):
            if inverse.is_a('IfcRelDefines') or inverse.is_a('IfcRelAssociates'):
                related = getattr(inverse, 'RelatedObjects', ())
                if related and all(getattr(item, 'GlobalId', None) in new_guids for item in related):
                    support.extend(result.traverse(inverse))
            elif inverse.is_a() in RELATIONS:
                allowed.add(inverse.GlobalId)
    allowed.update(entity.GlobalId for entity in support if entity.is_a('IfcRoot'))
    unrelated = sorted(entity.GlobalId for entity in result.by_type('IfcRoot')
                       if entity.GlobalId not in old and entity.GlobalId not in allowed)
    evidence['unrelated_added_roots'] = unrelated
    evidence['passed'] = evidence['passed'] and not unrelated
    evidence['scope'] += '; introduced roots must be occurrence support; unreachable non-root entities not audited'
    return evidence


def _expectations(row, spec, evidence, damaged, reference, policy):
    supplied = policy['targets'].get(row['target_id'], {})
    allowed = {'basis', 'ifc_class', 'width_mm', 'height_mm', 'opening_center_xy_m', 'opening_bottom_world_m',
               'match_center_world_m', 'coarse_match_m', 'host_guid', 'storey_guid', 'reference_guid',
               'opening_width_mm', 'opening_height_mm', 'target_center_offset_from_opening_m', 'target_center_offsets_from_opening_m'}
    if set(supplied) - allowed:
        raise ValueError('UNKNOWN_TARGET_EXPECTATION')
    snapshot = row['target']
    bounds = np.asarray(row['opening'].get('bounds_world_m'), dtype=float)
    if bounds.shape != (3, 2) or not np.isfinite(bounds).all():
        raise ValueError('INVALID_CANDIDATE_OPENING_SNAPSHOT')
    result = {'basis': 'candidate_snapshot_not_approved', 'ifc_class': snapshot['class'],
              'width_mm': snapshot.get('OverallWidth_mm'), 'height_mm': snapshot.get('OverallHeight_mm'),
              'opening_center_xy_m': bounds.mean(axis=1)[:2].tolist(), 'opening_bottom_world_m': float(bounds[2, 0]),
              'match_center_world_m': bounds.mean(axis=1).tolist(), 'coarse_match_m': policy['coarse_match_m'],
              'host_guid': row['wall_guid'], 'storey_guid': None, 'reference_guid': None}
    for edge in row['required_relations']:
        if edge['ifc_class'] == 'IfcRelContainedInSpatialStructure':
            matches = [v for v in evidence.get('required_relation_evidence', ()) if v['id'] == edge['id']]
            if len(matches) != 1 or len(matches[0].get('before', [])) != 1 or not matches[0].get('verified'):
                raise ValueError('MISSING_REQUIRED_EDGE_EVIDENCE:' + edge['id'])
            result['storey_guid'] = matches[0]['before'][0]['parent_guid']
    references = []
    for step in spec.get('source', {}).get('task_proposal', {}).get('retained_reference_step_ids', ()):
        original = reference.by_id(step)
        kept = _by_guid(damaged, original.GlobalId)
        if kept is not None and kept.is_a(snapshot['class']):
            references.append(kept.GlobalId)
    if len(set(references)) == 1:
        result['reference_guid'] = references[0]
    result.update(supplied)
    if result['ifc_class'] != snapshot['class']:
        raise ValueError('TARGET_CLASS_CONTRACT_MISMATCH')
    for key in ('width_mm', 'height_mm', 'coarse_match_m', 'opening_width_mm', 'opening_height_mm'):
        if key not in result: continue
        if type(result[key]) not in (int, float) or not math.isfinite(result[key]) or result[key] <= 0:
            raise ValueError('MISSING_DIMENSION_CONTRACT:' + row['target_id'])
    for key, shape in (('match_center_world_m', (3,)), ('opening_center_xy_m', (2,)),
                       ('target_center_offset_from_opening_m', (3,))):
        if key not in result: continue
        vector = np.asarray(result[key], dtype=float)
        if vector.shape != shape or not np.isfinite(vector).all():
            raise ValueError('INVALID_POSITION_CONTRACT:' + key)
        result[key] = vector.tolist()
    if 'target_center_offsets_from_opening_m' in result:
        offsets = np.asarray(result['target_center_offsets_from_opening_m'], dtype=float)
        if offsets.ndim != 2 or offsets.shape[1] != 3 or not len(offsets) or not np.isfinite(offsets).all():
            raise ValueError('INVALID_POSITION_ALTERNATIVES')
        if 'target_center_offset_from_opening_m' in result:
            raise ValueError('AMBIGUOUS_POSITION_CONTRACT')
        result['target_center_offsets_from_opening_m'] = offsets.tolist()
    if not math.isfinite(result['opening_bottom_world_m']):
        raise ValueError('INVALID_OPENING_BOTTOM')
    required = {'basis', 'ifc_class', 'width_mm', 'height_mm', 'opening_center_xy_m', 'opening_bottom_world_m',
                'match_center_world_m', 'host_guid', 'reference_guid'}
    if result['storey_guid'] is not None:
        required.add('storey_guid')
    result['explicit_contract'] = required.issubset(supplied) and bool(supplied.get('basis'))
    return result


def _aliases(report):
    report['products'] = {'required': report['metrics']['component_completion']['denominator'],
                          'correct': report['metrics']['component_completion']['numerator']}
    report['relations'] = {'required': report['metrics']['relation_completion']['denominator'],
                           'correct': report['metrics']['relation_completion']['numerator']}
    report['repair_success'] = report['metrics']['task_success']['value']
    report['interaction_success'] = report['metrics']['interactive_success']['value']
    return report


def _eligible(spec, policy):
    """Task admission marks do not change when a method fails to submit."""
    review = spec['review']
    authorization = review.get('authorization', {})
    delegated = (review.get('status') == 'accepted_by_delegation' and review.get('kind') == 'delegated_technical'
        and review.get('human_viewed') is False and bool(review.get('reviewer'))
        and isinstance(authorization, dict) and bool(authorization.get('user_quote')) and bool(authorization.get('at'))
        and review.get('technical_review_passed') is True)
    common = {'basis','ifc_class','width_mm','height_mm','opening_center_xy_m','opening_bottom_world_m',
              'match_center_world_m','host_guid','reference_guid'}
    explicit = []
    for row in spec['targets']:
        supplied = policy['targets'].get(row['target_id'], {})
        required = common | ({'storey_guid'} if any(edge['ifc_class'] == 'IfcRelContainedInSpatialStructure'
                                                  for edge in row['required_relations']) else set())
        explicit.append(required.issubset(supplied) and bool(supplied.get('basis'))
            and bool({'target_center_offset_from_opening_m','target_center_offsets_from_opening_m'} & supplied.keys()))
    return bool(policy['frozen'] and (review['status'] == 'accepted' or delegated)
        and spec.get('metrics', {}).get('formal_scoring_frozen') is True and all(explicit))


def _unavailable(report):
    # Keep observations for debugging, but an evaluator failure is not a model
    # score. The original task denominators remain available to every table row.
    report['diagnostic_metrics'] = deepcopy(report['metrics'])
    for name, metric in report['metrics'].items():
        if 'denominator' in metric:
            metric.update(numerator=None, value=None, status='not_evaluable')
        elif name in {'ifc_validation_pass', 'task_success', 'interactive_success'}:
            metric.update(value=None, status='not_evaluable')
    report['preservation'] = {**report['preservation'], 'status':'not_evaluable','passed':None}
    report['metrics']['collateral_changes'] = {'status':'not_evaluable','affected_root_count':None,
        'affected_root_ids':[], 'preservation_pass':None, 'extra_products':None}


def score(case: Path, result_path: Path | None, *, terminal, events=(), policy=None):
    """Score one unique submission; no side effects or implicit task acceptance.

    ``policy.targets`` maps target-1 etc. to explicit class, width_mm/height_mm,
    opening_center_xy_m/opening_bottom_world_m, host/storey/reference GUIDs,
    match_center_world_m and a nonempty provenance ``basis``. Missing fields
    use candidate snapshots only for diagnostics and block confirmed success.
    """
    case = Path(case)
    report = {'schema_version': SCHEMA, 'case_id': case.name, 'terminal': terminal,
              'evidence_class': 'independent_candidate_evaluation', 'formal_eligible': False,
              'status': 'not_evaluable', 'target_results': [], 'relation_details': [],
              'review_required': [], 'errors': [], 'checks': {},
              'preservation': {'status': 'not_evaluable', 'passed': None}, 'metrics': {}}
    try:
        spec, evidence = _task(case)
        effective = _policy(policy)
        report.update(case_id=spec['case_id'], policy=effective)
        report['formal_eligible'] = _eligible(spec,effective)
        den = {'quantity_completion': sum(spec['required_products'].values()),
               'component_completion': spec['required_product_count'], 'relation_completion': spec['required_relation_count']}
        metrics = {name: _metric(None, n, 'not_evaluable') for name, n in den.items()}
        metrics.update({name: _flag(None, 'not_evaluable') for name in ('ifc_validation_pass', 'task_success', 'interactive_success')})
        metrics['collateral_changes'] = {'status':'not_evaluable','affected_root_count':None,
            'affected_root_ids':[], 'preservation_pass':None, 'extra_products':None}
        report['metrics'] = metrics
        answer = read_json(case / 'private/answer-card.json')
        facts = [v['fact_id'] if isinstance(v, dict) else v for v in answer.get('required_user_facts', ())]
        report['clarification'] = clarification_score(facts, events)
        metrics['clarification'] = report['clarification']
        if terminal in {'not_run', 'ready', 'running', 'awaiting_user'}:
            if result_path is not None:
                raise ValueError('INTERMEDIATE_STATE_MUST_NOT_HAVE_SUBMISSION')
            state = 'not_run' if terminal == 'not_run' else 'pending'
            report['status'] = state
            report['preservation']['status'] = state
            metrics['collateral_changes']['status'] = state
            for name, n in den.items(): metrics[name] = _metric(None, n, state)
            for name in ('ifc_validation_pass', 'task_success', 'interactive_success'): metrics[name] = _flag(None, state)
            return _aliases(report)
        if terminal not in TERMINAL:
            raise ValueError('UNKNOWN_TERMINAL')
        if (terminal == 'submitted') != (result_path is not None):
            raise ValueError('TERMINAL_ARTIFACT_MISMATCH')
        for name, n in den.items(): metrics[name] = _metric(0, n)
        for name in ('ifc_validation_pass', 'task_success', 'interactive_success'): metrics[name] = _flag(False)
        report['status'] = 'scored'
        if terminal != 'submitted':
            return _aliases(report)
        damaged_path = case / 'private/mutation/damaged.ifc'
        reference_path = case / 'private/reference.ifc'
        if sha256(damaged_path) != spec['damaged_sha256'] or sha256(reference_path) != spec['source_sha256']:
            raise ValueError('EVALUATOR_INPUT_CHANGED')
        if not Path(result_path).is_file():
            report['checks']['reopen'] = False
            report['artifact_error'] = 'SUBMITTED_FILE_MISSING'
            return _aliases(report)
        report['input_bindings'] = {'damaged_sha256': spec['damaged_sha256'], 'source_sha256': spec['source_sha256'],
                                    'task_sha256':sha256(case/'private/task.json'), 'checks_sha256':sha256(case/'private/checks.json'),
                                    'answer_card_sha256':sha256(case/'private/answer-card.json'),
                                    'result_sha256': sha256(Path(result_path))}
        damaged, reference = ifcopenshell.open(str(damaged_path)), ifcopenshell.open(str(reference_path))
        try:
            with Path(result_path).open('rb') as handle:
                if b'ISO-10303-21;' not in handle.read(4096): raise ValueError('NOT_IFC_SPF')
            result = ifcopenshell.open(str(result_path))
        except (RuntimeError, OSError, ValueError, ifcopenshell.Error) as error:
            report['checks']['reopen'] = False
            report['artifact_error'] = f'{type(error).__name__}: {error}'
            return _aliases(report)
        report['checks'].update(reopen=True, schema=result.schema == damaged.schema == 'IFC2X3')
        try:
            validation = native_validation(result)
            report['native_validation'] = validation
            metrics['ifc_validation_pass'] = _flag(bool(validation['passed'] and report['checks']['schema']))
        except Exception as error:
            report['errors'].append(f'IFC_VALIDATOR:{type(error).__name__}:{error}')
            metrics['ifc_validation_pass'] = _flag(None, 'not_evaluable')
        # Do not return early on failed schema/EXPRESS: independent parts still count.
        old_ids = {p.GlobalId for p in damaged.by_type('IfcProduct')}
        new_products = [p for p in result.by_type('IfcProduct') if p.GlobalId not in old_ids]
        guids = Counter(p.GlobalId for p in result.by_type('IfcRoot'))
        duplicates = sorted(guid for guid, count in guids.items() if count > 1)
        report['duplicate_guids'] = duplicates
        unique_by_id = {p.GlobalId: p for p in new_products if p.GlobalId}
        counts = Counter(p.is_a() for p in unique_by_id.values())
        required = spec['required_products']
        credited = {cls: min(counts[cls], n) for cls, n in required.items()}
        q = _metric(sum(credited.values()), den['quantity_completion'])
        q.update(required_by_class=required, added_by_class={cls: counts[cls] for cls in required}, credited_by_class=credited,
                 excess_by_class={cls: max(0, counts[cls] - n) for cls, n in required.items()})
        metrics['quantity_completion'] = q
        new = [p for p in new_products if guids[p.GlobalId] == 1]
        target_views = []
        for row in spec['targets']:
            expected = _expectations(row, spec, evidence, damaged, reference, effective)
            match = _matching([p for p in new if p.is_a(row['target']['class'])],
                              np.asarray(expected['match_center_world_m']), expected['coarse_match_m'])
            if row['preserve_opening']:
                opening = _by_guid(result, row['opening_guid'])
                support = {'status': 'matched' if opening is not None else 'missing',
                           'guid': row['opening_guid'] if opening is not None else None,
                           'candidates': [row['opening_guid']] if opening is not None else []}
            else:
                support = _matching([p for p in new if p.is_a('IfcOpeningElement')],
                                    np.array([*expected['opening_center_xy_m'], expected['opening_bottom_world_m'] + expected['height_mm'] / 2000]),
                                    expected['coarse_match_m'])
            target_views.append((row, expected, match, support))
        # One occurrence (or supporting opening) cannot earn two target credits.
        for index in (2, 3):
            owners = Counter(view[index]['guid'] for view in target_views if view[index]['guid'])
            for view in target_views:
                if view[index]['guid'] and owners[view[index]['guid']] > 1:
                    view[index].update(status='ambiguous', guid=None)
        correct = unknown = restored = 0
        expected_new_counts = Counter(required)
        expected_new_counts['IfcOpeningElement'] = sum(not row['preserve_opening'] for row in spec['targets'])
        expected_new_counts = +expected_new_counts
        report['checks']['no_extra_products'] = counts == expected_new_counts
        report['checks']['unique_guids'] = not duplicates
        for row, expected, match, support in target_views:
            entry = {'target_id': row['target_id'], 'matching': match, 'opening_matching': support,
                     'expectations': expected, 'checks': {}, 'status': 'failed'}
            report['target_results'].append(entry)
            candidate = _by_guid(result, match['guid']) if match['guid'] else None
            opening = _by_guid(result, support['guid']) if support['guid'] else None
            checks = entry['checks']
            checks['unique_target'] = candidate is not None
            if candidate is not None:
                scale = ifcopenshell.util.unit.calculate_unit_scale(result) * 1000
                checks['target_geometry'] = _bounds(candidate) is not None
                checks['nominal_dimensions'] = all(getattr(candidate, attr, None) is not None and
                    abs(float(getattr(candidate, attr)) * scale - expected[key]) <= effective['length_mm']
                    for attr, key in (('OverallWidth','width_mm'),('OverallHeight','height_mm')))
            opening_bounds = _bounds(opening) if opening is not None else None
            checks['opening_geometry'] = opening_bounds is not None
            if opening_bounds is not None:
                tolerance = effective['length_mm'] / 1000
                checks['opening_position'] = bool(np.all(np.abs(opening_bounds.mean(axis=1)[:2] - expected['opening_center_xy_m']) <= tolerance)
                    and abs(opening_bounds[2, 0] - expected['opening_bottom_world_m']) <= tolerance)
                if 'opening_height_mm' in expected:
                    checks['opening_height'] = abs(float(np.diff(opening_bounds[2])[0]) * 1000 - expected['opening_height_mm']) <= effective['length_mm']
                if 'opening_width_mm' in expected:
                    host_edges = list(opening.VoidsElements)
                    checks['opening_width'] = False
                    if len(host_edges) == 1:
                        host_axes = ifcopenshell.util.placement.get_local_placement(host_edges[0].RelatingBuildingElement.ObjectPlacement)[:3,:3]
                        if np.allclose(host_axes.T @ host_axes,np.eye(3),atol=1e-9):
                            local_vertices = _mesh(opening)[0] @ host_axes
                            measured_width = float(np.ptp(local_vertices[:,0])) * 1000
                            entry['opening_width_evidence'] = {'actual_host_local_x_span_mm':measured_width,
                                'required_mm':expected['opening_width_mm'],'tolerance_mm':effective['length_mm']}
                            checks['opening_width'] = abs(measured_width-expected['opening_width_mm']) <= effective['length_mm']
                candidate_bounds = _bounds(candidate) if candidate is not None else None
                if candidate_bounds is not None:
                    checks['target_at_opening'] = bool(np.all(candidate_bounds[:, 1] >= opening_bounds[:, 0] - tolerance)
                        and np.all(candidate_bounds[:, 0] <= opening_bounds[:, 1] + tolerance))
                    if 'target_center_offset_from_opening_m' in expected or 'target_center_offsets_from_opening_m' in expected:
                        offsets = expected.get('target_center_offsets_from_opening_m', [expected.get('target_center_offset_from_opening_m')])
                        actual_offset = candidate_bounds.mean(axis=1) - opening_bounds.mean(axis=1)
                        errors = [float(np.max(np.abs(actual_offset - offset))) for offset in offsets]
                        entry['position_evidence'] = {'actual_center_offset_world_m':actual_offset.tolist(),
                            'allowed_offsets_world_m':offsets, 'max_axis_errors_m':errors}
                        checks['target_position'] = any(error <= tolerance for error in errors)
                    else:
                        checks['target_position'] = None
                        report['review_required'].append(row['target_id'] + ':exact_target_position_contract')
            fill = list(candidate.FillsVoids) if candidate is not None else []
            void = list(opening.VoidsElements) if opening is not None else []
            containment = list(candidate.ContainedInStructure) if candidate is not None else []
            actual_edges = {
                'IfcRelFillsElement': [(edge.GlobalId,edge.RelatingOpeningElement.GlobalId) for edge in fill],
                'IfcRelVoidsElement': [(edge.GlobalId,edge.RelatingBuildingElement.GlobalId) for edge in void],
                'IfcRelContainedInSpatialStructure': [(edge.GlobalId,edge.RelatingStructure.GlobalId) for edge in containment],
            }
            endpoints = {'IfcRelFillsElement': opening.GlobalId if opening is not None else None,
                         'IfcRelVoidsElement': expected['host_guid'], 'IfcRelContainedInSpatialStructure': expected['storey_guid']}
            relations = {cls: endpoints[cls] is not None and any(parent == endpoints[cls] for _,parent in actual)
                         for cls, actual in actual_edges.items()}
            checks['no_extra_target_relations'] = all(len(actual) == 1 and relations[cls]
                for cls,actual in actual_edges.items() if cls != 'IfcRelContainedInSpatialStructure' or expected['storey_guid'] is not None)
            for edge in row['required_relations']:
                restored += int(relations[edge['ifc_class']])
                report['relation_details'].append({'id': edge['id'], 'target_id': row['target_id'],
                    'ifc_class': edge['ifc_class'], 'restored': relations[edge['ifc_class']],
                    'expected_parent_guid': endpoints[edge['ifc_class']],
                    'actual': [{'relation_guid':guid,'parent_guid':parent} for guid,parent in actual_edges[edge['ifc_class']]],
                    'extra_invalid': [guid for guid,parent in actual_edges[edge['ifc_class']] if parent != endpoints[edge['ifc_class']]],
                    'duplicate': len([parent for _,parent in actual_edges[edge['ifc_class']]]) > len({parent for _,parent in actual_edges[edge['ifc_class']]})})
            checks['relations'] = all(relations[edge['ifc_class']] for edge in row['required_relations'])
            # A retained void is preservation/complete-component evidence, not an extra denominator.
            checks['host'] = relations['IfcRelVoidsElement']
            if candidate is not None and checks.get('target_geometry'):
                kept_reference = _by_guid(damaged, expected['reference_guid']) if expected['reference_guid'] else None
                if kept_reference is None:
                    checks['appearance'] = None
                    report['review_required'].append(row['target_id'] + ':retained_reference_binding')
                else:
                    checks['appearance'] = _appearance(candidate, kept_reference, row['kind'])
                    if checks['appearance'] is None:
                        report['review_required'].append(row['target_id'] + ':appearance_or_equivalent_tessellation')
            else:
                checks['appearance'] = False
            if not expected['explicit_contract']:
                checks['expectation_contract'] = None
                report['review_required'].append(row['target_id'] + ':candidate_expectations_require_review')
            if all(value is True for value in checks.values()):
                entry['status'] = 'passed'
                correct += 1
            elif not any(value is False for value in checks.values()):
                entry['status'] = 'needs_review'
                unknown += 1
        metrics['component_completion'] = _metric(correct, den['component_completion'], 'needs_review' if unknown else 'scored')
        if unknown:
            metrics['component_completion'].update(value=None, confirmed_correct=correct, unknown=unknown)
        metrics['relation_completion'] = _metric(restored, den['relation_completion'])
        try:
            if duplicates:
                report['preservation'] = {'status': 'not_evaluable', 'passed': None, 'reason': 'duplicate GlobalId'}
            else:
                report['preservation'] = {**_preservation_with_additions(damaged, result, list(unique_by_id)), 'status': 'scored'}
        except Exception as error:
            report['errors'].append(f'PRESERVATION:{type(error).__name__}:{error}')
        preservation = report['preservation']
        changed = set(preservation.get('removed_roots', ())) | set(preservation.get('modified_roots', ())) | set(preservation.get('extra_old_object_relations', ())) | set(preservation.get('unrelated_added_roots', ()))
        metrics['collateral_changes'] = {'status': preservation['status'], 'affected_root_count': len(changed) if preservation['passed'] is not None else None,
                                         'affected_root_ids': sorted(changed), 'preservation_pass': preservation['passed'],
                                         'extra_products': not report['checks']['no_extra_products']}
        gates = [metrics['ifc_validation_pass']['value'], preservation['passed'],
                 *report['checks'].values(), correct == den['component_completion'] if not unknown else None,
                 restored == den['relation_completion']]
        success = False if any(v is False for v in gates) else None if any(v is None for v in gates) else True
        if report['errors']:
            report['status'] = 'not_evaluable'
        elif success is None:
            report['status'] = 'needs_review'
        metrics['task_success'] = _flag(success, report['status'])
        metrics['interactive_success'] = _flag(False if report['clarification']['success'] is False or success is False else success, report['status'])
        if report['errors']:
            _unavailable(report)
    except Exception as error:
        report.update(status='not_evaluable', evaluator_error=f'{type(error).__name__}: {error}')
        _unavailable(report)
        for name in ('ifc_validation_pass', 'task_success', 'interactive_success'):
            report['metrics'][name] = _flag(None, 'not_evaluable')
    if 'component_completion' not in report['metrics']:
        # Invalid contracts have no invented denominators.
        return report
    return _aliases(report)
