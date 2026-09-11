"""Additive BIM JSON 2.1 semantic contract."""
from jsonschema import Draft202012Validator

from .schema import load_schema_v21
from .validation import _normalize_error, _sort_issues, ValidationIssue
from .validation_v2 import _semantic_issues
from .geometry_v2 import validate_geometry


def validate_v21_geometry(document):
    issues = validate_geometry(document)
    basic_paths = {f"/entities/{i}/attributes/Representation/kind" for i, e in enumerate(document["entities"]) if e["attributes"].get("Representation", {}).get("kind") == "basic_filling"}
    if basic_paths:
        from .basic_filling import validate_basic_filling, validate_basic_filling_document
        issues = [i for i in issues if not (i.code == "UNSUPPORTED_GEOMETRY_KIND" and i.path in basic_paths)]
        for index, record in enumerate(document["entities"]):
            rep = record["attributes"].get("Representation", {})
            if rep.get("kind") == "basic_filling":
                issues.extend(validate_basic_filling(rep, record["ifc_class"], f"/entities/{index}/attributes/Representation"))
        issues.extend(validate_basic_filling_document(document))
    return issues


def validate_v21_document(document):
    structural = [issue for error in Draft202012Validator(load_schema_v21()).iter_errors(document) for issue in _normalize_error(error)]
    if structural:
        return _sort_issues(structural)
    return _semantic_issues(document, extended=True)
