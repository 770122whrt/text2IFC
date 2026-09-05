"""Validate and curate genuine Phase 12 live structural Proof.

The runner's aggregate booleans are never curation authority.  This module
reconciles the redacted attempt ledger, binds the last valid Provider
documents to retained runtime artifacts, stages candidate Proof, and invokes
the family-neutral validator in a separate Python process before installation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scripts.ifc_repair.run_phase12_live_uat import (  # noqa: E402
    DEFAULT_CASES,
    DEFAULT_OUTPUT,
    DEFAULT_PROOF_ROOT,
    FROZEN_SOURCE_SHA256,
    PROGRAM_GUARD_REASON,
    SOURCE,
    _few_shot_binding_map,
)
from text2ifc_agent.prompt_registry import load_prompt_registry  # noqa: E402
from text2ifc_ifc_repair.prompt_profiles import select_prompt_profiles  # noqa: E402
from text2ifc_ifc_repair.property_resolution_stage import (  # noqa: E402
    TEMPLATE_ID as PROPERTY_RESOLUTION_TEMPLATE_ID,
)


LIVE_SOURCE_SCHEMA = "text2ifc/phase12-live-proof-source/0.1"
LIVE_UAT_SCHEMA = "text2ifc/phase12-live-uat/0.1"
LIVE_EVIDENCE_MODE = "live"
LIVE_PROVIDER = "deepseek-openai-compatible"
BASE_EVIDENCE_MODE = "offline_bound_deterministic"
EVIDENCE_SCOPE = "cross_scene_same_family_bimnet"
BASE_DAMAGE_CASE_ID = "phase12-d7n-beam-column-atomic"
BASE_DAMAGE_CASE = SOURCE.parent
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
        "door.add-with-opening.v0.3",
        "door.fill-existing-opening.v0.3",
        "occurrence.set-properties",
        "opening.add-to-wall",
        "window.add-with-opening.v0.2",
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
PROOF_CASE_IDS = {
    "complete": "phase12-live-deepseek-complete",
    "clarification-resume": "phase12-live-deepseek-clarification-resume",
}
FORBIDDEN_FALLBACK_FLAGS = frozenset(
    {"cached", "hand_authored", "prerecorded", "synthetic"}
)
VALIDATOR = ROOT / "scripts/ifc_repair/validate_success_cases.py"
PROOF_VALIDATION_SCHEMA = (
    ROOT / "schemas/agent/ifc-repair-proof-validation-0.2.schema.json"
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


def _path_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


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


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
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


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        value
        if isinstance(value, str)
        else json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )
    path.write_text(payload.rstrip() + "\n", encoding="utf-8")


def _safe_relative(root: Path, raw: Any) -> Path:
    relative = Path(str(raw).replace("\\", "/"))
    if not str(raw) or relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"LIVE_ARTIFACT_PATH_UNSAFE:{raw}")
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


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


def _effective_request(case_id: str) -> tuple[str, str, str | None]:
    case = _case_definition(case_id)
    initial = str(case.request)
    feedback = None if case.feedback is None else str(case.feedback)
    effective = (
        f"{initial}\n补充说明：{feedback.strip()}"
        if feedback is not None and case.feedback_kind == "add_detail"
        else initial
    )
    return effective, initial, feedback


def _case_from_result(result: Mapping[str, Any], case_id: str) -> Mapping[str, Any]:
    case = next(
        (
            item
            for item in result.get("cases", ())
            if isinstance(item, Mapping) and item.get("case_id") == case_id
        ),
        None,
    )
    if not isinstance(case, Mapping):
        raise ValueError(f"LIVE_CASE_MISSING:{case_id}")
    return case


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _artifact_from_final(run_root: Path, final: Mapping[str, Any], name: str) -> Path:
    artifacts = final.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise ValueError("LIVE_TERMINAL_ARTIFACTS_MISSING")
    return _safe_relative(run_root, artifacts.get(name))


def _application_from_terminal(path: Path) -> dict[str, Any]:
    terminal = _read(path)
    evidence = terminal.get("evidence")
    application = evidence.get("application") if isinstance(evidence, Mapping) else None
    if not isinstance(application, dict):
        raise ValueError("LIVE_TERMINAL_APPLICATION_MISSING")
    return application


def _runtime_authority(
    source_root: Path,
    result: Mapping[str, Any],
    case_id: str,
) -> dict[str, Any]:
    case = _case_from_result(result, case_id)
    final = case.get("final")
    if not _strict_success(final):
        raise ValueError("LIVE_SUCCESS_TERMINAL_INVALID")
    assert isinstance(final, Mapping)
    run_id = _require_text(final.get("run_id"), "LIVE_RUN_ID_REQUIRED")
    case_root = source_root / "cases" / case_id
    retained_case = _read(case_root / "case-result.json")
    if retained_case != case:
        raise ValueError("LIVE_CASE_RESULT_BINDING_MISMATCH")
    runtime_root = case_root / "runtime"
    run_root = runtime_root / "runs" / run_id
    if not run_root.is_dir():
        raise ValueError("LIVE_RUNTIME_RUN_MISSING")
    intent_path = _safe_relative(run_root, "intent/repair-intent.json")
    resolution_path = _safe_relative(run_root, "resolution.json")
    applied_changeset_path = _safe_relative(run_root, "changeset.json")
    bound_changeset_path = _safe_relative(
        run_root, "changeset/bound-changeset.json"
    )
    provider_draft_path = _safe_relative(run_root, "changeset/provider-draft.json")
    profile_path = _safe_relative(
        run_root, "changeset/prompt-profile-selection.json"
    )
    state_path = _safe_relative(run_root, "state.json")
    transitions_path = _safe_relative(run_root, "transitions.json")
    intent = _read(intent_path)
    applied_changeset = _read(applied_changeset_path)
    bound_changeset = _read(bound_changeset_path)
    provider_draft = _read(provider_draft_path)
    if _canonical_sha256(applied_changeset) != _canonical_sha256(bound_changeset):
        raise ValueError("LIVE_RUNTIME_CHANGESET_BINDING_MISMATCH")
    effective, initial, feedback = _effective_request(case_id)
    if case.get("request_sha256") != _text_sha256(initial) or case.get(
        "feedback_sha256"
    ) != (None if feedback is None else _text_sha256(feedback)):
        raise ValueError("LIVE_CASE_REQUEST_HASH_MISMATCH")
    effective_hash = _text_sha256(effective)
    if (
        intent.get("source_request_hash") != effective_hash
        or bound_changeset.get("source_request_hash") != effective_hash
    ):
        raise ValueError("LIVE_EFFECTIVE_REQUEST_BINDING_MISMATCH")
    contexts = []
    for path in run_root.glob("api-context*.json"):
        document = _read(path)
        context_intent = document.get("intent")
        if (
            document.get("repair_text") == effective
            and isinstance(context_intent, Mapping)
            and context_intent.get("source_request_hash") == effective_hash
        ):
            contexts.append(path)
    if len(contexts) != 1:
        raise ValueError("LIVE_EFFECTIVE_REQUEST_CONTEXT_MISMATCH")
    profile = _read(profile_path)
    expected_runtime_profiles = _expected_plan07_stage2_profiles(
        case_id,
        _require_text(
            provider_draft.get("schema_version"),
            "LIVE_RUNTIME_STAGE2_SCHEMA_REQUIRED",
        ),
    )
    if (
        frozenset(map(str, profile.get("profile_ids", ())))
        != expected_runtime_profiles
    ):
        raise ValueError("LIVE_RUNTIME_PROFILE_SELECTION_MISMATCH")
    if _read(state_path).get("run_id") != run_id or _read(
        transitions_path
    ).get("run_id") != run_id:
        raise ValueError("LIVE_RUNTIME_STATE_CHAIN_MISMATCH")
    audit_live_artifact_binding(
        result,
        case_id=case_id,
        intent=intent,
        provider_draft=provider_draft,
        changeset=bound_changeset,
    )
    manifest_path = _artifact_from_final(run_root, final, "manifest")
    evaluation_path = _artifact_from_final(run_root, final, "evaluation")
    repaired_path = _artifact_from_final(run_root, final, "successful_ifc")
    publication = _read(manifest_path)
    published = publication.get("artifacts")
    if not isinstance(published, list) or not published:
        raise ValueError("LIVE_PUBLICATION_MANIFEST_INVALID")
    published_paths = {
        str(item.get("path")): item
        for item in published
        if isinstance(item, Mapping)
    }
    for artifact in (evaluation_path, repaired_path):
        relative = artifact.relative_to(run_root).as_posix()
        record = published_paths.get(relative)
        if (
            not isinstance(record, Mapping)
            or record.get("sha256") != _path_sha256(artifact)
            or record.get("size_bytes") != artifact.stat().st_size
        ):
            raise ValueError("LIVE_PUBLICATION_ARTIFACT_BINDING_MISMATCH")
    terminal_paths = [
        run_root / str(relative)
        for relative in published_paths
        if str(relative).endswith("/evidence.json")
        or str(relative) == "publication/terminal/evidence.json"
    ]
    terminal_paths = [path for path in terminal_paths if path.is_file()]
    if len(terminal_paths) != 1:
        raise ValueError("LIVE_TERMINAL_EVIDENCE_MISSING")
    semantic_ref = str(bound_changeset.get("semantic_manifest_ref") or "")
    semantic_path = _safe_relative(run_root / "changeset", semantic_ref)
    return {
        "case": case,
        "run_id": run_id,
        "runtime_root": runtime_root,
        "run_root": run_root,
        "intent_path": intent_path,
        "resolution_path": resolution_path,
        "changeset_path": applied_changeset_path,
        "bound_changeset_path": bound_changeset_path,
        "provider_draft_path": provider_draft_path,
        "profile_path": profile_path,
        "semantic_path": semantic_path,
        "evaluation_path": evaluation_path,
        "repaired_path": repaired_path,
        "application": _application_from_terminal(terminal_paths[0]),
        "effective_request": effective,
        "initial_request": initial,
        "feedback": feedback,
        "changeset": bound_changeset,
    }


def _role_for_path(relative: str, fixed: Mapping[str, str], index: int) -> str:
    return fixed.get(relative, f"live_retained_artifact_{index:04d}")


def _write_case_files(case_root: Path, case_id: str) -> None:
    fixed_roles = {
        "manifest.json": "source_run_manifest",
        "base-damage-source-manifest.json": "base_damage_source_manifest",
        "original.ifc": "original_ground_truth",
        "damaged.ifc": "repair_input_ifc",
        "repaired.ifc": "published_repair_output",
        "request.txt": "user_request",
        "initial-request.txt": "initial_user_request",
        "clarification-answer.txt": "clarification_answer",
        "repair-intent.json": "stage1_repair_intent",
        "target-resolution.json": "deterministic_target_resolution",
        "semantic-manifests.json": "semantic_manifests",
        "changeset.json": "bound_changeset",
        "provider-draft.json": "live_provider_draft",
        "prompt-profile-selection.json": "live_prompt_profile_selection",
        "application.json": "application_result",
        "evaluation.json": "production_evaluation",
        "production-boundary.json": "production_input_boundary",
        "mutation_manifest.private.json": "mutation_manifest_private",
        "provider-evidence/live-uat-result.json": "live_provider_result",
        "provider-evidence/case-result.json": "live_provider_case_result",
    }
    entries = []
    for index, artifact in enumerate(sorted(case_root.rglob("*")), start=1):
        if not artifact.is_file() or artifact.name in {"FILES.json", "REPORT.md"}:
            continue
        relative = artifact.relative_to(case_root).as_posix()
        entries.append(
            {
                "path": relative,
                "role": _role_for_path(relative, fixed_roles, index),
                "sha256": _path_sha256(artifact),
                "size_bytes": artifact.stat().st_size,
            }
        )
    _write(
        case_root / "FILES.json",
        {
            "schema_version": "text2ifc/ifc-repair-proof-files/0.1",
            "case_id": case_id,
            "files": entries,
        },
    )


def _stage_case(
    stage_root: Path,
    source_root: Path,
    result: Mapping[str, Any],
    case_id: str,
) -> dict[str, Any]:
    authority = _runtime_authority(source_root, result, case_id)
    proof_case_id = PROOF_CASE_IDS[case_id]
    relative_root = Path("structural") / "live" / proof_case_id
    case_root = stage_root / relative_root
    case_root.mkdir(parents=True)
    for name in ("original.ifc", "damaged.ifc", "mutation_manifest.private.json"):
        _copy_file(BASE_DAMAGE_CASE / name, case_root / name)
    _copy_file(SOURCE, case_root / "damaged.ifc")
    base_manifest_path = BASE_DAMAGE_CASE / "manifest.json"
    _copy_file(base_manifest_path, case_root / "base-damage-source-manifest.json")
    _copy_file(authority["repaired_path"], case_root / "repaired.ifc")
    _copy_file(authority["intent_path"], case_root / "repair-intent.json")
    _copy_file(authority["resolution_path"], case_root / "target-resolution.json")
    _copy_file(authority["semantic_path"], case_root / "semantic-manifests.json")
    _copy_file(authority["changeset_path"], case_root / "changeset.json")
    _copy_file(authority["provider_draft_path"], case_root / "provider-draft.json")
    _copy_file(
        authority["profile_path"], case_root / "prompt-profile-selection.json"
    )
    _copy_file(authority["evaluation_path"], case_root / "evaluation.json")
    _write(case_root / "application.json", authority["application"])
    _write(case_root / "request.txt", authority["effective_request"])
    _write(case_root / "initial-request.txt", authority["initial_request"])
    if authority["feedback"] is not None:
        _write(case_root / "clarification-answer.txt", authority["feedback"])
    shutil.copytree(authority["runtime_root"], case_root / "runtime")
    provider_root = case_root / "provider-evidence"
    _copy_file(source_root / "live-uat-result.json", provider_root / "live-uat-result.json")
    _copy_file(
        source_root / "cases" / case_id / "case-result.json",
        provider_root / "case-result.json",
    )
    preflight_root = source_root / "preflight"
    if not preflight_root.is_dir():
        raise ValueError("LIVE_PREFLIGHT_EVIDENCE_MISSING")
    preflight = _read(preflight_root / "preflight.json")
    if preflight.get("status") != "passed":
        raise ValueError("LIVE_PREFLIGHT_EVIDENCE_FAILED")
    shutil.copytree(preflight_root, provider_root / "preflight")
    changeset = authority["changeset"]
    operation_count = len(changeset.get("operations", ()))
    _write(
        case_root / "production-boundary.json",
        {
            "schema_version": "text2ifc/production-input-boundary/0.2",
            "entrypoint": "run_phase12_live_uat.py",
            "ifc_inputs": ["damaged_ifc_path"],
            "request_inputs": ["public_request_bundle"],
            "original_ifc_supplied": False,
            "mutation_manifest_supplied": False,
            "deleted_object_ids_supplied": False,
            "private_comparator_available_during_repair": False,
            "damaged_ifc_sha256": _path_sha256(case_root / "damaged.ifc"),
            "request_sha256": changeset.get("source_request_hash"),
            "resolved_target_count": operation_count,
        },
    )
    base_manifest = _read(base_manifest_path)
    source_manifest = {
        "schema_version": LIVE_SOURCE_SCHEMA,
        "case_id": proof_case_id,
        "status": "passed",
        "provider": "deepseek-openai-compatible",
        "model": "deepseek-chat",
        "provider_evidence_mode": LIVE_EVIDENCE_MODE,
        "synthetic_fallback_used": False,
        "evidence_scope": EVIDENCE_SCOPE,
        "operation_count": operation_count,
        "source": base_manifest.get("source"),
        "damage": base_manifest.get("damage"),
        "base_damage_contract": {
            "case_id": BASE_DAMAGE_CASE_ID,
            "source_manifest_path": "base-damage-source-manifest.json",
            "source_manifest_sha256": _path_sha256(
                case_root / "base-damage-source-manifest.json"
            ),
            "mutation_manifest_path": "mutation_manifest.private.json",
            "mutation_manifest_sha256": _path_sha256(
                case_root / "mutation_manifest.private.json"
            ),
            "original_ifc_sha256": _path_sha256(case_root / "original.ifc"),
            "damaged_ifc_sha256": _path_sha256(case_root / "damaged.ifc"),
        },
        "live_contract": {
            "case_id": case_id,
            "live_uat_result_path": "provider-evidence/live-uat-result.json",
            "live_uat_result_sha256": _path_sha256(
                provider_root / "live-uat-result.json"
            ),
            "provider_draft_path": "provider-draft.json",
            "provider_draft_sha256": _path_sha256(case_root / "provider-draft.json"),
            "prompt_profile_selection_path": "prompt-profile-selection.json",
            "prompt_profile_selection_sha256": _path_sha256(
                case_root / "prompt-profile-selection.json"
            ),
        },
        "artifacts": {},
    }
    _write(case_root / "manifest.json", source_manifest)
    artifacts = {}
    for artifact in sorted(case_root.rglob("*")):
        if not artifact.is_file() or artifact.name in {
            "FILES.json",
            "REPORT.md",
            "manifest.json",
        }:
            continue
        relative = artifact.relative_to(case_root).as_posix()
        artifacts[relative] = {
            "path": relative,
            "bytes": artifact.stat().st_size,
            "sha256": _path_sha256(artifact),
        }
    source_manifest["artifacts"] = artifacts
    _write(case_root / "manifest.json", source_manifest)
    _write(
        case_root / "REPORT.md",
        (
            f"# Phase 12 live Proof: {case_id}\n\n"
            "Genuine live transcript and its retained RepairAPI runtime were "
            "strictly revalidated before installation.\n"
        ),
    )
    _write_case_files(case_root, proof_case_id)
    operation_types = sorted(
        {
            str(item.get("operation_type"))
            for item in changeset.get("operations", ())
            if isinstance(item, Mapping)
        }
    )
    return {
        "case_id": proof_case_id,
        "phase": "12",
        "status": "accepted",
        "operation_family": "structural",
        "case_kind": "live",
        "provider": "deepseek-openai-compatible",
        "model": "deepseek-chat",
        "provider_evidence_mode": LIVE_EVIDENCE_MODE,
        "evidence_scope": EVIDENCE_SCOPE,
        "operation_count": operation_count,
        "operation_types": operation_types,
        "original_ifc": (relative_root / "original.ifc").as_posix(),
        "damaged_ifc": (relative_root / "damaged.ifc").as_posix(),
        "repaired_ifc": (relative_root / "repaired.ifc").as_posix(),
        "report": (relative_root / "REPORT.md").as_posix(),
        "files": (relative_root / "FILES.json").as_posix(),
    }


def _default_validator_runner(
    command: Sequence[str], *, cwd: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _validate_subprocess(
    collection_root: Path,
    *,
    validator_runner: Callable[..., subprocess.CompletedProcess[str]],
    candidate_only: bool,
) -> dict[str, Any]:
    command = (sys.executable, str(VALIDATOR), "--root", str(collection_root), "--json")
    completed = validator_runner(command, cwd=ROOT)
    try:
        payload = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError("LIVE_CANDIDATE_VALIDATION_FAILED") from error
    if not isinstance(payload, dict):
        raise ValueError("LIVE_CANDIDATE_VALIDATION_FAILED")
    try:
        proof_validation_schema = _read(PROOF_VALIDATION_SCHEMA)
        Draft202012Validator.check_schema(proof_validation_schema)
        Draft202012Validator(proof_validation_schema).validate(payload)
    except Exception as error:
        raise ValueError("LIVE_CANDIDATE_VALIDATION_FAILED") from error
    cases = payload.get("cases")
    case_ids = {
        str(item.get("case_id"))
        for item in cases or ()
        if isinstance(item, Mapping)
    }
    common_pass = (
        completed.returncode == 0
        and payload.get("status") == "passed"
        and payload.get("errors") == []
        and isinstance(cases, list)
    )
    if candidate_only:
        common_pass = bool(
            common_pass
            and payload.get("case_count") == 2
            and payload.get("independently_recomputed_case_count") == 2
            and payload.get("legacy_unverifiable_case_count") == 0
            and case_ids == set(PROOF_CASE_IDS.values())
            and len(cases) == 2
            and all(
                item.get("provider_evidence_mode") == LIVE_EVIDENCE_MODE
                and item.get("live_transcript_status") == "strict_recomputed"
                and item.get("property_authority_coverage")
                == "strict_stage_1_5_recomputed"
                and int(item.get("property_claim_count", 0)) >= 1
                and item.get("current_property_acceptance_eligible") is True
                for item in cases
            )
        )
    else:
        manifest = _read(collection_root / "manifest.json")
        cases_by_id = {
            str(item.get("case_id")): item
            for item in cases
            if isinstance(item, Mapping)
        }
        required_property_cases = [
            cases_by_id.get(case_id) for case_id in PROOF_CASE_IDS.values()
        ]
        common_pass = bool(
            common_pass
            and payload.get("case_count") == manifest.get("case_count")
            and set(PROOF_CASE_IDS.values()).issubset(case_ids)
            and all(
                isinstance(item, Mapping)
                and item.get("property_authority_coverage")
                == "strict_stage_1_5_recomputed"
                and int(item.get("property_claim_count", 0)) >= 1
                and item.get("current_property_acceptance_eligible") is True
                for item in required_property_cases
            )
        )
    if not common_pass:
        raise ValueError("LIVE_CANDIDATE_VALIDATION_FAILED")
    return payload


def _resolve_source_root(run_root: Path | str) -> Path:
    requested = Path(run_root).resolve()
    if (requested / "live-uat-result.json").is_file():
        return requested
    candidates = sorted(
        path.parent
        for path in requested.glob("uat-*/live-uat-result.json")
        if path.is_file()
    )
    if not candidates:
        raise FileNotFoundError(requested / "live-uat-result.json")
    return candidates[-1]


def curate(
    run_root: Path | str = DEFAULT_OUTPUT,
    proof_root: Path | str = DEFAULT_PROOF_ROOT,
    *,
    validator_runner: Callable[..., subprocess.CompletedProcess[str]] = _default_validator_runner,
) -> dict[str, Any]:
    """Stage, independently validate, then atomically install two live cases."""

    source_root = _resolve_source_root(run_root)
    destination = Path(proof_root).resolve()
    live_result_path = source_root / "live-uat-result.json"
    result = _read(live_result_path)
    audit = audit_live_uat_result(result)
    if _path_sha256(SOURCE) != FROZEN_SOURCE_SHA256:
        raise ValueError("LIVE_FROZEN_SOURCE_DRIFT")
    destination.mkdir(parents=True, exist_ok=True)
    collection_path = destination / "manifest.json"
    collection = _read(collection_path)
    prior_cases = collection.get("cases")
    if not isinstance(prior_cases, list):
        raise ValueError("LIVE_PROOF_COLLECTION_INVALID")
    prior_ids = {str(item.get("case_id")) for item in prior_cases if isinstance(item, Mapping)}
    if prior_ids & set(PROOF_CASE_IDS.values()):
        raise ValueError("LIVE_PROOF_CASE_ALREADY_EXISTS")
    with tempfile.TemporaryDirectory(
        prefix="phase12-live-proof-", dir=destination.parent
    ) as temporary:
        stage_root = Path(temporary) / "candidate"
        stage_root.mkdir()
        entries = [
            _stage_case(stage_root, source_root, result, case_id)
            for case_id in SUCCESS_CASE_IDS
        ]
        _write(
            stage_root / "manifest.json",
            {
                "schema_version": "text2ifc/ifc-repair-success-collection/0.1",
                "case_count": 2,
                "cases": entries,
            },
        )
        _validate_subprocess(
            stage_root,
            validator_runner=validator_runner,
            candidate_only=True,
        )
        installed: list[Path] = []
        original_manifest = collection_path.read_bytes()
        try:
            for entry in entries:
                relative = Path(str(entry["files"])).parent
                target = destination / relative
                if target.exists():
                    raise ValueError("LIVE_PROOF_CASE_ALREADY_EXISTS")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(stage_root / relative, target)
                installed.append(target)
            updated = dict(collection)
            updated["cases"] = [*prior_cases, *entries]
            updated["case_count"] = len(updated["cases"])
            temporary_manifest = collection_path.with_suffix(".json.tmp")
            _write(temporary_manifest, updated)
            os.replace(temporary_manifest, collection_path)
            _validate_subprocess(
                destination,
                validator_runner=validator_runner,
                candidate_only=False,
            )
        except Exception:
            for target in reversed(installed):
                shutil.rmtree(target)
            collection_path.write_bytes(original_manifest)
            raise
    return {
        "schema_version": "text2ifc/phase12-live-proof-curation/0.1",
        "status": "passed",
        "proof_root": destination.as_posix(),
        "source_run_root": source_root.as_posix(),
        "case_ids": list(PROOF_CASE_IDS.values()),
        "program_guard_curated": False,
        "transcript_audit": audit,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Curate genuine Phase 12 live structural Proof."
    )
    parser.add_argument("--run-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--proof-root", type=Path, default=DEFAULT_PROOF_ROOT)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    payload = curate(args.run_root, args.proof_root)
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']} cases={len(payload['case_ids'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
