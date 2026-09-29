"""Prepare/check development question packages. Never starts a repair or Provider."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
for directory in (ROOT, ROOT / "src"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import ifcopenshell

from scripts.ifc_repair.repair_comparison.contracts import (
    PACKAGE_VERSION, PUBLIC_FILES, read_json, safe_path, sha256,
    validate_definition, write_json, damage_profile,
)
from scripts.ifc_repair.repair_comparison.inspection import inspect_damage
from scripts.ifc_repair.repair_comparison.review_materials import render_location, render_review, render_validation
from scripts.ifc_repair.repair_comparison.viewer import write_viewer
from text2ifc_ifc_repair.mutation import remove_door, remove_window_and_opening


def prepare_case(definition: dict[str, Any], *, repository_root: Path, output_dir: Path) -> dict[str, Any]:
    validate_definition(definition)
    repository_root = safe_path(Path(repository_root))
    source = safe_path(repository_root / definition["source"]["path"])
    output = safe_path(Path(output_dir))
    if not source.is_relative_to(repository_root):
        raise ValueError("SOURCE_OUTSIDE_REPOSITORY")
    if output.exists():
        previous_path = safe_path(output / "private/task.json")
        previous = read_json(previous_path) if previous_path.is_file() else {}
        if not (previous.get("purpose") == "development_only"
                and previous.get("formal_eligible") is False
                and previous.get("review", {}).get("status") == "pending_human_review"
                and previous.get("case_id") == definition["case_id"]):
            raise ValueError("ONLY_PENDING_DEVELOPMENT_CAN_REFRESH")
        for path in output.rglob("*"):
            safe_path(path)
    if source.is_relative_to(output):
        raise ValueError("OUTPUT_CONTAINS_SOURCE")
    source_hash = sha256(source)
    if source_hash != definition["source"]["sha256"]:
        raise ValueError("SOURCE_IFC_FINGERPRINT_MISMATCH")
    attributions = [safe_path(repository_root / path) for path in definition["source"].get("attribution_files", [])]
    if any(not path.is_file() or not path.is_relative_to(repository_root) for path in attributions):
        raise ValueError("ATTRIBUTION_FILE_UNAVAILABLE")
    if ifcopenshell.open(str(source)).schema != "IFC2X3":
        raise ValueError("UNSUPPORTED_IFC_SCHEMA")
    output.mkdir(parents=True, exist_ok=True)
    private = output / "private"
    private.mkdir(exist_ok=True)
    write_json(output / "build-status.json", {"state": "building", "network_transport_attempted": False})
    try:
        reference = private / "reference.ifc"
        shutil.copyfile(source, reference)
        damage = definition["damage"]
        # The production mutator atomically renames a restrictive temp directory.
        # Copy its bytes into an ordinary inherited directory for human review.
        (private / "mutation").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="repair-preparation-") as staging:
            common = {"source_path": reference, "output_dir": Path(staging) / "mutation", "expected_source_sha256": source_hash}
            if damage["kind"] == "window":
                mutation = remove_window_and_opening(**common, wall_global_id=damage["wall_guid"], opening_global_id=damage["opening_guid"], window_global_id=damage["target_guid"])
            else:
                mutation = remove_door(**common, door_global_id=damage["target_guid"], preserve_opening=damage["preserve_opening"])
            for artifact in common["output_dir"].iterdir():
                if artifact.is_file():
                    shutil.copyfile(artifact, private / "mutation" / artifact.name)
        damaged = private / "mutation/damaged.ifc"
        checks = inspect_damage(reference, damaged, definition)
        checks["checks"]["source_unchanged"] = sha256(source) == source_hash == sha256(reference)
        write_json(private / "checks.json", checks)
        validation = {**checks["damaged_validation"], "ifc_sha256": sha256(damaged), "ifc_schema": ifcopenshell.open(str(damaged)).schema,
                      "ifc_path": "private/mutation/damaged.ifc", "scope": "IFC schema and EXPRESS; not repair completeness"}
        write_json(private / "damaged-ifc-validation.json", validation)
        (output / "IFC-VALIDATION.md").write_text(render_validation(validation), encoding="utf-8")
        if not all(checks["checks"].values()):
            raise ValueError("DAMAGE_PREPARATION_CHECK_FAILED")
        public = output / "public"
        public.mkdir(exist_ok=True)
        shutil.copyfile(damaged, public / "model.ifc")
        (public / "request.txt").write_text(definition["request"]["text"].strip() + "\n", encoding="utf-8")
        task = {
            "schema_version": PACKAGE_VERSION, "purpose": "development_only", "formal_eligible": False,
            "case_id": definition["case_id"], "definition": definition,
            "review": {"status": "pending_human_review", "reviewer": None, "reviewed_at": None},
            "required_product_count": sum(definition["task"]["required_products"].values()),
            "damage_profile": damage_profile(definition["task"]["required_products"]),
            "required_relation_count": len(definition["task"]["required_relations"]),
            "source_sha256": source_hash, "damaged_sha256": mutation["damaged_sha256"],
            "excluded_formal_scene_family": definition["source"]["scene_family"],
            "budget": {"status": "not_calibrated", "provider_calls_allowed": False},
        }
        write_json(private / "task.json", task)
        write_json(private / "answer-card.json", {"status": "pending_human_review", **definition["clarification"], "reply_policy": "Only confirmed facts actually asked for. No private G lookup, method tips, or automatic whole-card injection."})
        if attributions:
            (private / "attribution").mkdir(exist_ok=True)
            for i, path in enumerate(attributions):
                shutil.copyfile(path, private / "attribution" / f"{i + 1:02d}-{path.name}")
        (private / "location.svg").write_text(render_location(checks), encoding="utf-8")
        visual = write_viewer(output, definition)
        if not visual["reference_geometry_unchanged"] or not visual["removed_target_absent_in_d"]:
            raise ValueError("VISUAL_REFERENCE_GEOMETRY_CHANGED")
        (output / "REVIEW.md").write_text(render_review(definition, checks, visual), encoding="utf-8")
        write_json(output / "build-status.json", {"state": "prepared_pending_human_review", "network_transport_attempted": False})
        (output / "integrity.json").unlink(missing_ok=True)
        result = check_package(output)
        if not result["valid"]:
            raise ValueError(f"PACKAGE_CHECK_FAILED: {result['errors']}")
        return result
    except Exception as error:
        # Keep failed preparation evidence; never clean up an existing/user directory.
        write_json(output / "build-status.json", {"state": "failed", "error": str(error), "network_transport_attempted": False})
        raise


def check_package(package_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        package = safe_path(Path(package_dir))
        # Path isolation still matters; review text is intentionally editable.
        for path in package.rglob("*"):
            safe_path(path)
        if set(p.name for p in (package / "public").iterdir()) != PUBLIC_FILES:
            errors.append("PUBLIC_FILE_ALLOWLIST_MISMATCH")
        status = read_json(package / "build-status.json")
        if status != {"state": "prepared_pending_human_review", "network_transport_attempted": False}:
            errors.append("PACKAGE_NOT_PREPARED")
        task = read_json(package / "private/task.json")
        if task["schema_version"] != PACKAGE_VERSION:
            errors.append("UNSUPPORTED_PACKAGE_VERSION")
        definition = task["definition"]
        validate_definition(definition)
        if task["review"]["status"] != "pending_human_review" or task["formal_eligible"] is not False:
            errors.append("DEVELOPMENT_PACKAGE_CANNOT_SELF_ACCEPT")
        reference = package / "private/reference.ifc"
        damaged = package / "private/mutation/damaged.ifc"
        public = package / "public/model.ifc"
        if sha256(reference) != task["source_sha256"] or sha256(damaged) != task["damaged_sha256"] or sha256(public) != sha256(damaged):
            errors.append("FROZEN_INPUT_BINDING_MISMATCH")
        model = ifcopenshell.open(str(public))
        if model.schema != "IFC2X3":
            errors.append("SCHEMA_MISMATCH")
        checks = read_json(package / "private/checks.json")
        if not all(checks["checks"].values()):
            errors.append("DAMAGE_CHECK_FAILED")
        validation = read_json(package / "private/damaged-ifc-validation.json")
        if not (validation["passed"] is True and validation["express_rules"] is True
                and validation["diagnostic_count"] == 0 and validation["diagnostics"] == []
                and validation["ifc_sha256"] == sha256(damaged) and validation["ifc_schema"] == model.schema
                and checks["source_validation"]["passed"] is True and checks["damaged_validation"]["passed"] is True):
            errors.append("NATIVE_IFC_VALIDATION_FAILED")
        public_text = public.read_text(encoding="utf-8") + (package / "public/request.txt").read_text(encoding="utf-8")
        if any(identity in public_text for identity in checks["removed_product_guids"]):
            errors.append("DELETED_ID_IN_PUBLIC_INPUT")
        if (package / "public/request.txt").read_text(encoding="utf-8").strip() != definition["request"]["text"].strip():
            errors.append("PUBLIC_REQUEST_MISMATCH")
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        errors.append(f"PACKAGE_UNREADABLE_OR_INVALID: {error}")
    return {"valid": not errors, "human_accepted": False, "errors": errors, "scope": "IFC input binding/reopen/public-projection; not runtime sandbox or experiment admission"}


def export_public(package_dir: Path, destination: Path) -> dict[str, Any]:
    result = check_package(package_dir)
    if not result["valid"]:
        raise ValueError(f"PACKAGE_CHECK_FAILED: {result['errors']}")
    package = safe_path(Path(package_dir))
    destination = safe_path(Path(destination))
    if destination.exists():
        raise FileExistsError(f"Export already exists: {destination}")
    if destination.is_relative_to(package):
        raise ValueError("EXPORT_MUST_BE_OUTSIDE_PRIVATE_PACKAGE")
    destination.mkdir(parents=True, exist_ok=False)
    for name in sorted(PUBLIC_FILES):
        shutil.copyfile(package / "public" / name, destination / name)
    return {"files": sorted(PUBLIC_FILES), "development_only": True, "runtime_isolation_verified": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="Create or refresh pending development packages in place")
    prepare.add_argument("--definitions", type=Path, default=Path(__file__).with_name("development_cases.private.json"))
    prepare.add_argument("--repository-root", type=Path, default=ROOT)
    prepare.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("check", help="Read-only package integrity and public-projection check")
    check.add_argument("package", type=Path)
    export = commands.add_parser("export", help="Copy only public files; does not run tools or models")
    export.add_argument("package", type=Path)
    export.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "check":
            result = check_package(args.package)
            exit_code = 0 if result["valid"] else 1
        elif args.command == "export":
            result = export_public(args.package, args.destination)
            exit_code = 0
        else:
            definitions = read_json(args.definitions)["cases"]
            if not definitions or len({row["case_id"] for row in definitions}) != len(definitions):
                raise ValueError("EMPTY_OR_DUPLICATE_CASE_BATCH")
            for definition in definitions:
                validate_definition(definition)
            output = safe_path(args.output)
            if output.exists() and any(output.iterdir()):
                readme = safe_path(output / "README.md")
                has_case = any((output / row["case_id"] / "private/task.json").is_file() for row in definitions)
                if not has_case or (readme.exists() and not readme.read_text(encoding="utf-8").startswith("# Repair 开发题包\n")):
                    raise ValueError("ONLY_OWNED_DEVELOPMENT_BATCH_CAN_REFRESH")
            output.mkdir(parents=True, exist_ok=True)
            result = {"cases": {}}
            for definition in definitions:
                result["cases"][definition["case_id"]] = prepare_case(definition, repository_root=args.repository_root, output_dir=output / definition["case_id"])
            lines = ["# Repair 开发题包", "", "两题均为待人审开发材料；未运行模型，不是正式实验或接受的 Repair Proof。", ""]
            lines += [f"- [{row['case_id']}：{row['task']['summary']}]({row['case_id']}/REVIEW.md)" for row in definitions]
            lines += [f"- [{row['case_id']}：同步视角网格对照]({row['case_id']}/VIEW.html)" for row in definitions]
            lines += ["", "只导出各题 public/。开发场景及其变体从正式未见样本中排除；按场景族统计，不按文件副本统计。", ""]
            (output / "README.md").write_text("\n".join(lines), encoding="utf-8")
            exit_code = 0
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        result, exit_code = {"error": str(error)}, 1
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
