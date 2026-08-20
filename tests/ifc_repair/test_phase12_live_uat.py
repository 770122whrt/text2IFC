from __future__ import annotations

import importlib.util
import hashlib
import json
import re
import shutil
import subprocess
from collections import deque
from pathlib import Path
from typing import Any, Mapping

import pytest

from text2ifc_agent.openai_compat import (
    OpenAICompatibleLiveProvider,
    OpenAICompatRuntimeConfig,
)
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput
from scripts.ifc_repair.run_phase12_live_uat import DEFAULT_CASES as FROZEN_LIVE_CASES


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/ifc_repair/run_phase12_live_uat.py"
CURATOR_SCRIPT = ROOT / "scripts/ifc_repair/curate_phase12_live_proof.py"
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
STAGE1_COMPACT_PROFILE_IDS = {
    "beam.add.v0.3",
    "column.add.v0.3",
    "door.add-with-opening.v0.2",
    "door.fill-existing-opening.v0.2",
    "occurrence.set-properties",
    "opening.add-to-wall",
    "window.add-with-opening",
}
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


def _curator_module():
    spec = importlib.util.spec_from_file_location(
        "phase12_live_curator", CURATOR_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _MockTransport:
    def __init__(
        self,
        responses: list[dict[str, Any]] | None = None,
        *,
        evidence_class: str = "live",
        include_private_gold: bool = False,
    ) -> None:
        self.responses = deque(responses or [])
        self.evidence_class = evidence_class
        self.include_private_gold = include_private_gold
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
            "evidence_class": self.evidence_class,
            "response_id": f"response-{len(self.calls)}",
            "model": "mock-reasoner",
            "transport_attempts": 1,
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
        }
        if self.include_private_gold:
            raw_response["private_gold"] = "CANARY-PRIVATE-GOLD-12-13"
        return LiveProviderResult(
            session_id=session_id,
            evidence_class=self.evidence_class,
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


def _public_source(excerpt: str) -> dict[str, str]:
    return {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": excerpt,
    }


def _structural_intent_operation(
    *,
    operation_id: str,
    family: str,
    parameters: dict[str, Any],
    excerpt: str,
    load_bearing: bool = False,
) -> dict[str, Any]:
    source = _public_source(excerpt)
    properties = []
    if load_bearing:
        properties.append(
            {
                "intent_kind": "natural_language_property",
                "property_phrase": f"{family} is load bearing",
                "raw_value": True,
                "raw_unit": None,
                "scope": "occurrence_direct",
                "source": _public_source(f"{family} is load bearing"),
            }
        )
    return {
        "operation_id": operation_id,
        "operation_type": f"add_{family}",
        "routing_intent": {
            "component_family": family,
            "action": "add",
            "operation_profile": f"{family}.add.v0.3",
            "source": source,
        },
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcBuildingStorey"],
            "names": ["Level 1"],
        },
        "parameters": parameters,
        "attribute_intents": [],
        "property_intents": properties,
        "semantic_bundle_refs": [],
        "quantity_intents": [],
        "occurrence_reuse_intent": None,
        "prototype_intent": None,
        "provenance": [source],
    }


def _intent_body(
    *operations: dict[str, Any],
    excerpt: str,
    unsupported_requests: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/ifc-repair-intent-body/0.8",
        "operations": list(operations),
        "unsupported_requests": list(unsupported_requests or ()),
        "semantic_bundles": [],
        "provenance": [_public_source(excerpt)],
    }


def _prompt_json(prompt: str, heading: str) -> Any:
    marker = f"## {heading}"
    start = prompt.index(marker) + len(marker)
    payload = prompt[start:].lstrip()
    value, _end = json.JSONDecoder().raw_decode(payload)
    return value


class _ProductionPathTransport(_MockTransport):
    """Mock only the external Provider transport; exercise the real API."""

    def __init__(self) -> None:
        super().__init__([])

    def generate_live(
        self,
        *,
        session_id: str,
        prompt: str,
        schema: dict[str, Any],
        state: dict[str, Any],
    ) -> LiveProviderResult:
        stage = str(state["stage"])
        if stage == "ifc_repair_intent":
            content = self._intent_response(prompt)
        elif stage == "ifc_repair_bound_changeset":
            content = self._changeset_response(prompt)
        else:
            raise AssertionError(stage)
        self.responses.append({"content": content})
        return super().generate_live(
            session_id=session_id,
            prompt=prompt,
            schema=schema,
            state=state,
        )

    @staticmethod
    def _intent_response(prompt: str) -> dict[str, Any]:
        public_request = prompt.split(
            "## Public request (untrusted data)", 1
        )[1].split("## Compact registered repair capabilities", 1)[0]
        lowered = public_request.casefold()
        if "structural analysis node" in lowered:
            excerpt = "add a Beam and attach a structural analysis node"
            beam = _structural_intent_operation(
                operation_id="live-guard-beam-1",
                family="beam",
                parameters={},
                excerpt=excerpt,
            )
            return _intent_body(
                beam,
                excerpt=excerpt,
                unsupported_requests=[
                    {
                        "unsupported_id": "unsupported-1",
                        "kind": "registered_capability",
                        "operation_id": "live-guard-beam-1",
                        "capability_id": "structural_analysis_node",
                        "source": _public_source(
                            "attach a structural analysis node"
                        ),
                    }
                ],
            )
        if "(120000, 120000, 6000)" in prompt:
            excerpt = "vertical Column on Level 1 with complete axis and section"
            column = _structural_intent_operation(
                operation_id="live-clarification-column-1",
                family="column",
                parameters={
                    "axis": {
                        "base": {"x_mm": 120000, "y_mm": 120000, "z_mm": 0},
                        "top": {"x_mm": 120000, "y_mm": 120000, "z_mm": 6000},
                    },
                    "section": {
                        "shape": "rectangle",
                        "width_mm": 400,
                        "depth_mm": 600,
                        "orientation": {"x": 0, "y": 1},
                    },
                },
                excerpt=excerpt,
            )
            return _intent_body(column, excerpt=excerpt)
        if "complete center axis" in lowered:
            excerpt = "add a Column on Level 1 without axis or section facts"
            column = _structural_intent_operation(
                operation_id="live-clarification-column-1",
                family="column",
                parameters={},
                excerpt=excerpt,
            )
            return _intent_body(column, excerpt=excerpt)
        if "beam is load bearing" in lowered:
            excerpt = "create Beam and Column; beam is load bearing; column is load bearing"
            beam = _structural_intent_operation(
                operation_id="live-complete-beam-1",
                family="beam",
                parameters={
                    "axis": {
                        "start": {"x_mm": 120000, "y_mm": 120000, "z_mm": 3000},
                        "end": {"x_mm": 126000, "y_mm": 120000, "z_mm": 3000},
                    },
                    "section": {
                        "shape": "rectangle",
                        "width_mm": 300,
                        "height_mm": 500,
                    },
                },
                excerpt=excerpt,
                load_bearing=True,
            )
            column = _structural_intent_operation(
                operation_id="live-complete-column-2",
                family="column",
                parameters={
                    "axis": {
                        "base": {"x_mm": 123000, "y_mm": 124000, "z_mm": 0},
                        "top": {"x_mm": 123000, "y_mm": 124000, "z_mm": 3000},
                    },
                    "section": {
                        "shape": "rectangle",
                        "width_mm": 400,
                        "depth_mm": 600,
                        "orientation": {"x": 0, "y": 1},
                    },
                },
                excerpt=excerpt,
                load_bearing=True,
            )
            return _intent_body(beam, column, excerpt=excerpt)
        raise AssertionError("unexpected Stage 1 request")

    @staticmethod
    def _changeset_response(prompt: str) -> dict[str, Any]:
        projection = _prompt_json(prompt, "Resolved operation projection")
        semantic_summary = _prompt_json(prompt, "Semantic group counts")
        operations = []
        scope: list[str] = []
        evidence: list[str] = []
        for operation_id, operation in projection["operations"].items():
            target_id = str(operation["target_global_id"])
            operation_evidence = list(operation["evidence_pointers"])
            operations.append(
                {
                    "operation_id": operation_id,
                    "operation_type": operation["operation_type"],
                    "target": {"storey_global_id": target_id},
                    "parameters": operation["parameters"],
                    "evidence_refs": operation_evidence,
                }
            )
            scope.extend(str(value) for value in operation["scope_ids"])
            evidence.extend(str(value) for value in operation_evidence)
        binding_lines = prompt.split("## Immutable bindings", 1)[1].split(
            "## Resolved operation projection", 1
        )[0]
        bindings = dict(
            re.findall(r"^- ([^:]+): (.+)$", binding_lines, flags=re.MULTILINE)
        )
        return {
            "schema_version": "text2ifc/ifc-repair-changeset-draft/0.2",
            "draft_id": "draft-live-production-path",
            "base_model_fingerprint": bindings["model"],
            "source_request_hash": bindings["source request"],
            "semantic_manifest_ref": bindings["semantic manifest ref"],
            "semantic_manifest_sha256": bindings["semantic manifest hash"],
            "semantic_summary": semantic_summary,
            "scope": {
                "target_ids": list(dict.fromkeys(scope)),
                "forbidden_ids": [],
            },
            "evidence_refs": list(dict.fromkeys(evidence)),
            "preconditions": [],
            "postconditions": [],
            "operations": operations,
        }


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
    frozen = next(
        (case for case in module.DEFAULT_CASES if case.case_id == case_id),
        None,
    )
    return module.LiveCase(
        case_id=case_id,
        request=(
            frozen.request
            if frozen is not None
            else f"public request for {case_id}"
        ),
        feedback=(
            frozen.feedback
            if frozen is not None and feedback is None
            else feedback
        ),
    )


def _guard_evidence(module: Any, **overrides: Any) -> dict[str, Any]:
    digest = "sha256:" + hashlib.sha256(module.SOURCE.read_bytes()).hexdigest()
    evidence = {
        "source_reference": str(module.SOURCE.resolve()),
        "source_sha256_before": digest,
        "source_sha256_after": digest,
        "source_unchanged": True,
        "stage2_attempts": 0,
        "candidate_output_paths": [],
        "mutation_attempted": False,
    }
    evidence.update(overrides)
    return evidence


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


def test_cli_accepts_the_frozen_deepseek_provider_key(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _module()
    invoked = False

    monkeypatch.setattr(module, "_environment", lambda _path: {})
    monkeypatch.setattr(
        module,
        "_config",
        lambda _environment: {
            "status": "ready",
            "provider": "deepseek-openai-compatible",
            "provider_key": "deepseek",
            "model": "deepseek-chat",
            "max_input_tokens": 65_536,
            "max_completion_tokens": 65_536,
            "secret_redacted": True,
        },
    )

    def fake_run_live_uat(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal invoked
        invoked = True
        return {"status": "passed", "transport_calls": 1}

    monkeypatch.setattr(module, "run_live_uat", fake_run_live_uat)

    exit_code = module.main(
        [
            "--provider",
            "deepseek",
            "--require-green-preflight",
            "--output-root",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert invoked is True


def test_cli_preflight_only_needs_no_provider_configuration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _module()
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "_environment",
        lambda _path: pytest.fail("preflight-only must not read Provider config"),
    )

    def fake_run_live_uat(*_args: Any, **kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {"status": "preflight_passed", "transport_calls": 0}

    monkeypatch.setattr(module, "run_live_uat", fake_run_live_uat)

    exit_code = module.main(
        [
            "--preflight-only",
            "--output-root",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert captured["preflight_only"] is True


def test_cli_rejects_every_non_deepseek_provider_before_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module()
    monkeypatch.setattr(
        module,
        "_environment",
        lambda _path: pytest.fail("configuration must not be read"),
    )

    with pytest.raises(SystemExit) as error:
        module.main(
            [
                "--provider",
                "mimo",
                "--require-green-preflight",
            ]
        )

    assert error.value.code == 2


def test_preflight_only_returns_before_transport_construction(
    tmp_path: Path,
) -> None:
    module = _module()
    transport_constructed = False

    def factory() -> _MockTransport:
        nonlocal transport_constructed
        transport_constructed = True
        return _MockTransport()

    result = module.run_live_uat(
        tmp_path / "run",
        transport_factory=factory,
        command_runner=_GreenCommandRunner(),
        case_executor=lambda *_args: pytest.fail("executor must not run"),
        cases=module.DEFAULT_CASES,
        proof_root=_proof_root(tmp_path),
        preflight_only=True,
    )

    assert result["status"] == "preflight_passed"
    assert result["reason_code"] is None
    assert result["execution_mode"] == "preflight_only"
    assert result["provider_evidence_mode"] == "not_run"
    assert result["runner_contract_eligible"] is False
    assert result["acceptance_eligible"] is False
    assert result["proof_acceptance_eligible"] is False
    assert result["transport_calls"] == 0
    assert result["cases"] == []
    assert result["preflight"]["status"] == "passed"
    assert transport_constructed is False


def test_fixed_live_requests_have_exact_public_structural_authority() -> None:
    module = _module()

    assert 'Storey named "Level 1"' in module.COMPLETE_REQUEST
    assert "(120000, 120000, 3000)" in module.COMPLETE_REQUEST
    assert "(126000, 120000, 3000)" in module.COMPLETE_REQUEST
    assert "300 mm wide and 500 mm high" in module.COMPLETE_REQUEST
    assert "(123000, 124000, 0)" in module.COMPLETE_REQUEST
    assert "(123000, 124000, 3000)" in module.COMPLETE_REQUEST
    assert "400 mm wide and 600 mm deep" in module.COMPLETE_REQUEST
    assert "the Beam is load bearing" in module.COMPLETE_REQUEST
    assert "the Column is load bearing" in module.COMPLETE_REQUEST
    assert "LoadBearing" not in module.COMPLETE_REQUEST

    assert "Column" in module.CLARIFICATION_REQUEST
    assert "member family" not in module.CLARIFICATION_REQUEST
    assert 'Storey named "Level 1"' in module.CLARIFICATION_REQUEST
    assert "center axis is base" not in module.CLARIFICATION_REQUEST
    assert 'Storey named "Level 1"' in module.PROGRAM_GUARD_REQUEST
    assert 'Storey named "Level 1"' in module.CLARIFICATION_ANSWER
    assert "(120000, 120000, 0)" in module.CLARIFICATION_ANSWER
    assert "(120000, 120000, 6000)" in module.CLARIFICATION_ANSWER
    assert "400 mm wide and 600 mm deep" in module.CLARIFICATION_ANSWER


def test_live_runner_uses_only_the_curated_public_damaged_d7n_input() -> None:
    module = _module()

    expected = (
        ROOT
        / "dataset/processed/proof/ifc-repair-success-cases"
        / "structural/batch/phase12-d7n-beam-column-atomic/damaged.ifc"
    ).resolve()
    assert module.SOURCE.resolve() == expected
    assert module.SOURCE.name == "damaged.ifc"
    assert module.SOURCE.is_file()
    assert module.FROZEN_SOURCE_SHA256 == (
        "sha256:25240558bcbe23c1bbf4916d0b9a0fbb"
        "de8202d63dbc7a488ef633ab40eb6127"
    )
    assert "sha256:" + hashlib.sha256(module.SOURCE.read_bytes()).hexdigest() == (
        module.FROZEN_SOURCE_SHA256
    )


def test_fixed_live_matrix_is_bound_to_an_independent_reviewed_digest() -> None:
    module = _module()

    assert module.FROZEN_CASE_MATRIX_SHA256 == (
        "sha256:1b9b181f42ca9eccdda5cffac323cb5c"
        "ec67633bf4859c1000e9f7324681fd2b"
    )
    assert module._case_matrix_sha256(module.DEFAULT_CASES) == (
        module.FROZEN_CASE_MATRIX_SHA256
    )


def test_live_runner_cannot_claim_independent_proof_before_plan_12_14(
    tmp_path: Path,
) -> None:
    module = _module()
    transport = _MockTransport(
        [{"content": {"ok": True}} for _ in range(6)]
    )

    def call(provider: Any, *, stage: str) -> None:
        provider.generate_live(
            session_id=f"mock-{stage}",
            prompt=PROFILE_PROMPT,
            schema={"type": "object"},
            state={"stage": stage, "attempt": 1},
        )

    strict = {
        "status": "passed",
        "l0_pass": True,
        "l1_pass": True,
        "l2_pass": True,
        "proof_validation_status": "pending_plan_12_14",
    }

    def executor(case: Any, provider: Any, _case_root: Path) -> dict[str, Any]:
        call(provider, stage="ifc_repair_intent")
        if case.case_id == "clarification-resume":
            provider.set_lineage("clarification-resume")
            call(provider, stage="ifc_repair_intent")
        if case.case_id != "program-guard":
            call(provider, stage="ifc_repair_bound_changeset")
            result = {
                "status": "succeeded",
                "complete_repair_success": True,
                "successful_artifact_publishable": True,
                "clarification_answer_applied": (
                    case.case_id == "clarification-resume"
                ),
                "strict_reopen_verification": strict,
            }
            if case.case_id == "clarification-resume":
                result.update(
                    {
                        "initial": {
                            "status": "clarification_required",
                            "complete_repair_success": False,
                            "successful_artifact_publishable": False,
                        },
                        "clarification": {
                            "clarification_id": "clarification-001",
                            "reason_code": "STRUCTURAL_REQUIRED_FIELDS_MISSING",
                            "question": "Provide the grouped structural details.",
                            "answer_modes": ["add_detail"],
                        },
                    }
                )
            return result
        return {
            "status": "unsupported",
            "reason_code": module.PROGRAM_GUARD_REASON,
            "complete_repair_success": False,
            "successful_artifact_publishable": False,
            "program_guard_evidence": _guard_evidence(module),
        }

    result = _run(
        module,
        tmp_path,
        transport=transport,
        runner=_GreenCommandRunner(),
        executor=executor,
        cases=module.DEFAULT_CASES,
    )

    assert result["status"] == "test_passed"
    assert result["runner_contract_eligible"] is False
    assert result["acceptance_eligible"] is False
    assert result["proof_acceptance_eligible"] is False
    assert result["proof_validation_status"] == "pending_plan_12_14"
    for case in result["cases"]:
        assert case["proof_acceptance_eligible"] is False
        assert case["proof_validation_status"] == "pending_plan_12_14"


def test_complete_transport_drives_the_real_repair_api_and_reopens_ifc2x3(
    tmp_path: Path,
) -> None:
    module = _module()
    transport = _ProductionPathTransport()
    provider = module.TranscriptProvider(transport)
    case = module.DEFAULT_CASES[0]
    provider.set_case(case.case_id)

    final = module._production_case_executor(
        case,
        provider,
        tmp_path / "complete",
    )

    assert final["status"] == "succeeded", (
        final["status"],
        final["reason_code"],
        final.get("clarification"),
    )
    assert final["complete_repair_success"] is True
    assert final["successful_artifact_publishable"] is True
    assert final["strict_reopen_verification"]["status"] == "passed"
    assert final["strict_reopen_verification"]["reopened_schema"] == "IFC2X3"
    assert final["strict_reopen_verification"]["operation_count"] == 2
    assert final["strict_reopen_verification"]["preservation_status"] == (
        "pending_plan_12_14"
    )
    assert final["strict_reopen_verification"][
        "ground_truth_isolation_status"
    ] == "pending_plan_12_14"
    assert [item["stage"] for item in provider.attempts] == [
        "stage1",
        "stage2",
    ]
    assert set(provider.attempts[0]["profile_ids"]) == STAGE1_COMPACT_PROFILE_IDS
    assert provider.attempts[0]["few_shot_ids"] == []
    assert set(provider.attempts[1]["profile_ids"]) == {
        "beam.add.v0.3",
        "column.add.v0.3",
    }
    assert set(provider.attempts[1]["few_shot_ids"]) == {
        "beam.add.v0.3.complete",
        "beam.add.v0.3.clarification",
        "beam.add.v0.3.type-reuse",
        "beam.add.v0.3.unsupported",
        "column.add.v0.3.complete",
        "column.add.v0.3.clarification",
        "column.add.v0.3.type-reuse",
        "column.add.v0.3.unsupported",
    }
    run_root = (
        tmp_path / "complete" / "runtime" / "runs" / final["run_id"]
    )
    intent = json.loads(
        (run_root / "intent" / "repair-intent.json").read_text(
            encoding="utf-8"
        )
    )
    assert [item["routing_intent"]["operation_profile"] for item in intent["operations"]] == [
        "beam.add.v0.3",
        "column.add.v0.3",
    ]
    assert [
        item["property_intents"][0]["property_phrase"]
        for item in intent["operations"]
    ] == ["beam is load bearing", "column is load bearing"]


def test_clarification_transport_drives_real_api_resume_and_publication(
    tmp_path: Path,
) -> None:
    module = _module()
    transport = _ProductionPathTransport()
    provider = module.TranscriptProvider(transport)
    case = module.DEFAULT_CASES[1]
    provider.set_case(case.case_id)

    final = module._production_case_executor(
        case,
        provider,
        tmp_path / "clarification",
    )

    assert final["initial"]["status"] == "clarification_required"
    assert final["initial"]["successful_artifact_publishable"] is False
    assert final["clarification"]["reason_code"] == "missing_required_parameter"
    assert final["clarification"]["answer_modes"] == ["add_detail", "cancel"]
    assert final["clarification_answer_applied"] is True
    assert final["status"] == "succeeded", (
        final["status"],
        final["reason_code"],
    )
    assert final["strict_reopen_verification"]["operation_count"] == 1
    assert [item["stage"] for item in provider.attempts] == [
        "stage1",
        "stage1",
        "stage2",
    ]
    assert [item["lineage"] for item in provider.attempts] == [
        "initial",
        "clarification-resume",
        "clarification-resume",
    ]


def test_program_guard_transport_stops_real_api_before_stage2_or_mutation(
    tmp_path: Path,
) -> None:
    module = _module()
    transport = _ProductionPathTransport()
    provider = module.TranscriptProvider(transport)
    case = module.DEFAULT_CASES[2]
    provider.set_case(case.case_id)

    final = module._production_case_executor(
        case,
        provider,
        tmp_path / "guard",
    )

    assert final["status"] == "unsupported", (
        final["status"],
        final["reason_code"],
    )
    assert final["reason_code"] == module.PROGRAM_GUARD_REASON
    assert final["complete_repair_success"] is False
    assert final["successful_artifact_publishable"] is False
    assert [item["stage"] for item in provider.attempts] == ["stage1"]
    assert final["program_guard_evidence"] == _guard_evidence(module)


def test_structural_normalizer_never_invents_an_optional_axis_reference() -> None:
    from text2ifc_ifc_repair.operations import create_default_registry

    parameters = {
        "axis": {
            "start": {"x_mm": 0, "y_mm": 0, "z_mm": 3000},
            "end": {"x_mm": 6000, "y_mm": 0, "z_mm": 3000},
        },
        "section": {
            "shape": "rectangle",
            "width_mm": 300,
            "height_mm": 500,
        },
    }
    prepared = create_default_registry().prepare_partial_parameters(
        {"operation_type": "add_beam", "parameters": parameters}
    )

    assert prepared == parameters
    assert "reference" not in prepared["axis"]


def test_registry_projects_structural_target_without_family_branching() -> None:
    from text2ifc_ifc_repair.operations import create_default_registry

    registry = create_default_registry()
    assert registry.bind_resolved_target("add_beam", "storey-a") == {
        "storey_global_id": "storey-a"
    }
    assert registry.bind_resolved_target("add_column", "storey-b") == {
        "storey_global_id": "storey-b"
    }


def test_default_preflight_runner_applies_a_bounded_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module()
    captured: dict[str, Any] = {}

    def fake_run(*_args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured.update(kwargs)
        return subprocess.CompletedProcess(("git", "diff", "--check"), 0, "", "")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    module._default_command_runner(("git", "diff", "--check"), cwd=ROOT)

    assert captured["timeout"] == 60


def test_default_preflight_runner_allows_the_real_full_suite_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module()
    captured: dict[str, Any] = {}

    def fake_run(*_args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured.update(kwargs)
        return subprocess.CompletedProcess(
            (module.sys.executable, "-m", "pytest", "tests/ifc_repair", "-q"),
            0,
            "",
            "",
        )

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    module._default_command_runner(
        (module.sys.executable, "-m", "pytest", "tests/ifc_repair", "-q"),
        cwd=ROOT,
    )

    assert captured["timeout"] == 7_200


def test_preflight_pytest_commands_use_run_local_temp_and_cache(
    tmp_path: Path,
) -> None:
    module = _module()
    preflight_root = tmp_path / "preflight"
    commands = dict(
        module._preflight_commands(preflight_root, _proof_root(tmp_path))
    )

    expected = {
        "focused": (
            preflight_root / "pytest-focused",
            preflight_root / "pytest-cache-focused",
        ),
        "full-suite": (
            preflight_root / "pytest-full-suite",
            preflight_root / "pytest-cache-full-suite",
        ),
    }
    for name, (base_temp, cache_dir) in expected.items():
        command = commands[name]
        assert f"--basetemp={base_temp.resolve()}" in command
        assert "-o" in command
        assert f"cache_dir={cache_dir.resolve()}" in command
        assert not any(".pytest-tmp" in item for item in command)


def test_preflight_timeout_has_a_distinct_blocking_reason_and_zero_transport(
    tmp_path: Path,
) -> None:
    module = _module()
    transport = _MockTransport()

    def timeout_runner(
        command: tuple[str, ...],
        *,
        cwd: Path,
    ) -> subprocess.CompletedProcess[str]:
        del cwd
        raise subprocess.TimeoutExpired(command, 180)

    result = module.run_live_uat(
        tmp_path / "run",
        transport_factory=lambda: transport,
        command_runner=timeout_runner,
        case_executor=lambda *_args: pytest.fail("executor must not run"),
        cases=module.DEFAULT_CASES,
        proof_root=_proof_root(tmp_path),
    )

    assert result["status"] == "preflight_failed"
    assert {
        check["reason_code"] for check in result["preflight"]["checks"]
    } == {"COMMAND_TIMEOUT"}
    assert result["transport_calls"] == 0
    assert transport.calls == []


def test_strict_reopen_rejects_a_stale_source_hash(tmp_path: Path) -> None:
    module = _module()
    runtime = tmp_path / "runtime"
    run_root = runtime / "runs" / "run-001"
    run_root.mkdir(parents=True)
    evaluation = run_root / "evaluation.json"
    evaluation.write_text("{}", encoding="utf-8")
    repaired = run_root / "repaired.ifc"
    shutil.copy2(module.SOURCE, repaired)

    def artifact(path: Path) -> dict[str, Any]:
        payload = path.read_bytes()
        return {
            "path": path.relative_to(run_root).as_posix(),
            "size_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    (run_root / "manifest.json").write_text(
        json.dumps(
            {"artifacts": [artifact(evaluation), artifact(repaired)]},
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (run_root / "state.json").write_text(
        json.dumps(
            {
                "source": {
                    "reference": str(module.SOURCE),
                    "sha256": "sha256:" + "0" * 64,
                }
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = module._strict_reopen_verification(
        runtime,
        {
            "run_id": "run-001",
            "successful_artifact_publishable": True,
            "artifacts": {
                "manifest": "manifest.json",
                "evaluation": "evaluation.json",
                "successful_ifc": "repaired.ifc",
            },
        },
    )

    assert result["status"] == "failed"
    assert result["reason_code"] == "LIVE_SOURCE_HASH_MISMATCH"


def test_strict_reopen_rejects_a_self_consistent_substitute_source(
    tmp_path: Path,
) -> None:
    module = _module()
    runtime = tmp_path / "runtime"
    run_root = runtime / "runs" / "run-001"
    run_root.mkdir(parents=True)
    evaluation = run_root / "evaluation.json"
    evaluation.write_text("{}", encoding="utf-8")
    repaired = run_root / "repaired.ifc"
    substitute = tmp_path / "substitute-damaged.ifc"
    shutil.copy2(module.SOURCE, repaired)
    shutil.copy2(module.SOURCE, substitute)

    def artifact(path: Path) -> dict[str, Any]:
        payload = path.read_bytes()
        return {
            "path": path.relative_to(run_root).as_posix(),
            "size_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    (run_root / "manifest.json").write_text(
        json.dumps(
            {"artifacts": [artifact(evaluation), artifact(repaired)]},
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (run_root / "state.json").write_text(
        json.dumps(
            {
                "source": {
                    "reference": str(substitute),
                    "sha256": "sha256:"
                    + hashlib.sha256(substitute.read_bytes()).hexdigest(),
                }
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = module._strict_reopen_verification(
        runtime,
        {
            "run_id": "run-001",
            "successful_artifact_publishable": True,
            "artifacts": {
                "manifest": "manifest.json",
                "evaluation": "evaluation.json",
                "successful_ifc": "repaired.ifc",
            },
        },
    )

    assert result["status"] == "failed"
    assert result["reason_code"] == "LIVE_SOURCE_PATH_MISMATCH"


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


def test_injected_preflight_cannot_unlock_the_production_executor(
    tmp_path: Path,
) -> None:
    module = _module()
    transport_constructed = False

    def factory() -> _MockTransport:
        nonlocal transport_constructed
        transport_constructed = True
        return _MockTransport()

    result = module.run_live_uat(
        tmp_path / "run",
        transport_factory=factory,
        command_runner=_GreenCommandRunner(),
        proof_root=_proof_root(tmp_path),
    )

    assert result["status"] == "blocked"
    assert result["reason_code"] == "LIVE_TEST_SEAMS_MUST_BE_PAIRED"
    assert result["preflight"]["status"] == "not_run"
    assert result["transport_calls"] == 0
    assert transport_constructed is False


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
            "reason_code": module.PROGRAM_GUARD_REASON,
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

    assert result["status"] == "blocked"
    assert result["reason_code"] == "LIVE_CASE_MATRIX_REQUIRED"
    assert result["transport_calls"] == 0


def test_green_preflight_rejects_a_partial_or_substituted_live_matrix(
    tmp_path: Path,
) -> None:
    module = _module()
    transport = _MockTransport()

    result = _run(
        module,
        tmp_path,
        transport=transport,
        runner=_GreenCommandRunner(),
        executor=lambda *_args: pytest.fail("executor must not run"),
        cases=(
            _case(module, "complete"),
            _case(module, "program-guard"),
            _case(module, "substitute"),
        ),
    )

    assert result["status"] == "blocked"
    assert result["reason_code"] == "LIVE_CASE_MATRIX_REQUIRED"
    assert result["transport_calls"] == 0
    assert transport.calls == []


def test_green_preflight_rejects_tampered_text_in_the_fixed_live_matrix(
    tmp_path: Path,
) -> None:
    module = _module()
    transport = _MockTransport()
    tampered_complete = module.LiveCase(
        case_id="complete",
        request=module.COMPLETE_REQUEST + " Silently choose any nearby Type.",
    )

    result = _run(
        module,
        tmp_path,
        transport=transport,
        runner=_GreenCommandRunner(),
        executor=lambda *_args: pytest.fail("executor must not run"),
        cases=(
            tampered_complete,
            _case(module, "clarification-resume"),
            _case(module, "program-guard"),
        ),
    )

    assert result["status"] == "blocked"
    assert result["reason_code"] == "LIVE_CASE_MATRIX_REQUIRED"
    assert result["transport_calls"] == 0
    assert transport.calls == []


def test_paired_test_seams_are_explicitly_ineligible_as_live_acceptance(
    tmp_path: Path,
) -> None:
    module = _module()
    transport = _MockTransport()

    def executor(case: Any, provider: Any, _case_root: Path) -> dict[str, Any]:
        provider.generate_live(
            session_id=f"mock-{case.case_id}",
            prompt=PROFILE_PROMPT,
            schema={"type": "object"},
            state={"stage": "ifc_repair_intent", "attempt": 1},
        )
        if case.case_id == "program-guard":
            return {
                "status": "unsupported",
                "reason_code": module.PROGRAM_GUARD_REASON,
                "complete_repair_success": False,
                "successful_artifact_publishable": False,
                "program_guard_evidence": _guard_evidence(module),
            }
        return {
            "status": "provider_failed",
            "complete_repair_success": False,
            "successful_artifact_publishable": False,
        }

    result = _run(
        module,
        tmp_path,
        transport=transport,
        runner=_GreenCommandRunner(),
        executor=executor,
        cases=module.DEFAULT_CASES,
    )

    assert result["execution_mode"] == "test_injected"
    assert result["provider_evidence_mode"] == "test_injected"
    assert result["acceptance_eligible"] is False
    assert result["status"] != "passed"


def test_production_runner_rejects_exact_transport_class_with_mimo_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _module()
    runner = _GreenCommandRunner()
    executor_called = False

    def production_executor(*_args: Any) -> dict[str, Any]:
        nonlocal executor_called
        executor_called = True
        return {}

    config = OpenAICompatRuntimeConfig(
        provider="mimo",
        provider_label="mimo-openai-compatible",
        api_key="not-used",
        api_key_env="MIMO_API_KEY",
        base_url="https://example.invalid/v1",
        base_url_env="OPENAI_BASE_URL",
        model="mimo-model",
        model_env="TEXT2IFC_MIMO_MODEL",
        max_completion_tokens=65_536,
        max_input_tokens=65_536,
    )
    transport = OpenAICompatibleLiveProvider(
        config=config,
        client_factory=lambda **_kwargs: object(),
    )
    monkeypatch.setattr(module, "_default_command_runner", runner)
    monkeypatch.setattr(module, "_production_case_executor", production_executor)

    result = module.run_live_uat(
        tmp_path / "run",
        transport_factory=lambda: transport,
        command_runner=runner,
        case_executor=production_executor,
        cases=module.DEFAULT_CASES,
        proof_root=_proof_root(tmp_path),
    )

    assert result["status"] == "blocked"
    assert result["reason_code"] == "LIVE_DEEPSEEK_TRANSPORT_REQUIRED"
    assert result["acceptance_eligible"] is False
    assert result["transport_calls"] == 0
    assert executor_called is False


def test_production_runner_rejects_deepseek_labels_on_a_replay_endpoint(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _module()
    runner = _GreenCommandRunner()
    executor_called = False

    def production_executor(*_args: Any) -> dict[str, Any]:
        nonlocal executor_called
        executor_called = True
        return {}

    config = OpenAICompatRuntimeConfig(
        provider="deepseek",
        provider_label="deepseek-openai-compatible",
        api_key="not-used",
        api_key_env="DEEPSEEK_API_KEY",
        base_url="http://127.0.0.1:8080/replay",
        base_url_env="OPENAI_BASE_URL",
        model="deepseek-chat",
        model_env="TEXT2IFC_DEEPSEEK_MODEL",
        max_completion_tokens=65_536,
        max_input_tokens=65_536,
    )
    transport = OpenAICompatibleLiveProvider(
        config=config,
        client_factory=lambda **_kwargs: object(),
    )
    monkeypatch.setattr(module, "_default_command_runner", runner)
    monkeypatch.setattr(module, "_production_case_executor", production_executor)

    result = module.run_live_uat(
        tmp_path / "run",
        transport_factory=lambda: transport,
        command_runner=runner,
        case_executor=production_executor,
        cases=module.DEFAULT_CASES,
        proof_root=_proof_root(tmp_path),
    )

    assert result["status"] == "blocked"
    assert result["reason_code"] == "LIVE_DEEPSEEK_TRANSPORT_REQUIRED"
    assert result["transport_calls"] == 0
    assert executor_called is False


def test_production_runner_rejects_an_injected_client_on_the_official_endpoint(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _module()
    runner = _GreenCommandRunner()
    executor_called = False

    def production_executor(*_args: Any) -> dict[str, Any]:
        nonlocal executor_called
        executor_called = True
        return {}

    config = OpenAICompatRuntimeConfig(
        provider="deepseek",
        provider_label="deepseek-openai-compatible",
        api_key="not-used",
        api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com",
        base_url_env="DEEPSEEK_BASE_URL",
        model="deepseek-chat",
        model_env="TEXT2IFC_DEEPSEEK_MODEL",
        max_completion_tokens=65_536,
        max_input_tokens=65_536,
    )
    transport = OpenAICompatibleLiveProvider(
        config=config,
        client_factory=lambda **_kwargs: object(),
    )
    monkeypatch.setattr(module, "_default_command_runner", runner)
    monkeypatch.setattr(module, "_production_case_executor", production_executor)

    result = module.run_live_uat(
        tmp_path / "run",
        transport_factory=lambda: transport,
        command_runner=runner,
        case_executor=production_executor,
        cases=module.DEFAULT_CASES,
        proof_root=_proof_root(tmp_path),
    )

    assert result["status"] == "blocked"
    assert result["reason_code"] == "LIVE_DEEPSEEK_TRANSPORT_REQUIRED"
    assert result["transport_calls"] == 0
    assert executor_called is False


@pytest.mark.parametrize(
    ("evidence_class", "include_private_gold"),
    (("cached", False), ("live", True)),
)
def test_non_genuine_or_private_transport_cannot_pass_as_live(
    tmp_path: Path,
    evidence_class: str,
    include_private_gold: bool,
) -> None:
    module = _module()
    transport = _MockTransport(
        [{"content": {"ok": True}} for _ in range(6)],
        evidence_class=evidence_class,
        include_private_gold=include_private_gold,
    )

    def call(provider: Any, *, stage: str) -> None:
        provider.generate_live(
            session_id=f"mock-{stage}",
            prompt=PROFILE_PROMPT,
            schema={"type": "object"},
            state={"stage": stage, "attempt": 1},
        )

    strict = {
        "status": "passed",
        "l0_pass": True,
        "l1_pass": True,
        "l2_pass": True,
    }

    def executor(case: Any, provider: Any, _case_root: Path) -> dict[str, Any]:
        call(provider, stage="ifc_repair_intent")
        if case.case_id == "clarification-resume":
            provider.set_lineage("clarification-resume")
            call(provider, stage="ifc_repair_intent")
        if case.case_id != "program-guard":
            call(provider, stage="ifc_repair_bound_changeset")
            final = {
                "status": "succeeded",
                "complete_repair_success": True,
                "successful_artifact_publishable": True,
                "clarification_answer_applied": (
                    case.case_id == "clarification-resume"
                ),
                "strict_reopen_verification": strict,
            }
            if case.case_id == "clarification-resume":
                final.update(
                    {
                        "initial": {
                            "status": "clarification_required",
                            "complete_repair_success": False,
                            "successful_artifact_publishable": False,
                        },
                        "clarification": {
                            "clarification_id": "clarification-001",
                            "reason_code": "STRUCTURAL_REQUIRED_FIELDS_MISSING",
                            "question": "Provide the grouped structural details.",
                            "answer_modes": ["add_detail"],
                        },
                    }
                )
            return final
        return {
            "status": "unsupported",
            "reason_code": module.PROGRAM_GUARD_REASON,
            "complete_repair_success": False,
            "successful_artifact_publishable": False,
            "program_guard_evidence": _guard_evidence(module),
        }

    result = _run(
        module,
        tmp_path,
        transport=transport,
        runner=_GreenCommandRunner(),
        executor=executor,
        cases=(
            _case(module, "complete"),
            _case(module, "clarification-resume"),
            _case(module, "program-guard"),
        ),
    )

    assert result["status"] == "failed"
    assert result["reason_code"] == "LIVE_CASE_CONTRACT_FAILED"
    assert [
        case["attempts"][0].get("evidence_class")
        for case in result["cases"]
    ] == [evidence_class, evidence_class, evidence_class]
    if include_private_gold:
        assert all(
            case["attempts"][0]["private_evidence_detected"] is True
            for case in result["cases"]
        )
        encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
        assert "CANARY-PRIVATE-GOLD-12-13" not in encoded
        assert "[REDACTED_PRIVATE]" in encoded
    assert all(case["contract_pass"] is False for case in result["cases"])


def test_published_case_without_strict_reopen_evidence_cannot_pass(
    tmp_path: Path,
) -> None:
    module = _module()
    transport = _MockTransport(
        [{"content": {"ok": True}} for _ in range(6)]
    )

    def call(provider: Any, *, stage: str) -> None:
        provider.generate_live(
            session_id=f"mock-{stage}",
            prompt=PROFILE_PROMPT,
            schema={"type": "object"},
            state={"stage": stage, "attempt": 1},
        )

    def executor(case: Any, provider: Any, _case_root: Path) -> dict[str, Any]:
        call(provider, stage="ifc_repair_intent")
        if case.case_id == "clarification-resume":
            provider.set_lineage("clarification-resume")
            call(provider, stage="ifc_repair_intent")
        if case.case_id != "program-guard":
            call(provider, stage="ifc_repair_bound_changeset")
            return {
                "status": "succeeded",
                "complete_repair_success": True,
                "successful_artifact_publishable": True,
                "clarification_answer_applied": (
                    case.case_id == "clarification-resume"
                ),
            }
        return {
            "status": "unsupported",
            "reason_code": module.PROGRAM_GUARD_REASON,
            "complete_repair_success": False,
            "successful_artifact_publishable": False,
            "program_guard_evidence": _guard_evidence(module),
        }

    result = _run(
        module,
        tmp_path,
        transport=transport,
        runner=_GreenCommandRunner(),
        executor=executor,
        cases=(
            _case(module, "complete"),
            _case(module, "clarification-resume"),
            _case(module, "program-guard"),
        ),
    )

    by_case = {item["case_id"]: item for item in result["cases"]}
    assert result["status"] == "failed"
    assert by_case["complete"]["contract_pass"] is False
    assert by_case["clarification-resume"]["contract_pass"] is False
    assert by_case["program-guard"]["contract_pass"] is True


def test_clarification_success_requires_the_initial_grouped_stop(
    tmp_path: Path,
) -> None:
    module = _module()
    transport = _MockTransport(
        [{"content": {"ok": True}} for _ in range(6)]
    )

    def call(provider: Any, *, stage: str) -> None:
        provider.generate_live(
            session_id=f"mock-{stage}",
            prompt=PROFILE_PROMPT,
            schema={"type": "object"},
            state={"stage": stage, "attempt": 1},
        )

    strict = {
        "status": "passed",
        "l0_pass": True,
        "l1_pass": True,
        "l2_pass": True,
    }

    def executor(case: Any, provider: Any, _case_root: Path) -> dict[str, Any]:
        call(provider, stage="ifc_repair_intent")
        if case.case_id == "clarification-resume":
            provider.set_lineage("clarification-resume")
            call(provider, stage="ifc_repair_intent")
        if case.case_id != "program-guard":
            call(provider, stage="ifc_repair_bound_changeset")
            final = {
                "status": "succeeded",
                "complete_repair_success": True,
                "successful_artifact_publishable": True,
                "clarification_answer_applied": (
                    case.case_id == "clarification-resume"
                ),
                "strict_reopen_verification": strict,
            }
            if case.case_id == "clarification-resume":
                final.update(
                    {
                        "initial": {
                            "status": "succeeded",
                            "complete_repair_success": True,
                            "successful_artifact_publishable": True,
                        },
                        "clarification": None,
                    }
                )
            return final
        return {
            "status": "unsupported",
            "reason_code": module.PROGRAM_GUARD_REASON,
            "complete_repair_success": False,
            "successful_artifact_publishable": False,
            "program_guard_evidence": _guard_evidence(module),
        }

    result = _run(
        module,
        tmp_path,
        transport=transport,
        runner=_GreenCommandRunner(),
        executor=executor,
        cases=(
            _case(module, "complete"),
            _case(module, "clarification-resume"),
            _case(module, "program-guard"),
        ),
    )

    by_case = {item["case_id"]: item for item in result["cases"]}
    assert result["status"] == "failed"
    assert by_case["complete"]["contract_pass"] is True
    assert by_case["clarification-resume"]["contract_pass"] is False
    assert by_case["program-guard"]["contract_pass"] is True


def test_program_guard_requires_the_frozen_capability_reason(
    tmp_path: Path,
) -> None:
    module = _module()
    transport = _MockTransport(
        [{"content": {"ok": True}} for _ in range(6)]
    )

    def call(provider: Any, *, stage: str) -> None:
        provider.generate_live(
            session_id=f"mock-{stage}",
            prompt=PROFILE_PROMPT,
            schema={"type": "object"},
            state={"stage": stage, "attempt": 1},
        )

    strict = {
        "status": "passed",
        "l0_pass": True,
        "l1_pass": True,
        "l2_pass": True,
    }
    clarification = {
        "clarification_id": "clarification-001",
        "reason_code": "STRUCTURAL_REQUIRED_FIELDS_MISSING",
        "question": "Provide the grouped structural details.",
        "answer_modes": ["add_detail"],
    }

    def executor(case: Any, provider: Any, _case_root: Path) -> dict[str, Any]:
        call(provider, stage="ifc_repair_intent")
        if case.case_id == "clarification-resume":
            provider.set_lineage("clarification-resume")
            call(provider, stage="ifc_repair_intent")
        if case.case_id != "program-guard":
            call(provider, stage="ifc_repair_bound_changeset")
            final = {
                "status": "succeeded",
                "complete_repair_success": True,
                "successful_artifact_publishable": True,
                "clarification_answer_applied": (
                    case.case_id == "clarification-resume"
                ),
                "strict_reopen_verification": strict,
            }
            if case.case_id == "clarification-resume":
                final.update(
                    {
                        "initial": {
                            "status": "clarification_required",
                            "complete_repair_success": False,
                            "successful_artifact_publishable": False,
                        },
                        "clarification": clarification,
                    }
                )
            return final
        return {
            "status": "unsupported",
            "reason_code": "SOME_OTHER_UNSUPPORTED_REASON",
            "complete_repair_success": False,
            "successful_artifact_publishable": False,
        }

    result = _run(
        module,
        tmp_path,
        transport=transport,
        runner=_GreenCommandRunner(),
        executor=executor,
        cases=(
            _case(module, "complete"),
            _case(module, "clarification-resume"),
            _case(module, "program-guard"),
        ),
    )

    by_case = {item["case_id"]: item for item in result["cases"]}
    assert result["status"] == "failed"
    assert by_case["complete"]["contract_pass"] is True
    assert by_case["clarification-resume"]["contract_pass"] is True
    assert by_case["program-guard"]["contract_pass"] is False


@pytest.mark.parametrize(
    "guard_evidence",
    (
        {},
        {"source_unchanged": False},
        {"mutation_attempted": True},
        {"candidate_output_paths": ["candidate.ifc"]},
        {"source_sha256_after": "sha256:" + "f" * 64},
    ),
)
def test_program_guard_requires_source_bound_zero_mutation_evidence(
    tmp_path: Path,
    guard_evidence: dict[str, Any],
) -> None:
    module = _module()
    transport = _MockTransport(
        [{"content": {"ok": True}} for _ in range(6)]
    )

    def call(provider: Any, *, stage: str) -> None:
        provider.generate_live(
            session_id=f"mock-{stage}",
            prompt=PROFILE_PROMPT,
            schema={"type": "object"},
            state={"stage": stage, "attempt": 1},
        )

    strict = {
        "status": "passed",
        "l0_pass": True,
        "l1_pass": True,
        "l2_pass": True,
    }
    clarification = {
        "clarification_id": "clarification-001",
        "reason_code": "STRUCTURAL_REQUIRED_FIELDS_MISSING",
        "question": "Provide the grouped structural details.",
        "answer_modes": ["add_detail"],
    }

    def executor(case: Any, provider: Any, _case_root: Path) -> dict[str, Any]:
        call(provider, stage="ifc_repair_intent")
        if case.case_id == "clarification-resume":
            provider.set_lineage("clarification-resume")
            call(provider, stage="ifc_repair_intent")
        if case.case_id != "program-guard":
            call(provider, stage="ifc_repair_bound_changeset")
            final = {
                "status": "succeeded",
                "complete_repair_success": True,
                "successful_artifact_publishable": True,
                "clarification_answer_applied": (
                    case.case_id == "clarification-resume"
                ),
                "strict_reopen_verification": strict,
            }
            if case.case_id == "clarification-resume":
                final.update(
                    {
                        "initial": {
                            "status": "clarification_required",
                            "complete_repair_success": False,
                            "successful_artifact_publishable": False,
                        },
                        "clarification": clarification,
                    }
                )
            return final
        return {
            "status": "unsupported",
            "reason_code": module.PROGRAM_GUARD_REASON,
            "complete_repair_success": False,
            "successful_artifact_publishable": False,
            "program_guard_evidence": (
                guard_evidence
                if not guard_evidence
                else _guard_evidence(module, **guard_evidence)
            ),
        }

    result = _run(
        module,
        tmp_path,
        transport=transport,
        runner=_GreenCommandRunner(),
        executor=executor,
        cases=module.DEFAULT_CASES,
    )

    by_case = {item["case_id"]: item for item in result["cases"]}
    assert by_case["program-guard"]["contract_pass"] is False


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

    strict = {
        "status": "passed",
        "l0_pass": True,
        "l1_pass": True,
        "l2_pass": True,
    }

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
                "strict_reopen_verification": strict,
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
                "strict_reopen_verification": strict,
                "initial": {
                    "status": "clarification_required",
                    "complete_repair_success": False,
                    "successful_artifact_publishable": False,
                },
                "clarification": {
                    "clarification_id": "clarification-001",
                    "reason_code": "STRUCTURAL_REQUIRED_FIELDS_MISSING",
                    "question": "Provide the grouped structural details.",
                    "answer_modes": ["add_detail"],
                },
            }
        if case.case_id == "program-guard":
            provider.set_lineage("initial")
            call(provider, stage="ifc_repair_intent", attempt=1, prompt=PROFILE_PROMPT)
            return {
                "status": "unsupported",
                "reason_code": module.PROGRAM_GUARD_REASON,
                "complete_repair_success": False,
                "successful_artifact_publishable": False,
                "program_guard_evidence": _guard_evidence(module),
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
            _case(module, "clarification-resume"),
            _case(module, "program-guard"),
        ),
    )

    assert result["status"] == "test_passed"
    assert result["execution_mode"] == "test_injected"
    assert result["acceptance_eligible"] is False
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
    assert complete_attempts[0]["raw_request_sha256"].startswith("sha256:")
    assert complete_attempts[0]["raw_response_sha256"].startswith("sha256:")
    assert complete_attempts[0]["request_sha256"].startswith("sha256:")
    assert complete_attempts[0]["response_sha256"].startswith("sha256:")
    assert (
        complete_attempts[0]["raw_request_sha256"]
        != complete_attempts[0]["request_sha256"]
    )
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


def _curation_attempt(
    *,
    case_id: str,
    stage: str,
    ordinal: int,
    parent_attempt_id: str | None,
    lineage: str,
) -> dict[str, Any]:
    attempt_id = f"{case_id}:{stage}:{ordinal:03d}"
    request = {"model": "deepseek-chat", "messages": ["redacted"]}
    response = {"id": f"response-{attempt_id}", "content": "{}"}
    canonical = lambda value: "sha256:" + hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    prompt_hash = canonical(request)
    response_hash = canonical(response)
    selected_profiles = {
        "complete": ["beam.add.v0.3", "column.add.v0.3"],
        "clarification-resume": ["column.add.v0.3"],
        "program-guard": ["beam.add.v0.3"],
    }[case_id]
    profiles = (
        sorted(STAGE1_COMPACT_PROFILE_IDS)
        if stage == "stage1"
        else selected_profiles
    )
    return {
        "attempt_id": attempt_id,
        "parent_attempt_id": parent_attempt_id,
        "case_id": case_id,
        "lineage": lineage,
        "stage": stage,
        "ordinal": ordinal,
        "stage_attempt": 1,
        "correction_reason": None,
        "evidence_class": "live",
        "http_status": 200,
        "fallback_flags": {
            "cached": False,
            "hand_authored": False,
            "prerecorded": False,
            "synthetic": False,
        },
        "private_evidence_detected": False,
        "provider": "deepseek-openai-compatible",
        "model": "deepseek-chat",
        "usage": {
            "prompt_tokens": 101,
            "completion_tokens": 37,
            "total_tokens": 138,
        },
        "raw_request_sha256": prompt_hash,
        "raw_response_sha256": response_hash,
        "request_sha256": prompt_hash,
        "response_sha256": response_hash,
        "request": request,
        "response": response,
        "metadata": {
            "provider": "deepseek-openai-compatible",
            "model": "deepseek-chat",
            "evidence_class": "live",
            "response_id": f"response-{attempt_id}",
            "transport_attempts": 1,
            "usage": {
                "prompt_tokens": 101,
                "completion_tokens": 37,
                "total_tokens": 138,
            },
        },
        "error": None,
        "profile_ids": profiles,
        "profile_versions": ["0.2" for _profile in profiles],
        "profile_hashes": [HASH_A for _profile in profiles],
        "few_shot_ids": (
            [f"{profile}.complete" for profile in profiles]
            if stage == "stage2"
            else []
        ),
        "few_shot_hashes": (
            [HASH_B for _profile in profiles] if stage == "stage2" else []
        ),
    }


def _curation_case(
    *,
    case_id: str,
    stages: tuple[tuple[str, str], ...],
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    stage_ordinals = {"stage1": 0, "stage2": 0}
    parent: str | None = None
    for stage, lineage in stages:
        stage_ordinals[stage] += 1
        attempt = _curation_attempt(
            case_id=case_id,
            stage=stage,
            ordinal=stage_ordinals[stage],
            parent_attempt_id=parent,
            lineage=lineage,
        )
        attempts.append(attempt)
        parent = str(attempt["attempt_id"])
    counts = {
        "stage1": sum(item[0] == "stage1" for item in stages),
        "stage2": sum(item[0] == "stage2" for item in stages),
    }
    if case_id == "program-guard":
        final: dict[str, Any] = {
            "status": "unsupported",
            "reason_code": "STRUCTURAL_ANALYSIS_UNSUPPORTED",
            "complete_repair_success": False,
            "successful_artifact_publishable": False,
            "program_guard_evidence": {
                "source_unchanged": True,
                "stage2_attempts": 0,
                "candidate_output_paths": [],
                "mutation_attempted": False,
            },
        }
    else:
        final = {
            "status": "succeeded",
            "reason_code": None,
            "run_id": f"run-{case_id}",
            "complete_repair_success": True,
            "successful_artifact_publishable": True,
            "artifacts": {
                "manifest": "publication/manifest.json",
                "evaluation": "evaluation.json",
                "successful_ifc": "repaired.ifc",
            },
            "strict_reopen_verification": {
                "status": "passed",
                "l0_pass": True,
                "l1_pass": True,
                "l2_pass": True,
            },
        }
        if case_id == "clarification-resume":
            final.update(
                {
                    "clarification_answer_applied": True,
                    "initial": {
                        "status": "clarification_required",
                        "complete_repair_success": False,
                        "successful_artifact_publishable": False,
                    },
                    "clarification": {
                        "clarification_id": "clarification-001",
                        "reason_code": "missing_required_parameter",
                        "question": "Provide the grouped structural facts.",
                        "answer_modes": ["add_detail", "cancel"],
                    },
                }
            )
    frozen = next(case for case in FROZEN_LIVE_CASES if case.case_id == case_id)
    return {
        "case_id": case_id,
        "request_sha256": "sha256:"
        + hashlib.sha256(frozen.request.encode("utf-8")).hexdigest(),
        "feedback_sha256": (
            None
            if frozen.feedback is None
            else "sha256:"
            + hashlib.sha256(frozen.feedback.encode("utf-8")).hexdigest()
        ),
        "status": "passed",
        "final": final,
        "attempts": attempts,
        "transport_calls": len(attempts),
        "transport_calls_by_stage": counts,
        "synthetic_fallback_used": False,
        "live_evidence_pass": True,
        "private_evidence_detected": False,
        "contract_pass": True,
        "proof_acceptance_eligible": False,
        "proof_validation_status": "pending_plan_12_14",
    }


def _valid_live_curation_result() -> dict[str, Any]:
    cases = [
        _curation_case(
            case_id="complete",
            stages=(("stage1", "initial"), ("stage2", "initial")),
        ),
        _curation_case(
            case_id="clarification-resume",
            stages=(
                ("stage1", "initial"),
                ("stage1", "clarification-resume"),
                ("stage2", "clarification-resume"),
            ),
        ),
        _curation_case(
            case_id="program-guard",
            stages=(("stage1", "initial"),),
        ),
    ]
    return {
        "schema_version": "text2ifc/phase12-live-uat/0.1",
        "status": "passed",
        "evidence_mode": "live",
        "execution_mode": "production_live",
        "provider_evidence_mode": "live",
        "runner_contract_eligible": True,
        "acceptance_eligible": False,
        "proof_validation_status": "pending_plan_12_14",
        "synthetic_fallback_used": False,
        "transport_calls": 6,
        "transport_calls_by_stage": {"stage1": 4, "stage2": 2},
        "provider_models": [
            {
                "provider": "deepseek-openai-compatible",
                "model": "deepseek-chat",
            }
        ],
        "cases": cases,
    }


def test_live_curator_accepts_only_complete_and_resumed_success_transcripts() -> None:
    curator = _curator_module()

    audit = curator.audit_live_uat_result(_valid_live_curation_result())

    assert audit["status"] == "passed"
    assert audit["success_case_ids"] == ["complete", "clarification-resume"]
    assert audit["program_guard_case_id"] == "program-guard"
    assert audit["transport_calls"] == 6


@pytest.mark.parametrize(
    ("defect", "expected_code"),
    (
        ("missing_provider", "LIVE_ATTEMPT_PROVIDER_REQUIRED"),
        ("missing_model", "LIVE_ATTEMPT_MODEL_REQUIRED"),
        ("missing_usage", "LIVE_ATTEMPT_USAGE_REQUIRED"),
        ("missing_raw_response", "LIVE_ATTEMPT_RAW_RESPONSE_REQUIRED"),
        ("redacted_hash_mismatch", "LIVE_ATTEMPT_REDACTED_HASH_MISMATCH"),
        ("missing_profile_hash", "LIVE_ATTEMPT_PROFILE_HASH_REQUIRED"),
        ("missing_few_shot_hash", "LIVE_ATTEMPT_FEW_SHOT_HASH_REQUIRED"),
        ("missing_profile_few_shot", "LIVE_ATTEMPT_PROFILE_ROUTING_MISMATCH"),
        ("fallback_true", "LIVE_ATTEMPT_FALLBACK_FLAG"),
        ("missing_response_id", "LIVE_ATTEMPT_RESPONSE_ID_REQUIRED"),
        ("wrong_profile", "LIVE_ATTEMPT_PROFILE_ROUTING_MISMATCH"),
        ("ordinal_mismatch", "LIVE_ATTEMPT_ORDINAL_MISMATCH"),
        ("broken_parent", "LIVE_ATTEMPT_PARENT_MISMATCH"),
        ("duplicate_attempt", "LIVE_ATTEMPT_ID_MISMATCH"),
        ("non_200", "LIVE_ATTEMPT_TRANSPORT_INVALID"),
        ("missing_correction_reason", "LIVE_ATTEMPT_CORRECTION_REASON_REQUIRED"),
        ("case_count_mismatch", "LIVE_CASE_STAGE_COUNT_MISMATCH"),
        ("aggregate_count_mismatch", "LIVE_AGGREGATE_STAGE_COUNT_MISMATCH"),
        ("provider_model_aggregate", "LIVE_PROVIDER_MODEL_AGGREGATE_MISMATCH"),
        ("usage_metadata_mismatch", "LIVE_ATTEMPT_METADATA_INVALID"),
        ("provider_identity", "LIVE_ATTEMPT_PROVIDER_IDENTITY_INVALID"),
        ("acceptance_self_claim", "LIVE_PROOF_ACCEPTANCE_SELF_CLAIM"),
        ("clarification_lineage", "LIVE_CLARIFICATION_LINEAGE_INVALID"),
        ("terminal_publication", "LIVE_SUCCESS_TERMINAL_INVALID"),
        ("synthetic_fallback", "LIVE_SYNTHETIC_FALLBACK_NOT_FALSE"),
    ),
)
def test_live_curator_rejects_each_single_transcript_defect(
    defect: str,
    expected_code: str,
) -> None:
    curator = _curator_module()
    result = _valid_live_curation_result()
    complete = result["cases"][0]
    first = complete["attempts"][0]
    stage2 = complete["attempts"][1]
    if defect == "missing_provider":
        first["provider"] = ""
    elif defect == "missing_model":
        first["model"] = ""
    elif defect == "missing_usage":
        first["usage"] = {}
    elif defect == "missing_raw_response":
        first.pop("response")
    elif defect == "redacted_hash_mismatch":
        first["response_sha256"] = "sha256:" + "0" * 64
    elif defect == "missing_profile_hash":
        first["profile_hashes"] = []
    elif defect == "missing_few_shot_hash":
        stage2["few_shot_hashes"] = []
    elif defect == "missing_profile_few_shot":
        stage2["few_shot_ids"].pop()
        stage2["few_shot_hashes"].pop()
    elif defect == "fallback_true":
        first["fallback_flags"]["cached"] = True
    elif defect == "missing_response_id":
        first["metadata"].pop("response_id")
    elif defect == "wrong_profile":
        first["profile_ids"].append("door.fill-existing-opening")
        first["profile_versions"].append("0.1")
        first["profile_hashes"].append(HASH_B)
    elif defect == "ordinal_mismatch":
        first["ordinal"] = 2
    elif defect == "broken_parent":
        stage2["parent_attempt_id"] = None
    elif defect == "duplicate_attempt":
        stage2["attempt_id"] = first["attempt_id"]
    elif defect == "non_200":
        first["http_status"] = 503
    elif defect == "missing_correction_reason":
        first["stage_attempt"] = 2
    elif defect == "case_count_mismatch":
        complete["transport_calls_by_stage"]["stage1"] = 2
    elif defect == "aggregate_count_mismatch":
        result["transport_calls_by_stage"]["stage1"] = 5
    elif defect == "provider_model_aggregate":
        result["provider_models"][0]["model"] = "unrelated-model"
    elif defect == "usage_metadata_mismatch":
        first["metadata"]["usage"]["total_tokens"] = 999
    elif defect == "provider_identity":
        first["provider"] = "fake-deepseek"
        first["metadata"]["provider"] = "fake-deepseek"
        result["provider_models"].append(
            {"provider": "fake-deepseek", "model": "deepseek-chat"}
        )
    elif defect == "acceptance_self_claim":
        result["acceptance_eligible"] = True
    elif defect == "clarification_lineage":
        result["cases"][1]["attempts"][1]["lineage"] = "initial"
    elif defect == "terminal_publication":
        complete["final"]["successful_artifact_publishable"] = False
    elif defect == "synthetic_fallback":
        result["synthetic_fallback_used"] = True
    else:  # pragma: no cover - the parametrization is exhaustive.
        raise AssertionError(defect)

    with pytest.raises(ValueError, match=expected_code):
        curator.audit_live_uat_result(result)


def _set_curation_response_document(
    attempt: dict[str, Any],
    document: Mapping[str, Any],
) -> None:
    response = dict(attempt["response"])
    response["content"] = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
    )
    attempt["response"] = response
    attempt["response_sha256"] = "sha256:" + hashlib.sha256(
        json.dumps(
            response,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


@pytest.mark.parametrize(
    ("artifact", "expected_code"),
    (
        ("intent", "LIVE_STAGE1_RESPONSE_ARTIFACT_MISMATCH"),
        ("changeset", "LIVE_STAGE2_RESPONSE_ARTIFACT_MISMATCH"),
    ),
)
def test_live_curator_binds_provider_responses_to_retained_runtime_artifacts(
    artifact: str,
    expected_code: str,
) -> None:
    curator = _curator_module()
    result = _valid_live_curation_result()
    complete = result["cases"][0]
    intent = {
        "operations": [],
        "semantic_bundles": [],
        "provenance": [],
    }
    provider_draft = {
        "schema_version": "text2ifc/ifc-repair-changeset-draft/0.2",
        "draft_id": "draft-complete",
        "base_model_fingerprint": "sha256:" + "1" * 64,
        "source_request_hash": "sha256:" + "2" * 64,
        "semantic_manifest_ref": "semantic-manifests.json",
        "semantic_manifest_sha256": "sha256:" + "3" * 64,
        "scope": {"target_ids": [], "forbidden_ids": []},
        "operations": [],
    }
    changeset = {
        **provider_draft,
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "binding_status": "bound",
        "changeset_id": "changeset-complete",
        "binder_authority": {"semantic_registry": "registered"},
    }
    _set_curation_response_document(
        complete["attempts"][0],
        {
            "schema_version": "text2ifc/ifc-repair-intent-body/0.5",
            **intent,
        },
    )
    _set_curation_response_document(complete["attempts"][1], provider_draft)
    if artifact == "intent":
        intent["operations"] = [{"operation_id": "unrelated-intent"}]
    else:
        provider_draft["base_model_fingerprint"] = "sha256:" + "9" * 64

    with pytest.raises(ValueError, match=expected_code):
        curator.audit_live_artifact_binding(
            result,
            case_id="complete",
            intent=intent,
            provider_draft=provider_draft,
            changeset=changeset,
        )
