"""Stratified independent spot checks; never human-review labels."""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

from .engine import write_json
from .validation import sha256


def _mesh(product):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    shape = ifcopenshell.geom.create_shape(settings, product)
    return np.array(shape.geometry.verts, dtype=float), np.array(shape.geometry.faces, dtype=int)


def _property(model, item):
    entity = model.by_guid(item["guid"])
    properties = [prop for rel in entity.IsDefinedBy if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition.is_a("IfcPropertySet") and rel.RelatingPropertyDefinition.Name == item["pset_name"] for prop in rel.RelatingPropertyDefinition.HasProperties if prop.Name == item["property_name"]]
    if len(properties) != 1:
        return None
    value = properties[0].NominalValue
    return {"type": value.is_a(), "value": value.wrappedValue} if value else None


def inspect_case(root: Path, case: dict) -> dict:
    folder = root / case["path"]
    manifest = json.loads((folder / "private/mutation.json").read_text(encoding="utf-8"))
    reference = folder.parent.parent / "private/reference.ifc"
    original = ifcopenshell.open(str(reference))
    damaged = ifcopenshell.open(str(folder / "public/model.ifc"))
    unit = ifcopenshell.util.unit.calculate_unit_scale(original)
    failures, removed, targets = [], set(), [*manifest["deletions"], *manifest["property_changes"]]
    for item in manifest["deletions"]:
        ids = [item["guid"]] + ([item["opening_guid"]] if item.get("opening_guid") and not item.get("preserve_opening", True) else [])
        for guid in ids:
            removed.add(guid)
            try:
                damaged.by_guid(guid)
                failures.append("deleted_identity_still_present:" + guid)
            except RuntimeError:
                pass
    coordinate_checks = 0
    for item in targets:
        entity = original.by_guid(item["guid"])
        matrix = np.array(ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement), dtype=float)
        matrix[:3, 3] *= unit
        storey = original.by_guid(item["storey"]["guid"])
        storey_matrix = np.array(ifcopenshell.util.placement.get_local_placement(storey.ObjectPlacement), dtype=float)
        storey_matrix[:3, 3] *= unit
        relative = np.linalg.solve(storey_matrix, matrix)
        if not np.allclose(matrix[:3, 3], item["geometry"]["origin_world_m"], atol=1e-8, rtol=0) or not np.allclose(relative[:3, 3], item["geometry"]["origin_storey_m"], atol=1e-8, rtol=0):
            failures.append("coordinate_snapshot_mismatch:" + item["guid"])
        coordinate_checks += 1
    for item in manifest["property_changes"]:
        if _property(original, item) != {"type": item["value_type"], "value": item["before"]} or _property(damaged, item) != {"type": item["value_type"], "value": item["after"]}:
            failures.append("property_before_after_mismatch:" + item["guid"])
    excluded_meshes = removed | {item["host"]["guid"] for item in manifest["deletions"] if item.get("host") and not item.get("preserve_opening", True)}
    candidates = sorted((product for product in original.by_type("IfcElement") if str(product.GlobalId) not in excluded_meshes and product.Representation is not None), key=lambda p: str(p.GlobalId))
    mesh_checked, mesh_errors = 0, []
    for product in candidates:
        if mesh_checked >= 3:
            break
        try:
            a, af = _mesh(product)
            b, bf = _mesh(damaged.by_guid(product.GlobalId))
            if a.shape != b.shape or af.shape != bf.shape or not np.array_equal(af, bf) or not np.allclose(a, b, atol=1e-8, rtol=0):
                failures.append("unchanged_mesh_mismatch:" + str(product.GlobalId))
            mesh_checked += 1
        except Exception as exc:
            mesh_errors.append({"guid": str(product.GlobalId), "reason": str(exc)[:200]})
            failures.append("preserved_mesh_check_error:" + str(product.GlobalId))
    prompt_checks = 0
    for frame, meta in case["prompt_templates"].items():
        if not meta["applicable"]:
            continue
        path = folder / "public" / f"request-{frame}.txt"
        text = path.read_text(encoding="utf-8")
        if sha256(path) != meta["sha256"] or any(guid in text for guid in removed):
            failures.append("prompt_hash_or_identity_failed:" + frame)
        matches = re.findall(r"放置原点[^。；]*?为[（(]([^）)]+)[）)]米", text)
        expected = [item["geometry"]["origin_world_m" if frame == "world" else "origin_host_m" if frame == "host_wall" else "origin_storey_m"] for item in targets]
        if len(matches) != len(expected):
            failures.append("prompt_coordinate_count_mismatch:" + frame)
        else:
            for token, point in zip(matches, expected):
                parsed = [float(v) for v in token.replace("，", ",").split(",")]
                if not np.allclose(parsed, point, atol=0.00000051, rtol=0):
                    failures.append("prompt_coordinate_value_mismatch:" + frame)
        prompt_checks += 1
    if mesh_checked == 0 and candidates:
        failures.append("no_independent_preserved_mesh_checked")
    return {"case_id": case["case_id"], "path": case["path"], "family": case["family"], "passed": not failures, "removed_identities_checked": len(removed), "coordinate_checks": coordinate_checks, "property_changes_checked": len(manifest["property_changes"]), "prompt_templates_checked": prompt_checks, "preserved_world_meshes_checked": mesh_checked, "mesh_errors": mesh_errors, "failures": failures, "human_reviewed": False}


def sample_dataset(root: Path, *, count=24, seed=42) -> dict:
    root = Path(root)
    candidates = []
    for path in sorted((root / "sources").glob("*/result.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        candidates.extend(case for case in result["cases"] if case["status"] == "passed")
    rng = random.Random(seed)
    rng.shuffle(candidates)
    selected = []
    families = sorted({case["family"] for case in candidates})
    for family in families:
        for prefix in ("formal-", "external-"):
            item = next((case for case in candidates if case["family"] == family and case["case_id"].startswith(prefix) and case not in selected), None)
            if item and len(selected) < count:
                selected.append(item)
    selected.extend(case for case in candidates if case not in selected and len(selected) < count)
    selected = selected[:count]
    results = [inspect_case(root, case) for case in selected]
    report = {"schema_version": "text2ifc/ifc-repair-dataset-sampling/1.0", "seed": seed, "requested_samples": count, "checked_samples": len(results), "passed_samples": sum(row["passed"] for row in results), "passed": bool(results) and all(row["passed"] for row in results), "checked_families": sorted({row["family"] for row in results}), "provider_calls": 0, "human_reviewed": False, "scope": "stratified independent removed identities, typed properties, world/storey coordinate and actual prompt text checks; up to three surviving world meshes per sampled case", "results": results}
    write_json(root / "sampling.json", report)
    return report
