import json
from copy import deepcopy
from pathlib import Path

from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput
from text2ifc_agent.session_store import SessionStore


ROOT = Path(__file__).resolve().parents[2]
PHASE6_1_COMPLETE = (
    ROOT / "dataset/processed/agent-demo/phase6.1-mimo-live/complete-room"
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
            "id": f"msg_phase62_{index + 1}",
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


def test_ready_phase6_2_session_generates_ifc_report_and_db_artifacts(tmp_path):
    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(
        original_input=(
            "创建一个长6米、宽4米、高3米的房间，南墙中间有一扇900mm宽、"
            "2100mm高的门，北墙中间有一扇1200mm宽、1500mm高、窗台900mm高的窗。"
            "墙体厚度为300mm。"
        )
    )
    _write_ready_design_brief_call(session.run_dir)
    store.mark_session_status(session.session_id, "ready")

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

    result = run_ready_session_to_ifc(
        store=store,
        session=session.session_hash,
        provider_factory=lambda: provider,
    )
    export = store.session_export_payload(session.session_hash)

    assert result.status == "compiled"
    assert result.session_hash == session.session_hash
    assert provider.session_ids == [
        f"phase6.2-{session.session_hash}-generator-01",
        f"phase6.2-{session.session_hash}-audit-01",
    ]
    assert (session.run_dir / "candidate.json").is_file()
    assert (session.run_dir / "output.ifc").is_file()
    assert (session.run_dir / "report.md").is_file()
    assert (session.run_dir / "semantic-coverage.json").is_file()
    assert (session.run_dir / "session-export.json").is_file()
    report = (session.run_dir / "report.md").read_text(encoding="utf-8")
    assert "## Semantic Coverage" in report
    assert "semantic-coverage.json" in report
    assert "semantic-capabilities.json" in report
    final_acceptance = json.loads((root / "final-acceptance.json").read_text(encoding="utf-8"))
    assert final_acceptance["session_hash"] == session.session_hash
    assert final_acceptance["artifacts"]["ifc"] == f"runs/{session.session_hash}/output.ifc"
    assert final_acceptance["artifacts"]["report"] == f"runs/{session.session_hash}/report.md"
    assert final_acceptance["artifacts"]["session_export"] == (
        f"runs/{session.session_hash}/session-export.json"
    )
    artifact_paths = {artifact["path"] for artifact in export["artifacts"]}
    assert f"runs/{session.session_hash}/candidate.json" in artifact_paths
    assert f"runs/{session.session_hash}/output.ifc" in artifact_paths
    assert f"runs/{session.session_hash}/report.md" in artifact_paths
    assert store.get_session(session.session_hash).status == "compiled"


def test_ready_session_applies_scoped_changeset_after_geometry_audit_revise(
    tmp_path, monkeypatch
):
    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="创建一个需要几何修复的矩形房间。")
    _write_ready_design_brief_call(session.run_dir)
    store.mark_session_status(session.session_id, "ready")

    regenerated_candidate = json.loads(
        (PHASE6_1_COMPLETE / "generator" / "candidate.json").read_text(
            encoding="utf-8"
        )
    )
    blocked_candidate = _geometry_blocked_candidate(regenerated_candidate)
    audit_revise = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "revise",
        "blocking": True,
        "deterministic_gate_status": "failed",
        "findings": [
            {
                "code": "GEOMETRY_TRUE_POSITIVE",
                "message": "东西墙方向错误，候选 BIM JSON 需要修复。",
                "evidence_path": "geometry-feedback.json",
            }
        ],
        "evidence_paths": [
            "design-brief/design-brief.json",
            "generator/candidate.json",
            "repair/route.json",
            "geometry-feedback.json",
        ],
    }
    audit_accept = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "accept",
        "blocking": False,
        "deterministic_gate_status": "passed",
        "findings": [],
        "evidence_paths": [
            "design-brief/design-brief.json",
            "generator/candidate.json",
            "repair/route.json",
            "geometry-feedback.json",
        ],
    }
    provider = _SequenceLiveProvider([blocked_candidate, audit_revise, audit_accept])
    scoped_calls = []

    def apply_scoped_round(**kwargs):
        scoped_calls.append(kwargs)
        return {
            "valid": True,
            "status": "applied",
            "candidate": regenerated_candidate,
            "revision": {
                "revision_id": "revision-01",
                "sequence": 1,
                "candidate_hash": "sha256:" + "1" * 64,
            },
            "preservation": {
                "unrelated_component_preservation_rate": 1.0,
                "forbidden_drift_ids": [],
            },
            "issues": [],
            "scope": {"scope_id": "scope-revision-01"},
            "stage": {
                "status": "changeset",
                "classification": "changeset",
                "response_id": "msg_changeset_1",
            },
        }

    monkeypatch.setattr(
        "text2ifc_agent.interactive_cli_flow.run_scoped_changeset_round",
        apply_scoped_round,
    )

    result = run_ready_session_to_ifc(
        store=store,
        session=session.session_hash,
        provider_factory=lambda: provider,
    )

    assert result.status == "compiled"
    assert provider.session_ids == [
        f"phase6.2-{session.session_hash}-generator-01",
        f"phase6.2-{session.session_hash}-audit-01",
        f"phase6.2-{session.session_hash}-audit-02",
    ]
    assert len(scoped_calls) == 1
    assert scoped_calls[0]["round_number"] == 1
    assert scoped_calls[0]["issues"]
    assert not (session.run_dir / "generator-regeneration-01").exists()
    assert (session.run_dir / "candidate-revision.json").is_file()
    assert (session.run_dir / "generator-before-changesets" / "candidate.json").is_file()
    geometry = json.loads(
        (session.run_dir / "geometry-feedback.json").read_text(encoding="utf-8")
    )
    assert geometry["success"] is True
    assert (session.run_dir / "output.ifc").is_file()
    assert store.get_session(session.session_hash).status == "compiled"


def test_geometry_gate_failure_regenerates_when_audit_incorrectly_accepts(tmp_path):
    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(
        original_input="Create a rectangular room whose geometry must be checked."
    )
    _write_ready_design_brief_call(session.run_dir)
    store.mark_session_status(session.session_id, "ready")

    regenerated_candidate = json.loads(
        (PHASE6_1_COMPLETE / "generator" / "candidate.json").read_text(
            encoding="utf-8"
        )
    )
    blocked_candidate = _geometry_blocked_candidate(regenerated_candidate)
    incorrect_accept = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "accept",
        "blocking": False,
        "deterministic_gate_status": "passed",
        "findings": [],
        "evidence_paths": [
            "design-brief/design-brief.json",
            "generator/candidate.json",
            "repair/route.json",
            "geometry-feedback.json",
        ],
    }
    final_accept = deepcopy(incorrect_accept)
    provider = _SequenceLiveProvider(
        [blocked_candidate, incorrect_accept, regenerated_candidate, final_accept]
    )
    progress_events = []

    result = run_ready_session_to_ifc(
        store=store,
        session=session.session_hash,
        provider_factory=lambda: provider,
        progress=lambda stage, payload: progress_events.append((stage, payload)),
    )

    assert result.status == "compiled"
    assert provider.session_ids == [
        f"phase6.2-{session.session_hash}-generator-01",
        f"phase6.2-{session.session_hash}-audit-01",
        f"phase6.2-{session.session_hash}-generator-02",
        f"phase6.2-{session.session_hash}-audit-02",
    ]
    feedback = json.loads(
        (
            session.run_dir
            / "generator-regeneration-01"
            / "generation-feedback.json"
        ).read_text(encoding="utf-8")
    )
    assert feedback["route"] == "regenerate_json"
    assert any(
        issue["source"] == "geometry_gate" for issue in feedback["issues"]
    )
    gate_statuses = [
        payload["status"]
        for stage, payload in progress_events
        if stage == "candidate_gates" and payload.get("status") != "started"
    ]
    assert gate_statuses == ["failed", "passed"]


def test_geometry_feedback_allows_two_generator_regeneration_rounds(tmp_path):
    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="Create a checked rectangular room.")
    _write_ready_design_brief_call(session.run_dir)
    store.mark_session_status(session.session_id, "ready")

    valid_candidate = json.loads(
        (PHASE6_1_COMPLETE / "generator" / "candidate.json").read_text(
            encoding="utf-8"
        )
    )
    first_blocked = _geometry_blocked_candidate(valid_candidate)
    second_blocked = _geometry_blocked_candidate_one_wall(valid_candidate)
    audit_revise = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "revise",
        "blocking": True,
        "deterministic_gate_status": "failed",
        "findings": [],
        "evidence_paths": [
            "design-brief/design-brief.json",
            "generator/candidate.json",
            "repair/route.json",
            "geometry-feedback.json",
        ],
    }
    audit_accept = {
        **audit_revise,
        "recommendation": "accept",
        "blocking": False,
        "deterministic_gate_status": "passed",
    }
    provider = _SequenceLiveProvider(
        [
            first_blocked,
            audit_revise,
            second_blocked,
            audit_revise,
            valid_candidate,
            audit_accept,
        ]
    )

    result = run_ready_session_to_ifc(
        store=store,
        session=session.session_hash,
        provider_factory=lambda: provider,
    )

    assert result.status == "compiled"
    assert provider.session_ids == [
        f"phase6.2-{session.session_hash}-generator-01",
        f"phase6.2-{session.session_hash}-audit-01",
        f"phase6.2-{session.session_hash}-generator-02",
        f"phase6.2-{session.session_hash}-audit-02",
        f"phase6.2-{session.session_hash}-generator-03",
        f"phase6.2-{session.session_hash}-audit-03",
    ]
    rounds = json.loads(
        (session.run_dir / "feedback-rounds.json").read_text(encoding="utf-8")
    )["rounds"]
    assert [record["round_index"] for record in rounds] == [0, 1, 2]
    assert rounds[-1]["route"] == "accepted"
    assert (session.run_dir / "generator-regeneration-01").is_dir()
    assert (session.run_dir / "generator-regeneration-02").is_dir()
    assert (session.run_dir / "evaluation-rounds" / "round-01").is_dir()
    assert (session.run_dir / "evaluation-rounds" / "round-02").is_dir()
    assert (session.run_dir / "evaluation-rounds" / "round-03").is_dir()


def test_failed_dynamic_gate_cannot_be_overridden_by_audit_accept(
    tmp_path, monkeypatch
):
    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(
        original_input="Create a checked room with correctly oriented openings."
    )
    _write_ready_design_brief_call(session.run_dir)
    store.mark_session_status(session.session_id, "ready")

    def write_opening_expected_facts(*, case_dir, case_id, design_brief):
        del case_id, design_brief
        payload = {
            "schema_version": "text2ifc/expected-facts/1.0",
            "total_counts": {"IfcDoor": 1},
            "required_relationships": {"opening_fill": {"doors": 1}},
        }
        path = Path(case_dir) / "expected-facts.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    monkeypatch.setattr(
        "text2ifc_agent.interactive_cli_flow.write_expected_facts",
        write_opening_expected_facts,
    )

    valid_candidate = json.loads(
        (PHASE6_1_COMPLETE / "generator" / "candidate.json").read_text(
            encoding="utf-8"
        )
    )
    first_blocked = _geometry_blocked_candidate(valid_candidate)
    second_blocked = _opening_axis_blocked_candidate(valid_candidate)
    incorrect_accept = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "accept",
        "blocking": False,
        "deterministic_gate_status": "passed",
        "findings": [],
        "evidence_paths": [
            "design-brief/design-brief.json",
            "generator/candidate.json",
            "repair/route.json",
            "gate-summary.json",
        ],
    }
    provider = _SequenceLiveProvider(
        [
            first_blocked,
            incorrect_accept,
            second_blocked,
            incorrect_accept,
            valid_candidate,
            incorrect_accept,
        ]
    )

    result = run_ready_session_to_ifc(
        store=store,
        session=session.session_hash,
        provider_factory=lambda: provider,
    )

    assert result.status == "compiled"
    assert provider.session_ids == [
        f"phase6.2-{session.session_hash}-generator-01",
        f"phase6.2-{session.session_hash}-audit-01",
        f"phase6.2-{session.session_hash}-generator-02",
        f"phase6.2-{session.session_hash}-audit-02",
        f"phase6.2-{session.session_hash}-generator-03",
        f"phase6.2-{session.session_hash}-audit-03",
    ]
    gate_summary = json.loads(
        (session.run_dir / "gate-summary.json").read_text(encoding="utf-8")
    )
    assert gate_summary["overall_status"] == "passed"
    case_result = json.loads(
        (session.run_dir / "case-result.json").read_text(encoding="utf-8")
    )
    assert case_result["deterministic_gates_passed"] is True


def test_phase6_2_cli_resumes_ready_session_to_ifc(tmp_path, capsys):
    from scripts.agent import run_phase6_2_cli

    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="创建一个完整的测试房间。")
    _write_ready_design_brief_call(session.run_dir)
    store.mark_session_status(session.session_id, "ready")
    store.close()

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

    exit_code = run_phase6_2_cli.main(
        [
            "--live",
            "--stop-after",
            "ifc",
            "--resume",
            session.session_hash,
            "--output-root",
            str(root),
            "--db",
            str(root / "sessions.sqlite"),
        ],
        live_provider_factory=lambda: provider,
    )
    summary = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert summary["status"] == "compiled"
    assert summary["session_hash"] == session.session_hash
    assert (session.run_dir / "output.ifc").is_file()
    assert (session.run_dir / "report.md").is_file()


def test_ready_session_stops_cleanly_when_generator_returns_draft(tmp_path):
    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="Create a building that remains draft.")
    _write_ready_design_brief_call(session.run_dir)
    store.mark_session_status(session.session_id, "ready")

    draft = {
        "draft_version": "bim-json-draft/1.0",
        "target_schema_version": "bim-json/2.0",
        "partial_document": {
            "schema_version": "bim-json/2.0",
            "ifc_schema": "IFC2X3",
            "units": {"length": "MILLIMETRE"},
            "entities": [],
            "relationships": [],
        },
        "missing_facts": [
            {
                "entity_id": "space",
                "path": "/entities",
                "code": "MISSING_IFCSPACE",
                "message": "No spaces defined.",
            }
        ],
        "losses": [],
        "clarification_targets": [],
        "provenance": {"source": "unit-test"},
    }
    provider = _SequenceLiveProvider([draft])

    result = run_ready_session_to_ifc(
        store=store,
        session=session.session_hash,
        provider_factory=lambda: provider,
    )

    assert result.status == "draft_or_blocked"
    assert result.generator_status == "draft"
    assert result.audit_status == "not_run"
    assert result.ifc_path is None
    assert not (session.run_dir / "output.ifc").exists()
    assert (session.run_dir / "issues.json").is_file()
    assert (session.run_dir / "route-decision.json").is_file()
    assert (session.run_dir / "feedback-rounds.json").is_file()
    assert store.get_session(session.session_hash).status == "draft_or_blocked"


def _geometry_blocked_candidate(candidate: dict) -> dict:
    candidate = deepcopy(candidate)
    for entity in candidate["entities"]:
        if entity.get("id") in {"wall-west", "wall-east"}:
            profile = entity["attributes"]["Representation"]["profile"]
            profile["x"] = 300
            profile["y"] = 4000
    return candidate


def _geometry_blocked_candidate_one_wall(candidate: dict) -> dict:
    candidate = deepcopy(candidate)
    for entity in candidate["entities"]:
        if entity.get("id") == "wall-west":
            profile = entity["attributes"]["Representation"]["profile"]
            profile["x"] = 300
            profile["y"] = 4000
    return candidate


def _opening_axis_blocked_candidate(candidate: dict) -> dict:
    candidate = deepcopy(candidate)
    opening = next(
        entity
        for entity in candidate["entities"]
        if entity.get("ifc_class") == "IfcOpeningElement"
    )
    representation = opening["attributes"]["Representation"]
    representation["profile"]["y"] = 2100
    representation["depth"] = 200
    return candidate


def _write_ready_design_brief_call(run_dir: Path) -> None:
    call_dir = run_dir / "calls" / "01-design-brief"
    call_dir.mkdir(parents=True)
    for source in (PHASE6_1_COMPLETE / "design-brief").iterdir():
        if source.is_file():
            (call_dir / source.name).write_text(
                source.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
    for name in ("conversation.json", "context-selection.json", "design-brief.json"):
        (call_dir / name).write_text(
            (PHASE6_1_COMPLETE / "design-brief" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    (run_dir / "design-brief.json").write_text(
        (call_dir / "design-brief.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
