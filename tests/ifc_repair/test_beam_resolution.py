from __future__ import annotations

import hashlib
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
        "excerpt": "add one beam on Level 1",
    }


def _intent(parameters: dict, *, target: dict | None = None) -> RepairIntent:
    registry = create_default_registry()
    source = _source()
    return RepairIntent.from_dict(
        {
            "schema_version": "text2ifc/ifc-repair-intent/0.5",
            "request_id": "beam-resolution-1",
            "source_request_hash": "sha256:" + "a" * 64,
            "model_fingerprint": "sha256:" + "b" * 64,
            "prompt_fingerprint": "sha256:" + "c" * 64,
            "operations": [
                {
                    "operation_id": "beam-1",
                    "operation_type": "add_beam",
                    "routing_intent": {
                        "component_family": "beam",
                        "action": "add",
                        "operation_profile": "beam.add",
                        "source": source,
                    },
                    "target_query": {
                        "schema_version": "text2ifc/ifc-target-query/0.1",
                        "allowed_ifc_classes": ["IfcBuildingStorey"],
                        **(target or {"names": ["Level 1"]}),
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


def _explicit_parameters() -> dict:
    return {
        "axis": {
            "start": {"x_mm": 100000, "y_mm": 100000, "z_mm": 3000},
            "end": {"x_mm": 103000, "y_mm": 104000, "z_mm": 3000},
        },
        "section": {"shape": "rectangle", "width_mm": 300, "height_mm": 500},
    }


def test_default_registry_resolves_explicit_and_exact_reference_beams_without_common_branches(
    tmp_path: Path,
) -> None:
    registry = create_default_registry()
    assert {"add_beam", "add_column"}.issubset(registry.operation_types)
    definition = registry.require("add_beam")
    assert definition.prompt_profile_id == "beam.add.v0.2"
    assert definition.target_ifc_classes == ("IfcBuildingStorey",)
    assert definition.semantic_scope_roles == {"beam": "beam_occurrence"}
    assert definition.generated_type_factory is not None

    database = tmp_path / "d7n.sqlite"
    metadata = build_ifc_index(D7N, database)
    expected_sha = metadata.source_ifc_sha256
    with SQLiteIndexRepository.open(database) as repository:
        explicit = resolve_repair_intent(
            _intent(_explicit_parameters()),
            repository,
            expected_source_sha256=expected_sha,
            operation_registry=registry,
        )
        assert explicit.status == "resolved"
        resolved = explicit.operations[0]
        assert resolved.parameters == _explicit_parameters()
        assert resolved.target_global_id
        assert repository.get_by_global_id(resolved.target_global_id).ifc_class == (
            "IfcBuildingStorey"
        )
        generated = [
            item
            for item in resolved.authorized_semantics
            if item.get("kind") == "system_generated_type"
        ]
        assert len(generated) == 1
        assert generated[0]["ifc_class"] == "IfcBeamType"

        reference = next(
            record
            for record in repository.iter_records()
            if record.ifc_class == "IfcBeam"
            and record.geometry_summary["axis_capability"]["status"]
            == "measured_current_ifc"
        )
        exact_reference = resolve_repair_intent(
            _intent(
                {
                    "axis": {
                        "reference": {
                            "schema_version": "text2ifc/ifc-target-query/0.1",
                            "allowed_ifc_classes": ["IfcBeam"],
                            "global_id": reference.ifc_global_id,
                        }
                    },
                    "section": {
                        "shape": "rectangle",
                        "width_mm": 300,
                        "height_mm": 500,
                    },
                },
                target={"global_id": reference.storey_global_id},
            ),
            repository,
            expected_source_sha256=expected_sha,
            operation_registry=registry,
        )
        assert exact_reference.status == "resolved"
        axis = exact_reference.operations[0].parameters["axis"]
        capability = reference.geometry_summary["axis_capability"]
        assert axis["start"] == {
            key: value
            for key, value in zip(
                ("x_mm", "y_mm", "z_mm"),
                capability["storey_local_start_mm"],
                strict=True,
            )
        }
        assert axis["end"] == {
            key: value
            for key, value in zip(
                ("x_mm", "y_mm", "z_mm"),
                capability["storey_local_end_mm"],
                strict=True,
            )
        }

        ambiguous = resolve_repair_intent(
            _intent(
                {
                    "axis": {
                        "reference": {
                            "schema_version": "text2ifc/ifc-target-query/0.1",
                            "allowed_ifc_classes": ["IfcBeam"],
                            "names": ["100x400 2"],
                            "storey_global_id": reference.storey_global_id,
                        }
                    },
                    "section": {
                        "shape": "rectangle",
                        "width_mm": 300,
                        "height_mm": 500,
                    },
                },
                target={"global_id": reference.storey_global_id},
            ),
            repository,
            expected_source_sha256=expected_sha,
            operation_registry=registry,
        )
        assert ambiguous.status == "clarification_required"
        assert ambiguous.reason_code == "STRUCTURAL_AXIS_REFERENCE_AMBIGUOUS"
        assert len(ambiguous.candidates) > 1


def test_beam_missing_and_unsupported_facts_are_grouped_before_resolution() -> None:
    definition = create_default_registry().require("add_beam")
    target_record = type(
        "Record",
        (),
        {
            "ifc_class": "IfcBuildingStorey",
            "ifc_global_id": "0STOREYAAAAAAAAAAAAAAA",
        },
    )()
    missing = definition.parameter_resolver(
        operation={
            "operation_id": "beam-missing",
            "parameters": {
                "axis": {},
                "section": {"shape": "rectangle", "width_mm": 300, "height_mm": 500},
            },
        },
        target_record=target_record,
        repository=None,
        context={},
    )
    assert missing["status"] == "clarification_required"
    assert missing["reason_code"] == "STRUCTURAL_FACTS_REQUIRED"
    assert {item["path"] for item in missing["candidates"]} == {
        "/parameters/axis/start",
        "/parameters/axis/end",
    }

    unsupported = (
        (
            {**_explicit_parameters(), "axis": {"start": {"x_mm": 0, "y_mm": 0, "z_mm": 0}, "end": {"x_mm": 3000, "y_mm": 0, "z_mm": 50}}},
            "STRUCTURAL_BEAM_NOT_HORIZONTAL",
        ),
        (
            {"axis": {"grid": "A/1"}, "section": _explicit_parameters()["section"]},
            "STRUCTURAL_GRID_PLACEMENT_UNSUPPORTED",
        ),
        (
            {"axis": _explicit_parameters()["axis"], "section": {"shape": "I", "width_mm": 300, "height_mm": 500}},
            "STRUCTURAL_SECTION_UNSUPPORTED",
        ),
        (
            {**_explicit_parameters(), "length_mm": 5000},
            "STRUCTURAL_SCALAR_EXTENT_UNSUPPORTED",
        ),
        (
            {**_explicit_parameters(), "analysis_member": True},
            "STRUCTURAL_ANALYSIS_UNSUPPORTED",
        ),
    )
    for parameters, code in unsupported:
        decision = definition.intent_capability_checker(
            operation={"operation_id": "beam-unsupported", "parameters": parameters}
        )
        assert decision == {"status": "unsupported", "reason_code": code}

    apply_source = (ROOT / "src" / "text2ifc_ifc_repair" / "apply.py").read_text(
        encoding="utf-8"
    )
    provider_source = (
        ROOT / "src" / "text2ifc_ifc_repair" / "provider_stage.py"
    ).read_text(encoding="utf-8")
    assert "add_beam" not in apply_source
    assert "add_beam" not in provider_source
    assert "IfcBeam" not in apply_source
