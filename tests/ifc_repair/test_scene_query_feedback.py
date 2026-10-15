"""Frozen offline family for actionable, public-only query failure feedback.

The real seed supplied only diagnostic codes/paths. These synthetic siblings
test error propagation, not model reliability or the seed case's repair answer.
The translated/reidentified scene is reserved until after the first fix.
"""
from copy import deepcopy
import hashlib
import json

import pytest

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.scene_context import PublicScene, SceneError
from tests.ifc_repair.test_scene_context import fixture_scene
from tests.ifc_repair.test_scene_grounding import QueueProvider, run
from tests.ifc_repair.test_scene_grounding_feedback import read_round
from tests.ifc_repair.test_scene_repair_api import (
    DEVELOPMENT, SelectedNeighboursProvider, scene_query_pages,
)
from tests.ifc_repair.test_spatial_grounding import body
from scripts.ifc_repair.repair_comparison.ours_adapter import _draft, _section


def selection(rank):
    return {"order_by": "world_y", "descending": False, "ranks": [rank]}


def sibling_scene(holdout=False):
    original = fixture_scene()
    if not holdout:
        return original
    records = deepcopy(original.records)
    for record in records:
        record["id"] = "translated-" + record["id"]
        if record.get("host_id"):
            record["host_id"] = "translated-" + record["host_id"]
        record["center_world_mm"][1] += 23000
        record["bounds_world_mm"]["y"] = [v + 23000 for v in record["bounds_world_mm"]["y"]]
        if record.get("wall_axis"):
            record["wall_axis"]["start_world_mm"][1] += 23000
    return PublicScene(records, original.storeys, project_unit_scale=.001)


@pytest.mark.parametrize("holdout", [False, True], ids=["development", "holdout"])
@pytest.mark.parametrize("empty,count,rank", [(True, 0, 1), (False, 4, 5)])
def test_rank_failure_reaches_retry_with_exact_path_and_public_cohort_count(tmp_path, holdout, empty, count, rank):
    scene = sibling_scene(holdout)
    query = {"ifc_classes": ["IfcDoor" if empty else "IfcWindow"], "select": selection(rank)}
    response = {"kind": "query", "query": query}
    result = run(tmp_path, QueueProvider([response, response]), scene=scene, max_rounds=2)
    issue = read_round(tmp_path, 2)["VALIDATION_FEEDBACK"][0]
    assert issue["code"] == "SCENE_SELECTION_RANK_INVALID"
    assert issue["path"] == "/query/select/ranks/0"
    assert f"{count} records" in issue["message"]
    assert "without select" in issue["message"]
    assert "Do not substitute" in issue["message"]
    assert len(issue["message"]) <= 500
    assert not scene.offered_ids - {"level"}
    assert scene.pages == []
    assert not result["valid"] and result["intent"] is None
    assert result["scene_diagnostics"]["rounds"][0]["issue_paths"] == ["/query/select/ranks/0"]
    assert not any(record["id"] in issue["message"] for record in scene.records)


def test_valid_last_rank_still_has_complete_selection_evidence():
    scene = fixture_scene()
    page = scene.query({"ifc_classes": ["IfcWindow"], "select": selection(4)})
    assert page["selection_complete"] and page["total_matches"] == 4
    assert page["selection"]["selected_ids"] == ["window-0"]


def test_unknown_geometry_still_precedes_out_of_range_rank_and_offers_no_identity(tmp_path):
    scene = fixture_scene()
    records = deepcopy(scene.records)
    records[-1].update(center_world_mm=None, bounds_world_mm=None, geometry_status="unavailable")
    scene = PublicScene(records, scene.storeys, project_unit_scale=.001)
    response = {"kind": "query", "query": {"ifc_classes": ["IfcWindow"], "select": selection(5)}}
    result = run(tmp_path, QueueProvider([response]), scene=scene, max_rounds=1)
    assert result["attempts"][0]["issues"][0]["code"] == "SCENE_SELECTION_INCOMPLETE"
    assert scene.pages == [] and scene.offered_ids == {"level"}


@pytest.mark.parametrize("role", ["target", "reference"])
def test_wrong_query_membership_reports_specific_binding_field_without_suggesting_identity(tmp_path, role):
    bind = {"operation_id": "offline-repair", "target_id": "wall"}
    if role == "reference":
        bind.update(reference_id="window-0", reference_query_id="q1")
    else:
        bind["target_query_id"] = "q2"
    response = {"kind": "intent", "intent": body(), "bindings": [bind]}
    result = run(tmp_path, QueueProvider([
        {"kind": "query", "query": {"ids": ["wall"]}},
        {"kind": "query", "query": {"ids": ["window-0"]}}, response, response]), max_rounds=4)
    issue = read_round(tmp_path, 4)["VALIDATION_FEEDBACK"][0]
    assert issue["code"] == "SCENE_QUERY_BINDING_INCOMPLETE"
    assert issue["path"] == f"/bindings/0/{role}_query_id"
    assert "not returned by the cited query" in issue["message"]
    assert "wall" not in issue["message"] and "window-0" not in issue["message"]
    assert not result["valid"] and not (tmp_path / "repair-intent.json").exists()


def test_mixed_operation_feedback_uses_binding_array_index_not_operation_order(tmp_path):
    document = body()
    second = deepcopy(document["operations"][0])
    second["operation_id"] = "second-operation"
    document["operations"].append(second)
    response = {"kind": "intent", "intent": document, "bindings": [
        {"operation_id": "second-operation", "target_id": "wall", "target_query_id": "q1"},
        {"operation_id": "offline-repair", "target_id": "wall", "target_query_id": "q2"},
    ]}
    result = run(tmp_path, QueueProvider([
        {"kind": "query", "query": {"ids": ["wall"]}},
        {"kind": "query", "query": {"ids": ["window-0"]}}, response]), max_rounds=3)
    assert result["attempts"][-1]["issues"][0]["path"] == "/bindings/1/target_query_id"
    assert not result["valid"] and document["operations"][0] == body()["operations"][0]


@pytest.mark.parametrize("reason", ["coverage", "geometry", "unoffered", "unknown_query"])
def test_query_binding_failure_reasons_remain_distinct_and_do_not_disclose_candidates(reason):
    scene = fixture_scene()
    if reason == "geometry":
        scene.records[-1].update(center_world_mm=None, bounds_world_mm=None, geometry_status="unavailable")
        page = scene.query({"ifc_classes": ["IfcWindow"], "world_bounds_mm": {"y": [0, 10000]}})
        identity, expected = "window-0", "unavailable geometry"
    elif reason == "coverage":
        page = scene.query({"ifc_classes": ["IfcWindow"], "limit": 1})
        identity, expected = page["records"][0]["id"], "complete cohort"
    else:
        page = scene.query({"ids": ["wall"]})
        identity, expected = ("never-offered" if reason == "unoffered" else "wall"), "returned query"
    with pytest.raises(SceneError) as caught:
        scene.verify_query_binding("q999" if reason == "unknown_query" else page["query_id"], identity)
    assert expected in str(caught.value)
    assert not any(record["id"] in str(caught.value) for record in scene.records)
    assert "never-offered" not in str(caught.value)


class RetryQueryProvider(SelectedNeighboursProvider):
    """Purposeful protocol failures, then reuse of actually returned query IDs."""
    def generate_candidate(self, **kw):
        self.calls.append(kw)
        prompt = kw["prompt"]
        if "## Immutable bindings" in prompt:
            value = _draft(prompt, kw.get("schema") or _section(prompt, "Draft schema"))
        else:
            round_number = sum(c["state"]["stage"] == "ifc_repair_scene_grounding" for c in self.calls)
            pages = scene_query_pages(prompt)
            if round_number == 1:
                value = {"kind": "query", "query": {"ifc_classes": ["IfcWindow"],
                    "names": ["synthetic-nonexistent-label"], "select": selection(2)}}
            else:
                if round_number == 2:
                    issue = _section(prompt, "Validation feedback")[0]
                    assert issue["path"] == "/query/select/ranks/0"
                    assert "0 records" in issue["message"]
                value = self.window(pages)
                if value["kind"] == "intent":
                    value["bindings"][0]["target_query_id"] = pages[0]["query_id"]
                    value["bindings"][0]["reference_query_id"] = pages[0 if round_number == 4 else 1]["query_id"]
                if round_number == 5:
                    issue = _section(prompt, "Validation feedback")[0]
                    assert issue["path"] == "/bindings/0/reference_query_id"
                    assert "not returned by the cited query" in issue["message"]
        return ProviderOutput(text=json.dumps(value, ensure_ascii=False), metadata={
            "provider": "fixture", "model": "offline-query-feedback", "evidence_class": "deterministic_replay",
            "usage": {"input_tokens": 11, "output_tokens": 7}})


def test_public_api_retries_failed_query_and_wrong_binding_then_publishes_verified_artifact(tmp_path):
    import ifcopenshell

    public = DEVELOPMENT / "case-001/public"
    source = tmp_path / "public.ifc"
    source.write_bytes((public / "model.ifc").read_bytes())
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    provider = RetryQueryProvider()
    result = RepairAPI(tmp_path, provider=provider, scene_grounding=True).start(
        source, (public / "request.txt").read_text(encoding="utf-8"))
    assert result.status == "succeeded" and result.successful_artifact_publishable, result.to_dict()
    assert len(provider.calls) == 6
    run_dir = tmp_path / result.run_directory
    evidence = json.loads((run_dir / "intent/grounding-evidence.json").read_text(encoding="utf-8"))
    assert evidence["derivations"][0]["target_query_id"] == "q1"
    assert evidence["derivations"][0]["reference_query_id"] == "q2"
    assert evidence["derivations"][0]["center_offset_mm"] == pytest.approx(12227.5, abs=.01)
    diagnostics = json.loads((run_dir / "intent/scene-diagnostics.json").read_text(encoding="utf-8"))
    assert [r["outcome"] for r in diagnostics["rounds"]] == ["invalid", "valid", "valid", "invalid", "valid"]
    source_model = ifcopenshell.open(str(source))
    source_ids = {p.GlobalId for p in source_model.by_type("IfcProduct")}
    repaired = ifcopenshell.open(str(run_dir / result.artifacts["successful_ifc"]))
    added = [w for w in repaired.by_type("IfcWindow") if w.GlobalId not in source_ids]
    assert repaired.schema == "IFC2X3" and len(added) == 1 and added[0].FillsVoids
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
