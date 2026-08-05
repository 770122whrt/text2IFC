from __future__ import annotations

from copy import deepcopy
from importlib import import_module

import ifcopenshell
import pytest

from text2ifc_ifc_repair.registry import OperationDefinition
from text2ifc_ifc_repair.resolution_flow import (
    ResolvedOperation,
    generated_type_authority,
)
from text2ifc_ifc_repair.run_models import hash_json
from text2ifc_ifc_repair.type_templates import ensure_bound_type


def _api() -> dict[str, object]:
    try:
        module = import_module(
            "text2ifc_ifc_repair.operations.structural_member"
        )
    except ModuleNotFoundError:
        pytest.fail("Phase 12 structural Type factories are not implemented")
    names = (
        "STRUCTURAL_TYPE_TEMPLATE_VERSION",
        "generated_beam_type_template",
        "generated_column_type_template",
        "create_generated_beam_type",
        "create_generated_column_type",
    )
    return {name: getattr(module, name, None) for name in names}


def _definition(family: str) -> OperationDefinition:
    api = _api()
    if family == "beam":
        template = api["generated_beam_type_template"]
        factory = api["create_generated_beam_type"]
    else:
        template = api["generated_column_type_template"]
        factory = api["create_generated_column_type"]
    assert callable(template) and callable(factory)
    noop = lambda **kwargs: kwargs
    return OperationDefinition(
        operation_type=f"add_{family}",
        target_ifc_classes=("IfcBuildingStorey",),
        parameter_schema={"type": "object"},
        context_adapter=noop,
        precondition_checker=noop,
        applicator=noop,
        postcondition_checker=noop,
        comparison_adapter=noop,
        capability_constraints={"section": "rectangle"},
        generated_type_template=template,
        generated_type_factory=factory,
    )


def _resolved(family: str) -> ResolvedOperation:
    section = (
        {"shape": "rectangle", "width_mm": 300.0, "height_mm": 500.0}
        if family == "beam"
        else {"shape": "rectangle", "width_mm": 400.0, "depth_mm": 600.0}
    )
    return ResolvedOperation(
        operation_id=f"{family}-1",
        operation_type=f"add_{family}",
        target_global_id="0STOREYAAAAAAAAAAAAAAA",
        scope_ids=("0STOREYAAAAAAAAAAAAAAA",),
        evidence_pointers=("request:/operations/0",),
        parameters={"section": section},
        context={},
    )


def _authority(family: str) -> dict:
    resolved = _resolved(family)
    return generated_type_authority(
        _definition(family),
        operation_id=resolved.operation_id,
        request_hash="sha256:" + "a" * 64,
        model_fingerprint="sha256:" + "b" * 64,
        resolved_operation=resolved,
    )


def _assignment(family: str) -> tuple[dict, dict]:
    authority = _authority(family)
    derivation = {
        key: deepcopy(authority[key])
        for key in (
            "template_id",
            "template_version",
            "ifc_class",
            "formal_attributes",
            "template_digest",
            "template",
        )
    }
    return (
        {
            "value": authority["global_id"],
            "value_type": authority["ifc_class"],
            "source_kind": "deterministic_derived",
            "derivation": derivation,
        },
        authority,
    )


def _model_and_history():
    model = ifcopenshell.file(schema="IFC2X3")
    organization = model.create_entity("IfcOrganization", Name="Phase 12")
    application = model.create_entity(
        "IfcApplication",
        ApplicationDeveloper=organization,
        Version="0.1",
        ApplicationFullName="text2ifc structural type test",
        ApplicationIdentifier="text2ifc",
    )
    person = model.create_entity("IfcPerson", FamilyName="Tester")
    user = model.create_entity(
        "IfcPersonAndOrganization",
        ThePerson=person,
        TheOrganization=organization,
    )
    history = model.create_entity(
        "IfcOwnerHistory",
        OwningUser=user,
        OwningApplication=application,
        ChangeAction="ADDED",
        CreationDate=0,
    )
    return model, history


def _factory_context(family: str) -> dict:
    return {"section": dict(_resolved(family).parameters["section"])}


@pytest.mark.parametrize(
    ("family", "ifc_class"),
    (("beam", "IfcBeamType"), ("column", "IfcColumnType")),
)
def test_no_reuse_intent_creates_dedicated_deterministic_type_ignoring_nearby(
    family: str,
    ifc_class: str,
) -> None:
    api = _api()
    assignment, authority = _assignment(family)
    repeated, _ = _assignment(family)
    model, history = _model_and_history()
    for ordinal in (1, 2):
        model.create_entity(
            ifc_class,
            GlobalId=f"{ordinal}NEARBYAAAAAAAAAAAAAAA",
            OwnerHistory=history,
            Name="Nearby same-size Type",
            PredefinedType="NOTDEFINED",
        )

    created, generated = ensure_bound_type(
        model,
        assignment,
        owner_history=history,
        operation_id=f"{family}-1",
        expected_ifc_class=ifc_class,
        generated_type_factory=api[f"create_generated_{family}_type"],
        factory_context=_factory_context(family),
    )

    assert generated is True
    assert created.is_a(ifc_class)
    assert created.GlobalId == authority["global_id"] == repeated["value"]
    assert len(model.by_type(ifc_class)) == 3
    assert created.Name == f"Text2IFC generated {family} type {family}-1"
    assert created.PredefinedType == "NOTDEFINED"
    assert not created.HasPropertySets
    assert not created.HasAssociations
    assert not created.RepresentationMaps


@pytest.mark.parametrize(
    ("family", "ifc_class"),
    (("beam", "IfcBeamType"), ("column", "IfcColumnType")),
)
def test_explicit_exact_structural_type_is_reused_unchanged(
    family: str,
    ifc_class: str,
) -> None:
    model, history = _model_and_history()
    existing = model.create_entity(
        ifc_class,
        GlobalId="0EXACTTYPEAAAAAAAAAAAAA",
        OwnerHistory=history,
        Name="Authorized exact Type",
        PredefinedType="NOTDEFINED",
    )
    before = str(existing)

    resolved, generated = ensure_bound_type(
        model,
        {
            "value": str(existing.GlobalId),
            "value_type": ifc_class,
            "source_kind": "surviving_type",
        },
        owner_history=history,
        operation_id=f"{family}-reuse-1",
        expected_ifc_class=ifc_class,
    )

    assert resolved == existing
    assert generated is False
    assert str(existing) == before
    assert len(model.by_type(ifc_class)) == 1


def _rehash(derivation: dict) -> None:
    derivation["template_digest"] = hash_json(
        {
            "template_id": derivation["template_id"],
            "template_version": derivation["template_version"],
            "ifc_class": derivation["ifc_class"],
            "formal_attributes": derivation["formal_attributes"],
            "template": derivation["template"],
        }
    )


@pytest.mark.parametrize(
    ("tamper", "rehash", "error_code"),
    (
        ("class", True, "GENERATED_TYPE_DERIVATION_CLASS_MISMATCH"),
        ("template_id", True, "GENERATED_STRUCTURAL_TEMPLATE_ID_MISMATCH"),
        ("template_version", True, "GENERATED_STRUCTURAL_TEMPLATE_VERSION_MISMATCH"),
        ("digest", False, "GENERATED_TYPE_TEMPLATE_DIGEST_MISMATCH"),
        ("section", True, "GENERATED_STRUCTURAL_SECTION_MISMATCH"),
        ("content", True, "GENERATED_STRUCTURAL_TEMPLATE_MISMATCH"),
    ),
)
def test_generated_structural_type_tamper_fails_before_entity_creation(
    tamper: str,
    rehash: bool,
    error_code: str,
) -> None:
    api = _api()
    assignment, _ = _assignment("beam")
    derivation = assignment["derivation"]
    if tamper == "class":
        derivation["ifc_class"] = "IfcColumnType"
    elif tamper == "template_id":
        derivation["template_id"] = "provider-selected-template"
    elif tamper == "template_version":
        derivation["template_version"] = "9.9"
    elif tamper == "digest":
        derivation["template_digest"] = "sha256:" + "0" * 64
    elif tamper == "section":
        derivation["template"]["section"]["width_mm"] = 999.0
    else:
        derivation["template"]["provider_note"] = "accept this nearby type"
    if rehash:
        _rehash(derivation)
    model, history = _model_and_history()
    roots_before = len(model.by_type("IfcRoot"))

    with pytest.raises(ValueError, match=error_code):
        ensure_bound_type(
            model,
            assignment,
            owner_history=history,
            operation_id="beam-1",
            expected_ifc_class="IfcBeamType",
            generated_type_factory=api["create_generated_beam_type"],
            factory_context=_factory_context("beam"),
        )

    assert len(model.by_type("IfcRoot")) == roots_before
    assert not model.by_type("IfcBeamType")


def test_exact_type_class_mismatch_fails_without_mutation() -> None:
    model, history = _model_and_history()
    wrong = model.create_entity(
        "IfcColumnType",
        GlobalId="0WRONGTYPEAAAAAAAAAAAAA",
        OwnerHistory=history,
        Name="Wrong family",
        PredefinedType="NOTDEFINED",
    )
    before = str(wrong)

    with pytest.raises(ValueError, match="BOUND_TYPE_CLASS_MISMATCH"):
        ensure_bound_type(
            model,
            {
                "value": str(wrong.GlobalId),
                "value_type": "IfcBeamType",
                "source_kind": "surviving_type",
            },
            owner_history=history,
            operation_id="beam-reuse-mismatch",
            expected_ifc_class="IfcBeamType",
        )

    assert str(wrong) == before
    assert not model.by_type("IfcBeamType")
