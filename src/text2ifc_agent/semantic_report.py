"""Chinese request/result table from reopened IFC, independent of coverage labels."""
import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element as util

from text2ifc_compiler.semantic_verification import material_value, verify_semantic_expectations
from text2ifc_presentation import item_appearance_signatures


def write_semantic_report(path, ifc_path, expectations, issues=(), *, appearance_notes=()):
    output = Path(path)
    model = ifcopenshell.open(str(ifc_path)) if ifc_path and Path(ifc_path).is_file() else None
    entities = {}
    if model:
        for entity in model.by_type('IfcObjectDefinition'):
            identity = util.get_psets(entity, should_inherit=False).get('Pset_text2IFCIdentity', {}).get('BimJsonId')
            if identity: entities[identity] = entity
    lines = ['# 请求与 IFC 语义核对', '',
             '本报告独立重开 IFC 读取有效值。性能属性为用户设计要求或声明，不代表实测或认证。', '',
             '| 构件 / 作用域 | 请求项 | 请求值 | IFC 读回值 | 结果 |',
             '|---|---|---|---|---|']
    def text(value):
        return json.dumps(value,ensure_ascii=False,sort_keys=True).replace('|','\\|').replace('\n',' ')
    for expected in expectations:
        entity = entities.get(expected['entity_id'])
        scope = expected.get('scope','effective')
        original = entity
        if entity and scope == 'inherited': entity = util.get_type(entity)
        actual = None
        kind = expected['kind']
        if entity:
            if kind == 'property': actual = util.get_psets(entity,should_inherit=scope=='effective').get(expected['pset'],{}).get(expected['property'])
            elif kind == 'material': actual = material_value(util.get_material(entity,should_inherit=scope=='effective'))
            elif kind == 'type':
                type_entity=util.get_type(original)
                actual=util.get_psets(type_entity,should_inherit=False).get('Pset_text2IFCIdentity',{}).get('BimJsonId') if type_entity else None
            elif kind == 'appearance': actual=[s for r in entity.Representation.Representations for i in r.Items for s in item_appearance_signatures(i)] if entity.Representation else []
            elif kind == 'part_appearance':
                from text2ifc_presentation.part_readback import read_part_styles
                actual = read_part_styles(entity)
            elif kind == 'template': actual=util.get_psets(entity,should_inherit=False).get('Pset_text2IFCBasicFilling',{})
        okay = bool(model) and not verify_semantic_expectations(model,[expected])
        label = '.'.join([expected.get('pset',''),expected.get('property','')]).strip('.') if kind=='property' else kind
        lines.append(f"| {expected['entity_id']} / {scope} | {label} | {text(expected.get('value'))} | {text(actual)} | {'通过' if okay else '未满足'} |")
    if not expectations: lines.extend(['', '没有显式语义附加要求；不据此推断材料或性能属性。'])
    if issues: lines.extend(['', '阻断详情：', '', *['- '+text(issue) for issue in issues]])
    if appearance_notes:
        lines.extend(['', '风格说明与来源：', '',
                      '以下原文保留供 Audit 和人工视觉核对，不作为 IFC 字段逐字比对，也不据此判定风格已经满足。'])
        for note in appearance_notes:
            lines.append('- ' + text(note['text']) + '（来源：' + note['source_path'] + '）')
    lines.extend(['', '人工主题/代表性 Proof 视觉审查：待审；普通运行的自动交付状态与人工审查分别记录。', ''])
    output.write_text('\n'.join(lines),encoding='utf-8')
    return output
