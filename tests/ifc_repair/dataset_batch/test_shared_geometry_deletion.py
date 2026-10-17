"""Native-valid shared geometry must survive product deletion unchanged.

The default boundary is the production deletion helper. During this bounded
diagnosis only, TEXT2IFC_GEOMETRY_GUARD_CANDIDATE can point to a temporary
context-manager module without changing the running dataset package or library.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid
import pytest

from scripts.ifc_repair.dataset_batch.engine import _remove_product_with_relationship_cleanup
from scripts.ifc_repair.dataset_batch.validation import native_validate
from scripts.ifc_repair.dataset_batch.wall_check import _mesh


@pytest.fixture
def delete_product():
    candidate = os.environ.get("TEXT2IFC_GEOMETRY_GUARD_CANDIDATE")
    if not candidate:
        return _remove_product_with_relationship_cleanup
    spec = importlib.util.spec_from_file_location("bounded_geometry_guard_candidate", Path(candidate))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def guarded(model, product):
        with module.guard_geometry(model, product):
            _remove_product_with_relationship_cleanup(model, product)

    return guarded


def shared_geometry_scene(kind="faces", face_count=12, *, styled=False, shared_placement=False):
    model = ifcopenshell.file(schema="IFC2X3")
    person = model.createIfcPerson(FamilyName="Offline")
    organization = model.createIfcOrganization(Name="Shared geometry regression")
    application = model.createIfcApplication(organization, "1", "Offline fixture", "fixture")
    owner = model.createIfcOwnerHistory(model.createIfcPersonAndOrganization(person, organization), application,
                                       None, "ADDED", None, None, None, 1)

    def root(cls, **kwargs):
        return model.create_entity(cls, GlobalId=ifcopenshell.guid.new(), OwnerHistory=owner, **kwargs)

    def axis(x=0.0):
        return model.createIfcAxis2Placement3D(model.createIfcCartesianPoint((float(x), 0.0, 0.0)),
                                              model.createIfcDirection((0.0, 0.0, 1.0)),
                                              model.createIfcDirection((1.0, 0.0, 0.0)))

    def placement(x=0.0, parent=None, relative=None):
        return model.createIfcLocalPlacement(parent, relative if relative is not None else axis(x))

    context = model.createIfcGeometricRepresentationContext(None, "Model", 3, 1e-5,
                                                           axis(), None)
    units = model.createIfcUnitAssignment([model.createIfcSIUnit(None, "LENGTHUNIT", None, "METRE")])
    project = root("IfcProject", Name="Geometry preservation", RepresentationContexts=[context], UnitsInContext=units)
    site = root("IfcSite", Name="Site", CompositionType="ELEMENT", ObjectPlacement=placement())
    building = root("IfcBuilding", Name="Building", CompositionType="ELEMENT", ObjectPlacement=placement(parent=site.ObjectPlacement))
    storey = root("IfcBuildingStorey", Name="Level A", CompositionType="ELEMENT", Elevation=0.0,
                  ObjectPlacement=placement(parent=building.ObjectPlacement))
    for parent, child in ((project, site), (site, building), (building, storey)):
        root("IfcRelAggregates", RelatingObject=parent, RelatedObjects=[child])
    target = root("IfcColumn", Name="Delete this column", ObjectPlacement=placement(parent=storey.ObjectPlacement))
    # IFC2X3 LocalPlacement.PlacesObject is [1:1]. Share its axis graph while
    # retaining one LocalPlacement per product, so this is a valid boundary.
    peer = root("IfcColumn", Name="Retain this column", ObjectPlacement=placement(
        3.0, storey.ObjectPlacement, target.ObjectPlacement.RelativePlacement if shared_placement else None))
    root("IfcRelContainedInSpatialStructure", RelatingStructure=storey, RelatedElements=[target, peer])
    coordinates = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
                   (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    polygons = []
    for index, quad in enumerate(quads):
        polygons.extend([(quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])]
                        if index < face_count - 6 else [quad])

    def make_faces(points=None, loops=None):
        points = points or [model.createIfcCartesianPoint(tuple(float(v) for v in xyz)) for xyz in coordinates]
        loops = loops or [model.createIfcPolyLoop([points[index] for index in polygon]) for polygon in polygons]
        faces = [model.createIfcFace([model.createIfcFaceOuterBound(loop, True)]) for loop in loops]
        return points, loops, faces

    points, loops, faces = make_faces()
    shell = model.createIfcClosedShell(faces)
    brep = model.createIfcFacetedBrep(shell)
    shape = model.createIfcShapeRepresentation(context, "Body", "Brep", [brep])
    target.Representation = model.createIfcProductDefinitionShape(None, None, [shape])
    peer_brep, peer_shape = brep, shape
    if kind == "pds":
        peer.Representation = target.Representation
    elif kind == "shape":
        peer.Representation = model.createIfcProductDefinitionShape(None, None, [shape])
    else:
        if kind == "brep":
            peer_brep = brep
        else:
            if kind == "shell":
                peer_shell = shell
            elif kind == "faces":
                peer_shell = model.createIfcClosedShell(faces)
            else:
                _, _, peer_faces = make_faces(points if kind == "points" else None, loops if kind == "loops" else None)
                peer_shell = model.createIfcClosedShell(peer_faces)
            peer_brep = model.createIfcFacetedBrep(peer_shell)
        peer_shape = model.createIfcShapeRepresentation(context, "Body", "Brep", [peer_brep])
        peer.Representation = model.createIfcProductDefinitionShape(None, None, [peer_shape])
    styled_items = []
    if styled:
        colour = model.createIfcColourRgb(None, 0.6, 0.7, 0.8)
        style = model.createIfcSurfaceStyle("Shared style", "BOTH", [model.createIfcSurfaceStyleShading(colour)])
        assignment = model.createIfcPresentationStyleAssignment([style])
        for item in {brep, peer_brep}:
            styled_items.append(model.createIfcStyledItem(item, [assignment], None))
        layer = model.createIfcPresentationLayerAssignment("Columns", None, list({shape, peer_shape}), None)
    else:
        layer = None
    return model, target.GlobalId, peer.GlobalId, {
        "layer_id": layer.id() if layer else None,
        "styled_item_ids": [item.id() for item in styled_items],
    }


def graph_snapshot(model, root):
    return {entity.id(): str(entity) for entity in model.traverse(root)}


def assert_preserved(model, target_guid, peer_guid, delete_product):
    target, peer = model.by_guid(target_guid), model.by_guid(peer_guid)
    baseline = native_validate(model)
    assert baseline["passed"], baseline["findings"]
    target_id = target.id()
    target_geometry_ids = {e.id() for root in (target.Representation, target.ObjectPlacement) for e in model.traverse(root)}
    peer_guid = peer.GlobalId
    survivor_graphs = {p.GlobalId: graph_snapshot(model, p) for p in model.by_type("IfcProduct") if p != target}
    protected_ids = {i for graph in survivor_graphs.values() for i in graph}
    before_mesh = _mesh(peer)
    assert before_mesh.closed and before_mesh.oriented and before_mesh.volume > 0
    delete_product(model, target)
    # A removed IfcOpenShell entity cannot safely be rendered in pytest locals.
    del target
    after = native_validate(model)
    assert after["passed"], after["findings"]
    with pytest.raises(RuntimeError):
        model.by_id(target_id)
    for guid, before_graph in survivor_graphs.items():
        assert graph_snapshot(model, model.by_guid(guid)) == before_graph
    after_mesh = _mesh(model.by_guid(peer_guid))
    assert after_mesh.fingerprint == before_mesh.fingerprint
    assert after_mesh.closed and after_mesh.oriented
    # Source-only geometry outside every surviving product graph must actually
    # disappear. Keeping an entire deleted column as orphan geometry is unsafe.
    for identifier in target_geometry_ids - protected_ids:
        with pytest.raises(RuntimeError):
            model.by_id(identifier)


def test_shared_face_above_clear_threshold_preserves_survivor(delete_product):
    model, target, peer, _ = shared_geometry_scene("faces", 12)
    assert_preserved(model, target, peer, delete_product)


@pytest.mark.parametrize("face_count", [6, 10, 11])
def test_shared_face_clear_threshold_boundaries(delete_product, face_count):
    model, target, peer, _ = shared_geometry_scene("faces", face_count)
    assert_preserved(model, target, peer, delete_product)


@pytest.mark.parametrize("kind", ["shell", "brep", "points", "loops", "independent"])
def test_geometry_sharing_boundaries(delete_product, kind):
    model, target, peer, _ = shared_geometry_scene(kind, 12)
    assert_preserved(model, target, peer, delete_product)


@pytest.mark.parametrize("kind", ["faces", "independent"])
def test_style_layer_and_shared_placement_are_preserved(delete_product, kind):
    model, target, peer, metadata = shared_geometry_scene(kind, 12, styled=True, shared_placement=True)
    peer_shape = model.by_guid(peer).Representation.Representations[0]
    assert_preserved(model, target, peer, delete_product)
    assert model.by_id(metadata["layer_id"]).AssignedItems == (peer_shape,)
    assert model.by_type("IfcSurfaceStyle")[0].Name == "Shared style"
    assert all(item.Item is not None for item in model.by_type("IfcStyledItem"))


@pytest.mark.parametrize("kind,attribute", [
    ("shape", "IfcShapeRepresentation.OfProductRepresentation"),
    ("pds", "IfcProductDefinitionShape.ShapeOfProduct"),
])
def test_direct_ifc2x3_representation_sharing_is_rejected_by_source_admission(kind, attribute):
    # Direct PDS/Shape sharing is an invalid IFC2X3 source, unlike shared faces,
    # shells, Breps, loops or points. Freeze the rejection instead of weakening
    # native admission just to manufacture a "green" preservation example.
    model, _, _, _ = shared_geometry_scene(kind, 12)
    before = model.to_string()
    result = native_validate(model)
    assert not result["passed"]
    assert any(finding["attribute"] == attribute for finding in result["findings"])
    assert model.to_string() == before
