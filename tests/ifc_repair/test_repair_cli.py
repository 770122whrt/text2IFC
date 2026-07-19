from __future__ import annotations

import importlib
import io
import json
from pathlib import Path

import pytest

from text2ifc_ifc_repair.run_models import (
    Clarification,
    ClarificationCandidate,
    RunResult,
    RunStage,
)


def _cli():
    try:
        return importlib.import_module("text2ifc_ifc_repair.cli")
    except ModuleNotFoundError:
        pytest.fail("Phase 9 public repair CLI is not implemented")


def _clarification(run_id: str = "repair-cli-fixture") -> Clarification:
    return Clarification(
        clarification_id="clarify-001",
        run_id=run_id,
        state_version=4,
        operation_id="intent-001",
        stage=RunStage.TARGETS_RESOLVED,
        resume_stage=RunStage.INTENT_READY,
        reason_code="ambiguous_target",
        question="请选择需要修复的窗。",
        answer_modes=("select_candidate", "add_detail", "cancel"),
        candidates=(
            ClarificationCandidate(
                token="candidate-east",
                public_id="2cXV28XOjE6f6irgi0CO4t",
                ifc_class="IfcWindow",
                name="二层东侧外窗",
                storey="Level 2",
                position="east facade",
                evidence=("name:二层东侧外窗", "storey:Level 2"),
            ),
        ),
    )


def _result(status: str, *, clarification: Clarification | None = None) -> RunResult:
    success = status == "succeeded"
    return RunResult(
        run_id="repair-cli-fixture",
        state_version=4 if clarification else 9,
        status=status,
        reason_code=clarification.reason_code if clarification else None,
        complete_repair_success=success,
        successful_artifact_publishable=success,
        run_directory="runs/repair-cli-fixture",
        artifacts={
            "manifest": "manifest.json",
            "evaluation": "evaluation/public-evaluation.json",
            **({"successful_ifc": "artifacts/repaired.ifc"} if success else {}),
        },
        clarification=clarification,
    )


class FakeAPI:
    def __init__(self, first: RunResult, resumed: RunResult | None = None) -> None:
        self.first = first
        self.resumed = resumed or first
        self.calls: list[tuple[str, object]] = []

    def start(self, source_ifc_path: Path, repair_text: str, *, run_id=None):
        self.calls.append(("start", (Path(source_ifc_path), repair_text, run_id)))
        return self.first

    def continue_with_answer(self, run_id: str, answer: dict[str, object]):
        self.calls.append(("continue", (run_id, answer)))
        return self.resumed

    def read_result(self, run_id: str):
        self.calls.append(("result", run_id))
        return self.first


def _run(api: FakeAPI, argv: list[str], stdin: str = ""):
    stdout, stderr = io.StringIO(), io.StringIO()
    code = _cli().main(
        argv,
        api_factory=lambda _root: api,
        input_stream=io.StringIO(stdin),
        output_stream=stdout,
        error_stream=stderr,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def test_json_is_one_compact_versioned_bounded_envelope(tmp_path: Path) -> None:
    api = FakeAPI(_result("succeeded"))
    source = tmp_path / "caller.ifc"
    source.write_text("caller-owned", encoding="utf-8")

    code, stdout, stderr = _run(
        api,
        ["start", str(source), "--request", "修复东侧外窗", "--output-root", str(tmp_path / "out"), "--json"],
    )

    assert code == 0 and stderr == ""
    assert stdout.count("\n") == 1
    payload = json.loads(stdout)
    assert payload == _result("succeeded").to_dict()
    assert len(stdout.encode("utf-8")) < 16 * 1024
    assert "provider_secret" not in stdout.casefold()
    assert "ISO-10303-21" not in stdout


def test_non_interactive_returns_the_same_clarification_without_reading_stdin(tmp_path: Path) -> None:
    clarification = _clarification()
    api = FakeAPI(_result("clarification_required", clarification=clarification))
    source = tmp_path / "caller.ifc"
    source.write_text("caller-owned", encoding="utf-8")

    class ForbiddenInput(io.StringIO):
        def readline(self, *args, **kwargs):
            raise AssertionError("--non-interactive must not read stdin")

    stdout, stderr = io.StringIO(), io.StringIO()
    code = _cli().main(
        ["start", str(source), "--request", "修复外窗", "--output-root", str(tmp_path / "out"), "--non-interactive", "--json"],
        api_factory=lambda _root: api,
        input_stream=ForbiddenInput(),
        output_stream=stdout,
        error_stream=stderr,
    )

    assert code == 2 and stderr.getvalue() == ""
    assert json.loads(stdout.getvalue())["clarification"] == clarification.to_dict()
    assert [name for name, _ in api.calls] == ["start"]


def test_interactive_candidate_selection_resumes_the_same_run(tmp_path: Path) -> None:
    api = FakeAPI(
        _result("clarification_required", clarification=_clarification()),
        _result("succeeded"),
    )
    source = tmp_path / "caller.ifc"
    source.write_text("caller-owned", encoding="utf-8")

    code, stdout, stderr = _run(
        api,
        ["start", str(source), "--request", "修复外窗", "--output-root", str(tmp_path / "out")],
        stdin="1\n",
    )

    assert code == 0 and stderr == ""
    assert "IfcWindow" in stdout and "Level 2" in stdout and "east facade" in stdout
    assert "2cXV28XOjE6f6irgi0CO4t" in stdout and "name:二层东侧外窗" in stdout
    assert api.calls[-1] == (
        "continue",
        ("repair-cli-fixture", {"kind": "select_candidate", "candidate_token": "candidate-east"}),
    )


@pytest.mark.parametrize(("stdin", "kind"), [("取消\n", "cancel"), ("", "eof")])
def test_cancel_and_eof_fail_safe_without_selecting_a_target(tmp_path: Path, stdin: str, kind: str) -> None:
    api = FakeAPI(
        _result("clarification_required", clarification=_clarification()),
        _result("cancelled"),
    )
    source = tmp_path / "caller.ifc"
    source.write_text("caller-owned", encoding="utf-8")

    code, stdout, stderr = _run(
        api,
        ["start", str(source), "--request", "修复外窗", "--output-root", str(tmp_path / "out")],
        stdin=stdin,
    )

    assert code == 8 and stderr == ""
    assert api.calls[-1] == ("continue", ("repair-cli-fixture", {"kind": kind}))
    assert "candidate-east" not in repr(api.calls[-1][1][1])


def test_continue_and_result_are_thin_api_calls(tmp_path: Path) -> None:
    api = FakeAPI(_result("succeeded"))
    answer = json.dumps({"kind": "add_detail", "detail": "东侧"}, ensure_ascii=False)
    continue_code, _, _ = _run(api, ["continue", "repair-cli-fixture", "--answer", answer, "--output-root", str(tmp_path)])
    result_code, _, _ = _run(api, ["result", "repair-cli-fixture", "--output-root", str(tmp_path)])

    assert continue_code == result_code == 0
    assert api.calls == [
        ("continue", ("repair-cli-fixture", {"kind": "add_detail", "detail": "东侧"})),
        ("result", "repair-cli-fixture"),
    ]


@pytest.mark.parametrize(
    ("status", "exit_code"),
    [
        ("succeeded", 0),
        ("clarification_required", 2),
        ("invalid_input", 3),
        ("unsupported", 3),
        ("provider_failed", 4),
        ("audit_failed", 5),
        ("application_failed", 5),
        ("not_publishable", 6),
        ("cancelled", 8),
    ],
)
def test_terminal_status_exit_classes_are_stable(tmp_path: Path, status: str, exit_code: int) -> None:
    clarification = _clarification() if status == "clarification_required" else None
    api = FakeAPI(_result(status, clarification=clarification))
    code, _, _ = _run(api, ["result", "repair-cli-fixture", "--output-root", str(tmp_path), "--non-interactive"])
    assert code == exit_code


def test_quiet_suppresses_normal_output_and_human_mode_is_concise(tmp_path: Path) -> None:
    quiet_api = FakeAPI(_result("succeeded"))
    code, stdout, stderr = _run(quiet_api, ["result", "repair-cli-fixture", "--output-root", str(tmp_path), "--quiet"])
    assert code == 0 and stdout == stderr == ""

    human_api = FakeAPI(_result("succeeded"))
    code, stdout, stderr = _run(human_api, ["result", "repair-cli-fixture", "--output-root", str(tmp_path)])
    assert code == 0 and stderr == ""
    assert "状态: succeeded" in stdout and "manifest.json" in stdout
    assert len(stdout.splitlines()) <= 12


def test_cli_source_contains_no_duplicate_pipeline_authority() -> None:
    module = _cli()
    source = Path(module.__file__).read_text(encoding="utf-8")
    forbidden = (
        "build_ifc_index",
        "generate_repair_intent",
        "generate_bound_changeset",
        "apply_changeset",
        "evaluate_production",
        "OpenAICompatibleLiveProvider",
        "Audit",
    )
    assert all(term not in source for term in forbidden)


def test_unknown_or_tampered_run_is_redacted_to_stderr(tmp_path: Path) -> None:
    class BrokenAPI(FakeAPI):
        def read_result(self, run_id: str):
            raise ValueError("RUN_TAMPER_DETECTED: provider_secret=do-not-print")

    code, stdout, stderr = _run(BrokenAPI(_result("invalid_input")), ["result", "repair-missing", "--output-root", str(tmp_path), "--json"])
    assert code == 7 and stdout == ""
    assert "RUN_TAMPER_DETECTED" in stderr
    assert "do-not-print" not in stderr and "provider_secret" not in stderr
