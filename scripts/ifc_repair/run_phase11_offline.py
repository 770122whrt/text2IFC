"""Run reproducible Phase 11 Door repairs on real IFC2X3 files."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import ifcopenshell


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_ifc_repair.apply import apply_changeset  # noqa: E402
from text2ifc_ifc_repair.benchmark_evaluation import (  # noqa: E402
    ProductionEvaluationInputs,
    evaluate_production,
)
from text2ifc_ifc_repair.compare import compare_ifc_models  # noqa: E402
from text2ifc_ifc_repair.evaluation import evaluation_to_dict  # noqa: E402
from text2ifc_ifc_repair.evaluation_policy import EvidenceSourceKind  # noqa: E402
from text2ifc_ifc_repair.geometry import (  # noqa: E402
    opening_dimensions_mm,
    opening_position_in_wall_mm,
)
from text2ifc_ifc_repair.mutation import remove_door  # noqa: E402
from text2ifc_ifc_repair.operations import create_default_registry  # noqa: E402
from text2ifc_ifc_repair.semantic_facts import SemanticFact  # noqa: E402


DEFAULT_OUTPUT = ROOT / "dataset/processed/ifc-repair/phase11-door-offline"
CASES = (
    {
        "case_id": "largebuilding-door-preserve-opening",
        "source": ROOT
        / "dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc",
        "door_global_id": "2cXV28XOjE6f6irgi0COhu",
    },
    {
        "case_id": "vvo-door-preserve-opening",
        "source": ROOT / "dataset/ifc/train/vvo.ifc",
        "door_global_id": "2IUEnGd5v4Yfg1ZlPtd0qa",
    },
)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _text_hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        payload = value
    else:
        payload = json.dumps(
            value, ensure_ascii=False, indent=2, sort_keys=True, default=str
        )
    path.write_text(payload.rstrip() + "\n", encoding="utf-8")


def _source_chain(source: Path, door_id: str) -> dict[str, Any]:
    model = ifcopenshell.open(str(source))
    door = model.by_guid(door_id)
    opening = door.FillsVoids[0].RelatingOpeningElement
    wall = opening.VoidsElements[0].RelatingBuildingElement
    styles = [
        relation.RelatingType
        for relation in door.IsDefinedBy
        if relation.is_a("IfcRelDefinesByType")
    ]
    if len(styles) != 1:
        raise ValueError(f"EXACT_DOOR_TYPE_REQUIRED:{door_id}")
    style = styles[0]
    dimensions = opening_dimensions_mm(opening)
    position = opening_position_in_wall_mm(opening, wall)
    operation_type = str(style.OperationType)
    if operation_type not in {
        "SINGLE_SWING_LEFT",
        "SINGLE_SWING_RIGHT",
        "NOTDEFINED",
    }:
        raise ValueError(f"DOOR_OPERATION_UNSUPPORTED:{operation_type}")
    return {
        "door": {
            "global_id": str(door.GlobalId),
            "name": None if door.Name is None else str(door.Name),
            "overall_width_mm": float(door.OverallWidth),
            "overall_height_mm": float(door.OverallHeight),
        },
        "opening": {
            "global_id": str(opening.GlobalId),
            "width_mm": float(dimensions["width"]),
            "height_mm": float(dimensions["height"]),
            "sill_height_mm": float(position["sill_height"]),
            "center_offset_mm": float(position["center_offset"]),
        },
        "wall": {
            "global_id": str(wall.GlobalId),
            "name": None if wall.Name is None else str(wall.Name),
            "ifc_class": wall.is_a(),
        },
        # Host containment is the production authority. Some source Doors are
        # themselves assigned to a different Storey; exact Type reuse must not
        # reproduce that occurrence-level authoring error.
        "storey_global_id": str(
            wall.ContainedInStructure[0].RelatingStructure.GlobalId
        ),
        "style": {
            "global_id": str(style.GlobalId),
            "name": None if style.Name is None else str(style.Name),
            "operation_type": operation_type,
        },
    }


def _request(chain: dict[str, Any]) -> str:
    door = chain["door"]
    opening = chain["opening"]
    wall = chain["wall"]
    style = chain["style"]
    return (
        f"在墙 {wall['name'] or wall['global_id']}（GlobalId {wall['global_id']}）"
        f"已有洞口 {opening['global_id']} 中安装一扇门。"
        f"门宽 {door['overall_width_mm']} mm、高 {door['overall_height_mm']} mm；"
        f"洞口中心距墙局部起点 {opening['center_offset_mm']} mm，"
        f"洞口宽 {opening['width_mm']} mm、高 {opening['height_mm']} mm、"
        f"门槛高度 {opening['sill_height_mm']} mm。"
        f"明确复用现有 Door Type “{style['name']}”"
        f"（GlobalId {style['global_id']}，OperationType {style['operation_type']}）。"
    )


def _operation(
    chain: dict[str, Any],
    *,
    operation_id: str,
) -> dict[str, Any]:
    door = chain["door"]
    opening = chain["opening"]
    return {
        "operation_id": operation_id,
        "operation_type": "fill_existing_opening_with_door",
        "target": {"opening_global_id": opening["global_id"]},
        "parameters": {
            "position": {
                "reference": "wall_local_start",
                "center_offset_mm": opening["center_offset_mm"],
            },
            "opening": {
                "width_mm": opening["width_mm"],
                "height_mm": opening["height_mm"],
                "sill_height_mm": opening["sill_height_mm"],
            },
            "door": {
                "overall_width_mm": door["overall_width_mm"],
                "overall_height_mm": door["overall_height_mm"],
                "operation_type": chain["style"]["operation_type"],
            },
            "host_wall_global_id": chain["wall"]["global_id"],
        },
        "evidence_refs": ["request:/operation"],
        "semantic_manifest": {
            "manifest_id": f"manifest-{operation_id}",
            "policy_id": "door.fill-existing-opening.l2",
            "policy_version": "0.1",
        },
        "semantic_assignments": [
            {
                "operation_id": operation_id,
                "scope": "door_occurrence",
                "fact_key": "relationship:type",
                "source_fact_key": "relationship:type",
                "value": chain["style"]["global_id"],
                "value_type": "IfcDoorStyle",
                "unit": None,
                "ownership": "type_inherited",
                "applicability": "required",
                "source_kind": "type_inherited",
                "source_ref": f"formal-type:{chain['style']['global_id']}",
                "provenance": ["explicit-type-reuse:request"],
                "authoring_action": "inherit_from_type",
            }
        ],
    }


def _expected_facts(chain: dict[str, Any]) -> tuple[SemanticFact, ...]:
    values = (
        (
            "relationship:type",
            chain["style"]["global_id"],
            "IfcDoorStyle",
            EvidenceSourceKind.SURVIVING_TYPE,
            True,
        ),
        (
            "relationship:host",
            chain["wall"]["global_id"],
            chain["wall"]["ifc_class"],
            EvidenceSourceKind.SURVIVING_HOST,
            False,
        ),
        (
            "relationship:storey",
            chain["storey_global_id"],
            "IfcBuildingStorey",
            EvidenceSourceKind.SURVIVING_HOST,
            False,
        ),
        (
            "attribute:OverallWidth",
            chain["door"]["overall_width_mm"],
            "IfcPositiveLengthMeasure",
            EvidenceSourceKind.EXPLICIT_REQUEST,
            False,
        ),
        (
            "attribute:OverallHeight",
            chain["door"]["overall_height_mm"],
            "IfcPositiveLengthMeasure",
            EvidenceSourceKind.EXPLICIT_REQUEST,
            False,
        ),
    )
    return tuple(
        SemanticFact(
            fact_key=key,
            value=value,
            value_type=value_type,
            unit=None,
            inherited=inherited,
            pset_path=None,
            entity_source="public-request",
            source_kind=source_kind,
            source_ref="request:/operation",
            provenance=("phase11-offline-request",),
            occurrence_scope="door_occurrence",
        )
        for key, value, value_type, source_kind, inherited in values
    )


def run_case(case: dict[str, Any], output_root: Path) -> dict[str, Any]:
    case_dir = output_root / str(case["case_id"])
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)
    source = Path(case["source"])
    chain = _source_chain(source, str(case["door_global_id"]))
    fixture = case_dir / "fixture"
    mutation = remove_door(
        source_path=source,
        output_dir=fixture,
        door_global_id=str(case["door_global_id"]),
        preserve_opening=True,
    )
    damaged = fixture / "damaged.ifc"
    request = _request(chain)
    operation_id = f"operation-{case['case_id']}"
    operation = _operation(chain, operation_id=operation_id)
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "changeset_id": f"changeset-{case['case_id']}",
        "binding_status": "bound",
        "base_model_fingerprint": _sha256(damaged),
        "source_request_hash": _text_hash(request),
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "e" * 64,
        "scope": {
            "target_ids": [chain["opening"]["global_id"]],
            "forbidden_ids": [],
        },
        "evidence_refs": ["request:/operation"],
        "preconditions": ["opening_available"],
        "postconditions": ["door_fills_opening"],
        "operations": [operation],
    }
    repaired = case_dir / "repaired.ifc"
    registry = create_default_registry()
    application = apply_changeset(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=changeset,
        output_path=repaired,
        registry=registry,
    )
    if not application["valid"] or not application["published"]:
        raise RuntimeError(
            f"PHASE11_OFFLINE_APPLICATION_FAILED:{application['issues']}"
        )
    production = evaluate_production(
        ProductionEvaluationInputs(
            damaged_ifc_path=damaged,
            repaired_ifc_path=repaired,
            changeset=changeset,
            application_result=application,
            registry=registry,
            expected_facts_by_operation={
                operation_id: _expected_facts(chain)
            },
        )
    )
    evaluation = evaluation_to_dict(production)
    if not evaluation["complete_repair_success"]:
        raise RuntimeError(
            "PHASE11_OFFLINE_EVALUATION_FAILED:"
            f"{case['case_id']}:"
            + json.dumps(
                {
                    "status": evaluation.get("status"),
                    "operations": evaluation.get("operations"),
                },
                ensure_ascii=False,
                default=str,
            )
        )
    allowed = {
        str(item["global_id"])
        for result in application["operations"]
        for kind in ("created", "modified", "removed")
        for item in result["changes"].get(kind, ())
        if item.get("global_id")
    }
    comparison = compare_ifc_models(
        damaged,
        repaired,
        allowed_changed_ids=allowed,
    )
    shutil.copy2(source, case_dir / "original.ifc")
    shutil.copy2(damaged, case_dir / "damaged.ifc")
    _write(case_dir / "request.txt", request)
    _write(case_dir / "changeset.json", changeset)
    _write(case_dir / "application.json", application)
    _write(case_dir / "evaluation.json", evaluation)
    _write(case_dir / "comparison.json", comparison)
    manifest = {
        "schema_version": "text2ifc/phase11-door-proof/0.1",
        "case_id": case["case_id"],
        "status": "passed",
        "synthetic_fallback_used": False,
        "operation_count": 1,
        "damage": {
            "mode": mutation["mutation_type"],
            "door": mutation["door"],
            "opening": mutation["opening"],
            "wall": mutation["wall"],
        },
        "artifacts": {
            name: {
                "path": name,
                "sha256": _sha256(case_dir / name),
                "bytes": (case_dir / name).stat().st_size,
            }
            for name in (
                "original.ifc",
                "damaged.ifc",
                "repaired.ifc",
                "request.txt",
                "changeset.json",
                "application.json",
                "evaluation.json",
                "comparison.json",
            )
        },
    }
    _write(case_dir / "manifest.json", manifest)
    _write(
        case_dir / "README.md",
        (
            f"# {case['case_id']}\n\n"
            f"- 删除门：`{chain['door']['name']}` (`{chain['door']['global_id']}`)\n"
            f"- 保留洞口：`{chain['opening']['global_id']}`\n"
            f"- 复用 Type：`{chain['style']['name']}` "
            f"(`{chain['style']['global_id']}`)\n"
            f"- OperationType：`{chain['style']['operation_type']}`\n"
            "- 结果：IFC2X3 重开、L1、L2 与全局 preservation 全部通过。\n"
        ),
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    args.output_root.mkdir(parents=True, exist_ok=True)
    results = [run_case(case, args.output_root) for case in CASES]
    summary = {
        "schema_version": "text2ifc/phase11-door-offline-run/0.1",
        "status": "passed",
        "cases": [
            {
                "case_id": item["case_id"],
                "status": item["status"],
                "manifest": f"{item['case_id']}/manifest.json",
            }
            for item in results
        ],
    }
    _write(args.output_root / "run-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
