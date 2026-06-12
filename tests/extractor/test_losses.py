from __future__ import annotations


def _kinds(result):
    return {item["kind"] for item in result.losses}


def test_unsupported_source_constructs_are_explicit_losses(
    hxp_result, i5n_result, vt2_result
) -> None:
    assert "MAPPED_GEOMETRY" in _kinds(hxp_result)
    assert "BOOLEAN_GEOMETRY" in _kinds(i5n_result)
    assert "FACETED_BREP_GEOMETRY" in _kinds(vt2_result)

    assert "MATERIAL_ASSOCIATION" in _kinds(hxp_result)
    assert "TYPE_RELATIONSHIP" in _kinds(hxp_result)
    assert "CONNECTION_RELATIONSHIP" in _kinds(hxp_result)


def test_unsupported_required_geometry_forces_draft_without_box_substitution(
    hxp_result,
) -> None:
    assert hxp_result.document is None
    assert hxp_result.draft is not None
    partial = hxp_result.draft["partial_document"]
    door = next(
        item
        for item in partial["entities"]
        if item.get("global_id") == "37teTCsZT7Qe4JdVA1Otbq"
    )
    assert "Representation" not in door["attributes"]
    assert any(
        loss["path"].endswith("/attributes/Representation")
        and loss["kind"] == "MAPPED_GEOMETRY"
        for loss in hxp_result.losses
    )
