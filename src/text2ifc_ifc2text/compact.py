"""Compact human-readable text, not lossy prose summarization of measured geometry.

The LLM writes a short architectural reading guide; deterministic tables preserve
coordinates and relations. Source identity and machine facts never enter the
reconstruction API. Original 0.3 renderers and evidence remain unchanged.
"""
from __future__ import annotations
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import json
import math
import re
from typing import Any
from .observation import CATEGORIES, all_items


def mm1(value: Any) -> str:
    if value is None:
        return '未确认'
    if isinstance(value, bool) or not math.isfinite(float(value)):
        raise ValueError('NONFINITE_COORDINATE')
    number = Decimal(str(value)).quantize(Decimal('.1'), rounding=ROUND_HALF_UP)
    return format(abs(number) if number == 0 else number, '.1f')


def pt(values) -> str:
    return '未确认' if values is None else '(' + ','.join(mm1(v) for v in values) + ')'


def cell(value) -> str:
    return str(value if value not in (None, '') else '未确认').replace('|','／').replace('\n',' ')


def bounds(item) -> str:
    b=item.get('bounds_mm')
    return '未确认' if not b else '/'.join(mm1(b[k][0])+'~'+mm1(b[k][1]) for k in ('x','y','z'))


def ring(points) -> str:
    # Display rounding only; no simplification of the measured shape.
    from shapely.geometry import Polygon
    p=[]
    for value in points:
        v=tuple(float(mm1(x)) for x in value)
        if not p or p[-1]!=v:
            p.append(v)
    if p and p[0]==p[-1]: p.pop()
    if len(p)<3 or not Polygon(p).is_valid or Polygon(p).area<=0:
        raise ValueError('ROUNDING_INVALID_RING')
    return '→'.join(pt(v) for v in p)


def footprint(item) -> str:
    f=item.get('footprint',{})
    if f.get('status')!='measured_projection':
        return '轮廓未确认；包围盒XYZ='+bounds(item)
    parts=[]
    for p in f['polygons']:
        text=ring(p['exterior_xy_mm'])
        for h in p.get('holes_xy_mm',[]): text+='；内环 '+ring(h)
        parts.append(text)
    return '；分离部分 '.join(parts)+'；Z='+ '~'.join(mm1(z) for z in f['z_range_mm'])


def material_text(m) -> str:
    origin='直接' if m.get('origin')=='occurrence' else '继承'
    kind=m['kind']
    if kind=='single_material': return origin+'：'+cell(m.get('name'))
    if kind=='material_list': return origin+'材料列表（非分层）：'+ '、'.join(cell(v) for v in m['names'])
    if kind in ('material_layer_set','material_layer_set_usage'):
        text=origin+'层序：'+' / '.join(cell(l.get('name'))+':'+mm1(l.get('thickness_mm')) for l in m['layers'])
        if kind=='material_layer_set_usage': text+='；'+str(m.get('direction'))+','+str(m.get('direction_sense'))+',偏移'+mm1(m.get('offset_mm'))
        return text
    return '关联形式尚不支持：'+cell(m.get('ifc_class',kind))


def material_catalog(facts):
    catalog={}; assignments={}
    for _,i in all_items(facts):
        ms=i.get('materials',[])
        if not ms: continue
        key='；'.join(material_text(m) for m in ms)
        if key not in catalog: catalog[key]='M'+str(len(catalog)+1).zfill(2)
        assignments[i['label']]=catalog[key]
    return catalog, assignments


def wall_bbox_needed(w):
    a,b=w.get('axis_start_mm'),w.get('axis_end_mm')
    box=w.get('bounds_mm'); t=w.get('thickness_mm'); h=w.get('height_mm')
    if a is None or b is None or box is None or t is None or h is None: return True
    d=math.hypot(b[0]-a[0],b[1]-a[1])
    if d<=0 or w.get('measurement_method')=='world_mesh_principal_axis': return True
    nx,ny=-(b[1]-a[1])/d,(b[0]-a[0])/d
    expected={'x':[min(a[0],b[0])-abs(nx)*t/2,max(a[0],b[0])+abs(nx)*t/2],
              'y':[min(a[1],b[1])-abs(ny)*t/2,max(a[1],b[1])+abs(ny)*t/2],
              'z':[a[2],a[2]+h]}
    return any(abs(x-y)>.2 for k in expected for x,y in zip(expected[k],box[k]))


def table(headers, rows):
    return '\n'.join(['|'+'|'.join(headers)+'|','|'+'|'.join('---' for _ in headers)+'|']+
                     ['|'+'|'.join(cell(c) for c in row)+'|' for row in rows])


def narrative_context(facts):
    catalog,_=material_catalog(facts)
    return {'storeys':[{'id':s['label'],'name':s.get('name'),
          'counts':{c:len(s.get(c,[])) for c in CATEGORIES},
          'derived_region_count':len(s.get('derived_spaces',[])),
          'boundary_relation_confirmed':any(r.get('boundary_walls') for r in s.get('spaces',[]))}
          for s in facts['storeys']],
          'material_descriptions':list(catalog),
          'limitations':dict(Counter(i['code'] for i in facts.get('issues',[]))),
          'not_described_classes':facts.get('unrepresented_classes',{})}


def validate_narration(output, context):
    if set(output)!={'overview','storey_notes'}: raise ValueError('NARRATION_FIELDS')
    if not isinstance(output['overview'],str) or len(output['overview'])>350: raise ValueError('OVERVIEW_LENGTH')
    ids=[s['id'] for s in context['storeys']]
    if [s['storey'] for s in output['storey_notes']]!=ids: raise ValueError('NARRATION_STOREYS')
    known=set(re.findall(r'\d+(?:\.\d+)?',json.dumps(context,ensure_ascii=False)))
    for part in [output['overview'],*[s['text'] for s in output['storey_notes']]]:
        if not isinstance(part,str) or len(part)>350: raise ValueError('NARRATION_LENGTH')
        if not set(re.findall(r'\d+(?:\.\d+)?',part))<=known: raise ValueError('NARRATION_NEW_NUMBER')
    # This guard does not certify qualitative prose; agent review remains required.


def compact_description(facts, narration=None) -> str:
    catalog,mats=material_catalog(facts)
    out=['# 建筑设计说明',
         '## 总体与读图约定',
         '本说明用于重建所述建筑。坐标与尺寸统一为毫米（mm），坐标保留一位小数；XY为源模型坐标轴，不假定地理北向。三维点写作(X,Y,Z)，轮廓为XY顶点顺序并自动闭合。楼层是源模型的标高记录，不等于使用楼层数量。',
         '以下表格均属于设计说明，不是另附模型。每个编号只创建一次。房间先描述，构件后定位，材料在各层末尾关联。未确认的用途、空间归属、材料和细节不补造。']
    if narration: out.append(narration['overview'])
    notes={s['storey']:s['text'] for s in narration['storey_notes']} if narration else {}
    floors=list(facts['storeys'])
    if any(facts.get('unassigned',{}).get(c) for c in CATEGORIES):
        floors.append({**facts['unassigned'],'label':'UNASSIGNED','name':'归属未确认','elevation_mm':None})
    for s in floors:
        out.append('## 楼层 '+s['label']+'｜'+cell(s.get('name'))+'；标高 '+mm1(s.get('elevation_mm')))
        if notes.get(s['label']): out.append(notes[s['label']])
        out.append('### 房间')
        for r in s.get('spaces',[]):
            out.append('**'+r['label']+'｜'+cell(r.get('long_name') or r.get('name'))+'**：'+footprint(r)+
                ('；边界墙 '+','.join(r['boundary_walls']) if r.get('boundary_walls') else '；边界墙未确认')+'。')
        for r in s.get('derived_spaces',[]):
            points=r.get('outline_xy_mm',[])
            out.append('**推导区域 '+s['label']+':'+r['label']+'**：'+(ring(points) if points else '轮廓未确认')+'；仅为墙轴围合候选，不是已核实的净房间，用途未知。')
        if not s.get('spaces') and not s.get('derived_spaces'): out.append('房间信息未确认，直接按下表布置构件。')
        out.append('### 构件位置')
        if s.get('walls'):
            out.append('墙体：A、B为三维参考轴端点，t为厚度，h为高度；“—”表示实体包围盒与该轴居中直墙的范围相符，仅省去重复范围，不保证精细形状相同。其他范围按X/Y/Z列示。共享墙仅建一次。')
            out.append(table(['墙体','A→B','t×h','特殊包围盒XYZ','关联房间'],[
                [w['label'],pt(w.get('axis_start_mm'))+'→'+pt(w.get('axis_end_mm')),
                 mm1(w.get('thickness_mm'))+'×'+mm1(w.get('height_mm')),
                 bounds(w) if wall_bbox_needed(w) else '—',','.join(w.get('spaces',[])) or '未确认'] for w in s['walls']]))
        if s.get('openings'):
            out.append('开口：s为沿宿主参考轴自起点的中心距离，b为开口底部相对墙底高度，n为法向偏移；w/h/d为在宿主局部坐标中的几何尺寸。开口是切割体，不一定是门窗洞；偏移或深度异常者不假定为常规通行口。填充门窗另列，不重复造洞。')
            out.append(table(['开口','宿主墙','w×h×d','s,b,n','填充'],[
                [i['label'],i.get('host_wall'),'×'.join(mm1(i.get('dimensions_mm',{}).get(k)) for k in ('width','height','depth')),
                 ','.join(mm1((i.get('host_position_mm') or {}).get(k)) for k in ('center_offset_mm','sill_height_mm','normal_offset_mm')),i.get('filling') or '无已确认填充'] for i in s['openings']]))
        for c,title in [('doors','门'),('windows','窗')]:
            if not s.get(c): continue
            out.append(title+'：名义尺寸与实体几何范围分别保留；造型未详述时不能把包围盒当作完整门窗形状。宿主可能位于其他楼层。')
            out.append(table([title,'宿主墙/开口','名义宽×高','实体包围盒X/Y/Z'],[
                [i['label'],cell(i.get('host_wall'))+'/'+cell(i.get('opening')),
                 mm1(i.get('overall_width_mm'))+'×'+mm1(i.get('overall_height_mm')),bounds(i)] for i in s[c]]))
        for c,title in [('slabs','楼板'),('coverings','覆盖层')]:
            for i in s.get(c,[]):
                out.append('**'+title+' '+i['label']+'**：'+footprint(i)+'；分类 '+cell(i.get('predefined_type'))+'。')
        for i in s.get('stairs',[]):
            out.append('**楼梯 '+i['label']+'**：包围盒XYZ='+bounds(i)+'；几何高度覆盖 '+','.join(i.get('spans_storeys_by_geometry',[]))+'；踏步、梯段、实际连通细节未完整描述。')
        out.append('### 材料')
        groups={}
        for c in CATEGORIES:
            if c=='openings': continue
            for i in s.get(c,[]): groups.setdefault(mats.get(i['label'],'材料关联未确认'),[]).append(i['label'])
        out.append('；'.join(','.join(labels)+'：'+m for m,labels in groups.items())+'。' if groups else '本层无已确认材料关联。')
    if catalog:
        out.append('## 材料索引')
        out.append('层厚同为毫米；列表不代表分层，层序不额外推断内外侧或性能。')
        out.append(table(['编号','源关联'],[[identifier,description] for description,identifier in catalog.items()]))
    out.append('## 未确认项')
    out.append('包围盒不是形心或完整造型，投影不证明通行；空间边界缺项表示本次未提取，不代表源模型一定没有。表格保留范围内的事实，精细实体、用途、实际通行关系不在本次保证范围。')
    issues=Counter(i['code'] for i in facts.get('issues',[]))
    if issues: out.append('提取记录：'+'；'.join(code+'×'+str(n) for code,n in sorted(issues.items()))+'。')
    other=facts.get('unrepresented_classes',{})
    if other: out.append('尚未逐件描述：'+'；'.join(k+'×'+str(v) for k,v in sorted(other.items()))+'；不以此声明整栋所有类别完整。')
    return '\n\n'.join(out)+'\n'
