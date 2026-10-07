"""Actual public API chain with keyless Provider fixtures, development D only."""
import hashlib
import json
from pathlib import Path

import pytest

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI
from scripts.ifc_repair.repair_comparison.ours_adapter import _draft, _section, fixture_intent

ROOT = Path(__file__).resolve().parents[2]
DEVELOPMENT = ROOT / "dataset/processed/ifc-repair/repair-comparison/development"


class SceneDemoProvider:
    """Frozen deterministic search fixture, not a model localization score."""
    def __init__(self, kind, *, ask_first=False, mixed_queries=False):
        self.kind, self.ask_first, self.mixed_queries = kind, ask_first, mixed_queries
        self.calls = []

    def generate_candidate(self, **kw):
        self.calls.append(kw)
        prompt = kw["prompt"]
        if "## Immutable bindings" in prompt:
            value = _draft(prompt, kw.get("schema") or _section(prompt, "Draft schema"))
        else:
            pages = _section(prompt, "Read-only query results so far")
            if self.kind == "door":
                value = self.door(pages)
            else:
                value = self.window(pages)
        return ProviderOutput(text=json.dumps(value, ensure_ascii=False), metadata={
            "provider": "fixture", "model": "offline-scene-fixture", "evidence_class": "deterministic_replay",
            "usage": {"input_tokens": 11, "output_tokens": 7}})

    def door(self, pages):
        if not pages:
            return {"kind": "query", "query": {"ifc_classes": ["IfcOpeningElement"],
                     "world_bounds_mm": {"x": [1914, 1916], "y": [-6189, -6187], "z": [3099, 3101]}}}
        target = next(r for r in pages[0]["records"] if not r["filling_ids"])
        if len(pages) == 1:
            return {"kind": "query", "query": {"ifc_classes": ["IfcDoor"],
                     "world_bounds_mm": {"x": [6888, 6890], "y": [-11613, -11611], "z": [3100, 5500]}}}
        reference = pages[1]["records"][0]
        operation_type = reference["type_summary"]["formal_attributes"]["OperationType"]
        body = fixture_intent("door", {"allowed_ifc_classes": ["IfcOpeningElement"], "global_id": target["id"]},
                 {"fit_existing_opening": True, "door": {"operation_type": operation_type, "formal_enum_explicit": False}})
        _reuse_type(body, reference)
        return {"kind": "intent", "intent": body, "bindings": [{"operation_id": "offline-repair",
                  "target_id": target["id"], "target_point_world_mm": [1915, -6188, 3100],
                  "reference_id": reference["id"], "reference_point_world_mm": [6889,-11612,3100]}]}

    def window(self, pages):
        if not pages:
            return {"kind": "query", "query": {"ifc_classes": ["IfcWall"],
                  "world_bounds_mm": {"x": [-14800, -14550], "z": [0, 1]}, "limit": 80}}
        if len(pages) == 1:
            walls = [r for r in pages[0]["records"] if r.get("wall_axis") and r["wall_axis"]["length_mm"] > 10000]
            host = min(walls, key=lambda r: r["center_world_mm"][0])
            query = {"ifc_classes": ["IfcWindow"], "host_id": host["id"],
                     "order_by": "world_y", "descending": True}
            if self.mixed_queries:
                query.update(ifc_classes=['IfcWindow', 'IfcOpeningElement'],
                             storey_id=host['storey_id'], order_by='id', descending=False)
            return {"kind": "query", "query": query}
        windows = sorted([r for r in pages[1]["records"] if r['ifc_class']=='IfcWindow'],
                         key=lambda r:r['center_world_mm'][1], reverse=True)
        target_id = pages[1]["query"]["host_id"]
        body = fixture_intent("window", {"allowed_ifc_classes": ["IfcWall"]},
                   {"opening": {"width_mm": 915., "height_mm": 1830., "sill_height_mm": 305.}, "window": {"fit_opening": True}})
        if self.ask_first and len([c for c in self.calls if c['state']['stage']=='ifc_repair_scene_grounding']) <= 3:
            body["operations"][0]["target_query"]["global_id"] = target_id
            body["operations"][0]["parameters"]["opening"].pop("width_mm")
            return {"kind": "clarification", "intent": body, "reason": "missing_user_fact",
                    "question": "要补的窗宽度是多少毫米？", "candidate_ids": []}
        reference = windows[1]
        _reuse_type(body, reference)
        return {"kind": "intent", "intent": body, "bindings": [{"operation_id": "offline-repair", "target_id": target_id,
                    "reference_id": reference["id"],
                    "position": {"kind": "between_ranked", "ifc_class": "IfcWindow", "order_by": "world_y",
                                 "descending": True, "ranks": [2,3], "reference_ids": [r["id"] for r in windows[1:3]]}}]}


def _reuse_type(body, reference):
    body["operations"][0]["prototype_intent"] = {"reference_kind": "global_id", "reference": reference["type_id"],
        "source": body["operations"][0]["provenance"][0]}


@pytest.mark.parametrize("case,kind,mixed_queries", [("case-001", "window", False),
    ("case-002", "door", False), ("case-001", "window", True)])
def test_scene_mode_public_demo_complete_chain_no_identity_in_request(tmp_path, case, kind, mixed_queries):
    public = DEVELOPMENT / case / "public"
    source = public / "model.ifc"
    request = (public / "request.txt").read_text(encoding="utf-8")
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    provider = SceneDemoProvider(kind, mixed_queries=mixed_queries)
    api = RepairAPI(tmp_path / "native", provider=provider, scene_grounding=True)
    result = api.start(source, request)
    assert result.status == "succeeded", result.to_dict()
    assert result.successful_artifact_publishable
    assert len(provider.calls) == 4  # no extra lookup or model correction for mixed-query coverage
    run = tmp_path / "native" / result.run_directory
    repaired = run / result.artifacts["successful_ifc"]
    import ifcopenshell
    result_model = ifcopenshell.open(str(repaired))
    assert result_model.schema == "IFC2X3"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    evidence = json.loads((run / "intent/grounding-evidence.json").read_text(encoding="utf-8"))
    if kind == "window":
        assert abs(evidence["derivations"][0]["center_offset_mm"]-12227.5) < .01
    reference_id = evidence["derivations"][0]["reference_occurrence_id"]
    source_model = ifcopenshell.open(str(source))
    before_ids = {p.GlobalId for p in source_model.by_type("IfcProduct")}
    new_occurrences = [p for p in result_model.by_type("IfcWindow" if kind=="window" else "IfcDoor") if p.GlobalId not in before_ids]
    assert len(new_occurrences) == 1
    reference = source_model.by_guid(reference_id)
    ref_type = reference.IsDefinedBy[0].RelatingType if reference.IsDefinedBy[0].is_a('IfcRelDefinesByType') else next(r.RelatingType for r in reference.IsDefinedBy if r.is_a('IfcRelDefinesByType'))
    new_type = next(r.RelatingType for r in new_occurrences[0].IsDefinedBy if r.is_a('IfcRelDefinesByType'))
    assert new_type.GlobalId == ref_type.GlobalId
    assert new_type.RepresentationMaps
    assert any(r.RepresentationType=="MappedRepresentation" for r in new_occurrences[0].Representation.Representations)
    from scripts.ifc_repair.repair_comparison.scoring import _appearance
    assert _appearance(new_occurrences[0],reference,kind) is True
    assert "Level 1" in provider.calls[0]["prompt"]
    assert all("private" not in str(c["state"]) for c in provider.calls)


def test_scene_clarification_resume_persists_mode_across_api_restart(tmp_path):
    source = DEVELOPMENT / "case-001/public/model.ifc"
    provider = SceneDemoProvider("window", ask_first=True)
    api = RepairAPI(tmp_path, provider=provider, scene_grounding=True)
    waiting = api.start(source, "一层西侧长墙第二与第三扇窗中间补窗，高1830毫米，窗台305毫米。")
    assert waiting.status == "clarification_required", waiting.to_dict()
    assert "宽度" in waiting.clarification.question
    restarted = RepairAPI(tmp_path, provider=provider)  # method comes from saved task, not today's default
    result = restarted.continue_with_answer(waiting.run_id, {"kind": "add_detail", "detail": "宽915毫米。"},
                clarification_id=waiting.clarification.clarification_id, expected_state_version=waiting.state_version)
    assert result.run_id == waiting.run_id and result.status == "succeeded", result.to_dict()
    assert result.state_version > waiting.state_version
    assert all(c["state"]["stage"] != "ifc_repair_intent" for c in provider.calls)


@pytest.mark.parametrize('mode',['truncated','unoffered'])
def test_scene_api_invalid_model_output_cannot_publish_or_touch_source(tmp_path,mode):
    from tests.ifc_repair.test_scene_grounding import body, QueueProvider
    source=DEVELOPMENT/'case-002/public/model.ifc'
    before=source.read_bytes()
    value='{"kind":' if mode=='truncated' else {'kind':'intent','intent':body(),
                'bindings':[{'operation_id':'offline-repair','target_id':'deleted-private-target'}]}
    provider=QueueProvider([value]*8)
    api=RepairAPI(tmp_path,provider=provider,scene_grounding=True)
    result=api.start(source,'请修复损坏的门。')
    assert result.status=='provider_failed' and not result.successful_artifact_publishable
    assert 'successful_ifc' not in result.artifacts and result.clarification is None
    assert len(provider.calls)==8 and source.read_bytes()==before
    assert not list((tmp_path/result.run_directory).rglob('successful/repaired.ifc'))


def test_scene_application_write_failure_is_atomic_and_source_is_immutable(tmp_path,monkeypatch):
    import ifcopenshell
    source=DEVELOPMENT/'case-002/public/model.ifc'
    before=source.read_bytes()
    write=ifcopenshell.file.write
    injected=[]
    def fail(model,path,*args,**kwargs):
        value=write(model,path,*args,**kwargs)
        if 'application-candidate.ifc-' in str(path):
            injected.append(str(path))
            raise OSError('offline injected candidate write failure')
        return value
    monkeypatch.setattr(ifcopenshell.file,'write',fail)
    result=RepairAPI(tmp_path,provider=SceneDemoProvider('door'),scene_grounding=True).start(source,'在二层空洞补门。')
    assert injected and not result.successful_artifact_publishable
    assert 'successful_ifc' not in result.artifacts
    assert source.read_bytes()==before and all(not Path(p).exists() for p in injected)
