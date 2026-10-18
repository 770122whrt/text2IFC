"""Host-only compatibility evaluation for explicitly selected public IFC pairs.

This module never enters a repair runtime. It reads private expectations only
inside the evaluator, freezes them before a round, and returns code-only
summaries. Controls are synthetic evaluator self-tests, never live evidence.

Comparison criteria come from the 2026-10-10 smoke evaluator: 1 mm bounds,
centered geometric surface witness, floor/host/opening relations, exact instance
property value and IFC type, and preservation_v2. Native IFC2X3 schema and
EXPRESS validation remains mandatory. This is not a benchmark capability metric.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import ifcopenshell
import numpy as np

from scripts.ifc_repair.dataset_batch.prompt_check import _actual_host, _floor_of, _instance_property
from scripts.ifc_repair.dataset_batch.validation import native_validate
from scripts.ifc_repair.repair_comparison.batch_cases import load_pair_candidates
from scripts.ifc_repair.repair_comparison.contracts import sha256
from scripts.ifc_repair.repair_comparison.formal_scoring import _same_centered_surface
from scripts.ifc_repair.repair_comparison.preservation_v2 import preservation
from scripts.ifc_repair.repair_comparison.scoring import _bounds, _mesh
from text2ifc_ifc_repair.compare import normalized_model_diff


SCHEMA = "text2ifc/host-pair-evaluator/1.0"
CRITERIA = "smoke-20261010/geometry-property-preservation+native-express"
TOLERANCE_M = 0.001
REPO = Path(__file__).resolve().parents[3]
LEGACY_SOURCE = REPO / ".tmp/repair-e-random-20261010/check_results.py"


class EvaluatorError(ValueError):
    """A public-safe, fixed error code without private data or raw exceptions."""


def _need(condition, code):
    if not condition:
        raise EvaluatorError(code)


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        _need(_read(path) == value, "EVALUATOR_FROZEN_RECORD_CHANGED")
        return
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def _bind(path, bindings, expected=None):
    path = Path(path).resolve()
    actual = sha256(path)
    _need(expected is None or actual == expected, "EVALUATOR_INPUT_BINDING_CHANGED")
    _need(str(path) not in bindings or bindings[str(path)] == actual, "EVALUATOR_INPUT_BINDING_CHANGED")
    bindings[str(path)] = actual
    return path


def _bound_read(path, bindings, expected=None):
    return _read(_bind(path, bindings, expected))


def _recheck(bindings):
    for name, expected in bindings.items():
        path = Path(name)
        _need(path.is_file() and sha256(path) == expected, "EVALUATOR_INPUT_BINDING_CHANGED")


def _within(root, relative):
    path = (root / relative).resolve()
    _need(path.is_relative_to(root.resolve()), "EVALUATOR_PRIVATE_PATH_INVALID")
    return path


def _runtime():
    return {"python": platform.python_version(), "ifcopenshell": ifcopenshell.version, "numpy": np.__version__}


def _code_bindings():
    functions = (_bounds, _mesh, _same_centered_surface, preservation, _instance_property,
                 _floor_of, _actual_host, native_validate, normalized_model_diff, load_pair_candidates)
    paths = {Path(__file__).resolve(), *(Path(fn.__code__.co_filename).resolve() for fn in functions)}
    if LEGACY_SOURCE.is_file():
        paths.add(LEGACY_SOURCE)
    return {str(path): sha256(path) for path in sorted(paths)}


def _nominal(entity, path):
    matches = [prop for rel in entity.IsDefinedBy if rel.is_a("IfcRelDefinesByProperties")
               and rel.RelatingPropertyDefinition.is_a("IfcPropertySet")
               for prop in rel.RelatingPropertyDefinition.HasProperties
               if str(rel.RelatingPropertyDefinition.Name) + "." + str(prop.Name) == path]
    _need(len(matches) == 1 and matches[0].is_a("IfcPropertySingleValue"), "PROPERTY_NOT_UNIQUE")
    return matches[0]


def _geometry_mesh(entity):
    vertices, faces, _, _ = _mesh(entity)
    return vertices, faces, [], [-1] * len(faces)


def _compare(case, result_path):
    """The legacy geometric/property/preservation criteria, with fixed codes."""
    manifest = _read(case["manifest_path"])
    damaged = ifcopenshell.open(case["model_path"])
    reference = ifcopenshell.open(case["reference_path"])
    result = ifcopenshell.open(str(result_path))
    old = {product.GlobalId for product in damaged.by_type("IfcProduct")}
    new = [product for product in result.by_type("IfcProduct") if product.GlobalId not in old]
    checks, codes = [], []
    for target in manifest["deletions"]:
        expected = reference.by_guid(target["guid"])
        expected_bounds = _bounds(expected)
        candidates = [product for product in new if product.is_a() == expected.is_a()
                      and (bounds := _bounds(product)) is not None
                      and np.max(np.abs(bounds.mean(axis=1) - expected_bounds.mean(axis=1))) < 0.05]
        if len(candidates) != 1:
            checks.append(False)
            codes.append("GEOMETRY_TARGET_NOT_UNIQUE")
            continue
        actual = candidates[0]
        position = bool(np.max(np.abs(_bounds(actual) - expected_bounds)) <= TOLERANCE_M)
        surface = True if _same_centered_surface(_geometry_mesh(actual), _geometry_mesh(expected), "window") else None
        floor = _floor_of(actual)
        membership = floor is not None and floor.GlobalId == _floor_of(expected).GlobalId
        relations = True
        if actual.is_a() in {"IfcWindow", "IfcDoor"}:
            host, wanted_host = _actual_host(actual), _actual_host(expected)
            relations = host is not None and wanted_host is not None and host.GlobalId == wanted_host.GlobalId
            if relations:
                opening = actual.FillsVoids[0].RelatingOpeningElement
                wanted_opening = expected.FillsVoids[0].RelatingOpeningElement
                relations = bool(np.max(np.abs(_bounds(opening) - _bounds(wanted_opening))) <= TOLERANCE_M)
        checks.extend([position, surface, membership, relations])
        for flag, code in ((position, "GEOMETRY_POSITION"), (surface, "GEOMETRY_SURFACE_UNPROVEN"),
                           (membership, "FLOOR_MEMBERSHIP"), (relations, "HOST_OR_OPENING")):
            if flag is not True:
                codes.append(code)
    # Only normalize the requested property difference in an evaluator-owned
    # projection. The value and IFC type are checked before this normalization.
    shadow = ifcopenshell.file.from_string(result.to_string())
    for change in manifest["property_changes"]:
        path = change["pset_name"] + "." + change["property_name"]
        actual_type, value = _instance_property(result.by_guid(change["guid"]), path)
        correct = actual_type == change["value_type"] and type(value) is type(change["before"]) and value == change["before"]
        checks.append(correct)
        if not correct:
            codes.append("PROPERTY_VALUE_OR_TYPE")
        prop = _nominal(shadow.by_guid(change["guid"]), path)
        prop.NominalValue = shadow.create_entity(change["value_type"], change["after"])
    preserved = preservation(damaged, shadow, [product.GlobalId for product in new])
    checks.append(preserved["passed"])
    if not preserved["passed"]:
        codes.append("PRESERVATION")
    expected_new = len(manifest["deletions"]) + sum(bool(target.get("opening_guid")) and not target.get("preserve_opening", True)
                                                  for target in manifest["deletions"])
    checks.append(len(new) == expected_new)
    if len(new) != expected_new:
        codes.append("NEW_PRODUCT_COUNT")
    status = "failed" if False in checks else "review_required" if None in checks else "passed"
    return {"status": status, "codes": sorted(set(codes)), "preservation": preserved["passed"]}


def _manifest_contract(manifest, source_hash, damaged_hash):
    _need(manifest.get("schema_version") == "text2ifc/ifc-repair-dataset-mutation/1.3"
          and manifest.get("source_sha256") == source_hash
          and manifest.get("damaged_sha256") == damaged_hash, "EVALUATOR_MUTATION_UNSUPPORTED")
    deletions, changes = manifest.get("deletions"), manifest.get("property_changes")
    _need(isinstance(deletions, list) and isinstance(changes, list) and bool(deletions or changes),
          "EVALUATOR_MUTATION_UNSUPPORTED")
    _need(all(isinstance(row, dict) and {"guid", "ifc_class"} <= set(row) for row in deletions),
          "EVALUATOR_MUTATION_UNSUPPORTED")
    _need(all(isinstance(row, dict) and {"guid", "pset_name", "property_name", "value_type", "before", "after"} <= set(row)
              for row in changes), "EVALUATOR_MUTATION_UNSUPPORTED")


def _restore_properties(case, manifest, state):
    # A source reference is a valid geometry oracle only if preservation and
    # native validation prove it. For mixed cases restore recorded before-values
    # on G; for property-only cases start from D, whose psets may not exist in G.
    base = case["reference_path"] if manifest["deletions"] else case["model_path"]
    model = ifcopenshell.open(base)
    for change in manifest["property_changes"]:
        prop = _nominal(model.by_guid(change["guid"]), change["pset_name"] + "." + change["property_name"])
        prop.NominalValue = model.create_entity(change["value_type"], change["before"])
    path = state / "private/controls" / (case["case_id"] + ".ifc")
    _need(not path.exists(), "EVALUATOR_CONTROL_ALREADY_EXISTS")
    path.parent.mkdir(parents=True, exist_ok=True)
    model.write(str(path))
    return path, "evaluator_property_restoration_on_" + ("reference" if manifest["deletions"] else "damaged")


def _gather(dataset, case_ids, state, existing_controls):
    public = load_pair_candidates(dataset / "public", case_ids=case_ids,
                                  delivery_receipt=dataset / "private/finalization/summary.json")
    _need({row["case_id"] for row in public} == set(case_ids), "EVALUATOR_SELECTION_INVALID")
    bindings = _code_bindings()
    export = _bound_read(dataset / "private/evaluation/export.json", bindings)
    mapping = {row["case_id"]: row for row in export["pair_provenance"]}
    public_by_id = {row["case_id"]: row for row in public}
    production, cases = dataset / "private/production", []
    for case_id in case_ids:
        supplied, pair = public_by_id[case_id], mapping[case_id]
        for name, expected in supplied["upstream_admission"]["metadata_bindings"].items():
            _bind(name, bindings, expected)
        folder = _within(production, pair["case_path"])
        seal = _bound_read(folder / "private/seal.json", bindings)
        meta = _bound_read(folder / "case.json", bindings, seal["sha256"]["case.json"])
        manifest_path = folder / "private/mutation.json"
        manifest = _bound_read(manifest_path, bindings, seal["sha256"]["private/mutation.json"])
        model = _bind(supplied["model_path"], bindings, supplied["input_digests"]["model.ifc"])
        _bind(supplied["request_path"], bindings, supplied["input_digests"]["request.txt"])
        reference = _within(production / "sources", pair["source_id"] + "/private/reference.ifc")
        _bind(reference, bindings, meta["source_sha256"])
        _manifest_contract(manifest, meta["source_sha256"], supplied["input_digests"]["model.ifc"])
        case = {"case_id": case_id, "model_path": str(model), "reference_path": str(reference),
                "manifest_path": str(manifest_path), "oracle_preparation_codes": []}
        if case_id in existing_controls:
            control = existing_controls[case_id]
            control_path = _bind(control["path"], bindings, control["sha256"])
            role = "reused_frozen_evaluator_control"
        elif not manifest["property_changes"]:
            control_path, role = reference, "preassigned_private_reference_geometry_control"
        else:
            try:
                control_path, role = _restore_properties(case, manifest, state)
            except Exception:
                case["oracle_preparation_codes"] = ["ORACLE_RESTORATION_UNSUPPORTED"]
                control_path, role = None, "unsupported"
        if control_path is not None:
            _bind(control_path, bindings)
        case["positive_control"] = {"path": str(control_path) if control_path else None,
                                    "sha256": sha256(control_path) if control_path else None, "role": role}
        cases.append(case)
    _recheck(bindings)
    return {"schema_version": SCHEMA, "criteria_version": CRITERIA, "tolerance_m": TOLERANCE_M,
            "host_only": True, "dataset_root": str(dataset), "case_ids": case_ids,
            "runtime": _runtime(), "bindings": bindings, "cases": cases}


def _load_record(state):
    record = _read(state / "private/evaluator-bindings.json")
    _need(record.get("schema_version") == SCHEMA and record.get("criteria_version") == CRITERIA
          and record.get("runtime") == _runtime(), "EVALUATOR_CONTRACT_CHANGED")
    _recheck(record["bindings"])
    return record


def _self_check(record):
    rows = []
    for case in record["cases"]:
        row = {"case_id": case["case_id"], "passed": False, "positive": "unavailable",
               "native_schema_express": False, "damaged": "unavailable",
               "codes": list(case["oracle_preparation_codes"])}
        if not row["codes"]:
            try:
                oracle = case["positive_control"]["path"]
                positive = _compare(case, oracle)
                native = native_validate(Path(oracle))
                negative = _compare(case, case["model_path"])
                row.update(positive=positive["status"], native_schema_express=native["passed"] is True,
                           damaged=negative["status"])
                if positive["status"] != "passed":
                    row["codes"].append("POSITIVE_COMPARISON_INVALID")
                    row["codes"].extend(positive["codes"])
                if native["passed"] is not True:
                    row["codes"].append("POSITIVE_NATIVE_INVALID")
                if negative["status"] != "failed":
                    row["codes"].append("DAMAGED_NEGATIVE_INVALID")
                row["passed"] = not row["codes"]
            except Exception:
                row["codes"].append("CONTROL_EVALUATION_ERROR")
        rows.append(row)
    _recheck(record["bindings"])
    return {"schema_version": SCHEMA, "criteria_version": CRITERIA, "evaluator_admitted": all(row["passed"] for row in rows),
            "passed_cases": sum(row["passed"] for row in rows), "total_cases": len(rows), "cases": rows,
            "real_calls": False}


def _summary_digest(summary):
    payload = {key: value for key, value in summary.items() if key != "bindings_sha256"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def _admission(state, record):
    summary = _read(state / "evaluator-summary.json")
    _need(summary.get("bindings_sha256") == sha256(state / "private/evaluator-bindings.json")
          and _summary_digest(summary) == record.get("self_check_sha256"), "EVALUATOR_ADMISSION_CHANGED")
    return summary


def prepare_evaluator(dataset_root: Path, case_ids: list[str], state_dir: Path, *, existing_controls: dict | None = None) -> dict:
    """Freeze expectations and require positive/native/negative controls per case.

    A false ``evaluator_admitted`` or an exception blocks the entire selection.
    Resume verifies every binding before reusing the same-round receipt. A fresh
    round needs its own state_dir; no case is sampled, dropped, or substituted.
    ``existing_controls`` maps case IDs to already frozen {path, sha256} pairs.
    """
    dataset, state = Path(dataset_root).resolve(), Path(state_dir).resolve()
    _need(isinstance(case_ids, list) and bool(case_ids) and len(case_ids) == len(set(case_ids)), "EVALUATOR_SELECTION_INVALID")
    _need(not state.is_relative_to(dataset) and not dataset.is_relative_to(state), "EVALUATOR_STATE_PATH_INVALID")
    binding_path, summary_path = state / "private/evaluator-bindings.json", state / "evaluator-summary.json"
    if binding_path.exists():
        record = _load_record(state)
        _need(record["dataset_root"] == str(dataset) and record["case_ids"] == case_ids, "EVALUATOR_SELECTION_CHANGED")
    else:
        record = _gather(dataset, case_ids, state, existing_controls or {})
        summary = _self_check(record)
        record["self_check_sha256"] = _summary_digest(summary)
        _write_once(binding_path, record)
        summary["bindings_sha256"] = sha256(binding_path)
        _write_once(summary_path, summary)
        return summary
    if summary_path.exists():
        return _admission(state, record)
    # Recover only a receipt publication interrupted after the immutable record.
    summary = _self_check(record)
    _need(_summary_digest(summary) == record.get("self_check_sha256"), "EVALUATOR_ADMISSION_CHANGED")
    summary["bindings_sha256"] = sha256(binding_path)
    _write_once(summary_path, summary)
    return summary


def evaluate_result(state_dir: Path, case_id: str, result_path: Path) -> dict:
    """Independently inspect one frozen submission; return no model/private text."""
    state, result = Path(state_dir).resolve(), Path(result_path).resolve()
    record = _load_record(state)
    admission = _admission(state, record)
    _need(admission.get("evaluator_admitted") is True, "EVALUATOR_SELF_CHECK_REQUIRED")
    _need(case_id in record["case_ids"], "EVALUATOR_CASE_NOT_SELECTED")
    _need(not result.is_relative_to(state / "private") and not result.is_relative_to(Path(record["dataset_root"])),
          "EVALUATOR_ORACLE_IS_NOT_LIVE_OUTPUT")
    before = sha256(result)
    _need(before not in {case["positive_control"]["sha256"] for case in record["cases"]}, "EVALUATOR_ORACLE_IS_NOT_LIVE_OUTPUT")
    case = next(row for row in record["cases"] if row["case_id"] == case_id)
    try:
        checked = _compare(case, result)
        native = native_validate(result)
        checked["native_schema_express"] = native["passed"] is True
        if native["passed"] is not True:
            checked["status"] = "failed"
            checked["codes"].append("NATIVE_SCHEMA_EXPRESS")
    except Exception:
        checked = {"status": "evaluation_error", "codes": ["RESULT_EVALUATION_ERROR"], "native_schema_express": False}
    _need(sha256(result) == before, "EVALUATED_RESULT_CHANGED")
    _recheck(record["bindings"])
    return {"case_id": case_id, **checked, "result_sha256": before, "evaluator_admitted": True,
            "criteria_version": CRITERIA, "bindings_sha256": admission["bindings_sha256"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--dataset", type=Path, required=True)
    prepare.add_argument("--case-id", action="append", required=True)
    prepare.add_argument("--state-dir", type=Path, required=True)
    check = sub.add_parser("check")
    check.add_argument("--state-dir", type=Path, required=True)
    check.add_argument("--case-id", required=True)
    check.add_argument("--result", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            summary = prepare_evaluator(args.dataset, args.case_id, args.state_dir)
            passed = summary["evaluator_admitted"]
        else:
            summary = evaluate_result(args.state_dir, args.case_id, args.result)
            passed = summary["status"] == "passed"
    except EvaluatorError as error:
        summary, passed = {"status": "blocked", "codes": [str(error)]}, False
    except Exception:
        summary, passed = {"status": "blocked", "codes": ["EVALUATOR_ERROR"]}, False
    print(json.dumps(summary, ensure_ascii=False, allow_nan=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
