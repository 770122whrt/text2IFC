"""Legal Storey relation multiplicity must not imply ambiguous member ownership.

These are offline applicator regressions on two public IFC2X3 scenes. No
Provider, private repair Gold, schema relaxation or new structural policy is
involved. Each existing occurrence keeps its original spatial ownership.
"""
from __future__ import annotations

import hashlib
import uuid
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid
import pytest

from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.geometry import measure_straight_rectangular_member
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.operations.beam import beam_operation_definition
from text2ifc_ifc_repair.operations.column import column_operation_definition
from text2ifc_ifc_repair.operations.hosted_opening import body_context, deterministic_global_id
from text2ifc_ifc_repair.operations.structural_member import create_straight_rectangular_member
from text2ifc_ifc_repair.registry import OperationRegistry
from text2ifc_ifc_repair.resolution_flow import ResolvedOperation, generated_type_authority


ROOT = Path(__file__).resolve().parents[2]
SCENES = {name: ROOT / "dataset/external/bimnet" / f"{name}.ifc" for name in ("d7n", "vvo")}
STOREYS = {"d7n": "0K_MqVdrL0JOCMi_GblRwJ", "vvo": "1vTeahUkP60PdWqwCTjSGJ"}
COUNTS_AND_ORDER = [(0, False), (1, False), (2, False), (2, True), (3, False), (3, True)]
REQUEST = "Create straight rectangular structural members in the selected storey."


def _hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _guid(label: str) -> str:
    return ifcopenshell.guid.compress(uuid.uuid5(uuid.NAMESPACE_URL, label).hex)


def _definition(family: str):
    return beam_operation_definition() if family == "beam" else column_operation_definition()


def _parameters(family: str) -> dict:
    if family == "beam":
        return {
            "axis": {"start": {"x_mm": 100000, "y_mm": 100000, "z_mm": 3000},
                     "end": {"x_mm": 103000, "y_mm": 104000, "z_mm": 3000}},
            "section": {"shape": "rectangle", "width_mm": 300, "height_mm": 500},
        }
    return {
        "axis": {"base": {"x_mm": 110000, "y_mm": 100000, "z_mm": 0},
                 "top": {"x_mm": 110000, "y_mm": 100000, "z_mm": 6000}},
        "section": {"shape": "rectangle", "width_mm": 400, "depth_mm": 600,
                    "orientation": {"x": 0, "y": 1}},
    }


def _scene(tmp_path: Path, scene: str, count: int, reverse: bool):
    source = SCENES[scene]
    source_hash = _hash(source)
    model = ifcopenshell.open(str(source))
    storey = model.by_guid(STOREYS[scene])
    elements = sorted({item for relation in storey.ContainsElements for item in relation.RelatedElements},
                      key=lambda item: str(item.GlobalId))
    assert len(elements) >= 3
    for relation in tuple(storey.ContainsElements):
        model.remove(relation)
    indices = list(range(count))
    if reverse:
        indices.reverse()
    for index in indices:
        model.create_entity(
            "IfcRelContainedInSpatialStructure",
            GlobalId=_guid(f"multi-containment:{scene}:{count}:{index}"),
            OwnerHistory=storey.OwnerHistory,
            Name=f"Fixture group {index}",
            RelatedElements=elements[index::count],
            RelatingStructure=storey,
        )
    path = tmp_path / "source.ifc"
    model.write(str(path))
    assert _hash(source) == source_hash
    return path, str(storey.GlobalId)


def _operation(family: str, storey_id: str, source: Path) -> dict:
    definition = _definition(family)
    operation_id = f"multi-containment-{family}"
    parameters = _parameters(family)
    resolved = ResolvedOperation(
        operation_id=operation_id,
        operation_type=f"add_{family}",
        target_global_id=storey_id,
        scope_ids=(storey_id,),
        evidence_pointers=("request:/operations/0",),
        parameters=parameters,
        context={},
    )
    authority = generated_type_authority(
        definition,
        operation_id=operation_id,
        request_hash="sha256:" + hashlib.sha256(REQUEST.encode()).hexdigest(),
        model_fingerprint=_hash(source),
        resolved_operation=resolved,
    )
    assignment = {
        "operation_id": operation_id, "scope": f"{family}_occurrence",
        "fact_key": "relationship:type", "source_fact_key": "relationship:type",
        "value": authority["global_id"], "value_type": f"Ifc{family.title()}Type",
        "unit": None, "ownership": "type_inherited", "applicability": "required",
        "source_kind": "deterministic_derived", "source_ref": f"generated-type:{authority['global_id']}",
        "provenance": ["generated-type-template:0.1"],
        "derivation": {key: authority[key] for key in (
            "template_id", "template_version", "ifc_class", "formal_attributes", "template_digest", "template")},
        "authoring_action": "inherit_from_type",
    }
    return {
        "operation_id": operation_id, "operation_type": f"add_{family}",
        "target": {"storey_global_id": storey_id}, "parameters": parameters,
        "evidence_refs": ["request:/operations/0"],
        "semantic_manifest": {"manifest_id": f"manifest-{family}",
                              "policy_id": definition.evaluation_policy.policy_id, "policy_version": "0.1"},
        "semantic_assignments": [assignment],
    }


def _changeset(source: Path, storey_id: str, families: tuple[str, ...]) -> dict:
    operations = [_operation(family, storey_id, source) for family in families]
    return {
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "changeset_id": "changeset-multi-containment", "binding_status": "bound",
        "base_model_fingerprint": _hash(source),
        "source_request_hash": "sha256:" + hashlib.sha256(REQUEST.encode()).hexdigest(),
        "semantic_manifest_ref": "semantic-manifest.json", "semantic_manifest_sha256": "sha256:" + "c" * 64,
        "scope": {"target_ids": [storey_id], "forbidden_ids": []}, "evidence_refs": ["request:/operations/0"],
        "preconditions": ["target_exists", "structural_axis_available", "structural_type_authorized"],
        "postconditions": [name for family in families for name in _definition(family).postcondition_names],
        "operations": operations,
    }


def _apply(source: Path, output: Path, changeset: dict, registry=None) -> dict:
    original = _hash(source)
    result = apply_changeset(damaged_ifc_path=source, repair_request=REQUEST, changeset=changeset,
                            output_path=output, registry=registry or create_default_registry())
    assert _hash(source) == original
    return result


@pytest.mark.parametrize("scene", SCENES)
@pytest.mark.parametrize("count,reverse", COUNTS_AND_ORDER)
@pytest.mark.parametrize("family", ("beam", "column"))
def test_legal_storey_multiplicity_preserves_old_ownership_and_single_new_ownership(
    tmp_path: Path, scene: str, count: int, reverse: bool, family: str,
) -> None:
    source, storey_id = _scene(tmp_path, scene, count, reverse)
    before = ifcopenshell.open(str(source))
    old_relations = {str(item.GlobalId): item.to_string() for item in before.by_type("IfcRelContainedInSpatialStructure")}
    old_elements = {str(item.GlobalId): item.to_string() for item in before.by_type("IfcElement")}
    original_relation_ids = [str(item.GlobalId) for item in before.by_guid(storey_id).ContainsElements]
    output = tmp_path / "repaired.ifc"
    result = _apply(source, output, _changeset(source, storey_id, (family,)))

    assert result["valid"] and result["published"], result["issues"]
    reopened = ifcopenshell.open(str(output))
    assert reopened.schema == "IFC2X3"
    changes = result["operations"][0]["changes"]
    occurrence = reopened.by_guid(next(item["global_id"] for item in changes["created"] if item["role"] == family))
    contained = occurrence.ContainedInStructure
    assert len(contained) == 1 and str(contained[0].RelatingStructure.GlobalId) == storey_id
    assert len(reopened.by_type(f"Ifc{family.title()}")) == len(before.by_type(f"Ifc{family.title()}")) + 1
    typed = [item for item in occurrence.IsDefinedBy if item.is_a("IfcRelDefinesByType")]
    assert len(typed) == 1 and typed[0].RelatingType.is_a(f"Ifc{family.title()}Type")
    measured = measure_straight_rectangular_member(occurrence, relative_to=reopened.by_guid(storey_id))
    parameters = _parameters(family)
    endpoints = ("start", "end") if family == "beam" else ("base", "top")
    for measured_key, endpoint in zip(("axis_start_mm", "axis_end_mm"), endpoints):
        assert measured[measured_key] == pytest.approx(tuple(parameters["axis"][endpoint][axis] for axis in ("x_mm", "y_mm", "z_mm")))
    for guid, original in old_elements.items():
        assert reopened.by_guid(guid).to_string() == original
    for guid, original in old_relations.items():
        if count == 1 and guid in original_relation_ids:
            assert {str(item.GlobalId) for item in reopened.by_guid(guid).RelatedElements} == (
                {str(item.GlobalId) for item in before.by_guid(guid).RelatedElements} | {str(occurrence.GlobalId)})
        else:
            assert reopened.by_guid(guid).to_string() == original
    if count == 1:
        assert str(contained[0].GlobalId) == original_relation_ids[0]
        assert len(reopened.by_guid(storey_id).ContainsElements) == 1
        assert any(item["role"] == "spatial_containment" for item in changes["modified"])
    else:
        assert str(contained[0].GlobalId) not in old_relations
        assert contained[0].RelatedElements == (occurrence,)
        assert len(reopened.by_guid(storey_id).ContainsElements) == count + 1
        assert any(item["role"] == "spatial_containment" for item in changes["created"])
        assert not any(item["role"] == "spatial_containment" for item in changes["modified"])
    root_ids = [str(item.GlobalId) for item in reopened.by_type("IfcRoot")]
    assert len(root_ids) == len(set(root_ids))


@pytest.mark.parametrize("family", ("beam", "column"))
@pytest.mark.parametrize("reverse", (False, True))
@pytest.mark.parametrize("conflict_index", (0, 1, 2))
def test_same_axis_conflict_in_every_old_relation_still_blocks_without_publication(
    tmp_path: Path, family: str, reverse: bool, conflict_index: int,
) -> None:
    source, storey_id = _scene(tmp_path, "d7n", 3, reverse)
    model = ifcopenshell.open(str(source))
    storey = model.by_guid(storey_id)
    parameters = _parameters(family)
    endpoints = ("start", "end") if family == "beam" else ("base", "top")
    member = create_straight_rectangular_member(
        model=model, occurrence_class=f"Ifc{family.title()}",
        occurrence_global_id=_guid(f"existing-{family}-{conflict_index}"), operation_id="existing-member",
        axis_start_mm=tuple(parameters["axis"][endpoints[0]][key] for key in ("x_mm", "y_mm", "z_mm")),
        axis_end_mm=tuple(parameters["axis"][endpoints[1]][key] for key in ("x_mm", "y_mm", "z_mm")),
        section=deepcopy(parameters["section"]), storey=storey,
        owner_history=storey.OwnerHistory, representation_context=body_context(model),
    )["occurrence"]
    relation = storey.ContainsElements[conflict_index]
    relation.RelatedElements = (*relation.RelatedElements, member)
    model.write(str(source))
    output = tmp_path / "must-not-exist.ifc"
    result = _apply(source, output, _changeset(source, storey_id, (family,)))
    assert not result["valid"] and not result["published"] and not output.exists()
    assert any(item["code"] == "STRUCTURAL_EXISTING_SAME_AXIS_OVERLAP" for item in result["issues"])


@pytest.mark.parametrize("family", ("beam", "column"))
@pytest.mark.parametrize("invalid_storey", ("missing", "wrong_class"))
def test_invalid_storey_is_not_replaced_with_any_other_storey(
    tmp_path: Path, family: str, invalid_storey: str,
) -> None:
    source, _ = _scene(tmp_path, "d7n", 3, False)
    model = ifcopenshell.open(str(source))
    target = _guid("missing-storey") if invalid_storey == "missing" else str(model.by_type("IfcWall")[0].GlobalId)
    output = tmp_path / "must-not-exist.ifc"
    result = _apply(source, output, _changeset(source, target, (family,)))
    assert not result["valid"] and not result["published"] and not output.exists()
    assert any(item["code"] in ("TARGET_NOT_FOUND", "TARGET_CLASS_NOT_ALLOWED") for item in result["issues"])


@pytest.mark.parametrize("family", ("beam", "column"))
def test_type_authority_stays_mandatory_with_multiple_storey_relations(tmp_path: Path, family: str) -> None:
    source, storey_id = _scene(tmp_path, "d7n", 3, False)
    changeset = _changeset(source, storey_id, (family,))
    assignment = changeset["operations"][0]["semantic_assignments"][0]
    assignment.update(fact_key="attribute:Name", source_fact_key="attribute:Name", value="Explicit test name",
                      value_type="IfcLabel", ownership="occurrence_direct", applicability="conditional",
                      source_kind="explicit_value", source_ref="request:/name", derivation=None,
                      provenance=["request:/name"], authoring_action="set_attribute")
    output = tmp_path / "must-not-exist.ifc"
    result = _apply(source, output, changeset)
    assert not result["valid"] and not result["published"] and not output.exists()
    assert any(item["code"] == "STRUCTURAL_TYPE_AUTHORITY_REQUIRED" for item in result["issues"])


@pytest.mark.parametrize("family", ("beam", "column"))
def test_deterministic_member_id_collision_stays_blocking_with_multiple_relations(tmp_path: Path, family: str) -> None:
    source, storey_id = _scene(tmp_path, "d7n", 3, False)
    operation = _changeset(source, storey_id, (family,))["operations"][0]
    model = ifcopenshell.open(str(source))
    storey = model.by_guid(storey_id)
    existing_type = model.by_type(f"Ifc{family.title()}Type")[0]
    assignment = operation["semantic_assignments"][0]
    assignment.update(value=str(existing_type.GlobalId), source_kind="type_inherited",
                      source_ref=f"ifc:{existing_type.GlobalId}", derivation=None,
                      provenance=[f"ifc:{existing_type.GlobalId}"])
    parameters = _parameters(family)
    endpoints = ("start", "end") if family == "beam" else ("base", "top")
    duplicate = create_straight_rectangular_member(
        model=model, occurrence_class=f"Ifc{family.title()}",
        occurrence_global_id=deterministic_global_id(operation, family), operation_id="pre-existing-collision",
        axis_start_mm=tuple(parameters["axis"][endpoints[0]][key] + (100000 if key == "x_mm" else 0)
                            for key in ("x_mm", "y_mm", "z_mm")),
        axis_end_mm=tuple(parameters["axis"][endpoints[1]][key] + (100000 if key == "x_mm" else 0)
                          for key in ("x_mm", "y_mm", "z_mm")),
        section=deepcopy(parameters["section"]), storey=storey,
        owner_history=storey.OwnerHistory, representation_context=body_context(model),
    )["occurrence"]
    relation = storey.ContainsElements[-1]
    relation.RelatedElements = (*relation.RelatedElements, duplicate)
    model.write(str(source))
    output = tmp_path / "must-not-exist.ifc"
    changeset = _changeset(source, storey_id, (family,))
    changeset["operations"][0] = operation
    result = _apply(source, output, changeset)
    assert not result["valid"] and not result["published"] and not output.exists()
    assert any(item["code"] == "DETERMINISTIC_GLOBAL_ID_COLLISION" for item in result["issues"])


def test_mixed_structural_failure_rolls_back_created_containment_and_entire_transaction(tmp_path: Path) -> None:
    source, storey_id = _scene(tmp_path, "vvo", 3, True)
    changeset = _changeset(source, storey_id, ("beam", "column"))
    registry = OperationRegistry()
    registry.register(beam_operation_definition())
    registry.register(replace(column_operation_definition(), postcondition_checker=lambda **kwargs: {
        "valid": False, "checks": [],
        "issues": [{"code": "INJECTED_COLUMN_POSTCONDITION_FAILURE", "path": "/postconditions", "message": "injected"}],
    }))
    output = tmp_path / "must-not-exist.ifc"
    result = _apply(source, output, changeset, registry)
    assert not result["valid"] and not result["published"] and not output.exists()
    assert [item["code"] for item in result["issues"]] == ["INJECTED_COLUMN_POSTCONDITION_FAILURE"]


def test_mixed_beam_and_column_have_separate_single_ownership_without_rewriting_old_relations(tmp_path: Path) -> None:
    source, storey_id = _scene(tmp_path, "vvo", 3, True)
    before = ifcopenshell.open(str(source))
    relations = {str(item.GlobalId): item.to_string() for item in before.by_type("IfcRelContainedInSpatialStructure")}
    output = tmp_path / "repaired.ifc"
    result = _apply(source, output, _changeset(source, storey_id, ("beam", "column")))
    assert result["valid"] and result["published"], result["issues"]
    reopened = ifcopenshell.open(str(output))
    assert len(reopened.by_guid(storey_id).ContainsElements) == 5
    for guid, original in relations.items():
        assert reopened.by_guid(guid).to_string() == original
    for item in result["operations"]:
        family = item["operation_type"].removeprefix("add_")
        occurrence_id = next(change["global_id"] for change in item["changes"]["created"] if change["role"] == family)
        occurrence = reopened.by_guid(occurrence_id)
        assert len(occurrence.ContainedInStructure) == 1
        assert occurrence.ContainedInStructure[0].RelatedElements == (occurrence,)
        assert str(occurrence.ContainedInStructure[0].RelatingStructure.GlobalId) == storey_id
