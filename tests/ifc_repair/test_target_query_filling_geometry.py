"""Opening-dimension constraints must match opening-filling targets.

A natural-language request may describe a Window or Door by the dimensions of
the opening it fills. The index stores such fillings with
``dimensions_mm.overall_width`` / ``overall_height``, while hosted openings
store ``dimensions_mm.width`` / ``height`` / ``depth``. The opening dimension
constraints must read both shapes so a filling selected by its opening size is
offered as a public candidate instead of failing as ``not_found``.
"""

from __future__ import annotations

from pathlib import Path

from text2ifc_ifc_repair.index_models import (
    AliasFact,
    ElementRecord,
    IndexMetadata,
)
from text2ifc_ifc_repair.index_store import SQLiteIndexRepository
from text2ifc_ifc_repair.target_query import TargetQuery, resolve_target


def _filling_record(guid: str, name: str, tag: str, **changes: object) -> ElementRecord:
    values = dict(
        record_id=f"ifc:{guid}",
        ifc_global_id=guid,
        identity_reliable=True,
        ifc_class="IfcWindow",
        name=name,
        long_name=None,
        tag=tag,
        object_type="819mm x 759mm",
        type_name="819mm x 759mm",
        type_global_id=None,
        storey_name="Level 2",
        storey_global_id="0STOREYAAAAAAAAAAAAAAA",
        geometry_capability="opening_filling",
        geometry_summary={
            "dimensions_mm": {
                "overall_width": 819.0,
                "overall_height": 759.0,
            }
        },
        facets={"editable_target": True, "opening_global_ids": ["0OPENINGAAAAAAAAAAAAA1"]},
        provenance={"source": "fixture"},
        aliases=(AliasFact(name.casefold(), name, "name", "IfcRoot.Name"),),
        relationships=(),
        properties=(),
    )
    values.update(changes)
    return ElementRecord(**values)


def _repository(tmp_path: Path, records: list[ElementRecord]) -> Path:
    database = tmp_path / "targets.sqlite"
    metadata = IndexMetadata(
        "sha256:" + "1" * 64, "IFC2X3", "fixture", 1, "2026-07-19T00:00:00Z"
    )
    with SQLiteIndexRepository.create(database, metadata) as repository:
        for record in records:
            repository.put_record(record)
        repository.publish()
    return database


def test_opening_dimension_constraints_match_filling_targets(tmp_path: Path) -> None:
    """A Window described by its opening size is offered, not ``not_found``."""
    target = _filling_record("0AAAAAAAAAAAAAAAAAAAAA", "window 819x759", "149537")
    same_size_peer = _filling_record(
        "0BBBBBBBBBBBBBBBBBBBBB", "window same size", "147994"
    )
    other_storey = _filling_record(
        "0CCCCCCCCCCCCCCCCCCCCC",
        "window elsewhere",
        "147995",
        storey_name="Level 3",
    )
    database = _repository(tmp_path, [target, same_size_peer, other_storey])
    query = TargetQuery.from_dict(
        {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcWindow"],
            "storey_name": "Level 2",
            "geometry_constraints": [
                {"field": "opening_width_mm", "value": 819.0, "tolerance_mm": 1.0},
                {"field": "opening_height_mm", "value": 759.0, "tolerance_mm": 1.0},
            ],
        }
    )
    with SQLiteIndexRepository.open(database) as repository:
        result = resolve_target(repository, query)

    assert result.status == "ambiguous"
    offered = sorted(hit.ifc_global_id for hit in result.candidates)
    assert offered == sorted([target.ifc_global_id, same_size_peer.ifc_global_id])


def test_opening_dimension_constraints_match_exact_filling_dimensions(
    tmp_path: Path,
) -> None:
    """A zero-tolerance request matches filling dimensions without float noise.

    IFC OverallWidth/Height are metre floats multiplied by a unit scale; the
    stored millimetre value must be free of tessellation/unit noise so a
    user's exact millimetre statement matches at ``tolerance_mm=0``.
    """
    target = _filling_record("0AAAAAAAAAAAAAAAAAAAAA", "window 819x759", "149537")
    database = _repository(tmp_path, [target])
    query = TargetQuery.from_dict(
        {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcWindow"],
            "storey_name": "Level 2",
            "geometry_constraints": [
                {"field": "opening_width_mm", "value": 819, "tolerance_mm": 0},
                {"field": "opening_height_mm", "value": 759, "tolerance_mm": 0},
            ],
        }
    )
    with SQLiteIndexRepository.open(database) as repository:
        result = resolve_target(repository, query)

    assert result.status == "resolved"
    assert result.resolved_target_id == target.record_id


def test_opening_dimension_constraints_still_match_hosted_openings(
    tmp_path: Path,
) -> None:
    """The existing hosted-opening ``width``/``height`` shape keeps working."""
    target = _filling_record(
        "0AAAAAAAAAAAAAAAAAAAAA",
        "opening 800x2480",
        "100001",
        ifc_class="IfcOpeningElement",
        geometry_capability="measured_hosted_opening",
        geometry_summary={
            "dimensions_mm": {"width": 800.0, "height": 2480.0, "depth": 160.0}
        },
    )
    database = _repository(tmp_path, [target])
    query = TargetQuery.from_dict(
        {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcOpeningElement"],
            "geometry_constraints": [
                {"field": "opening_width_mm", "value": 800.0, "tolerance_mm": 1.0},
                {"field": "opening_height_mm", "value": 2480.0, "tolerance_mm": 1.0},
                {"field": "opening_depth_mm", "value": 160.0, "tolerance_mm": 1.0},
            ],
        }
    )
    with SQLiteIndexRepository.open(database) as repository:
        result = resolve_target(repository, query)

    assert result.status == "resolved"
    assert result.resolved_target_id == target.record_id


def test_filling_with_mismatched_dimensions_is_not_offered(tmp_path: Path) -> None:
    """The fix must not loosen the constraint: wrong sizes still exclude."""
    wrong_size = _filling_record(
        "0BBBBBBBBBBBBBBBBBBBBB",
        "window 750x2200",
        "147051",
        geometry_summary={
            "dimensions_mm": {
                "overall_width": 750.0,
                "overall_height": 2200.0,
            }
        },
    )
    database = _repository(tmp_path, [wrong_size])
    query = TargetQuery.from_dict(
        {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcWindow"],
            "storey_name": "Level 2",
            "geometry_constraints": [
                {"field": "opening_width_mm", "value": 819.0, "tolerance_mm": 1.0},
                {"field": "opening_height_mm", "value": 759.0, "tolerance_mm": 1.0},
            ],
        }
    )
    with SQLiteIndexRepository.open(database) as repository:
        result = resolve_target(repository, query)

    assert result.status == "not_found"
    assert result.candidates == ()


def test_overall_dimension_mismatch_excludes_filling(tmp_path: Path) -> None:
    """A filling whose overall width misses the tolerance stays excluded."""
    near_width = _filling_record(
        "0CCCCCCCCCCCCCCCCCCCCC",
        "window 829x759",
        "149999",
        geometry_summary={
            "dimensions_mm": {
                "overall_width": 829.0,
                "overall_height": 759.0,
            }
        },
    )
    database = _repository(tmp_path, [near_width])
    query = TargetQuery.from_dict(
        {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcWindow"],
            "storey_name": "Level 2",
            "geometry_constraints": [
                {"field": "opening_width_mm", "value": 819.0, "tolerance_mm": 1.0},
                {"field": "opening_height_mm", "value": 759.0, "tolerance_mm": 1.0},
            ],
        }
    )
    with SQLiteIndexRepository.open(database) as repository:
        result = resolve_target(repository, query)

    assert result.status == "not_found"
    assert result.candidates == ()
