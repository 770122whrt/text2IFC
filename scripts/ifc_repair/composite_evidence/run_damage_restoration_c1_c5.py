"""Genuine live runner for the C1-C5 damage-restoration case set (non-vvo).

Mirrors ``run_damage_restoration.py`` but loads the C1-C5 freeze
(``damage-restoration-c1-c5-freeze.json``: sixty5/str, 1px, d7n) and
applies the corresponding damage recipes (beams/columns via
``remove_structural_members``; doors via ``remove_doors_batch`` preserving
openings; windows via ``remove_windows_and_openings_batch``).  The repair
runs against the live Provider through the production ``RepairAPI`` public
path, then the repaired model is compared with the original.

Large models (sixty5, 117k entities) need an evaluation deadline above the
180 s default; the deadline is raised through the public orchestrator
``evaluation_stage`` seam — every gate still runs.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
for p in (str(ROOT), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from text2ifc_knowledge.property_search import (  # noqa: E402
    _prepare_windows_torch_runtime,
)

_prepare_windows_torch_runtime()

import ifcopenshell  # noqa: E402

from scripts.ifc_repair import run_phase12_live_uat as live  # noqa: E402
from scripts.ifc_repair.composite_evidence import baseline_fingerprint  # noqa: E402
from scripts.ifc_repair.composite_evidence.restoration_debug import (  # noqa: E402
    compare_damage_restoration,
)
from scripts.ifc_repair.composite_evidence.run_c1_c5_light_preflight import (  # noqa: E402
    load_light_preflight_evidence,
)
from text2ifc_agent.openai_compat import (  # noqa: E402
    OpenAICompatibleLiveProvider,
    load_openai_compatible_runtime_config,
)
from text2ifc_knowledge import (  # noqa: E402
    create_property_runtime_from_environment,
)
from text2ifc_knowledge.property_runtime import (  # noqa: E402
    PROPERTY_BGE_MODEL_PATH_ENV,
    PROPERTY_QDRANT_PATH_ENV,
)
from text2ifc_ifc_repair.api import RepairAPI  # noqa: E402
from text2ifc_ifc_repair.benchmark_evaluation import evaluate_production  # noqa: E402
from text2ifc_ifc_repair.evaluation import (  # noqa: E402
    EvaluationExecutionPolicy,
)
from text2ifc_ifc_repair.mutation import (  # noqa: E402
    remove_doors_batch,
    remove_structural_members,
    remove_windows_and_openings_batch,
)
from text2ifc_ifc_repair.orchestrator import RepairOrchestrator  # noqa: E402
from text2ifc_ifc_repair.type_templates import (  # noqa: E402
    type_authority_fingerprint,
)

DOC_DIR = ROOT / "docs" / "validation" / "repair-composite-milestone"
FREEZE_PATH = DOC_DIR / "damage-restoration-c1-c5-freeze.json"
FREEZE = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
RESULT_SCHEMA = "text2ifc/damage-restoration-c1-c5-execution-result/0.1"
TARGET_MATCH_TOLERANCE_MM = 0.1
TYPE_CLASS_BY_DAMAGE_KEY = {
    "beams": ("IfcBeam", "IfcBeamType", "restore-beam"),
    "columns": ("IfcColumn", "IfcColumnType", "restore-column"),
    "doors": ("IfcDoor", "IfcDoorStyle", "restore-door"),
    "windows": ("IfcWindow", "IfcWindowStyle", "restore-window"),
}
OPERATION_TYPE_BY_DAMAGE_KEY = {
    "beams": "add_beam",
    "columns": "add_column",
    "doors": "fill_existing_opening_with_door",
    "windows": "add_window_with_opening_to_wall",
}


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _public_repair_request(case: Mapping[str, Any]) -> str:
    request = str(case["request"]).strip()
    request = (
        f"{request} Use a target-matching tolerance of "
        f"{TARGET_MATCH_TOLERANCE_MM:g} mm for every stated millimetre "
        "geometry selector; this tolerance applies only to identifying "
        "existing IFC targets, not to the dimensions created or restored."
    )
    if "operation type NOTDEFINED" in request:
        request += (
            " For every Door explicitly requested with operation type "
            "NOTDEFINED, I explicitly accept NOTDEFINED."
        )
    return request


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _large_model_evaluation_stage(inputs):
    return evaluate_production(
        replace(
            inputs,
            execution_policy=EvaluationExecutionPolicy(deadline_seconds=900.0),
        )
    )


def _orchestrator_factory(**kwargs):
    kwargs["evaluation_stage"] = _large_model_evaluation_stage
    return RepairOrchestrator(**kwargs)


def _prepare_property_runtime_environment(
    environment: Mapping[str, str],
    *,
    cache_root: Path | None,
) -> dict[str, str]:
    prepared = dict(environment)
    if cache_root is None:
        return prepared
    resolved_cache = cache_root.resolve()
    model_path = resolved_cache / "models" / "BAAI-bge-m3"
    if not model_path.is_dir():
        raise RuntimeError("PROPERTY_BGE_MODEL_CACHE_MISSING")
    prepared.setdefault(PROPERTY_BGE_MODEL_PATH_ENV, str(model_path))
    prepared.setdefault(
        PROPERTY_QDRANT_PATH_ENV,
        str((resolved_cache / "property-resolution" / "qdrant").resolve()),
    )
    return prepared


def _require_ready_property_runtime(runtime: Any) -> None:
    health = getattr(runtime, "health", None)
    if (
        health is None
        or getattr(health, "status", None) != "ready"
        or getattr(health, "acceptance_eligible", None) is not True
    ):
        reason = getattr(health, "reason_code", None)
        raise RuntimeError(reason or "PROPERTY_RUNTIME_NOT_READY")


def _updated_transport_call_count(
    current: int,
    attempts: list[Mapping[str, Any]],
) -> int:
    return current + len(attempts)


def _matches_expected_value(expected: Any, actual: Any) -> bool:
    if isinstance(expected, Mapping):
        return isinstance(actual, Mapping) and all(
            key in actual and _matches_expected_value(value, actual[key])
            for key, value in expected.items()
        )
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return (
            isinstance(actual, (int, float))
            and not isinstance(actual, bool)
            and abs(float(expected) - float(actual)) <= 1e-3
        )
    return expected == actual


def _expected_operation_content(
    key: str,
    member: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if key == "beams":
        return {}, {
            "axis": member["axis"],
            "section": {
                "shape": "rectangle",
                "width_mm": member["section"]["width_mm"],
                "height_mm": member["section"]["height_mm"],
            },
        }
    if key == "columns":
        return {}, {
            "axis": member["axis"],
            "section": {
                "shape": "rectangle",
                "width_mm": member["section"]["width_mm"],
                "depth_mm": member["section"]["depth_mm"],
            },
        }
    if key == "doors":
        return {"opening_global_id": member["opening"]["gid"]}, {}
    opening = member["opening"]
    return {"wall_global_id": member["wall_query"]["wall_global_id"]}, {
        "position": {
            "reference": "wall_local_start",
            "center_offset_mm": opening["center_offset_mm"],
        },
        "opening": {
            "width_mm": opening["width_mm"],
            "height_mm": opening["height_mm"],
            "sill_height_mm": opening["sill_height_mm"],
        },
    }


def _resolve_restoration_tags(
    case: Mapping[str, Any],
    bound_changeset: Mapping[str, Any],
) -> dict[str, list[str]]:
    """Bind frozen damage roles to actual provider operation IDs by content."""

    operations = list(bound_changeset.get("operations") or ())
    relevant_types = set(OPERATION_TYPE_BY_DAMAGE_KEY.values())
    expected_count = sum(
        len(case["damage"].get(key, ()))
        for key in OPERATION_TYPE_BY_DAMAGE_KEY
    )
    relevant_operations = [
        operation
        for operation in operations
        if operation.get("operation_type") in relevant_types
    ]
    if len(relevant_operations) != expected_count:
        raise ValueError("RESTORATION_OPERATION_BINDING_CARDINALITY")
    result = {key: [] for key in OPERATION_TYPE_BY_DAMAGE_KEY}
    used_ids: set[str] = set()
    for key, operation_type in OPERATION_TYPE_BY_DAMAGE_KEY.items():
        for member in case["damage"].get(key, ()):
            expected_target, expected_parameters = _expected_operation_content(
                key, member
            )
            matches = [
                operation
                for operation in relevant_operations
                if operation.get("operation_type") == operation_type
                and str(operation.get("operation_id") or "") not in used_ids
                and _matches_expected_value(
                    expected_target, operation.get("target") or {}
                )
                and _matches_expected_value(
                    expected_parameters, operation.get("parameters") or {}
                )
            ]
            if len(matches) != 1:
                reason = "MISSING" if not matches else "AMBIGUOUS"
                raise ValueError(
                    f"RESTORATION_OPERATION_BINDING_{reason}:{key}"
                )
            operation_id = str(matches[0]["operation_id"])
            used_ids.add(operation_id)
            result[key].append(operation_id)
    return result


def _apply_damage(case: Mapping[str, Any], case_root: Path) -> Path:
    source = ROOT / str(case["source"])
    scratch = case_root / "damage"
    beams = [m["gid"] for m in case["damage"].get("beams", [])]
    columns = [m["gid"] for m in case["damage"].get("columns", [])]
    doors = case["damage"].get("doors", [])
    windows = case["damage"].get("windows", [])
    current = source
    if beams or columns:
        remove_structural_members(
            source_path=source,
            output_dir=scratch / "structural",
            beam_global_ids=tuple(beams),
            column_global_ids=tuple(columns),
        )
        current = scratch / "structural" / "damaged.ifc"
    if doors:
        remove_doors_batch(
            source_path=current,
            output_dir=scratch / "doors",
            door_global_ids=[d["gid"] for d in doors],
            preserve_openings=True,
        )
        current = scratch / "doors" / "damaged.ifc"
    if windows:
        remove_windows_and_openings_batch(
            source_path=current,
            output_dir=scratch / "windows",
            targets=[
                {
                    "wall_global_id": w["wall_query"]["wall_global_id"],
                    "window_global_id": w["gid"],
                    "opening_global_id": w["opening_gid"],
                }
                for w in windows
            ],
        )
        current = scratch / "windows" / "damaged.ifc"
    return current


def _single_type_global_id(entity: Any) -> str:
    matches = [
        relation.RelatingType
        for relation in entity.IsDefinedBy
        if relation.is_a("IfcRelDefinesByType")
    ]
    if len(matches) != 1:
        raise ValueError("DAMAGE_RESTORATION_TYPE_BINDING_AMBIGUOUS")
    return str(matches[0].GlobalId)


def _by_guid_optional(model: Any, global_id: str) -> Any | None:
    try:
        return model.by_guid(global_id)
    except RuntimeError:
        return None


def _type_reuse_preflight(
    case: Mapping[str, Any],
    *,
    original_model: Any,
    damaged_model: Any,
) -> dict[str, Any]:
    """Require every restoration Type to survive damage unchanged."""

    records = []
    for key, (occurrence_class, type_class, _) in (
        TYPE_CLASS_BY_DAMAGE_KEY.items()
    ):
        for member in case["damage"].get(key, []):
            prototype = member.get("prototype_intent")
            if (
                not isinstance(prototype, Mapping)
                or prototype.get("reference_kind") != "global_id"
                or not str(prototype.get("reference", ""))
            ):
                raise ValueError("DAMAGE_RESTORATION_TYPE_REUSE_REQUIRED")
            type_global_id = str(prototype["reference"])
            original_occurrence = _by_guid_optional(
                original_model, str(member["gid"])
            )
            if (
                original_occurrence is None
                or not original_occurrence.is_a(occurrence_class)
                or _single_type_global_id(original_occurrence)
                != type_global_id
            ):
                raise ValueError("DAMAGE_RESTORATION_TYPE_REFERENCE_MISMATCH")
            surviving_type = _by_guid_optional(damaged_model, type_global_id)
            if surviving_type is None or not surviving_type.is_a(type_class):
                raise ValueError("DAMAGE_RESTORATION_TYPE_REUSE_UNAVAILABLE")
            records.append(
                {
                    "damage_key": key,
                    "type_class": type_class,
                    "type_global_id": type_global_id,
                    "fingerprint": type_authority_fingerprint(surviving_type),
                }
            )
    return {"status": "passed", "types": records}


def _verify_exact_type_reuse(
    case: Mapping[str, Any],
    *,
    damaged_model: Any,
    repaired_model: Any,
    preflight: Mapping[str, Any],
    repaired_tags: Mapping[str, list[str]] | None = None,
) -> dict[str, Any]:
    type_counts_unchanged = all(
        len(repaired_model.by_type(type_class))
        == len(damaged_model.by_type(type_class))
        for type_class in {value[1] for value in TYPE_CLASS_BY_DAMAGE_KEY.values()}
    )
    type_graphs_unchanged = all(
        (
            (
                entity := _by_guid_optional(
                    repaired_model, str(record["type_global_id"])
                )
            )
            is not None
            and type_authority_fingerprint(entity) == record["fingerprint"]
        )
        for record in preflight["types"]
    )
    occurrence_bindings_exact = True
    for key, (occurrence_class, _, tag_prefix) in (
        TYPE_CLASS_BY_DAMAGE_KEY.items()
    ):
        for index, member in enumerate(
            case["damage"].get(key, []), start=1
        ):
            tag = (
                repaired_tags[key][index - 1]
                if repaired_tags is not None
                else f"{tag_prefix}-{index}"
            )
            matches = [
                entity
                for entity in repaired_model.by_type(occurrence_class)
                if str(entity.Tag) == tag
            ]
            occurrence_bindings_exact = occurrence_bindings_exact and (
                len(matches) == 1
                and _single_type_global_id(matches[0])
                == str(member["prototype_intent"]["reference"])
            )
    valid = (
        type_counts_unchanged
        and type_graphs_unchanged
        and occurrence_bindings_exact
    )
    return {
        "status": "passed" if valid else "failed",
        "type_counts_unchanged": type_counts_unchanged,
        "type_graphs_unchanged": type_graphs_unchanged,
        "occurrence_bindings_exact": occurrence_bindings_exact,
    }


def _execute_case(
    *,
    case: Mapping[str, Any],
    provider: Any,
    case_root: Path,
    _property_runtime: Any = None,
) -> dict[str, Any]:
    source = ROOT / str(case["source"])
    damaged = _apply_damage(case, case_root)

    damaged_model = ifcopenshell.open(str(damaged))
    original_model = ifcopenshell.open(str(source))
    type_reuse_preflight = _type_reuse_preflight(
        case,
        original_model=original_model,
        damaged_model=damaged_model,
    )
    damage_summary = {
        "beams_removed": len(case["damage"].get("beams", [])),
        "columns_removed": len(case["damage"].get("columns", [])),
        "doors_removed": len(case["damage"].get("doors", [])),
        "windows_removed": len(case["damage"].get("windows", [])),
        "beam_count": (
            len(original_model.by_type("IfcBeam")),
            len(damaged_model.by_type("IfcBeam")),
        ),
        "column_count": (
            len(original_model.by_type("IfcColumn")),
            len(damaged_model.by_type("IfcColumn")),
        ),
        "door_count": (
            len(original_model.by_type("IfcDoor")),
            len(damaged_model.by_type("IfcDoor")),
        ),
        "window_count": (
            len(original_model.by_type("IfcWindow")),
            len(damaged_model.by_type("IfcWindow")),
        ),
        "damaged_sha256": _sha256_path(damaged),
        "source_sha256": _sha256_path(source),
        "type_reuse_preflight": type_reuse_preflight,
    }

    runtime = case_root / "runtime"
    api = RepairAPI(
        runtime,
        provider=provider,
        orchestrator_factory=_orchestrator_factory,
        property_knowledge_runtime=_property_runtime,
        intent_schema_version=live.REPAIR_INTENT_SCHEMA_VERSION_0_8,
    )
    provider.set_lineage("initial")
    started = time.monotonic()
    initial = api.start(damaged, _public_repair_request(case))
    latency_seconds = round(time.monotonic() - started, 3)
    summary = live._result_summary(initial)

    comparison_payload = None
    repaired_path = None
    if summary.get("status") == "succeeded":
        runs_root = runtime / "runs"
        run_root = (
            runs_root / "runs" / str(summary["run_id"])
            if (runs_root / "runs" / str(summary["run_id"])).is_dir()
            else runs_root / str(summary["run_id"])
        )
        repaired_path = (
            run_root / str(summary["artifacts"]["successful_ifc"])
        )
        bound_changeset = json.loads(
            (run_root / "changeset/bound-changeset.json").read_text(
                encoding="utf-8"
            )
        )
        repaired_tags = _resolve_restoration_tags(case, bound_changeset)
        focused_debug = compare_damage_restoration(
            case,
            original_path=source,
            repaired_path=repaired_path,
            repaired_tags=repaired_tags,
        )
        comparison = focused_debug["whole_model_ifccompare"]
        repaired_model = ifcopenshell.open(str(repaired_path))
        type_reuse = _verify_exact_type_reuse(
            case,
            damaged_model=damaged_model,
            repaired_model=repaired_model,
            preflight=type_reuse_preflight,
            repaired_tags=repaired_tags,
        )
        counts = {
            ifc_class: {
                "original": len(original_model.by_type(ifc_class)),
                "repaired": len(repaired_model.by_type(ifc_class)),
            }
            for ifc_class in (
                "IfcBeam",
                "IfcColumn",
                "IfcWall",
                "IfcDoor",
                "IfcWindow",
                "IfcOpeningElement",
            )
        }
        comparison_payload = {
            **comparison,
            "comparator": (
                "text2ifc_ifc_repair.compare.compare_ifc_models"
            ),
            "comparison_mode": "private_post_repair_original_comparison",
            "added_ids_count": len(comparison.get("added_ids") or []),
            "removed_ids_count": len(comparison.get("removed_ids") or []),
            "modified_ids_count": len(comparison.get("modified_ids") or []),
            "unexpected_changed_ids_count": len(
                comparison.get("unexpected_changed_ids") or []
            ),
            "class_counts": counts,
            "class_counts_restored": all(
                item["original"] == item["repaired"]
                for item in counts.values()
            ),
            "exact_type_reuse": type_reuse,
            "restoration_operation_bindings": repaired_tags,
            "focused_geometry_property_debug": focused_debug,
            "identity_equivalent": bool(
                comparison.get("complete_preservation_success")
            ),
        }
        private_evaluation_passed = (
            comparison_payload["comparison_status"] == "passed"
            and comparison_payload["class_counts_restored"]
            and type_reuse["status"] == "passed"
            and focused_debug["status"] == "passed"
        )
        comparison_payload["restoration_acceptance_status"] = (
            "passed" if private_evaluation_passed else "failed"
        )
        if not private_evaluation_passed:
            summary = {
                **summary,
                "status": "not_publishable",
                "reason_code": "DAMAGE_RESTORATION_PRIVATE_EVALUATION_FAILED",
                "complete_repair_success": False,
                "successful_artifact_publishable": False,
            }

    return {
        **summary,
        "damage": damage_summary,
        "latency_seconds": latency_seconds,
        "original_comparison": comparison_payload,
        "repaired_ifc_path": str(repaired_path) if repaired_path else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-genuine", action="store_true")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT
        / "dataset/processed/ifc-repair-runs/repair-damage-restoration-c1-c5",
    )
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument(
        "--property-cache-root",
        type=Path,
        help=(
            "explicit shared cache containing models/BAAI-bge-m3 and "
            "property-resolution/qdrant"
        ),
    )
    parser.add_argument(
        "--preflight-evidence",
        type=Path,
        help=(
            "machine-readable, zero-network full or C1-C5 light "
            "preflight.json; required for --execute-genuine"
        ),
    )
    parser.add_argument(
        "--case",
        action="append",
        default=None,
        help="execute only these case ids (repeatable)",
    )
    args = parser.parse_args()

    output_root = args.output_root.resolve()
    if output_root.exists() and any(output_root.iterdir()):
        print(f"ERROR: output root not empty: {output_root}", file=sys.stderr)
        return 2
    output_root.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "created_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "freeze_sha256": "sha256:"
        + hashlib.sha256(FREEZE_PATH.read_bytes()).hexdigest(),
        "semantics": FREEZE["semantics"],
        "status": "not_started",
        "cases": [],
    }

    drift = baseline_fingerprint.cmd_verify()
    result["preflight_fingerprint"] = (
        "clean" if drift == 0 else f"DRIFT:{drift}"
    )
    if drift != 0:
        result["status"] = "blocked"
        result["reason_code"] = "DAMAGE_RESTORATION_C1_C5_BASELINE_DRIFT"
        _write_json(output_root / "execution-result.json", result)
        return 1
    if not args.execute_genuine:
        result["status"] = "ready_for_genuine_execution"
        _write_json(output_root / "execution-result.json", result)
        print(json.dumps({"status": result["status"]}, ensure_ascii=False))
        return 0

    if args.preflight_evidence is None:
        result["status"] = "blocked"
        result["reason_code"] = "FULL_PREFLIGHT_EVIDENCE_REQUIRED"
        _write_json(output_root / "execution-result.json", result)
        return 1
    try:
        try:
            preflight = load_light_preflight_evidence(
                args.preflight_evidence
            )
        except ValueError as light_error:
            try:
                preflight = live._load_green_full_preflight_evidence(
                    args.preflight_evidence
                )
            except ValueError:
                raise light_error
    except Exception as error:
        result["status"] = "blocked"
        result["reason_code"] = (
            f"FULL_PREFLIGHT_EVIDENCE_INVALID:{type(error).__name__}"
        )
        result["preflight_error"] = str(error)[:512]
        _write_json(output_root / "execution-result.json", result)
        return 1
    result["preflight"] = {
        "status": preflight["status"],
        "mode": preflight["mode"],
        "evidence_path": preflight["evidence_path"],
        "evidence_file_sha256": preflight["evidence_file_sha256"],
        "network_transport_attempted": preflight[
            "network_transport_attempted"
        ],
        "checks": [
            {
                "name": check["name"],
                "status": check["status"],
                "result_sha256": check["result_sha256"],
            }
            for check in preflight["checks"]
        ],
    }

    environment: dict[str, str] = {}
    if args.env_file.is_file():
        for line in args.env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            environment[key.strip()] = value.strip()

    try:
        environment = _prepare_property_runtime_environment(
            environment,
            cache_root=args.property_cache_root,
        )
        property_runtime = create_property_runtime_from_environment(
            environment, project_root=ROOT
        )
        _require_ready_property_runtime(property_runtime)
    except Exception as error:
        result["status"] = "blocked"
        result["reason_code"] = str(error)[:512]
        _write_json(output_root / "execution-result.json", result)
        return 1
    result["property_runtime"] = property_runtime.health.to_dict()

    config = load_openai_compatible_runtime_config(environment)
    transport = OpenAICompatibleLiveProvider(config=config)
    if not live._approved_deepseek_transport(transport):
        result["status"] = "blocked"
        result["reason_code"] = "LIVE_DEEPSEEK_TRANSPORT_REQUIRED"
        _write_json(output_root / "execution-result.json", result)
        return 1
    provider = live.TranscriptProvider(transport)

    total_calls = 0
    selected = (
        [c for c in FREEZE["cases"] if str(c["case_id"]) in set(args.case)]
        if args.case
        else list(FREEZE["cases"])
    )
    for case in selected:
        case_id = str(case["case_id"])
        if baseline_fingerprint.cmd_verify() != 0:
            result["status"] = "failed"
            result["reason_code"] = "BASELINE_DRIFT_BETWEEN_CASES"
            result["stopped_after_case"] = case_id
            break
        provider.set_case(case_id)
        case_root = output_root / "cases" / case_id
        case_root.mkdir(parents=True, exist_ok=True)
        before = len(provider.attempts)
        try:
            final = _execute_case(
                case=case,
                provider=provider,
                case_root=case_root,
                _property_runtime=property_runtime,
            )
            execution_error = None
        except Exception as error:
            execution_error = f"{type(error).__name__}: {error}"[:512]
            final = {
                "status": "provider_failed",
                "reason_code": type(error).__name__,
                "complete_repair_success": False,
                "successful_artifact_publishable": False,
            }
        attempts = provider.attempts[before:]
        total_calls = _updated_transport_call_count(total_calls, attempts)
        _write_json(case_root / "case-result.json", final)
        _write_json(case_root / "live-attempts.json", attempts)
        result["cases"].append(
            {
                "case_id": case_id,
                "status": final.get("status"),
                "reason_code": final.get("reason_code"),
                "case_result": (
                    f"cases/{case_id}/case-result.json"
                ),
                "genuine_provider_calls": len(attempts),
            }
        )
        if execution_error:
            print(f"STOP at {case_id}: {execution_error}", file=sys.stderr)
            result["status"] = "failed"
            result["stopped_after_case"] = case_id
            break
        if final.get("status") != "succeeded":
            result["status"] = "failed"
            result["reason_code"] = str(
                final.get("reason_code") or "CASE_NOT_PUBLISHABLE"
            )
            result["stopped_after_case"] = case_id
            print(
                f"STOP at {case_id}: {result['reason_code']}",
                file=sys.stderr,
            )
            break
        comparison = final.get("original_comparison") or {}
        print(
            f"  {case_id}: {final.get('status')} "
            f"(class_counts_restored={comparison.get('class_counts_restored')}, "
            f"comparison={comparison.get('comparison_status')})"
        )

    result["transport_calls"] = total_calls
    if result.get("status") in (None, "not_started"):
        result["status"] = "completed"
    _write_json(output_root / "execution-result.json", result)
    print(
        json.dumps(
            {"status": result["status"], "transport_calls": total_calls},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
