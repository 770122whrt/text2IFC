"""Single-case genuine H3 diagnostic for Repair Milestone R1.

Runs only the frozen H3 case (natural target clarification + stable-identity
resume) through the same production case executor used by the ordered R1
12-case acceptance runner. This is a diagnostic-only run: it never counts as
the uninterrupted R1 acceptance run and must precede a fresh full run.

Boundaries:
- reads the frozen manifest (request, model hash, resume binding);
- sends only the frozen request, the public resume answer and damaged-IFC
  derived context through the production seams;
- preserves every genuine Provider attempt append-only;
- fails closed on any deterministic defect without patch-and-retry.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scripts.ifc_repair import run_phase12_live_uat as live
from scripts.ifc_repair import run_repair_milestone_r1 as r1
from scripts.ifc_repair.run_repair_milestone_r1 import _case_contract_pass
from text2ifc_agent.openai_compat import (
    OpenAICompatibleLiveProvider,
    load_openai_compatible_runtime_config,
)
from text2ifc_knowledge.property_runtime import (
    create_property_runtime_from_environment,
)

SCHEMA_VERSION = "text2ifc/r1-h3-genuine-diagnostic/0.1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=r1.DEFAULT_MANIFEST)
    parser.add_argument(
        "--output-root", type=Path, default=r1.DEFAULT_OUTPUT
    )
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--authorization-reference", required=True)
    args = parser.parse_args(argv)

    run_root = args.output_root / (
        "r1-h3-genuine-diagnostic-"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    )
    run_root.mkdir(parents=True, exist_ok=False)

    loaded = r1.load_execution_manifest(args.manifest)
    h3 = next(
        (
            case
            for case in loaded["public_cases"]
            if case["case_id"] == "H3"
        ),
        None,
    )
    if h3 is None:
        raise SystemExit("H3_MANIFEST_CASE_MISSING")
    if h3.get("feedback_kind") != "select_candidate":
        raise SystemExit("H3_MANIFEST_RESUME_BINDING_INVALID")

    environment = live._environment(args.env_file)

    def transport_factory() -> OpenAICompatibleLiveProvider:
        config = load_openai_compatible_runtime_config(environment)
        return OpenAICompatibleLiveProvider(config=config)

    transport = transport_factory()
    if not live._approved_deepseek_transport(transport):
        raise SystemExit("H3_LIVE_DEEPSEEK_TRANSPORT_REQUIRED")

    property_runtime, readiness = live._open_property_runtime(
        lambda: create_property_runtime_from_environment(
            environment, project_root=ROOT
        )
    )
    if property_runtime is None:
        raise SystemExit(
            "H3_PROPERTY_RUNTIME_NOT_READY: "
            + str(readiness.get("reason_code"))
        )

    provider = live.TranscriptProvider(transport)
    provider.set_case("H3")
    case_root = run_root / "case"
    case_root.mkdir(parents=True)
    case = live.LiveCase(
        case_id="H3",
        request=str(h3["request"]),
        feedback=h3["feedback"],
        feedback_kind=h3["feedback_kind"],
    )
    execution_error: str | None = None
    try:
        final = dict(
            live._production_case_executor(
                case,
                provider,
                case_root,
                property_knowledge_runtime=property_runtime,
                source_path=h3["source_path"],
                expected_source_sha256=(
                    "sha256:" + str(h3["source_sha256"])
                ),
                evaluation_execution_policy=r1._r1_evaluation_execution_policy(),
                performance_slo_seconds=r1.R1_PERFORMANCE_SLO_SECONDS,
            )
        )
    except Exception as error:  # fail closed; no retry in this run
        execution_error = str(
            getattr(error, "code", None) or str(error) or type(error).__name__
        )[:256]
        final = {
            "status": "provider_failed",
            "reason_code": execution_error.split(":", 1)[0],
            "complete_repair_success": False,
            "successful_artifact_publishable": False,
        }
    finally:
        live._close_property_runtime(property_runtime)

    private_evidence = live._private_evidence_detected(final)
    final = live._redact_for_evidence(final)
    attempts = list(provider.attempts)
    counts = live._counts(attempts)
    live_pass = live._live_attempt_evidence_pass(attempts)
    contract_pass = _case_contract_pass(
        "success",
        final,
        live_evidence_pass=live_pass,
        private_evidence_detected=private_evidence,
        expect_resume=True,
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "passed" if contract_pass else "failed",
        "diagnostic_only": True,
        "full_r1_acceptance_run": False,
        "authorization_reference": str(args.authorization_reference),
        "case_id": "H3",
        "contract_pass": contract_pass,
        "final": final,
        "attempts": attempts,
        "transport_calls": len(attempts),
        "transport_calls_by_stage": counts,
        "synthetic_fallback_used": False,
        "private_evidence_detected": private_evidence,
        "execution_error": execution_error,
        "manifest_path": str(args.manifest),
        "manifest_sha256": loaded["manifest_sha256"],
    }
    live._write_json(run_root / "h3-genuine-diagnostic-result.json", result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "transport_calls": result["transport_calls"],
                "transport_calls_by_stage": counts,
                "result": str(
                    run_root / "h3-genuine-diagnostic-result.json"
                ),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
