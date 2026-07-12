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
