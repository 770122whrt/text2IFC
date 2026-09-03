from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from types import SimpleNamespace

import ifcopenshell

from text2ifc_ifc_repair.orchestrator import RepairOrchestrator


def _ifc(path: Path) -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    model.create_entity("IfcProject", GlobalId="0000000000000000000001", Name="Fixture")
    model.write(str(path))


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _evaluation(publishable: bool) -> dict[str, object]:
    status = "passed" if publishable else "failed"
    return {
        "schema_version": "text2ifc/ifc-repair-evaluation-public/0.2",
        "policy_version": "phase8.1",
        "status": status,
        "reason": "fixture evaluation",
        "complete_repair_success": publishable,
        "successful_artifact_publishable": publishable,
        "diagnostic_artifact_retained": not publishable,
        "application": {"check_id": "application.valid", "status": status, "reason": "fixture"},
        "preservation": {"check_id": "preservation.valid", "status": status, "reason": "fixture"},
        "operations": [],
    }


def test_complete_multi_operation_transaction_runs_once_and_publishes_only_after_evaluation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.ifc"
    _ifc(source)
    source_hash = _sha256(source)
    calls = {"transaction": 0, "evaluation": 0}

    def transaction_stage(**kwargs):
        calls["transaction"] += 1
        output = Path(kwargs["output_path"])
        shutil.copyfile(kwargs["damaged_ifc_path"], output)
        return {
            "valid": True,
            "published": True,
            "audit": {
                "valid": True,
                "operation_audits": [
                    {"operation_id": "operation-1", "valid": True},
                    {"operation_id": "operation-2", "valid": True},
                ],
                "issues": [],
            },
            "operations": [
                {"operation_id": "operation-1", "changes": {}},
                {"operation_id": "operation-2", "changes": {}},
            ],
            "postconditions": [],
            "output": {"path": str(output), "sha256": _sha256(output).removeprefix("sha256:")},
            "issues": [],
        }

    def evaluation_stage(inputs):
        calls["evaluation"] += 1
        assert tuple(inputs.expected_facts_by_operation) == ("operation-1", "operation-2")
        return _evaluation(True)

    evidence = SimpleNamespace(
        expected_facts_by_operation={"operation-1": (), "operation-2": ()},
        applicability_by_operation={"operation-1": {}, "operation-2": {}},
        conflicts=(),
    )
    orchestrator = RepairOrchestrator(
        run_directory=tmp_path / "run",
        changeset_stage=lambda _: None,
        apply_stage=transaction_stage,
        evaluation_stage=evaluation_stage,
        evidence_builder=lambda **kwargs: evidence,
    )
    changeset = {
        "base_model_fingerprint": source_hash,
        "operations": [
            {"operation_id": "operation-1", "operation_type": "fixture"},
            {"operation_id": "operation-2", "operation_type": "fixture"},
        ],
    }

    result = orchestrator.apply_and_evaluate(
        source_ifc_path=source,
        repair_request="apply two operations",
        intent=SimpleNamespace(),
        resolution=SimpleNamespace(),
        changeset=changeset,
        registry=SimpleNamespace(),
        records_by_global_id={},
        type_records_by_global_id={},
    )

    assert calls == {"transaction": 1, "evaluation": 1}
    assert _sha256(source) == source_hash
    assert result.status == "succeeded"
    assert result.successful_ifc is not None
    assert Path(result.successful_ifc).is_file()
    assert ifcopenshell.open(result.successful_ifc).schema == "IFC2X3"
    assert result.diagnostic_candidate is None


def test_one_mandatory_operation_failure_keeps_the_whole_changeset_unpublished(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.ifc"
    _ifc(source)
    calls = {"transaction": 0, "evaluation": 0}

    def failed_transaction(**kwargs):
        calls["transaction"] += 1
        return {
            "valid": False,
            "published": False,
            "audit": {
                "valid": False,
                "operation_audits": [
                    {"operation_id": "operation-1", "valid": True},
                    {"operation_id": "operation-2", "valid": False},
                ],
                "issues": [{"code": "PRECONDITION_FAILED"}],
            },
            "operations": [],
            "postconditions": [],
            "output": None,
            "issues": [{"code": "PRECONDITION_FAILED"}],
        }

    def must_not_evaluate(_inputs):
        calls["evaluation"] += 1
        raise AssertionError("production evaluator must not receive a partial candidate")

    orchestrator = RepairOrchestrator(
        run_directory=tmp_path / "run",
        changeset_stage=lambda _: None,
        apply_stage=failed_transaction,
        evaluation_stage=must_not_evaluate,
    )
    result = orchestrator.apply_and_evaluate(
        source_ifc_path=source,
        repair_request="apply two operations",
        intent=SimpleNamespace(),
        resolution=SimpleNamespace(),
        changeset={
            "base_model_fingerprint": _sha256(source),
            "operations": [
                {"operation_id": "operation-1", "operation_type": "fixture"},
                {"operation_id": "operation-2", "operation_type": "fixture"},
            ],
        },
        registry=SimpleNamespace(),
        records_by_global_id={},
        type_records_by_global_id={},
    )

    assert calls == {"transaction": 1, "evaluation": 0}
    assert result.status == "audit_failed"
    assert result.successful_ifc is None
    assert result.diagnostic_candidate is None
    assert result.evaluation["schema_version"].endswith("/0.2")
