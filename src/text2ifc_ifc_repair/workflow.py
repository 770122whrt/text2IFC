"""Evidence-producing end-to-end workflows for IFC repair evaluation."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from text2ifc_agent.providers import ProviderOutput
from text2ifc_text.splits import atomic_write_text

from .apply import apply_changeset
from .benchmark_evaluation import (
    BenchmarkEvaluationInputs,
    ProductionEvaluationInputs,
    evaluate_benchmark,
)
from .context import build_repair_context
from .mutation import remove_window_and_opening
from .operations import create_default_registry
from .projection import project_public_repair_spec, render_repair_request
from .provider_stage import generate_repair_changeset
from .evaluation_projection import (
    assert_public_bundle_has_no_canaries,
    filter_gold_only_canaries,
    project_public_evaluation,
)
from .evaluation import (
    aggregate_level,
    aggregate_operation,
    aggregate_repair,
    evaluation_to_dict,
    make_l3_not_required,
)
from .evaluation_models import CheckResult, EvaluationStatus, EvidenceFact


LARGE_BUILDING_SHA256 = (
    "102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725"
)


class DeterministicPublicRuleProvider:
    """Offline Provider fixture derived exclusively from public contracts."""

    def __init__(self, changeset: Mapping[str, Any]) -> None:
        self._changeset = dict(changeset)

    def generate_candidate(self, **kwargs: Any) -> ProviderOutput:
        del kwargs
        return ProviderOutput(
            text=json.dumps(self._changeset, ensure_ascii=False, sort_keys=True),
            metadata={
                "provider": "deterministic-public-rule",
                "evidence_class": "offline_fake",
                "response_id": "offline-public-rule-001",
            },
        )


def run_offline_window_repair_case(
    **kwargs: Any,
) -> dict[str, Any]:
    """Run the Window case with a public-only deterministic fake Provider."""

    return _run_window_repair_case(
        **kwargs,
        provider=None,
        evidence_class="offline_fake",
        bypass_provider=False,
    )


def run_offline_window_benchmark_case(
    **kwargs: Any,
) -> dict[str, Any]:
    """Run frozen deterministic ChangeSet evidence with zero Provider calls."""

    return _run_window_repair_case(
        **kwargs,
        provider=None,
        evidence_class="offline_benchmark",
        bypass_provider=True,
    )


def run_live_window_repair_case(
    *,
    provider: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run the same public contract with a configured real Provider."""

    return _run_window_repair_case(
        **kwargs,
        provider=provider,
        evidence_class="live_provider_uat",
        bypass_provider=False,
    )


def _run_window_repair_case(
    *,
    source_path: Path | str,
    output_dir: Path | str,
    case_id: str,
    wall_global_id: str,
    opening_global_id: str,
    window_global_id: str,
    expected_source_sha256: str = LARGE_BUILDING_SHA256,
    provider: Any | None,
    evidence_class: str,
    bypass_provider: bool,
) -> dict[str, Any]:
    """Execute one immutable evidence run using a selected Provider."""

    source = Path(source_path).resolve()
    output = Path(output_dir).resolve()
    if output.exists():
        raise FileExistsError(f"evaluation output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        mutation_dir = stage / "mutation"
        remove_window_and_opening(
            source_path=source,
            output_dir=mutation_dir,
            wall_global_id=wall_global_id,
            opening_global_id=opening_global_id,
            window_global_id=window_global_id,
            expected_source_sha256=expected_source_sha256,
        )
        private_manifest = _read_json(
            mutation_dir / "mutation_manifest.private.json"
        )
        public_spec = project_public_repair_spec(
            private_manifest, request_id=case_id
        )
        repair_request = render_repair_request(public_spec)
        request_hash = "sha256:" + hashlib.sha256(
            repair_request.encode("utf-8")
        ).hexdigest()
        registry = create_default_registry()
        failure_policy = registry.require_evaluation_policy(
            str(public_spec["requested_operation_type"])
        )
        public_context = build_repair_context(
            mutation_dir / "damaged.ifc",
            public_spec,
            registry=registry,
        )
        atomic_write_text(stage / "repair_request.txt", repair_request)
        atomic_write_text(
            stage / "public-repair-spec.json", _json(public_spec)
        )
        atomic_write_text(stage / "public-context.json", _json(public_context))

        provider_calls = 0
        selected_provider = provider
        if bypass_provider:
            fake_changeset = _public_rule_changeset(
                case_id=case_id,
                request_hash=request_hash,
                public_spec=public_spec,
                public_context=public_context,
            )
            provider_result = {
                "valid": True,
                "changeset": fake_changeset,
                "issues": [],
                "prompt": {
                    "provider_calls": 0,
                    "evidence_source": "frozen-deterministic-changeset",
                },
            }
        else:
            if selected_provider is None:
                fake_changeset = _public_rule_changeset(
                    case_id=case_id,
                    request_hash=request_hash,
                    public_spec=public_spec,
                    public_context=public_context,
                )
                selected_provider = DeterministicPublicRuleProvider(fake_changeset)
            try:
                provider_calls += 1
                provider_result = generate_repair_changeset(
                    provider=selected_provider,
                    case_id=case_id,
                    repair_request=repair_request,
                    source_request_hash=request_hash,
                    public_spec=public_spec,
                    public_context=public_context,
                    registry=registry,
                    output_dir=stage / "provider",
                )
            except Exception as error:
                if evidence_class != "live_provider_uat":
                    raise
                atomic_write_text(
                    stage / "provider" / "provider-exception.json",
                    _json(
                        {
                            "error_type": type(error).__name__,
                            "message": str(error),
                        }
                    ),
                )
                evaluation = _failure_evaluation(
                    case_id=case_id,
                    evidence_class=evidence_class,
                    failure_stage="provider",
                    issues=[
                        {
                            "code": "PROVIDER_EXECUTION_FAILED",
                            "path": "/provider",
                            "message": f"{type(error).__name__}: {error}",
                        }
                    ],
                    operation_id=f"operation-{case_id}",
                    operation_type=failure_policy.operation_type,
                    policy_id=failure_policy.policy_id,
                    policy_version=failure_policy.version,
                    provider_calls=provider_calls,
                )
                _finalize_evidence_bundle(stage, output, evaluation)
                return evaluation
        if not provider_result["valid"] or provider_result["changeset"] is None:
            evaluation = _failure_evaluation(
                case_id=case_id,
                evidence_class=evidence_class,
                failure_stage="provider",
                issues=provider_result["issues"],
                prompt=provider_result.get("prompt", {}),
                operation_id=f"operation-{case_id}",
                operation_type=failure_policy.operation_type,
                policy_id=failure_policy.policy_id,
                policy_version=failure_policy.version,
                provider_calls=provider_calls,
            )
            _finalize_evidence_bundle(stage, output, evaluation)
            return evaluation
        changeset = provider_result["changeset"]
        application = apply_changeset(
            damaged_ifc_path=mutation_dir / "damaged.ifc",
            repair_request=repair_request,
            changeset=changeset,
            output_path=stage / "repaired.ifc",
            registry=registry,
        )
        atomic_write_text(stage / "audit-report.json", _json(application["audit"]))
        stored_application = json.loads(json.dumps(application))
        if stored_application.get("output"):
            stored_application["output"]["path"] = "repaired.ifc"
        atomic_write_text(
            stage / "application-report.json", _json(stored_application)
        )
        if not application["valid"] or not application["published"]:
            evaluation = _failure_evaluation(
                case_id=case_id,
                evidence_class=evidence_class,
                failure_stage="application",
                issues=application["issues"],
                prompt=provider_result["prompt"],
                operation_id=f"operation-{case_id}",
                operation_type=failure_policy.operation_type,
                policy_id=failure_policy.policy_id,
                policy_version=failure_policy.version,
                provider_calls=provider_calls,
            )
            _finalize_evidence_bundle(stage, output, evaluation)
            return evaluation

        benchmark = evaluate_benchmark(
            BenchmarkEvaluationInputs(
                production=ProductionEvaluationInputs(
                    damaged_ifc_path=mutation_dir / "damaged.ifc",
                    repaired_ifc_path=stage / "repaired.ifc",
                    changeset=changeset,
                    application_result=application,
                    registry=registry,
                ),
                private_original_ifc_path=source,
                private_mutation_mapping={
                    str(operation["operation_id"]): {
                        role: str(private_manifest["target"][role]["global_id"])
                        for role in ("wall", "opening", "window")
                    }
                    for operation in changeset["operations"]
                },
            )
        )
        private_evaluation = dict(benchmark.private_report)
        private_evaluation["case_id"] = case_id
        private_evaluation["evidence_class"] = evidence_class
        private_evaluation["prompt"] = provider_result["prompt"]
        evaluation = project_public_evaluation(
            private_evaluation,
            metadata={
                "case_id": case_id,
                "evidence_class": evidence_class,
                "provider_calls": provider_calls,
            },
        )
        if not evaluation["successful_artifact_publishable"]:
            diagnostic = stage / "diagnostic" / "repaired-candidate.ifc"
            diagnostic.parent.mkdir(parents=True, exist_ok=True)
            os.replace(stage / "repaired.ifc", diagnostic)
            stored_application["output"]["path"] = "diagnostic/repaired-candidate.ifc"
            atomic_write_text(
                stage / "application-report.json", _json(stored_application)
            )
        _finalize_evidence_bundle(
            stage,
            output,
            evaluation,
            private_evaluation=private_evaluation,
            public_prompt=provider_result["prompt"],
            canaries=_private_boundary_canaries(
                private_manifest,
                private_evaluation=private_evaluation,
                authorized_public_bundle={
                    "damaged_ifc": mutation_dir / "damaged.ifc",
                    "application_output": (
                        stage / "repaired.ifc"
                        if (stage / "repaired.ifc").is_file()
                        else stage / "diagnostic" / "repaired-candidate.ifc"
                    ),
                },
            ),
        )
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return evaluation


def _public_rule_changeset(
    *,
    case_id: str,
    request_hash: str,
    public_spec: Mapping[str, Any],
    public_context: Mapping[str, Any],
) -> dict[str, Any]:
    description = str(public_spec["target"]["description"])
    candidates = [
        candidate
        for candidate in public_context["candidate_targets"]
        if str(candidate["name"]) == description
    ]
    if len(candidates) != 1:
        raise ValueError("PUBLIC_RULE_TARGET_AMBIGUOUS")
    wall_id = str(candidates[0]["ifc_global_id"])
    opening = public_spec["opening"]
    reference = public_spec["target"]["local_reference"]
    evidence = [
        "spec:/opening",
        "spec:/target/local_reference",
        "context:/candidate_targets/0",
    ]
    return {
        "schema_version": "text2ifc/ifc-repair-changeset/0.1",
        "changeset_id": f"changeset-{case_id}",
        "base_model_fingerprint": public_context["base_model_fingerprint"],
        "source_request_hash": request_hash,
        "scope": {"target_ids": [wall_id], "forbidden_ids": []},
        "evidence_refs": evidence,
        "preconditions": ["target_exists", "opening_interval_available"],
        "postconditions": ["opening_voids_wall", "window_fills_opening"],
        "operations": [
            {
                "operation_id": f"operation-{case_id}",
                "operation_type": public_spec["requested_operation_type"],
                "target": {"wall_global_id": wall_id},
                "parameters": {
                    "position": {
                        "reference": reference["reference"],
                        "center_offset_mm": reference[
                            "opening_center_offset_mm"
                        ],
                    },
                    "opening": {
                        "width_mm": opening["width_mm"],
                        "height_mm": opening["height_mm"],
                        "sill_height_mm": opening["sill_height_mm"],
                    },
                    "window": {"fit_opening": True},
                },
                "evidence_refs": evidence,
            }
        ],
    }


def _artifact_manifest(
    root: Path,
    *,
    case_id: str,
    evidence_class: str,
    prompt: Mapping[str, Any],
) -> dict[str, Any]:
    artifacts = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative.startswith("private/") or relative.endswith(".private.json"):
            continue
        artifacts.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size,
                "visibility": "public_or_runtime",
            }
        )
    return {
        "schema_version": "text2ifc/ifc-repair-artifact-manifest/0.1",
        "case_id": case_id,
        "evidence_class": evidence_class,
        "prompt": dict(prompt),
        "private_input_exclusion": {
            "provider_received_private_artifacts": False,
            "provider_input_artifacts": [
                "repair_request.txt",
                "public-repair-spec.json",
                "public-context.json",
                "public ChangeSet schema",
                "public operation definitions",
            ],
        },
        "artifacts": artifacts,
    }


def _failure_evaluation(
    *,
    case_id: str,
    evidence_class: str,
    failure_stage: str,
    issues: Any,
    operation_id: str,
    operation_type: str,
    policy_id: str,
    policy_version: str,
    provider_calls: int = 0,
    prompt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    frozen_issues = list(issues)
    application = _terminal_failure_check(
        check_id="application.valid",
        status=EvaluationStatus.FAILED,
        reason="Repair application could not reach a valid published candidate.",
        failure_stage=failure_stage,
        issues=frozen_issues,
    )
    preservation = _terminal_failure_check(
        check_id="preservation.valid",
        status=EvaluationStatus.NOT_EVALUABLE,
        reason="Preservation cannot be evaluated before a repaired candidate exists.",
        failure_stage=failure_stage,
        issues=frozen_issues,
    )
    l1_check = _terminal_failure_check(
        check_id="l1.pre-application",
        status=EvaluationStatus.NOT_EVALUABLE,
        reason="L1 cannot be evaluated before a repaired candidate exists.",
        failure_stage=failure_stage,
        issues=frozen_issues,
    )
    l2_check = _terminal_failure_check(
        check_id="l2.pre-application",
        status=EvaluationStatus.NOT_EVALUABLE,
        reason="L2 cannot be evaluated before a repaired candidate exists.",
        failure_stage=failure_stage,
        issues=frozen_issues,
    )
    l1 = aggregate_level(
        level="L1",
        checks=(l1_check,),
        reason="No candidate was available for independent L1 evaluation.",
        evidence=l1_check.evidence,
    )
    l2 = aggregate_level(
        level="L2",
        checks=(l2_check,),
        reason="No candidate was available for semantic L2 evaluation.",
        evidence=l2_check.evidence,
    )
    l3_observation = CheckResult(
        check_id="l3.pre-application",
        policy_id="l3.v1.1-observation",
        applicability="informational",
        mandatory=False,
        status=EvaluationStatus.NOT_EVALUABLE,
        reason="No authoring identity exists before application.",
        evidence=l2_check.evidence,
    )
    l3 = make_l3_not_required(
        checks=(l3_observation,),
        reason="L3 authoring and identity exactness is not required in v1.1.",
        evidence=l3_observation.evidence,
    )
    operation = aggregate_operation(
        operation_id=operation_id,
        operation_type=operation_type,
        mandatory=True,
        policy_id=policy_id,
        policy_version=policy_version,
        levels=(l1, l2, l3),
        reason="The requested operation did not reach evaluable application output.",
        evidence=application.evidence,
    )
    terminal = aggregate_repair(
        policy_version="phase8.1",
        application=application,
        preservation=preservation,
        operations=(operation,),
        reason="Workflow terminated before a publishable repaired candidate existed.",
        evidence=application.evidence,
        diagnostic_artifact_retained=False,
    )
    return project_public_evaluation(
        evaluation_to_dict(terminal),
        metadata={
            "case_id": case_id,
            "evidence_class": evidence_class,
            "provider_calls": provider_calls,
            "failure_stage": failure_stage,
            "issues": frozen_issues,
            "prompt": dict(prompt or {}),
        },
    )


def _terminal_failure_check(
    *,
    check_id: str,
    status: EvaluationStatus,
    reason: str,
    failure_stage: str,
    issues: list[Any],
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        policy_id="evaluation.phase8",
        applicability="required",
        mandatory=True,
        status=status,
        reason=reason,
        evidence=(
            EvidenceFact(
                fact_id=f"{check_id}.evidence",
                source_kind="workflow_failure",
                source_ref=f"workflow:{failure_stage}",
                expected_state="available",
                actual_state="unavailable",
                expected_value="valid publishable repaired candidate",
                actual_value={"failure_stage": failure_stage, "issues": issues},
                provenance=("workflow-terminal-failure",),
            ),
        ),
    )


def _finalize_evidence_bundle(
    stage: Path,
    output: Path,
    evaluation: Mapping[str, Any],
    *,
    private_evaluation: Mapping[str, Any] | None = None,
    public_prompt: Mapping[str, Any] | None = None,
    canaries: tuple[str, ...] = (),
) -> None:
    atomic_write_text(stage / "evaluation_report.json", _json(evaluation))
    if private_evaluation is not None:
        private_dir = stage / "private"
        private_dir.mkdir(parents=True, exist_ok=True)
        atomic_write_text(
            private_dir / "evaluation-private.json", _json(private_evaluation)
        )
        atomic_write_text(stage / "evaluation-public.json", _json(evaluation))
    atomic_write_text(stage / "report.md", _render_chinese_report(evaluation))
    manifest = _artifact_manifest(
        stage,
        case_id=str(evaluation["case_id"]),
        evidence_class=str(evaluation["evidence_class"]),
        prompt=public_prompt or evaluation.get("prompt", {}),
    )
    atomic_write_text(stage / "artifact-manifest.json", _json(manifest))
    if canaries:
        public_files = tuple(
            path
            for path in stage.rglob("*")
            if path.is_file()
            and not path.relative_to(stage).as_posix().startswith("private/")
            and not path.name.endswith(".private.json")
        )
        assert_public_bundle_has_no_canaries(
            {"public_files": public_files}, canaries
        )
    os.replace(stage, output)


def _render_chinese_report(evaluation: Mapping[str, Any]) -> str:
    status = "通过" if evaluation["complete_repair_success"] else "失败"
    evidence_class = str(evaluation["evidence_class"])
    title = (
        "IFC2X3 ChangeSet 真实 Provider UAT 报告"
        if evidence_class == "live_provider_uat"
        else "IFC2X3 ChangeSet 离线确定性验证报告"
    )
    provider_note = (
        "本次运行使用已配置的真实 Provider，结果按 UAT 证据保存。\n"
        if evidence_class == "live_provider_uat"
        else "本次运行使用公开输入驱动的确定性 fake Provider，仅作为自动测试证据，"
        "未冒充真实 Provider UAT。真实 Provider 的结果必须单独保存并标记。\n"
    )
    lines = (
        f"# {title}\n\n"
        f"- 案例：`{evaluation['case_id']}`\n"
        f"- 证据类型：`{evidence_class}`\n"
        f"- 完整修复结果：**{status}**\n"
    )
    if evaluation.get("operations") and "levels" in evaluation["operations"][0]:
        levels = {
            level["level"]: level["status"]
            for level in evaluation["operations"][0]["levels"]
        }
        lines += (
            f"- L1: `{levels.get('L1')}`\n"
            f"- L2: `{levels.get('L2')}`\n"
            f"- L3: `{levels.get('L3')}`\n"
            f"- successful artifact publishable: "
            f"`{evaluation.get('successful_artifact_publishable')}`\n"
        )
    elif evaluation.get("operations"):
        metrics = evaluation["operations"][0]["metrics"]
        lines += (
            f"- 洞口中心误差：{metrics['center_error_mm']} mm\n"
            f"- 方向误差：{metrics['orientation_error_degrees']}°\n"
            f"- 恢复洞口体积：{metrics['restored_void_volume_m3']} m³\n"
            f"- 非目标漂移：{len(evaluation['common']['unexpected_changed_ids'])} 项\n"
        )
    elif evaluation.get("failure_stage"):
        lines += f"- 失败阶段：`{evaluation['failure_stage']}`\n"
    return lines + "\n## 真实 Provider UAT\n\n" + provider_note


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def _private_boundary_canaries(
    private_manifest: Mapping[str, Any],
    *,
    private_evaluation: Mapping[str, Any],
    authorized_public_bundle: Any | None = None,
) -> tuple[str, ...]:
    # Mutation inputs such as the Host/Opening IDs and source path can also be
    # authorized public workflow inputs. Only evaluator-private semantic Gold
    # facts are valid whole-bundle canaries.
    del private_manifest
    canaries = _private_semantic_canaries(private_evaluation)
    if authorized_public_bundle is None:
        return canaries
    return filter_gold_only_canaries(canaries, authorized_public_bundle)


def _private_semantic_canaries(
    private_evaluation: Mapping[str, Any],
) -> tuple[str, ...]:
    """Derive Gold-only semantic values and identifiers from private L2 evidence."""

    tokens: set[str] = set()
    semantic_prefixes = (
        "window.material",
        "window.classification",
        "window.pset",
        "window.quantity",
        "window.name",
        "window.tag",
        "window.instance",
        "window.is-external",
    )
    for operation in private_evaluation.get("operations", ()):
        for level in operation.get("levels", ()):
            if level.get("level") != "L2":
                continue
            for check in level.get("checks", ()):
                if not str(check.get("check_id", "")).startswith(semantic_prefixes):
                    continue
                for evidence in check.get("evidence", ()):
                    if evidence.get("source_kind") != "private_original":
                        continue
                    tokens.update(_private_canary_scalars(evidence.get("expected_value")))
                    source_ref = str(evidence.get("source_ref", ""))
                    if source_ref:
                        tokens.add(source_ref)
    return tuple(sorted(token for token in tokens if len(token.encode("utf-8")) >= 4))


def _private_canary_scalars(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        children = (
            (
                value.get("value"),
                value.get("entity_source"),
                value.get("pset_path"),
            )
            if "value" in value
            else tuple(value.values())
        )
        tokens: set[str] = set()
        for child in children:
            tokens.update(_private_canary_scalars(child))
        return tokens
    if isinstance(value, (list, tuple)):
        tokens = set()
        for child in value:
            tokens.update(_private_canary_scalars(child))
        return tokens
    if isinstance(value, str) and value:
        return {value}
    return set()
