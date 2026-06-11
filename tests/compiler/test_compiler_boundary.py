import copy
from pathlib import Path

import pytest

import text2ifc_compiler.compiler as compiler_module
from text2ifc_compiler import (
    IfcValidationIssue,
    compile_document,
    containment_map,
    hierarchy_snapshot,
    identity_map,
    open_ifc,
    verify_ifc,
)


IFC_CLASS_BY_KIND = {
    "wall": "IfcWall",
    "column": "IfcColumn",
    "beam": "IfcBeam",
    "slab": "IfcSlab",
    "door": "IfcDoor",
    "window": "IfcWindow",
    "stair": "IfcStair",
    "stair_flight": "IfcStairFlight",
    "roof": "IfcRoof",
}


def _remove_required_field(document: dict) -> dict:
    document.pop("target_schema")
    return document


def _duplicate_id(document: dict) -> dict:
    document["elements"][0]["id"] = document["project"]["id"]
    return document


def _break_storey_reference(document: dict) -> dict:
    document["elements"][0]["storey_id"] = "missing-storey"
    return document


@pytest.mark.parametrize(
    ("mutate", "expected_code", "expected_path"),
    [
        (_remove_required_field, "REQUIRED_FIELD", "/target_schema"),
        (_duplicate_id, "DUPLICATE_ID", "/elements/0/id"),
        (
            _break_storey_reference,
            "UNRESOLVED_STOREY_REFERENCE",
            "/elements/0/storey_id",
        ),
    ],
)
def test_invalid_input_returns_contract_issues_without_touching_output(
    complete_document: dict,
    tmp_path: Path,
    mutate,
    expected_code: str,
    expected_path: str,
) -> None:
    output = tmp_path / "model.ifc"
    sentinel = b"existing-ifc-sentinel"
    output.write_bytes(sentinel)

    result = compile_document(mutate(complete_document), output)

    assert not result.success
    assert result.output_path is None
    assert [(issue.code, issue.path) for issue in result.input_issues] == [
        (expected_code, expected_path)
    ]
    assert result.ifc_issues == ()
    assert output.read_bytes() == sentinel
    assert set(tmp_path.iterdir()) == {output}


def test_complete_document_compiles_to_reopenable_ifc2x3(
    complete_document: dict, tmp_path: Path
) -> None:
    output = tmp_path / "complete.ifc"

    result = compile_document(complete_document, output)

    assert result.success
    assert result.output_path == output.resolve()
    model = open_ifc(output)
    assert model.schema == "IFC2X3"
    assert len(model.by_type("IfcProject")) == 1
    assert verify_ifc(model) == ()


def test_hierarchy_names_elevations_and_aggregation_are_exact(
    complete_document: dict, tmp_path: Path
) -> None:
    output = tmp_path / "hierarchy.ifc"
    compile_document(complete_document, output)

    snapshot = hierarchy_snapshot(output)

    assert snapshot == {
        "project": {
            "id": "project-001",
            "name": "Complete contract project",
        },
        "site": {"id": "site-001", "name": "Main site"},
        "building": {"id": "building-001", "name": "Main building"},
        "storeys": [
            {"id": "storey-001", "name": "Ground floor", "elevation": 0.0},
            {
                "id": "storey-002",
                "name": "First floor",
                "elevation": 3000.0,
            },
        ],
    }


def test_all_supported_classes_counts_and_containment_are_exact(
    complete_document: dict, tmp_path: Path
) -> None:
    output = tmp_path / "elements.ifc"
    compile_document(complete_document, output)
    model = open_ifc(output)

    expected_counts = {
        ifc_class: sum(
            element["kind"] == kind
            for element in complete_document["elements"]
        )
        for kind, ifc_class in IFC_CLASS_BY_KIND.items()
    }
    assert {
        ifc_class: len(model.by_type(ifc_class))
        for ifc_class in IFC_CLASS_BY_KIND.values()
    } == expected_counts
    assert containment_map(model) == {
        element["id"]: element["storey_id"]
        for element in complete_document["elements"]
    }


def test_identity_mapping_is_unique_stable_and_recoverable(
    complete_document: dict,
    canonical_ids: set[str],
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.ifc"
    second = tmp_path / "second.ifc"

    compile_document(complete_document, first)
    compile_document(complete_document, second)

    first_mapping = identity_map(first)
    second_mapping = identity_map(second)
    assert first_mapping == second_mapping
    assert set(first_mapping) == canonical_ids
    assert len(set(first_mapping.values())) == len(canonical_ids)
    assert all(len(global_id) == 22 for global_id in first_mapping.values())


def test_verification_failure_never_replaces_destination(
    complete_document: dict,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "verified.ifc"
    sentinel = b"known-good-existing-output"
    output.write_bytes(sentinel)
    before = set(tmp_path.iterdir())
    calls = 0

    def fail_reopened_verification(source) -> tuple[IfcValidationIssue, ...]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return ()
        return (
            IfcValidationIssue(
                code="IFC_SCHEMA_ERROR",
                entity="IfcProject",
                attribute="UnitsInContext",
                message="Injected reopened verification failure.",
            ),
        )

    monkeypatch.setattr(
        compiler_module, "verify_ifc", fail_reopened_verification
    )

    result = compile_document(complete_document, output)

    assert not result.success
    assert result.output_path is None
    assert [issue.code for issue in result.ifc_issues] == [
        "IFC_SCHEMA_ERROR"
    ]
    assert output.read_bytes() == sentinel
    assert set(tmp_path.iterdir()) == before


def test_compilation_does_not_mutate_input(
    complete_document: dict, tmp_path: Path
) -> None:
    original = copy.deepcopy(complete_document)

    compile_document(complete_document, tmp_path / "immutable.ifc")

    assert complete_document == original

