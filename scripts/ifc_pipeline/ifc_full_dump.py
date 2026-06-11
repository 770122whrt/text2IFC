"""
IFC Full Dump - 将IFC文件的全部信息完整导出为可读txt
包含：项目结构、所有构件详情、属性集、材料、几何、空间关系
"""

import ifcopenshell
import ifcopenshell.util.element as util_elem
import ifcopenshell.util.placement as util_place
import sys, os, json
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')


def safe_str(val):
    if val is None:
        return "N/A"
    if isinstance(val, (list, tuple)):
        return str([round(v, 2) if isinstance(v, float) else v for v in val])
    if isinstance(val, float):
        return f"{val:.2f}"
    return str(val)


def dump_entity_detail(ifc, entity, lines, indent=2):
    """Dump detailed info for a single entity."""
    pad = " " * indent
    eid = entity.id()
    cls = entity.is_a()
    lines.append(f"{pad}[#{eid}] {cls}")

    # All attributes
    info = entity.get_info(include_identifier=False)
    for k, v in info.items():
        if k == 'type' or v is None:
            continue
        # Skip complex nested for now, handle separately
        if isinstance(v, ifcopenshell.entity_instance):
            lines.append(f"{pad}  {k}: {v.is_a()}(#{v.id()})")
        elif isinstance(v, tuple) and len(v) > 0 and isinstance(v[0], ifcopenshell.entity_instance):
            lines.append(f"{pad}  {k}: [{', '.join(f'{e.is_a()}(#{e.id()})' for e in v[:5])}{'...' if len(v) > 5 else ''}]")
        else:
            lines.append(f"{pad}  {k}: {safe_str(v)}")

    # Property sets
    try:
        psets = util_elem.get_psets(entity)
        if psets:
            lines.append(f"{pad}  [属性集]")
            for pname, pdata in psets.items():
                lines.append(f"{pad}    {pname}:")
                for pk, pv in pdata.items():
                    if pk == 'id':
                        continue
                    lines.append(f"{pad}      {pk} = {safe_str(pv)}")
    except:
        pass

    # Materials
    try:
        for rel in entity.HasAssociations:
            if rel.is_a('IfcRelAssociatesMaterial'):
                m = rel.RelatingMaterial
                lines.append(f"{pad}  [材料关联] {m.is_a()}")
                if m.is_a('IfcMaterial'):
                    lines.append(f"{pad}    材料: {m.Name}")
                elif m.is_a('IfcMaterialLayerSet'):
                    lines.append(f"{pad}    层集名称: {m.LayerSetName}")
                    for i, layer in enumerate(m.MaterialLayers):
                        lname = layer.Material.Name if layer.Material else "?"
                        lines.append(f"{pad}    层{i+1}: {lname}, 厚度={layer.LayerThickness}")
                elif m.is_a('IfcMaterialLayerSetUsage'):
                    lines.append(f"{pad}    层集用法: ForSet={rel.RelatingMaterial.ForLayerSet.LayerSetName if rel.RelatingMaterial.ForLayerSet else '?'}")
                elif m.is_a('IfcMaterialList'):
                    for mat in m.Materials:
                        lines.append(f"{pad}    材料: {mat.Name}")
    except:
        pass

    # Geometry
    try:
        if entity.Representation:
            for rep in entity.Representation.Representations:
                rtype = rep.RepresentationType
                ctx = rep.ContextOfItems
                lines.append(f"{pad}  [几何表达] 类型={rtype}, 上下文={ctx.is_a()}")
                for item in rep.Items:
                    lines.append(f"{pad}    几何项: {item.is_a()}")
                    if item.is_a('IfcExtrudedAreaSolid'):
                        p = item.SweptArea
                        lines.append(f"{pad}      截面: {p.is_a()}")
                        if p.is_a('IfcRectangleProfileDef'):
                            lines.append(f"{pad}      矩形截面: {p.XDim:.1f} x {p.YDim:.1f}")
                        elif p.is_a('IfcArbitraryClosedProfileDef'):
                            lines.append(f"{pad}      任意截面(含孔洞={p.is_a('IfcArbitraryProfileDefWithVoids')})")
                        lines.append(f"{pad}      拉伸深度: {item.Depth:.1f}")
                        loc = item.Position.Location.Coordinates
                        lines.append(f"{pad}      位置: ({loc[0]:.1f}, {loc[1]:.1f}, {loc[2]:.1f})")
                    elif item.is_a('IfcMappedItem'):
                        lines.append(f"{pad}      映射源: {item.MappingSource.is_a()}(#{item.MappingSource.id()})")
                    elif item.is_a('IfcBooleanClippingResult'):
                        lines.append(f"{pad}      布尔运算: {item.Operator}")
    except:
        pass

    # Spatial containment
    try:
        if entity.ContainedInStructure:
            for rel in entity.ContainedInStructure:
                s = rel.RelatingStructure
                lines.append(f"{pad}  [所在空间] {s.is_a()} \"{s.Name}\"(#{s.id()})")
    except:
        pass

    # Voids (openings)
    try:
        if entity.HasOpenings:
            for rel in entity.HasOpenings:
                op = rel.RelatedOpeningElement
                lines.append(f"{pad}  [开洞] {op.Name}(#{op.id()})")
    except:
        pass

    # Fills (door/window fills opening)
    try:
        if entity.FillsVoids:
            for rel in entity.FillsVoids:
                op = rel.RelatingOpeningElement
                lines.append(f"{pad}  [填充洞口] {op.Name}(#{op.id()})")
    except:
        pass


def safe_by_type(ifc, cls_name):
    """by_type with schema compatibility."""
    try:
        return ifc.by_type(cls_name)
    except RuntimeError:
        return []


def dump_ifc_full(ifc_path, output_path):
    """Full dump of an IFC file to text."""
    ifc = ifcopenshell.open(ifc_path)
    lines = []

    lines.append("=" * 80)
    lines.append(f"IFC完整信息导出")
    lines.append(f"文件: {os.path.basename(ifc_path)}")
    lines.append(f"Schema: {ifc.schema}")
    lines.append(f"总实体数: {len(list(ifc))}")
    lines.append("=" * 80)
    lines.append("")

    # ── Section 1: Project Hierarchy ──
    lines.append("━" * 60)
    lines.append("【一、项目层级结构】")
    lines.append("━" * 60)
    for cls_name in ['IfcProject', 'IfcSite', 'IfcBuilding', 'IfcBuildingStorey']:
        entities = safe_by_type(ifc, cls_name)
        for e in entities:
            dump_entity_detail(ifc, e, lines, indent=2)
            lines.append("")

    # ── Section 2: All Building Elements ──
    element_classes = [
        'IfcWall', 'IfcWallStandardCase', 'IfcColumn', 'IfcBeam', 'IfcSlab',
        'IfcRoof', 'IfcStair', 'IfcStairFlight', 'IfcRamp', 'IfcRailing',
        'IfcCurtainWall', 'IfcPlate', 'IfcMember', 'IfcFooting',
    ]

    lines.append("━" * 60)
    lines.append("【二、建筑构件详情】")
    lines.append("━" * 60)

    seen_ids = set()
    for cls_name in element_classes:
        entities = safe_by_type(ifc, cls_name)
        if not entities:
            continue
        lines.append(f"\n--- {cls_name} ({len(entities)}个) ---")
        for e in entities:
            if e.id() in seen_ids:
                continue
            seen_ids.add(e.id())
            dump_entity_detail(ifc, e, lines, indent=2)
            lines.append("")

    # ── Section 3: Openings (Doors/Windows/OpeningElements) ──
    opening_classes = ['IfcDoor', 'IfcWindow', 'IfcOpeningElement']
    lines.append("━" * 60)
    lines.append("【三、门窗与洞口】")
    lines.append("━" * 60)

    for cls_name in opening_classes:
        entities = safe_by_type(ifc, cls_name)
        if not entities:
            continue
        lines.append(f"\n--- {cls_name} ({len(entities)}个) ---")
        for e in entities:
            dump_entity_detail(ifc, e, lines, indent=2)
            lines.append("")

    # ── Section 4: Materials ──
    materials = ifc.by_type('IfcMaterial')
    mat_layersets = ifc.by_type('IfcMaterialLayerSet')
    mat_lists = ifc.by_type('IfcMaterialList')

    lines.append("━" * 60)
    lines.append("【四、材料定义】")
    lines.append("━" * 60)

    if materials:
        lines.append(f"\nIfcMaterial ({len(materials)}个):")
        for m in materials:
            lines.append(f"  [{m.id()}] {m.Name}")

    if mat_layersets:
        lines.append(f"\nIfcMaterialLayerSet ({len(mat_layersets)}个):")
        for mls in mat_layersets:
            lines.append(f"  [{mls.id()}] {mls.LayerSetName}")
            for i, layer in enumerate(mls.MaterialLayers):
                lname = layer.Material.Name if layer.Material else "?"
                lines.append(f"    层{i+1}: {lname}, 厚度={layer.LayerThickness}")

    if mat_lists:
        lines.append(f"\nIfcMaterialList ({len(mat_lists)}个):")
        for ml in mat_lists:
            names = [m.Name for m in ml.Materials]
            lines.append(f"  [{ml.id()}] {', '.join(names)}")

    lines.append("")

    # ── Section 5: MEP Elements ──
    mep_classes = [
        'IfcFlowSegment', 'IfcFlowTerminal', 'IfcFlowFitting',
        'IfcFlowController', 'IfcFlowMovingDevice', 'IfcEnergyConversionDevice',
        'IfcElectricDistributionPoint', 'IfcLamp', 'IfcLightFixture',
        'IfcPipeFitting', 'IfcDuctFitting', 'IfcCableCarrierFitting',
    ]
    # IFC4+ only
    if ifc.schema in ('IFC4', 'IFC4X3', 'IFC4X3_ADD2'):
        mep_classes.extend(['IfcDistributionSystem', 'IfcDistributionPort'])

    lines.append("━" * 60)
    lines.append("【五、MEP设备管线】")
    lines.append("━" * 60)

    mep_found = False
    for cls_name in mep_classes:
        try:
            entities = safe_by_type(ifc, cls_name)
        except RuntimeError:
            continue
        if entities:
            mep_found = True
            lines.append(f"\n--- {cls_name} ({len(entities)}个) ---")
            for e in entities[:10]:
                dump_entity_detail(ifc, e, lines, indent=2)
                lines.append("")
            if len(entities) > 10:
                lines.append(f"  ... 共{len(entities)}个，仅显示前10个")

    if not mep_found:
        lines.append("  本模型不包含MEP设备管线构件")
    lines.append("")

    # ── Section 6: Spatial Relationships ──
    lines.append("━" * 60)
    lines.append("【六、空间关系】")
    lines.append("━" * 60)

    containment = ifc.by_type('IfcRelContainedInSpatialStructure')
    lines.append(f"\n空间包含关系 ({len(containment)}条):")
    for rel in containment:
        structure = rel.RelatingStructure
        products = rel.RelatedElements
        type_counts = defaultdict(int)
        for p in products:
            type_counts[p.is_a()] += 1
        count_str = ', '.join(f"{t}:{c}" for t, c in type_counts.items())
        lines.append(f"  {structure.is_a()} \"{structure.Name}\" → [{count_str}]")

    # Aggregates
    aggregates = ifc.by_type('IfcRelAggregates')
    lines.append(f"\n聚合关系 ({len(aggregates)}条):")
    for rel in aggregates:
        parent = rel.RelatingObject
        children = rel.RelatedObjects
        child_str = ', '.join(f"{c.is_a()} \"{c.Name}\"" for c in children[:5])
        lines.append(f"  {parent.is_a()} \"{parent.Name}\" → [{child_str}]")

    # Voids
    voids = ifc.by_type('IfcRelVoidsElement')
    lines.append(f"\n开洞关系 ({len(voids)}条):")
    for rel in voids:
        el = rel.RelatingBuildingElement
        op = rel.RelatedOpeningElement
        lines.append(f"  {el.Name}(#{el.id()}) ← 开洞 {op.Name}(#{op.id()})")

    # Connects
    connects = ifc.by_type('IfcRelConnectsPathElements')
    lines.append(f"\n路径连接关系 ({len(connects)}条):")

    # Assignments
    assigns = ifc.by_type('IfcRelAssignsToGroup')
    lines.append(f"\n分组关系 ({len(assigns)}条):")

    lines.append("")

    # ── Section 7: Type Objects ──
    lines.append("━" * 60)
    lines.append("【七、类型定义】")
    lines.append("━" * 60)

    type_classes = [
        'IfcWallType', 'IfcColumnType', 'IfcBeamType', 'IfcSlabType',
        'IfcDoorType', 'IfcWindowType', 'IfcStairType', 'IfcRoofType',
        'IfcPlateType', 'IfcMemberType', 'IfcCurtainWallType',
    ]

    for cls_name in type_classes:
        try:
            entities = safe_by_type(ifc, cls_name)
        except RuntimeError:
            continue
        if entities:
            lines.append(f"\n{cls_name} ({len(entities)}个):")
            for e in entities:
                info = e.get_info(include_identifier=False)
                lines.append(f"  [{e.id()}] {e.Name} | PredefinedType={info.get('PredefinedType')}")

    lines.append("")

    # ── Section 8: Quantities Summary ──
    lines.append("━" * 60)
    lines.append("【八、实体类型统计】")
    lines.append("━" * 60)
    from collections import Counter
    types = Counter(e.is_a() for e in ifc)
    for t, c in types.most_common(50):
        lines.append(f"  {t}: {c}")
    lines.append("")

    lines.append("=" * 80)
    lines.append("导出完成")
    lines.append("=" * 80)

    text = '\n'.join(lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    return len(lines)


def main():
    base_dir = Path("E:/code for project/bimnet/dataset/ifc")
    output_dir = Path("E:/code for project/bimnet/dataset/ifc_full_dump")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_files = []
    for split in ['train', 'test']:
        split_dir = base_dir / split
        if split_dir.exists():
            for f in sorted(split_dir.glob('*.ifc')):
                all_files.append((split, f))

    print(f"找到 {len(all_files)} 个IFC文件待完整导出")
    print()

    for split, ifc_path in all_files:
        out_path = output_dir / f"{ifc_path.stem}_full.txt"
        print(f"[{split}] {ifc_path.name} → {out_path.name} ...", end=" ", flush=True)
        try:
            nlines = dump_ifc_full(str(ifc_path), str(out_path))
            print(f"✓ ({nlines}行)")
        except Exception as e:
            print(f"✗ 错误: {e}")
            import traceback
            traceback.print_exc()

    print()
    print(f"完成! 完整导出保存在: {output_dir}")


if __name__ == '__main__':
    main()
