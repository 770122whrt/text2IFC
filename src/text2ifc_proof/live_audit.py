"""Independent retained live-transcript audit, without curator/runner imports.

Frozen case definitions and audit functions are shared with the live runner.
This module performs no Provider call and does not grant live admission.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from text2ifc_agent.prompt_registry import load_prompt_registry
from text2ifc_ifc_repair.prompt_profiles import select_prompt_profiles
from text2ifc_ifc_repair.property_resolution_stage import (
    TEMPLATE_ID as PROPERTY_RESOLUTION_TEMPLATE_ID,
)

COMPLETE_REQUEST = (
    'On the IFC Building Storey named "Level 1", add one horizontal straight '
    "rectangular Beam with center axis from (120000, 120000, 3000) mm to "
    "(126000, 120000, 3000) mm and a rectangular section 300 mm wide and "
    "500 mm high. On the same Storey, add one vertical straight rectangular "
    "Column with center-axis base (123000, 124000, 0) mm and top "
    "(123000, 124000, 3000) mm, a section 400 mm wide and 600 mm deep, and "
    "local width direction (0, 1). Create both in one atomic ChangeSet, "
    "generate dedicated structural Types, state that the Beam is load "
    "bearing, and state that the Column is load bearing."
)


CLARIFICATION_REQUEST = (
    'On the IFC Building Storey named "Level 1", add one vertical straight '
    "rectangular Column with center-axis base (120000, 120000, 0) mm and top "
    "(120000, 120000, 6000) mm, a section 400 mm wide and 600 mm deep, and "
    "local width direction (0, 1). Set its natural-language property "
    '"load bearing status or external status" to true, but do not choose '
    "between those two meanings without clarification."
)


CLARIFICATION_PROPERTY_IDENTITY = (
    "ifc2x3:Pset_ColumnCommon.LoadBearing"
)


WINDOW_SEMANTIC_REQUEST = (
    'For the IfcWindow with GlobalId "1PkWQ2IbXBH9Ib7VGdBY7r", set '
    "外窗=true on this occurrence only. Do not change its Type or any "
    "other Window."
)


PROGRAM_GUARD_REQUEST = (
    'On the IFC Building Storey named "Level 1", add a straight rectangular '
    "Beam and attach a structural analysis node; structural analysis "
    "relationships are outside this operation contract."
)


PROGRAM_GUARD_REASON = "STRUCTURAL_ANALYSIS_UNSUPPORTED"


class LiveCase:
    """One fixed public live case; intentionally simple for importlib seams."""

    __slots__ = (
        "case_id",
        "request",
        "feedback",
        "feedback_kind",
        "expect_program_guard",
    )

    def __init__(
        self,
        *,
        case_id: str,
        request: str,
        feedback: str | None = None,
        feedback_kind: str | None = None,
        expect_program_guard: bool = False,
    ) -> None:
        if not case_id or not request.strip():
            raise ValueError("LIVE_CASE_ID_AND_REQUEST_REQUIRED")
        self.case_id = case_id
        self.request = request
        self.feedback = feedback
        self.expect_program_guard = bool(expect_program_guard)
        if feedback is None:
            if feedback_kind is not None:
                raise ValueError("LIVE_CASE_FEEDBACK_KIND_WITHOUT_FEEDBACK")
            self.feedback_kind = None
        else:
            resolved_kind = feedback_kind or "add_detail"
            if resolved_kind not in {"add_detail", "select_candidate"}:
                raise ValueError("LIVE_CASE_FEEDBACK_KIND_UNSUPPORTED")
            self.feedback_kind = resolved_kind


DEFAULT_CASES = (
    LiveCase(case_id="complete", request=COMPLETE_REQUEST),
    LiveCase(
        case_id="clarification-resume",
        request=CLARIFICATION_REQUEST,
        feedback=CLARIFICATION_PROPERTY_IDENTITY,
        feedback_kind="select_candidate",
    ),
    LiveCase(
        case_id="window-semantic-canary",
        request=WINDOW_SEMANTIC_REQUEST,
    ),
    LiveCase(
        case_id="program-guard",
        request=PROGRAM_GUARD_REQUEST,
        expect_program_guard=True,
    ),
)


LIVE_UAT_SCHEMA = "text2ifc/phase12-live-uat/0.1"


LIVE_EVIDENCE_MODE = "live"


LIVE_PROVIDER = "deepseek-openai-compatible"


SUCCESS_CASE_IDS = ("complete", "clarification-resume")


SEMANTIC_CANARY_CASE_ID = "window-semantic-canary"


PROGRAM_GUARD_CASE_ID = "program-guard"


REQUIRED_CASE_IDS = (
    *SUCCESS_CASE_IDS,
    SEMANTIC_CANARY_CASE_ID,
    PROGRAM_GUARD_CASE_ID,
)


EXPECTED_STAGE1_PROFILES = frozenset(
    {
        "beam.add.v0.3",
        "column.add.v0.3",
        "door.add-with-opening.v0.2",
        "door.fill-existing-opening.v0.2",
        "occurrence.set-properties",
        "opening.add-to-wall",
        "window.add-with-opening",
    }
)


EXPECTED_SELECTED_PROFILES = {
    "complete": frozenset(
        {"beam.add.stage2.v0.1", "column.add.stage2.v0.1"}
    ),
    "clarification-resume": frozenset({"column.add.stage2.v0.1"}),
    "window-semantic-canary": frozenset({"occurrence.set-properties"}),
    "program-guard": frozenset({"beam.add.stage2.v0.1"}),
}


HISTORICAL_SELECTED_PROFILES = {
    "complete": frozenset({"beam.add.v0.3", "column.add.v0.3"}),
    "clarification-resume": frozenset({"column.add.v0.3"}),
    "window-semantic-canary": frozenset({"occurrence.set-properties"}),
    "program-guard": frozenset({"beam.add.v0.3"}),
}


PROPERTY_RESOLUTION_TEMPLATE_HASH = str(
    load_prompt_registry()[PROPERTY_RESOLUTION_TEMPLATE_ID]["sha256"]
)


FORBIDDEN_FALLBACK_FLAGS = frozenset(
    {"cached", "hand_authored", "prerecorded", "synthetic"}
)


def _canonical_sha256(value: Any) -> str:
    rendered = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _text_sha256(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _valid_sha256(value: Any) -> bool:
    text = str(value or "")
    normalized = text.removeprefix("sha256:").casefold()
    return len(normalized) == 64 and all(
        character in "0123456789abcdef" for character in normalized
    )


def _require_text(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(code)
    return value


def _stage2_response_schema(response: Mapping[str, Any]) -> str:
    content = response.get("content")
    if not isinstance(content, str):
        choices = response.get("choices")
        if (
            not isinstance(choices, list)
            or len(choices) != 1
            or not isinstance(choices[0], Mapping)
        ):
            raise ValueError("LIVE_ATTEMPT_STAGE2_RESPONSE_INVALID")
        message = choices[0].get("message")
        if not isinstance(message, Mapping):
            raise ValueError("LIVE_ATTEMPT_STAGE2_RESPONSE_INVALID")
        content = message.get("content")
    if not isinstance(content, str):
        raise ValueError("LIVE_ATTEMPT_STAGE2_RESPONSE_INVALID")
    try:
        document = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError("LIVE_ATTEMPT_STAGE2_RESPONSE_INVALID") from error
    if not isinstance(document, Mapping):
        raise ValueError("LIVE_ATTEMPT_STAGE2_RESPONSE_INVALID")
    return _require_text(
        document.get("schema_version"),
        "LIVE_ATTEMPT_STAGE2_SCHEMA_REQUIRED",
    )


def _expected_plan07_stage2_profiles(
    case_id: str,
    schema_version: str,
) -> frozenset[str]:
    if schema_version == "text2ifc/ifc-repair-changeset-draft/0.3":
        return EXPECTED_SELECTED_PROFILES[case_id]
    if schema_version == "text2ifc/ifc-repair-changeset-draft/0.2":
        return HISTORICAL_SELECTED_PROFILES[case_id]
    raise ValueError("LIVE_ATTEMPT_STAGE2_SCHEMA_UNREVIEWED")


def _profile_identity_from_records(
    raw_profiles: Any,
    *,
    error_code: str,
) -> dict[str, list[str]]:
    if (
        not isinstance(raw_profiles, Sequence)
        or isinstance(raw_profiles, (str, bytes))
        or not raw_profiles
    ):
        raise ValueError(error_code)
    profile_ids: list[str] = []
    profile_versions: list[str] = []
    profile_hashes: list[str] = []
    for raw_profile in raw_profiles:
        if not isinstance(raw_profile, Mapping):
            raise ValueError(error_code)
        profile_id = _require_text(raw_profile.get("profile_id"), error_code)
        profile_version = _require_text(
            raw_profile.get("profile_version"), error_code
        )
        profile_hash = str(raw_profile.get("profile_hash") or "")
        if not _valid_sha256(profile_hash):
            raise ValueError(error_code)
        profile_ids.append(profile_id)
        profile_versions.append(profile_version)
        profile_hashes.append(profile_hash)
    if len(set(profile_ids)) != len(profile_ids):
        raise ValueError(error_code)
    return {
        "profile_ids": profile_ids,
        "profile_versions": profile_versions,
        "profile_hashes": profile_hashes,
    }


def _stage2_identity_from_selection(raw_selection: Any) -> dict[str, Any]:
    error_code = "LIVE_ATTEMPT_EXPECTED_STAGE2_CONTRACT_INVALID"
    if not isinstance(raw_selection, Mapping):
        raise ValueError(error_code)
    identity = _profile_identity_from_records(
        raw_selection.get("profiles"),
        error_code=error_code,
    )
    if (
        raw_selection.get("profile_ids") != identity["profile_ids"]
        or raw_selection.get("profile_hashes") != identity["profile_hashes"]
    ):
        raise ValueError(error_code)
    few_shot_ids = raw_selection.get("few_shot_ids")
    few_shot_hashes = raw_selection.get("few_shot_hashes")
    if (
        not isinstance(few_shot_ids, list)
        or not isinstance(few_shot_hashes, list)
        or len(few_shot_ids) != len(few_shot_hashes)
        or len(set(map(str, few_shot_ids))) != len(few_shot_ids)
        or any(not isinstance(value, str) or not value for value in few_shot_ids)
        or any(not _valid_sha256(value) for value in few_shot_hashes)
    ):
        raise ValueError(error_code)
    return {
        **identity,
        "few_shot_bindings": dict(
            zip(few_shot_ids, few_shot_hashes, strict=True)
        ),
    }


def _attempt_round_contract(
    raw_rounds: Sequence[Mapping[str, Any]] | None,
    *,
    property_resolution_expected: bool,
    stage2_expected: bool,
) -> list[dict[str, Any]] | None:
    if raw_rounds is None:
        return None
    if (
        not isinstance(raw_rounds, Sequence)
        or isinstance(raw_rounds, (str, bytes))
        or not raw_rounds
    ):
        raise ValueError("LIVE_ATTEMPT_ROUND_CONTRACT_INVALID")
    stage_ranks = {"stage1": 0, "property_resolution": 1, "stage2": 2}
    normalized: list[dict[str, Any]] = []
    seen_lineages: set[str] = set()
    for index, raw_round in enumerate(raw_rounds):
        if not isinstance(raw_round, Mapping) or set(raw_round) != {
            "lineage",
            "stages",
        }:
            raise ValueError("LIVE_ATTEMPT_ROUND_CONTRACT_INVALID")
        lineage = _require_text(
            raw_round.get("lineage"),
            "LIVE_ATTEMPT_ROUND_CONTRACT_INVALID",
        )
        stages = raw_round.get("stages")
        if (
            lineage in seen_lineages
            or not isinstance(stages, list)
            or not stages
            or (index == 0 and stages[0] != "stage1")
            or any(stage not in stage_ranks for stage in stages)
            or len(stages) != len(set(stages))
            or [stage_ranks[stage] for stage in stages]
            != sorted(stage_ranks[stage] for stage in stages)
        ):
            raise ValueError("LIVE_ATTEMPT_ROUND_CONTRACT_INVALID")
        if "stage2" in stages and (
            index != len(raw_rounds) - 1
            or stages[-1] != "stage2"
            or (
                property_resolution_expected
                and stages[-2:] != ["property_resolution", "stage2"]
            )
        ):
            raise ValueError("LIVE_ATTEMPT_ROUND_CONTRACT_INVALID")
        seen_lineages.add(lineage)
        normalized.append({"lineage": lineage, "stages": list(stages)})
    configured_stages = {"stage1"}
    if property_resolution_expected:
        configured_stages.add("property_resolution")
    if stage2_expected:
        configured_stages.add("stage2")
    offered_stages = {
        stage for round_contract in normalized for stage in round_contract["stages"]
    }
    if offered_stages != configured_stages:
        raise ValueError("LIVE_ATTEMPT_ROUND_CONTRACT_INVALID")
    if stage2_expected and normalized[-1]["stages"][-1] != "stage2":
        raise ValueError("LIVE_ATTEMPT_ROUND_CONTRACT_INVALID")
    return normalized


def audit_live_attempts(
    *,
    case_id: str,
    raw_attempts: Any,
    expected_stage1_profiles: Sequence[Mapping[str, Any]],
    expected_stage2_selection: Mapping[str, Any] | None,
    expected_property_resolution_template: Mapping[str, Any] | None,
    expected_provider: str,
    expected_model: str,
    expected_evidence_mode: str,
    expected_thinking: Mapping[str, Any],
    expected_rounds: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Audit an arbitrary genuine case against caller-supplied frozen identities.

    Plan 07 retains its legacy private contract through ``_audit_attempts``.
    This public seam lets later frozen milestones supply their own immutable
    prompt identities without teaching the Phase 12 curator new case IDs.
    """

    normalized_case_id = _require_text(case_id, "LIVE_ATTEMPT_CASE_REQUIRED")
    stage1_identity = _profile_identity_from_records(
        expected_stage1_profiles,
        error_code="LIVE_ATTEMPT_EXPECTED_STAGE1_CONTRACT_INVALID",
    )
    stage2_identity = (
        None
        if expected_stage2_selection is None
        else _stage2_identity_from_selection(expected_stage2_selection)
    )
    if expected_property_resolution_template is None:
        stage15_identity = None
    else:
        template_id = _require_text(
            expected_property_resolution_template.get("template_id"),
            "LIVE_ATTEMPT_EXPECTED_TEMPLATE_CONTRACT_INVALID",
        )
        template_hash = str(
            expected_property_resolution_template.get("template_hash") or ""
        )
        if not _valid_sha256(template_hash):
            raise ValueError("LIVE_ATTEMPT_EXPECTED_TEMPLATE_CONTRACT_INVALID")
        stage15_identity = {
            "template_id": template_id,
            "template_hash": template_hash,
        }
    contract = {
        "stage1": stage1_identity,
        "stage2": stage2_identity,
        "property_resolution": stage15_identity,
        "provider": _require_text(
            expected_provider, "LIVE_ATTEMPT_EXPECTED_PROVIDER_REQUIRED"
        ),
        "model": _require_text(
            expected_model, "LIVE_ATTEMPT_EXPECTED_MODEL_REQUIRED"
        ),
        "evidence_mode": _require_text(
            expected_evidence_mode,
            "LIVE_ATTEMPT_EXPECTED_EVIDENCE_MODE_REQUIRED",
        ),
        "thinking": dict(expected_thinking),
    }
    if not contract["thinking"]:
        raise ValueError("LIVE_ATTEMPT_EXPECTED_THINKING_REQUIRED")
    contract["rounds"] = _attempt_round_contract(
        expected_rounds,
        property_resolution_expected=stage15_identity is not None,
        stage2_expected=stage2_identity is not None,
    )
    attempts, counts, provider_models = _audit_attempts(
        normalized_case_id,
        raw_attempts,
        contract=contract,
    )
    return {
        "case_id": normalized_case_id,
        "attempt_count": len(attempts),
        "transport_calls": len(attempts),
        "transport_calls_by_stage": counts,
        "provider_models": [
            {"provider": provider, "model": model}
            for provider, model in sorted(provider_models)
        ],
    }


def _audit_attempts(
    case_id: str,
    raw_attempts: Any,
    *,
    contract: Mapping[str, Any] | None = None,
) -> tuple[list[Mapping[str, Any]], dict[str, int], set[tuple[str, str]]]:
    if not isinstance(raw_attempts, list) or not raw_attempts:
        raise ValueError("LIVE_CASE_ATTEMPTS_REQUIRED")
    attempts: list[Mapping[str, Any]] = []
    ordinals = {"stage1": 0, "property_resolution": 0, "stage2": 0}
    stage_ranks = {"stage1": 0, "property_resolution": 1, "stage2": 2}
    previous: str | None = None
    previous_stage: str | None = None
    previous_stage_attempt: int | None = None
    previous_lineage: str | None = None
    previous_stage_rank = -1
    round_contract = (
        None if contract is None else contract.get("rounds")
    )
    round_index = 0
    round_stage_index = 0
    provider_models: set[tuple[str, str]] = set()
    seen_ids: set[str] = set()
    expected_evidence_mode = (
        LIVE_EVIDENCE_MODE
        if contract is None
        else str(contract["evidence_mode"])
    )
    expected_provider = (
        LIVE_PROVIDER if contract is None else str(contract["provider"])
    )
    expected_model = None if contract is None else str(contract["model"])
    for raw in raw_attempts:
        if not isinstance(raw, Mapping):
            raise ValueError("LIVE_ATTEMPT_OBJECT_REQUIRED")
        stage = str(raw.get("stage") or "")
        if stage not in ordinals:
            raise ValueError("LIVE_ATTEMPT_STAGE_INVALID")
        stage_rank = stage_ranks[stage]
        if round_contract is None:
            if stage_rank < previous_stage_rank:
                raise ValueError("LIVE_ATTEMPT_STAGE_ORDER_INVALID")
        else:
            assert isinstance(round_contract, list)
            if (
                previous_lineage is not None
                and raw.get("lineage") != previous_lineage
            ):
                current_stages = round_contract[round_index]["stages"]
                if round_stage_index != len(current_stages) - 1:
                    raise ValueError("LIVE_ATTEMPT_ROUND_SEQUENCE_INVALID")
                round_index += 1
                round_stage_index = 0
                previous_stage = None
                previous_stage_attempt = None
            if round_index >= len(round_contract):
                raise ValueError("LIVE_ATTEMPT_ROUND_SEQUENCE_INVALID")
            expected_round = round_contract[round_index]
            if raw.get("lineage") != expected_round["lineage"]:
                raise ValueError("LIVE_ATTEMPT_ROUND_LINEAGE_INVALID")
            if previous_stage is not None and stage != previous_stage:
                round_stage_index += 1
            expected_stages = expected_round["stages"]
            if (
                round_stage_index >= len(expected_stages)
                or stage != expected_stages[round_stage_index]
            ):
                raise ValueError("LIVE_ATTEMPT_ROUND_SEQUENCE_INVALID")
        ordinals[stage] += 1
        if raw.get("ordinal") != ordinals[stage]:
            raise ValueError("LIVE_ATTEMPT_ORDINAL_MISMATCH")
        attempt_id = str(raw.get("attempt_id") or "")
        expected_id = f"{case_id}:{stage}:{ordinals[stage]:03d}"
        if attempt_id != expected_id or attempt_id in seen_ids:
            raise ValueError("LIVE_ATTEMPT_ID_MISMATCH")
        seen_ids.add(attempt_id)
        if raw.get("case_id") != case_id:
            raise ValueError("LIVE_ATTEMPT_CASE_MISMATCH")
        if raw.get("parent_attempt_id") != previous:
            raise ValueError("LIVE_ATTEMPT_PARENT_MISMATCH")
        previous = attempt_id
        stage_attempt = raw.get("stage_attempt")
        if not isinstance(stage_attempt, int) or stage_attempt < 1:
            raise ValueError("LIVE_ATTEMPT_STAGE_ATTEMPT_INVALID")
        if stage == "property_resolution" and stage_attempt > 2:
            raise ValueError("LIVE_ATTEMPT_STAGE15_RETRY_EXHAUSTED")
        correction = raw.get("correction_reason")
        if stage_attempt > 1 and (
            not isinstance(correction, str) or not correction.strip()
        ):
            raise ValueError("LIVE_ATTEMPT_CORRECTION_REASON_REQUIRED")
        if stage != previous_stage:
            if stage_attempt != 1:
                raise ValueError(
                    "LIVE_ATTEMPT_STAGE_ATTEMPT_SEQUENCE_INVALID"
                )
        elif stage == "property_resolution":
            assert previous_stage_attempt is not None
            if (
                stage_attempt != 1
                and stage_attempt != previous_stage_attempt + 1
            ):
                raise ValueError(
                    "LIVE_ATTEMPT_STAGE_ATTEMPT_SEQUENCE_INVALID"
                )
        else:
            assert previous_stage_attempt is not None
            if stage_attempt != previous_stage_attempt + 1:
                raise ValueError(
                    "LIVE_ATTEMPT_STAGE_ATTEMPT_SEQUENCE_INVALID"
                )
        previous_stage = stage
        previous_stage_attempt = stage_attempt
        previous_lineage = str(raw.get("lineage") or "")
        previous_stage_rank = stage_rank
        if contract is not None and contract.get(stage) is None:
            raise ValueError("LIVE_ATTEMPT_STAGE_NOT_EXPECTED")
        if (
            raw.get("evidence_class") != expected_evidence_mode
            or raw.get("http_status") != 200
            or raw.get("error") is not None
            or raw.get("private_evidence_detected") is not False
        ):
            raise ValueError("LIVE_ATTEMPT_TRANSPORT_INVALID")
        fallback = raw.get("fallback_flags")
        if (
            not isinstance(fallback, Mapping)
            or set(fallback) != FORBIDDEN_FALLBACK_FLAGS
            or any(fallback[key] is not False for key in FORBIDDEN_FALLBACK_FLAGS)
        ):
            raise ValueError("LIVE_ATTEMPT_FALLBACK_FLAG")
        provider = _require_text(
            raw.get("provider"), "LIVE_ATTEMPT_PROVIDER_REQUIRED"
        )
        if provider != expected_provider:
            raise ValueError("LIVE_ATTEMPT_PROVIDER_IDENTITY_INVALID")
        model = _require_text(raw.get("model"), "LIVE_ATTEMPT_MODEL_REQUIRED")
        if expected_model is not None and model != expected_model:
            raise ValueError("LIVE_ATTEMPT_MODEL_IDENTITY_INVALID")
        provider_models.add((provider, model))
        usage = raw.get("usage")
        if not isinstance(usage, Mapping) or not usage:
            raise ValueError("LIVE_ATTEMPT_USAGE_REQUIRED")
        if any(
            not isinstance(usage.get(key), int) or int(usage[key]) < 0
            for key in ("prompt_tokens", "completion_tokens", "total_tokens")
        ) or int(usage["total_tokens"]) < 1:
            raise ValueError("LIVE_ATTEMPT_USAGE_REQUIRED")
        request = raw.get("request")
        response = raw.get("response")
        if request is None or response is None:
            raise ValueError("LIVE_ATTEMPT_RAW_RESPONSE_REQUIRED")
        if not _valid_sha256(raw.get("raw_request_sha256")) or not _valid_sha256(
            raw.get("raw_response_sha256")
        ):
            raise ValueError("LIVE_ATTEMPT_RAW_HASH_REQUIRED")
        try:
            request_hash = _canonical_sha256(request)
            response_hash = _canonical_sha256(response)
        except (TypeError, ValueError) as error:
            raise ValueError("LIVE_ATTEMPT_REDACTED_PAYLOAD_INVALID") from error
        if (
            raw.get("request_sha256") != request_hash
            or raw.get("response_sha256") != response_hash
        ):
            raise ValueError("LIVE_ATTEMPT_REDACTED_HASH_MISMATCH")
        metadata = raw.get("metadata")
        if not isinstance(metadata, Mapping):
            raise ValueError("LIVE_ATTEMPT_METADATA_REQUIRED")
        _require_text(
            metadata.get("response_id"), "LIVE_ATTEMPT_RESPONSE_ID_REQUIRED"
        )
        if (
            metadata.get("provider") != provider
            or metadata.get("model") != model
            or metadata.get("evidence_class") != expected_evidence_mode
            or metadata.get("usage") != usage
            or not isinstance(metadata.get("transport_attempts"), int)
            or int(metadata["transport_attempts"]) < 1
        ):
            raise ValueError("LIVE_ATTEMPT_METADATA_INVALID")
        if contract is not None:
            request_configuration = metadata.get("request_configuration")
            request_extra_body = (
                request.get("extra_body") if isinstance(request, Mapping) else None
            )
            expected_thinking = contract["thinking"]
            if (
                not isinstance(request, Mapping)
                or request.get("model") != expected_model
                or not isinstance(request_extra_body, Mapping)
                or request_extra_body.get("thinking") != expected_thinking
                or not isinstance(request_configuration, Mapping)
                or request_configuration.get("thinking") != expected_thinking
            ):
                raise ValueError("LIVE_ATTEMPT_THINKING_CONFIGURATION_INVALID")
            if expected_thinking.get("type") == "enabled":
                temperature = request_configuration.get("temperature")
                if (
                    not isinstance(temperature, Mapping)
                    or temperature.get("effective") is not False
                ):
                    raise ValueError(
                        "LIVE_ATTEMPT_THINKING_CONFIGURATION_INVALID"
                    )
        profile_ids = raw.get("profile_ids")
        profile_versions = raw.get("profile_versions")
        profile_hashes = raw.get("profile_hashes")
        if stage == "property_resolution":
            expected_template = (
                {
                    "template_id": PROPERTY_RESOLUTION_TEMPLATE_ID,
                    "template_hash": PROPERTY_RESOLUTION_TEMPLATE_HASH,
                }
                if contract is None
                else contract["property_resolution"]
            )
            assert isinstance(expected_template, Mapping)
            if raw.get("template_id") != expected_template["template_id"]:
                raise ValueError("LIVE_ATTEMPT_TEMPLATE_ID_REQUIRED")
            if raw.get("template_hash") != expected_template["template_hash"]:
                raise ValueError("LIVE_ATTEMPT_TEMPLATE_HASH_REQUIRED")
            if any(
                raw.get(key) not in (None, [])
                for key in (
                    "profile_ids",
                    "profile_versions",
                    "profile_hashes",
                    "few_shot_ids",
                    "few_shot_hashes",
                    "few_shot_bindings",
                )
            ):
                raise ValueError("LIVE_ATTEMPT_TEMPLATE_ROUTING_MISMATCH")
        else:
            if (
                not isinstance(profile_ids, list)
                or not profile_ids
                or not isinstance(profile_versions, list)
                or not profile_versions
                or not isinstance(profile_hashes, list)
                or not profile_hashes
                or any(not _valid_sha256(value) for value in profile_hashes)
            ):
                raise ValueError("LIVE_ATTEMPT_PROFILE_HASH_REQUIRED")
            if (
                len(profile_ids) != len(profile_versions)
                or len(profile_ids) != len(profile_hashes)
                or len(set(map(str, profile_ids))) != len(profile_ids)
            ):
                raise ValueError("LIVE_ATTEMPT_PROFILE_ROUTING_MISMATCH")
            if contract is None:
                if stage == "stage1":
                    expected_profile_generation = EXPECTED_STAGE1_PROFILES
                else:
                    if not isinstance(response, Mapping):
                        raise ValueError("LIVE_ATTEMPT_STAGE2_RESPONSE_INVALID")
                    expected_profile_generation = (
                        _expected_plan07_stage2_profiles(
                            case_id,
                            _stage2_response_schema(response),
                        )
                    )
                if frozenset(map(str, profile_ids)) != expected_profile_generation:
                    raise ValueError("LIVE_ATTEMPT_PROFILE_ROUTING_MISMATCH")
            else:
                expected_identity = contract[stage]
                assert isinstance(expected_identity, Mapping)
                if any(
                    raw.get(key) != expected_identity[key]
                    for key in (
                        "profile_ids",
                        "profile_versions",
                        "profile_hashes",
                    )
                ):
                    raise ValueError("LIVE_ATTEMPT_PROFILE_ROUTING_MISMATCH")
                if stage == "stage1" and any(
                    raw.get(key) not in (None, [])
                    for key in (
                        "few_shot_ids",
                        "few_shot_hashes",
                        "few_shot_bindings",
                    )
                ):
                    raise ValueError("LIVE_ATTEMPT_PROFILE_ROUTING_MISMATCH")
        if stage == "stage2":
            few_shot_binding_map = _few_shot_binding_map(
                raw.get("few_shot_bindings")
            )
            if contract is None:
                if not isinstance(response, Mapping):
                    raise ValueError("LIVE_ATTEMPT_STAGE2_RESPONSE_INVALID")
                expected_profile_generation = _expected_plan07_stage2_profiles(
                    case_id,
                    _stage2_response_schema(response),
                )
                expected_selection = select_prompt_profiles(
                    sorted(expected_profile_generation)
                ).to_dict()
                expected_few_shot_binding_map = dict(
                    zip(
                        expected_selection["few_shot_ids"],
                        expected_selection["few_shot_hashes"],
                        strict=True,
                    )
                )
                expected_versions = [
                    str(profile["profile_version"])
                    for profile in expected_selection["profiles"]
                ]
                expected_profile_ids = expected_selection["profile_ids"]
                expected_profile_hashes = expected_selection["profile_hashes"]
            else:
                expected_selection = contract["stage2"]
                assert isinstance(expected_selection, Mapping)
                expected_few_shot_binding_map = expected_selection[
                    "few_shot_bindings"
                ]
                expected_versions = expected_selection["profile_versions"]
                expected_profile_ids = expected_selection["profile_ids"]
                expected_profile_hashes = expected_selection["profile_hashes"]
            if few_shot_binding_map is None:
                raise ValueError("LIVE_ATTEMPT_FEW_SHOT_HASH_REQUIRED")
            if expected_few_shot_binding_map and not few_shot_binding_map:
                raise ValueError("LIVE_ATTEMPT_FEW_SHOT_HASH_REQUIRED")
            if (
                profile_ids != expected_profile_ids
                or profile_versions != expected_versions
                or profile_hashes != expected_profile_hashes
                or few_shot_binding_map != expected_few_shot_binding_map
            ):
                raise ValueError("LIVE_ATTEMPT_PROFILE_ROUTING_MISMATCH")
        attempts.append(raw)
    if round_contract is not None:
        assert isinstance(round_contract, list)
        if (
            round_index != len(round_contract) - 1
            or round_stage_index
            != len(round_contract[round_index]["stages"]) - 1
        ):
            raise ValueError("LIVE_ATTEMPT_ROUND_SEQUENCE_INVALID")
    if contract is not None and any(
        contract.get(stage) is not None and ordinals[stage] < 1
        for stage in ordinals
    ):
        raise ValueError("LIVE_ATTEMPT_STAGE_REQUIRED")
    return attempts, ordinals, provider_models


def _strict_success(final: Any) -> bool:
    if not isinstance(final, Mapping):
        return False
    strict = final.get("strict_reopen_verification")
    return bool(
        final.get("status") == "succeeded"
        and final.get("complete_repair_success") is True
        and final.get("successful_artifact_publishable") is True
        and isinstance(strict, Mapping)
        and strict.get("status") == "passed"
        and strict.get("l0_pass") is True
        and strict.get("l1_pass") is True
        and strict.get("l2_pass") is True
    )


def audit_live_uat_result(result: Mapping[str, Any]) -> dict[str, Any]:
    """Reconcile genuine live attempt evidence without trusting runner flags."""

    if result.get("schema_version") != LIVE_UAT_SCHEMA:
        raise ValueError("LIVE_UAT_SCHEMA_INVALID")
    if (
        result.get("status") != "passed"
        or result.get("evidence_mode") != LIVE_EVIDENCE_MODE
        or result.get("provider_evidence_mode") != LIVE_EVIDENCE_MODE
        or result.get("execution_mode") != "production_live"
        or result.get("runner_contract_eligible") is not True
    ):
        raise ValueError("LIVE_UAT_PRODUCTION_MODE_REQUIRED")
    if result.get("synthetic_fallback_used") is not False:
        raise ValueError("LIVE_SYNTHETIC_FALLBACK_NOT_FALSE")
    if (
        result.get("acceptance_eligible") is not False
        or result.get("proof_validation_status") != "pending_plan_12_14"
    ):
        raise ValueError("LIVE_PROOF_ACCEPTANCE_SELF_CLAIM")
    raw_cases = result.get("cases")
    if not isinstance(raw_cases, list) or [
        item.get("case_id") if isinstance(item, Mapping) else None
        for item in raw_cases
    ] != list(REQUIRED_CASE_IDS):
        raise ValueError("LIVE_CASE_MATRIX_INVALID")
    aggregate = {"stage1": 0, "property_resolution": 0, "stage2": 0}
    transport_calls = 0
    provider_models: set[tuple[str, str]] = set()
    for case in raw_cases:
        assert isinstance(case, Mapping)
        case_id = str(case["case_id"])
        if (
            case.get("status") != "passed"
            or case.get("contract_pass") is not True
            or case.get("live_evidence_pass") is not True
            or case.get("private_evidence_detected") is not False
            or case.get("synthetic_fallback_used") is not False
            or case.get("proof_acceptance_eligible") is not False
            or case.get("proof_validation_status") != "pending_plan_12_14"
        ):
            raise ValueError("LIVE_PROOF_ACCEPTANCE_SELF_CLAIM")
        frozen = _case_definition(case_id)
        if case.get("request_sha256") != _text_sha256(frozen.request) or case.get(
            "feedback_sha256"
        ) != (None if frozen.feedback is None else _text_sha256(frozen.feedback)):
            raise ValueError("LIVE_CASE_REQUEST_HASH_MISMATCH")
        attempts, counts, case_models = _audit_attempts(
            case_id, case.get("attempts")
        )
        if case.get("transport_calls") != len(attempts) or case.get(
            "transport_calls_by_stage"
        ) != counts:
            raise ValueError("LIVE_CASE_STAGE_COUNT_MISMATCH")
        transport_calls += len(attempts)
        for stage in aggregate:
            aggregate[stage] += counts[stage]
        provider_models.update(case_models)
        final = case.get("final")
        if case_id == "complete":
            if (
                not _strict_success(final)
                or counts
                != {"stage1": 1, "property_resolution": 2, "stage2": 1}
            ):
                raise ValueError("LIVE_SUCCESS_TERMINAL_INVALID")
            if any(item.get("lineage") != "initial" for item in attempts):
                raise ValueError("LIVE_COMPLETE_LINEAGE_INVALID")
        elif case_id == "clarification-resume":
            assert isinstance(final, Mapping)
            initial = final.get("initial")
            clarification = final.get("clarification")
            lineage = [item.get("lineage") for item in attempts]
            if (
                not _strict_success(final)
                or counts
                != {"stage1": 1, "property_resolution": 1, "stage2": 1}
                or lineage != [
                    "initial",
                    "initial",
                    "clarification-resume",
                ]
                or final.get("clarification_answer_applied") is not True
                or not isinstance(initial, Mapping)
                or initial.get("status") != "clarification_required"
                or initial.get("successful_artifact_publishable") is not False
                or not isinstance(clarification, Mapping)
                or not str(clarification.get("clarification_id") or "")
                or clarification.get("reason_code") != "property_resolution"
                or clarification.get("answer_modes")
                not in (
                    ["select_candidate", "cancel"],
                    ["select_candidate", "add_detail", "cancel"],
                )
            ):
                raise ValueError("LIVE_CLARIFICATION_LINEAGE_INVALID")
        elif case_id == SEMANTIC_CANARY_CASE_ID:
            if (
                not _strict_success(final)
                or counts
                != {"stage1": 1, "property_resolution": 1, "stage2": 1}
                or any(item.get("lineage") != "initial" for item in attempts)
            ):
                raise ValueError("LIVE_SEMANTIC_CANARY_INVALID")
        else:
            assert isinstance(final, Mapping)
            guard = final.get("program_guard_evidence")
            if (
                final.get("status") != "unsupported"
                or final.get("reason_code") != PROGRAM_GUARD_REASON
                or final.get("successful_artifact_publishable") is not False
                or counts
                != {"stage1": 1, "property_resolution": 0, "stage2": 0}
                or [item.get("lineage") for item in attempts] != ["initial"]
                or not isinstance(guard, Mapping)
                or guard.get("source_unchanged") is not True
                or guard.get("stage2_attempts") != 0
                or guard.get("candidate_output_paths") != []
                or guard.get("mutation_attempted") is not False
            ):
                raise ValueError("LIVE_PROGRAM_GUARD_INVALID")
    if result.get("transport_calls") != transport_calls or result.get(
        "transport_calls_by_stage"
    ) != aggregate:
        raise ValueError("LIVE_AGGREGATE_STAGE_COUNT_MISMATCH")
    expected_models = [
        {"provider": provider, "model": model}
        for provider, model in sorted(provider_models)
    ]
    if result.get("provider_models") != expected_models:
        raise ValueError("LIVE_PROVIDER_MODEL_AGGREGATE_MISMATCH")
    return {
        "schema_version": "text2ifc/phase12-live-transcript-audit/0.1",
        "status": "passed",
        "success_case_ids": list(SUCCESS_CASE_IDS),
        "semantic_canary_case_id": SEMANTIC_CANARY_CASE_ID,
        "program_guard_case_id": PROGRAM_GUARD_CASE_ID,
        "transport_calls": transport_calls,
        "transport_calls_by_stage": aggregate,
        "provider_models": expected_models,
    }


def _response_document(attempt: Mapping[str, Any]) -> dict[str, Any]:
    response = attempt.get("response")
    if not isinstance(response, Mapping):
        raise ValueError("LIVE_RESPONSE_DOCUMENT_MISSING")
    content: Any = response.get("content")
    if content is None:
        choices = response.get("choices")
        if isinstance(choices, list) and len(choices) == 1:
            choice = choices[0]
            if isinstance(choice, Mapping):
                message = choice.get("message")
                if isinstance(message, Mapping):
                    content = message.get("content")
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except json.JSONDecodeError as error:
            raise ValueError("LIVE_RESPONSE_DOCUMENT_INVALID") from error
    if not isinstance(content, dict):
        raise ValueError("LIVE_RESPONSE_DOCUMENT_MISSING")
    return content


def _bind_stage1(document: Mapping[str, Any], intent: Mapping[str, Any]) -> None:
    expected = {
        "operations": intent.get("operations", []),
        "semantic_bundles": intent.get("semantic_bundles", []),
        "provenance": intent.get("provenance", []),
    }
    actual = {key: document.get(key, []) for key in expected}
    if actual != expected:
        raise ValueError("LIVE_STAGE1_RESPONSE_ARTIFACT_MISMATCH")


def _bind_stage2(
    document: Mapping[str, Any], changeset: Mapping[str, Any]
) -> None:
    for key in (
        "base_model_fingerprint",
        "source_request_hash",
        "semantic_manifest_ref",
        "semantic_manifest_sha256",
        "scope",
    ):
        if document.get(key) != changeset.get(key):
            raise ValueError("LIVE_STAGE2_RESPONSE_ARTIFACT_MISMATCH")
    actual_operations = document.get("operations")
    expected_operations = changeset.get("operations")
    if not isinstance(actual_operations, list) or not isinstance(
        expected_operations, list
    ) or len(actual_operations) != len(expected_operations):
        raise ValueError("LIVE_STAGE2_RESPONSE_ARTIFACT_MISMATCH")
    expected_by_id = {
        str(item.get("operation_id")): item
        for item in expected_operations
        if isinstance(item, Mapping)
    }
    for actual in actual_operations:
        if not isinstance(actual, Mapping):
            raise ValueError("LIVE_STAGE2_RESPONSE_ARTIFACT_MISMATCH")
        expected = expected_by_id.get(str(actual.get("operation_id")))
        if expected is None or any(
            actual.get(key) != expected.get(key)
            for key in (
                "operation_id",
                "operation_type",
                "target",
                "parameters",
                "evidence_refs",
            )
        ):
            raise ValueError("LIVE_STAGE2_RESPONSE_ARTIFACT_MISMATCH")


def audit_live_artifact_binding(
    result: Mapping[str, Any],
    *,
    case_id: str,
    intent: Mapping[str, Any],
    provider_draft: Mapping[str, Any],
    changeset: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind final Provider response content to retained deterministic artifacts."""

    audit_live_uat_result(result)
    case = next(
        (
            item
            for item in result["cases"]
            if isinstance(item, Mapping) and item.get("case_id") == case_id
        ),
        None,
    )
    if case_id not in SUCCESS_CASE_IDS or not isinstance(case, Mapping):
        raise ValueError("LIVE_SUCCESS_CASE_REQUIRED")
    attempts = case.get("attempts")
    assert isinstance(attempts, list)
    stage1 = [item for item in attempts if item.get("stage") == "stage1"]
    stage2 = [item for item in attempts if item.get("stage") == "stage2"]
    if not stage1 or not stage2:
        raise ValueError("LIVE_SUCCESS_STAGE_RESPONSE_MISSING")
    _bind_stage1(_response_document(stage1[-1]), intent)
    _bind_stage2(_response_document(stage2[-1]), provider_draft)
    for key in (
        "base_model_fingerprint",
        "source_request_hash",
        "semantic_manifest_ref",
        "semantic_manifest_sha256",
        "scope",
    ):
        if provider_draft.get(key) != changeset.get(key):
            raise ValueError("LIVE_BOUND_CHANGESET_AUTHORITY_MISMATCH")
    draft_operations = provider_draft.get("operations")
    bound_operations = changeset.get("operations")
    if not isinstance(draft_operations, list) or not isinstance(
        bound_operations, list
    ) or len(draft_operations) != len(bound_operations):
        raise ValueError("LIVE_BOUND_CHANGESET_AUTHORITY_MISMATCH")
    for draft, bound in zip(draft_operations, bound_operations, strict=True):
        if not isinstance(draft, Mapping) or not isinstance(bound, Mapping) or any(
            draft.get(key) != bound.get(key)
            for key in (
                "operation_id",
                "operation_type",
                "target",
                "parameters",
                "evidence_refs",
            )
        ):
            raise ValueError("LIVE_BOUND_CHANGESET_AUTHORITY_MISMATCH")
    return {
        "status": "passed",
        "case_id": case_id,
        "stage1_attempt_id": stage1[-1]["attempt_id"],
        "stage2_attempt_id": stage2[-1]["attempt_id"],
    }


def _case_definition(case_id: str) -> Any:
    return next(case for case in DEFAULT_CASES if case.case_id == case_id)


def _few_shot_binding_map(value: Any) -> dict[str, str] | None:
    if not isinstance(value, list):
        return None
    result: dict[str, str] = {}
    for item in value:
        if not isinstance(item, Mapping):
            return None
        few_shot_id = item.get("few_shot_id")
        few_shot_hash = item.get("few_shot_hash")
        if (
            not isinstance(few_shot_id, str)
            or not few_shot_id.strip()
            or not isinstance(few_shot_hash, str)
            or re.fullmatch(r"sha256:[0-9a-f]{64}", few_shot_hash) is None
            or few_shot_id in result
        ):
            return None
        result[few_shot_id] = few_shot_hash
    return result
