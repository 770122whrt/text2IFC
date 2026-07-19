"""Opt-in Phase 9 DeepSeek two-stage public repair UAT."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.openai_compat import load_openai_compatible_config  # noqa: E402
from text2ifc_ifc_repair.api import RepairAPI  # noqa: E402


SOURCE = ROOT / "dataset" / "external" / "bim-whale-ifc-samples" / "LargeBuilding" / "IFC" / "LargeBuilding.ifc"
DEFAULT_OUTPUT = ROOT / "dataset" / "processed" / "ifc-repair" / "phase9-live-uat"
TOKEN_GUARD = 65_536


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    if args.check_config == args.live:
        parser.error("choose exactly one of --check-config or --live")

    environment = _environment(args.env_file)
    check = _config_result(environment)
    if args.check_config:
        print(_compact(check))
        return 0
    args.output_root.mkdir(parents=True, exist_ok=True)
    if check["status"] != "ready":
        result = {**check, "schema_version": "text2ifc/phase9-live-uat/0.1", "mode": "live", "provider_attempts": {"stage1": 0, "stage2": 0}}
        _write(args.output_root / "live-uat-result.json", result)
        print(_compact(result))
        return 2
    unique = datetime.now(timezone.utc).strftime("uat-%Y%m%dT%H%M%S%fZ")
    output = args.output_root / unique
    try:
        api = RepairAPI.from_environment(output, environment)
        result = api.start(
            SOURCE,
            "请修复二层外墙上缺失的窗，保持现有 IFC2X3 关系和语义证据。",
        )
        run_dir = output / result.run_directory
        payload = {
            "schema_version": "text2ifc/phase9-live-uat/0.1",
            "mode": "live",
            "status": result.status,
            "run_id": result.run_id,
            "complete_repair_success": result.complete_repair_success,
            "successful_artifact_publishable": result.successful_artifact_publishable,
            "artifacts": dict(result.artifacts),
            "provider_attempts": {
                "stage1": len(list((run_dir / "intent").glob("live-attempt-*.json"))),
                "stage2": len(list((run_dir / "changeset").glob("attempt-*/provider-metadata.json"))),
            },
            "token_guard": {"max_input_tokens": TOKEN_GUARD, "max_completion_tokens": TOKEN_GUARD},
            "evidence_class": "live_provider_uat",
        }
        exit_code = 0
    except Exception as error:
        payload = {
            "schema_version": "text2ifc/phase9-live-uat/0.1",
            "mode": "live",
            "status": "provider_failed",
            "reason_code": getattr(error, "code", type(error).__name__),
            "complete_repair_success": False,
            "successful_artifact_publishable": False,
            "provider_attempts": {
                "stage1": len(list(output.rglob("intent/live-attempt-*.json"))),
                "stage2": len(list(output.rglob("changeset/attempt-*/provider-metadata.json"))),
            },
            "token_guard": {"max_input_tokens": TOKEN_GUARD, "max_completion_tokens": TOKEN_GUARD},
            "evidence_class": "live_provider_uat",
        }
        exit_code = 2
    _write(output / "live-uat-result.json", payload)
    print(_compact(payload))
    return exit_code


def _config_result(environment: dict[str, str]) -> dict[str, object]:
    config = load_openai_compatible_config(environment)
    configured = bool(config.get("configured"))
    guards_ok = (
        config.get("max_input_tokens") == TOKEN_GUARD
        and config.get("max_completion_tokens") == TOKEN_GUARD
    )
    return {
        "schema_version": "text2ifc/phase9-live-config/0.1",
        "status": "ready" if configured and guards_ok else "not_configured",
        "provider": config.get("provider", "deepseek-openai-compatible"),
        "model": config.get("model"),
        "max_input_tokens": config.get("max_input_tokens"),
        "max_completion_tokens": config.get("max_completion_tokens"),
        "missing": list(config.get("missing", [])),
        "secret_redacted": True,
    }


def _environment(path: Path) -> dict[str, str]:
    values = dict(os.environ)
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return values


def _compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_compact(value) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
