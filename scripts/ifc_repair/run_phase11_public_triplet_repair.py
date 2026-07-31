"""Run the supplied Door audit repair without any private benchmark input.

This process accepts exactly a damaged IFC and a frozen public request bundle.
It deliberately has no argument, import, or code path for an original IFC,
deleted occurrence identifiers, or a mutation manifest.  Private comparison
is a separate post-repair command.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping

import ifcopenshell
import ifcopenshell.util.element


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from text2ifc_ifc_repair.apply import apply_changeset  # noqa: E402
from text2ifc_ifc_repair.benchmark_evaluation import (  # noqa: E402
    ProductionEvaluationInputs,
    evaluate_production,
)
from text2ifc_ifc_repair.compare import compare_ifc_models  # noqa: E402
from text2ifc_ifc_repair.evaluation import evaluation_to_dict  # noqa: E402
from text2ifc_ifc_repair.evaluation_policy import (  # noqa: E402
    EvidenceSourceKind,
)
from text2ifc_ifc_repair.index_store import (  # noqa: E402
    SQLiteIndexRepository,
)
from text2ifc_ifc_repair.indexer import build_ifc_index  # noqa: E402
from text2ifc_ifc_repair.operations import (  # noqa: E402
    create_default_registry,
)
from text2ifc_ifc_repair.repair_intent import RepairIntent  # noqa: E402
from text2ifc_ifc_repair.resolution_flow import (  # noqa: E402
    ResolvedOperation,
    resolve_repair_intent,
)
from text2ifc_ifc_repair.semantic_facts import SemanticFact  # noqa: E402
from text2ifc_ifc_repair.spatial import resolve_opening_storey  # noqa: E402


SCHEMA_VERSION = "text2ifc/phase11-public-triplet-repair/0.1"


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _text_sha256(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (
        value
        if isinstance(value, str)
        else json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            default=str,
        )
    )
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _generated_type_authority(
    operation: ResolvedOperation,
) -> dict[str, Any]:
    matches = [
        dict(item)
        for item in operation.authorized_semantics
        if item.get("kind") == "system_generated_type"
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "PUBLIC_GENERATED_TYPE_AUTHORITY_REQUIRED:"
            f"{operation.operation_id}:{len(matches)}"
        )
    return matches[0]


def _generated_type_assignment(
    operation: ResolvedOperation,
    *,
    scope: str,
) -> tuple[dict[str, Any], str]:
    authority = _generated_type_authority(operation)
    type_id = str(authority["global_id"])
    return (
        {
            "operation_id": operation.operation_id,
            "scope": scope,
            "fact_key": "relationship:type",
            "source_fact_key": "relationship:type",
            "value": type_id,
            "value_type": authority["ifc_class"],
            "unit": None,
            "ownership": "type_inherited",
            "applicability": "required",
            "source_kind": "deterministic_derived",
            "source_ref": f"generated-type:{type_id}",
            "provenance": [
                f"generated-type-template:{authority['template_version']}"
            ],
            "derivation": {
                "template_id": authority["template_id"],
                "template_version": authority["template_version"],
                "ifc_class": authority["ifc_class"],
                "formal_attributes": authority["formal_attributes"],
                "template_digest": authority["template_digest"],
                "template": authority["template"],
            },
            "authoring_action": "inherit_from_type",
        },
        type_id,
    )


def _wall_is_external(model: Any, wall: Any) -> bool:
    psets = ifcopenshell.util.element.get_psets(
        wall,
        psets_only=True,
        should_inherit=True,
    )
    common = next(
        (
            value
            for name, value in psets.items()
            if str(name).casefold() == "pset_wallcommon"
        ),
        None,
    )
    value = common.get("IsExternal") if isinstance(common, Mapping) else None
    if not isinstance(value, bool):
        raise RuntimeError(
            f"PUBLIC_WALL_EXTERNALITY_UNAVAILABLE:{wall.GlobalId}"
        )
    return value


def _quantity_assignment(
    operation_id: str,
    fact_key: str,
    value: float,
    value_type: str,
) -> dict[str, Any]:
    return {
        "operation_id": operation_id,
        "scope": "window_occurrence",
        "fact_key": fact_key,
        "source_fact_key": fact_key,
        "value": value,
        "value_type": value_type,
        "unit": None,
        "ownership": "occurrence_direct",
        "applicability": "required",
        "source_kind": "deterministic_derived",
        "source_ref": "resolved:/operation/window-dimensions",
        "provenance": ["registered-window-parameter-policy:0.2"],
        "authoring_action": "set_quantity",
    }


def _bind_operation(
    operation: ResolvedOperation,
    *,
    damaged_model: Any,
) -> tuple[dict[str, Any], str]:
    operation_type = operation.operation_type
    parameters = operation.to_dict()["parameters"]
    if operation_type == "add_window_with_opening_to_wall":
        type_assignment, type_id = _generated_type_assignment(
            operation,
            scope="window_occurrence",
        )
        wall = damaged_model.by_guid(operation.target_global_id)
        is_external = _wall_is_external(damaged_model, wall)
        opening = parameters["opening"]
        assignments = [
            type_assignment,
            {
                "operation_id": operation.operation_id,
                "scope": "window_occurrence",
                "fact_key": "pset:Pset_WindowCommon.IsExternal",
                "source_fact_key": "pset:Pset_WindowCommon.IsExternal",
                "value": is_external,
                "value_type": "IfcBoolean",
                "unit": None,
                "ownership": "occurrence_direct",
                "applicability": "required",
                "source_kind": "deterministic_derived",
                "source_ref": (
                    "damaged-ifc:/resolved-wall/"
                    "Pset_WallCommon.IsExternal"
                ),
                "provenance": [
                    "deterministic-host-externality-projection:0.1"
                ],
                "authoring_action": "set_occurrence_pset",
            },
            _quantity_assignment(
                operation.operation_id,
                "quantity:window-base.Width",
                float(opening["width_mm"]),
                "IfcQuantityLength",
            ),
            _quantity_assignment(
                operation.operation_id,
                "quantity:window-base.Height",
                float(opening["height_mm"]),
                "IfcQuantityLength",
            ),
            _quantity_assignment(
                operation.operation_id,
                "quantity:window-base.Area",
                float(opening["width_mm"]) * float(opening["height_mm"]),
                "IfcQuantityArea",
            ),
        ]
        return (
            {
                "operation_id": operation.operation_id,
                "operation_type": operation_type,
                "target": {"wall_global_id": operation.target_global_id},
                "parameters": parameters,
                "evidence_refs": ["request:/operations"],
                "semantic_manifest": {
                    "manifest_id": f"manifest-{operation.operation_id}",
                    "policy_id": "window.add-with-opening.l2",
                    "policy_version": "0.2",
                },
                "semantic_assignments": assignments,
            },
            type_id,
        )
    if operation_type == "fill_existing_opening_with_door":
        type_assignment, type_id = _generated_type_assignment(
            operation,
            scope="door_occurrence",
        )
        return (
            {
                "operation_id": operation.operation_id,
                "operation_type": operation_type,
                "target": {
                    "opening_global_id": operation.target_global_id
                },
                "parameters": parameters,
                "evidence_refs": ["request:/operations"],
                "semantic_manifest": {
                    "manifest_id": f"manifest-{operation.operation_id}",
                    "policy_id": "door.fill-existing-opening.l2",
                    "policy_version": "0.1",
                },
                "semantic_assignments": [type_assignment],
            },
            type_id,
        )
    raise RuntimeError(f"PUBLIC_OPERATION_UNSUPPORTED:{operation_type}")


def _fact(
    *,
    key: str,
    value: Any,
    value_type: str,
    inherited: bool,
    source_kind: EvidenceSourceKind,
    operation_id: str,
    scope: str,
) -> SemanticFact:
    return SemanticFact(
        fact_key=key,
        value=value,
        value_type=value_type,
        unit=None,
        inherited=inherited,
        pset_path=None,
        entity_source="public-damaged-ifc-and-request",
        source_kind=source_kind,
        source_ref=(
            f"current-ifc:{value}"
            if key.startswith("relationship:")
            else "request:/operations"
        ),
        provenance=(
            "phase11-public-triplet-authority",
            f"operation:{operation_id}",
        ),
        occurrence_scope=scope,
    )


def _expected_facts(
    operation: Mapping[str, Any],
    *,
    damaged_model: Any,
    generated_type_id: str,
) -> tuple[SemanticFact, ...]:
    operation_id = str(operation["operation_id"])
    operation_type = str(operation["operation_type"])
    if operation_type == "add_window_with_opening_to_wall":
        scope = "window_occurrence"
        wall = damaged_model.by_guid(
            operation["target"]["wall_global_id"]
        )
        storey = wall.ContainedInStructure[0].RelatingStructure
        width = float(operation["parameters"]["opening"]["width_mm"])
        height = float(operation["parameters"]["opening"]["height_mm"])
        values = (
            (
                "relationship:type",
                generated_type_id,
                "IfcWindowStyle",
                True,
                EvidenceSourceKind.DETERMINISTIC_POLICY,
            ),
            (
                "relationship:host",
                str(wall.GlobalId),
                wall.is_a(),
                False,
                EvidenceSourceKind.SURVIVING_HOST,
            ),
            (
                "relationship:storey",
                str(storey.GlobalId),
                "IfcBuildingStorey",
                False,
                EvidenceSourceKind.SURVIVING_HOST,
            ),
            (
                "attribute:OverallWidth",
                width,
                "IfcPositiveLengthMeasure",
                False,
                EvidenceSourceKind.EXPLICIT_REQUEST,
            ),
            (
                "attribute:OverallHeight",
                height,
                "IfcPositiveLengthMeasure",
                False,
                EvidenceSourceKind.EXPLICIT_REQUEST,
            ),
            (
                "pset:Pset_WindowCommon.IsExternal",
                _wall_is_external(damaged_model, wall),
                "IfcBoolean",
                False,
                EvidenceSourceKind.SURVIVING_HOST,
            ),
            (
                "quantity:window-base.Width",
                width,
                "IfcQuantityLength",
                False,
                EvidenceSourceKind.DETERMINISTIC_POLICY,
            ),
            (
                "quantity:window-base.Height",
                height,
                "IfcQuantityLength",
                False,
                EvidenceSourceKind.DETERMINISTIC_POLICY,
            ),
            (
                "quantity:window-base.Area",
                width * height,
                "IfcQuantityArea",
                False,
                EvidenceSourceKind.DETERMINISTIC_POLICY,
            ),
        )
    else:
        scope = "door_occurrence"
        opening = damaged_model.by_guid(
            operation["target"]["opening_global_id"]
        )
        wall = opening.VoidsElements[0].RelatingBuildingElement
        storey = resolve_opening_storey(opening, wall)
        door = operation["parameters"]["door"]
        values = (
            (
                "relationship:type",
                generated_type_id,
                "IfcDoorStyle",
                True,
                EvidenceSourceKind.DETERMINISTIC_POLICY,
            ),
            (
                "relationship:host",
                str(wall.GlobalId),
                wall.is_a(),
                False,
                EvidenceSourceKind.SURVIVING_HOST,
            ),
            (
                "relationship:storey",
                str(storey.GlobalId),
                "IfcBuildingStorey",
                False,
                EvidenceSourceKind.SURVIVING_HOST,
            ),
            (
                "attribute:OverallWidth",
                float(door["overall_width_mm"]),
                "IfcPositiveLengthMeasure",
                False,
                EvidenceSourceKind.EXPLICIT_REQUEST,
            ),
            (
                "attribute:OverallHeight",
                float(door["overall_height_mm"]),
                "IfcPositiveLengthMeasure",
                False,
                EvidenceSourceKind.EXPLICIT_REQUEST,
            ),
        )
    return tuple(
        _fact(
            key=key,
            value=value,
            value_type=value_type,
            inherited=inherited,
            source_kind=source_kind,
            operation_id=operation_id,
            scope=scope,
        )
        for key, value, value_type, inherited, source_kind in values
    )


def run_public_repair(
    *,
    damaged_ifc: Path,
    public_request_bundle: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Resolve, bind, apply, reopen and evaluate using public inputs only."""

    bundle = json.loads(public_request_bundle.read_text(encoding="utf-8"))
    request = str(bundle["request"])
    operation_documents = list(bundle["operations"])
    output_root.mkdir(parents=True, exist_ok=False)
    damaged_copy = output_root / "damaged.ifc"
    shutil.copy2(damaged_ifc, damaged_copy)
    request_hash = _text_sha256(request)
    damaged_hash = _sha256(damaged_copy)
    prompt_hash = _text_sha256(
        "phase11-public-geometry-request-fixture/0.1"
    )
    provenance = {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": request[:2048],
    }
    intent_document = {
        "schema_version": "text2ifc/ifc-repair-intent/0.1",
        "request_id": str(bundle["request_id"]),
        "source_request_hash": request_hash,
        "model_fingerprint": damaged_hash,
        "prompt_fingerprint": prompt_hash,
        "operations": [
            {
                **document,
                "attribute_intents": [],
                "prototype_intent": None,
                "provenance": [
                    {
                        "source_kind": "user_request",
                        "reference": (
                            f"request:/operations/{index}"
                        ),
                        "excerpt": str(document["request_excerpt"]),
                    }
                ],
            }
            for index, document in enumerate(operation_documents)
        ],
        "provenance": [provenance],
    }
    for operation in intent_document["operations"]:
        operation.pop("request_excerpt", None)
    registry = create_default_registry()
    intent = RepairIntent.from_dict(
        intent_document,
        registry=registry,
        require_complete=False,
    )
    index_path = output_root / "target-index.sqlite"
    metadata = build_ifc_index(damaged_copy, index_path)
    with SQLiteIndexRepository.open(index_path) as repository:
        resolution = resolve_repair_intent(
            intent,
            repository,
            expected_source_sha256=metadata.source_ifc_sha256,
            operation_registry=registry,
        )
    if resolution.status != "resolved":
        raise RuntimeError(
            "PUBLIC_TARGET_RESOLUTION_FAILED:"
            + json.dumps(resolution.to_dict(), ensure_ascii=False)
        )
    damaged_model = ifcopenshell.open(str(damaged_copy))
    bound_pairs = [
        _bind_operation(item, damaged_model=damaged_model)
        for item in resolution.operations
    ]
    operations = [pair[0] for pair in bound_pairs]
    generated_type_ids = {
        operation["operation_id"]: pair[1]
        for operation, pair in zip(operations, bound_pairs, strict=True)
    }
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "changeset_id": str(bundle["changeset_id"]),
        "binding_status": "bound",
        "base_model_fingerprint": damaged_hash,
        "source_request_hash": request_hash,
        "semantic_manifest_ref": "semantic-manifests.json",
        "semantic_manifest_sha256": "sha256:" + "d" * 64,
        "scope": {
            "target_ids": [
                str(item.target_global_id)
                for item in resolution.operations
            ],
            "forbidden_ids": [],
        },
        "evidence_refs": ["request:/operations"],
        "preconditions": ["public_targets_available"],
        "postconditions": ["windows_and_doors_hosted"],
        "operations": operations,
    }
    expected = {
        operation["operation_id"]: _expected_facts(
            operation,
            damaged_model=damaged_model,
            generated_type_id=generated_type_ids[
                operation["operation_id"]
            ],
        )
        for operation in operations
    }
    repaired = output_root / "repaired.ifc"
    application = apply_changeset(
        damaged_ifc_path=damaged_copy,
        repair_request=request,
        changeset=changeset,
        output_path=repaired,
        registry=registry,
    )
    if not application.get("valid") or not application.get("published"):
        raise RuntimeError(
            "PUBLIC_APPLICATION_FAILED:"
            + json.dumps(application.get("issues"), ensure_ascii=False)
        )
    evaluation = evaluation_to_dict(
        evaluate_production(
            ProductionEvaluationInputs(
                damaged_ifc_path=damaged_copy,
                repaired_ifc_path=repaired,
                changeset=changeset,
                application_result=application,
                registry=registry,
                expected_facts_by_operation=expected,
            )
        )
    )
    if not evaluation["complete_repair_success"]:
        raise RuntimeError(
            "PUBLIC_EVALUATION_FAILED:"
            + json.dumps(evaluation, ensure_ascii=False, default=str)
        )
    allowed = {
        str(item["global_id"])
        for result in application["operations"]
        for change_kind in ("created", "modified", "removed")
        for item in result["changes"].get(change_kind, ())
        if item.get("global_id")
    }
    comparison = compare_ifc_models(
        damaged_copy,
        repaired,
        allowed_changed_ids=allowed,
    )
    boundary = {
        "schema_version": "text2ifc/production-input-boundary/0.2",
        "entrypoint": "run_phase11_public_triplet_repair.py",
        "ifc_inputs": ["damaged_ifc_path"],
        "request_inputs": ["public_request_bundle"],
        "original_ifc_supplied": False,
        "mutation_manifest_supplied": False,
        "deleted_object_ids_supplied": False,
        "private_comparator_available_during_repair": False,
        "damaged_ifc_sha256": damaged_hash,
        "request_sha256": request_hash,
        "changeset_canonical_sha256": _text_sha256(
            json.dumps(
                changeset,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        ),
        "public_request_bundle_sha256": _sha256(public_request_bundle),
        "resolved_target_count": len(resolution.operations),
    }
    family_counts = {
        family: sum(
            1
            for operation in operations
            if str(operation["operation_type"]).startswith(
                f"{'add_' if family == 'window' else ''}{family}"
            )
            or (
                family == "door"
                and "door" in str(operation["operation_type"])
            )
        )
        for family in ("window", "door")
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "case_id": str(bundle["case_id"]),
        "status": "passed",
        "synthetic_fallback_used": False,
        "operation_count": len(operations),
        "operation_families": {
            family: count
            for family, count in family_counts.items()
            if count
        },
        "one_atomic_changeset": True,
        "public_targeting": {
            "guid_free": True,
            "name_free": True,
            "strategy": (
                "wall_and_opening_geometry_signature_from_public_request"
            ),
            "resolved_operation_count": len(resolution.operations),
        },
        "production_input_boundary": boundary,
        "generated_type_ids": generated_type_ids,
        "artifacts": {},
    }
    _write(output_root / "request.txt", request)
    _write(output_root / "repair-intent.json", intent.to_dict())
    _write(output_root / "target-resolution.json", resolution.to_dict())
    _write(output_root / "changeset.json", changeset)
    _write(output_root / "application.json", application)
    _write(output_root / "evaluation.json", evaluation)
    _write(output_root / "comparison.json", comparison)
    _write(output_root / "production-boundary.json", boundary)
    for name in (
        "damaged.ifc",
        "repaired.ifc",
        "request.txt",
        "repair-intent.json",
        "target-resolution.json",
        "changeset.json",
        "application.json",
        "evaluation.json",
        "comparison.json",
        "production-boundary.json",
    ):
        path = output_root / name
        manifest["artifacts"][name] = {
            "path": name,
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
        }
    _write(output_root / "manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--damaged-ifc", type=Path, required=True)
    parser.add_argument(
        "--public-request-bundle",
        type=Path,
        required=True,
    )
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run_public_repair(
        damaged_ifc=args.damaged_ifc,
        public_request_bundle=args.public_request_bundle,
        output_root=args.output_root,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "case_id": result["case_id"],
                "operation_count": result["operation_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
