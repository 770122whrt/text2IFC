from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from text2ifc_compiler import compile_document
from text2ifc_compiler.verification import IfcValidationIssue
from text2ifc_jsonfix.repair_cases import repair_case


def _api():
    try:
        module = importlib.import_module("text2ifc_jsonfix.ifc_artifact")
    except ModuleNotFoundError as exc:
        pytest.fail(f"strict IFC2X3 artifact checker is not implemented: {exc}")
    return module


def _step(schema_clause: str) -> str:
    return (
        "ISO-10303-21;\n"
        "HEADER;\n"
        "FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');\n"
        "FILE_NAME('fixture.ifc','2026-06-21T00:00:00',(),(),'',"
        "'text2IFC','');\n"
        f"{schema_clause}\n"
        "ENDSEC;\n"
        "DATA;\n"
        "ENDSEC;\n"
        "END-ISO-10303-21;\n"
    )


def _write(path: Path, schema_clause: str) -> Path:
    path.write_text(_step(schema_clause), encoding="ascii")
    return path


def _codes(result) -> set[str]:
    return {issue["code"] for issue in result.issues}


def test_real_generated_ifc2x3_passes_all_strict_gates(tmp_path: Path) -> None:
    module = _api()
    case = repair_case("missing-piece-repair")
    output = tmp_path / "output.ifc"
    compilation = compile_document(case["expected"], output)
    assert compilation.success

    result = module.check_ifc2x3_artifact(output)

    assert result.success
    assert result.declared_file_schema == "IFC2X3"
    assert result.declared_schema_identifiers == ("IFC2X3",)
    assert result.reopened_schema == "IFC2X3"
    assert result.ifc_validation_error_count == 0
    assert result.issues == ()


@pytest.mark.parametrize("schema", ["IFC4", "IFC4X3"])
def test_non_ifc2x3_declaration_fails_even_when_reopen_matches(
    schema: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _api()
    path = _write(tmp_path / f"{schema}.ifc", f"FILE_SCHEMA(('{schema}'));")

    class Model:
        def __init__(self, value: str) -> None:
            self.schema = value

    monkeypatch.setattr(module.ifcopenshell, "open", lambda _: Model(schema))
    monkeypatch.setattr(module, "verify_ifc", lambda _: ())

    result = module.check_ifc2x3_artifact(path)

    assert not result.success
    assert result.declared_file_schema == schema
    assert result.reopened_schema == schema
    assert "DECLARED_SCHEMA_NOT_IFC2X3" in _codes(result)
    assert "REOPENED_SCHEMA_NOT_IFC2X3" in _codes(result)


@pytest.mark.parametrize(
    ("schema_clause", "expected_code"),
    [
        ("", "FILE_SCHEMA_MISSING"),
        (
            "FILE_SCHEMA(('IFC2X3','IFC4'));",
            "FILE_SCHEMA_IDENTIFIER_COUNT",
        ),
        (
            "FILE_SCHEMA(('IFC2X3'));\nFILE_SCHEMA(('IFC2X3'));",
            "FILE_SCHEMA_DECLARATION_COUNT",
        ),
    ],
)
def test_missing_or_ambiguous_file_schema_fails(
    schema_clause: str,
    expected_code: str,
    tmp_path: Path,
) -> None:
    module = _api()
    path = _write(tmp_path / "ambiguous.ifc", schema_clause)

    result = module.check_ifc2x3_artifact(path)

    assert not result.success
    assert expected_code in _codes(result)


def test_reopen_failure_is_a_hard_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _api()
    path = _write(
        tmp_path / "broken.ifc",
        "FILE_SCHEMA(('IFC2X3'));",
    )

    def fail_open(_: str):
        raise RuntimeError("cannot reopen")

    monkeypatch.setattr(module.ifcopenshell, "open", fail_open)

    result = module.check_ifc2x3_artifact(path)

    assert not result.success
    assert result.reopened_schema is None
    assert "IFC_REOPEN_FAILED" in _codes(result)


def test_declared_and_reopened_schema_mismatch_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _api()
    path = _write(
        tmp_path / "mismatch.ifc",
        "FILE_SCHEMA(('IFC2X3'));",
    )

    class Model:
        schema = "IFC4"

    monkeypatch.setattr(module.ifcopenshell, "open", lambda _: Model())
    monkeypatch.setattr(module, "verify_ifc", lambda _: ())

    result = module.check_ifc2x3_artifact(path)

    assert not result.success
    assert result.declared_file_schema == "IFC2X3"
    assert result.reopened_schema == "IFC4"
    assert "SCHEMA_DECLARATION_REOPEN_MISMATCH" in _codes(result)


def test_full_ifc_validation_errors_fail_the_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _api()
    case = repair_case("missing-piece-repair")
    output = tmp_path / "invalid.ifc"
    assert compile_document(case["expected"], output).success
    monkeypatch.setattr(
        module,
        "verify_ifc",
        lambda _: (
            IfcValidationIssue(
                code="IFC_EXPRESS_RULE",
                entity="IfcWall:#1",
                attribute="",
                message="Synthetic rule failure.",
            ),
        ),
    )

    result = module.check_ifc2x3_artifact(output)

    assert not result.success
    assert result.ifc_validation_error_count == 1
    assert "IFC_VALIDATION_ERRORS" in _codes(result)
