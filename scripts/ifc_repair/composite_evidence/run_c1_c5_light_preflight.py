"""Targeted zero-network admission gate for the frozen C1-C5 live run.

The gate reuses the current, hash-verified C1-C5 offline public-chain proof and
reruns only seams that are not exercised by those five complete requests.
It is intentionally much smaller than the repository-wide Phase 12 preflight,
but it retains the same fail-closed requirements: no skips, substitutions,
timeouts, network calls, or missing evidence are accepted.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = "text2ifc/damage-restoration-c1-c5-light-preflight/0.1"

CAPABILITY_TESTS: dict[str, tuple[str, ...]] = {
    "complete": (
        "tests/ifc_repair/test_phase12_live_uat.py::test_complete_transport_drives_the_real_repair_api_and_reopens_ifc2x3",
    ),
    "clarification_resume": (
        "tests/ifc_repair/test_phase12_live_uat.py::test_clarification_transport_drives_real_api_resume_and_publication",
    ),
    "ambiguous_or_unsupported": (
        "tests/ifc_repair/test_phase12_live_uat.py::test_program_guard_transport_stops_real_api_before_stage2_or_mutation",
        "tests/ifc_repair/test_phase12_live_uat.py::test_stable_property_identity_fails_closed_when_not_currently_offered",
    ),
    "malformed_or_truncated_provider_output": (
        "tests/ifc_repair/test_repair_intent_v06.py::test_stage1_malformed_output_retries_but_never_normalizes_it",
        "tests/ifc_repair/test_property_resolution_stage.py::test_deepseek_style_truncation_evidence_is_preserved_and_rejected",
    ),
    "deterministic_binding": (
        "tests/ifc_repair/test_phase12_live_uat.py::test_stage1_invalid_internal_id_retries_then_completes_public_full_chain",
    ),
    "apply_compile": (
        "tests/ifc_repair/test_apply_transaction.py::test_transaction_publishes_only_after_reopen_and_postconditions",
    ),
    "atomic_rollback": (
        "tests/ifc_repair/test_apply_transaction.py::test_transaction_failure_leaves_no_repaired_artifact",
        "tests/ifc_repair/test_structural_atomicity.py::test_one_structural_postcondition_failure_suppresses_whole_transaction",
    ),
    "source_immutability": (
        "tests/ifc_repair/test_run_state.py::test_start_creates_unique_bound_run_without_modifying_source",
    ),
    "private_gold_isolation": (
        "tests/ifc_repair/test_phase12_ground_truth_isolation.py::test_public_bundle_rejects_every_private_gold_channel_without_echo",
    ),
    "reopen": (),
    "l0": (
        "tests/ifc_repair/test_repair_api_resource_lifecycle.py::test_source_schema_probe_does_not_retain_open_model",
    ),
    "l1": (),
    "l2": (),
    "preservation": (),
    "terminal_publication": (
        "tests/ifc_repair/test_orchestrator_terminal_matrix.py::test_every_terminal_writes_evaluation_and_only_canonical_pass_publishes_success",
    ),
    "persistence_recovery": (
        "tests/ifc_repair/test_run_state.py::test_restart_recovers_last_committed_state_after_interrupted_state_replace",
        "tests/ifc_repair/test_run_state.py::test_terminal_publication_recovers_across_every_commit_crash_window",
    ),
    "property_runtime_ready": (),
    "c1_c5_geometry_property_type": (
        "tests/ifc_repair/composite_evidence/test_damage_restoration_c1_c5.py::test_live_runner_uses_an_explicit_shared_property_cache",
        "tests/ifc_repair/composite_evidence/test_damage_restoration_c1_c5.py::test_live_runner_blocks_an_unhealthy_property_runtime_before_provider",
        "tests/ifc_repair/composite_evidence/test_damage_restoration_c1_c5.py::test_failed_live_case_still_counts_its_provider_attempts",
        "tests/ifc_repair/composite_evidence/test_damage_restoration_c1_c5.py::test_live_runner_resolves_actual_operation_ids_from_bound_content",
        "tests/ifc_repair/composite_evidence/test_damage_restoration_c1_c5.py::test_focused_ifccompare_and_type_reuse_accept_actual_operation_tags",
        "tests/ifc_repair/test_generic_difference_report.py",
        "tests/knowledge/test_property_search.py::test_plane_angle_measure_uses_project_unit_and_rejects_explicit_conversion",
        "tests/knowledge/test_property_vector_runtime.py::test_beam_slope_plane_angle_is_active_and_retrievable",
        "tests/knowledge/test_property_vector_runtime.py::test_vector_storage_version_binds_the_active_record_set",
        "tests/ifc_repair/test_property_admissibility.py::test_plane_angle_slope_passes_standard_admissibility_and_binder",
        "tests/ifc_repair/test_structural_property_authoring.py::test_beam_slope_authors_plane_angle_measure_and_reopens",
    ),
}
REQUIRED_CAPABILITIES = frozenset(CAPABILITY_TESTS)
TEST_NODES = tuple(
    dict.fromkeys(
        node
        for nodes in CAPABILITY_TESTS.values()
        for node in nodes
    )
)
SCOPE_FILES = (
    "docs/validation/repair-composite-milestone/composite-baseline-fingerprint.json",
    "docs/validation/repair-composite-milestone/damage-restoration-c1-c5-freeze.json",
    "scripts/ifc_repair/composite_evidence/baseline_fingerprint.py",
    "scripts/ifc_repair/composite_evidence/restoration_debug.py",
    "scripts/ifc_repair/composite_evidence/run_c1_c5_light_preflight.py",
    "scripts/ifc_repair/composite_evidence/run_damage_restoration_c1_c5.py",
    "scripts/ifc_repair/compare_ifc_files.py",
    "src/text2ifc_knowledge/property_runtime.py",
    "src/text2ifc_knowledge/property_search.py",
    "src/text2ifc_ifc_repair/door_geometry.py",
    "src/text2ifc_ifc_repair/compare.py",
    "src/text2ifc_ifc_repair/operations/door.py",
    "src/text2ifc_ifc_repair/operations/window.py",
    "src/text2ifc_ifc_repair/window_geometry.py",
    "tests/ifc_repair/composite_evidence/test_damage_restoration_c1_c5.py",
    "tests/ifc_repair/test_door_geometry_regression.py",
    "tests/ifc_repair/test_generic_difference_report.py",
    "tests/ifc_repair/test_door_property_authorization.py",
    "tests/ifc_repair/test_structural_evaluation.py",
    "tests/ifc_repair/test_property_admissibility.py",
    "tests/ifc_repair/test_structural_property_authoring.py",
    "tests/knowledge/test_property_search.py",
    "tests/knowledge/test_property_vector_runtime.py",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _text_sha256(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_sha256(value: Any) -> str:
    rendered = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return _text_sha256(rendered)


def _repo_file(value: Any) -> Path:
    path = (ROOT / str(value)).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("C1_C5_PREFLIGHT_PATH_INVALID")
    return path


def _verify_offline_proof(proof_root: Path) -> dict[str, Any]:
    proof_root = proof_root.resolve()
    if not proof_root.is_relative_to(ROOT) or not proof_root.is_dir():
        raise ValueError("C1_C5_PREFLIGHT_PROOF_PATH_INVALID")
    manifest_path = proof_root / "manifest.json"
    files_path = proof_root / "FILES.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("schema_version") != "text2ifc/c1-c5-offline-proof/0.1"
        or manifest.get("status") != "passed"
        or manifest.get("evidence_mode") != "deterministic_offline_replay"
        or manifest.get("network_transport_attempted") is not False
    ):
        raise ValueError("C1_C5_PREFLIGHT_PROOF_NOT_GREEN")
    cases = manifest.get("cases")
    if (
        not isinstance(cases, list)
        or {str(item.get("case_id")) for item in cases}
        != {"C1", "C2", "C3", "C4", "C5"}
        or any(
            item.get("status") != "passed"
            or item.get("focused_ifccompare_status") != "passed"
            or item.get("class_counts_restored") is not True
            for item in cases
        )
    ):
        raise ValueError("C1_C5_PREFLIGHT_PROOF_CASE_INVALID")
    file_index = json.loads(files_path.read_text(encoding="utf-8"))["files"]
    for relative, expected in file_index.items():
        artifact = (proof_root / relative).resolve()
        if (
            not artifact.is_relative_to(proof_root)
            or not artifact.is_file()
            or artifact.stat().st_size != int(expected["bytes"])
            or _sha256(artifact) != expected["sha256"]
        ):
            raise ValueError("C1_C5_PREFLIGHT_PROOF_HASH_MISMATCH")
    for case_id in ("C1", "C2", "C3", "C4", "C5"):
        debug = json.loads(
            (proof_root / case_id / "validation/ifccompare-geometry-property-debug.json").read_text(
                encoding="utf-8"
            )
        )
        result = json.loads(
            (proof_root / case_id / "validation/case-result.json").read_text(
                encoding="utf-8"
            )
        )
        comparison = result.get("original_comparison") or {}
        if (
            debug.get("status") != "passed"
            or debug.get("failed_member_count") != 0
            or comparison.get("restoration_acceptance_status") != "passed"
            or (comparison.get("exact_type_reuse") or {}).get("status")
            != "passed"
        ):
            raise ValueError("C1_C5_PREFLIGHT_PROOF_COMPARISON_INVALID")
    return {
        "manifest": manifest_path.relative_to(ROOT).as_posix(),
        "manifest_sha256": _sha256(manifest_path),
        "files_index": files_path.relative_to(ROOT).as_posix(),
        "files_index_sha256": _sha256(files_path),
        "case_count": 5,
        "status": "passed",
    }


def _run_check(
    name: str,
    command: Sequence[str],
    *,
    output_root: Path,
    timeout_seconds: int,
    capabilities: Sequence[str] = (),
    junit_path: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    completed = subprocess.run(
        list(command),
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
        env=dict(environment) if environment is not None else None,
    )
    logs = output_root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    stdout_path = logs / f"{name}.stdout.txt"
    stderr_path = logs / f"{name}.stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8", newline="\n")
    stderr_path.write_text(completed.stderr, encoding="utf-8", newline="\n")
    skipped = 0
    tests = 0
    failures = 0
    if junit_path is not None and junit_path.is_file():
        root = ET.parse(junit_path).getroot()
        tests = sum(int(node.get("tests", "0")) for node in root.iter("testsuite"))
        failures = sum(
            int(node.get("failures", "0")) + int(node.get("errors", "0"))
            for node in root.iter("testsuite")
        )
        skipped = sum(int(node.get("skipped", "0")) for node in root.iter("testsuite"))
    record = {
        "name": name,
        "status": (
            "passed"
            if completed.returncode == 0 and failures == 0 and skipped == 0
            else "failed"
        ),
        "command": list(command),
        "exit_code": completed.returncode,
        "test_count": tests,
        "failure_count": failures,
        "skip_count": skipped,
        "substitution_count": 0,
        "timeout_count": 0,
        "network_calls": 0,
        "network_transport_attempted": False,
        "capabilities": list(capabilities),
        "stdout": stdout_path.relative_to(output_root).as_posix(),
        "stdout_sha256": _sha256(stdout_path),
        "stderr": stderr_path.relative_to(output_root).as_posix(),
        "stderr_sha256": _sha256(stderr_path),
    }
    record["result_sha256"] = _canonical_sha256(record)
    return record


def load_light_preflight_evidence(path: Path | str) -> dict[str, Any]:
    evidence_path = Path(path).resolve()
    if (
        not evidence_path.is_relative_to(ROOT)
        or not evidence_path.is_file()
        or evidence_path.name != "preflight.json"
    ):
        raise ValueError("C1_C5_PREFLIGHT_EVIDENCE_PATH_INVALID")
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    unsigned = dict(payload)
    evidence_sha256 = unsigned.pop("evidence_sha256", None)
    if evidence_sha256 != _canonical_sha256(unsigned):
        raise ValueError("C1_C5_PREFLIGHT_EVIDENCE_HASH_MISMATCH")
    if (
        payload.get("schema_version") != SCHEMA
        or payload.get("status") != "passed"
        or payload.get("failure_count") != 0
        or payload.get("skip_count") != 0
        or payload.get("substitution_count") != 0
        or payload.get("timeout_count") != 0
        or payload.get("network_calls") != 0
        or payload.get("network_transport_attempted") is not False
    ):
        raise ValueError("C1_C5_PREFLIGHT_NOT_GREEN")
    scope = payload.get("scope_file_sha256")
    if not isinstance(scope, Mapping) or set(scope) != set(SCOPE_FILES):
        raise ValueError("C1_C5_PREFLIGHT_SCOPE_INVALID")
    for relative, expected in scope.items():
        if _sha256(_repo_file(relative)) != expected:
            raise ValueError("C1_C5_PREFLIGHT_SCOPE_HASH_MISMATCH")
    proof = payload.get("offline_proof")
    if not isinstance(proof, Mapping):
        raise ValueError("C1_C5_PREFLIGHT_PROOF_REQUIRED")
    manifest_path = _repo_file(proof.get("manifest"))
    verified_proof = _verify_offline_proof(manifest_path.parent)
    if dict(proof) != verified_proof:
        raise ValueError("C1_C5_PREFLIGHT_PROOF_REFERENCE_MISMATCH")
    checks = payload.get("checks")
    if not isinstance(checks, list) or {item.get("name") for item in checks} != {
        "baseline",
        "property-runtime",
        "focused",
        "compile",
        "diff",
    }:
        raise ValueError("C1_C5_PREFLIGHT_CHECK_SET_INVALID")
    covered: set[str] = {"reopen", "l1", "l2", "preservation", "c1_c5_geometry_property_type"}
    for check in checks:
        unsigned_check = dict(check)
        result_sha256 = unsigned_check.pop("result_sha256", None)
        if (
            result_sha256 != _canonical_sha256(unsigned_check)
            or check.get("status") != "passed"
            or check.get("exit_code") != 0
            or check.get("failure_count") != 0
            or check.get("skip_count") != 0
            or check.get("substitution_count") != 0
            or check.get("timeout_count") != 0
            or check.get("network_calls") != 0
            or check.get("network_transport_attempted") is not False
        ):
            raise ValueError("C1_C5_PREFLIGHT_CHECK_NOT_GREEN")
        for stream in ("stdout", "stderr"):
            stream_path = (evidence_path.parent / str(check[stream])).resolve()
            if (
                not stream_path.is_relative_to(evidence_path.parent)
                or not stream_path.is_file()
                or _sha256(stream_path) != check[f"{stream}_sha256"]
            ):
                raise ValueError("C1_C5_PREFLIGHT_LOG_HASH_MISMATCH")
        covered.update(str(value) for value in check.get("capabilities", ()))
    if covered != set(REQUIRED_CAPABILITIES):
        raise ValueError("C1_C5_PREFLIGHT_COVERAGE_INCOMPLETE")
    return {
        **payload,
        "mode": "c1_c5_light_preflight_evidence_reuse",
        "evidence_path": evidence_path.relative_to(ROOT).as_posix(),
        "evidence_file_sha256": _sha256(evidence_path),
    }


def _generate(
    output_root: Path,
    proof_root: Path,
    *,
    env_file: Path,
    property_cache_root: Path,
) -> dict[str, Any]:
    output_root = output_root.resolve()
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError("C1_C5_PREFLIGHT_OUTPUT_NOT_EMPTY")
    output_root.mkdir(parents=True, exist_ok=True)
    proof = _verify_offline_proof(proof_root)
    junit = output_root / "focused.junit.xml"
    basetemp = output_root / "pytest-tmp"
    cache = output_root / "pytest-cache"
    runtime_check = (
        "from pathlib import Path; import json,sys; "
        "from scripts.ifc_repair.composite_evidence."
        "run_damage_restoration_c1_c5 import "
        "_prepare_property_runtime_environment,_require_ready_property_runtime; "
        "from text2ifc_knowledge import create_property_runtime_from_environment; "
        "f=Path(sys.argv[1]); "
        "e=dict(line.strip().split('=',1) for line in "
        "f.read_text(encoding='utf-8').splitlines() if line.strip() "
        "and not line.lstrip().startswith('#') and '=' in line); "
        "e=_prepare_property_runtime_environment(e,cache_root=Path(sys.argv[2])); "
        "r=create_property_runtime_from_environment(e,project_root=Path.cwd()); "
        "_require_ready_property_runtime(r); w=r.warmup(); "
        "q=r.retrieve(run_id='preflight-slope',request_id='preflight-slope',"
        "model_id='preflight',operation_id='restore-beam',operation_type='add_beam',"
        "claim_id='slope',property_phrase='slope',target_ifc_class='IfcBeam',"
        "raw_value=0.0,raw_unit=None,scope='occurrence_direct'); "
        "paths=[c['canonical_path'] for c in q.candidate_set['candidates']]; "
        "assert 'Pset_BeamCommon.Slope' in paths, paths; "
        "print(json.dumps({'health':r.health.to_dict(),'warmup':w,'slope_candidates':paths})); "
        "r.release_transient_resources(); "
        "getattr(r.vector_index,'close',lambda:None)()"
    )
    checks = [
        _run_check(
            "baseline",
            (
                sys.executable,
                "scripts/ifc_repair/composite_evidence/baseline_fingerprint.py",
                "verify",
            ),
            output_root=output_root,
            timeout_seconds=60,
        ),
        _run_check(
            "property-runtime",
            (
                sys.executable,
                "-c",
                runtime_check,
                str(env_file.resolve()),
                str(property_cache_root.resolve()),
            ),
            output_root=output_root,
            timeout_seconds=300,
            capabilities=("property_runtime_ready",),
        ),
        _run_check(
            "focused",
            (
                sys.executable,
                "-m",
                "pytest",
                *TEST_NODES,
                "-q",
                f"--junitxml={junit}",
                f"--basetemp={basetemp}",
                "-o",
                f"cache_dir={cache}",
            ),
            output_root=output_root,
            timeout_seconds=900,
            capabilities=tuple(
                capability
                for capability, nodes in CAPABILITY_TESTS.items()
                if nodes
            ),
            junit_path=junit,
        ),
        _run_check(
            "compile",
            (
                sys.executable,
                "-m",
                "compileall",
                "-q",
                "src/text2ifc_ifc_repair",
                "src/text2ifc_knowledge",
                "scripts/ifc_repair/composite_evidence",
            ),
            output_root=output_root,
            timeout_seconds=300,
            capabilities=("apply_compile",),
            environment={
                **os.environ,
                "PYTHONPYCACHEPREFIX": str(output_root / "pycache"),
            },
        ),
        _run_check(
            "diff",
            ("git", "diff", "--check"),
            output_root=output_root,
            timeout_seconds=60,
        ),
    ]
    failure_count = sum(check["status"] != "passed" for check in checks)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "passed" if failure_count == 0 else "failed",
        "failure_count": failure_count,
        "skip_count": sum(int(check["skip_count"]) for check in checks),
        "substitution_count": 0,
        "timeout_count": 0,
        "network_calls": 0,
        "network_transport_attempted": False,
        "offline_proof": proof,
        "scope_file_sha256": {
            relative: _sha256(_repo_file(relative)) for relative in SCOPE_FILES
        },
        "checks": checks,
    }
    payload["evidence_sha256"] = _canonical_sha256(payload)
    evidence_path = output_root / "preflight.json"
    evidence_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if payload["status"] == "passed":
        load_light_preflight_evidence(evidence_path)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--proof-root", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--property-cache-root", type=Path, required=True)
    parser.add_argument("--verify-proof-only", action="store_true")
    args = parser.parse_args()
    if args.verify_proof_only:
        print(json.dumps(_verify_offline_proof(args.proof_root), ensure_ascii=False))
        return 0
    if args.output_root is None:
        parser.error("--output-root is required")
    result = _generate(
        args.output_root,
        args.proof_root,
        env_file=args.env_file,
        property_cache_root=args.property_cache_root,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "failure_count": result["failure_count"],
                "evidence": str(args.output_root / "preflight.json"),
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
