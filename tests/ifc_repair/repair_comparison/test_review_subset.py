"""Private IFC views retain source geometry and never become repair inputs."""
import copy

import ifcopenshell
import ifcopenshell.util.element
import pytest

from scripts.ifc_repair.repair_comparison.contracts import sha256
from scripts.ifc_repair.repair_comparison.inspection import native_validation
from scripts.ifc_repair.repair_comparison.viewer import collect_meshes, compare_meshes
from tests.ifc_repair.repair_comparison.test_preparation import build, sample


def test_review_subset_preserves_meshes_and_sources_and_excludes_obstructions(sample):
    root, source, definition = sample
    model = ifcopenshell.open(str(source))
    wall = model.by_type('IfcWall')[0]
    obstruction = model.create_entity(
        'IfcBeam', GlobalId=ifcopenshell.guid.new(), OwnerHistory=wall.OwnerHistory,
        Name='unrelated obstruction', ObjectPlacement=ifcopenshell.util.element.copy_deep(
            model, wall.ObjectPlacement),
        Representation=ifcopenshell.util.element.copy_deep(
            model, wall.Representation, exclude=('IfcGeometricRepresentationContext',)),
    )
    model.write(str(source))
    definition['source']['sha256'] = sha256(source)
    _, _, _, package = build((root, source, definition))
    inputs = [package / 'private/reference.ifc', package / 'private/mutation/damaged.ifc',
              package / 'public/model.ifc', package / 'public/request.txt']
    original_bytes = {p: p.read_bytes() for p in inputs}

    from scripts.ifc_repair.repair_comparison.viewer import write_review_subsets
    report = write_review_subsets(package, definition)

    for side, filename, original in (
        ('G', 'review-original.ifc', inputs[0]),
        ('D', 'review-damaged.ifc', inputs[1]),
    ):
        view = package / 'private' / filename
        subset = ifcopenshell.open(str(view))
        assert not subset.by_type('IfcBeam')
        assert all(e.GlobalId != obstruction.GlobalId for e in subset.by_type('IfcProduct'))
        assert len(subset.by_type('IfcWall')) == 1
        assert len(subset.by_type('IfcOpeningElement')) == 1
        assert len(subset.by_type('IfcDoor')) == (1 if side == 'G' else 0)
        assert native_validation(subset)['passed']
        meshes = collect_meshes(view)
        comparisons = compare_meshes(collect_meshes(original), meshes, list(meshes['meshes']))
        assert all(row['unchanged'] for row in comparisons)
        assert report[side]['geometry_unchanged']
        assert report[side]['validation']['passed']
    assert all(p.read_bytes() == before for p, before in original_bytes.items())
    assert sorted(p.name for p in (package / 'public').iterdir()) == ['model.ifc', 'request.txt']


def test_unknown_review_target_is_rejected_before_writing(sample):
    _, _, definition, package = build(sample)
    definition = copy.deepcopy(definition)
    definition['damage']['target_guid'] = ifcopenshell.guid.new()
    from scripts.ifc_repair.repair_comparison.viewer import write_review_subsets
    with pytest.raises(ValueError, match='REVIEW_OBJECT_NOT_FOUND'):
        write_review_subsets(package, definition)
    assert not (package / 'private/review-original.ifc').exists()
    assert not (package / 'private/review-damaged.ifc').exists()
