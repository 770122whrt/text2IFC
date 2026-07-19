from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import ifcopenshell
import pytest

from text2ifc_ifc_repair.orchestrator import RepairOrchestrator
from text2ifc_ifc_repair.run_artifacts import (
    RunArtifactError,
    publish_terminal_artifacts,
)


CANARY = "CANARY-GOLD-PRIVATE-09-04"


def _evaluation() -> dict[str, object]:
    return {
        "schema_version": "text2ifc/ifc-repair-evaluation-public/0.2",
        "policy_version": "phase8.1",
        "status": "passed",
        "reason": "public",
        "complete_repair_success": True,
        "successful_artifact_publishable": True,
        "diagnostic_artifact_retained": False,
        "application": {"check_id": "application.valid", "status": "passed", "reason": "public"},
        "preservation": {"check_id": "preservation.valid", "status": "passed", "reason": "public"},
        "operations": [],
    }


def _candidate(path: Path) -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    model.create_entity("IfcProject", GlobalId="0000000000000000000001")
    model.write(str(path))


def test_production_orchestrator_and_artifact_signatures_have_no_gold_channel() -> None:
    forbidden = {
        "original_ifc_path", "private_original_ifc_path", "mutation_mapping",
        "private_mutation_mapping", "gold", "gold_facts",
    }
    assert forbidden.isdisjoint(inspect.signature(RepairOrchestrator).parameters)
    assert forbidden.isdisjoint(inspect.signature(RepairOrchestrator.apply_and_evaluate).parameters)
    assert forbidden.isdisjoint(inspect.signature(publish_terminal_artifacts).parameters)


def test_whole_public_bundle_canary_scan_is_terminal_and_leaks_no_canary(
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    run.mkdir()
    candidate = run / "candidate.ifc"
    _candidate(candidate)

    with pytest.raises(RunArtifactError, match="PRIVATE_CANARY") as error:
        publish_terminal_artifacts(
            run_directory=run,
            terminal_status="succeeded",
            evaluation=_evaluation(),
            candidate_ifc_path=candidate,
            evidence={"provider_prompt": CANARY},
            private_canaries=(CANARY,),
        )

    assert CANARY not in str(error.value)
    assert not (run / "successful" / "repaired.ifc").exists()
    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in run.rglob("*")
        if path.is_file() and path.suffix != ".ifc"
    )
    assert CANARY not in public_text


def test_candidate_path_escape_symlink_and_hash_tamper_fail_closed(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    outside = tmp_path / "outside.ifc"
    _candidate(outside)

    with pytest.raises(RunArtifactError, match="CANDIDATE_OUTSIDE_RUN"):
        publish_terminal_artifacts(
            run_directory=run,
            terminal_status="succeeded",
            evaluation=_evaluation(),
            candidate_ifc_path=outside,
            evidence={},
        )

    candidate = run / "candidate.ifc"
    _candidate(candidate)
    wrong_hash = "sha256:" + "0" * 64
    with pytest.raises(RunArtifactError, match="CANDIDATE_HASH_MISMATCH"):
        publish_terminal_artifacts(
            run_directory=run,
            terminal_status="succeeded",
            evaluation=_evaluation(),
            candidate_ifc_path=candidate,
            expected_candidate_sha256=wrong_hash,
            evidence={},
        )


def test_manifest_uses_relative_bounded_paths_and_is_signed_by_content(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    candidate = run / "candidate.ifc"
    _candidate(candidate)
    artifacts = publish_terminal_artifacts(
        run_directory=run,
        terminal_status="succeeded",
        evaluation=_evaluation(),
        candidate_ifc_path=candidate,
        expected_candidate_sha256="sha256:" + hashlib.sha256(candidate.read_bytes()).hexdigest(),
        evidence={"safe": True},
    )
    manifest = json.loads(Path(artifacts.manifest_path).read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "text2ifc/ifc-repair-artifact-manifest/0.1"
    assert len(manifest["artifacts"]) <= 64
    assert all(not Path(item["path"]).is_absolute() for item in manifest["artifacts"])
    assert all(".." not in Path(item["path"]).parts for item in manifest["artifacts"])
    assert all(len(item["sha256"]) == 64 for item in manifest["artifacts"])
