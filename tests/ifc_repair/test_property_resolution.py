from __future__ import annotations

import math
from types import MappingProxyType

import pytest

from text2ifc_ifc_repair.index_models import PropertyFact
from text2ifc_ifc_repair.property_intent import (
    ExactPropertyIntent,
    PropertyResolutionStatus,
    resolve_exact_property_intent,
)
from text2ifc_ifc_repair.repair_intent import PublicProvenance
from text2ifc_knowledge.registry import IfcKnowledgeRegistry, load_ifc2x3_registry


def _intent(
    *,
    set_name: str | None = "Pset_WindowCommon",
    property_name: str | None = "FireRating",
    value: object = "EI30",
    requested_value_type: str | None = None,
    requested_unit: str | None = None,
) -> ExactPropertyIntent:
    return ExactPropertyIntent(
        set_name=set_name,
        property_name=property_name,
        value=value,
        requested_value_type=requested_value_type,
        requested_unit=requested_unit,
        scope=None,
        source=PublicProvenance(
            source_kind="user_request",
            reference="request:/text",
            excerpt="set a window property",
        ),
    )


def _registry_with_property(
    *,
    template_type: str,
    applicable_classes: tuple[str, ...] = ("IfcWindow",),
) -> IfcKnowledgeRegistry:
    base = load_ifc2x3_registry()
    pset = MappingProxyType(
        {
            "name": "Pset_Test",
            "applicable_classes": applicable_classes,
            "properties": MappingProxyType(
                {
                    "Value": MappingProxyType(
                        {
                            "data_type": "IfcLabel",
                            "template_type": template_type,
                        }
                    )
                }
            ),
        }
    )
    return IfcKnowledgeRegistry(
        base.declarations,
        MappingProxyType({"Pset_Test": pset}),
    )


def test_exact_window_fire_rating_resolves_from_checked_in_registry_offline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_network(*args, **kwargs):
        raise AssertionError("property resolution must not access the network")

    monkeypatch.setattr("urllib.request.urlopen", no_network)
    result = resolve_exact_property_intent(
        _intent(),
        target_ifc_class="IfcWindow",
        existing_facts=(),
        registry=load_ifc2x3_registry(),
    )

    assert result.status is PropertyResolutionStatus.STANDARD_RESOLVED
    assert result.classification == "standard"
    assert result.value_type == "IfcLabel"
    assert result.applicable_classes == ("IfcWindow",)
    assert result.template_type == "TypePropertySingleValue"
    assert result.requires_confirmation is False


def test_case_mismatch_is_not_corrected_and_becomes_custom_candidate() -> None:
    result = resolve_exact_property_intent(
        _intent(set_name="pset_windowcommon", property_name="firerating"),
        target_ifc_class="IfcWindow",
        existing_facts=(),
        registry=load_ifc2x3_registry(),
    )

    assert result.status is PropertyResolutionStatus.CUSTOM_CONFIRMATION_REQUIRED
    assert result.classification == "custom"
    assert result.set_name == "pset_windowcommon"
    assert result.property_name == "firerating"
    assert result.value_type == "IfcLabel"
    assert result.reason_code == "UNKNOWN_EXACT_PROPERTY"
    assert result.requires_confirmation is True


@pytest.mark.parametrize(
    ("registry", "target_class", "reason"),
    [
        (
            _registry_with_property(template_type="TypePropertySingleValue"),
            "IfcDoor",
            "STANDARD_PROPERTY_INAPPLICABLE",
        ),
        (
            _registry_with_property(template_type="TypePropertyEnumeratedValue"),
            "IfcWindow",
            "STANDARD_PROPERTY_TEMPLATE_UNSUPPORTED",
        ),
    ],
)
def test_inapplicable_and_non_single_standard_properties_fail_closed(
    registry: IfcKnowledgeRegistry,
    target_class: str,
    reason: str,
) -> None:
    result = resolve_exact_property_intent(
        _intent(set_name="Pset_Test", property_name="Value"),
        target_ifc_class=target_class,
        existing_facts=(),
        registry=registry,
    )
    assert result.status is PropertyResolutionStatus.CLARIFICATION_REQUIRED
    assert result.reason_code == reason
    assert result.requires_confirmation is True


def test_registry_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    from text2ifc_knowledge.registry import RegistryDriftError

    def drift():
        raise RegistryDriftError("hash mismatch")

    monkeypatch.setattr(
        "text2ifc_ifc_repair.property_intent.check_registry_files",
        drift,
    )
    result = resolve_exact_property_intent(
        _intent(),
        target_ifc_class="IfcWindow",
        existing_facts=(),
        registry=load_ifc2x3_registry(),
    )
    assert result.status is PropertyResolutionStatus.CLARIFICATION_REQUIRED
    assert result.reason_code == "REGISTRY_DRIFT"


@pytest.mark.parametrize(
    ("value", "expected_type"),
    [
        ("W-007", "IfcLabel"),
        (True, "IfcBoolean"),
        (7, "IfcInteger"),
    ],
)
def test_custom_safe_primitives_produce_unconfirmed_preview(
    value: object,
    expected_type: str,
) -> None:
    result = resolve_exact_property_intent(
        _intent(
            set_name="Custom_Asset",
            property_name="AssetValue",
            value=value,
        ),
        target_ifc_class="IfcWindow",
        existing_facts=(),
        registry=load_ifc2x3_registry(),
    )
    assert result.status is PropertyResolutionStatus.CUSTOM_CONFIRMATION_REQUIRED
    assert result.value_type == expected_type
    assert result.requires_confirmation is True


def test_custom_decimal_requires_explicit_unambiguous_type_and_unit() -> None:
    missing_type = resolve_exact_property_intent(
        _intent(set_name="Custom_Energy", property_name="UValue", value=1.2),
        target_ifc_class="IfcWindow",
        existing_facts=(),
        registry=load_ifc2x3_registry(),
    )
    missing_unit = resolve_exact_property_intent(
        _intent(
            set_name="Custom_Energy",
            property_name="UValue",
            value=1.2,
            requested_value_type="IfcThermalTransmittanceMeasure",
        ),
        target_ifc_class="IfcWindow",
        existing_facts=(),
        registry=load_ifc2x3_registry(),
    )
    complete = resolve_exact_property_intent(
        _intent(
            set_name="Custom_Energy",
            property_name="UValue",
            value=1.2,
            requested_value_type="IfcThermalTransmittanceMeasure",
            requested_unit="W/(m2.K)",
        ),
        target_ifc_class="IfcWindow",
        existing_facts=(),
        registry=load_ifc2x3_registry(),
    )

    assert missing_type.reason_code == "CUSTOM_VALUE_TYPE_REQUIRED"
    assert missing_unit.reason_code == "CUSTOM_UNIT_REQUIRED"
    assert complete.status is PropertyResolutionStatus.CUSTOM_CONFIRMATION_REQUIRED
    assert complete.value_type == "IfcThermalTransmittanceMeasure"
    assert complete.unit == "W/(m2.K)"


@pytest.mark.parametrize("bad_value", [[], {}, math.inf, -math.inf, math.nan])
def test_non_scalar_and_non_finite_values_fail_closed(bad_value: object) -> None:
    result = resolve_exact_property_intent(
        _intent(
            set_name="Custom_Asset",
            property_name="BadValue",
            value=bad_value,
        ),
        target_ifc_class="IfcWindow",
        existing_facts=(),
        registry=load_ifc2x3_registry(),
    )
    assert result.status is PropertyResolutionStatus.CLARIFICATION_REQUIRED
    assert result.reason_code == "PROPERTY_VALUE_INVALID"


def test_requested_type_conflict_does_not_override_official_metadata() -> None:
    result = resolve_exact_property_intent(
        _intent(requested_value_type="IfcInteger"),
        target_ifc_class="IfcWindow",
        existing_facts=(
            PropertyFact(
                "pset",
                "Pset_WindowCommon",
                "FireRating",
                "EI60",
                "IfcInteger",
                None,
                False,
                "fixture",
            ),
        ),
        registry=load_ifc2x3_registry(),
    )
    assert result.status is PropertyResolutionStatus.CLARIFICATION_REQUIRED
    assert result.reason_code == "REQUESTED_VALUE_TYPE_CONFLICT"
    assert result.value_type == "IfcLabel"

