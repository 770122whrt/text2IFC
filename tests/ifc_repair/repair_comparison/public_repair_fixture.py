"""Hand-authored public-D-only script for OFFLINE TOOL TESTS, never a model run.

Only model.ifc is read. The script follows the two fixed public development
requests. It is not installed as a tool/helper for A/C and is not a production
localizer or a source of model capability scores.
"""
import sys
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.guid
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

model = ifcopenshell.open('model.ifc')
scale = ifcopenshell.util.unit.calculate_unit_scale(model)
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)


def bounds(product):
    shape = ifcopenshell.geom.create_shape(settings, product)
    points = np.array(shape.geometry.verts).reshape(-1, 3)
    return np.stack([points.min(axis=0), points.max(axis=0)], axis=1)


def relocated(product, delta):
    clone = ifcopenshell.util.element.copy(model, product)
    representation = product.Representation
    copied_representations = [ifcopenshell.util.element.copy(model, rep) for rep in representation.Representations]
    clone.Representation = model.createIfcProductDefinitionShape(representation.Name, representation.Description, copied_representations)
    matrix = ifcopenshell.util.placement.get_local_placement(product.ObjectPlacement).copy()
    matrix[:3, 3] += delta / scale
    point = model.createIfcCartesianPoint(tuple(float(v) for v in matrix[:3, 3]))
    axis = model.createIfcDirection(tuple(float(v) for v in matrix[:3, 2]))
    ref = model.createIfcDirection(tuple(float(v) for v in matrix[:3, 0]))
    clone.ObjectPlacement = model.createIfcLocalPlacement(None, model.createIfcAxis2Placement3D(point, axis, ref))
    return clone


def relation(ifc_class, **attributes):
    return model.create_entity(ifc_class, GlobalId=ifcopenshell.guid.new(), OwnerHistory=model.by_type('IfcOwnerHistory')[0], **attributes)


if sys.argv[1] == 'window':
    walls = []
    for wall in model.by_type('IfcWall'):
        box = bounds(wall)
        if box[0, 1] - box[0, 0] < .3 and box[1, 1] - box[1, 0] > 10 and abs(box[2, 0]) < .001:
            walls.append((box[0].mean(), wall))
    host = min(walls, key=lambda item: item[0])[1]
    windows = [fill.RelatedBuildingElement for void in host.HasOpenings for fill in void.RelatedOpeningElement.HasFillings
               if fill.RelatedBuildingElement.is_a('IfcWindow')]
    windows.sort(key=lambda w: bounds(w)[1].mean(), reverse=True)
    reference, other = windows[1:3]
    delta = (bounds(other).mean(axis=1) - bounds(reference).mean(axis=1)) / 2
    target = relocated(reference, delta)
    opening = relocated(reference.FillsVoids[0].RelatingOpeningElement, delta)
    relation('IfcRelVoidsElement', RelatingBuildingElement=host, RelatedOpeningElement=opening)
else:
    openings = [o for o in model.by_type('IfcOpeningElement') if not o.HasFillings and o.VoidsElements
                and np.max(np.abs(bounds(o).mean(axis=1)[:2] - [1.915, -6.188])) < .01]
    assert len(openings) == 1
    opening = openings[0]
    references = [d for d in model.by_type('IfcDoor') if np.max(np.abs(bounds(d).mean(axis=1)[:2] - [6.889, -11.612])) < .01]
    assert len(references) == 1
    reference = references[0]
    opening_box, reference_box = bounds(opening), bounds(reference)
    delta = opening_box.mean(axis=1) - reference_box.mean(axis=1)
    delta[2] = opening_box[2, 0] - reference_box[2, 0]
    target = relocated(reference, delta)
relation('IfcRelFillsElement', RelatingOpeningElement=opening, RelatedBuildingElement=target)
container = reference.ContainedInStructure[0]
container.RelatedElements = (*container.RelatedElements, target)
model.write('output/repaired.ifc')
print('offline public-input fixture written')
