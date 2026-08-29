"""Route-faithful Phase 12.1 Stage 1.5 semantic evaluation.

This runner never executes Stage 2 or writes IFC.  Public retrieval and
Provider predictions are durably frozen before the evaluator may open Gold.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
from time import perf_counter
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from text2ifc_agent.openai_compat import (  # noqa: E402
    OpenAICompatibleLiveProvider,
    load_openai_compatible_runtime_config,
)
from text2ifc_ifc_repair.property_admissibility import (  # noqa: E402
    admit_property_decision,
)
from text2ifc_ifc_repair.property_intent import (  # noqa: E402
    ExactPropertyIntent,
    NaturalLanguagePropertyIntent,
    PropertyResolutionStatus,
    resolve_exact_property_intent,
)
from text2ifc_ifc_repair.property_resolution_stage import (  # noqa: E402
    TEMPLATE_ID as PROPERTY_RESOLUTION_TEMPLATE_ID,
    generate_property_resolution_decision,
)
from text2ifc_ifc_repair.repair_intent import PublicProvenance  # noqa: E402
from text2ifc_knowledge.property_runtime import (  # noqa: E402
    PropertyKnowledgeRuntime,
    create_property_runtime_from_environment,
    load_property_runtime_config,
)
from text2ifc_text.splits import atomic_write_text  # noqa: E402


PREDICTION_LEDGER_SCHEMA = (
    "text2ifc/phase12.1-property-semantic-prediction-ledger/0.2"
)
SEMANTIC_REPORT_SCHEMA = "text2ifc/phase12.1-property-semantic-evaluation/0.3"
DEFAULT_OUTPUT = (
    ROOT / "dataset/processed/ifc-repair-runs/phase12-1-semantic-evaluation"
)
PLAN06_ACCEPTANCE_COMMIT = "350f4030fbae9c75c7c1d6341d63f35c07410bd8"
FROZEN_FIXTURE_PATHS = (
    "tests/fixtures/knowledge/phase10_2_property_retrieval.json",
    "tests/fixtures/knowledge/phase12_1_property_resolution.json",
    "tests/fixtures/knowledge/phase12_1_property_retrieval_public.json",
)
SEMANTIC_TAXONOMY_PATH = (
    "tests/fixtures/knowledge/phase12_1_property_semantic_taxonomy_v0_3.json"
)
SEMANTIC_TAXONOMY_VERSION = "text2ifc/property-semantic-taxonomy/0.3"
SEMANTIC_TAXONOMY_SHA256 = (
    "sha256:d20539658c42ecf252b05579a5262a6b4d536152802995b790a59238972cfc04"
)
HISTORICAL_SEMANTIC_TAXONOMY_VERSION = (
    "text2ifc/property-semantic-taxonomy/0.2"
)
TAXONOMY_RESCORE_SOURCE_RUN_ID = (
    "post-fix-semantic-20260828T143544739263Z"
)
TAXONOMY_RESCORE_SOURCE_LEDGER_SHA256 = (
    "0ff4198396ece4740389f1b570975d99dff05938fdb2f01f1ddcc6964ec73ce3"
)
TAXONOMY_RESCORE_SOURCE_REPORT_SHA256 = (
    "3d059a0b20a64f4020aeedbce4f0db8d9b019c0aeaee24ef6214be4ffcdfd097"
)
SEMANTIC_BENCHMARK_ID = "phase12.1-stage1.5-semantic-acceptance"
DEFAULT_EVALUATION_LABEL = "STAGE15_SEMANTIC_EVALUATION"
POST_FIX_EVALUATION_LABEL = "POST_FIX_STAGE15_ACCEPTANCE_EVALUATION"
CANONICAL_PROPERTY = re.compile(
    r"(?P<set>[A-Za-z_][A-Za-z0-9_]*)\.(?P<property>[A-Za-z_][A-Za-z0-9_]*)"
)
PRIVATE_PROVIDER_KEYS = frozenset(
    {
        "expected",
        "expected_route",
        "authorize",
        "benchmark_gold",
        "private_gold",
        "mutation_recipe",
        "deleted_identity",
    }
)
OUTCOME_NAMES = (
    "correct_offered_candidate_selection",
    "clarification",
    "unsupported",
    "retrieval_failure",
    "semantic_selection_failure",
    "unoffered_selection",
    "malformed_retry_exhaustion",
    "admissibility_rejection",
    "infrastructure_runtime_failure",
)


def _environment(path: Path) -> dict[str, str]:
    values = dict(os.environ)
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _close_runtime(runtime: Any | None) -> None:
    if runtime is None:
        return
    close = getattr(getattr(runtime, "vector_index", None), "close", None)
    if callable(close):
        close()


def probe_property_runtime_readiness(
    *,
    environment: Mapping[str, str] | None = None,
    project_root: Path | str = ROOT,
    require_no_network: bool = True,
) -> dict[str, Any]:
    """Open the production BGE/Qdrant runtime without any Provider call."""

    root = Path(project_root).resolve()
    try:
        config = load_property_runtime_config(
            environment,
            project_root=root,
        )
    except Exception as error:
        return {
            "status": "not_ready",
            "reason_code": str(error).split(":", 1)[0][:128]
            or type(error).__name__,
            "provider_calls": 0,
            "network_allowed": False,
            "configuration": None,
        }
    configuration = config.to_redacted_dict()
    if require_no_network and config.qdrant_url is not None:
        return {
            "status": "not_ready",
            "reason_code": "NO_NETWORK_PROBE_REQUIRES_LOCAL_QDRANT",
            "provider_calls": 0,
            "network_allowed": False,
            "configuration": configuration,
        }

    started = perf_counter()
    runtime = None
    try:
        runtime = create_property_runtime_from_environment(
            environment,
            project_root=root,
        )
        health = runtime.health.to_dict()
        ready = (
            health.get("status") == "ready"
            and health.get("acceptance_eligible") is True
        )
        return {
            "status": "ready" if ready else "not_ready",
            "reason_code": (
                None
                if ready
                else health.get("reason_code") or "PROPERTY_RUNTIME_NOT_READY"
            ),
            "provider_calls": 0,
            "network_allowed": not require_no_network,
            "configuration": configuration,
            "health": health,
            "latency_ms": (perf_counter() - started) * 1000.0,
        }
    except Exception as error:
        return {
            "status": "not_ready",
            "reason_code": str(error).split(":", 1)[0][:128]
            or type(error).__name__,
            "provider_calls": 0,
            "network_allowed": not require_no_network,
            "configuration": configuration,
            "latency_ms": (perf_counter() - started) * 1000.0,
        }
    finally:
        _close_runtime(runtime)


@dataclass
class _ProviderTiming:
    attempt: int
    latency_ms: float
    usage: dict[str, Any]
    error: str | None


class _TimedProvider:
    """Measure Provider attempts while preserving the general evidence delegate."""

    def __init__(self, provider: Any) -> None:
        self._provider = provider
        self.calls: list[_ProviderTiming] = []

    def provider_evidence_delegate(self) -> Any:
        return self._provider

    def __getattr__(self, name: str):
        if name not in {"generate_live", "generate_candidate"}:
            raise AttributeError(name)
        method = getattr(self._provider, name, None)
        if not callable(method):
            raise AttributeError(name)

        def measured(**arguments):
            return self._call(name, arguments)

        return measured

    def _call(self, method_name: str, arguments: Mapping[str, Any]):
        method = getattr(self._provider, method_name)
        started = perf_counter()
        result: Any = None
        error_name: str | None = None
        try:
            result = method(**dict(arguments))
            return result
        except Exception as error:
            error_name = type(error).__name__
            raise
        finally:
            output = getattr(result, "output", result)
            metadata = dict(getattr(output, "metadata", {}) or {})
            usage = metadata.get("usage")
            self.calls.append(
                _ProviderTiming(
                    attempt=int(dict(arguments.get("state", {})).get("attempt", 1)),
                    latency_ms=max(0.0, (perf_counter() - started) * 1000.0),
                    usage=dict(usage) if isinstance(usage, Mapping) else {},
                    error=error_name,
                )
            )


def _json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ) + "\n"


def _write_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, _json(value))


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _load_public_cases(project_root: Path) -> list[dict[str, Any]]:
    from scripts.ifc_repair import run_phase12_offline

    return run_phase12_offline._property_evaluation_public_cases(project_root)
def _canonical_file_sha256(path: Path) -> str:
    canonical_bytes = path.read_bytes().replace(b"\r\n", b"\n")
    return "sha256:" + hashlib.sha256(canonical_bytes).hexdigest()



def _load_gold_cases(
    project_root: Path,
    *,
    taxonomy_path: str = SEMANTIC_TAXONOMY_PATH,
    taxonomy_version: str = SEMANTIC_TAXONOMY_VERSION,
    taxonomy_sha256: str = SEMANTIC_TAXONOMY_SHA256,
) -> list[dict[str, Any]]:
    from scripts.ifc_repair import run_phase12_offline

    base_cases = run_phase12_offline._property_evaluation_gold_cases(project_root)
    resolved_taxonomy_path = project_root / taxonomy_path
    if _canonical_file_sha256(resolved_taxonomy_path) != taxonomy_sha256:
        raise RuntimeError("PHASE12_1_SEMANTIC_TAXONOMY_CHANGED")
    taxonomy = _read(resolved_taxonomy_path)
    if (
        taxonomy.get("schema_version") != taxonomy_version
        or taxonomy.get("benchmark_id") != SEMANTIC_BENCHMARK_ID
        or taxonomy.get("case_count") != 60
    ):
        raise RuntimeError("PHASE12_1_SEMANTIC_TAXONOMY_INVALID")
    taxonomy_rows = list(taxonomy.get("cases", ()))
    taxonomy_by_id = {str(row.get("case_id")): row for row in taxonomy_rows}
    base_ids = {str(case["id"]) for case in base_cases}
    if (
        len(taxonomy_rows) != 60
        or len(taxonomy_by_id) != 60
        or set(taxonomy_by_id) != base_ids
    ):
        raise RuntimeError("PHASE12_1_SEMANTIC_TAXONOMY_JOIN_MISMATCH")
    allowed_routes = {
        "exact_bypass",
        "confirmed_standard",
        "clarification_required",
        "unsupported_property",
        "unsupported_operation",
        "inadmissible",
    }
    merged: list[dict[str, Any]] = []
    for base_case in base_cases:
        case = dict(base_case)
        taxonomy_row = taxonomy_by_id[str(case["id"])]
        expected_route = str(taxonomy_row.get("expected_route") or "")
        if expected_route not in allowed_routes:
            raise RuntimeError("PHASE12_1_SEMANTIC_TAXONOMY_ROUTE_INVALID")
        if bool(case["authorize"]) and expected_route not in {
            "exact_bypass",
            "confirmed_standard",
        }:
            raise RuntimeError("PHASE12_1_SEMANTIC_TAXONOMY_AUTHORITY_CONFLICT")
        if not bool(case["authorize"]) and expected_route in {
            "exact_bypass",
            "confirmed_standard",
        }:
            raise RuntimeError("PHASE12_1_SEMANTIC_TAXONOMY_AUTHORITY_CONFLICT")
        case["expected_route"] = expected_route
        case["semantic_category"] = str(taxonomy_row["semantic_category"])
        merged.append(case)
    return merged


def verify_frozen_fixtures(
    project_root: Path | str = ROOT,
    *,
    checkpoint: str = PLAN06_ACCEPTANCE_COMMIT,
) -> None:
    root = Path(project_root).resolve()
    completed = subprocess.run(
        ["git", "diff", "--exit-code", checkpoint, "--", *FROZEN_FIXTURE_PATHS],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("PHASE12_1_FROZEN_FIXTURE_CHANGED")
    if (
        _canonical_file_sha256(root / SEMANTIC_TAXONOMY_PATH)
        != SEMANTIC_TAXONOMY_SHA256
    ):
        raise RuntimeError("PHASE12_1_SEMANTIC_TAXONOMY_CHANGED")



def _source(case: Mapping[str, Any]) -> PublicProvenance:
    return PublicProvenance(
        source_kind="user_request",
        reference=f"evaluation-public-case:{case['case_id']}",
        excerpt=str(case["property_phrase"]),
    )


def _exact_bypass_prediction(
    case: Mapping[str, Any],
    runtime: PropertyKnowledgeRuntime,
) -> dict[str, Any]:
    match = CANONICAL_PROPERTY.fullmatch(str(case["property_phrase"]))
    if match is None or runtime.registry is None:
        raise RuntimeError("EXACT_BYPASS_INPUT_INVALID")
    intent = ExactPropertyIntent(
        set_name=match.group("set"),
        property_name=match.group("property"),
        value=case["raw_value"],
        requested_value_type=None,
        requested_unit=case["raw_unit"],
        scope=case["scope"],
        source=_source(case),
        intent_kind="exact_property",
    )
    resolution = resolve_exact_property_intent(
        intent,
        target_ifc_class=str(case["target_ifc_class"]),
        existing_facts=(),
        registry=runtime.registry,
    )
    selected_path = (
        str(case["property_phrase"])
        if resolution.status is PropertyResolutionStatus.STANDARD_RESOLVED
        else None
    )
    return {
        "case_id": str(case["case_id"]),
        "route": "exact_bypass",
        "query": None,
        "candidate_set": None,
        "candidate_paths": [],
        "stage_valid": None,
        "classification": "exact_bypass",
        "selected_candidate_id": None,
        "selected_path": selected_path,
        "issue_codes": [],
        "error_code": None,
        "admissibility_status": (
            "passed" if selected_path is not None else "rejected"
        ),
        "admissibility_reason_code": resolution.reason_code,
        "provider_attempt_count": 0,
        "retry_count": 0,
        "token_usage": {},
        "latency_ms": 0.0,
        "attempts": [],
        "provider_acceptance_eligible": True,
    }


def _attempt_lineage(
    *,
    stage_result: Mapping[str, Any],
    provider_dir: Path,
    timings: Sequence[_ProviderTiming],
) -> list[dict[str, Any]]:
    lineage: list[dict[str, Any]] = []
    for index, attempt in enumerate(stage_result.get("attempts", ())):
        attempt_dir = provider_dir / str(attempt["artifact_dir"])
        metadata_path = attempt_dir / "provider-metadata.json"
        metadata = _read(metadata_path) if metadata_path.is_file() else {}
        timing = timings[index] if index < len(timings) else None
        usage = metadata.get("usage")
        if not isinstance(usage, Mapping) and timing is not None:
            usage = timing.usage
        lineage.append(
            {
                "attempt_id": attempt["attempt_id"],
                "attempt": int(attempt["attempt"]),
                "status": attempt["status"],
                "parse_status": attempt["parse_status"],
                "issue_codes": [
                    str(issue["code"]) for issue in attempt.get("issues", ())
                ],
                "evidence_class": attempt["evidence_class"],
                "acceptance_eligible": bool(attempt["acceptance_eligible"]),
                "latency_ms": 0.0 if timing is None else timing.latency_ms,
                "usage": dict(usage) if isinstance(usage, Mapping) else {},
                "provider_error": None if timing is None else timing.error,
                "renderer_input_path": str(
                    (attempt_dir / "renderer-input.json").resolve()
                ),
                "rendered_prompt_path": str(
                    (attempt_dir / "rendered-prompt.txt").resolve()
                ),
                "raw_response_path": str(
                    (attempt_dir / "raw-response.json").resolve()
                ),
                "parsed_response_path": str(
                    (attempt_dir / "parsed-response.json").resolve()
                ),
                "validation_feedback_path": str(
                    (attempt_dir / "validation-feedback.json").resolve()
                ),
                "provider_metadata_path": str(metadata_path.resolve()),
            }
        )
    return lineage


def _summed_usage(attempts: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    keys = ("prompt_tokens", "completion_tokens", "total_tokens")
    return {
        key: sum(
            int(dict(attempt.get("usage", {})).get(key, 0) or 0)
            for attempt in attempts
        )
        for key in keys
    }


def _persist_prediction(
    case_root: Path,
    prediction: Mapping[str, Any],
) -> dict[str, Any]:
    path = (case_root / "prediction.json").resolve()
    document = json.loads(json.dumps(dict(prediction), ensure_ascii=False))
    _write_atomic(path, document)
    return {
        "case_id": document["case_id"],
        "prediction_path": str(path),
        "prediction": document,
        **document,
    }


def _execute_natural_case(
    *,
    case: Mapping[str, Any],
    case_index: int,
    case_root: Path,
    runtime: PropertyKnowledgeRuntime,
    provider: _TimedProvider,
) -> dict[str, Any]:
    try:
        retrieval = runtime.retrieve(
            run_id="phase12-1-semantic-evaluation",
            request_id="phase12-1-semantic-evaluation",
            model_id="stage15-semantic-evaluation",
            operation_id=f"property-semantic-operation-{case_index + 1}",
            operation_type="set_occurrence_properties",
            claim_id=f"property-semantic-claim-{case_index + 1}",
            property_phrase=str(case["property_phrase"]),
            target_ifc_class=str(case["target_ifc_class"]),
            raw_value=case["raw_value"],
            raw_unit=case["raw_unit"],
            scope=case["scope"],
        )
    except Exception as error:
        return {
            "case_id": str(case["case_id"]),
            "route": "infrastructure_runtime_failure",
            "query": None,
            "candidate_set": None,
            "candidate_paths": [],
            "stage_valid": False,
            "classification": "invalid",
            "selected_candidate_id": None,
            "selected_path": None,
            "issue_codes": [],
            "error_code": str(error).split(":", 1)[0],
            "admissibility_status": "not_run",
            "admissibility_reason_code": None,
            "provider_attempt_count": 0,
            "retry_count": 0,
            "token_usage": {},
            "latency_ms": 0.0,
            "attempts": [],
            "provider_acceptance_eligible": False,
        }

    _write_atomic(case_root / "public-query.json", retrieval.query)
    _write_atomic(case_root / "offered-top-k.json", retrieval.candidate_set)
    candidate_paths = [
        str(item["canonical_path"])
        for item in retrieval.candidate_set["candidates"]
    ]
    if not candidate_paths:
        return {
            "case_id": str(case["case_id"]),
            "route": "not_invoked_no_candidates",
            "query": retrieval.query,
            "candidate_set": retrieval.candidate_set,
            "candidate_paths": [],
            "stage_valid": None,
            "classification": "not_invoked",
            "selected_candidate_id": None,
            "selected_path": None,
            "issue_codes": [],
            "error_code": None,
            "admissibility_status": "not_run",
            "admissibility_reason_code": "PROPERTY_RETRIEVAL_EMPTY",
            "provider_attempt_count": 0,
            "retry_count": 0,
            "token_usage": {},
            "latency_ms": 0.0,
            "attempts": [],
            "provider_acceptance_eligible": True,
        }

    before = len(provider.calls)
    provider_dir = case_root / "provider"
    stage_result = generate_property_resolution_decision(
        query=retrieval.query,
        candidate_set=retrieval.candidate_set,
        output_dir=provider_dir,
        provider=provider,
    )
    timings = provider.calls[before:]
    attempts = _attempt_lineage(
        stage_result=stage_result,
        provider_dir=provider_dir,
        timings=timings,
    )
    decision = stage_result.get("decision")
    selected_id = (
        None
        if not isinstance(decision, Mapping)
        else decision.get("selected_candidate_id")
    )
    offered = {
        str(item["candidate_id"]): item
        for item in retrieval.candidate_set["candidates"]
    }
    selected = None if selected_id is None else offered.get(str(selected_id))
    selected_path = (
        None if selected is None else str(selected["canonical_path"])
    )

    admission_status = "not_run"
    admission_reason: str | None = None
    if bool(stage_result.get("valid")) and isinstance(decision, Mapping):
        assert runtime.policy is not None
        assert runtime.registry is not None
        claim = NaturalLanguagePropertyIntent(
            property_phrase=str(case["property_phrase"]),
            raw_value=case["raw_value"],
            raw_unit=case["raw_unit"],
            scope=case["scope"],
            source=_source(case),
        )
        admission = admit_property_decision(
            query=retrieval.query,
            candidate_set=retrieval.candidate_set,
            decision=decision,
            decision_trace=stage_result["trace"],
            policy=runtime.policy,
            records=runtime.records,
            registry=runtime.registry,
            claim=claim,
        )
        admission_document = admission.to_dict()
        _write_atomic(case_root / "admissibility.json", admission_document)
        admission_status = admission.status
        admission_reason = admission.reason_code

    issue_codes = [
        code
        for attempt in attempts
        for code in attempt["issue_codes"]
    ]
    issue_codes.extend(
        str(issue["code"]) for issue in stage_result.get("issues", ())
    )
    issue_codes = sorted(set(issue_codes))
    infrastructure_failure = (
        "PROPERTY_PROVIDER_REQUEST_FAILED" in issue_codes
        or stage_result.get("error_code")
        in {
            "PROPERTY_RESOLUTION_ATTEMPT_LIMIT_INVALID",
            "PROPERTY_RESOLUTION_INPUT_INVALID",
            "PROPERTY_RESOLUTION_PROVIDER_INVALID",
        }
    )
    return {
        "case_id": str(case["case_id"]),
        "route": (
            "infrastructure_runtime_failure"
            if infrastructure_failure
            else "property_resolution"
        ),
        "query": retrieval.query,
        "candidate_set": retrieval.candidate_set,
        "candidate_paths": candidate_paths,
        "stage_valid": bool(stage_result.get("valid")),
        "classification": str(stage_result.get("classification") or "invalid"),
        "selected_candidate_id": selected_id,
        "selected_path": selected_path,
        "issue_codes": issue_codes,
        "error_code": stage_result.get("error_code"),
        "prompt": dict(stage_result.get("prompt") or {}),
        "admissibility_status": admission_status,
        "admissibility_reason_code": admission_reason,
        "provider_attempt_count": len(attempts),
        "retry_count": max(0, len(attempts) - 1),
        "token_usage": _summed_usage(attempts),
        "latency_ms": sum(float(item["latency_ms"]) for item in attempts),
        "attempts": attempts,
        "provider_acceptance_eligible": bool(
            stage_result.get("acceptance_eligible")
        ),
    }


def _prediction_abort_reason(
    prediction: Mapping[str, Any],
    *,
    require_genuine_provider: bool,
) -> str | None:
    if prediction.get("route") == "infrastructure_runtime_failure":
        issue_codes = [str(item) for item in prediction.get("issue_codes", ())]
        if "PROPERTY_PROVIDER_REQUEST_FAILED" in issue_codes:
            return "PROPERTY_PROVIDER_REQUEST_FAILED"
        return str(
            prediction.get("error_code") or "INFRASTRUCTURE_RUNTIME_FAILURE"
        )
    if not require_genuine_provider:
        return None
    attempts = list(prediction.get("attempts", ()))
    if prediction.get("route") == "property_resolution" and (
        not attempts
        or any(str(item.get("evidence_class")) != "live" for item in attempts)
    ):
        return "GENUINE_PROVIDER_EVIDENCE_REQUIRED"
    return None


def _prediction_ledger(
    *,
    rows: Sequence[Mapping[str, Any]],
    runtime_health: Mapping[str, Any],
    destination: Path,
    status: str,
    reason_code: str | None,
    expected_case_count: int,
    abort_case_id: str | None,
    require_genuine_provider: bool,
    evaluation_label: str = DEFAULT_EVALUATION_LABEL,
) -> dict[str, Any]:
    invoked = [row for row in rows if row["route"] == "property_resolution"]
    live_eligible = (
        status == "completed"
        and require_genuine_provider
        and bool(invoked)
        and runtime_health.get("acceptance_eligible") is True
        and all(
            bool(row.get("attempts"))
            and all(
                str(attempt.get("evidence_class")) == "live"
                for attempt in row["attempts"]
            )
            for row in invoked
        )
    )
    if status == "aborted" and require_genuine_provider:
        evidence_mode = "genuine_live_aborted"
    else:
        evidence_mode = "genuine_live" if live_eligible else "injected_offline"
    return {
        "schema_version": PREDICTION_LEDGER_SCHEMA,
        "semantic_contract": {
            "benchmark_id": SEMANTIC_BENCHMARK_ID,
            "evaluation_label": evaluation_label,
            "taxonomy_version": SEMANTIC_TAXONOMY_VERSION,
            "template_id": PROPERTY_RESOLUTION_TEMPLATE_ID,
        },
        "status": status,
        "reason_code": reason_code,
        "case_count": len(rows),
        "expected_case_count": expected_case_count,
        "abort_case_id": abort_case_id,
        "knowledge_health": dict(runtime_health),
        "provider_evidence_mode": evidence_mode,
        "semantic_accuracy_claim_eligible": live_eligible,
        "prediction_frozen_before_gold": True,
        "gold_accessed_during_prediction": False,
        "ifc_publication_attempted": False,
        "provider_attempt_count": sum(
            int(row["provider_attempt_count"]) for row in rows
        ),
        "retry_count": sum(int(row["retry_count"]) for row in rows),
        "cases": list(rows),
        "output_path": str(destination),
    }


def produce_semantic_prediction_ledger(
    *,
    output_root: Path | str,
    ledger_path: Path | str,
    provider: Any,
    project_root: Path | str = ROOT,
    property_runtime: PropertyKnowledgeRuntime | None = None,
    environment: Mapping[str, str] | None = None,
    verify_fixture_freeze: bool = True,
    require_genuine_provider: bool = False,
    evaluation_label: str = DEFAULT_EVALUATION_LABEL,
) -> dict[str, Any]:
    """Execute public routes and freeze predictions without loading Gold."""

    root = Path(project_root).resolve()
    output = Path(output_root).resolve()
    destination = Path(ledger_path).resolve()
    if verify_fixture_freeze:
        verify_frozen_fixtures(root)
    public_cases = _load_public_cases(root)
    output.mkdir(parents=True, exist_ok=False)
    created_runtime = property_runtime is None
    try:
        runtime = property_runtime or create_property_runtime_from_environment(
            environment,
            project_root=root,
        )
    except Exception as error:
        ledger = _prediction_ledger(
            rows=(),
            runtime_health={
                "status": "not_ready",
                "reason_code": str(error).split(":", 1)[0]
                or type(error).__name__,
                "acceptance_eligible": False,
            },
            destination=destination,
            status="aborted",
            reason_code=str(error).split(":", 1)[0] or type(error).__name__,
            expected_case_count=len(public_cases),
            abort_case_id=None,
            require_genuine_provider=require_genuine_provider,
            evaluation_label=evaluation_label,
        )
        _write_atomic(destination, ledger)
        return ledger
    if runtime.health.status != "ready":
        ledger = _prediction_ledger(
            rows=(),
            runtime_health=runtime.health.to_dict(),
            destination=destination,
            status="aborted",
            reason_code=(
                runtime.health.reason_code or "PROPERTY_RUNTIME_NOT_READY"
            ),
            expected_case_count=len(public_cases),
            abort_case_id=None,
            require_genuine_provider=require_genuine_provider,
            evaluation_label=evaluation_label,
        )
        _write_atomic(destination, ledger)
        if created_runtime:
            _close_runtime(runtime)
        return ledger
    measured_provider = _TimedProvider(provider)
    rows: list[dict[str, Any]] = []
    abort_reason: str | None = None
    abort_case_id: str | None = None
    try:
        for index, case in enumerate(public_cases):
            case_id = str(case["case_id"])
            case_root = output / "cases" / case_id
            case_root.mkdir(parents=True)
            try:
                if CANONICAL_PROPERTY.fullmatch(str(case["property_phrase"])):
                    prediction = _exact_bypass_prediction(case, runtime)
                else:
                    prediction = _execute_natural_case(
                        case=case,
                        case_index=index,
                        case_root=case_root,
                        runtime=runtime,
                        provider=measured_provider,
                    )
                persisted = _persist_prediction(case_root, prediction)
                rows.append(persisted)
                abort_reason = _prediction_abort_reason(
                    persisted,
                    require_genuine_provider=require_genuine_provider,
                )
            except Exception as error:
                abort_reason = (
                    str(error).split(":", 1)[0] or type(error).__name__
                )
                _write_atomic(
                    case_root / "evaluation-abort.json",
                    {
                        "case_id": case_id,
                        "reason_code": abort_reason,
                        "exception_type": type(error).__name__,
                    },
                )
            if abort_reason is not None:
                abort_case_id = case_id
                break
    finally:
        if created_runtime:
            _close_runtime(runtime)

    ledger = _prediction_ledger(
        rows=rows,
        runtime_health=runtime.health.to_dict(),
        destination=destination,
        status="aborted" if abort_reason is not None else "completed",
        reason_code=abort_reason,
        expected_case_count=len(public_cases),
        abort_case_id=abort_case_id,
        require_genuine_provider=require_genuine_provider,
        evaluation_label=evaluation_label,
    )
    _write_atomic(destination, ledger)
    return ledger


def classify_semantic_outcome(
    prediction: Mapping[str, Any],
    gold: Mapping[str, Any],
) -> str:
    route = str(prediction.get("route") or "")
    expected = gold.get("expected")
    candidate_paths = {
        str(item) for item in prediction.get("candidate_paths", ())
    }
    if route == "infrastructure_runtime_failure":
        return "infrastructure_runtime_failure"
    if route == "exact_bypass":
        return (
            "exact_bypass"
            if prediction.get("selected_path") == expected and bool(gold["authorize"])
            else "admissibility_rejection"
        )
    if expected is not None and str(expected) not in candidate_paths:
        return "retrieval_failure"
    if route == "not_invoked_no_candidates":
        return "unsupported"

    issue_codes = {str(item) for item in prediction.get("issue_codes", ())}
    if {
        "PROPERTY_CANDIDATE_NOT_OFFERED",
        "PROPERTY_CONFLICT_CANDIDATE_NOT_OFFERED",
    } & issue_codes:
        return "unoffered_selection"
    if not bool(prediction.get("stage_valid")):
        if "PROPERTY_PROVIDER_REQUEST_FAILED" in issue_codes:
            return "infrastructure_runtime_failure"
        return "malformed_retry_exhaustion"

    classification = str(prediction.get("classification") or "")
    if classification == "clarification_required":
        return "clarification"
    if classification == "unsupported":
        return "unsupported"
    if classification == "confirmed":
        if prediction.get("admissibility_status") != "passed":
            return "admissibility_rejection"
        if (
            bool(gold["authorize"])
            and prediction.get("selected_path") == expected
        ):
            return "correct_offered_candidate_selection"
        return "semantic_selection_failure"
    return "malformed_retry_exhaustion"


def _expected_route(gold: Mapping[str, Any]) -> str:
    explicit = gold.get("expected_route")
    if isinstance(explicit, str) and explicit:
        return explicit
    phrase = str(gold["phrase"])
    if CANONICAL_PROPERTY.fullmatch(phrase):
        return "exact_bypass" if bool(gold["authorize"]) else "inadmissible"
    return "confirmed_standard" if bool(gold["authorize"]) else "unsupported"


def _outcome_matches_gold(
    outcome: str,
    prediction: Mapping[str, Any],
    gold: Mapping[str, Any],
) -> bool:
    expected_route = _expected_route(gold)
    if expected_route == "confirmed_standard":
        return (
            outcome == "correct_offered_candidate_selection"
            and prediction.get("selected_path") == gold.get("expected")
        )
    if expected_route == "exact_bypass":
        return (
            outcome == "exact_bypass"
            and prediction.get("selected_path") == gold.get("expected")
        )
    if expected_route == "clarification_required":
        return outcome == "clarification"
    if expected_route in {
        "unsupported",
        "unsupported_property",
        "unsupported_operation",
    }:
        return outcome == "unsupported"
    if expected_route == "inadmissible":
        return outcome == "admissibility_rejection"
    return False


def _family(gold: Mapping[str, Any]) -> str:
    if gold.get("family"):
        return str(gold["family"])
    name = str(gold["class"]).casefold()
    if "window" in name:
        return "window"
    if "door" in name:
        return "door"
    if "wall" in name:
        return "wall"
    if "beam" in name:
        return "beam"
    if "column" in name:
        return "column"
    return "other"


def _percentile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(item) for item in values)
    index = min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def _wilson_interval(successes: int, total: int) -> dict[str, float]:
    if total == 0:
        return {"lower": 0.0, "upper": 1.0}
    z = 1.959963984540054
    rate = successes / total
    denominator = 1.0 + z * z / total
    centre = (rate + z * z / (2.0 * total)) / denominator
    radius = (
        z
        * math.sqrt(
            rate * (1.0 - rate) / total
            + z * z / (4.0 * total * total)
        )
        / denominator
    )
    return {"lower": centre - radius, "upper": centre + radius}


def _scored_accuracy(
    rows: Sequence[Mapping[str, Any]],
    *,
    acceptance_eligible: bool,
) -> float | None:
    if not acceptance_eligible or not rows:
        return None
    return sum(bool(row["passed"]) for row in rows) / len(rows)


def _scored_accuracy_95ci(
    rows: Sequence[Mapping[str, Any]],
    *,
    acceptance_eligible: bool,
) -> dict[str, float] | None:
    if not acceptance_eligible or not rows:
        return None
    return _wilson_interval(
        sum(bool(row["passed"]) for row in rows),
        len(rows),
    )


def _family_slice(
    rows: Sequence[Mapping[str, Any]],
    *,
    acceptance_eligible: bool,
) -> dict[str, Any]:
    invoked = [row for row in rows if row["provider_invoked"]]
    return {
        "case_count": len(rows),
        "provider_invoked_count": len(invoked),
        "strict_outcome_accuracy": _scored_accuracy(
            rows,
            acceptance_eligible=acceptance_eligible,
        ),
        "strict_outcome_accuracy_95ci": _scored_accuracy_95ci(
            rows,
            acceptance_eligible=acceptance_eligible,
        ),
        "invoked_strict_outcome_accuracy": _scored_accuracy(
            invoked,
            acceptance_eligible=acceptance_eligible,
        ),
        "invoked_strict_outcome_accuracy_95ci": _scored_accuracy_95ci(
            invoked,
            acceptance_eligible=acceptance_eligible,
        ),
    }


def _private_provider_input_detected(prediction: Mapping[str, Any]) -> bool:
    for attempt in prediction.get("attempts", ()):
        path = Path(str(attempt["renderer_input_path"]))
        if not path.is_file():
            return True
        document = _read(path)
        pending = [document]
        while pending:
            value = pending.pop()
            if isinstance(value, Mapping):
                if PRIVATE_PROVIDER_KEYS & {str(key) for key in value}:
                    return True
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
    return False


def score_semantic_prediction_ledger(
    *,
    ledger_path: Path | str,
    output_path: Path | str,
    project_root: Path | str = ROOT,
    source_taxonomy_version: str = SEMANTIC_TAXONOMY_VERSION,
    scoring_taxonomy_path: str = SEMANTIC_TAXONOMY_PATH,
    scoring_taxonomy_version: str = SEMANTIC_TAXONOMY_VERSION,
    scoring_taxonomy_sha256: str = SEMANTIC_TAXONOMY_SHA256,
    rescore_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Open Gold only after every public prediction is durably frozen."""

    root = Path(project_root).resolve()
    source = Path(ledger_path).resolve()
    destination = Path(output_path).resolve()
    ledger = _read(source)
    semantic_contract = dict(ledger.get("semantic_contract") or {})
    if semantic_contract.get("benchmark_id") != SEMANTIC_BENCHMARK_ID:
        raise RuntimeError("PHASE12_1_SEMANTIC_BENCHMARK_MISMATCH")
    if semantic_contract.get("taxonomy_version") != source_taxonomy_version:
        raise RuntimeError("PHASE12_1_SEMANTIC_TAXONOMY_MISMATCH")
    if semantic_contract.get("template_id") != PROPERTY_RESOLUTION_TEMPLATE_ID:
        raise RuntimeError("PHASE12_1_SEMANTIC_TEMPLATE_MISMATCH")
    if not str(semantic_contract.get("evaluation_label") or "").strip():
        raise RuntimeError("PHASE12_1_SEMANTIC_EVALUATION_LABEL_REQUIRED")

    if ledger.get("schema_version") != PREDICTION_LEDGER_SCHEMA:
        raise RuntimeError("PHASE12_1_SEMANTIC_LEDGER_VERSION")
    if ledger.get("status") != "completed" or ledger.get("case_count") != 60:
        raise RuntimeError("PHASE12_1_SEMANTIC_LEDGER_INCOMPLETE")
    if ledger.get("prediction_frozen_before_gold") is not True:
        raise RuntimeError("PHASE12_1_PREDICTION_NOT_FROZEN")

    ledger_cases = list(ledger.get("cases", ()))
    if len(ledger_cases) != 60:
        raise RuntimeError("PHASE12_1_SEMANTIC_LEDGER_CASE_COUNT")
    for row in ledger_cases:
        prediction_path = Path(str(row.get("prediction_path") or ""))
        if not prediction_path.is_file():
            raise RuntimeError("PHASE12_1_CASE_PREDICTION_MISSING")
        if _read(prediction_path) != row.get("prediction"):
            raise RuntimeError("PHASE12_1_CASE_PREDICTION_CHANGED")

    public_cases = _load_public_cases(root)
    public_ids = {str(case["case_id"]) for case in public_cases}
    ledger_ids = {str(case["case_id"]) for case in ledger_cases}
    if public_ids != ledger_ids:
        raise RuntimeError("PHASE12_1_SEMANTIC_PUBLIC_JOIN_MISMATCH")

    # This is the first evaluator-only Gold access in the execution path.
    if (
        scoring_taxonomy_path == SEMANTIC_TAXONOMY_PATH
        and scoring_taxonomy_version == SEMANTIC_TAXONOMY_VERSION
        and scoring_taxonomy_sha256 == SEMANTIC_TAXONOMY_SHA256
    ):
        gold_cases = _load_gold_cases(root)
    else:
        gold_cases = _load_gold_cases(
            root,
            taxonomy_path=scoring_taxonomy_path,
            taxonomy_version=scoring_taxonomy_version,
            taxonomy_sha256=scoring_taxonomy_sha256,
        )
    gold_by_id = {str(case["id"]): case for case in gold_cases}
    if set(gold_by_id) != ledger_ids:
        raise RuntimeError("PHASE12_1_SEMANTIC_GOLD_JOIN_MISMATCH")

    acceptance_eligible = bool(ledger.get("semantic_accuracy_claim_eligible"))
    scored_rows: list[dict[str, Any]] = []
    for row in ledger_cases:
        case_id = str(row["case_id"])
        prediction = dict(row["prediction"])
        gold = gold_by_id[case_id]
        outcome = classify_semantic_outcome(prediction, gold)
        scored_rows.append(
            {
                "case_id": case_id,
                "family": _family(gold),
                "semantic_category": str(gold["semantic_category"]),
                "route": prediction["route"],
                "outcome": outcome,
                "expected_route": _expected_route(gold),
                "passed": (
                    _outcome_matches_gold(outcome, prediction, gold)
                    if acceptance_eligible
                    else None
                ),
                "provider_invoked": int(
                    prediction.get("provider_attempt_count", 0)
                )
                > 0,
                "expected_path_offered": (
                    gold.get("expected") is not None
                    and str(gold["expected"])
                    in set(prediction.get("candidate_paths", ()))
                ),
                "selected_path": prediction.get("selected_path"),
                "provider_attempt_count": int(
                    prediction.get("provider_attempt_count", 0)
                ),
                "retry_count": int(prediction.get("retry_count", 0)),
                "token_usage": dict(prediction.get("token_usage", {})),
                "latency_ms": float(prediction.get("latency_ms", 0.0)),
            }
        )

    outcome_counts = Counter(str(row["outcome"]) for row in scored_rows)
    family_slices: dict[str, Any] = {}
    for family in ("window", "door", "wall", "beam", "column"):
        rows = [row for row in scored_rows if row["family"] == family]
        family_slices[family] = _family_slice(
            rows,
            acceptance_eligible=acceptance_eligible,
        )

    invoked_rows = [row for row in scored_rows if row["provider_invoked"]]
    selection_rows = [
        row
        for row in scored_rows
        if row["provider_invoked"]
        and row["expected_route"] == "confirmed_standard"
        and row["expected_path_offered"]
    ]
    clarification_rows = [
        row
        for row in scored_rows
        if row["provider_invoked"]
        and row["expected_route"] == "clarification_required"
    ]
    unsupported_rows = [
        row
        for row in scored_rows
        if row["provider_invoked"]
        and row["expected_route"]
        in {"unsupported_property", "unsupported_operation"}
    ]
    inadmissible_rows = [
        row
        for row in scored_rows
        if row["expected_route"] == "inadmissible"
    ]
    false_authorization_count = sum(
        row["selected_path"] is not None
        and row["outcome"]
        not in {"admissibility_rejection", "unoffered_selection"}
        and not bool(gold_by_id[row["case_id"]]["authorize"])
        for row in scored_rows
    )
    unresolved_confirmed_count = sum(
        row["expected_route"] == "confirmed_standard"
        and row["expected_path_offered"]
        and row["outcome"] != "correct_offered_candidate_selection"
        for row in scored_rows
    )
    private_leakage_count = sum(
        _private_provider_input_detected(row["prediction"])
        for row in ledger_cases
    )
    latencies = [
        float(attempt["latency_ms"])
        for row in ledger_cases
        for attempt in row["prediction"].get("attempts", ())
    ]
    usage = {
        key: sum(
            int(dict(row["token_usage"]).get(key, 0) or 0)
            for row in scored_rows
        )
        for key in ("prompt_tokens", "completion_tokens", "total_tokens")
    }

    metrics = {
        "complete_route_case_count": len(scored_rows),
        "provider_invoked_case_count": len(invoked_rows),
        "strict_outcome_accuracy": _scored_accuracy(
            scored_rows,
            acceptance_eligible=acceptance_eligible,
        ),
        "strict_outcome_accuracy_95ci": _scored_accuracy_95ci(
            scored_rows,
            acceptance_eligible=acceptance_eligible,
        ),
        "offered_candidate_selection_accuracy": _scored_accuracy(
            selection_rows,
            acceptance_eligible=acceptance_eligible,
        ),
        "offered_candidate_selection_accuracy_95ci": _scored_accuracy_95ci(
            selection_rows,
            acceptance_eligible=acceptance_eligible,
        ),
        "clarification_accuracy": _scored_accuracy(
            clarification_rows,
            acceptance_eligible=acceptance_eligible,
        ),
        "clarification_accuracy_95ci": _scored_accuracy_95ci(
            clarification_rows,
            acceptance_eligible=acceptance_eligible,
        ),
        "unsupported_accuracy": _scored_accuracy(
            unsupported_rows,
            acceptance_eligible=acceptance_eligible,
        ),
        "unsupported_accuracy_95ci": _scored_accuracy_95ci(
            unsupported_rows,
            acceptance_eligible=acceptance_eligible,
        ),
        "inadmissible_accuracy": _scored_accuracy(
            inadmissible_rows,
            acceptance_eligible=acceptance_eligible,
        ),
        "inadmissible_accuracy_95ci": _scored_accuracy_95ci(
            inadmissible_rows,
            acceptance_eligible=acceptance_eligible,
        ),
        "outcome_counts": {
            name: int(outcome_counts.get(name, 0))
            for name in (*OUTCOME_NAMES, "exact_bypass")
        },
        "false_authorization_count": false_authorization_count,
        "unoffered_selection_count": int(
            outcome_counts.get("unoffered_selection", 0)
        ),
        "malformed_retry_exhaustion_count": int(
            outcome_counts.get("malformed_retry_exhaustion", 0)
        ),
        "final_unresolved_confirmed_count": unresolved_confirmed_count,
        "private_leakage_count": private_leakage_count,
        "false_publication_count": 0,
        "provider_attempt_count": int(ledger["provider_attempt_count"]),
        "retry_count": int(ledger["retry_count"]),
        "token_usage": usage,
        "latency_ms": {
            "p50": None if not latencies else statistics.median(latencies),
            "p95": _percentile(latencies, 0.95),
            "total": sum(latencies),
        },
        "family_slices": family_slices,
    }
    hard_gates = {
        "strict_route_outcomes": metrics["strict_outcome_accuracy"] == 1.0,
        "offered_selection": (
            metrics["offered_candidate_selection_accuracy"] == 1.0
        ),
        "clarification": metrics["clarification_accuracy"] == 1.0,
        "unsupported": metrics["unsupported_accuracy"] == 1.0,
        "inadmissible": metrics["inadmissible_accuracy"] == 1.0,
        "family_slices": all(
            value["invoked_strict_outcome_accuracy"] == 1.0
            for value in family_slices.values()
            if value["provider_invoked_count"]
        ),
        "zero_false_authorization": false_authorization_count == 0,
        "zero_unoffered_selection": (
            metrics["unoffered_selection_count"] == 0
        ),
        "zero_private_leakage": private_leakage_count == 0,
        "zero_false_publication": True,
        "zero_unresolved_when_gold_offered": unresolved_confirmed_count == 0,
    }
    status = (
        "offline_contract_only"
        if not acceptance_eligible
        else ("passed" if all(hard_gates.values()) else "failed")
    )
    report = {
        "schema_version": SEMANTIC_REPORT_SCHEMA,
        "evaluation_mode": (
            "taxonomy_corrected_rescore"
            if rescore_evidence is not None
            else "semantic_evaluation"
        ),
        "status": status,
        "reason_code": (
            None
            if status == "passed"
            else (
                "OFFLINE_PROVIDER_DOUBLE_NOT_SEMANTIC_EVIDENCE"
                if status == "offline_contract_only"
                else "STAGE_1_5_SEMANTIC_GATE_FAILED"
            )
        ),
        "case_count": len(scored_rows),
        "prediction_ledger_path": str(source),
        "prediction_frozen_before_gold": True,
        "gold_opened_after_prediction_persistence": True,
        "semantic_contract": semantic_contract,
        "scoring_taxonomy": {
            "path": scoring_taxonomy_path,
            "version": scoring_taxonomy_version,
            "canonical_sha256": scoring_taxonomy_sha256,
        },
        "rescore_evidence": (
            None if rescore_evidence is None else dict(rescore_evidence)
        ),
        "semantic_accuracy_claim_eligible": acceptance_eligible,
        "stage_1_5_semantic_evaluation_status": (
            "evaluated_live"
            if acceptance_eligible
            else "not_evaluated_offline"
        ),
        "ifc_publication_attempted": False,
        "metrics": metrics,
        "hard_gates": hard_gates if acceptance_eligible else None,
        "cases": scored_rows,
        "output_path": str(destination),
    }
    _write_atomic(destination, report)
    return report


def _raw_file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rescore_semantic_prediction_ledger(
    *,
    ledger_path: Path | str,
    source_report_path: Path | str,
    output_path: Path | str,
    source_prediction_run: str,
    project_root: Path | str = ROOT,
) -> dict[str, Any]:
    """Score the accepted frozen predictions under the corrected taxonomy."""

    source = Path(ledger_path).resolve()
    historical_report = Path(source_report_path).resolve()
    destination = Path(output_path).resolve()
    if source_prediction_run != TAXONOMY_RESCORE_SOURCE_RUN_ID:
        raise RuntimeError("PHASE12_1_TAXONOMY_RESCORE_SOURCE_RUN_MISMATCH")
    if destination in {source, historical_report}:
        raise RuntimeError("PHASE12_1_TAXONOMY_RESCORE_OUTPUT_COLLISION")

    source_ledger_hash = _raw_file_sha256(source)
    source_report_hash = _raw_file_sha256(historical_report)
    if source_ledger_hash != TAXONOMY_RESCORE_SOURCE_LEDGER_SHA256:
        raise RuntimeError("PHASE12_1_TAXONOMY_RESCORE_LEDGER_CHANGED")
    if source_report_hash != TAXONOMY_RESCORE_SOURCE_REPORT_SHA256:
        raise RuntimeError("PHASE12_1_TAXONOMY_RESCORE_REPORT_CHANGED")

    ledger = _read(source)
    if ledger.get("gold_accessed_during_prediction") is not False:
        raise RuntimeError("PHASE12_1_TAXONOMY_RESCORE_GOLD_BOUNDARY_INVALID")
    prediction_paths = [
        Path(str(row.get("prediction_path") or "")).resolve()
        for row in ledger.get("cases", ())
    ]
    prediction_hashes = {
        path: _raw_file_sha256(path) for path in prediction_paths
    }
    evidence = {
        "source_prediction_run": source_prediction_run,
        "source_prediction_ledger": str(source),
        "source_prediction_ledger_sha256": source_ledger_hash,
        "source_historical_report": str(historical_report),
        "source_historical_report_sha256": source_report_hash,
        "provider_calls_during_rescore": 0,
        "predictions_regenerated": 0,
        "predictions_modified": 0,
        "prediction_artifact_count": len(prediction_paths),
        "gold_accessed_during_original_prediction": False,
        "gold_opened_only_by_post_prediction_scorer": True,
        "historical_result_preserved": True,
    }
    report = score_semantic_prediction_ledger(
        ledger_path=source,
        output_path=destination,
        project_root=project_root,
        source_taxonomy_version=HISTORICAL_SEMANTIC_TAXONOMY_VERSION,
        rescore_evidence=evidence,
    )
    if _raw_file_sha256(source) != source_ledger_hash:
        raise RuntimeError("PHASE12_1_TAXONOMY_RESCORE_LEDGER_MODIFIED")
    if _raw_file_sha256(historical_report) != source_report_hash:
        raise RuntimeError("PHASE12_1_TAXONOMY_RESCORE_REPORT_MODIFIED")
    if any(
        _raw_file_sha256(path) != expected_hash
        for path, expected_hash in prediction_hashes.items()
    ):
        raise RuntimeError("PHASE12_1_TAXONOMY_RESCORE_PREDICTION_MODIFIED")
    return report


def run_semantic_evaluation(
    *,
    output_root: Path | str,
    provider: Any,
    environment: Mapping[str, str] | None = None,
    project_root: Path | str = ROOT,
    evaluation_label: str = DEFAULT_EVALUATION_LABEL,
) -> dict[str, Any]:
    """Run retrieval plus Stage 1.5 only, then score frozen predictions."""

    output = Path(output_root).resolve()
    ledger_path = output / "prediction-ledger.json"
    report_path = output / "semantic-evaluation-report.json"
    ledger = produce_semantic_prediction_ledger(
        output_root=output,
        ledger_path=ledger_path,
        provider=provider,
        project_root=project_root,
        environment=environment,
        require_genuine_provider=True,
        evaluation_label=evaluation_label,
    )
    if ledger["status"] != "completed":
        return {
            "status": str(ledger["status"]),
            "reason_code": ledger.get("reason_code"),
            "prediction_ledger": str(ledger_path),
            "semantic_report": None,
            "provider_attempt_count": ledger["provider_attempt_count"],
            "semantic_accuracy_claim_eligible": False,
            "ifc_publication_attempted": False,
        }
    report = score_semantic_prediction_ledger(
        ledger_path=ledger_path,
        output_path=report_path,
        project_root=project_root,
    )
    return {
        "status": report["status"],
        "prediction_ledger": str(ledger_path),
        "semantic_report": str(report_path),
        "provider_attempt_count": ledger["provider_attempt_count"],
        "semantic_accuracy_claim_eligible": report[
            "semantic_accuracy_claim_eligible"
        ],
        "ifc_publication_attempted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-runtime", action="store_true")
    mode.add_argument("--run-live-semantic-evaluation", action="store_true")
    mode.add_argument("--rescore-ledger", type=Path)
    parser.add_argument("--provider", choices=("deepseek",), default="deepseek")
    parser.add_argument("--require-provider-call", action="store_true")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-report", type=Path)
    arguments = parser.parse_args(argv)

    if arguments.rescore_ledger is not None:
        source_ledger = arguments.rescore_ledger.resolve()
        source_report = (
            arguments.source_report.resolve()
            if arguments.source_report is not None
            else source_ledger.parent / "semantic-evaluation-report.json"
        )
        run_root = arguments.output_root / datetime.now(timezone.utc).strftime(
            "taxonomy-rescore-%Y%m%dT%H%M%S%fZ"
        )
        report = rescore_semantic_prediction_ledger(
            ledger_path=source_ledger,
            source_report_path=source_report,
            output_path=run_root / "semantic-evaluation-report.json",
            source_prediction_run=source_ledger.parent.name,
            project_root=ROOT,
        )
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "semantic_report": report["output_path"],
                    "provider_calls_during_rescore": 0,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0 if report["status"] == "passed" else 2

    environment = _environment(arguments.env_file)

    if arguments.check_runtime:
        readiness = probe_property_runtime_readiness(
            environment=environment,
            project_root=ROOT,
            require_no_network=True,
        )
        print(json.dumps(readiness, ensure_ascii=False, sort_keys=True))
        return 0 if readiness["status"] == "ready" else 2

    if not arguments.require_provider_call:
        parser.error(
            "--require-provider-call is mandatory for live semantic evaluation"
        )
    verify_frozen_fixtures(ROOT)
    readiness = probe_property_runtime_readiness(
        environment=environment,
        project_root=ROOT,
        require_no_network=True,
    )
    if readiness["status"] != "ready":
        print(json.dumps(readiness, ensure_ascii=False, sort_keys=True))
        return 2

    provider_config = load_openai_compatible_runtime_config(environment)
    provider = OpenAICompatibleLiveProvider(config=provider_config)
    from scripts.ifc_repair import run_phase12_live_uat as live_uat

    if not live_uat._approved_deepseek_transport(provider):
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason_code": "LIVE_DEEPSEEK_TRANSPORT_REQUIRED",
                    "provider_calls": 0,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2

    run_root = arguments.output_root / datetime.now(timezone.utc).strftime(
        "post-fix-semantic-%Y%m%dT%H%M%S%fZ"
    )
    result = run_semantic_evaluation(
        output_root=run_root,
        provider=provider,
        environment=environment,
        project_root=ROOT,
        evaluation_label=POST_FIX_EVALUATION_LABEL,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
