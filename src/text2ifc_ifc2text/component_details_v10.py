"""Native parametric door/window extraction; unsupported geometry is never boxed.

This module reads source data at IFC2Text only. The generation side receives its
public description, not the source IFC or this reader's diagnostic evidence.
"""
from __future__ import annotations

import math
import json
import numpy as np
import ifcopenshell.util.placement as placement
import ifcopenshell.util.unit as unit

from text2ifc_contract.component_geometry import validate_components, MAX_SOLIDS
from text2ifc_presentation import item_appearance_signatures
from jsonschema import Draft202012Validator
from text2ifc_contract.schema import load_schema_v26

VERSION = 'text2ifc/ifc2text-component-detail/1.0'


class UnsupportedComponent(ValueError):
    pass


def _position(matrix, scale):
    return {'origin':(matrix[:3,3]*scale).tolist(), 'axis':matrix[:3,2].tolist(), 'ref_direction':matrix[:3,0].tolist()}


def _rigid(matrix):
    rotation = matrix[:3,:3]
    if not np.isfinite(matrix).all() or not np.allclose(rotation.T@rotation,np.eye(3),atol=1e-9,rtol=0) or not math.isclose(np.linalg.det(rotation),1.,abs_tol=1e-9):
        raise UnsupportedComponent('Scaled or reflected mapping requires an explicit supported normalization; it is not silently orthogonalized.')


def _polyline(curve, scale):
    if not curve.is_a('IfcPolyline'):
        raise UnsupportedComponent(f'Unsupported profile curve {curve.is_a()}; straight closed polylines are required.')
    points = [list(p.Coordinates) for p in curve.Points]
    if any(len(p) != 2 for p in points):
        raise UnsupportedComponent('A 2D profile is required.')
    return [[float(x)*scale for x in p] for p in points]


def _solid(item, matrix, scale, index, inherited_style):
    if item.is_a() != 'IfcExtrudedAreaSolid':
        raise UnsupportedComponent(f'{item.is_a()} is outside native straight-extrusion support.')
    area = item.SweptArea
    profile_matrix = np.eye(4)
    if area.is_a() == 'IfcRectangleProfileDef':
        profile = {'kind':'rectangle','x':float(area.XDim)*scale,'y':float(area.YDim)*scale}
        if area.Position: profile_matrix = placement.get_axis2placement(area.Position)
    elif area.is_a() == 'IfcCircleProfileDef':
        profile = {'kind':'circle','radius':float(area.Radius)*scale}
        if area.Position: profile_matrix = placement.get_axis2placement(area.Position)
    elif area.is_a() in {'IfcArbitraryClosedProfileDef','IfcArbitraryProfileDefWithVoids'}:
        profile = {'kind':'polygon','points':_polyline(area.OuterCurve,scale)}
        if area.is_a() == 'IfcArbitraryProfileDefWithVoids':
            profile['holes'] = [_polyline(c,scale) for c in area.InnerCurves]
    else:
        raise UnsupportedComponent(f'Unsupported profile {area.is_a()}.')
    transformed = matrix @ placement.get_axis2placement(item.Position) @ profile_matrix
    _rigid(transformed)
    # Extrusion direction is authored in solid coordinates, not profile coordinates.
    direction = profile_matrix[:3,:3].T @ np.asarray(item.ExtrudedDirection.DirectionRatios,dtype=float)
    definition = {'id':f'geometry-{index:03d}','profile':profile,'position':_position(transformed,scale),
                  'direction':direction.tolist(),'depth':float(item.Depth)*scale}
    part = {'id':f'part-{index:03d}', 'role':'frame' if profile.get('holes') else 'solid',
            'geometry_refs':[definition['id']], 'placement':_position(np.eye(4),1.)}
    signatures = item_appearance_signatures(item) or inherited_style
    if len(signatures)>1:
        raise UnsupportedComponent('Multiple effective surface styles require clarification.')
    if signatures:
        style = signatures[0]
        part['appearance'] = {'color':[float(style[k]) for k in ('red','green','blue')], 'transparency':float(style['transparency'])}
    return definition,part


def read_component_geometry(product):
    """All-or-refuse product geometry, with item-level reasons for human review."""
    result = {'schema_version':VERSION,'product_global_id':getattr(product,'GlobalId',None),
              'product_name':getattr(product,'Name',None), 'source_product_id':product.id()}
    unsupported = []; definitions = []; parts = []
    def reject(item, reason):
        unsupported.append({'source_item_id':item.id(),'ifc_class':item.is_a(),'reason':reason,
                            'impact':'The product has no complete supported reconstruction; no simplified replacement is emitted.'})
    if product.is_a() not in {'IfcDoor','IfcWindow'}:
        reject(product,'Only IfcDoor and IfcWindow component extraction is supported.')
    if product.file.schema != 'IFC2X3':
        reject(product,'This component route currently admits IFC2X3 sources only; IFC4 has not been admitted.')
    scale = unit.calculate_unit_scale(product.file)*1000
    if not math.isfinite(scale) or scale<=0:
        reject(product,'Invalid length unit.')
    bodies = [r for r in getattr(getattr(product,'Representation',None),'Representations',()) if r.RepresentationIdentifier == 'Body']
    if len(bodies) != 1:
        reject(product,'Exactly one Body representation is required.')
    named_items = {}
    for aspect in getattr(getattr(product,'Representation',None),'HasShapeAspects',()):
        try:
            metadata = json.loads(aspect.Description or '{}')
        except (ValueError,TypeError):
            continue
        if not isinstance(metadata,dict) or metadata.get('version') != 'text2ifc/component-part/1.0': continue
        for shape in aspect.ShapeRepresentations:
            for item in shape.Items:
                if item.id() in named_items:
                    reject(item,'Duplicate managed part ownership.')
                named_items[item.id()] = (aspect.Name,metadata.get('role'))
    visited = 0
    def walk(item, matrix, stack, inherited_style=()):
        nonlocal visited
        visited += 1
        if visited > MAX_SOLIDS or len(stack)>16:
            raise UnsupportedComponent('Mapping/solid expansion limit exceeded.')
        if item.id() in stack:
            reject(item,'Cyclic representation mapping.'); return
        try:
            if item.is_a('IfcMappedItem'):
                transform = placement.get_mappeditem_transformation(item)
                _rigid(transform)
                style = item_appearance_signatures(item) or inherited_style
                for child in item.MappingSource.MappedRepresentation.Items:
                    walk(child,matrix@transform,(*stack,item.id()),style)
            else:
                definition,part = _solid(item,matrix,scale,len(parts)+1,inherited_style)
                # Keep managed stable part IDs across successive native loops.
                # Ordinary source STEP IDs remain diagnostic only.
                definition['id'] = f'geometry-{len(definitions)+1:03d}'
                part['geometry_refs'] = [definition['id']]
                if item.id() in named_items:
                    part['id'],part['role'] = named_items[item.id()]
                existing = next((p for p in parts if p['id'] == part['id']),None)
                if existing:
                    if existing.get('appearance') != part.get('appearance') or existing['role'] != part['role']:
                        raise UnsupportedComponent('Conflicting styles or roles within a managed part.')
                    existing['geometry_refs'].extend(part['geometry_refs'])
                else:
                    parts.append(part)
                definitions.append(definition)
        except (UnsupportedComponent, ValueError, TypeError, AttributeError, RuntimeError) as exc:
            reject(item,str(exc))
    if not unsupported:
        try:
            for item in bodies[0].Items: walk(item,np.eye(4),())
        except UnsupportedComponent as exc:
            reject(product,str(exc))
    representation = {'kind':'component_geometry','geometry_version':'text2ifc/components/1.0','definitions':definitions,'parts':parts}
    if not unsupported:
        if not parts: reject(product,'Empty Body has no supported geometry.')
        else:
            schema = load_schema_v26()
            validator = Draft202012Validator({'$defs':schema['$defs'],'$ref':'#/$defs/componentGeometry'})
            for error in validator.iter_errors(representation):
                reject(product,f'Invalid native parameters at {list(error.path)}: {error.message}')
            if not unsupported:
                for issue in validate_components(representation,product.is_a(),'/Representation'):
                    reject(product,f'{issue.code}: {issue.path}: {issue.message}')
    if unsupported:
        return {**result,'status':'unsupported','unsupported':unsupported}
    return {**result,'status':'supported','representation':representation,
            'scope':'Geometry, RGB and transparency. Roles without source semantics are neutral solid labels.',
            'not_evaluated':['physical_part_materials','specular_highlights','non_body_representations']}
