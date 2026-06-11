import copy
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract" / "fixtures" / "complete.json"
CLI = ROOT / "scripts" / "bim_json" / "validate.py"
SUPPORTED_KINDS = {
    "wall",
    "column",
    "beam",
    "slab",
    "door",
    "window",
    "stair",
    "stair_flight",
    "roof",
}


def _complete_document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _contract_api():
    try:
        schema_module = importlib.import_module("text2ifc_contract.schema")
        validation_module = importlib.import_module("text2ifc_contract.validation")
    except ModuleNotFoundError as exc:
        pytest.fail(f"contract API is not implemented: {exc}")
    return schema_module.load_schema, validation_module.validate_document


def _issues(document):
    _, validate_document = _contract_api()
    return [
        {"code": issue.code, "path": issue.path, "message": issue.message}
        for issue in validate_document(document)
    ]


def _assert_issue(issues, code, path):
    assert any(
        issue["code"] == code and issue["path"] == path for issue in issues
    ), issues


def _run_cli(path):
    return subprocess.run(
        [sys.executable, str(CLI), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_complete_fixture_covers_every_supported_kind_and_validates():
    document = _complete_document()

    assert {element["kind"] for element in document["elements"]} == SUPPORTED_KINDS
    assert _issues(document) == []


@pytest.mark.parametrize(
    ("mutation", "code", "path"),
    [
        (lambda doc: doc.pop("contract_version"), "REQUIRED_FIELD", "/contract_version"),
        (
            lambda doc: doc.__setitem__("contract_version", "bim-json/2.0"),
            "INVALID_ENUM",
            "/contract_version",
        ),
        (
            lambda doc: doc.__setitem__("target_schema", "IFC4"),
            "INVALID_ENUM",
            "/target_schema",
        ),
        (
            lambda doc: doc["units"].__setitem__("length", "METRE"),
            "INVALID_ENUM",
            "/units/length",
        ),
        (
            lambda doc: doc["project"].__setitem__("name", 42),
            "INVALID_TYPE",
            "/project/name",
        ),
        (
            lambda doc: doc["project"].__setitem__("unexpected", True),
            "UNSUPPORTED_FIELD",
            "/project/unexpected",
        ),
        (
            lambda doc: doc["elements"][0].__setitem__("kind", "furniture"),
            "INVALID_ENUM",
            "/elements/0/kind",
        ),
        (
            lambda doc: doc["elements"][0]["dimensions"].__setitem__("height", 0),
            "VALUE_OUT_OF_RANGE",
            "/elements/0/dimensions/height",
        ),
    ],
)
def test_invalid_documents_return_stable_codes_and_paths(mutation, code, path):
    document = _complete_document()
    mutation(document)

    _assert_issue(_issues(document), code, path)


@pytest.mark.parametrize(
    ("path_parts", "expected_path"),
    [
        (("contract_version",), "/contract_version"),
        (("target_schema",), "/target_schema"),
        (("units",), "/units"),
        (("project",), "/project"),
        (("site",), "/site"),
        (("building",), "/building"),
        (("storeys",), "/storeys"),
        (("elements",), "/elements"),
        (("project", "id"), "/project/id"),
        (("project", "name"), "/project/name"),
        (("site", "id"), "/site/id"),
        (("site", "name"), "/site/name"),
        (("building", "id"), "/building/id"),
        (("building", "name"), "/building/name"),
        (("storeys", 0, "id"), "/storeys/0/id"),
        (("storeys", 0, "name"), "/storeys/0/name"),
        (("storeys", 0, "elevation"), "/storeys/0/elevation"),
        (("elements", 0, "id"), "/elements/0/id"),
        (("elements", 0, "kind"), "/elements/0/kind"),
        (("elements", 0, "name"), "/elements/0/name"),
        (("elements", 0, "storey_id"), "/elements/0/storey_id"),
        (("elements", 0, "dimensions"), "/elements/0/dimensions"),
    ],
)
def test_every_common_required_field_is_rejected_when_missing(
    path_parts, expected_path
):
    document = _complete_document()
    parent = document
    for part in path_parts[:-1]:
        parent = parent[part]
    parent.pop(path_parts[-1])

    _assert_issue(_issues(document), "REQUIRED_FIELD", expected_path)


@pytest.mark.parametrize(
    ("kind", "dimension"),
    [
        ("wall", "length"),
        ("wall", "height"),
        ("wall", "thickness"),
        ("column", "width"),
        ("column", "depth"),
        ("column", "height"),
        ("beam", "length"),
        ("beam", "width"),
        ("beam", "height"),
        ("slab", "length"),
        ("slab", "width"),
        ("slab", "thickness"),
        ("door", "width"),
        ("door", "height"),
        ("window", "width"),
        ("window", "height"),
        ("stair", "length"),
        ("stair", "width"),
        ("stair", "height"),
        ("stair_flight", "width"),
        ("stair_flight", "rise"),
        ("stair_flight", "run"),
        ("roof", "length"),
        ("roof", "width"),
        ("roof", "thickness"),
    ],
)
def test_every_family_dimension_is_rejected_when_missing(kind, dimension):
    document = _complete_document()
    index = next(
        index
        for index, element in enumerate(document["elements"])
        if element["kind"] == kind
    )
    document["elements"][index]["dimensions"].pop(dimension)

    _assert_issue(
        _issues(document),
        "REQUIRED_FIELD",
        f"/elements/{index}/dimensions/{dimension}",
    )


def test_optional_element_properties_may_be_omitted():
    document = _complete_document()
    for element in document["elements"]:
        element.pop("properties", None)

    assert _issues(document) == []


def test_validation_does_not_mutate_input():
    document = _complete_document()
    original = copy.deepcopy(document)

    _issues(document)

    assert document == original


def test_schema_is_valid_draft_2020_12_and_has_only_local_references():
    load_schema, _ = _contract_api()
    schema = load_schema()

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "$ref":
                    assert child.startswith("#"), child
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(schema)


def test_cli_returns_zero_and_empty_errors_for_valid_document():
    result = _run_cli(FIXTURE)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"valid": True, "errors": []}


def test_cli_returns_one_and_structured_errors_for_contract_failure(tmp_path):
    path = tmp_path / "invalid.json"
    document = _complete_document()
    document.pop("contract_version")
    path.write_text(json.dumps(document), encoding="utf-8")

    result = _run_cli(path)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["valid"] is False
    _assert_issue(payload["errors"], "REQUIRED_FIELD", "/contract_version")


def test_cli_returns_two_for_malformed_json(tmp_path):
    path = tmp_path / "malformed.json"
    path.write_text("{", encoding="utf-8")

    result = _run_cli(path)

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    _assert_issue(payload["errors"], "INVALID_JSON", "/")


def test_cli_rejects_files_larger_than_ten_mebibytes(tmp_path):
    path = tmp_path / "large.json"
    path.write_bytes(b" " * (10 * 1024 * 1024 + 1))

    result = _run_cli(path)

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    _assert_issue(payload["errors"], "FILE_TOO_LARGE", "/")


def test_cli_caps_emitted_validation_errors_at_one_thousand(tmp_path):
    path = tmp_path / "many-errors.json"
    document = _complete_document()
    document["elements"] = [{} for _ in range(1100)]
    path.write_text(json.dumps(document), encoding="utf-8")

    result = _run_cli(path)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["valid"] is False
    assert len(payload["errors"]) == 1000
