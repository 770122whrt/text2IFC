from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.guid
import pytest

from scripts.ifc_repair.run_phase12_public_structural_repair import (
    run_public_repair,
)
from scripts.ifc_repair.validate_success_cases import (
    validate_success_case_collection,
)


ROOT = Path(__file__).resolve().parents[2]
D7N = ROOT / "dataset" / "ifc" / "test" / "d7n.ifc"
STOREY_ID = "0K_MqVdrL0JOCMi_GblRwJ"
CASE_ID = "phase12-d7n-beam-column-strict-proof"
CASE_PATH = Path("structural") / "single" / CASE_ID


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


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
        coordinates[0] += 0.0051
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
