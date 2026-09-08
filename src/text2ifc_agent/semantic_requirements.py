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
    issues = []
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
