"""Failure-family regression tests for the door semantic-role authorization defect.

Defect (frozen after diagnosis, fix applied same day): the door operation's
L1 authorization map (``operations/door.py::_l1_authorization``) authorized
only door/fills/type/opening/voids roles, while its own semantic authoring —
declared through ``semantic_scope_roles = {"door": "door_occurrence",
"opening": "opening_occurrence"}`` and the generic scope rewriting in
``semantic_authoring.py::_scoped_semantic_role`` — authors family-scoped
effects with ``semantic_door_*`` roles whenever the door operation carries a
property intent.  The whole-model L1 scope check then rejected the created
``IfcPropertySet``/``IfcRelDefinesByProperties`` ("Registry policy does not
authorize this role/class/effect") and the run ended ``not_publishable``.

Violated invariant: an operation's L1 authorization must cover the full
effect space its own semantic authoring can produce.  Beam/column satisfy it
(``structural_l1_authorization`` authorizes ``semantic_{family}_*``), window
satisfies it (``semantic_pset`` + ``semantic_opening_quantities``); the door
map now mirrors the same pattern.

Family coverage:

* positive — the mechanism assertion: every semantic role the door authoring
  can emit is authorized, for both add (creates opening) and fill variants;
* boundary — indexed multi-pset variants (2..64) like the siblings;
* negative — authorization stays exact: a fabricated role or a wrong class
  for an authorized role must remain unauthorized (the fix adds roles, it
  must not weaken the exact role/class contract);
* consistency — the door role set equals the structural pattern modulo
  family prefix, preventing the next family drift.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_ifc_repair.evaluation_policy import (  # noqa: E402
    structural_l1_authorization,
)
from text2ifc_ifc_repair.operations.door import _l1_authorization  # noqa: E402


SEMANTIC_SUFFIXES = (
    "pset",
    "pset_relationship",
    "quantities",
    "quantity_relationship",
    "material_relationship",
    "classification_relationship",
)


def test_door_authorization_covers_all_door_semantic_roles() -> None:
    """The mechanism assertion: every authorable semantic role is authorized."""

    for creates_opening in (True, False):
        created = _l1_authorization(creates_opening=creates_opening)["created"]
        for suffix in SEMANTIC_SUFFIXES:
            role = f"semantic_door_{suffix}"
            assert role in created, (creates_opening, role)


def test_door_authorization_covers_opening_scoped_quantities() -> None:
    """The add path creates an opening; opening-scoped quantities must be
    authorized exactly like the window operation authorizes them."""

    created = _l1_authorization(creates_opening=True)["created"]
    assert created["semantic_opening_quantities"] == "IfcElementQuantity"
    assert (
        created["semantic_opening_quantity_relationship"]
        == "IfcRelDefinesByProperties"
    )


def test_door_authorization_covers_indexed_multi_pset_variants() -> None:
    """Multiple psets per door (property + quantity intents) stay authorized."""

    created = _l1_authorization(creates_opening=True)["created"]
    for index in (2, 17, 64):
        assert created[f"semantic_door_pset_{index}"] == "IfcPropertySet"
        assert (
            created[f"semantic_door_pset_relationship_{index}"]
            == "IfcRelDefinesByProperties"
        )
        assert (
            created[f"semantic_door_material_relationship_{index}"]
            == "IfcRelAssociatesMaterial"
        )
    assert "semantic_door_pset_65" not in created


def test_door_relation_authorizations_declare_door_endpoints() -> None:
    """Relationship roles must authorize their door endpoint like structural."""

    relations = _l1_authorization(creates_opening=True)["relations"]
    for suffix in (
        "pset_relationship",
        "quantity_relationship",
        "material_relationship",
        "classification_relationship",
    ):
        relation = relations[f"semantic_door_{suffix}"]
        assert relation["added_endpoint_roles"] == ("door",), relation


def test_door_role_set_mirrors_structural_pattern() -> None:
    """Family-drift guard: door authorizes the same effect space as beam/column."""

    structural = structural_l1_authorization("beam")["created"]
    door = _l1_authorization(creates_opening=True)["created"]
    for role, ifc_class in structural.items():
        if role.startswith("semantic_beam_"):
            door_role = role.replace("semantic_beam_", "semantic_door_", 1)
            assert door.get(door_role) == ifc_class, door_role
        elif role in {"beam", "structural_type", "structural_type_relationship",
                      "spatial_containment"}:
            continue  # family-specific occurrence/type roles
    # and the reverse: every semantic_door_ role exists in the structural map
    for role in door:
        if role.startswith("semantic_door_"):
            beam_role = role.replace("semantic_door_", "semantic_beam_", 1)
            assert beam_role in structural, role


def test_fabricated_role_stays_unauthorized() -> None:
    """The fix adds roles; it must not weaken the exact role/class contract."""

    created = _l1_authorization(creates_opening=True)["created"]
    assert "semantic_door_totally_fabricated" not in created
    assert created["semantic_door_pset"] == "IfcPropertySet"
    assert created["semantic_door_pset"] != "IfcElementQuantity"


def test_fill_door_authorization_also_carries_semantic_roles() -> None:
    """Fill-door property intents must authorize the same way as add-door."""

    created = _l1_authorization(creates_opening=False)["created"]
    assert "opening" not in created
    assert "voids_relationship" not in created
    for suffix in SEMANTIC_SUFFIXES:
        assert f"semantic_door_{suffix}" in created
