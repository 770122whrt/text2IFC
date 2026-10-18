"""Expand identity-mapped window Breps without moving or replacing objects."""
from pathlib import Path

import ifcopenshell
import pytest

from scripts.ifc_repair.repair_comparison.inspection import native_validation
from tests.ifc_repair.repair_comparison.test_preparation import sample


@pytest.fixture
def mapped_windows(sample):
    _, source, _ = sample
    model = ifcopenshell.open(str(source))
    wall = model.by_type('IfcWall')[0]
    context = wall.Representation.Representations[0].ContextOfItems
    origin = wall.ObjectPlacement.RelativePlacement
    coordinates = [(0., 0., 0.), (.9, 0., 0.), (.9, .075, 0.), (0., .075, 0.),
                   (0., 0., .5), (.9, 0., .5), (.9, .075, .5), (0., .075, .5)]
    points = [model.create_entity('IfcCartesianPoint', Coordinates=p) for p in coordinates]
    indices = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
               (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    faces = []
    for face in indices:
        loop = model.create_entity('IfcPolyLoop', Polygon=[points[i] for i in face])
        bound = model.create_entity('IfcFaceOuterBound', Bound=loop, Orientation=True)
        faces.append(model.create_entity('IfcFace', Bounds=[bound]))
    solid = model.create_entity('IfcFacetedBrep',
        Outer=model.create_entity('IfcClosedShell', CfsFaces=faces))
    representation = model.create_entity('IfcShapeRepresentation', ContextOfItems=context,
        RepresentationIdentifier='Body', RepresentationType='Brep', Items=[solid])
    mapping = model.create_entity('IfcRepresentationMap', MappingOrigin=origin,
        MappedRepresentation=representation)
    for x in (1., 3.):
        target = model.create_entity('IfcCartesianTransformationOperator3D',
            LocalOrigin=model.create_entity('IfcCartesianPoint', Coordinates=(0., 0., 0.)), Scale=1.)
        item = model.create_entity('IfcMappedItem', MappingSource=mapping, MappingTarget=target)
        body = model.create_entity('IfcShapeRepresentation', ContextOfItems=context,
            RepresentationIdentifier='Body', RepresentationType='MappedRepresentation', Items=[item])
        placement = model.create_entity('IfcAxis2Placement3D',
            Location=model.create_entity('IfcCartesianPoint', Coordinates=(x, 0., 0.)))
        model.create_entity('IfcWindow', GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=wall.OwnerHistory, Name='same window name', OverallWidth=.9, OverallHeight=.5,
            ObjectPlacement=model.create_entity('IfcLocalPlacement', RelativePlacement=placement),
            Representation=model.create_entity('IfcProductDefinitionShape', Representations=[body]))
    model.write(str(source))
    assert native_validation(str(source))['passed']
    return source


def test_expansion_preserves_source_roots_relations_and_all_geometry(mapped_windows, tmp_path):
    from scripts.ifc_repair.repair_comparison.viewer_compatibility import expand_window_breps
    original = mapped_windows.read_bytes()
    output = tmp_path / 'candidate.ifc'
    report = expand_window_breps(mapped_windows, output)
    assert mapped_windows.read_bytes() == original
    assert report['converted_window_count'] == 2
    assert all(report['checks'].values())
    assert report['validation']['diagnostic_count'] == 0
    model = ifcopenshell.open(str(output))
    windows = model.by_type('IfcWindow')
    assert len(windows) == 2
    bodies = [w.Representation.Representations[0] for w in windows]
    assert all(b.RepresentationType == 'Brep' for b in bodies)
    assert bodies[0].Items[0] != bodies[1].Items[0]
    assert bodies[0].Items[0].Outer != bodies[1].Items[0].Outer


def test_nonidentity_mapping_is_rejected_without_publishing(mapped_windows, tmp_path):
    from scripts.ifc_repair.repair_comparison.viewer_compatibility import expand_window_breps
    model = ifcopenshell.open(str(mapped_windows))
    model.by_type('IfcMappedItem')[0].MappingTarget.Scale = 2.
    model.write(str(mapped_windows))
    output = tmp_path / 'candidate.ifc'
    with pytest.raises(ValueError, match='NONIDENTITY_WINDOW_MAPPING'):
        expand_window_breps(mapped_windows, output)
    assert not output.exists()


def test_inplace_output_is_rejected(mapped_windows):
    from scripts.ifc_repair.repair_comparison.viewer_compatibility import expand_window_breps
    original = mapped_windows.read_bytes()
    with pytest.raises(ValueError, match='SOURCE_OUTPUT_MUST_DIFFER'):
        expand_window_breps(mapped_windows, mapped_windows)
    assert mapped_windows.read_bytes() == original


def test_formal_004_expansion_retains_all_twelve_windows_and_valid_geometry(tmp_path):
    from scripts.ifc_repair.repair_comparison.viewer_compatibility import expand_window_breps
    root = Path(__file__).resolve().parents[3]
    source = root / ('dataset/processed/ifc-repair/repair-comparison/formal/'
                     'formal-004/private/reference.ifc')
    report = expand_window_breps(source, tmp_path / 'formal-004.ifc')
    assert report['converted_window_count'] == 6
    assert report['window_count'] == 12
    assert all(report['checks'].values())
    assert report['validation']['passed']


@pytest.mark.parametrize('report_role', ['source', 'output'])
def test_cli_report_cannot_overwrite_source_or_candidate(mapped_windows, tmp_path, monkeypatch, report_role):
    from scripts.ifc_repair.repair_comparison import viewer_compatibility as api
    output = tmp_path / 'candidate.ifc'
    report = mapped_windows if report_role == 'source' else output
    monkeypatch.setattr('sys.argv', ['probe', '--source', str(mapped_windows),
        '--output', str(output), '--report', str(report)])

    def unexpected_write(*args):
        raise AssertionError('Report path must be checked before writing the candidate')

    monkeypatch.setattr(api, 'expand_window_breps', unexpected_write)
    with pytest.raises(ValueError, match='REPORT_MUST_DIFFER_FROM_IFC_PATHS'):
        api.main()
    assert not output.exists()
