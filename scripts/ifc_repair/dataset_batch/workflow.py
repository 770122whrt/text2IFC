"""Persistent source-level work units; reports, not IFC bodies, cross the pool."""
from __future__ import annotations

import contextlib
import json
import shutil
import time
from pathlib import Path

import ifcopenshell

from .engine import apply_recipe, build_recipes, inventory_model, seal_case, verify_seal, write_json
from .validation import native_validate, product_state, program_hash, sha256


def prepare_source(spec: dict, repository_root: str, admission_root: str, count: int, seed: int) -> dict:
    source = (Path(repository_root) / spec["input_path"]).resolve()
    root = Path(repository_root).resolve()
    if not source.is_relative_to(root) or source.stat().st_size >= 20_000_000 or sha256(source) != spec["source_sha256"]:
        return {"passed": False, "source_id": spec["source_id"], "reason": "source_binding_or_size_failed"}
    folder = Path(admission_root) / spec["source_sha256"]
    folder.mkdir(parents=True, exist_ok=True)
    result_file = folder / "admission.json"
    if result_file.exists():
        cached = json.loads(result_file.read_text(encoding="utf-8"))
        seal_path = folder / "seal.json"
        if seal_path.exists():
            seal = json.loads(seal_path.read_text(encoding="utf-8"))["sha256"]
            required = {"admission.json", "native.json"} | ({"inventory.json"} if (folder / "inventory.json").exists() else set())
            if set(seal) != required or any(sha256(folder / name) != value for name, value in seal.items()):
                raise ValueError("ADMISSION_CACHE_INTEGRITY_FAILED")
        if seal_path.exists() and cached.get("code_sha256") == program_hash() and cached.get("ifcopenshell_version") == ifcopenshell.version and cached.get("target_cases") == count and cached.get("seed") == seed and cached.get("source_sha256") == sha256(source) and cached.get("inventory_version") == 3 and all((folder / name).is_file() and sha256(folder / name) == value for name, value in cached.get("artifact_hashes", {}).items()) and cached.get("artifact_hashes"):
            return {**cached, "source_id": spec["source_id"], "admission_folder": str(folder)}
    started = time.monotonic()
    with (folder / "native.log").open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        native = native_validate(source)
        write_json(folder / "native.json", native)
        inventory = inventory_model(source) if native["passed"] else None
        if inventory is not None:
            write_json(folder / "inventory.json", inventory)
            recipes = build_recipes(inventory, count=30, seed=seed)
        else:
            recipes = []
    passed = native["passed"] and len(recipes) >= count and sha256(source) == spec["source_sha256"]
    result = {"passed": passed, "source_id": spec["source_id"], "source_sha256": spec["source_sha256"], "ifcopenshell_version": ifcopenshell.version, "express_rules": True, "target_cases": count, "seed": seed, "native_findings": native["finding_count"], "available_recipes": len(recipes), "eligible_targets": {key: len(value) for key, value in inventory["targets"].items()} if inventory else {}, "eligible_properties": len(inventory["properties"]) if inventory else 0, "excluded_targets": len(inventory["excluded_targets"]) if inventory else 0, "inventory_version": 3, "artifact_hashes": {name: sha256(folder / name) for name in ("native.json", "inventory.json") if (folder / name).is_file()}, "geometry_scope": inventory.get("geometry_scope") if inventory else None, "elapsed_seconds": round(time.monotonic() - started, 3), "reason": None if passed else "native_validation_or_recipe_capacity_failed", "admission_folder": str(folder)}
    write_json(result_file, result)
    result["code_sha256"] = program_hash()
    write_json(result_file, result)
    write_json(folder / "seal.json", {"sha256": {name: sha256(folder / name) for name in ("admission.json", "native.json", "inventory.json") if (folder / name).is_file()}})
    return result


def process_source(spec: dict, repository_root: str, dataset_root: str, count: int, seed: int) -> dict:
    started = time.monotonic()
    root = Path(dataset_root)
    original = (Path(repository_root) / spec["input_path"]).resolve()
    if sha256(original) != spec["source_sha256"]:
        raise ValueError("SOURCE_CHANGED")
    admission = prepare_source(spec, repository_root, str(root / "private/admissions"), count, seed)
    if not admission["passed"]:
        return {"source_id": spec["source_id"], "passed_cases": 0, "target_cases": count, "status": "blocked", "admission": admission}
    source_root = root / "sources" / spec["source_id"]
    private = source_root / "private"
    private.mkdir(parents=True, exist_ok=True)
    reference = private / "reference.ifc"
    if not reference.exists():
        shutil.copyfile(original, reference)
    if sha256(reference) != spec["source_sha256"]:
        raise ValueError("PRIVATE_REFERENCE_CHANGED")
    source_file = private / "source.json"
    if source_file.exists() and json.loads(source_file.read_text(encoding="utf-8"))["source_sha256"] != spec["source_sha256"]:
        raise ValueError("CANNOT_REPLACE_EXISTING_MOTHER_MODEL")
    write_json(source_file, {**spec, "reference_role": "mother model fixed before synthetic damage; private reference for later evaluation", "derivatives_inherit_human_review": False})
    (source_root / "SOURCE.md").write_text(f"# {spec['source_id']} 来源与修改声明\n\n许可：{spec.get('license', 'unknown')}。\n\n来源：{spec.get('source_url', '')}\n\n原文件：`{spec['input_path']}`。原SHA-256：`{spec['source_sha256']}`。\n\n本目录的IFC派生副本经过人工设计的构件删除或实例属性更改。原件保留在private/reference.ifc；许可与署名证据见private/source.json。研究使用和可修改来源筛选不等于训练准入或本仓库正式Proof验收。\n", encoding="utf-8")
    folder = Path(admission["admission_folder"])
    inventory = json.loads((folder / "inventory.json").read_text(encoding="utf-8"))
    recipes = build_recipes(inventory, count=30, seed=seed)
    before_model = ifcopenshell.open(str(reference))
    baseline_state = product_state(before_model)
    cases, passed_hashes = [], set()
    with (private / "generation.log").open("a", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        for index, recipe in enumerate(recipes, 1):
            output = source_root / "cases" / f"case-{index:03d}"
            if output.exists():
                if not verify_seal(output):
                    raise ValueError("EXISTING_CASE_BINDING_FAILED")
                case = json.loads((output / "case.json").read_text(encoding="utf-8"))
                stored_recipe = json.loads((output / "private/recipe.json").read_text(encoding="utf-8"))
                if stored_recipe != recipe or case["source_sha256"] != spec["source_sha256"] or sha256(output / "public/model.ifc") != case["damaged_sha256"]:
                    raise ValueError("EXISTING_CASE_BINDING_FAILED")
            else:
                case = apply_recipe(reference, recipe, output, inventory=inventory, baseline_state=baseline_state)
            if case["status"] == "passed" and case["damaged_sha256"] in passed_hashes:
                case = {**case, "status": "failed", "machine_validated": False, "duplicate_damaged_content": True}
                write_json(output / "case.json", case)
                seal_case(output)
            if case["status"] == "passed":
                passed_hashes.add(case["damaged_sha256"])
            cases.append({**case, "case_id": f"{spec['source_id']}-{index:03d}", "path": output.relative_to(root).as_posix()})
            write_json(private / "progress.json", {"completed_cases": len(cases), "passed_cases": len(passed_hashes), "target_cases": count, "last_case": index})
            if len(passed_hashes) >= count:
                break
    unchanged = sha256(original) == spec["source_sha256"] == sha256(reference)
    result = {"schema_version": "text2ifc/ifc-repair-dataset-source-result/1.0", "source_id": spec["source_id"], "status": "complete" if len(passed_hashes) == count and unchanged else "incomplete", "target_cases": count, "attempted_cases": len(cases), "passed_cases": len(passed_hashes), "source_unchanged": unchanged, "provider_calls": 0, "cases": cases, "elapsed_seconds": round(time.monotonic() - started, 3)}
    write_json(source_root / "result.json", result)
    return result
