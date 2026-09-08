"""Frozen deterministic failure family: exact Type must not erase requests.

Scope: Stage 1 -> production resolution and public pause/resume. These are
offline regression cases, not a capability evaluation or accepted Proof.
"""
from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import replace
from pathlib import Path

import ifcopenshell
import pytest

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.index_store import SQLiteIndexRepository
from text2ifc_ifc_repair.indexer import build_ifc_index
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.repair_intent import RepairIntent
from text2ifc_ifc_repair.resolution_flow import resolve_repair_intent
from text2ifc_presentation import AppearanceSpec, assign_item_appearance

VERSION = "text2ifc/ifc-repair-intent/0.10"
SOURCE = {"source_kind": "user_request", "reference": "request:/text", "excerpt": "Use exact Type; preserve other objects."}
TYPE_ID = "0000000000000000000003"
STOREY_ID = "0000000000000000000002"


def _source(path: Path, family="beam", duplicate_material=False):
    model = ifcopenshell.file(schema="IFC2X3")
    model.create_entity("IfcProject", GlobalId="0000000000000000000001", Name="Offline fixture")
    model.create_entity("IfcBuildingStorey", GlobalId=STOREY_ID, Name="Level 1")
    type_object = model.create_entity("IfcBeamType" if family == "beam" else "IfcColumnType", GlobalId=TYPE_ID, Name="Exact type", PredefinedType="NOTDEFINED")
    material = model.create_entity("IfcMaterial", Name="Steel")
    model.create_entity("IfcRelAssociatesMaterial", GlobalId="0000000000000000000004", RelatedObjects=[type_object], RelatingMaterial=material)
    if duplicate_material:
        model.create_entity("IfcMaterial", Name="Steel")
    prop = model.create_entity("IfcPropertySingleValue", Name="LoadBearing", NominalValue=model.create_entity("IfcBoolean", True))
    pset = model.create_entity("IfcPropertySet", GlobalId="0000000000000000000005", Name="Pset_BeamCommon" if family == "beam" else "Pset_ColumnCommon", HasProperties=[prop])
    type_object.HasPropertySets = [pset]
    origin = model.create_entity("IfcAxis2Placement3D", Location=model.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.)))
    block = model.create_entity("IfcBlock", Position=origin, XLength=1., YLength=1., ZLength=1.)
    context = model.create_entity("IfcGeometricRepresentationContext", ContextType="Model", CoordinateSpaceDimension=3, Precision=1.e-5, WorldCoordinateSystem=origin)
    rep = model.create_entity("IfcShapeRepresentation", ContextOfItems=context, RepresentationIdentifier="Body", RepresentationType="CSG", Items=[block])
    type_object.RepresentationMaps = [model.create_entity("IfcRepresentationMap", MappingOrigin=origin, MappedRepresentation=rep)]
    assign_item_appearance(model, item=block, spec=AppearanceSpec("blue", .1, .2, .3))
    model.write(str(path))


def _document(*, family="beam", color=None, material=None, value=None, scope=None, exact=True, version=VERSION):
    op = {
        "operation_id": "member-1", "operation_type": f"add_{family}",
        "routing_intent": {"component_family": family, "action": "add", "operation_profile": f"{family}.add.v0.3", "source": SOURCE},
        "target_query": {"schema_version": "text2ifc/ifc-target-query/0.1", "allowed_ifc_classes": ["IfcBuildingStorey"], "global_id": STOREY_ID},
        "parameters": {"axis": {"start": {"x_mm": 0, "y_mm": 0, "z_mm": 3000}, "end": {"x_mm": 4000, "y_mm": 0, "z_mm": 3000}}, "section": {"shape": "rectangle", "width_mm": 300, "height_mm": 500}},
        "attribute_intents": [], "property_intents": [], "quantity_intents": [], "semantic_bundle_refs": [], "occurrence_reuse_intent": None,
        "prototype_intent": {"reference_kind": "global_id", "reference": TYPE_ID, "source": SOURCE} if exact else None,
        "appearance_intent": None, "provenance": [SOURCE],
    }
    if family == "column":
        op["parameters"] = {"axis": {"base": {"x_mm": 0, "y_mm": 0, "z_mm": 0}, "top": {"x_mm": 0, "y_mm": 0, "z_mm": 3000}}, "section": {"shape": "rectangle", "width_mm": 400, "depth_mm": 500, "orientation": {"x": 1, "y": 0}}}
    if color is not None:
        op["appearance_intent"] = {"intent_kind": "surface_color_rgb", "red": color[0], "green": color[1], "blue": color[2], "source": SOURCE}
    if material is not None:
        op["attribute_intents"] = [{"intent_kind": "material", "name": "Material", "value": material, "source": SOURCE}]
    if value is not None:
        op["property_intents"] = [{"intent_kind": "exact_property", "set_name": "Pset_BeamCommon" if family == "beam" else "Pset_ColumnCommon", "property_name": "LoadBearing", "raw_value": value, "raw_unit": None, "requested_value_type": "IfcBoolean", "scope": scope, "source": SOURCE}]
    return {"schema_version": version, "request_id": "offline-conflict", "source_request_hash": "sha256:" + "a" * 64, "model_fingerprint": "sha256:" + "b" * 64, "prompt_fingerprint": "sha256:" + "c" * 64, "operations": [op], "unsupported_requests": [], "semantic_bundles": [], "provenance": [SOURCE]}


def _resolve(tmp_path, document, *, duplicate_material=False):
    source = tmp_path / "source.ifc"
    family = document["operations"][0]["routing_intent"]["component_family"]
    _source(source, family, duplicate_material)
    before = source.read_bytes()
    index = tmp_path / "index.sqlite"
    metadata = build_ifc_index(source, index)
    # Preserve the baseline shape to reproduce the missing route independently
    # of registration (the additive shape is tested through the public API).
    version = document["schema_version"]
    document = {**document, "schema_version": "text2ifc/ifc-repair-intent/0.9"}
    registry = create_default_registry()
    intent = replace(RepairIntent.from_dict(document, registry=registry), schema_version=version)
    kwargs = {"expected_source_sha256": metadata.source_ifc_sha256, "operation_registry": registry}
    if "source_ifc_path" in inspect.signature(resolve_repair_intent).parameters:
        kwargs["source_ifc_path"] = source
    with SQLiteIndexRepository.open(index) as repository:
        result = resolve_repair_intent(intent, repository, **kwargs)
    assert source.read_bytes() == before
    return result


@pytest.mark.parametrize("family", ["beam", "column"])
@pytest.mark.parametrize("claims,reason", [
    ({"color": (.9, .1, .1)}, "EXACT_TYPE_APPEARANCE_CONFLICT"),
    ({"material": "Timber"}, "EXACT_TYPE_MATERIAL_CONFLICT"),
    ({"value": False}, "EXACT_TYPE_PROPERTY_CONFLICT"),
    ({"value": False, "scope": "type_owned"}, "TYPE_PROPERTY_MUTATION_DEFERRED"),
])
def test_exact_type_conflicts_pause_before_stage2(tmp_path, family, claims, reason):
    result = _resolve(tmp_path, _document(family=family, **claims))
    assert (result.status, result.reason_code) == ("clarification_required", reason)


@pytest.mark.parametrize("claims", [
    {}, {"color": (.1, .2, .3), "material": "Steel", "value": True},
    {"value": False, "scope": "occurrence_direct"},
    {"exact": False, "color": (.9, .1, .1), "material": "Timber", "value": False},
])
def test_compatible_and_explicit_instance_scope_do_not_force_type_clarification(tmp_path, claims):
    assert _resolve(tmp_path, _document(**claims)).status == "resolved"


def test_same_material_label_does_not_authorize_ambiguous_identity(tmp_path):
    result = _resolve(tmp_path, _document(material="Steel"), duplicate_material=True)
    assert result.reason_code == "EXACT_TYPE_MATERIAL_IDENTITY_AMBIGUOUS"
    assert result.status == "clarification_required"


def test_published_09_retains_historical_priority(tmp_path):
    result = _resolve(tmp_path, _document(color=(.9, .1, .1), version="text2ifc/ifc-repair-intent/0.9"))
    assert result.status == "resolved"


def test_public_api_conflict_resume_uses_new_contract_and_never_calls_stage2(tmp_path):
    source = tmp_path / "caller.ifc"
    _source(source)
    before = source.read_bytes()
    class Provider:
        calls = 0
        def generate_candidate(self, **kwargs):
            self.calls += 1
            document = _document(color=(.9, .1, .1))
            body = {key: document[key] for key in ("operations", "unsupported_requests", "semantic_bundles", "provenance")}
            body["schema_version"] = "text2ifc/ifc-repair-intent-body/0.10"
            return ProviderOutput(text=json.dumps(body), metadata={"provider": "offline-frozen", "model": "test"})
    provider = Provider()
    def forbidden_stage2(**kwargs):
        pytest.fail("conflicting exact Type request reached Stage2")
    api = RepairAPI(tmp_path / "runs", provider=provider, changeset_stage=forbidden_stage2)
    pending = api.start(source, "Use exact Type; RGB 0.9, 0.1, 0.1.")
    assert pending.status == "clarification_required", pending
    assert "EXACT_TYPE_APPEARANCE_CONFLICT" in pending.clarification.question
    resumed = api.continue_with_answer(pending.run_id, clarification_id=pending.clarification.clarification_id, expected_state_version=pending.state_version, answer={"kind": "add_detail", "detail": "Keep the requested color and exact Type."})
    assert resumed.status == "clarification_required"
    assert provider.calls == 2
    assert source.read_bytes() == before
    assert not list((tmp_path / "runs").rglob("successful-repaired.ifc"))
