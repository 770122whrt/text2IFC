from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from text2ifc_jsonfix.composer import compose_patches


ROOT = Path(__file__).resolve().parents[2]
BASE_FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def _api():
    try:
        module = importlib.import_module("text2ifc_jsonfix.provenance")
    except ModuleNotFoundError as exc:
        pytest.fail(f"patch provenance report is not implemented: {exc}")
    return module.build_provenance_report


@pytest.fixture
def base_document() -> dict:
    document = json.loads(BASE_FIXTURE.read_text(encoding="utf-8"))
    document["provenance"]["document_id"] = "provenance-base"
    return document


def _patch() -> dict:
    return {
        "patch_version": "bim-json-patch/1.0",
        "target_schema_version": "bim-json/2.0",
        "target_ifc_schema": "IFC2X3",
        "target_document_id": "provenance-base",
        "layers": [
            {
                "id": "agent-repair-1",
                "kind": "agent",
                "provenance": {
                    "source": "agent-provider",
                    "prompt_version": "patch-v1",
                },
                "operations": [
                    {
                        "op": "add_entity",
                        "target": {
                            "collection": "entities",
                            "id": "wall-west",
                        },
                        "value": {
                            "id": "wall-west",
                            "ifc_class": "IfcWall",
                            "attributes": {
                                "Name": "West wall",
                                "ObjectPlacement": {
                                    "relative_to": "storey-1",
                                    "origin": [0, 3000, 0],
                                    "axis": [0, 0, 1],
                                    "ref_direction": [0, 1, 0],
                                },
                                "Representation": {
                                    "kind": "extruded_profile",
                                    "profile": {
                                        "kind": "rectangle",
                                        "x": 4000,
                                        "y": 200,
                                    },
                                    "depth": 2800,
                                    "direction": [0, 0, 1],
                                },
                            },
                            "property_sets": {},
                            "provenance": {
                                "source": "agent-patch",
                                "layer_id": "agent-repair-1",
                            },
                        },
                    },
                    {
                        "op": "set_property",
                        "target": {
                            "collection": "entities",
                            "id": "wall-1",
                            "property_set": "Pset_WallCommon",
                            "property": "FireRating",
                        },
                        "value": "R30",
                    },
                    {
                        "op": "mark_missing",
                        "target": {
                            "collection": "entities",
                            "id": "wall-west",
                            "path": "attributes.Description",
                        },
                        "value": {
                            "reason": "The user did not provide a description."
                        },
                    },
                ],
            },
            {
                "id": "validator-loss-1",
                "kind": "validator",
                "provenance": {"source": "formal-validator"},
                "operations": [
                    {
                        "op": "mark_unsupported_loss",
                        "target": {
                            "collection": "entities",
                            "id": "wall-west",
                            "path": "attributes.SourceBrep",
                        },
                        "value": {
                            "source_ifc_class": "IfcFacetedBrep",
                            "substitution": "none",
                        },
                    }
                ],
            },
        ],
    }


def _facts(report: dict, *, origin: str, category: str) -> list[dict]:
    return [
        fact
        for fact in report["facts"]
        if fact["origin"] == origin and fact["category"] == category
    ]


def test_report_distinguishes_base_and_patch_fact_categories(
    base_document: dict,
) -> None:
    build_provenance_report = _api()
    result = compose_patches(base_document, [_patch()])
    assert result.valid

    report = build_provenance_report(base_document, result)

    assert report["schema_version"] == "text2ifc/jsonfix-provenance-v1"
    assert report["target_document_id"] == "provenance-base"
    assert _facts(report, origin="base", category="entity")
    assert _facts(report, origin="base", category="property")
    assert _facts(report, origin="base", category="relationship")
    assert _facts(report, origin="patch", category="entity")
    assert _facts(report, origin="patch", category="property")
    assert _facts(report, origin="patch", category="missing")
    assert _facts(report, origin="patch", category="loss")


def test_patch_facts_keep_layer_kind_and_provenance(
    base_document: dict,
) -> None:
    build_provenance_report = _api()
    result = compose_patches(base_document, [_patch()])

    report = build_provenance_report(base_document, result)
    patch_facts = [
        fact for fact in report["facts"] if fact["origin"] == "patch"
    ]

    agent_facts = [
        fact for fact in patch_facts if fact["layer_id"] == "agent-repair-1"
    ]
    validator_facts = [
        fact for fact in patch_facts if fact["layer_id"] == "validator-loss-1"
    ]
    assert agent_facts
    assert all(fact["layer_kind"] == "agent" for fact in agent_facts)
    assert all(
        fact["layer_provenance"]["prompt_version"] == "patch-v1"
        for fact in agent_facts
    )
    assert len(validator_facts) == 1
    assert validator_facts[0]["layer_kind"] == "validator"
    assert validator_facts[0]["category"] == "loss"


def test_provenance_report_is_deterministic_and_counted(
    base_document: dict,
) -> None:
    build_provenance_report = _api()
    result = compose_patches(base_document, [_patch()])

    first = build_provenance_report(base_document, result)
    second = build_provenance_report(base_document, result)

    assert first == second
    assert first["summary"]["total_fact_count"] == len(first["facts"])
    assert first["summary"]["patch_fact_count"] == 4
    assert first["facts"] == sorted(
        first["facts"],
        key=lambda fact: (
            fact["origin"],
            fact["category"],
            fact["path"],
            fact.get("layer_id") or "",
        ),
    )
