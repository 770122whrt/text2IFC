import json
from pathlib import Path

from scripts.agent import run_phase6_5_live_stability


def test_live_harness_config_check_is_redacted(tmp_path, monkeypatch):
    monkeypatch.setenv("API_KEY", "unit-secret-value")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://provider.invalid")
    monkeypatch.setenv("TEXT2IFC_DEEPSEEK_MODEL", "deepseek-test")
    output_root = tmp_path / "live"

    exit_code = run_phase6_5_live_stability.main(
        ["--check-config", "--output-root", str(output_root)]
    )

    assert exit_code == 0
    payload = json.loads((output_root / "config-check.json").read_text(encoding="utf-8"))
    assert payload["configured"] is True
    assert payload["provider"] == "deepseek-openai-compatible"
    assert payload["config"] == {"api_key": "[REDACTED]", "base_url": "[REDACTED]"}
    assert "unit-secret-value" not in json.dumps(payload)


def test_campaign_requires_independent_consecutive_real_sessions(tmp_path):
    statuses = iter(["compiled", "audit_blocked", "compiled", "compiled", "compiled"])

    def runner(*, case_name, run_index, run_root, **kwargs):
        del kwargs
        status = next(statuses)
        session_hash = f"{case_name}-{run_index:02d}"
        case_dir = run_root / "runs" / session_hash
        case_dir.mkdir(parents=True)
        if status == "compiled":
            (case_dir / "output.ifc").write_text("ISO-10303-21;", encoding="ascii")
            (case_dir / "report.md").write_text("# report\n", encoding="utf-8")
        return {
            "session_hash": session_hash,
            "status": status,
            "provider": "deepseek-openai-compatible",
            "evidence_class": "real_provider",
            "response_ids": [f"response-{run_index}"],
            "usage": [{"total_tokens": 1}],
            "preservation_rate": 1.0,
            "bounded_rounds": 1,
            "gates_passed": status == "compiled",
            "artifacts": {
                "ifc": f"runs/{session_hash}/output.ifc" if status == "compiled" else "",
                "report": f"runs/{session_hash}/report.md" if status == "compiled" else "",
            },
        }

    result = run_phase6_5_live_stability.run_campaign(
        output_root=tmp_path / "campaign",
        case_name="two-storey",
        run_limit=5,
        required_consecutive=3,
        workflow_runner=runner,
    )

    assert result["run_count"] == 5
    assert result["accepted_count"] == 4
    assert result["max_consecutive_accepted"] == 3
    assert result["stable"] is True
    assert len({row["session_hash"] for row in result["runs"]}) == 5
    assert (tmp_path / "campaign" / "stability-matrix.json").is_file()
    assert (tmp_path / "campaign" / "stability-report.md").is_file()


def test_live_harness_has_no_scripted_model_answer_option():
    parser = run_phase6_5_live_stability.build_parser()
    option_strings = {
        option
        for action in parser._actions
        for option in action.option_strings
    }
    assert "--case" in option_strings
    assert "--runs" in option_strings
    assert "--env-file" in option_strings
    assert "--output-root" in option_strings
    assert "--timeout-seconds" in option_strings
    assert "--trace-level" in option_strings
    assert "--scripted-stdin" not in option_strings
    assert "--answers-json" not in option_strings


def test_live_harness_exposes_graded_cases_with_single_run_defaults():
    parser = run_phase6_5_live_stability.build_parser()
    case_action = next(action for action in parser._actions if action.dest == "case")

    assert {"easy", "medium", "hard"} <= set(case_action.choices)
    args = parser.parse_args(["--case", "medium"])
    assert args.runs == 1
    assert args.required_consecutive == 1


def test_graded_cases_resolve_to_distinct_fixture_files():
    assert run_phase6_5_live_stability.case_fixture_path("easy").name == "two-storey-case.json"
    assert run_phase6_5_live_stability.case_fixture_path("medium").name == (
        "medium-two-storey-l-shape.json"
    )
    assert run_phase6_5_live_stability.case_fixture_path("hard").name == (
        "hard-three-storey-l-shape.json"
    )


def test_medium_case_is_a_two_storey_l_shape_without_prewritten_model_output():
    payload = json.loads(
        run_phase6_5_live_stability.case_fixture_path("medium").read_text(
            encoding="utf-8"
        )
    )
    text = payload["input"]

    assert payload["difficulty"] == "medium"
    assert payload["storey_count"] == 2
    assert payload["expected_minimums"]["IfcSpace"] >= 9
    assert payload["expected_minimums"]["IfcWall"] >= 20
    assert "L 形" in text
    assert "storey-1-wall-notch-horizontal" in text
    assert "storey-2-wall-notch-vertical" in text
    assert "opening-medium-stair" in text
    assert "20 级" in text
    assert "踢面高 150" in text
    assert "踏面进深 170" in text
    assert "design_brief" not in payload
    assert "model_output" not in payload


def test_medium_case_uses_half_wall_thickness_for_perimeter_clear_bounds():
    payload = json.loads(
        run_phase6_5_live_stability.case_fixture_path("medium").read_text(
            encoding="utf-8"
        )
    )
    text = payload["input"]

    assert "space-1-reception bounds x=100..3000,y=100..4000" in text
    assert "space-1-office-north bounds x=100..3000,y=4000..7900" in text
    assert "space-1-service-north bounds x=5800..9900,y=2400..4900" in text
    assert "space-2-office-south bounds x=100..3800,y=100..4000" in text
    assert "space-2-office-north bounds x=100..3800,y=4000..7900" in text
    assert "space-2-east-north bounds x=5800..9900,y=2400..4900" in text


def test_hard_case_is_three_storey_with_two_stair_systems_and_no_model_output():
    payload = json.loads(
        run_phase6_5_live_stability.case_fixture_path("hard").read_text(
            encoding="utf-8"
        )
    )
    text = payload["input"]

    assert payload["difficulty"] == "hard"
    assert payload["storey_count"] == 3
    assert payload["expected_minimums"]["IfcSpace"] >= 16
    assert payload["expected_minimums"]["IfcWall"] >= 40
    assert payload["expected_minimums"]["IfcDoor"] >= 12
    assert payload["expected_minimums"]["IfcWindow"] >= 9
    assert payload["expected_minimums"]["IfcStair"] == 2
    assert payload["expected_minimums"]["IfcStairFlight"] == 2
    assert "storey-1 基准标高 0" in text
    assert "storey-2 基准标高 3150" in text
    assert "storey-3 基准标高 6500" in text
    assert "首层墙体 Z=0..3000" in text
    assert "二层墙体 Z=3150..6350" in text
    assert "三层墙体 Z=6500..9500" in text
    assert "slab-storey-2 Z=3000..3150" in text
    assert "slab-storey-3 Z=6350..6500" in text
    assert "roof-hard Z=9500..9650" in text
    assert "所有外墙、内墙和楼梯核心边界墙的厚度均为 200" in text
    assert "stair-hard-1-2" in text
    assert "stair-hard-2-3" in text
    assert "opening-hard-stair-1-2" in text
    assert "opening-hard-stair-2-3" in text
    assert "storey-3-wall-notch-horizontal" in text
    assert "wall-3-office-north-shaft" in text
    assert "design_brief" not in payload
    assert "model_output" not in payload
