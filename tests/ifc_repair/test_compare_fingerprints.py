from __future__ import annotations

import ifcopenshell
import pytest

from text2ifc_ifc_repair import compare as compare_module


PSET_GUID = "0AAAAAAAAAAAAAAAAAAAAA"
PROXY_GUIDS = ("1AAAAAAAAAAAAAAAAAAAAA", "2AAAAAAAAAAAAAAAAAAAAA")


def _property_model(
    *,
    pset_guid: str = PSET_GUID,
    property_order: tuple[str, ...] = ("A", "B"),
    list_values: tuple[str, ...] = ("first", "second"),
) -> ifcopenshell.file:
    model = ifcopenshell.file(schema="IFC2X3")
    properties = {
        "A": model.create_entity(
            "IfcPropertySingleValue",
            Name="A",
            NominalValue=model.create_entity("IfcLabel", "alpha"),
        ),
        "B": model.create_entity(
            "IfcPropertyListValue",
            Name="B",
            ListValues=[
                model.create_entity("IfcLabel", value) for value in list_values
            ],
        ),
    }
    model.create_entity(
        "IfcPropertySet",
        GlobalId=pset_guid,
        Name="Pset_Test",
        HasProperties=[properties[name] for name in property_order],
    )
    return model


def _shared_mapping_model(*, endpoint_x: float) -> ifcopenshell.file:
    model = ifcopenshell.file(schema="IFC2X3")
    origin = model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
    axis = model.create_entity("IfcAxis2Placement3D", Location=origin)
    context = model.create_entity(
        "IfcGeometricRepresentationContext",
        ContextIdentifier="Body",
        ContextType="Model",
        CoordinateSpaceDimension=3,
        Precision=1e-5,
        WorldCoordinateSystem=axis,
    )
    endpoint = model.create_entity(
        "IfcCartesianPoint",
        Coordinates=(endpoint_x, 0.0, 0.0),
    )
    polyline = model.create_entity(
        "IfcPolyline",
        Points=[
            model.create_entity(
                "IfcCartesianPoint",
                Coordinates=(0.0, 0.0, 0.0),
            ),
            endpoint,
        ],
    )
    mapped_representation = model.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="Body",
        RepresentationType="Curve3D",
        Items=[polyline],
    )
    representation_map = model.create_entity(
        "IfcRepresentationMap",
        MappingOrigin=axis,
        MappedRepresentation=mapped_representation,
    )
    for global_id in PROXY_GUIDS:
        transform = model.create_entity(
            "IfcCartesianTransformationOperator3D",
            LocalOrigin=origin,
            Scale=1.0,
        )
        mapped_item = model.create_entity(
            "IfcMappedItem",
            MappingSource=representation_map,
            MappingTarget=transform,
        )
        product_representation = model.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=context,
            RepresentationIdentifier="Body",
            RepresentationType="MappedRepresentation",
            Items=[mapped_item],
        )
        product_shape = model.create_entity(
            "IfcProductDefinitionShape",
            Representations=[product_representation],
        )
        model.create_entity(
            "IfcBuildingElementProxy",
            GlobalId=global_id,
            Name=f"Proxy {global_id[0]}",
            Representation=product_shape,
            CompositionType="ELEMENT",
        )
    return model


def test_duplicate_root_guid_is_rejected_instead_of_overwriting_a_root() -> None:
    before = _property_model()
    after = _property_model()
    after.create_entity(
        "IfcPropertySet",
        GlobalId=PSET_GUID,
        Name="Duplicate",
        HasProperties=[],
    )
    expected_error = getattr(
        compare_module, "ComparisonIntegrityError", RuntimeError
    )

    with pytest.raises(expected_error, match="DUPLICATE_ROOT_GLOBAL_ID"):
        compare_module.normalized_model_diff(before, after)


def test_empty_root_guid_is_rejected_instead_of_becoming_a_comparison_key() -> None:
    before = _property_model()
    after = _property_model(pset_guid="")
    expected_error = getattr(
        compare_module, "ComparisonIntegrityError", RuntimeError
    )

    with pytest.raises(expected_error, match="EMPTY_ROOT_GLOBAL_ID"):
        compare_module.normalized_model_diff(before, after)


def test_unordered_pset_members_do_not_create_false_drift() -> None:
    before = _property_model(property_order=("A", "B"))
    after = _property_model(property_order=("B", "A"))

    changes = compare_module.normalized_model_diff(before, after)

    assert changes == {"created": [], "modified": [], "removed": []}


def test_shifted_step_ids_do_not_become_cross_file_identity() -> None:
    before = _property_model()
    after = ifcopenshell.file(schema="IFC2X3")
    after.create_entity("IfcCartesianPoint", Coordinates=(9.0, 9.0))
    properties = [
        after.create_entity(
            "IfcPropertySingleValue",
            Name="A",
            NominalValue=after.create_entity("IfcLabel", "alpha"),
        ),
        after.create_entity(
            "IfcPropertyListValue",
            Name="B",
            ListValues=[
                after.create_entity("IfcLabel", "first"),
                after.create_entity("IfcLabel", "second"),
            ],
        ),
    ]
    after.create_entity(
        "IfcPropertySet",
        GlobalId=PSET_GUID,
        Name="Pset_Test",
        HasProperties=properties,
    )

    changes = compare_module.normalized_model_diff(before, after)

    assert changes == {"created": [], "modified": [], "removed": []}


def test_ordered_property_list_reordering_is_detected() -> None:
    before = _property_model(list_values=("first", "second"))
    after = _property_model(list_values=("second", "first"))

    changes = compare_module.normalized_model_diff(before, after)

    assert [item["global_id"] for item in changes["modified"]] == [PSET_GUID]


def test_shared_representation_change_marks_every_referencing_root() -> None:
    before = _shared_mapping_model(endpoint_x=1.0)
    after = _shared_mapping_model(endpoint_x=2.0)

    profiled = compare_module.profile_normalized_model_diff(before, after)

    assert [item["global_id"] for item in profiled["changes"]["modified"]] == list(
        PROXY_GUIDS
    )
    assert profiled["metrics"]["before"]["shared_entity_cache_hits"] > 0
    assert profiled["metrics"]["after"]["shared_entity_cache_hits"] > 0


def test_expired_comparison_budget_never_returns_partial_success() -> None:
    before = _property_model()
    after = _property_model()

    with pytest.raises(
        compare_module.ComparisonTimeoutError,
        match="COMPARISON_TIMEOUT",
    ):
        compare_module.profile_normalized_model_diff(
            before,
            after,
            timeout_seconds=0.0,
        )


def test_aligned_step_records_are_used_only_as_a_fast_change_certificate() -> None:
    before = _property_model(list_values=("first", "second"))
    after = _property_model(list_values=("first", "changed"))

    profiled = compare_module.profile_normalized_model_diff(before, after)

    assert profiled["metrics"]["strategy"] == "aligned_step_certificate"
    assert [item["global_id"] for item in profiled["changes"]["modified"]] == [
        PSET_GUID
    ]


def test_file_comparison_reports_identity_failure_without_claiming_success(
    tmp_path,
) -> None:
    before_path = tmp_path / "before.ifc"
    after_path = tmp_path / "after.ifc"
    _property_model().write(str(before_path))
    after = _property_model()
    after.create_entity(
        "IfcPropertySet",
        GlobalId=PSET_GUID,
        Name="Duplicate",
        HasProperties=[],
    )
    after.write(str(after_path))

    report = compare_module.compare_ifc_models(
        before_path,
        after_path,
        allowed_changed_ids=[],
    )

    assert report["complete_preservation_success"] is False
    assert report["comparison_error_code"] == "DUPLICATE_ROOT_GLOBAL_ID"
