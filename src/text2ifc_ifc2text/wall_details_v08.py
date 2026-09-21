"""Explicitly closed public wall contours; v0.7 run evidence stays unchanged."""
from __future__ import annotations
import re
from .compact import mm1, ring
from .observation import all_items
from .wall_details_v07 import detailed_description, wall_detail_text

VERSION='text2ifc/ifc2text-wall-detail/0.8'
COMMON=('以下轮廓均为同一墙体扣除洞口之前的实体，不新增墙。点列首尾相同，末尾闭合点不可省略；'
        '按世界XY底面及Z标高定位，沿世界+Z拉伸，不以矩形替代斜端或截短。原有洞口另按其位置扣除一次。')


def closed_ring(points):
    value=ring(points)
    return value+'→'+value.split('→')[0]


def detail_text(wall):
    d=wall['solid_detail']
    return ('**墙 '+wall['label']+' 的实体轮廓**：底面闭合外轮廓（世界XY，mm）'+closed_ring(d['bottom_outline_xy_mm'])+
        '；底面Z='+mm1(d['bottom_z_mm'])+'；+Z拉伸 '+mm1(d['height_mm'])+'。')


def explicit_description(facts,narration=None):
    text=detailed_description(facts,narration)
    for category,w in all_items(facts):
        if category=='walls' and w.get('solid_detail',{}).get('requires_explicit_outline') and w['solid_detail'].get('status')=='supported_vertical_extrusion':
            old=wall_detail_text(w)
            if text.count(old)!=1:raise ValueError('DETAILED_WALL_NOT_UNIQUE')
            text=text.replace(old,detail_text(w))
    parts=re.split(r'(?=^## 楼层 )',text,flags=re.M)
    for n,part in enumerate(parts):
        marker=re.search(r'^\*\*墙 [^\n]+ 的实体轮廓\*\*',part,flags=re.M)
        if marker:parts[n]=part[:marker.start()]+COMMON+'\n\n'+part[marker.start():]
    return ''.join(parts)


def single_wall_description(wall):
    d=wall['solid_detail']
    return ('建立一个单墙几何诊断模型，不是整栋建筑。长度均为mm，XY即世界坐标系。'+
        '基本层级为项目、场地、建筑、一个楼层S01，楼层参考标高 '+mm1(d['bottom_z_mm'])+'。'+
        '只创建一面墙，不生成空间、楼板、屋顶、门窗、洞口或楼梯，无材料和外观要求。\n\n'+COMMON+'\n\n'+
        detail_text(wall)+'\n\n本单墙诊断不含洞口，不做扣洞操作。闭合点列的最后一项与第一项完全相同，请原样保留。\n')
