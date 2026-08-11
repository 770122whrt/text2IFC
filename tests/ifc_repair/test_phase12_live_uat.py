from __future__ import annotations

import importlib.util
import json
import subprocess
from collections import deque
from pathlib import Path
from typing import Any

import pytest

from text2ifc_agent.providers import LiveProviderResult, ProviderOutput


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/ifc_repair/run_phase12_live_uat.py"
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
PROFILE_PROMPT = json.dumps(
    {
        "selected_profiles": [
            {
                "profile_id": "beam.add",
                "profile_version": "0.1",
                "profile_hash": HASH_A,
            }
        ],
        "few_shots": [
            {
                "example_id": "beam.add.complete",
                "example_hash": HASH_B,
            }
        ],
    },
    sort_keys=True,
)


def _module():
    spec = importlib.util.spec_from_file_location("phase12_live", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _MockTransport:
    def __init__(self, responses: list[dict[str, Any]] | None = None) -> None:
        self.responses = deque(responses or [])
        self.calls: list[dict[str, Any]] = []

    def generate_live(
        self,
        *,
        session_id: str,
        prompt: str,
        schema: dict[str, Any],
        state: dict[str, Any],
    ) -> LiveProviderResult:
        self.calls.append(
            {
                "session_id": session_id,
                "prompt": prompt,
                "schema": schema,
                "state": state,
            }
        )
        response = self.responses.popleft()
        text = json.dumps(response["content"], ensure_ascii=False, sort_keys=True)
        metadata = {
            "provider": "mock-deepseek",
            "model": "mock-reasoner",
            "usage": {
                "prompt_tokens": response.get("prompt_tokens", 101),
                "completion_tokens": response.get("completion_tokens", 37),
                "total_tokens": response.get("total_tokens", 138),
            },
            "api_key": "SECRET-TRANSPORT-TOKEN",
        }
        raw_response = {
            "id": f"response-{len(self.calls)}",
            "model": "mock-reasoner",
            "usage": metadata["usage"],
            "content": text,
            "private_gold": "CANARY-PRIVATE-GOLD-12-13",
        }
        return LiveProviderResult(
            session_id=session_id,
            evidence_class="live",
            http_status=200,
            request={
                "model": "mock-reasoner",
                "prompt": prompt,
                "authorization": "Bearer SECRET-TRANSPORT-TOKEN",
            },
            response=raw_response,
            events=(
                {
                    "sequence": 0,
                    "event": "chat.completion",
                    "data": raw_response,
                },
            ),
            output=ProviderOutput(text=text, metadata=metadata),
        )


class _GreenCommandRunner:
    def __init__(self, *, fail: str | None = None, forge: str | None = None) -> None:
        self.fail = fail
        self.forge = forge
        self.calls: list[tuple[str, ...]] = []

    @staticmethod
    def _name(command: tuple[str, ...]) -> str:
        rendered = " ".join(command).replace("\\", "/")
        if "test_phase12_live_uat.py" in rendered:
            return "focused"
        if "run_phase12_offline.py" in rendered:
            return "offline"
        if "-m pytest tests/ifc_repair -q" in rendered:
            return "full-suite"
        if "-m compileall" in rendered:
            return "compile"
        if rendered.startswith("git diff --check"):
            return "diff"
        if "validate_success_cases.py" in rendered:
            return "proof"
        raise AssertionError(f"unexpected preflight command: {rendered}")

    def __call__(
        self,
        command: tuple[str, ...],
        *,
        cwd: Path,
    ) -> subprocess.CompletedProcess[str]:
        del cwd
        command = tuple(str(item) for item in command)
        self.calls.append(command)
        name = self._name(command)
        if name == self.fail:
            return subprocess.CompletedProcess(command, 9, "", f"{name} failed")
        if name == "offline" and self.forge != "offline":
            output = Path(command[command.index("--output-root") + 1])
            output.mkdir(parents=True, exist_ok=True)
            (output / "run-summary.json").write_text(
                json.dumps(
                    {
                        "schema_version": "text2ifc/phase12-offline-matrix/0.1",
                        "status": "passed",
                        "matrix_complete": True,
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
        if name == "proof":
            stdout = json.dumps(
                {
                    "schema_version": "text2ifc/ifc-repair-proof-validation/0.1",
                    "status": "passed",
                    "case_count": 22,
                    "operation_count": 57,
                    "checked_file_count": 361,
                    "reopened_ifc_count": 66,
                    "errors": [],
                },
                sort_keys=True,
            )
            if self.forge == "proof":
                stdout = '{"status":"passed"}'
            return subprocess.CompletedProcess(command, 0, stdout, "")
        return subprocess.CompletedProcess(command, 0, f"{name} passed", "")


def _proof_root(tmp_path: Path) -> Path:
    root = tmp_path / "proof"
    root.mkdir()
    (root / "manifest.json").write_text(
        json.dumps({"case_count": 22, "cases": []}, sort_keys=True),
        encoding="utf-8",
    )
    return root


def _case(module: Any, case_id: str, *, feedback: str | None = None):
    return module.LiveCase(
        case_id=case_id,
        request=f"public request for {case_id}",
        feedback=feedback,
    )


def _run(
    module: Any,
    tmp_path: Path,
    *,
    transport: _MockTransport,
    runner: _GreenCommandRunner,
    executor: Any,
    cases: tuple[Any, ...],
    evidence_mode: str = "live",
) -> dict[str, Any]:
    return module.run_live_uat(
        tmp_path / "run",
        transport_factory=lambda: transport,
        command_runner=runner,
        case_executor=executor,
        cases=cases,
        proof_root=_proof_root(tmp_path),
        evidence_mode=evidence_mode,
    )


@pytest.mark.parametrize(
    "failed_gate",
    ("focused", "offline", "full-suite", "compile", "diff", "proof"),
)
def test_each_failed_preflight_gate_blocks_transport(
    tmp_path: Path,
    failed_gate: str,
) -> None:
    module = _module()
    transport = _MockTransport()
    executor_called = False

    def executor(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal executor_called
        executor_called = True
        return {"status": "succeeded", "successful_artifact_publishable": True}

    result = _run(
        module,
        tmp_path,
        transport=transport,
        runner=_GreenCommandRunner(fail=failed_gate),
        executor=executor,
        cases=(_case(module, "complete"),),
    )

    assert result["status"] == "preflight_failed"
    assert result["preflight"]["status"] == "failed"
    assert result["transport_calls"] == 0
    assert transport.calls == []
    assert executor_called is False


@pytest.mark.parametrize("forged_gate", ("offline", "proof"))
def test_caller_claimed_green_without_machine_artifact_is_rejected(
    tmp_path: Path,
    forged_gate: str,
) -> None:
    module = _module()
    transport = _MockTransport()

    result = _run(
        module,
        tmp_path,
        transport=transport,
        runner=_GreenCommandRunner(forge=forged_gate),
        executor=lambda *_args: pytest.fail("executor must not run"),
        cases=(_case(module, "complete"),),
    )

    failed = {item["name"]: item for item in result["preflight"]["checks"]}
    assert result["status"] == "preflight_failed"
    assert failed[forged_gate]["status"] == "failed"
    assert failed[forged_gate]["exit_code"] == 0
    assert result["transport_calls"] == 0


@pytest.mark.parametrize(
    "evidence_mode",
    ("synthetic", "cached", "prerecorded", "hand-authored"),
)
def test_non_live_evidence_modes_are_blocking_and_never_touch_transport(
    tmp_path: Path,
    evidence_mode: str,
) -> None:
    module = _module()
    transport = _MockTransport()
    runner = _GreenCommandRunner()

    result = _run(
        module,
        tmp_path,
        transport=transport,
        runner=runner,
        executor=lambda *_args: pytest.fail("executor must not run"),
        cases=(_case(module, "complete"),),
        evidence_mode=evidence_mode,
    )

    assert result["status"] == "blocked"
    assert result["reason_code"] == "LIVE_EVIDENCE_MODE_REQUIRED"
    assert result["synthetic_fallback_used"] is False
    assert result["transport_calls"] == 0
    assert transport.calls == []
    assert runner.calls == []


def test_green_preflight_binds_commands_results_and_artifact_hashes(
    tmp_path: Path,
) -> None:
    module = _module()

    result = _run(
        module,
        tmp_path,
        transport=_MockTransport(),
        runner=_GreenCommandRunner(),
        executor=lambda *_args: {
            "status": "unsupported",
            "reason_code": "STRUCTURAL_PROFILE_UNSUPPORTED",
            "successful_artifact_publishable": False,
        },
        cases=(),
    )

    checks = result["preflight"]["checks"]
    assert [item["name"] for item in checks] == [
        "focused",
        "offline",
        "full-suite",
        "compile",
        "diff",
        "proof",
    ]
    assert all(item["status"] == "passed" for item in checks)
    assert all(item["command"] for item in checks)
    assert all(item["stdout_sha256"].startswith("sha256:") for item in checks)
    assert all(item["stderr_sha256"].startswith("sha256:") for item in checks)
    assert all(item["result_sha256"].startswith("sha256:") for item in checks)
    assert {item["name"] for item in checks if item["artifacts"]} >= {
        "offline",
        "proof",
    }
    for check in checks:
        for artifact in check["artifacts"]:
            assert artifact["sha256"].startswith("sha256:")
            assert artifact["size_bytes"] > 0


def test_complete_clarification_resume_and_program_guard_have_exact_lineage(
    tmp_path: Path,
) -> None:
    module = _module()
    transport = _MockTransport(
        [
            {"content": {"operations": [{"beam_start": [0, 0, 0]}]}},
            {"content": {"operations": [{"axis": {"start": {}, "end": {}}}]}},
            {"content": {"operations": [{"beam_axis": "noncanonical"}]}},
            {"content": {"operations": [{"parameters": {"axis": {}}}]}},
            {"content": {"classification": "clarification_required"}},
            {"content": {"classification": "repair_intent"}},
            {"content": {"schema_version": "canonical-draft"}},
            {"content": {"classification": "unsupported"}},
        ]
    )

    def call(
        provider: Any,
        *,
        stage: str,
        attempt: int,
        prompt: str,
    ) -> Any:
        return provider.generate_live(
            session_id=f"mock-{stage}",
            prompt=prompt,
            schema={"type": "object"},
            state={"stage": stage, "attempt": attempt},
        )

    def executor(case: Any, provider: Any, _case_root: Path) -> dict[str, Any]:
        if case.case_id == "complete":
            provider.set_lineage("initial")
            call(provider, stage="ifc_repair_intent", attempt=1, prompt=PROFILE_PROMPT)
            call(
                provider,
                stage="ifc_repair_intent",
                attempt=2,
                prompt=(
                    PROFILE_PROMPT
                    + '\nVALIDATION_FEEDBACK=[{"code":"REPAIR_INTENT_SCHEMA_INVALID"}]'
                ),
            )
            call(provider, stage="ifc_repair_bound_changeset", attempt=1, prompt=PROFILE_PROMPT)
            call(
                provider,
                stage="ifc_repair_bound_changeset",
                attempt=2,
                prompt=(
                    PROFILE_PROMPT
                    + '\nVALIDATION_FEEDBACK=[{"code":"DRAFT_SCHEMA_INVALID"}]'
                ),
            )
            return {
                "status": "succeeded",
                "complete_repair_success": True,
                "successful_artifact_publishable": True,
            }
        if case.case_id == "clarification-resume":
            provider.set_lineage("initial")
            call(provider, stage="ifc_repair_intent", attempt=1, prompt=PROFILE_PROMPT)
            provider.set_lineage("clarification-resume")
            call(provider, stage="ifc_repair_intent", attempt=1, prompt=PROFILE_PROMPT)
            call(provider, stage="ifc_repair_bound_changeset", attempt=1, prompt=PROFILE_PROMPT)
            return {
                "status": "succeeded",
                "complete_repair_success": True,
                "successful_artifact_publishable": True,
                "clarification_answer_applied": True,
            }
        if case.case_id == "program-guard":
            provider.set_lineage("initial")
            call(provider, stage="ifc_repair_intent", attempt=1, prompt=PROFILE_PROMPT)
            return {
                "status": "unsupported",
                "reason_code": "STRUCTURAL_PROFILE_UNSUPPORTED",
                "complete_repair_success": False,
                "successful_artifact_publishable": False,
            }
        raise AssertionError(case.case_id)

    result = _run(
        module,
        tmp_path,
        transport=transport,
        runner=_GreenCommandRunner(),
        executor=executor,
        cases=(
            _case(module, "complete"),
            _case(module, "clarification-resume", feedback="bounded answer"),
            _case(module, "program-guard"),
        ),
    )

    assert result["status"] == "passed"
    assert result["transport_calls"] == 8
    assert result["transport_calls_by_stage"] == {"stage1": 5, "stage2": 3}
    by_case = {item["case_id"]: item for item in result["cases"]}
    assert by_case["complete"]["transport_calls_by_stage"] == {
        "stage1": 2,
        "stage2": 2,
    }
    assert by_case["clarification-resume"]["transport_calls_by_stage"] == {
        "stage1": 2,
        "stage2": 1,
    }
    assert by_case["program-guard"]["transport_calls_by_stage"] == {
        "stage1": 1,
        "stage2": 0,
    }

    complete_attempts = by_case["complete"]["attempts"]
    assert [item["stage"] for item in complete_attempts] == [
        "stage1",
        "stage1",
        "stage2",
        "stage2",
    ]
    assert [item["ordinal"] for item in complete_attempts] == [1, 2, 1, 2]
    assert complete_attempts[1]["correction_reason"] == (
        "REPAIR_INTENT_SCHEMA_INVALID"
    )
    assert complete_attempts[3]["correction_reason"] == "DRAFT_SCHEMA_INVALID"
    assert complete_attempts[0]["parent_attempt_id"] is None
    assert all(
        item["parent_attempt_id"] == complete_attempts[index - 1]["attempt_id"]
        for index, item in enumerate(complete_attempts)
        if index
    )
    resumed = by_case["clarification-resume"]["attempts"]
    assert [item["lineage"] for item in resumed] == [
        "initial",
        "clarification-resume",
        "clarification-resume",
    ]
    assert resumed[1]["parent_attempt_id"] == resumed[0]["attempt_id"]

    assert complete_attempts[0]["response"]["content"].find("beam_start") >= 0
    assert "\"axis\"" not in complete_attempts[0]["response"]["content"]
    assert complete_attempts[2]["response"]["content"].find("beam_axis") >= 0
    assert complete_attempts[0]["provider"] == "mock-deepseek"
    assert complete_attempts[0]["model"] == "mock-reasoner"
    assert complete_attempts[0]["usage"]["prompt_tokens"] == 101
    assert complete_attempts[0]["request_sha256"].startswith("sha256:")
    assert complete_attempts[0]["response_sha256"].startswith("sha256:")
    assert complete_attempts[0]["profile_hashes"] == [HASH_A]
    assert complete_attempts[0]["few_shot_hashes"] == [HASH_B]
    assert result["provider_models"] == [
        {"provider": "mock-deepseek", "model": "mock-reasoner"}
    ]
    assert result["synthetic_fallback_used"] is False

    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
    assert "SECRET-TRANSPORT-TOKEN" not in encoded
    assert "CANARY-PRIVATE-GOLD-12-13" not in encoded
    assert "[REDACTED]" in encoded
    assert "[REDACTED_PRIVATE]" in encoded

