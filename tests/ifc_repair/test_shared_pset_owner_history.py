"""Occurrence property copy-on-write must preserve the existing owner graph.

Independent synthetic Beam and Window scenes exercise the production transaction
and real native schema/EXPRESS validation, including IfcApplication uniqueness.
These are offline regressions, not Provider or blind capability evidence.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import uuid

import ifcopenshell
import ifcopenshell.validate
import pytest

from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair import semantic_authoring


SCENES = ("beam", "window")
SCALARS = ("boolean", "identifier")
SHARING = ("shared_pset", "shared_property", "ordinary_pset")
OWNER_CLASSES = (
    "IfcOwnerHistory",
    "IfcApplication",
    "IfcPersonAndOrganization",
    "IfcPerson",
    "IfcOrganization",
)


def _guid(key: str) -> str:
    return ifcopenshell.guid.compress(uuid.uuid5(uuid.NAMESPACE_URL, key).hex)


def _native_diagnostics(model):
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(model, logger, express_rules=True)
    return logger.statements


def _direct_pset(element):
    return next(
        relation.RelatingPropertyDefinition
        for relation in element.IsDefinedBy
        if relation.is_a("IfcRelDefinesByProperties")
    )


def _values(pset):
    return {
        prop.Name: (prop.NominalValue.is_a(), prop.NominalValue.wrappedValue)
        for prop in pset.HasProperties
    }


def _owner_graph(model):
    return {
        ifc_class: tuple(entity.to_string() for entity in model.by_type(ifc_class))
        for ifc_class in OWNER_CLASSES
    }


def _source(scene: str, scalar: str, sharing: str):
    """Build valid IFC2X3 public input without a pristine or private benchmark."""
    model = ifcopenshell.file(schema="IFC2X3")
    model.header.file_name.time_stamp = "2026-10-08T00:00:00"
    key = f"text2ifc/shared-pset-regression/{scene}/{scalar}/{sharing}"

    def root(ifc_class, label, **kwargs):
        return model.create_entity(
            ifc_class,
            GlobalId=_guid(f"{key}/{label}"),
            OwnerHistory=owner,
            Name=label,
            **kwargs,
        )

    organization = model.create_entity("IfcOrganization", Name=f"{scene} studio")
    application = model.create_entity(
        "IfcApplication",
        ApplicationDeveloper=organization,
        Version="1.0",
        ApplicationFullName=f"{scene} source writer",
        ApplicationIdentifier=f"text2ifc-{scene}",
    )
    person = model.create_entity("IfcPerson", FamilyName=f"{scene} author")
    user = model.create_entity(
        "IfcPersonAndOrganization", ThePerson=person, TheOrganization=organization
    )
    owner = model.create_entity(
        "IfcOwnerHistory",
        OwningUser=user,
        OwningApplication=application,
        ChangeAction="ADDED",
        CreationDate=0,
    )

    def axis(location):
        return model.create_entity(
            "IfcAxis2Placement3D",
            Location=model.create_entity("IfcCartesianPoint", Coordinates=location),
        )

    context = model.create_entity(
        "IfcGeometricRepresentationContext",
        ContextType="Model",
        CoordinateSpaceDimension=3,
        Precision=1e-6,
        WorldCoordinateSystem=axis((0.0, 0.0, 0.0)),
    )
    units = model.create_entity(
        "IfcUnitAssignment",
        Units=[model.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")],
    )
    project = root(
        "IfcProject", "Project", RepresentationContexts=[context], UnitsInContext=units
    )
    building = root("IfcBuilding", "Building", CompositionType="ELEMENT")
    storey = root(
        "IfcBuildingStorey", "Storey", CompositionType="ELEMENT", Elevation=0.0
    )
    for parent, child in ((project, building), (building, storey)):
        root(
            "IfcRelAggregates",
            f"aggregate-{child.Name}",
            RelatingObject=parent,
            RelatedObjects=[child],
        )
    ifc_class = "IfcBeam" if scene == "beam" else "IfcWindow"
    products = []
    for index, label in enumerate(("Target", "Peer")):
        product = root(ifc_class, label)
        if scene == "window":
            product.OverallWidth = 0.9
            product.OverallHeight = 1.2
        product.ObjectPlacement = model.create_entity(
            "IfcLocalPlacement", RelativePlacement=axis((float(index * 4), 0.0, 1.0))
        )
        profile = model.create_entity(
            "IfcRectangleProfileDef",
            ProfileType="AREA",
            Position=model.create_entity(
                "IfcAxis2Placement2D",
                Location=model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0)),
            ),
            XDim=0.2,
            YDim=0.3,
        )
        solid = model.create_entity(
            "IfcExtrudedAreaSolid",
            SweptArea=profile,
            Position=axis((0.0, 0.0, 0.0)),
            ExtrudedDirection=model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)),
            Depth=3.0 if scene == "beam" else 1.2,
        )
        shape = model.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=context,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[solid],
        )
        product.Representation = model.create_entity(
            "IfcProductDefinitionShape", Representations=[shape]
        )
        products.append(product)
    root(
        "IfcRelContainedInSpatialStructure",
        "containment",
        RelatedElements=products,
        RelatingStructure=storey,
    )

    set_name = f"Pset_{'Beam' if scene == 'beam' else 'Window'}Common"
    prop_name, value_type, old_value, new_value = (
        ("LoadBearing" if scene == "beam" else "IsExternal", "IfcBoolean", False, True)
        if scalar == "boolean"
        else ("Reference", "IfcIdentifier", f"{scene}-OLD", f"{scene}-NEW")
    )

    def prop(name, ifc_type, value):
        return model.create_entity(
            "IfcPropertySingleValue",
            Name=name,
            NominalValue=model.create_entity(ifc_type, value),
        )

    initial = prop(prop_name, value_type, old_value)

    def pset(label, requested):
        return root(
            "IfcPropertySet",
            label,
            HasProperties=[requested, prop("Keep", "IfcLabel", "unchanged")],
        )

    target_pset = pset("target-pset", initial)
    target_pset.Name = set_name
    target, peer = products
    if sharing == "shared_pset":
        root(
            "IfcRelDefinesByProperties",
            "shared-pset-relationship",
            RelatedObjects=products,
            RelatingPropertyDefinition=target_pset,
        )
    else:
        peer_prop = initial if sharing == "shared_property" else prop(prop_name, value_type, old_value)
        peer_pset = pset("peer-pset", peer_prop)
        peer_pset.Name = set_name
        for element, owned in ((target, target_pset), (peer, peer_pset)):
            root(
                "IfcRelDefinesByProperties",
                f"{element.Name}-properties",
                RelatedObjects=[element],
                RelatingPropertyDefinition=owned,
            )
    inherited = pset("type-pset", prop(prop_name, value_type, old_value))
    inherited.Name = set_name
    type_kwargs = (
        {"PredefinedType": "BEAM"}
        if scene == "beam"
        else {
            "ConstructionType": "NOTDEFINED",
            "OperationType": "NOTDEFINED",
            "ParameterTakesPrecedence": False,
            "Sizeable": False,
        }
    )
    existing_type = root(
        "IfcBeamType" if scene == "beam" else "IfcWindowStyle",
        "Existing shared Type",
        HasPropertySets=[inherited],
        **type_kwargs,
    )
    root(
        "IfcRelDefinesByType",
        "shared-type-relationship",
        RelatedObjects=products,
        RelatingType=existing_type,
    )
    return model, target, peer, existing_type, prop_name, value_type, old_value, new_value


def _case(tmp_path: Path, scene: str, scalar: str, sharing: str):
    fixture = _source(scene, scalar, sharing)
    model, target, peer, existing_type, prop_name, value_type, old_value, new_value = fixture
    source = tmp_path / "source.ifc"
    model.write(str(source))
    reopened = ifcopenshell.open(str(source))
    diagnostics = _native_diagnostics(reopened)
    assert not diagnostics, diagnostics
    request = f"Set the target {scene} {prop_name} to {new_value}; preserve all other facts."
    fact_key = f"pset:{_direct_pset(target).Name}.{prop_name}"
    operation = {
        "operation_id": "property-1",
        "operation_type": "set_occurrence_properties",
        "target": {"element_global_id": str(target.GlobalId)},
        "parameters": {},
        "evidence_refs": ["property-resolution:/claim-1/decision.json"],
        "semantic_manifest": {
            "manifest_id": "owner-history-regression",
            "policy_id": "occurrence.property.l2",
            "policy_version": "0.1",
        },
        "semantic_assignments": [{
            "operation_id": "property-1",
            "fact_key": fact_key,
            "source_fact_key": fact_key,
            "value": new_value,
            "value_type": value_type,
            "unit": None,
            "ownership": "occurrence_direct",
            "applicability": "required",
            "source_kind": "explicit_request",
            "source_ref": "property-resolution:/claim-1/decision.json",
            "provenance": ["property-resolution:sha256:fixture"],
            "authoring_action": "set_occurrence_pset",
        }],
    }
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.2",
        "changeset_id": f"shared-pset-{scene}-{scalar}-{sharing}",
        "binding_status": "bound",
        "base_model_fingerprint": "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_request_hash": "sha256:" + hashlib.sha256(request.encode()).hexdigest(),
        "scope": {"target_ids": [str(target.GlobalId)], "forbidden_ids": []},
        "evidence_refs": operation["evidence_refs"],
        "preconditions": ["target_exists"],
        "postconditions": ["requested_properties_match"],
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "e" * 64,
        "operations": [operation],
    }
    return source, reopened, request, changeset, fixture


@pytest.mark.parametrize("scene", SCENES)
@pytest.mark.parametrize("scalar", SCALARS)
@pytest.mark.parametrize("sharing", SHARING)
def test_occurrence_upsert_preserves_owner_graph_and_passes_express(
    tmp_path: Path, scene: str, scalar: str, sharing: str
) -> None:
    source, before, request, changeset, fixture = _case(tmp_path, scene, scalar, sharing)
    _, target, peer, existing_type, prop_name, value_type, old_value, new_value = fixture
    source_bytes = source.read_bytes()
    candidate = tmp_path / "candidate.ifc"
    result = apply_changeset(
        damaged_ifc_path=source,
        repair_request=request,
        changeset=changeset,
        output_path=candidate,
        registry=create_default_registry(),
    )
    assert result["valid"] and result["published"], result
    assert source.read_bytes() == source_bytes
    after = ifcopenshell.open(str(candidate))
    assert after.schema == "IFC2X3"
    updated = after.by_guid(str(target.GlobalId))
    unchanged_peer = after.by_guid(str(peer.GlobalId))
    assert _values(_direct_pset(updated)) == {
        prop_name: (value_type, new_value), "Keep": ("IfcLabel", "unchanged")
    }
    assert _values(_direct_pset(unchanged_peer)) == {
        prop_name: (value_type, old_value), "Keep": ("IfcLabel", "unchanged")
    }
    for product in before.by_type("IfcProduct"):
        if not product.Representation:
            continue
        repaired = after.by_guid(str(product.GlobalId))
        assert repaired.to_string() == product.to_string()
        assert repaired.ObjectPlacement.to_string() == product.ObjectPlacement.to_string()
        assert repaired.Representation.to_string() == product.Representation.to_string()
    for root in before.by_type("IfcTypeObject"):
        repaired = after.by_guid(str(root.GlobalId))
        assert repaired.to_string() == root.to_string()
        assert tuple(ps.to_string() for ps in repaired.HasPropertySets) == tuple(
            ps.to_string() for ps in root.HasPropertySets
        )
    assert _values(after.by_guid(str(existing_type.GlobalId)).HasPropertySets[0])[prop_name] == (value_type, old_value)
    diagnostics = _native_diagnostics(after)
    assert not diagnostics, diagnostics
    assert _owner_graph(after) == _owner_graph(before)
    assert _direct_pset(updated).OwnerHistory.id() == before.by_guid(str(target.GlobalId)).OwnerHistory.id()
    if sharing == "shared_pset":
        assert _direct_pset(updated).GlobalId != _direct_pset(unchanged_peer).GlobalId
        old_relation = next(
            rel for rel in before.by_type("IfcRelDefinesByProperties")
            if len(rel.RelatedObjects) == 2
        )
        assert tuple(after.by_guid(old_relation.GlobalId).RelatedObjects) == (unchanged_peer,)


@pytest.mark.parametrize("scene", SCENES)
@pytest.mark.parametrize("scalar", SCALARS)
def test_failure_after_shared_pset_copy_publishes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scene: str, scalar: str
) -> None:
    source, _, request, changeset, _ = _case(tmp_path, scene, scalar, "shared_pset")
    source_bytes = source.read_bytes()
    reached = []

    def fail_after_copy(model, assignment):
        reached.append(len(model.by_type("IfcPropertySet")))
        raise RuntimeError("injected property failure after copy-on-write")

    monkeypatch.setattr(semantic_authoring, "_ifc_typed_value", fail_after_copy)
    candidate = tmp_path / "candidate.ifc"
    result = apply_changeset(
        damaged_ifc_path=source, repair_request=request, changeset=changeset,
        output_path=candidate, registry=create_default_registry(),
    )
    assert reached == [3]
    assert not result["valid"] and not result["published"]
    assert result["issues"][0]["code"] == "OPERATION_APPLICATION_FAILED"
    assert not candidate.exists()
    assert source.read_bytes() == source_bytes
    assert not _native_diagnostics(ifcopenshell.open(str(source)))


@pytest.mark.parametrize("scene", SCENES)
def test_shared_type_mutation_is_rejected_before_copy(
    tmp_path: Path, scene: str
) -> None:
    source, _, request, changeset, _ = _case(tmp_path, scene, "boolean", "shared_pset")
    source_bytes = source.read_bytes()
    changeset["operations"][0]["semantic_assignments"][0]["ownership"] = "type_inherited"
    candidate = tmp_path / "candidate.ifc"
    result = apply_changeset(
        damaged_ifc_path=source, repair_request=request, changeset=changeset,
        output_path=candidate, registry=create_default_registry(),
    )
    assert not result["valid"] and not result["published"]
    assert not candidate.exists()
    assert source.read_bytes() == source_bytes
