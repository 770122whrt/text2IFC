"""Read-only description observations, including actual projected space outlines.

Extends the historical 0.1 facts without changing the legacy extraction API.
A projection is not a navigable room, and an extraction gap is not source absence.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit
from shapely.geometry import Polygon
from shapely.ops import unary_union

from text2ifc_extractor.materials import extract_material_assignments
from .facts import extract_building_facts

CATEGORIES = ('walls', 'openings', 'doors', 'windows', 'spaces', 'stairs', 'slabs', 'coverings')


def all_items(facts: dict[str, Any]):
    for storey in [*facts['storeys'], facts.get('unassigned', {})]:
        for category in CATEGORIES:
            for item in storey.get(category, []):
                yield category, item


def projected_footprint(entity: Any) -> dict[str, Any]:
    """Union non-degenerate mesh triangles in XY, in millimetres, retaining holes."""
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    shape = ifcopenshell.geom.create_shape(settings, entity)
    geometry = shape.geometry
    vertices = list(geometry.verts)
    faces = list(geometry.faces)
    points = [tuple(1000.0 * vertices[j + k] for k in range(3))
              for j in range(0, len(vertices), 3)]
    if not points:
        raise ValueError('SPACE_MESH_EMPTY')
    triangles = []
    for j in range(0, len(faces), 3):
        triangle = Polygon([points[faces[j + k]][:2] for k in range(3)])
        if triangle.is_valid and triangle.area > 1e-6:
            triangles.append(triangle)
    if not triangles:
        raise ValueError('SPACE_PROJECTION_EMPTY')
    outline = unary_union(triangles)
    polygons = [outline] if outline.geom_type == 'Polygon' else list(outline.geoms)
    if any(p.geom_type != 'Polygon' or not p.is_valid for p in polygons):
        raise ValueError('SPACE_PROJECTION_INVALID')
    def ring(coords):
        return [[round(float(x), 6), round(float(y), 6)] for x, y in coords]
    result = {
        'status': 'measured_projection', 'method': 'world_mesh_triangle_xy_union',
        'area_m2': round(outline.area / 1_000_000.0, 8),
        'polygons': [{'exterior_xy_mm': ring(p.exterior.coords),
                      'holes_xy_mm': [ring(h.coords) for h in p.interiors]}
                     for p in sorted(polygons, key=lambda p: (p.bounds, p.area))],
        'z_range_mm': [min(p[2] for p in points), max(p[2] for p in points)],
        'not_proven': ['walkability', 'room_function', 'semantic_connectivity'],
    }
    return result


def _associated(entity):
    return [r.RelatingMaterial for r in getattr(entity, 'HasAssociations', ()) or ()
            if r.is_a('IfcRelAssociatesMaterial')]


def _material(material, scale_mm: float) -> dict[str, Any]:
    if material.is_a('IfcMaterial'):
        return {'kind': 'single_material', 'name': str(material.Name) if material.Name else None}
    if material.is_a('IfcMaterialList'):
        return {'kind': 'material_list',
                'names': [str(m.Name) if m.Name else None for m in material.Materials]}
    usage = material.is_a('IfcMaterialLayerSetUsage')
    layer_set = material.ForLayerSet if usage else material
    if layer_set.is_a('IfcMaterialLayerSet'):
        record = {'kind': 'material_layer_set_usage' if usage else 'material_layer_set',
                  'name': getattr(layer_set, 'LayerSetName', None),
                  'layers': [{'name': str(l.Material.Name) if l.Material and l.Material.Name else None,
                              'thickness_mm': None if l.LayerThickness is None else float(l.LayerThickness)*scale_mm}
                             for l in layer_set.MaterialLayers]}
        if usage:
            record.update(direction=material.LayerSetDirection, direction_sense=material.DirectionSense,
                          offset_mm=float(material.OffsetFromReferenceLine)*scale_mm)
        return record
    return {'kind': 'unsupported_material_association', 'ifc_class': material.is_a()}


def read_materials(entity: Any, scale_mm: float) -> list[dict[str, Any]]:
    direct = _associated(entity)
    # Reuse the established layer-set usage parser; retain non-layer assignments too.
    existing, _ = extract_material_assignments(entity, scale_mm)
    records = []
    for value in direct:
        record = _material(value, scale_mm)
        record['origin'] = 'occurrence'
        if value.is_a('IfcMaterialLayerSetUsage') and existing:
            record['parser'] = 'text2ifc_extractor.materials+description_projection'
        records.append(record)
    if direct:
        return records
    types = []
    for r in [*(getattr(entity, 'IsTypedBy', ()) or ()), *(getattr(entity, 'IsDefinedBy', ()) or ())]:
        if r.is_a('IfcRelDefinesByType') and r.RelatingType not in types:
            types.append(r.RelatingType)
    for t in types:
        for value in _associated(t):
            records.append({**_material(value, scale_mm), 'origin': 'type',
                            'type_name': getattr(t, 'Name', None)})
    return records


def extract_description_facts(path: str | Path) -> dict[str, Any]:
    facts = extract_building_facts(path)
    facts['schema_version'] = 'text2ifc/ifc2text-facts/0.2'
    model = ifcopenshell.open(str(path))
    scale_mm = ifcopenshell.util.unit.calculate_unit_scale(model) * 1000.0
    roots: dict[str, list[Any]] = {}
    for entity in model.by_type('IfcRoot'):
        gid = getattr(entity, 'GlobalId', None)
        if gid:
            roots.setdefault(str(gid), []).append(entity)
    from .facts import _storey_for, _world_bounds_mm
    floors_by_gid = {s['source_global_id']: s for s in facts['storeys']}
    for category, cls, prefix in (('slabs', 'IfcSlab', 'L'), ('coverings', 'IfcCovering', 'C')):
        for s in [*facts['storeys'], facts['unassigned']]:
            s[category] = []
        for n, entity in enumerate(sorted(model.by_type(cls), key=lambda e: e.id()), 1):
            floor = _storey_for(entity)
            owner = floors_by_gid.get(getattr(floor, 'GlobalId', None))
            item = {'label':f'{prefix}{n:03d}', 'source_global_id':entity.GlobalId,
                    'name':getattr(entity, 'Name', None), 'ifc_class':cls,
                    'predefined_type':getattr(entity, 'PredefinedType', None),
                    'storey':owner['label'] if owner else None}
            try:
                item['bounds_mm'] = _world_bounds_mm(entity)
                item['centroid_mm'] = [(item['bounds_mm'][a][0]+item['bounds_mm'][a][1])/2 for a in ('x','y','z')]
            except Exception as error:
                facts['issues'].append({'code':'HORIZONTAL_ELEMENT_GEOMETRY_UNAVAILABLE',
                                        'entity':item['label'], 'error_type':type(error).__name__})
            (owner if owner is not None else facts['unassigned'])[category].append(item)
    # Do not silently choose an entity when a corrupt IFC duplicates an identity.
    for category, item in all_items(facts):
        entities = roots.get(item.get('source_global_id'), [])
        if len(entities) != 1:
            facts['issues'].append({'code': 'SOURCE_IDENTITY_NOT_UNIQUE', 'entity': item['label']})
            continue
        entity = entities[0]
        item['bbox_center_mm'] = item.get('centroid_mm')
        item['materials'] = read_materials(entity, scale_mm)
        item['material_status'] = 'observed' if item['materials'] else 'not_confirmed_by_extractor'
        if category in ('spaces', 'slabs', 'coverings'):
            try:
                item['footprint'] = projected_footprint(entity)
            except Exception as error:
                item['footprint'] = {'status': 'unavailable', 'error_type': type(error).__name__}
                facts['issues'].append({'code': 'SPACE_OUTLINE_UNAVAILABLE', 'entity': item['label']})
        if category == 'walls':
            # Material layer reference axes are not necessarily body centrelines.
            item['axis_interpretation'] = 'source_reference_axis_or_measured_proxy'
            item['reconstruction_status'] = ('approximate_axis' if item.get('measurement_method') == 'world_mesh_principal_axis'
                                             else 'source_reference_axis')
    # Use world placement for levels; retain declared Elevation as a separate observation.
    for storey in facts['storeys']:
        entities = roots.get(storey.get('source_global_id'), [])
        if len(entities) == 1:
            entity = entities[0]
            storey['declared_elevation_mm'] = storey.get('elevation_mm')
            if getattr(entity, 'ObjectPlacement', None):
                transform = ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement)
                storey['elevation_mm'] = float(transform[2, 3])*scale_mm
    represented = {item.get('source_global_id') for _, item in all_items(facts)}
    excluded = Counter(p.is_a() for p in model.by_type('IfcElement')
                       if getattr(p, 'GlobalId', None) not in represented)
    facts['unrepresented_classes'] = dict(sorted(excluded.items()))
    facts['description_precision'] = {'coordinate_unit': 'metre', 'coordinate_decimal_places': 2,
                                      'facts_unit': 'millimetre', 'facts_rounded_for_text_only': True}
    return facts
