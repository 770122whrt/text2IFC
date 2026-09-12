import html
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(root), str(root/'src')]
from text2ifc_ifc_repair.index_store import SQLiteIndexRepository
from text2ifc_ifc_repair.target_query import TargetQuery, resolve_target
from markdown_it import MarkdownIt

case = root/'dataset/processed/proof/repair/phase12.1/semantic-appearance-20260908/vvo-instance-properties'
repo = SQLiteIndexRepository.open(root/'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01/repair/runtime-live-04/runs/repair-vvo-property-relation-live-04/index/targets.sqlite')
target = repo.get_by_global_id('2CsmzAChHF6O6maGXlo6PS')
query = TargetQuery(allowed_ifc_classes=('IfcWall',), storey_name=target.storey_name,
    geometry_constraints=({'field':'wall_length_mm','value':2220,'tolerance_mm':10},
                          {'field':'wall_thickness_mm','value':240,'tolerance_mm':1}))
resolved = resolve_target(repo, query)
assert resolved.status == 'ambiguous' and len(resolved.candidates) >= 2
(case/'evidence/no-guid-location-boundary.json').write_text(json.dumps({
    'basis':'Read-only current damaged IFC index; no Provider call',
    'user_selector':'标高0层，约2.22米长、240毫米厚的墙',
    'query':{'storey_name':query.storey_name,'geometry_constraints':query.geometry_constraints,'global_id':None},
    'result':resolved.to_dict(),
    'limitation':'direction currently means signed wall axis orientation, not building facade position; north facade / ordinal position not expressible in current query schema.'},ensure_ascii=False,indent=2),encoding='utf-8')

records = [r for r in repo.iter_records() if r.storey_name == target.storey_name and r.ifc_class in {'IfcWall','IfcWallStandardCase'}
           and 'coordinate_basis' in r.geometry_summary]
segments = []
for r in records:
    g = r.geometry_summary
    b = g['coordinate_basis']
    s = b['world_axis_start_mm']
    d = b['world_axis_direction']
    length = g['dimensions_mm']['length']
    segments.append((r, s[:2], [s[i]+d[i]*length for i in [0,1]]))
xs=[p[0] for _,a,b in segments for p in [a,b]]
ys=[p[1] for _,a,b in segments for p in [a,b]]
scale=min(900/(max(xs)-min(xs)),680/(max(ys)-min(ys)))
def point(p): return [70+(p[0]-min(xs))*scale,110+(max(ys)-p[1])*scale]
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="900" viewBox="0 0 1120 900">',
     '<rect width="1120" height="900" fill="#fafaf5"/>',
     '<g font-family="sans-serif" fill="#283c32"><text x="45" y="38" font-size="24">标高0层 · 墙体轴线定位示意</text>',
     '<text x="45" y="70" font-size="15">依据损坏 IFC 的实际墙轴线；北向为模型 +Y。仅作定位，不是施工平面图。</text></g>']
for r,a,b in segments:
    a,b=point(a),point(b)
    chosen=r.record_id==target.record_id
    svg.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{"#d66532" if chosen else "#7a8580"}" stroke-width="{9 if chosen else 5}" stroke-linecap="round"/>')
    if chosen:
        mid=[(a[i]+b[i])/2 for i in [0,1]]
        svg += [f'<circle cx="{mid[0]}" cy="{mid[1]}" r="17" fill="none" stroke="#d66532" stroke-width="2"/>',
                f'<path d="M {mid[0]} {mid[1]} L {mid[0]+80} {mid[1]+55} L {mid[0]+270} {mid[1]+55}" fill="none" stroke="#d66532" stroke-width="2"/>',
                f'<text x="{mid[0]+85}" y="{mid[1]+48}" font-family="sans-serif" font-size="17" fill="#a54319">目标短墙：长约 2.218m，厚 240mm</text>']
svg += ['<path d="M1040 180 L1040 110 L1032 127 M1040 110 L1048 127" stroke="#283c32" stroke-width="3" fill="none"/>',
        '<text x="1028" y="100" font-family="sans-serif" font-size="18">北</text>',
        '<text x="45" y="855" font-family="sans-serif" font-size="16">橙色：北侧西半部，三段短横墙中最靠东的一段。旁边还有一段约 2.215m 的墙。</text>', '</svg>']
(case/'evidence/views/location-plan.svg').write_text('\n'.join(svg),encoding='utf-8')

path=case/'REPORT.md'
before=path.read_bytes()
(case/'evidence/report-before-human-language.md').write_bytes(before)
report=before.decode('utf-8')
intro='''## 这案到底修了什么？

墙一直都在，形状也没有坏。我们人为断开了“这面墙”和“它的资料页”之间的一条连接。修复后，软件可以重新从这面墙直接读到原有信息。因此原始、损坏、修复三个模型的外观相同；这案应看属性前后对照，不能用“有没有补出一面墙”判断成功。

本案是一个偏底层的属性关联测试，原始请求确实比较技术化，不能当作“已证明理解普通工程师语言”的案例。

## 不用输入 GUID，怎样找到这面墙？

在楼层列表选择 **“标高0”**，查看**北侧西半部的折线外墙，三段短横墙中最靠东的一段**；墙长约 **2.218 米**、厚 **240 毫米**。下面的橙色段就是目标，点击原始／损坏／修复视图的定位链接也能直接选中它。

![目标墙的平面定位](evidence/views/location-plan.svg)

“标高0”是源模型中的楼层名称，其实际标高约 -2.344 米，不能直接替它改叫“一层”。GUID 只作为内部稳定编号留在真实请求和机器证据里，不要求人工抄写。

**当前能力边界：** 楼层＋约 2.22 米长度会同时命中两段墙，现有代码正确返回多候选。任意“北侧／从西数第二个／距转角若干米”的组合定位还需要补充空间位置合同与澄清流程；本页的人工定位说明不等于该生产能力已实现。

下一份自然语言请求可以采用这样的表达（**示意，尚未作为新的 Provider 输入执行**）：

> 请检查“标高0”层北侧西半部的折线外墙，最靠东那段约2.2米长、240毫米厚的墙。它的属性页里外墙标记和参考编号缺失了。请根据输入模型中仍能确认的信息恢复；如果目标或原值不唯一，先让我确认，不要改墙的形状或旁边的构件。

'''
report=report.replace('## 原始、破坏、修复三份 IFC',intro+'## 原始、破坏、修复三份 IFC',1)
report=report.replace('[实际公共请求](request.html)指定目标墙 `2CsmzAChHF6O6maGXlo6PS`（基本墙:240:223174）的实例 Pset_WallCommon。',
    '[保留的原始技术请求](request.html)指定上图目标墙的常用属性资料。')
report=report.replace('| Reference | "240" | 此直接关联缺失 | "240" | IfcIdentifier |','| 参考编号（Reference） | "240" | 墙的直接资料连接缺失 | "240" | IfcIdentifier |')
report=report.replace('| IsExternal | true | 此直接关联缺失 | true | IfcBoolean |','| 标记为外墙（IsExternal） | 是 | 墙的直接资料连接缺失 | 是 | IfcBoolean |')
report=report.replace('| ExtendToStructure | false | 此直接关联缺失 | false | IfcBoolean |','| 延伸到结构标记（ExtendToStructure） | 否 | 墙的直接资料连接缺失 | 否 | IfcBoolean |')
report=report.replace('| LoadBearing | false | 此直接关联缺失 | false | IfcBoolean |','| 承重墙标记（LoadBearing） | 否 | 墙的直接资料连接缺失 | 否 | IfcBoolean |')
report=report.replace('## 中文请求全文','## 原始技术请求全文（真实输入，原样保留）')
path.write_text(report,encoding='utf-8')
# Refresh the existing view; do not create a new website or viewer.
existing=(case/'REPORT.html').read_text(encoding='utf-8')
prefix=existing[:existing.index('</style>')+len('</style>')]
(case/'REPORT.html').write_text(prefix+MarkdownIt('commonmark').enable('table').render(report)+'</html>',encoding='utf-8')
print(json.dumps({'report_updated':True,'ifc_and_request_unchanged':True,'no_guid_query_status':resolved.status,'candidate_count':len(resolved.candidates)}))
