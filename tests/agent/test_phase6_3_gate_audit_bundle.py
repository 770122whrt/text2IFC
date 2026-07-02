import json
from pathlib import Path

from text2ifc_agent.gate_audit_bundle import (
    gate_summary_hash,
    hash_json_file,
    validate_gate_summary_binding,
    write_gate_summary,
)
from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput
from text2ifc_agent.session_store import SessionStore


ROOT = Path(__file__).resolve().parents[2]
PHASE6_1_COMPLETE = (
    ROOT / "dataset/processed/agent-demo/phase6.1-mimo-live/complete-room"
)


def test_gate_summary_binds_candidate_expected_facts_and_gate_evidence(tmp_path):
    case_dir = _write_gate_case(tmp_path)

    summary = write_gate_summary(case_dir=case_dir, case_id="gate-bundle")

    summary_path = case_dir / "gate-summary.json"
    assert summary_path.is_file()
    assert summary["schema_version"] == "text2ifc/gate-summary/1.0"
    assert summary["candidate_path"] == "generator/candidate.json"
    assert summary["candidate_hash"] == hash_json_file(
        case_dir / "generator" / "candidate.json"
    )
    assert summary["expected_facts_path"] == "expected-facts.json"
    assert summary["expected_facts_hash"] == hash_json_file(
        case_dir / "expected-facts.json"
    )
    assert summary["artifact_hashes"]["generator/candidate.json"] == summary[
        "candidate_hash"
    ]
    assert summary["artifact_hashes"]["expected-facts.json"] == summary[
        "expected_facts_hash"
    ]

    gates = {gate["name"]: gate for gate in summary["gates"]}
    assert gates["bim_json_validation"]["status"] == "passed"
    assert gates["semantic_coverage"]["status"] == "failed"
    assert gates["semantic_coverage"]["issue_codes"] == ["UNSUPPORTED_FACT"]
    assert gates["ifc_compile_reopen"]["status"] == "passed"
    assert gates["geometry"]["status"] == "failed"
    assert gates["geometry"]["issue_codes"] == ["ROOM_ENCLOSURE_OPEN"]
    assert summary["overall_status"] == "failed"


def test_gate_summary_binding_rejects_stale_candidate_hash(tmp_path):
    case_dir = _write_gate_case(tmp_path)
    summary = write_gate_summary(case_dir=case_dir, case_id="stale-bundle")
    _write_json(case_dir / "generator" / "candidate.json", {"changed": True})

    issues = validate_gate_summary_binding(case_dir=case_dir, summary=summary)

    assert issues == [
        {
            "code": "CANDIDATE_HASH_MISMATCH",
            "path": "/candidate_hash",
            "expected": hash_json_file(case_dir / "generator" / "candidate.json"),
            "actual": summary["candidate_hash"],
        }
    ]


def test_decisive_audit_prompt_receives_gate_summary_bundle(tmp_path):
    root = tmp_path / "phase6.3-gate-summary-flow"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="complete room fixture")
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
            "gate-summary.json",
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

    assert result.status == "compiled"
    gate_summary_path = session.run_dir / "gate-summary.json"
    assert gate_summary_path.is_file()
    prompt_inputs = json.loads(
        (session.run_dir / "audit" / "prompt-render-input.json").read_text(
            encoding="utf-8"
        )
    )
    assert prompt_inputs["GATE_SUMMARY"]["candidate_hash"] == hash_json_file(
        session.run_dir / "generator" / "candidate.json"
    )
    assert prompt_inputs["GATE_SUMMARY_HASH"] == gate_summary_hash(gate_summary_path)
    assert prompt_inputs["CANDIDATE_HASH"] == prompt_inputs["GATE_SUMMARY"][
        "candidate_hash"
    ]
    assert "gate-summary.json" in prompt_inputs["EVIDENCE_PATHS"]


def _write_gate_case(tmp_path: Path) -> Path:
    case_dir = tmp_path / "case"
    generator = case_dir / "generator"
    repair = case_dir / "repair"
    generator.mkdir(parents=True)
    repair.mkdir()
    _write_json(
        generator / "candidate.json",
        {
            "schema_version": "text2ifc/bim-json/2.0",
            "entities": [],
            "relationships": [],
        },
    )
    _write_json(generator / "validation.json", {"valid": True, "issues": []})
    _write_json(
        case_dir / "expected-facts.json",
        {
            "schema_version": "text2ifc/expected-facts/1.0",
            "storeys": [{"id": "storey-1"}],
        },
    )
    _write_json(
        case_dir / "semantic-coverage.json",
        {
            "valid": False,
            "blocking_facts": [
                {
                    "path": "/known_facts/door/opening_direction",
                    "coverage_state": "unsupported_draft",
                    "reason": "Unsupported fact.",
                }
            ],
        },
    )
    _write_json(case_dir / "ifc-verification.json", {"success": True, "input_issues": [], "ifc_issues": []})
    _write_json(
        case_dir / "geometry-feedback.json",
        {
            "success": False,
            "issues": [
                {
                    "code": "ROOM_ENCLOSURE_OPEN",
                    "path": "/spaces/space-1",
                    "message": "Room enclosure is open.",
                }
            ],
        },
    )
    _write_json(repair / "route.json", {"route": "no_repair_needed"})
    return case_dir


def _write_ready_design_brief_call(run_dir: Path) -> None:
    call_dir = run_dir / "calls" / "01-design-brief"
    design_dir = run_dir / "design-brief"
    call_dir.mkdir(parents=True)
    design_dir.mkdir(parents=True)
    for source in (PHASE6_1_COMPLETE / "design-brief").iterdir():
        if source.is_file():
            for target_dir in (call_dir, design_dir):
                (target_dir / source.name).write_text(
                    source.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
    (run_dir / "design-brief.json").write_text(
        (call_dir / "design-brief.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )


class _SequenceLiveProvider:
    def __init__(self, payloads: list[dict]) -> None:
        self.payloads = payloads
        self.call_count = 0

    def generate_live(self, *, session_id, prompt, schema, state):
        del prompt, schema, state
        self.call_count += 1
        payload = self.payloads.pop(0)
        text = json.dumps(payload, ensure_ascii=False)
        response = {
            "id": f"msg_phase63_gate_{self.call_count}",
            "type": "message",
            "role": "assistant",
            "model": "unit-test",
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": text}],
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }
        return LiveProviderResult(
            session_id=session_id,
            evidence_class="unit_test_fixture",
            http_status=200,
            request={
                "model": "unit-test",
                "max_tokens": 131072,
                "stream": True,
                "messages": [{"role": "user", "content": "<redacted-test-prompt>"}],
            },
            response=response,
            events=(),
            output=ProviderOutput(
                text=text,
                metadata={"provider": "unit-test", "session_id": session_id},
            ),
        )


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
