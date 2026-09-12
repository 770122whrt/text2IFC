"""Verify requested channels on actual IFC Body items, never provenance JSON."""
import math
from . import item_appearance_signatures
from text2ifc_contract.part_appearance import valid_part_appearance


def read_part_styles(product):
    representation = getattr(product, 'Representation', None)
    if not representation:
        return {}
    body = {i.id() for r in representation.Representations if r.RepresentationIdentifier == 'Body' for i in r.Items}
    result = {}
    for aspect in getattr(representation, 'HasShapeAspects', ()):
        role = {'Framing': 'frame', 'Lining': 'frame', 'Panel': 'panel', 'Glazing': 'glazing'}.get(aspect.Name)
        if role:
            for rep in aspect.ShapeRepresentations:
                for item in rep.Items:
                    if item.id() in body:
                        result.setdefault(role, []).append(item_appearance_signatures(item))
    return result


def part_request_matches(product, requested):
    if not valid_part_appearance(requested, product.is_a()):
        return False
    actual = read_part_styles(product)
    for part, channels in requested.items():
        values = actual.get(part, [])
        if not values or any(len(v) != 1 for v in values):
            return False
        wanted = dict(zip(('red', 'green', 'blue'), channels.get('color', [])))
        if 'transparency' in channels:
            wanted['transparency'] = channels['transparency']
        if any(not all(math.isclose(v[0][k], n, rel_tol=0, abs_tol=1e-6) for k, n in wanted.items()) for v in values):
            return False
    return True
