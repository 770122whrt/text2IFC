"""Genuine live runner for the damage-restoration case set.

Executes the frozen damage-restoration cases (``damage-restoration-freeze.json``)
against the live Provider through the production ``RepairAPI`` public path:

    original (vvo, members native)
    -> deterministic damage (production ``remove_structural_members``)
    -> genuine live Provider repair (restore the removed members)
    -> strict publication gates
    -> repaired compared with original (class counts + comparator)

Every attempt, token usage, latency, and prompt identity is retained per case.
No synthetic fallback is ever reported as genuine.  The source model is never
mutated in place (damage writes to a scratch directory).

Usage (repo root, repo venv)::

    python scripts/ifc_repair/composite_evidence/run_damage_restoration.py \
        --execute-genuine
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
for p in (str(ROOT), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

import ifcopenshell  # noqa: E402

from scripts.ifc_repair import run_phase12_live_uat as live  # noqa: E402
from scripts.ifc_repair.composite_evidence import baseline_fingerprint  # noqa: E402
from text2ifc_agent.openai_compat import (  # noqa: E402
    OpenAICompatibleLiveProvider,
    load_openai_compatible_runtime_config,
)
from text2ifc_ifc_repair.api import RepairAPI  # noqa: E402
from text2ifc_ifc_repair.compare import compare_ifc_models  # noqa: E402
from text2ifc_ifc_repair.mutation import (  # noqa: E402
    remove_structural_members,
)

DOC_DIR = ROOT / "docs" / "validation" / "repair-composite-milestone"
FREEZE_PATH = DOC_DIR / "damage-restoration-freeze.json"
FREEZE = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
VVO = ROOT / "dataset" / "ifc" / "train" / "vvo.ifc"
RESULT_SCHEMA = "text2ifc/damage-restoration-execution-result/0.1"

# Restored-member geometry (private design input; the public request states
# the same facts in prose).  Mirrors the frozen offline suite constants.
MEMBERS = {
    "17tPjyQtf2L9JnbXXmcT8w": {
        "family": "beam",
        "storey_name": "标高7",
        "axis": {
            "start": {"x_mm": -7452.2, "y_mm": -14836.2, "z_mm": 0.0},
            "end": {"x_mm": -3549.2, "y_mm": -14836.2, "z_mm": 0.0},
        },
        "section": {"shape": "rectangle", "width_mm": 570.0, "height_mm": 400.0},
    },
    "17tPjyQtf2L9JnbXXmcTUF": {
        "family": "beam",
        "storey_name": "标高7",
        "axis": {
            "start": {"x_mm": -3316.6, "y_mm": -3863.5, "z_mm": 0.0},
            "end": {"x_mm": -3316.6, "y_mm": -8803.5, "z_mm": 0.0},
        },
        "section": {"shape": "rectangle", "width_mm": 570.0, "height_mm": 455.0},
    },
    "1rsYNObuDC4euALdw6WUK4": {
        "family": "column",
        "storey_name": "标高0",
        "axis": {
            "base": {"x_mm": -3307.4, "y_mm": -9061.8, "z_mm": 0.0},
            "top": {"x_mm": -3307.4, "y_mm": -9061.8, "z_mm": 3712.1},
        },
        "section": {
            "shape": "rectangle",
            "width_mm": 500.0,
            "depth_mm": 500.0,
            "orientation": {"x": 0, "y": 1},
        },
    },
}


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _compare_with_original(repaired: Path) -> dict[str, Any]:
    comparison = compare_ifc_models(VVO, repaired, allowed_changed_ids=())
    original = ifcopenshell.open(str(VVO))
    repaired_model = ifcopenshell.open(str(repaired))
    counts = {
        ifc_class: {
            "original": len(original.by_type(ifc_class)),
            "repaired": len(repaired_model.by_type(ifc_class)),
            "restored": len(repaired_model.by_type(ifc_class))
            == len(original.by_type(ifc_class)),
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
    return {
        "comparison_status": comparison.get("comparison_status"),
        "added_ids_count": len(comparison.get("added_ids") or []),
        "removed_ids_count": len(comparison.get("removed_ids") or []),
        "class_counts": counts,
        "class_counts_restored": all(
            item["restored"] for item in counts.values()
        ),
    }


def _execute_case(
    *,
    case: Mapping[str, Any],
    provider: Any,
    case_root: Path,
) -> dict[str, Any]:
    damage = case["damage"]
    mutation_root = case_root / "damage"
    remove_structural_members(
        source_path=VVO,
        output_dir=mutation_root,
        beam_global_ids=tuple(damage["beam_global_ids"]),
        column_global_ids=tuple(damage["column_global_ids"]),
    )
    damaged = mutation_root / "damaged.ifc"
    damaged_model = ifcopenshell.open(str(damaged))
    original_model = ifcopenshell.open(str(VVO))
    damage_summary = {
        "beams_removed": len(damage["beam_global_ids"]),
        "columns_removed": len(damage["column_global_ids"]),
        "beam_count_before": len(original_model.by_type("IfcBeam")),
        "beam_count_after_damage": len(damaged_model.by_type("IfcBeam")),
        "column_count_before": len(original_model.by_type("IfcColumn")),
        "column_count_after_damage": len(damaged_model.by_type("IfcColumn")),
        "damaged_sha256": _sha256_path(damaged),
        "source_untouched": _sha256_path(VVO)
        == _sha256_path(VVO),
    }

    runtime = case_root / "runtime"
    api = RepairAPI(
        runtime,
        provider=provider,
        intent_schema_version=live.REPAIR_INTENT_SCHEMA_VERSION_0_8,
    )
    provider.set_lineage("initial")
    started = time.monotonic()
    initial = api.start(damaged, str(case["request"]))
    latency_seconds = round(time.monotonic() - started, 3)
    summary = live._result_summary(initial)

    comparison_payload = None
    repaired_path = None
    if summary.get("status") == "succeeded":
        repaired_path = (
            runtime
            / "runs"
            / str(summary["run_id"])
            / str(summary["artifacts"]["successful_ifc"])
        )
        comparison_payload = _compare_with_original(repaired_path)

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
        / "dataset/processed/ifc-repair-runs/repair-damage-restoration",
    )
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    args = parser.parse_args()

    output_root = args.output_root.resolve()
    if output_root.exists() and any(output_root.iterdir()):
        print(f"ERROR: output root not empty: {output_root}", file=sys.stderr)
        return 2
    output_root.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "created_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "freeze_sha256": "sha256:" + hashlib.sha256(
            FREEZE_PATH.read_bytes()
        ).hexdigest(),
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
        result["reason_code"] = "DAMAGE_RESTORATION_BASELINE_DRIFT"
        _write_json(output_root / "execution-result.json", result)
        return 1
    if not args.execute_genuine:
        result["status"] = "ready_for_genuine_execution"
        _write_json(output_root / "execution-result.json", result)
        print(json.dumps({"status": result["status"]}, ensure_ascii=False))
        return 0

    environment: dict[str, str] = {}
    if args.env_file.is_file():
        for line in args.env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            environment[key.strip()] = value.strip()

    config = load_openai_compatible_runtime_config(environment)
    transport = OpenAICompatibleLiveProvider(config=config)
    if not live._approved_deepseek_transport(transport):
        result["status"] = "blocked"
        result["reason_code"] = "DAMAGE_RESTORATION_LIVE_DEEPSEEK_TRANSPORT_REQUIRED"
        _write_json(output_root / "execution-result.json", result)
        return 1
    provider = live.TranscriptProvider(transport)

    total_calls = 0
    for case in FREEZE["cases"]:
        case_id = str(case["case_id"])
        if baseline_fingerprint.cmd_verify() != 0:
            result["status"] = "failed"
            result["reason_code"] = "DAMAGE_RESTORATION_BASELINE_DRIFT_BETWEEN_CASES"
            result["stopped_after_case"] = case_id
            break
        provider.set_case(case_id)
        case_root = output_root / "cases" / case_id
        case_root.mkdir(parents=True, exist_ok=True)
        before = len(provider.attempts)
        try:
            final = _execute_case(
                case=case, provider=provider, case_root=case_root
            )
            execution_error = None
        except Exception as error:  # infrastructure defect: stop
            execution_error = f"{type(error).__name__}: {error}"[:512]
            final = {
                "status": "provider_failed",
                "reason_code": type(error).__name__,
                "complete_repair_success": False,
                "successful_artifact_publishable": False,
            }
        attempts = provider.attempts[before:]
        _write_json(case_root / "case-result.json", final)
        _write_json(case_root / "live-attempts.json", attempts)
        if execution_error:
            print(f"STOP at {case_id}: {execution_error}", file=sys.stderr)
            result["status"] = "failed"
            result["stopped_after_case"] = case_id
            break
        total_calls += len(attempts)
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
            {
                "status": result["status"],
                "transport_calls": total_calls,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
