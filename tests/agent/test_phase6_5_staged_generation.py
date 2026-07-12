import copy
import json

import pytest

from text2ifc_agent.candidate_index import build_candidate_index
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput
from text2ifc_agent.revisions import hash_json_value
from text2ifc_agent.staged_generation import build_skeleton_workspace, run_staged_generation
from text2ifc_contract.validation_v2 import validate_v2_document


def _entity(entity_id, ifc_class, relative_to=None):
    attributes = {"Name": entity_id}
    if relative_to:
        attributes["ObjectPlacement"] = {
            "relative_to": relative_to,
            "origin": [0, 0, 0],
            "axis": [0, 0, 1],
            "ref_direction": [1, 0, 0],
        }
    if ifc_class in {
        "IfcWall",
        "IfcSpace",
        "IfcOpeningElement",
        "IfcWindow",
        "IfcSlab",
        "IfcStair",
        "IfcStairFlight",
    }:
        attributes["Representation"] = {
            "kind": "extruded_profile",
            "profile": {"kind": "rectangle", "x": 1000, "y": 200},
            "depth": 3000,
            "direction": [0, 0, 1],
        }
    return {
        "id": entity_id,
        "ifc_class": ifc_class,
        "attributes": attributes,
        "property_sets": {},
        "provenance": {"source": "staged-test"},
    }


def _relationship(relationship_id, ifc_class, **attributes):
    return {
        "id": relationship_id,
        "ifc_class": ifc_class,
        "attributes": attributes,
        "provenance": {"source": "staged-test"},
    }


def _fixture(storey_count):
    storey_ids = [f"storey-{index}" for index in range(1, storey_count + 1)]
    skeleton = {
        "schema_version": "bim-json/2.0",
        "ifc_schema": "IFC2X3",
        "units": {"length": "MILLIMETRE"},
        "entities": [
            _entity("project-main", "IfcProject"),
            _entity("site-main", "IfcSite", "project-main"),
            _entity("building-main", "IfcBuilding", "site-main"),
            *[_entity(storey_id, "IfcBuildingStorey", "building-main") for storey_id in storey_ids],
        ],
        "relationships": [],
        "provenance": {"source": "staged-test"},
    }
    packages = [
        {
            "package_id": "package-skeleton",
            "kind": "skeleton",
            "storey_id": None,
            "owned_component_ids": [entity["id"] for entity in skeleton["entities"]],
            "allowed_reference_ids": [],
        }
    ]
    package_values = []
    for index, storey_id in enumerate(storey_ids, start=1):
        ids = {
            "wall": f"wall-{index}",
            "space": f"space-{index}",
            "opening": f"opening-{index}",
            "window": f"window-{index}",
            "void": f"void-{index}",
            "fill": f"fill-{index}",
        }
        values = [
            _entity(ids["wall"], "IfcWall", storey_id),
            _entity(ids["space"], "IfcSpace", storey_id),
            _entity(ids["opening"], "IfcOpeningElement", ids["wall"]),
            _entity(ids["window"], "IfcWindow", ids["opening"]),
            _relationship(
                ids["void"],
                "IfcRelVoidsElement",
                RelatingBuildingElement=ids["wall"],
                RelatedOpeningElement=ids["opening"],
            ),
            _relationship(
                ids["fill"],
                "IfcRelFillsElement",
                RelatingOpeningElement=ids["opening"],
                RelatedBuildingElement=ids["window"],
            ),
        ]
        packages.append(
            {
                "package_id": f"package-{storey_id}",
                "kind": "storey_local",
                "storey_id": storey_id,
                "owned_component_ids": [value["id"] for value in values],
                "allowed_reference_ids": [storey_id],
            }
        )
        package_values.append(values)

    cross_values = []
    for index, storey_id in enumerate(storey_ids, start=1):
        cross_values.append(_entity(f"slab-{index}", "IfcSlab", storey_id))
    for index in range(1, storey_count):
        cross_values.extend(
            [
                _entity(f"stair-{index}-{index + 1}", "IfcStair", f"storey-{index}"),
                _entity(f"flight-{index}-{index + 1}", "IfcStairFlight", f"stair-{index}-{index + 1}"),
                _entity(f"landing-{index}-{index + 1}", "IfcSlab", f"storey-{index + 1}"),
                _entity(f"stair-opening-{index + 1}", "IfcOpeningElement", f"slab-{index + 1}"),
            ]
        )
    cross_values.append(_entity("roof-main", "IfcSlab", storey_ids[-1]))
    packages.append(
        {
            "package_id": "package-cross-storey",
            "kind": "cross_storey",
            "storey_id": None,
            "owned_component_ids": [value["id"] for value in cross_values],
            "allowed_reference_ids": storey_ids,
        }
    )
    package_values.append(cross_values)
    manifest = {
        "schema_version": "text2ifc/generation-package-manifest/1.0",
        "status": "ready",
        "storey_count": storey_count,
        "packages": packages,
        "issues": [],
    }
    expected = {
        "schema_version": "text2ifc/expected-facts/1.0",
        "storeys": [
            {"id": storey_id, "elevation_mm": (index - 1) * 3150}
            for index, storey_id in enumerate(storey_ids, start=1)
        ],
        "generation_package_manifest": manifest,
    }
    return skeleton, manifest, expected, package_values


def _changesets(skeleton, manifest, expected, package_values):
    workspace = copy.deepcopy(skeleton)
    results = []
    revision_id = "revision-00"
    for sequence, (package, values) in enumerate(zip(manifest["packages"][1:], package_values), start=1):
        index = build_candidate_index(workspace)
        operations = [
            {
                "operation_id": f"operation-add-{value['id']}",
                "op": "add_relationship" if value["ifc_class"].startswith("IfcRel") else "add_entity",
                "target_id": value["id"],
                "value": value,
                "evidence_refs": [f"issue-{package['package_id']}:/expected"],
            }
            for value in values
        ]
        results.append(
            {
                "schema_version": "text2ifc/bim-json-changeset/1.0",
                "changeset_id": f"changeset-package-{sequence}",
                "base_revision_id": revision_id,
                "base_candidate_hash": index["candidate_hash"],
                "expected_facts_hash": hash_json_value(expected),
                "source_issue_ids": [f"issue-{package['package_id']}"],
                "scope_id": f"scope-package-{sequence}",
                "operations": operations,
            }
        )
        for value in values:
            collection = "relationships" if value["ifc_class"].startswith("IfcRel") else "entities"
            workspace[collection].append(copy.deepcopy(value))
        revision_id = f"revision-{sequence:02d}"
    return results


class SequenceProvider:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = []

    def generate_live(self, *, session_id, prompt, schema, state):
        payload = self.payloads[len(self.calls)]
        self.calls.append({"session_id": session_id, "state": state, "schema": schema})
        text = json.dumps(payload, ensure_ascii=False)
        return LiveProviderResult(
            session_id=session_id,
            evidence_class="unit_test_fixture",
            http_status=200,
            request={"model": "fake", "messages": [{"role": "user", "content": prompt}]},
            response={
                "id": f"response-package-{len(self.calls)}",
                "model": "fake",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 10, "output_tokens": 10},
            },
            events=(),
            output=ProviderOutput(text=text, metadata={"provider": "fake"}),
        )


@pytest.mark.parametrize("storey_count", [2, 3, 5])
def test_skeleton_workspace_uses_explicit_dynamic_storeys(storey_count):
    expected = {
        "storeys": [
            {"id": f"level-{index}", "elevation_mm": (index - 1) * 3300}
            for index in range(1, storey_count + 1)
        ]
    }

    skeleton = build_skeleton_workspace(expected)

    storeys = [entity for entity in skeleton["entities"] if entity["ifc_class"] == "IfcBuildingStorey"]
    assert [entity["id"] for entity in storeys] == [f"level-{index}" for index in range(1, storey_count + 1)]
    assert [entity["attributes"]["Elevation"] for entity in storeys] == [
        (index - 1) * 3300 for index in range(1, storey_count + 1)
    ]
    assert validate_v2_document(skeleton) == []


@pytest.mark.parametrize("storey_count", [2, 3])
def test_staged_generation_composes_dynamic_storeys_and_only_final_is_formal(
    tmp_path, storey_count
):
    skeleton, manifest, expected, package_values = _fixture(storey_count)
    provider = SequenceProvider(_changesets(skeleton, manifest, expected, package_values))

    result = run_staged_generation(
        provider=provider,
        output_dir=tmp_path,
        case_id=f"case-{storey_count}",
        user_request="创建多层建筑。",
        conversation=[{"role": "user", "content": "创建多层建筑。"}],
        design_brief={"status": "ready"},
        expected_facts=expected,
        skeleton=skeleton,
        manifest=manifest,
        trace_level="debug",
    )

    assert result["valid"] is True
    assert result["status"] == "formal"
    assert validate_v2_document(result["candidate"]) == []
    assert len(result["package_records"]) == storey_count + 1
    assert all(record["status"] == "accepted" for record in result["package_records"])
    assert all(record["pre_apply_status"] == "partial_not_formal" for record in result["package_records"])
    assert (tmp_path / "candidate.json").is_file()
    assert not (tmp_path / "output.ifc").exists()
    assert len(provider.calls) == storey_count + 1
    assert all((tmp_path / record["artifact_dir"] / "response.raw.json").is_file() for record in result["package_records"])


def test_staged_generation_stops_on_package_draft_without_promoting_candidate(tmp_path):
    skeleton, manifest, expected, package_values = _fixture(2)
    payloads = _changesets(skeleton, manifest, expected, package_values)
    payloads[1] = {
        "draft_version": "bim-json-draft/1.0",
        "target_schema_version": "bim-json/2.0",
        "partial_document": {"entities": {"wall-2": {"attributes": {}}}},
        "missing_facts": [
            {
                "entity_id": "wall-2",
                "path": "/entities/wall-2/attributes/Representation",
                "code": "MISSING_GEOMETRY",
                "message": "Geometry is not explicit.",
            }
        ],
        "losses": [],
        "clarification_targets": [],
        "provenance": {"source": "staged-test"},
    }
    provider = SequenceProvider(payloads)

    result = run_staged_generation(
        provider=provider,
        output_dir=tmp_path,
        case_id="case-draft",
        user_request="创建两层建筑。",
        conversation=[{"role": "user", "content": "创建两层建筑。"}],
        design_brief={"status": "ready"},
        expected_facts=expected,
        skeleton=skeleton,
        manifest=manifest,
    )

    assert result["valid"] is False
    assert result["status"] == "draft_required"
    assert len(result["package_records"]) == 2
    assert not (tmp_path / "candidate.json").exists()
    assert not (tmp_path / "output.ifc").exists()


def test_staged_generation_retries_only_the_failed_package_within_three_attempts(tmp_path):
    skeleton, manifest, expected, package_values = _fixture(2)
    valid_payloads = _changesets(skeleton, manifest, expected, package_values)
    provider = SequenceProvider([skeleton, *valid_payloads])

    result = run_staged_generation(
        provider=provider,
        output_dir=tmp_path,
        case_id="case-package-retry",
        user_request="创建两层建筑。",
        conversation=[{"role": "user", "content": "创建两层建筑。"}],
        design_brief={"status": "ready"},
        expected_facts=expected,
        skeleton=skeleton,
        manifest=manifest,
    )

    assert result["valid"] is True
    assert len(provider.calls) == len(valid_payloads) + 1
    assert result["package_records"][0]["attempt_count"] == 2
    assert all(record["attempt_count"] == 1 for record in result["package_records"][1:])
    assert (tmp_path / "package-01-package-storey-1" / "attempt-02" / "changeset.json").is_file()


def test_staged_scope_exposes_manifest_relationship_ownership_to_provider(tmp_path):
    skeleton, manifest, expected, package_values = _fixture(2)
    first = manifest["packages"][1]
    relationship_ids = [
        value["id"] for value in package_values[0] if value["ifc_class"].startswith("IfcRel")
    ]
    first["owned_component_ids"] = [
        value for value in first["owned_component_ids"] if value not in relationship_ids
    ]
    first["owned_relationship_ids"] = relationship_ids
    provider = SequenceProvider(_changesets(skeleton, manifest, expected, package_values))

    result = run_staged_generation(
        provider=provider,
        output_dir=tmp_path,
        case_id="case-relationship-scope",
        user_request="创建两层建筑。",
        conversation=[{"role": "user", "content": "创建两层建筑。"}],
        design_brief={"status": "ready"},
        expected_facts=expected,
        skeleton=skeleton,
        manifest=manifest,
    )

    assert result["valid"] is True
    prompt_inputs = json.loads(
        (tmp_path / "package-01-package-storey-1" / "prompt-render-input.json").read_text(
            encoding="utf-8"
        )
    )
    assert prompt_inputs["CHANGE_SCOPE"]["relationship_ids"] == relationship_ids
    assert not set(relationship_ids) & set(prompt_inputs["CHANGE_SCOPE"]["entity_ids"])
