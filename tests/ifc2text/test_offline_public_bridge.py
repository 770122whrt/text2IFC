from __future__ import annotations

import copy
import json
from pathlib import Path

from text2ifc_agent.clarification import ClarificationCall
from text2ifc_agent.context_selection import select_design_brief_context
from text2ifc_agent.prompt_registry import load_prompt_registry
from text2ifc_agent.providers import FakeAgentProvider, LiveProviderResult, ProviderOutput
from text2ifc_agent.session_store import SessionStore
from text2ifc_ifc2text.llm_pipeline import run_llm_description
from text2ifc_ifc2text.text2ifc_public import reconstruct_description_with_public_text2ifc


ROOT = Path(__file__).resolve().parents[2]
PHASE6_1_COMPLETE = ROOT / "dataset/processed/agent-demo/phase6.1-mimo-live/complete-room"


class _SequenceLiveProvider:
    def __init__(self, payloads: list[dict]) -> None:
        self.payloads = payloads
        self.session_ids: list[str] = []

    def generate_live(self, *, session_id, prompt, schema, state):
        del prompt, schema, state
        index = len(self.session_ids)
        self.session_ids.append(session_id)
        payload = self.payloads[index]
        text = json.dumps(payload, ensure_ascii=False)
        response = {
            "id": f"ifc2text-bridge-{index + 1}",
            "type": "message",
            "role": "assistant",
            "model": "offline-frozen-provider",
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": text}],
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }
        return LiveProviderResult(
            session_id=session_id,
            evidence_class="offline_frozen_fixture",
            http_status=200,
            request={"model": "offline-frozen-provider"},
            response=response,
            events=(),
            output=ProviderOutput(
                text=text,
                metadata={"provider": "offline-frozen-provider", "session_id": session_id},
            ),
        )


def _room_facts() -> dict:
    walls = []
    wall_specs = [
        ("W001", [0, 0, 0], [6000, 0, 0]),
        ("W002", [6000, 0, 0], [6000, 4000, 0]),
        ("W003", [6000, 4000, 0], [0, 4000, 0]),
        ("W004", [0, 4000, 0], [0, 0, 0]),
    ]
    for label, start, end in wall_specs:
        walls.append(
            {
                "label": label,
                "source_global_id": f"source-{label}",
                "name": label,
                "ifc_class": "IfcWall",
                "storey": "S01",
                "axis_start_mm": start,
                "axis_end_mm": end,
                "length_mm": 6000 if start[1] == end[1] else 4000,
                "thickness_mm": 300,
                "height_mm": 3000,
                "measurement_status": "measured",
                "spaces": ["R001"],
                "openings": [],
            }
        )
    return {
        "source": {"path": "not-for-prompt.ifc", "sha256": "sha256:private", "ifc_schema": "IFC2X3", "size_bytes": 1},
        "units": {"length": "millimetre", "area": "square_metre"},
        "coordinate_system": {"frame": "ifc_world", "axis_convention": "no inferred north"},
        "building": {"project_name": "Bridge", "building_name": "Room", "storey_count": 1},
        "capability": {
            "explicit_space_count": 1,
            "derived_space_count": 0,
            "wall_count": 4,
            "door_count": 1,
            "window_count": 1,
            "opening_count": 0,
            "measurement_issue_count": 0,
        },
        "storeys": [
            {
                "label": "S01",
                "source_global_id": "source-storey",
                "name": "一层",
                "elevation_mm": 0,
                "spaces": [
                    {
                        "label": "R001",
                        "source_global_id": "source-space",
                        "name": "房间",
                        "storey": "S01",
                        "source_kind": "ifc_space",
                        "bounds_mm": {"x": [0, 6000], "y": [0, 4000], "z": [0, 3000]},
                        "size_mm": {"x": 6000, "y": 4000, "z": 3000},
                        "boundary_walls": ["W001", "W002", "W003", "W004"],
                    }
                ],
                "derived_spaces": [],
                "walls": walls,
                "openings": [],
                "doors": [
                    {
                        "label": "D001",
                        "source_global_id": "source-door",
                        "name": "门",
                        "ifc_class": "IfcDoor",
                        "storey": "S01",
                        "host_wall": "W001",
                        "overall_width_mm": 900,
                        "overall_height_mm": 2100,
                        "host_position_mm": {"center_offset_mm": 3000, "sill_height_mm": 0, "normal_offset_mm": 0},
                        "measurement_status": "measured",
                    }
                ],
                "windows": [
                    {
                        "label": "N001",
                        "source_global_id": "source-window",
                        "name": "窗",
                        "ifc_class": "IfcWindow",
                        "storey": "S01",
                        "host_wall": "W003",
                        "overall_width_mm": 1200,
                        "overall_height_mm": 1500,
                        "host_position_mm": {"center_offset_mm": 3000, "sill_height_mm": 900, "normal_offset_mm": 0},
                        "measurement_status": "measured",
                    }
                ],
                "stairs": [],
            }
        ],
        "unassigned": {"walls": [], "openings": [], "doors": [], "windows": [], "spaces": [], "stairs": []},
        "issues": [],
    }


def _writing_responses(run_id: str) -> dict[str, dict]:
    refs = ["S01:R001", "S01:W001", "S01:W002", "S01:W003", "S01:W004", "S01:D001", "S01:N001"]
    outline = {
        "schema_version": "text2ifc/ifc2text-outline/0.1",
        "structure": "total-part-total",
        "sections": [
            {
                "section_id": "opening",
                "kind": "opening_overview",
                "title": "整体概况",
                "storey": None,
                "allowed_fact_refs": ["building", "S01"],
                "required_fact_refs": ["building", "S01"],
                "primary_owned_fact_refs": ["building", "S01"],
                "required_limitations": [],
            },
            {
                "section_id": "room",
                "kind": "spaces",
                "title": "一层房间与构件",
                "storey": "S01",
                "allowed_fact_refs": refs,
                "required_fact_refs": refs,
                "primary_owned_fact_refs": refs,
                "required_limitations": [],
            },
            {
                "section_id": "closing",
                "kind": "closing_summary",
                "title": "总结",
                "storey": None,
                "allowed_fact_refs": ["building"],
                "required_fact_refs": [],
                "primary_owned_fact_refs": [],
                "required_limitations": [],
            },
        ],
        "unresolved_fact_refs": [],
    }
    request = (
        "请创建一个单层矩形房间，长6米、宽4米、高3米；四面墙闭合，墙厚300毫米；"
        "南侧墙中央设置一扇宽0.9米、高2.1米的门，北侧墙中央设置一扇宽1.2米、"
        "高1.5米、窗台高0.9米的窗。"
    )
    section_payloads = {
        "opening": ("这是一个单层矩形房间，采用统一建筑坐标进行定位。", ["building", "S01"]),
        "room": (request, refs),
        "closing": ("以上说明覆盖房间、四面围护墙以及一门一窗的主要重建事实。", ["building"]),
    }
    responses: dict[str, dict] = {
        f"{run_id}:outline": {"text": json.dumps(outline, ensure_ascii=False)},
    }
    for section_id, (text, used) in section_payloads.items():
        responses[f"{run_id}:section:{section_id}"] = {
            "text": json.dumps(
                {
                    "schema_version": "text2ifc/ifc2text-section/0.1",
                    "section_id": section_id,
                    "text": text,
                    "used_fact_refs": used,
                    "omitted_required_fact_refs": [],
                    "unresolved_fact_refs": [],
                },
                ensure_ascii=False,
            )
        }
    responses[f"{run_id}:merge"] = {
        "text": json.dumps(
            {
                "schema_version": "text2ifc/ifc2text-merge/0.1",
                "section_order": ["opening", "room", "closing"],
                "transition_text": [],
                "limitations": [],
                "blocked_sections": [],
            },
            ensure_ascii=False,
        )
    }
    return responses


def _design_brief_invoker(store: SessionStore):
    frozen = json.loads((PHASE6_1_COMPLETE / "design-brief" / "design-brief.json").read_text(encoding="utf-8"))
    registry = load_prompt_registry()
    template = registry["design-brief.v2.25"]

    def invoke(transcript: list[dict], call_index: int) -> ClarificationCall:
        session = store.list_sessions()[-1]
        request = transcript[0]["content"]
        selection = select_design_brief_context(user_request=request, conversation=transcript)
        brief = copy.deepcopy(frozen)
        brief["original_request"] = request
        brief["fact_sources"][0]["source_turns"] = ["turn-user-001"]
        brief["provenance"]["source_turns"] = ["turn-user-001"]
        brief["provenance"]["few_shot_ids"] = []
        brief["provenance"]["selected_evidence_ids"] = brief["fact_sources"][0]["evidence_refs"]
        call_dir = session.run_dir / "calls" / f"{call_index:02d}-design-brief"
        call_dir.mkdir(parents=True, exist_ok=True)
        (call_dir / "conversation.json").write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
        (call_dir / "context-selection.json").write_text(json.dumps(selection, ensure_ascii=False, indent=2), encoding="utf-8")
        (call_dir / "design-brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
        (call_dir / "prompt-rendered.md").write_text("offline deterministic Design Brief fixture\n", encoding="utf-8")
        (call_dir / "request.redacted.json").write_text(
            json.dumps({"mode": "offline_fixture", "request_length": len(request)}), encoding="utf-8"
        )
        (call_dir / "response.raw.json").write_text(
            json.dumps(
                {
                    "id": f"offline-brief-{call_index}",
                    "mode": "offline_fixture",
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                }
            ),
            encoding="utf-8",
        )
        (call_dir / "model-text.txt").write_text(json.dumps(brief, ensure_ascii=False), encoding="utf-8")
        (call_dir / "validation.json").write_text(
            json.dumps({"valid": True, "issue_count": 0, "issues": []}), encoding="utf-8"
        )
        (call_dir / "metrics.json").write_text(
            json.dumps(
                {
                    "prompt_template_id": template["template_id"],
                    "prompt_template_hash": template["sha256"],
                    "schema_semantic_valid": True,
                    "evidence_class": "offline_frozen_fixture",
                }
            ),
            encoding="utf-8",
        )
        return ClarificationCall(
            call_index=call_index,
            response_id=f"offline-brief-{call_index}",
            prompt_template_id=template["template_id"],
            prompt_template_hash=template["sha256"],
            artifact_dir=str(call_dir),
            brief=brief,
            evidence_catalog=selection["evidence"],
        )

    return invoke


def test_fake_ifc2text_text_enters_real_public_generation_path_and_compiles(tmp_path: Path) -> None:
    writing_run_id = "offline-public-bridge"
    writing = run_llm_description(
        facts=_room_facts(),
        output_dir=tmp_path / "writing",
        provider=FakeAgentProvider(_writing_responses(writing_run_id)),
        run_id=writing_run_id,
    )
    description = Path(writing["description_path"]).read_text(encoding="utf-8")
    assert "长6米、宽4米、高3米" in description

    candidate = json.loads((PHASE6_1_COMPLETE / "generator" / "candidate.json").read_text(encoding="utf-8"))
    audit = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "accept",
        "blocking": False,
        "deterministic_gate_status": "passed",
        "findings": [],
        "evidence_paths": ["design-brief/design-brief.json", "generator/candidate.json"],
    }
    generation_provider = _SequenceLiveProvider([candidate, audit])
    root = tmp_path / "generation"
    with SessionStore.open(root / "sessions.sqlite", artifact_root=root) as store:
        result = reconstruct_description_with_public_text2ifc(
            description,
            store=store,
            invoke_design_brief=_design_brief_invoker(store),
            provider_factory=lambda: generation_provider,
        )
        assert result["status"] == "compiled"
        assert result["ifc_path"] is not None
        assert Path(result["ifc_path"]).is_file()
        session = store.get_session(result["session_id"])
        assert session.original_input == description
        assert (root / "final-acceptance.json").is_file()
        assert generation_provider.session_ids == [
            f"phase6.2-{session.session_hash}-generator-01",
            f"phase6.2-{session.session_hash}-audit-01",
        ]
