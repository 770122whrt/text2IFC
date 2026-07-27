"""Reproducible Phase 10.5 offline, performance, and live UAT runner.

The runner never projects private mutation manifests into either Provider
stage.  Offline evidence is deterministic; ``--live`` delegates to the
existing no-fallback DeepSeek runner and records its actual terminal state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_ifc_repair.evaluation import (  # noqa: E402
    EvaluationExecutionPolicy,
    execute_validation_and_diff,
)


MANIFEST = (
    ROOT
    / "dataset/manifests/ifc-repair-cases/"
    "phase10.5-window-fidelity-cases.json"
)
DEFAULT_OUTPUT = (
    ROOT / "dataset/processed/ifc-repair/phase10.5-window-fidelity"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_manifest() -> dict[str, Any]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if payload.get("schema_version") != (
        "text2ifc/phase10.5-window-fidelity-cases/0.1"
    ):
        raise ValueError("PHASE10_5_MANIFEST_VERSION_INVALID")
    cases = payload.get("cases")
    if not isinstance(cases, list) or len(cases) != 5:
        raise ValueError("PHASE10_5_CASE_MATRIX_INVALID")
    return payload


def _verify_artifact(item: dict[str, Any], role: str) -> dict[str, Any]:
    path = ROOT / str(item["path"])
    if not path.is_file():
        raise FileNotFoundError(f"{role}:{path}")
    actual = _sha256(path)
    expected = str(item["sha256"]).removeprefix("sha256:")
    if actual != expected:
        raise ValueError(f"{role.upper()}_HASH_MISMATCH:{path}")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": f"sha256:{actual}",
        "bytes": path.stat().st_size,
    }


def verify_matrix(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    verified = []
    seen: set[str] = set()
    for case in manifest["cases"]:
        case_id = str(case["case_id"])
        if case_id in seen:
            raise ValueError(f"PHASE10_5_CASE_DUPLICATE:{case_id}")
        seen.add(case_id)
        request = str(case["public_request"])
        facts = case.get("public_facts")
        if not request.strip() or not isinstance(facts, list) or not facts:
            raise ValueError(f"PHASE10_5_PUBLIC_CONTRACT_INVALID:{case_id}")
        record = {
            "case_id": case_id,
            "mode": case["mode"],
            "source": _verify_artifact(case["source"], "source"),
            "public_request": request,
            "public_request_sha256": _canonical_hash(request),
            "public_facts": list(facts),
            "repair_intent_version": "text2ifc/ifc-repair-intent/0.4",
            "semantic_manifest_version": (
                "text2ifc/ifc-repair-semantic-manifest/0.2"
            ),
            "bound_changeset_version": "text2ifc/ifc-repair-changeset/0.3",
        }
        if "damaged" in case:
            record["damaged"] = _verify_artifact(case["damaged"], "damaged")
        if "repaired_reference" in case:
            record["repaired_reference"] = _verify_artifact(
                case["repaired_reference"], "repaired"
            )
        verified.append(record)
    return verified


def run_offline_tests() -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/ifc_repair/test_occurrence_semantic_intent.py",
        "tests/ifc_repair/test_occurrence_semantic_resolution.py",
        "tests/ifc_repair/test_occurrence_semantic_authoring.py",
        "tests/ifc_repair/test_occurrence_fidelity.py",
        "tests/ifc_repair/test_benchmark_occurrence_fidelity.py",
        "tests/ifc_repair/test_phase10_3_vvo_batch_e2e.py",
        "-q",
    ]
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "wall_seconds": time.monotonic() - started,
        "command": command[1:],
        "stdout_sha256": _canonical_hash(completed.stdout),
        "stderr_sha256": _canonical_hash(completed.stderr),
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
        "synthetic_fallback": False,
    }


def run_performance(
    matrix: list[dict[str, Any]],
    output: Path,
) -> dict[str, Any]:
    advanced = next(
        item
        for item in matrix
        if item["case_id"] == "advancedproject-five-window-shared-bundle"
    )
    damaged = ROOT / advanced["damaged"]["path"]
    repaired = ROOT / advanced["repaired_reference"]["path"]
    cache_dir = output / "validation-cache"
    policy = EvaluationExecutionPolicy(
        mode="accelerated",
        deadline_seconds=180.0,
        max_workers=2,
        rss_limit_bytes=4 * 1024**3,
        cache_mode="read_write",
    )
    runs = []
    for temperature in ("cold", "warm"):
        result = execute_validation_and_diff(
            damaged_ifc_path=damaged,
            repaired_ifc_path=repaired,
            cache_dir=cache_dir,
            policy=policy,
        )
        runs.append(
            {
                "temperature": temperature,
                "status": result["status"],
                "reason_code": result["reason_code"],
                "metrics": result["metrics"],
                "cache": result.get("results", {})
                .get("validation", {})
                .get("cache"),
                "validation_status": result.get("results", {})
                .get("validation", {})
                .get("comparison", {})
                .get("status"),
                "diff_status": (
                    "complete"
                    if result.get("results", {}).get("diff") is not None
                    else "missing"
                ),
            }
        )
    passed = all(
        item["status"] == "passed"
        and float(item["metrics"]["wall_seconds"]) <= 180.0
        and 0 < int(item["metrics"]["peak_rss_bytes"]) <= 4 * 1024**3
        for item in runs
    )
    return {
        "status": "passed" if passed else "failed",
        "deadline_seconds": 180.0,
        "rss_limit_bytes": 4 * 1024**3,
        "runs": runs,
    }


def run_live(output: Path, env_file: Path) -> dict[str, Any]:
    live_output = output / "deepseek-live"
    command = build_live_command(live_output, env_file)
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    delegated_result_path = _latest_delegated_result_path(live_output)
    delegated_result = (
        json.loads(delegated_result_path.read_text(encoding="utf-8"))
        if delegated_result_path is not None
        else {}
    )
    contract_versions = dict(delegated_result.get("contract_versions") or {})
    expected_contracts = {
        "requested_repair_intent": "text2ifc/ifc-repair-intent/0.4",
        "actual_repair_intent": "text2ifc/ifc-repair-intent/0.4",
        "expected_bound_changeset": "text2ifc/ifc-repair-changeset/0.3",
        "actual_bound_changeset": "text2ifc/ifc-repair-changeset/0.3",
    }
    contract_match = all(
        contract_versions.get(key) == value
        for key, value in expected_contracts.items()
    )
    artifact_hashes = _live_artifact_hashes(live_output)
    passed = (
        completed.returncode == 0
        and delegated_result.get("contract_pass") is True
        and contract_match
    )
    return {
        "status": "passed" if passed else "provider_failed",
        "returncode": completed.returncode,
        "wall_seconds": time.monotonic() - started,
        "provider": "deepseek-openai-compatible",
        "configured_input_tokens": 65536,
        "configured_output_tokens": 65536,
        "requested_contracts": expected_contracts,
        "actual_contracts": contract_versions,
        "contract_match": contract_match,
        "provider_attempts": delegated_result.get("provider_attempts", {}),
        "runtime_source": delegated_result.get("runtime_source"),
        "prompt_response_artifact_hashes": artifact_hashes,
        "delegated_result_path": (
            delegated_result_path.relative_to(live_output).as_posix()
            if delegated_result_path is not None
            else None
        ),
        "command": command[1:],
        "stdout_sha256": _canonical_hash(completed.stdout),
        "stderr_sha256": _canonical_hash(completed.stderr),
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "synthetic_fallback": False,
    }


def build_live_command(live_output: Path, env_file: Path) -> list[str]:
    """Build the exact no-fallback command without contacting the Provider."""

    return [
        sys.executable,
        "-B",
        str(ROOT / "scripts/ifc_repair/run_phase10_1_full_replication_uat.py"),
        "--live",
        "--env-file",
        str(env_file),
        "--output-root",
        str(live_output),
        "--intent-schema-version",
        "text2ifc/ifc-repair-intent/0.4",
    ]


def _live_artifact_hashes(live_output: Path) -> list[dict[str, Any]]:
    """Record hashes and sizes, never prompt/response contents."""

    patterns = (
        "**/runtime/runs/*/intent/rendered-prompt.md",
        "**/runtime/runs/*/intent/attempt-*.json",
        "**/runtime/runs/*/changeset/attempt-*/rendered-prompt.md",
        "**/runtime/runs/*/changeset/attempt-*/raw-response.txt",
    )
    records: list[dict[str, Any]] = []
    for pattern in patterns:
        for path in sorted(live_output.glob(pattern)):
            records.append(
                {
                    "path": path.relative_to(live_output).as_posix(),
                    "sha256": f"sha256:{_sha256(path)}",
                    "bytes": path.stat().st_size,
                }
            )
    return records


def _latest_delegated_result_path(live_output: Path) -> Path | None:
    """Locate the delegated timestamped UAT result deterministically."""

    candidates = [
        path
        for path in live_output.glob("*/result.json")
        if path.is_file()
    ]
    direct = live_output / "result.json"
    if direct.is_file():
        candidates.append(direct)
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime_ns, path.as_posix()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--skip-offline", action="store_true")
    parser.add_argument("--skip-performance", action="store_true")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest()
    matrix = verify_matrix(manifest)
    result = {
        "schema_version": "text2ifc/phase10.5-window-fidelity-uat/0.1",
        "manifest": MANIFEST.relative_to(ROOT).as_posix(),
        "matrix": matrix,
        "offline": (
            {"status": "skipped"}
            if args.skip_offline
            else run_offline_tests()
        ),
        "performance": (
            {"status": "skipped"}
            if args.skip_performance
            else run_performance(matrix, output)
        ),
        "live": (
            run_live(output, args.env_file.resolve())
            if args.live
            else {"status": "not_run", "synthetic_fallback": False}
        ),
    }
    statuses = (
        result["offline"]["status"],
        result["performance"]["status"],
        result["live"]["status"],
    )
    result["status"] = (
        "passed"
        if statuses[0] in {"passed", "skipped"}
        and statuses[1] in {"passed", "skipped"}
        and statuses[2] in {"passed", "not_run"}
        else "failed"
    )
    target = output / "phase10.5-uat-result.json"
    target.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "output": str(target),
                "offline": result["offline"]["status"],
                "performance": result["performance"]["status"],
                "live": result["live"]["status"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
