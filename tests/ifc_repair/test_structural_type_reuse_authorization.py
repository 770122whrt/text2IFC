"""Exact existing structural Type reuse must authorize relation extension.

When an ``add_beam``/``add_column`` operation reuses an exact existing
``IfcBeamType``/``IfcColumnType``, the applicator extends the *existing*
``IfcRelDefinesByType`` and records it as a ``modified`` effect with the
``structural_type_relationship`` role. The generated-Type path instead
*creates* a new relation, which the ``created`` authorization table already
covers. The ``modified`` table must authorize the same role/class, otherwise
every exact-Type-reuse repair fails the ``l1.scope.*`` authorization gate
even though its actual IFC effect is exactly the declared one.
"""

from __future__ import annotations

import pytest

from text2ifc_ifc_repair.evaluation_policy import structural_l1_authorization


@pytest.mark.parametrize("family", ["beam", "column"])
def test_modified_authorization_covers_existing_type_relation_extension(
    family: str,
) -> None:
    authorization = structural_l1_authorization(family)

    modified = authorization["modified"]
    assert modified["structural_type_relationship"] == "IfcRelDefinesByType"
    assert modified["spatial_containment"] == (
        "IfcRelContainedInSpatialStructure"
    )


@pytest.mark.parametrize("family", ["beam", "column"])
def test_relation_authorization_allows_modified_existing_type_relation(
    family: str,
) -> None:
    authorization = structural_l1_authorization(family)

    relation = authorization["relations"]["structural_type_relationship"]
    assert relation["ifc_class"] == "IfcRelDefinesByType"
    # The relation extends RelatedObjects by exactly this operation's member;
    # the existing type itself must never count as modified.
    assert "structural_type" not in authorization["modified"]


@pytest.mark.parametrize("family", ["beam", "column"])
def test_required_type_relationship_binding_accepts_created_or_modified(
    family: str,
) -> None:
    """Exact reuse extends an existing relation; generation creates one.

    Either way the operation must bind the structural type relationship
    exactly once, and the required-role enforcement must accept both forms.
    """
    from text2ifc_ifc_repair.evaluation import _application_role_binding_errors

    authorization = structural_l1_authorization(family)

    def _errors_for(changes: dict) -> tuple[str, ...]:
        role_entries: dict[tuple[str, str], list[str]] = {}
        id_roles: dict[str, list[str]] = {}
        for change_kind in ("created", "modified", "removed"):
            for item in changes.get(change_kind, ()):
                role_entries.setdefault(
                    (change_kind, str(item["role"])), []
                ).append(str(item["global_id"]))
                id_roles.setdefault(str(item["global_id"]), []).append(
                    str(item["role"])
                )
        return _application_role_binding_errors(
            role_entries=role_entries,
            id_roles=id_roles,
            authorization=authorization,
        )

    generated_path = {
        "created": [
            {"role": family, "global_id": "0MEMBERAAAAAAAAAAAAAA1"},
            {
                "role": "structural_type",
                "global_id": "0TYPEAAAAAAAAAAAAAAAAA1",
            },
            {
                "role": "structural_type_relationship",
                "global_id": "0RELAAAAAAAAAAAAAAAAAA1",
            },
            {
                "role": "spatial_containment",
                "global_id": "0RELAAAAAAAAAAAAAAAAA2",
            },
        ],
        "modified": [],
    }
    reuse_path = {
        "created": [
            {"role": family, "global_id": "0MEMBERAAAAAAAAAAAAAA1"},
        ],
        "modified": [
            {
                "role": "structural_type_relationship",
                "global_id": "0EXISTINGRELEXISTINGRE1",
            },
            {
                "role": "spatial_containment",
                "global_id": "0RELAAAAAAAAAAAAAAAAA2",
            },
        ],
    }
    missing_relation = {
        "created": [{"role": family, "global_id": "0MEMBERAAAAAAAAAAAAAA1"}],
        "modified": [
            {
                "role": "spatial_containment",
                "global_id": "0RELAAAAAAAAAAAAAAAAA2",
            }
        ],
    }

    assert _errors_for(generated_path) == ()
    assert _errors_for(reuse_path) == ()
    errors = _errors_for(missing_relation)
    assert any(
        "structural_type_relationship" in message for message in errors
    ), errors
