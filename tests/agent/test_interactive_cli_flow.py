import json

from text2ifc_agent.context_selection import select_design_brief_context
from text2ifc_agent.clarification import ClarificationCall
from text2ifc_agent.interactive_cli_flow import (
    make_openai_design_brief_invoker,
    run_design_brief_clarification_loop,
)
from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config
from text2ifc_agent.session_store import SessionStore


EVIDENCE = [
    {"evidence_id": "schema:bim-json-v2:representation"},
    {"evidence_id": "capability:IFC2X3:IfcSpace"},
    {"evidence_id": "capability:IFC2X3:IfcWall"},
]


def _brief(*, original_request: str, status: str, source_turns=None):
    source_turns = source_turns or ["turn-user-001"]
    blocker = {
        "id": "mf-wall-thickness",
        "code": "WALL_THICKNESS_MISSING",
        "path": "/known_facts/walls/thickness_mm",
        "message": "墙体厚度尚未提供。",
        "reason": "生成实体墙体需要明确厚度。",
        "blocking": True,
        "evidence_refs": ["schema:bim-json-v2:representation"],
        "source_turns": ["turn-user-001"],
    }
    return {
        "schema_version": "text2ifc/design-brief/2.0",
        "language": "zh-CN",
        "original_request": original_request,
        "status": status,
        "known_facts": {
            "space": {"length_mm": 6000, "width_mm": 4000, "height_mm": 3000},
            "walls": {"count": 4, "enclosure": "closed"},
        },
        "fact_sources": [
            {
                "path": "/known_facts",
                "source_turns": source_turns,
                "evidence_refs": ["capability:IFC2X3:IfcSpace"],
            }
        ],
        "missing_facts": [blocker] if status != "ready" else [],
        "ambiguities": [],
        "unsupported_requests": [],
        "user_corrections": [],
        "clarification_questions": (
            [
                {
                    "id": "q-wall-thickness",
                    "text": "墙体厚度是多少毫米？",
                    "targets": ["mf-wall-thickness"],
                    "reason": "缺少厚度时不能生成墙体。",
                    "evidence_refs": ["schema:bim-json-v2:representation"],
                }
            ]
            if status == "needs_clarification"
            else []
        ),
        "provenance": {
            "source_turns": source_turns,
            "selected_evidence_ids": [
                "schema:bim-json-v2:representation",
                "capability:IFC2X3:IfcSpace",
                "capability:IFC2X3:IfcWall",
            ],
            "few_shot_ids": [],
        },
    }


def _call(index, *, original_request, status, source_turns=None):
    return ClarificationCall(
        call_index=index,
        response_id=f"msg_phase62_{index}",
        prompt_template_id="design-brief.v2.1",
        prompt_template_hash="sha256:prompt-v2.1",
        artifact_dir=f"calls/{index:02d}-design-brief",
        brief=_brief(
            original_request=original_request,
            status=status,
            source_turns=source_turns,
        ),
        evidence_catalog=EVIDENCE,
    )


def test_design_brief_loop_persists_agent_question_and_recall(tmp_path):
    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="创建一个6米乘4米的房间，高3米。")
    observed = []

    def invoke(transcript, call_index):
        observed.append((transcript, call_index))
        if call_index == 1:
            return _call(
                call_index,
                original_request=session.original_input,
                status="needs_clarification",
            )
        return _call(
            call_index,
            original_request=session.original_input,
            status="ready",
            source_turns=["turn-user-001", "turn-user-003"],
        )

    result = run_design_brief_clarification_loop(
        store=store,
        session=session.session_hash,
        invoke_design_brief=invoke,
        user_answers=["墙体厚度为300mm。"],
    )
    export = store.session_export_payload(session.session_hash)

    assert result.status == "ready"
    assert [call_index for _, call_index in observed] == [1, 2]
    assert [turn["role"] for turn in export["turns"]] == ["user", "assistant", "user"]
    assert export["turns"][1]["text"] == "墙体厚度是多少毫米？"
    assert export["turns"][2]["text"] == "墙体厚度为300mm。"
    assert export["agent_calls"][0]["payload"]["response_id"] == "msg_phase62_1"
    assert export["agent_calls"][1]["payload"]["response_id"] == "msg_phase62_2"
    assert (root / "runs" / session.session_hash / "design-brief.json").is_file()


def test_unknown_answer_routes_to_draft_without_ifc_artifact(tmp_path):
    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="创建一个房间。")

    def invoke(transcript, call_index):
        status = "needs_clarification" if call_index == 1 else "draft_required"
        return _call(
            call_index,
            original_request=session.original_input,
            status=status,
            source_turns=["turn-user-001"] if call_index == 1 else ["turn-user-001", "turn-user-003"],
        )

    result = run_design_brief_clarification_loop(
        store=store,
        session=session.session_hash,
        invoke_design_brief=invoke,
        user_answers=["这个厚度我不知道。"],
    )
    export = store.session_export_payload(session.session_hash)

    assert result.status == "draft_required"
    assert store.get_session(session.session_hash).status == "draft_required"
    assert not (root / "runs" / session.session_hash / "output.ifc").exists()
    assert "这个厚度我不知道。" in json.dumps(export["turns"], ensure_ascii=False)


def test_phase6_2_cli_runs_design_brief_loop_with_injected_invoker(
    tmp_path, capsys
):
    from scripts.agent import run_phase6_2_cli

    root = tmp_path / "phase6.2-interactive-cli"
    scripted_stdin = tmp_path / "clarified-room.stdin"
    scripted_stdin.write_text(
        "\n".join(
            [
                "创建一个6米乘4米、高3米的房间，南墙有门，北墙有窗。",
                "墙体厚度为300mm。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    observed = []

    def invoke(transcript, call_index):
        observed.append((transcript, call_index))
        original_request = transcript[0]["content"]
        if call_index == 1:
            return _call(
                call_index,
                original_request=original_request,
                status="needs_clarification",
            )
        return _call(
            call_index,
            original_request=original_request,
            status="ready",
            source_turns=["turn-user-001", "turn-user-003"],
        )

    exit_code = run_phase6_2_cli.main(
        [
            "--live",
            "--stop-after",
            "design-brief",
            "--scripted-stdin",
            str(scripted_stdin),
            "--output-root",
            str(root),
            "--db",
            str(root / "sessions.sqlite"),
        ],
        design_brief_invoker=invoke,
    )
    summary = json.loads(capsys.readouterr().out)
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    export = store.session_export_payload(summary["session_hash"])

    assert exit_code == 0
    assert summary["status"] == "ready"
    assert [call_index for _, call_index in observed] == [1, 2]
    assert export["turns"][1]["text"] == "墙体厚度是多少毫米？"
    assert export["turns"][2]["text"] == "墙体厚度为300mm。"
    assert (root / "runs" / summary["session_hash"] / "design-brief.json").is_file()


def test_openai_design_brief_invoker_writes_trace_and_returns_call(tmp_path):
    captured = {}
    original_request = "创建一个6米乘4米、高3米的房间。"
    brief = _brief(
        original_request=original_request,
        status="needs_clarification",
    )
    selection = select_design_brief_context(
        user_request=original_request,
        conversation=[
            {"turn_id": "turn-user-001", "role": "user", "content": original_request}
        ],
    )
    selected_evidence_ids = [item["evidence_id"] for item in selection["evidence"]]
    brief["fact_sources"][0]["evidence_refs"] = ["schema:bim-json-v2:representation"]
    brief["provenance"]["selected_evidence_ids"] = selected_evidence_ids

    class Response:
        def model_dump(self):
            return {
                "id": "chatcmpl-design-001",
                "object": "chat.completion",
                "model": "mimo-v2.5-pro",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(brief, ensure_ascii=False),
                        },
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 200,
                    "total_tokens": 300,
                },
            }

    class ChatCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return Response()

    class Client:
        def __init__(self):
            self.chat = type("Chat", (), {"completions": ChatCompletions()})()

    config = load_openai_compatible_runtime_config(
        {
            "API_KEY": "secret-api-key",
            "OpenAI_BASE_URL": "https://api.xiaomimimo.com",
            "TEXT2IFC_MIMO_MODEL": "mimo-v2.5-pro",
        }
    )
    invoker = make_openai_design_brief_invoker(
        config=config,
        run_dir=tmp_path,
        client_factory=lambda **kwargs: Client(),
    )

    call = invoker(
        [{"turn_id": "turn-user-001", "role": "user", "content": original_request}],
        1,
    )

    assert call.response_id == "chatcmpl-design-001"
    assert call.prompt_template_id == "design-brief.v2.1"
    assert call.brief == brief
    assert captured["model"] == "mimo-v2.5-pro"
    assert captured["max_completion_tokens"] == 1024
    assert "text2ifc/design-brief/2.0" in captured["messages"][0]["content"]
    assert (tmp_path / "calls" / "01-design-brief" / "prompt-rendered.md").is_file()
    assert (tmp_path / "calls" / "01-design-brief" / "response.raw.json").is_file()
    metrics = json.loads(
        (tmp_path / "calls" / "01-design-brief" / "metrics.json").read_text(
            encoding="utf-8"
        )
    )
    assert metrics["response_id"] == "chatcmpl-design-001"
    assert metrics["finish_reason"] == "stop"


def test_phase6_2_cli_builds_default_openai_design_brief_invoker(
    tmp_path, capsys
):
    from scripts.agent import run_phase6_2_cli

    root = tmp_path / "phase6.2-interactive-cli"
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "API_KEY=secret-api-key",
                "OpenAI_BASE_URL=https://api.xiaomimimo.com",
                "TEXT2IFC_MIMO_MODEL=mimo-v2.5-pro",
            ]
        ),
        encoding="utf-8",
    )
    original_request = "创建一个6米乘4米、高3米的房间。"
    scripted_stdin = tmp_path / "clarified-room.stdin"
    scripted_stdin.write_text(original_request + "\n墙体厚度为300mm。\n", encoding="utf-8")

    first = _brief(original_request=original_request, status="needs_clarification")
    first_selection = select_design_brief_context(
        user_request=original_request,
        conversation=[{"turn_id": "turn-user-001", "role": "user", "content": original_request}],
    )
    first["fact_sources"][0]["evidence_refs"] = ["schema:bim-json-v2:representation"]
    first["provenance"]["selected_evidence_ids"] = [
        item["evidence_id"] for item in first_selection["evidence"]
    ]
    second = _brief(
        original_request=original_request,
        status="ready",
        source_turns=["turn-user-001", "turn-user-003"],
    )
    second["fact_sources"][0]["evidence_refs"] = ["schema:bim-json-v2:representation"]
    second["provenance"]["selected_evidence_ids"] = [
        item["evidence_id"] for item in first_selection["evidence"]
    ]
    responses = [first, second]

    class Response:
        def __init__(self, payload, index):
            self.payload = payload
            self.index = index

        def model_dump(self):
            return {
                "id": f"chatcmpl-design-{self.index}",
                "object": "chat.completion",
                "model": "mimo-v2.5-pro",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(self.payload, ensure_ascii=False),
                        },
                    }
                ],
                "usage": {"total_tokens": 10 + self.index},
            }

    class ChatCompletions:
        def __init__(self):
            self.index = 0

        def create(self, **kwargs):
            self.index += 1
            return Response(responses[self.index - 1], self.index)

    class Client:
        def __init__(self):
            self.chat = type("Chat", (), {"completions": ChatCompletions()})()

    exit_code = run_phase6_2_cli.main(
        [
            "--live",
            "--stop-after",
            "design-brief",
            "--env-file",
            str(env_file),
            "--scripted-stdin",
            str(scripted_stdin),
            "--output-root",
            str(root),
            "--db",
            str(root / "sessions.sqlite"),
        ],
        openai_client_factory=lambda **kwargs: Client(),
    )

    summary = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert summary["status"] == "ready"
    assert (root / "runs" / summary["session_hash"] / "design-brief.json").is_file()
    assert (
        root / "runs" / summary["session_hash"] / "calls" / "01-design-brief" / "response.raw.json"
    ).is_file()
