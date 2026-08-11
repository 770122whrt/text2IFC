"""Run the frozen Phase 12 d7n/vvo structural and four-family matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping

import ifcopenshell


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from text2ifc_ifc_repair.apply import apply_changeset  # noqa: E402
from text2ifc_ifc_repair.benchmark_evaluation import (  # noqa: E402
    ProductionEvaluationInputs,
    evaluate_production,
)
from text2ifc_ifc_repair.compare import compare_ifc_models  # noqa: E402
from text2ifc_ifc_repair.evaluation import evaluation_to_dict  # noqa: E402
from text2ifc_ifc_repair.index_store import SQLiteIndexRepository  # noqa: E402
from text2ifc_ifc_repair.indexer import build_ifc_index  # noqa: E402
from text2ifc_ifc_repair.mutation import remove_structural_members  # noqa: E402
from text2ifc_ifc_repair.operations import create_default_registry  # noqa: E402
from text2ifc_ifc_repair.repair_intent import RepairIntent  # noqa: E402
from text2ifc_ifc_repair.resolution_flow import resolve_repair_intent  # noqa: E402
from text2ifc_ifc_repair.semantic_authoring import (  # noqa: E402
    parse_semantic_manifest,
    semantic_manifest_expected_facts,
    semantic_manifest_to_dict,
)
from text2ifc_knowledge.property_search import (  # noqa: E402
    create_default_property_resolver,
)
from scripts.ifc_repair.run_phase12_public_structural_repair import (  # noqa: E402
    _bound_changeset,
    _build_authority,
    _intent_document,
    _production_evidence_document,
    run_public_repair,
)


DEFAULT_OUTPUT = ROOT / "dataset/processed/ifc-repair/phase12-offline"
D7N = ROOT / "dataset/ifc/test/d7n.ifc"
VVO = ROOT / "dataset/ifc/train/vvo.ifc"
FOUR_FAMILY_BASE = (
    ROOT
    / "dataset/processed/proof/ifc-repair-success-cases"
    / "mixed/door-window/vvo-authority-triplet-public-repair"
)

D7N_BEAM_ID = "1RnWak0Kr6GxkeYF4Sd_bw"
D7N_COLUMN_ID = "3dldEzenf9LvnDJYNNzLsH"
D7N_BEAM_STOREY = "0K_MqVdrL0JOCMi_Gblgiw"
D7N_COLUMN_STOREY = "0K_MqVdrL0JOCMi_GblRwJ"
VVO_BEAM_ID = "17tPjyQtf2L9JnbXXmcTUF"
VVO_COLUMN_ID = "1rsYNObuDC4euALdw6WUK4"
VVO_BEAM_STOREY = "1vTeahUkP60PdWqwCTjUuM"
VVO_COLUMN_STOREY = "1vTeahUkP60PdWqwCTjeRs"
VVO_MIXED_STOREY = "1vTeahUkP60PdWqwCTjSGJ"

SUCCESS_CASE_IDS = (
    "phase12-d7n-beam-loadbearing",
    "phase12-d7n-column-loadbearing",
    "phase12-d7n-beam-column-atomic",
    "phase12-vvo-beam-material-present",
    "phase12-vvo-column-material-absent",
    "phase12-vvo-door-window-beam-column-atomic",
)
FAILURE_CASE_IDS = (
    "phase12-d7n-beam-column-rollback",
    "phase12-vvo-door-window-beam-column-rollback",
)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _text_sha256(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = (
        value
        if isinstance(value, str)
        else json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
            default=str,
        )
    )
    path.write_text(rendered.rstrip() + "\n", encoding="utf-8")


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"PHASE12_JSON_OBJECT_REQUIRED:{path}")
    return value


def _beam_parameters(*, x_mm: float, y_mm: float, z_mm: float) -> dict[str, Any]:
    return {
        "axis": {
            "start": {"x_mm": x_mm, "y_mm": y_mm, "z_mm": z_mm},
            "end": {"x_mm": x_mm + 3000, "y_mm": y_mm + 4000, "z_mm": z_mm},
        },
        "section": {"shape": "rectangle", "width_mm": 300, "height_mm": 500},
    }


def _column_parameters(*, x_mm: float, y_mm: float) -> dict[str, Any]:
    return {
        "axis": {
            "base": {"x_mm": x_mm, "y_mm": y_mm, "z_mm": 0},
            "top": {"x_mm": x_mm, "y_mm": y_mm, "z_mm": 6000},
        },
        "section": {
            "shape": "rectangle",
            "width_mm": 400,
            "depth_mm": 600,
            "orientation": {"x": 0, "y": 1},
        },
    }


def _load_bearing(family: str, index: int) -> dict[str, Any]:
    phrase = f"{family} is load bearing"
    return {
        "intent_kind": "natural_language_property",
        "property_phrase": phrase,
        "raw_value": True,
        "raw_unit": None,
        "scope": "occurrence_direct",
        "source": {
            "source_kind": "user_request",
            "reference": f"request:/operations/{index}/properties/0",
            "excerpt": phrase,
        },
    }


def _material(label: str, index: int) -> dict[str, Any]:
    return {
        "intent_kind": "material",
        "name": f"material:{label}",
        "value": label,
        "source": {
            "source_kind": "user_request",
            "reference": f"request:/operations/{index}/materials/0",
            "excerpt": f"material={label}",
        },
    }


def _operation(
    *,
    case_id: str,
    family: str,
    index: int,
    storey_id: str,
    parameters: Mapping[str, Any],
    load_bearing: bool = False,
    material: str | None = None,
) -> dict[str, Any]:
    return {
        "operation_id": f"{case_id}-{family}-{index + 1}",
        "operation_type": f"add_{family}",
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcBuildingStorey"],
            "global_id": storey_id,
        },
        "parameters": dict(parameters),
        "property_intents": (
            [_load_bearing(family, index)] if load_bearing else []
        ),
        "attribute_intents": (
            [_material(material, index)] if material is not None else []
        ),
    }


def _bundle(case_id: str, request: str, operations: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/phase12-public-structural-request/0.1",
        "case_id": case_id,
        "request_id": f"request-{case_id}",
        "changeset_id": f"changeset-{case_id}",
        "request": request.strip(),
        "operations": operations,
    }


def _structural_specs() -> dict[str, dict[str, Any]]:
    return {
        "phase12-d7n-beam-loadbearing": {
            "source": D7N,
            "beam_ids": (D7N_BEAM_ID,),
            "column_ids": (),
            "operations": [
                _operation(
                    case_id="phase12-d7n-beam-loadbearing",
                    family="beam",
                    index=0,
                    storey_id=D7N_BEAM_STOREY,
                    parameters=_beam_parameters(x_mm=100000, y_mm=100000, z_mm=0),
                    load_bearing=True,
                )
            ],
            "request": "Add one horizontal rectangular Beam and make the Beam load bearing.",
        },
        "phase12-d7n-column-loadbearing": {
            "source": D7N,
            "beam_ids": (),
            "column_ids": (D7N_COLUMN_ID,),
            "operations": [
                _operation(
                    case_id="phase12-d7n-column-loadbearing",
                    family="column",
                    index=0,
                    storey_id=D7N_COLUMN_STOREY,
                    parameters=_column_parameters(x_mm=110000, y_mm=110000),
                    load_bearing=True,
                )
            ],
            "request": "Add one vertical rectangular Column and make the Column load bearing.",
        },
        "phase12-d7n-beam-column-atomic": {
            "source": D7N,
            "beam_ids": (D7N_BEAM_ID,),
            "column_ids": (D7N_COLUMN_ID,),
            "operations": [
                _operation(
                    case_id="phase12-d7n-beam-column-atomic",
                    family="beam",
                    index=0,
                    storey_id=D7N_COLUMN_STOREY,
                    parameters=_beam_parameters(x_mm=120000, y_mm=120000, z_mm=3000),
                ),
                _operation(
                    case_id="phase12-d7n-beam-column-atomic",
                    family="column",
                    index=1,
                    storey_id=D7N_COLUMN_STOREY,
                    parameters=_column_parameters(x_mm=123000, y_mm=124000),
                ),
            ],
            "request": "Add one Beam supported by one Column in one atomic ChangeSet.",
        },
        "phase12-vvo-beam-material-present": {
            "source": VVO,
            "beam_ids": (VVO_BEAM_ID,),
            "column_ids": (),
            "operations": [
                _operation(
                    case_id="phase12-vvo-beam-material-present",
                    family="beam",
                    index=0,
                    storey_id=VVO_BEAM_STOREY,
                    parameters=_beam_parameters(x_mm=200000, y_mm=200000, z_mm=0),
                    material="C_钢筋砼C30",
                )
            ],
            "request": "Add one horizontal rectangular Beam with explicitly authorized material C_钢筋砼C30.",
        },
        "phase12-vvo-column-material-absent": {
            "source": VVO,
            "beam_ids": (),
            "column_ids": (VVO_COLUMN_ID,),
            "operations": [
                _operation(
                    case_id="phase12-vvo-column-material-absent",
                    family="column",
                    index=0,
                    storey_id=VVO_COLUMN_STOREY,
                    parameters=_column_parameters(x_mm=210000, y_mm=210000),
                )
            ],
            "request": "Add one vertical rectangular Column; no material is specified.",
        },
    }


def _artifact_index(case_root: Path) -> dict[str, dict[str, Any]]:
    return {
        path.relative_to(case_root).as_posix(): {
            "path": path.relative_to(case_root).as_posix(),
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(case_root.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }


def _augment_source_case(
    *,
    case_root: Path,
    source: Path,
    mutation_root: Path,
) -> dict[str, Any]:
    shutil.copy2(source, case_root / "original.ifc")
    shutil.copy2(
        mutation_root / "mutation_manifest.private.json",
        case_root / "mutation_manifest.private.json",
    )
    shutil.copy2(
        mutation_root / "mutation_report.json",
        case_root / "mutation_report.json",
    )
    manifest = _read(case_root / "manifest.json")
    manifest["schema_version"] = "text2ifc/phase12-offline-case/0.1"
    manifest["evidence_scope"] = "cross_scene_same_family_bimnet"
    manifest["source"] = {
        "path": source.relative_to(ROOT).as_posix(),
        "schema": "IFC2X3",
        "size_bytes": source.stat().st_size,
        "sha256": _sha256(source),
    }
    manifest["damage"] = _read(mutation_root / "mutation_report.json")
    manifest["artifacts"] = _artifact_index(case_root)
    _write(case_root / "manifest.json", manifest)
    return manifest


def _run_structural_case(
    *,
    case_id: str,
    spec: Mapping[str, Any],
    accepted_root: Path,
    scratch_root: Path,
) -> dict[str, Any]:
    source = Path(spec["source"])
    mutation_root = scratch_root / case_id
    remove_structural_members(
        source_path=source,
        output_dir=mutation_root,
        beam_global_ids=tuple(spec["beam_ids"]),
        column_global_ids=tuple(spec["column_ids"]),
        expected_source_sha256=_sha256(source).removeprefix("sha256:"),
    )
    request_bundle = scratch_root / f"{case_id}.request.json"
    _write(
        request_bundle,
        _bundle(case_id, str(spec["request"]), list(spec["operations"])),
    )
    case_root = accepted_root / case_id
    run_public_repair(
        damaged_ifc=mutation_root / "damaged.ifc",
        public_request_bundle=request_bundle,
        output_root=case_root,
    )
    manifest = _augment_source_case(
        case_root=case_root,
        source=source,
        mutation_root=mutation_root,
    )
    return {
        "case_id": case_id,
        "status": "passed",
        "relative_path": case_root.relative_to(accepted_root.parent).as_posix(),
        "operation_count": int(manifest["operation_count"]),
        "operation_types": sorted(
            {
                item["operation_type"]
                for item in _read(case_root / "changeset.json")["operations"]
            }
        ),
    }


def _shift_structural_sources(value: Any, *, offset: int) -> Any:
    if isinstance(value, dict):
        return {
            key: _shift_structural_sources(child, offset=offset)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [_shift_structural_sources(child, offset=offset) for child in value]
    if isinstance(value, str):
        return re.sub(
            r"request:/operations/(\d+)",
            lambda match: (
                f"request:/operations/{int(match.group(1)) + offset}"
            ),
            value,
        )
    return value


def _upgrade_legacy_mixed_operation(operation: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(operation))
    operation_type = str(result["operation_type"])
    routing = {
        "add_window_with_opening_to_wall": (
            "window",
            "add",
            "window.add-with-opening",
        ),
        "fill_existing_opening_with_door": (
            "door",
            "fill",
            "door.fill-existing-opening.v0.2",
        ),
    }
    try:
        family, action, profile = routing[operation_type]
    except KeyError as error:
        raise ValueError(
            f"PHASE12_LEGACY_MIXED_OPERATION_UNSUPPORTED:{operation_type}"
        ) from error
    provenance = list(result.get("provenance") or [])
    if not provenance:
        raise ValueError("PHASE12_LEGACY_MIXED_PROVENANCE_MISSING")
    result["routing_intent"] = {
        "component_family": family,
        "action": action,
        "operation_profile": profile,
        "source": provenance[0],
    }
    result.setdefault("property_intents", [])
    result.setdefault("quantity_intents", [])
    result.setdefault("semantic_bundle_refs", [])
    result.setdefault("occurrence_reuse_intent", None)
    return result


def _mixed_private_manifest(original: Path, damaged: Path) -> dict[str, Any]:
    mapping = _read(FOUR_FAMILY_BASE / "private-evaluation/benchmark-mapping.json")
    model = ifcopenshell.open(str(original))
    targets: list[dict[str, Any]] = []
    for index, item in enumerate(mapping["damage"]["removed_doors"], start=1):
        targets.append(_private_target(model, str(item["global_id"]), f"door-{index}"))
    for index, item in enumerate(mapping["damage"]["removed_windows"], start=1):
        targets.append(_private_target(model, str(item["global_id"]), f"window-{index}"))
        targets.append(
            _private_target(
                model,
                str(item["opening_global_id"]),
                f"window-opening-{index}",
            )
        )
    return {
        "schema_version": "text2ifc/phase12-private-damage-manifest/0.1",
        "visibility": "evaluator_only_after_production",
        "source": {
            "path": VVO.relative_to(ROOT).as_posix(),
            "schema": "IFC2X3",
            "size_bytes": original.stat().st_size,
            "sha256": _sha256(original),
        },
        "damaged_ifc": {"path": "damaged.ifc", "sha256": _sha256(damaged)},
        "targets": targets,
        "role_mapping": {
            target["role"]: target["entity"]["global_id"] for target in targets
        },
    }


def _private_target(model: Any, global_id: str, role: str) -> dict[str, Any]:
    entity = model.by_guid(global_id)
    return {
        "role": role,
        "entity": {
            "ifc_class": str(entity.is_a()),
            "global_id": str(entity.GlobalId),
            "step_id": int(entity.id()),
            "name": None if entity.Name is None else str(entity.Name),
        },
    }


def _mixed_intent_document(
    *,
    request: str,
    damaged_hash: str,
    duplicate_beam: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    base = _read(FOUR_FAMILY_BASE / "agent/repair-intent.json")
    case_id = (
        "phase12-vvo-door-window-beam-column-rollback"
        if duplicate_beam
        else "phase12-vvo-door-window-beam-column-atomic"
    )
    structural_operations = [
        _operation(
            case_id=case_id,
            family="beam",
            index=0,
            storey_id=VVO_MIXED_STOREY,
            parameters=_beam_parameters(x_mm=100000, y_mm=100000, z_mm=3000),
        ),
        _operation(
            case_id=case_id,
            family="column",
            index=1,
            storey_id=VVO_MIXED_STOREY,
            parameters=_column_parameters(x_mm=103000, y_mm=104000),
        ),
    ]
    if duplicate_beam:
        structural_operations.append(
            _operation(
                case_id=case_id,
                family="beam",
                index=2,
                storey_id=VVO_MIXED_STOREY,
                parameters=_beam_parameters(
                    x_mm=100000,
                    y_mm=100000,
                    z_mm=3000,
                ),
            )
        )
    structural_bundle = _bundle(case_id, request, structural_operations)
    structural = _intent_document(structural_bundle, damaged_hash=damaged_hash)
    shifted = _shift_structural_sources(
        structural["operations"],
        offset=len(base["operations"]),
    )
    intent = {
        "schema_version": "text2ifc/ifc-repair-intent/0.5",
        "request_id": f"request-{case_id}",
        "source_request_hash": _text_sha256(request),
        "model_fingerprint": damaged_hash,
        "prompt_fingerprint": _text_sha256(
            "phase12-frozen-public-four-family-request/0.1"
        ),
        "operations": [
            *(
                _upgrade_legacy_mixed_operation(item)
                for item in base["operations"]
            ),
            *shifted,
        ],
        "semantic_bundles": [],
        "provenance": [
            {
                "source_kind": "user_request",
                "reference": "request:/text",
                "excerpt": request[:2048],
            }
        ],
    }
    public_bundle = {
        "schema_version": "text2ifc/phase12-public-four-family-request/0.1",
        "case_id": case_id,
        "changeset_id": f"changeset-{case_id}",
        "request": request,
        "repair_intent": intent,
    }
    return intent, public_bundle


def _legacy_manifest_document(
    operation: Mapping[str, Any],
    *,
    damaged_hash: str,
) -> dict[str, Any]:
    reference = operation.get("semantic_manifest")
    reference = reference if isinstance(reference, Mapping) else {}
    return {
        "schema_version": "text2ifc/ifc-repair-semantic-manifest/0.3",
        "manifest_id": str(reference.get("manifest_id") or ""),
        "operation_id": str(operation["operation_id"]),
        "operation_type": str(operation["operation_type"]),
        "base_model_fingerprint": damaged_hash,
        "policy": {
            "policy_id": str(reference.get("policy_id") or ""),
            "policy_version": str(reference.get("policy_version") or ""),
        },
        "assignments": deepcopy(list(operation.get("semantic_assignments") or [])),
    }


def _run_mixed_case(
    *,
    output_root: Path,
    duplicate_beam: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    case_id = (
        "phase12-vvo-door-window-beam-column-rollback"
        if duplicate_beam
        else "phase12-vvo-door-window-beam-column-atomic"
    )
    case_root = output_root / case_id
    case_root.mkdir(parents=True)
    original = case_root / "original.ifc"
    damaged = case_root / "damaged.ifc"
    shutil.copy2(FOUR_FAMILY_BASE / "01-original.ifc", original)
    shutil.copy2(FOUR_FAMILY_BASE / "02-damaged.ifc", damaged)
    damaged_hash = _sha256(damaged)
    base_request = (
        FOUR_FAMILY_BASE / "input/request.txt"
    ).read_text(encoding="utf-8").strip()
    request = (
        base_request
        + "\nAdd one horizontal rectangular Beam and one vertical rectangular "
        "Column on the exact authorized Storey in the same atomic ChangeSet."
    )
    if duplicate_beam:
        request += " Add a second Beam on the same axis for rollback verification."
    intent_document, public_bundle = _mixed_intent_document(
        request=request,
        damaged_hash=damaged_hash,
        duplicate_beam=duplicate_beam,
    )
    public_bundle_path = case_root / "public-request-bundle.json"
    _write(public_bundle_path, public_bundle)
    registry = create_default_registry()
    intent = RepairIntent.from_dict(
        intent_document,
        registry=registry,
        require_complete=False,
    )
    index_path = case_root / "target-index.sqlite"
    metadata = build_ifc_index(damaged, index_path)
    with SQLiteIndexRepository.open(index_path) as repository:
        resolution = resolve_repair_intent(
            intent,
            repository,
            expected_source_sha256=metadata.source_ifc_sha256,
            operation_registry=registry,
            property_knowledge_resolver=create_default_property_resolver(),
        )
        records = {item.ifc_global_id: item for item in repository.iter_records()}
        type_records = {
            item.ifc_global_id: item for item in repository.iter_type_records()
        }
    if resolution.status != "resolved":
        raise RuntimeError(
            "PHASE12_MIXED_RESOLUTION_FAILED:"
            + json.dumps(resolution.to_dict(), ensure_ascii=False)
        )
    evidence, manifests, _, _, _ = (
        _build_authority(
            intent=intent,
            resolution=resolution,
            registry=registry,
            records=records,
            type_records=type_records,
            base_model_fingerprint=damaged_hash,
        )
    )
    manifest_name = "semantic-manifests.json"
    base_changeset = _read(
        FOUR_FAMILY_BASE / "changeset/bound-changeset.json"
    )
    structural_documents = [
        semantic_manifest_to_dict(manifest)
        for manifest in manifests
        if manifest.operation_type in {"add_beam", "add_column"}
    ]
    legacy_documents = [
        _legacy_manifest_document(operation, damaged_hash=damaged_hash)
        for operation in base_changeset["operations"]
    ]
    manifest_payload = {
        "schema_version": "text2ifc/ifc-repair-semantic-manifest-bundle/0.1",
        "manifests": [*legacy_documents, *structural_documents],
    }
    manifest_hash = _text_sha256(
        json.dumps(
            manifest_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    changeset = _bound_changeset(
        bundle=public_bundle,
        intent=intent,
        resolution=resolution,
        manifests=manifests,
        manifest_name=manifest_name,
        manifest_hash=manifest_hash,
        damaged_hash=damaged_hash,
    )
    generated_structural = [
        operation
        for operation in changeset["operations"]
        if operation["operation_type"] in {"add_beam", "add_column"}
    ]
    changeset["operations"] = [
        *deepcopy(base_changeset["operations"]),
        *generated_structural,
    ]
    changeset["evidence_refs"] = list(
        dict.fromkeys(
            [
                *changeset.get("evidence_refs", ()),
                *(
                    str(reference)
                    for operation in changeset["operations"]
                    for reference in operation.get("evidence_refs", ())
                ),
            ]
        )
    )
    changeset["semantic_manifest_ref"] = manifest_name
    changeset["semantic_manifest_sha256"] = manifest_hash
    repaired = case_root / "repaired.ifc"
    candidate = case_root / "repaired.candidate.ifc"
    application: dict[str, Any] | None = None
    try:
        application = apply_changeset(
            damaged_ifc_path=damaged,
            repair_request=request,
            changeset=changeset,
            output_path=candidate,
            registry=registry,
        )
        _write(case_root / "request.txt", request)
        _write(case_root / "repair-intent.json", intent.to_dict())
        _write(case_root / "target-resolution.json", resolution.to_dict())
        _write(
            case_root / "production-evidence.json",
            _production_evidence_document(evidence),
        )
        _write(case_root / manifest_name, manifest_payload)
        _write(case_root / "changeset.json", changeset)
        _write(case_root / "application.json", application)
        if not application.get("valid") or not application.get("published"):
            return application, {"case_id": case_id, "case_root": case_root}

        expected = dict(evidence.expected_facts_by_operation)
        for document in legacy_documents:
            legacy_manifest = parse_semantic_manifest(document)
            legacy_facts = semantic_manifest_expected_facts(legacy_manifest)
            replacements = {fact.fact_key: fact for fact in legacy_facts}
            generated_facts = expected[legacy_manifest.operation_id]
            merged = tuple(
                replacements.pop(fact.fact_key, fact) for fact in generated_facts
            )
            expected[legacy_manifest.operation_id] = (
                *merged,
                *(replacements[key] for key in sorted(replacements)),
            )
        evaluation = evaluation_to_dict(
            evaluate_production(
                ProductionEvaluationInputs(
                    damaged_ifc_path=damaged,
                    repaired_ifc_path=candidate,
                    changeset=changeset,
                    application_result=application,
                    registry=registry,
                    expected_facts_by_operation=expected,
                )
            )
        )
        _write(case_root / "evaluation.json", evaluation)
        if not evaluation["complete_repair_success"]:
            failed = [
                {
                    "operation_id": item.get("operation_id"),
                    "status": item.get("status"),
                    "levels": {
                        level.get("level"): level.get("status")
                        for level in item.get("levels", ())
                    },
                }
                for item in evaluation.get("operations", ())
                if item.get("status") != "passed"
            ]
            raise RuntimeError(
                "PHASE12_MIXED_EVALUATION_FAILED:"
                + json.dumps(failed, ensure_ascii=False)
            )
        allowed = {
            str(item["global_id"])
            for operation in application["operations"]
            for section in ("created", "modified", "removed")
            for item in operation["changes"].get(section, ())
            if item.get("global_id")
        }
        comparison = compare_ifc_models(
            damaged,
            candidate,
            allowed_changed_ids=allowed,
        )
        if not comparison["complete_preservation_success"]:
            raise RuntimeError("PHASE12_MIXED_PRESERVATION_FAILED")
        application["output"]["path"] = str(repaired)
        _write(case_root / "application.json", application)
        os.replace(candidate, repaired)
    except Exception as error:
        if application is not None and application.get("published") is True:
            blocking_code = (
                str(error).split(":", 1)[0]
                if isinstance(error, RuntimeError)
                else "PHASE12_MIXED_FINALIZATION_FAILED"
            )
            candidate_output = application.get("output")
            application["published"] = False
            application["output"] = None
            application["issues"] = [
                {
                    "code": blocking_code,
                    "path": "/publication_gate",
                    "message": "Final publication gate rejected the candidate IFC.",
                }
            ]
            application["publication_gate"] = {
                "status": "blocked",
                "blocking_code": blocking_code,
                "candidate_sha256": (
                    candidate_output.get("sha256")
                    if isinstance(candidate_output, Mapping)
                    else None
                ),
            }
            _write(case_root / "application.json", application)
        raise
    finally:
        if candidate.exists():
            candidate.unlink()
    boundary = {
        "schema_version": "text2ifc/production-input-boundary/0.2",
        "entrypoint": "run_phase12_offline.py",
        "ifc_inputs": ["damaged_ifc_path"],
        "request_inputs": ["public_request_bundle"],
        "original_ifc_supplied": False,
        "mutation_manifest_supplied": False,
        "deleted_object_ids_supplied": False,
        "private_comparator_available_during_repair": False,
        "damaged_ifc_sha256": damaged_hash,
        "request_sha256": intent.source_request_hash,
        "public_request_bundle_sha256": _sha256(public_bundle_path),
        "resolved_target_count": len(resolution.operations),
        "changeset_canonical_sha256": _text_sha256(
            json.dumps(
                changeset,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        ),
    }
    private_manifest = _mixed_private_manifest(original, damaged)
    _write(case_root / "comparison.json", comparison)
    _write(case_root / "production-boundary.json", boundary)
    _write(case_root / "mutation_manifest.private.json", private_manifest)
    manifest = {
        "schema_version": "text2ifc/phase12-offline-case/0.1",
        "case_id": case_id,
        "status": "passed",
        "provider_evidence_mode": "offline_bound_deterministic",
        "synthetic_fallback_used": False,
        "evidence_scope": "cross_scene_same_family_bimnet",
        "operation_count": len(resolution.operations),
        "operation_families": {"window": 2, "door": 2, "beam": 1, "column": 1},
        "source": private_manifest["source"],
        "damage": _read(
            FOUR_FAMILY_BASE / "validation/source-run-manifest.json"
        )["damage"],
        "production_input_boundary": boundary,
        "artifacts": _artifact_index(case_root),
    }
    _write(case_root / "manifest.json", manifest)
    return application, {"case_id": case_id, "case_root": case_root, "manifest": manifest}


def _run_structural_failure(failed_root: Path, scratch_root: Path) -> dict[str, Any]:
    case_id = "phase12-d7n-beam-column-rollback"
    case_root = failed_root / case_id
    case_root.mkdir(parents=True)
    source_hash = _sha256(D7N)
    parameters = _beam_parameters(x_mm=130000, y_mm=130000, z_mm=3000)
    operations = [
        _operation(
            case_id=case_id,
            family="beam",
            index=index,
            storey_id=D7N_COLUMN_STOREY,
            parameters=parameters,
        )
        for index in range(2)
    ]
    bundle_path = scratch_root / f"{case_id}.request.json"
    _write(bundle_path, _bundle(case_id, "Add two Beams on the same axis.", operations))
    failure_stage = ""
    try:
        run_public_repair(
            damaged_ifc=D7N,
            public_request_bundle=bundle_path,
            output_root=case_root / "attempt",
        )
    except RuntimeError as error:
        failure_stage = str(error).split(":", 1)[0]
    if failure_stage != "PUBLIC_STRUCTURAL_APPLICATION_FAILED":
        raise RuntimeError("PHASE12_STRUCTURAL_ROLLBACK_DID_NOT_FAIL")
    attempt_root = case_root / "attempt"
    application = _read(attempt_root / "application.json")
    if (
        application.get("valid") is not False
        or application.get("published") is not False
        or (attempt_root / "repaired.ifc").exists()
    ):
        raise RuntimeError("PHASE12_STRUCTURAL_ROLLBACK_PUBLICATION_LEAK")
    issues = application.get("issues")
    if not isinstance(issues, list) or not issues:
        raise RuntimeError("PHASE12_STRUCTURAL_ROLLBACK_ISSUE_MISSING")
    blocking = str(issues[0].get("code") or "")
    if blocking != "STRUCTURAL_SAME_AXIS_OVERLAP":
        raise RuntimeError("PHASE12_STRUCTURAL_ROLLBACK_CODE_MISMATCH")
    damaged_input = attempt_root / "damaged.ifc"
    changeset = _read(attempt_root / "changeset.json")
    damaged_input_hash = _sha256(damaged_input)
    changeset_fingerprint = str(changeset.get("base_model_fingerprint") or "")
    source_unchanged = (
        damaged_input_hash == source_hash
        and changeset_fingerprint == damaged_input_hash
    )
    failure = {
        "case_id": case_id,
        "status": "failed_expected",
        "valid": application["valid"],
        "published": application["published"],
        "blocking_code": blocking,
        "failure_stage": failure_stage,
        "source_unchanged": source_unchanged,
        "damaged_ifc_sha256": damaged_input_hash,
        "damaged_ifc_bytes": damaged_input.stat().st_size,
        "changeset_base_model_fingerprint": changeset_fingerprint,
    }
    _write(case_root / "failure.json", failure)
    return failure


def _run_mixed_failure(failed_root: Path) -> dict[str, Any]:
    source_hash = _sha256(FOUR_FAMILY_BASE / "02-damaged.ifc")
    application, metadata = _run_mixed_case(
        output_root=failed_root,
        duplicate_beam=True,
    )
    case_root = Path(metadata["case_root"])
    if (
        application.get("valid") is not False
        or application.get("published") is not False
        or (case_root / "repaired.ifc").exists()
    ):
        raise RuntimeError("PHASE12_MIXED_ROLLBACK_PUBLICATION_LEAK")
    issues = application.get("issues", ())
    blocking = str(issues[0].get("code")) if issues else "UNKNOWN_FAILURE"
    if blocking != "STRUCTURAL_SAME_AXIS_OVERLAP":
        raise RuntimeError("PHASE12_MIXED_ROLLBACK_CODE_MISMATCH")
    damaged_input = case_root / "damaged.ifc"
    changeset = _read(case_root / "changeset.json")
    damaged_input_hash = _sha256(damaged_input)
    changeset_fingerprint = str(changeset.get("base_model_fingerprint") or "")
    source_unchanged = (
        damaged_input_hash == source_hash
        and changeset_fingerprint == damaged_input_hash
    )
    failure = {
        "case_id": metadata["case_id"],
        "status": "failed_expected",
        "valid": application["valid"],
        "published": application["published"],
        "blocking_code": blocking,
        "source_unchanged": source_unchanged,
        "damaged_ifc_sha256": damaged_input_hash,
        "damaged_ifc_bytes": damaged_input.stat().st_size,
        "changeset_base_model_fingerprint": changeset_fingerprint,
    }
    _write(case_root / "failure.json", failure)
    return failure


def run_offline_matrix(
    output_root: Path | str = DEFAULT_OUTPUT,
    *,
    case_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    output = Path(output_root).resolve()
    if output.exists():
        raise FileExistsError(f"Phase 12 offline output already exists: {output}")
    output.mkdir(parents=True)
    accepted_root = output / "accepted"
    failed_root = output / "failed"
    accepted_root.mkdir()
    selected = tuple(case_ids) if case_ids is not None else SUCCESS_CASE_IDS
    unknown = set(selected) - set(SUCCESS_CASE_IDS)
    if unknown:
        raise ValueError(f"PHASE12_OFFLINE_CASE_UNKNOWN:{sorted(unknown)}")
    if len(set(selected)) != len(selected):
        raise ValueError("PHASE12_OFFLINE_CASE_DUPLICATE")

    accepted: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    specs = _structural_specs()
    with tempfile.TemporaryDirectory(prefix="phase12-offline-", dir=output) as tmp:
        scratch = Path(tmp)
        for case_id in selected:
            if case_id in specs:
                accepted.append(
                    _run_structural_case(
                        case_id=case_id,
                        spec=specs[case_id],
                        accepted_root=accepted_root,
                        scratch_root=scratch,
                    )
                )
            else:
                _, metadata = _run_mixed_case(
                    output_root=accepted_root,
                    duplicate_beam=False,
                )
                manifest = metadata["manifest"]
                accepted.append(
                    {
                        "case_id": case_id,
                        "status": "passed",
                        "relative_path": Path(metadata["case_root"])
                        .relative_to(output)
                        .as_posix(),
                        "operation_count": int(manifest["operation_count"]),
                        "operation_types": sorted(
                            {
                                item["operation_type"]
                                for item in _read(
                                    Path(metadata["case_root"]) / "changeset.json"
                                )["operations"]
                            }
                        ),
                    }
                )
        if case_ids is None:
            failures.append(_run_structural_failure(failed_root, scratch))
            failures.append(_run_mixed_failure(failed_root))

    accepted_ids = {item["case_id"] for item in accepted}
    failure_ids = {item["case_id"] for item in failures}
    coverage = {
        "beam_only": "phase12-d7n-beam-loadbearing" in accepted_ids,
        "column_only": "phase12-d7n-column-loadbearing" in accepted_ids,
        "beam_column_atomic": "phase12-d7n-beam-column-atomic" in accepted_ids,
        "beam_loadbearing": "phase12-d7n-beam-loadbearing" in accepted_ids,
        "column_loadbearing": "phase12-d7n-column-loadbearing" in accepted_ids,
        "material_present": "phase12-vvo-beam-material-present" in accepted_ids,
        "material_absent": "phase12-vvo-column-material-absent" in accepted_ids,
        "rollback": "phase12-d7n-beam-column-rollback" in failure_ids,
        "door_window_beam_column_atomic": (
            "phase12-vvo-door-window-beam-column-atomic" in accepted_ids
        ),
        "door_window_beam_column_rollback": (
            "phase12-vvo-door-window-beam-column-rollback" in failure_ids
        ),
    }
    matrix_complete = (
        case_ids is None
        and accepted_ids == set(SUCCESS_CASE_IDS)
        and failure_ids == set(FAILURE_CASE_IDS)
        and all(coverage.values())
    )
    summary = {
        "schema_version": "text2ifc/phase12-offline-matrix/0.1",
        "status": "passed" if matrix_complete else "partial",
        "matrix_complete": matrix_complete,
        "evidence_scope": "cross_scene_same_family_bimnet",
        "accepted_cases": accepted,
        "failed_cases": failures,
        "coverage": coverage,
    }
    _write(output / "run-summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args(argv)
    result = run_offline_matrix(arguments.output_root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
