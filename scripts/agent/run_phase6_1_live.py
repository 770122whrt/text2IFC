"""Run traceable Phase 6.1 stages against the real Mimo provider."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.live_pipeline import (  # noqa: E402
    clarified_room_case,
    compare_design_brief_runs,
    complete_room_case,
    run_clarification_case,
    run_design_brief_stage,
    run_generator_stage,
    run_repair_stage,
    run_audit_report_stage,
    run_final_acceptance_stage,
)
from text2ifc_agent.clarification import ClarificationError  # noqa: E402
from text2ifc_agent.live_trace import write_live_trace  # noqa: E402
from text2ifc_agent.providers import (  # noqa: E402
    MimoAgentProvider,
    ProviderOutputError,
    load_mimo_config_from_env,
)


DEFAULT_ENV_FILE = ROOT / ".env"
DEFAULT_LIVE_ROOT = (
    ROOT
    / "dataset"
    / "processed"
    / "agent-demo"
    / "phase6.1-mimo-live"
)
DEFAULT_V1_BASELINE = (
    ROOT
    / "dataset"
    / "processed"
    / "agent-demo"
    / "phase6-mimo-live"
    / "attempt-03"
)


def default_output_dir(*, stage: str, case_id: str) -> Path:
    if stage == "clarify":
        return DEFAULT_LIVE_ROOT / case_id
    if stage == "generate":
        return DEFAULT_LIVE_ROOT / case_id / "generator"
    if stage == "finalize":
        return DEFAULT_LIVE_ROOT
    return DEFAULT_LIVE_ROOT / case_id / stage


def main(
    argv: list[str] | None = None,
    *,
    provider_factory=MimoAgentProvider,
) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=(
            "design-brief",
            "clarify",
            "generate",
            "repair",
            "audit-report",
            "finalize",
        ),
        default="design-brief",
    )
    parser.add_argument(
        "--case", choices=("complete-room", "clarified-room"), default="complete-room"
    )
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--answers", type=Path)
    parser.add_argument("--case-dir", type=Path)
    parser.add_argument("--design-source-dir", type=Path)
    parser.add_argument("--generator-source-dir", type=Path)
    parser.add_argument("--v1-baseline-dir", type=Path, default=DEFAULT_V1_BASELINE)
    args = parser.parse_args(argv)
    _load_env_file(args.env_file)

    if args.check_config:
        print(json.dumps(load_mimo_config_from_env(), ensure_ascii=False, sort_keys=True))
        return 0
    if not args.live:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": "--live is required for Phase 6.1 semantic evidence",
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2

    if args.output_dir is not None:
        output_dir = args.output_dir
    else:
        output_dir = default_output_dir(stage=args.stage, case_id=args.case)
    if args.stage == "clarify" and args.case != "clarified-room":
        parser.error("--stage clarify requires --case clarified-room")
    if args.stage == "design-brief" and args.case != "complete-room":
        parser.error("--stage design-brief requires --case complete-room")
    case = clarified_room_case() if args.case == "clarified-room" else complete_room_case()
    try:
        if args.stage == "clarify":
            provider = provider_factory()
            if args.answers is None or not args.answers.is_file():
                parser.error("--stage clarify requires an existing --answers JSON file")
            answer_payload = json.loads(args.answers.read_text(encoding="utf-8"))
            answers = answer_payload.get("answers")
            if not isinstance(answers, list) or not all(
                isinstance(answer, str) and answer for answer in answers
            ):
                parser.error("answer file must contain a non-empty string answers list")
            result = run_clarification_case(
                provider=provider,
                output_dir=output_dir,
                case=case,
                answers=answers,
            )
        elif args.stage == "generate":
            provider = provider_factory()
            design_source_dir = args.design_source_dir or (
                DEFAULT_LIVE_ROOT / "complete-room" / "design-brief"
                if args.case == "complete-room"
                else DEFAULT_LIVE_ROOT / "clarified-room"
            )
            result = run_generator_stage(
                provider=provider,
                output_dir=output_dir,
                design_source_dir=design_source_dir,
                case_id=args.case,
            )
        elif args.stage == "repair":
            generator_source_dir = args.generator_source_dir or (
                DEFAULT_LIVE_ROOT / args.case / "generator"
            )
            result = run_repair_stage(
                provider_factory=provider_factory,
                output_dir=output_dir,
                generator_source_dir=generator_source_dir,
                case_id=args.case,
            )
        elif args.stage == "audit-report":
            provider = provider_factory()
            case_dir = args.case_dir or (DEFAULT_LIVE_ROOT / args.case)
            result = run_audit_report_stage(
                provider=provider,
                case_dir=case_dir,
                case_id=args.case,
            )
        elif args.stage == "finalize":
            case_dir = args.case_dir or (DEFAULT_LIVE_ROOT / args.case)
            result = run_final_acceptance_stage(
                case_dir=case_dir,
                output_dir=output_dir,
                case_id=args.case,
            )
        else:
            provider = provider_factory()
            result = run_design_brief_stage(
                provider=provider,
                output_dir=output_dir,
                case=case,
            )
    except (ProviderOutputError, ClarificationError) as exc:
        live_result = getattr(exc, "live_result", None)
        if live_result is not None:
            write_live_trace(result=live_result, output_dir=output_dir)
        failure = {
            "status": "blocked_provider_failure",
            "message": str(exc),
            "details": getattr(exc, "details", {}),
            "output_dir": str(output_dir),
        }
        print(json.dumps(failure, ensure_ascii=False, sort_keys=True))
        return 2

    if args.stage == "design-brief" and (
        args.v1_baseline_dir.is_dir()
        and (args.v1_baseline_dir / "model-text.txt").is_file()
        and (args.v1_baseline_dir / "response-metadata.json").is_file()
    ):
        comparison = compare_design_brief_runs(
            v1_dir=args.v1_baseline_dir,
            v2_dir=output_dir,
            output_path=output_dir / "comparison.json",
        )
        result["comparison_regressions"] = comparison["regressions"]
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["valid"] else 2


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _unquote(value.strip())
        if key and key not in os.environ:
            os.environ[key] = value


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
