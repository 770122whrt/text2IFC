"""Task-local authoring context; full frozen request artifacts remain authoritative."""
from __future__ import annotations

from .authoring_contract import build_authoring_contract
from .candidate_index import build_candidate_index
from .early_recovery import semantic_dependency_context


def select_changeset_context(*, candidate, scope, field_recovery=False, package=None):
    index = build_candidate_index(candidate)
    records = {**index['entities'], **index['relationships']}
    selected = set(scope.get('entity_ids', [])) | set(scope.get('relationship_ids', []))
    readable = set((package or {}).get('allowed_reference_ids', []))
    readable.update(semantic_dependency_context(candidate, selected))
    # Follow explicit IDs in records (placement parents and relation endpoints),
    # never infer a target from a name or turn a read dependency into permission.
    def references(value):
        if isinstance(value, str):
            return {value} if value in records else set()
        if isinstance(value, dict):
            return set().union(*(references(v) for v in value.values())) if value else set()
        if isinstance(value, list):
            return set().union(*(references(v) for v in value)) if value else set()
        return set()
    pending = set(selected | readable)
    visited = set()
    while pending:
        key = pending.pop()
        if key in visited or key not in records:
            continue
        visited.add(key)
        refs = references(records[key].get('attributes', {})) - visited
        readable.update(refs)
        pending.update(refs)
    read_only = {key: records[key] for key in sorted(readable - selected) if key in records}
    classes = {records[k]['ifc_class'] for k in selected | set(read_only) if k in records}
    names = ['changeset-single-component.json']
    if package:
        # Incomplete class declarations must retain the full registry, rather
        # than silently omitting a needed class for a newly generated component.
        declared = package.get('owned_component_classes', {})
        complete = set(package.get('owned_component_ids', [])) <= set(declared)
        classes.update(declared.values())
        if package.get('owned_relationship_ids'):
            complete = False
        if not complete:
            classes = None
        names = ['changeset-staged-package-add.json']
        if package['kind'] == 'cross_storey':
            names += ['changeset-staged-cross-storey.json', 'changeset-staged-negative-y-stair.json']
        elif package['kind'] == 'storey_local':
            names += ['changeset-staged-door-opening.json', 'changeset-staged-orthogonal-walls.json']
            if not complete or 'IfcRailing' in classes:
                names.append('changeset-staged-linear-railing.json')
    elif not field_recovery and (scope.get('relationship_ids') or read_only):
        names.append('changeset-coupled-dependency.json')
    return {'schema_version':'text2ifc/changeset-context-selection/1.0',
        'few_shot_names':names, 'authoring_contract':build_authoring_contract(classes),
        'read_only_components':read_only}
