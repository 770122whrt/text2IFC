"""Retain wall coordinates through text; historical renderers stay unchanged."""
from .compact import bounds, cell, mm1, pt, wall_bbox_needed
from .component_description_v10 import _n, _vec
from .component_description_v11 import component_description as previous
from .observation import all_items
from .wall_details_v08 import detail_text


def _number(value):
    return '未确认' if value is None else _n(value)


def _point(value):
    return '未确认' if value is None else _vec(value)


def component_description(facts, narration=None):
    text = previous(facts, narration)
    for category, wall in all_items(facts):
        if category != 'walls':
            continue
        common = [bounds(wall) if wall_bbox_needed(wall) else '—',
                  ','.join(wall.get('spaces', [])) or '未确认']
        old = [wall['label'], pt(wall.get('axis_start_mm'))+'→'+pt(wall.get('axis_end_mm')),
               mm1(wall.get('thickness_mm'))+'×'+mm1(wall.get('height_mm')), *common]
        new = [wall['label'], _point(wall.get('axis_start_mm'))+'→'+_point(wall.get('axis_end_mm')),
               _number(wall.get('thickness_mm'))+'×'+_number(wall.get('height_mm')), *common]
        before = '|'+ '|'.join(cell(v) for v in old)+'|'
        after = '|'+ '|'.join(cell(v) for v in new)+'|'
        if text.count(before) != 1:
            raise ValueError('WALL_TABLE_ROW_NOT_UNIQUE')
        text = text.replace(before, after, 1)
        detail = wall.get('solid_detail', {})
        if detail.get('requires_explicit_outline') and detail.get('status') == 'supported_vertical_extrusion':
            points = detail['bottom_outline_xy_mm']
            if points[0] != points[-1]:
                points = [*points, points[0]]
            replacement = ('**墙 '+wall['label']+' 的实体轮廓**：底面闭合外轮廓（世界XY，mm）'+
                           '→'.join(_vec(p) for p in points)+'；底面Z='+_n(detail['bottom_z_mm'])+
                           '；+Z拉伸 '+_n(detail['height_mm'])+'。')
            before = detail_text(wall)
            if text.count(before) != 1:
                raise ValueError('DETAILED_WALL_NOT_UNIQUE')
            text = text.replace(before, replacement, 1)
    return text.replace('## 总体与读图约定\n',
        '## 总体与读图约定\n\n墙体轴线、厚度与显式实体轮廓保留提取数值，最多显示九位小数；'
        '这表示数值传递精度，不表示源模型的测量精度。坐标换算时不再取整。'
        '普通矩形墙按轴线、厚度和高度参数建立；另列实体轮廓的墙保留该轮廓，不用矩形替代。\n', 1)
