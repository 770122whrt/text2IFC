"""
IFC Model Parser → Natural Language Description
Parses IFC files using ifcopenshell schema and generates structured text descriptions.
"""

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.placement
import os
import sys
import json
from pathlib import Path
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')

# ── Helpers ──────────────────────────────────────────────────────────────────

def safe_name(entity):
    """Get name, handle None."""
    return entity.Name if entity.Name else "未命名"

def get_element_quantity(element):
    """Extract basic geometric quantities from property sets."""
    quantities = {}
    try:
        psets = ifcopenshell.util.element.get_psets(element)
        for pname, pdata in psets.items():
            if 'Quantity' in pname or 'qto' in pname.lower():
                for k, v in pdata.items():
                    if k != 'id' and isinstance(v, (int, float)):
                        quantities[k] = v
    except:
        pass
    return quantities

def get_element_properties(element):
    """Extract property set values."""
    props = {}
    try:
        psets = ifcopenshell.util.element.get_psets(element)
        for pname, pdata in psets.items():
            if 'Pset' in pname or 'Common' in pname:
                for k, v in pdata.items():
                    if k != 'id' and isinstance(v, (str, int, float, bool)):
                        props[k] = v
    except:
        pass
    return props

def get_material(element):
    """Get material name(s) for an element."""
    materials = []
    try:
        rels = element.HasAssociations
        if rels:
            for rel in rels:
                if rel.is_a('IfcRelAssociatesMaterial'):
                    mat = rel.RelatingMaterial
                    if mat.is_a('IfcMaterial'):
                        materials.append(mat.Name)
                    elif mat.is_a('IfcMaterialLayerSet'):
                        for layer in mat.MaterialLayers:
                            if layer.Material:
                                materials.append(layer.Material.Name)
                    elif mat.is_a('IfcMaterialList'):
                        for m in mat.Materials:
                            materials.append(m.Name)
    except:
        pass
    return materials

def get_storey(element):
    """Get the storey name for an element."""
    try:
        if element.ContainedInStructure:
            for rel in element.ContainedInStructure:
                structure = rel.RelatingStructure
                if structure.is_a('IfcBuildingStorey'):
                    return safe_name(structure)
    except:
        pass
    return "未知楼层"

def get_bbox_dimensions(element):
    """Try to get bounding box dimensions."""
    try:
        if element.Representation:
            for rep in element.Representation.Representations:
                for item in rep.Items:
                    if item.is_a('IfcExtrudedAreaSolid'):
                        profile = item.SweptArea
                        if profile.is_a('IfcRectangleProfileDef'):
                            return {
                                'width': profile.XDim,
                                'height': profile.YDim,
                                'depth': item.Depth
                            }
    except:
        pass
    return None

def classify_wall(name):
    """Classify wall by name pattern."""
    name_lower = name.lower() if name else ''
    if '外' in name or 'exterior' in name_lower or 'outer' in name_lower:
        return '外墙'
    elif '内' in name or 'interior' in name_lower or 'inner' in name_lower:
        return '内墙'
    elif '隔' in name or 'partition' in name_lower:
        return '隔墙'
    else:
        return '墙体'

def classify_window(name):
    """Classify window type."""
    if '推拉' in name or 'sliding' in name.lower():
        return '推拉窗'
    elif '固定' in name or 'fixed' in name.lower():
        return '固定窗'
    elif '平开' in name or 'casement' in name.lower():
        return '平开窗'
    else:
        return '窗'

def classify_door(name):
    """Classify door type."""
    if '单扇' in name or 'single' in name.lower():
        return '单扇门'
    elif '双扇' in name or 'double' in name.lower():
        return '双扇门'
    elif '推拉' in name or 'sliding' in name.lower():
        return '推拉门'
    else:
        return '门'


# ── Main Parser ──────────────────────────────────────────────────────────────

def parse_ifc_to_text(ifc_path):
    """Parse a single IFC file and return natural language description."""
    ifc = ifcopenshell.open(ifc_path)
    filename = os.path.basename(ifc_path)
    lines = []

    lines.append(f"{'='*70}")
    lines.append(f"IFC模型自然语言描述")
    lines.append(f"文件: {filename}")
    lines.append(f"Schema版本: {ifc.schema}")
    lines.append(f"{'='*70}")
    lines.append("")

    # ── 1. Project Structure ──
    lines.append("【一、项目层级结构】")
    lines.append("")

    projects = ifc.by_type('IfcProject')
    for p in projects:
        lines.append(f"  项目名称: {safe_name(p)}")

    sites = ifc.by_type('IfcSite')
    for s in sites:
        lines.append(f"  场地名称: {safe_name(s)}")

    buildings = ifc.by_type('IfcBuilding')
    for b in buildings:
        lines.append(f"  建筑名称: {safe_name(b) if safe_name(b) else '(未命名建筑)'}")

    storeys = ifc.by_type('IfcBuildingStorey')
    lines.append(f"  楼层数量: {len(storeys)}层")
    for st in sorted(storeys, key=lambda x: x.Elevation if x.Elevation else 0):
        elev = st.Elevation if st.Elevation else 0
        lines.append(f"    - {safe_name(st)}: 标高 {elev}mm ({elev/1000:.3f}m)")
    lines.append("")

    # ── 2. Structural Elements ──
    lines.append("【二、结构构件】")
    lines.append("")

    # Walls
    walls = ifc.by_type('IfcWallStandardCase') + ifc.by_type('IfcWall')
    # Deduplicate by GlobalId
    seen = set()
    unique_walls = []
    for w in walls:
        if w.GlobalId not in seen:
            seen.add(w.GlobalId)
            unique_walls.append(w)

    if unique_walls:
        wall_types = defaultdict(list)
        for w in unique_walls:
            wtype = classify_wall(safe_name(w))
            wall_types[wtype].append(w)

        lines.append(f"  墙体总数: {len(unique_walls)}面")
        for wtype, wlist in wall_types.items():
            lines.append(f"    - {wtype}: {len(wlist)}面")

        # Detail for first few walls
        lines.append(f"  墙体明细 (前5面):")
        for w in unique_walls[:5]:
            storey = get_storey(w)
            mat = get_material(w)
            mat_str = ', '.join(mat) if mat else '未指定'
            dims = get_bbox_dimensions(w)
            dim_str = f" 宽{dims['width']:.0f}mm × 高{dims['height']:.0f}mm × 厚{dims['depth']:.0f}mm" if dims else ""
            lines.append(f"    · {safe_name(w)} | 楼层: {storey} | 材料: {mat_str}{dim_str}")
        lines.append("")

    # Columns
    columns = ifc.by_type('IfcColumn')
    if columns:
        lines.append(f"  柱子总数: {len(columns)}根")
        for c in columns:
            storey = get_storey(c)
            mat = get_material(c)
            mat_str = ', '.join(mat) if mat else '未指定'
            dims = get_bbox_dimensions(c)
            dim_str = f" 截面{dims['width']:.0f}mm × {dims['height']:.0f}mm" if dims else ""
            lines.append(f"    · {safe_name(c)} | 楼层: {storey} | 材料: {mat_str}{dim_str}")
        lines.append("")

    # Beams
    beams = ifc.by_type('IfcBeam')
    if beams:
        lines.append(f"  梁总数: {len(beams)}根")
        for b in beams:
            storey = get_storey(b)
            mat = get_material(b)
            mat_str = ', '.join(mat) if mat else '未指定'
            dims = get_bbox_dimensions(b)
            dim_str = f" 截面{dims['width']:.0f}mm × {dims['height']:.0f}mm" if dims else ""
            lines.append(f"    · {safe_name(b)} | 楼层: {storey} | 材料: {mat_str}{dim_str}")
        lines.append("")

    # Slabs
    slabs = ifc.by_type('IfcSlab')
    if slabs:
        lines.append(f"  楼板总数: {len(slabs)}块")
        for s in slabs:
            storey = get_storey(s)
            mat = get_material(s)
            mat_str = ', '.join(mat) if mat else '未指定'
            lines.append(f"    · {safe_name(s)} | 楼层: {storey} | 材料: {mat_str}")
        lines.append("")

    # Roof
    roofs = ifc.by_type('IfcRoof')
    if roofs:
        lines.append(f"  屋顶总数: {len(roofs)}个")
        for r in roofs:
            lines.append(f"    · {safe_name(r)}")
        lines.append("")

    # Stairs
    stairs = ifc.by_type('IfcStair') + ifc.by_type('IfcStairFlight')
    if stairs:
        lines.append(f"  楼梯总数: {len(stairs)}个")
        for s in stairs:
            lines.append(f"    · {safe_name(s)}")
        lines.append("")

    # ── 3. Openings ──
    lines.append("【三、门窗与洞口】")
    lines.append("")

    doors = ifc.by_type('IfcDoor')
    if doors:
        door_types = defaultdict(int)
        for d in doors:
            door_types[classify_door(safe_name(d))] += 1
        lines.append(f"  门总数: {len(doors)}扇")
        for dtype, count in door_types.items():
            lines.append(f"    - {dtype}: {count}扇")
        for d in doors[:5]:
            storey = get_storey(d)
            lines.append(f"    · {safe_name(d)} | 楼层: {storey}")
        if len(doors) > 5:
            lines.append(f"    ... 共{len(doors)}扇门")
        lines.append("")

    windows = ifc.by_type('IfcWindow')
    if windows:
        win_types = defaultdict(int)
        for w in windows:
            win_types[classify_window(safe_name(w))] += 1
        lines.append(f"  窗总数: {len(windows)}扇")
        for wtype, count in win_types.items():
            lines.append(f"    - {wtype}: {count}扇")
        for w in windows[:5]:
            storey = get_storey(w)
            lines.append(f"    · {safe_name(w)} | 楼层: {storey}")
        if len(windows) > 5:
            lines.append(f"    ... 共{len(windows)}扇窗")
        lines.append("")

    openings = ifc.by_type('IfcOpeningElement')
    if openings:
        lines.append(f"  洞口总数: {len(openings)}个")
        lines.append("")

    # ── 4. Materials ──
    lines.append("【四、材料信息】")
    lines.append("")

    materials = ifc.by_type('IfcMaterial')
    if materials:
        lines.append(f"  材料种类: {len(materials)}种")
        for m in materials:
            lines.append(f"    · {m.Name}")
        lines.append("")

    # ── 5. MEP Elements ──
    lines.append("【五、MEP设备管线】")
    lines.append("")

    mep_classes = [
        'IfcFlowSegment', 'IfcFlowTerminal', 'IfcFlowFitting',
        'IfcFlowController', 'IfcFlowMovingDevice', 'IfcEnergyConversionDevice',
        'IfcDistributionPort', 'IfcPipeFitting', 'IfcDuctFitting',
        'IfcElectricDistributionPoint', 'IfcLamp', 'IfcLightFixture',
    ]
    mep_total = 0
    for cls in mep_classes:
        elems = ifc.by_type(cls)
        if elems:
            mep_total += len(elems)
            lines.append(f"  {cls}: {len(elems)}个")
    if mep_total == 0:
        lines.append("  本模型不包含MEP设备管线")
    lines.append("")

    # ── 6. Relationships ──
    lines.append("【六、空间与连接关系】")
    lines.append("")

    containment = ifc.by_type('IfcRelContainedInSpatialStructure')
    lines.append(f"  空间包含关系: {len(containment)}条")
    for rel in containment[:5]:
        structure = rel.RelatingStructure
        products = rel.RelatedElements
        lines.append(f"    {safe_name(structure)} 包含 {len(products)}个构件")
    lines.append("")

    voids = ifc.by_type('IfcRelVoidsElement')
    if voids:
        lines.append(f"  墙体开洞关系: {len(voids)}条")
        lines.append("")

    connects = ifc.by_type('IfcRelConnectsPathElements')
    if connects:
        lines.append(f"  构件连接关系: {len(connects)}条")
        lines.append("")

    # ── 7. Statistics Summary ──
    lines.append("【七、统计汇总】")
    lines.append("")
    lines.append(f"  总构件数 (IfcProduct): {len(ifc.by_type('IfcProduct'))}")
    lines.append(f"  总实体数: {len(list(ifc))}")
    lines.append(f"  墙体: {len(unique_walls) if unique_walls else 0}")
    lines.append(f"  柱子: {len(columns) if columns else 0}")
    lines.append(f"  梁: {len(beams) if beams else 0}")
    lines.append(f"  楼板: {len(slabs) if slabs else 0}")
    lines.append(f"  门: {len(doors) if doors else 0}")
    lines.append(f"  窗: {len(windows) if windows else 0}")
    lines.append(f"  洞口: {len(openings) if openings else 0}")
    lines.append(f"  MEP设备: {mep_total}")
    lines.append("")

    # ── 8. Natural Language Summary ──
    lines.append("【八、自然语言概述】")
    lines.append("")

    # Build narrative
    storey_names = [safe_name(st) for st in storeys]
    wall_count = len(unique_walls) if unique_walls else 0
    col_count = len(columns) if columns else 0
    beam_count = len(beams) if beams else 0
    slab_count = len(slabs) if slabs else 0
    door_count = len(doors) if doors else 0
    win_count = len(windows) if windows else 0

    narrative = f"这是一个{ifc.schema}格式的BIM模型。"
    narrative += f"项目包含{len(buildings)}栋建筑，共{len(storeys)}层"
    if storey_names:
        narrative += f"（{'、'.join(storey_names)}）"
    narrative += "。"

    if wall_count > 0:
        narrative += f"模型中有{wall_count}面墙体"
        if wall_types:
            detail_parts = [f"{len(v)}面{k}" for k, v in wall_types.items()]
            narrative += f"（{'，'.join(detail_parts)}）"
        narrative += "。"

    if col_count > 0:
        narrative += f"设有{col_count}根柱子。"
    if beam_count > 0:
        narrative += f"{beam_count}根梁。"
    if slab_count > 0:
        narrative += f"{slab_count}块楼板。"
    if door_count > 0:
        narrative += f"共{door_count}扇门。"
    if win_count > 0:
        narrative += f"{win_count}扇窗。"
    if mep_total > 0:
        narrative += f"包含{mep_total}个MEP设备/管线构件。"
    else:
        narrative += "不包含MEP设备管线。"

    if materials:
        mat_names = [m.Name for m in materials]
        narrative += f"涉及{len(materials)}种材料：{'、'.join(mat_names)}。"

    lines.append(f"  {narrative}")
    lines.append("")
    lines.append(f"{'='*70}")

    return '\n'.join(lines)


# ── Batch Processing ─────────────────────────────────────────────────────────

def main():
    base_dir = Path("E:/code for project/bimnet/dataset/ifc")
    output_dir = Path("E:/code for project/bimnet/dataset/ifc_descriptions")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_files = []
    for split in ['train', 'test']:
        split_dir = base_dir / split
        if split_dir.exists():
            for f in sorted(split_dir.glob('*.ifc')):
                all_files.append((split, f))

    print(f"找到 {len(all_files)} 个IFC文件待解析")
    print()

    for split, ifc_path in all_files:
        print(f"解析 [{split}] {ifc_path.name} ...")
        try:
            text = parse_ifc_to_text(str(ifc_path))
            out_path = output_dir / f"{ifc_path.stem}.txt"
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"  → 写入 {out_path.name}")
        except Exception as e:
            print(f"  ✗ 错误: {e}")

    print()
    print(f"完成! 描述文件保存在: {output_dir}")


if __name__ == '__main__':
    main()
