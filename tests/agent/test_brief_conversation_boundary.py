"""Reject impossible source citations before paying for any Provider call."""
import copy
import json
from types import SimpleNamespace

import pytest

from text2ifc_agent.generation_budget import GenerationBudget, BudgetedProvider
from text2ifc_agent.live_pipeline import run_design_brief_stage
from text2ifc_agent.interactive_cli_flow import make_openai_design_brief_invoker
from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config
from tests.agent.test_phase6_5_staged_generation import SequenceProvider


def turns():
    return [{"turn_id": "source-A", "role": "user", "content": "创建教学空间。"}]


def invalid(kind):
    rows = turns()
    if kind == "missing": rows[0].pop("turn_id")
    elif kind == "blank": rows[0]["turn_id"] = " "
    elif kind == "numeric": rows[0]["turn_id"] = 1
    elif kind == "duplicate": rows.append(copy.deepcopy(rows[0]))
    elif kind == "cross_role_duplicate": rows.append({**rows[0], "role": "assistant"})
    elif kind == "no_user": rows[0]["role"] = "assistant"
    elif kind == "bad_role": rows[0]["role"] = "system"
    elif kind == "bad_content": rows[0]["content"] = {"not": "text"}
    elif kind == "empty": rows = []
    elif kind == "bad_record": rows.append(None)
    return rows


def invoke(entry, rows, tmp_path, provider):
    case = dict(case_id="boundary", user_request="创建教学空间。", conversation=rows)
    if entry == "stage":
        return run_design_brief_stage(provider=provider, output_dir=tmp_path / "brief", case=case,
                                      design_brief_schema_version="text2ifc/design-brief/2.4")
    if entry == "cli":
        config = load_openai_compatible_runtime_config({"TEXT2IFC_PROVIDER": "deepseek", "API_KEY": "offline-test",
            "OPENAI_BASE_URL": "https://example.invalid", "TEXT2IFC_DEEPSEEK_MODEL": "fake"})
        def forbidden(**kwargs):
            raise AssertionError("invalid transcript reached transport")
        return make_openai_design_brief_invoker(config=config, run_dir=tmp_path,
            client_factory=lambda **_: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=forbidden))))(rows, 1)
    from tests.agent.test_semantic_authority_completeness import valid_brief
    _, brief = valid_brief()
    brief["schema_version"] = "text2ifc/design-brief/2.4"
    if entry == "semantic_repair":
        from text2ifc_agent.brief_semantic_repair import repair_semantic_brief as repair
    else:
        from text2ifc_agent.brief_plan_repair import repair_plan_brief as repair
    return repair(provider=provider, output_dir=tmp_path / "repair", brief=brief,
                  case=case, evidence_catalog=[], session_id="boundary")


@pytest.mark.parametrize("entry", ["stage", "cli", "semantic_repair", "plan_repair"])
@pytest.mark.parametrize("kind", ["missing", "blank", "numeric", "duplicate", "cross_role_duplicate",
                                  "no_user", "bad_role", "bad_content", "empty", "bad_record"])
def test_invalid_transcript_stops_before_transport_and_budget(tmp_path, entry, kind):
    rows = invalid(kind); before = copy.deepcopy(rows)
    raw = SequenceProvider([{"invalid": True}]); budget = GenerationBudget(tmp_path)
    with pytest.raises(ValueError, match="DESIGN_BRIEF_CONVERSATION_INVALID"):
        invoke(entry, rows, tmp_path, BudgetedProvider(raw, budget))
    assert raw.calls == []
    assert budget.snapshot()["calls_used"] == 0
    assert not list(tmp_path.rglob("design-brief.json"))
    assert not list(tmp_path.rglob("output.ifc"))
    assert rows == before


@pytest.mark.parametrize("version", ["2.0", "2.1", "2.2", "2.3", "2.4", "2.5"])
@pytest.mark.parametrize("multi", [False, True])
def test_valid_arbitrary_ids_reach_provider_without_renumbering(tmp_path, version, multi):
    rows = turns()
    if multi:
        rows += [{"turn_id": "question:9", "role": "assistant", "content": "墙厚？"},
                 {"turn_id": "answer:27", "role": "user", "content": "240毫米。"}]
    before = copy.deepcopy(rows)
    provider = SequenceProvider([{"invalid": True}])
    result = run_design_brief_stage(provider=provider, output_dir=tmp_path, case={
        "case_id": "other-scene", "user_request": rows[0]["content"], "conversation": rows},
        design_brief_schema_version="text2ifc/design-brief/" + version)
    assert len(provider.calls) == 1
    assert not result["valid"]
    assert json.loads((tmp_path / "conversation.json").read_text(encoding="utf-8")) == before == rows
