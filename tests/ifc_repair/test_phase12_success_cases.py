from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import ifcopenshell
import ifcopenshell.guid
import ifcopenshell.util.unit
import pytest
from jsonschema import Draft202012Validator
from text2ifc_agent.prompt_registry import load_prompt_registry
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.prompt_profiles import (
    compact_profile_catalog,
    load_prompt_profiles,
    select_prompt_profiles,
)

from scripts.ifc_repair.run_phase12_public_structural_repair import (
    run_public_repair,
)
from scripts.ifc_repair.run_phase12_live_uat import DEFAULT_CASES as FROZEN_LIVE_CASES
from scripts.ifc_repair import validate_success_cases as success_validator
from scripts.ifc_repair.validate_success_cases import (
    ProofValidationResult,
    validate_success_case_collection,
)


ROOT = Path(__file__).resolve().parents[2]
D7N = ROOT / "dataset" / "ifc" / "test" / "d7n.ifc"
STOREY_ID = "0K_MqVdrL0JOCMi_GblRwJ"
CASE_ID = "phase12-d7n-beam-column-strict-proof"
CASE_PATH = Path("structural") / "single" / CASE_ID
BASE_DAMAGE_CASE_ID = "phase12-d7n-beam-column-atomic"
BASE_DAMAGE_CASE = (
    ROOT
    / "dataset/processed/proof/ifc-repair-success-cases"
    / "structural/batch"
    / BASE_DAMAGE_CASE_ID
)
LIVE_CASE_ID = "phase12-live-deepseek-complete"
LIVE_CASE_PATH = Path("structural") / "live" / LIVE_CASE_ID
CURATOR_SCRIPT = ROOT / "scripts/ifc_repair/curate_phase12_live_proof.py"
STAGE15_TEMPLATE_HASH = load_prompt_registry()[
    "ifc-property-resolution.v0.2"
]["sha256"]


def _curator_module():
    spec = importlib.util.spec_from_file_location(
        "phase12_live_curator_success_cases", CURATOR_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_payload_sha256(value: Any) -> str:
    rendered = (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )
    return "sha256:" + hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _canonical_transport_sha256(value: Any) -> str:
    rendered = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _beam_parameters() -> dict[str, Any]:
    return {
        "axis": {
            "start": {"x_mm": 100000, "y_mm": 100000, "z_mm": 3000},
            "end": {"x_mm": 103000, "y_mm": 104000, "z_mm": 3000},
        },
        "section": {"shape": "rectangle", "width_mm": 300, "height_mm": 500},
    }


def _column_parameters() -> dict[str, Any]:
    return {
        "axis": {
            "base": {"x_mm": 103000, "y_mm": 104000, "z_mm": 0},
            "top": {"x_mm": 103000, "y_mm": 104000, "z_mm": 6000},
        },
        "section": {
            "shape": "rectangle",
            "width_mm": 400,
            "depth_mm": 600,
            "orientation": {"x": 0, "y": 1},
        },
    }


def _public_bundle() -> dict[str, Any]:
    def load_bearing(family: str, index: int) -> dict[str, Any]:
        set_name = (
            "Pset_BeamCommon" if family == "beam" else "Pset_ColumnCommon"
        )
        return {
            "intent_kind": "exact_property",
            "set_name": set_name,
            "property_name": "LoadBearing",
            "raw_value": True,
            "raw_unit": None,
            "requested_value_type": "IfcBoolean",
            "scope": "occurrence_direct",
            "source": {
                "source_kind": "user_request",
                "reference": f"request:/operations/{index}/properties/0",
                "excerpt": f"{set_name}.LoadBearing=true",
            },
        }

    return {
        "schema_version": "text2ifc/phase12-public-structural-request/0.1",
        "case_id": CASE_ID,
        "request": (
            "Add one 300 by 500 mm horizontal beam and one 400 by 600 mm "
            "vertical column on the selected storey, and set LoadBearing=true "
            "on both occurrences."
        ),
        "operations": [
            {
                "operation_id": "proof-beam-1",
                "operation_type": "add_beam",
                "target_query": {
                    "schema_version": "text2ifc/ifc-target-query/0.1",
                    "allowed_ifc_classes": ["IfcBuildingStorey"],
                    "global_id": STOREY_ID,
                },
                "parameters": _beam_parameters(),
                "property_intents": [load_bearing("beam", 0)],
            },
            {
                "operation_id": "proof-column-1",
                "operation_type": "add_column",
                "target_query": {
                    "schema_version": "text2ifc/ifc-target-query/0.1",
                    "allowed_ifc_classes": ["IfcBuildingStorey"],
                    "global_id": STOREY_ID,
                },
                "parameters": _column_parameters(),
                "property_intents": [load_bearing("column", 1)],
            },
        ],
    }


def _role_for(path: Path) -> str:
    return {
        "original.ifc": "original_ground_truth",
        "damaged.ifc": "repair_input_ifc",
        "repaired.ifc": "published_repair_output",
        "request.txt": "user_request",
        "repair-intent.json": "stage1_repair_intent",
        "target-resolution.json": "deterministic_target_resolution",
        "changeset.json": "bound_changeset",
        "application.json": "application_result",
        "evaluation.json": "production_evaluation",
        "manifest.json": "source_run_manifest",
        "production-boundary.json": "production_input_boundary",
    }.get(path.name, "proof_artifact_" + path.stem.replace(".", "_"))


def _refresh_source_run_manifest(case_root: Path) -> None:
    """Keep runner-owned artifact hashes valid after a deliberate IFC edit."""

    manifest_path = case_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        return
    for name, entry in artifacts.items():
        artifact = case_root / name
        if artifact.is_file() and isinstance(entry, dict):
            entry["sha256"] = _sha256(artifact)
            entry["bytes"] = artifact.stat().st_size
    _write_json(manifest_path, manifest)


def _refresh_files(case_root: Path) -> None:
    entries = []
    for artifact in sorted(case_root.rglob("*")):
        if not artifact.is_file() or artifact.name in {"FILES.json", "REPORT.md"}:
            continue
        entries.append(
            {
                "path": artifact.relative_to(case_root).as_posix(),
                "role": _role_for(artifact),
                "sha256": _sha256(artifact),
                "size_bytes": artifact.stat().st_size,
            }
        )
    _write_json(case_root / "FILES.json", {"case_id": CASE_ID, "files": entries})


def _collection_manifest(collection_root: Path) -> None:
    _write_json(
        collection_root / "manifest.json",
        {
            "case_count": 1,
            "cases": [
                {
                    "case_id": CASE_ID,
                    "status": "accepted",
                    "provider_evidence_mode": "offline_bound_deterministic",
                    "operation_count": 2,
                    "operation_types": ["add_beam", "add_column"],
                    "original_ifc": (CASE_PATH / "original.ifc").as_posix(),
                    "damaged_ifc": (CASE_PATH / "damaged.ifc").as_posix(),
                    "repaired_ifc": (CASE_PATH / "repaired.ifc").as_posix(),
                    "report": (CASE_PATH / "REPORT.md").as_posix(),
                    "files": (CASE_PATH / "FILES.json").as_posix(),
                }
            ],
        },
    )


@pytest.fixture(scope="module")
def structural_proof_base(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A genuine public-run Beam+Column proof, built only once per module."""

    base = tmp_path_factory.mktemp("phase12-structural-proof")
    bundle = base / "request.json"
    _write_json(bundle, _public_bundle())
    run_public_repair(
        damaged_ifc=D7N,
        public_request_bundle=bundle,
        output_root=base / "runner-output",
    )
    return base / "runner-output"


def _proof_collection(tmp_path: Path, base: Path) -> tuple[Path, Path]:
    collection = tmp_path / "proof"
    case_root = collection / CASE_PATH
    shutil.copytree(base, case_root)
    shutil.copy2(D7N, case_root / "original.ifc")
    (case_root / "REPORT.md").write_text("# Phase 12 strict proof\n", encoding="utf-8")
    _refresh_source_run_manifest(case_root)
    _refresh_files(case_root)
    _collection_manifest(collection)
    return collection, case_root


def _created_id(case_root: Path, role: str) -> str:
    application = json.loads((case_root / "application.json").read_text(encoding="utf-8"))
    matches = [
        item["global_id"]
        for operation in application["operations"]
        for item in operation["changes"]["created"]
        if item.get("role") == role
    ]
    assert len(matches) == 1
    return str(matches[0])


def _rewrite_ifc(case_root: Path, mutate) -> None:
    path = case_root / "repaired.ifc"
    model = ifcopenshell.open(str(path))
    mutate(model)
    model.write(str(path))
    _refresh_source_run_manifest(case_root)
    _refresh_files(case_root)


def _assert_blocked(collection: Path, check_id: str) -> None:
    case_root = collection / CASE_PATH
    saved = json.loads(
        (case_root / "evaluation.json").read_text(encoding="utf-8")
    )
    assert saved["status"] == "passed"
    assert saved["complete_repair_success"] is True
    result = validate_success_case_collection(collection)
    assert result.status == "failed"
    assert len(result.errors) == 1
    assert check_id in result.errors[0]


def test_valid_beam_column_public_proof_is_strictly_recomputed(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, _ = _proof_collection(tmp_path, structural_proof_base)

    result = validate_success_case_collection(collection)

    assert result.status == "passed", result.errors
    assert result.reopened_ifc_count == 3
    assert result.independently_recomputed_case_count == 1
    assert result.cases[0]["audit_coverage"] == "strict_recomputed"
    assert (
        result.cases[0]["structural_audit_coverage"]
        == "strict_structural_recomputed"
    )
    assert result.cases[0]["independent_l1_operation_count"] == 2
    assert result.cases[0]["independent_l2_operation_count"] == 2


def test_saved_success_cannot_mask_endpoint_error_beyond_five_mm(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    beam_id = _created_id(case_root, "beam")

    def move_endpoint(model: Any) -> None:
        beam = model.by_guid(beam_id)
        coordinates = list(beam.ObjectPlacement.RelativePlacement.Location.Coordinates)
        coordinates[0] += 0.0051 / ifcopenshell.util.unit.calculate_unit_scale(model)
        beam.ObjectPlacement.RelativePlacement.Location.Coordinates = tuple(coordinates)

    _rewrite_ifc(case_root, move_endpoint)
    _assert_blocked(collection, "l1.structural.axis-points")


def test_saved_success_cannot_mask_second_type_relationship(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    beam_id = _created_id(case_root, "beam")

    def duplicate_type_relation(model: Any) -> None:
        beam = model.by_guid(beam_id)
        existing = next(
            relation
            for relation in beam.IsDefinedBy
            if relation.is_a("IfcRelDefinesByType")
        )
        model.create_entity(
            "IfcRelDefinesByType",
            GlobalId=ifcopenshell.guid.new(),
            RelatedObjects=[beam],
            RelatingType=existing.RelatingType,
        )

    _rewrite_ifc(case_root, duplicate_type_relation)
    _assert_blocked(collection, "l1.structural.relationships")


def test_saved_success_cannot_mask_missing_structural_type(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    column_id = _created_id(case_root, "column")

    def remove_type_relation(model: Any) -> None:
        column = model.by_guid(column_id)
        relation = next(
            item
            for item in column.IsDefinedBy
            if item.is_a("IfcRelDefinesByType")
        )
        model.remove(relation)

    _rewrite_ifc(case_root, remove_type_relation)
    _assert_blocked(collection, "l1.structural.relationships")


def test_saved_success_cannot_mask_partial_atomic_output(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    column_id = _created_id(case_root, "column")

    def remove_one_bound_operation(model: Any) -> None:
        model.remove(model.by_guid(column_id))

    _rewrite_ifc(case_root, remove_one_bound_operation)
    _assert_blocked(collection, "l1.structural.product")


def test_saved_success_cannot_mask_requested_pset_semantic_defect(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    beam_id = _created_id(case_root, "beam")

    def corrupt_requested_value(model: Any) -> None:
        beam = model.by_guid(beam_id)
        pset = next(
            relation.RelatingPropertyDefinition
            for relation in beam.IsDefinedBy
            if relation.is_a("IfcRelDefinesByProperties")
            and relation.RelatingPropertyDefinition.is_a("IfcPropertySet")
            and relation.RelatingPropertyDefinition.Name == "Pset_BeamCommon"
        )
        prop = next(item for item in pset.HasProperties if item.Name == "LoadBearing")
        prop.NominalValue = model.create_entity("IfcBoolean", False)

    _rewrite_ifc(case_root, corrupt_requested_value)
    _assert_blocked(
        collection,
        "beam.pset:pset:Pset_BeamCommon.LoadBearing",
    )


def test_saved_success_cannot_mask_generated_type_contract_defect(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    beam_id = _created_id(case_root, "beam")

    def corrupt_generated_type(model: Any) -> None:
        beam = model.by_guid(beam_id)
        relation = next(
            item
            for item in beam.IsDefinedBy
            if item.is_a("IfcRelDefinesByType")
        )
        relation.RelatingType.Name = "forged saved-success type"

    _rewrite_ifc(case_root, corrupt_generated_type)
    _assert_blocked(collection, "l2.structural.type-authority")


@pytest.mark.parametrize(
    ("mutate_files", "check_id"),
    (
        (
            lambda files: files["files"][0].pop("sha256"),
            "proof.hash.required",
        ),
        (
            lambda files: files["files"][0].update({"sha256": "sha256:" + "0" * 64}),
            "proof.hash.sha256",
        ),
    ),
)
def test_missing_or_stale_proof_hash_is_a_specific_blocking_check(
    tmp_path: Path,
    structural_proof_base: Path,
    mutate_files,
    check_id: str,
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    files_path = case_root / "FILES.json"
    files = json.loads(files_path.read_text(encoding="utf-8"))
    mutate_files(files)
    _write_json(files_path, files)

    _assert_blocked(collection, check_id)


def test_indexed_structural_proof_artifact_cannot_be_missing(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    (case_root / "target-resolution.json").unlink()

    _assert_blocked(collection, "proof.artifact.missing")


def test_rehashed_request_cannot_spoof_bound_structural_provenance(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    (case_root / "request.txt").write_text(
        "A different public request that was never bound to this repair.\n",
        encoding="utf-8",
    )
    _refresh_source_run_manifest(case_root)
    _refresh_files(case_root)

    _assert_blocked(
        collection,
        "l0.structural.changeset-audit:SOURCE_REQUEST_HASH_MISMATCH",
    )


def test_rehashed_intent_cannot_spoof_bound_structural_operation_identity(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    intent_path = case_root / "repair-intent.json"
    intent = json.loads(intent_path.read_text(encoding="utf-8"))
    intent["operations"][0]["operation_id"] = "forged-intent-operation"
    _write_json(intent_path, intent)
    _refresh_source_run_manifest(case_root)
    _refresh_files(case_root)

    _assert_blocked(collection, "l0.structural.provenance:intent_operation_identity")


def test_rehashed_resolution_cannot_spoof_structural_model_binding(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    resolution_path = case_root / "target-resolution.json"
    resolution = json.loads(resolution_path.read_text(encoding="utf-8"))
    resolution["source_ifc_sha256"] = "sha256:" + "0" * 64
    _write_json(resolution_path, resolution)
    _refresh_source_run_manifest(case_root)
    _refresh_files(case_root)

    _assert_blocked(collection, "l0.structural.provenance:resolution_model_hash")


def test_duplicate_requested_pset_relationship_is_not_collapsed_to_a_set(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    beam_id = _created_id(case_root, "beam")

    def duplicate_requested_pset(model: Any) -> None:
        beam = model.by_guid(beam_id)
        source = next(
            relation.RelatingPropertyDefinition
            for relation in beam.IsDefinedBy
            if relation.is_a("IfcRelDefinesByProperties")
            and relation.RelatingPropertyDefinition.is_a("IfcPropertySet")
            and relation.RelatingPropertyDefinition.Name == "Pset_BeamCommon"
        )
        duplicate = model.create_entity(
            "IfcPropertySet",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=source.OwnerHistory,
            Name=source.Name,
            HasProperties=[
                model.create_entity(
                    "IfcPropertySingleValue",
                    Name="LoadBearing",
                    NominalValue=model.create_entity("IfcBoolean", True),
                )
            ],
        )
        model.create_entity(
            "IfcRelDefinesByProperties",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=source.OwnerHistory,
            RelatedObjects=[beam],
            RelatingPropertyDefinition=duplicate,
        )

    _rewrite_ifc(case_root, duplicate_requested_pset)
    _assert_blocked(collection, "l2.structural.semantic-scope")


def test_rehashed_manifest_and_ifc_cannot_invent_unrequested_semantic_value(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    manifest_path = case_root / "semantic-manifests.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    changeset_path = case_root / "changeset.json"
    changeset = json.loads(changeset_path.read_text(encoding="utf-8"))
    for document in manifest["manifests"]:
        if document["operation_id"] == "proof-beam-1":
            next(
                item
                for item in document["assignments"]
                if item["fact_key"] == "pset:Pset_BeamCommon.LoadBearing"
            )["value"] = False
    for operation in changeset["operations"]:
        if operation["operation_id"] == "proof-beam-1":
            next(
                item
                for item in operation["semantic_assignments"]
                if item["fact_key"] == "pset:Pset_BeamCommon.LoadBearing"
            )["value"] = False
    _write_json(manifest_path, manifest)
    changeset["semantic_manifest_sha256"] = _canonical_payload_sha256(manifest)
    _write_json(changeset_path, changeset)
    beam_id = _created_id(case_root, "beam")

    def match_the_forged_manifest(model: Any) -> None:
        beam = model.by_guid(beam_id)
        pset = next(
            relation.RelatingPropertyDefinition
            for relation in beam.IsDefinedBy
            if relation.is_a("IfcRelDefinesByProperties")
            and relation.RelatingPropertyDefinition.Name == "Pset_BeamCommon"
        )
        prop = next(item for item in pset.HasProperties if item.Name == "LoadBearing")
        prop.NominalValue = model.create_entity("IfcBoolean", False)

    _rewrite_ifc(case_root, match_the_forged_manifest)
    _assert_blocked(collection, "semantic_authority_replay")


def test_relationship_extension_cannot_hide_owner_history_mutation(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    beam_id = _created_id(case_root, "beam")

    def mutate_shared_owner_history(model: Any) -> None:
        beam = model.by_guid(beam_id)
        relation = beam.ContainedInStructure[0]
        owner_history = model.create_entity(
            "IfcOwnerHistory", *tuple(relation.OwnerHistory)
        )
        owner_history.LastModifiedDate = 1
        relation.OwnerHistory = owner_history

    _rewrite_ifc(case_root, mutate_shared_owner_history)
    _assert_blocked(collection, "l0.structural.preservation:modified_root")


def test_undeclared_ifcroot_preservation_drift_is_blocking(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)

    def add_unrelated_root(model: Any) -> None:
        project = model.by_type("IfcProject")[0]
        model.create_entity(
            "IfcBuildingElementProxy",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=project.OwnerHistory,
            Name="undeclared preservation drift",
        )

    _rewrite_ifc(case_root, add_unrelated_root)
    _assert_blocked(collection, "l0.structural.preservation")


def test_private_gold_input_boundary_drift_is_blocking(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    boundary_path = case_root / "production-boundary.json"
    boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
    boundary["original_ifc_supplied"] = True
    _write_json(boundary_path, boundary)
    _refresh_source_run_manifest(case_root)
    _refresh_files(case_root)

    _assert_blocked(collection, "l0.structural.isolation")


def test_camel_case_private_gold_key_is_blocking(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    boundary_path = case_root / "production-boundary.json"
    boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
    boundary["originalIfcPath"] = "unavailable.ifc"
    _write_json(boundary_path, boundary)
    _refresh_source_run_manifest(case_root)
    _refresh_files(case_root)

    _assert_blocked(collection, "l0.structural.isolation:private_field")


def test_synthetic_fallback_cannot_be_promoted_by_saved_success(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    source_manifest_path = case_root / "manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_manifest["synthetic_fallback_used"] = True
    _write_json(source_manifest_path, source_manifest)
    _refresh_files(case_root)

    _assert_blocked(collection, "l0.structural.no-fallback")


def test_collection_cannot_relabel_live_source_run_as_offline(
    tmp_path: Path, structural_proof_base: Path
) -> None:
    collection, case_root = _proof_collection(tmp_path, structural_proof_base)
    source_manifest_path = case_root / "manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_manifest["provider_evidence_mode"] = "live"
    _write_json(source_manifest_path, source_manifest)
    _refresh_files(case_root)

    _assert_blocked(
        collection,
        "l0.structural.provenance:provider_evidence_mode_binding",
    )


def _live_attempt(
    *,
    case_id: str,
    stage: str,
    ordinal: int,
    parent: str | None,
    lineage: str,
    response_document: Mapping[str, Any],
) -> dict[str, Any]:
    attempt_id = f"{case_id}:{stage}:{ordinal:03d}"
    request = {"model": "deepseek-chat", "messages": [f"{case_id}:{stage}"]}
    response = {
        "id": f"response-{case_id}-{stage}-{ordinal}",
        "content": json.dumps(
            response_document,
            ensure_ascii=False,
            sort_keys=True,
        ),
    }
    usage = {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
    }
    selected_profiles = {
        "complete": ["beam.add.v0.3", "column.add.v0.3"],
        "clarification-resume": ["column.add.v0.3"],
        "window-semantic-canary": ["occurrence.set-properties"],
        "program-guard": ["beam.add.v0.3"],
    }[case_id]
    if stage == "stage1":
        registry = create_default_registry()
        catalog = compact_profile_catalog(
            load_prompt_profiles(),
            include_profile_ids=[
                str(registry.require(operation_type).prompt_profile_id)
                for operation_type in registry.operation_types
            ],
        )
        profile_ids = [str(item["profile_id"]) for item in catalog]
        profile_versions = [str(item["profile_version"]) for item in catalog]
        profile_hashes = [str(item["profile_hash"]) for item in catalog]
        few_shot_ids: list[str] = []
        few_shot_hashes: list[str] = []
    elif stage == "stage2":
        selection = select_prompt_profiles(selected_profiles).to_dict()
        profile_ids = selection["profile_ids"]
        profile_versions = [
            str(profile["profile_version"])
            for profile in selection["profiles"]
        ]
        profile_hashes = selection["profile_hashes"]
        few_shot_ids = selection["few_shot_ids"]
        few_shot_hashes = selection["few_shot_hashes"]
    else:
        profile_ids = []
        profile_versions = []
        profile_hashes = []
        few_shot_ids = []
        few_shot_hashes = []
    few_shot_bindings = [
        {"few_shot_id": few_shot_id, "few_shot_hash": few_shot_hash}
        for few_shot_id, few_shot_hash in zip(
            few_shot_ids,
            few_shot_hashes,
            strict=True,
        )
    ]
    return {
        "attempt_id": attempt_id,
        "parent_attempt_id": parent,
        "case_id": case_id,
        "lineage": lineage,
        "stage": stage,
        "ordinal": ordinal,
        "stage_attempt": 1,
        "correction_reason": None,
        "evidence_class": "live",
        "http_status": 200,
        "fallback_flags": {
            "cached": False,
            "hand_authored": False,
            "prerecorded": False,
            "synthetic": False,
        },
        "private_evidence_detected": False,
        "provider": "deepseek-openai-compatible",
        "model": "deepseek-chat",
        "usage": usage,
        "raw_request_sha256": _canonical_transport_sha256(request),
        "raw_response_sha256": _canonical_transport_sha256(response),
        "request_sha256": _canonical_transport_sha256(request),
        "response_sha256": _canonical_transport_sha256(response),
        "request": request,
        "response": response,
        "metadata": {
            "provider": "deepseek-openai-compatible",
            "model": "deepseek-chat",
            "evidence_class": "live",
            "response_id": response["id"],
            "transport_attempts": 1,
            "usage": usage,
        },
        "error": None,
        "template_id": (
            "ifc-property-resolution.v0.2"
            if stage == "property_resolution"
            else None
        ),
        "template_hash": (
            STAGE15_TEMPLATE_HASH if stage == "property_resolution" else None
        ),
        "profile_ids": profile_ids,
        "profile_versions": profile_versions,
        "profile_hashes": profile_hashes,
        "few_shot_ids": few_shot_ids,
        "few_shot_hashes": few_shot_hashes,
        "few_shot_bindings": few_shot_bindings,
    }


def _upgrade_live_intent(intent: Mapping[str, Any]) -> dict[str, Any]:
    upgraded = json.loads(json.dumps(intent))
    upgraded["schema_version"] = "text2ifc/ifc-repair-intent/0.8"
    upgraded["unsupported_requests"] = []
    for operation in upgraded.get("operations", ()):
        routing = operation.get("routing_intent")
        if not isinstance(routing, dict):
            continue
        if operation.get("operation_type") == "add_beam":
            routing["operation_profile"] = "beam.add.v0.3"
        elif operation.get("operation_type") == "add_column":
            routing["operation_profile"] = "column.add.v0.3"
    return upgraded


def _provider_draft(changeset: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/ifc-repair-changeset-draft/0.2",
        "draft_id": "draft-live-proof",
        **{
            key: changeset[key]
            for key in (
                "base_model_fingerprint",
                "source_request_hash",
                "semantic_manifest_ref",
                "semantic_manifest_sha256",
                "scope",
                "evidence_refs",
                "preconditions",
                "postconditions",
                "operations",
            )
            if key in changeset
        },
    }


def _replace_live_response_document(
    attempt: dict[str, Any], document: Mapping[str, Any]
) -> None:
    response = dict(attempt["response"])
    response["content"] = json.dumps(document, ensure_ascii=False, sort_keys=True)
    attempt["response"] = response
    attempt["response_sha256"] = _canonical_transport_sha256(response)


def _live_result(
    *,
    intent: Mapping[str, Any],
    changeset: Mapping[str, Any],
    damaged_sha256: str,
) -> dict[str, Any]:
    intent_body = {
        "schema_version": "text2ifc/ifc-repair-intent-body/0.8",
        "operations": intent["operations"],
        "unsupported_requests": intent.get("unsupported_requests", []),
        "semantic_bundles": intent.get("semantic_bundles", []),
        "provenance": intent.get("provenance", []),
    }
    complete_stage1 = _live_attempt(
        case_id="complete",
        stage="stage1",
        ordinal=1,
        parent=None,
        lineage="initial",
        response_document=intent_body,
    )
    complete_property_1 = _live_attempt(
        case_id="complete",
        stage="property_resolution",
        ordinal=1,
        parent=complete_stage1["attempt_id"],
        lineage="initial",
        response_document={"selected_candidate_id": "beam-property"},
    )
    complete_property_2 = _live_attempt(
        case_id="complete",
        stage="property_resolution",
        ordinal=2,
        parent=complete_property_1["attempt_id"],
        lineage="initial",
        response_document={"selected_candidate_id": "column-property"},
    )
    draft = _provider_draft(changeset)
    complete_stage2 = _live_attempt(
        case_id="complete",
        stage="stage2",
        ordinal=1,
        parent=complete_property_2["attempt_id"],
        lineage="initial",
        response_document=draft,
    )
    clarification_stage1 = _live_attempt(
        case_id="clarification-resume",
        stage="stage1",
        ordinal=1,
        parent=None,
        lineage="initial",
        response_document=intent_body,
    )
    clarification_property = _live_attempt(
        case_id="clarification-resume",
        stage="property_resolution",
        ordinal=1,
        parent=clarification_stage1["attempt_id"],
        lineage="initial",
        response_document={"selected_candidate_id": None},
    )
    resumed_stage2 = _live_attempt(
        case_id="clarification-resume",
        stage="stage2",
        ordinal=1,
        parent=clarification_property["attempt_id"],
        lineage="clarification-resume",
        response_document=draft,
    )
    window_stage1 = _live_attempt(
        case_id="window-semantic-canary",
        stage="stage1",
        ordinal=1,
        parent=None,
        lineage="initial",
        response_document=intent_body,
    )
    window_property = _live_attempt(
        case_id="window-semantic-canary",
        stage="property_resolution",
        ordinal=1,
        parent=window_stage1["attempt_id"],
        lineage="initial",
        response_document={"selected_candidate_id": "window-property"},
    )
    window_stage2 = _live_attempt(
        case_id="window-semantic-canary",
        stage="stage2",
        ordinal=1,
        parent=window_property["attempt_id"],
        lineage="initial",
        response_document=draft,
    )
    guard_stage1 = _live_attempt(
        case_id="program-guard",
        stage="stage1",
        ordinal=1,
        parent=None,
        lineage="initial",
        response_document={"classification": "unsupported"},
    )
    strict = {
        "status": "passed",
        "l0_pass": True,
        "l1_pass": True,
        "l2_pass": True,
    }
    published = {
        "status": "succeeded",
        "reason_code": None,
        "run_id": "run-live-proof",
        "complete_repair_success": True,
        "successful_artifact_publishable": True,
        "strict_reopen_verification": strict,
        "artifacts": {
            "manifest": "publication/manifest.json",
            "evaluation": "evaluation.json",
            "successful_ifc": "repaired.ifc",
        },
    }
    frozen = {case.case_id: case for case in FROZEN_LIVE_CASES}
    request_fields = {
        case_id: {
            "request_sha256": "sha256:"
            + hashlib.sha256(case.request.encode("utf-8")).hexdigest(),
            "feedback_sha256": (
                None
                if case.feedback is None
                else "sha256:"
                + hashlib.sha256(case.feedback.encode("utf-8")).hexdigest()
            ),
        }
        for case_id, case in frozen.items()
    }
    cases = [
        {
            "case_id": "complete",
            **request_fields["complete"],
            "status": "passed",
            "final": published,
            "attempts": [
                complete_stage1,
                complete_property_1,
                complete_property_2,
                complete_stage2,
            ],
            "transport_calls": 4,
            "transport_calls_by_stage": {
                "stage1": 1,
                "property_resolution": 2,
                "stage2": 1,
            },
            "synthetic_fallback_used": False,
            "live_evidence_pass": True,
            "private_evidence_detected": False,
            "contract_pass": True,
            "proof_acceptance_eligible": False,
            "proof_validation_status": "pending_plan_12_14",
        },
        {
            "case_id": "clarification-resume",
            **request_fields["clarification-resume"],
            "status": "passed",
            "final": {
                **published,
                "clarification_answer_applied": True,
                "initial": {
                    "status": "clarification_required",
                    "complete_repair_success": False,
                    "successful_artifact_publishable": False,
                },
                "clarification": {
                    "clarification_id": "clarification-001",
                    "reason_code": "property_resolution",
                    "question": "Select the intended IFC property.",
                    "answer_modes": ["select_candidate", "cancel"],
                },
            },
            "attempts": [
                clarification_stage1,
                clarification_property,
                resumed_stage2,
            ],
            "transport_calls": 3,
            "transport_calls_by_stage": {
                "stage1": 1,
                "property_resolution": 1,
                "stage2": 1,
            },
            "synthetic_fallback_used": False,
            "live_evidence_pass": True,
            "private_evidence_detected": False,
            "contract_pass": True,
            "proof_acceptance_eligible": False,
            "proof_validation_status": "pending_plan_12_14",
        },
        {
            "case_id": "window-semantic-canary",
            **request_fields["window-semantic-canary"],
            "status": "passed",
            "final": dict(published),
            "attempts": [window_stage1, window_property, window_stage2],
            "transport_calls": 3,
            "transport_calls_by_stage": {
                "stage1": 1,
                "property_resolution": 1,
                "stage2": 1,
            },
            "synthetic_fallback_used": False,
            "live_evidence_pass": True,
            "private_evidence_detected": False,
            "contract_pass": True,
            "proof_acceptance_eligible": False,
            "proof_validation_status": "pending_plan_12_14",
        },
        {
            "case_id": "program-guard",
            **request_fields["program-guard"],
            "status": "passed",
            "final": {
                "status": "unsupported",
                "reason_code": "STRUCTURAL_ANALYSIS_UNSUPPORTED",
                "complete_repair_success": False,
                "successful_artifact_publishable": False,
                "program_guard_evidence": {
                    "source_reference": str(
                        BASE_DAMAGE_CASE / "damaged.ifc"
                    ),
                    "source_sha256_before": damaged_sha256,
                    "source_sha256_after": damaged_sha256,
                    "source_unchanged": True,
                    "stage2_attempts": 0,
                    "candidate_output_paths": [],
                    "mutation_attempted": False,
                },
            },
            "attempts": [guard_stage1],
            "transport_calls": 1,
            "transport_calls_by_stage": {
                "stage1": 1,
                "property_resolution": 0,
                "stage2": 0,
            },
            "synthetic_fallback_used": False,
            "live_evidence_pass": True,
            "private_evidence_detected": False,
            "contract_pass": True,
            "proof_acceptance_eligible": False,
            "proof_validation_status": "pending_plan_12_14",
        },
    ]
    return {
        "schema_version": "text2ifc/phase12-live-uat/0.1",
        "status": "passed",
        "evidence_mode": "live",
        "execution_mode": "production_live",
        "provider_evidence_mode": "live",
        "runner_contract_eligible": True,
        "acceptance_eligible": False,
        "proof_validation_status": "pending_plan_12_14",
        "synthetic_fallback_used": False,
        "transport_calls": 11,
        "transport_calls_by_stage": {
            "stage1": 4,
            "property_resolution": 4,
            "stage2": 3,
        },
        "provider_models": [
            {
                "provider": "deepseek-openai-compatible",
                "model": "deepseek-chat",
            }
        ],
        "cases": cases,
    }


def _refresh_live_proof(case_root: Path, *, case_id: str = LIVE_CASE_ID) -> None:
    source_manifest_path = case_root / "manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    artifacts: dict[str, Any] = {}
    for artifact in sorted(case_root.rglob("*")):
        if not artifact.is_file() or artifact.name in {
            "FILES.json",
            "REPORT.md",
            "manifest.json",
        }:
            continue
        relative = artifact.relative_to(case_root).as_posix()
        artifacts[relative] = {
            "path": relative,
            "bytes": artifact.stat().st_size,
            "sha256": _sha256(artifact),
        }
    source_manifest["artifacts"] = artifacts
    _write_json(source_manifest_path, source_manifest)

    prior = json.loads((BASE_DAMAGE_CASE / "FILES.json").read_text(encoding="utf-8"))
    prior_roles = {str(item["path"]): str(item["role"]) for item in prior["files"]}
    entries = []
    for artifact in sorted(case_root.rglob("*")):
        if not artifact.is_file() or artifact.name in {"FILES.json", "REPORT.md"}:
            continue
        relative = artifact.relative_to(case_root).as_posix()
        role = {
            "manifest.json": "source_run_manifest",
            "base-damage-source-manifest.json": "base_damage_source_manifest",
            "provider-evidence/live-uat-result.json": "live_provider_result",
            "provider-draft.json": "live_provider_draft",
            "prompt-profile-selection.json": "live_prompt_profile_selection",
        }.get(relative, prior_roles.get(relative, f"live_artifact_{artifact.stem}"))
        entries.append(
            {
                "path": relative,
                "role": role,
                "sha256": _sha256(artifact),
                "size_bytes": artifact.stat().st_size,
            }
        )
    _write_json(
        case_root / "FILES.json",
        {
            "schema_version": "text2ifc/ifc-repair-proof-files/0.2",
            "case_id": case_id,
            "files": entries,
        },
    )


def _live_proof_collection(tmp_path: Path) -> tuple[Path, Path]:
    collection = tmp_path / "live-proof"
    case_root = collection / LIVE_CASE_PATH
    shutil.copytree(BASE_DAMAGE_CASE, case_root)
    base_manifest_path = case_root / "base-damage-source-manifest.json"
    shutil.copy2(case_root / "manifest.json", base_manifest_path)
    intent = _upgrade_live_intent(
        json.loads(
            (case_root / "repair-intent.json").read_text(encoding="utf-8")
        )
    )
    _write_json(case_root / "repair-intent.json", intent)
    changeset = json.loads((case_root / "changeset.json").read_text(encoding="utf-8"))
    damaged_sha256 = _sha256(case_root / "damaged.ifc")
    live_result = _live_result(
        intent=intent,
        changeset=changeset,
        damaged_sha256=damaged_sha256,
    )
    provider_root = case_root / "provider-evidence"
    provider_root.mkdir()
    live_result_path = provider_root / "live-uat-result.json"
    _write_json(live_result_path, live_result)
    provider_draft_path = case_root / "provider-draft.json"
    _write_json(provider_draft_path, _provider_draft(changeset))
    profile_path = case_root / "prompt-profile-selection.json"
    _write_json(
        profile_path,
        select_prompt_profiles(
            ["beam.add.v0.3", "column.add.v0.3"]
        ).to_dict(),
    )

    base_manifest_sha256 = _sha256(base_manifest_path)
    private_path = case_root / "mutation_manifest.private.json"
    source_manifest = {
        "schema_version": "text2ifc/phase12-live-proof-source/0.1",
        "case_id": LIVE_CASE_ID,
        "status": "passed",
        "provider": "deepseek-openai-compatible",
        "model": "deepseek-chat",
        "provider_evidence_mode": "live",
        "synthetic_fallback_used": False,
        "evidence_scope": "cross_scene_same_family_bimnet",
        "operation_count": len(changeset["operations"]),
        "source": json.loads(base_manifest_path.read_text(encoding="utf-8"))["source"],
        "damage": json.loads(base_manifest_path.read_text(encoding="utf-8"))["damage"],
        "base_damage_contract": {
            "case_id": BASE_DAMAGE_CASE_ID,
            "source_manifest_path": "base-damage-source-manifest.json",
            "source_manifest_sha256": base_manifest_sha256,
            "mutation_manifest_path": "mutation_manifest.private.json",
            "mutation_manifest_sha256": _sha256(private_path),
            "original_ifc_sha256": _sha256(case_root / "original.ifc"),
            "damaged_ifc_sha256": damaged_sha256,
        },
        "live_contract": {
            "case_id": "complete",
            "live_uat_result_path": "provider-evidence/live-uat-result.json",
            "live_uat_result_sha256": _sha256(live_result_path),
            "provider_draft_path": "provider-draft.json",
            "provider_draft_sha256": _sha256(provider_draft_path),
            "prompt_profile_selection_path": "prompt-profile-selection.json",
            "prompt_profile_selection_sha256": _sha256(profile_path),
        },
        "artifacts": {},
    }
    _write_json(case_root / "manifest.json", source_manifest)
    boundary_path = case_root / "production-boundary.json"
    boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
    boundary["entrypoint"] = "run_phase12_live_uat.py"
    _write_json(boundary_path, boundary)
    (case_root / "REPORT.md").write_text(
        "# Phase 12 live strict proof\n",
        encoding="utf-8",
    )
    _refresh_live_proof(case_root)
    _write_json(
        collection / "manifest.json",
        {
            "schema_version": "text2ifc/ifc-repair-success-collection/0.1",
            "case_count": 1,
            "cases": [
                {
                    "case_id": LIVE_CASE_ID,
                    "phase": "12",
                    "status": "accepted",
                    "operation_family": "structural",
                    "case_kind": "live",
                    "provider": "deepseek-openai-compatible",
                    "model": "deepseek-chat",
                    "provider_evidence_mode": "live",
                    "evidence_scope": "cross_scene_same_family_bimnet",
                    "operation_count": len(changeset["operations"]),
                    "operation_types": sorted(
                        {item["operation_type"] for item in changeset["operations"]}
                    ),
                    "original_ifc": (LIVE_CASE_PATH / "original.ifc").as_posix(),
                    "damaged_ifc": (LIVE_CASE_PATH / "damaged.ifc").as_posix(),
                    "repaired_ifc": (LIVE_CASE_PATH / "repaired.ifc").as_posix(),
                    "report": (LIVE_CASE_PATH / "REPORT.md").as_posix(),
                    "files": (LIVE_CASE_PATH / "FILES.json").as_posix(),
                }
            ],
        },
    )
    return collection, case_root


def test_live_structural_proof_recomputes_transcript_and_base_damage_authority(
    tmp_path: Path,
) -> None:
    collection, _case_root = _live_proof_collection(tmp_path)

    result = validate_success_case_collection(collection)

    assert result.status == "passed", result.errors
    assert result.independently_recomputed_case_count == 1
    assert result.cases[0]["provider_evidence_mode"] == "live"
    assert result.cases[0]["live_transcript_status"] == "strict_recomputed"
    assert result.cases[0]["base_damage_case_id"] == BASE_DAMAGE_CASE_ID


def test_property_authority_replay_accepts_public_user_candidate_selection(
    tmp_path: Path,
) -> None:
    from scripts.ifc_repair import run_phase12_live_uat as live_uat
    from tests.ifc_repair.test_phase12_live_uat import _ProductionPathTransport
    from tests.ifc_repair.test_property_resolution_family_e2e import (
        _runtime as offline_property_runtime,
    )

    case = next(
        item for item in live_uat.DEFAULT_CASES
        if item.case_id == "clarification-resume"
    )
    provider = live_uat.TranscriptProvider(_ProductionPathTransport())
    provider.set_case(case.case_id)
    case_root = tmp_path / "clarification"
    final = live_uat._production_case_executor(
        case,
        provider,
        case_root,
        property_knowledge_runtime=offline_property_runtime(),
    )
    assert final["status"] == "succeeded"
    run_root = case_root / "runtime" / "runs" / str(final["run_id"])
    source_manifest = run_root / "proof-source-manifest.json"
    _write_json(source_manifest, {"status": "test-fixture"})
    roles = {
        f"artifact-{index}": path
        for index, path in enumerate(run_root.rglob("*"), start=1)
        if path.is_file()
    }
    roles["source_run_manifest"] = source_manifest
    intent = json.loads(
        (run_root / "intent" / "repair-intent.json").read_text(
            encoding="utf-8"
        )
    )
    changeset = json.loads(
        (run_root / "changeset" / "bound-changeset.json").read_text(
            encoding="utf-8"
        )
    )
    retained_resolution = json.loads(
        (run_root / "resolution.json").read_text(encoding="utf-8")
    )
    retained_manifest = json.loads(
        (run_root / "semantic-manifest.json").read_text(encoding="utf-8")
    )

    def replay() -> dict[str, Any]:
        return success_validator._audit_structural_authority_replay(
            damaged_ifc_path=live_uat.SOURCE,
            damaged_sha256=success_validator._normalize_sha256(
                _sha256(live_uat.SOURCE)
            ),
            intent=intent,
            changeset=changeset,
            retained_resolution=retained_resolution,
            retained_manifest=retained_manifest,
            roles=roles,
            provider_evidence_mode="offline_bound_deterministic",
        )

    authority = replay()

    assert authority["property_authority_coverage"] == (
        "strict_stage_1_5_recomputed"
    )
    assert authority["property_claim_count"] == 1
    assert authority["current_property_acceptance_eligible"] is True

    user_decision_path = next(
        run_root.glob(
            "property-resolution/operation-*/claim-*/decision-result-user.json"
        )
    )
    user_decision = json.loads(user_decision_path.read_text(encoding="utf-8"))
    user_decision["decision"]["selected_candidate_id"] = "candidate:forged"
    _write_json(user_decision_path, user_decision)
    with pytest.raises(
        ValueError,
        match="property_user_decision_binding",
    ):
        replay()

    user_decision["decision"]["selected_candidate_id"] = (
        "candidate:2:ifc2x3:Pset_ColumnCommon.LoadBearing"
    )
    _write_json(user_decision_path, user_decision)
    state_path = run_root / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    answer_transition = next(
        transition
        for transition in state["transitions"]
        if isinstance(transition.get("answer"), dict)
        and transition["answer"].get("kind") == "select_candidate"
    )
    answer_transition["answer"]["candidate_token"] = "candidate:forged"
    _write_json(state_path, state)
    with pytest.raises(
        ValueError,
        match="property_user_answer_binding",
    ):
        replay()


@pytest.mark.parametrize(
    ("defect", "check_id"),
    (
        ("schema_downgrade", "l0.structural.live:source_manifest_schema"),
        ("missing_base", "l0.structural.live:base_damage_manifest_missing"),
        ("base_binding", "l0.structural.live:base_damage_binding"),
    ),
)
def test_live_proof_cannot_bypass_underlying_damage_authority(
    tmp_path: Path,
    defect: str,
    check_id: str,
) -> None:
    collection, case_root = _live_proof_collection(tmp_path)
    source_manifest_path = case_root / "manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    if defect == "schema_downgrade":
        source_manifest["schema_version"] = "text2ifc/phase12-offline-case/0.1"
    elif defect == "missing_base":
        (case_root / "base-damage-source-manifest.json").unlink()
    elif defect == "base_binding":
        source_manifest["base_damage_contract"]["damaged_ifc_sha256"] = (
            "sha256:" + "0" * 64
        )
    else:  # pragma: no cover - the parametrization is exhaustive.
        raise AssertionError(defect)
    _write_json(source_manifest_path, source_manifest)
    _refresh_live_proof(case_root)

    result = validate_success_case_collection(collection)

    assert result.status == "failed"
    assert any(check_id in error for error in result.errors), result.errors


def test_validator_cli_accepts_the_frozen_root_option(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, Path] = {}

    def fake_validate(root: Path) -> ProofValidationResult:
        captured["root"] = Path(root)
        return ProofValidationResult(
            status="passed",
            collection_root=Path(root).resolve().as_posix(),
        )

    monkeypatch.setattr(
        success_validator,
        "validate_success_case_collection",
        fake_validate,
    )

    exit_code = success_validator.main(
        ["--root", str(tmp_path), "--json"]
    )

    assert exit_code == 0
    assert captured["root"] == tmp_path
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "passed"


def _curator_source_run(tmp_path: Path) -> Path:
    source = tmp_path / "source-live-run"
    source.mkdir()
    intent = _upgrade_live_intent(
        json.loads(
            (BASE_DAMAGE_CASE / "repair-intent.json").read_text(encoding="utf-8")
        )
    )
    changeset = json.loads(
        (BASE_DAMAGE_CASE / "changeset.json").read_text(encoding="utf-8")
    )
    live_result = _live_result(
        intent=intent,
        changeset=changeset,
        damaged_sha256=_sha256(BASE_DAMAGE_CASE / "damaged.ifc"),
    )
    for case in live_result["cases"]:
        case_id = str(case["case_id"])
        case_root = source / "cases" / case_id
        case_root.mkdir(parents=True)
        if case_id == "program-guard":
            _write_json(case_root / "case-result.json", case)
            continue
        frozen = next(item for item in FROZEN_LIVE_CASES if item.case_id == case_id)
        effective_request = (
            f"{frozen.request}\n补充说明：{frozen.feedback.strip()}"
            if frozen.feedback is not None
            and frozen.feedback_kind == "add_detail"
            else frozen.request
        )
        effective_hash = "sha256:" + hashlib.sha256(
            effective_request.encode("utf-8")
        ).hexdigest()
        case_intent = json.loads(json.dumps(intent))
        case_changeset = json.loads(json.dumps(changeset))
        case_intent["source_request_hash"] = effective_hash
        case_changeset["source_request_hash"] = effective_hash
        successful_stage1 = [
            attempt for attempt in case["attempts"] if attempt["stage"] == "stage1"
        ][-1]
        successful_stage2 = [
            attempt for attempt in case["attempts"] if attempt["stage"] == "stage2"
        ][-1]
        _replace_live_response_document(
            successful_stage1,
            {
                "schema_version": "text2ifc/ifc-repair-intent-body/0.8",
                "operations": case_intent["operations"],
                "unsupported_requests": case_intent.get(
                    "unsupported_requests", []
                ),
                "semantic_bundles": case_intent.get("semantic_bundles", []),
                "provenance": case_intent.get("provenance", []),
            },
        )
        _replace_live_response_document(
            successful_stage2,
            _provider_draft(case_changeset),
        )
        run_id = f"run-{case_id}"
        case["final"]["run_id"] = run_id
        run_root = case_root / "runtime" / "runs" / run_id
        (run_root / "intent").mkdir(parents=True)
        (run_root / "property-resolution").mkdir()
        (run_root / "changeset" / "attempt-001").mkdir(parents=True)
        (run_root / "publication" / "terminal").mkdir(parents=True)
        _write_json(run_root / "intent" / "repair-intent.json", case_intent)
        shutil.copy2(
            BASE_DAMAGE_CASE / "target-resolution.json",
            run_root / "resolution.json",
        )
        for destination in (
            run_root / "changeset.json",
            run_root / "changeset" / "bound-changeset.json",
        ):
            _write_json(destination, case_changeset)
        _write_json(
            run_root / "changeset" / "provider-draft.json",
            _provider_draft(case_changeset),
        )
        shutil.copy2(
            BASE_DAMAGE_CASE / "semantic-manifests.json",
            run_root / "changeset" / "semantic-manifests.json",
        )
        shutil.copy2(
            BASE_DAMAGE_CASE / "evaluation.json",
            run_root / "evaluation.json",
        )
        shutil.copy2(
            BASE_DAMAGE_CASE / "repaired.ifc",
            run_root / "repaired.ifc",
        )
        _write_json(
            run_root / "publication" / "terminal" / "evidence.json",
            {
                "evidence": {
                    "application": json.loads(
                        (BASE_DAMAGE_CASE / "application.json").read_text(
                            encoding="utf-8"
                        )
                    )
                }
            },
        )
        publication_artifacts = []
        for artifact in (
            run_root / "evaluation.json",
            run_root / "repaired.ifc",
            run_root / "publication" / "terminal" / "evidence.json",
        ):
            publication_artifacts.append(
                {
                    "path": artifact.relative_to(run_root).as_posix(),
                    "size_bytes": artifact.stat().st_size,
                    "sha256": _sha256(artifact),
                }
            )
        _write_json(
            run_root / "publication" / "manifest.json",
            {"artifacts": publication_artifacts},
        )
        _write_json(
            run_root / "state.json",
            {
                "run_id": run_id,
                "source": {
                    "reference": str((BASE_DAMAGE_CASE / "damaged.ifc").resolve()),
                    "sha256": _sha256(BASE_DAMAGE_CASE / "damaged.ifc"),
                },
                "status": "succeeded",
            },
        )
        _write_json(
            run_root / "transitions.json",
            {"run_id": run_id, "terminal_status": "succeeded"},
        )
        _write_json(
            run_root / "api-context.json",
            {
                "schema_version": "text2ifc/ifc-repair-api-context/0.1",
                "repair_text": effective_request,
                "intent": case_intent,
            },
        )
        profiles = (
            ["beam.add.v0.3", "column.add.v0.3"]
            if case_id == "complete"
            else (
                ["column.add.v0.3"]
                if case_id == "clarification-resume"
                else ["occurrence.set-properties"]
            )
        )
        _write_json(
            run_root / "changeset" / "prompt-profile-selection.json",
            select_prompt_profiles(profiles).to_dict(),
        )
        for index, attempt in enumerate(case["attempts"], start=1):
            if attempt["stage"] == "stage1":
                relative = f"intent/attempt-{index:03d}.json"
            elif attempt["stage"] == "property_resolution":
                relative = f"property-resolution/transcript-attempt-{index:03d}.json"
            else:
                relative = "changeset/attempt-001/provider-metadata.json"
            _write_json(
                run_root / relative,
                attempt,
            )
        case["final"]["artifacts"] = {
            "manifest": "publication/manifest.json",
            "evaluation": "evaluation.json",
            "successful_ifc": "repaired.ifc",
        }
        _write_json(case_root / "case-result.json", case)
    _write_json(source / "live-uat-result.json", live_result)
    preflight = {
        "schema_version": "text2ifc/phase12-live-preflight/0.3",
        "status": "passed",
        "failure_count": 0,
        "skip_count": 0,
        "substitution_count": 0,
        "timeout_count": 0,
        "network_calls": 0,
        "checks": [],
    }
    preflight["evidence_sha256"] = _canonical_transport_sha256(preflight)
    (source / "preflight").mkdir()
    _write_json(source / "preflight" / "preflight.json", preflight)
    return source


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _empty_proof(root: Path) -> Path:
    root.mkdir()
    _write_json(
        root / "manifest.json",
        {
            "schema_version": "text2ifc/ifc-repair-success-collection/0.1",
            "case_count": 0,
            "cases": [],
        },
    )
    (root / "README.md").write_text("# Proof\n", encoding="utf-8")
    return root


def _strict_validator_payload(
    *,
    case_ids: Sequence[str] = (
        "phase12-live-deepseek-complete",
        "phase12-live-deepseek-clarification-resume",
    ),
    case_count: int = 2,
    independently_recomputed: int = 2,
    legacy_unverifiable: int = 0,
) -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/ifc-repair-proof-validation/0.2",
        "status": "passed",
        "case_count": case_count,
        "independently_recomputed_case_count": independently_recomputed,
        "legacy_unverifiable_case_count": legacy_unverifiable,
        "errors": [],
        "cases": [
            {
                "case_id": case_id,
                "provider_evidence_mode": "live",
                "live_transcript_status": "strict_recomputed",
                "property_authority_coverage": "strict_stage_1_5_recomputed",
                "property_claim_count": 1,
                "current_property_acceptance_eligible": True,
            }
            for case_id in case_ids
        ],
    }


def _proof_validation_v02_payload(
    *,
    schema_version: str = "text2ifc/ifc-repair-proof-validation/0.2",
    coverage_by_case: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    case_ids = (
        "phase12-live-deepseek-complete",
        "phase12-live-deepseek-clarification-resume",
    )
    coverage = dict(coverage_by_case or {})
    return {
        "schema_version": schema_version,
        "status": "passed",
        "case_count": 2,
        "independently_recomputed_case_count": 2,
        "legacy_unverifiable_case_count": 0,
        "errors": [],
        "cases": [
            {
                "case_id": case_id,
                "provider_evidence_mode": "live",
                "live_transcript_status": "strict_recomputed",
                "property_authority_coverage": coverage.get(
                    case_id, "strict_stage_1_5_recomputed"
                ),
                "property_claim_count": 1,
                "current_property_acceptance_eligible": True,
            }
            for case_id in case_ids
        ],
    }


def test_proof_validation_v02_formalizes_the_validator_curator_boundary() -> None:
    schema_path = (
        ROOT / "schemas/agent/ifc-repair-proof-validation-0.2.schema.json"
    )
    assert schema_path.is_file()
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    payload = ProofValidationResult(
        status="passed",
        collection_root="fixture",
        case_count=1,
        independently_recomputed_case_count=1,
        cases=[
            {
                "case_id": "case-1",
                "provider_evidence_mode": "live",
                "live_transcript_status": "strict_recomputed",
                "property_authority_coverage": "strict_stage_1_5_recomputed",
                "property_claim_count": 1,
                "current_property_acceptance_eligible": True,
            }
        ],
    ).to_dict()

    assert payload["schema_version"] == (
        "text2ifc/ifc-repair-proof-validation/0.2"
    )
    Draft202012Validator(schema).validate(payload)

    missing_boundary_field = json.loads(json.dumps(payload))
    del missing_boundary_field["cases"][0]["property_authority_coverage"]
    assert list(Draft202012Validator(schema).iter_errors(missing_boundary_field))


def test_unrecomputed_property_authority_distinguishes_non_property_from_alias(
    tmp_path: Path,
) -> None:
    non_property = success_validator._unrecomputed_property_authority(
        intent={"operations": [{"property_intents": []}]},
        roles={},
    )
    assert non_property == {
        "property_authority_coverage": "not_applicable",
        "property_claim_count": 0,
        "property_reason_codes": [],
        "historical_alias_present": False,
        "current_property_acceptance_eligible": True,
    }

    resolution = tmp_path / "target-resolution.json"
    _write_json(
        resolution,
        {
            "property_resolutions": [
                {"decision": {"reason_code": "REVIEWED_ALIAS_EXACT"}}
            ]
        },
    )
    property_bearing = success_validator._unrecomputed_property_authority(
        intent={
            "operations": [
                {
                    "property_intents": [
                        {"intent_kind": "natural_language_property"}
                    ]
                }
            ]
        },
        roles={"deterministic_target_resolution": resolution},
    )
    assert property_bearing == {
        "property_authority_coverage": "historical_property_artifact_only",
        "property_claim_count": 1,
        "property_reason_codes": ["REVIEWED_ALIAS_EXACT"],
        "historical_alias_present": True,
        "current_property_acceptance_eligible": False,
    }


@pytest.mark.parametrize(
    "payload",
    (
        _proof_validation_v02_payload(
            schema_version="text2ifc/ifc-repair-proof-validation/0.1"
        ),
        _proof_validation_v02_payload(
            coverage_by_case={
                "phase12-live-deepseek-complete": "not_applicable",
            }
        ),
    ),
    ids=("old-contract", "required-property-case-not-applicable"),
)
def test_live_curator_rejects_non_v02_or_non_strict_property_authority(
    tmp_path: Path,
    payload: Mapping[str, Any],
) -> None:
    curator = _curator_module()
    proof = _empty_proof(tmp_path / "proof")

    def validator_runner(
        command: Sequence[str],
        *,
        cwd: Path,
    ) -> subprocess.CompletedProcess[str]:
        del cwd
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps(payload),
            "",
        )

    with pytest.raises(ValueError, match="LIVE_CANDIDATE_VALIDATION_FAILED"):
        curator._validate_subprocess(
            proof,
            validator_runner=validator_runner,
            candidate_only=True,
        )


def test_public_curate_runs_validator_in_a_separate_process_before_install(
    tmp_path: Path,
) -> None:
    curator = _curator_module()
    source = _curator_source_run(tmp_path)
    proof = _empty_proof(tmp_path / "proof")
    before = _tree_bytes(proof)
    calls: list[tuple[tuple[str, ...], Path]] = []

    def failed_validator(
        command: Sequence[str],
        *,
        cwd: Path,
    ) -> subprocess.CompletedProcess[str]:
        calls.append((tuple(str(item) for item in command), cwd))
        return subprocess.CompletedProcess(
            command,
            1,
            json.dumps(
                {
                    "schema_version": "text2ifc/ifc-repair-proof-validation/0.2",
                    "status": "failed",
                    "case_count": 2,
                    "independently_recomputed_case_count": 0,
                    "legacy_unverifiable_case_count": 0,
                    "errors": ["injected independent failure"],
                    "cases": [],
                }
            ),
            "",
        )

    with pytest.raises(ValueError, match="LIVE_CANDIDATE_VALIDATION_FAILED"):
        curator.curate(
            source,
            proof,
            validator_runner=failed_validator,
        )

    assert len(calls) == 1
    command, cwd = calls[0]
    assert Path(command[0]).resolve() == Path(sys.executable).resolve()
    assert Path(command[1]).resolve() == CURATOR_SCRIPT.with_name(
        "validate_success_cases.py"
    ).resolve()
    assert "--root" in command
    assert cwd == ROOT
    assert _tree_bytes(proof) == before
    assert not list(proof.glob("structural/live/*"))


def test_public_curate_installs_only_two_strict_success_cases_after_validation(
    tmp_path: Path,
) -> None:
    curator = _curator_module()
    source = _curator_source_run(tmp_path)
    proof = _empty_proof(tmp_path / "proof")
    calls: list[tuple[tuple[str, ...], Path]] = []

    def passed_validator(
        command: Sequence[str],
        *,
        cwd: Path,
    ) -> subprocess.CompletedProcess[str]:
        calls.append((tuple(str(item) for item in command), cwd))
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps(_strict_validator_payload()),
            "",
        )

    result = curator.curate(
        source,
        proof,
        validator_runner=passed_validator,
    )

    assert result["status"] == "passed"
    assert len(calls) == 2
    manifest = json.loads((proof / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["case_count"] == 2
    assert [case["case_id"] for case in manifest["cases"]] == list(
        _strict_validator_payload()["cases"][index]["case_id"]
        for index in range(2)
    )
    for case_id in (
        "phase12-live-deepseek-complete",
        "phase12-live-deepseek-clarification-resume",
    ):
        case_root = proof / "structural" / "live" / case_id
        assert (case_root / "runtime" / "runs").is_dir()
        assert (case_root / "provider-evidence" / "live-uat-result.json").is_file()
    assert not (proof / "structural" / "live" / "program-guard").exists()


def test_public_curate_resolves_the_latest_timestamped_runner_directory(
    tmp_path: Path,
) -> None:
    curator = _curator_module()
    source = _curator_source_run(tmp_path)
    live_root = tmp_path / "phase12-live"
    live_root.mkdir()
    timestamped = live_root / "uat-20260817T120000000000Z"
    shutil.copytree(source, timestamped)
    proof = _empty_proof(tmp_path / "proof")

    def passed_validator(
        command: Sequence[str],
        *,
        cwd: Path,
    ) -> subprocess.CompletedProcess[str]:
        del cwd
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps(_strict_validator_payload()),
            "",
        )

    result = curator.curate(
        live_root,
        proof,
        validator_runner=passed_validator,
    )

    assert result["status"] == "passed"
    assert result["source_run_root"] == timestamped.resolve().as_posix()


@pytest.mark.parametrize(
    "forged_payload",
    (
        _strict_validator_payload(case_ids=("wrong-complete", "wrong-resume")),
        _strict_validator_payload(case_count=3),
        _strict_validator_payload(independently_recomputed=1),
        _strict_validator_payload(legacy_unverifiable=1),
    ),
    ids=("wrong-case-ids", "wrong-count", "not-recomputed", "legacy"),
)
def test_public_curate_rejects_forged_passed_validator_summary_without_install(
    tmp_path: Path,
    forged_payload: Mapping[str, Any],
) -> None:
    curator = _curator_module()
    source = _curator_source_run(tmp_path)
    proof = _empty_proof(tmp_path / "proof")
    before = _tree_bytes(proof)

    def forged_validator(
        command: Sequence[str],
        *,
        cwd: Path,
    ) -> subprocess.CompletedProcess[str]:
        del cwd
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps(forged_payload),
            "",
        )

    with pytest.raises(ValueError, match="LIVE_CANDIDATE_VALIDATION_FAILED"):
        curator.curate(source, proof, validator_runner=forged_validator)

    assert _tree_bytes(proof) == before
    assert not list(proof.glob("structural/live/*"))
