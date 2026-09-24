"""Recheck archived real roundtrip evidence offline; never invokes a Provider.

Writes a new evidence directory. --require-clean exits nonzero on the observed
roundtrip defects, so the same command can serve as a red-capable diagnosis.
No archived input, production code, or prompt is modified.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.semantic_coverage import build_design_geometry_expectation
from text2ifc_contract.materials import validate_materials
from text2ifc_contract.basic_filling import validate_basic_filling_document
from scripts.ifc2text.attribution_counterfactuals_v01 import profile_info
from scripts.ifc2text.attribute_roundtrip_v01 import mesh_bounds
from scripts.ifc2text.check_wall_context_v09 import compile_case


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--require-clean", action="store_true")
    parser.add_argument("--report-name", default="chain-audit.json")
    args = parser.parse_args()
    out = args.evidence_root.resolve()
    target = out / args.report_name
    if target.exists():
        raise FileExistsError(target)
    trace = load(out / "attribution/attribution.json")
    context = load(out / "wall-context/summary.json")
    run = ROOT / trace["baseline_run"]
    case = run.parents[2]
    source = ROOT / "dataset/external/bimnet/hxp.ifc"
    files = {
        "source_ifc": source,
        "extracted_facts": case / "source-facts.json",
        "text": case / "design-description.md",
        "brief_raw_response": run / "design-brief/response.raw.json",
        "brief": run / "design-brief/design-brief.json",
        "generator_raw_response": run / "generator/response.raw.json",
        "generator_parsed_output": run / "generator/parsed-output.json",
        "generator_candidate": run / "generator/candidate.json",
        "compiled_candidate": run / "candidate.json",
        "reconstructed_ifc": run / "output.ifc",
        "geometry_expectation": run / "geometry-expectation.json",
        "audit": run / "audit/parsed-output.json",
        "terminal": case / "reconstruction-128k/generation-result.json",
    }
    before = {key: digest(path) for key, path in files.items()}
    brief = load(files["brief"])
    expected = load(out / "attribution/expectation-replay/expected-facts.json")
    projected = copy.deepcopy(expected)
    raw = [(floor, space) for floor in brief["known_facts"]["storeys"]
           for space in floor.get("spaces", [])]
    for space in projected["spaces"]:
        matches = [(f, s) for f, s in raw if space["id"].lower() == s["id"].lower()
                   or space["id"].lower().endswith("-" + s["id"].lower())]
        assert len(matches) == 1
        floor, original = matches[0]
        points, z = original["polygon"], original["z_mm"]
        assert z[0] == floor["elevation_mm"]
        space["bounds"] = {axis: [min(p[i] for p in points), max(p[i] for p in points)]
                           for i, axis in enumerate("xy")}
        space["height_mm"] = z[1] - z[0]
    def geometry(facts):
        return build_design_geometry_expectation(case_id="audit", design_brief=brief, expected_facts=facts)
    initial, changed = geometry(expected), geometry(projected)

    import ifcopenshell
    original_model = ifcopenshell.open(str(source))
    rebuilt_model = ifcopenshell.open(str(files["reconstructed_ifc"]))
    wall_evidence = {}
    for label in ("W011", "W013", "W015"):
        record = trace["traces"][label]
        a = original_model.by_guid(record["source_observation"]["source_global_id"])
        b = rebuilt_model.by_guid(record["candidate_observation"]["source_global_id"])
        aa, bb = mesh_bounds(a, no_openings=True), mesh_bounds(b, no_openings=True)
        wall_evidence[label] = {
            "source_profiles": profile_info(a), "candidate_profiles": profile_info(b),
            "no_openings_bbox_size_delta_mm": {k: abs((aa[k][1]-aa[k][0])-(bb[k][1]-bb[k][0])) for k in "xyz"},
            "historical_text_rows": record["text_rows"],
        }
    merged = load(out / "wall-context/rebased.json")
    material_issues = [{"code": i.code, "path": i.path} for i in validate_materials(merged)]
    filling_issues = [{"code": i.code, "path": i.path} for i in validate_basic_filling_document(merged)]
    terminal = load(files["terminal"])
    facts = load(files["extracted_facts"])
    generator_raw = load(files["generator_raw_response"])
    raw_content = generator_raw["choices"][0]["message"]["content"]
    try:
        raw_parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        raw_parsed = None

    # Isolate D001's depth loss using only bounds already present in Brief.
    doors = [d for floor in brief["known_facts"]["storeys"] for d in floor.get("doors", []) if d["id"] == "D001"]
    assert len(doors) == 1
    y = doors[0]["solid_bbox_xyz_mm"]["y"]
    graph = copy.deepcopy(load(files["generator_candidate"]))
    door = next(e for e in graph["entities"] if e["ifc_class"] == "IfcDoor" and e["attributes"].get("Name") == "D001")
    rep = door["attributes"]["Representation"]
    assert rep["kind"] == "basic_filling" and "parameters" not in rep
    rep["parameters"] = {"frame_depth": y[1] - y[0]}
    door_path = out / (target.stem + "-door-counterfactual.ifc")
    if door_path.exists():
        raise FileExistsError(door_path)
    door_path.with_suffix(".json").write_text(json.dumps(graph, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    model, compilation = compile_case(graph, door_path)
    door_result = {"mode": "offline one-parameter counterfactual; no Provider and no production fix",
                   "changed_field": "D001 Representation.parameters.frame_depth", "value_mm": y[1]-y[0],
                   "fact_origin": "existing Brief solid_bbox_xyz_mm", "compilation": compilation}
    if model is not None:
        product = next(e for e in model.by_type("IfcDoor") if e.Name == "D001")
        bounds = mesh_bounds(product)
        src_bounds = trace["traces"]["D001"]["source_observation"]["bounds_mm"]
        old_bounds = trace["traces"]["D001"]["candidate_observation"]["bounds_mm"]
        door_result.update(source_bounds_mm=src_bounds, original_candidate_bounds_mm=old_bounds,
                           counterfactual_bounds_mm=bounds,
                           bbox_coordinate_max_delta_mm=max(abs(bounds[k][i]-src_bounds[k][i]) for k in "xyz" for i in (0,1)),
                           shape_equivalence_proven=False)
    report = {
        "evidence_kind": "fresh offline remeasurement of archived real Provider artifacts",
        "new_provider_calls": 0,
        "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "files": {key: {"path": str(path.relative_to(ROOT)), "sha256": before[key]} for key, path in files.items()},
        "source_fact_source_record": facts["source"],
        "source_fact_hash_matches_current_source": facts["source"]["sha256"] == "sha256:" + before["source_ifc"],
        "raw_generator_json_equals_parsed_output": raw_parsed == load(files["generator_parsed_output"]),
        "text_equals_brief_original_request": brief["original_request"] == files["text"].read_text(encoding="utf-8"),
        "generator_candidate_equals_compiled_candidate": load(files["generator_candidate"]) == load(files["compiled_candidate"]),
        "generator_parsed_equals_candidate": load(files["generator_parsed_output"]) == load(files["generator_candidate"]),
        "terminal": {k: terminal.get(k) for k in ("status", "audit_status", "gate_status", "exception", "ifc_role", "final_acceptance_exists")},
        "comparison": trace["comparison_summary"],
        "unassessed": {"count": trace["unassessed_record_count"], "reasons": trace["unassessed_reasons"]},
        "space_projection_counterfactual": {
            "mode": "only project polygon/z_mm already in Brief; not a production fix",
            "before_space_count": len(initial["spaces"]), "after_space_count": len(changed["spaces"]),
            "before_unresolved": initial["unresolved"], "after_unresolved": changed["unresolved"],
        },
        "wall_geometry": wall_evidence,
        "door_depth_counterfactual": door_result,
        "integrated_contract_reproduction": {
            "status": context["status"], "independent_material_validation": material_issues,
            "independent_filling_validation": filling_issues,
            "baseline_compiles": context["compilation"]["baseline"]["success"],
            "integrated_compiles": context["compilation"]["rebased"]["success"],
        },
        "all_archived_inputs_unchanged": all(digest(path) == before[key] for key, path in files.items()),
        "limitations": ["No fresh LLM generation or accepted whole-building IFC.",
                        "Bounds projection does not prove exact polygon or room semantics.",
                        "Archived normalized source in wall-context is separate from original-source comparison.",
                        "A diagnostic compiler replay is not the full public generation controller."],
    }
    report["roundtrip_clean"] = (not any(trace["comparison_summary"][k] for k in
        ("missing", "extra", "geometric_deviations", "material_content_differences", "relation_differences"))
        and not initial["unresolved"] and context["compilation"]["rebased"]["success"])
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(target), "roundtrip_clean": report["roundtrip_clean"],
        "spaces_before_after": [len(initial["spaces"]), len(changed["spaces"])],
        "integrated_compiles": context["compilation"]["rebased"]["success"],
        "inputs_unchanged": report["all_archived_inputs_unchanged"]}, ensure_ascii=False))
    return 1 if args.require_clean and not report["roundtrip_clean"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
