import json
from copy import deepcopy
import io
import subprocess
import sys
from pathlib import Path

from text2ifc_agent.clarification import ClarificationCall
from text2ifc_agent.context_selection import select_design_brief_context
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput, ProviderOutputError
from text2ifc_agent.session_store import SessionStore


ROOT = Path(__file__).resolve().parents[2]
PHASE6_1_COMPLETE = ROOT / "dataset/processed/agent-demo/phase6.1-mimo-live/complete-room"
EVIDENCE = [
    {"evidence_id": "schema:bim-json-v2:representation"},
    {"evidence_id": "capability:IFC2X3:IfcSpace"},
    {"evidence_id": "capability:IFC2X3:IfcWall"},
]

ORIGINAL_REQUEST = "\u521b\u5efa\u4e00\u4e2a6\u7c73\u4e584\u7c73\u3001\u9ad83\u7c73\u7684\u623f\u95f4\u3002"
QUESTION_TEXT = "\u5899\u4f53\u539a\u5ea6\u662f\u591a\u5c11\u6beb\u7c73\uff1f"
ANSWER_TEXT = "\u5899\u4f53\u539a\u5ea6\u4e3a300mm\u3002"


def test_live_repl_prints_mimo_question_before_reading_user_answer(tmp_path):
    from scripts.agent import run_text2ifc_chat

    root = tmp_path / "phase6.2-fix-repl"
    output = io.StringIO()
    prompts_seen: list[str] = []
    session_hash_holder: dict[str, str] = {}

    def invoke(transcript, call_index):
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

    def input_func(prompt):
        prompts_seen.append(prompt)
        if len(prompts_seen) == 1:
            return ORIGINAL_REQUEST
        visible = output.getvalue()
        assert QUESTION_TEXT in visible
        store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
        try:
            sessions = store.list_sessions()
            assert len(sessions) == 1
            session_hash_holder["value"] = sessions[0].session_hash
            events = store.list_events(sessions[0].session_hash)
        finally:
            store.close()
        event_types = [event.event_type for event in events]
        assert "assistant_question_displayed" in event_types
        assert "user_answer_requested" in event_types
        assert event_types.index("assistant_question_displayed") < event_types.index(
            "user_answer_requested"
        )
        return ANSWER_TEXT

    exit_code = run_text2ifc_chat.main(
        [
            "--live",
            "--stop-after",
            "design-brief",
            "--output-root",
            str(root),
            "--db",
            str(root / "sessions.sqlite"),
        ],
        design_brief_invoker=invoke,
        input_func=input_func,
        stdout=output,
    )

    assert exit_code == 0
    rendered = output.getvalue()
    assert "\u8bf7\u8f93\u5165\u5efa\u7b51\u9700\u6c42" in rendered
    assert "\u9700\u8981\u8865\u5145\u4fe1\u606f" in rendered
    assert "\u9700\u6c42\u5df2\u660e\u786e" in rendered
    assert "session_hash" in rendered

    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    try:
        session = store.get_session(session_hash_holder["value"])
        export = store.session_export_payload(session.session_hash)
    finally:
        store.close()

    assert session.status == "ready"
    assert [turn["role"] for turn in export["turns"]] == ["user", "assistant", "user"]
    assert export["turns"][1]["text"] == QUESTION_TEXT
    assert export["turns"][2]["text"] == ANSWER_TEXT
    started = [
        event
        for event in export["events"]
        if event["event_type"] == "repl_session_started"
    ][0]
    assert started["payload"]["interaction_mode"] == "human_repl_live"
    assert started["payload"]["input_source"] == "terminal"


def test_live_repl_quit_records_incomplete_without_ifc(tmp_path):
    from scripts.agent import run_text2ifc_chat

    root = tmp_path / "phase6.2-fix-repl"
    output = io.StringIO()
    answers = iter([ORIGINAL_REQUEST, "quit"])

    exit_code = run_text2ifc_chat.main(
        [
            "--live",
            "--stop-after",
            "design-brief",
            "--output-root",
            str(root),
            "--db",
            str(root / "sessions.sqlite"),
        ],
        design_brief_invoker=lambda transcript, call_index: _call(
            call_index,
            original_request=transcript[0]["content"],
            status="needs_clarification",
        ),
        input_func=lambda prompt: next(answers),
        stdout=output,
    )

    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    try:
        session = store.list_sessions()[0]
    finally:
        store.close()

    assert exit_code == 0
    assert session.status == "incomplete"
    assert not (root / "runs" / session.session_hash / "output.ifc").exists()
    assert "\u5df2\u9000\u51fa" in output.getvalue()


def test_live_repl_reprompts_empty_clarification_answer(tmp_path):
    from scripts.agent import run_text2ifc_chat

    root = tmp_path / "phase6.2-fix-repl"
    output = io.StringIO()
    answers = iter([ORIGINAL_REQUEST, "   ", ANSWER_TEXT])

    def invoke(transcript, call_index):
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

    exit_code = run_text2ifc_chat.main(
        [
            "--live",
            "--stop-after",
            "design-brief",
            "--output-root",
            str(root),
            "--db",
            str(root / "sessions.sqlite"),
        ],
        design_brief_invoker=invoke,
        input_func=lambda prompt: next(answers),
        stdout=output,
    )

    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    try:
        session = store.list_sessions()[0]
        export = store.session_export_payload(session.session_id)
    finally:
        store.close()

    rendered = output.getvalue()
    event_types = [event["event_type"] for event in export["events"]]
    assert exit_code == 0
    assert session.status == "ready"
    assert "\u56de\u7b54\u4e0d\u80fd\u4e3a\u7a7a" in rendered
    assert [turn["text"] for turn in export["turns"]] == [
        ORIGINAL_REQUEST,
        QUESTION_TEXT,
        ANSWER_TEXT,
    ]
    assert event_types.count("user_empty_answer_rejected") == 1
    assert event_types.count("user_answer_received") == 1
    assert event_types.index("user_empty_answer_rejected") < event_types.index(
        "user_answer_received"
    )


def test_live_repl_acknowledges_answer_before_rerunning_design_brief(tmp_path):
    from scripts.agent import run_text2ifc_chat

    root = tmp_path / "phase6.2-fix-repl"
    output = io.StringIO()
    answers = iter([ORIGINAL_REQUEST, ANSWER_TEXT])

    def invoke(transcript, call_index):
        original_request = transcript[0]["content"]
        if call_index == 1:
            return _call(
                call_index,
                original_request=original_request,
                status="needs_clarification",
            )
        assert "\u5df2\u6536\u5230\u56de\u7b54\uff0c\u6b63\u5728\u7ee7\u7eed\u68b3\u7406\u9700\u6c42" in output.getvalue()
        return _call(
            call_index,
            original_request=original_request,
            status="ready",
            source_turns=["turn-user-001", "turn-user-003"],
        )

    exit_code = run_text2ifc_chat.main(
        [
            "--live",
            "--stop-after",
            "design-brief",
            "--output-root",
            str(root),
            "--db",
            str(root / "sessions.sqlite"),
        ],
        design_brief_invoker=invoke,
        input_func=lambda prompt: next(answers),
        stdout=output,
    )

    assert exit_code == 0
    assert "\u9700\u6c42\u5df2\u660e\u786e" in output.getvalue()


def test_live_repl_ready_session_compiles_ifc_with_fix_acceptance_report(tmp_path):
    from scripts.agent import run_text2ifc_chat

    root = tmp_path / "phase6.2-fix-repl"
    output = io.StringIO()
    answers = iter([ORIGINAL_REQUEST, ANSWER_TEXT])

    def invoke(transcript, call_index):
        if call_index == 1:
            call = _call(
                call_index,
                original_request=transcript[0]["content"],
                status="needs_clarification",
            )
        else:
            call = _call(
                call_index,
                original_request=transcript[0]["content"],
                status="ready",
                source_turns=["turn-user-001", "turn-user-003"],
            )
        _write_design_brief_trace_fixture(root, call_index, transcript, call.brief)
        return call

    candidate = json.loads(
        (PHASE6_1_COMPLETE / "generator" / "candidate.json").read_text(
            encoding="utf-8"
        )
    )
    audit = {
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
    provider = _SequenceLiveProvider([candidate, audit])

    exit_code = run_text2ifc_chat.main(
        [
            "--live",
            "--output-root",
            str(root),
            "--db",
            str(root / "sessions.sqlite"),
        ],
        design_brief_invoker=invoke,
        live_provider_factory=lambda: provider,
        input_func=lambda prompt: next(answers),
        stdout=output,
    )

    final = json.loads((root / "final-acceptance.json").read_text(encoding="utf-8"))
    report_path = root / final["artifacts"]["report"]
    report = report_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert final["schema_version"] == "text2ifc/phase6.2-fix-final-acceptance-v1"
    assert final["interaction_mode"] == "human_repl_live"
    assert final["input_source"] == "terminal"
    assert (root / final["artifacts"]["ifc"]).is_file()
    assert "## REPL Interaction Evidence" in report
    assert "human_repl_live" in report
    assert "input_source" in report
    assert "assistant_question_displayed" in report
    assert "report.md:" in output.getvalue()


def test_repl_chat_script_path_help_runs_from_repo_root():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "agent" / "run_text2ifc_chat.py"),
            "--help",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode == 0
    assert "--live" in result.stdout
    assert "ModuleNotFoundError" not in result.stderr


def test_default_live_repl_design_brief_trace_is_session_scoped(tmp_path):
    from scripts.agent import run_text2ifc_chat

    root = tmp_path / "phase6.2-fix-repl"
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "API_KEY=secret-api-key",
                "OpenAI_BASE_URL=https://api.xiaomimimo.com",
                "TEXT2IFC_MIMO_MODEL=mimo-v2.5-pro",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output = io.StringIO()
    ready_brief = _brief(original_request=ORIGINAL_REQUEST, status="ready")
    selection = select_design_brief_context(
        user_request=ORIGINAL_REQUEST,
        conversation=[
            {"turn_id": "turn-user-001", "role": "user", "content": ORIGINAL_REQUEST}
        ],
    )
    selected_evidence_ids = [item["evidence_id"] for item in selection["evidence"]]
    ready_brief["fact_sources"][0]["evidence_refs"] = selected_evidence_ids[:1]
    ready_brief["provenance"]["selected_evidence_ids"] = selected_evidence_ids
    candidate = json.loads(
        (PHASE6_1_COMPLETE / "generator" / "candidate.json").read_text(
            encoding="utf-8"
        )
    )
    audit = {
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
    provider = _SequenceLiveProvider([candidate, audit])

    exit_code = run_text2ifc_chat.main(
        [
            "--live",
            "--env-file",
            str(env_file),
            "--output-root",
            str(root),
            "--db",
            str(root / "sessions.sqlite"),
        ],
        openai_client_factory=lambda **kwargs: _OpenAIClientSequence([ready_brief]),
        live_provider_factory=lambda: provider,
        input_func=lambda prompt: ORIGINAL_REQUEST,
        stdout=output,
    )

    final = json.loads((root / "final-acceptance.json").read_text(encoding="utf-8"))
    run_dir = root / "runs" / final["session_hash"]

    assert exit_code == 0
    assert not (root / "calls" / "01-design-brief").exists()
    assert (run_dir / "calls" / "01-design-brief" / "conversation.json").is_file()
    assert (run_dir / "design-brief" / "conversation.json").is_file()
    assert (run_dir / "output.ifc").is_file()


def test_live_repl_routes_geometry_failure_through_audit_before_final_status(tmp_path):
    from scripts.agent import run_text2ifc_chat

    root = tmp_path / "phase6.2-fix-repl"
    output = io.StringIO()
    answers = iter([ORIGINAL_REQUEST, ANSWER_TEXT])

    def invoke(transcript, call_index):
        if call_index == 1:
            call = _call(
                call_index,
                original_request=transcript[0]["content"],
                status="needs_clarification",
            )
        else:
            call = _call(
                call_index,
                original_request=transcript[0]["content"],
                status="ready",
                source_turns=["turn-user-001", "turn-user-003"],
            )
        _write_design_brief_trace_fixture(root, call_index, transcript, call.brief)
        return call

    candidate = _geometry_blocked_candidate()
    audit = {
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
    provider = _SequenceLiveProvider([candidate, audit])

    exit_code = run_text2ifc_chat.main(
        [
            "--live",
            "--output-root",
            str(root),
            "--db",
            str(root / "sessions.sqlite"),
        ],
        design_brief_invoker=invoke,
        live_provider_factory=lambda: provider,
        input_func=lambda prompt: next(answers),
        stdout=output,
    )

    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    try:
        session = store.list_sessions()[0]
    finally:
        store.close()
    rendered = output.getvalue()
    run_dir = root / "runs" / session.session_hash

    assert exit_code == 2
    assert session.status == "audit_blocked"
    assert (run_dir / "output.ifc").is_file()
    assert (run_dir / "report.md").is_file()
    assert (run_dir / "geometry-feedback.json").is_file()
    audit_input = json.loads(
        (run_dir / "audit" / "prompt-render-input.json").read_text(encoding="utf-8")
    )
    gate_feedback = audit_input["DETERMINISTIC_GATES"]["geometry_feedback"]
    assert gate_feedback["success"] is False
    assert [issue["code"] for issue in gate_feedback["issues"]] == [
        "WALL_ORIENTATION_MISMATCH",
        "WALL_ORIENTATION_MISMATCH",
        "ROOM_ENCLOSURE_OPEN",
    ]
    audit_validation = json.loads(
        (run_dir / "audit" / "validation.json").read_text(encoding="utf-8")
    )
    assert audit_validation["valid"] is False
    assert {
        issue["code"] for issue in audit_validation["issues"]
    } == {"AUDIT_OVERRIDE_ATTEMPT"}
    assert "Generator" in rendered
    assert "Audit" in rendered
    assert "audit_blocked" in rendered
    assert "output.ifc" in rendered
    assert "report.md" in rendered
    assert "geometry-feedback.json" in rendered
    report = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "geometry-feedback.json" in report
    assert "repair/repair-attempts.json" in report
    assert "audit/validation.json" in report


def test_live_repl_records_provider_failure_without_traceback(tmp_path):
    from scripts.agent import run_text2ifc_chat

    root = tmp_path / "phase6.2-fix-repl"
    output = io.StringIO()

    def invoke(transcript, call_index):
        call = _call(
            call_index,
            original_request=transcript[0]["content"],
            status="ready",
            source_turns=["turn-user-001"],
        )
        _write_design_brief_trace_fixture(root, call_index, transcript, call.brief)
        return call

    class FailingProvider:
        def generate_live(self, *, session_id, prompt, schema, state):
            del prompt, schema, state
            raise ProviderOutputError(
                "OpenAI-compatible live request failed for generator: RuntimeError",
                details={
                    "provider": "deepseek-openai-compatible",
                    "failure_class": "provider_connection_error",
                    "exception_type": "RuntimeError",
                    "session_id": session_id,
                    "request": {"model": "deepseek-v4-flash", "max_tokens": 8192},
                },
            )

    exit_code = run_text2ifc_chat.main(
        [
            "--live",
            "--output-root",
            str(root),
            "--db",
            str(root / "sessions.sqlite"),
        ],
        design_brief_invoker=invoke,
        live_provider_factory=FailingProvider,
        input_func=lambda prompt: ORIGINAL_REQUEST,
        stdout=output,
    )

    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    try:
        session = store.list_sessions()[0]
        export = store.session_export_payload(session.session_id)
    finally:
        store.close()
    run_dir = root / "runs" / session.session_hash
    provider_error = json.loads(
        (run_dir / "generator" / "provider-error.json").read_text(encoding="utf-8")
    )
    issues = json.loads((run_dir / "issues.json").read_text(encoding="utf-8"))
    route_decision = json.loads(
        (run_dir / "route-decision.json").read_text(encoding="utf-8")
    )
    feedback_rounds = json.loads(
        (run_dir / "feedback-rounds.json").read_text(encoding="utf-8")
    )

    assert exit_code == 2
    assert session.status == "provider_failed"
    assert provider_error["stage"] == "generator"
    assert provider_error["failure_class"] == "provider_connection_error"
    assert provider_error["provider"] == "deepseek-openai-compatible"
    assert issues["schema_version"] == "text2ifc/issues/1.0"
    assert issues["issues"][0]["source"] == "provider"
    assert issues["issues"][0]["owner"] == "provider"
    assert issues["issues"][0]["issue_type"] == "provider_format_error"
    assert issues["issues"][0]["suggested_route"] == "provider_retry"
    assert route_decision["schema_version"] == "text2ifc/route-decision/2.0"
    assert route_decision["route"] == "provider_retry"
    assert route_decision["target_stage"] == "provider"
    assert feedback_rounds["schema_version"] == "text2ifc/feedback-rounds/1.0"
    assert feedback_rounds["rounds"][0]["attempted_action"] == "prepare_provider_retry"
    assert (run_dir / "session-export.json").is_file()
    assert any(event["event_type"] == "generator_provider_failed" for event in export["events"])
    rendered = output.getvalue()
    assert "Provider: failed" in rendered
    assert "generator/provider-error.json" in rendered
    assert "Traceback" not in rendered


def _brief(*, original_request: str, status: str, source_turns=None):
    source_turns = source_turns or ["turn-user-001"]
    blocker = {
        "id": "mf-wall-thickness",
        "code": "WALL_THICKNESS_MISSING",
        "path": "/known_facts/walls/thickness_mm",
        "message": "\u5899\u4f53\u539a\u5ea6\u5c1a\u672a\u63d0\u4f9b\u3002",
        "reason": "\u751f\u6210\u5b9e\u4f53\u5899\u9700\u8981\u660e\u786e\u539a\u5ea6\u3002",
        "blocking": True,
        "evidence_refs": ["schema:bim-json-v2:representation"],
        "source_turns": source_turns,
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
                    "text": QUESTION_TEXT,
                    "targets": ["mf-wall-thickness"],
                    "reason": "\u7f3a\u5c11\u539a\u5ea6\u65f6\u4e0d\u80fd\u751f\u6210\u5899\u4f53\u3002",
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
        response_id=f"msg_phase62_fix_{index}",
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
            "id": f"msg_phase62_fix_provider_{index + 1}",
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
                "messages": [{"role": "user", "content": "<redacted-test-prompt>"}],
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


def _geometry_blocked_candidate() -> dict:
    candidate = json.loads(
        (PHASE6_1_COMPLETE / "generator" / "candidate.json").read_text(
            encoding="utf-8"
        )
    )
    candidate = deepcopy(candidate)
    for entity in candidate["entities"]:
        if entity.get("id") in {"wall-west", "wall-east"}:
            profile = entity["attributes"]["Representation"]["profile"]
            profile["x"] = 300
            profile["y"] = 4000
    return candidate


class _OpenAIClientSequence:
    def __init__(self, payloads: list[dict]) -> None:
        self.chat = type(
            "Chat",
            (),
            {"completions": _OpenAIChatCompletionsSequence(payloads)},
        )()


class _OpenAIChatCompletionsSequence:
    def __init__(self, payloads: list[dict]) -> None:
        self.payloads = payloads
        self.index = 0

    def create(self, **kwargs):
        del kwargs
        self.index += 1
        payload = self.payloads[self.index - 1]
        return _OpenAIResponse(payload, self.index)


class _OpenAIResponse:
    def __init__(self, payload: dict, index: int) -> None:
        self.payload = payload
        self.index = index

    def model_dump(self):
        return {
            "id": f"chatcmpl-phase62-fix-design-{self.index}",
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
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 200,
                "total_tokens": 300,
            },
        }


def _write_design_brief_trace_fixture(
    root: Path,
    call_index: int,
    transcript: list[dict],
    brief: dict,
) -> None:
    runs = list((root / "runs").iterdir())
    assert len(runs) == 1
    call_dir = runs[0] / "calls" / f"{call_index:02d}-design-brief"
    call_dir.mkdir(parents=True, exist_ok=True)
    payloads = {
        "conversation.json": transcript,
        "context-selection.json": {"evidence": EVIDENCE, "few_shots": []},
        "request.redacted.json": {"model": "mimo-v2.5-pro"},
        "response.raw.json": {"id": f"msg_phase62_fix_{call_index}"},
        "design-brief.json": brief,
        "validation.json": {"valid": True, "issue_count": 0, "issues": []},
        "metrics.json": {"response_id": f"msg_phase62_fix_{call_index}"},
    }
    for name, payload in payloads.items():
        (call_dir / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    (call_dir / "prompt-rendered.md").write_text("<test design brief prompt>\n", encoding="utf-8")
    (call_dir / "model-text.txt").write_text(
        json.dumps(brief, ensure_ascii=False),
        encoding="utf-8",
    )
