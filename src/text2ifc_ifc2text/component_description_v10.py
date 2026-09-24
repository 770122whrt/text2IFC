"""Human-readable native parameters, attached to each floor's door/window list."""
from __future__ import annotations

import copy
import math
import re

import ifcopenshell
import ifcopenshell.util.placement
import ifcopenshell.util.unit

from .component_details_v10 import read_component_geometry, _position, _rigid
from .observation import all_items
from .opening_details_v09 import opening_description


def enrich_component_details(source, facts):
    result=copy.deepcopy(facts)
    model=ifcopenshell.open(str(source))
    scale=ifcopenshell.util.unit.calculate_unit_scale(model)*1000.
    for category,item in all_items(result):
        if category not in {'doors','windows'}:
            continue
        product=model.by_guid(item['source_global_id'])
        detail=read_component_geometry(product)
        if detail['status']=='supported':
            matrix=ifcopenshell.util.placement.get_local_placement(product.ObjectPlacement)
            _rigid(matrix)
            detail['product_world_placement']=_position(matrix,scale)
        item['component_detail']=detail
    result['component_detail_version']='text2ifc/ifc2text-component-detail/1.0'
    return result


def _n(value):
    value=float(value)
    if not math.isfinite(value):
        raise ValueError('NONFINITE_COMPONENT_PARAMETER')
    # Nine decimals retain unit directions even when multiplied by long extrusions.
    return f'{value:.9f}'.rstrip('0').rstrip('.') if value else '0'


def _vec(values):
    return '('+','.join(_n(v) for v in values)+')'


def _pose(value):
    return '原点'+_vec(value['origin'])+'，局部Z轴'+_vec(value['axis'])+'，局部X轴'+_vec(value['ref_direction'])


def _profile(value):
    kind=value['kind']
    if kind=='rectangle':
        return '中心矩形，X向尺寸='+_n(value['x'])+'，Y向尺寸='+_n(value['y'])
    if kind=='circle':
        return '中心圆形，半径='+_n(value['radius'])
    if kind=='polygon':
        text='多边形，闭合外环='+'→'.join(_vec(p) for p in value['points'])
        for index,ring in enumerate(value.get('holes',[]),1):
            text+='；内环'+str(index)+'='+'→'.join(_vec(p) for p in ring)
        return text
    raise ValueError('UNSUPPORTED_COMPONENT_PROFILE')


def describe_component(item):
    detail=item.get('component_detail')
    if not detail:
        raise ValueError('COMPONENT_DETAIL_REQUIRED: '+item['label'])
    lines=['#### '+item['label']+' 部件几何']
    if detail['status']=='unsupported':
        lines.append('本构件不支持完整重建，需要人工确认。拒绝以普通门窗模板、包围盒或已支持的部分实体替代。')
        for issue in detail['unsupported']:
            lines.append('- 不支持 '+issue['ifc_class']+'：'+issue['reason'])
        return '\n'.join(lines)
    if detail['status']!='supported':
        raise ValueError('UNKNOWN_COMPONENT_DETAIL_STATUS')
    lines.append('整体仍是一扇'+item['ifc_class']+'；以下部件是该构件的几何组成，不另建门窗产品。')
    if not item.get('host_wall') and not item.get('opening'):
        lines.append('源模型未提供宿主墙和开口，按独立构件保留，不新增宿主或开口；归层沿用上表。')
    lines.append('构件放置（世界坐标）：'+_pose(detail['product_world_placement'])+'。名义宽高沿用上表，部件几何不按名义尺寸缩放。')
    lines.append('长度为mm；下列部件位置相对于构件，实体位置相对于部件，截面位于实体局部XY平面；挤出方向相对于实体。局部Y轴=Z轴×X轴，方向向量须归一化。')
    rep=detail['representation']
    lines.append('实体定义：')
    for d in rep['definitions']:
        lines.append('- '+d['id']+'：'+_profile(d['profile'])+'；实体坐标系：'+_pose(d['position'])+
                     '；挤出方向'+_vec(d['direction'])+'，深度='+_n(d['depth'])+'。')
    lines.append('部件与实体引用：')
    for p in rep['parts']:
        text='- '+p['id']+'：角色='+p['role']+'；实体='+','.join(p['geometry_refs'])+'；部件坐标系：'+_pose(p['placement'])
        if p.get('repeat'):
            text+='；重复数量='+str(p['repeat']['count'])+'，平移步长（构件坐标系）='+_vec(p['repeat']['step'])
        if p.get('appearance'):
            text+='；RGB='+_vec(p['appearance']['color'])+'，透明度='+_n(p['appearance']['transparency'])
        lines.append(text+'。')
    return '\n'.join(lines)


def component_description(facts,narration=None):
    # Validate coverage before rendering any public output.
    for category,item in all_items(facts):
        if category in {'doors','windows'} and not item.get('component_detail'):
            raise ValueError('COMPONENT_DETAIL_REQUIRED: '+item['label'])
    text=opening_description(facts,narration)
    floors={s['label']:s for s in facts['storeys']}
    floors['UNASSIGNED']=facts.get('unassigned',{})
    chunks=re.split(r'(?=^## 楼层 )',text,flags=re.M)
    for index,chunk in enumerate(chunks):
        match=re.match(r'## 楼层 ([^｜\n]+)',chunk)
        if not match:
            continue
        floor=floors[match.group(1)]
        items=[*floor.get('doors',[]),*floor.get('windows',[])]
        if not items:
            continue
        addition='\n\n### 门窗部件说明\n\n'+'\n\n'.join(describe_component(i) for i in items)+'\n\n'
        # Keep this floor's detail before any document-wide material/unknown section.
        split=re.search(r'^## (?!楼层 )',chunk,flags=re.M)
        at=split.start() if split else len(chunk)
        chunks[index]=chunk[:at]+addition+chunk[at:]
    return ''.join(chunks)
