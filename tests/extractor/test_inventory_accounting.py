from __future__ import annotations

import hashlib

from text2ifc_contract.draft import validate_draft
from text2ifc_extractor import extract_ifc2x3

from .conftest import HXP


def test_source_provenance_and_inventory_are_complete(hxp_result) -> None:
    expected_hash = hashlib.sha256(HXP.read_bytes()).hexdigest()

    assert hxp_result.source_sha256 == expected_hash
    assert hxp_result.draft is not None
    assert validate_draft(hxp_result.draft) == []
    provenance = hxp_result.draft["provenance"]
    assert provenance["source_path"] == "dataset/ifc/train/hxp.ifc"
    assert provenance["source_sha256"] == expected_hash
    assert provenance["ifc_schema"] == "IFC2X3"

    assert hxp_result.inventory
    for category in hxp_result.inventory.values():
        assert category["source"] == (
            category["represented"] + category["reported"]
        )


def test_repeated_extraction_is_canonical_and_step_id_independent() -> None:
    first = extract_ifc2x3(HXP)
    second = extract_ifc2x3(HXP)

    assert first.source_sha256
    assert first.draft == second.draft
    assert first.inventory == second.inventory
    assert "#416" not in repr(first.draft)
