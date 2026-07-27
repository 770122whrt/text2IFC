"""Built-in IFC repair operation registrations."""

from __future__ import annotations

from text2ifc_ifc_repair.registry import OperationRegistry

from .window import window_operation_definition
from .occurrence_property import occurrence_property_operation_definition
from .opening import opening_operation_definition


def create_default_registry() -> OperationRegistry:
    registry = OperationRegistry()
    registry.register(window_operation_definition())
    registry.register(occurrence_property_operation_definition())
    registry.register(opening_operation_definition())
    return registry
