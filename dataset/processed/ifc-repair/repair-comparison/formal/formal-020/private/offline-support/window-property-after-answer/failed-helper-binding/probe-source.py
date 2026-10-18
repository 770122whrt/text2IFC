"""Bound 020 mixed repair after one prewritten answer; no model or private G input."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import traceback

HERE = Path(__file__).absolute().parent
REPO = next(parent for parent in HERE.parents if (parent / "pyproject.toml").is_file() and (parent / "src/text2ifc_ifc_repair").is_dir())
BASE = REPO / ".tmp/repair-comparison-formal-expansion"
PACKAGE = next((parent for parent in [HERE, *HERE.parents] if parent.name == "formal-020" and (parent / "private/task.json").is_file()), BASE / "next-ten-packages/formal-020")
ROOT = PACKAGE / "private/offline-support/window-property-after-answer"
sys.path[:0] = [str(REPO), str(REPO / "src")]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=str)+"\n", encoding="utf-8")
    if path.name == "phase.json":
        print(json.dumps(value, ensure_ascii=True), flush=True)


def parse_request(request: str) -> dict:
    num = r"(-?\d+(?:\.\d+)?)"
    target = re.search(r"1．在标高\s*"+num+r"\s*米的楼层，平面中心约（X="+num+r"、Y="+num+r"\s*米）", request)
    reference = re.search(r"请参照标高\s*"+num+r"\s*米楼层、平面中心约（X="+num+r"、Y="+num+r"\s*米）", request)
    sizes = re.search(r"窗名义宽\s*"+num+r"\s*毫米、高\s*"+num+r"\s*毫米；墙洞宽\s*"+num+r"\s*毫米、高\s*"+num+r"\s*毫米", request)
    door = re.search(r"2．标高\s*"+num+r"\s*米的楼层，平面中心约在（X="+num+r"、Y="+num+r"\s*米）、实体竖向范围为 Z="+num+r"\s*至\s*"+num+r"\s*米", request)
    if not all((target, reference, sizes, door)) or "请恢复为外门" not in request:
        raise ValueError("PUBLIC_REQUEST_SPEC_PARSING_FAILED")
    return {"window_storey_world_m": float(target[1]), "window_xy_m": [float(target[2]), float(target[3])],
            "reference_storey_world_m": float(reference[1]), "reference_xy_m": [float(reference[2]), float(reference[3])],
            "window_width_mm": float(sizes[1]), "window_height_mm": float(sizes[2]),
            "opening_width_mm": float(sizes[3]), "opening_height_mm": float(sizes[4]),
            "door_storey_world_m": float(door[1]), "door_xy_m": [float(door[2]), float(door[3])],
            "door_z_m": [float(door[4]), float(door[5])], "door_IsExternal": True,
            "source": "parsed original public request only"}


def direct_values(entity, set_name, name) -> list[dict]:
    values = []
    for relation in entity.IsDefinedBy:
        if not relation.is_a("IfcRelDefinesByProperties"):
            continue
        pset = relation.RelatingPropertyDefinition
        if not pset.is_a("IfcPropertySet") or pset.Name != set_name:
            continue
        for item in pset.HasProperties:
            if item.is_a("IfcPropertySingleValue") and item.Name == name:
                value = item.NominalValue
                values.append({"value": value.wrappedValue if value is not None else None,
                               "value_type": value.is_a() if value is not None else None,
                               "unit": str(item.Unit) if item.Unit is not None else None})
    return values


def run() -> dict:
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.placement
    import ifcopenshell.util.unit
    import numpy as np
    from scripts.ifc_repair.offline.run_phase12_public_structural_repair import _production_evidence_document
    from scripts.ifc_repair.repair_comparison.inspection import native_validation
    from scripts.ifc_repair.repair_comparison.viewer import collect_meshes
    from text2ifc_ifc_repair.apply import apply_changeset
    from text2ifc_ifc_repair.changesets import bind_repair_changeset
    from text2ifc_ifc_repair.compare import compare_ifc_models
    from text2ifc_ifc_repair.evaluation import evaluation_to_dict
    from text2ifc_ifc_repair.geometry import straight_wall_axis, wall_dimensions_mm, opening_position_in_wall_mm
    from text2ifc_ifc_repair.index_store import SQLiteIndexRepository
    from text2ifc_ifc_repair.indexer import build_ifc_index
    from text2ifc_ifc_repair.operations import create_default_registry
    from text2ifc_ifc_repair.production_evaluation import ProductionEvaluationInputs, evaluate_production
    from text2ifc_ifc_repair.production_evidence import build_production_evidence
    from text2ifc_ifc_repair.registry import OperationRegistry
    from text2ifc_ifc_repair.repair_intent import RepairIntent, hash_request
    from text2ifc_ifc_repair.resolution_flow import resolve_repair_intent
    from text2ifc_ifc_repair.semantic_authoring import semantic_manifest_to_dict, semantic_manifest_expected_facts
    from text2ifc_knowledge.property_search import create_historical_alias_baseline_resolver

    started = time.monotonic()
    if ROOT.exists():
        raise FileExistsError("MIXED_EVIDENCE_MUST_NOT_BE_OVERWRITTEN")
    initial = (PACKAGE / "public/request.txt").read_text(encoding="utf-8").strip()
    public = parse_request(initial)
    card = read(PACKAGE / "private/answer-card.json")
    if card["required_user_facts"] != ["window_opening_bottom"] or card["status"] != "pending_human_review":
        raise ValueError("PREWRITTEN_HEIGHT_CARD_SCOPE_CHANGED")
    fact = deepcopy(card["facts"]["window_opening_bottom"])
    # The card is the explicitly simulated answer channel. No task mutation map,
    # private target identity or source G geometry is used in public execution.
    public["opening_bottom_world_m"] = float(fact["world_elevation_m"])
    public["answer_source"] = "prewritten answer, deterministic offline fixture; no model question or human reply"
    request = initial+"\n\n澄清答复（离线预写事实）：\n"+fact["answer_text"]
    ROOT.mkdir(parents=True)
    shutil.copy2(Path(__file__), ROOT / "probe-source.py")
    damaged = ROOT / "damaged.ifc"
    shutil.copy2(PACKAGE / "public/model.ifc", damaged)
    protected = [PACKAGE / "public/model.ifc", PACKAGE / "public/request.txt", PACKAGE / "private/reference.ifc", PACKAGE / "private/mutation/damaged.ifc"]
    protected_before = {path.relative_to(PACKAGE).as_posix(): sha(path) for path in protected}
    (ROOT / "request-initial.txt").write_text(initial+"\n", encoding="utf-8")
    (ROOT / "request-after-answer.txt").write_text(request+"\n", encoding="utf-8")
    write(ROOT / "simulated-answer.json", {"fact_id": "window_opening_bottom", "answer": fact,
          "questions_generated": False, "human_reply_observed": False, "model_calls": 0})
    write(ROOT / "public-facts.json", public)
    write(ROOT / "phase.json", {"stage": "public-only-selection"})
    dmodel = ifcopenshell.open(damaged)
    unit = ifcopenshell.util.unit.calculate_unit_scale(dmodel)
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)

    def bounds(entity):
        shape = ifcopenshell.geom.create_shape(settings, entity)
        vertices = np.asarray(shape.geometry.verts).reshape(-1, 3)
        return np.asarray([[vertices[:, i].min(), vertices[:, i].max()] for i in range(3)])

    def storeys(entity):
        return [(str(relation.RelatingStructure.GlobalId),
                 float(ifcopenshell.util.placement.get_local_placement(relation.RelatingStructure.ObjectPlacement)[2, 3])*unit)
                for relation in entity.ContainedInStructure if relation.RelatingStructure.is_a("IfcBuildingStorey")]

    reference_hits = []
    for entity in dmodel.by_type("IfcWindow"):
        if len(list(entity.FillsVoids)) != 1:
            continue
        floor = storeys(entity)
        if len(floor) != 1 or abs(floor[0][1]-public["reference_storey_world_m"]) > .001:
            continue
        if abs(float(entity.OverallWidth)*unit*1000-public["window_width_mm"]) > .01 or abs(float(entity.OverallHeight)*unit*1000-public["window_height_mm"]) > .01:
            continue
        opening = entity.FillsVoids[0].RelatingOpeningElement
        if np.max(np.abs(bounds(opening)[:2].mean(axis=1)-public["reference_xy_m"])) <= .001:
            reference_hits.append(entity)
    if len(reference_hits) != 1:
        raise ValueError("PUBLIC_REFERENCE_COORDINATES_NOT_UNIQUE")
    reference = reference_hits[0]
    ref_opening = reference.FillsVoids[0].RelatingOpeningElement
    if len(list(ref_opening.VoidsElements)) != 1:
        raise ValueError("PUBLIC_REFERENCE_HOST_NOT_UNIQUE")
    wall = ref_opening.VoidsElements[0].RelatingBuildingElement
    host_storeys = storeys(wall)
    if len(host_storeys) != 1 or abs(host_storeys[0][1]-public["window_storey_world_m"]) > .001:
        raise ValueError("REQUESTED_WINDOW_STOREY_UNSUPPORTED_BY_HOST_CONTAINMENT")
    types = [relation.RelatingType for relation in reference.IsDefinedBy if relation.is_a("IfcRelDefinesByType")]
    if len(types) != 1 or not types[0].RepresentationMaps:
        raise ValueError("PUBLIC_REFERENCE_MAPPED_TYPE_REQUIRED")
    wall_matrix = ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement)
    point = np.linalg.inv(wall_matrix) @ np.asarray([public["window_xy_m"][0]/unit, public["window_xy_m"][1]/unit, public["opening_bottom_world_m"]/unit, 1.])
    axis_start, axis_end = straight_wall_axis(wall)
    axis = np.asarray(axis_end)-np.asarray(axis_start)
    axis /= np.linalg.norm(axis)
    center_mm = float(np.dot(point[:3]-axis_start, axis))*unit*1000
    sill_mm = float(point[2])*unit*1000
    dims = wall_dimensions_mm(wall)
    wall_bounds = bounds(wall)
    if not (public["opening_width_mm"]/2 <= center_mm <= dims["length"]-public["opening_width_mm"]/2 and
            wall_bounds[2, 0]-.001 <= public["opening_bottom_world_m"] and
            public["opening_bottom_world_m"]+public["opening_height_mm"]/1000 <= wall_bounds[2, 1]+.001):
        raise ValueError("PUBLIC_REQUEST_OPENING_OUTSIDE_HOST")
    door_hits = []
    for entity in dmodel.by_type("IfcDoor"):
        floor = storeys(entity)
        if len(floor) != 1 or abs(floor[0][1]-public["door_storey_world_m"]) > .001:
            continue
        box = bounds(entity)
        if np.max(np.abs(box[:2].mean(axis=1)-public["door_xy_m"])) <= .001 and np.max(np.abs(box[2]-public["door_z_m"])) <= .001:
            door_hits.append(entity)
    if len(door_hits) != 1:
        raise ValueError("PUBLIC_DOOR_COORDINATES_NOT_UNIQUE")
    door = door_hits[0]
    selection = {"selection_source": "D-only world geometry and initial public facts", "wall_id": str(wall.GlobalId),
                 "reference_window_id": str(reference.GlobalId), "reference_type_id": str(types[0].GlobalId),
                 "door_id": str(door.GlobalId), "host_storey_id": host_storeys[0][0], "host_storey_world_m": host_storeys[0][1],
                 "reference_geometry_world_bounds_m": bounds(reference).tolist(), "door_geometry_world_bounds_m": bounds(door).tolist(),
                 "center_offset_wall_local_mm": center_mm, "opening_bottom_wall_local_mm": sill_mm,
                 "opening_bottom_world_m": public["opening_bottom_world_m"], "no_G_or_private_identity_used": True}
    write(ROOT / "public-selection.json", selection)
    source = {"source_kind": "user_request", "reference": "request:/text", "excerpt": request[:2048]}
    common = {"attribute_intents": [], "property_intents": [], "semantic_bundle_refs": [], "quantity_intents": [],
              "occurrence_reuse_intent": None, "prototype_intent": None, "provenance": [source]}
    operations = [
        {**deepcopy(common), "operation_id": "01-window", "operation_type": "add_window_with_opening_to_wall",
         "routing_intent": {"component_family": "window", "action": "add_with_opening", "operation_profile": "window.add-with-opening.v0.3", "source": source},
         "target_query": {"schema_version": "text2ifc/ifc-target-query/0.1", "allowed_ifc_classes": ["IfcWall"], "global_id": selection["wall_id"]},
         "parameters": {"position": {"reference": "wall_local_start", "center_offset_mm": center_mm},
                        "opening": {"width_mm": public["opening_width_mm"], "height_mm": public["opening_height_mm"], "sill_height_mm": sill_mm},
                        "window": {"fit_opening": True}},
         "attribute_intents": [{"intent_kind": "attribute", "name": key, "value": value, "source": source}
                               for key, value in (("OverallWidth", public["window_width_mm"]), ("OverallHeight", public["window_height_mm"]))],
         "prototype_intent": {"reference_kind": "global_id", "reference": selection["reference_type_id"], "source": source}},
        {**deepcopy(common), "operation_id": "02-door-property", "operation_type": "set_occurrence_properties",
         "routing_intent": {"component_family": "door", "action": "set_properties", "operation_profile": "occurrence.set-properties", "source": source},
         "target_query": {"schema_version": "text2ifc/ifc-target-query/0.1", "allowed_ifc_classes": ["IfcDoor"], "global_id": selection["door_id"]},
         "parameters": {}, "property_intents": [{"intent_kind": "exact_property", "set_name": "Pset_DoorCommon", "property_name": "IsExternal",
                                                   "raw_value": True, "raw_unit": None, "requested_value_type": "IfcBoolean", "scope": "occurrence_direct", "source": source}]},
    ]
    damaged_hash = "sha256:"+sha(damaged)
    intent_document = {"schema_version": "text2ifc/ifc-repair-intent/0.8", "request_id": "candidate-020-after-preset-answer",
                       "source_request_hash": hash_request(request), "model_fingerprint": damaged_hash,
                       "prompt_fingerprint": "sha256:"+hashlib.sha256(b"offline-bound-020-no-provider").hexdigest(),
                       "operations": operations, "unsupported_requests": [], "semantic_bundles": [], "provenance": [source]}
    write(ROOT / "public-intent-input.json", intent_document)
    registry = create_default_registry()
    intent = RepairIntent.from_dict(intent_document, registry=registry)
    write(ROOT / "phase.json", {"stage": "public-resolve"})
    metadata = build_ifc_index(damaged, ROOT / "target-index.sqlite")
    with SQLiteIndexRepository.open(ROOT / "target-index.sqlite") as repository:
        resolution = resolve_repair_intent(intent, repository, expected_source_sha256=metadata.source_ifc_sha256,
            operation_registry=registry, property_knowledge_resolver=create_historical_alias_baseline_resolver(),
            source_ifc_path=damaged, installation_references={"01-window": {
                "target_global_id": selection["wall_id"], "reference_global_id": selection["reference_window_id"]}})
        records = {row.ifc_global_id: row for row in repository.iter_records()}
        type_records = {row.ifc_global_id: row for row in repository.iter_type_records()}
    write(ROOT / "repair-intent.json", intent.to_dict())
    write(ROOT / "target-resolution.json", resolution.to_dict())
    if resolution.status != "resolved":
        raise ValueError("MIXED_PUBLIC_RESOLUTION_FAILED")
    policy_facts, absent = {}, {}
    canonical = []
    for resolved in resolution.operations:
        bound = {"operation_id": resolved.operation_id, "operation_type": resolved.operation_type,
                 "target": registry.bind_resolved_target(resolved.operation_type, resolved.target_global_id),
                 "parameters": resolved.to_dict()["parameters"], "evidence_refs": list(resolved.evidence_pointers)}
        canonical.append(bound)
        policy_facts[resolved.operation_id] = registry.build_semantic_policy_facts(resolved.operation_type, operation=bound)
        policy = registry.require_evaluation_policy(resolved.operation_type)
        absent[resolved.operation_id] = tuple(spec.check_id for spec in policy.semantic_facts if spec.applicability.value == "conditional")
    evidence = build_production_evidence(intent=intent, resolution=resolution, changeset={"operations": canonical}, registry=registry,
        records_by_global_id=records, type_records_by_global_id=type_records,
        deterministic_policy_facts_by_operation=policy_facts, verified_absent_categories_by_operation=absent)
    manifests = tuple(registry.build_semantic_manifest(evidence.operation_types[key], production_evidence=evidence,
        operation_id=key, base_model_fingerprint=damaged_hash) for key in sorted(evidence.operation_types))
    payload = {"schema_version": "text2ifc/ifc-repair-semantic-manifest-bundle/0.1", "manifests": [semantic_manifest_to_dict(row) for row in manifests]}
    canonical_payload = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n"
    (ROOT / "semantic-manifests.json").write_text(canonical_payload, encoding="utf-8")
    manifest_hash = "sha256:"+hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    scope = {"target_ids": list(dict.fromkeys(row.target_global_id for row in resolution.operations)), "forbidden_ids": []}
    refs = list(dict.fromkeys(ref for operation in canonical for ref in operation["evidence_refs"]))
    draft = {"schema_version": "text2ifc/ifc-repair-changeset-draft/0.2", "draft_id": "draft-candidate-020-mixed",
             "source_request_hash": intent.source_request_hash, "base_model_fingerprint": damaged_hash,
             "semantic_manifest_ref": "semantic-manifests.json", "semantic_manifest_sha256": manifest_hash,
             "semantic_summary": {"required": sum(len(row.assignments) for row in manifests), "conditional": 0, "not_required": 0},
             "scope": scope, "evidence_refs": refs, "preconditions": [], "postconditions": [], "operations": canonical}
    changeset = bind_repair_changeset(draft=draft, semantic_manifests=manifests,
        semantic_manifest_hashes={row.operation_id: manifest_hash for row in manifests},
        source_request_hash=intent.source_request_hash, base_model_fingerprint=damaged_hash,
        bound_schema_version="text2ifc/ifc-repair-changeset/0.4", resolved_authority={"operations": canonical, "scope": scope, "evidence_refs": refs})
    write(ROOT / "production-evidence.json", _production_evidence_document(evidence))
    write(ROOT / "bound-draft.json", draft)
    write(ROOT / "changeset.json", changeset)
    write(ROOT / "phase.json", {"stage": "atomic-apply"})
    candidate = ROOT / "repaired.candidate.ifc"
    application = apply_changeset(damaged_ifc_path=damaged, repair_request=request, changeset=changeset, output_path=candidate, registry=registry)
    write(ROOT / "application.json", application)
    if not application.get("valid") or not application.get("published"):
        raise ValueError("MIXED_ATOMIC_APPLICATION_FAILED")
    evaluation = evaluation_to_dict(evaluate_production(ProductionEvaluationInputs(
        damaged_ifc_path=damaged, repaired_ifc_path=candidate, changeset=changeset, application_result=application,
        registry=registry, expected_facts_by_operation={row.operation_id: semantic_manifest_expected_facts(row) for row in manifests})))
    write(ROOT / "evaluation.json", evaluation)
    if not evaluation["complete_repair_success"]:
        raise ValueError("MIXED_PRODUCTION_EVALUATION_FAILED")
    allowed = {str(item["global_id"]) for operation in application["operations"] for kind in ("created", "modified", "removed")
               for item in operation["changes"].get(kind, ()) if item.get("global_id")}
    comparison = compare_ifc_models(damaged, candidate, allowed_changed_ids=allowed)
    write(ROOT / "comparison.json", comparison)
    if not comparison["complete_preservation_success"]:
        raise ValueError("MIXED_PRESERVATION_FAILED")
    repaired_path = ROOT / "repaired.ifc"
    os.replace(candidate, repaired_path)
    application["output"]["path"] = str(repaired_path)
    write(ROOT / "application.json", application)
    write(ROOT / "phase.json", {"stage": "independent-post-publication-checks"})
    repaired = ifcopenshell.open(repaired_path)
    created_windows = [row for row in application["operations"][0]["changes"]["created"] if row["ifc_class"] == "IfcWindow"]
    if len(created_windows) != 1:
        raise ValueError("ONE_NEW_WINDOW_REQUIRED")
    window = repaired.by_guid(created_windows[0]["global_id"])
    opening = window.FillsVoids[0].RelatingOpeningElement
    opening_box = bounds(opening)
    window_box = bounds(window)
    nominal = [float(window.OverallWidth)*unit*1000, float(window.OverallHeight)*unit*1000]
    actual_floor = storeys(window)
    values = direct_values(repaired.by_guid(selection["door_id"]), "Pset_DoorCommon", "IsExternal")
    local_ref = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), reference)
    local_new = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), window)
    mesh_same = (tuple(local_ref.geometry.faces) == tuple(local_new.geometry.faces) and
                 len(local_ref.geometry.verts) == len(local_new.geometry.verts) and
                 np.max(np.abs(np.asarray(local_ref.geometry.verts)-np.asarray(local_new.geometry.verts))) <= 1e-9)
    # Reuse the preparation's already measured D baseline only on the private
    # evaluation side, after publication. Never load VIEW/G data for selection,
    # resolution, semantic authority, binding or application.
    view_path = PACKAGE / "VIEW.html"
    view = view_path.read_text(encoding="utf-8")
    embedded = re.search(r'<script id="ifc-data" type="application/json">(.*?)</script>', view, re.S)
    if embedded is None:
        raise ValueError("VERIFIED_D_MESH_BASELINE_NOT_FOUND")
    task_after_publication = read(PACKAGE / "private/task.json")
    if task_after_publication["damaged_sha256"] != sha(damaged):
        raise ValueError("D_MESH_BASELINE_ROLE_OR_FINGERPRINT_MISMATCH")
    dmeshes = json.loads(embedded.group(1))["after"]
    write(ROOT / "damaged-mesh-baseline.json", dmeshes)
    write(ROOT / "damaged-mesh-baseline-origin.json", {
        "role": "private evaluation only, previously actual IfcOpenShell D world meshes",
        "source": "VIEW.html embedded after field", "view_sha256": sha(view_path),
        "D_sha256": task_after_publication["damaged_sha256"],
        "D_hash_matches_executed_input": True, "loaded_after_publication": True,
        "source_G_meshes_used": False, "production_input": False,
        "mesh_count": len(dmeshes["meshes"]), "D_meshes_not_rebuilt": True})
    rmeshes = collect_meshes(repaired_path)
    write(ROOT / "repaired-actual-mesh-summary.json", {"generator": "ifcopenshell.geom", "version": ifcopenshell.version,
        "R_sha256": sha(repaired_path), "coordinates": rmeshes["coordinates"],
        "mesh_count": len(rmeshes["meshes"]), "errors": rmeshes["errors"],
        "each_retained_D_mesh_checked": True})
    unchanged_geometry = all(guid in rmeshes["meshes"] and mesh == rmeshes["meshes"][guid]
                             for guid, mesh in dmeshes["meshes"].items() if guid != selection["wall_id"])
    independent = {"opening_xy_max_error_mm": float(np.max(np.abs(opening_box[:2].mean(axis=1)-public["window_xy_m"]))*1000),
                   "opening_z_max_error_mm": float(np.max(np.abs(opening_box[2]-[public["opening_bottom_world_m"], public["opening_bottom_world_m"]+public["opening_height_mm"]/1000]))*1000),
                   "nominal_dimension_errors_mm": np.abs(np.asarray(nominal)-[public["window_width_mm"], public["window_height_mm"]]).tolist(),
                   "opening_dimensions_mm": opening_position_in_wall_mm(opening, repaired.by_guid(selection["wall_id"]))["geometry_bounds_mm"],
                   "window_bounds_world_m": window_box.tolist(), "reference_actual_local_mesh_identical": bool(mesh_same),
                   "host_forward_attributes_unchanged": wall.get_info(recursive=True, include_identifier=False) == repaired.by_guid(selection["wall_id"]).get_info(recursive=True, include_identifier=False),
                   "door_forward_attributes_unchanged": door.get_info(recursive=True, include_identifier=False) == repaired.by_guid(selection["door_id"]).get_info(recursive=True, include_identifier=False),
                   "window_unique_requested_storey": len(actual_floor) == 1 and abs(actual_floor[0][1]-public["window_storey_world_m"]) < .001,
                   "door_IsExternal": values, "door_unique_IfcBoolean_true": len(values) == 1 and values[0]["value"] is True and values[0]["value_type"] == "IfcBoolean" and values[0]["unit"] is None,
                   "other_product_geometry_unchanged": not dmeshes["errors"] and not rmeshes["errors"] and unchanged_geometry,
                   "preparation_geometry_tolerance_mm_not_formal_scoring_tolerance": .05}
    write(ROOT / "independent-public-requirements.json", independent)
    # The first G parse is after publication and after all public-fact checks.
    gold = ifcopenshell.open(PACKAGE / "private/reference.ifc")
    removed_windows = [entity for entity in gold.by_type("IfcWindow") if not any(str(entity.GlobalId) == str(keep.GlobalId) for keep in dmodel.by_type("IfcWindow"))]
    gold_check = {"G_first_opened_after_publication": True, "used_in_resolve_apply": False, "missing_window_count": len(removed_windows),
                  "bounds_error_mm": float(np.max(np.abs(bounds(removed_windows[0])-window_box))*1000) if len(removed_windows) == 1 else None}
    write(ROOT / "gold-post-publication-comparison.json", gold_check)
    native = native_validation(repaired)
    write(ROOT / "native-validation.json", native)
    # Explicitly injected second operation failure, fresh registry, no production edits.
    negative_registry = OperationRegistry()
    for operation_type in registry.operation_types:
        definition = registry.require(operation_type)
        if operation_type == "set_occurrence_properties":
            definition = replace(definition, postcondition_checker=lambda **kwargs: {"valid": False, "checks": [],
                "issues": [{"code": "INJECTED_OFFLINE_SECOND_OPERATION_FAILURE", "path": "/postconditions", "message": "Explicit offline atomic rollback probe"}]})
        negative_registry.register(definition)
    negative_output = ROOT / "atomic-must-not-publish.ifc"
    rollback = apply_changeset(damaged_ifc_path=damaged, repair_request=request, changeset=changeset, output_path=negative_output, registry=negative_registry)
    write(ROOT / "injected-atomic-rollback.json", rollback)
    rollback_ok = rollback.get("valid") is False and rollback.get("published") is False and not negative_output.exists() and sha(damaged) == damaged_hash.removeprefix("sha256:") and any(row.get("code") == "INJECTED_OFFLINE_SECOND_OPERATION_FAILURE" for row in rollback.get("issues", ()))
    unchanged = all(sha(path) == protected_before[path.relative_to(PACKAGE).as_posix()] for path in protected)
    result = {"schema_version": "repair-comparison-mixed-after-answer-support/0.1", "case": "020", "timestamp": datetime.now(timezone.utc).isoformat(),
              "one_atomic_changeset": len(changeset["operations"]) == 2, "operation_types": [row["operation_type"] for row in changeset["operations"]],
              "real_exact_resolver_manifest_binder_used": True, "production_evaluation_passed": evaluation["complete_repair_success"],
              "preservation_passed": comparison["complete_preservation_success"], "independent_public_requirements": independent,
              "post_publication_G_comparison": gold_check, "repaired_native_diagnostics": native["diagnostic_count"],
              "atomic_second_operation_rollback_passed": rollback_ok, "original_inputs_unchanged": unchanged,
              "questions_generated": False, "human_reply_observed": False, "provider_calls": 0,
              "initial_natural_clarification_or_resume_tested": False, "natural_property_retrieval_tested": False,
              "full_B_experiment_runtime_verified": False, "four_arm_admission": False, "review_status": "pending_human_review",
              "evidence_scope": "execution feasibility after prewritten height answer, exact standard property intent; not model performance",
              "seconds": time.monotonic()-started}
    result["passed"] = bool(result["one_atomic_changeset"] and result["production_evaluation_passed"] and result["preservation_passed"] and rollback_ok and unchanged and native["diagnostic_count"] == 0 and
        independent["opening_xy_max_error_mm"] <= .05 and independent["opening_z_max_error_mm"] <= .05 and max(independent["nominal_dimension_errors_mm"]) <= .05 and mesh_same and
        independent["window_unique_requested_storey"] and independent["door_unique_IfcBoolean_true"] and independent["other_product_geometry_unchanged"] and
        independent["host_forward_attributes_unchanged"] and independent["door_forward_attributes_unchanged"] and
        gold_check["missing_window_count"] == 1 and gold_check["bounds_error_mm"] <= .05)
    write(ROOT / "result.json", result)
    write(ROOT / "phase.json", {"stage": "complete", "passed": result["passed"]})
    (ROOT / "README.md").write_text("# formal-020 答复明确后的组合执行检查\n\n这是离线确定性检查，未调用模型、未生成问题、未观察真人回复；不证明自然澄清、检索、恢复或四组准入。\n\n"
        "输入只有本目录damaged.ifc、原request-initial.txt和明确模拟的simulated-answer.json。选择身份从公开D实际几何获得，不用私有目标Name/GUID；source G首次解析在发布后，只供独立比较。\n\n"
        "主结果result.json；真实既有exact resolver、semantic-manifests.json、bound-draft.json、changeset.json和application/evaluation/comparison记录完整保留；最终repaired.ifc仅在生产评价及保全通过后发布。\n\n"
        "independent-public-requirements.json核对洞口世界位置/高度、名义尺寸、实际参照网格、楼层及唯一IfcBoolean(true)。injected-atomic-rollback.json为明确注入的第二操作失败，不发布部分补窗。\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    try:
        result = run()
        print(json.dumps({key: result[key] for key in ("case", "passed", "atomic_second_operation_rollback_passed", "repaired_native_diagnostics", "seconds")}, ensure_ascii=True), flush=True)
        raise SystemExit(0 if result["passed"] else 1)
    except Exception as error:
        traceback.print_exc()
        if ROOT.exists() and not (ROOT / "result.json").is_file():
            write(ROOT / "failure.json", {"error_type": type(error).__name__, "message": str(error), "model_calls": 0, "evidence_role": "failed offline preparation; not formal score"})
        raise
