import hashlib
import json
from pathlib import Path

import pytest
import ifcopenshell

from text2ifc_ifc_repair.context import build_repair_context, validate_repair_context
from text2ifc_ifc_repair.mutation import remove_window_and_opening
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.projection import project_public_repair_spec


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


def test_context_is_budgeted_and_retains_the_true_wall_candidate(
    tmp_path: Path,
) -> None:
    case_dir = tmp_path / "case"
    remove_window_and_opening(
        source_path=SOURCE,
        output_dir=case_dir,
        wall_global_id="1F6umJ5H50aeL3A1As_wTm",
        opening_global_id="2cXV28XOjE6f6irhW0CO4t",
        window_global_id="2cXV28XOjE6f6irgi0CO4t",
    )
    private_manifest = json.loads(
        (case_dir / "mutation_manifest.private.json").read_text(encoding="utf-8")
    )
    public_spec = project_public_repair_spec(
        private_manifest,
        request_id="large-building-window-repair-001",
    )

    context = build_repair_context(
        case_dir / "damaged.ifc",
        public_spec,
        registry=create_default_registry(),
        max_candidates=8,
        max_bytes=12_000,
    )

    damaged_hash = hashlib.sha256((case_dir / "damaged.ifc").read_bytes()).hexdigest()
    assert context["schema_version"] == "text2ifc/ifc-repair-context/0.1"
    assert context["base_model_fingerprint"] == f"sha256:{damaged_hash}"
    assert context["request_operation_hints"] == [
        "add_window_with_opening_to_wall"
    ]
    assert validate_repair_context(context) == []
    assert set(context) == {
        "schema_version",
        "base_model_fingerprint",
        "request_operation_hints",
        "candidate_targets",
        "model_constraints",
        "context_budget",
    }
    assert len(context["candidate_targets"]) <= 8

    target = context["candidate_targets"][0]
    assert target["target_id"] == "ifc:1F6umJ5H50aeL3A1As_wTm"
    assert target["ifc_global_id"] == "1F6umJ5H50aeL3A1As_wTm"
    assert target["ifc_class"] == "IfcWallStandardCase"
    assert target["name"] == "Basic Wall:Outside wall:346660"
    assert target["storey"] == "Level 1"
    assert target["geometry_capability"] == "straight_wall"
    assert target["details"]["dimensions_mm"] == {
        "length": pytest.approx(8200.0),
        "thickness": pytest.approx(200.0),
        "height": pytest.approx(3850.0),
    }
    assert target["details"]["existing_openings"] == [
        {
            "center_offset_mm": pytest.approx(4857.5),
            "interval_mm": [pytest.approx(4400.0), pytest.approx(5315.0)],
            "sill_height_mm": pytest.approx(305.0),
            "width_mm": pytest.approx(915.0),
            "height_mm": pytest.approx(1830.0),
        }
    ]

    budget = context["context_budget"]
    assert budget["actual_bytes"] <= budget["max_bytes"] == 12_000
    assert budget["selected_candidate_count"] == len(context["candidate_targets"])
    assert budget["omitted_candidate_count"] >= 0
    assert budget["estimated_tokens"] == (budget["actual_bytes"] + 3) // 4

    serialized = json.dumps(context, ensure_ascii=False, sort_keys=True)
    assert "2cXV28XOjE6f6irhW0CO4t" not in serialized
    assert "2cXV28XOjE6f6irgi0CO4t" not in serialized


def test_context_rejects_duplicate_storey_class_and_name_matches(
    tmp_path: Path,
) -> None:
    case_dir = tmp_path / "case"
    remove_window_and_opening(
        source_path=SOURCE,
        output_dir=case_dir,
        wall_global_id="1F6umJ5H50aeL3A1As_wTm",
        opening_global_id="2cXV28XOjE6f6irhW0CO4t",
        window_global_id="2cXV28XOjE6f6irgi0CO4t",
    )
    private_manifest = json.loads(
        (case_dir / "mutation_manifest.private.json").read_text(encoding="utf-8")
    )
    public_spec = project_public_repair_spec(
        private_manifest,
        request_id="large-building-window-repair-ambiguous",
    )
    model = ifcopenshell.open(str(case_dir / "damaged.ifc"))
    target_name = public_spec["target"]["description"]
    target_id = private_manifest["target"]["wall"]["global_id"]
    renamed = 0
    for wall in model.by_type("IfcWall"):
        if str(wall.GlobalId) == target_id:
            continue
        storeys = [
            relation.RelatingStructure
            for relation in wall.ContainedInStructure
            if relation.RelatingStructure.is_a("IfcBuildingStorey")
        ]
        if len(storeys) == 1 and str(storeys[0].Name or "") == "Level 1":
            wall.Name = target_name
            renamed += 1
            if renamed == 3:
                break
    assert renamed == 3
    ambiguous_path = case_dir / "ambiguous.ifc"
    model.write(str(ambiguous_path))

    with pytest.raises(ValueError, match="CONTEXT_TARGET_AMBIGUOUS"):
        build_repair_context(
            ambiguous_path,
            public_spec,
            registry=create_default_registry(),
        )
