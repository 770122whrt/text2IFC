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
from text2ifc_ifc_repair.semantic_authoring import (
    SemanticManifestError,
    apply_semantic_assignments,
)
from text2ifc_ifc_repair.type_templates import (
    ensure_bound_type,
    type_authority_fingerprint,
)
from text2ifc_ifc_repair.operations.structural_member import bind_structural_type


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


def _direct_psets(element) -> list:
    return [
        relation.RelatingPropertyDefinition
        for relation in element.IsDefinedBy
        if relation.is_a("IfcRelDefinesByProperties")
    ]


def _direct_materials(element) -> list:
    return [
        relation.RelatingMaterial
        for relation in element.HasAssociations
        if relation.is_a("IfcRelAssociatesMaterial")
    ]


def _material_assignment(
    family: str,
    label: str,
    *,
    source_ref: str = "request:/materials/0",
) -> dict:
    return {
        "operation_id": f"{family}-semantic-1",
        "scope": f"{family}_occurrence",
        "fact_key": f"material:{label}",
        "source_fact_key": f"material:{label}",
        "value": label,
        "value_type": "IfcMaterial",
        "unit": None,
        "ownership": "occurrence_direct",
        "applicability": "required",
        "source_kind": "explicit_value",
        "source_ref": source_ref,
        "provenance": ["request:/materials/0"],
        "authoring_action": "reuse_material",
    }


def _pset_assignment(family: str) -> dict:
    set_name = "Pset_BeamCommon" if family == "beam" else "Pset_ColumnCommon"
    return {
        "operation_id": f"{family}-semantic-1",
        "scope": f"{family}_occurrence",
        "fact_key": f"pset:{set_name}.LoadBearing",
        "source_fact_key": f"pset:{set_name}.LoadBearing",
        "value": True,
        "value_type": "IfcBoolean",
        "unit": None,
        "ownership": "occurrence_direct",
        "applicability": "required",
        "source_kind": "explicit_value",
        "source_ref": "request:/properties/0",
        "provenance": ["request:/properties/0"],
        "authoring_action": "set_occurrence_pset",
    }


def _apply_semantics(model, occurrence, family: str, assignments: list[dict]):
    return apply_semantic_assignments(
        model=model,
        operation={
            "operation_id": f"{family}-semantic-1",
            "semantic_assignments": assignments,
        },
        application={
            "created": [
                {
                    "role": family,
                    "ifc_class": occurrence.is_a(),
                    "global_id": str(occurrence.GlobalId),
                }
            ]
        },
        target_role=family,
    )


def _type_preservation_fixture(family: str):
    model, history = _model_and_history()
    occurrence_class = "IfcBeam" if family == "beam" else "IfcColumn"
    type_class = f"{occurrence_class}Type"
    inherited_pset = model.create_entity(
        "IfcPropertySet",
        GlobalId="0TYPEPSETAAAAAAAAAAAAAA",
        OwnerHistory=history,
        Name="Compiler-owned type facts",
        HasProperties=[
            model.create_entity(
                "IfcPropertySingleValue",
                Name="Reference",
                NominalValue=model.create_entity("IfcIdentifier", "TYPE-01"),
            )
        ],
    )
    world = model.create_entity(
        "IfcAxis2Placement3D",
        Location=model.create_entity(
            "IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)
        ),
    )
    context = model.create_entity(
        "IfcGeometricRepresentationContext",
        ContextType="Model",
        CoordinateSpaceDimension=3,
        Precision=1e-5,
        WorldCoordinateSystem=world,
    )
    representation = model.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[],
    )
    representation_map = model.create_entity(
        "IfcRepresentationMap",
        MappingOrigin=world,
        MappedRepresentation=representation,
    )
    reused_type = model.create_entity(
        type_class,
        GlobalId="0EXACTRICHAAAAAAAAAAAAA",
        OwnerHistory=history,
        Name="Authorized rich Type",
        RepresentationMaps=[representation_map],
        HasPropertySets=[inherited_pset],
        PredefinedType="NOTDEFINED",
    )
    inherited_material = model.create_entity("IfcMaterial", Name="Steel")
    model.create_entity(
        "IfcRelAssociatesMaterial",
        GlobalId="0TYPEMATERIALAAAAAAAAAA",
        OwnerHistory=history,
        RelatedObjects=[reused_type],
        RelatingMaterial=inherited_material,
    )
    reference = model.create_entity(
        occurrence_class,
        GlobalId="0REFERENCEAAAAAAAAAAAAA",
        OwnerHistory=history,
        Name="Authorized reference occurrence",
    )
    direct_pset = model.create_entity(
        "IfcPropertySet",
        GlobalId="0DIRECTPSETAAAAAAAAAAAA",
        OwnerHistory=history,
        Name="Reference occurrence facts",
        HasProperties=[],
    )
    model.create_entity(
        "IfcRelDefinesByProperties",
        GlobalId="0DIRECTPSETRELAAAAAAAAA",
        OwnerHistory=history,
        RelatedObjects=[reference],
        RelatingPropertyDefinition=direct_pset,
    )
    direct_material = model.create_entity("IfcMaterial", Name="Occurrence-only")
    model.create_entity(
        "IfcRelAssociatesMaterial",
        GlobalId="0DIRECTMATRELAAAAAAAAAA",
        OwnerHistory=history,
        RelatedObjects=[reference],
        RelatingMaterial=direct_material,
    )
    relation = model.create_entity(
        "IfcRelDefinesByType",
        GlobalId="0EXACTTYPERELAAAAAAAAAA",
        OwnerHistory=history,
        RelatedObjects=[reference],
        RelatingType=reused_type,
    )
    return model, history, reused_type, inherited_material, reference, relation


@pytest.mark.parametrize("family", ("beam", "column"))
def test_exact_type_binding_preserves_type_maps_psets_and_materials_without_copying_direct_facts(
    family: str,
) -> None:
    model, history, reused_type, _, reference, relation = _type_preservation_fixture(
        family
    )
    occurrence_class = "IfcBeam" if family == "beam" else "IfcColumn"
    occurrence = model.create_entity(
        occurrence_class,
        GlobalId=f"0NEW{family.upper()}AAAAAAAAAAAAAA"[:22],
        OwnerHistory=history,
        Name="New structural occurrence",
    )
    before = type_authority_fingerprint(reused_type)

    result = bind_structural_type(
        model=model,
        occurrence=occurrence,
        assignment={
            "value": str(reused_type.GlobalId),
            "value_type": reused_type.is_a(),
            "source_kind": "surviving_type",
        },
        owner_history=history,
        operation_id=f"{family}-reuse-rich",
        expected_ifc_class=reused_type.is_a(),
        generated_type_factory=None,
        factory_context={},
    )

    assert result["type"] == reused_type
    assert result["generated"] is False
    assert result["relationship"] == relation
    assert set(relation.RelatedObjects) == {reference, occurrence}
    assert type_authority_fingerprint(reused_type) == before
    assert _direct_psets(occurrence) == []
    assert _direct_materials(occurrence) == []
    assert _direct_psets(reference)
    assert {item.Name for item in _direct_materials(reference)} == {
        "Occurrence-only"
    }


@pytest.mark.parametrize("family", ("beam", "column"))
def test_omitted_structural_semantics_author_nothing_and_do_not_clarify(
    family: str,
) -> None:
    model, history = _model_and_history()
    occurrence_class = "IfcBeam" if family == "beam" else "IfcColumn"
    occurrence = model.create_entity(
        occurrence_class,
        GlobalId=f"0EMPTY{family.upper()}AAAAAAAAAAAA"[:22],
        OwnerHistory=history,
    )
    roots_before = len(model.by_type("IfcRoot"))

    result = _apply_semantics(model, occurrence, family, [])

    assert result == {"created": [], "modified": [], "updated": [], "skipped": []}
    assert len(model.by_type("IfcRoot")) == roots_before
    assert _direct_psets(occurrence) == []
    assert _direct_materials(occurrence) == []


@pytest.mark.parametrize("existing", (True, False))
def test_explicit_material_reuses_unique_exact_label_or_creates_only_that_label(
    existing: bool,
) -> None:
    model, history = _model_and_history()
    occurrence = model.create_entity(
        "IfcBeam",
        GlobalId="0MATERIALBEAMAAAAAAAAAA",
        OwnerHistory=history,
    )
    expected = model.create_entity("IfcMaterial", Name="C30") if existing else None

    _apply_semantics(model, occurrence, "beam", [_material_assignment("beam", "C30")])

    direct = _direct_materials(occurrence)
    assert len(direct) == 1
    assert direct[0].Name == "C30"
    if existing:
        assert direct[0] == expected
    assert [item.Name for item in model.by_type("IfcMaterial")].count("C30") == 1
    assert not model.by_type("IfcMaterialProperties")


def test_explicit_pset_is_direct_but_type_inherited_material_stays_inherited() -> None:
    model, history, reused_type, inherited_material, _, _ = _type_preservation_fixture(
        "beam"
    )
    occurrence = model.create_entity(
        "IfcBeam",
        GlobalId="0SEMANTICBEAMAAAAAAAAAA",
        OwnerHistory=history,
    )
    bind_structural_type(
        model=model,
        occurrence=occurrence,
        assignment={
            "value": str(reused_type.GlobalId),
            "value_type": "IfcBeamType",
            "source_kind": "surviving_type",
        },
        owner_history=history,
        operation_id="beam-semantic-1",
        expected_ifc_class="IfcBeamType",
        generated_type_factory=None,
        factory_context={},
    )

    result = _apply_semantics(
        model,
        occurrence,
        "beam",
        [_pset_assignment("beam"), _material_assignment("beam", "Steel")],
    )

    direct_psets = _direct_psets(occurrence)
    assert len(direct_psets) == 1
    assert direct_psets[0].Name == "Pset_BeamCommon"
    assert direct_psets[0].HasProperties[0].Name == "LoadBearing"
    assert direct_psets[0].HasProperties[0].NominalValue.wrappedValue is True
    assert _direct_materials(occurrence) == []
    assert inherited_material in [
        relation.RelatingMaterial
        for relation in reused_type.HasAssociations
        if relation.is_a("IfcRelAssociatesMaterial")
    ]
    assert "material:Steel" in result["skipped"]


def test_explicit_material_conflict_with_reused_type_fails_before_semantic_mutation() -> None:
    model, history, reused_type, _, _, _ = _type_preservation_fixture("beam")
    occurrence = model.create_entity(
        "IfcBeam",
        GlobalId="0CONFLICTBEAMAAAAAAAAAA",
        OwnerHistory=history,
    )
    bind_structural_type(
        model=model,
        occurrence=occurrence,
        assignment={
            "value": str(reused_type.GlobalId),
            "value_type": "IfcBeamType",
            "source_kind": "surviving_type",
        },
        owner_history=history,
        operation_id="beam-semantic-1",
        expected_ifc_class="IfcBeamType",
        generated_type_factory=None,
        factory_context={},
    )
    fingerprint = type_authority_fingerprint(reused_type)
    roots_before = len(model.by_type("IfcRoot"))

    with pytest.raises(
        SemanticManifestError, match="STRUCTURAL_MATERIAL_TYPE_CONFLICT"
    ):
        _apply_semantics(
            model,
            occurrence,
            "beam",
            [_pset_assignment("beam"), _material_assignment("beam", "C30")],
        )

    assert len(model.by_type("IfcRoot")) == roots_before
    assert type_authority_fingerprint(reused_type) == fingerprint
    assert _direct_psets(occurrence) == []
    assert _direct_materials(occurrence) == []
    assert not [item for item in model.by_type("IfcMaterial") if item.Name == "C30"]


def test_explicit_material_label_must_resolve_uniquely_before_mutation() -> None:
    model, history = _model_and_history()
    occurrence = model.create_entity(
        "IfcColumn",
        GlobalId="0AMBIGUOUSCOLUMNAAAAAAA",
        OwnerHistory=history,
    )
    model.create_entity("IfcMaterial", Name="Steel")
    model.create_entity("IfcMaterial", Name="Steel")
    roots_before = len(model.by_type("IfcRoot"))

    with pytest.raises(
        SemanticManifestError, match="SEMANTIC_MATERIAL_LABEL_AMBIGUOUS"
    ):
        _apply_semantics(
            model,
            occurrence,
            "column",
            [_material_assignment("column", "Steel")],
        )

    assert len(model.by_type("IfcRoot")) == roots_before
    assert _direct_materials(occurrence) == []


def test_generated_type_does_not_absorb_explicit_occurrence_semantics() -> None:
    api = _api()
    assignment, _ = _assignment("beam")
    model, history = _model_and_history()
    occurrence = model.create_entity(
        "IfcBeam",
        GlobalId="0GENERATEDBEAMAAAAAAAAA",
        OwnerHistory=history,
    )
    binding = bind_structural_type(
        model=model,
        occurrence=occurrence,
        assignment=assignment,
        owner_history=history,
        operation_id="beam-1",
        expected_ifc_class="IfcBeamType",
        generated_type_factory=api["create_generated_beam_type"],
        factory_context=_factory_context("beam"),
    )
    generated_type = binding["type"]
    before = type_authority_fingerprint(generated_type)

    _apply_semantics(
        model,
        occurrence,
        "beam",
        [_pset_assignment("beam"), _material_assignment("beam", "C30")],
    )

    assert type_authority_fingerprint(generated_type) == before
    assert not generated_type.HasPropertySets
    assert not generated_type.HasAssociations
    assert len(_direct_psets(occurrence)) == 1
    assert {item.Name for item in _direct_materials(occurrence)} == {"C30"}
