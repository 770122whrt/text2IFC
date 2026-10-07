"""Compile actual IFC meshes into a dependency-free, private review viewer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
from ifcopenshell.api.root import remove_product

from scripts.ifc_repair.repair_comparison.contracts import sha256, write_json
from scripts.ifc_repair.repair_comparison.inspection import native_validation
from text2ifc_ifc_repair.mutation import _snapshot_owner_history, _restore_owner_history


def collect_meshes(path: Path) -> dict[str, Any]:
    model = ifcopenshell.open(str(path))
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    meshes, errors = {}, []
    for entity in model.by_type('IfcElement'):
        if not entity.Representation:
            continue
        try:
            shape = ifcopenshell.geom.create_shape(settings, entity)
            vertices, faces = list(shape.geometry.verts), list(shape.geometry.faces)
            if not vertices or not faces:
                raise ValueError('empty mesh')
            bounds = [[min(vertices[i::3]), max(vertices[i::3])] for i in range(3)]
            meshes[entity.GlobalId] = {
                'guid': entity.GlobalId, 'class': entity.is_a(), 'name': entity.Name,
                'tag': getattr(entity, 'Tag', None), 'vertices': vertices, 'faces': faces,
                'bounds': bounds,
                'placement': ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement).tolist(),
            }
        except (RuntimeError, ValueError) as error:
            errors.append({'guid': entity.GlobalId, 'class': entity.is_a(), 'error': str(error)})
    return {'meshes': meshes, 'errors': errors, 'coordinates': 'world metres; no per-model recentering'}


def compare_meshes(before: dict, after: dict, guids: list[str]) -> list[dict]:
    rows = []
    for guid in guids:
        a, b = before['meshes'].get(guid), after['meshes'].get(guid)
        same = bool(a and b and all(a[key] == b[key] for key in ('vertices', 'faces', 'placement')))
        rows.append({'guid': guid, 'tag': a.get('tag') if a else None, 'unchanged': same,
                     'bounds_g_m': a['bounds'] if a else None, 'bounds_d_m': b['bounds'] if b else None})
    return rows


def write_review_subsets(package: Path, definition: dict) -> dict:
    """Isolate existing IFC products for an external viewer, privately.

    Keep complete host walls and all their void/fill chains, plus the original
    spatial hierarchy. No geometry, placements, names or contexts are replaced.
    These derived files are inspection aids, never formal inputs or outputs.
    """
    private = package / 'private'
    inputs = {'G': private / 'reference.ifc', 'D': private / 'mutation/damaged.ifc'}
    source_bytes = {side: path.read_bytes() for side, path in inputs.items()}
    original = ifcopenshell.open(str(inputs['G']))
    damage = definition['damage']
    targets = damage if isinstance(damage, list) else [damage]
    selected = {item['target_guid'] for item in targets}
    selected.update(definition['task'].get('reference_guids', []))
    hosts = set()
    for guid in selected.copy():
        try:
            entity = original.by_guid(guid)
        except RuntimeError as error:
            raise ValueError('REVIEW_OBJECT_NOT_FOUND') from error
        if not entity.is_a('IfcProduct'):
            raise ValueError('REVIEW_OBJECT_NOT_FOUND')
        if entity.is_a('IfcWall'):
            hosts.add(entity.GlobalId)
        for relation in getattr(entity, 'FillsVoids', ()):
            opening = relation.RelatingOpeningElement
            selected.add(opening.GlobalId)
            hosts.update(r.RelatingBuildingElement.GlobalId for r in opening.VoidsElements)
        if entity.is_a('IfcOpeningElement'):
            hosts.update(r.RelatingBuildingElement.GlobalId for r in entity.VoidsElements)
    selected.update(hosts)
    for guid in hosts:
        for relation in original.by_guid(guid).HasOpenings:
            opening = relation.RelatedOpeningElement
            selected.add(opening.GlobalId)
            selected.update(r.RelatedBuildingElement.GlobalId for r in opening.HasFillings)
    report = {'purpose': 'private external-viewer inspection only; not formal input or repair',
              'input_bindings': {side: sha256(path) for side, path in inputs.items()},
              'retained_host_guids': sorted(hosts)}
    for side, path in inputs.items():
        model = ifcopenshell.open(str(path))
        owners = _snapshot_owner_history(model)
        for entity in list(model.by_type('IfcProduct')):
            if entity.GlobalId not in selected and not entity.is_a('IfcSpatialStructureElement'):
                remove_product(model, product=entity)
        _restore_owner_history(model, owners)
        output = private / ('review-original.ifc' if side == 'G' else 'review-damaged.ifc')
        model.write(str(output))
        reopened = ifcopenshell.open(str(output))
        validation = native_validation(reopened)
        meshes = collect_meshes(output)
        comparisons = compare_meshes(collect_meshes(path), meshes, list(meshes['meshes']))
        unchanged = not meshes['errors'] and all(row['unchanged'] for row in comparisons)
        report[side] = {'path': output.relative_to(package).as_posix(),
                        'product_count': len(reopened.by_type('IfcProduct')),
                        'geometry_unchanged': unchanged, 'validation': validation}
        if not validation['passed'] or not unchanged:
            raise ValueError('REVIEW_SUBSET_VALIDATION_FAILED')
    report['source_files_unchanged'] = all(path.read_bytes() == source_bytes[side] for side, path in inputs.items())
    if not report['source_files_unchanged']:
        raise ValueError('REVIEW_SOURCE_CHANGED')
    write_json(private / 'review-subsets.json', report)
    return report


def write_viewer(package: Path, definition: dict) -> dict:
    before = collect_meshes(package / 'private/reference.ifc')
    after = collect_meshes(package / 'private/mutation/damaged.ifc')
    damage = definition['damage']
    targets = [t['target_guid'] for t in damage] if isinstance(damage, list) else [damage['target_guid']]
    target = targets[0]
    refs = definition['task'].get('reference_guids', [])
    comparisons = compare_meshes(before, after, refs)
    audit = {
        'purpose': 'private human visual inspection; never export to tested system',
        'removed_target': {k: v for k, v in before['meshes'][target].items() if k not in ('vertices', 'faces')},
        'removed_targets': [{k: v for k, v in before['meshes'][g].items() if k not in ('vertices', 'faces')} for g in targets],
        'removed_target_absent_in_d': all(g not in after['meshes'] for g in targets),
        'reference_geometry_unchanged': all(row['unchanged'] for row in comparisons),
        'references': comparisons,
        'mesh_count': {'G': len(before['meshes']), 'D': len(after['meshes'])},
        'mesh_errors': {'G': before['errors'], 'D': after['errors']},
        'scope': 'Exact world vertex/face and placement comparison of listed references; not an independent IFC validator.',
    }
    checks = json.loads((package / 'private/checks.json').read_text(encoding='utf-8'))
    data = {'title': definition['case_id'] + ' · ' + definition['task']['summary'],
            'floor_z': checks['host']['bounds_world_m'][2][0],
            'target': target, 'targets': targets, 'refs': refs, 'before': before, 'after': after, 'audit': audit}
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    template = Path(__file__).with_name('viewer.html').read_text(encoding='utf-8')
    (package / 'VIEW.html').write_text(template.replace('__IFC_DATA__', payload), encoding='utf-8')
    write_json(package / 'private/visual-inspection.json', audit)
    return audit
