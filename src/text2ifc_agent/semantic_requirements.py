"""Request-owned semantic expectations, projected before candidate generation.

No IFC/candidate facts are used to manufacture the requested values. Canonical
requirements use stable entity IDs, exactly like the geometry expected facts.
"""
from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping


SEMANTIC_FIELDS = {'material', 'materials', 'property_sets', 'type_id', 'appearance', 'part_appearance', 'template'}
SEMANTIC_BRIEF_VERSIONS = {'text2ifc/design-brief/2.1', 'text2ifc/design-brief/2.2', 'text2ifc/design-brief/2.3', 'text2ifc/design-brief/2.4', 'text2ifc/design-brief/2.5', 'text2ifc/design-brief/2.6', 'text2ifc/design-brief/2.7'}
SEMANTIC_KINDS = {'material', 'property', 'type', 'appearance', 'template'}


@lru_cache(maxsize=1)
def _appearance_schema():
    from text2ifc_contract.schema import load_schema_v21
    return load_schema_v21()['properties']['appearance']


@lru_cache(maxsize=1)
def element_appearance_schema():
    """Request grammar derives from the executable whole-element contract."""
    from text2ifc_contract.schema import load_schema_v21
    schema = copy.deepcopy(load_schema_v21()['$defs']['entity']['properties']['appearance'])
    schema['minProperties'] = 1
    return schema


@lru_cache(maxsize=1)
def _material_validator():
    """Use the compiler's material grammar, including its referenced definitions."""
    from jsonschema import Draft202012Validator
    from text2ifc_contract.schema import load_schema_v21
    schema = load_schema_v21()
    return Draft202012Validator({'$ref': '#/$defs/materialAssignment', '$defs': schema['$defs']})


def _project_appearance(selection, source_path):
    """Separate the known narrative field; never discard unknown constraints."""
    from jsonschema import Draft202012Validator

    issues, notes = [], []
    if not isinstance(selection, Mapping):
        return {}, notes, [{'code': 'REQUEST_APPEARANCE_INVALID', 'path': '/appearance',
                            'message': f'外观请求必须为对象；来源：{source_path}。'}]
    schema = _appearance_schema()
    constraints = {key: copy.deepcopy(value) for key, value in selection.items()
                   if key in schema['properties']}
    for key in selection:
        if key not in schema['properties'] and key != 'style_notes':
            issues.append({'code': 'REQUEST_APPEARANCE_UNSUPPORTED_FIELD', 'path': '/appearance',
                           'message': f'顶层外观不支持字段 {key!r}，需明确适用构件或受支持表达；来源：{source_path}。'})
    if 'style_notes' in selection:
        if isinstance(selection['style_notes'], str):
            notes.append({'text': selection['style_notes'], 'source_path': source_path + '/style_notes'})
        else:
            issues.append({'code': 'REQUEST_APPEARANCE_INVALID', 'path': '/appearance/style_notes',
                           'message': f'风格说明必须为文字，不能隐藏结构化要求；来源：{source_path}。'})
    for error in Draft202012Validator(schema).iter_errors(constraints):
        pointer = '/appearance' + ''.join('/' + str(key) for key in error.path)
        issues.append({'code': 'REQUEST_APPEARANCE_INVALID', 'path': pointer,
                       'message': f'外观请求不符合当前字段类型或支持范围：{error.message}；来源：{source_path}。'})
    return constraints, notes, issues


def generation_schema_version(brief: Mapping[str, Any]) -> str:
    if brief.get('schema_version') in {'text2ifc/design-brief/2.6', 'text2ifc/design-brief/2.7'}:
        return 'bim-json/2.3'
    if brief.get('schema_version') == 'text2ifc/design-brief/2.5':
        return 'bim-json/2.2'
    known = brief.get('known_facts', {})
    if brief.get('schema_version') in SEMANTIC_BRIEF_VERSIONS or (
        isinstance(known, Mapping) and known.get('semantic_requirements')
    ):
        return 'bim-json/2.1'
    return 'bim-json/2.0'


def project_semantic_requirements(brief: Mapping[str, Any]) -> dict[str, Any]:
    known = brief.get('known_facts', {})
    expectations: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    records: list[tuple[str, Mapping[str, Any]]] = []
    if brief.get('schema_version') in SEMANTIC_BRIEF_VERSIONS and (
        not isinstance(known, Mapping) or not isinstance(known.get('semantic_requirements'), list)
    ):
        issues.append({'code': 'SEMANTIC_AUTHORITY_INCOMPLETE',
                       'path': '/known_facts/semantic_requirements',
                       'message': '语义提取尚未明确：缺少数组不能视为用户无要求。请依据原始对话校正 Brief，禁止据此清除候选语义。'})

    def walk(value, path):
        if isinstance(value, Mapping):
            if path != '/known_facts' and SEMANTIC_FIELDS.intersection(value):
                records.append((path, value))
                return
            for key, child in value.items():
                if path == '/known_facts' and key in {'appearance', 'semantic_review'}:
                    continue
                walk(child, f'{path}/{key}')
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f'{path}/{index}')

    walk(known, '/known_facts')
    for path, record in records:
        if brief.get('schema_version') in {'text2ifc/design-brief/2.2', 'text2ifc/design-brief/2.3', 'text2ifc/design-brief/2.4', 'text2ifc/design-brief/2.5', 'text2ifc/design-brief/2.6', 'text2ifc/design-brief/2.7'} and not path.startswith('/known_facts/semantic_requirements/'):
            issues.append({'code': 'SEMANTIC_AUTHORITY_NON_CANONICAL', 'path': path,
                           'message': '结构化语义要求必须完整放入 semantic_requirements，不能散落后被遗漏。'})
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
            if not isinstance(material, Mapping) or not _material_validator().is_valid(material):
                issues.append({'code': 'SEMANTIC_MATERIAL_INCOMPLETE', 'path': path,
                               'message': '材料需符合实际材料合同：single_material 必须含非空 name；分层需完整层名和正厚度。空对象、未知字段和不完整构造不能成为冻结要求；请按用户原文校正，不得猜测。'})
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
        for field, kind in [('type_id', 'type'), ('appearance', 'appearance'), ('part_appearance', 'part_appearance'), ('template', 'template')]:
            if field in record:
                if field == 'appearance':
                    from jsonschema import Draft202012Validator
                    malformed = list(Draft202012Validator(element_appearance_schema()).iter_errors(record[field]))
                    if malformed:
                        issues.append({'code': 'SEMANTIC_AUTHORITY_APPEARANCE_INVALID', 'path': path+'/appearance',
                            'message': '构件 appearance 只支持非空数值 RGB/透明度覆盖；主题及窗框、玻璃等部件说明不能作为整件外观字段。'})
                        continue
                expectations.append({**base, 'kind': kind, 'value': copy.deepcopy(record[field])})
    from .brief_semantic_roles import filter_roles
    expectations, role_issues = filter_roles(brief, expectations)
    issues.extend(role_issues)
    if brief.get('schema_version') == 'text2ifc/design-brief/2.7':
        from .brief_semantic_roles import role_index
        from text2ifc_contract.property_validation import validate_property_sets
        from text2ifc_knowledge.registry import load_ifc2x3_registry
        identities, _ = role_index(brief)
        registry = load_ifc2x3_registry()
        executable = []
        for row in expectations:
            if row['kind'] != 'property':
                executable.append(row)
                continue
            cls = identities.get(row['entity_id'], {}).get('ifc_class')
            rejected = validate_property_sets(cls, {row['pset']: {row['property']: row['value']}},
                path=row['source_path'] + '/property_sets', registry=registry)
            if rejected:
                issues.extend({'code': 'SEMANTIC_PROPERTY_NOT_ADMISSIBLE', 'path': i.path,
                    'message': f'{i.code}: {i.message} Correct extraction from the user request; native IFC attributes are not Pset properties. Do not invent a replacement property or discard an explicit unsupported request.'}
                    for i in rejected)
            else:
                executable.append(row)
        expectations = executable
    from .part_appearance import validate_part_requests
    issues.extend(validate_part_requests(brief, expectations))
    if brief.get('schema_version') in {'text2ifc/design-brief/2.2', 'text2ifc/design-brief/2.3', 'text2ifc/design-brief/2.4', 'text2ifc/design-brief/2.5', 'text2ifc/design-brief/2.6', 'text2ifc/design-brief/2.7'}:
        review = known.get('semantic_review', {}) if isinstance(known, Mapping) else {}
        for kind in sorted(SEMANTIC_KINDS):
            entry = review.get(kind, {}) if isinstance(review, Mapping) else {}
            status = entry.get('status') if isinstance(entry, Mapping) else None
            has_values = any(e['kind'] == kind or (kind == 'appearance' and e['kind'] == 'part_appearance') for e in expectations)
            if status not in {'specified', 'not_specified', 'unresolved'} or (
                status == 'unresolved'
            ):
                issues.append({'code': 'SEMANTIC_AUTHORITY_INCOMPLETE',
                               'path': f'/known_facts/semantic_review/{kind}',
                               'message': '该类语义尚未完成检查，不能按无要求发布或删除。'})
            elif (status == 'specified' and not has_values) or (status == 'not_specified' and has_values):
                issues.append({'code': 'SEMANTIC_AUTHORITY_CONFLICT',
                               'path': f'/known_facts/semantic_review/{kind}',
                               'message': '语义检查声明与结构化要求不一致，需校正 Brief。'})
    encoded = json.dumps(expectations, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return {'schema_version': 'text2ifc/request-semantics/1.0', 'expectations': expectations,
            'authority_declared': isinstance(known, Mapping) and isinstance(known.get('semantic_requirements'), list),
            'issues': issues, 'valid': not issues, 'expectations_hash': hashlib.sha256(encoded).hexdigest()}


def request_semantics_for_case(root: Path) -> dict[str, Any]:
    from .run_report import resolve_final_design_brief_dir
    paths = [resolve_final_design_brief_dir(root) / 'design-brief.json', root / 'design-brief.json']
    brief_path = next((p for p in paths if p.is_file()), None)
    brief = json.loads(brief_path.read_text(encoding='utf-8')) if brief_path else {}
    projected = project_semantic_requirements(brief)
    projected['minimum_schema_version'] = generation_schema_version(brief) if brief.get('schema_version') in SEMANTIC_BRIEF_VERSIONS else None
    projected['appearance_requests'], projected['appearance_notes'] = [], []

    def add_appearance(selection, source_path):
        constraints, notes, issues = _project_appearance(selection, source_path)
        if constraints:
            projected['appearance_requests'].append(constraints)
        projected['appearance_notes'].extend(notes)
        projected['issues'].extend(issues)

    known = brief.get('known_facts', {})
    if isinstance(known, Mapping) and 'appearance' in known:
        add_appearance(known['appearance'], brief_path.relative_to(root).as_posix() + '#/known_facts/appearance')
    frozen_path = root / 'expected-facts.json'
    if frozen_path.is_file():
        frozen = json.loads(frozen_path.read_text(encoding='utf-8'))
        projected['entity_id_contract'] = copy.deepcopy(frozen.get('entity_id_contract', {}))
        if 'semantic_expectations' in frozen:
            # Both request projections constrain output. A changed Brief cannot
            # weaken a saved expectation during resume or final acceptance.
            projected['expectations'] = [*frozen['semantic_expectations'], *projected['expectations']]
        projected['issues'].extend(frozen.get('semantic_projection_issues', []))
        if frozen.get('generation_schema_version') in {'bim-json/2.1', 'bim-json/2.2', 'bim-json/2.3'}:
            projected['minimum_schema_version'] = frozen['generation_schema_version']
        if 'appearance' in frozen:
            add_appearance(frozen['appearance'], 'expected-facts.json#/appearance')
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
        constraints, _notes, invalid = _project_appearance(selection, '/appearance')
        issues.extend(invalid)
        actual = candidate.get('appearance', {})
        if constraints and (not isinstance(actual, Mapping) or
                            any(actual.get(key) != value for key, value in constraints.items())):
            issue = {'code':'REQUEST_APPEARANCE_MISMATCH','path':'/appearance','message':'候选遗漏或改变了冻结请求的主题/seed。'}
            if issue not in issues:
                issues.append(issue)
    return issues


def unauthorized_candidate_semantics(candidate, expectations):
    """Defaults cannot manufacture facts or grant whole-product style overrides."""
    if candidate.get('schema_version') not in {'bim-json/2.1', 'bim-json/2.2', 'bim-json/2.3'}:
        return []
    allowed_properties = {(e['entity_id'], e.get('pset'), e.get('property'))
                          for e in expectations if e['kind'] == 'property'}
    allowed_materials = {e['entity_id'] for e in expectations if e['kind'] == 'material'}
    allowed_appearance = {e['entity_id'] for e in expectations if e['kind'] == 'appearance'}
    from .part_appearance import unauthorized_parts
    issues = [*_unauthorized_candidate_types(candidate, expectations), *unauthorized_parts(candidate, expectations)]
    for record in candidate.get('entities', []):
        entity_id = record['id']
        if 'appearance' in record and entity_id not in allowed_appearance:
            issues.append({'code': 'UNREQUESTED_APPEARANCE', 'path': f'/entities/{entity_id}/appearance',
                           'message': '整件外观覆盖没有冻结请求授权；主题或部件风格说明不能授权整件同色/同透明度。撤销该可选字段后使用确定性主题和模板部件样式。'})
        if record.get('materials') and entity_id not in allowed_materials:
            issues.append({'code': 'UNREQUESTED_MATERIAL', 'path': f'/entities/{entity_id}/materials',
                           'message': '配色或模板不能补写未经请求授权的材料。'})
        for pset, values in record.get('property_sets', {}).items():
            for prop in values:
                if (entity_id, pset, prop) not in allowed_properties:
                    pset_token = pset.replace('~', '~0').replace('/', '~1')
                    prop_token = prop.replace('~', '~0').replace('/', '~1')
                    issues.append({'code': 'UNREQUESTED_PROPERTY', 'path': f'/entities/{entity_id}/property_sets/{pset_token}/{prop_token}',
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
