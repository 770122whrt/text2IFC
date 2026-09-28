"""Compile parameterized parts to actual IFC solids and ShapeAspects."""
import json

import numpy as np
from ifcopenshell.api.geometry import assign_representation
from text2ifc_contract.component_geometry import expanded_parts
from text2ifc_contract.placement import _local_transform

from .geometry import _axis2placement3d


ASPECT_VERSION = 'text2ifc/component-part/1.0'


def _curve(model, points):
    return model.createIfcPolyline([model.createIfcCartesianPoint(tuple(float(x) for x in p)) for p in points])


def _profile(model, spec):
    origin = model.createIfcAxis2Placement2D(model.createIfcCartesianPoint((0.,0.)), None)
    if spec['kind'] == 'rectangle':
        return model.createIfcRectangleProfileDef('AREA',None,origin,float(spec['x']),float(spec['y']))
    if spec['kind'] == 'circle':
        return model.createIfcCircleProfileDef('AREA',None,origin,float(spec['radius']))
    outer = _curve(model,spec['points'])
    if spec.get('holes'):
        return model.createIfcArbitraryProfileDefWithVoids('AREA',None,outer,[_curve(model,h) for h in spec['holes']])
    return model.createIfcArbitraryClosedProfileDef('AREA',None,outer)


def solid_transform(part, definition):
    return np.asarray(_local_transform(part['placement'])) @ np.asarray(_local_transform(definition['position']))


def add_component_geometry(model, product, representation, context):
    definitions = {d['id']:d for d in representation['definitions']}
    parts = []
    for part in expanded_parts(representation):
        items = []
        for ref in part['geometry_refs']:
            spec = definitions[ref]
            matrix = solid_transform(part,spec)
            position = {'origin':matrix[:3,3].tolist(),'axis':matrix[:3,2].tolist(),'ref_direction':matrix[:3,0].tolist()}
            item = model.createIfcExtrudedAreaSolid(_profile(model,spec['profile']),_axis2placement3d(model,position),
                model.createIfcDirection(tuple(float(v) for v in spec['direction'])),float(spec['depth']))
            items.append(item)
        parts.append((part,items))
    body = model.createIfcShapeRepresentation(context,'Body','SweptSolid',[i for _,items in parts for i in items])
    assign_representation(model,product=product,representation=body)
    for part,items in parts:
        shape = model.createIfcShapeRepresentation(context,'Body','SweptSolid',items)
        model.createIfcShapeAspect([shape],part['id'],json.dumps({'version':ASPECT_VERSION,'role':part['role']},sort_keys=True),
            True,product.Representation)


def component_display_spec(part, record, document):
    from text2ifc_presentation import AppearanceSpec
    from text2ifc_presentation.generation import THEMES
    palette = THEMES[document.get('appearance',{}).get('profile','neutral-architectural')]
    # A part's requested display wins; missing display uses the ordinary product theme.
    fallback = 'glazing' if record['ifc_class'] == 'IfcWindow' else 'panel'
    type_id = next((r['attributes']['RelatingType'] for r in document['relationships']
        if r['ifc_class'] == 'IfcRelDefinesByType' and record['id'] in r['attributes']['RelatedObjects']),None)
    inherited = next((e.get('appearance') for e in document['entities'] if e['id'] == type_id),None)
    appearance = part.get('appearance') or record.get('appearance') or inherited
    return AppearanceSpec('component', *(appearance.get('color',palette[fallback]) if appearance else palette[fallback]),
        transparency=appearance.get('transparency',0.) if appearance else (.45 if fallback == 'glazing' else 0.))


def apply_component_appearance(model, document):
    from .semantic_verification import _index
    from text2ifc_presentation import assign_item_appearance
    indexed = _index(model)
    for record in document['entities']:
        rep = record['attributes'].get('Representation',{})
        if rep.get('kind') != 'component_geometry': continue
        product = indexed[record['id']][0]
        parts = {p['id']:p for p in expanded_parts(rep)}
        for aspect in product.Representation.HasShapeAspects:
            spec = component_display_spec(parts[aspect.Name],record,document)
            for shape in aspect.ShapeRepresentations:
                for item in shape.Items:
                    assign_item_appearance(model,item=item,spec=spec)


def verify_components(model, document):
    """Read real IFC geometry, ownership, display and nominal sizes after reopening.

    No properties written by this compiler are used as evidence of the solids.
    Precision here checks deterministic compilation; roundtrip comparison has its
    separate 1 mm acceptance tolerance.
    """
    from ifcopenshell.util.placement import get_axis2placement, get_local_placement
    from text2ifc_contract.placement import world_transform_for
    from text2ifc_presentation import item_appearance_signatures
    from .semantic_verification import _index
    from .verification import IfcValidationIssue
    indexed = _index(model); issues = []
    def close(a,b):
        a,b = np.asarray(a), np.asarray(b)
        return a.shape == b.shape and np.allclose(a,b,atol=1e-6,rtol=0)
    def points(curve):
        return [list(p.Coordinates) for p in curve.Points]
    for record in document['entities']:
        rep = record['attributes'].get('Representation',{})
        if rep.get('kind') != 'component_geometry': continue
        def fail(message):
            issues.append(IfcValidationIssue('IFC_COMPONENT_MISMATCH',record['id'],'Representation',message))
        products = indexed.get(record['id'],[])
        if len(products) != 1:
            fail('Expected exactly one product identity.'); continue
        product = products[0]
        try:
            if product.is_a() != record['ifc_class']: fail('Product class changed.')
            for name in ('OverallWidth','OverallHeight'):
                if name in record['attributes'] and not close(getattr(product,name),record['attributes'][name]):
                    fail(f'Nominal {name} changed.')
            if not close(get_local_placement(product.ObjectPlacement),world_transform_for(document,record['id'])):
                fail('Product placement changed.')
            bodies = [s for s in product.Representation.Representations if s.RepresentationIdentifier == 'Body']
            if len(bodies) != 1 or bodies[0].RepresentationType != 'SweptSolid':
                fail('Expected one Body/SweptSolid.'); continue
            actual = list(product.Representation.HasShapeAspects)
            parts = expanded_parts(rep)
            if len(actual) != len(parts) or {a.Name for a in actual} != {p['id'] for p in parts}:
                fail('Part identities missing, duplicated or unexpected.'); continue
            aspects = {a.Name:a for a in actual}; definitions = {d['id']:d for d in rep['definitions']}
            owned = []
            for part in parts:
                aspect = aspects[part['id']]
                if json.loads(aspect.Description) != {'version':ASPECT_VERSION,'role':part['role']} or not aspect.ProductDefinitional:
                    fail(f"Part role changed: {part['id']}.")
                if len(aspect.ShapeRepresentations) != 1:
                    fail('Unexpected part representations.'); continue
                items = list(aspect.ShapeRepresentations[0].Items)
                owned.extend(i.id() for i in items)
                if len(items) != len(part['geometry_refs']): fail('Part solid count changed.'); continue
                for item,ref in zip(items,part['geometry_refs']):
                    spec = definitions[ref]; profile = spec['profile']; area = item.SweptArea
                    if not item.is_a('IfcExtrudedAreaSolid'): fail('Unexpected solid kind.'); continue
                    if not close(item.Depth,spec['depth']): fail('Extrusion depth changed.')
                    direction = np.asarray(spec['direction'],dtype=float); direction /= np.linalg.norm(direction)
                    actual_direction = np.asarray(item.ExtrudedDirection.DirectionRatios); actual_direction /= np.linalg.norm(actual_direction)
                    if not close(direction,actual_direction): fail('Extrusion direction changed.')
                    if not close(get_axis2placement(item.Position),solid_transform(part,spec)): fail('Solid placement changed.')
                    if profile['kind'] == 'rectangle':
                        if not area.is_a('IfcRectangleProfileDef') or not close([area.XDim,area.YDim],[profile['x'],profile['y']]): fail('Rectangle changed.')
                    elif profile['kind'] == 'circle':
                        if not area.is_a('IfcCircleProfileDef') or not close(area.Radius,profile['radius']): fail('Circle changed.')
                    else:
                        expected_class = 'IfcArbitraryProfileDefWithVoids' if profile.get('holes') else 'IfcArbitraryClosedProfileDef'
                        if area.is_a() != expected_class or not close(points(area.OuterCurve),profile['points']): fail('Polygon changed.')
                        holes = list(getattr(area,'InnerCurves',()))
                        if len(holes) != len(profile.get('holes',[])) or any(not close(points(a),b) for a,b in zip(holes,profile.get('holes',[]))): fail('Profile holes changed.')
                    if profile['kind'] in {'rectangle','circle'} and not close(get_axis2placement(area.Position),np.eye(4)):
                        fail('Profile placement changed.')
                    styles = item_appearance_signatures(item)
                    wanted = component_display_spec(part,record,document).signature()
                    if len(styles) != 1 or any(not close(styles[0][k],wanted[k]) for k in ('red','green','blue','transparency')):
                        fail('Part display changed.')
            body_ids = [i.id() for i in bodies[0].Items]
            if len(owned) != len(set(owned)) or len(body_ids) != len(set(body_ids)) or set(owned) != set(body_ids):
                fail('Missing, shared or unowned Body solids.')
        except (AttributeError, TypeError, ValueError, KeyError, RuntimeError) as exc:
            fail(f'Cannot read actual component geometry: {exc}')
    return tuple(issues)
