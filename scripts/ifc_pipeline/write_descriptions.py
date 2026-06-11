"""
Generate natural language descriptions for each IFC model.
Based on parsed data + architectural knowledge.
"""
import json, sys, os, re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

with open('E:/code for project/bimnet/dataset/ifc_parsed_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)


def classify_wall(name):
    if '外' in name or 'Exterior' in name or 'Outer' in name: return '外墙'
    elif '内' in name or 'Interior' in name: return '内墙'
    elif '隔' in name or 'Partition' in name: return '隔墙'
    elif 'Generic' in name: return '通用墙'
    else: return '墙体'

def get_thickness(name):
    m = re.search(r'(\d+)mm', name)
    if m: return int(m.group(1))
    m = re.search(r'[:\-]\s*(\d{2,3})(?:[:\s]|$)', name)
    if m: return int(m.group(1))
    return None

def classify_door(name):
    if '双扇' in name or 'Double' in name: return '双扇门'
    elif '单扇' in name or 'Single' in name: return '单扇门'
    elif '平开' in name: return '平开门'
    elif '推拉' in name or 'Sliding' in name: return '推拉门'
    else: return '门'

def classify_window(name):
    if '推拉' in name or 'Sliding' in name: return '推拉窗'
    elif '固定' in name or 'Fixed' in name: return '固定窗'
    elif '平开' in name or 'Casement' in name: return '平开窗'
    else: return '窗'

def describe_model(d):
    """Generate a rich natural language description for one IFC model."""
    lines = []
    fname = d['filename']
    storeys = d['storeys']
    walls = d['walls']
    cols = d['columns']
    beams = d['beams']
    slabs = d['slabs']
    doors = d['doors']
    wins = d['windows']
    mats = d['materials']
    stairs = d['stairs']
    roofs = d['roofs']
    mep = d['mep']

    # ── Header ──
    lines.append(f"# IFC模型描述: {fname}")
    lines.append("")
    lines.append(f"- Schema版本: {d['schema']}")
    lines.append(f"- 数据集划分: {d['split']}")
    lines.append("")

    # ── Building Overview ──
    lines.append("## 1. 建筑概况")
    lines.append("")

    # Infer building type
    total_doors = len(doors)
    total_windows = len(wins)
    total_walls = len(walls)
    has_stairs = len(stairs) > 0
    num_storeys = len(storeys)

    # Classify wall types
    ext_walls = [w for w in walls if w.get('is_external') == True]
    int_walls = [w for w in walls if w.get('is_external') == False]
    wall_type_counts = {}
    thicknesses = set()
    load_bearing_count = 0
    for w in walls:
        wt = classify_wall(w['name'])
        wall_type_counts[wt] = wall_type_counts.get(wt, 0) + 1
        t = get_thickness(w['name'])
        if t: thicknesses.add(t)

    # Storey info
    storey_desc = []
    for s in storeys:
        elev_m = s['elev'] / 1000 if s['elev'] else 0
        storey_desc.append(f"{s['name']}（标高{elev_m:.2f}m）")

    lines.append(f"本模型为{d['schema']}格式的BIM模型，包含{num_storeys}个楼层：{'、'.join(storey_desc)}。")

    # Building scale estimation
    if num_storeys >= 6:
        lines.append(f"这是一栋{num_storeys}层建筑，属于中高层建筑。")
    elif num_storeys >= 3:
        lines.append(f"这是一栋{num_storeys}层建筑，属于多层建筑。")
    else:
        lines.append(f"这是一栋{num_storeys}层建筑，属于低层建筑。")

    lines.append("")

    # ── Structural System ──
    lines.append("## 2. 结构体系")
    lines.append("")

    # Determine structural type
    has_frame = len(cols) > 0 or len(beams) > 0
    wall_bearing = any('LoadBearing' in str(w) for w in walls)

    if has_frame and total_walls > 20:
        struct_type = "框架-剪力墙结构"
    elif has_frame:
        struct_type = "框架结构"
    elif total_walls > 30:
        struct_type = "剪力墙结构"
    else:
        struct_type = "砖混结构"

    lines.append(f"根据构件组成判断，本建筑可能为**{struct_type}**。")
    lines.append("")

    # Walls
    lines.append(f"### 2.1 墙体")
    lines.append("")
    lines.append(f"共{total_walls}面墙体。")

    if ext_walls and int_walls:
        lines.append(f"- 外墙{len(ext_walls)}面，内墙{len(int_walls)}面")
    elif ext_walls:
        lines.append(f"- 外墙{len(ext_walls)}面（模型中所有墙均标记为外墙）")

    if thicknesses:
        lines.append(f"- 墙厚种类：{', '.join(str(t)+'mm' for t in sorted(thicknesses))}")
        main_thickness = max(set(thicknesses), key=lambda t: sum(1 for w in walls if get_thickness(w['name']) == t))
        lines.append(f"- 主要墙厚：{main_thickness}mm")

    for wt, cnt in wall_type_counts.items():
        lines.append(f"- {wt}：{cnt}面")

    lines.append("")

    # Columns
    if cols:
        lines.append(f"### 2.2 柱子")
        lines.append("")
        lines.append(f"共{len(cols)}根柱子。")
        col_types = {}
        for c in cols:
            ct = c['name'].split(':')[1] if ':' in c['name'] else c['name']
            col_types[ct] = col_types.get(ct, 0) + 1
        for ct, cnt in col_types.items():
            lines.append(f"- {ct}：{cnt}根")
        lines.append("")

    # Beams
    if beams:
        lines.append(f"### 2.3 梁")
        lines.append("")
        lines.append(f"共{len(beams)}根梁。")
        beam_types = {}
        for b in beams:
            bt = b['name'].split(':')[0] if ':' in b['name'] else b['name']
            beam_types[bt] = beam_types.get(bt, 0) + 1
        for bt, cnt in beam_types.items():
            lines.append(f"- {bt}：{cnt}根")
        lines.append("")

    # Slabs
    if slabs:
        lines.append(f"### 2.4 楼板")
        lines.append("")
        lines.append(f"共{len(slabs)}块楼板。")
        for s in slabs:
            lines.append(f"- {s['name']}（类型：{s['pretype']}）")
        lines.append("")

    # Roofs
    if roofs:
        lines.append(f"### 2.5 屋顶")
        lines.append("")
        lines.append(f"共{len(roofs)}个屋顶构件。")
        for r in roofs:
            lines.append(f"- {r['name']}")
        lines.append("")

    # Stairs
    if stairs:
        lines.append(f"### 2.6 楼梯")
        lines.append("")
        lines.append(f"共{len(stairs)}个楼梯/梯段构件。")
        lines.append("")

    # ── Openings ──
    lines.append("## 3. 门窗")
    lines.append("")

    if doors:
        door_types = {}
        for do in doors:
            dt = classify_door(do['name'])
            door_types[dt] = door_types.get(dt, 0) + 1
        lines.append(f"### 3.1 门")
        lines.append("")
        lines.append(f"共{len(doors)}扇门。")
        for dt, cnt in door_types.items():
            lines.append(f"- {dt}：{cnt}扇")

        widths = [do['w'] for do in doors if do['w']]
        heights = [do['h'] for do in doors if do['h']]
        if widths:
            lines.append(f"- 宽度范围：{min(widths):.0f}mm ~ {max(widths):.0f}mm")
        if heights:
            lines.append(f"- 高度范围：{min(heights):.0f}mm ~ {max(heights):.0f}mm")

        # Detect large doors (likely entrance)
        large_doors = [do for do in doors if do['w'] and do['w'] > 1500]
        if large_doors:
            lines.append(f"- 其中{len(large_doors)}扇为大门（宽度>1500mm），可能为入口或防火门")

        lines.append("")

    if wins:
        win_types = {}
        for wi in wins:
            wt = classify_window(wi['name'])
            win_types[wt] = win_types.get(wt, 0) + 1
        lines.append(f"### 3.2 窗")
        lines.append("")
        lines.append(f"共{len(wins)}扇窗。")
        for wt, cnt in win_types.items():
            lines.append(f"- {wt}：{cnt}扇")

        widths = [wi['w'] for wi in wins if wi['w']]
        heights = [wi['h'] for wi in wins if wi['h']]
        if widths:
            lines.append(f"- 宽度范围：{min(widths):.0f}mm ~ {max(widths):.0f}mm")
        if heights:
            lines.append(f"- 高度范围：{min(heights):.0f}mm ~ {max(heights):.0f}mm")
        lines.append("")

    if not doors and not wins:
        lines.append("本模型未定义门窗构件。")
        lines.append("")

    # ── Materials ──
    lines.append("## 4. 材料")
    lines.append("")
    if mats:
        lines.append(f"共使用{len(mats)}种材料：")
        for m in mats:
            lines.append(f"- {m}")

        # Classify materials
        concrete_mats = [m for m in mats if '混凝土' in m or 'Concrete' in m or '砼' in m]
        steel_mats = [m for m in mats if '钢' in m or 'Steel' in m or '不锈钢' in m]
        wood_mats = [m for m in mats if '木' in m or 'Wood' in m or '胡桃' in m or '樱桃' in m]
        glass_mats = [m for m in mats if '玻璃' in m or 'Glass' in m]
        aluminum_mats = [m for m in mats if '铝' in m or 'Aluminum' in m or '铝合金' in m]

        lines.append("")
        if concrete_mats:
            lines.append(f"- 混凝土类：{', '.join(concrete_mats)}")
        if steel_mats:
            lines.append(f"- 钢材类：{', '.join(steel_mats)}")
        if wood_mats:
            lines.append(f"- 木材类：{', '.join(wood_mats)}")
        if glass_mats:
            lines.append(f"- 玻璃类：{', '.join(glass_mats)}")
        if aluminum_mats:
            lines.append(f"- 铝材类：{', '.join(aluminum_mats)}")
    else:
        lines.append("本模型未定义材料信息。")
    lines.append("")

    # ── MEP ──
    lines.append("## 5. MEP设备管线")
    lines.append("")
    if mep:
        for m in mep:
            lines.append(f"- {m['type']}: {m['count']}个")
    else:
        lines.append("本模型不包含MEP设备管线构件（暖通、给排水、电气等）。")
    lines.append("")

    # ── Summary ──
    lines.append("## 6. 模型特征总结")
    lines.append("")
    complexity = '复杂' if total_walls > 60 or len(doors) > 25 else '中等' if total_walls > 30 else '简单'
    lines.append(f"- 建筑规模：{num_storeys}层，{complexity}模型")
    lines.append(f"- 构件统计：{total_walls}墙、{len(cols)}柱、{len(beams)}梁、{len(slabs)}板、{len(doors)}门、{len(wins)}窗")
    lines.append(f"- 结构类型：{struct_type}")
    lines.append(f"- MEP：{'有' if mep else '无'}")
    lines.append(f"- 楼梯：{'有' if stairs else '无'}")
    lines.append(f"- 屋顶：{'有' if roofs else '无'}")

    return '\n'.join(lines)


# ── Main ──
output_dir = Path("E:/code for project/bimnet/dataset/ifc_descriptions")
output_dir.mkdir(parents=True, exist_ok=True)

for d in data:
    fname = d['filename'].replace('.ifc', '')
    desc = describe_model(d)
    out_path = output_dir / f"{fname}.txt"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(desc)
    print(f"✓ {d['filename']} → {out_path.name}")

print(f"\n完成! {len(data)}个描述文件保存在: {output_dir}")
