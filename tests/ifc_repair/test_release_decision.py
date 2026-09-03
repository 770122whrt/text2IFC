from text2ifc_ifc_repair.release_decision import build_release_decision


def _evaluation(*, l1: str = "passed", l2: str = "passed") -> dict:
    complete = l1 == l2 == "passed"
    return {
        "status": "passed" if complete else "failed",
        "successful_artifact_publishable": complete,
        "operations": [
            {
                "operation_id": "operation-door-001",
                "levels": [
                    {"level": "L1", "status": l1},
                    {"level": "L2", "status": l2},
                    {"level": "L3", "status": "not_required"},
                ],
            }
        ],
    }


def test_release_requires_l0_l1_l2_and_no_blocking_findings() -> None:
    passed = build_release_decision(
        l0_pass=True,
        production_evaluation=_evaluation(),
    )
    blocked = build_release_decision(
        l0_pass=True,
        production_evaluation=_evaluation(),
        blocking_findings=[
            {
                "code": "DOOR_GEOMETRY_ALIGNED_WITH_OPENING",
                "message": "Door misses retained Opening.",
            }
        ],
    )

    assert passed["publishable"] is True
    assert passed["l0_pass"] is True
    assert passed["l1_pass"] is True
    assert passed["l2_pass"] is True
    assert blocked["publishable"] is False


def test_release_fails_closed_when_any_level_is_missing_or_failed() -> None:
    failed_l1 = build_release_decision(
        l0_pass=True,
        production_evaluation=_evaluation(l1="failed"),
    )
    missing_levels = build_release_decision(
        l0_pass=True,
        production_evaluation={
            "status": "passed",
            "successful_artifact_publishable": True,
            "operations": [{"operation_id": "operation-door-001"}],
        },
    )

    assert failed_l1["publishable"] is False
    assert failed_l1["l1_pass"] is False
    assert missing_levels["publishable"] is False
    assert missing_levels["l1_pass"] is False
    assert missing_levels["l2_pass"] is False
