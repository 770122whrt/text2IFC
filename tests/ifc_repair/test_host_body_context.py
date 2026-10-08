"""Frozen synthetic family for a hosted Opening's representation context.

IFC context labels are free text. A hosted Opening must use the unique 3D
Body context linked to its selected public wall, rather than an unrelated
global context chosen by its label or STEP order. These are offline regression
fixtures; no formal-case identities, pristine IFC or private Gold are used.
"""
from __future__ import annotations

import json

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.guid
import ifcopenshell.util.shape
import pytest

from scripts.ifc_repair.repair_comparison.inspection import native_validation
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.operations.hosted_opening import body_context
from text2ifc_ifc_repair.registry import OperationRegistryError
from tests.ifc_repair.repair_comparison.test_b_common_installation_native_seam import (
    AddingBrepDoorProvider,
    _direct_addition_binding,
)
from tests.ifc_repair.test_door_direct_body_reference import (
    _body,
    _reference_signature,
    assert_authored_installation,
    assert_complete_public_reuse,
    brep_scene,
)
from tests.ifc_repair.test_hosted_opening_normal_origin import _axis_frame_bounds


def _root_context(model, *, label="Design", identifier="Plan", dimensions=3):
    point = model.createIfcCartesianPoint((0.,) * dimensions)
    placement = (model.createIfcAxis2Placement3D(point) if dimensions == 3
                 else model.createIfcAxis2Placement2D(point))
    return model.createIfcGeometricRepresentationContext(
        identifier, label, dimensions, 1e-5, placement, None,
    )


def _subcontext(model, parent, *, identifier="Body", view="MODEL_VIEW"):
    return model.createIfcGeometricRepresentationSubContext(
        ContextIdentifier=identifier,
        ContextType=parent.ContextType,
        ParentContext=parent,
        TargetView=view,
        UserDefinedTargetView="Authored public 3D view" if view == "USERDEFINED" else None,
    )


def _representation(model, context, *, identifier="Body"):
    # Unit tests exercise context selection alone; full IFC geometry and native
    # schema/EXPRESS validity are covered by the public-API fixtures below.
    point = model.createIfcCartesianPoint((0.,) * context.CoordinateSpaceDimension)
    item = model.createIfcGeometricSet([point])
    return model.createIfcShapeRepresentation(context, identifier, "GeometricSet", [item])


def _product(model, representations):
    wall = model.createIfcWall(ifcopenshell.guid.new(), Name="Public host")
    wall.Representation = model.createIfcProductDefinitionShape(
        None, None, representations,
    )
    return wall


@pytest.mark.parametrize("label,identifier", [
    ("Design", "Plan"), ("Outline", "Plan"), ("Sketch", "Plan"),
    ("建筑三维表示", None),
])
@pytest.mark.parametrize("host_first", [False, True])
def test_product_body_context_ignores_labels_and_unrelated_global_preferences(
    label, identifier, host_first,
):
    model = ifcopenshell.file(schema="IFC2X3")
    host = _root_context(model, label=label, identifier=identifier) if host_first else None
    unrelated = _root_context(model, label="Model", identifier=None)
    preferred = _subcontext(model, unrelated)
    if host is None:
        host = _root_context(model, label=label, identifier=identifier)
    wall = _product(model, [_representation(model, host)])
    before = model.to_string()

    selected = body_context(model, product=wall)

    assert selected == host
    assert selected not in (unrelated, preferred)
    assert model.to_string() == before


@pytest.mark.parametrize("identifier,view", [
    ("Body", "MODEL_VIEW"), ("Public detailed geometry", "PLAN_VIEW"),
    ("Opaque 3D", "USERDEFINED"),
])
def test_product_body_context_keeps_its_linked_3d_subcontext(identifier, view):
    model = ifcopenshell.file(schema="IFC2X3")
    unrelated = _root_context(model, label="Model", identifier=None)
    _subcontext(model, unrelated)
    parent = _root_context(model)
    linked = _subcontext(model, parent, identifier=identifier, view=view)
    wall = _product(model, [_representation(model, linked)])

    assert linked.CoordinateSpaceDimension == 3
    assert body_context(model, product=wall) == linked


def test_product_body_context_ignores_axis_and_accepts_repeated_same_context():
    model = ifcopenshell.file(schema="IFC2X3")
    host = _root_context(model)
    axis = _root_context(model, label="Plan", dimensions=2)
    wall = _product(model, [
        _representation(model, axis, identifier="Axis"),
        _representation(model, host), _representation(model, host),
    ])

    assert body_context(model, product=wall) == host


@pytest.mark.parametrize("representation_state", ["absent", "axis_only"])
def test_explicit_product_without_body_cannot_fall_back_to_global_context(representation_state):
    model = ifcopenshell.file(schema="IFC2X3")
    preferred = _subcontext(model, _root_context(model, label="Model"))
    wall = _product(model, [_representation(model, preferred, identifier="Axis")])
    if representation_state == "absent":
        wall.Representation = None
    before = model.to_string()

    with pytest.raises(OperationRegistryError) as error:
        body_context(model, product=wall)

    assert error.value.code == "BODY_CONTEXT_NOT_FOUND"
    assert model.to_string() == before


@pytest.mark.parametrize("subcontext", [False, True])
def test_explicit_product_with_2d_body_is_rejected_even_when_global_model_exists(subcontext):
    model = ifcopenshell.file(schema="IFC2X3")
    _subcontext(model, _root_context(model, label="Model"))
    parent = _root_context(model, label="Plan", dimensions=2)
    linked = _subcontext(model, parent) if subcontext else parent
    wall = _product(model, [_representation(model, linked)])
    before = model.to_string()

    with pytest.raises(OperationRegistryError) as error:
        body_context(model, product=wall)

    assert error.value.code == "BODY_CONTEXT_NOT_FOUND"
    assert model.to_string() == before


@pytest.mark.parametrize("reverse", [False, True])
def test_explicit_product_with_distinct_body_contexts_is_ambiguous(reverse):
    model = ifcopenshell.file(schema="IFC2X3")
    first = _root_context(model, label="Design")
    second = _subcontext(model, _root_context(model, label="Model"))
    representations = [_representation(model, first), _representation(model, second)]
    wall = _product(model, representations[::-1] if reverse else representations)
    before = model.to_string()

    with pytest.raises(OperationRegistryError) as error:
        body_context(model, product=wall)

    assert error.value.code == "BODY_CONTEXT_AMBIGUOUS"
    assert model.to_string() == before


@pytest.mark.parametrize("variant", ["preferred_subcontext", "other_body_subcontext", "model_root"])
def test_legacy_no_product_context_selection_remains_available(variant):
    model = ifcopenshell.file(schema="IFC2X3")
    root = _root_context(model, label="Model", identifier=None)
    expected = root
    if variant != "model_root":
        expected = _subcontext(model, root, view=(
            "MODEL_VIEW" if variant == "preferred_subcontext" else "PLAN_VIEW"
        ))
    before = model.to_string()

    assert body_context(model) == expected
    assert model.to_string() == before


def design_context_scene(*, millimetres=False, angle=0., sign=1.):
    """Valid synthetic public Brep scene with no globally preferred context.

    All 3D roots have identifier Plan. Only the Design root is linked to the
    selected wall's Body. Outline and Sketch are unused competing roots. The
    desired hole was not retained in the public source, so it is a genuine
    add-door-with-opening operation rather than fill-existing-opening.
    """
    model, opening, reference, unit = brep_scene(
        millimetres=millimetres, angle=angle, sign=sign, target_thickness_mm=100.,
    )
    binding = _direct_addition_binding(model, opening, unit)
    # _direct_addition_binding deletes opening; never dereference its old SWIG
    # entity after that operation.
    wall = model.by_guid(binding["target_wall"])
    host = _body(wall).ContextOfItems
    host.ContextIdentifier = "Plan"
    host.ContextType = "Design"
    # Reused helper families may gain preferred Body subcontexts later. They
    # are unrelated to this fixture's mechanism and must not mask the defect.
    for context in list(model.by_type("IfcGeometricRepresentationSubContext")):
        for representation in model.by_type("IfcRepresentation"):
            if representation.ContextOfItems == context:
                representation.ContextOfItems = context.ParentContext
        model.remove(context)
    extra = [_root_context(model, label=label) for label in ("Outline", "Sketch")]
    project = model.by_type("IfcProject")[0]
    project.RepresentationContexts = [*project.RepresentationContexts, *extra]
    binding["reference"] = reference.GlobalId
    return model, wall, reference, unit, binding


class RecordingAddingBrepDoorProvider(AddingBrepDoorProvider):
    def __init__(self, fixture):
        super().__init__(fixture)
        self.calls = []

    def generate_candidate(self, **kwargs):
        self.calls.append(kwargs)
        return super().generate_candidate(**kwargs)


def _wall_volume(wall):
    shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), wall)
    return ifcopenshell.util.shape.get_volume(shape.geometry)


@pytest.mark.parametrize("millimetres,angle,sign", [
    (False, 0., 1.), (False, 90., -1.),
    (True, 37., 1.), (True, 180., -1.),
])
def test_public_api_adds_complete_door_and_through_wall_opening_using_host_body_context(
    tmp_path, millimetres, angle, sign,
):
    model, wall, reference, unit, binding = design_context_scene(
        millimetres=millimetres, angle=angle, sign=sign,
    )
    contexts = model.by_type("IfcGeometricRepresentationContext")
    assert not model.by_type("IfcGeometricRepresentationSubContext")
    assert sorted(context.ContextType for context in contexts) == ["Design", "Outline", "Sketch"]
    assert all(context.ContextIdentifier == "Plan" and context.CoordinateSpaceDimension == 3
               for context in contexts)
    host_context_id = _body(wall).ContextOfItems.id()
    reference_signature = _reference_signature(model, reference)
    original_wall_body = _body(wall).to_string()
    original_project = model.by_type("IfcProject")[0].to_string()
    before_volume = _wall_volume(wall)
    source = tmp_path / "public.ifc"
    model.write(str(source))
    before = source.read_bytes()
    source_validation = native_validation(ifcopenshell.open(str(source)))
    assert source_validation["passed"], source_validation
    provider = RecordingAddingBrepDoorProvider(binding)
    request = (
        "Open a new 900 by 2100 mm hole at public world point "
        + json.dumps(binding["target_point_world_mm"])
        + ". Add a single-swing door, preserving the retained complete frame, leaf, "
        "hardware and finish. Adapt the installation to the target wall face and "
        "wall thickness. Keep other existing elements unchanged."
    )

    result = RepairAPI(tmp_path / "native", provider=provider, scene_grounding=True).start(source, request)

    assert source.read_bytes() == before
    assert result.status == "succeeded", result.to_dict()
    assert result.successful_artifact_publishable, result.to_dict()
    run = tmp_path / "native" / result.run_directory
    output = ifcopenshell.open(str(run / result.artifacts["successful_ifc"]))
    added = [door for door in output.by_type("IfcDoor") if door.GlobalId != reference.GlobalId]
    assert len(added) == 1
    door = added[0]
    assert door.OverallWidth / unit == pytest.approx(900.)
    assert door.OverallHeight / unit == pytest.approx(2100.)
    assert len(door.FillsVoids) == 1
    opening = door.FillsVoids[0].RelatingOpeningElement
    retained_wall = output.by_guid(wall.GlobalId)
    assert len(opening.VoidsElements) == 1
    assert opening.VoidsElements[0].RelatingBuildingElement == retained_wall
    assert _body(opening).ContextOfItems == _body(retained_wall).ContextOfItems
    assert _body(opening).ContextOfItems.id() == host_context_id
    ranges = _axis_frame_bounds(opening, retained_wall, unit=unit)
    for actual, expected in zip(ranges, ([500., 1400.], [0., 100.], [0., 2100.])):
        assert actual == pytest.approx(expected, abs=1e-5)
    assert before_volume - _wall_volume(retained_wall) == pytest.approx(
        900. * 2100. * 100. / 1e9, abs=1e-7,
    )
    assert_complete_public_reuse(output, door, output.by_guid(reference.GlobalId), reference_signature)
    assert_authored_installation(door, opening, sign=sign, thickness=100.)
    assert _body(retained_wall).to_string() == original_wall_body
    assert output.by_type("IfcProject")[0].to_string() == original_project
    output_validation = native_validation(output)
    assert output_validation["passed"] and output_validation["express_rules"]
    assert output_validation["diagnostic_count"] == 0, output_validation
    manifest = json.loads((run / result.artifacts["manifest"]).read_text(encoding="utf8"))
    evidence = next(artifact["path"] for artifact in manifest["artifacts"] if artifact["role"] == "public_evidence")
    application = json.loads((run / evidence).read_text(encoding="utf8"))["evidence"]["application"]
    assert application["valid"] and application["published"]
    assert provider.calls
