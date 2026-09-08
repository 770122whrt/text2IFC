from __future__ import annotations

import json
from pathlib import Path

import ifcopenshell.util.element
import pytest

from text2ifc_compiler import compile_document, open_ifc


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.mark.parametrize('version', ['bim-json/2.0', 'bim-json/2.1'])
@pytest.mark.parametrize('name', ['南墙门洞关联', 'wall-1', ''])
def test_relationship_name_is_literal_not_entity_reference(tmp_path, version, name):
    payload = document()
    payload['schema_version'] = version
    for relation in payload['relationships']:
        relation['attributes']['Name'] = name
    output = tmp_path / 'named-relations.ifc'
    result = compile_document(payload, output)
    assert result.success, result
    model = open_ifc(output)
    for kind in ['IfcRelVoidsElement', 'IfcRelFillsElement']:
        assert model.by_type(kind)[0].Name == name


@pytest.mark.parametrize('kind', ['IfcRelVoidsElement', 'IfcRelFillsElement', 'IfcRelAggregates', 'IfcRelDefinesByType', 'IfcRelConnectsPathElements'])
def test_relationship_literal_metadata_survives_all_compiler_routes(tmp_path, kind):
    payload = document()
    metadata = {'Name': '关系名称', 'Description': 'wall-1 is text here'}
    if kind in {'IfcRelVoidsElement', 'IfcRelFillsElement'}:
        relation = next(r for r in payload['relationships'] if r['ifc_class'] == kind)
    elif kind == 'IfcRelAggregates':
        relation = {'id': 'aggregate-labelled', 'ifc_class': kind,
                    'attributes': {'RelatingObject': 'building-1', 'RelatedObjects': ['storey-1']}, 'provenance': {'source': 'test'}}
        payload['relationships'].append(relation)
    elif kind == 'IfcRelDefinesByType':
        payload['schema_version'] = 'bim-json/2.1'
        payload['entities'].append({'id': 'beam-type', 'ifc_class': 'IfcBeamType',
                                    'attributes': {'Name': 'Beam type', 'PredefinedType': 'BEAM'},
                                    'property_sets': {}, 'provenance': {'source': 'test'}})
        relation = {'id': 'type-labelled', 'ifc_class': kind,
                    'attributes': {'RelatingType': 'beam-type', 'RelatedObjects': ['beam-1']}, 'provenance': {'source': 'test'}}
        payload['relationships'].append(relation)
    else:
        wall = json.loads(json.dumps(next(e for e in payload['entities'] if e['id'] == 'wall-1')))
        wall['id'] = 'wall-second'
        payload['entities'].append(wall)
        relation = {'id': 'connect-labelled', 'ifc_class': kind, 'attributes': {
            'RelatingElement': 'wall-1', 'RelatedElement': 'wall-second',
            'RelatingPriorities': [], 'RelatedPriorities': [],
            'RelatedConnectionType': 'ATSTART', 'RelatingConnectionType': 'ATEND'}, 'provenance': {'source': 'test'}}
        payload['relationships'].append(relation)
    relation['attributes'].update(metadata)
    output = tmp_path / 'metadata.ifc'
    result = compile_document(payload, output)
    assert result.success, result
    found = [r for r in open_ifc(output).by_type(kind) if r.Name == metadata['Name']]
    assert len(found) == 1
    assert found[0].Description == metadata['Description']


def _bim_id(entity) -> str:
    return ifcopenshell.util.element.get_psets(entity)[
        "Pset_text2IFCIdentity"
    ]["BimJsonId"]


def test_v2_generates_bookkeeping_and_explicit_void_fill_relations(
    tmp_path: Path,
) -> None:
    output = tmp_path / "relations-v2.ifc"
    assert compile_document(document(), output).success
    model = open_ifc(output)

    void = model.by_type("IfcRelVoidsElement")
    fill = model.by_type("IfcRelFillsElement")
    assert len(void) == 1
    assert len(fill) == 1
    assert _bim_id(void[0].RelatingBuildingElement) == "wall-1"
    assert _bim_id(void[0].RelatedOpeningElement) == "opening-1"
    assert _bim_id(fill[0].RelatingOpeningElement) == "opening-1"
    assert _bim_id(fill[0].RelatedBuildingElement) == "door-1"

    assert model.by_type("IfcRelAggregates")
    assert model.by_type("IfcRelContainedInSpatialStructure")
    assert model.by_type("IfcRelDefinesByProperties")


def test_v2_deduplicates_explicit_spatial_aggregates_already_derived_from_placement(
    tmp_path: Path,
) -> None:
    payload = document()
    payload["relationships"].extend(
        [
            {
                "id": "aggregate-project-site",
                "ifc_class": "IfcRelAggregates",
                "attributes": {
                    "RelatingObject": "project-1",
                    "RelatedObjects": ["site-1"],
                },
                "provenance": {"source": "test"},
            },
            {
                "id": "aggregate-site-building",
                "ifc_class": "IfcRelAggregates",
                "attributes": {
                    "RelatingObject": "site-1",
                    "RelatedObjects": ["building-1"],
                },
                "provenance": {"source": "test"},
            },
            {
                "id": "aggregate-building-storey",
                "ifc_class": "IfcRelAggregates",
                "attributes": {
                    "RelatingObject": "building-1",
                    "RelatedObjects": ["storey-1"],
                },
                "provenance": {"source": "test"},
            },
        ]
    )

    output = tmp_path / "deduplicated-spatial-aggregates.ifc"
    result = compile_document(payload, output)

    assert result.success
    model = open_ifc(output)
    spatial_aggregates = [
        relation
        for relation in model.by_type("IfcRelAggregates")
        if relation.RelatingObject.is_a()
        in {"IfcProject", "IfcSite", "IfcBuilding"}
    ]
    assert len(spatial_aggregates) == 3
