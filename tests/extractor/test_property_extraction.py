from __future__ import annotations


def _partial(result):
    document = result.draft["partial_document"] if result.draft else result.document
    assert document is not None
    return document


def test_native_attributes_and_standard_properties_preserve_names_and_types(
    hxp_result,
) -> None:
    document = _partial(hxp_result)
    wall = next(
        item
        for item in document["entities"]
        if item.get("global_id") == "226kTvWe52dBaVNzWNVUTS"
    )

    assert wall["attributes"]["Name"] == "基本墙:墙240:3866"
    assert wall["property_sets"]["Pset_WallCommon"]["Reference"] == "墙240"
    assert wall["property_sets"]["Pset_WallCommon"]["IsExternal"] is True
    assert wall["property_sets"]["Pset_WallCommon"]["LoadBearing"] is False
