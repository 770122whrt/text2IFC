"""Private compatibility probe: expand identity-mapped window Breps on a copy.

This is input preparation, never a model repair or an accepted experiment result.
Only the identity mapping / unstyled FacetedBrep family is supported. Geometry is
copied exactly, not tessellated or reconstructed; source files stay untouched.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.placement
import numpy as np

from .contracts import safe_path, write_json
from .inspection import native_validation
from .viewer import collect_meshes, compare_meshes


def expand_window_breps(source: Path, output: Path) -> dict:
    source, output = safe_path(Path(source)), safe_path(Path(output))
    if source == output:
        raise ValueError('SOURCE_OUTPUT_MUST_DIFFER')
    original = source.read_bytes()
    model = ifcopenshell.open(str(source))
    roots = {e.GlobalId: e.to_string() for e in model.by_type('IfcRoot')}
    before = collect_meshes(source)
    if before['errors']:
        raise ValueError('SOURCE_GEOMETRY_FAILED')
    if model.by_type('IfcStyledItem'):
        raise ValueError('STYLED_BREP_EXPANSION_UNSUPPORTED')

    converted = []
    for window in model.by_type('IfcWindow'):
        if not window.Representation:
            raise ValueError('WINDOW_REPRESENTATION_MISSING')
        representations = list(window.Representation.Representations)
        bodies = [r for r in representations if r.RepresentationIdentifier == 'Body']
        if len(bodies) != 1:
            raise ValueError('WINDOW_BODY_MUST_BE_UNIQUE')
        body = bodies[0]
        if body.RepresentationType != 'MappedRepresentation':
            continue
        items = []
        copied = {}
        for item in body.Items:
            if not item.is_a('IfcMappedItem'):
                raise ValueError('WINDOW_BODY_MAPPING_UNSUPPORTED')
            transform = ifcopenshell.util.placement.get_mappeditem_transformation(item)
            if not np.allclose(transform, np.eye(4), atol=1e-10, rtol=0):
                raise ValueError('NONIDENTITY_WINDOW_MAPPING')
            mapped = item.MappingSource.MappedRepresentation
            if mapped.RepresentationType != 'Brep' or not all(
                    solid.is_a('IfcFacetedBrep') for solid in mapped.Items):
                raise ValueError('WINDOW_MAPPING_MUST_BE_FACETED_BREP')
            items.extend(ifcopenshell.util.element.copy_deep(
                model, solid, copied_entities=copied) for solid in mapped.Items)
        # Keep existing ShapeModel / ProductDefinitionShape ownership intact.
        # IFC2X3 WR11 also disallows an abandoned ShapeRepresentation.
        body.Items = items
        body.RepresentationType = 'Brep'
        converted.append(window.GlobalId)

    # Publish only after reopening, validation and geometry/identity checks.
    staged = output.with_suffix('.pending.ifc')
    if staged.exists():
        raise ValueError('COMPATIBILITY_STAGING_FILE_ALREADY_EXISTS')
    try:
        model.write(str(staged))
        reopened = ifcopenshell.open(str(staged))
        after = collect_meshes(staged)
        comparisons = compare_meshes(before, after, sorted(before['meshes']))
        new_roots = {e.GlobalId: e.to_string() for e in reopened.by_type('IfcRoot')}
        validation = native_validation(str(staged))
        checks = {
            'source_unchanged': source.read_bytes() == original,
            'same_schema': reopened.schema == model.schema,
            'same_root_identities': set(new_roots) == set(roots),
            'all_root_attributes_and_relations_unchanged': roots == new_roots,
            'same_geometry_members': set(before['meshes']) == set(after['meshes']),
            'all_world_vertices_faces_and_placements_unchanged': all(r['unchanged'] for r in comparisons),
            'no_geometry_errors': not after['errors'],
            'all_windows_have_geometry': all(w.GlobalId in after['meshes'] for w in reopened.by_type('IfcWindow')),
            'all_window_bodies_direct': all(r.RepresentationType != 'MappedRepresentation'
                for w in reopened.by_type('IfcWindow') for r in w.Representation.Representations
                if r.RepresentationIdentifier == 'Body'),
            'native_schema_express_passed': validation['passed'],
        }
        if not all(checks.values()):
            raise ValueError('COMPATIBILITY_PRESERVATION_FAILED: ' +
                ', '.join(name for name, passed in checks.items() if not passed))
        windows = []
        for window in reopened.by_type('IfcWindow'):
            geometry = after['meshes'][window.GlobalId]
            storey = ifcopenshell.util.element.get_container(window)
            windows.append({'guid': window.GlobalId, 'name': window.Name,
                'storey': storey.Name if storey else None,
                'bounds_world_m': geometry['bounds'],
                'center_world_m': [sum(axis) / 2 for axis in geometry['bounds']],
                'converted': window.GlobalId in converted})
        staged.replace(output)
        return {'purpose': 'private viewer compatibility candidate; pending usBIM confirmation',
            'source': str(source), 'output': str(output), 'ifcopenshell_version': ifcopenshell.version,
            'converted_window_count': len(converted), 'window_count': len(windows),
            'compared_geometry_count': len(comparisons), 'checks': checks,
            'validation': validation, 'windows': windows,
            'usbim_visual_verification': 'pending_human_review',
            'formal_input_replaced': False}
    finally:
        if staged.exists():
            staged.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report_path = safe_path(args.report)
    if report_path in {safe_path(args.source), safe_path(args.output)}:
        raise ValueError('REPORT_MUST_DIFFER_FROM_IFC_PATHS')
    report = expand_window_breps(args.source, args.output)
    write_json(report_path, report)
    print(f"Expanded {report['converted_window_count']} windows; "
          f"preserved {report['compared_geometry_count']} element meshes; "
          "schema + EXPRESS passed. usBIM verification is pending.")


if __name__ == '__main__':
    main()
