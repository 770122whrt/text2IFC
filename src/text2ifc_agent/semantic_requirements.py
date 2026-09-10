"""Request-owned semantic expectations, projected before candidate generation.

No IFC/candidate facts are used to manufacture the requested values. Canonical
requirements use stable entity IDs, exactly like the geometry expected facts.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


SEMANTIC_FIELDS = {'material', 'materials', 'property_sets', 'type_id', 'appearance', 'template'}


def generation_schema_version(brief: Mapping[str, Any]) -> str:
    known = brief.get('known_facts', {})
    if brief.get('schema_version') == 'text2ifc/design-brief/2.1' or (
        isinstance(known, Mapping) and known.get('semantic_requirements')
    ):
        return 'bim-json/2.1'
    return 'bim-json/2.0'


def project_semantic_requirements(brief: Mapping[str, Any]) -> dict[str, Any]:
    known = brief.get('known_facts', {})
    expectations: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    records: list[tuple[str, Mapping[str, Any]]] = []

    def walk(value, path):
        if isinstance(value, Mapping):
            if path != '/known_facts' and SEMANTIC_FIELDS.intersection(value):
                records.append((path, value))
                return
            for key, child in value.items():
                if path == '/known_facts' and key == 'appearance':
                    continue
                walk(child, f'{path}/{key}')
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f'{path}/{index}')

    walk(known, '/known_facts')
    for path, record in records:
        entity_id = record.get('entity_id') or record.get('id')
        if not isinstance(entity_id, str) or not entity_id:
            issues.append({'code': 'SEMANTIC_TARGET_REQUIRED', 'path': path,
                           'message': '语义请求缺少稳定构件身份，需澄清作用对象。'})
            continue
        scope = record.get('scope', 'effective')
        if scope not in {'direct', 'effective', 'inherited'}:
            issues.append({'code': 'SEMANTIC_SCOPE_INVALID', 'path': path, 'message': '无效语义作用域。'})
            continue
        base = {'entity_id': entity_id, 'scope': scope, 'source_path': path}
        if 'material' in record or 'materials' in record:
            material = record.get('material')
            if material is None:
                assignments = record.get('materials')
                material = assignments[0] if isinstance(assignments, list) and len(assignments) == 1 else None
            if not isinstance(material, Mapping):
                issues.append({'code': 'SEMANTIC_MATERIAL_INCOMPLETE', 'path': path,
                               'message': '材料需明确单材料或完整层构造，不得丢弃或猜测。'})
            else:
                expectations.append({**base, 'kind': 'material', 'value': copy.deepcopy(dict(material))})
        property_sets = record.get('property_sets', {})
        if not isinstance(property_sets, Mapping):
            issues.append({'code': 'SEMANTIC_PROPERTY_INCOMPLETE', 'path': path, 'message': '属性集合需为对象。'})
            property_sets = {}
        for pset, values in property_sets.items():
            if not isinstance(values, Mapping):
                issues.append({'code': 'SEMANTIC_PROPERTY_INCOMPLETE', 'path': path, 'message': '属性需明确值。'})
                continue
            for name, value in values.items():
                if value is None:
                    issues.append({'code': 'SEMANTIC_PROPERTY_INCOMPLETE', 'path': path,
                                   'message': '明确请求的属性缺少值；不写 null 占位。'})
                else:
                    expectations.append({**base, 'kind': 'property', 'pset': pset,
                                         'property': name, 'value': copy.deepcopy(value)})
        for field, kind in [('type_id', 'type'), ('appearance', 'appearance'), ('template', 'template')]:
            if field in record:
                expectations.append({**base, 'kind': kind, 'value': copy.deepcopy(record[field])})
    encoded = json.dumps(expectations, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return {'schema_version': 'text2ifc/request-semantics/1.0', 'expectations': expectations,
            'issues': issues, 'valid': not issues, 'expectations_hash': hashlib.sha256(encoded).hexdigest()}


def request_semantics_for_case(root: Path) -> dict[str, Any]:
    from .run_report import resolve_final_design_brief_dir
    paths = [resolve_final_design_brief_dir(root) / 'design-brief.json', root / 'design-brief.json']
    brief = next((json.loads(p.read_text(encoding='utf-8')) for p in paths if p.is_file()), {})
    projected = project_semantic_requirements(brief)
    projected['minimum_schema_version'] = 'bim-json/2.1' if brief.get('schema_version') == 'text2ifc/design-brief/2.1' else None
    projected['appearance_requests'] = [brief['known_facts']['appearance']] if isinstance(brief.get('known_facts', {}).get('appearance'), Mapping) else []
    frozen_path = root / 'expected-facts.json'
    if frozen_path.is_file():
        frozen = json.loads(frozen_path.read_text(encoding='utf-8'))
        projected['entity_id_contract'] = copy.deepcopy(frozen.get('entity_id_contract', {}))
        if 'semantic_expectations' in frozen:
            # Both request projections constrain output. A changed Brief cannot
            # weaken a saved expectation during resume or final acceptance.
            projected['expectations'] = [*frozen['semantic_expectations'], *projected['expectations']]
        projected['issues'].extend(frozen.get('semantic_projection_issues', []))
        if frozen.get('generation_schema_version') == 'bim-json/2.1':
            projected['minimum_schema_version'] = 'bim-json/2.1'
        if isinstance(frozen.get('appearance'), Mapping):
            projected['appearance_requests'].append(frozen['appearance'])
    projected['valid'] = not projected['issues']
    encoded = json.dumps(projected['expectations'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    projected['expectations_hash'] = hashlib.sha256(encoded).hexdigest()
    return projected


def bind_semantic_targets(candidate, request):
    """Resolve only frozen identity aliases; never infer requested values.

    Geometry permits both the Brief ID and its deterministic canonical ID.
    Semantic checks must use the same pair, while refusing collisions across
    instances or storeys. Saved expectations remain byte-for-byte untouched.
    """
    bound = copy.deepcopy(request)
    families = {'walls': {'IfcWall', 'IfcWallStandardCase'}, 'spaces': {'IfcSpace'},
                'doors': {'IfcDoor'}, 'windows': {'IfcWindow'}}
    records = [(item, families[group])
               for group, items in request.get('entity_id_contract', {}).items()
               if group in families for item in items]
    for expectation in bound['expectations']:
        identity = expectation['entity_id']
        matches = [(item, family) for item, family in records
                   if identity in {item.get('brief_id'), item.get('entity_id')}]
        if not matches:
            continue
        aliases = {value for item, _ in matches
                   for value in (item.get('brief_id'), item.get('entity_id')) if value}
        targets = [e for e in candidate.get('entities', []) if e.get('id') in aliases]
        # A bare Brief ID repeated on multiple storeys cannot select one merely
        # because another storey's candidate happens to be missing.
        canonical = {(item.get('entity_id'), item.get('storey')) for item, _ in matches}
        if len(canonical) != 1 or len(targets) != 1:
            bound['issues'].append({'code': 'SEMANTIC_TARGET_BINDING_AMBIGUOUS',
                                    'path': expectation.get('source_path', '/semantic_expectations'),
                                    'message': '冻结身份映射没有唯一候选构件，不能猜测语义作用对象。'})
            continue
        if targets[0].get('ifc_class') not in matches[0][1]:
            bound['issues'].append({'code': 'SEMANTIC_TARGET_FAMILY_MISMATCH',
                                    'path': expectation.get('source_path', '/semantic_expectations'),
                                    'message': '候选构件类别与冻结身份映射不兼容。'})
            continue
        expectation['entity_id'] = targets[0]['id']
    encoded = json.dumps(bound['expectations'], ensure_ascii=False, sort_keys=True,
                         separators=(',', ':')).encode('utf-8')
    bound['expectations_hash'] = hashlib.sha256(encoded).hexdigest()
    bound['valid'] = not bound['issues']
    return bound


def bind_geometry_targets(candidate, expected_facts, geometry):
    """Bind geometric expectations through the same frozen identity pairs."""
    projected = copy.deepcopy(geometry)
    aliases = {}
    for collection in ('spaces', 'walls', 'doors', 'windows'):
        values = projected.get(collection, {})
        request = {'expectations': [{'entity_id': identity} for identity in values],
                   'entity_id_contract': expected_facts.get('entity_id_contract', {}), 'issues': []}
        bound = bind_semantic_targets(candidate, request)
        if bound['issues']:
            projected['complete'] = False
            projected.setdefault('unresolved', []).extend(
                {'path': issue['path'], 'reason': issue['code']} for issue in bound['issues'])
            continue
        aliases.update({old: new['entity_id'] for old, new in zip(values, bound['expectations'])})
        projected[collection] = {aliases[old]: value for old, value in values.items()}
    # Explicit contact obligations are IDs as well; bounds and provenance stay
    # request-owned. Do not regenerate dimensions from the candidate.
    for collection in ('slabs', 'roof', 'stairs', 'floor_openings', 'products'):
        for value in projected.get(collection, {}).values():
            if isinstance(value, dict) and isinstance(value.get('must_touch_walls'), list):
                value['must_touch_walls'] = [aliases.get(wall, wall) for wall in value['must_touch_walls']]
    if isinstance(projected.get('accepted_wall_sets'), list):
        projected['accepted_wall_sets'] = [
            bind_geometry_targets(candidate, expected_facts, wall_set)
            for wall_set in projected['accepted_wall_sets']]
    return projected


def request_contract_issues(candidate, request):
    issues = []
    if request.get('minimum_schema_version') and candidate.get('schema_version') != request['minimum_schema_version']:
        issues.append({'code':'REQUEST_CONTRACT_DOWNGRADE','path':'/schema_version', 'message':'新请求必须保留其 Generation 语义合同。'})
    for selection in request.get('appearance_requests', []):
        if any(candidate.get('appearance', {}).get(key) != value for key, value in selection.items()):
            issues.append({'code':'REQUEST_APPEARANCE_MISMATCH','path':'/appearance','message':'候选遗漏或改变了冻结请求的主题/seed。'})
    return issues


def unauthorized_candidate_semantics(candidate, expectations):
    """New-version defaults cannot manufacture physical or performance facts."""
    if candidate.get('schema_version') != 'bim-json/2.1':
        return []
    allowed_properties = {(e['entity_id'], e.get('pset'), e.get('property'))
                          for e in expectations if e['kind'] == 'property'}
    allowed_materials = {e['entity_id'] for e in expectations if e['kind'] == 'material'}
    issues = _unauthorized_candidate_types(candidate, expectations)
    for record in candidate.get('entities', []):
        entity_id = record['id']
        if record.get('materials') and entity_id not in allowed_materials:
            issues.append({'code': 'UNREQUESTED_MATERIAL', 'path': f'/entities/{entity_id}/materials',
                           'message': '配色或模板不能补写未经请求授权的材料。'})
        for pset, values in record.get('property_sets', {}).items():
            for prop in values:
                if (entity_id, pset, prop) not in allowed_properties:
                    issues.append({'code': 'UNREQUESTED_PROPERTY', 'path': f'/entities/{entity_id}/property_sets/{pset}/{prop}',
                                   'message': '属性没有冻结请求或有依据的推导，不能自动补值。'})
    return issues


def _unauthorized_candidate_types(candidate, expectations):
    """Check explicit Generation Type objects and membership, before compilation.

    Compiler-created basic-filling attachments are not candidate records. A
    candidate provenance label cannot grant that deterministic-code exception.
    """
    from text2ifc_knowledge.registry import load_ifc2x3_registry

    requested_pairs = {
        (e['entity_id'], e['value']) for e in expectations
        if e['kind'] == 'type' and isinstance(e.get('value'), str)
    }
    allowed_types = {type_id for _, type_id in requested_pairs}
    registry = load_ifc2x3_registry()
    issues = []
    for record in candidate.get('entities', []):
        declaration = registry.declaration(record.get('ifc_class', ''))
        is_type = declaration and (
            record['ifc_class'] == 'IfcTypeObject' or 'IfcTypeObject' in declaration.get('supertypes', [])
        )
        if is_type and record['id'] not in allowed_types:
            issues.append({'code': 'UNREQUESTED_TYPE', 'path': f"/entities/{record['id']}",
                           'message': '显式 Type／Style 未获冻结请求授权；编译器最小附件不能由候选自报。'})
    for relation in candidate.get('relationships', []):
        if relation.get('ifc_class') != 'IfcRelDefinesByType':
            continue
        attributes = relation.get('attributes', {})
        type_id = attributes.get('RelatingType')
        if type_id not in allowed_types:
            issues.append({'code': 'UNREQUESTED_TYPE_ASSIGNMENT',
                           'path': f"/relationships/{relation['id']}/attributes/RelatingType",
                           'message': '类型关联指向未请求的 Type，不能由候选自行增加类型组织。'})
        elif any((instance, type_id) not in requested_pairs for instance in attributes.get('RelatedObjects', [])):
            issues.append({'code': 'UNREQUESTED_TYPE_ASSIGNMENT',
                           'path': f"/relationships/{relation['id']}/attributes/RelatedObjects",
                           'message': '类型关联包含未经请求授权的实例，不能扩大共享类型的作用范围。'})
    return issues
