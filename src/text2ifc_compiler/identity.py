from typing import Any
from uuid import UUID, uuid5

import ifcopenshell.guid
from ifcopenshell.api.pset.add_pset import add_pset
from ifcopenshell.api.pset.edit_pset import edit_pset


TEXT2IFC_IDENTITY_NAMESPACE = UUID("2ec49c5a-2761-5a6f-80d9-5626a53f3b0b")
IDENTITY_PSET = "Pset_text2IFCIdentity"
IDENTITY_PROPERTY = "BimJsonId"


def global_id_for(
    contract_version: str, object_kind: str, bim_json_id: str
) -> str:
    identity = f"{contract_version}\x1f{object_kind}\x1f{bim_json_id}"
    return ifcopenshell.guid.compress(str(uuid5(
        TEXT2IFC_IDENTITY_NAMESPACE, identity
    )))


def assign_identity(
    ifc_file: Any,
    entity: Any,
    *,
    contract_version: str,
    object_kind: str,
    bim_json_id: str,
) -> None:
    entity.GlobalId = global_id_for(
        contract_version, object_kind, bim_json_id
    )
    pset = add_pset(
        ifc_file, product=entity, name=IDENTITY_PSET
    )
    edit_pset(
        ifc_file,
        pset=pset,
        properties={IDENTITY_PROPERTY: bim_json_id},
    )

