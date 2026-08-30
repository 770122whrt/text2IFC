from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

import pytest

from scripts.ifc_repair import curate_phase12_live_proof as live_proof


SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
STAGE15_TEMPLATE = {
    "template_id": live_proof.PROPERTY_RESOLUTION_TEMPLATE_ID,
    "template_hash": live_proof.PROPERTY_RESOLUTION_TEMPLATE_HASH,
}
STAGE1_PROFILES = [
    {
        "profile_id": "occurrence.set-properties",
        "profile_version": "0.1",
        "profile_hash": SHA_A,
    }
]
STAGE2_SELECTION = {
    "profile_ids": ["occurrence.set-properties"],
    "profiles": [
        {
            "profile_id": "occurrence.set-properties",
            "profile_version": "0.1",
            "profile_hash": SHA_A,
        }
    ],
    "profile_hashes": [SHA_A],
    "few_shot_ids": ["occurrence.set-properties.complete"],
    "few_shot_hashes": [SHA_B],
}


def _canonical_sha256(value: Any) -> str:
    rendered = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _attempt(
    *,
    case_id: str,
    stage: str,
    parent_attempt_id: str | None,
) -> dict[str, Any]:
    request = {
        "model": "deepseek-v4-flash",
        "extra_body": {"thinking": {"type": "enabled"}},
    }
    response = {"id": f"response-{stage}", "content": {"ok": True}}
    usage = {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    attempt = {
        "attempt_id": f"{case_id}:{stage}:001",
        "parent_attempt_id": parent_attempt_id,
        "case_id": case_id,
        "lineage": "initial",
        "stage": stage,
        "ordinal": 1,
        "stage_attempt": 1,
        "correction_reason": None,
        "evidence_class": "live",
        "http_status": 200,
        "fallback_flags": {
            "cached": False,
            "hand_authored": False,
            "prerecorded": False,
            "synthetic": False,
        },
        "private_evidence_detected": False,
        "provider": "deepseek-openai-compatible",
        "model": "deepseek-v4-flash",
        "usage": usage,
        "raw_request_sha256": "sha256:" + "1" * 64,
        "raw_response_sha256": "sha256:" + "2" * 64,
        "request_sha256": _canonical_sha256(request),
        "response_sha256": _canonical_sha256(response),
        "request": request,
        "response": response,
        "metadata": {
            "response_id": f"response-{stage}",
            "provider": "deepseek-openai-compatible",
            "model": "deepseek-v4-flash",
            "evidence_class": "live",
            "usage": usage,
            "transport_attempts": 1,
            "request_configuration": {
                "thinking": {"type": "enabled"},
                "temperature": {"value": 0, "effective": False},
            },
        },
        "error": None,
        "template_id": None,
        "template_hash": None,
        "profile_ids": ["occurrence.set-properties"],
        "profile_versions": ["0.1"],
        "profile_hashes": [SHA_A],
        "few_shot_ids": [],
        "few_shot_hashes": [],
        "few_shot_bindings": [],
    }
    if stage == "property_resolution":
        attempt.update(
            {
                "template_id": STAGE15_TEMPLATE["template_id"],
                "template_hash": STAGE15_TEMPLATE["template_hash"],
                "profile_ids": [],
                "profile_versions": [],
                "profile_hashes": [],
            }
        )
    elif stage == "stage2":
        attempt.update(
            {
                "few_shot_ids": STAGE2_SELECTION["few_shot_ids"],
                "few_shot_hashes": STAGE2_SELECTION["few_shot_hashes"],
                "few_shot_bindings": [
                    {
                        "few_shot_id": STAGE2_SELECTION["few_shot_ids"][0],
                        "few_shot_hash": STAGE2_SELECTION["few_shot_hashes"][0],
                    }
                ],
            }
        )
    return attempt


def _r1_attempts(case_id: str = "H3") -> list[dict[str, Any]]:
    stage1 = _attempt(case_id=case_id, stage="stage1", parent_attempt_id=None)
    stage15 = _attempt(
        case_id=case_id,
        stage="property_resolution",
        parent_attempt_id=stage1["attempt_id"],
    )
    stage2 = _attempt(
        case_id=case_id,
        stage="stage2",
        parent_attempt_id=stage15["attempt_id"],
    )
    return [stage1, stage15, stage2]


def _audit(
    attempts: list[dict[str, Any]],
    *,
    expected_rounds: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return live_proof.audit_live_attempts(
        case_id="H3",
        raw_attempts=attempts,
        expected_stage1_profiles=STAGE1_PROFILES,
        expected_stage2_selection=STAGE2_SELECTION,
        expected_property_resolution_template=STAGE15_TEMPLATE,
        expected_provider="deepseek-openai-compatible",
        expected_model="deepseek-v4-flash",
        expected_evidence_mode="live",
        expected_thinking={"type": "enabled"},
        expected_rounds=expected_rounds,
    )


def _r1_add_detail_attempts(case_id: str = "H3") -> list[dict[str, Any]]:
    attempts = [
        _attempt(case_id=case_id, stage="stage1", parent_attempt_id=None),
        _attempt(
            case_id=case_id,
            stage="property_resolution",
            parent_attempt_id=None,
        ),
        _attempt(case_id=case_id, stage="stage1", parent_attempt_id=None),
        _attempt(
            case_id=case_id,
            stage="property_resolution",
            parent_attempt_id=None,
        ),
        _attempt(case_id=case_id, stage="stage2", parent_attempt_id=None),
    ]
    for attempt in attempts[:2]:
        attempt["lineage"] = "initial"
    for attempt in attempts[2:]:
        attempt["lineage"] = "clarification-resume"
    _rechain_attempts(attempts)
    return attempts


R1_ADD_DETAIL_ROUNDS = [
    {
        "lineage": "initial",
        "stages": ["stage1", "property_resolution"],
    },
    {
        "lineage": "clarification-resume",
        "stages": ["stage1", "property_resolution", "stage2"],
    },
]


R1_TARGET_SELECT_ROUNDS = [
    {
        "lineage": "initial",
        "stages": ["stage1"],
    },
    {
        "lineage": "clarification-resume",
        "stages": ["property_resolution", "stage2"],
    },
]


def _r1_target_select_attempts(case_id: str = "H3") -> list[dict[str, Any]]:
    attempts = [
        _attempt(case_id=case_id, stage="stage1", parent_attempt_id=None),
        _attempt(
            case_id=case_id,
            stage="property_resolution",
            parent_attempt_id=None,
        ),
        _attempt(case_id=case_id, stage="stage2", parent_attempt_id=None),
    ]
    attempts[0]["lineage"] = "initial"
    for attempt in attempts[1:]:
        attempt["lineage"] = "clarification-resume"
    _rechain_attempts(attempts)
    return attempts


def test_r1_live_attempt_audit_accepts_target_select_resume_without_stage1(
) -> None:
    result = _audit(
        _r1_target_select_attempts(),
        expected_rounds=R1_TARGET_SELECT_ROUNDS,
    )

    assert result["transport_calls_by_stage"] == {
        "stage1": 1,
        "property_resolution": 1,
        "stage2": 1,
    }


def test_r1_live_attempt_audit_rejects_h3_resume_without_lineage() -> None:
    attempts = _r1_target_select_attempts()
    attempts[1].pop("lineage")

    with pytest.raises(
        ValueError,
        match="LIVE_ATTEMPT_ROUND_LINEAGE_INVALID",
    ):
        _audit(attempts, expected_rounds=R1_TARGET_SELECT_ROUNDS)


def test_r1_live_attempt_audit_rejects_h3_resume_stage_order_drift() -> None:
    attempts = _r1_target_select_attempts()
    attempts[1:] = [attempts[2], attempts[1]]
    _rechain_attempts(attempts)

    with pytest.raises(
        ValueError,
        match="LIVE_ATTEMPT_ROUND_SEQUENCE_INVALID",
    ):
        _audit(attempts, expected_rounds=R1_TARGET_SELECT_ROUNDS)


def test_r1_live_attempt_audit_accepts_explicit_add_detail_round_contract(
) -> None:
    result = _audit(
        _r1_add_detail_attempts(),
        expected_rounds=R1_ADD_DETAIL_ROUNDS,
    )

    assert result["attempt_count"] == 5
    assert result["transport_calls_by_stage"] == {
        "stage1": 2,
        "property_resolution": 2,
        "stage2": 1,
    }


def test_plan07_contract_none_keeps_single_round_stage_order() -> None:
    case_id = "complete"
    attempts = [
        _attempt(case_id=case_id, stage="stage1", parent_attempt_id=None),
        _attempt(
            case_id=case_id,
            stage="property_resolution",
            parent_attempt_id=None,
        ),
        _attempt(
            case_id=case_id,
            stage="property_resolution",
            parent_attempt_id=None,
        ),
        _attempt(case_id=case_id, stage="stage2", parent_attempt_id=None),
    ]
    stage1 = attempts[0]
    stage1_ids = sorted(live_proof.EXPECTED_STAGE1_PROFILES)
    stage1["profile_ids"] = stage1_ids
    stage1["profile_versions"] = ["legacy" for _item in stage1_ids]
    stage1["profile_hashes"] = [SHA_A for _item in stage1_ids]
    selection = live_proof.select_prompt_profiles(
        sorted(live_proof.EXPECTED_SELECTED_PROFILES[case_id])
    ).to_dict()
    stage2 = attempts[-1]
    stage2["profile_ids"] = selection["profile_ids"]
    stage2["profile_versions"] = [
        str(profile["profile_version"]) for profile in selection["profiles"]
    ]
    stage2["profile_hashes"] = selection["profile_hashes"]
    stage2["few_shot_ids"] = selection["few_shot_ids"]
    stage2["few_shot_hashes"] = selection["few_shot_hashes"]
    stage2["few_shot_bindings"] = [
        {"few_shot_id": few_shot_id, "few_shot_hash": few_shot_hash}
        for few_shot_id, few_shot_hash in zip(
            selection["few_shot_ids"],
            selection["few_shot_hashes"],
            strict=True,
        )
    ]
    _rechain_attempts(attempts)

    _audited, counts, _models = live_proof._audit_attempts(
        case_id,
        attempts,
        contract=None,
    )

    assert counts == {"stage1": 1, "property_resolution": 2, "stage2": 1}


def test_r1_live_attempt_audit_rejects_rank_regression_without_round_contract(
) -> None:
    with pytest.raises(ValueError, match="LIVE_ATTEMPT_STAGE_ORDER_INVALID"):
        _audit(_r1_add_detail_attempts())


def test_r1_live_attempt_audit_requires_lineage_on_second_stage1_round(
) -> None:
    attempts = _r1_add_detail_attempts()
    attempts[2].pop("lineage")

    with pytest.raises(
        ValueError,
        match="LIVE_ATTEMPT_ROUND_LINEAGE_INVALID",
    ):
        _audit(attempts, expected_rounds=R1_ADD_DETAIL_ROUNDS)


def test_r1_live_attempt_audit_rejects_swapped_round_lineage(
) -> None:
    attempts = _r1_add_detail_attempts()
    for attempt in attempts[:2]:
        attempt["lineage"] = "clarification-resume"
    for attempt in attempts[2:]:
        attempt["lineage"] = "initial"

    with pytest.raises(
        ValueError,
        match="LIVE_ATTEMPT_ROUND_LINEAGE_INVALID",
    ):
        _audit(attempts, expected_rounds=R1_ADD_DETAIL_ROUNDS)


def test_r1_live_attempt_audit_requires_each_new_round_to_start_at_one(
) -> None:
    attempts = _r1_add_detail_attempts()
    attempts[2]["stage_attempt"] = 2
    attempts[2]["correction_reason"] = "forged_cross_round_retry"

    with pytest.raises(
        ValueError,
        match="LIVE_ATTEMPT_STAGE_ATTEMPT_SEQUENCE_INVALID",
    ):
        _audit(attempts, expected_rounds=R1_ADD_DETAIL_ROUNDS)


def test_r1_live_attempt_audit_rejects_stage2_before_final_resolution(
) -> None:
    attempts = _r1_add_detail_attempts()
    attempts[-2:] = [attempts[-1], attempts[-2]]
    _rechain_attempts(attempts)

    with pytest.raises(
        ValueError,
        match="LIVE_ATTEMPT_ROUND_SEQUENCE_INVALID",
    ):
        _audit(attempts, expected_rounds=R1_ADD_DETAIL_ROUNDS)


def test_r1_live_attempt_audit_accepts_arbitrary_case_contract() -> None:
    result = _audit(_r1_attempts())

    assert result["case_id"] == "H3"
    assert result["attempt_count"] == 3
    assert result["transport_calls_by_stage"] == {
        "stage1": 1,
        "property_resolution": 1,
        "stage2": 1,
    }
    assert result["provider_models"] == [
        {
            "provider": "deepseek-openai-compatible",
            "model": "deepseek-v4-flash",
        }
    ]


@pytest.mark.parametrize("stage", ["stage1", "stage2"])
def test_r1_live_attempt_audit_rejects_profile_identity_drift(stage: str) -> None:
    attempts = _r1_attempts()
    attempt = next(item for item in attempts if item["stage"] == stage)
    attempt["profile_ids"] = ["wrong.profile"]

    with pytest.raises(ValueError, match="LIVE_ATTEMPT_PROFILE_ROUTING_MISMATCH"):
        _audit(attempts)


def test_r1_live_attempt_audit_rejects_stage15_template_drift() -> None:
    attempts = _r1_attempts()
    attempt = next(
        item for item in attempts if item["stage"] == "property_resolution"
    )
    attempt["template_hash"] = SHA_A

    with pytest.raises(ValueError, match="LIVE_ATTEMPT_TEMPLATE_HASH_REQUIRED"):
        _audit(attempts)


@pytest.mark.parametrize("source", ["request", "metadata"])
def test_r1_live_attempt_audit_rejects_thinking_mode_drift(source: str) -> None:
    attempts = _r1_attempts()
    attempt = attempts[0]
    if source == "request":
        attempt["request"]["extra_body"]["thinking"] = {"type": "disabled"}
        attempt["request_sha256"] = _canonical_sha256(attempt["request"])
    else:
        attempt["metadata"]["request_configuration"]["thinking"] = {
            "type": "disabled"
        }

    with pytest.raises(
        ValueError, match="LIVE_ATTEMPT_THINKING_CONFIGURATION_INVALID"
    ):
        _audit(attempts)


@pytest.mark.parametrize("tamper", ["fallback", "private"])
def test_r1_live_attempt_audit_rejects_non_live_provenance(tamper: str) -> None:
    attempts = _r1_attempts()
    if tamper == "fallback":
        attempts[0]["fallback_flags"]["synthetic"] = True
        expected = "LIVE_ATTEMPT_FALLBACK_FLAG"
    else:
        attempts[0]["private_evidence_detected"] = True
        expected = "LIVE_ATTEMPT_TRANSPORT_INVALID"

    with pytest.raises(ValueError, match=expected):
        _audit(attempts)


@pytest.mark.parametrize("tamper", ["ordinal", "parent"])
def test_r1_live_attempt_audit_rejects_lineage_drift(tamper: str) -> None:
    attempts = _r1_attempts()
    if tamper == "ordinal":
        attempts[1]["ordinal"] = 2
        expected = "LIVE_ATTEMPT_ORDINAL_MISMATCH"
    else:
        attempts[1]["parent_attempt_id"] = "H3:stage1:999"
        expected = "LIVE_ATTEMPT_PARENT_MISMATCH"

    with pytest.raises(ValueError, match=expected):
        _audit(attempts)


def test_r1_live_attempt_audit_accepts_a_hash_chained_stage_retry() -> None:
    attempts = _r1_attempts()
    stage1_retry = deepcopy(attempts[0])
    stage1_retry.update(
        {
            "attempt_id": "H3:stage1:002",
            "parent_attempt_id": attempts[0]["attempt_id"],
            "ordinal": 2,
            "stage_attempt": 2,
            "correction_reason": "schema_retry",
        }
    )
    attempts.insert(1, stage1_retry)
    attempts[2]["parent_attempt_id"] = stage1_retry["attempt_id"]

    result = _audit(attempts)

    assert result["attempt_count"] == 4
    assert result["transport_calls_by_stage"] == {
        "stage1": 2,
        "property_resolution": 1,
        "stage2": 1,
    }


def _rechain_attempts(attempts: list[dict[str, Any]]) -> None:
    ordinals = {"stage1": 0, "property_resolution": 0, "stage2": 0}
    parent: str | None = None
    for attempt in attempts:
        stage = str(attempt["stage"])
        ordinals[stage] += 1
        attempt["ordinal"] = ordinals[stage]
        attempt["attempt_id"] = (
            f"{attempt['case_id']}:{stage}:{ordinals[stage]:03d}"
        )
        attempt["parent_attempt_id"] = parent
        parent = str(attempt["attempt_id"])


def test_r1_live_attempt_audit_rejects_cross_stage_reordering() -> None:
    attempts = _r1_attempts()
    attempts = [attempts[0], attempts[2], attempts[1]]
    _rechain_attempts(attempts)

    with pytest.raises(ValueError, match="LIVE_ATTEMPT_STAGE_ORDER_INVALID"):
        _audit(attempts)


@pytest.mark.parametrize("stage", ["stage1", "property_resolution", "stage2"])
def test_r1_live_attempt_audit_requires_each_stage_chain_to_start_at_one(
    stage: str,
) -> None:
    attempts = _r1_attempts()
    attempt = next(item for item in attempts if item["stage"] == stage)
    attempt["stage_attempt"] = 2
    attempt["correction_reason"] = "forged_retry"

    with pytest.raises(
        ValueError,
        match="LIVE_ATTEMPT_STAGE_ATTEMPT_SEQUENCE_INVALID",
    ):
        _audit(attempts)


def test_r1_live_attempt_audit_rejects_a_stage_retry_gap() -> None:
    attempts = _r1_attempts()
    stage1_retry = deepcopy(attempts[0])
    stage1_retry.update(
        {
            "attempt_id": "H3:stage1:003",
            "parent_attempt_id": attempts[0]["attempt_id"],
            "ordinal": 2,
            "stage_attempt": 3,
            "correction_reason": "forged_retry_gap",
        }
    )
    attempts.insert(1, stage1_retry)
    _rechain_attempts(attempts)

    with pytest.raises(
        ValueError,
        match="LIVE_ATTEMPT_STAGE_ATTEMPT_SEQUENCE_INVALID",
    ):
        _audit(attempts)


def test_r1_live_attempt_audit_rejects_more_than_two_stage15_attempts_per_claim(
) -> None:
    attempts = _r1_attempts()
    first = attempts[1]
    second = deepcopy(first)
    second.update(
        {
            "attempt_id": "H3:property_resolution:002",
            "stage_attempt": 2,
            "correction_reason": "schema_retry",
        }
    )
    third = deepcopy(first)
    third.update(
        {
            "attempt_id": "H3:property_resolution:003",
            "stage_attempt": 3,
            "correction_reason": "schema_retry",
        }
    )
    attempts[1:2] = [first, second, third]
    _rechain_attempts(attempts)

    with pytest.raises(ValueError, match="LIVE_ATTEMPT_STAGE15_RETRY_EXHAUSTED"):
        _audit(attempts)


def test_r1_live_attempt_audit_allows_a_second_stage15_claim_to_restart_at_one(
) -> None:
    attempts = _r1_attempts()
    first = attempts[1]
    retry = deepcopy(first)
    retry.update(
        {
            "attempt_id": "H3:property_resolution:002",
            "stage_attempt": 2,
            "correction_reason": "schema_retry",
        }
    )
    second_claim = deepcopy(first)
    second_claim.update(
        {
            "attempt_id": "H3:property_resolution:003",
            "stage_attempt": 1,
            "correction_reason": None,
        }
    )
    attempts[1:2] = [first, retry, second_claim]
    _rechain_attempts(attempts)

    result = _audit(attempts)

    assert result["transport_calls_by_stage"]["property_resolution"] == 3
