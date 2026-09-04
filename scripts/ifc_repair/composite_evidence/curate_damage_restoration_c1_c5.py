"""Curate immutable C1-C5 live evidence with focused IFCcompare debug."""

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

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
for path in (str(ROOT), str(SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)

from scripts.ifc_repair.composite_evidence.restoration_debug import (  # noqa: E402
    compare_damage_restoration,
)
from text2ifc_ifc_repair.compare import (  # noqa: E402
    build_ifc_difference_report,
)

FREEZE_PATH = (
    ROOT
    / "docs/validation/repair-composite-milestone"
    / "damage-restoration-c1-c5-freeze.json"
)
FREEZE = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
SCHEMA_VERSION = "text2ifc/damage-restoration-proof/0.3"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _canonical(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _copy(source: Path, target: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix.lower() in {".json", ".jsonl", ".md", ".txt"}:
        target.write_text(
            source.read_text(encoding="utf-8"),
            encoding="utf-8",
            newline="\n",
        )
    else:
        shutil.copy2(source, target)


def _inside(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"PROOF_SOURCE_OUTSIDE_RUN_ROOT:{resolved}")
    return resolved


def _single(paths: list[Path], *, label: str) -> Path:
    if len(paths) != 1:
        raise ValueError(f"PROOF_{label}_CARDINALITY:{len(paths)}")
    return paths[0]


def _damaged_ifc(case_run_root: Path) -> Path:
    for step in ("windows", "doors", "structural"):
        candidate = case_run_root / "damage" / step / "damaged.ifc"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"PROOF_DAMAGED_IFC_NOT_FOUND:{case_run_root}")


def _run_directory(
    case_run_root: Path,
    result: Mapping[str, Any],
) -> Path:
    run_id = str(result.get("run_id") or "")
    candidates = [
        case_run_root / "runtime" / "runs" / run_id,
        case_run_root / "runtime" / "runs" / "runs" / run_id,
    ]
    matches = [path for path in candidates if run_id and path.is_dir()]
    if not matches:
        matches = [
            path
            for path in (case_run_root / "runtime").rglob("state.json")
            if path.parent.name == run_id
        ]
        matches = [path.parent for path in matches]
    return _single(matches, label="RUN_DIRECTORY")


def validate_recorded_debug(
    recorded: Mapping[str, Any],
    recomputed: Mapping[str, Any],
) -> None:
    """Refuse curation if stored and freshly recomputed debug diverge."""

    def semantic_payload(payload: Mapping[str, Any]) -> Any:
        normalized = json.loads(json.dumps(payload))
        metrics = (
            normalized.get("whole_model_ifccompare", {}).get(
                "comparison_metrics", {}
            )
        )
        for key in list(metrics):
            if key.endswith("_seconds") and key != "timeout_seconds":
                metrics.pop(key)
        return normalized

    if _canonical(semantic_payload(recorded)) != _canonical(
        semantic_payload(recomputed)
    ):
        raise ValueError("PROOF_IFCCOMPARE_DEBUG_MISMATCH")
    if recomputed.get("status") != "passed":
        raise ValueError("PROOF_IFCCOMPARE_DEBUG_FAILED")


def validate_selected_case_execution(
    execution: Mapping[str, Any],
    *,
    case_id: str,
) -> Mapping[str, Any]:
    """Validate one selected case from a completed source batch."""

    if execution.get("status") != "completed":
        raise ValueError("PROOF_SOURCE_EXECUTION_NOT_COMPLETED")
    matches = [
        item
        for item in execution.get("cases", ())
        if str(item.get("case_id")) == case_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"PROOF_SOURCE_CASE_CARDINALITY:{case_id}:{len(matches)}"
        )
    if matches[0].get("status") != "succeeded":
        raise ValueError(f"PROOF_CASE_NOT_SUCCEEDED:{case_id}")
    return matches[0]


def restoration_tags_for_result(
    result: Mapping[str, Any],
) -> dict[str, list[str]]:
    comparison = result.get("original_comparison") or {}
    bindings = comparison.get("restoration_operation_bindings")
    if not isinstance(bindings, Mapping):
        raise ValueError("PROOF_RESTORATION_BINDINGS_MISSING")
    normalized: dict[str, list[str]] = {}
    for key in ("beams", "columns", "doors", "windows"):
        values = bindings.get(key)
        if not isinstance(values, list) or any(
            not isinstance(value, str) or not value for value in values
        ):
            raise ValueError(f"PROOF_RESTORATION_BINDINGS_INVALID:{key}")
        normalized[key] = list(values)
    return normalized


def load_public_request(run_dir: Path) -> str:
    payload = json.loads(
        (run_dir / "intent/renderer-input.json").read_text(encoding="utf-8")
    )
    request = payload.get("REPAIR_REQUEST")
    if not isinstance(request, str) or not request.strip():
        raise ValueError("PROOF_PUBLIC_REQUEST_MISSING")
    return request.strip()


def _repaired_entity_by_tag(model: Any, ifc_class: str, tag: str) -> Any:
    matches = [
        entity
        for entity in model.by_type(ifc_class)
        if str(getattr(entity, "Tag", None) or "") == tag
    ]
    if len(matches) != 1:
        raise ValueError(f"PROOF_REPAIRED_TAG_CARDINALITY:{tag}:{len(matches)}")
    return matches[0]


def build_guid_trace(
    case: Mapping[str, Any],
    result: Mapping[str, Any],
    *,
    repaired_path: Path,
) -> list[dict[str, Any]]:
    """Map every frozen removed component to the rebuilt IFC identity."""

    bindings = restoration_tags_for_result(result)
    model = ifcopenshell.open(str(repaired_path))
    ifc_classes = {
        "beams": "IfcBeam",
        "columns": "IfcColumn",
        "doors": "IfcDoor",
        "windows": "IfcWindow",
    }
    singular = {
        "beams": "beam",
        "columns": "column",
        "doors": "door",
        "windows": "window",
    }
    rows: list[dict[str, Any]] = []
    for key in ("beams", "columns", "doors", "windows"):
        for index, member in enumerate(case["damage"].get(key, ()), start=1):
            tag = bindings[key][index - 1]
            repaired = _repaired_entity_by_tag(model, ifc_classes[key], tag)
            rows.append(
                {
                    "role": f"{singular[key]}-{index}",
                    "repaired_tag": tag,
                    "damage_action": "removed",
                    "original_ifc_class": ifc_classes[key],
                    "original_global_id": str(member["gid"]),
                    "repair_action": "rebuilt",
                    "repaired_ifc_class": repaired.is_a(),
                    "repaired_global_id": str(repaired.GlobalId),
                }
            )
            if key not in {"doors", "windows"}:
                continue
            repaired_opening = ifcopenshell.util.element.get_filled_void(
                repaired
            )
            if repaired_opening is None:
                raise ValueError(f"PROOF_REPAIRED_OPENING_MISSING:{tag}")
            original_opening_id = (
                member.get("opening_gid")
                if key == "windows"
                else member["opening"]["gid"]
            )
            opening_was_retained = key == "doors" and bool(
                member.get("preserve_opening")
            )
            rows.append(
                {
                    "role": f"{singular[key]}-opening-{index}",
                    "repaired_tag": None,
                    "damage_action": (
                        "retained" if opening_was_retained else "removed"
                    ),
                    "original_ifc_class": "IfcOpeningElement",
                    "original_global_id": str(original_opening_id),
                    "repair_action": (
                        "reused" if opening_was_retained else "rebuilt"
                    ),
                    "repaired_ifc_class": repaired_opening.is_a(),
                    "repaired_global_id": str(repaired_opening.GlobalId),
                }
            )
    return rows


def _copy_runtime_evidence(run_dir: Path, case_root: Path) -> None:
    required = {
        "intent/repair-intent.json": "agent/repair-intent.json",
        "intent/rendered-prompt.md": "agent/rendered-intent-prompt.md",
        "intent/renderer-input.json": "agent/intent-renderer-input.json",
        "changeset/bound-changeset.json": "changeset/bound-changeset.json",
        "changeset/prompt-profile-selection.json": (
            "changeset/prompt-profile-selection.json"
        ),
        "semantic-manifests.json": "changeset/semantic-manifests.json",
        "state.json": "terminal/state.json",
    }
    for source_name, target_name in required.items():
        _copy(run_dir / source_name, case_root / target_name)
    for source in sorted((run_dir / "changeset").glob("semantic-manifest-*.json")):
        _copy(source, case_root / "changeset" / source.name)
    public_evaluation = _single(
        list((run_dir / ".terminal-bundles").rglob("public-evaluation.json")),
        label="PUBLIC_EVALUATION",
    )
    terminal_evidence = _single(
        list((run_dir / ".terminal-bundles").rglob("terminal/evidence.json")),
        label="TERMINAL_EVIDENCE",
    )
    _copy(public_evaluation, case_root / "validation/public-evaluation.json")
    _copy(terminal_evidence, case_root / "terminal/evidence.json")


def _case_report(
    case: Mapping[str, Any],
    result: Mapping[str, Any],
    debug: Mapping[str, Any],
    generic: Mapping[str, Any],
    *,
    guid_trace: list[Mapping[str, Any]],
    source_batch_id: str,
) -> str:
    comparison = result["original_comparison"]
    damage = result["damage"]
    lines = [
        f"# {case['case_id']} damage-restoration proof",
        "",
        "这是一次真实 Provider 的个案可行性/可靠性证据，不构成系统级能力提升结论。",
        "",
        f"- source: `{case['source']}`",
        f"- source batch: `{source_batch_id}`",
        f"- terminal status: `{result['status']}`",
        f"- latency: `{result.get('latency_seconds')}` seconds",
        "- source IFC was not mutated in place",
        "- private original and damage mapping were introduced only after repair",
        "",
        "## Focused IFCcompare geometry/property debug",
        "",
        f"- focused status: `{debug['status']}`",
        f"- restored members: `{debug['member_count']}`",
        f"- failed members: `{debug['failed_member_count']}`",
        "- geometry compares request→repaired and original→repaired in a "
        "common physical frame",
        "- properties compare request→original→repaired for each frozen "
        "occurrence property",
        "- Type check requires the exact surviving Type GlobalId and an "
        "unchanged Type graph",
        "",
        "| member | geometry | properties | exact Type |",
        "|---|---:|---:|---:|",
    ]
    for member in debug["members"]:
        lines.append(
            "| "
            f"`{member['repaired_tag']}` | "
            f"{member['geometry']['status']} | "
            f"{member['properties']['status']} | "
            f"{member['type_reuse']['status']} |"
        )
    lines.extend(
        [
            "",
            "## Damage and reconstruction GUID trace",
            "",
            "| role | damage action | original class | original GUID | repair action | repaired class | repaired GUID |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for row in guid_trace:
        lines.append(
            "| "
            f"{row['role']} | {row['damage_action']} | "
            f"{row['original_ifc_class']} | `{row['original_global_id']}` | "
            f"{row['repair_action']} | {row['repaired_ifc_class']} | "
            f"`{row['repaired_global_id']}` |"
        )
    lines.extend(
        [
            "",
            "## Whole-model boundary",
            "",
            f"- IFCcompare execution: `{comparison['comparison_status']}`",
            "- generic changed products: "
            f"`{generic['summary']['changed_product_count']}` "
            f"{generic['summary']['changed_product_classes']}",
            f"- class counts restored: `{comparison['class_counts_restored']}`",
            f"- identity-equivalent: `{comparison['identity_equivalent']}`",
            "- restored occurrences and relationships may receive new "
            "GlobalIds; therefore whole-model identity is not used as the "
            "geometry/property acceptance gate",
            "",
            "## Damage coverage",
            "",
            f"- beams: `{damage['beams_removed']}`",
            f"- columns: `{damage['columns_removed']}`",
            f"- doors: `{damage['doors_removed']}`",
            f"- windows: `{damage['windows_removed']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _files_index(root: Path) -> dict[str, Any]:
    files = {}
    excluded = {"FILES.json", "manifest.json"}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.name in excluded:
            continue
        files[path.relative_to(root).as_posix()] = {
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
        }
    return files


def _load_source_batch(
    case_run_root: Path,
    *,
    case_id: str,
) -> dict[str, Any]:
    case_run_root = case_run_root.resolve()
    source_run_root = case_run_root.parent.parent
    execution_path = source_run_root / "execution-result.json"
    execution = json.loads(execution_path.read_text(encoding="utf-8"))
    validate_selected_case_execution(execution, case_id=case_id)
    preflight = execution.get("preflight") or {}
    raw_preflight_path = Path(str(preflight.get("evidence_path") or ""))
    preflight_path = (
        raw_preflight_path
        if raw_preflight_path.is_absolute()
        else ROOT / raw_preflight_path
    ).resolve()
    if not preflight_path.is_file():
        raise FileNotFoundError("PROOF_PREFLIGHT_EVIDENCE_NOT_FOUND")
    if _sha256(preflight_path) != preflight.get("evidence_file_sha256"):
        raise ValueError("PROOF_PREFLIGHT_HASH_MISMATCH")
    return {
        "case_run_root": case_run_root,
        "source_run_root": source_run_root,
        "execution_path": execution_path,
        "execution": execution,
        "preflight_path": preflight_path,
    }


def _curate_case(
    case: Mapping[str, Any],
    *,
    case_run_root: Path,
    proof_root: Path,
    source_batch_id: str,
) -> dict[str, Any]:
    case_id = str(case["case_id"])
    source_root = case_run_root.resolve()
    result_path = source_root / "case-result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("status") != "succeeded":
        raise ValueError(f"PROOF_CASE_NOT_SUCCEEDED:{case_id}")
    comparison = result.get("original_comparison") or {}
    recorded_debug = comparison.get("focused_geometry_property_debug") or {}
    case_root = proof_root / case_id
    source_ifc = ROOT / str(case["source"])
    repaired_ifc = _inside(Path(result["repaired_ifc_path"]), source_root)
    _copy(source_ifc, case_root / "01-original.ifc")
    _copy(_damaged_ifc(source_root), case_root / "02-damaged.ifc")
    _copy(repaired_ifc, case_root / "03-repaired.ifc")
    _copy(result_path, case_root / "validation/case-result.json")
    _copy(
        source_root / "live-attempts.json",
        case_root / "agent/live-attempts.json",
    )
    run_dir = _run_directory(source_root, result)
    _copy_runtime_evidence(run_dir, case_root)
    (case_root / "input").mkdir(parents=True, exist_ok=True)
    (case_root / "input/request.txt").write_text(
        load_public_request(run_dir) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (case_root / "input/frozen-request.txt").write_text(
        str(case["request"]).strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    recomputed_debug = compare_damage_restoration(
        case,
        original_path=case_root / "01-original.ifc",
        repaired_path=case_root / "03-repaired.ifc",
        repaired_tags=restoration_tags_for_result(result),
    )
    validate_recorded_debug(recorded_debug, recomputed_debug)
    _write_json(
        case_root / "validation/ifccompare-geometry-property-debug.json",
        recomputed_debug,
    )
    generic = build_ifc_difference_report(
        case_root / "01-original.ifc",
        case_root / "03-repaired.ifc",
        timeout_seconds=900.0,
    )
    _write_json(
        case_root / "validation/generic-ifccompare.json",
        generic,
    )
    guid_trace = build_guid_trace(
        case,
        result,
        repaired_path=case_root / "03-repaired.ifc",
    )
    _write_json(
        case_root / "validation/damage-reconstruction-guid-trace.json",
        {"case_id": case_id, "components": guid_trace},
    )
    report = _case_report(
        case,
        result,
        recomputed_debug,
        generic,
        guid_trace=guid_trace,
        source_batch_id=source_batch_id,
    )
    (case_root / "REPORT.md").write_text(
        report,
        encoding="utf-8",
        newline="\n",
    )
    files = _files_index(case_root)
    _write_json(case_root / "FILES.json", {"files": files})
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "status": "passed",
        "provider_evidence_mode": "genuine_live_provider",
        "synthetic_fallback_used": False,
        "claim_level": "case_viability_and_reliability_only",
        "source_batch": source_batch_id,
        "damage_reconstruction_guid_trace": guid_trace,
        "focused_ifccompare_status": recomputed_debug["status"],
        "generic_ifccompare_summary": generic["summary"],
        "whole_model_identity_equivalent": comparison["identity_equivalent"],
        "damage": {
            key: damage
            for key, damage in result["damage"].items()
            if key.endswith("_removed")
        },
        "artifacts": sorted(files),
    }
    _write_json(case_root / "manifest.json", manifest)
    return manifest


def curate_case_runs(
    *,
    case_run_roots: Mapping[str, Path],
    proof_root: Path,
) -> dict[str, Any]:
    expected_ids = [str(case["case_id"]) for case in FREEZE["cases"]]
    if set(case_run_roots) != set(expected_ids):
        raise ValueError("PROOF_CASE_RUN_SET_INCOMPLETE")
    proof_root = proof_root.resolve()
    if proof_root.exists():
        raise FileExistsError(f"PROOF_ROOT_ALREADY_EXISTS:{proof_root}")

    sources: dict[str, dict[str, Any]] = {}
    batches_by_execution: dict[Path, dict[str, Any]] = {}
    for case_id in expected_ids:
        source = _load_source_batch(
            Path(case_run_roots[case_id]),
            case_id=case_id,
        )
        result = json.loads(
            (source["case_run_root"] / "case-result.json").read_text(
                encoding="utf-8"
            )
        )
        if result.get("status") != "succeeded":
            raise ValueError(f"PROOF_CASE_NOT_SUCCEEDED:{case_id}")
        sources[case_id] = source
        execution_path = source["execution_path"]
        if execution_path not in batches_by_execution:
            batches_by_execution[execution_path] = {
                "batch_id": f"batch-{len(batches_by_execution) + 1:02d}",
                "source": source,
                "case_ids": [],
            }
        batches_by_execution[execution_path]["case_ids"].append(case_id)

    proof_root.mkdir(parents=True)
    _copy(FREEZE_PATH, proof_root / "freeze.json")
    source_batches = []
    case_to_batch: dict[str, str] = {}
    for batch in batches_by_execution.values():
        batch_id = batch["batch_id"]
        source = batch["source"]
        batch_root = proof_root / "source-runs" / batch_id
        _copy(source["execution_path"], batch_root / "execution-result.json")
        _copy(source["preflight_path"], batch_root / "preflight.json")
        batch_manifest = {
            "batch_id": batch_id,
            "status": source["execution"]["status"],
            "selected_cases": batch["case_ids"],
            "execution_sha256": _sha256(batch_root / "execution-result.json"),
            "preflight_sha256": _sha256(batch_root / "preflight.json"),
        }
        _write_json(batch_root / "manifest.json", batch_manifest)
        source_batches.append(batch_manifest)
        for case_id in batch["case_ids"]:
            case_to_batch[case_id] = batch_id

    manifests = []
    for case in FREEZE["cases"]:
        case_id = str(case["case_id"])
        manifests.append(
            _curate_case(
                case,
                case_run_root=sources[case_id]["case_run_root"],
                proof_root=proof_root,
                source_batch_id=case_to_batch[case_id],
            )
        )
    root_report = [
        "# C1-C5 damage-restoration live proof",
        "",
        "All five frozen cases completed through the public API path in two "
        "completed source batches using the same frozen production baseline.",
        "C1-C2 are from batch-01; C3-C5 are from batch-02.",
        "Focused IFCcompare is the acceptance/debug evidence for restored "
        "geometry, requested occurrence properties, and exact Type reuse.",
        "Whole-model GlobalId identity is reported as a boundary, not treated "
        "as geometry equivalence.",
        "These are case-level viability/reliability results, not a class-level "
        "capability claim.",
        "",
        "| case | source batch | focused IFCcompare | generic changed products | columns |",
        "|---|---|---:|---:|---:|",
    ]
    freeze_by_id = {str(case["case_id"]): case for case in FREEZE["cases"]}
    for manifest in manifests:
        case = freeze_by_id[manifest["case_id"]]
        root_report.append(
            f"| {manifest['case_id']} | {manifest['source_batch']} | "
            f"{manifest['focused_ifccompare_status']} | "
            f"{manifest['generic_ifccompare_summary']['changed_product_count']} | "
            f"{len(case['damage'].get('columns', []))} |"
        )
    (proof_root / "REPORT.md").write_text(
        "\n".join(root_report) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    files = _files_index(proof_root)
    _write_json(proof_root / "FILES.json", {"files": files})
    root_manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "passed",
        "source_batches": source_batches,
        "cases": manifests,
        "freeze_sha256": _sha256(proof_root / "freeze.json"),
        "artifacts": sorted(files),
    }
    _write_json(proof_root / "manifest.json", root_manifest)
    return root_manifest


def curate(*, run_root: Path, proof_root: Path) -> dict[str, Any]:
    run_root = run_root.resolve()
    return curate_case_runs(
        case_run_roots={
            str(case["case_id"]): run_root / "cases" / str(case["case_id"])
            for case in FREEZE["cases"]
        },
        proof_root=proof_root,
    )


def _parse_case_run(value: str) -> tuple[str, Path]:
    case_id, separator, raw_path = value.partition("=")
    if not separator or not case_id or not raw_path:
        raise ValueError("CASE_RUN_FORMAT_MUST_BE_CASE_ID=PATH")
    return case_id, Path(raw_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--run-root", type=Path)
    source.add_argument(
        "--case-run",
        action="append",
        help="selected successful case root as CASE_ID=PATH; repeat for C1-C5",
    )
    parser.add_argument("--proof-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.run_root is not None:
            result = curate(run_root=args.run_root, proof_root=args.proof_root)
        else:
            case_run_roots = dict(
                _parse_case_run(value) for value in (args.case_run or ())
            )
            result = curate_case_runs(
                case_run_roots=case_run_roots,
                proof_root=args.proof_root,
            )
    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"status": result["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "curate",
    "curate_case_runs",
    "load_public_request",
    "restoration_tags_for_result",
    "validate_recorded_debug",
    "validate_selected_case_execution",
]
