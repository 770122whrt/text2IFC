"""Synthetic controls for the host-only evaluator; never live repair evidence."""
from __future__ import annotations

import importlib
import ast
import json
from pathlib import Path
import types

import ifcopenshell
import pytest
from ifcopenshell.api.root.remove_product import remove_product

from scripts.ifc_repair.repair_comparison.contracts import sha256
from tests.ifc_repair.dataset_batch.conftest import scene_factory


def evaluator():
    return importlib.import_module("scripts.ifc_repair.repair_comparison.host_evaluator")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def synthetic_dataset(tmp_path, scene_factory, monkeypatch):
    module = evaluator()
    root = tmp_path / "dataset"
    production = root / "private/production"
    public = root / "public"
    public.mkdir(parents=True)
    provenance, cases = [], []
    for index, kind in enumerate(("geometry", "property", "mixed")):
        identifier = f"synthetic-{kind}"
        source = production / "sources" / str(index) / "private/reference.ifc"
        source.parent.mkdir(parents=True)
        scene_factory(source, shared_property=False)
        damaged = ifcopenshell.open(str(source))
        deletions, changes = [], []
        if kind != "property":
            beam = damaged.by_type("IfcBeam")[0]
            deletions.append({"guid": beam.GlobalId, "ifc_class": "IfcBeam"})
            remove_product(damaged, product=beam)
        if kind != "geometry":
            window = damaged.by_type("IfcWindow")[0]
            prop = module._nominal(window, "Pset_WindowCommon.Reference")
            # The recorded before-value is deliberately absent from G.
            changes.append({"guid": window.GlobalId, "pset_name": "Pset_WindowCommon",
                            "property_name": "Reference", "value_type": "IfcIdentifier",
                            "before": "case-specific restored", "after": "damaged"})
            prop.NominalValue = damaged.create_entity("IfcIdentifier", "damaged")
        model = public / (identifier + ".ifc")
        damaged.write(str(model))
        request = public / (identifier + ".txt")
        request.write_text("Synthetic authored request", encoding="utf-8")
        folder = production / "sources" / str(index) / "cases" / identifier
        meta = folder / "case.json"
        manifest = folder / "private/mutation.json"
        write_json(meta, {"source_sha256": sha256(source)})
        write_json(manifest, {"schema_version": "text2ifc/ifc-repair-dataset-mutation/1.3",
                             "source_sha256": sha256(source), "damaged_sha256": sha256(model),
                             "deletions": deletions, "property_changes": changes})
        seal = folder / "private/seal.json"
        write_json(seal, {"sha256": {"case.json": sha256(meta), "private/mutation.json": sha256(manifest)}})
        provenance.append({"case_id": identifier, "source_id": str(index),
                           "case_path": str(folder.relative_to(production))})
        cases.append({"case_id": identifier, "model_path": str(model), "request_path": str(request),
                      "category": kind, "input_digests": {"model.ifc": sha256(model), "request.txt": sha256(request)},
                      "upstream_admission": {"metadata_bindings": {str(seal): sha256(seal)}}})
    export = root / "private/evaluation/export.json"
    write_json(export, {"pair_provenance": provenance})

    def selected(public_root, *, case_ids, delivery_receipt):
        assert public_root == public
        assert len(set(case_ids)) == len(case_ids)
        return [row for row in cases if row["case_id"] in case_ids]

    monkeypatch.setattr(module, "load_pair_candidates", selected)
    return root, cases


def test_explicit_arbitrary_cases_get_positive_negative_and_native_controls(synthetic_dataset, tmp_path):
    module = evaluator()
    root, cases = synthetic_dataset
    selected = [row["case_id"] for row in reversed(cases)]
    state = tmp_path / "round"
    report = module.prepare_evaluator(root, selected, state)
    assert report["evaluator_admitted"] is True
    assert report["passed_cases"] == 3
    assert [row["case_id"] for row in report["cases"]] == selected
    assert all(row["positive"] == "passed" and row["damaged"] == "failed"
               and row["native_schema_express"] is True for row in report["cases"])
    visible = json.dumps(report)
    assert "case-specific restored" not in visible and "private/" not in visible
    assert module.prepare_evaluator(root, selected, state) == report


def test_frozen_bindings_reject_input_drift_and_case_reselection(synthetic_dataset, tmp_path):
    module = evaluator()
    root, cases = synthetic_dataset
    state = tmp_path / "round"
    assert module.prepare_evaluator(root, [cases[0]["case_id"]], state)["evaluator_admitted"]
    with pytest.raises(module.EvaluatorError, match="EVALUATOR_SELECTION_CHANGED"):
        module.prepare_evaluator(root, [cases[1]["case_id"]], state)
    path = Path(cases[0]["model_path"])
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(module.EvaluatorError, match="EVALUATOR_INPUT_BINDING_CHANGED"):
        module.prepare_evaluator(root, [cases[0]["case_id"]], state)


def test_positive_format_failure_blocks_the_entire_selection(synthetic_dataset, tmp_path, monkeypatch):
    module = evaluator()
    root, cases = synthetic_dataset
    monkeypatch.setattr(module, "native_validate", lambda _: {"passed": False})
    report = module.prepare_evaluator(root, [cases[0]["case_id"]], tmp_path / "round")
    assert report["evaluator_admitted"] is False and report["passed_cases"] == 0
    assert "POSITIVE_NATIVE_INVALID" in report["cases"][0]["codes"]
    with pytest.raises(module.EvaluatorError, match="EVALUATOR_SELF_CHECK_REQUIRED"):
        module.evaluate_result(tmp_path / "round", cases[0]["case_id"], tmp_path / "output.ifc")


def test_oracle_bytes_cannot_be_submitted_as_live_output(synthetic_dataset, tmp_path):
    module = evaluator()
    root, cases = synthetic_dataset
    state = tmp_path / "round"
    module.prepare_evaluator(root, [cases[1]["case_id"]], state)
    binding = json.loads((state / "private/evaluator-bindings.json").read_text(encoding="utf-8"))
    oracle = Path(binding["cases"][0]["positive_control"]["path"])
    output = tmp_path / "output.ifc"
    output.write_bytes(oracle.read_bytes())
    with pytest.raises(module.EvaluatorError, match="EVALUATOR_ORACLE_IS_NOT_LIVE_OUTPUT"):
        module.evaluate_result(state, cases[1]["case_id"], output)


@pytest.mark.parametrize("native_pass", [True, False])
def test_result_api_requires_independent_comparison_and_native_validation(synthetic_dataset, tmp_path, monkeypatch, native_pass):
    module = evaluator()
    root, cases = synthetic_dataset
    state = tmp_path / "round"
    module.prepare_evaluator(root, [cases[1]["case_id"]], state)
    binding = json.loads((state / "private/evaluator-bindings.json").read_text(encoding="utf-8"))
    model = ifcopenshell.open(binding["cases"][0]["positive_control"]["path"])
    model.header.file_name.name = "synthetic-test-result.ifc"
    output = tmp_path / "output.ifc"
    model.write(str(output))
    if not native_pass:
        monkeypatch.setattr(module, "native_validate", lambda _: {"passed": False})
    report = module.evaluate_result(state, cases[1]["case_id"], output)
    assert report["status"] == ("passed" if native_pass else "failed")
    assert report["native_schema_express"] is native_pass
    if not native_pass:
        assert report["codes"] == ["NATIVE_SCHEMA_EXPRESS"]


def test_exact_property_type_and_non_task_preservation_are_mandatory(synthetic_dataset, tmp_path):
    module = evaluator()
    root, cases = synthetic_dataset
    state = tmp_path / "round"
    module.prepare_evaluator(root, [cases[1]["case_id"]], state)
    binding = json.loads((state / "private/evaluator-bindings.json").read_text(encoding="utf-8"))
    case = binding["cases"][0]
    result = ifcopenshell.open(case["positive_control"]["path"])
    expected = json.loads(Path(case["manifest_path"]).read_text(encoding="utf-8"))["property_changes"][0]
    prop = module._nominal(result.by_guid(expected["guid"]), "Pset_WindowCommon.Reference")
    prop.NominalValue = result.create_entity("IfcLabel", expected["before"])
    result.by_type("IfcWall")[0].Name = "Unrequested change"
    path = tmp_path / "wrong.ifc"
    result.write(str(path))
    report = module.evaluate_result(state, cases[1]["case_id"], path)
    assert report["status"] == "failed"
    assert {"PROPERTY_VALUE_OR_TYPE", "PRESERVATION"} <= set(report["codes"])


def test_unknown_manifest_schema_stops_without_resampling(synthetic_dataset, tmp_path):
    module = evaluator()
    root, cases = synthetic_dataset
    manifest = root / "private/production/sources/0/cases/synthetic-geometry/private/mutation.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["schema_version"] = "future-unsupported"
    write_json(manifest, data)
    seal = manifest.parent / "seal.json"
    data = json.loads(seal.read_text(encoding="utf-8"))
    data["sha256"]["private/mutation.json"] = sha256(manifest)
    write_json(seal, data)
    cases[0]["upstream_admission"]["metadata_bindings"][str(seal)] = sha256(seal)
    with pytest.raises(module.EvaluatorError, match="EVALUATOR_MUTATION_UNSUPPORTED"):
        module.prepare_evaluator(root, [cases[0]["case_id"]], tmp_path / "round")


def test_damaged_control_that_passes_blocks_admission(synthetic_dataset, tmp_path, monkeypatch):
    module = evaluator()
    root, cases = synthetic_dataset
    monkeypatch.setattr(module, "_compare", lambda *_: {"status": "passed", "codes": []})
    report = module.prepare_evaluator(root, [cases[0]["case_id"]], tmp_path / "round")
    assert not report["evaluator_admitted"]
    assert "DAMAGED_NEGATIVE_INVALID" in report["cases"][0]["codes"]


def test_summary_tampering_cannot_promote_control_failure(synthetic_dataset, tmp_path, monkeypatch):
    module = evaluator()
    root, cases = synthetic_dataset
    state = tmp_path / "round"
    monkeypatch.setattr(module, "native_validate", lambda _: {"passed": False})
    report = module.prepare_evaluator(root, [cases[0]["case_id"]], state)
    assert not report["evaluator_admitted"]
    report["evaluator_admitted"] = True
    write_json(state / "evaluator-summary.json", report)
    with pytest.raises(module.EvaluatorError, match="EVALUATOR_ADMISSION_CHANGED"):
        module.prepare_evaluator(root, [cases[0]["case_id"]], state)


def test_surface_without_independent_witness_cannot_pass(synthetic_dataset, tmp_path, monkeypatch):
    module = evaluator()
    root, cases = synthetic_dataset
    monkeypatch.setattr(module, "_same_centered_surface", lambda *_: False)
    report = module.prepare_evaluator(root, [cases[0]["case_id"]], tmp_path / "round")
    assert not report["evaluator_admitted"]
    assert report["cases"][0]["positive"] == "review_required"
    assert "GEOMETRY_SURFACE_UNPROVEN" in report["cases"][0]["codes"]


def test_comparison_migration_matches_frozen_legacy_on_all_synthetic_controls(synthetic_dataset, tmp_path):
    module = evaluator()
    if not module.LEGACY_SOURCE.is_file():
        pytest.skip("One-time migration check requires the preserved historical source script")
    root, cases = synthetic_dataset
    state = tmp_path / "round"
    module.prepare_evaluator(root, [row["case_id"] for row in cases], state)
    binding = json.loads((state / "private/evaluator-bindings.json").read_text(encoding="utf-8"))
    # Load only source definitions; no historical plan, IFC, output, or report.
    tree = ast.parse(module.LEGACY_SOURCE.read_text(encoding="utf-8"))
    definitions = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef))
                   or isinstance(node, ast.Assign) and any(isinstance(name, ast.Name) and name.id == "TOLERANCE_M"
                                                           for name in node.targets)]
    legacy = types.ModuleType("synthetic_legacy_evaluator")
    legacy.__file__, legacy.REPO = str(module.LEGACY_SOURCE), module.REPO
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(module.LEGACY_SOURCE), "exec"), legacy.__dict__)
    legacy.DATASET = root / "private/production"
    legacy.CASES, legacy.SOURCES = {}, {}
    for case in binding["cases"]:
        key = case["case_id"]
        legacy.CASES[key] = {"model_path": case["model_path"], "source_id": key,
                             "source_sha256": sha256(Path(case["reference_path"])),
                             "dataset_path": str(Path(case["manifest_path"]).parent.parent.relative_to(legacy.DATASET))}
        legacy.SOURCES[key] = {"input_path": case["reference_path"]}
        for path in (case["positive_control"]["path"], case["model_path"]):
            old, migrated = legacy.check(key, path), module._compare(case, path)
            assert migrated["status"] == old["status"]
            assert migrated["preservation"] == old["preservation"]


@pytest.mark.parametrize("corruption,code", [("floor", "FLOOR_MEMBERSHIP"), ("host", "HOST_OR_OPENING"),
                                             ("opening", "HOST_OR_OPENING"), ("position", "GEOMETRY_POSITION")])
def test_hosted_geometry_checks_remain_independent(scene_factory, tmp_path, corruption, code):
    module = evaluator()
    reference = scene_factory(tmp_path / "reference.ifc", shared_property=False)
    damaged = ifcopenshell.open(str(reference))
    target = damaged.by_type("IfcWindow")[0]
    target_id = target.GlobalId
    opening_id = target.FillsVoids[0].RelatingOpeningElement.GlobalId
    remove_product(damaged, product=target)
    damaged_path = tmp_path / "damaged.ifc"
    damaged.write(str(damaged_path))
    manifest = tmp_path / "mutation.json"
    write_json(manifest, {"deletions": [{"guid": target_id, "ifc_class": "IfcWindow",
                                         "opening_guid": opening_id, "preserve_opening": True}], "property_changes": []})
    case = {"manifest_path": str(manifest), "reference_path": str(reference), "model_path": str(damaged_path)}
    assert module._compare(case, reference)["status"] == "passed"
    result = ifcopenshell.open(str(reference))
    target = result.by_guid(target_id)
    if corruption == "floor":
        target.ContainedInStructure[0].RelatedElements = tuple(p for p in target.ContainedInStructure[0].RelatedElements if p != target)
        wrong_floor = result.create_entity("IfcBuildingStorey", GlobalId=ifcopenshell.guid.new(),
                                           OwnerHistory=target.OwnerHistory, Name="Wrong floor", CompositionType="ELEMENT")
        result.create_entity("IfcRelContainedInSpatialStructure", GlobalId=ifcopenshell.guid.new(),
                             OwnerHistory=target.OwnerHistory, RelatingStructure=wrong_floor, RelatedElements=[target])
    elif corruption == "host":
        result.by_guid(opening_id).VoidsElements[0].RelatingBuildingElement = result.by_type("IfcBeam")[0]
    elif corruption == "opening":
        opening = result.by_guid(opening_id)
        opening.Representation.Representations[0].Items[0].Depth += 0.01
    else:
        xyz = list(target.ObjectPlacement.RelativePlacement.Location.Coordinates)
        xyz[0] += 0.01
        target.ObjectPlacement.RelativePlacement.Location.Coordinates = tuple(xyz)
    output = tmp_path / "wrong.ifc"
    result.write(str(output))
    checked = module._compare(case, output)
    assert checked["status"] == "failed" and code in checked["codes"]
