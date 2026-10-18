"""Independent development scorer for the two reviewed-format simple tasks.

No ChangeSet, application record or B evaluation is an input. This module is
evaluation-side only. Geometry equivalence beyond the mesh witness below is
reported for review, never silently failed or accepted. Formal rules are not
frozen and this is not four-arm admission or a model capability score.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit
from ifcopenshell.api.root import remove_product
import numpy as np

from text2ifc_ifc_repair.compare import normalized_model_diff
from .contracts import read_json, sha256
from .inspection import geometry_snapshot, native_validation
from .ledger import TERMINAL


def clarification_score(required, events):
    required = set(required)
    asked, answered = set(), set()
    for event in events:
        if event['kind'] == 'answer':
            payload = event['payload']
            requested = set(payload.get('requested_fact_ids', []))
            asked.update(requested)
            answered.update(requested.intersection(payload.get('answered_fact_ids', [])))
    return {'status': 'scored' if required else 'not_applicable', 'required': sorted(required),
            'asked': sorted(asked), 'answered': sorted(answered), 'success': required.issubset(asked & answered) if required else None}


def _bounds(entity):
    snap = geometry_snapshot(entity)
    return np.array(snap['bounds_world_m']) if snap['geometry_status'] == 'available' else None


def _center(entity):
    bounds = _bounds(entity)
    if bounds is not None:
        return bounds.mean(axis=1)
    placement = ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement)
    return np.array(placement[:3, 3]) * ifcopenshell.util.unit.calculate_unit_scale(entity.file)


def _mesh(entity):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    shape = ifcopenshell.geom.create_shape(settings, entity)
    vertices = np.array(shape.geometry.verts).reshape(-1, 3)
    faces = np.array(shape.geometry.faces).reshape(-1, 3)
    if not len(vertices) or not len(faces):
        raise ValueError('EMPTY_MESH')
    styles = []
    for material in shape.geometry.materials:
        diffuse = material.diffuse
        styles.append((round(diffuse.r(), 5), round(diffuse.g(), 5), round(diffuse.b(), 5), round(material.transparency, 5)))
    return vertices, faces, styles, list(shape.geometry.material_ids)


def _mesh_signature(mesh, signs=(1, 1, 1)):
    vertices, faces, styles, material_ids = mesh
    center = (vertices.min(axis=0) + vertices.max(axis=0)) / 2
    vertices = np.round((vertices - center) * signs, 6)
    triangles = []
    for index, face in enumerate(faces):
        material = material_ids[index]
        style = styles[material] if 0 <= material < len(styles) else None
        triangles.append((tuple(sorted(tuple(vertices[i]) for i in face)), style))
    return Counter(triangles)


def _appearance(candidate, reference, kind):
    # Exact triangulated surface witness ignores STEP IDs, entity trees and mesh
    # vertex numbering. A different tessellation needs independent review.
    wanted = _mesh_signature(_mesh(reference))
    actual = _mesh(candidate)
    signs = [(1, 1, 1)] if kind == 'window' else [(1, 1, 1), (-1, -1, 1), (-1, 1, 1), (1, -1, 1)]
    return True if any(_mesh_signature(actual, sign) == wanted for sign in signs) else None


def _preservation(damaged, result, new_products):
    # Subtract only newly created products in an evaluator-owned in-memory copy.
    # Inverse membership updates are normalized by the IFC library. The host's
    # intrinsic geometry/properties are never waived merely because it is a host.
    stripped = ifcopenshell.file.from_string(result.to_string())
    for guid in new_products:
        try:
            entity = stripped.by_guid(guid)
        except RuntimeError:
            continue
        remove_product(stripped, product=entity)
    baseline = ifcopenshell.file.from_string(damaged.to_string())
    # Ownership timestamps may change during legitimate editing or subtraction;
    # they are not a requested preservation property of either development task.
    history = baseline.by_type('IfcOwnerHistory')[0]
    for model in (baseline, stripped):
        normalized_history = model.add(history)
        for root in model.by_type('IfcRoot'):
            root.OwnerHistory = normalized_history
    diff = normalized_model_diff(baseline, stripped)
    old_ids = {p.GlobalId for p in damaged.by_type('IfcProduct')}
    extra_relations = []
    for row in diff['created']:
        entity = stripped.by_guid(row['global_id'])
        if entity.is_a('IfcRelationship'):
            references = [v for value in entity for v in (value if isinstance(value, tuple) else (value,)) if hasattr(v, 'GlobalId')]
            if any(v.GlobalId in old_ids for v in references):
                extra_relations.append(row['global_id'])
    return {'passed': not diff['removed'] and not diff['modified'] and not extra_relations,
            'removed_roots': [r['global_id'] for r in diff['removed']],
            'modified_roots': [r['global_id'] for r in diff['modified']], 'extra_old_object_relations': extra_relations,
            'scope': 'unchanged existing roots after subtracting new products; no whole-host waiver'}


def score(case: Path, result_path: Path | None, *, terminal, events=()):
    """Use frozen D + explicit R/terminal + private pre-run task conditions."""
    case = Path(case)
    spec = read_json(case / 'private/task.json')
    definition = spec['definition']
    task, kind = definition['task'], definition['damage']['kind']
    if (kind not in {'window', 'door'} or spec['required_product_count'] != 1
            or spec['required_relation_count'] != (3 if kind == 'window' else 2)
            or task['required_products'] != {'IfcWindow' if kind == 'window' else 'IfcDoor': 1}):
        raise ValueError('SCORER_ONLY_SUPPORTS_CURRENT_SINGLE_TARGET_DEVELOPMENT_TASKS')
    required_facts = definition['clarification']['required_user_facts']
    fact_ids = [v['fact_id'] if isinstance(v, dict) else v for v in required_facts]
    report = {'case_id': spec['case_id'], 'rule_version': 'development-simple-0.1',
              'evidence_class': 'offline_development_evaluation', 'formal_eligible': False,
              'status': 'scored', 'terminal': terminal, 'repair_success': False, 'interaction_success': False,
              'products': {'required': spec['required_product_count'], 'correct': 0},
              'relations': {'required': spec['required_relation_count'], 'correct': 0},
              'clarification': clarification_score(fact_ids, events), 'checks': {}, 'review_required': []}
    if terminal in {'ready', 'running', 'awaiting_user'}:
        report.update(status='pending', repair_success=None, interaction_success=None)
        return report
    if terminal not in TERMINAL:
        raise ValueError('UNKNOWN_TERMINAL')
    if terminal != 'submitted':
        if result_path is not None:
            raise ValueError('NON_SUBMISSION_MUST_NOT_HAVE_ARTIFACT')
        return report
    if result_path is None:
        raise ValueError('SUBMITTED_ARTIFACT_REQUIRED')
    damaged_path = case / 'private/mutation/damaged.ifc'
    reference_path = case / 'private/reference.ifc'
    try:
        if sha256(damaged_path) != spec['damaged_sha256'] or sha256(reference_path) != spec['source_sha256']:
            raise ValueError('EVALUATOR_INPUT_CHANGED')
        damaged = ifcopenshell.open(str(damaged_path))
        reference = ifcopenshell.open(str(reference_path))
        try:
            with Path(result_path).open('rb') as handle:
                if b'ISO-10303-21;' not in handle.read(4096):
                    raise ValueError('NOT_IFC_SPF')
            result = ifcopenshell.open(str(result_path))
        except (RuntimeError, OSError, ValueError, ifcopenshell.Error) as error:
            report['checks']['reopen'] = False
            report['artifact_error'] = f'{type(error).__name__}: {error}'
            return report
        checks = report['checks']
        checks['reopen'] = True
        checks['schema'] = damaged.schema == result.schema
        validation = native_validation(result)
        report['native_validation'] = validation
        checks['native_schema_express'] = validation['passed']
        if not validation['passed']:
            return report
        old_ids = {p.GlobalId for p in damaged.by_type('IfcProduct')}
        new = [p for p in result.by_type('IfcProduct') if p.GlobalId not in old_ids]
        target_class = 'IfcWindow' if kind == 'window' else 'IfcDoor'
        targets = [p for p in new if p.is_a(target_class)]
        original = reference.by_guid(definition['damage']['target_guid'])
        expected_opening = original.FillsVoids[0].RelatingOpeningElement
        expected_host = expected_opening.VoidsElements[0].RelatingBuildingElement
        expected_storey = original.ContainedInStructure[0].RelatingStructure.GlobalId
        expected_center = _center(expected_opening)
        # Matching uses only class and coarse position, never dimensions/relations.
        matches = [p for p in targets if np.max(np.abs(_center(p) - expected_center)) <= .5]
        report['match_candidates'] = [p.GlobalId for p in matches]
        checks['unique_target'] = len(matches) == 1
        checks['quantity'] = len(targets) == 1
        expected_counts = {target_class: 1, **({'IfcOpeningElement': 1} if kind == 'window' else {})}
        checks['no_extra_products'] = dict(Counter(p.is_a() for p in new)) == expected_counts
        report['preservation'] = _preservation(damaged, result, [p.GlobalId for p in new])
        checks['preservation'] = report['preservation']['passed']
        if len(matches) == 1:
            candidate = matches[0]
            bounds = _bounds(candidate)
            checks['target_geometry'] = bounds is not None
            scale = ifcopenshell.util.unit.calculate_unit_scale(result) * 1000
            expected_scale = ifcopenshell.util.unit.calculate_unit_scale(reference) * 1000
            tolerance = task['tolerances']['length_mm']
            checks['nominal_dimensions'] = all(getattr(candidate, k, None) is not None and abs(getattr(candidate, k) * scale - getattr(original, k) * expected_scale) <= tolerance for k in ('OverallWidth', 'OverallHeight'))
            # Position bound is separate from the coarse match; opening is checked
            # geometrically as well as by its host identity after matching.
            expected_bounds = _bounds(original)
            checks['position'] = bounds is not None and bool(np.all(np.abs(bounds - expected_bounds) <= tolerance / 1000))
            fills = list(candidate.FillsVoids)
            opening = fills[0].RelatingOpeningElement if len(fills) == 1 else None
            fill_ok = opening is not None and (kind == 'window' or opening.GlobalId == expected_opening.GlobalId)
            if opening:
                opening_bounds = _bounds(opening)
                checks['opening_geometry'] = opening_bounds is not None and bool(np.all(np.abs(opening_bounds - _bounds(expected_opening)) <= tolerance / 1000))
                voids = list(opening.VoidsElements)
                host_ok = len(voids) == 1 and voids[0].RelatingBuildingElement.GlobalId == expected_host.GlobalId
            else:
                checks['opening_geometry'], host_ok = False, False
            containment_ok = len(candidate.ContainedInStructure) == 1 and candidate.ContainedInStructure[0].RelatingStructure.GlobalId == expected_storey
            relation_checks = {'opening_fill': fill_ok, 'storey_containment': containment_ok, 'host_void': host_ok}
            report['relations']['details'] = {row['id']: relation_checks[row['id']] for row in task['required_relations']}
            report['relations']['correct'] = sum(report['relations']['details'].values())
            checks['relations'] = all(report['relations']['details'].values()) and host_ok
            reference_guid = task['reference_guids'][0 if kind == 'window' else 1]
            if bounds is not None:
                appearance = _appearance(candidate, damaged.by_guid(reference_guid), kind)
                checks['appearance'] = appearance
                if appearance is None:
                    report['review_required'].append('appearance_or_equivalent_tessellation')
            else:
                checks['appearance'] = False
            component_keys = ('target_geometry', 'nominal_dimensions', 'position', 'opening_geometry', 'relations', 'appearance')
            report['products']['correct'] = int(all(checks[k] is True for k in component_keys))
        if report['review_required'] and not any(v is False for v in checks.values()):
            report.update(status='needs_review', repair_success=None)
        else:
            report['repair_success'] = bool(checks) and all(v is True for v in checks.values())
        report['interaction_success'] = report['repair_success'] and report['clarification']['success'] is not False
    except Exception as error:
        report.update(status='not_evaluable', repair_success=None, interaction_success=None, evaluator_error=f'{type(error).__name__}: {error}')
    return report
