from __future__ import annotations

from pathlib import Path

from text2ifc_ifc_repair.index_store import SQLiteIndexRepository
from text2ifc_ifc_repair.indexer import build_ifc_index
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.repair_intent import RepairIntent
from text2ifc_ifc_repair.resolution_flow import resolve_repair_intent


ROOT = Path(__file__).resolve().parents[2]
D7N = ROOT / "dataset" / "ifc" / "test" / "d7n.ifc"


def _source() -> dict:
    return {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": "add one column on Level 1",
    }


def _intent(parameters: dict) -> RepairIntent:
    source = _source()
    registry = create_default_registry()
    return RepairIntent.from_dict(
        {
            "schema_version": "text2ifc/ifc-repair-intent/0.5",
            "request_id": "column-resolution-1",
            "source_request_hash": "sha256:" + "a" * 64,
            "model_fingerprint": "sha256:" + "b" * 64,
            "prompt_fingerprint": "sha256:" + "c" * 64,
            "operations": [
                {
                    "operation_id": "column-1",
                    "operation_type": "add_column",
                    "routing_intent": {
                        "component_family": "column",
                        "action": "add",
                        "operation_profile": "column.add",
                        "source": source,
                    },
                    "target_query": {
                        "schema_version": "text2ifc/ifc-target-query/0.1",
                        "allowed_ifc_classes": ["IfcBuildingStorey"],
                        "names": ["Level 1"],
                    },
                    "parameters": parameters,
                    "attribute_intents": [],
                    "property_intents": [],
                    "semantic_bundle_refs": [],
                    "quantity_intents": [],
                    "occurrence_reuse_intent": None,
                    "prototype_intent": None,
                    "provenance": [source],
                }
            ],
            "semantic_bundles": [],
            "provenance": [source],
        },
        registry=registry,
    )


def _axis(*, inclined: bool = False) -> dict:
    return {
        "base": {"x_mm": 100000, "y_mm": 100000, "z_mm": 0},
        "top": {
            "x_mm": 100050 if inclined else 100000,
            "y_mm": 100000,
            "z_mm": 6000,
        },
    }


def test_default_registry_resolves_square_and_oriented_column_contracts(
    tmp_path: Path,
) -> None:
    registry = create_default_registry()
    assert {"add_beam", "add_column"}.issubset(registry.operation_types)
    definition = registry.require("add_column")
    assert definition.prompt_profile_id == "column.add.v0.2"
    assert definition.target_ifc_classes == ("IfcBuildingStorey",)
    assert definition.semantic_scope_roles == {"column": "column_occurrence"}
    assert definition.generated_type_factory is not None

    database = tmp_path / "d7n.sqlite"
    metadata = build_ifc_index(D7N, database)
    with SQLiteIndexRepository.open(database) as repository:
        square_parameters = {
            "axis": _axis(),
            "section": {
                "shape": "rectangle",
                "width_mm": 500,
                "depth_mm": 500,
            },
        }
        square = resolve_repair_intent(
            _intent(square_parameters),
            repository,
            expected_source_sha256=metadata.source_ifc_sha256,
            operation_registry=registry,
        )
        assert square.status == "resolved"
        assert square.operations[0].parameters == square_parameters
        assert "orientation" not in square.operations[0].parameters["section"]

        missing_orientation = resolve_repair_intent(
            _intent(
                {
                    "axis": _axis(),
                    "section": {
                        "shape": "rectangle",
                        "width_mm": 400,
                        "depth_mm": 600,
                    },
                }
            ),
            repository,
            expected_source_sha256=metadata.source_ifc_sha256,
            operation_registry=registry,
        )
        assert missing_orientation.status == "clarification_required"
        assert (
            missing_orientation.reason_code
            == "STRUCTURAL_COLUMN_ORIENTATION_REQUIRED"
        )
        assert missing_orientation.candidates == (
            {
                "path": "/parameters/section/orientation",
                "fact": "required_for_non_square_column",
            },
        )

        oriented_parameters = {
            "axis": _axis(),
            "section": {
                "shape": "rectangle",
                "width_mm": 400,
                "depth_mm": 600,
                "orientation": {"x": 0, "y": 1},
            },
        }
        oriented = resolve_repair_intent(
            _intent(oriented_parameters),
            repository,
            expected_source_sha256=metadata.source_ifc_sha256,
            operation_registry=registry,
        )
        assert oriented.status == "resolved"
        assert oriented.operations[0].parameters == oriented_parameters
        generated = [
            item
            for item in oriented.operations[0].authorized_semantics
            if item.get("kind") == "system_generated_type"
        ]
        assert len(generated) == 1
        assert generated[0]["ifc_class"] == "IfcColumnType"


def test_column_capability_rejects_inclined_grid_analysis_and_split_requests() -> None:
    checker = create_default_registry().require("add_column").intent_capability_checker
    cases = (
        (
            {
                "axis": _axis(inclined=True),
                "section": {"shape": "rectangle", "width_mm": 500, "depth_mm": 500},
            },
            "STRUCTURAL_COLUMN_NOT_VERTICAL",
        ),
        (
            {
                "axis": {"grid": "A/1"},
                "section": {"shape": "rectangle", "width_mm": 500, "depth_mm": 500},
            },
            "STRUCTURAL_GRID_PLACEMENT_UNSUPPORTED",
        ),
        (
            {
                "axis": _axis(),
                "section": {"shape": "round", "width_mm": 500, "depth_mm": 500},
            },
            "STRUCTURAL_SECTION_UNSUPPORTED",
        ),
        (
            {
                "axis": _axis(),
                "section": {"shape": "rectangle", "width_mm": 500, "depth_mm": 500},
                "analysis_member": True,
            },
            "STRUCTURAL_ANALYSIS_UNSUPPORTED",
        ),
        (
            {
                "axis": _axis(),
                "section": {"shape": "rectangle", "width_mm": 500, "depth_mm": 500},
                "split_at_storeys": True,
            },
            "STRUCTURAL_STOREY_SPLIT_UNSUPPORTED",
        ),
    )
    for parameters, code in cases:
        assert checker(
            operation={"operation_id": "column-unsupported", "parameters": parameters}
        ) == {"status": "unsupported", "reason_code": code}
