"""Curate immutable C1-C5 live evidence with focused IFCcompare debug."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
for path in (str(ROOT), str(SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)

from scripts.ifc_repair.composite_evidence.restoration_debug import (  # noqa: E402
    compare_damage_restoration,
)

FREEZE_PATH = (
    ROOT
    / "docs/validation/repair-composite-milestone"
    / "damage-restoration-c1-c5-freeze.json"
)
FREEZE = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
SCHEMA_VERSION = "text2ifc/damage-restoration-proof/0.2"


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

    if _canonical(recorded) != _canonical(recomputed):
        raise ValueError("PROOF_IFCCOMPARE_DEBUG_MISMATCH")
    if recomputed.get("status") != "passed":
        raise ValueError("PROOF_IFCCOMPARE_DEBUG_FAILED")


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
) -> str:
    comparison = result["original_comparison"]
    damage = result["damage"]
    lines = [
        f"# {case['case_id']} damage-restoration proof",
        "",
        "这是一次真实 Provider 的个案可行性/可靠性证据，不构成系统级能力提升结论。",
        "",
        f"- source: `{case['source']}`",
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
            "## Whole-model boundary",
            "",
            f"- IFCcompare execution: `{comparison['comparison_status']}`",
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


def _curate_case(
    case: Mapping[str, Any],
    *,
    run_root: Path,
    proof_root: Path,
) -> dict[str, Any]:
    case_id = str(case["case_id"])
    source_root = run_root / "cases" / case_id
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
    (case_root / "input").mkdir(parents=True, exist_ok=True)
    (case_root / "input/request.txt").write_text(
        str(case["request"]) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _copy(result_path, case_root / "validation/case-result.json")
    _copy(
        source_root / "live-attempts.json",
        case_root / "agent/live-attempts.json",
    )
    _copy_runtime_evidence(_run_directory(source_root, result), case_root)
    recomputed_debug = compare_damage_restoration(
        case,
        original_path=case_root / "01-original.ifc",
        repaired_path=case_root / "03-repaired.ifc",
    )
    validate_recorded_debug(recorded_debug, recomputed_debug)
    _write_json(
        case_root / "validation/ifccompare-geometry-property-debug.json",
        recomputed_debug,
    )
    report = _case_report(case, result, recomputed_debug)
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
        "focused_ifccompare_status": recomputed_debug["status"],
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


def curate(*, run_root: Path, proof_root: Path) -> dict[str, Any]:
    run_root = run_root.resolve()
    proof_root = proof_root.resolve()
    if proof_root.exists():
        raise FileExistsError(f"PROOF_ROOT_ALREADY_EXISTS:{proof_root}")
    execution_path = run_root / "execution-result.json"
    execution = json.loads(execution_path.read_text(encoding="utf-8"))
    if execution.get("status") != "completed":
        raise ValueError("PROOF_EXECUTION_NOT_COMPLETED")
    expected_ids = [str(case["case_id"]) for case in FREEZE["cases"]]
    actual_ids = [str(case.get("case_id")) for case in execution.get("cases", [])]
    if actual_ids != expected_ids or any(
        case.get("status") != "succeeded" for case in execution["cases"]
    ):
        raise ValueError("PROOF_EXECUTION_CASE_SET_INCOMPLETE")
    proof_root.mkdir(parents=True)
    _copy(execution_path, proof_root / "execution-result.json")
    _copy(FREEZE_PATH, proof_root / "freeze.json")
    preflight = execution.get("preflight") or {}
    preflight_path = Path(str(preflight.get("evidence_path") or ""))
    if not preflight_path.is_file():
        raise FileNotFoundError("PROOF_PREFLIGHT_EVIDENCE_NOT_FOUND")
    if _sha256(preflight_path) != preflight.get("evidence_file_sha256"):
        raise ValueError("PROOF_PREFLIGHT_HASH_MISMATCH")
    _copy(preflight_path, proof_root / "preflight/preflight.json")
    manifests = [
        _curate_case(case, run_root=run_root, proof_root=proof_root)
        for case in FREEZE["cases"]
    ]
    root_report = [
        "# C1-C5 damage-restoration live proof",
        "",
        "All five frozen cases completed through the public API path after a "
        "green zero-network preflight.",
        "Focused IFCcompare is the acceptance/debug evidence for restored "
        "geometry, requested occurrence properties, and exact Type reuse.",
        "Whole-model GlobalId identity is reported as a boundary, not treated "
        "as geometry equivalence.",
        "These are case-level viability/reliability results, not a class-level "
        "capability claim.",
        "",
        "| case | focused IFCcompare | columns |",
        "|---|---:|---:|",
    ]
    freeze_by_id = {str(case["case_id"]): case for case in FREEZE["cases"]}
    for manifest in manifests:
        case = freeze_by_id[manifest["case_id"]]
        root_report.append(
            f"| {manifest['case_id']} | {manifest['focused_ifccompare_status']} | "
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
        "cases": manifests,
        "preflight_sha256": _sha256(proof_root / "preflight/preflight.json"),
        "freeze_sha256": _sha256(proof_root / "freeze.json"),
        "artifacts": sorted(files),
    }
    _write_json(proof_root / "manifest.json", root_manifest)
    return root_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--proof-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = curate(run_root=args.run_root, proof_root=args.proof_root)
    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"status": result["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["curate", "validate_recorded_debug"]
