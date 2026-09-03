from __future__ import annotations

import hashlib
import json
from pathlib import Path

import ifcopenshell
import pytest

from text2ifc_ifc_repair import mutation
from text2ifc_ifc_repair.compare import compare_ifc_models


ROOT = Path(__file__).resolve().parents[2]
D7N = ROOT / "dataset" / "ifc" / "test" / "d7n.ifc"
VVO = ROOT / "dataset" / "ifc" / "train" / "vvo.ifc"

CASES = (
    (
        "d7n",
        D7N,
        "1RnWak0Kr6GxkeYF4Sd_bw",
        "3dldEzenf9LvnDJYNNzLsH",
        "1EazmrnrP3p9dtRknlmbVD",
        "3dldEzenf9LvnDJYNNzLsV",
        "0K_MqVdrL0JOCMi_Gblgiw",
        "0K_MqVdrL0JOCMi_GblRwJ",
    ),
    (
        "vvo",
        VVO,
        "17tPjyQtf2L9JnbXXmcTUF",
        "1rsYNObuDC4euALdw6WUK4",
        "17tPjyQtf2L9JnbXXmcTTd",
        "1rsYNObuDC4euALdw6WUK0",
        "1vTeahUkP60PdWqwCTjUuM",
        "1vTeahUkP60PdWqwCTjeRs",
    ),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _root_ids(model: object) -> set[str]:
    return {str(item.GlobalId) for item in model.by_type("IfcRoot")}


def _optional_guid(model: object, global_id: str) -> object | None:
    try:
        return model.by_guid(global_id)
    except RuntimeError:
        return None


def _authorized_changed_roots(model: object, target_ids: tuple[str, ...]) -> set[str]:
    allowed = set(target_ids)
    for target_id in target_ids:
        target = model.by_guid(target_id)
        for relationship in model.get_inverse(target):
            if relationship.is_a("IfcRelationship"):
                allowed.add(str(relationship.GlobalId))
        for relationship in target.IsDefinedBy:
            if relationship.is_a("IfcRelDefinesByProperties"):
                definition = relationship.RelatingPropertyDefinition
                if definition.is_a("IfcRoot"):
                    allowed.add(str(definition.GlobalId))
    return allowed


@pytest.mark.parametrize(
    (
        "case_id",
        "source",
        "beam_id",
        "column_id",
        "beam_type_id",
        "column_type_id",
        "beam_storey_id",
        "column_storey_id",
    ),
    CASES,
)
def test_real_structural_damage_is_deterministic_source_bound_and_private(
    tmp_path: Path,
    case_id: str,
    source: Path,
    beam_id: str,
    column_id: str,
    beam_type_id: str,
    column_type_id: str,
    beam_storey_id: str,
    column_storey_id: str,
) -> None:
    remove = getattr(mutation, "remove_structural_members")
    source_hash = _sha256(source)
    outputs = [tmp_path / f"{case_id}-{index}" for index in (1, 2)]
    for output in outputs:
        remove(
            source_path=source,
            output_dir=output,
            beam_global_ids=(beam_id,),
            column_global_ids=(column_id,),
            expected_source_sha256=source_hash,
        )

    assert _sha256(source) == source_hash
    assert _sha256(outputs[0] / "damaged.ifc") == _sha256(
        outputs[1] / "damaged.ifc"
    )
    first_manifest = json.loads(
        (outputs[0] / "mutation_manifest.private.json").read_text(
            encoding="utf-8"
        )
    )
    second_manifest = json.loads(
        (outputs[1] / "mutation_manifest.private.json").read_text(
            encoding="utf-8"
        )
    )
    assert first_manifest == second_manifest
    assert first_manifest["source"] == {
        "path": source.resolve().as_posix(),
        "schema": "IFC2X3",
        "size_bytes": source.stat().st_size,
        "sha256": source_hash,
    }
    assert first_manifest["damaged_ifc"]["sha256"] == _sha256(
        outputs[0] / "damaged.ifc"
    )

    targets = first_manifest["targets"]
    assert [target["role"] for target in targets] == ["beam", "column"]
    assert [target["entity"]["global_id"] for target in targets] == [
        beam_id,
        column_id,
    ]
    for target in targets:
        assert isinstance(target["entity"]["step_id"], int)
        assert target["type"]["global_id"]
        assert target["storey"]["global_id"]
        assert set(target["geometry"]) == {
            "axis_capability",
            "section_capability",
            "representation_summary",
        }
        assert "property_sets" in target["semantics"]
        assert "material_associations" in target["semantics"]

    report_text = (outputs[0] / "mutation_report.json").read_text(
        encoding="utf-8"
    )
    for private_value in (beam_id, column_id, str(targets[0]["entity"]["step_id"])):
        assert private_value not in report_text

    damaged = ifcopenshell.open(str(outputs[0] / "damaged.ifc"))
    assert damaged.schema == "IFC2X3"
    assert _optional_guid(damaged, beam_id) is None
    assert _optional_guid(damaged, column_id) is None
    for surviving_id in (
        beam_type_id,
        column_type_id,
        beam_storey_id,
        column_storey_id,
    ):
        assert damaged.by_guid(surviving_id) is not None

    source_model = ifcopenshell.open(str(source))
    removed_roots = _root_ids(source_model) - _root_ids(damaged)
    allowed = _authorized_changed_roots(source_model, (beam_id, column_id))
    assert removed_roots <= allowed
    comparison = compare_ifc_models(
        source,
        outputs[0] / "damaged.ifc",
        allowed_changed_ids=allowed,
    )
    assert comparison["complete_preservation_success"] is True
    assert comparison["unexpected_changed_ids"] == []


def test_structural_mutation_rejects_wrong_source_fingerprint_before_output(
    tmp_path: Path,
) -> None:
    remove = getattr(mutation, "remove_structural_members")
    output = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="SOURCE_IFC_FINGERPRINT_MISMATCH"):
        remove(
            source_path=D7N,
            output_dir=output,
            beam_global_ids=("1RnWak0Kr6GxkeYF4Sd_bw",),
            column_global_ids=(),
            expected_source_sha256="0" * 64,
        )
    assert not output.exists()


def test_structural_mutation_rejects_empty_duplicate_and_wrong_family_targets(
    tmp_path: Path,
) -> None:
    remove = getattr(mutation, "remove_structural_members")
    with pytest.raises(ValueError, match="STRUCTURAL_MUTATION_EMPTY"):
        remove(source_path=D7N, output_dir=tmp_path / "empty")
    with pytest.raises(ValueError, match="STRUCTURAL_MUTATION_DUPLICATE_TARGET"):
        remove(
            source_path=D7N,
            output_dir=tmp_path / "duplicate",
            beam_global_ids=("1RnWak0Kr6GxkeYF4Sd_bw",) * 2,
        )
    with pytest.raises(ValueError, match="STRUCTURAL_MUTATION_TARGET_INVALID"):
        remove(
            source_path=D7N,
            output_dir=tmp_path / "wrong-family",
            beam_global_ids=("3dldEzenf9LvnDJYNNzLsH",),
        )
