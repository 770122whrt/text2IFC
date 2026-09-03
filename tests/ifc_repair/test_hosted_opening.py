from pathlib import Path

import ifcopenshell

from text2ifc_ifc_repair.operations.hosted_opening import (
    body_context,
    millimetres_to_project_units,
    project_units_to_millimetres,
)


DENTAL_CLINIC = Path(
    "dataset/external/ifc-bench/projects/dental_clinic/arc.ifc"
)


def test_metric_ifc_uses_model_context_when_body_subcontext_is_absent() -> None:
    model = ifcopenshell.open(DENTAL_CLINIC)

    context = body_context(model)

    assert context.is_a("IfcGeometricRepresentationContext")
    assert context.ContextType == "Model"
    assert context.CoordinateSpaceDimension == 3


def test_public_millimetres_are_converted_at_the_ifc_boundary() -> None:
    model = ifcopenshell.open(DENTAL_CLINIC)

    assert millimetres_to_project_units(model, 915.0) == 0.915
    assert project_units_to_millimetres(model, 0.915) == 915.0
