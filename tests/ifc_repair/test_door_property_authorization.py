"""Door semantic authoring effects must be authorized exactly by L1."""

from __future__ import annotations

from text2ifc_ifc_repair.evaluation_policy import structural_l1_authorization
from text2ifc_ifc_repair.operations.door import _l1_authorization


SEMANTIC_SUFFIXES = (
    "pset",
    "pset_relationship",
    "quantities",
    "quantity_relationship",
    "material_relationship",
    "classification_relationship",
)


def test_door_authorization_covers_all_door_semantic_roles() -> None:
    for creates_opening in (True, False):
        created = _l1_authorization(creates_opening=creates_opening)["created"]
        for suffix in SEMANTIC_SUFFIXES:
            assert f"semantic_door_{suffix}" in created


def test_door_authorization_covers_opening_scoped_quantities() -> None:
    created = _l1_authorization(creates_opening=True)["created"]
    assert created["semantic_opening_quantities"] == "IfcElementQuantity"
    assert created["semantic_opening_quantity_relationship"] == (
        "IfcRelDefinesByProperties"
    )


def test_door_authorization_covers_indexed_multi_pset_variants() -> None:
    created = _l1_authorization(creates_opening=True)["created"]
    for index in (2, 17, 64):
        assert created[f"semantic_door_pset_{index}"] == "IfcPropertySet"
        assert created[f"semantic_door_pset_relationship_{index}"] == (
            "IfcRelDefinesByProperties"
        )
        assert created[f"semantic_door_material_relationship_{index}"] == (
            "IfcRelAssociatesMaterial"
        )
    assert "semantic_door_pset_65" not in created


def test_door_relation_authorizations_declare_door_endpoints() -> None:
    relations = _l1_authorization(creates_opening=True)["relations"]
    for suffix in (
        "pset_relationship",
        "quantity_relationship",
        "material_relationship",
        "classification_relationship",
    ):
        assert relations[f"semantic_door_{suffix}"][
            "added_endpoint_roles"
        ] == ("door",)


def test_door_role_set_mirrors_structural_pattern() -> None:
    structural = structural_l1_authorization("beam")["created"]
    door = _l1_authorization(creates_opening=True)["created"]
    for role, ifc_class in structural.items():
        if role.startswith("semantic_beam_"):
            door_role = role.replace("semantic_beam_", "semantic_door_", 1)
            assert door.get(door_role) == ifc_class
    for role in door:
        if role.startswith("semantic_door_"):
            beam_role = role.replace("semantic_door_", "semantic_beam_", 1)
            assert beam_role in structural


def test_fabricated_role_stays_unauthorized() -> None:
    created = _l1_authorization(creates_opening=True)["created"]
    assert "semantic_door_totally_fabricated" not in created
    assert created["semantic_door_pset"] == "IfcPropertySet"
    assert created["semantic_door_pset"] != "IfcElementQuantity"


def test_fill_door_authorization_also_carries_semantic_roles() -> None:
    created = _l1_authorization(creates_opening=False)["created"]
    assert "opening" not in created
    assert "voids_relationship" not in created
    for suffix in SEMANTIC_SUFFIXES:
        assert f"semantic_door_{suffix}" in created
