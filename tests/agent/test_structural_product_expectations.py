"""Explicit beam/column facts must survive public Generation orchestration."""
from copy import deepcopy

import pytest

from text2ifc_agent.expected_facts import ExpectedFactsError, build_expected_facts
from text2ifc_agent.semantic_coverage import build_design_geometry_expectation


def brief(collection="columns", *, name="reading-post", storey="upper", bounds=None):
    return {"known_facts": {
        "storeys": [{"id": "ground", "elevation_mm": 0, "net_height_mm": 3400},
                    {"id": "upper", "elevation_mm": 4200, "net_height_mm": 3400}],
        collection: [{"id": name, "storey": storey, "bounds_mm": bounds or {
            "x": [-1600, -1300], "y": [5200, 5500], "z": [4200, 7600]}}],
    }}


@pytest.mark.parametrize("collection,family", [("columns", "IfcColumn"), ("beams", "IfcBeam")])
def test_explicit_structural_product_reaches_counts_ownership_and_world_geometry(collection, family):
    source = brief(collection); before = deepcopy(source)
    expected = build_expected_facts(case_id="unrelated-library", design_brief=source)
    assert expected["total_counts"].get(family) == 1
    product = expected["products"][0]
    assert product["id"] == "reading-post" and product["ifc_class"] == family
    package = next(p for p in expected["generation_package_manifest"]["packages"] if p["storey_id"] == "upper")
    assert package["owned_component_classes"]["reading-post"] == family
    geometry = build_design_geometry_expectation(case_id="unrelated-library", design_brief=source, expected_facts=expected)
    assert geometry["products"]["reading-post"]["bbox"] == {
        "x": [-1.6, -1.3], "y": [5.2, 5.5], "z": [4.2, 7.6]}
    assert source == before


@pytest.mark.parametrize("change", ["missing_bounds", "reversed", "zero", "nan", "infinity", "bool", "missing_storey"])
def test_incomplete_structural_fact_blocks_package_instead_of_disappearing(change):
    source = brief(); item = source["known_facts"]["columns"][0]
    if change == "missing_bounds": item.pop("bounds_mm")
    elif change == "missing_storey": item["storey"] = "not-offered"
    else:
        item["bounds_mm"]["x"] = {"reversed": [10, 0], "zero": [0, 0],
            "nan": [0, float("nan")], "infinity": [0, float("inf")], "bool": [False, 300]}[change]
    expected = build_expected_facts(case_id="other-scene", design_brief=source)
    assert expected["total_counts"].get("IfcColumn") == 1
    assert expected["generation_package_manifest"]["status"] == "draft_required"
    assert expected["generation_package_manifest"]["issues"]


def test_structural_ids_must_not_collide_across_families():
    source=brief(); source["known_facts"]["beams"]=deepcopy(source["known_facts"]["columns"])
    with pytest.raises(ExpectedFactsError, match="IDENTITY"):
        build_expected_facts(case_id="duplicate",design_brief=source)


@pytest.mark.parametrize("invalid", [{"id":"one"}, [None], [{"storey":"upper"}], [{"id":"", "storey":"upper"}]])
def test_structural_collection_cannot_be_silently_dropped_or_get_an_invented_identity(invalid):
    source=brief();source["known_facts"]["columns"]=invalid
    with pytest.raises(ExpectedFactsError, match="PRODUCT"):
        build_expected_facts(case_id="malformed-family",design_brief=source)


def test_absent_structural_requests_create_no_columns_or_beams():
    source=brief(); source["known_facts"].pop("columns")
    expected=build_expected_facts(case_id="no-structure",design_brief=source)
    assert "IfcColumn" not in expected["total_counts"] and "IfcBeam" not in expected["total_counts"]
    assert expected["products"] == []


def _model(*, family="IfcColumn", storey="upper", shift=0, include=True):
    from text2ifc_agent.geometry_authoring import rectangular_prism_attributes
    def spatial(identity, cls, parent=None, elevation=0):
        attributes={"Name":identity}
        if parent:
            attributes["ObjectPlacement"]={"relative_to":parent,"origin":[0,0,elevation],
                "axis":[0,0,1],"ref_direction":[1,0,0]}
        if cls=="IfcBuildingStorey":attributes["Elevation"]=elevation
        return {"id":identity,"ifc_class":cls,"attributes":attributes,
            "property_sets":{},"provenance":{"source":"test"}}
    entities=[spatial("project","IfcProject"),spatial("site","IfcSite","project"),
        spatial("building","IfcBuilding","site"),spatial("ground","IfcBuildingStorey","building"),
        spatial("upper","IfcBuildingStorey","building",4200)]
    if include:
        base=0 if storey=="upper" else 4200
        entities.append({"id":"reading-post","ifc_class":family,
            "attributes":{"Name":"reading-post",**rectangular_prism_attributes(relative_to=storey,
                lower=[-1600+shift,5200,base],upper=[-1300+shift,5500,base+3400])},
            "property_sets":{},"provenance":{"source":"test"}})
    return {"schema_version":"bim-json/2.2","ifc_schema":"IFC2X3","units":{"length":"MILLIMETRE"},
        "entities":entities,"relationships":[],"provenance":{"source":"test"}}


@pytest.mark.parametrize("mutation", ["none", "wrong_class", "wrong_storey", "shift", "missing"])
def test_reopened_ifc_must_match_structural_family_storey_and_world_bounds(tmp_path, mutation):
    from text2ifc_compiler import compile_document
    from text2ifc_quality.generated_ifc import check_generated_ifc
    source=brief();expected=build_expected_facts(case_id="structural",design_brief=source)
    geometry=build_design_geometry_expectation(case_id="structural",design_brief=source,expected_facts=expected)
    doc=_model(family="IfcBeam" if mutation=="wrong_class" else "IfcColumn",
        storey="ground" if mutation=="wrong_storey" else "upper",
        shift=100 if mutation=="shift" else 0,include=mutation!="missing")
    result=compile_document(doc,tmp_path/'structural.ifc')
    assert result.success,(result.input_issues,result.ifc_issues)
    checked=check_generated_ifc(result.output_path,geometry)
    assert checked.success == (mutation=="none"),checked
