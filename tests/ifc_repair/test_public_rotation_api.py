"""Original public mixed case through RepairAPI with an explicit offline Provider.

Only the damaged public IFC and unchanged public request are read. This is a
revealed-case regression, not a model localization or capability result.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np
import pytest

from scripts.ifc_repair.repair_comparison.ours_adapter import _draft, _section, fixture_intent
from tests.ifc_repair.test_scene_repair_api import SceneDemoProvider, scene_query_pages
from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI


ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "dataset/processed/ifc-repair/external-20-pilot-40-20261010/sources/reserve-005/cases/case-001-a01/public"
PUBLIC_HASHES = {
    "model.ifc": "910a9473af77af4fd9d387586101d33e78120231cc6a1753561ca2d482022419",
    "request.txt": "05c2ec14bdb0a14089bd9ca3988f8b08f1f134230141b03c1929b9488a58618c",
}


class PublicMixedRotationProvider:
    """Three actual public queries, then hand-authored Intent and native draft."""

    def __init__(self, source, request):
        self.model = ifcopenshell.open(str(source))
        self.scale_mm = ifcopenshell.util.unit.calculate_unit_scale(self.model) * 1000
        self.request = request
        self.names = re.findall(r"(?:宿主墙|现存IfcDoor|现存IfcWindow)「([^」]+)」", request)
        assert len(self.names) == 4
        self.calls = []
        self.public_bindings = None

    def generate_candidate(self, **kwargs):
        self.calls.append(kwargs)
        prompt = kwargs["prompt"]
        if "## Immutable bindings" in prompt:
            value = _draft(prompt, kwargs.get("schema") or _section(prompt, "Draft schema"))
        else:
            value = self._scene_response(scene_query_pages(prompt))
        return ProviderOutput(text=json.dumps(value, ensure_ascii=False), metadata={
            "provider": "fixture", "model": "offline-public-mixed-rotation",
            "evidence_class": "deterministic_fake", "network_transport_attempted": False,
        })

    def _scene_response(self, pages):
        if not pages:
            return {"kind": "query", "query": {
                "ifc_classes": ["IfcWall", "IfcDoor", "IfcWindow"],
                "names": self.names, "detail": "summary"}}
        by_name = {row["name"]: row for row in pages[0]["records"]}
        assert len(by_name) == 4
        door_host, door_ref, window_host, window_ref = [by_name[name] for name in self.names]
        if len(pages) == 1:
            return {"kind": "query", "query": {
                "ifc_classes": ["IfcOpeningElement"], "host_id": door_host["id"],
                "predicates": [{"kind": "empty_opening", "value": True}], "detail": "summary"}}
        assert len(pages[1]["records"]) == 1
        door_opening = pages[1]["records"][0]
        if len(pages) == 2:
            return {"kind": "query", "query": {
                "ids": [row["id"] for page in pages for row in page["records"]],
                "detail": "geometry"}}
        assert len(pages) == 3
        details = {row["id"]: row for row in pages[2]["records"]}
        door_ref, window_ref = details[door_ref["id"]], details[window_ref["id"]]
        opening_bounds = window_ref["opening"]["body_bounds_local_mm"]
        params = {
            "door": {"fit_existing_opening": True, "door": {
                "operation_type": door_ref["type_summary"]["formal_attributes"]["OperationType"],
                "formal_enum_explicit": False}},
            "window": {"opening": {
                "width_mm": opening_bounds["x"][1] - opening_bounds["x"][0],
                "height_mm": opening_bounds["z"][1] - opening_bounds["z"][0],
                "sill_height_mm": 100.0}, "window": {"fit_opening": True}},
        }
        body = None
        operations, bindings = [], []
        for kind, target, reference in [
            ("door", door_opening, door_ref), ("window", window_host, window_ref),
        ]:
            current = fixture_intent(kind, {"allowed_ifc_classes": [
                "IfcOpeningElement" if kind == "door" else "IfcWall"]}, params[kind])
            op = current["operations"][0]
            op["operation_id"] = "offline-public-" + kind
            excerpt = next(line for line in self.request.splitlines()
                           if "补建一扇" + ("门" if kind == "door" else "窗") in line)
            op["provenance"][0]["excerpt"] = excerpt
            op["prototype_intent"] = {"reference_kind": "global_id", "reference": reference["type_id"],
                                      "source": deepcopy(op["provenance"][0])}
            public_reference = self.model.by_guid(reference["id"])
            op["attribute_intents"] = [{"intent_kind": "attribute", "name": name,
                "value": float(getattr(public_reference, name)) * self.scale_mm,
                "source": deepcopy(op["provenance"][0])} for name in ("OverallWidth", "OverallHeight")]
            operations.append(op)
            bindings.append({"operation_id": op["operation_id"], "target_id": target["id"],
                "reference_id": reference["id"], "target_query_id": pages[2]["query_id"],
                "reference_query_id": pages[2]["query_id"]})
            body = current
        body["operations"] = operations
        body["provenance"] = [deepcopy(op["provenance"][0]) for op in operations]
        self.public_bindings = {"door": (door_host["id"], door_ref["id"], door_opening["id"]),
                                "window": (window_host["id"], window_ref["id"], None)}
        return {"kind": "intent", "intent": body, "bindings": bindings}


def _pose_mm(product, scale_mm):
    value = ifcopenshell.util.placement.get_local_placement(product.ObjectPlacement).copy()
    value[:3, 3] *= scale_mm
    return value


def _uncut_local_min_mm(product):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, False)
    settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, True)
    shape = ifcopenshell.geom.create_shape(settings, product)
    return np.asarray(shape.geometry.verts).reshape(-1, 3).min(axis=0) * 1000


@pytest.mark.skipif(not all((PUBLIC / name).is_file() for name in PUBLIC_HASHES),
                   reason="requires the local frozen reserve-005 public IFC/request fixture; not admission when skipped")
def test_original_public_mixed_rotation_api_publishes_exact_public_pose(tmp_path):
    for name, expected in PUBLIC_HASHES.items():
        assert hashlib.sha256((PUBLIC / name).read_bytes()).hexdigest() == expected
    # Exercise a byte-identical public source in the isolated test workspace.
    source = tmp_path / "public.ifc"
    source.write_bytes((PUBLIC / "model.ifc").read_bytes())
    request = (PUBLIC / "request.txt").read_text(encoding="utf-8")
    provider = PublicMixedRotationProvider(source, request)
    api = RepairAPI(tmp_path / "native", provider=provider, scene_grounding=True)
    result = api.start(source, request)
    (tmp_path / "offline-api-result.json").write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    assert hashlib.sha256(source.read_bytes()).hexdigest() == PUBLIC_HASHES["model.ifc"]
    assert hashlib.sha256((PUBLIC / "model.ifc").read_bytes()).hexdigest() == PUBLIC_HASHES["model.ifc"]
    assert result.status == "succeeded", result.to_dict()
    assert result.successful_artifact_publishable
    assert api.read_result(result.run_id).successful_artifact_publishable
    assert len(provider.calls) == 5  # three public queries, Intent, bound draft
    run = api.store.runs_root / result.run_id
    repaired = ifcopenshell.open(str(run / result.artifacts["successful_ifc"]))
    assert repaired.schema == "IFC2X3"
    old_ids = {p.GlobalId for p in provider.model.by_type("IfcProduct")}
    new_products = [p for p in repaired.by_type("IfcProduct") if p.GlobalId not in old_ids]
    assert sorted(p.is_a() for p in new_products) == ["IfcDoor", "IfcOpeningElement", "IfcWindow"]
    for kind, offset in [("door", [100., 0., 0.]), ("window", [3131., 0., 100.])]:
        host_id, reference_id, retained_opening_id = provider.public_bindings[kind]
        host, reference = [provider.model.by_guid(identity) for identity in (host_id, reference_id)]
        product = next(p for p in new_products if p.is_a("IfcDoor" if kind == "door" else "IfcWindow"))
        expected_base = _pose_mm(host, provider.scale_mm) @ [*(_uncut_local_min_mm(host) + offset), 1.]
        reference_pose = _pose_mm(reference, provider.scale_mm)
        actual_pose = _pose_mm(product, provider.scale_mm)
        assert actual_pose[:3, 3] == pytest.approx(expected_base[:3], abs=.001)
        assert actual_pose[:3, :3] == pytest.approx(reference_pose[:3, :3] @ np.diag([-1., -1., 1.]), abs=1e-8)
        assert len(product.FillsVoids) == 1
        opening = product.FillsVoids[0].RelatingOpeningElement
        assert opening.VoidsElements[0].RelatingBuildingElement.GlobalId == host_id
        assert ifcopenshell.util.element.get_container(product).GlobalId == ifcopenshell.util.element.get_container(host).GlobalId
        assert ifcopenshell.util.element.get_type(product).GlobalId == ifcopenshell.util.element.get_type(reference).GlobalId
        if kind == "door":
            assert opening.GlobalId == retained_opening_id
        else:
            original_opening = reference.FillsVoids[0].RelatingOpeningElement
            expected_relative = np.linalg.inv(reference_pose) @ _pose_mm(original_opening, provider.scale_mm)
            actual_relative = np.linalg.inv(actual_pose) @ _pose_mm(opening, provider.scale_mm)
            assert actual_relative == pytest.approx(expected_relative, abs=.001)
    report = json.loads((run / result.artifacts["evaluation"]).read_text(encoding="utf-8"))
    checks = [check for op in report["operations"] for level in op["levels"] for check in level["checks"]]
    public_checks = [check for check in checks if check["check_id"] == "l2.public-request-geometry"]
    assert len(public_checks) == 2 and all(check["status"] == "passed" for check in public_checks)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == PUBLIC_HASHES["model.ifc"]


def test_formal001_original_public_door_request_still_publishes(tmp_path):
    """Adjacent original public door path, fake inference with actual API gates."""
    public = ROOT / "dataset/processed/ifc-repair/repair-comparison/formal/formal-001/public"
    if not all((public / name).is_file() for name in ("model.ifc", "request.txt")):
        pytest.skip("requires the local frozen formal-001 public fixture; not admission when skipped")
    request = (public / "request.txt").read_text(encoding="utf-8")
    source = tmp_path / "public.ifc"
    source.write_bytes((public / "model.ifc").read_bytes())
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    assert before == "ba29acc5355a0039e0e7504f5003abebfcd69fa0fb209dea3a55a2d22e255189"

    class Provider(SceneDemoProvider):
        def __init__(self):
            super().__init__("door")
            self.opening_id = None

        def door(self, pages):
            if not pages:
                return {"kind": "query", "query": {"ifc_classes": ["IfcOpeningElement"],
                    "predicates": [{"kind": "empty_opening", "value": True}],
                    "world_bounds_mm": {"x": [-8376, -8374], "y": [-462, -460], "z": [0, 1]}}}
            assert len(pages[0]["records"]) == 1
            target = pages[0]["records"][0]
            self.opening_id = target["id"]
            if len(pages) == 1:
                return {"kind": "query", "query": {"ifc_classes": ["IfcDoor"],
                    "host_id": target["host_id"],
                    "world_bounds_mm": {"x": [-5376, -5374], "y": [-462, -460]}}}
            assert len(pages[1]["records"]) == 1
            reference = pages[1]["records"][0]
            body = fixture_intent("door", {"allowed_ifc_classes": ["IfcOpeningElement"]},
                {"fit_existing_opening": True, "door": {
                    "operation_type": reference["type_summary"]["formal_attributes"]["OperationType"],
                    "formal_enum_explicit": False}})
            op = body["operations"][0]
            op["provenance"][0]["excerpt"] = request.strip()
            op["prototype_intent"] = {"reference_kind": "global_id", "reference": reference["type_id"],
                                      "source": deepcopy(op["provenance"][0])}
            return {"kind": "intent", "intent": body, "bindings": [{"operation_id": op["operation_id"],
                "target_id": target["id"], "reference_id": reference["id"]}]}

    provider = Provider()
    api = RepairAPI(tmp_path / "native", provider=provider, scene_grounding=True)
    result = api.start(source, request)
    assert result.status == "succeeded", result.to_dict()
    assert api.read_result(result.run_id).successful_artifact_publishable
    repaired = ifcopenshell.open(str(api.store.runs_root / result.run_id / result.artifacts["successful_ifc"]))
    original = ifcopenshell.open(str(source))
    old_ids = {p.GlobalId for p in original.by_type("IfcProduct")}
    added = [p for p in repaired.by_type("IfcProduct") if p.GlobalId not in old_ids]
    assert len(added) == 1 and added[0].is_a("IfcDoor")
    assert added[0].FillsVoids[0].RelatingOpeningElement.GlobalId == provider.opening_id
    scale = ifcopenshell.util.unit.calculate_unit_scale(repaired) * 1000
    assert added[0].OverallWidth * scale == pytest.approx(800, abs=.001)
    assert added[0].OverallHeight * scale == pytest.approx(2075, abs=.001)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    assert hashlib.sha256((public / "model.ifc").read_bytes()).hexdigest() == before
