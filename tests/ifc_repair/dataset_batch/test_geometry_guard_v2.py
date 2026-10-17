"""Focused comparison of frozen guard and isolated id-positive guard v2.

Set TEXT2IFC_GUARD_V2_BASELINE=1 and select ``trimmed_deletion`` for a red
reproduction before installing v2. The same four cases then run against v2.
All IFC mutation is confined to tiny fixtures and pytest temporary files.
"""
from __future__ import annotations

import ast
import hashlib
import importlib
import importlib.util
import inspect
import os
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element
import pytest
from ifcopenshell.api.root.remove_product import remove_product

from scripts.ifc_repair.dataset_batch.geometry_deletion import guard_geometry as baseline_guard
from scripts.ifc_repair.dataset_batch.validation import native_validate


@pytest.fixture
def guard():
    if os.environ.get("TEXT2IFC_GUARD_V2_BASELINE") == "1":
        return baseline_guard
    return importlib.import_module("scripts.ifc_repair.dataset_geometry_guard_v2").guard_geometry


@pytest.fixture(scope="module")
def siblings():
    path = Path(__file__).with_name("test_shared_geometry_deletion.py")
    spec = importlib.util.spec_from_file_location("guard_v2_shared_geometry_siblings", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _native(model):
    result = native_validate(model)
    assert result["passed"], result["findings"]


def _delete(guard):
    def delete(model, product):
        with guard(model, product):
            remove_product(model, product=product)
    return delete


def _trimmed_scene(scene_factory, tmp_path, kind, *, shared=True, styled=False):
    source = scene_factory(tmp_path / "fixture.ifc")
    model = ifcopenshell.open(str(source))
    target, peer = model.by_type(kind)[:2]
    solids = [product.Representation.Representations[0].Items[0] for product in (target, peer)]
    width, depth = float(solids[0].SweptArea.XDim), float(solids[0].SweptArea.YDim)

    def profile():
        segments = []
        for point, direction, length in (((0.0, 0.0), (1.0, 0.0), width), ((width, 0.0), (0.0, 1.0), depth),
                                         ((width, depth), (-1.0, 0.0), width), ((0.0, depth), (0.0, -1.0), depth)):
            line = model.createIfcLine(model.createIfcCartesianPoint(point), model.createIfcVector(model.createIfcDirection(direction), 1.0))
            curve = model.createIfcTrimmedCurve(line, [model.createIfcParameterValue(0.0)], [model.createIfcParameterValue(length)], True, "PARAMETER")
            segments.append(model.createIfcCompositeCurveSegment("CONTINUOUS", True, curve))
        return model.createIfcArbitraryClosedProfileDef("AREA", None, model.createIfcCompositeCurve(segments, False))

    shared_profile = profile()
    for index, solid in enumerate(solids):
        old = solid.SweptArea
        solid.SweptArea = shared_profile if shared or index == 0 else profile()
        ifcopenshell.util.element.remove_deep2(model, old)
    metadata = {}
    if styled:
        colour = model.createIfcColourRgb(None, 0.6, 0.7, 0.8)
        style = model.createIfcSurfaceStyle("Shared trimmed style", "BOTH", [model.createIfcSurfaceStyleShading(colour)])
        assignment = model.createIfcPresentationStyleAssignment([style])
        styled_items = [model.createIfcStyledItem(solid, [assignment], None) for solid in solids]
        shapes = [product.Representation.Representations[0] for product in (target, peer)]
        layer = model.createIfcPresentationLayerAssignment("Trimmed products", None, shapes, None)
        metadata = {"layer_id": layer.id(), "style_id": style.id(), "assignment_id": assignment.id(),
                    "target_styled_id": styled_items[0].id(), "peer_styled_id": styled_items[1].id(),
                    "peer_shape_id": shapes[1].id()}
    return model, str(target.GlobalId), str(peer.GlobalId), metadata


def _inline_values(model, product):
    return [(node.is_a(), node.wrappedValue) for node in model.traverse(product.Representation) if node.id() == 0]


@pytest.mark.parametrize("kind", ["IfcDoor", "IfcBeam"])
def test_frozen_guard_fails_on_native_valid_inline_values(scene_factory, tmp_path, kind):
    model, target, peer, _ = _trimmed_scene(scene_factory, tmp_path, kind)
    _native(model)
    product = model.by_guid(target)
    values = [node for node in model.traverse(product.Representation) if node.id() == 0]
    assert len(values) == 8 and {value.is_a() for value in values} == {"IfcParameterValue"}
    with pytest.raises(RuntimeError, match="Only entities with ids"):
        model.get_inverse(values[0])
    before = model.to_string()
    with pytest.raises(RuntimeError, match="Only entities with ids.*IfcParameterValue"):
        with baseline_guard(model, product):
            pytest.fail("The old guard must fail before its body is entered")
    assert model.to_string() == before


@pytest.mark.parametrize("kind", ["IfcDoor", "IfcBeam"])
@pytest.mark.parametrize("shared", [True, False])
def test_trimmed_deletion_keeps_peer_and_cleans_exclusive_graph(scene_factory, tmp_path, siblings, guard, kind, shared):
    model, target, peer, _ = _trimmed_scene(scene_factory, tmp_path, kind, shared=shared)
    peer_values = _inline_values(model, model.by_guid(peer))
    assert len(peer_values) == 8
    siblings.assert_preserved(model, target, peer, _delete(guard))
    assert _inline_values(model, model.by_guid(peer)) == peer_values


@pytest.mark.parametrize("shared", [True, False])
def test_trimmed_style_layer_links_and_definitions_survive(scene_factory, tmp_path, siblings, guard, shared):
    model, target, peer, meta = _trimmed_scene(scene_factory, tmp_path, "IfcBeam", shared=shared, styled=True)
    definitions = {identifier: str(model.by_id(identifier)) for identifier in (meta["style_id"], meta["assignment_id"])}
    peer_style = str(model.by_id(meta["peer_styled_id"]))
    siblings.assert_preserved(model, target, peer, _delete(guard))
    assert tuple(item.id() for item in model.by_id(meta["layer_id"]).AssignedItems) == (meta["peer_shape_id"],)
    assert str(model.by_id(meta["peer_styled_id"])) == peer_style
    assert all(str(model.by_id(identifier)) == before for identifier, before in definitions.items())
    with pytest.raises(RuntimeError):
        model.by_id(meta["target_styled_id"])


@pytest.mark.parametrize("kind", ["faces", "shell", "brep", "independent"])
def test_existing_shared_geometry_and_metadata_boundaries(siblings, guard, kind):
    model, target, peer, meta = siblings.shared_geometry_scene(kind, 12, styled=True, shared_placement=True)
    peer_shape = model.by_guid(peer).Representation.Representations[0].id()
    siblings.assert_preserved(model, target, peer, _delete(guard))
    assert tuple(item.id() for item in model.by_id(meta["layer_id"]).AssignedItems) == (peer_shape,)
    assert model.by_type("IfcSurfaceStyle")[0].Name == "Shared style"
    assert all(item.Item is not None for item in model.by_type("IfcStyledItem"))


def test_native_valid_mapped_representation_sharing(siblings, guard):
    model, target, peer, _ = siblings.shared_geometry_scene("independent", 12)
    products = [model.by_guid(guid) for guid in (target, peer)]
    mapped_shape = products[0].Representation.Representations[0]
    origin = model.createIfcAxis2Placement3D(model.createIfcCartesianPoint((0.0, 0.0, 0.0)), None, None)
    representation_map = model.createIfcRepresentationMap(origin, mapped_shape)
    for product in products:
        old_shape = product.Representation.Representations[0]
        operator = model.createIfcCartesianTransformationOperator3D(None, None, model.createIfcCartesianPoint((0.0, 0.0, 0.0)), 1.0, None)
        item = model.createIfcMappedItem(representation_map, operator)
        product.Representation.Representations = [model.createIfcShapeRepresentation(mapped_shape.ContextOfItems, "Body", "MappedRepresentation", [item])]
        if old_shape != mapped_shape:
            ifcopenshell.util.element.remove_deep2(model, old_shape)
    siblings.assert_preserved(model, target, peer, _delete(guard))


@pytest.mark.parametrize("kind,attribute", [("shape", "IfcShapeRepresentation.OfProductRepresentation"), ("pds", "IfcProductDefinitionShape.ShapeOfProduct")])
def test_invalid_ifc2x3_direct_representation_sharing_stays_rejected(siblings, kind, attribute):
    model, _, _, _ = siblings.shared_geometry_scene(kind, 12)
    before = model.to_string()
    result = native_validate(model)
    assert not result["passed"]
    assert any(finding["attribute"] == attribute for finding in result["findings"])
    assert model.to_string() == before


def test_guard_body_exception_restores_detached_fields(scene_factory, tmp_path, guard):
    model, target, _, _ = _trimmed_scene(scene_factory, tmp_path, "IfcBeam")
    _native(model)
    before = model.to_string()
    with pytest.raises(RuntimeError, match="injected caller failure"):
        with guard(model, model.by_guid(target)):
            assert model.by_guid(target).Representation is None
            assert model.by_guid(target).ObjectPlacement is None
            raise RuntimeError("injected caller failure")
    assert model.to_string() == before
    _native(model)


def test_target_not_deleted_restores_fields_and_rejects(scene_factory, tmp_path, guard):
    model, target, _, _ = _trimmed_scene(scene_factory, tmp_path, "IfcBeam")
    before = model.to_string()
    with pytest.raises(ValueError, match="GEOMETRY_GUARD_TARGET_NOT_DELETED"):
        with guard(model, model.by_guid(target)):
            pass
    assert model.to_string() == before


def test_incomplete_exclusive_cleanup_cannot_silently_pass(siblings, guard, monkeypatch):
    model, target, peer, _ = siblings.shared_geometry_scene("independent", 12)
    _native(model)
    peer_before = siblings.graph_snapshot(model, model.by_guid(peer))
    monkeypatch.setattr(ifcopenshell.util.element, "remove_deep2", lambda *args, **kwargs: None)
    with pytest.raises(ValueError, match="EXCLUSIVE_GEOMETRY_RETAINED"):
        _delete(guard)(model, model.by_guid(target))
    assert siblings.graph_snapshot(model, model.by_guid(peer)) == peer_before


@pytest.mark.parametrize("condition", ["not_product", "batched"])
def test_invalid_guard_entry_does_not_detach_or_mutate(siblings, guard, condition):
    model, target, _, _ = siblings.shared_geometry_scene("independent", 12)
    product = model.by_guid(target)
    if condition == "not_product":
        selected = product.Representation.Representations[0]
        code = "GEOMETRY_GUARD_REQUIRES_IFCPRODUCT"
    else:
        selected = product
        ifcopenshell.util.element.batch_remove_deep2(model)
        code = "GEOMETRY_GUARD_REQUIRES_UNBATCHED_MODEL"
    before = model.to_string()
    with pytest.raises(ValueError, match=code):
        with guard(model, selected):
            pytest.fail("Invalid entry must fail before guard body")
    assert model.to_string() == before


def test_only_two_id_positive_filters_change_frozen_guard_and_binding():
    candidate = importlib.import_module("scripts.ifc_repair.dataset_geometry_guard_v2")
    baseline_path = Path(inspect.getfile(inspect.unwrap(baseline_guard)))
    assert hashlib.sha256(baseline_path.read_bytes()).hexdigest() == candidate.BASELINE_GUARD_SHA256
    assert candidate.GUARD_VERSION == "text2ifc/dataset-geometry-guard/2.0"
    candidate_tree = ast.parse(inspect.getsource(candidate.guard_geometry))
    baseline_tree = ast.parse(inspect.getsource(baseline_guard))
    filters = 0
    for node in ast.walk(candidate_tree):
        if isinstance(node, ast.comprehension) and node.ifs:
            expected = ast.parse(f"{node.target.id}.id() > 0", mode="eval").body
            matches = [condition for condition in node.ifs if ast.dump(condition) == ast.dump(expected)]
            if matches:
                assert len(matches) == 1
                node.ifs = [condition for condition in node.ifs if condition not in matches]
                filters += 1
    assert filters == 2
    assert ast.dump(candidate_tree, include_attributes=False) == ast.dump(baseline_tree, include_attributes=False)
