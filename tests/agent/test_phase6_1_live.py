import json
import importlib.util
from pathlib import Path

from text2ifc_agent.context_selection import select_design_brief_context
from text2ifc_agent.live_pipeline import (
    PROJECT_ROOT,
    compare_design_brief_runs,
    complete_room_case,
    clarified_room_case,
    portable_artifact_path,
    run_clarification_case,
    run_design_brief_stage,
    run_generator_stage,
    run_repair_stage,
    run_audit_report_stage,
    run_final_acceptance_stage,
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


class _SequenceLiveProvider:
    def __init__(self, payloads: list[dict]) -> None:
        self.payloads = payloads
        self.prompts = []
        self.session_ids = []

    def generate_live(self, *, session_id, prompt, schema, state):
        index = len(self.prompts)
        self.prompts.append(prompt)
        self.session_ids.append(session_id)
        return _RecordingLiveProvider(self.payloads[index]).generate_live(
            session_id=session_id,
            prompt=prompt,
            schema=schema,
            state=state,
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


def test_live_clarification_run_preserves_two_provider_calls_and_all_turns(
    tmp_path: Path,
):
    case = clarified_room_case()
    first = _valid_ready_brief(complete_room_case())
    first["original_request"] = case["user_request"]
    first["status"] = "needs_clarification"
    first["known_facts"]["walls"].pop("thickness_mm")
    first["user_corrections"] = []
    first["missing_facts"] = [
        {
            "id": "mf-wall-thickness",
            "code": "WALL_THICKNESS_MISSING",
            "path": "/known_facts/walls/thickness_mm",
            "message": "墙体厚度尚未提供。",
            "reason": "生成用户要求的实体墙体需要明确厚度。",
            "blocking": True,
            "evidence_refs": ["schema:bim-json-v2:representation"],
            "source_turns": ["turn-user-001"],
        }
    ]
    first["clarification_questions"] = [
        {
            "id": "q-wall-thickness",
            "text": "请问墙体厚度是多少毫米？",
            "targets": ["mf-wall-thickness"],
            "reason": "缺少厚度时不能生成所要求的实体墙体。",
            "evidence_refs": ["schema:bim-json-v2:representation"],
        }
    ]
    for fact_source in first["fact_sources"]:
        fact_source["source_turns"] = ["turn-user-001"]
    first["provenance"]["source_turns"] = ["turn-user-001"]
    second = json.loads(json.dumps(first, ensure_ascii=False))
    second["status"] = "ready"
    second["known_facts"]["walls"]["thickness_mm"] = 300
    second["missing_facts"] = []
    second["clarification_questions"] = []
    for fact_source in second["fact_sources"]:
        fact_source["source_turns"] = ["turn-user-001"]
        if fact_source["path"] == "/known_facts/walls":
            fact_source["source_turns"].append("turn-user-003")
    second["provenance"]["source_turns"] = [
        "turn-user-001",
        "turn-user-003",
    ]
    provider = _SequenceLiveProvider([first, second])

    result = run_clarification_case(
        provider=provider,
        output_dir=tmp_path,
        case=case,
        answers=["墙体厚度为300毫米。"],
    )

    assert result["status"] == "ready"
    assert result["valid"] is True
    assert result["live_call_count"] == 2
    assert provider.session_ids == [
        "phase6.1-clarified-room-design-brief-01",
        "phase6.1-clarified-room-design-brief-02",
    ]
    assert "请问墙体厚度是多少毫米？" in provider.prompts[1]
    assert "墙体厚度为300毫米。" in provider.prompts[1]
    conversation = json.loads(
        (tmp_path / "conversation.json").read_text(encoding="utf-8")
    )
    assert [turn["role"] for turn in conversation] == [
        "user",
        "assistant",
        "user",
    ]
    assert conversation[-1]["content"] == "墙体厚度为300毫米。"
    assert json.loads(
        (tmp_path / "design-brief.json").read_text(encoding="utf-8")
    ) == second
    metrics = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["response_ids"] == [
        "msg_unit_design_brief_v2",
        "msg_unit_design_brief_v2",
    ]
    assert metrics["answer_turn_count"] == 1
    assert metrics["all_strict_output_contract_valid"] is True
    assert (tmp_path / "calls/01-design-brief/response.raw.json").is_file()
    assert (tmp_path / "calls/02-design-brief/response.raw.json").is_file()


def test_live_clarification_cli_consumes_answer_file_with_injected_provider(
    tmp_path: Path, capsys
):
    case = clarified_room_case()
    first = _valid_ready_brief(complete_room_case())
    first["original_request"] = case["user_request"]
    first["status"] = "needs_clarification"
    first["known_facts"]["walls"].pop("thickness_mm")
    first["user_corrections"] = []
    first["missing_facts"] = [
        {
            "id": "mf-wall-thickness",
            "code": "WALL_THICKNESS_MISSING",
            "path": "/known_facts/walls/thickness_mm",
            "message": "墙体厚度尚未提供。",
            "reason": "生成实体墙体需要明确厚度。",
            "blocking": True,
            "evidence_refs": ["schema:bim-json-v2:representation"],
            "source_turns": ["turn-user-001"],
        }
    ]
    first["clarification_questions"] = [
        {
            "id": "q-wall-thickness",
            "text": "请问墙体厚度是多少毫米？",
            "targets": ["mf-wall-thickness"],
            "reason": "缺少厚度时不能生成实体墙体。",
            "evidence_refs": ["schema:bim-json-v2:representation"],
        }
    ]
    for fact_source in first["fact_sources"]:
        fact_source["source_turns"] = ["turn-user-001"]
    first["provenance"]["source_turns"] = ["turn-user-001"]
    second = json.loads(json.dumps(first, ensure_ascii=False))
    second["status"] = "ready"
    second["known_facts"]["walls"]["thickness_mm"] = 300
    second["missing_facts"] = []
    second["clarification_questions"] = []
    for fact_source in second["fact_sources"]:
        fact_source["source_turns"] = ["turn-user-001"]
        if fact_source["path"] == "/known_facts/walls":
            fact_source["source_turns"].append("turn-user-003")
    second["provenance"]["source_turns"] = [
        "turn-user-001",
        "turn-user-003",
    ]
    provider = _SequenceLiveProvider([first, second])
    answer_file = tmp_path / "answers.json"
    answer_file.write_text(
        json.dumps({"answers": ["墙体厚度为300毫米。"]}, ensure_ascii=False),
        encoding="utf-8",
    )
    script_path = Path("scripts/agent/run_phase6_1_live.py")
    spec = importlib.util.spec_from_file_location("run_phase6_1_live_clarify", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output_dir = tmp_path / "output"

    exit_code = module.main(
        [
            "--stage",
            "clarify",
            "--case",
            "clarified-room",
            "--answers",
            str(answer_file),
            "--live",
            "--output-dir",
            str(output_dir),
        ],
        provider_factory=lambda: provider,
    )

    summary = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert summary["status"] == "ready"
    assert summary["live_call_count"] == 2


def _write_ready_design_source(path: Path) -> Path:
    path.mkdir(parents=True)
    case = complete_room_case()
    brief = _valid_ready_brief(case)
    selection = select_design_brief_context(
        user_request=case["user_request"],
        conversation=case["conversation"],
    )
    (path / "input.txt").write_text(case["user_request"] + "\n", encoding="utf-8")
    (path / "conversation.json").write_text(
        json.dumps(case["conversation"], ensure_ascii=False),
        encoding="utf-8",
    )
    (path / "design-brief.json").write_text(
        json.dumps(brief, ensure_ascii=False),
        encoding="utf-8",
    )
    (path / "context-selection.json").write_text(
        json.dumps(selection, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def test_live_generator_stage_renders_exact_contracts_and_routes_formal(
    tmp_path: Path,
):
    source_dir = _write_ready_design_source(tmp_path / "design-source")
    formal = json.loads(
        Path("tests/contract_v2/fixtures/minimal.json").read_text(encoding="utf-8")
    )
    provider = _RecordingLiveProvider(formal)
    output_dir = tmp_path / "generator"

    result = run_generator_stage(
        provider=provider,
        output_dir=output_dir,
        design_source_dir=source_dir,
        case_id="complete-room",
    )

    assert result["status"] == "formal"
    assert result["classification"] == "formal"
    assert result["valid"] is True
    assert result["strict_output_contract_valid"] is True
    assert json.loads(
        (output_dir / "candidate.json").read_text(encoding="utf-8")
    ) == formal
    assert not (output_dir / "draft.json").exists()
    expected_files = {
        "input.txt",
        "conversation.json",
        "design-brief.json",
        "generator-context.json",
        "prompt-render-input.json",
        "prompt-rendered.md",
        "request.redacted.json",
        "response.raw.json",
        "response-metadata.json",
        "events.jsonl",
        "model-text.txt",
        "parsed-output.json",
        "candidate.json",
        "classification.json",
        "validation.json",
        "metrics.json",
        "trace-manifest.json",
    }
    assert expected_files <= {item.name for item in output_dir.iterdir()}
    renderer_inputs = json.loads(
        (output_dir / "prompt-render-input.json").read_text(encoding="utf-8")
    )
    assert renderer_inputs["FORMAL_SCHEMA"]["$id"].endswith(
        "/bim-json/2.0/schema.json"
    )
    assert renderer_inputs["DRAFT_SCHEMA"]["$id"].endswith(
        "/bim-json/draft/1.0/schema.json"
    )
    assert "SCHEMA_SUMMARY" not in renderer_inputs
    assert "bim-json-draft/1.0" in provider.prompt
    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["response_id"] == "msg_unit_design_brief_v2"
    assert metrics["normalization_diagnostics"] == []


def test_live_generator_stage_blocks_unknown_contract_without_editing_output(
    tmp_path: Path,
):
    source_dir = _write_ready_design_source(tmp_path / "design-source")
    unknown = {
        "draft_version": "text2ifc/draft-envelope/1.0",
        "target_schema_version": "bim-json/2.0",
        "partial_document": {},
    }
    provider = _RecordingLiveProvider(unknown)
    output_dir = tmp_path / "generator"

    result = run_generator_stage(
        provider=provider,
        output_dir=output_dir,
        design_source_dir=source_dir,
        case_id="complete-room",
    )

    assert result["status"] == "blocked_failure"
    assert result["classification"] == "unknown_contract"
    assert result["valid"] is False
    assert not (output_dir / "candidate.json").exists()
    assert not (output_dir / "draft.json").exists()
    assert json.loads(
        (output_dir / "parsed-output.json").read_text(encoding="utf-8")
    ) == unknown
    classification = json.loads(
        (output_dir / "classification.json").read_text(encoding="utf-8")
    )
    assert classification["diagnostics"][0]["code"] == "UNKNOWN_DRAFT_VERSION"


def test_live_generator_cli_uses_injected_provider_and_design_source(
    tmp_path: Path, capsys
):
    source_dir = _write_ready_design_source(tmp_path / "design-source")
    formal = json.loads(
        Path("tests/contract_v2/fixtures/minimal.json").read_text(encoding="utf-8")
    )
    provider = _RecordingLiveProvider(formal)
    script_path = Path("scripts/agent/run_phase6_1_live.py")
    spec = importlib.util.spec_from_file_location("run_phase6_1_live_generate", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output_dir = tmp_path / "generator"

    exit_code = module.main(
        [
            "--stage",
            "generate",
            "--case",
            "complete-room",
            "--design-source-dir",
            str(source_dir),
            "--live",
            "--output-dir",
            str(output_dir),
        ],
        provider_factory=lambda: provider,
    )

    summary = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert summary["status"] == "formal"
    assert summary["classification"] == "formal"


def test_live_cli_uses_stable_generator_directory_name():
    script_path = Path("scripts/agent/run_phase6_1_live.py")
    spec = importlib.util.spec_from_file_location("run_phase6_1_live_paths", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    path = module.default_output_dir(stage="generate", case_id="complete-room")

    assert path == module.DEFAULT_LIVE_ROOT / "complete-room" / "generator"


def _write_valid_generator_source(path: Path) -> Path:
    path.mkdir(parents=True)
    formal = json.loads(
        Path("tests/contract_v2/fixtures/minimal.json").read_text(encoding="utf-8")
    )
    case = complete_room_case()
    brief = _valid_ready_brief(case)
    files = {
        "input.txt": case["user_request"] + "\n",
        "conversation.json": json.dumps(case["conversation"], ensure_ascii=False),
        "design-brief.json": json.dumps(brief, ensure_ascii=False),
        "candidate.json": json.dumps(formal, ensure_ascii=False),
        "validation.json": json.dumps({"valid": True, "issue_count": 0, "issues": []}),
        "metrics.json": json.dumps(
            {
                "response_id": "msg_live_formal",
                "contract_status": "formal",
                "contract_valid": True,
                "evidence_class": "live",
            }
        ),
        "generator-context.json": json.dumps(
            {"capability_profile": [], "few_shots": []}
        ),
    }
    for name, content in files.items():
        (path / name).write_text(content, encoding="utf-8")
    return path


def _write_repairable_generator_source(path: Path) -> Path:
    path.mkdir(parents=True)
    formal = json.loads(
        Path("tests/contract_v2/fixtures/minimal.json").read_text(encoding="utf-8")
    )
    case = complete_room_case()
    brief = _valid_ready_brief(case)
    files = {
        "input.txt": case["user_request"] + "\n",
        "conversation.json": json.dumps(case["conversation"], ensure_ascii=False),
        "design-brief.json": json.dumps(brief, ensure_ascii=False),
        "candidate.json": json.dumps(formal, ensure_ascii=False),
        "validation.json": json.dumps(
            {
                "valid": False,
                "issue_count": 1,
                "issues": [
                    {
                        "code": "INVALID_ENUM",
                        "path": "/entities/0/ifc_class",
                        "message": "Invalid IFC class enum.",
                    }
                ],
            }
        ),
        "metrics.json": json.dumps(
            {
                "response_id": "msg_live_invalid_enum",
                "contract_status": "invalid",
                "contract_valid": False,
                "evidence_class": "live",
            }
        ),
        "generator-context.json": json.dumps(
            {"capability_profile": [{"evidence_id": "schema:formal"}], "few_shots": []}
        ),
    }
    for name, content in files.items():
        (path / name).write_text(content, encoding="utf-8")
    return path


def _write_auditable_case_dir(path: Path) -> Path:
    case = complete_room_case()
    design = path / "design-brief"
    generator = path / "generator"
    repair = path / "repair"
    design.mkdir(parents=True)
    generator.mkdir(parents=True)
    repair.mkdir(parents=True)
    formal = json.loads(
        Path("tests/contract_v2/fixtures/minimal.json").read_text(encoding="utf-8")
    )
    brief = _valid_ready_brief(case)

    (design / "input.txt").write_text(case["user_request"] + "\n", encoding="utf-8")
    (design / "conversation.json").write_text(
        json.dumps(case["conversation"], ensure_ascii=False),
        encoding="utf-8",
    )
    (design / "prompt-rendered.md").write_text("Design Brief prompt", encoding="utf-8")
    (design / "request.redacted.json").write_text(
        json.dumps({"request": {"model": "mimo-v2.5-pro"}}),
        encoding="utf-8",
    )
    (design / "response.raw.json").write_text(
        json.dumps({"id": "msg_design", "stop_reason": "end_turn"}),
        encoding="utf-8",
    )
    (design / "model-text.txt").write_text(
        json.dumps(brief, ensure_ascii=False),
        encoding="utf-8",
    )
    (design / "design-brief.json").write_text(
        json.dumps(brief, ensure_ascii=False),
        encoding="utf-8",
    )
    (design / "validation.json").write_text(
        json.dumps({"valid": True, "issues": []}),
        encoding="utf-8",
    )
    (design / "metrics.json").write_text(
        json.dumps({"response_id": "msg_design", "evidence_class": "live"}),
        encoding="utf-8",
    )

    (generator / "prompt-rendered.md").write_text("Generator prompt", encoding="utf-8")
    (generator / "response.raw.json").write_text(
        json.dumps({"id": "msg_generator", "stop_reason": "end_turn"}),
        encoding="utf-8",
    )
    (generator / "model-text.txt").write_text(
        json.dumps(formal, ensure_ascii=False),
        encoding="utf-8",
    )
    (generator / "candidate.json").write_text(
        json.dumps(formal, ensure_ascii=False),
        encoding="utf-8",
    )
    (generator / "validation.json").write_text(
        json.dumps({"valid": True, "issues": []}),
        encoding="utf-8",
    )
    (generator / "metrics.json").write_text(
        json.dumps({"response_id": "msg_generator", "evidence_class": "live"}),
        encoding="utf-8",
    )

    (repair / "route.json").write_text(
        json.dumps({"route": "no_repair_needed", "provider_call_count": 0}),
        encoding="utf-8",
    )
    (repair / "metrics.json").write_text(
        json.dumps({"route": "no_repair_needed", "evidence_class": "live-derived-no-call"}),
        encoding="utf-8",
    )
    return path


def _write_finalizable_case_dir(path: Path) -> Path:
    case_dir = _write_auditable_case_dir(path)
    live_candidate = json.loads(
        (
            PROJECT_ROOT
            / "dataset/processed/agent-demo/phase6.1-mimo-live/complete-room/generator/candidate.json"
        ).read_text(encoding="utf-8")
    )
    generator = case_dir / "generator"
    (generator / "candidate.json").write_text(
        json.dumps(live_candidate, ensure_ascii=False),
        encoding="utf-8",
    )
    (generator / "model-text.txt").write_text(
        json.dumps(live_candidate, ensure_ascii=False),
        encoding="utf-8",
    )
    (case_dir / "audit").mkdir(parents=True)
    (case_dir / "audit" / "audit-report.json").write_text(
        json.dumps(
            {
                "schema_version": "text2ifc/audit/2.0",
                "recommendation": "accept",
                "blocking": False,
                "deterministic_gate_status": "passed",
                "findings": [],
                "evidence_paths": [
                    "design-brief/design-brief.json",
                    "generator/candidate.json",
                    "repair/route.json",
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (case_dir / "audit" / "metrics.json").write_text(
        json.dumps(
            {
                "response_id": "msg_audit_accept",
                "evidence_class": "live",
                "valid": True,
                "strict_output_contract_valid": True,
            }
        ),
        encoding="utf-8",
    )
    return case_dir


def test_successful_first_pass_repair_stage_never_creates_provider(tmp_path: Path):
    source_dir = _write_valid_generator_source(tmp_path / "generator")
    calls = []

    def forbidden_provider_factory():
        calls.append("created")
        raise AssertionError("no provider may be created for first-pass success")

    output_dir = tmp_path / "repair"
    result = run_repair_stage(
        provider_factory=forbidden_provider_factory,
        output_dir=output_dir,
        generator_source_dir=source_dir,
        case_id="complete-room",
    )

    assert calls == []
    assert result["route"] == "no_repair_needed"
    assert result["provider_call_count"] == 0
    assert result["repair_attempts"] == []
    assert result["valid"] is True
    route = json.loads((output_dir / "route.json").read_text(encoding="utf-8"))
    assert route["route"] == "no_repair_needed"
    assert route["repair_attempts"] == []
    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["evidence_class"] == "live-derived-no-call"
    assert metrics["source_generator_response_id"] == "msg_live_formal"


def test_repair_stage_calls_provider_once_for_eligible_contract_failure(
    tmp_path: Path,
):
    source_dir = _write_repairable_generator_source(tmp_path / "generator")
    repaired = json.loads(
        Path("tests/contract_v2/fixtures/minimal.json").read_text(encoding="utf-8")
    )
    repaired["entities"][0]["ifc_class"] = "IfcProject"
    provider = _RecordingLiveProvider(repaired)
    created = []

    def provider_factory():
        created.append("created")
        return provider

    output_dir = tmp_path / "repair"
    result = run_repair_stage(
        provider_factory=provider_factory,
        output_dir=output_dir,
        generator_source_dir=source_dir,
        case_id="complete-room",
    )

    assert created == ["created"]
    assert result["route"] == "repair_attempted"
    assert result["provider_call_count"] == 1
    assert result["valid"] is True
    assert result["repair_attempts"][0]["result_status"] == "improved"
    assert "INVALID_ENUM" in provider.prompt
    assert (output_dir / "prompt-rendered.md").is_file()
    assert (output_dir / "response.raw.json").is_file()
    assert json.loads(
        (output_dir / "repaired-candidate.json").read_text(encoding="utf-8")
    ) == repaired
    fact_delta = json.loads((output_dir / "fact-delta.json").read_text(encoding="utf-8"))
    assert fact_delta["valid"] is True
    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["evidence_class"] == "unit_test_fixture"
    assert metrics["source_generator_response_id"] == "msg_live_invalid_enum"


def test_repair_cli_records_zero_calls_for_live_first_pass_success(
    tmp_path: Path, capsys
):
    source_dir = _write_valid_generator_source(tmp_path / "generator")
    script_path = Path("scripts/agent/run_phase6_1_live.py")
    spec = importlib.util.spec_from_file_location("run_phase6_1_live_repair", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output_dir = tmp_path / "repair"

    exit_code = module.main(
        [
            "--stage",
            "repair",
            "--case",
            "complete-room",
            "--generator-source-dir",
            str(source_dir),
            "--live",
            "--output-dir",
            str(output_dir),
        ],
        provider_factory=lambda: (_ for _ in ()).throw(
            AssertionError("provider must not be created")
        ),
    )

    summary = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert summary["route"] == "no_repair_needed"
    assert summary["provider_call_count"] == 0


def test_live_audit_report_stage_calls_provider_and_generates_report(
    tmp_path: Path,
):
    case_dir = _write_auditable_case_dir(tmp_path / "complete-room")
    payload = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "accept",
        "blocking": False,
        "deterministic_gate_status": "passed",
        "findings": [],
        "evidence_paths": [
            "design-brief/design-brief.json",
            "generator/candidate.json",
            "repair/route.json",
        ],
    }
    provider = _RecordingLiveProvider(payload)

    result = run_audit_report_stage(
        provider=provider,
        case_dir=case_dir,
        case_id="complete-room",
    )

    assert result["status"] == "accepted"
    assert result["valid"] is True
    assert result["response_id"] == "msg_unit_design_brief_v2"
    assert "repair/route.json" in provider.prompt
    assert (case_dir / "audit" / "prompt-rendered.md").is_file()
    assert (case_dir / "audit" / "response.raw.json").is_file()
    assert json.loads(
        (case_dir / "audit" / "audit-report.json").read_text(encoding="utf-8")
    ) == payload
    report = (case_dir / "report.md").read_text(encoding="utf-8")
    assert "## Audit Agent" in report
    assert "(audit/audit-report.json)" in report


def test_live_audit_report_stage_blocks_fenced_output_contract(tmp_path: Path):
    case_dir = _write_auditable_case_dir(tmp_path / "complete-room")
    payload = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "accept",
        "blocking": False,
        "deterministic_gate_status": "passed",
        "findings": [],
        "evidence_paths": [
            "design-brief/design-brief.json",
            "generator/candidate.json",
            "repair/route.json",
        ],
    }
    provider = _RecordingLiveProvider(payload, fenced=True)

    result = run_audit_report_stage(
        provider=provider,
        case_dir=case_dir,
        case_id="complete-room",
    )

    assert result["status"] == "blocked_output_contract"
    assert result["valid"] is False
    metrics = json.loads((case_dir / "audit" / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["strict_output_contract_valid"] is False
    assert metrics["normalization_diagnostics"][0]["code"] == "OUTER_JSON_FENCE_REMOVED"


def test_audit_report_cli_uses_injected_provider_and_case_dir(
    tmp_path: Path,
    capsys,
):
    case_dir = _write_auditable_case_dir(tmp_path / "complete-room")
    payload = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "accept",
        "blocking": False,
        "deterministic_gate_status": "passed",
        "findings": [],
        "evidence_paths": [
            "design-brief/design-brief.json",
            "generator/candidate.json",
            "repair/route.json",
        ],
    }
    provider = _RecordingLiveProvider(payload)
    script_path = Path("scripts/agent/run_phase6_1_live.py")
    spec = importlib.util.spec_from_file_location("run_phase6_1_live_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    exit_code = module.main(
        [
            "--stage",
            "audit-report",
            "--case",
            "complete-room",
            "--case-dir",
            str(case_dir),
            "--live",
        ],
        provider_factory=lambda: provider,
    )

    summary = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert summary["status"] == "accepted"
    assert summary["response_id"] == "msg_unit_design_brief_v2"
    assert (case_dir / "report.md").is_file()


def test_final_acceptance_stage_writes_geometry_checked_ifc_and_root_report(
    tmp_path: Path,
):
    case_dir = _write_finalizable_case_dir(tmp_path / "complete-room")
    output_dir = tmp_path / "phase6.1-mimo-live"

    result = run_final_acceptance_stage(
        case_dir=case_dir,
        output_dir=output_dir,
        case_id="complete-room",
    )

    assert result["valid"] is True
    assert result["ifc_path"] == str(output_dir / "output.ifc")
    assert (output_dir / "output.ifc").is_file()
    assert (output_dir / "report.md").is_file()
    geometry = json.loads((output_dir / "geometry-feedback.json").read_text(encoding="utf-8"))
    assert geometry["success"] is True
    assert geometry["issues"] == []
    east_bbox = geometry["metrics"]["walls"]["wall-east"]["bbox"]
    assert east_bbox["x"] == [5.85, 6.15]
    metrics = json.loads((output_dir / "acceptance-metrics.json").read_text(encoding="utf-8"))
    assert metrics["audit_response_id"] == "msg_audit_accept"
    assert metrics["compile_reopen_success"] is True
    assert metrics["geometry_success"] is True
    report = (output_dir / "report.md").read_text(encoding="utf-8")
    assert "output.ifc" in report
    assert "complete-room/report.md" in report
