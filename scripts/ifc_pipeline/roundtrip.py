"""
IFC → Structured Text → IFC Round-Trip Pipeline

三层架构：
  Level 1: IFC → JSON (结构化中间表示，保留所有建筑语义)
  Level 2: JSON → Natural Language (人类可读描述)
  Level 3: Natural Language → JSON → IFC (Text2BIM核心路径)

本文件实现 Level 1 的往返验证：IFC → JSON → IFC
"""

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.owner.settings as owner_settings
import ifcopenshell.util.element as util_elem
import json, sys, os, re
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')


# ═══════════════════════════════════════════════════════════════════════════
# PART 1: IFC → Structured Text (JSON)
# ═══════════════════════════════════════════════════════════════════════════

def extract_ifc_to_json(ifc_path):
    """Extract all building-relevant info from IFC to a structured dict."""
    ifc = ifcopenshell.open(ifc_path)
    model = {
        'schema': ifc.schema,
        'filename': os.path.basename(ifc_path),
        'project': {},
        'site': {},
        'building': {},
        'storeys': [],
        'walls': [],
        'columns': [],
        'beams': [],
        'slabs': [],
        'doors': [],
        'windows': [],
        'stairs': [],
        'stair_flights': [],
        'roofs': [],
        'materials': [],
        'material_assignments': {},  # element_id -> material_name
    }

    # Project
    for p in ifc.by_type('IfcProject'):
        model['project'] = {'name': p.Name or 'Default Project'}

    # Site
    for s in ifc.by_type('IfcSite'):
        model['site'] = {
            'name': s.Name or 'Default Site',
            'latitude': list(s.RefLatitude) if s.RefLatitude else None,
            'longitude': list(s.RefLongitude) if s.RefLongitude else None,
        }

    # Building
    for b in ifc.by_type('IfcBuilding'):
        pset = util_elem.get_psets(b) if b else {}
        num_storeys = None
        for pn, pv in pset.items():
            if isinstance(pv, dict) and 'NumberOfStoreys' in pv:
                num_storeys = pv['NumberOfStoreys']
        model['building'] = {
            'name': b.Name or '',
            'num_storeys': num_storeys,
        }

    # Storeys
    for st in ifc.by_type('IfcBuildingStorey'):
        model['storeys'].append({
            'name': st.Name,
            'elevation': st.Elevation if st.Elevation else 0,
        })

    # Materials
    for m in ifc.by_type('IfcMaterial'):
        model['materials'].append(m.Name)

    # Material assignments
    for rel in ifc.by_type('IfcRelAssociatesMaterial'):
        mat = rel.RelatingMaterial
        mat_name = None
        if mat.is_a('IfcMaterial'):
            mat_name = mat.Name
        elif mat.is_a('IfcMaterialLayerSet'):
            mat_name = mat.LayerSetName
        if mat_name:
            for obj in rel.RelatedObjects:
                model['material_assignments'][obj.id()] = mat_name

    # Helper: get geometry profile info
    def get_profile(element):
        try:
            if element.Representation:
                for rep in element.Representation.Representations:
                    for item in rep.Items:
                        if item.is_a('IfcExtrudedAreaSolid'):
                            p = item.SweptArea
                            result = {'depth': item.Depth}
                            if p.is_a('IfcRectangleProfileDef'):
                                result['type'] = 'rectangle'
                                result['x_dim'] = p.XDim
                                result['y_dim'] = p.YDim
                            elif p.is_a('IfcCircleProfileDef'):
                                result['type'] = 'circle'
                                result['radius'] = p.Radius
                            elif p.is_a('IfcArbitraryClosedProfileDef'):
                                result['type'] = 'arbitrary'
                            return result
        except:
            pass
        return None

    # Helper: get storey name
    def get_storey_name(el):
        try:
            for rel in el.ContainedInStructure:
                s = rel.RelatingStructure
                if s.is_a('IfcBuildingStorey'):
                    return s.Name
        except:
            pass
        return None

    # Helper: get pset properties
    def get_pset_props(el):
        props = {}
        try:
            psets = util_elem.get_psets(el)
            for pn, pv in psets.items():
                if isinstance(pv, dict):
                    for k, v in pv.items():
                        if k != 'id' and isinstance(v, (str, int, float, bool)):
                            props[k] = v
        except:
            pass
        return props

    # Walls
    seen = set()
    for w in ifc.by_type('IfcWallStandardCase') + ifc.by_type('IfcWall'):
        if w.GlobalId in seen:
            continue
        seen.add(w.GlobalId)
        props = get_pset_props(w)
        profile = get_profile(w)
        model['walls'].append({
            'name': w.Name,
            'storey': get_storey_name(w),
            'is_external': props.get('IsExternal'),
            'load_bearing': props.get('LoadBearing'),
            'profile': profile,
        })

    # Columns
    for c in ifc.by_type('IfcColumn'):
        props = get_pset_props(c)
        profile = get_profile(c)
        model['columns'].append({
            'name': c.Name,
            'storey': get_storey_name(c),
            'load_bearing': props.get('LoadBearing'),
            'profile': profile,
        })

    # Beams
    for b in ifc.by_type('IfcBeam'):
        profile = get_profile(b)
        model['beams'].append({
            'name': b.Name,
            'storey': get_storey_name(b),
            'profile': profile,
        })

    # Slabs
    for s in ifc.by_type('IfcSlab'):
        profile = get_profile(s)
        model['slabs'].append({
            'name': s.Name,
            'storey': get_storey_name(s),
            'predefined_type': s.PredefinedType or 'FLOOR',
            'profile': profile,
        })

    # Doors
    for d in ifc.by_type('IfcDoor'):
        model['doors'].append({
            'name': d.Name,
            'storey': get_storey_name(d),
            'width': d.OverallWidth,
            'height': d.OverallHeight,
        })

    # Windows
    for w in ifc.by_type('IfcWindow'):
        model['windows'].append({
            'name': w.Name,
            'storey': get_storey_name(w),
            'width': w.OverallWidth,
            'height': w.OverallHeight,
        })

    # Stairs
    for s in ifc.by_type('IfcStair'):
        model['stairs'].append({'name': s.Name, 'storey': get_storey_name(s)})
    for s in ifc.by_type('IfcStairFlight'):
        model['stair_flights'].append({'name': s.Name, 'storey': get_storey_name(s)})

    # Roofs
    for r in ifc.by_type('IfcRoof'):
        model['roofs'].append({'name': r.Name})

    return model


# ═══════════════════════════════════════════════════════════════════════════
# PART 2: Structured Text (JSON) → IFC
# ═══════════════════════════════════════════════════════════════════════════

def create_ifc_from_json(model, output_path):
    """Reconstruct an IFC file from structured JSON model."""
    schema = model.get('schema', 'IFC2X3')
    ifc = ifcopenshell.file(schema=schema)

    # ── Owner setup ──
    person = ifcopenshell.api.run('owner.add_person', ifc, identification='BIMNET', family_name='System')
    org = ifcopenshell.api.run('owner.add_organisation', ifc, identification='BIMNET', name='BIMNet Text2BIM')
    pao = ifcopenshell.api.run('owner.add_person_and_organisation', ifc, person=person, organisation=org)
    owner_settings.get_user = lambda f: pao

    if schema == 'IFC2X3':
        app = ifc.createIfcApplication()
        app.ApplicationDeveloper = org
        app.Version = '1.0'
        app.ApplicationFullName = 'BIMNet Text2BIM'
        app.ApplicationIdentifier = 'bimnet'
        owner_settings.get_application = lambda f: app

    ifcopenshell.api.run('owner.create_owner_history', ifc)

    # ── Project ──
    project = ifcopenshell.api.run('root.create_entity', ifc,
        ifc_class='IfcProject', name=model['project'].get('name', 'Project'))
    context = ifcopenshell.api.run('context.add_context', ifc, context_type='Model')

    # Units (millimeters)
    length = ifc.createIfcSIUnit(None, 'LENGTHUNIT', 'MILLI', 'METRE')
    ifcopenshell.api.run('unit.assign_unit', ifc, units=[length])

    # ── Hierarchy ──
    site = ifcopenshell.api.run('root.create_entity', ifc,
        ifc_class='IfcSite', name=model['site'].get('name', 'Site'))
    building = ifcopenshell.api.run('root.create_entity', ifc,
        ifc_class='IfcBuilding', name=model['building'].get('name', 'Building'))

    ifcopenshell.api.run('aggregate.assign_object', ifc, products=[site], relating_object=project)
    ifcopenshell.api.run('aggregate.assign_object', ifc, products=[building], relating_object=site)

    # Storeys - create a mapping from name to entity
    storey_map = {}
    for st_data in model['storeys']:
        storey = ifcopenshell.api.run('root.create_entity', ifc,
            ifc_class='IfcBuildingStorey', name=st_data['name'])
        storey.Elevation = st_data.get('elevation', 0)
        storey_map[st_data['name']] = storey
        ifcopenshell.api.run('aggregate.assign_object', ifc, products=[storey], relating_object=building)

    # Default storey if none defined
    if not storey_map:
        default_storey = ifcopenshell.api.run('root.create_entity', ifc,
            ifc_class='IfcBuildingStorey', name='Default Storey')
        storey_map['Default Storey'] = default_storey
        ifcopenshell.api.run('aggregate.assign_object', ifc, products=[default_storey], relating_object=building)

    # ── Helper: get or create storey ──
    def get_storey(storey_name):
        if storey_name and storey_name in storey_map:
            return storey_map[storey_name]
        return list(storey_map.values())[0]  # fallback to first storey

    def write_pset(product, name, properties):
        values = {k: v for k, v in properties.items() if v is not None}
        if not values:
            return
        pset = ifcopenshell.api.run('pset.add_pset', ifc, product=product, name=name)
        ifcopenshell.api.run('pset.edit_pset', ifc, pset=pset, properties=values)

    # ── Materials ──
    mat_map = {}
    for mat_name in model['materials']:
        mat = ifcopenshell.api.run('material.add_material', ifc, name=mat_name)
        mat_map[mat_name] = mat

    # ── Walls ──
    wall_entities = []
    for w_data in model['walls']:
        wall = ifcopenshell.api.run('root.create_entity', ifc,
            ifc_class='IfcWall', name=w_data.get('name', 'Wall'))
        storey = get_storey(w_data.get('storey'))
        ifcopenshell.api.run('spatial.assign_container', ifc, products=[wall], relating_structure=storey)

        # Geometry
        profile = w_data.get('profile')
        if profile:
            if profile.get('type') == 'rectangle':
                length_val = profile.get('x_dim', 5000)
                thickness_val = profile.get('y_dim', 240)
                height_val = profile.get('depth', 3000)
                # For walls, x_dim is length along wall, y_dim is thickness
                rep = ifcopenshell.api.run('geometry.add_wall_representation',
                    ifc, context=context,
                    length=length_val, height=height_val, thickness=thickness_val)
                ifcopenshell.api.run('geometry.assign_representation', ifc, product=wall, representation=rep)

        # Material assignment
        mat_name = model.get('material_assignments', {}).get(str(w_data.get('id', '')))
        if mat_name and mat_name in mat_map:
            ifcopenshell.api.run('material.assign_material', ifc, products=[wall], material=mat_map[mat_name])

        write_pset(wall, 'Pset_WallCommon', {
            'IsExternal': w_data.get('is_external'),
            'LoadBearing': w_data.get('load_bearing'),
        })

        wall_entities.append(wall)

    # ── Columns ──
    for c_data in model['columns']:
        col = ifcopenshell.api.run('root.create_entity', ifc,
            ifc_class='IfcColumn', name=c_data.get('name', 'Column'))
        storey = get_storey(c_data.get('storey'))
        ifcopenshell.api.run('spatial.assign_container', ifc, products=[col], relating_structure=storey)

    # ── Beams ──
    for b_data in model['beams']:
        beam = ifcopenshell.api.run('root.create_entity', ifc,
            ifc_class='IfcBeam', name=b_data.get('name', 'Beam'))
        storey = get_storey(b_data.get('storey'))
        ifcopenshell.api.run('spatial.assign_container', ifc, products=[beam], relating_structure=storey)

    # ── Slabs ──
    for s_data in model['slabs']:
        slab = ifcopenshell.api.run('root.create_entity', ifc,
            ifc_class='IfcSlab', name=s_data.get('name', 'Slab'))
        storey = get_storey(s_data.get('storey'))
        ifcopenshell.api.run('spatial.assign_container', ifc, products=[slab], relating_structure=storey)

    # ── Doors ──
    for d_data in model['doors']:
        door = ifcopenshell.api.run('root.create_entity', ifc,
            ifc_class='IfcDoor', name=d_data.get('name', 'Door'))
        door.OverallWidth = d_data.get('width')
        door.OverallHeight = d_data.get('height')
        storey = get_storey(d_data.get('storey'))
        ifcopenshell.api.run('spatial.assign_container', ifc, products=[door], relating_structure=storey)

    # ── Windows ──
    for w_data in model['windows']:
        win = ifcopenshell.api.run('root.create_entity', ifc,
            ifc_class='IfcWindow', name=w_data.get('name', 'Window'))
        win.OverallWidth = w_data.get('width')
        win.OverallHeight = w_data.get('height')
        storey = get_storey(w_data.get('storey'))
        ifcopenshell.api.run('spatial.assign_container', ifc, products=[win], relating_structure=storey)

    # ── Stairs ──
    for s_data in model['stairs']:
        stair = ifcopenshell.api.run('root.create_entity', ifc,
            ifc_class='IfcStair', name=s_data.get('name', 'Stair'))
        storey = get_storey(s_data.get('storey'))
        ifcopenshell.api.run('spatial.assign_container', ifc, products=[stair], relating_structure=storey)

    # ── Roofs ──
    for r_data in model['roofs']:
        roof = ifcopenshell.api.run('root.create_entity', ifc,
            ifc_class='IfcRoof', name=r_data.get('name', 'Roof'))

    # ── Write ──
    ifc.write(output_path)
    return ifc


# ═══════════════════════════════════════════════════════════════════════════
# PART 3: Round-trip verification
# ═══════════════════════════════════════════════════════════════════════════

def verify_roundtrip(original_path, reconstructed_path):
    """Compare original and reconstructed IFC files."""
    orig = ifcopenshell.open(original_path)
    recon = ifcopenshell.open(reconstructed_path)

    report = []
    report.append(f"Round-trip verification: {os.path.basename(original_path)}")
    report.append(f"{'='*60}")

    # Compare entity counts for key types
    for cls in ['IfcWall', 'IfcColumn', 'IfcBeam', 'IfcSlab', 'IfcDoor',
                'IfcWindow', 'IfcStair', 'IfcRoof', 'IfcMaterial',
                'IfcBuildingStorey', 'IfcBuilding', 'IfcSite', 'IfcProject']:
        orig_count = len(orig.by_type(cls))
        recon_count = len(recon.by_type(cls))
        status = '✓' if orig_count == recon_count else '✗'
        report.append(f"  {status} {cls}: {orig_count} → {recon_count}")

    # Compare wall names
    orig_names = sorted([w.Name for w in orig.by_type('IfcWall')])
    recon_names = sorted([w.Name for w in recon.by_type('IfcWall')])
    name_match = orig_names == recon_names
    report.append(f"  {'✓' if name_match else '✗'} Wall names match: {name_match}")

    return '\n'.join(report)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    base_dir = Path("E:/code for project/bimnet/dataset/ifc")
    json_dir = Path("E:/code for project/bimnet/dataset/processed/roundtrip_json")
    recon_dir = Path("E:/code for project/bimnet/dataset/processed/roundtrip_ifc")
    json_dir.mkdir(parents=True, exist_ok=True)
    recon_dir.mkdir(parents=True, exist_ok=True)

    # Process first 3 files as proof of concept
    test_files = [
        ('train', 'vt2_1.ifc'),
        ('train', 'i5n.ifc'),
        ('train', 'hxp.ifc'),
    ]

    for split, fname in test_files:
        ifc_path = base_dir / split / fname
        stem = fname.replace('.ifc', '')

        print(f"\n{'='*60}")
        print(f"Processing: {fname}")
        print(f"{'='*60}")

        # Step 1: IFC → JSON
        print(f"  Step 1: IFC → JSON ...", end=' ', flush=True)
        model = extract_ifc_to_json(str(ifc_path))
        json_path = json_dir / f"{stem}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(model, f, ensure_ascii=False, indent=2)
        print(f"✓ ({len(model['walls'])} walls, {len(model['doors'])} doors, {len(model['windows'])} windows)")

        # Step 2: JSON → IFC
        print(f"  Step 2: JSON → IFC ...", end=' ', flush=True)
        recon_path = recon_dir / f"{stem}_reconstructed.ifc"
        create_ifc_from_json(model, str(recon_path))
        print(f"✓")

        # Step 3: Verify
        print(f"  Step 3: Verify round-trip ...")
        report = verify_roundtrip(str(ifc_path), str(recon_path))
        print(report)

    print(f"\n{'='*60}")
    print(f"JSON中间表示: {json_dir}")
    print(f"重建IFC: {recon_dir}")


if __name__ == '__main__':
    main()
