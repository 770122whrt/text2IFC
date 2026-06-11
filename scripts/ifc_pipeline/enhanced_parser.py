"""
Enhanced IFC Parser - 修复审查报告中的所有问题
修复内容：
1. 楼板按PredefinedType分类（FLOOR/LANDING/ROOF/BASESLAB）
2. 墙体LoadBearing属性提取
3. 墙厚从几何截面提取
4. 楼梯分离Stair和StairFlight
5. 材料分类修正
"""

import ifcopenshell
import ifcopenshell.util.element as util_elem
import sys, os, json, re
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')


def safe(el): return el.Name if el.Name else ''


def get_materials(el):
    mats = []
    try:
        for rel in el.HasAssociations:
            if rel.is_a('IfcRelAssociatesMaterial'):
                m = rel.RelatingMaterial
                if m.is_a('IfcMaterial'):
                    mats.append(m.Name)
                elif m.is_a('IfcMaterialLayerSet'):
                    for l in m.MaterialLayers:
                        if l.Material:
                            mats.append(f"{l.Material.Name}({l.LayerThickness}mm)")
                elif m.is_a('IfcMaterialList'):
                    for x in m.Materials:
                        mats.append(x.Name)
    except:
        pass
    return mats


def get_wall_thickness(el):
    """Extract wall thickness from geometry or material layers."""
    # Method 1: from geometry (RectangleProfileDef)
    try:
        if el.Representation:
            for rep in el.Representation.Representations:
                for item in rep.Items:
                    if item.is_a('IfcExtrudedAreaSolid'):
                        p = item.SweptArea
                        if p.is_a('IfcRectangleProfileDef'):
                            # For walls, the smaller dim is thickness
                            return min(p.XDim, p.YDim)
    except:
        pass
    # Method 2: from material layer set
    try:
        for rel in el.HasAssociations:
            if rel.is_a('IfcRelAssociatesMaterial'):
                m = rel.RelatingMaterial
                if m.is_a('IfcMaterialLayerSetUsage') and m.ForLayerSet:
                    total = sum(l.LayerThickness for l in m.ForLayerSet.MaterialLayers)
                    return total
                elif m.is_a('IfcMaterialLayerSet'):
                    return sum(l.LayerThickness for l in m.MaterialLayers)
    except:
        pass
    # Method 3: from name pattern
    name = safe(el)
    m = re.search(r'(\d+)mm', name)
    if m: return int(m.group(1))
    m = re.search(r'[:\-]\s*(\d{2,3})(?:[:\s]|$)', name)
    if m: return int(m.group(1))
    return None


def get_pset(el):
    try:
        return util_elem.get_psets(el)
    except:
        return {}


def get_storey(el):
    try:
        for rel in el.ContainedInStructure:
            s = rel.RelatingStructure
            if s.is_a('IfcBuildingStorey'):
                return safe(s)
    except:
        pass
    return '?'


def parse_one(path):
    ifc = ifcopenshell.open(path)
    r = {'schema': ifc.schema, 'filename': os.path.basename(path)}

    # Project hierarchy
    r['project'] = [{'name': safe(p), 'id': p.id()} for p in ifc.by_type('IfcProject')]
    r['site'] = [{'name': safe(s), 'lat': s.RefLatitude, 'lon': s.RefLongitude} for s in ifc.by_type('IfcSite')]
    r['building'] = []
    for b in ifc.by_type('IfcBuilding'):
        pset = get_pset(b)
        num_storeys = None
        for pn, pv in pset.items():
            if isinstance(pv, dict) and 'NumberOfStoreys' in pv:
                num_storeys = pv['NumberOfStoreys']
        r['building'].append({'name': safe(b), 'num_storeys': num_storeys})

    # Storeys with elevation analysis
    storeys = []
    for st in ifc.by_type('IfcBuildingStorey'):
        elev = st.Elevation if st.Elevation else 0
        storeys.append({
            'name': safe(st), 'elev': elev, 'id': st.id(),
            'above_ground': elev >= 0
        })
    r['storeys'] = storeys

    # Walls with LoadBearing and thickness
    walls_raw = ifc.by_type('IfcWallStandardCase') + ifc.by_type('IfcWall')
    seen = set()
    walls = []
    for w in walls_raw:
        if w.GlobalId not in seen:
            seen.add(w.GlobalId)
            pset = get_pset(w)
            is_ext = None
            load_bearing = None
            for pn, pv in pset.items():
                if isinstance(pv, dict):
                    if 'IsExternal' in pv: is_ext = pv['IsExternal']
                    if 'LoadBearing' in pv: load_bearing = pv['LoadBearing']
            thickness = get_wall_thickness(w)
            walls.append({
                'name': safe(w), 'storey': get_storey(w),
                'material': get_materials(w), 'is_external': is_ext,
                'load_bearing': load_bearing, 'thickness': thickness,
                'id': w.GlobalId
            })
    r['walls'] = walls

    # Columns with dimensions
    cols = []
    for c in ifc.by_type('IfcColumn'):
        dims = None
        try:
            if c.Representation:
                for rep in c.Representation.Representations:
                    for item in rep.Items:
                        if item.is_a('IfcExtrudedAreaSolid'):
                            p = item.SweptArea
                            if p.is_a('IfcRectangleProfileDef'):
                                dims = {'w': p.XDim, 'h': p.YDim, 'depth': item.Depth}
        except:
            pass
        pset = get_pset(c)
        load_bearing = None
        for pn, pv in pset.items():
            if isinstance(pv, dict) and 'LoadBearing' in pv:
                load_bearing = pv['LoadBearing']
        cols.append({
            'name': safe(c), 'storey': get_storey(c),
            'material': get_materials(c), 'dims': dims,
            'load_bearing': load_bearing
        })
    r['columns'] = cols

    # Beams with dimensions
    beams = []
    for b in ifc.by_type('IfcBeam'):
        dims = None
        try:
            if b.Representation:
                for rep in b.Representation.Representations:
                    for item in rep.Items:
                        if item.is_a('IfcExtrudedAreaSolid'):
                            p = item.SweptArea
                            if p.is_a('IfcRectangleProfileDef'):
                                dims = {'w': p.XDim, 'h': p.YDim, 'depth': item.Depth}
        except:
            pass
        beams.append({
            'name': safe(b), 'storey': get_storey(b),
            'material': get_materials(b), 'dims': dims
        })
    r['beams'] = beams

    # Slabs with PredefinedType classification
    slabs = []
    for s in ifc.by_type('IfcSlab'):
        pretype = s.PredefinedType if s.PredefinedType else 'UNDEFINED'
        # Classify: FLOOR, LANDING, ROOF, BASESLAB
        slabs.append({
            'name': safe(s), 'storey': get_storey(s),
            'material': get_materials(s), 'pretype': pretype,
            'slab_category': pretype  # FLOOR/LANDING/ROOF/BASESLAB
        })
    r['slabs'] = slabs

    # Doors with dimensions
    r['doors'] = [{
        'name': safe(d), 'storey': get_storey(d),
        'w': d.OverallWidth, 'h': d.OverallHeight,
        'material': get_materials(d)
    } for d in ifc.by_type('IfcDoor')]

    # Windows with dimensions
    r['windows'] = [{
        'name': safe(w), 'storey': get_storey(w),
        'w': w.OverallWidth, 'h': w.OverallHeight,
        'material': get_materials(w)
    } for w in ifc.by_type('IfcWindow')]

    # Materials
    r['materials'] = [m.Name for m in ifc.by_type('IfcMaterial')]

    # Stairs - SEPARATE IfcStair and IfcStairFlight
    r['stairs'] = [{'name': safe(s)} for s in ifc.by_type('IfcStair')]
    r['stair_flights'] = [{'name': safe(s)} for s in ifc.by_type('IfcStairFlight')]

    # Roofs
    r['roofs'] = [{'name': safe(r2)} for r2 in ifc.by_type('IfcRoof')]

    # MEP
    mep = []
    for cls in ['IfcFlowSegment', 'IfcFlowTerminal', 'IfcFlowFitting',
                'IfcFlowController', 'IfcEnergyConversionDevice']:
        try:
            elems = ifc.by_type(cls)
            if elems: mep.append({'type': cls, 'count': len(elems)})
        except:
            pass
    r['mep'] = mep

    r['opening_count'] = len(ifc.by_type('IfcOpeningElement'))
    r['total_entities'] = len(list(ifc))

    return r


def main():
    base_dir = Path("E:/code for project/bimnet/dataset/ifc")
    out_path = Path("E:/code for project/bimnet/dataset/processed/ifc_parsed_enhanced.json")

    all_data = []
    for split in ['train', 'test']:
        split_dir = base_dir / split
        for f in sorted(split_dir.glob('*.ifc')):
            print(f'Parsing [{split}] {f.name} ...', end=' ', flush=True)
            try:
                r = parse_one(str(f))
                r['split'] = split
                all_data.append(r)
                print(f'✓ ({r["total_entities"]} entities)')
            except Exception as e:
                print(f'✗ {e}')

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f'\nDone. {len(all_data)} files → {out_path}')


if __name__ == '__main__':
    main()
