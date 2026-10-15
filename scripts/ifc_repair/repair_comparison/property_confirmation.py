"""Host-only verification for explicitly delegated existing-property approval.

This is not a default consent mechanism. The caller must have recorded the user's
delegation before calling it. Only the supplied public request, damaged IFC and
already bound Ledger snapshot are read; no reference, Gold, report or live call
is used. Unsupported or incomplete evidence returns None, leaving clarification
pending. Public transaction summaries omit property facts and cannot be approved.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
import re
from typing import Any, Mapping

import ifcopenshell
import ifcopenshell.util.unit
import jsonschema

from scripts.ifc_repair.dataset_batch.prompt_check import _instance_property, _parse_property
from scripts.ifc_repair.dataset_batch.prompt_check_v3 import HEADER as _HEADER_13, NAME_HEADER as _HOST_HEADER_13, _property as _parse_property_13
from scripts.ifc_repair.dataset_request_v4 import PREFIX as _PREFIX_14
from text2ifc_ifc_repair.property_intent import PropertyConfirmationBatch, PropertyConfirmationPreview
from text2ifc_ifc_repair.repair_intent import hash_request
from text2ifc_ifc_repair.resolution_flow import PROPERTY_CONFIRMATION_EXCERPT_MAX, _validate_property_transaction_preview


POLICY_VERSION = 'public-existing-property-confirmation/0.1'
_HEADER = '请按以下要求修复模型。距离和放置坐标单位为米，几何尺寸单位为毫米。'
_WORLD = '世界坐标采用IFC模型的项目放置坐标系。'
_HOST = '采用各宿主墙已有的自身放置原点及轴方向。'
_FOOTER = '除以上补建、洞口关系及指定实例属性外，其余构件、楼层、尺寸、位置、类型和材料保持原样。'
_UNIT_APPENDIX = ('属性更改中的数值沿用该属性在 IFC 中的有效单位（属性未单独指定时沿用项目对应单位），'
                 '保留原属性类型和单位；上述几何尺寸的毫米约定不适用于属性值。单位缺失或冲突时请提出澄清。')
_POINT = r'[（(][-+0-9.eE,，]+[）)]'
_AXES = _POINT + '、' + _POINT + '、' + _POINT + '。'
_NUMBER = r'[-+0-9.eE]+'
_WORLD_HOST = ('宿主墙世界原点为' + _POINT + '米，世界X/Y/Z轴分别为' + _AXES
               + '宿主墙未扣洞口的世界外包范围下角点为' + _POINT + '米，上角点为' + _POINT + '米。')
_WORLD_POSITION = '放置原点的世界坐标为' + _POINT + '米。世界X/Y/Z轴分别为' + _AXES
_HOST_POSITION = (r'宿主墙「[^」\r\n]+」，补建或修改位置在该墙自身X轴[正负]向一侧。'
                  + '放置原点相对墙自身放置原点，沿墙自身X方向距离' + _NUMBER + '米，Y方向距离'
                  + _NUMBER + '米，Z方向距离' + _NUMBER + '米。构件自身X/Y/Z轴相对墙自身坐标系的方向分别为' + _AXES)
_STRING_TYPES = {'IfcLabel', 'IfcText', 'IfcIdentifier'}
_SCALAR_TYPES = _STRING_TYPES | {'IfcBoolean', 'IfcInteger', 'IfcReal'}
_MEASURE_UNITS = {
    'IfcLengthMeasure': ('LENGTHUNIT', 'METRE', ''),
    'IfcPositiveLengthMeasure': ('LENGTHUNIT', 'METRE', ''),
    'IfcAreaMeasure': ('AREAUNIT', 'SQUARE_METRE', '2'),
    'IfcVolumeMeasure': ('VOLUMEUNIT', 'CUBIC_METRE', '3'),
}


def _require(condition: bool) -> None:
    if not condition:
        raise ValueError('PUBLIC_PROPERTY_NOT_PROVEN')


def _items(document: Mapping[str, Any]) -> list[PropertyConfirmationPreview]:
    kind = document.get('preview_kind')
    if kind == 'property_transaction':
        transaction = _validate_property_transaction_preview(document)
        items = [item for batch in transaction['batches'] for item in batch.items]
    elif kind == 'property_batch':
        items = list(PropertyConfirmationBatch.from_dict(document).items)
    else:
        _require(kind is None)
        item = PropertyConfirmationPreview.from_dict(document)
        _require(item.to_dict() == dict(document))
        items = [item]
    _require(0 < len(items) <= 1024)
    return items


def _rows(text: str) -> tuple[str, list[str], Any]:
    if text.startswith(_PREFIX_14):
        text = text[len(_PREFIX_14):]
    lines = [line for line in text.splitlines() if line.strip()]
    # The optional unit policy is part of the already-verified full request hash.
    # It adds no target/property facts and does not replace source unit proof.
    if lines and lines[-1] == _UNIT_APPENDIX:
        lines.pop()
    _require(len(lines) >= 3 and lines[-1] == _FOOTER)
    _require(lines[0] in {_HEADER + _WORLD, _HEADER + _HOST, _HEADER_13, _HOST_HEADER_13})
    modern = lines[0] in {_HEADER_13, _HOST_HEADER_13}
    mode = 'world' if lines[0] in {_HEADER + _WORLD, _HEADER_13} else 'host_wall'
    rows = []
    for line in lines[1:-1]:
        if line.startswith('属性更改'):
            rows.append(line)
        else:
            # Geometry instructions are not an authorization to alter properties.
            _require(bool(re.match(r'^\d+\. 补建一[扇根][门窗梁柱]：', line)))
            _require('实例属性' not in line and '属性更改' not in line)
    _require(0 < len(rows) <= 1024)
    position = ('(?:' + _WORLD_HOST + ')?' + _WORLD_POSITION) if mode == 'world' else _HOST_POSITION
    for index, row in enumerate(rows, 1):
        _require(row.startswith(f'属性更改{index}：'))
        if modern:
            # The 1.3 cursor parser consumes the entire row, including optional
            # orientation and rounding tolerance, and rejects leftover clauses.
            continue
        pattern = (rf'属性更改{index}：现有Ifc\w+，归属楼层「[^」\r\n]+」。' + position
                   + r'将实例属性「[^」\r\n]+」改为[^\r\n]+，保留其原属性类型。')
        _require(re.fullmatch(pattern, row) is not None)
    return mode, rows, _parse_property_13 if modern else _parse_property


def _public_excerpt(excerpt: str, text: str) -> bool:
    normalized = ' '.join(text.split())
    if excerpt and excerpt in normalized:
        return True
    # Native resolution normalizes whitespace then truncates at 160 chars.
    # This validates public provenance only; target/path/value/type are always
    # checked independently below against every complete public property row.
    if excerpt.endswith('…'):
        if len(excerpt) not in {PROPERTY_CONFIRMATION_EXCERPT_MAX - 1, PROPERTY_CONFIRMATION_EXCERPT_MAX}:
            return False
        excerpt = excerpt[:-1]
        if excerpt in normalized:
            return True
    # A preview can quote the property requirement and a later unit convention.
    # Require every literal sentence in public order; do not accept paraphrases,
    # reordered statements or invented facts. Structured facts remain mandatory.
    parts = [part.strip() for part in excerpt.split('。') if part.strip()]
    if not 2 <= len(parts) <= 8:
        return False
    cursor = 0
    for part in parts:
        found = normalized.find(part, cursor)
        if found < 0:
            return False
        cursor = found + len(part)
    return True


def _direct_property(entity: Any, path: str) -> Any:
    # The shared parser already requires one direct single-value property.
    _instance_property(entity, path)
    return next(prop for rel in entity.IsDefinedBy if rel.is_a('IfcRelDefinesByProperties')
                and rel.RelatingPropertyDefinition.is_a('IfcPropertySet')
                for prop in rel.RelatingPropertyDefinition.HasProperties
                if str(rel.RelatingPropertyDefinition.Name) + '.' + str(prop.Name) == path)


def _effective_unit(prop: Any, value_type: str) -> str | None:
    """Independently prove the unit; coordinate scales never supply this fact."""
    _require(value_type in _SCALAR_TYPES or value_type in _MEASURE_UNITS)
    unit = prop.Unit
    if value_type not in _MEASURE_UNITS:
        _require(unit is None)
        return None
    unit_type, name, suffix = _MEASURE_UNITS[value_type]
    if unit is None:
        projects = prop.file.by_type('IfcProject')
        _require(len(projects) == 1 and projects[0].UnitsInContext is not None)
        units = [item for item in projects[0].UnitsInContext.Units or ()
                 if getattr(item, 'UnitType', None) == unit_type]
        _require(len(units) == 1)
        unit = units[0]
    if unit.is_a('IfcConversionBasedUnit'):
        # Only preserve a publicly existing, fully defined international foot.
        # A familiar Name alone cannot authorize an arbitrary conversion graph.
        _require(unit_type == 'LENGTHUNIT' and unit.UnitType == 'LENGTHUNIT' and unit.Name == 'FOOT')
        _require(unit.Dimensions is not None and tuple(unit.Dimensions) == (1, 0, 0, 0, 0, 0, 0))
        conversion = unit.ConversionFactor
        _require(conversion is not None and conversion.ValueComponent is not None)
        factor = conversion.ValueComponent.wrappedValue
        _require(type(factor) in {int, float} and math.isfinite(factor) and factor == .3048)
        component = conversion.UnitComponent
        _require(component is not None and component.is_a('IfcSIUnit')
                 and component.UnitType == 'LENGTHUNIT' and component.Name == 'METRE' and component.Prefix is None)
        return 'FOOT'
    _require(unit.is_a('IfcSIUnit') and unit.UnitType == unit_type and unit.Name == name)
    prefixes = {None: 'm', 'MILLI': 'mm', 'CENTI': 'cm'}
    _require(unit.Prefix in prefixes)
    return prefixes[unit.Prefix] + suffix


def _value_matches(value: Any, value_type: str) -> bool:
    if value_type in _STRING_TYPES:
        return type(value) is str
    if value_type == 'IfcBoolean':
        return type(value) is bool
    if value_type == 'IfcInteger':
        return type(value) is int
    if value_type == 'IfcReal' or value_type in _MEASURE_UNITS:
        return (type(value) in {int, float} and math.isfinite(value)
                and (value_type != 'IfcPositiveLengthMeasure' or value > 0))
    return False


def _verify(state: Mapping[str, Any], public_ifc: Path, public_request: Path) -> dict[str, Any]:
    _require(state['status'] == 'awaiting_user' and state['arm'] in {'B', 'E', 'F'})
    question = state['question']
    binding = question['binding']
    native = binding['native_question']
    _require(native['reason_code'] == 'property_confirmation')
    _require(question['question_id'] == native['clarification_id'])
    _require(type(binding['state_version']) is int and binding['state_version'] == native['state_version'])
    _require('confirm_property' in native['answer_modes'] and not native.get('candidates'))
    document = native['property_preview']
    items = _items(document)
    _require(native['operation_id'] in {item.operation_id for item in items})
    existing_native = state.get('native', {}).get('result')
    if existing_native is not None:
        _require(existing_native['clarification'] == native and existing_native['state_version'] == binding['state_version'])

    raw_ifc = public_ifc.read_bytes()
    raw_request = public_request.read_bytes()
    source_sha = hashlib.sha256(raw_ifc).hexdigest()
    _require(source_sha == state['metadata']['input_sha256'])
    text = raw_request.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    # DirectRunner writes task.txt from request.txt.strip() plus one newline.
    text = text.strip() + '\n'
    request_hash = hash_request(text)
    model = state['metadata']['runtime']['model_requested']
    _require(isinstance(model, str) and bool(model))
    model_hash = hash_request(model)
    _require(all(item.request_hash == request_hash and item.model_fingerprint == model_hash for item in items))

    mode, rows, parse_property = _rows(text)
    damaged = ifcopenshell.file.from_string(raw_ifc.decode('utf-8'))
    _require(damaged.schema == 'IFC2X3')
    scale = ifcopenshell.util.unit.calculate_unit_scale(damaged)
    cache: dict[int, Any] = {}
    expected: dict[tuple[str, str], tuple[Any, str, str | None]] = {}
    all_ids = [root.GlobalId for root in damaged.by_type('IfcRoot')]
    for row in rows:
        parsed = parse_property(row, damaged, mode, scale, cache)
        target = parsed['entity']
        identity = (target.GlobalId, parsed['path'])
        _require(identity not in expected and all_ids.count(target.GlobalId) == 1)
        actual_type, _ = parsed['actual']
        unit = _effective_unit(_direct_property(target, parsed['path']), actual_type)
        value = parsed['value']
        _require(_value_matches(value, actual_type))
        expected[identity] = (value, actual_type, unit)
    _require(len(items) == len(expected))
    seen = set()
    for item in items:
        identity = (item.target_global_id, item.set_name + '.' + item.property_name)
        _require(identity in expected and identity not in seen)
        seen.add(identity)
        value, actual_type, unit = expected[identity]
        # 75 and 75.0 express the same REAL/measure. Booleans and strings do not.
        # Preserve the request's raw numeric value: never convert using headers.
        _require(_value_matches(item.value, actual_type) and item.value == value and item.value_type == actual_type)
        _require(item.scope == 'occurrence_direct' and item.unit == unit)
        _require(item.source.source_kind == 'user_request' and item.source.reference.startswith('request:'))
        _require(bool(item.source.excerpt.strip()) and _public_excerpt(item.source.excerpt, text))
        _require(bool(item.operation_id))
    answer = {'kind': 'confirm_property', 'preview_hash': document['preview_hash']}
    jsonschema.Draft202012Validator.check_schema(native['answer_schema'])
    jsonschema.Draft202012Validator(native['answer_schema']).validate(answer)
    # Detect public-input changes while the snapshot was being checked.
    _require(public_ifc.read_bytes() == raw_ifc and public_request.read_bytes() == raw_request)
    return {
        'source': 'user_confirmed',
        'question_id': question['question_id'],
        'event_id': 'delegated-property:' + str(state['run_id']) + ':' + question['question_id'] + ':' + document['preview_hash'][7:23],
        'text': '根据用户预先授权的现有实例属性确认策略，已用公开请求和受损 IFC 核对全部目标、属性路径、值、类型和有效单位；这是委托策略自动确认，未经逐项人工审阅。',
        'native_answer': answer,
        'provenance': {'policy_version': POLICY_VERSION, 'human_reviewed': False,
                       'evidence_sources': ['public_request', 'damaged_ifc'],
                       'public_ifc_sha256': source_sha, 'public_request_sha256': hashlib.sha256(raw_request).hexdigest(),
                       'request_hash': request_hash, 'model_fingerprint': model_hash,
                       'preview_hash': document['preview_hash'], 'verified_property_count': len(items),
                       'effective_units': sorted({unit for _, _, unit in expected.values() if unit is not None})},
    }


def verified_answer(state: Mapping[str, Any], public_ifc: Path, public_request: Path) -> dict[str, Any] | None:
    """Return a hash-bound delegated answer, or None without changing anything.

    Caller owns delegation, quiescence, admission and replay protection. This
    function only verifies a snapshot and never submits its returned answer.
    """
    try:
        return _verify(state, Path(public_ifc), Path(public_request))
    except Exception:
        # Malformed IFC, unsupported syntax and absent facts cannot imply consent.
        return None
