import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/ifc_repair/run_phase11_live_uat.py"


def _module():
    spec = importlib.util.spec_from_file_location("phase11_live", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_live_configuration_projection_is_redacted_and_64k() -> None:
    module = _module()
    environment = module._environment(ROOT / ".env")
    config = module._config(environment)

    assert config["status"] == "ready"
    assert config["max_input_tokens"] == 65_536
    assert config["max_completion_tokens"] == 65_536
    assert config["secret_redacted"] is True
    assert "api_key" not in config


def test_live_attempt_counter_distinguishes_stage1_and_stage2(
    tmp_path: Path,
) -> None:
    module = _module()
    intent = tmp_path / "runs/run-1/intent"
    stage2 = tmp_path / "runs/run-1/changeset/attempt-01"
    intent.mkdir(parents=True)
    stage2.mkdir(parents=True)
    (intent / "attempt-01.json").write_text("{}", encoding="utf-8")
    (intent / "attempt-02.json").write_text("{}", encoding="utf-8")
    (stage2 / "provider-metadata.json").write_text("{}", encoding="utf-8")

    assert module._attempts(tmp_path) == {"stage1": 2, "stage2": 1}


def test_unsupported_contract_requires_exact_terminal_capability_rejection() -> None:
    module = _module()
    attempts = {"stage1": 1, "stage2": 0}

    assert module._contract_pass(
        final={
            "status": "unsupported",
            "reason_code": "DOOR_OPERATION_TYPE_UNSUPPORTED",
            "complete_repair_success": False,
            "successful_artifact_publishable": False,
        },
        attempts=attempts,
        expectation={
            "status": "unsupported",
            "reason_code": "DOOR_OPERATION_TYPE_UNSUPPORTED",
            "publish": False,
            "stage2_attempts": 0,
        },
        feedback_expected=False,
        feedback_applied=False,
        strict_verification={"status": "not_applicable"},
    ) is True

    for wrong in (
        {
            "status": "provider_failed",
            "reason_code": "REPAIR_INTENT_RETRY_EXHAUSTED",
            "complete_repair_success": False,
            "successful_artifact_publishable": False,
        },
        {
            "status": "unsupported",
            "reason_code": "DOOR_OPERATION_UNSUPPORTED",
            "complete_repair_success": False,
            "successful_artifact_publishable": False,
        },
    ):
        assert module._contract_pass(
            final=wrong,
            attempts=attempts,
            expectation={
                "status": "unsupported",
                "reason_code": "DOOR_OPERATION_TYPE_UNSUPPORTED",
                "publish": False,
                "stage2_attempts": 0,
            },
            feedback_expected=False,
            feedback_applied=False,
            strict_verification={"status": "not_applicable"},
        ) is False


def test_publish_contract_requires_independent_reopen_verification() -> None:
    module = _module()
    final = {
        "status": "succeeded",
        "complete_repair_success": True,
        "successful_artifact_publishable": True,
    }
    expectation = {
        "status": "succeeded",
        "publish": True,
        "stage2_attempts": 1,
    }

    assert module._contract_pass(
        final=final,
        attempts={"stage1": 1, "stage2": 1},
        expectation=expectation,
        feedback_expected=False,
        feedback_applied=False,
        strict_verification={
            "status": "passed",
            "l0_pass": True,
            "l1_pass": True,
            "l2_pass": True,
        },
    ) is True
    assert module._contract_pass(
        final=final,
        attempts={"stage1": 1, "stage2": 1},
        expectation=expectation,
        feedback_expected=False,
        feedback_applied=False,
        strict_verification={
            "status": "failed",
            "l0_pass": True,
            "l1_pass": False,
            "l2_pass": True,
        },
    ) is False
