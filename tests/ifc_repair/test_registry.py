import pytest

from text2ifc_ifc_repair.registry import (
    OperationDefinition,
    OperationRegistry,
    OperationRegistryError,
)


def _definition(operation_type: str) -> OperationDefinition:
    return OperationDefinition(
        operation_type=operation_type,
        target_ifc_classes=("IfcWall",),
        parameter_schema={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["marker"],
            "properties": {"marker": {"type": "string"}},
        },
        context_adapter=lambda **kwargs: {"context": kwargs},
        precondition_checker=lambda **kwargs: [{"precondition": kwargs}],
        applicator=lambda **kwargs: {"applied": kwargs},
        postcondition_checker=lambda **kwargs: [{"postcondition": kwargs}],
        comparison_adapter=lambda **kwargs: {"comparison": kwargs},
        capability_constraints={"fixture": True},
    )


def test_second_operation_registers_without_dispatcher_changes() -> None:
    registry = OperationRegistry()
    registry.register(_definition("fixture_add_component"))
    operation = {
        "operation_type": "fixture_add_component",
        "parameters": {"marker": "ok"},
    }

    assert registry.operation_types == ("fixture_add_component",)
    assert registry.validate_parameters(operation) == []
    assert registry.dispatch(
        "comparison_adapter", operation, observed="value"
    ) == {"comparison": {"operation": operation, "observed": "value"}}


def test_unknown_operation_has_a_stable_machine_error() -> None:
    registry = OperationRegistry()

    with pytest.raises(OperationRegistryError) as caught:
        registry.require("not_registered")

    assert caught.value.code == "UNKNOWN_OPERATION_TYPE"
    assert str(caught.value) == "UNKNOWN_OPERATION_TYPE: not_registered"


def test_operation_target_schema_has_a_stable_machine_error() -> None:
    definition = _definition("fixture_add_component")
    definition = OperationDefinition(
        **{
            **definition.__dict__,
            "target_schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["wall_global_id"],
                "properties": {"wall_global_id": {"type": "string"}},
            },
        }
    )
    registry = OperationRegistry()
    registry.register(definition)

    issues = registry.validate_target(
        {
            "operation_type": "fixture_add_component",
            "target": {"wrong_global_id": "wall-public"},
        }
    )

    assert {issue.code for issue in issues} == {"OPERATION_TARGET_SCHEMA_ERROR"}
