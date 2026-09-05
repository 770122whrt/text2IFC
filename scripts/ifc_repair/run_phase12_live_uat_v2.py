"""Versioned Phase 12 Plan 07 live UAT on reconstructable VVO damage."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scripts.ifc_repair import run_phase12_live_uat as base
from text2ifc_agent.openai_compat import (
    OpenAICompatibleLiveProvider,
    load_openai_compatible_runtime_config,
)
from text2ifc_knowledge.property_runtime import (
    create_property_runtime_from_environment,
)


DEFAULT_OUTPUT = ROOT / "dataset/processed/ifc-repair-runs/phase12-live-v2"
DEFAULT_PROOF_ROOT = (
    ROOT / "dataset/processed/proof/ifc-repair-success-cases-v2-plan07-staging"
)
SOURCE = (
    ROOT
    / "dataset/processed/ifc-repair-runs"
    / "phase12-plan07-v2-restoration-20260903T-live-baseline"
    / "accepted/phase12-v2-vvo-beam-column-atomic-restoration/damaged.ifc"
)
FROZEN_SOURCE_SHA256 = (
    "sha256:636135b4bc12ea3e45d9a7155f714834"
    "ff5eaaba1f2d3d2e7a5ae84a525a59aa"
)
LIVE_CASE_CONTRACT_VERSION = "phase12-plan07-live-cases/0.2"
APPROVED_MODEL = "deepseek-v4-flash"

COMPLETE_REQUEST = (
    'In the damaged IFC, on the Building Storey named "标高7", restore the '
    "missing horizontal straight rectangular Beam with center axis from "
    "(-3316.629521, -3863.522838, 0) mm to "
    "(-3316.629521, -8803.522838, 0) mm and a rectangular section 455 mm "
    'wide and 570 mm high. On the Building Storey named "标高0", restore '
    "the missing vertical straight rectangular Column with center-axis base "
    "(-3307.426702, -9061.783140, 0) mm and top "
    "(-3307.426702, -9061.783140, 3712.059993) mm and a square section "
    "500 mm wide and 500 mm deep. Create both in one atomic ChangeSet, "
    "generate dedicated structural Types, state that the Beam is load "
    "bearing, and state that the Column is load bearing."
)
CLARIFICATION_REQUEST = (
    'In the damaged IFC, on the Building Storey named "标高0", restore the '
    "missing vertical straight rectangular Column with center-axis base "
    "(-3307.426702, -9061.783140, 0) mm and top "
    "(-3307.426702, -9061.783140, 3712.059993) mm and a square section "
    "500 mm wide and 500 mm deep. Set its natural-language property "
    '"load bearing status or external status" to true, but do not choose '
    "between those two meanings without clarification."
)
CLARIFICATION_PROPERTY_IDENTITY = base.CLARIFICATION_PROPERTY_IDENTITY
WINDOW_SEMANTIC_REQUEST = (
    'For the IfcWindow with GlobalId "2IUEnGd5v4Yfg1ZlPtd0c_", set '
    "外窗=true on this occurrence only. Do not change its Type or any "
    "other Window."
)
PROGRAM_GUARD_REQUEST = (
    'On the IFC Building Storey named "标高7", add a straight rectangular '
    "Beam and attach a structural analysis node; structural analysis "
    "relationships are outside this operation contract."
)

DEFAULT_CASES = (
    base.LiveCase(case_id="complete", request=COMPLETE_REQUEST),
    base.LiveCase(
        case_id="clarification-resume",
        request=CLARIFICATION_REQUEST,
        feedback=CLARIFICATION_PROPERTY_IDENTITY,
        feedback_kind="select_candidate",
    ),
    base.LiveCase(
        case_id="window-semantic-canary",
        request=WINDOW_SEMANTIC_REQUEST,
    ),
    base.LiveCase(
        case_id="program-guard",
        request=PROGRAM_GUARD_REQUEST,
        expect_program_guard=True,
    ),
)
REQUIRED_CASE_IDS = tuple(case.case_id for case in DEFAULT_CASES)
_case_matrix_sha256 = base._case_matrix_sha256
FROZEN_CASE_MATRIX_SHA256 = (
    "sha256:9c2328f09d36bcad1b393337aa5d0308"
    "77e8a53b24c1ffaed87db4723de24afb"
)
V2_ADMISSION_SCHEMA = "text2ifc/phase12-live-changed-scope-admission/0.2"
V2_ADMISSION_BASIS = (
    "prior full-preflight admission plus zero-network revalidation of every "
    "Plan 07 v2 changed scope"
)
V2_REQUIRED_SCOPE_FILES = frozenset(
    {
        "scripts/ifc_repair/run_phase12_offline.py",
        "scripts/ifc_repair/curate_phase12_structural_proof.py",
        "scripts/ifc_repair/validate_success_cases.py",
        "scripts/ifc_repair/run_phase12_live_uat.py",
        "scripts/ifc_repair/run_phase12_live_uat_v2.py",
        "src/text2ifc_ifc_repair/index_adapters.py",
        "src/text2ifc_ifc_repair/indexer.py",
        "src/text2ifc_ifc_repair/mutation.py",
        "src/text2ifc_ifc_repair/structural_restoration.py",
        "tests/ifc_repair/test_phase12_dataset_e2e.py",
        "tests/ifc_repair/test_phase12_live_uat.py",
        "tests/ifc_repair/test_phase12_live_uat_v2.py",
        "tests/ifc_repair/test_structural_index.py",
        "tests/ifc_repair/test_structural_mutation.py",
        "tests/ifc_repair/test_structural_restoration.py",
    }
)


def _evidence_path(record: Any) -> Path:
    if not isinstance(record, Mapping):
        raise ValueError("LIVE_V2_ADMISSION_EVIDENCE_RECORD_INVALID")
    path = (ROOT / str(record.get("path") or "")).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("LIVE_V2_ADMISSION_EVIDENCE_PATH_INVALID")
    if base._path_sha256(path) != record.get("sha256"):
        raise ValueError("LIVE_V2_ADMISSION_EVIDENCE_HASH_MISMATCH")
    return path


def _junit_counts(path: Path) -> dict[str, int]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    return {
        key: sum(int(suite.get(key, "0")) for suite in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }


def _load_v2_changed_scope_admission(path: Path | str) -> dict[str, Any]:
    admission_path = Path(path).resolve()
    if not admission_path.is_relative_to(ROOT) or not admission_path.is_file():
        raise ValueError("LIVE_V2_ADMISSION_PATH_INVALID")
    payload = json.loads(admission_path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != V2_ADMISSION_SCHEMA
        or payload.get("status") != "passed"
        or payload.get("admission_basis") != V2_ADMISSION_BASIS
        or payload.get("provider_calls") != 0
        or payload.get("network_transport_attempted") is not False
        or payload.get("skip_count") != 0
        or payload.get("substitution_count") != 0
        or payload.get("timeout_count") != 0
        or payload.get("case_contract_version")
        != LIVE_CASE_CONTRACT_VERSION
        or payload.get("case_matrix_sha256") != FROZEN_CASE_MATRIX_SHA256
        or payload.get("source_sha256") != FROZEN_SOURCE_SHA256
    ):
        raise ValueError("LIVE_V2_ADMISSION_CONTRACT_INVALID")

    parent = json.loads(
        _evidence_path(payload.get("parent_admission")).read_text(
            encoding="utf-8"
        )
    )
    if (
        parent.get("schema_version") != base.CHANGED_SCOPE_ADMISSION_SCHEMA
        or parent.get("status") != "passed"
        or parent.get("provider_calls") != 0
        or parent.get("network_transport_attempted") is not False
    ):
        raise ValueError("LIVE_V2_PARENT_ADMISSION_INVALID")

    offline = json.loads(
        _evidence_path(payload.get("offline_matrix")).read_text(encoding="utf-8")
    )
    if (
        offline.get("status") != "passed"
        or offline.get("matrix_complete") is not True
        or len(offline.get("accepted_cases", ())) != 6
        or len(offline.get("failed_cases", ())) != 2
        or offline.get("property_resolution", {}).get("provider_network_calls")
        != 0
    ):
        raise ValueError("LIVE_V2_OFFLINE_MATRIX_INVALID")

    proof = json.loads(
        _evidence_path(payload.get("proof_validation")).read_text(
            encoding="utf-8-sig"
        )
    )
    if (
        proof.get("status") != "passed"
        or proof.get("case_count") != 6
        or proof.get("operation_count") != 12
        or proof.get("errors") != []
        or proof.get("legacy_unverifiable_case_count") != 0
        or any(
            case.get("structural_audit_coverage")
            != "strict_restoration_triplet_recomputed"
            or case.get("independent_structural_restoration_eligible") is not True
            for case in proof.get("cases", ())
        )
    ):
        raise ValueError("LIVE_V2_PROOF_VALIDATION_INVALID")

    if _junit_counts(_evidence_path(payload.get("structural_junit"))) != {
        "tests": 13,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
    }:
        raise ValueError("LIVE_V2_STRUCTURAL_TESTS_INVALID")
    if _junit_counts(_evidence_path(payload.get("live_runner_junit"))) != {
        "tests": 108,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
    }:
        raise ValueError("LIVE_V2_RUNNER_TESTS_INVALID")

    scope_hashes = payload.get("scope_file_sha256")
    if (
        not isinstance(scope_hashes, Mapping)
        or set(scope_hashes) != V2_REQUIRED_SCOPE_FILES
        or any(
            base._path_sha256((ROOT / relative).resolve()) != digest
            for relative, digest in scope_hashes.items()
        )
    ):
        raise ValueError("LIVE_V2_SCOPE_HASH_MISMATCH")
    if base._path_sha256(SOURCE) != FROZEN_SOURCE_SHA256:
        raise ValueError("LIVE_V2_SOURCE_DRIFT")
    return {
        **payload,
        "mode": "changed_scope_evidence_reuse_v2",
        "admission_path": admission_path.relative_to(ROOT).as_posix(),
    }


def run_live_uat_v2(
    output_root: Path | str,
    *,
    transport_factory: Callable[[], Any],
    proof_root: Path | str = DEFAULT_PROOF_ROOT,
    preflight_only: bool = False,
    admission_evidence_path: Path | str | None = None,
    property_runtime_factory: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    return base.run_live_uat(
        output_root,
        transport_factory=transport_factory,
        cases=DEFAULT_CASES,
        proof_root=proof_root,
        preflight_only=preflight_only,
        admission_evidence_path=admission_evidence_path,
        property_runtime_factory=property_runtime_factory,
        source_path=SOURCE,
        expected_source_sha256=FROZEN_SOURCE_SHA256,
        required_case_ids=REQUIRED_CASE_IDS,
        case_matrix_sha256=FROZEN_CASE_MATRIX_SHA256,
        case_contract_version=LIVE_CASE_CONTRACT_VERSION,
        admission_loader=_load_v2_changed_scope_admission,
    )


def _config_ready(environment: Mapping[str, str]) -> dict[str, Any]:
    config = base._config(environment)
    config["required_model"] = APPROVED_MODEL
    if config.get("model") != APPROVED_MODEL:
        config["status"] = "not_configured"
        config["reason_code"] = "LIVE_V2_MODEL_MISMATCH"
    return config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--require-green-preflight", action="store_true")
    parser.add_argument("--changed-scope-admission", type=Path)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--proof-root", type=Path, default=DEFAULT_PROOF_ROOT)
    args = parser.parse_args(argv)

    environment = base._environment(args.env_file)
    config = _config_ready(environment)
    if args.check_config:
        print(json.dumps(config, ensure_ascii=False, sort_keys=True))
        return 0 if config["status"] == "ready" else 2
    if not args.preflight_only and not args.require_green_preflight:
        parser.error("--require-green-preflight is mandatory for live execution")
    if not args.preflight_only and args.changed_scope_admission is None:
        parser.error(
            "--changed-scope-admission is mandatory for live execution"
        )
    if not args.preflight_only and config["status"] != "ready":
        print(json.dumps(config, ensure_ascii=False, sort_keys=True))
        return 2

    run_kind = "preflight" if args.preflight_only else "uat"
    run_dir = args.output_root / datetime.now(timezone.utc).strftime(
        f"{run_kind}-%Y%m%dT%H%M%S%fZ"
    )

    def transport_factory() -> OpenAICompatibleLiveProvider:
        if args.preflight_only:
            raise AssertionError("preflight-only must not construct Provider transport")
        runtime = load_openai_compatible_runtime_config(environment)
        if runtime.model != APPROVED_MODEL:
            raise ValueError("LIVE_V2_MODEL_MISMATCH")
        return OpenAICompatibleLiveProvider(config=runtime)

    result = run_live_uat_v2(
        run_dir,
        transport_factory=transport_factory,
        proof_root=args.proof_root,
        preflight_only=args.preflight_only,
        admission_evidence_path=args.changed_scope_admission,
        property_runtime_factory=lambda: create_property_runtime_from_environment(
            environment,
            project_root=ROOT,
        ),
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "reason_code": result.get("reason_code"),
                "transport_calls": result["transport_calls"],
                "result": str(run_dir / "live-uat-result.json"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    expected = "preflight_passed" if args.preflight_only else "passed"
    return 0 if result["status"] == expected else 2


if __name__ == "__main__":
    raise SystemExit(main())
