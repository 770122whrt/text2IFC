from text2ifc_agent.fact_delta import evaluate_repair_fact_delta


def test_fact_delta_allows_only_evidence_backed_permitted_change():
    before = {
        "schema_version": "bim-json/2.0",
        "entities": [
            {
                "id": "wall-west",
                "attributes": {
                    "ObjectPlacement": {"ref_direction": [1, 0, 0]}
                },
            }
        ],
    }
    after = {
        "schema_version": "bim-json/2.0",
        "entities": [
            {
                "id": "wall-west",
                "attributes": {
                    "ObjectPlacement": {"ref_direction": [0, 1, 0]}
                },
            }
        ],
    }
    path = "/entities/0/attributes/ObjectPlacement/ref_direction"

    report = evaluate_repair_fact_delta(
        before=before,
        after=after,
        allowed_change_paths=[path],
        evidence_by_path={
            path: [
                "turn-user-001",
                "schema:bim-json-v2:object-placement",
            ]
        },
    )

    assert report["valid"] is True
    assert report["issue_count"] == 0
    assert {change["path"] for change in report["changes"]} == {
        path + "/0",
        path + "/1",
    }


def test_fact_delta_blocks_added_fact_without_existing_evidence():
    before = {"schema_version": "bim-json/2.0", "entities": []}
    after = {
        "schema_version": "bim-json/2.0",
        "entities": [
            {
                "id": "door-2",
                "attributes": {"OverallWidth": 900},
            }
        ],
    }

    report = evaluate_repair_fact_delta(
        before=before,
        after=after,
        allowed_change_paths=["/entities"],
        evidence_by_path={},
    )

    assert report["valid"] is False
    assert any(issue["code"] == "MISSING_DELTA_EVIDENCE" for issue in report["issues"])


def test_fact_delta_blocks_unpermitted_removal_and_supervisor_evidence():
    before = {
        "schema_version": "bim-json/2.0",
        "entities": [{"id": "wall-1", "attributes": {"Name": "Wall"}}],
    }
    after = {"schema_version": "bim-json/2.0", "entities": []}

    unpermitted = evaluate_repair_fact_delta(
        before=before,
        after=after,
        allowed_change_paths=["/relationships"],
        evidence_by_path={},
    )
    supervisor = evaluate_repair_fact_delta(
        before=before,
        after={
            "schema_version": "bim-json/2.0",
            "entities": [{"id": "wall-1", "attributes": {"Name": "Rewritten"}}],
        },
        allowed_change_paths=["/entities/0/attributes/Name"],
        evidence_by_path={
            "/entities/0/attributes/Name": ["supervisor:semantic-decision"]
        },
    )

    assert any(issue["code"] == "UNPERMITTED_FACT_DELTA" for issue in unpermitted["issues"])
    assert any(issue["code"] == "FORBIDDEN_DELTA_EVIDENCE" for issue in supervisor["issues"])
