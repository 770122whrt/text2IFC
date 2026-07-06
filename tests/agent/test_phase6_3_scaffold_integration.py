import json
from copy import deepcopy
from pathlib import Path

from text2ifc_agent.complex_scaffold import build_scaffold_candidate
from text2ifc_agent.expected_facts import build_expected_facts
import text2ifc_agent.interactive_cli_flow as interactive_flow
from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput
from text2ifc_agent.session_store import SessionStore

from tests.agent.test_phase6_3_complex_scaffold import (
    _complex_two_storey_nested_design_brief,
)


ROOT = Path(__file__).resolve().parents[2]
PHASE6_1_COMPLETE = ROOT / "dataset/processed/agent-demo/phase6.1-mimo-live/complete-room"


def test_ready_session_promotes_complex_scaffold_when_generator_omits_dynamic_facts(tmp_path):
    root = tmp_path / "phase6.3-scaffold-integration"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="complex two-storey scaffold integration")
    design_brief = _complex_two_storey_nested_design_brief()
    _write_ready_design_brief_call(session.run_dir, design_brief)
    store.mark_session_status(session.session_id, "ready")
    expected = build_expected_facts(
        case_id=session.session_hash,
        design_brief=design_brief,
    )
    incomplete_candidate = _dynamic_incomplete_candidate(
        build_scaffold_candidate(
            case_id=session.session_hash,
            design_brief=design_brief,
            expected_facts=expected,
        )
    )
    audit = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "accept",
        "blocking": False,
        "deterministic_gate_status": "passed",
        "findings": [],
        "evidence_paths": [
            "expected-facts.json",
            "scaffold/candidate.json",
            "gate-summary.json",
            "generator/candidate.json",
        ],
    }
    provider = _SequenceLiveProvider([incomplete_candidate, audit])

    result = run_ready_session_to_ifc(
        store=store,
        session=session.session_hash,
        provider_factory=lambda: provider,
    )

    assert result.status == "compiled"
    assert (session.run_dir / "scaffold" / "candidate.json").is_file()
    assert (session.run_dir / "scaffold" / "route.json").is_file()
    assert (session.run_dir / "generator" / "original-candidate-before-scaffold.json").is_file()
    gate_summary = json.loads(
        (session.run_dir / "gate-summary.json").read_text(encoding="utf-8")
    )
    route = json.loads((session.run_dir / "scaffold" / "route.json").read_text(encoding="utf-8"))
    assert gate_summary["overall_status"] == "passed"
    assert route["route"] == "scaffold_promoted"
    assert (session.run_dir / "output.ifc").is_file()
    store.close()


def test_ready_session_uses_complex_scaffold_when_generator_output_is_unparsed(tmp_path):
    root = tmp_path / "phase6.3-scaffold-invalid-generator"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="complex two-storey invalid generator")
    design_brief = _complex_two_storey_nested_design_brief()
    _write_ready_design_brief_call(session.run_dir, design_brief)
    store.mark_session_status(session.session_id, "ready")
    audit = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "accept",
        "blocking": False,
        "deterministic_gate_status": "passed",
        "findings": [],
        "evidence_paths": [
            "expected-facts.json",
            "scaffold/candidate.json",
            "generator/classification.json",
            "generator/original-validation-before-scaffold.json",
        ],
    }
    provider = _SequenceLiveProvider(['{"schema_version":"bim-json/2.0","entities":[340000?]}', audit])

    result = run_ready_session_to_ifc(
        store=store,
        session=session.session_hash,
        provider_factory=lambda: provider,
    )

    assert result.status == "compiled"
    assert (session.run_dir / "scaffold" / "candidate.json").is_file()
    assert (session.run_dir / "generator" / "original-validation-before-scaffold.json").is_file()
    route = json.loads((session.run_dir / "scaffold" / "route.json").read_text(encoding="utf-8"))
    generator_validation = json.loads(
        (session.run_dir / "generator" / "validation.json").read_text(encoding="utf-8")
    )
    assert route["route"] == "scaffold_promoted_from_generator_failure"
    assert generator_validation["valid"] is True
    assert (session.run_dir / "output.ifc").is_file()
    store.close()


def test_ready_session_uses_complex_scaffold_when_ready_generator_returns_draft(tmp_path):
    root = tmp_path / "phase6.3-scaffold-draft-generator"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="complex two-storey draft generator")
    design_brief = _complex_two_storey_nested_design_brief()
    _write_ready_design_brief_call(session.run_dir, design_brief)
    store.mark_session_status(session.session_id, "ready")
    draft = {
        "draft_version": "bim-json-draft/1.0",
        "target_schema_version": "bim-json/2.0",
        "missing_facts": [
            {
                "code": "not_generated",
                "entity_id": "wall-1",
                "message": "generator omitted formal geometry already represented in Design Brief",
                "path": "/walls",
            }
        ],
        "partial_document": {
            "schema_version": "bim-json/2.0",
            "ifc_schema": "IFC2X3",
            "units": {"length": "MILLIMETRE"},
            "entities": [],
            "relationships": [],
        },
        "clarification_targets": [],
        "losses": [],
        "provenance": {"source": "unit-test"},
    }
    audit = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "accept",
        "blocking": False,
        "deterministic_gate_status": "passed",
        "findings": [],
        "evidence_paths": [
            "expected-facts.json",
            "scaffold/candidate.json",
            "generator/original-classification-before-scaffold.json",
        ],
    }
    provider = _SequenceLiveProvider([draft, audit])

    result = run_ready_session_to_ifc(
        store=store,
        session=session.session_hash,
        provider_factory=lambda: provider,
    )

    assert result.status == "compiled"
    route = json.loads((session.run_dir / "scaffold" / "route.json").read_text(encoding="utf-8"))
    assert route["route"] == "scaffold_promoted_from_generator_failure"
    assert (session.run_dir / "generator" / "draft.json").is_file()
    assert (session.run_dir / "generator" / "candidate.json").is_file()
    store.close()


def test_ready_session_promotes_complex_scaffold_after_geometry_audit_block(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "phase6.3-scaffold-geometry-recovery"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="complex two-storey geometry recovery")
    design_brief = _complex_two_storey_nested_design_brief()
    _write_ready_design_brief_call(session.run_dir, design_brief)
    store.mark_session_status(session.session_id, "ready")
    expected = build_expected_facts(
        case_id=session.session_hash,
        design_brief=design_brief,
    )
    malformed_candidate = _geometry_mismatched_candidate(
        build_scaffold_candidate(
            case_id=session.session_hash,
            design_brief=design_brief,
            expected_facts=expected,
        )
    )
    audit_block = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "revise",
        "blocking": True,
        "deterministic_gate_status": "failed",
        "findings": [
            {
                "code": "ROOM_ENCLOSURE_OPEN",
                "message": "几何门禁显示墙体闭合失败，需要重建几何候选。",
                "path": "/geometry",
            }
        ],
        "evidence_paths": [
            "geometry-feedback.json",
            "gate-summary.json",
            "generator/candidate.json",
        ],
    }
    audit_accept = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "accept",
        "blocking": False,
        "deterministic_gate_status": "passed",
        "findings": [],
        "evidence_paths": [
            "expected-facts.json",
            "scaffold/candidate.json",
            "geometry-feedback.json",
            "gate-summary.json",
        ],
    }
    provider = _SequenceLiveProvider([malformed_candidate, audit_block, audit_accept])
    original_gate_stage = interactive_flow.run_candidate_gate_stage
    gate_calls = {"count": 0}

    def gate_stage_with_first_geometry_failure(*, case_dir, output_dir, case_id):
        result = original_gate_stage(
            case_dir=case_dir,
            output_dir=output_dir,
            case_id=case_id,
        )
        gate_calls["count"] += 1
        if gate_calls["count"] == 1:
            geometry_feedback = {
                "success": False,
                "issues": [
                    {
                        "code": "WALL_BBOX_MISMATCH",
                        "message": "unit test injected wall bbox mismatch",
                        "path": "/walls/storey-2-wall-north/bbox",
                    },
                    {
                        "code": "ROOM_ENCLOSURE_OPEN",
                        "message": "unit test injected open enclosure",
                        "path": "/walls",
                    },
                ],
                "metrics": {},
                "expectation_source": "unit-test",
            }
            (Path(output_dir) / "geometry-feedback.json").write_text(
                json.dumps(geometry_feedback, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            return {
                **result,
                "valid": False,
                "geometry_success": False,
                "geometry_feedback": geometry_feedback,
            }
        return result

    monkeypatch.setattr(
        interactive_flow,
        "run_candidate_gate_stage",
        gate_stage_with_first_geometry_failure,
    )

    result = run_ready_session_to_ifc(
        store=store,
        session=session.session_hash,
        provider_factory=lambda: provider,
    )

    assert result.status == "compiled"
    assert result.audit_status == "accepted"
    route = json.loads((session.run_dir / "scaffold" / "route.json").read_text(encoding="utf-8"))
    gate_summary = json.loads(
        (session.run_dir / "gate-summary.json").read_text(encoding="utf-8")
    )
    assert route["route"] == "scaffold_promoted_from_geometry_audit"
    assert "ROOM_ENCLOSURE_OPEN" in route["source_issue_codes"]
    assert gate_summary["overall_status"] == "passed"
    assert (session.run_dir / "generator" / "original-candidate-before-scaffold.json").is_file()
    assert (session.run_dir / "output.ifc").is_file()
    store.close()


def _dynamic_incomplete_candidate(candidate: dict) -> dict:
    result = deepcopy(candidate)
    removed_ids = {
        entity["id"]
        for entity in result["entities"]
        if entity["ifc_class"] == "IfcDoor" and entity["id"].startswith("door-second-floor")
    }
    removed_ids.update(
        entity["id"]
        for entity in result["entities"]
        if entity["ifc_class"] == "IfcOpeningElement"
        and any(entity["id"] == f"opening-{door_id}" for door_id in removed_ids)
    )
    result["entities"] = [
        entity for entity in result["entities"] if entity["id"] not in removed_ids
    ]
    result["relationships"] = [
        relationship
        for relationship in result["relationships"]
        if not _references_removed_or_window_fill(relationship, removed_ids)
    ]
    return result


def _geometry_mismatched_candidate(candidate: dict) -> dict:
    result = deepcopy(candidate)
    for entity in result["entities"]:
        if entity.get("id") == "storey-2-wall-north":
            placement = entity["attributes"]["ObjectPlacement"]
            placement["origin"] = [
                placement["origin"][0],
                placement["origin"][1] - 750,
                placement["origin"][2],
            ]
            break
    return result


def _references_removed_or_window_fill(
    relationship: dict,
    removed_ids: set[str],
) -> bool:
    attributes = relationship.get("attributes", {})
    if any(value in removed_ids for value in attributes.values()):
        return True
    if relationship["ifc_class"] == "IfcRelFillsElement":
        return str(attributes.get("RelatedBuildingElement", "")).startswith("window-")
    if relationship["ifc_class"] == "IfcRelVoidsElement":
        return str(attributes.get("RelatedOpeningElement", "")).startswith("opening-window-")
    return False


def _write_ready_design_brief_call(run_dir: Path, design_brief: dict) -> None:
    call_dir = run_dir / "calls" / "01-design-brief"
    call_dir.mkdir(parents=True)
    for source in (PHASE6_1_COMPLETE / "design-brief").iterdir():
        if source.is_file():
            (call_dir / source.name).write_text(
                source.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
    (call_dir / "design-brief.json").write_text(
        json.dumps(design_brief, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class _SequenceLiveProvider:
    def __init__(self, payloads: list[dict]) -> None:
        self.payloads = list(payloads)
        self.call_count = 0

    def generate_live(self, *, session_id, prompt, schema, state):
        del prompt, schema, state
        self.call_count += 1
        payload = self.payloads.pop(0)
        text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        response = {
            "id": f"msg_phase63_scaffold_{self.call_count}",
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
