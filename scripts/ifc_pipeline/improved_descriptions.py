"""
Improved Description Generator - 修复审查报告中所有问题
修复：
1. 楼板按PredefinedType分类
2. 材料分类修正（钢筋混凝土→混凝土，钢化玻璃→玻璃）
3. 结构类型推断加免责声明
4. 楼层分析标高判断地上/地下
5. 外墙全部标记的数据质量声明
6. 墙厚从几何+材料双提取
7. 楼梯分离assembly和flight
"""

import json, sys, os, re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

with open('E:/code for project/bimnet/dataset/processed/ifc_parsed_enhanced.json', 'r', encoding='utf-8') as f:
    data = json.load(f)


def classify_wall(name):
    if '外' in name or 'Exterior' in name or 'Outer' in name: return '外墙'
    elif '内' in name or 'Interior' in name: return '内墙'
    elif '隔' in name or 'Partition' in name: return '隔墙'
    elif 'Generic' in name: return '通用墙'
    else: return '墙体'


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


def classify_material(name):
    """Correct material classification with domain knowledge."""
    n = name.lower()
    # Concrete: 钢筋混凝土, 钢筋砼, concrete → concrete ONLY
    if '钢筋混凝土' in name or '钢筋砼' in name or 'concrete' in n:
        return '混凝土类'
    if '混凝土' in name or '砼' in name:
        return '混凝土类'
    # Glass: 钢化玻璃, 玻璃, glass → glass (NOT steel)
    if '钢化玻璃' in name or '玻璃' in name or 'glass' in n:
        return '玻璃类'
    # Steel: 不锈钢, 钢 (but NOT 钢筋混凝土, 钢化玻璃)
    if '不锈钢' in name or '钢' in name:
        if '钢筋' not in name and '钢化' not in name:
            return '钢材类'
    if 'steel' in n:
        return '钢材类'
    # Aluminum
    if '铝' in name or 'aluminum' in n or '铝合金' in name:
        return '铝材类'
    # Wood
    if '木' in name or 'wood' in n or '胡桃' in name or '樱桃' in name or '松' in name:
        return '木材类'
    # Paint/coating
    if '漆' in name or 'paint' in n or '涂料' in name:
        return '涂料类'
    # Gypsum/plaster
    if '石膏' in name or 'gypsum' in n:
        return '石膏类'
    # Metal generic
    if '金属' in name or 'metal' in n or '黄铜' in name or '锌' in name:
        return '金属类'
    return '其他'


def analyze_storeys(storeys):
    """Analyze storey elevations to determine above/below ground."""
    above = [s for s in storeys if s['elev'] >= 0]
    below = [s for s in storeys if s['elev'] < 0]

    # Detect if storeys are reference levels (very close together)
    elevs = sorted([s['elev'] for s in storeys])
    if len(elevs) >= 3:
        max_elev = max(elevs)
        min_elev = min(elevs)
        height_range = max_elev - min_elev
        avg_spacing = height_range / (len(elevs) - 1) if len(elevs) > 1 else 0

        # If average spacing < 1m, likely reference levels, not real floors
        if avg_spacing < 1000 and len(elevs) > 3:
            return {
                'type': 'reference_levels',
                'total': len(storeys),
                'above': len(above),
                'below': len(below),
                'height_range_mm': height_range,
                'likely_floors': max(1, int(height_range / 3000)),  # assume ~3m per floor
                'note': f'标高间距过小（平均{avg_spacing:.0f}mm），可能是参考标高而非实际楼层'
            }

    return {
        'type': 'normal',
        'total': len(storeys),
        'above': len(above),
        'below': len(below),
        'height_range_mm': max(elevs) - min(elevs) if elevs else 0,
        'likely_floors': len(storeys),
        'note': None
    }


def infer_structural_type(d):
    """Infer structural type with caveats."""
    walls = d['walls']
    cols = d['columns']
    beams = d['beams']

    load_bearing_walls = [w for w in walls if w.get('load_bearing') == True]
    non_bearing_walls = [w for w in walls if w.get('load_bearing') == False]

    # Check if LoadBearing data is meaningful
    has_lb_data = len(load_bearing_walls) + len(non_bearing_walls) > 0

    if has_lb_data and len(load_bearing_walls) == 0:
        # No load-bearing walls → cannot be shear wall or masonry
        if len(cols) > 3:
            return '框架结构', '所有墙体LoadBearing=False，柱子较多，推断为框架结构'
        else:
            return '无法确定', '所有墙体LoadBearing=False，柱子数量不足以判断框架体系'

    if len(cols) >= 4 and len(beams) >= 2:
        return '框架-剪力墙结构', '柱梁体系完整，同时存在较多墙体'
    elif len(cols) >= 4:
        return '框架结构', '柱子较多，可能为框架结构'
    elif len(load_bearing_walls) > 10:
        return '剪力墙结构', '较多承重墙体，无明显框架体系'
    elif len(walls) > 20 and len(cols) == 0:
        return '剪力墙结构', '仅墙体无柱，可能为剪力墙结构'
    else:
        return '无法确定', '构件信息不足以推断结构类型'


def describe_model(d):
    """Generate improved natural language description."""
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
    stair_flights = d['stair_flights']
    roofs = d['roofs']

    # ── Header ──
    lines.append(f"# IFC模型描述: {fname}")
    lines.append("")
    lines.append(f"- Schema版本: {d['schema']}")
    lines.append(f"- 数据集划分: {d['split']}")
    lines.append(f"- 总实体数: {d['total_entities']}")
    lines.append("")

    # ── Building Overview ──
    lines.append("## 1. 建筑概况")
    lines.append("")

    storey_analysis = analyze_storeys(storeys)

    if storey_analysis['type'] == 'reference_levels':
        lines.append(f"本模型包含{storey_analysis['total']}个标高层，标高范围"
                     f"{storeys[0]['elev']:.0f}mm ~ {storeys[-1]['elev']:.0f}mm。")
        lines.append(f"**注意：** {storey_analysis['note']}")
        lines.append(f"根据标高间距推断，实际楼层数约{storey_analysis['likely_floors']}层。")
    else:
        above = storey_analysis['above']
        below = storey_analysis['below']
        height_m = storey_analysis['height_range_mm'] / 1000
        lines.append(f"本模型包含{storey_analysis['total']}个楼层，"
                     f"建筑高度约{height_m:.1f}m。")
        if below > 0:
            lines.append(f"- 地上{above}层，地下{below}层")
        else:
            lines.append(f"- 全部为地上楼层")

    # Storey details
    lines.append("")
    lines.append("楼层明细：")
    for s in storeys:
        elev_m = s['elev'] / 1000
        marker = "↑地上" if s['elev'] >= 0 else "↓地下"
        lines.append(f"- {s['name']}：标高{elev_m:.2f}m ({marker})")
    lines.append("")

    # ── Structural System ──
    lines.append("## 2. 结构体系")
    lines.append("")

    struct_type, struct_reason = infer_structural_type(d)
    lines.append(f"推断结构类型：**{struct_type}**")
    lines.append(f"推断依据：{struct_reason}")

    # Data quality note on IsExternal
    ext_walls = [w for w in walls if w.get('is_external') == True]
    if len(ext_walls) == len(walls) and len(walls) > 5:
        lines.append("")
        lines.append(f"**数据质量说明：** 所有{len(walls)}面墙均标记为IsExternal=True，"
                     f"这可能是源模型的建模约定或错误，而非实际建筑状况。"
                     f"真实的建筑应包含外墙和内墙。")
    lines.append("")

    # Walls
    lines.append("### 2.1 墙体")
    lines.append("")
    lines.append(f"共{len(walls)}面墙体。")

    # Wall types
    wall_types = {}
    for w in walls:
        wt = classify_wall(w['name'])
        wall_types[wt] = wall_types.get(wt, 0) + 1
    for wt, cnt in wall_types.items():
        lines.append(f"- {wt}：{cnt}面")

    # LoadBearing
    lb_walls = [w for w in walls if w.get('load_bearing') == True]
    non_lb = [w for w in walls if w.get('load_bearing') == False]
    if lb_walls or non_lb:
        lines.append(f"- 承重墙：{len(lb_walls)}面")
        lines.append(f"- 非承重墙：{len(non_lb)}面")

    # Wall thickness
    thicknesses = [w['thickness'] for w in walls if w.get('thickness')]
    if thicknesses:
        thickness_set = sorted(set(round(t) for t in thicknesses))
        lines.append(f"- 墙厚种类：{', '.join(str(t)+'mm' for t in thickness_set)}")
        main_t = max(set(round(t) for t in thicknesses),
                     key=lambda t: sum(1 for x in thicknesses if round(x) == t))
        lines.append(f"- 主要墙厚：{main_t}mm")
    else:
        lines.append("- 墙厚：未从几何或材料层中提取到")
    lines.append("")

    # Columns
    if cols:
        lines.append("### 2.2 柱子")
        lines.append("")
        lines.append(f"共{len(cols)}根柱子。")
        for c in cols[:5]:
            dim_str = f" ({c['dims']['w']:.0f}×{c['dims']['h']:.0f}mm)" if c.get('dims') else ""
            lines.append(f"- {c['name']}{dim_str}")
        if len(cols) > 5:
            lines.append(f"- ... 共{len(cols)}根")
        lines.append("")

    # Beams
    if beams:
        lines.append("### 2.3 梁")
        lines.append("")
        lines.append(f"共{len(beams)}根梁。")
        for b in beams[:5]:
            dim_str = f" ({b['dims']['w']:.0f}×{b['dims']['h']:.0f}mm)" if b.get('dims') else ""
            lines.append(f"- {b['name']}{dim_str}")
        if len(beams) > 5:
            lines.append(f"- ... 共{len(beams)}根")
        lines.append("")

    # Slabs - FIXED: classify by PredefinedType
    if slabs:
        lines.append("### 2.4 楼板/屋面")
        lines.append("")
        floor_slabs = [s for s in slabs if s['pretype'] == 'FLOOR']
        landing_slabs = [s for s in slabs if s['pretype'] == 'LANDING']
        roof_slabs = [s for s in slabs if s['pretype'] == 'ROOF']
        other_slabs = [s for s in slabs if s['pretype'] not in ('FLOOR', 'LANDING', 'ROOF')]

        lines.append(f"共{len(slabs)}块板构件：")
        if floor_slabs:
            lines.append(f"- 楼板(FLOOR)：{len(floor_slabs)}块")
        if landing_slabs:
            lines.append(f"- 平台板(LANDING)：{len(landing_slabs)}块")
        if roof_slabs:
            lines.append(f"- 屋面板(ROOF)：{len(roof_slabs)}块")
        if other_slabs:
            lines.append(f"- 其他板：{len(other_slabs)}块")
        lines.append("")

    # Roofs
    if roofs:
        lines.append("### 2.5 屋顶")
        lines.append("")
        lines.append(f"共{len(roofs)}个屋顶构件。")
        lines.append("")

    # Stairs - FIXED: separate assembly and flight
    if stairs or stair_flights:
        lines.append("### 2.6 楼梯")
        lines.append("")
        if stairs and stair_flights:
            lines.append(f"共{len(stairs)}个楼梯，包含{len(stair_flights)}个梯段。")
        elif stairs:
            lines.append(f"共{len(stairs)}个楼梯。")
        elif stair_flights:
            lines.append(f"共{len(stair_flights)}个梯段。")
        lines.append("")

    # ── Openings ──
    lines.append("## 3. 门窗")
    lines.append("")

    if doors:
        door_types = {}
        for do in doors:
            dt = classify_door(do['name'])
            door_types[dt] = door_types.get(dt, 0) + 1
        lines.append("### 3.1 门")
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
        large_doors = [do for do in doors if do['w'] and do['w'] > 1500]
        if large_doors:
            lines.append(f"- 其中{len(large_doors)}扇宽度>1500mm，可能为入口或防火门")
        lines.append("")

    if wins:
        win_types = {}
        for wi in wins:
            wt = classify_window(wi['name'])
            win_types[wt] = win_types.get(wt, 0) + 1
        lines.append("### 3.2 窗")
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

    # ── Materials - FIXED classification ──
    lines.append("## 4. 材料")
    lines.append("")
    if mats:
        lines.append(f"共使用{len(mats)}种材料：")
        for m in mats:
            lines.append(f"- {m}")

        # Correct classification
        mat_groups = {}
        for m in mats:
            cat = classify_material(m)
            mat_groups.setdefault(cat, []).append(m)

        lines.append("")
        lines.append("材料分类：")
        for cat in ['混凝土类', '钢材类', '铝材类', '木材类', '玻璃类', '涂料类', '石膏类', '金属类', '其他']:
            if cat in mat_groups:
                lines.append(f"- {cat}：{', '.join(mat_groups[cat])}")
    else:
        lines.append("本模型未定义材料信息。")
    lines.append("")

    # ── MEP ──
    lines.append("## 5. MEP设备管线")
    lines.append("")
    if d['mep']:
        for m in d['mep']:
            lines.append(f"- {m['type']}: {m['count']}个")
    else:
        lines.append("本模型不包含MEP设备管线构件。")
    lines.append("")

    # ── Summary ──
    lines.append("## 6. 模型特征总结")
    lines.append("")
    complexity = '复杂' if d['total_entities'] > 50000 else '中等' if d['total_entities'] > 10000 else '简单'

    floor_slab_count = len([s for s in slabs if s['pretype'] == 'FLOOR'])
    lines.append(f"- 建筑规模：{storey_analysis['likely_floors']}层推断楼层，{complexity}模型（{d['total_entities']}实体）")
    lines.append(f"- 构件统计：{len(walls)}墙、{len(cols)}柱、{len(beams)}梁、{floor_slab_count}楼板")
    lines.append(f"- 门窗：{len(doors)}门、{len(wins)}窗")
    lines.append(f"- 结构类型：{struct_type}")
    lines.append(f"- 楼梯：{len(stairs)}个楼梯/{len(stair_flights)}个梯段")
    lines.append(f"- MEP：{'有' if d['mep'] else '无'}")

    return '\n'.join(lines)


# ── Main ──
output_dir = Path("E:/code for project/bimnet/dataset/processed/descriptions")
output_dir.mkdir(parents=True, exist_ok=True)

for d in data:
    fname = d['filename'].replace('.ifc', '')
    desc = describe_model(d)
    out_path = output_dir / f"{fname}.txt"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(desc)
    print(f"✓ {d['filename']}")

print(f"\nDone. {len(data)} descriptions → {output_dir}")
