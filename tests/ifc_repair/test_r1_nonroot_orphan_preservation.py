from __future__ import annotations

from pathlib import Path
from typing import Any

import ifcopenshell
import pytest

from scripts.ifc_repair import validate_success_cases as proof_validator
from tests.ifc_repair.test_beam_application import D7N
from tests.ifc_repair.test_repair_milestone_r1_proof import _apply_property_case
from tests.ifc_repair.test_repair_milestone_r1_proof_reaudit import (
    _apply_mixed_delta,
)
from text2ifc_ifc_repair import compare as comparison


ORPHAN_POINT = (9876.5, 123.25, -4.0)


def _forward_reachable_entity_ids(model: Any) -> set[int]:
    """Independently traverse only explicit forward attributes from IfcRoot."""

    reachable: set[int] = set()
    pending = list(model.by_type("IfcRoot"))
    while pending:
        entity = pending.pop()
        step_id = int(entity.id())
        if step_id <= 0 or step_id in reachable:
            continue
        reachable.add(step_id)
        values = [entity[index] for index in range(len(entity))]
        while values:
            value = values.pop()
            if isinstance(value, (tuple, list)):
                values.extend(value)
            elif (
                hasattr(value, "id")
                and hasattr(value, "is_a")
                and int(value.id()) > 0
                and int(value.id()) not in reachable
            ):
                pending.append(value)
    return reachable


def _write_orphan_point_model(
    path: Path,
    *,
    coordinates: tuple[float, float, float] | None,
    force_step_renumber: bool = False,
) -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    if force_step_renumber:
        discarded = model.create_entity(
            "IfcCartesianPoint",
            Coordinates=(0.0, 0.0, 0.0),
        )
        model.remove(discarded)
    if coordinates is not None:
        model.create_entity("IfcCartesianPoint", Coordinates=coordinates)
    model.write(str(path))


@pytest.mark.parametrize(
    "orphan_kind",
    ("cartesian_point", "property_single_value"),
)
def test_r1_property_preservation_rejects_added_unreachable_nonroot_entity(
    tmp_path: Path,
    orphan_kind: str,
) -> None:
    source, repaired, changeset, application = _apply_property_case(
        tmp_path,
        ifc_class="IfcWindow",
        set_name="Pset_WindowCommon",
        property_name="IsExternal",
        value_type="IfcBoolean",
        value=True,
    )
    tampered = ifcopenshell.open(str(repaired))
    if orphan_kind == "cartesian_point":
        tampered.create_entity("IfcCartesianPoint", Coordinates=ORPHAN_POINT)
    else:
        tampered.create_entity(
            "IfcPropertySingleValue",
            Name="DetachedEvidence",
            Description=None,
            NominalValue=tampered.create_entity("IfcLabel", "detached"),
            Unit=None,
        )
    tampered.write(str(repaired))

    repaired_model = ifcopenshell.open(str(repaired))
    matching = (
        [
            entity
            for entity in repaired_model.by_type("IfcCartesianPoint")
            if tuple(float(value) for value in entity.Coordinates)
            == ORPHAN_POINT
        ]
        if orphan_kind == "cartesian_point"
        else [
            entity
            for entity in repaired_model.by_type("IfcPropertySingleValue")
            if str(entity.Name or "") == "DetachedEvidence"
        ]
    )
    assert len(matching) == 1
    orphan = matching[0]
    assert not orphan.is_a("IfcRoot")
    assert int(orphan.id()) not in _forward_reachable_entity_ids(repaired_model)

    with pytest.raises(
        ValueError,
        match="proof.global_preservation:nonroot_orphan_delta",
    ):
        proof_validator._audit_authorized_repair_preservation(
            damaged_ifc_path=source,
            repaired_ifc_path=repaired,
            changeset=changeset,
            application=application,
            damaged_model=ifcopenshell.open(str(source)),
            repaired_model=repaired_model,
        )


def test_unreachable_nonroot_fingerprint_is_step_id_independent_after_reopen(
    tmp_path: Path,
) -> None:
    source = tmp_path / "orphan-source.ifc"
    renumbered = tmp_path / "orphan-renumbered.ifc"
    _write_orphan_point_model(source, coordinates=ORPHAN_POINT)
    _write_orphan_point_model(
        renumbered,
        coordinates=ORPHAN_POINT,
        force_step_renumber=True,
    )
    source_model = ifcopenshell.open(str(source))
    renumbered_model = ifcopenshell.open(str(renumbered))
    assert source_model.by_type("IfcCartesianPoint")[0].id() != (
        renumbered_model.by_type("IfcCartesianPoint")[0].id()
    )

    assert comparison.unreachable_non_root_fingerprint_multiset(
        source_model
    ) == comparison.unreachable_non_root_fingerprint_multiset(renumbered_model)


@pytest.mark.parametrize(
    "repaired_coordinates",
    ((9876.5, 123.25, -3.0), None),
    ids=("modified", "deleted"),
)
def test_unreachable_nonroot_fingerprint_rejects_source_orphan_drift(
    tmp_path: Path,
    repaired_coordinates: tuple[float, float, float] | None,
) -> None:
    source = tmp_path / "orphan-source.ifc"
    repaired = tmp_path / "orphan-repaired.ifc"
    _write_orphan_point_model(source, coordinates=ORPHAN_POINT)
    _write_orphan_point_model(repaired, coordinates=repaired_coordinates)

    assert comparison.unreachable_non_root_fingerprint_multiset(
        ifcopenshell.open(str(source))
    ) != comparison.unreachable_non_root_fingerprint_multiset(
        ifcopenshell.open(str(repaired))
    )


def test_r1_property_preservation_allows_authorized_reachable_nonroot_delta(
    tmp_path: Path,
) -> None:
    source, repaired, changeset, application = _apply_property_case(
        tmp_path,
        ifc_class="IfcWindow",
        set_name="Pset_WindowCommon",
        property_name="IsExternal",
        value_type="IfcBoolean",
        value=True,
    )
    source_model = ifcopenshell.open(str(source))
    repaired_model = ifcopenshell.open(str(repaired))
    assert comparison.unreachable_non_root_fingerprint_multiset(
        source_model
    ) == comparison.unreachable_non_root_fingerprint_multiset(repaired_model)

    proof_validator._audit_authorized_repair_preservation(
        damaged_ifc_path=source,
        repaired_ifc_path=repaired,
        changeset=changeset,
        application=application,
        damaged_model=source_model,
        repaired_model=repaired_model,
    )


def test_r1_mixed_structural_preservation_allows_authorized_reachable_geometry(
    tmp_path: Path,
) -> None:
    repaired, changeset, application = _apply_mixed_delta(tmp_path)
    source_model = ifcopenshell.open(str(D7N))
    repaired_model = ifcopenshell.open(str(repaired))
    assert comparison.unreachable_non_root_fingerprint_multiset(
        source_model
    ) == comparison.unreachable_non_root_fingerprint_multiset(repaired_model)

    proof_validator._audit_authorized_repair_preservation(
        damaged_ifc_path=D7N,
        repaired_ifc_path=repaired,
        changeset=changeset,
        application=application,
        damaged_model=source_model,
        repaired_model=repaired_model,
    )
