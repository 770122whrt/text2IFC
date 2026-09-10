"""Request-owned permissions for explicit Generation semantic ChangeSets.

This module does not apply a patch or move inherited candidate values. It derives
bounded operations from freshly reproduced diagnostics and frozen request facts.
The same contract constrains model context, scope and atomic application.
"""
from __future__ import annotations

import copy
from collections.abc import Mapping

from .candidate_index import build_candidate_index
from .revisions import hash_json_value, validate_change_scope
from .semantic_requirements import (
    bind_semantic_targets, project_semantic_requirements, unauthorized_candidate_semantics,
)


SEMANTIC_FIELDS = {'materials', 'property_sets', 'appearance', 'template'}


def build_semantic_correction(*, candidate, design_brief, expected_facts, issues):
    index = build_candidate_index(candidate)
    contract = {'schema_version': 'text2ifc/generation-semantic-correction/1.0',
                'candidate_hash': index['candidate_hash'],
                'expected_facts_hash': hash_json_value(expected_facts),
                'source_issue_ids': [], 'edits': {}, 'dependencies': [], 'issues': []}
    if candidate.get('schema_version') != 'bim-json/2.1':
        return contract
    request = project_semantic_requirements(design_brief)
    request['expectations'] = [*expected_facts.get('semantic_expectations', []), *request['expectations']]
    request['issues'].extend(expected_facts.get('semantic_projection_issues', []))
    request['entity_id_contract'] = expected_facts.get('entity_id_contract', {})
    request = bind_semantic_targets(candidate, request)
    expected = request['expectations']
    fresh = {i['path']: i for i in unauthorized_candidate_semantics(candidate, expected)}
    selected = {}
    for issue in issues:
        row = issue.to_dict() if hasattr(issue, 'to_dict') else issue
        path = _collection_path(row.get('actual_ref', ''))
        if path in fresh:
            selected[path] = fresh[path]
            contract['source_issue_ids'].append(row['issue_id'])
    contract['source_issue_ids'] = sorted(set(contract['source_issue_ids']))
    if not selected:
        return contract
    if request['issues']:
        return _block(contract, 'REQUEST_INVALID', 'Frozen semantic targets or values cannot be uniquely projected.')
    # Equal duplicates arise from the two frozen projections. Conflicting ones
    # cannot be resolved by choosing whichever projection happens to come last.
    values = {}
    for item in expected:
        key = (item['entity_id'], item['kind'], item.get('scope', 'effective'), item.get('pset'), item.get('property'))
        if key in values and hash_json_value(values[key]) != hash_json_value(item.get('value')):
            return _block(contract, 'REQUEST_CONFLICT', f'Conflicting frozen values for {key}.')
        values[key] = item.get('value')
    entities, relationships = index['entities'], index['relationships']
    edits = contract['edits']
    removed_types = {path.split('/')[2] for path, i in selected.items() if i['code'] == 'UNREQUESTED_TYPE'}
    requested_pairs = {(e['entity_id'], e['value']) for e in expected if e['kind'] == 'type'}
    affected = set()

    for identity in sorted(removed_types):
        if any(e['entity_id'] == identity for e in expected):
            return _block(contract, 'REQUEST_CONFLICT', f'Removing {identity} would erase an explicitly requested semantic target.')
        edits[identity] = {'op': 'remove_entity'}
        for reference_id, row in {**entities, **relationships}.items():
            if reference_id == identity or not _contains_id(row.get('attributes'), identity):
                continue
            attrs = row.get('attributes', {})
            if (row['ifc_class'] != 'IfcRelDefinesByType' or attrs.get('RelatingType') != identity
                    or identity in attrs.get('RelatedObjects', [])):
                return _block(contract, 'UNKNOWN_REFERENCE', f'{reference_id} references {identity} outside the supported Type membership graph.')
            edits[reference_id] = {'op': 'remove_relationship'}
            contract['dependencies'].append(_dependency(identity, reference_id,
                'Unrequested Type removal requires explicit removal of its membership relationship.'))
            affected.update(attrs.get('RelatedObjects', []))

    for path, issue in selected.items():
        parts = path.split('/')
        identity = parts[2]
        if identity in edits and edits[identity]['op'].startswith('remove_'):
            continue
        if issue['code'] == 'UNREQUESTED_TYPE_ASSIGNMENT':
            attrs = relationships[identity]['attributes']
            members = attrs.get('RelatedObjects', [])
            if len(members) != len(set(members)) or any(m not in entities for m in members):
                return _block(contract, 'MEMBERSHIP_AMBIGUOUS', f'{identity} does not contain distinct, existing instances.')
            kept = [m for m in members if (m, attrs.get('RelatingType')) in requested_pairs]
            affected.update(set(members) - set(kept))
            edits[identity] = ({'op': 'update_relationship', 'changes': {'/attributes/RelatedObjects': kept}}
                               if kept else {'op': 'remove_relationship'})
        elif issue['code'] == 'UNREQUESTED_MATERIAL':
            _set_edit(edits, identity, '/materials', [])
        elif issue['code'] == 'UNREQUESTED_APPEARANCE':
            edits.setdefault(identity, {'op': 'update_entity'}).setdefault('remove_paths', []).append('/appearance')
            contract['schema_version'] = 'text2ifc/generation-semantic-correction/1.1'
        elif issue['code'] == 'UNREQUESTED_PROPERTY':
            properties = edits.get(identity, {}).get('changes', {}).get('/property_sets')
            if properties is None:
                properties = copy.deepcopy(entities[identity].get('property_sets', {}))
            pset, prop = [_unescape(t) for t in parts[4:6]]
            properties[pset].pop(prop)
            if not properties[pset]:
                properties.pop(pset)
            _set_edit(edits, identity, '/property_sets', properties)

    # A semantic edit on a retained Type can also remove effective values from
    # its instances. Only the request, never the deleted Type, supplies values.
    for row in relationships.values():
        if row['ifc_class'] == 'IfcRelDefinesByType' and row['attributes'].get('RelatingType') in edits:
            affected.update(row['attributes'].get('RelatedObjects', []))
    for identity in sorted(affected):
        if identity not in entities:
            return _block(contract, 'MEMBERSHIP_AMBIGUOUS', f'Unknown instance {identity}.')
        remaining = [r for rid, r in relationships.items() if r['ifc_class'] == 'IfcRelDefinesByType'
                     and edits.get(rid, {}).get('op') != 'remove_relationship'
                     and identity in edits.get(rid, {}).get('changes', {}).get('/attributes/RelatedObjects', r['attributes'].get('RelatedObjects', []))]
        if len(remaining) > 1:
            return _block(contract, 'MEMBERSHIP_AMBIGUOUS', f'Multiple effective Types for {identity}.')
        requirements = [e for e in expected if e['entity_id'] == identity and e['kind'] in {'material', 'property'}]
        if not remaining:
            detached_values = {}
            for item in requirements:
                key = (item['kind'], item.get('pset'), item.get('property'))
                value_hash = hash_json_value(item['value'])
                if key in detached_values and detached_values[key] != value_hash:
                    return _block(contract, 'REQUEST_CONFLICT', f'{identity} has conflicting direct/effective values after detachment.')
                detached_values[key] = value_hash
        for item in requirements:
            row = entities[identity]
            pointer = '/materials' if item['kind'] == 'material' else '/property_sets'
            current = copy.deepcopy(edits.get(identity, {}).get('changes', {}).get(pointer, row.get(pointer[1:], [] if pointer == '/materials' else {})))
            actual = _semantic_value(current, item)
            inherited = None
            if remaining:
                type_id = remaining[0]['attributes'].get('RelatingType')
                if type_id not in entities:
                    return _block(contract, 'MEMBERSHIP_AMBIGUOUS', f'Unknown retained Type for {identity}.')
                type_field = edits.get(type_id, {}).get('changes', {}).get(pointer, entities[type_id].get(pointer[1:], [] if pointer == '/materials' else {}))
                inherited = _semantic_value(type_field, item)
            if item.get('scope') == 'inherited':
                if hash_json_value(inherited) == hash_json_value(item['value']):
                    continue
                # A new direct attachment would silently change the user's
                # explicit scope. Leave this conflict for clarification.
                return _block(contract, 'INHERITED_SCOPE', f'{identity} requires inherited semantics; direct reattachment is not authorized.')
            effective = inherited if actual is None and item.get('scope', 'effective') == 'effective' else actual
            if hash_json_value(effective) == hash_json_value(item['value']):
                continue
            desired = [item['value']] if item['kind'] == 'material' else copy.deepcopy(current)
            if item['kind'] == 'property':
                desired.setdefault(item['pset'], {})[item['property']] = item['value']
            if hash_json_value(desired) != hash_json_value(current):
                # Preserving an existing requested Type's effective values must
                # not quietly turn them into direct overrides.
                if remaining and item.get('scope', 'effective') == 'effective':
                    return _block(contract, 'INHERITED_SCOPE', f'{identity} retains a Type; resolve effective semantics without guessing an override.')
                _set_edit(edits, identity, pointer, desired)
                for rid, relation in relationships.items():
                    if relation['ifc_class'] == 'IfcRelDefinesByType' and rid in edits and identity in relation['attributes'].get('RelatedObjects', []):
                        dependency = _dependency(rid, identity,
                            'Membership cleanup requires preserving this instance value from the frozen request.')
                        if dependency not in contract['dependencies']:
                            contract['dependencies'].append(dependency)
    contract['request_hash'] = hash_json_value(expected)
    return contract


def extend_semantic_scope(*, candidate, scope, correction, scope_id, base_revision_id):
    """Add only proven operations; no geometry dependency traversal from Types."""
    index = build_candidate_index(candidate)
    scope = copy.deepcopy(scope or {'schema_version': 'text2ifc/change-scope/1.0',
        'scope_id': scope_id, 'base_revision_id': base_revision_id, 'source_issue_ids': [],
        'entity_ids': [], 'relationship_ids': [], 'allowed_paths': {}, 'dependencies': [], 'forbidden_ids': []})
    scope['source_issue_ids'] = sorted(set(scope['source_issue_ids']) | set(correction['source_issue_ids']))
    scope['dependencies'].extend(correction['dependencies'])
    for identity, edit in correction['edits'].items():
        kind = 'entity_ids' if identity in index['entities'] else 'relationship_ids'
        scope[kind] = sorted(set(scope[kind]) | {identity})
        # Scope 1.0 has no operation vocabulary. /attributes is a location,
        # not permission to remove: the separate bound contract enforces that.
        paths = [*edit.get('changes', {}), *edit.get('remove_paths', [])] or ['/attributes']
        scope['allowed_paths'][identity] = sorted(set(scope['allowed_paths'].get(identity, [])) | set(paths))
    scope['forbidden_ids'] = sorted(set(index['component_hashes']) - set(scope['entity_ids']) - set(scope['relationship_ids']))
    errors = validate_change_scope(scope)
    if errors:
        raise ValueError(f'Invalid semantic scope: {errors}')
    return scope


def validate_semantic_application(*, candidate, composed, expected_facts, correction):
    if (correction['candidate_hash'] != build_candidate_index(candidate)['candidate_hash']
            or correction['expected_facts_hash'] != hash_json_value(expected_facts)):
        return [_issue('STALE', 'Semantic correction is not bound to this candidate and request.')]
    after = build_candidate_index(composed)
    records = {**after['entities'], **after['relationships']}
    errors = []
    for identity, edit in correction['edits'].items():
        record = records.get(identity)
        if edit['op'].startswith('remove_'):
            if record is not None:
                errors.append(_issue('INCOMPLETE', f'{identity} and its explicit dependencies must be removed together.'))
        elif record is None or any(hash_json_value(_read_pointer(record, p)) != hash_json_value(value) for p, value in edit.get('changes', {}).items()):
            errors.append(_issue('VALUE_MISMATCH', f'{identity} must preserve the exact request-owned correction values.'))
        elif any(p.lstrip('/') in record for p in edit.get('remove_paths', [])):
            errors.append(_issue('VALUE_MISMATCH', f'{identity} must omit the unauthorized optional override, not replace it with null or an empty value.'))
    return errors


def protected_semantic_removal(record, permitted_paths):
    from text2ifc_knowledge.registry import load_ifc2x3_registry
    declaration = load_ifc2x3_registry().declaration(record.get('ifc_class', ''))
    is_type = declaration and (record['ifc_class'] == 'IfcTypeObject' or 'IfcTypeObject' in declaration.get('supertypes', []))
    return (is_type or record.get('ifc_class') == 'IfcRelDefinesByType'
            or (permitted_paths and all(p.split('/')[1] in SEMANTIC_FIELDS for p in permitted_paths)))


def _collection_path(reference):
    if not isinstance(reference, str):
        return ''
    if reference.startswith(('entity:', 'relationship:')) and '#' in reference:
        kind, rest = reference.split(':', 1)
        identity, pointer = rest.split('#', 1)
        return f"/{'entities' if kind == 'entity' else 'relationships'}/{identity}{pointer}"
    return reference


def _set_edit(edits, identity, pointer, value):
    edits.setdefault(identity, {'op': 'update_entity'}).setdefault('changes', {})[pointer] = copy.deepcopy(value)


def _semantic_value(field, expectation):
    if expectation['kind'] == 'material':
        return field[0] if isinstance(field, list) and len(field) == 1 else None
    return field.get(expectation['pset'], {}).get(expectation['property']) if isinstance(field, Mapping) else None


def _contains_id(value, identity):
    if isinstance(value, str):
        return value == identity
    if isinstance(value, Mapping):
        return any(_contains_id(v, identity) for v in value.values())
    if isinstance(value, list):
        return any(_contains_id(v, identity) for v in value)
    return False


def _unescape(token):
    return token.replace('~1', '/').replace('~0', '~')


def _read_pointer(record, pointer):
    value = record
    for token in pointer.lstrip('/').split('/'):
        if not isinstance(value, Mapping) or _unescape(token) not in value:
            return None
        value = value[_unescape(token)]
    return value


def _issue(code, message):
    return {'code': 'SEMANTIC_CORRECTION_' + code, 'path': '/semantic_correction', 'message': message}


def _dependency(target, dependency, reason):
    return {'target_id': target, 'dependency_id': dependency,
            'relationship_type': 'IfcRelDefinesByType', 'reason': reason}


def _block(contract, code, message):
    contract['issues'].append(_issue(code, message))
    return contract
