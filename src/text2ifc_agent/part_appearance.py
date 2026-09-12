"""Request authority for basic filling colours, independent of candidate values."""
from text2ifc_contract.part_appearance import valid_part_appearance


def validate_part_requests(brief, expectations):
    from .brief_semantic_roles import role_index
    parts = [r for r in expectations if r['kind'] == 'part_appearance']
    if not parts:
        return []
    identities, _ = role_index(brief)
    whole = {r['entity_id'] for r in expectations if r['kind'] == 'appearance'}
    typed = {r['entity_id'] for r in expectations if r['kind'] == 'type' and r['value'] in whole}
    templates = {r['entity_id'] for r in expectations if r['kind'] == 'template'}
    template_families = {}
    for row in expectations:
        if row['kind'] == 'template' and isinstance(row['value'], dict):
            family = {'door-left': 'IfcDoor', 'door-right': 'IfcDoor',
                      'window-single': 'IfcWindow', 'window-double-vertical': 'IfcWindow'}.get(row['value'].get('template_id'))
            template_families.setdefault(row['entity_id'], set()).add(family)
    issues, channels = [], {}
    for row in parts:
        identity = row['entity_id']; value = row['value']
        cls = identities.get(identity, {}).get('ifc_class')
        # A frozen template explicitly names its occurrence family. Legacy Brief
        # geometry may omit a defining ID record; do not invent such geometry.
        # The candidate contract and reopened verifier still enforce actual class.
        families = template_families.get(identity, set())
        if cls is None and len(families) == 1:
            cls = next(iter(families))
        if (brief.get('schema_version') not in {'text2ifc/design-brief/2.5','text2ifc/design-brief/2.6'}
                or cls not in {'IfcDoor', 'IfcWindow'} or row['scope'] == 'inherited'
                or not valid_part_appearance(value, cls) or identity not in templates
                or families != {cls}
                or identity in whole | typed):
            issues.append({'code': 'SEMANTIC_PART_APPEARANCE_CONFLICT', 'path': row['source_path'],
                'message': '部件配色仅支持明确基础门窗实例及适用部件；不能与整件或继承 Type 外观同时作用，也不能省略构造模板。请澄清或校正语义，保持用户尺寸和位置。'})
            continue
        for part, values in value.items():
            for key, val in values.items():
                token = (identity, part, key)
                if token in channels and channels[token] != val:
                    issues.append({'code': 'SEMANTIC_PART_APPEARANCE_CONFLICT', 'path': row['source_path'],
                                   'message': '同一部件通道出现冲突值，不能静默择一。'})
                channels[token] = val
    return issues


def unauthorized_parts(candidate, expectations):
    if candidate.get('schema_version') not in {'bim-json/2.2','bim-json/2.3'}:
        return []
    allowed = {(r['entity_id'], part, key) for r in expectations if r['kind'] == 'part_appearance'
               and isinstance(r.get('value'), dict) for part, value in r['value'].items()
               if isinstance(value, dict) for key in value}
    issues = []
    for record in candidate.get('entities', []):
        overrides = record.get('part_appearance', {})
        if not isinstance(overrides, dict):
            continue  # Structural contract reports malformed values.
        for part, value in overrides.items():
            if isinstance(value, dict):
                for key in value:
                    if (record['id'], part, key) not in allowed:
                        issues.append({'code': 'UNREQUESTED_PART_APPEARANCE',
                            'path': f"/entities/{record['id']}/part_appearance/{part}/{key}",
                            'message': '此部件通道没有冻结请求授权；保持主题默认值，不能扩大外观修改范围。'})
    return issues
