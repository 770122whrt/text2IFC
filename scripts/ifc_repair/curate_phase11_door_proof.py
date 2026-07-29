"""Independently validate and curate Phase 11 offline Door proof packages."""

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

from text2ifc_ifc_repair.prompt_profiles import (  # noqa: E402
    load_prompt_profiles,
    select_prompt_profiles,
)


DEFAULT_SOURCE = ROOT / "dataset/processed/ifc-repair/phase11-door-offline"
DEFAULT_COLLECTION = (
    ROOT / "dataset/processed/proof/ifc-repair-success-cases"
)
PROFILE_BY_OPERATION = {
    "add_window_with_opening_to_wall": "window.add-with-opening",
    "add_opening_to_wall": "opening.add-to-wall",
    "add_door_with_opening_to_wall": "door.add-with-opening",
    "fill_existing_opening_with_door": "door.fill-existing-opening",
}
FAMILY_BY_OPERATION = {
    "add_window_with_opening_to_wall": "window",
    "add_opening_to_wall": "opening",
    "add_door_with_opening_to_wall": "door",
    "fill_existing_opening_with_door": "door",
}
MIXED_BUCKET_BY_FAMILIES = {
    frozenset({"door", "window"}): "mixed/door-window",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        payload = value
    else:
        payload = json.dumps(
            value, ensure_ascii=False, indent=2, sort_keys=True
        )
    path.write_text(payload.rstrip() + "\n", encoding="utf-8")


def _validate_source_case(case_dir: Path) -> dict[str, Any]:
    manifest = _read(case_dir / "manifest.json")
    if manifest.get("status") != "passed":
        raise ValueError("SOURCE_CASE_NOT_PASSED")
    if manifest.get("synthetic_fallback_used") is not False:
        raise ValueError("SYNTHETIC_FALLBACK_NOT_FALSE")
    for name, record in manifest["artifacts"].items():
        artifact = case_dir / name
        if not artifact.is_file():
            raise FileNotFoundError(f"SOURCE_ARTIFACT_MISSING:{name}")
        if artifact.stat().st_size != int(record["bytes"]):
            raise ValueError(f"SOURCE_ARTIFACT_SIZE_MISMATCH:{name}")
        if _sha256(artifact) != str(record["sha256"]):
            raise ValueError(f"SOURCE_ARTIFACT_HASH_MISMATCH:{name}")
    for name in ("original.ifc", "damaged.ifc", "repaired.ifc"):
        if ifcopenshell.open(str(case_dir / name)).schema != "IFC2X3":
            raise ValueError(f"SOURCE_IFC_SCHEMA_MISMATCH:{name}")
    changeset = _read(case_dir / "changeset.json")
    if changeset["base_model_fingerprint"] != _sha256(
        case_dir / "damaged.ifc"
    ):
        raise ValueError("SOURCE_CHANGESET_FINGERPRINT_MISMATCH")
    operation_count = int(manifest["operation_count"])
    if len(changeset["operations"]) != operation_count:
        raise ValueError("SOURCE_CHANGESET_OPERATION_COUNT_MISMATCH")
    application = _read(case_dir / "application.json")
    if (
        application.get("valid") is not True
        or application.get("published") is not True
        or len(application.get("operations", ())) != operation_count
    ):
        raise ValueError("SOURCE_APPLICATION_NOT_PUBLISHED")
    evaluation = _read(case_dir / "evaluation.json")
    if (
        evaluation.get("status") != "passed"
        or evaluation.get("complete_repair_success") is not True
        or evaluation.get("successful_artifact_publishable") is not True
        or len(evaluation.get("operations", ())) != operation_count
    ):
        raise ValueError("SOURCE_EVALUATION_NOT_PUBLISHABLE")
    for operation in evaluation["operations"]:
        levels = {
            item["level"]: item["status"] for item in operation["levels"]
        }
        if levels.get("L1") != "passed" or levels.get("L2") != "passed":
            raise ValueError(
                f"SOURCE_OPERATION_GATE_FAILED:{operation['operation_id']}"
            )
    comparison = _read(case_dir / "comparison.json")
    if comparison.get("complete_preservation_success") is not True:
        raise ValueError("SOURCE_COMPARISON_NOT_PRESERVED")
    return manifest


def _routing_evidence(changeset: dict[str, Any]) -> dict[str, Any]:
    profiles = load_prompt_profiles()
    operation_bindings = []
    profile_ids = []
    for operation in changeset["operations"]:
        operation_type = str(operation["operation_type"])
        try:
            profile_id = PROFILE_BY_OPERATION[operation_type]
        except KeyError as error:
            raise ValueError(
                f"PROOF_OPERATION_PROFILE_MISSING:{operation_type}"
            ) from error
        profile = profiles[profile_id]
        if profile.operation_type != operation_type:
            raise ValueError("PROOF_PROFILE_OPERATION_MISMATCH")
        profile_ids.append(profile_id)
        operation_bindings.append(
            {
                "operation_id": operation["operation_id"],
                "operation_type": operation_type,
                "profile_id": profile_id,
                "profile_hash": profile.profile_hash,
            }
        )
    selected = select_prompt_profiles(profile_ids, profiles)
    return {
        "schema_version": "text2ifc/phase11-prompt-routing-proof/0.1",
        "operation_bindings": operation_bindings,
        "selected": selected.to_dict(),
    }


def _proof_classification(
    changeset: dict[str, Any],
    *,
    operation_count: int,
) -> tuple[str, str, str, list[str]]:
    operation_types = sorted(
        {str(item["operation_type"]) for item in changeset["operations"]}
    )
    try:
        families = {
            FAMILY_BY_OPERATION[operation_type]
            for operation_type in operation_types
        }
    except KeyError as exc:
        raise ValueError(f"UNSUPPORTED_PROOF_OPERATION:{exc.args[0]}") from exc

    if len(families) == 1:
        family = next(iter(families))
        case_kind = "batch" if operation_count > 1 else "single"
        return family, case_kind, f"{family}/{case_kind}", operation_types

    family_key = frozenset(families)
    try:
        bucket = MIXED_BUCKET_BY_FAMILIES[family_key]
    except KeyError as exc:
        joined = ",".join(sorted(families))
        raise ValueError(f"UNSUPPORTED_MIXED_PROOF_FAMILIES:{joined}") from exc
    return "mixed", "mixed", bucket, operation_types


def _copy_case(
    *,
    source_case: Path,
    collection_root: Path,
) -> dict[str, Any]:
    source_manifest = _validate_source_case(source_case)
    changeset = _read(source_case / "changeset.json")
    operation_count = int(source_manifest["operation_count"])
    operation_family, case_kind, bucket, operation_types = (
        _proof_classification(
            changeset,
            operation_count=operation_count,
        )
    )
    relative_case = f"{bucket}/{source_manifest['case_id']}"
    destination = collection_root / relative_case
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    copies = {
        "01-original.ifc": ("original.ifc", "original_ground_truth"),
        "02-damaged.ifc": ("damaged.ifc", "repair_input_ifc"),
        "03-repaired.ifc": ("repaired.ifc", "published_repair_output"),
        "input/request.txt": ("request.txt", "user_request"),
        "changeset/bound-changeset.json": (
            "changeset.json",
            "bound_changeset",
        ),
        "validation/application.json": (
            "application.json",
            "application_result",
        ),
        "validation/production-evaluation.json": (
            "evaluation.json",
            "production_evaluation",
        ),
        "validation/ifc-comparison.json": (
            "comparison.json",
            "ifc_comparison",
        ),
        "validation/source-run-manifest.json": (
            "manifest.json",
            "source_run_manifest",
        ),
    }
    optional = {
        "agent/repair-intent.json": (
            "repair-intent.json",
            "guid_free_repair_intent",
        ),
        "agent/target-resolution.json": (
            "target-resolution.json",
            "deterministic_target_resolution",
        ),
        "validation/injected-failure-changeset.json": (
            "injected-failure-changeset.json",
            "injected_failure_changeset",
        ),
        "validation/injected-failure-application.json": (
            "injected-failure-application.json",
            "injected_failure_application",
        ),
        "validation/evaluation-warm.json": (
            "evaluation-warm.json",
            "production_evaluation_warm",
        ),
    }
    for relative, pair in optional.items():
        if (source_case / pair[0]).is_file():
            copies[relative] = pair
    for relative, (source_name, _) in copies.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_case / source_name, target)

    routing_path = destination / "agent/prompt-routing-evidence.json"
    _write(routing_path, _routing_evidence(changeset))
    entries = [
        {
            "path": relative,
            "role": role,
            "size_bytes": (destination / relative).stat().st_size,
            "sha256": _sha256(destination / relative),
        }
        for relative, (_, role) in sorted(copies.items())
    ]
    entries.append(
        {
            "path": "agent/prompt-routing-evidence.json",
            "role": "prompt_profile_evidence",
            "size_bytes": routing_path.stat().st_size,
            "sha256": _sha256(routing_path),
        }
    )
    files = {
        "schema_version": "text2ifc/ifc-repair-proof-files/0.2",
        "case_id": source_manifest["case_id"],
        "files": sorted(entries, key=lambda item: item["path"]),
    }
    _write(destination / "FILES.json", files)
    removed_doors = source_manifest.get("damage", {}).get(
        "removed_doors", ()
    )
    public_targeting = source_manifest.get("public_targeting", {})
    if not removed_doors:
        door = source_manifest.get("damage", {}).get("door")
        removed_doors = [] if door is None else [door]
    report = (
        f"# {source_manifest['case_id']}\n\n"
        "- 证据模式：offline deterministic bound ChangeSet。\n"
        f"- operation 数量：{source_manifest['operation_count']}。\n"
        f"- operation 类型：{', '.join(operation_types)}。\n"
        "- original、damaged、repaired IFC 均已独立重开为 IFC2X3。\n"
        "- application、L1、L2、preservation 与文件哈希均已重新验证。\n"
        "- Prompt Profile 与 few-shot 指纹由当前不可变目录重新计算。\n"
        + (
            "- 用户请求和 RepairIntent 均不含 IFC GlobalId；名称、楼层与墙局部位置"
            "经确定性索引解析后，才在内部 ChangeSet 绑定 GUID。\n"
            if public_targeting.get("guid_free") is True
            else ""
        )
        + "- synthetic fallback：false。\n\n"
        + "## 被删除 Door\n\n"
        + (
            "\n".join(
                f"- `{item.get('name')}` (`{item.get('global_id')}`)"
                for item in removed_doors
            )
            if removed_doors
            else "- 本案例不删除 Door occurrence。\n"
        )
        + "\n"
    )
    _write(destination / "REPORT.md", report)
    return {
        "case_id": source_manifest["case_id"],
        "operation_family": operation_family,
        "case_kind": case_kind,
        "operation_types": operation_types,
        "operation_count": operation_count,
        "provider": "offline-deterministic",
        "model": "phase11-bound-fixture",
        "provider_evidence_mode": "offline_bound_deterministic",
        "status": "accepted",
        "report": f"{relative_case}/REPORT.md",
        "files": f"{relative_case}/FILES.json",
        "original_ifc": f"{relative_case}/01-original.ifc",
        "damaged_ifc": f"{relative_case}/02-damaged.ifc",
        "repaired_ifc": f"{relative_case}/03-repaired.ifc",
    }


def curate(
    source_root: Path = DEFAULT_SOURCE,
    collection_root: Path = DEFAULT_COLLECTION,
) -> dict[str, Any]:
    summary = _read(source_root / "run-summary.json")
    if summary.get("status") != "passed":
        raise ValueError("PHASE11_SOURCE_RUN_NOT_PASSED")
    case_entries = []
    for record in summary["cases"]:
        case_id = str(record["case_id"])
        case_entries.append(
            _copy_case(
                source_case=source_root / case_id,
                collection_root=collection_root,
            )
        )
    curated_case_ids = {item["case_id"] for item in case_entries}
    collection = _read(collection_root / "manifest.json")
    retained = [
        item
        for item in collection["cases"]
        if not (
            item.get("provider_evidence_mode")
            == "offline_bound_deterministic"
            and item.get("case_id") in curated_case_ids
        )
    ]
    collection["cases"] = [*retained, *case_entries]
    collection["case_count"] = len(collection["cases"])
    collection["operation_families"] = sorted(
        {
            str(item["operation_family"])
            for item in collection["cases"]
        }
    )
    collection["generated_at"] = "2026-07-29"
    collection["future_operation_families"] = [
        item
        for item in collection.get("future_operation_families", ())
        if item != "door"
    ]
    _write(collection_root / "manifest.json", collection)
    legacy_root = collection_root / "door/offline"
    for case_id in curated_case_ids:
        legacy_case = legacy_root / case_id
        if legacy_case.exists():
            shutil.rmtree(legacy_case)
    if legacy_root.exists() and not any(legacy_root.iterdir()):
        legacy_root.rmdir()
    return {
        "schema_version": "text2ifc/phase11-proof-curation/0.1",
        "status": "passed",
        "case_count": len(case_entries),
        "operation_count": sum(
            int(item["operation_count"]) for item in case_entries
        ),
        "cases": [item["case_id"] for item in case_entries],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument(
        "--collection-root", type=Path, default=DEFAULT_COLLECTION
    )
    args = parser.parse_args(argv)
    result = curate(args.source_root.resolve(), args.collection_root.resolve())
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
