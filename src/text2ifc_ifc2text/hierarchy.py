"""Floor -> rooms -> component positions -> materials, with complete fact coverage.

LLM outputs only paragraph groupings of immutable, human-readable fact fragments.
Coordinates and source-supported statements are inserted by code, not regenerated.
There is no room/component cardinality cutoff. Batches limit request length only.
"""
from __future__ import annotations

import json
import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from .observation import CATEGORIES

LAYOUT_VERSION = 'text2ifc/ifc2text-layout/0.3'


def coordinate_m(mm: float) -> str:
    if isinstance(mm, bool) or not math.isfinite(float(mm)):
        raise ValueError('NONFINITE_COORDINATE')
    value = (Decimal(str(mm))/Decimal(1000)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    return f'{abs(value) if value == 0 else value:.2f}'


def point(values) -> str:
    return '未确认' if values is None else '(' + ', '.join(coordinate_m(v) for v in values) + ') m'


def rounded_ring(values) -> list[list[float]]:
    """Round only the displayed XY ring; reject a collapsed/invalid footprint."""
    from shapely.geometry import Polygon
    points = []
    for value in values:
        xy = [float(coordinate_m(v)) * 1000 for v in value]
        if not points or xy != points[-1]:
            points.append(xy)
    if points and points[0] != points[-1]:
        points.append(list(points[0]))
    if len(points) < 4:
        raise ValueError('COORDINATE_ROUNDING_RING_COLLAPSED')
    polygon = Polygon(points)
    if not polygon.is_valid or polygon.area <= 0:
        raise ValueError('COORDINATE_ROUNDING_RING_INVALID')
    return points


def dimension(mm) -> str:
    if mm is None:
        return '未确认'
    if not math.isfinite(float(mm)):
        raise ValueError('NONFINITE_DIMENSION')
    return f'{float(mm):.2f}'.rstrip('0').rstrip('.') + ' mm'


def bounds_text(bounds) -> str:
    if not bounds:
        return '本次未确认几何范围'
    return '包围盒范围为' + '，'.join(f'{axis.upper()} {coordinate_m(bounds[axis][0])}～{coordinate_m(bounds[axis][1])} m' for axis in ('x','y','z'))


def _space_text(item) -> str:
    label = item['label']
    name = item.get('long_name') or item.get('name') or '名称未确认'
    footprint = item.get('footprint', {})
    text = f'房间 {label}（{name}）：'
    if footprint.get('status') == 'measured_projection':
        parts = []
        for index, p in enumerate(footprint['polygons'], 1):
            part = '平面外轮廓' + (f'第{index}部分' if len(footprint['polygons']) > 1 else '') + '依次经过 ' + '、'.join(point(v) for v in rounded_ring(p['exterior_xy_mm']))
            for hindex, hole in enumerate(p.get('holes_xy_mm', []), 1):
                part += f'；内环{hindex}依次经过 ' + '、'.join(point(v) for v in rounded_ring(hole))
            parts.append(part)
        text += '；'.join(parts)
        z = footprint['z_range_mm']
        text += f'；竖向范围 {coordinate_m(z[0])}～{coordinate_m(z[1])} m'
    else:
        text += bounds_text(item.get('bounds_mm')) + '；本次未确认实际平面轮廓，不将包围盒当作矩形房间'
    walls = item.get('boundary_walls', [])
    text += '；明确边界墙为 ' + '、'.join(walls) if walls else '；本次未确认边界墙关联'
    return text + '。'


def _component_text(category, item) -> str:
    label = item['label']
    if category in ('slabs', 'coverings'):
        name = '楼板' if category == 'slabs' else '覆盖层'
        footprint = item.get('footprint', {})
        text = f'{name} {label}：'
        if footprint.get('status') == 'measured_projection':
            text += '平面投影外轮廓为 ' + '；'.join('、'.join(point(v) for v in rounded_ring(p['exterior_xy_mm'])) for p in footprint['polygons'])
            for p in footprint['polygons']:
                for hole in p.get('holes_xy_mm', []):
                    text += '；内环为 ' + '、'.join(point(v) for v in rounded_ring(hole))
            z = footprint['z_range_mm']
            text += f'；世界底标高 {coordinate_m(z[0])} m，顶标高 {coordinate_m(z[1])} m，竖向厚度 {dimension(z[1]-z[0])}'
        else:
            text += bounds_text(item.get('bounds_mm')) + '；实际轮廓未确认'
        if item.get('predefined_type'):
            text += '；源构件分类 ' + item['predefined_type']
        return text + '。'
    if category == 'walls':
        text = f'墙 {label}：'
        if item.get('axis_start_mm') is not None and item.get('axis_end_mm') is not None:
            axis = '几何近似轴' if item.get('measurement_method') == 'world_mesh_principal_axis' else '参考轴'
            text += f'{axis}由 {point(item["axis_start_mm"])} 至 {point(item["axis_end_mm"])}'
            text += f'；厚 {dimension(item.get("thickness_mm"))}，高 {dimension(item.get("height_mm"))}'
        else:
            text += bounds_text(item.get('bounds_mm')) + '；本次未确认可重建轴线'
        # Explicit world bounds preserve the difference between reference axis and body.
        if item.get('bounds_mm'):
            text += '；' + bounds_text(item['bounds_mm'])
        return text + '。'
    if category in ('doors', 'windows', 'openings'):
        name = {'doors':'门','windows':'窗','openings':'开口'}[category]
        text = f'{name} {label}：'
        host = item.get('host_wall')
        text += f'宿主墙 {host}' if host else '本次未确认宿主墙'
        dims = item.get('dimensions_mm', {})
        width = dims.get('width') if category == 'openings' else item.get('overall_width_mm')
        height = dims.get('height') if category == 'openings' else item.get('overall_height_mm')
        text += f'；宽 {dimension(width)}，高 {dimension(height)}'
        if category == 'openings' and dims.get('depth') is not None:
            text += f'，深 {dimension(dims["depth"])}'
        if item.get('bounds_mm'):
            text += '；' + bounds_text(item['bounds_mm'])
        elif item.get('centroid_mm'):
            text += '；包围盒中心 ' + point(item['centroid_mm'])
        pos = item.get('host_position_mm')
        if pos:
            text += f'；沿宿主参考轴中心偏移 {coordinate_m(pos["center_offset_mm"])} m，墙局部底部高度 {coordinate_m(pos["sill_height_mm"])} m'
            if pos.get('normal_offset_mm') is not None:
                text += f'，法向偏移 {coordinate_m(pos["normal_offset_mm"])} m'
        if item.get('opening'):
            text += f'；填充开口 {item["opening"]}，开口与填充构件分别计一次'
        if item.get('filling'):
            text += f'；由 {item["filling"]} 填充，不另造重复开口'
        return text + '。'
    return f'楼梯 {label}：{bounds_text(item.get("bounds_mm"))}；本次几何高度覆盖的楼层为 ' + ('、'.join(item.get('spans_storeys_by_geometry', [])) or '未确认') + '，不据此保证通行连接。'


def _material_text(material) -> str:
    origin = '构件直接关联' if material.get('origin') == 'occurrence' else '类型继承关联'
    kind = material['kind']
    if kind == 'single_material':
        return origin + '材料“' + str(material.get('name') or '未命名') + '”'
    if kind == 'material_list':
        return origin + '材料列表 ' + '、'.join(str(n or '未命名') for n in material['names']) + '；列表不表示分层顺序或厚度'
    if kind in ('material_layer_set_usage', 'material_layer_set'):
        text = origin + '分层材料，按源层序为 ' + '、'.join(f'{l.get("name") or "未命名"} {dimension(l.get("thickness_mm"))}' for l in material['layers'])
        if kind == 'material_layer_set_usage':
            text += f'；层集方向 {material.get("direction")}，方向符号 {material.get("direction_sense")}，参考线偏移 {dimension(material.get("offset_mm"))}'
        return text + '；不额外推断内外侧或性能'
    return '材料关联形式 ' + material.get('ifc_class', kind) + ' 尚未支持描述'


def make_hierarchy_plan(facts: dict[str, Any]) -> dict[str, Any]:
    blocks: list[dict[str, Any]] = []
    counter = 0
    def block(title: str, level: int, lines: list[str]):
        nonlocal counter
        if not lines:
            return
        items = []
        for line in lines:
            counter += 1
            items.append({'id': f'F{counter:05d}', 'text': line})
        blocks.append({'id': f'B{len(blocks)+1:03d}', 'title': title, 'level': level, 'items': items})
    level_count = len(facts['storeys'])
    block('整体说明', 2, [
        f'本说明按源模型的 {level_count} 个楼层记录组织；这些记录也可能包含基准或顶层标高，不据记录数量另行推断使用楼层。',
        '以下世界坐标统一以米表示，保留两位小数；尺寸和材料层厚另标单位。只重建明确描述的事实，未确认事项不补默认建筑几何。',
        'X、Y 表示源坐标轴，不自动解释为东西南北。参考轴、几何范围与材料参考线应合并理解，不把任意参考轴默认为墙中心线。',
    ])
    storeys = list(facts['storeys'])
    if any(facts.get('unassigned', {}).get(c) for c in CATEGORIES):
        storeys += [{**facts['unassigned'], 'label': 'UNASSIGNED', 'name':'归属未确认', 'elevation_mm': None, 'derived_spaces': []}]
    counts: dict[str, int] = {c: 0 for c in CATEGORIES}
    for s in storeys:
        label = s['label']
        elevation = '未确认' if s.get('elevation_mm') is None else coordinate_m(s['elevation_mm']) + ' m'
        block(f'楼层 {label}｜{s.get("name") or "未命名"}', 2, [f'本层世界基准标高 {elevation}。'])
        rooms = s.get('spaces', [])
        room_ids = {r['label'] for r in rooms}
        lines = [_space_text(r) for r in rooms]
        counts['spaces'] += len(rooms)
        for r in s.get('derived_spaces', []):
            lines.append(f'几何推导区域 {label}:{r["label"]}：用途未知；轴线围合轮廓为 ' + '、'.join(point(p) for p in r.get('outline_xy_mm', [])) + '；不是已验证的净房间。')
        if not lines:
            lines = ['本次未确认房间空间信息；不补造房间，以下直接描述构件布置。']
        block('房间组织', 3, lines)
        owners: dict[str, list[tuple[str, dict]]] = {r['label']: [] for r in rooms}
        owners['公共与共用构件'] = []
        walls = {w['label']: w for w in s.get('walls', [])}
        boundary_by_wall: dict[str, set[str]] = {}
        for room in rooms:
            for wall_id in room.get('boundary_walls', []):
                boundary_by_wall.setdefault(wall_id, set()).add(room['label'])
        for category in ('walls','doors','windows','openings','stairs','slabs','coverings'):
            for item in s.get(category, []):
                counts[category] += 1
                wall = item if category == 'walls' else walls.get(item.get('host_wall'), {})
                connections = (set(wall.get('spaces', [])) | boundary_by_wall.get(wall.get('label'), set())) & room_ids
                owner = next(iter(connections)) if len(connections) == 1 else '公共与共用构件'
                owners[owner].append((category, item))
        block('构件位置', 3, ['以下每个构件仅完整描述一次；共用或归属未确认的构件集中列出，房间引用不生成副本。'])
        for owner, items in owners.items():
            if not items:
                continue
            block(f'房间 {owner}的构件' if owner != '公共与共用构件' else owner, 4,
                  [_component_text(c, i) for c, i in items])
        groups: dict[str, list[str]] = {}
        for category in CATEGORIES:
            for item in s.get(category, []):
                if category == 'openings':
                    continue
                materials = item.get('materials', [])
                desc = '；'.join(_material_text(m) for m in materials) if materials else '本次材料关联未确认'
                groups.setdefault(desc, []).append(item['label'])
        block('材料', 3, ['、'.join(labels) + '：' + desc + '。' for desc, labels in groups.items()] or ['本层没有已确认的材料关联。'])
    limits = ['本说明不将包围盒相交当作房间冲突，也不将几何邻近当作通行；空间用途及未提取信息继续保持未确认。']
    for code, n in sorted(__import__('collections').Counter(i['code'] for i in facts.get('issues', [])).items()):
        limits.append(f'本次记录 {code} 类提取或推导限制 {n} 项。')
    omitted = facts.get('unrepresented_classes', {})
    if omitted:
        limits.append('尚未逐件描述的源构件类别及数量：' + '、'.join(f'{c} {n}' for c, n in sorted(omitted.items())) + '；不声称整栋建筑所有类别均已覆盖。')
    block('总结与限制', 2, limits)
    return {'schema_version': 'text2ifc/ifc2text-hierarchy/0.3', 'blocks': blocks,
            'component_counts': counts, 'precision': {'coordinate_unit':'m', 'decimal_places':2},
            'fact_fragment_count': counter, 'unrepresented_classes': omitted}


def batch_plan(plan: dict[str, Any], *, max_chars: int = 6000) -> list[dict[str, Any]]:
    if max_chars < 500:
        raise ValueError('BATCH_LIMIT_TOO_SMALL')
    # Split only between complete fact fragments; never truncate items or drop rooms.
    batches: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    size = 0
    for block in plan['blocks']:
        for item in block['items']:
            overhead = 150 + len(block['title'])
            cost = len(json.dumps(item, ensure_ascii=False)) + overhead
            if cost > max_chars:
                raise ValueError(f'SINGLE_FACT_EXCEEDS_BATCH_LIMIT:{item["id"]}')
            if current and size + cost > max_chars:
                batches.append({'blocks': current})
                current, size = [], 0
            if not current or current[-1]['id'] != block['id']:
                current.append({k: block[k] for k in ('id','title','level')})
                current[-1]['items'] = []
            current[-1]['items'].append(dict(item))
            size += cost
    if current:
        batches.append({'blocks': current})
    for n, batch in enumerate(batches, 1):
        batch['batch_id'] = f'batch-{n:03d}'
    return batches


def assemble_hierarchy(plan: dict[str, Any], outputs: list[dict[str, Any]]) -> str:
    expected = [(b['id'], i['id']) for b in plan['blocks'] for i in b['items']]
    actual = []
    paragraphs: dict[str, list[list[str]]] = {}
    for output in outputs:
        if set(output) != {'schema_version','groups'} or output['schema_version'] != LAYOUT_VERSION:
            raise ValueError('LAYOUT_SCHEMA_INVALID')
        for group in output['groups']:
            if set(group) != {'block_id','paragraphs'} or not isinstance(group['paragraphs'], list):
                raise ValueError('LAYOUT_GROUP_INVALID')
            for paragraph in group['paragraphs']:
                if not isinstance(paragraph, list) or not paragraph or any(not isinstance(v, str) for v in paragraph):
                    raise ValueError('LAYOUT_PARAGRAPH_INVALID')
                actual.extend((group['block_id'], item_id) for item_id in paragraph)
            paragraphs.setdefault(group['block_id'], []).extend(group['paragraphs'])
    if actual != expected:
        raise ValueError('LAYOUT_COVERAGE_OR_ORDER_INVALID')
    chunks = ['# 建筑设计说明']
    for block in plan['blocks']:
        chunks.append('#' * block['level'] + ' ' + block['title'])
        by_id = {i['id']: i['text'] for i in block['items']}
        for group in paragraphs[block['id']]:
            chunks.append(''.join(by_id[ref] for ref in group))
    return '\n\n'.join(chunks) + '\n'
