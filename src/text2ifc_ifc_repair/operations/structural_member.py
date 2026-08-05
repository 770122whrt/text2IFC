"""Shared deterministic primitives for straight rectangular structural members."""

from __future__ import annotations

import math
from typing import Any, Mapping

from text2ifc_ifc_repair.run_models import hash_json


STRUCTURAL_TYPE_TEMPLATE_VERSION = "0.1"
_STRUCTURAL_TYPE_CONTRACTS = {
    "beam": {
        "ifc_class": "IfcBeamType",
        "template_id": "text2ifc-rectangular-beam-type",
        "section_keys": ("shape", "width_mm", "height_mm"),
    },
    "column": {
        "ifc_class": "IfcColumnType",
        "template_id": "text2ifc-rectangular-column-type",
        "section_keys": ("shape", "width_mm", "depth_mm"),
    },
}


def generated_beam_type_template(
    *,
    operation_id: str,
    request_hash: str,
    model_fingerprint: str,
    resolved_operation: Any,
) -> dict[str, Any]:
    del request_hash, model_fingerprint
    return _generated_structural_type_template(
        family="beam",
        operation_id=operation_id,
        resolved_operation=resolved_operation,
    )


def generated_column_type_template(
    *,
    operation_id: str,
    request_hash: str,
    model_fingerprint: str,
    resolved_operation: Any,
) -> dict[str, Any]:
    del request_hash, model_fingerprint
    return _generated_structural_type_template(
        family="column",
        operation_id=operation_id,
        resolved_operation=resolved_operation,
    )


def create_generated_beam_type(
    *,
    model: Any,
    global_id: str,
    owner_history: Any,
    operation_id: str,
    derivation: Mapping[str, Any],
    context: Mapping[str, Any],
) -> Any:
    return _create_generated_structural_type(
        family="beam",
        model=model,
        global_id=global_id,
        owner_history=owner_history,
        operation_id=operation_id,
        derivation=derivation,
        context=context,
    )


def create_generated_column_type(
    *,
    model: Any,
    global_id: str,
    owner_history: Any,
    operation_id: str,
    derivation: Mapping[str, Any],
    context: Mapping[str, Any],
) -> Any:
    return _create_generated_structural_type(
        family="column",
        model=model,
        global_id=global_id,
        owner_history=owner_history,
        operation_id=operation_id,
        derivation=derivation,
        context=context,
    )


def _generated_structural_type_template(
    *,
    family: str,
    operation_id: str,
    resolved_operation: Any,
) -> dict[str, Any]:
    contract = _contract(family)
    section = _canonical_section(
        family,
        getattr(resolved_operation, "parameters", {}).get("section"),
    )
    return {
        "template_id": contract["template_id"],
        "template_version": STRUCTURAL_TYPE_TEMPLATE_VERSION,
        "ifc_class": contract["ifc_class"],
        **_structural_template_payload(
            family=family,
            operation_id=operation_id,
            section=section,
        ),
    }


def _create_generated_structural_type(
    *,
    family: str,
    model: Any,
    global_id: str,
    owner_history: Any,
    operation_id: str,
    derivation: Mapping[str, Any],
    context: Mapping[str, Any],
) -> Any:
    contract = _contract(family)
    if str(derivation.get("template_id")) != contract["template_id"]:
        raise ValueError("GENERATED_STRUCTURAL_TEMPLATE_ID_MISMATCH")
    if (
        str(derivation.get("template_version"))
        != STRUCTURAL_TYPE_TEMPLATE_VERSION
    ):
        raise ValueError("GENERATED_STRUCTURAL_TEMPLATE_VERSION_MISMATCH")
    if dict(derivation.get("formal_attributes", {})):
        raise ValueError("GENERATED_STRUCTURAL_TEMPLATE_MISMATCH")

    section = _canonical_section(family, context.get("section"))
    template = derivation.get("template")
    if not isinstance(template, Mapping):
        raise ValueError("GENERATED_STRUCTURAL_TEMPLATE_MISMATCH")
    if template.get("section") != section:
        raise ValueError("GENERATED_STRUCTURAL_SECTION_MISMATCH")
    expected = _structural_template_payload(
        family=family,
        operation_id=operation_id,
        section=section,
    )
    if dict(template) != expected:
        raise ValueError("GENERATED_STRUCTURAL_TEMPLATE_MISMATCH")

    name = str(expected["name"])
    return model.create_entity(
        contract["ifc_class"],
        GlobalId=global_id,
        OwnerHistory=owner_history,
        Name=name,
        Description=(
            f"{contract['template_id']}/{STRUCTURAL_TYPE_TEMPLATE_VERSION}"
        ),
        ElementType=name,
        PredefinedType="NOTDEFINED",
    )


def _structural_template_payload(
    *,
    family: str,
    operation_id: str,
    section: Mapping[str, Any],
) -> dict[str, Any]:
    contract = _contract(family)
    canonical_section = dict(section)
    return {
        "name": f"Text2IFC generated {family} type {operation_id}",
        "predefined_type": "NOTDEFINED",
        "section": canonical_section,
        "section_digest": hash_json(
            {
                "ifc_class": contract["ifc_class"],
                "section": canonical_section,
            }
        ),
    }


def _canonical_section(family: str, value: Any) -> dict[str, Any]:
    contract = _contract(family)
    if not isinstance(value, Mapping):
        raise ValueError("GENERATED_STRUCTURAL_SECTION_REQUIRED")
    keys = tuple(str(key) for key in value)
    expected_keys = tuple(contract["section_keys"])
    if set(keys) != set(expected_keys) or value.get("shape") != "rectangle":
        raise ValueError("GENERATED_STRUCTURAL_SECTION_INVALID")
    result: dict[str, Any] = {"shape": "rectangle"}
    for key in expected_keys[1:]:
        raw = value.get(key)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise ValueError("GENERATED_STRUCTURAL_SECTION_INVALID")
        number = float(raw)
        if not math.isfinite(number) or number <= 0.0:
            raise ValueError("GENERATED_STRUCTURAL_SECTION_INVALID")
        result[key] = number
    return result


def _contract(family: str) -> Mapping[str, Any]:
    try:
        return _STRUCTURAL_TYPE_CONTRACTS[family]
    except KeyError as error:
        raise ValueError("GENERATED_STRUCTURAL_FAMILY_UNSUPPORTED") from error


__all__ = [
    "STRUCTURAL_TYPE_TEMPLATE_VERSION",
    "create_generated_beam_type",
    "create_generated_column_type",
    "generated_beam_type_template",
    "generated_column_type_template",
]
