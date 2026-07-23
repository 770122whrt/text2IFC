from __future__ import annotations

import inspect

import pytest

from text2ifc_ifc_repair.property_intent import (
    AuthorizedPropertyFact,
    normalize_property_scope,
)
from text2ifc_ifc_repair.repair_intent import PublicProvenance
from text2ifc_ifc_repair.registry import OperationDefinition, OperationRegistry
from text2ifc_ifc_repair.resolution_flow import generated_type_authority


def _definition(operation_type: str = "fixture_add_component") -> OperationDefinition:
    return OperationDefinition(
        operation_type=operation_type,
        target_ifc_classes=("IfcWall",),
        parameter_schema={"type": "object"},
        context_adapter=lambda **kwargs: kwargs,
        precondition_checker=lambda **kwargs: (),
        applicator=lambda **kwargs: kwargs,
        postcondition_checker=lambda **kwargs: (),
        comparison_adapter=lambda **kwargs: kwargs,
        capability_constraints={},
        editable_occurrence_ifc_class="IfcFixtureElement",
        inherited_type_evidence_role="IfcFixtureElementType",
        generated_type_template=lambda **kwargs: {
            "template_version": "0.1",
            "ifc_class": "IfcFixtureElementType",
            "name": f"Text2IFC {kwargs['operation_id']}",
        },
    )


def test_missing_scope_is_occurrence_direct_and_type_owned_is_deferred() -> None:
    assert normalize_property_scope(None) == "occurrence_direct"
    assert normalize_property_scope("occurrence_direct") == "occurrence_direct"
    with pytest.raises(ValueError, match="TYPE_PROPERTY_MUTATION_DEFERRED"):
        normalize_property_scope("type_owned")


def test_authorized_fact_rejects_shared_type_ownership() -> None:
    with pytest.raises(ValueError, match="PROPERTY_OWNERSHIP_NOT_AUTHORIZED"):
        AuthorizedPropertyFact(
            operation_id="op-1",
            target_global_id="0TARGETAAAAAAAAAAAAAAAA",
            request_hash="sha256:" + "a" * 64,
            model_fingerprint="sha256:" + "b" * 64,
            set_name="Pset_WindowCommon",
            property_name="FireRating",
            value="EI30",
            value_type="IfcLabel",
            unit=None,
            ownership="type_owned",
            source=PublicProvenance("user_request", "request:/text", "EI30"),
            confirmation_ref=None,
            confirmation_hash=None,
            classification="standard",
        )


def test_no_type_intent_uses_operation_bound_system_template_not_project_type() -> None:
    definition = _definition()
    first = generated_type_authority(
        definition,
        operation_id="op-1",
        request_hash="sha256:" + "a" * 64,
        model_fingerprint="sha256:" + "b" * 64,
    )
    second = generated_type_authority(
        definition,
        operation_id="op-1",
        request_hash="sha256:" + "a" * 64,
        model_fingerprint="sha256:" + "b" * 64,
    )
    changed = generated_type_authority(
        definition,
        operation_id="op-2",
        request_hash="sha256:" + "a" * 64,
        model_fingerprint="sha256:" + "b" * 64,
    )

    assert first == second
    assert first != changed
    assert first["kind"] == "system_generated_type"
    assert first["template_version"] == "0.1"
    assert first["ifc_class"] == "IfcFixtureElementType"
    assert first["global_id"]
    assert "project_type" not in str(first).casefold()


def test_fixture_operation_registers_generic_property_adapter_hooks() -> None:
    registry = OperationRegistry()
    registry.register(_definition())
    definition = registry.require("fixture_add_component")

    assert definition.editable_occurrence_ifc_class == "IfcFixtureElement"
    assert definition.inherited_type_evidence_role == "IfcFixtureElementType"
    assert callable(definition.generated_type_template)


def test_common_property_flow_has_no_window_class_branch_and_window_owns_adapter() -> None:
    import text2ifc_ifc_repair.property_intent as property_module
    import text2ifc_ifc_repair.resolution_flow as resolution_module
    from text2ifc_ifc_repair.operations.window import window_operation_definition

    assert "IfcWindow" not in inspect.getsource(property_module)
    assert "IfcWindow" not in inspect.getsource(resolution_module)

    definition = window_operation_definition()
    assert definition.editable_occurrence_ifc_class == "IfcWindow"
    assert definition.inherited_type_evidence_role == "IfcWindowStyle"
    authority = generated_type_authority(
        definition,
        operation_id="window-1",
        request_hash="sha256:" + "a" * 64,
        model_fingerprint="sha256:" + "b" * 64,
    )
    assert authority["ifc_class"] == "IfcWindowStyle"
    assert authority["template_version"] == "0.1"
