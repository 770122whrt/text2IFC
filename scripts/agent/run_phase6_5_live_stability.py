"""Run independent real-DeepSeek Phase 6.5 stability sessions."""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
for import_root in (ROOT, ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from scripts.agent.run_phase6_2_cli import load_env_file  # noqa: E402
from scripts.agent import run_text2ifc_chat  # noqa: E402
from text2ifc_agent.openai_compat import load_openai_compatible_config  # noqa: E402
from text2ifc_agent.session_store import SessionStore  # noqa: E402


CASE_ROOT = ROOT / "dataset" / "processed" / "agent-demo" / "phase6.5-cases"
DEFAULT_OUTPUT_ROOT = (
    ROOT / "dataset" / "processed" / "agent-demo" / "phase6.5-live-stability"
)
WorkflowRunner = Callable[..., dict[str, Any]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=("two-storey", "three-storey"))
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--required-consecutive", type=int, default=3)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--timeout-seconds", type=float, default=1800.0)
    parser.add_argument("--trace-level", choices=("compact", "debug", "full"), default="compact")
    parser.add_argument("--check-config", action="store_true")
    return parser


def run_campaign(
    *,
    output_root: Path | str,
    case_name: str,
    run_limit: int,
    required_consecutive: int = 3,
    workflow_runner: WorkflowRunner | None = None,
    env_file: Path | None = None,
    timeout_seconds: float = 1800.0,
    trace_level: str = "compact",
) -> dict[str, Any]:
    if run_limit < 1 or required_consecutive < 1:
        raise ValueError("run limits must be positive")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    runner = workflow_runner or _run_real_workflow
    rows: list[dict[str, Any]] = []
    current_consecutive = 0
    max_consecutive = 0
    for run_index in range(1, run_limit + 1):
        row = runner(
            case_name=case_name,
            run_index=run_index,
            run_root=root,
            env_file=env_file or ROOT / ".env",
            timeout_seconds=timeout_seconds,
            trace_level=trace_level,
        )
        accepted = _is_live_acceptance(row)
        row = {**row, "accepted": accepted, "run_index": run_index, "case_name": case_name}
        rows.append(row)
        current_consecutive = current_consecutive + 1 if accepted else 0
        max_consecutive = max(max_consecutive, current_consecutive)
        _write_json(root / "campaign-runs" / case_name / f"run-{run_index:02d}.json", row)
        if current_consecutive >= required_consecutive:
            break
    result = {
        "schema_version": "text2ifc/phase6.5-live-stability/1.0",
        "case_name": case_name,
        "provider": "deepseek-openai-compatible",
        "required_consecutive": required_consecutive,
        "run_limit": run_limit,
        "run_count": len(rows),
        "accepted_count": sum(row["accepted"] for row in rows),
        "max_consecutive_accepted": max_consecutive,
        "stable": max_consecutive >= required_consecutive,
        "runs": rows,
    }
    _write_json(root / "stability-matrix.json", result)
    _write_report(root / "stability-report.md", result)
    return result


def _run_real_workflow(
    *,
    case_name: str,
    run_index: int,
    run_root: Path,
    env_file: Path,
    timeout_seconds: float,
    trace_level: str,
) -> dict[str, Any]:
    fixture = _read_json(CASE_ROOT / f"{case_name}-case.json")
    transcript = io.StringIO()
    driver = _CanonicalInputDriver(str(fixture["input"]))
    os.environ["TEXT2IFC_PROVIDER_TIMEOUT_SECONDS"] = str(timeout_seconds)
    exit_code = run_text2ifc_chat.main(
        [
            "--live",
            "--env-file",
            str(env_file),
            "--output-root",
            str(run_root),
            "--db",
            str(run_root / "sessions.sqlite"),
            "--trace-level",
            trace_level,
            "--generation-strategy",
            "staged",
        ],
        input_func=driver,
        stdout=transcript,
    )
    store = SessionStore.open(run_root / "sessions.sqlite", artifact_root=run_root)
    try:
        session = store.list_sessions()[-1]
    finally:
        store.close()
    run_dir = run_root / "runs" / session.session_hash
    response_ids, usage = _provider_evidence(run_dir)
    preservation = _read_optional_json(run_dir / "component-preservation.json")
    feedback = _read_optional_json(run_dir / "feedback-rounds.json")
    rounds = len(feedback.get("rounds", []))
    artifacts = {
        "ifc": f"runs/{session.session_hash}/output.ifc" if (run_dir / "output.ifc").is_file() else "",
        "report": f"runs/{session.session_hash}/report.md" if (run_dir / "report.md").is_file() else "",
        "session_export": f"runs/{session.session_hash}/session-export.json",
    }
    row = {
        "session_hash": session.session_hash,
        "status": session.status,
        "exit_code": exit_code,
        "provider": "deepseek-openai-compatible",
        "evidence_class": "real_provider",
        "response_ids": response_ids,
        "usage": usage,
        "clarification_fallback_used": driver.fallback_used,
        "preservation_rate": preservation.get("unrelated_component_preservation_rate"),
        "bounded_rounds": rounds,
        "gates_passed": session.status == "compiled",
        "artifacts": artifacts,
        "stdout_path": f"campaign-runs/{case_name}/run-{run_index:02d}.stdout.txt",
    }
    stdout_path = run_root / row["stdout_path"]
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(transcript.getvalue(), encoding="utf-8")
    return row


def _is_live_acceptance(row: dict[str, Any]) -> bool:
    return bool(
        row.get("status") == "compiled"
        and row.get("provider") == "deepseek-openai-compatible"
        and row.get("evidence_class") == "real_provider"
        and row.get("response_ids")
        and row.get("gates_passed") is True
        and row.get("preservation_rate") == 1.0
        and not row.get("clarification_fallback_used", False)
        and row.get("artifacts", {}).get("ifc")
        and row.get("artifacts", {}).get("report")
    )


class _CanonicalInputDriver:
    def __init__(self, prompt: str) -> None:
        self.prompt = prompt
        self.calls = 0
        self.fallback_used = False

    def __call__(self, prompt: str) -> str:
        del prompt
        self.calls += 1
        if self.calls == 1:
            return self.prompt
        self.fallback_used = True
        return "当前输入未提供该事实，请保持 Draft 并明确列出缺失项，不要编造。"


def _provider_evidence(run_dir: Path) -> tuple[list[str], list[dict[str, Any]]]:
    response_ids: list[str] = []
    usage: list[dict[str, Any]] = []
    for path in sorted(run_dir.rglob("metrics.json")):
        payload = _read_optional_json(path)
        response_id = payload.get("response_id")
        if response_id:
            response_ids.append(str(response_id))
        if isinstance(payload.get("usage"), dict):
            usage.append(dict(payload["usage"]))
    return sorted(set(response_ids)), usage


def _write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Phase 6.5 Live Stability Campaign",
        "",
        f"- case: `{result['case_name']}`",
        f"- run_count: `{result['run_count']}`",
        f"- accepted_count: `{result['accepted_count']}`",
        f"- max_consecutive_accepted: `{result['max_consecutive_accepted']}`",
        f"- stable: `{result['stable']}`",
        "",
        "| Run | Session | Status | Accepted | Rounds |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in result["runs"]:
        lines.append(
            f"| {row['run_index']} | {row['session_hash']} | {row['status']} | "
            f"{row['accepted']} | {row.get('bounded_rounds')} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional_json(path: Path) -> dict[str, Any]:
    return _read_json(path) if path.is_file() else {}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    load_env_file(args.env_file)
    args.output_root.mkdir(parents=True, exist_ok=True)
    if args.check_config:
        config = load_openai_compatible_config(dict(os.environ))
        result = {
            "schema_version": "text2ifc/phase6.5-live-config/1.0",
            "provider": "deepseek-openai-compatible",
            "configured": bool(config["configured"]),
            "missing": list(config["missing"]),
            "model": config["model"],
            "config": {"api_key": "[REDACTED]", "base_url": "[REDACTED]"},
        }
        _write_json(args.output_root / "config-check.json", result)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["configured"] else 2
    if not args.case:
        parser.error("--case is required unless --check-config is used")
    result = run_campaign(
        output_root=args.output_root,
        case_name=args.case,
        run_limit=args.runs,
        required_consecutive=args.required_consecutive,
        env_file=args.env_file,
        timeout_seconds=args.timeout_seconds,
        trace_level=args.trace_level,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["stable"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
