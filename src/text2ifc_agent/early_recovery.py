"""Evidence-derived field recovery; no heuristic choice of IFC semantic values."""
from __future__ import annotations

import re
from collections.abc import Mapping

from text2ifc_contract.validation_v2 import validate_v2_document, _attribute_type_matches
from text2ifc_knowledge.registry import load_ifc2x3_registry

from .authoring_contract import build_authoring_contract
from .candidate_index import CandidateIndexError, build_candidate_index
from .change_scope import derive_change_scope

_FIELD = re.compile(r'^/entities/(\d+)/attributes/([A-Za-z][A-Za-z0-9]*)$')


def build_field_recovery_group(candidate, feedback):
    """Authorize exact scalar fields from independently reproduced validator errors.

    Terminal-s spelling or unique exact enum-value matches offer a bounded rename.
    The Provider must confirm meaning or return Draft; this is not a semantic proof.
    No value substitution, conflicting targets or geometry edits are authorized.
    """
    blocked = {'eligible': False, 'scope': None, 'issues': []}
    if candidate.get('schema_version') != 'bim-json/2.1' or not feedback:
        return blocked
    try:
        build_candidate_index(candidate)
        actual = validate_v2_document(candidate)
    except (CandidateIndexError, KeyError, TypeError, ValueError):
        return blocked
    if {(i.code, i.path) for i in actual} != {(i.get('code'), i.get('path')) for i in feedback}:
        return blocked
    registry = load_ifc2x3_registry()
    resolved, renames = [], {}
    for number, issue in enumerate(actual):
        match = _FIELD.fullmatch(issue.path)
        if match is None:
            return blocked
        entity = candidate['entities'][int(match[1])]
        field = match[2]
        attrs = entity['attributes']
        declaration = registry.entity(entity['ifc_class'])
        try:
            offered = build_authoring_contract([entity['ifc_class']])['classes'][entity['ifc_class']]['attributes']
        except ValueError:
            return blocked
        paths = [field]
        if issue.code == 'INVALID_IFC_ATTRIBUTE_TYPE':
            # Enumerations have a closed legal vocabulary. Arbitrary replacement
            # numbers, strings and missing user facts are not authorized here.
            if 'enum' not in offered.get(field, {}):
                return blocked
        elif issue.code == 'INVALID_IFC_ATTRIBUTE':
            matches = [a for a in declaration['attributes'] if a['name'] in offered
                and a['name'] not in attrs and not a['derived']
                and (field == a['name'] + 's' or field + 's' == a['name'])
                and _attribute_type_matches(attrs[field], a)]
            if not matches and isinstance(attrs[field], str):
                # Closed tokens only: never infer an identity from free text,
                # numerical type compatibility or a fuzzy spelling score.
                matches = [a for a in declaration['attributes'] if not a['derived']
                    and attrs[field] in offered.get(a['name'], {}).get('enum', [])]
            if len(matches) != 1:
                return blocked
            replacement = matches[0]['name']
            if replacement in attrs or '/attributes/' + replacement in renames.get(entity['id'], {}):
                return blocked
            paths.append(replacement)
            renames.setdefault(entity['id'], {})['/attributes/' + replacement] = attrs[field]
        else:
            return blocked
        for key in paths:
            resolved.append({'issue_id': f'field-recovery-{number:04d}-{key}',
                'actual_ref': f"entity:{entity['id']}#/attributes/{key}",
                'expected_fact_ref': 'schema:IFC2X3',
                'evidence': f'{issue.code}: {issue.message}; preserve all unrelated values.'})
    scope = derive_change_scope(candidate=candidate, issues=resolved,
        scope_id='scope-revision-01', base_revision_id='revision-00', traverse_dependencies=False)
    return {'eligible': scope['scope'] is not None, 'scope': scope['scope'],
        'issues': resolved, 'required_field_values': renames}


def semantic_dependency_context(candidate, component_ids):
    """Include Type attachments and every shared occurrence as read-only evidence."""
    index = build_candidate_index(candidate)
    records = {**index['entities'], **index['relationships']}
    selected = set(component_ids)
    # A Type may attach its instances through multiple relations. Expand the
    # read anchors once to the Type, then collect every directly affected user.
    for relation in index['relationships'].values():
        attrs = relation.get('attributes', {})
        if relation.get('ifc_class') == 'IfcRelDefinesByType' and (
            set(attrs.get('RelatedObjects', [])) & selected
        ):
            selected.add(attrs.get('RelatingType'))
    related = set()
    for rid, relation in index['relationships'].items():
        if relation.get('ifc_class') not in {'IfcRelDefinesByType', 'IfcRelDefinesByProperties', 'IfcRelAssociatesMaterial'}:
            continue
        attrs = relation.get('attributes', {})
        refs = set()
        for value in attrs.values():
            if isinstance(value, str) and value in records:
                refs.add(value)
            elif isinstance(value, list):
                refs.update(v for v in value if isinstance(v, str) and v in records)
        if refs & selected or rid in selected:
            related.update(refs | {rid})
    return {key: records[key] for key in sorted(related - set(component_ids))}
