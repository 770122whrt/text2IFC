"""Genuine live runner for the Composite Repair Milestone evidence pack.

Executes the frozen composite acceptance cases
(``composite-acceptance-freeze.json``) against the live Provider exactly once
in frozen order ``C1 -> C2 -> C3 -> C4 -> C5 -> C5-N`` through the production
``RepairAPI`` public path, re-verifying the baseline fingerprint between
cases, capturing full provenance per attempt (stage, tokens, latency,
prompt/profile identity), and stopping on the first new
deterministic/infrastructure defect.

No synthetic/cached fallback is ever reported as genuine success.  The
negative twin must terminate ``unsupported`` with zero mutation and no Stage 2
attempt.

Usage (repo root, repo venv)::

    python scripts/ifc_repair/composite_evidence/run_composite.py --execute-genuine
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scripts.ifc_repair import run_phase12_live_uat as live  # noqa: E402
from scripts.ifc_repair.composite_evidence import baseline_fingerprint  # noqa: E402
from scripts.ifc_repair.composite_evidence.composite_proof import (  # noqa: E402
    CompositeProofError,
    verify_composite_case,
)
from scripts.ifc_repair.composite_evidence.offline_driver import load_freeze  # noqa: E402
from scripts.ifc_repair.composite_evidence.preservation import (  # noqa: E402
    CompositePreservationError,
    verify_exact_composed_delta,
    verify_negative_zero_mutation,
    verify_no_unrelated_mutation,
)
from scripts.ifc_repair.composite_evidence.strict_reopen import (  # noqa: E402
    strict_reopen_verification,
)
from text2ifc_agent.openai_compat import (  # noqa: E402
    OpenAICompatibleLiveProvider,
    load_openai_compatible_runtime_config,
)
from text2ifc_ifc_repair.api import RepairAPI  # noqa: E402
from text2ifc_knowledge.property_runtime import (  # noqa: E402
    create_property_runtime_from_environment,
)

FREEZE = load_freeze()
DOC_DIR = ROOT / "docs" / "validation" / "repair-composite-milestone"
PROOF_ROOT = (
    ROOT / "dataset" / "processed" / "proof" / "repair-composite-milestone"
)
RESULT_SCHEMA = "text2ifc/composite-repair-execution-result/0.1"


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _execute_case(
    *,
    case: Mapping[str, Any],
    provider: Any,
    case_root: Path,
    property_runtime: Any,
) -> dict[str, Any]:
    """Drive the production RepairAPI for one composite case."""

    import ifcopenshell

    source = ROOT / str(FREEZE["models"][case["model_id"]]["path"])
    expected_sha = "sha256:" + str(FREEZE["models"][case["model_id"]]["sha256"])
    source_sha_before = _sha256_path(source)
    if source_sha_before != expected_sha:
        raise ValueError("COMPOSITE_SOURCE_HASH_MISMATCH")

    runtime = case_root / "runtime"
    api = RepairAPI(
        runtime,
        provider=provider,
        intent_schema_version=live.REPAIR_INTENT_SCHEMA_VERSION_0_8,
        property_knowledge_runtime=property_runtime,
    )
    provider.set_lineage("initial")
    started = time.monotonic()
    initial = api.start(source, str(case["request"]))
    final = initial
    clarification_payload = None
    answer_applied = False
    if initial.status == "clarification_required" and initial.clarification is not None:
        # Composite cases are designed complete; a clarification is a
        # deterministic-contract signal — record it honestly.
        clarification_payload = {
            "clarification_id": initial.clarification.clarification_id,
            "reason_code": initial.clarification.reason_code,
            "question": initial.clarification.question,
        }
    latency_seconds = round(time.monotonic() - started, 3)
    summary = live._result_summary(final)

    candidate_outputs = sorted(
        str(value)
        for key, value in (summary.get("artifacts") or {}).items()
        if key in {"successful_ifc", "diagnostic_candidate"} and value
    )
    return {
        **summary,
        "initial_status": live._result_summary(initial)["status"],
        "clarification": clarification_payload,
        "clarification_answer_applied": answer_applied,
        "latency_seconds": latency_seconds,
        "source_path": str(source),
        "source_sha256_before": source_sha_before,
        "source_sha256_after": _sha256_path(source),
        "candidate_output_paths": candidate_outputs,
        "strict_reopen_verification": strict_reopen_verification(
            runtime=runtime,
            final=summary,
            source_path=source,
            expected_source_sha256=expected_sha,
        ),
        "initial_summary": live._result_summary(initial),
    }


def _case_contract(
    *,
    case: Mapping[str, Any],
    final: Mapping[str, Any],
    attempts: Sequence[Mapping[str, Any]],
    case_root: Path,
) -> dict[str, Any]:
    """Post-execution proof: independent recomputation from IFC artifacts."""

    case_id = str(case["case_id"])
    proof_payload: dict[str, Any] = {
        "case_id": case_id,
        "status": "not_run",
    }
    negative = case.get("expected_terminal_class") == "UNSUPPORTED_ATOMIC_GUARD"

    if negative:
        ok = (
            final.get("status") == "unsupported"
            and final.get("successful_artifact_publishable") is False
            and not final.get("candidate_output_paths")
            and final.get("source_sha256_before") == final.get("source_sha256_after")
            and not [a for a in attempts if a.get("stage") == "stage2"]
        )
        proof_payload = {
            "case_id": case_id,
            "negative_guard": {
                "status": "unsupported",
                "reason_code": final.get("reason_code"),
                "zero_mutation": final.get("source_sha256_before")
                == final.get("source_sha256_after"),
                "stage2_attempts": sum(
                    1 for a in attempts if a.get("stage") == "stage2"
                ),
            },
            "status": "passed" if ok else "failed",
        }
        try:
            guard = verify_composite_case(
                case=case,
                changeset={},
                application={},
                source_model=None,
                repaired_model=None,
                source_path=ROOT
                / str(FREEZE["models"][case["model_id"]]["path"]),
                repaired_path=None,
                live_attempt_evidence=attempts,
            )
            proof_payload["composite_proof"] = guard
        except CompositeProofError as error:
            proof_payload["composite_proof_error"] = str(error)
            proof_payload["status"] = "failed"
        return proof_payload

    # Positive case: run the full operation-bound composite proof against the
    # published repaired IFC + run-record changeset/application.
    import ifcopenshell

    source = ROOT / str(FREEZE["models"][case["model_id"]]["path"])
    strict = final.get("strict_reopen_verification") or {}
    artifacts = final.get("artifacts") or {}
    ok = (
        final.get("status") == "succeeded"
        and final.get("complete_repair_success") is True
        and final.get("successful_artifact_publishable") is True
        and strict.get("status") == "passed"
        and strict.get("l0_pass") is True
        and strict.get("l1_pass") is True
        and strict.get("l2_pass") is True
    )
    proof_payload["production_strict_reopen"] = strict
    if not ok:
        proof_payload["status"] = "failed"
        return proof_payload

    runtime_root = case_root / "runtime"
    run_id = str(final.get("run_id"))
    run_root = runtime_root / "runs" / run_id
    changeset_path = run_root / "changeset" / "bound-changeset.json"
    if not changeset_path.is_file():
        changeset_path = run_root / "changeset.json"
    changeset = json.loads(changeset_path.read_text(encoding="utf-8"))
    evidence_path = (
        run_root / "manifest" / "terminal" / "evidence.json"
    )
    if not evidence_path.is_file():
        # locate via artifacts manifest reference
        manifest_rel = str(artifacts.get("manifest"))
        manifest_path = run_root / manifest_rel if manifest_rel else None
        if manifest_path is not None and manifest_path.is_file():
            evidence_path = manifest_path.parent / "terminal" / "evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))["evidence"]
    application = evidence["application"]
    repaired_path = Path(str(artifacts["successful_ifc"]))
    if not repaired_path.is_absolute():
        repaired_path = run_root / repaired_path

    try:
        proof = verify_composite_case(
            case=case,
            changeset=changeset,
            application=application,
            source_model=ifcopenshell.open(str(source)),
            repaired_model=ifcopenshell.open(str(repaired_path)),
            source_path=source,
            repaired_path=repaired_path,
            live_attempt_evidence=attempts,
        )
        preservation_exact = verify_exact_composed_delta(
            case=case,
            application=application,
            source_model=ifcopenshell.open(str(source)),
            repaired_model=ifcopenshell.open(str(repaired_path)),
        )
        preservation_comparator = verify_no_unrelated_mutation(
            case=case,
            application=application,
            source_path=source,
            repaired_path=repaired_path,
        )
        proof_payload["composite_proof"] = proof
        proof_payload["preservation_exact_delta"] = preservation_exact
        proof_payload["preservation_comparator"] = preservation_comparator
        proof_payload["repaired_ifc_path"] = str(repaired_path)
        proof_payload["changeset_path"] = str(changeset_path)
        proof_payload["status"] = "passed"
    except (CompositeProofError, CompositePreservationError) as error:
        proof_payload["status"] = "failed"
        proof_payload["proof_error"] = str(error)
    return proof_payload


def run_genuine(
    *,
    output_root: Path,
    transport_factory: Callable[[], Any],
    property_runtime_factory: Callable[[], Any],
    execute: bool,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "created_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "base_revision": FREEZE["base_revision"],
        "freeze_sha256": FREEZE["freeze_sha256"],
        "execution_order": list(FREEZE["execution_order"]),
        "status": "not_started",
        "cases": [],
        "transport_calls": 0,
        "transport_calls_by_stage": {"stage1": 0, "property_resolution": 0, "stage2": 0},
    }

    # Pre-execution fingerprint gate (spec 1.2 / 10.1).
    drift = baseline_fingerprint.cmd_verify()
    result["preflight_fingerprint"] = (
        "clean" if drift == 0 else f"DRIFT:{drift}"
    )
    if drift != 0:
        result["status"] = "blocked"
        result["reason_code"] = "COMPOSITE_BASELINE_DRIFT"
        _write_json(output_root / "composite-execution-result.json", result)
        return result
    if not execute:
        result["status"] = "ready_for_genuine_execution"
        _write_json(output_root / "composite-execution-result.json", result)
        return result

    transport = transport_factory()
    if not live._approved_deepseek_transport(transport):
        result["status"] = "blocked"
        result["reason_code"] = "COMPOSITE_LIVE_DEEPSEEK_TRANSPORT_REQUIRED"
        _write_json(output_root / "composite-execution-result.json", result)
        return result
    property_runtime, readiness = live._open_property_runtime(
        property_runtime_factory
    )
    result["property_runtime_readiness"] = readiness
    if property_runtime is None:
        result["status"] = "blocked"
        result["reason_code"] = readiness.get("reason_code") or "PROPERTY_RUNTIME_NOT_READY"
        _write_json(output_root / "composite-execution-result.json", result)
        return result

    provider = live.TranscriptProvider(transport)
    case_results: list[dict[str, Any]] = []
    try:
        for case in FREEZE["cases"]:
            case_id = str(case["case_id"])
            # Fingerprint re-verification between cases (spec 1.2).
            if baseline_fingerprint.cmd_verify() != 0:
                result["status"] = "failed"
                result["reason_code"] = "COMPOSITE_BASELINE_DRIFT_BETWEEN_CASES"
                result["stopped_after_case"] = case_id
                break
            provider.set_case(case_id)
            before = len(provider.attempts)
            case_root = output_root / "cases" / case_id
            case_root.mkdir(parents=True, exist_ok=True)
            started = time.monotonic()
            try:
                final = _execute_case(
                    case=case,
                    provider=provider,
                    case_root=case_root,
                    property_runtime=property_runtime,
                )
                execution_error = None
            except Exception as error:  # infrastructure defect: stop per 10.2
                execution_error = f"{type(error).__name__}: {error}"[:512]
                final = {
                    "status": "provider_failed",
                    "reason_code": type(error).__name__,
                    "complete_repair_success": False,
                    "successful_artifact_publishable": False,
                    "artifacts": {},
                }
            attempts = provider.attempts[before:]
            counts = live._counts(attempts)
            live_pass = live._live_attempt_evidence_pass(attempts)
            contract = _case_contract(
                case=case,
                final=final,
                attempts=attempts,
                case_root=case_root,
            )
            case_result = {
                "case_id": case_id,
                "model_id": case["model_id"],
                "request_sha256": case["request_sha256"],
                "final": final,
                "attempts": attempts,
                "transport_calls": len(attempts),
                "transport_calls_by_stage": counts,
                "live_evidence_pass": live_pass,
                "contract": contract,
                "execution_error": execution_error,
                "wall_time_seconds": round(time.monotonic() - started, 3),
                "status": (
                    "passed"
                    if contract.get("status") == "passed"
                    and live_pass
                    and execution_error is None
                    else "failed"
                ),
            }
            _write_json(case_root / "case-result.json", case_result)
            case_results.append(case_result)
            if execution_error is not None:
                result["stopped_after_case"] = case_id
                result["reason_code"] = "COMPOSITE_EXECUTION_DEFECT_STOP"
                break
    finally:
        live._close_property_runtime(property_runtime)

    aggregate = live._counts(provider.attempts)
    result.update(
        {
            "transport_calls": len(provider.attempts),
            "transport_calls_by_stage": aggregate,
            "cases": case_results,
            "status": (
                "passed"
                if len(case_results) == len(FREEZE["cases"])
                and all(item["status"] == "passed" for item in case_results)
                else "failed"
            ),
        }
    )
    _write_json(output_root / "composite-execution-result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-genuine", action="store_true")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "dataset/processed/ifc-repair-runs/repair-composite-milestone",
    )
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    args = parser.parse_args()

    output_root = args.output_root.resolve()
    if output_root.exists() and any(output_root.iterdir()):
        print(
            f"ERROR: output root not empty: {output_root}",
            file=sys.stderr,
        )
        return 2
    output_root.mkdir(parents=True, exist_ok=True)

    environment: dict[str, str] = {}
    if args.env_file.is_file():
        for line in args.env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            environment[key.strip()] = value.strip()

    def transport_factory() -> Any:
        config = load_openai_compatible_runtime_config(environment)
        return OpenAICompatibleLiveProvider(config=config)

    def property_runtime_factory() -> Any:
        return create_property_runtime_from_environment(
            environment, project_root=ROOT
        )

    result = run_genuine(
        output_root=output_root,
        transport_factory=transport_factory,
        property_runtime_factory=property_runtime_factory,
        execute=args.execute_genuine,
    )
    print(json.dumps({k: result.get(k) for k in (
        "status", "reason_code", "transport_calls", "transport_calls_by_stage",
    )}, ensure_ascii=False))
    for case in result.get("cases", []):
        print(
            f"  {case['case_id']}: {case['status']} "
            f"(contract={case['contract'].get('status')}, "
            f"live_pass={case['live_evidence_pass']})"
        )
    return 0 if result.get("status") in {"passed", "ready_for_genuine_execution"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
