import json
import importlib.util
from pathlib import Path

from text2ifc_agent.context_selection import select_design_brief_context
from text2ifc_agent.live_pipeline import (
    PROJECT_ROOT,
    compare_design_brief_runs,
    complete_room_case,
    portable_artifact_path,
    run_design_brief_stage,
)
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput


class _RecordingLiveProvider:
    def __init__(self, payload: dict, *, fenced: bool = False) -> None:
        self.payload = payload
        self.fenced = fenced
        self.prompt = ""

    def generate_live(self, *, session_id, prompt, schema, state):
        self.prompt = prompt
        text = json.dumps(self.payload, ensure_ascii=False)
        if self.fenced:
            text = "```json\n" + text + "\n```"
        response = {
            "id": "msg_unit_design_brief_v2",
            "type": "message",
            "role": "assistant",
            "model": "mimo-v2.5-pro",
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": text}],
            "usage": {"input_tokens": 100, "output_tokens": 200},
        }
        return LiveProviderResult(
            session_id=session_id,
            evidence_class="unit_test_fixture",
            http_status=200,
            request={
                "model": "mimo-v2.5-pro",
                "max_tokens": 131072,
                "stream": True,
                "messages": [{"role": "user", "content": prompt}],
            },
            response=response,
            events=(
                {
                    "sequence": 0,
                    "event": "message_start",
                    "data": {"type": "message_start", "message": response},
                },
                {
                    "sequence": 1,
                    "event": "message_stop",
                    "data": {"type": "message_stop"},
                },
            ),
            output=ProviderOutput(
                text=text,
                metadata={"provider": "mimo", "session_id": session_id},
            ),
        )


def test_repository_artifact_paths_are_portable():
    path = PROJECT_ROOT / "dataset" / "processed" / "trace.json"

    assert portable_artifact_path(path) == "dataset/processed/trace.json"


def _valid_ready_brief(case: dict) -> dict:
    selection = select_design_brief_context(
        user_request=case["user_request"],
        conversation=case["conversation"],
    )
    evidence_ids = [item["evidence_id"] for item in selection["evidence"]]
    few_shot_ids = [item["few_shot_id"] for item in selection["few_shots"]]
    return {
        "schema_version": "text2ifc/design-brief/2.0",
        "language": "zh-CN",
        "original_request": case["user_request"],
        "status": "ready",
        "known_facts": {
            "space": {
                "shape": "rectangular",
                "length_mm": 6000,
                "width_mm": 4000,
                "height_mm": 3000,
            },
            "walls": {"count": 4, "enclosure": "closed", "thickness_mm": 300},
            "door": {
                "host": "south_wall",
                "position": "center",
                "width_mm": 900,
                "height_mm": 2100,
            },
            "window": {
                "host": "north_wall",
                "position": "center",
                "width_mm": 1200,
                "height_mm": 1500,
                "sill_height_mm": 900,
            },
        },
        "fact_sources": [
            {
                "path": "/known_facts/space",
                "source_turns": ["turn-user-001"],
                "evidence_refs": ["capability:IFC2X3:IfcSpace"],
            },
            {
                "path": "/known_facts/walls",
                "source_turns": ["turn-user-001", "turn-user-003"],
                "evidence_refs": ["capability:IFC2X3:IfcWall"],
            },
            {
                "path": "/known_facts/door",
                "source_turns": ["turn-user-001"],
                "evidence_refs": ["capability:IFC2X3:IfcDoor"],
            },
            {
                "path": "/known_facts/window",
                "source_turns": ["turn-user-001"],
                "evidence_refs": ["capability:IFC2X3:IfcWindow"],
            },
        ],
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
        "user_corrections": [
            {
                "path": "/known_facts/walls/thickness_mm",
                "value": 300,
                "source_turn": "turn-user-003",
                "evidence_refs": ["schema:bim-json-v2:representation"],
            }
        ],
        "clarification_questions": [],
        "provenance": {
            "source_turns": [
                "turn-user-001",
                "turn-assistant-002",
                "turn-user-003",
            ],
            "selected_evidence_ids": evidence_ids,
            "few_shot_ids": few_shot_ids,
        },
    }


def test_complete_room_case_preserves_real_conversation_without_supervisor_decisions():
    case = complete_room_case()

    assert case["user_request"].startswith("请创建一个单层矩形房间")
    assert case["conversation"][-1] == {
        "turn_id": "turn-user-003",
        "role": "user",
        "content": "厚度为300毫米。",
    }
    serialized = json.dumps(case, ensure_ascii=False)
    assert "supervisor_feedback" not in serialized
    assert "门开启方向" not in serialized
    assert "窗户类型" not in serialized


def test_design_brief_stage_writes_reproducible_unedited_trace(tmp_path: Path):
    case = complete_room_case()
    payload = _valid_ready_brief(case)
    provider = _RecordingLiveProvider(payload)

    result = run_design_brief_stage(
        provider=provider,
        output_dir=tmp_path,
        case=case,
    )

    expected_files = {
        "input.txt",
        "conversation.json",
        "context-selection.json",
        "prompt-render-input.json",
        "prompt-rendered.md",
        "request.redacted.json",
        "response.raw.json",
        "response-metadata.json",
        "events.jsonl",
        "model-text.txt",
        "design-brief.json",
        "validation.json",
        "metrics.json",
        "trace-manifest.json",
    }
    assert expected_files <= {path.name for path in tmp_path.iterdir()}
    assert json.loads((tmp_path / "design-brief.json").read_text(encoding="utf-8")) == payload
    assert (tmp_path / "model-text.txt").read_text(encoding="utf-8") == json.dumps(
        payload, ensure_ascii=False
    )
    validation = json.loads((tmp_path / "validation.json").read_text(encoding="utf-8"))
    assert validation == {"issue_count": 0, "issues": [], "valid": True}
    metrics = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["parse_valid"] is True
    assert metrics["schema_semantic_valid"] is True
    assert metrics["strict_output_contract_valid"] is True
    assert metrics["response_id"] == "msg_unit_design_brief_v2"
    assert metrics["stop_reason"] == "end_turn"
    assert result["status"] == "ready"
    assert "supervisor_feedback" not in provider.prompt
    assert "text2ifc/design-brief/2.0" in provider.prompt
    manifest = json.loads(
        (tmp_path / "trace-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["template_id"] == "design-brief.v2.1"


def test_design_brief_stage_records_invalid_model_output_without_editing_it(tmp_path: Path):
    case = complete_room_case()
    payload = _valid_ready_brief(case)
    payload["schema_version"] = "text2ifc/design-brief/9.9"
    provider = _RecordingLiveProvider(payload)

    result = run_design_brief_stage(
        provider=provider,
        output_dir=tmp_path,
        case=case,
    )

    assert result["status"] == "blocked_prompt_defect"
    assert not (tmp_path / "design-brief.json").exists()
    assert json.loads((tmp_path / "parsed-output.json").read_text(encoding="utf-8")) == payload
    validation = json.loads((tmp_path / "validation.json").read_text(encoding="utf-8"))
    assert validation["valid"] is False
    assert validation["issues"][0]["code"] == "UNSUPPORTED_DESIGN_BRIEF_VERSION"


def test_design_brief_stage_blocks_fenced_live_text_even_when_json_is_valid(
    tmp_path: Path,
):
    case = complete_room_case()
    provider = _RecordingLiveProvider(_valid_ready_brief(case), fenced=True)

    result = run_design_brief_stage(
        provider=provider,
        output_dir=tmp_path,
        case=case,
    )

    assert result["status"] == "blocked_output_contract"
    assert result["valid"] is False
    assert (tmp_path / "design-brief.json").is_file()
    metrics = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["parse_valid"] is True
    assert metrics["schema_semantic_valid"] is True
    assert metrics["strict_output_contract_valid"] is False
    assert metrics["normalization_diagnostics"][0]["code"] == (
        "OUTER_JSON_FENCE_REMOVED"
    )


def test_v1_v2_comparison_is_derived_from_trace_artifacts(tmp_path: Path):
    case = complete_room_case()
    v1_dir = tmp_path / "v1"
    v2_dir = tmp_path / "v2"
    v1_dir.mkdir()
    v1_payload = {
        "schema_version": "text2ifc/design-brief/1.0",
        "language": "zh-CN",
        "original_request": case["user_request"],
        "known_facts": {},
        "missing_facts": [],
        "ambiguities": [],
        "user_corrections": [],
        "clarification_questions": ["墙体厚度是多少？"],
        "provenance": {"source": "user_request"},
    }
    (v1_dir / "model-text.txt").write_text(
        "```json\n" + json.dumps(v1_payload, ensure_ascii=False) + "\n```",
        encoding="utf-8",
    )
    (v1_dir / "response-metadata.json").write_text(
        json.dumps(
            {
                "id": "msg_v1",
                "model": "mimo-v2.5-pro",
                "stop_reason": "end_turn",
            }
        ),
        encoding="utf-8",
    )
    provider = _RecordingLiveProvider(_valid_ready_brief(case))
    run_design_brief_stage(provider=provider, output_dir=v2_dir, case=case)

    comparison = compare_design_brief_runs(
        v1_dir=v1_dir,
        v2_dir=v2_dir,
        output_path=v2_dir / "comparison.json",
    )

    assert comparison["v1"]["response_id"] == "msg_v1"
    assert comparison["v1"]["normalization_codes"] == [
        "OUTER_JSON_FENCE_REMOVED"
    ]
    assert comparison["v1"]["question_count"] == 1
    assert comparison["v2"]["question_count"] == 0
    assert comparison["v2"]["evidence_valid"] is True
    assert comparison["regressions"] == []
    assert comparison["improvements"]
    persisted = json.loads(
        (v2_dir / "comparison.json").read_text(encoding="utf-8")
    )
    assert persisted == comparison


def test_live_cli_runs_design_brief_case_through_injected_provider(
    tmp_path: Path, capsys
):
    script_path = Path("scripts/agent/run_phase6_1_live.py")
    assert script_path.is_file(), "Phase 6.1 live CLI is missing"
    spec = importlib.util.spec_from_file_location("run_phase6_1_live", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    case = complete_room_case()
    provider = _RecordingLiveProvider(_valid_ready_brief(case))

    exit_code = module.main(
        [
            "--stage",
            "design-brief",
            "--case",
            "complete-room",
            "--live",
            "--output-dir",
            str(tmp_path),
        ],
        provider_factory=lambda: provider,
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["status"] == "ready"
    assert output["evidence_class"] == "unit_test_fixture"
    assert (tmp_path / "design-brief.json").is_file()
