"""Frozen independent addendum: read actual IFC parts against request HEX colours.

Never supplied to Provider. Hex is evaluated at its stated 8-bit precision;
raw IFC RGB and channel error are reported, not inferred from writer metadata.
"""
import argparse
import hashlib
import json
from pathlib import Path
import ifcopenshell

EXPECTED = {'frame': (51, 61, 64), 'panel': (168, 121, 80)}


def check(path):
    path = Path(path); model = ifcopenshell.open(str(path)); rows = []
    for family, count in [('IfcDoor', 15), ('IfcWindow', 40)]:
        products = model.by_type(family)
        rows.append({'check': family + ':count', 'expected': count, 'actual': len(products), 'passed': len(products) == count})
        for product in products:
            rep = product.Representation
            body = {i.id() for r in rep.Representations if r.RepresentationIdentifier == 'Body' for i in r.Items} if rep else set()
            for role, names in [('frame', {'Lining', 'Framing'}), *([('panel', {'Panel'})] if family == 'IfcDoor' else [])]:
                items = [i for a in getattr(rep, 'HasShapeAspects', ()) if a.Name in names
                         for r in a.ShapeRepresentations for i in r.Items if i.id() in body]
                actual = []
                for item in items:
                    surfaces = []
                    for binding in item.StyledByItem:
                        for wrapper in binding.Styles:
                            styles = wrapper.Styles if wrapper.is_a('IfcPresentationStyleAssignment') else [wrapper]
                            for style in styles:
                                if style.is_a('IfcSurfaceStyle'):
                                    surfaces.extend(s for s in style.Styles if s.is_a('IfcSurfaceStyleShading'))
                    colors = [[s.SurfaceColour.Red, s.SurfaceColour.Green, s.SurfaceColour.Blue] for s in surfaces]
                    actual.append({'item_id': item.id(), 'rgb': colors,
                        'rgb8': [[round(v * 255) for v in color] for color in colors]})
                wanted = list(EXPECTED[role])
                passed = bool(items) and all(len(r['rgb8']) == 1 and r['rgb8'][0] == wanted for r in actual)
                rows.append({'check': product.GlobalId + ':' + role, 'name': product.Name,
                    'expected_rgb8': wanted, 'actual': actual, 'passed': passed})
    return {'status': 'passed' if all(r['passed'] for r in rows) else 'failed',
        'ifc_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'basis': 'Frozen Chinese request; actual ShapeAspect Body-item styles at HEX 8-bit precision',
        'checks': rows, 'passed': sum(r['passed'] for r in rows), 'total': len(rows)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('ifc', type=Path); parser.add_argument('output', type=Path)
    args = parser.parse_args(); report = check(args.ifc)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('status', 'passed', 'total')}))
    raise SystemExit(0 if report['status'] == 'passed' else 1)
