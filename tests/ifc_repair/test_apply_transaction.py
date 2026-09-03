import hashlib
from pathlib import Path

import ifcopenshell

from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.mutation import remove_window_and_opening
from text2ifc_ifc_repair.registry import OperationDefinition, OperationRegistry


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "dataset"
    / "external"
    / "bim-whale-ifc-samples"
    / "LargeBuilding"
    / "IFC"
    / "LargeBuilding.ifc"
)
WALL_ID = "1F6umJ5H50aeL3A1As_wTm"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _definition(operation_type: str, *, fail_apply: bool = False) -> OperationDefinition:
    def applicator(**kwargs):
        if fail_apply:
            raise RuntimeError("fixture apply failure")
        return {"created": [], "modified": [], "removed": []}

    return OperationDefinition(
        operation_type=operation_type,
        target_ifc_classes=("IfcWall",),
        parameter_schema={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["marker"],
            "properties": {"marker": {"type": "string"}},
        },
        context_adapter=lambda **kwargs: {},
        precondition_checker=lambda **kwargs: {
            "checks": [{"code": "FIXTURE_READY", "status": "passed", "evidence": {}}],
            "issues": [],
            "evidence": {},
        },
        applicator=applicator,
        postcondition_checker=lambda **kwargs: {
            "valid": True,
            "checks": [{"code": "FIXTURE_DONE", "status": "passed", "evidence": {}}],
            "issues": [],
        },
        comparison_adapter=lambda **kwargs: {},
        capability_constraints={"fixture": True},
    )


def _changeset(damaged: Path, request: str, operation_types: list[str]) -> dict:
    evidence = ["request:/fixture"]
    return {
        "schema_version": "text2ifc/ifc-repair-changeset/0.1",
        "changeset_id": "changeset-transaction-fixture",
        "base_model_fingerprint": "sha256:" + _sha256(damaged),
        "source_request_hash": "sha256:"
        + hashlib.sha256(request.encode("utf-8")).hexdigest(),
        "scope": {"target_ids": [WALL_ID], "forbidden_ids": []},
        "evidence_refs": evidence,
        "preconditions": ["target_exists"],
        "postconditions": ["fixture_done"],
        "operations": [
            {
                "operation_id": f"operation-{index}",
                "operation_type": operation_type,
                "target": {"wall_global_id": WALL_ID},
                "parameters": {"marker": operation_type},
                "evidence_refs": evidence,
            }
            for index, operation_type in enumerate(operation_types, start=1)
        ],
    }


def _damaged_case(tmp_path: Path) -> Path:
    case_dir = tmp_path / "case"
    remove_window_and_opening(
        source_path=SOURCE,
        output_dir=case_dir,
        wall_global_id=WALL_ID,
        opening_global_id="2cXV28XOjE6f6irhW0CO4t",
        window_global_id="2cXV28XOjE6f6irgi0CO4t",
    )
    return case_dir / "damaged.ifc"


def test_transaction_publishes_only_after_reopen_and_postconditions(
    tmp_path: Path,
) -> None:
    damaged = _damaged_case(tmp_path)
    before_hash = _sha256(damaged)
    output = tmp_path / "repaired.ifc"
    request = "fixture transaction\n"
    registry = OperationRegistry()
    registry.register(_definition("fixture_noop"))

    result = apply_changeset(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=_changeset(damaged, request, ["fixture_noop"]),
        output_path=output,
        registry=registry,
    )

    assert result["valid"] is True
    assert result["published"] is True
    assert result["operations"][0]["changes"] == {
        "created": [],
        "modified": [],
        "removed": [],
    }
    assert _sha256(damaged) == before_hash
    assert ifcopenshell.open(str(output)).schema == "IFC2X3"


def test_transaction_failure_leaves_no_repaired_artifact(tmp_path: Path) -> None:
    damaged = _damaged_case(tmp_path)
    output = tmp_path / "repaired.ifc"
    request = "fixture transaction\n"
    registry = OperationRegistry()
    registry.register(_definition("fixture_first"))
    registry.register(_definition("fixture_fails", fail_apply=True))

    result = apply_changeset(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=_changeset(
            damaged, request, ["fixture_first", "fixture_fails"]
        ),
        output_path=output,
        registry=registry,
    )

    assert result["valid"] is False
    assert result["published"] is False
    assert [issue["code"] for issue in result["issues"]] == [
        "OPERATION_APPLICATION_FAILED"
    ]
    assert not output.exists()
