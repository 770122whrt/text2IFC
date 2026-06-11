import json
from pathlib import Path

import ifcopenshell
from ifcopenshell.api.project.create_file import create_file

from scripts.bim_json import compile_ifc as compile_cli
from text2ifc_compiler import verify_ifc


def _run_cli(capsys, argv: list[str]) -> tuple[int, dict]:
    exit_code = compile_cli.main(argv)
    payload = json.loads(capsys.readouterr().out)
    return exit_code, payload


def test_verifier_reports_stable_errors_for_deliberately_invalid_ifc() -> None:
    invalid = create_file("IFC2X3")
    invalid.create_entity(
        "IfcRoof", GlobalId=ifcopenshell.guid.new()
    )

    issues = verify_ifc(invalid)

    assert [
        (issue.code, issue.entity, issue.attribute, issue.message)
        for issue in issues
    ] == [
        (
            "IFC_SCHEMA_ERROR",
            "IfcRoof",
            "IfcRoof.OwnerHistory",
            "Attribute not optional",
        ),
        (
            "IFC_SCHEMA_ERROR",
            "IfcRoof",
            "IfcRoof.ShapeType",
            "Attribute not optional",
        ),
    ]


def test_cli_compiles_valid_json_with_machine_readable_success(
    complete_document: dict,
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "valid.json"
    output = tmp_path / "valid.ifc"
    source.write_text(json.dumps(complete_document), encoding="utf-8")

    exit_code, payload = _run_cli(
        capsys, [str(source), str(output)]
    )

    assert exit_code == 0
    assert payload == {
        "success": True,
        "output_path": str(output.resolve()),
        "schema": "IFC2X3",
        "input_errors": [],
        "ifc_errors": [],
    }
    assert output.is_file()
    assert verify_ifc(output) == ()


def test_cli_contract_failure_preserves_existing_destination(
    complete_document: dict,
    tmp_path: Path,
    capsys,
) -> None:
    complete_document.pop("target_schema")
    source = tmp_path / "invalid.json"
    output = tmp_path / "existing.ifc"
    source.write_text(json.dumps(complete_document), encoding="utf-8")
    sentinel = b"existing-output"
    output.write_bytes(sentinel)
    before = set(tmp_path.iterdir())

    exit_code, payload = _run_cli(
        capsys, [str(source), str(output)]
    )

    assert exit_code == 1
    assert payload["success"] is False
    assert payload["output_path"] is None
    assert payload["schema"] is None
    assert [
        (issue["code"], issue["path"])
        for issue in payload["input_errors"]
    ] == [("REQUIRED_FIELD", "/target_schema")]
    assert payload["ifc_errors"] == []
    assert output.read_bytes() == sentinel
    assert set(tmp_path.iterdir()) == before


def test_cli_rejects_malformed_and_oversized_json(
    tmp_path: Path,
    capsys,
) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    malformed_output = tmp_path / "malformed.ifc"

    malformed_code, malformed_payload = _run_cli(
        capsys, [str(malformed), str(malformed_output)]
    )

    assert malformed_code == 2
    assert malformed_payload["input_errors"][0]["code"] == "INVALID_JSON"
    assert not malformed_output.exists()

    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b" " * (compile_cli.MAX_INPUT_BYTES + 1))
    oversized_output = tmp_path / "oversized.ifc"

    oversized_code, oversized_payload = _run_cli(
        capsys, [str(oversized), str(oversized_output)]
    )

    assert oversized_code == 2
    assert oversized_payload["input_errors"][0]["code"] == "FILE_TOO_LARGE"
    assert not oversized_output.exists()


def test_cli_usage_failure_is_stable(capsys) -> None:
    exit_code, payload = _run_cli(capsys, [])

    assert exit_code == 2
    assert payload["input_errors"] == [
        {
            "code": "USAGE_ERROR",
            "path": "/",
            "message": "Expected input JSON and output IFC paths.",
        }
    ]


def test_cli_output_failure_is_machine_readable(
    complete_document: dict,
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "valid.json"
    source.write_text(json.dumps(complete_document), encoding="utf-8")
    output = tmp_path / "missing-parent" / "output.ifc"

    exit_code, payload = _run_cli(
        capsys, [str(source), str(output)]
    )

    assert exit_code == 1
    assert payload["success"] is False
    assert payload["input_errors"] == []
    assert [issue["code"] for issue in payload["ifc_errors"]] == [
        "IFC_OUTPUT_ERROR"
    ]
    assert not output.exists()
