"""Preflight-gated, transcript-preserving Phase 12 live structural UAT.

The transport factory is deliberately invoked only after all six offline
preflight gates have been executed and machine-verified.  Tests inject a mock
transport at this public seam; the CLI creates the live Provider lazily after
the same gate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from text2ifc_knowledge.property_search import (  # noqa: E402
    _prepare_windows_torch_runtime,
)

_prepare_windows_torch_runtime()

import ifcopenshell  # noqa: E402

from scripts.ifc_repair.validate_success_cases import (  # noqa: E402
    audit_repaired_operations,
)
from text2ifc_agent.openai_compat import (  # noqa: E402
    OpenAICompatibleLiveProvider,
    load_openai_compatible_config,
    load_openai_compatible_runtime_config,
)
from text2ifc_agent.prompt_registry import load_prompt_registry  # noqa: E402
from text2ifc_agent.providers import (  # noqa: E402
    ProviderOutputError,
    redact_provider_payload,
)
from text2ifc_ifc_repair.api import RepairAPI  # noqa: E402
from text2ifc_ifc_repair.prompt_profiles import select_prompt_profiles  # noqa: E402
from text2ifc_ifc_repair.property_resolution_stage import (  # noqa: E402
    TEMPLATE_ID as PROPERTY_RESOLUTION_TEMPLATE_ID,
)
from text2ifc_ifc_repair.repair_intent import (  # noqa: E402
    REPAIR_INTENT_SCHEMA_VERSION_0_8,
)
from text2ifc_knowledge.property_runtime import (  # noqa: E402
    create_property_runtime_from_environment,
)


DEFAULT_OUTPUT = ROOT / "dataset/processed/ifc-repair-runs/phase12-live"
DEFAULT_PROOF_ROOT = (
    ROOT / "dataset/processed/proof/ifc-repair-success-cases"
)
SOURCE = (
    DEFAULT_PROOF_ROOT
    / "structural/batch/phase12-d7n-beam-column-atomic/damaged.ifc"
)
PROPERTY_RESOLUTION_TEMPLATE_HASH = str(
    load_prompt_registry()[PROPERTY_RESOLUTION_TEMPLATE_ID]["sha256"]
)
FROZEN_SOURCE_SHA256 = (
    "sha256:25240558bcbe23c1bbf4916d0b9a0fbb"
    "de8202d63dbc7a488ef633ab40eb6127"
)
TOKEN_GUARD = 65_536
LIVE_EVIDENCE_MODE = "live"
PROOF_VALIDATION_PENDING = "pending_plan_12_14"
APPROVED_DEEPSEEK_ENDPOINT = ("https", "api.deepseek.com", None, ("", "/"))
FORBIDDEN_EVIDENCE_MODES = frozenset(
    {"synthetic", "cached", "prerecorded", "hand-authored"}
)
PREFLIGHT_NAMES = (
    "focused",
    "offline",
    "full-suite",
    "compile",
    "diff",
    "proof",
)
CHANGED_SCOPE_ADMISSION_SCHEMA = (
    "text2ifc/phase12-live-changed-scope-admission/0.1"
)
CHANGED_SCOPE_ADMISSION_BASIS = (
    "previous full-preflight evidence + focused revalidation of all "
    "previously failed/changed scopes"
)
REQUIRED_CHANGED_SCOPE_RESOLUTIONS = frozenset(
    {
        "retrieval_evaluator_contract",
        "sequential_accelerated_parity",
        "cold_warm_cache_parity",
        "reopened_model_reuse_parity",
    }
)
REQUIRED_CHANGED_SCOPE_FILES = frozenset(
    {
        ".planning/phases/12.1-property-resolution-rag-reranker/12.1-VALIDATION.md",
        "scripts/ifc_repair/run_phase12_offline.py",
        "tests/knowledge/test_property_retrieval_evaluation.py",
        "src/text2ifc_ifc_repair/evaluation.py",
        "tests/ifc_repair/test_validation_acceleration.py",
        "scripts/ifc_repair/curate_phase12_live_proof.py",
        "scripts/ifc_repair/run_phase12_live_uat.py",
        "tests/ifc_repair/test_phase12_live_uat.py",
    }
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

    __slots__ = ("case_id", "request", "feedback", "feedback_kind")

    def __init__(
        self,
        *,
        case_id: str,
        request: str,
        feedback: str | None = None,
        feedback_kind: str | None = None,
    ) -> None:
        if not case_id or not request.strip():
            raise ValueError("LIVE_CASE_ID_AND_REQUEST_REQUIRED")
        self.case_id = case_id
        self.request = request
        self.feedback = feedback
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
    LiveCase(case_id="program-guard", request=PROGRAM_GUARD_REQUEST),
)
REQUIRED_CASE_IDS = tuple(case.case_id for case in DEFAULT_CASES)
FROZEN_CASE_MATRIX_SHA256 = (
    "sha256:8d5dec1c09a2b66ec10703930b340437"
    "cb3ae9de02f502e0b9c22ef186e14f5c"
)


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _text_sha256(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _path_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _repository_evidence_path(value: Any) -> Path:
    path = (ROOT / str(value)).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("CHANGED_SCOPE_ADMISSION_PATH_INVALID")
    return path


def _verify_changed_scope_evidence_refs(
    value: Any,
    *,
    reason_code: str,
) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError(reason_code)
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(reason_code)
        evidence_path = _repository_evidence_path(item.get("path"))
        if _path_sha256(evidence_path) != item.get("sha256"):
            raise ValueError(reason_code)


def _load_changed_scope_admission(path: Path | str) -> dict[str, Any]:
    admission_path = Path(path).resolve()
    if (
        not admission_path.is_relative_to(ROOT)
        or not admission_path.is_file()
    ):
        raise ValueError("CHANGED_SCOPE_ADMISSION_PATH_INVALID")
    payload = json.loads(admission_path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != CHANGED_SCOPE_ADMISSION_SCHEMA
        or payload.get("status") != "passed"
        or payload.get("admission_basis") != CHANGED_SCOPE_ADMISSION_BASIS
    ):
        raise ValueError("CHANGED_SCOPE_ADMISSION_CONTRACT_INVALID")
    if (
        payload.get("provider_calls") != 0
        or payload.get("predictions_regenerated") != 0
        or payload.get("network_transport_attempted") is not False
    ):
        raise ValueError("CHANGED_SCOPE_ADMISSION_OFFLINE_EVIDENCE_REQUIRED")

    source_ref = payload.get("source_preflight")
    if not isinstance(source_ref, Mapping):
        raise ValueError("CHANGED_SCOPE_SOURCE_PREFLIGHT_REQUIRED")
    source_path = _repository_evidence_path(source_ref.get("path"))
    if _path_sha256(source_path) != source_ref.get("sha256"):
        raise ValueError("CHANGED_SCOPE_SOURCE_PREFLIGHT_HASH_MISMATCH")
    source = json.loads(source_path.read_text(encoding="utf-8"))
    failed_source_checks = {
        str(item.get("name"))
        for item in source.get("checks", ())
        if item.get("status") == "failed"
    }
    if (
        source.get("status") != "failed"
        or source.get("network_transport_attempted") is not False
        or source.get("network_calls") != 0
        or source.get("skip_count") != 0
        or source.get("substitution_count") != 0
        or source.get("timeout_count") != 0
        or failed_source_checks != {"retrieval-evaluation", "full-suite"}
    ):
        raise ValueError("CHANGED_SCOPE_SOURCE_PREFLIGHT_INVALID")
    prior_suite = payload.get("prior_full_suite")
    if not isinstance(prior_suite, Mapping) or dict(prior_suite) != {
        "passed_count": 1151,
        "failed_count": 4,
    }:
        raise ValueError("CHANGED_SCOPE_PRIOR_SUITE_COUNTS_INVALID")
    full_suite = next(
        (
            item
            for item in source.get("checks", ())
            if item.get("name") == "full-suite"
        ),
        None,
    )
    artifacts = (
        full_suite.get("artifacts", ())
        if isinstance(full_suite, Mapping)
        else ()
    )
    full_log_ref = next(
        (
            item
            for item in artifacts
            if item.get("path") == "logs/full-suite.stdout.txt"
        ),
        None,
    )
    if not isinstance(full_log_ref, Mapping):
        raise ValueError("CHANGED_SCOPE_PRIOR_SUITE_LOG_REQUIRED")
    full_log_path = (source_path.parent / str(full_log_ref["path"])).resolve()
    if (
        not full_log_path.is_relative_to(source_path.parent)
        or not full_log_path.is_file()
        or _path_sha256(full_log_path) != full_log_ref.get("sha256")
        or "4 failed, 1151 passed" not in full_log_path.read_text(
            encoding="utf-8"
        )
    ):
        raise ValueError("CHANGED_SCOPE_PRIOR_SUITE_LOG_INVALID")

    resolved = payload.get("resolved_checks")
    if not isinstance(resolved, list):
        raise ValueError("CHANGED_SCOPE_RESOLUTIONS_REQUIRED")
    resolved_ids = {str(item.get("check_id")) for item in resolved}
    if (
        len(resolved) != len(REQUIRED_CHANGED_SCOPE_RESOLUTIONS)
        or resolved_ids != REQUIRED_CHANGED_SCOPE_RESOLUTIONS
        or any(
            item.get("status") != "passed"
            or item.get("exit_code") != 0
            or item.get("skip_count") != 0
            or item.get("substitution_count") != 0
            or item.get("timeout_count") != 0
            or item.get("network_calls") != 0
            for item in resolved
        )
    ):
        raise ValueError("CHANGED_SCOPE_RESOLUTIONS_INVALID")
    for item in resolved:
        _verify_changed_scope_evidence_refs(
            item.get("evidence"),
            reason_code="CHANGED_SCOPE_RESOLUTION_EVIDENCE_INVALID",
        )
    _verify_changed_scope_evidence_refs(
        payload.get("supporting_evidence"),
        reason_code="CHANGED_SCOPE_SUPPORTING_EVIDENCE_INVALID",
    )

    scope_hashes = payload.get("scope_file_sha256")
    if (
        not isinstance(scope_hashes, Mapping)
        or set(scope_hashes) != REQUIRED_CHANGED_SCOPE_FILES
        or any(
            _path_sha256(_repository_evidence_path(scope_path))
            != scope_hashes[scope_path]
            for scope_path in REQUIRED_CHANGED_SCOPE_FILES
        )
    ):
        raise ValueError("CHANGED_SCOPE_FILE_HASH_MISMATCH")
    return {
        **payload,
        "mode": "changed_scope_evidence_reuse",
        "admission_path": admission_path.relative_to(ROOT).as_posix(),
    }


def _canonical_sha256(value: Any) -> str:
    rendered = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return _text_sha256(rendered)


def _transport_payload_sha256(value: Any) -> str:
    try:
        return _canonical_sha256(value)
    except (TypeError, ValueError):
        return _text_sha256(repr(value))


def _case_matrix_sha256(cases: Sequence[LiveCase]) -> str:
    return _canonical_sha256(
        [
            {
                "case_id": case.case_id,
                "request": case.request,
                "feedback": case.feedback,
                "feedback_kind": case.feedback_kind,
            }
            for case in cases
        ]
    )


def _approved_deepseek_transport(transport: Any) -> bool:
    if type(transport) is not OpenAICompatibleLiveProvider:
        return False
    config = getattr(transport, "config", None)
    try:
        endpoint = urlsplit(str(config.base_url))
        port = endpoint.port
    except (AttributeError, TypeError, ValueError):
        return False
    approved_scheme, approved_host, approved_port, approved_paths = (
        APPROVED_DEEPSEEK_ENDPOINT
    )
    return (
        getattr(transport, "uses_default_sdk_client", False) is True
        and config.provider == "deepseek"
        and config.provider_label == "deepseek-openai-compatible"
        and endpoint.scheme.casefold() == approved_scheme
        and (endpoint.hostname or "").casefold() == approved_host
        and port == approved_port
        and endpoint.path in approved_paths
        and not endpoint.username
        and not endpoint.password
        and not endpoint.query
        and not endpoint.fragment
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


_PRIVATE_KEY_PARTS = (
    "private",
    "gold",
    "original_ifc",
    "mutation_manifest",
    "deleted_object",
    "removed_global",
    "removed_step",
)
_PRIVATE_VALUE_PATTERNS = (
    re.compile(r"canary[-_ ]?private", re.IGNORECASE),
    re.compile(r"private[-_ ]?gold", re.IGNORECASE),
    re.compile(r"gold[-_ ]?changeset", re.IGNORECASE),
    re.compile(r"mutation_manifest\.private", re.IGNORECASE),
)


def _private_evidence_detected(value: Any, *, key: str = "") -> bool:
    normalized_key = key.casefold().replace("-", "_")
    compact_key = normalized_key.replace("_", "")
    if any(
        part in normalized_key or part.replace("_", "") in compact_key
        for part in _PRIVATE_KEY_PARTS
    ):
        return True
    if isinstance(value, Mapping):
        return any(
            _private_evidence_detected(child, key=str(raw_key))
            for raw_key, child in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_private_evidence_detected(item) for item in value)
    return isinstance(value, str) and any(
        pattern.search(value) for pattern in _PRIVATE_VALUE_PATTERNS
    )


def _redact_for_evidence(value: Any, *, key: str = "") -> Any:
    """Redact secrets plus any evaluator-only structural evidence."""

    redacted = redact_provider_payload(value)
    if isinstance(redacted, Mapping):
        result: dict[str, Any] = {}
        for raw_key, child in redacted.items():
            child_key = str(raw_key)
            normalized = child_key.casefold().replace("-", "_")
            if any(part in normalized for part in _PRIVATE_KEY_PARTS):
                result[child_key] = "[REDACTED_PRIVATE]"
            else:
                result[child_key] = _redact_for_evidence(
                    child,
                    key=child_key,
                )
        return result
    if isinstance(redacted, (list, tuple)):
        return [_redact_for_evidence(item, key=key) for item in redacted]
    if isinstance(redacted, str) and any(
        pattern.search(redacted) for pattern in _PRIVATE_VALUE_PATTERNS
    ):
        return "[REDACTED_PRIVATE]"
    return redacted


def _unique_matches(pattern: str, value: str) -> list[str]:
    return list(dict.fromkeys(re.findall(pattern, value, flags=re.IGNORECASE)))


def _prompt_few_shot_bindings(prompt: str) -> list[dict[str, str]]:
    pairs: list[tuple[str, str]] = []

    def collect(value: Any) -> None:
        if isinstance(value, Mapping):
            few_shot_id = value.get("example_id", value.get("few_shot_id"))
            few_shot_hash = value.get(
                "example_hash",
                value.get("few_shot_hash", value.get("sha256")),
            )
            if (
                isinstance(few_shot_id, str)
                and few_shot_id.strip()
                and isinstance(few_shot_hash, str)
                and re.fullmatch(r"sha256:[0-9a-f]{64}", few_shot_hash)
            ):
                pairs.append((few_shot_id, few_shot_hash))
            for child in value.values():
                collect(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    decoder = json.JSONDecoder()
    for match in re.finditer(r"[\[{]", prompt):
        try:
            document, _end = decoder.raw_decode(prompt, match.start())
        except json.JSONDecodeError:
            continue
        collect(document)

    unique_pairs = list(dict.fromkeys(pairs))
    return [
        {"few_shot_id": few_shot_id, "few_shot_hash": few_shot_hash}
        for few_shot_id, few_shot_hash in unique_pairs
    ]


def _prompt_identities(prompt: str) -> dict[str, Any]:
    hash_pattern = r"(sha256:[0-9a-f]{64})"
    few_shot_bindings = _prompt_few_shot_bindings(prompt)
    return {
        "profile_ids": _unique_matches(
            r'"profile_id"\s*:\s*"([^"]+)"', prompt
        ),
        # Versions are positional identity fields. Multiple selected profiles
        # commonly share one version (for example Beam + Column v0.3), so
        # deduplicating them breaks alignment with profile_ids/profile_hashes.
        "profile_versions": re.findall(
            r'"profile_version"\s*:\s*"([^"]+)"', prompt
        ),
        "profile_hashes": _unique_matches(
            rf'"profile_hash"\s*:\s*"{hash_pattern}"', prompt
        ),
        # Legacy arrays remain derived evidence only. Authorization validates
        # the bound records below and never reconstructs identity by position.
        "few_shot_ids": [
            item["few_shot_id"] for item in few_shot_bindings
        ],
        "few_shot_hashes": [
            item["few_shot_hash"] for item in few_shot_bindings
        ],
        "few_shot_bindings": few_shot_bindings,
    }


def _correction_reason(prompt: str, stage_attempt: int) -> str | None:
    if stage_attempt <= 1:
        return None
    codes = _unique_matches(r'"code"\s*:\s*"([A-Z0-9_]+)"', prompt)
    return codes[-1] if codes else "VALIDATION_CORRECTION"


def _stage_name(raw: Any) -> str:
    stage = str(raw)
    if stage == "ifc_property_resolution":
        return "property_resolution"
    if "intent" in stage:
        return "stage1"
    if "changeset" in stage:
        return "stage2"
    raise ValueError(f"LIVE_TRANSCRIPT_STAGE_UNSUPPORTED:{stage}")


class TranscriptProvider:
    """Wrap one live Provider and retain redacted, attempt-level evidence."""

    def __init__(self, transport: Any) -> None:
        generate_live = getattr(transport, "generate_live", None)
        if not callable(generate_live):
            raise ValueError("LIVE_TRANSPORT_INTERFACE_REQUIRED")
        self._transport = transport
        self._case_id: str | None = None
        self._lineage = "initial"
        self._counts: dict[tuple[str, str], int] = {}
        self._last_attempt_by_case: dict[str, str] = {}
        self.attempts: list[dict[str, Any]] = []

    def set_case(self, case_id: str) -> None:
        self._case_id = case_id
        self._lineage = "initial"

    def provider_evidence_delegate(self) -> Any:
        """Expose the actual transport through the general Provider evidence seam."""

        return self._transport

    def set_lineage(self, lineage: str) -> None:
        if not self._case_id:
            raise ValueError("LIVE_TRANSCRIPT_CASE_NOT_BOUND")
        if not lineage:
            raise ValueError("LIVE_TRANSCRIPT_LINEAGE_REQUIRED")
        self._lineage = lineage

    def generate_live(
        self,
        *,
        session_id: str,
        prompt: str,
        schema: dict[str, Any],
        state: dict[str, Any],
    ) -> Any:
        if not self._case_id:
            raise ValueError("LIVE_TRANSCRIPT_CASE_NOT_BOUND")
        stage = _stage_name(state.get("stage"))
        count_key = (self._case_id, stage)
        ordinal = self._counts.get(count_key, 0) + 1
        self._counts[count_key] = ordinal
        attempt_id = f"{self._case_id}:{stage}:{ordinal:03d}"
        parent_attempt_id = self._last_attempt_by_case.get(self._case_id)
        stage_attempt = int(state.get("attempt", 1))
        request_arguments = {
            "session_id": session_id,
            "prompt": prompt,
            "schema": schema,
            "state": state,
        }
        try:
            live_result = self._transport.generate_live(**request_arguments)
        except Exception as error:
            live_result = getattr(error, "live_result", None)
            request = (
                request_arguments
                if live_result is None
                else getattr(live_result, "request", request_arguments)
            )
            response = (
                {"error_type": type(error).__name__}
                if live_result is None
                else getattr(live_result, "response", {})
            )
            metadata = dict(getattr(error, "details", {}) or {})
            self._append_attempt(
                attempt_id=attempt_id,
                parent_attempt_id=parent_attempt_id,
                stage=stage,
                ordinal=ordinal,
                stage_attempt=stage_attempt,
                evidence_class=getattr(live_result, "evidence_class", None),
                http_status=getattr(live_result, "http_status", None),
                request=request,
                response=response,
                metadata=metadata,
                prompt=prompt,
                state=state,
                error=type(error).__name__,
            )
            raise
        output = getattr(live_result, "output", None)
        metadata = dict(getattr(output, "metadata", {}) or {})
        self._append_attempt(
            attempt_id=attempt_id,
            parent_attempt_id=parent_attempt_id,
            stage=stage,
            ordinal=ordinal,
            stage_attempt=stage_attempt,
            evidence_class=getattr(live_result, "evidence_class", None),
            http_status=getattr(live_result, "http_status", None),
            request=getattr(live_result, "request", request_arguments),
            response=getattr(live_result, "response", {}),
            metadata=metadata,
            prompt=prompt,
            state=state,
            error=None,
        )
        return live_result

    def _append_attempt(
        self,
        *,
        attempt_id: str,
        parent_attempt_id: str | None,
        stage: str,
        ordinal: int,
        stage_attempt: int,
        evidence_class: Any,
        http_status: Any,
        request: Any,
        response: Any,
        metadata: Mapping[str, Any],
        prompt: str,
        state: Mapping[str, Any],
        error: str | None,
    ) -> None:
        assert self._case_id is not None
        raw_request_sha256 = _transport_payload_sha256(request)
        raw_response_sha256 = _transport_payload_sha256(response)
        private_evidence = any(
            _private_evidence_detected(value)
            for value in (request, response, metadata)
        )
        safe_request = _redact_for_evidence(request)
        safe_response = _redact_for_evidence(response)
        safe_metadata = _redact_for_evidence(dict(metadata))
        usage = safe_metadata.get("usage")
        if not isinstance(usage, Mapping) and isinstance(safe_response, Mapping):
            usage = safe_response.get("usage")
        usage = dict(usage) if isinstance(usage, Mapping) else {}
        identities = _prompt_identities(prompt)
        template_id = state.get("template_id")
        template_hash = state.get("template_hash")
        normalized_evidence_class = str(evidence_class or "")
        fallback_flags = {
            mode.replace("-", "_"): normalized_evidence_class == mode
            for mode in sorted(FORBIDDEN_EVIDENCE_MODES)
        }
        record = {
            "attempt_id": attempt_id,
            "parent_attempt_id": parent_attempt_id,
            "case_id": self._case_id,
            "lineage": self._lineage,
            "stage": stage,
            "ordinal": ordinal,
            "stage_attempt": stage_attempt,
            "correction_reason": _correction_reason(prompt, stage_attempt),
            "evidence_class": normalized_evidence_class or None,
            "http_status": http_status,
            "fallback_flags": fallback_flags,
            "private_evidence_detected": private_evidence,
            "provider": safe_metadata.get("provider"),
            "model": safe_metadata.get("model"),
            "usage": usage,
            "raw_request_sha256": raw_request_sha256,
            "raw_response_sha256": raw_response_sha256,
            "request_sha256": _canonical_sha256(safe_request),
            "response_sha256": _canonical_sha256(safe_response),
            "request": safe_request,
            "response": safe_response,
            "metadata": safe_metadata,
            "error": error,
            "template_id": (
                str(template_id) if isinstance(template_id, str) else None
            ),
            "template_hash": (
                str(template_hash) if isinstance(template_hash, str) else None
            ),
            **identities,
        }
        self.attempts.append(record)
        self._last_attempt_by_case[self._case_id] = attempt_id


def _default_command_runner(
    command: tuple[str, ...],
    *,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    rendered = " ".join(command).replace("\\", "/")
    timeout_seconds = 1_500
    if "-m pytest tests/knowledge tests/ifc_repair -q" in rendered:
        timeout_seconds = 7_200
    elif "test_phase12_live_uat.py" in rendered:
        timeout_seconds = 300
    elif "-m compileall" in rendered:
        timeout_seconds = 300
    elif rendered.startswith("git diff --check"):
        timeout_seconds = 60
    return subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=timeout_seconds,
    )


def _preflight_commands(
    preflight_root: Path,
    proof_root: Path,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    python = str(Path(sys.executable).resolve())
    retrieval_output = preflight_root / "property-retrieval-evaluation"
    offline_output = preflight_root / "offline-matrix"
    focused_basetemp = (preflight_root / "pytest-focused").resolve()
    focused_cache = (preflight_root / "pytest-cache-focused").resolve()
    full_basetemp = (preflight_root / "pytest-full-suite").resolve()
    full_cache = (preflight_root / "pytest-cache-full-suite").resolve()
    return (
        (
            "focused",
            (
                python,
                "-m",
                "pytest",
                "tests/ifc_repair/test_phase12_live_uat.py",
                "-q",
                f"--basetemp={focused_basetemp}",
                "-o",
                f"cache_dir={focused_cache}",
            ),
        ),
        (
            "retrieval-evaluation",
            (
                python,
                "scripts/ifc_repair/run_phase12_offline.py",
                "--output-root",
                str(retrieval_output),
                "--property-retrieval-evaluation-only",
            ),
        ),
        (
            "offline",
            (
                python,
                "scripts/ifc_repair/run_phase12_offline.py",
                "--output-root",
                str(offline_output),
            ),
        ),
        (
            "full-suite",
            (
                python,
                "-m",
                "pytest",
                "tests/knowledge",
                "tests/ifc_repair",
                "-q",
                f"--basetemp={full_basetemp}",
                "-o",
                f"cache_dir={full_cache}",
            ),
        ),
        (
            "compile",
            (python, "-m", "compileall", "-q", "src", "tests", "scripts"),
        ),
        ("diff", ("git", "diff", "--check")),
        (
            "proof",
            (
                python,
                "scripts/ifc_repair/validate_success_cases.py",
                "--collection-root",
                str(proof_root),
                "--json",
            ),
        ),
    )


def _artifact_record(path: Path, *, root: Path) -> dict[str, Any]:
    resolved = path.resolve()
    try:
        reference = resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        reference = resolved.as_posix()
    return {
        "path": reference,
        "sha256": _path_sha256(path),
        "size_bytes": path.stat().st_size,
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _git_text(*arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        return ""
    return str(completed.stdout or "").strip()


def _execution_identity() -> dict[str, Any]:
    status_text = _git_text("status", "--porcelain=v1", "--untracked-files=normal")
    status_entries = [line for line in status_text.splitlines() if line]
    dependencies: dict[str, str | None] = {}
    for package in (
        "ifcopenshell",
        "jsonschema",
        "pytest",
        "qdrant-client",
        "sentence-transformers",
        "torch",
    ):
        try:
            dependencies[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            dependencies[package] = None
    branch = _git_text("branch", "--show-current") or "(detached)"
    return {
        "repository": {
            "commit": _git_text("rev-parse", "HEAD"),
            "branch": branch,
            "worktree_clean": not status_entries,
            "tracked_change_count": sum(
                not entry.startswith("??") for entry in status_entries
            ),
            "untracked_count": sum(
                entry.startswith("??") for entry in status_entries
            ),
            "worktree_porcelain_v1": status_entries,
            "worktree_porcelain_v1_sha256": _text_sha256(status_text),
        },
        "python": {
            "executable": str(Path(sys.executable).resolve()),
            "version": sys.version,
            "implementation": platform.python_implementation(),
        },
        "platform": {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "dependencies": dependencies,
    }


def _pytest_summary_counts(stdout: str) -> dict[str, int]:
    return {
        label: sum(
            int(match)
            for match in re.findall(rf"\b(\d+)\s+{label}\b", stdout)
        )
        for label in (
            "passed",
            "failed",
            "errors",
            "skipped",
            "deselected",
            "xfailed",
            "xpassed",
        )
    }


def _preflight_check_counts(
    *,
    name: str,
    command: tuple[str, ...],
    stdout: str,
    execution_reason: str | None,
) -> dict[str, int]:
    skip_count = 0
    substitution_count = 0
    network_calls = 0
    if name in {"focused", "full-suite"}:
        pytest_counts = _pytest_summary_counts(stdout)
        skip_count = pytest_counts["skipped"]
        substitution_count = sum(
            pytest_counts[key] for key in ("deselected", "xfailed", "xpassed")
        )
    elif name in {"retrieval-evaluation", "offline"}:
        try:
            output = Path(command[command.index("--output-root") + 1])
            if name == "retrieval-evaluation":
                report = _read_json(output / "property-evaluation.json")
                network_calls = int(report.get("provider_network_calls", 0))
            else:
                summary = _read_json(output / "run-summary.json")
                property_resolution = summary.get("property_resolution")
                if isinstance(property_resolution, Mapping):
                    network_calls = int(
                        property_resolution.get("provider_network_calls", 0)
                    )
        except (FileNotFoundError, TypeError, ValueError):
            network_calls = 0
    return {
        "skip_count": skip_count,
        "substitution_count": substitution_count,
        "timeout_count": int(execution_reason == "COMMAND_TIMEOUT"),
        "network_calls": network_calls,
    }


def _verify_preflight_semantics(
    *,
    name: str,
    command: tuple[str, ...],
    completed: subprocess.CompletedProcess[str],
    preflight_root: Path,
    proof_root: Path,
) -> tuple[str | None, list[Path]]:
    if int(completed.returncode) != 0:
        return f"COMMAND_EXIT_{completed.returncode}", []
    if name in {"focused", "full-suite"}:
        counts = _pytest_summary_counts(str(completed.stdout or ""))
        if counts["passed"] < 1:
            return "PYTEST_SUMMARY_MISSING", []
        if counts["failed"] or counts["errors"]:
            return "PYTEST_FAILURES_PRESENT", []
        if counts["skipped"]:
            return "PYTEST_SKIPS_PRESENT", []
        if any(counts[key] for key in ("deselected", "xfailed", "xpassed")):
            return "PYTEST_SUBSTITUTIONS_PRESENT", []
    if name == "retrieval-evaluation":
        output = Path(command[command.index("--output-root") + 1]).resolve()
        report_path = output / "property-evaluation.json"
        ledger_path = output / "property-retrieval-ledger.json"
        if not report_path.is_file() or not ledger_path.is_file():
            return "PROPERTY_RETRIEVAL_EVALUATION_MISSING", []
        try:
            report = _read_json(report_path)
            ledger = _read_json(ledger_path)
        except Exception as error:
            return (
                f"PROPERTY_RETRIEVAL_EVALUATION_INVALID:{type(error).__name__}",
                [],
            )
        if int(report.get("provider_network_calls", -1)) != 0:
            return "PROPERTY_RETRIEVAL_EVALUATION_NETWORK_NONZERO", [
                report_path,
                ledger_path,
            ]
        hard_gates = report.get("hard_gates")
        candidate = report.get("candidate")
        health = report.get("knowledge_health")
        retrieval_metrics = report.get("retrieval_metrics")
        valid = (
            report.get("schema_version")
            == "text2ifc/phase12.1-property-resolution-evaluation/0.3"
            and report.get("status") == "passed"
            and report.get("case_count") == 60
            and report.get("retrieval_capability") == "evaluated"
            and report.get("stage_1_5_semantic_evaluation_status")
            == "not_evaluated_offline"
            and isinstance(candidate, Mapping)
            and candidate.get("semantic_scored_count") == 0
            and candidate.get("confirmed_standard_precision") is None
            and candidate.get("false_standard_authorization_count") is None
            and isinstance(hard_gates, Mapping)
            and bool(hard_gates)
            and all(value is True for value in hard_gates.values())
            and isinstance(health, Mapping)
            and health.get("status") == "ready"
            and health.get("runtime_mode") == "production"
            and health.get("acceptance_eligible") is True
            and isinstance(retrieval_metrics, Mapping)
            and retrieval_metrics.get("case_count") == 60
            and Path(
                str(retrieval_metrics.get("retrieval_ledger_path") or "")
            ).resolve()
            == ledger_path
            and ledger.get("schema_version")
            == "text2ifc/phase12.1-property-retrieval-ledger/0.1"
            and ledger.get("status") == "passed"
            and ledger.get("case_count") == 60
            and ledger.get("provider_network_calls") == 0
        )
        if not valid:
            return "PROPERTY_RETRIEVAL_EVALUATION_NOT_GREEN", [
                report_path,
                ledger_path,
            ]
        return None, [report_path, ledger_path]
    if name == "offline":
        output = Path(command[command.index("--output-root") + 1])
        summary_path = output / "run-summary.json"
        if not summary_path.is_file():
            return "OFFLINE_SUMMARY_MISSING", []
        try:
            summary = _read_json(summary_path)
        except Exception as error:
            return f"OFFLINE_SUMMARY_INVALID:{type(error).__name__}", []
        if (
            summary.get("schema_version")
            != "text2ifc/phase12-offline-matrix/0.1"
            or summary.get("status") != "passed"
            or summary.get("matrix_complete") is not True
        ):
            return "OFFLINE_MATRIX_NOT_GREEN", [summary_path]
        property_resolution = summary.get("property_resolution")
        if (
            not isinstance(property_resolution, Mapping)
            or not isinstance(
                property_resolution.get("provider_network_calls"), int
            )
        ):
            return "OFFLINE_PROVIDER_NETWORK_ACCOUNTING_MISSING", [summary_path]
        if int(property_resolution["provider_network_calls"]) != 0:
            return "OFFLINE_PROVIDER_NETWORK_CALLS_NONZERO", [summary_path]
        return None, [summary_path]
    if name == "proof":
        try:
            proof = json.loads(completed.stdout)
        except (json.JSONDecodeError, TypeError):
            return "PROOF_RESULT_INVALID", []
        required_counts = (
            "case_count",
            "operation_count",
            "checked_file_count",
            "reopened_ifc_count",
        )
        valid = (
            isinstance(proof, Mapping)
            and proof.get("schema_version")
            == "text2ifc/ifc-repair-proof-validation/0.2"
            and proof.get("status") == "passed"
            and proof.get("errors") == []
            and all(int(proof.get(key, 0)) > 0 for key in required_counts)
        )
        manifest = proof_root / "manifest.json"
        if not valid or not manifest.is_file():
            return "PROOF_RESULT_NOT_MACHINE_GREEN", []
        try:
            manifest_document = _read_json(manifest)
        except Exception as error:
            return f"PROOF_MANIFEST_INVALID:{type(error).__name__}", []
        if int(manifest_document.get("case_count", -1)) != int(
            proof["case_count"]
        ):
            return "PROOF_MANIFEST_RESULT_MISMATCH", [manifest]
        return None, [manifest]
    del preflight_root
    return None, []


def run_preflight(
    preflight_root: Path,
    *,
    proof_root: Path,
    command_runner: Callable[..., subprocess.CompletedProcess[str]],
) -> dict[str, Any]:
    started_at = _utc_now()
    execution_identity = _execution_identity()
    preflight_root.mkdir(parents=True, exist_ok=True)
    logs = preflight_root / "logs"
    logs.mkdir()
    checks: list[dict[str, Any]] = []
    for name, command in _preflight_commands(preflight_root, proof_root):
        check_started_at = _utc_now()
        execution_reason: str | None = None
        try:
            completed = command_runner(command, cwd=ROOT)
        except subprocess.TimeoutExpired as error:
            execution_reason = "COMMAND_TIMEOUT"
            completed = subprocess.CompletedProcess(
                command,
                124,
                str(error.stdout or ""),
                str(error.stderr or f"TimeoutExpired: {error}")[:512],
            )
        except Exception as error:
            execution_reason = "COMMAND_EXECUTION_ERROR"
            completed = subprocess.CompletedProcess(
                command,
                255,
                "",
                f"{type(error).__name__}: {error}"[:512],
            )
        stdout = str(completed.stdout or "")
        stderr = str(completed.stderr or "")
        stdout_path = logs / f"{name}.stdout.txt"
        stderr_path = logs / f"{name}.stderr.txt"
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        if execution_reason is None:
            reason, semantic_artifacts = _verify_preflight_semantics(
                name=name,
                command=command,
                completed=completed,
                preflight_root=preflight_root,
                proof_root=proof_root,
            )
        else:
            reason, semantic_artifacts = execution_reason, []
        artifact_paths = [
            path
            for path in (stdout_path, stderr_path, *semantic_artifacts)
            if path.is_file() and path.stat().st_size > 0
        ]
        check_counts = _preflight_check_counts(
            name=name,
            command=command,
            stdout=stdout,
            execution_reason=execution_reason,
        )
        check_finished_at = _utc_now()
        record = {
            "name": name,
            "command": list(command),
            "started_at_utc": check_started_at,
            "finished_at_utc": check_finished_at,
            "exit_code": int(completed.returncode),
            "status": "passed" if reason is None else "failed",
            "reason_code": reason,
            "stdout_sha256": _text_sha256(stdout),
            "stderr_sha256": _text_sha256(stderr),
            "artifacts": [
                _artifact_record(path, root=preflight_root)
                for path in artifact_paths
            ],
            "network_transport_attempted": bool(check_counts["network_calls"]),
            **check_counts,
        }
        record["result_sha256"] = _canonical_sha256(record)
        checks.append(record)
    status = "passed" if all(item["status"] == "passed" for item in checks) else "failed"
    finished_at = _utc_now()
    result = {
        "schema_version": "text2ifc/phase12-live-preflight/0.4",
        "status": status,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "execution_identity": execution_identity,
        "failure_count": sum(item["status"] != "passed" for item in checks),
        "skip_count": sum(int(item["skip_count"]) for item in checks),
        "substitution_count": sum(
            int(item["substitution_count"]) for item in checks
        ),
        "timeout_count": sum(int(item["timeout_count"]) for item in checks),
        "network_calls": sum(int(item["network_calls"]) for item in checks),
        "network_transport_attempted": any(
            bool(item["network_transport_attempted"]) for item in checks
        ),
        "checks": checks,
    }
    result["evidence_sha256"] = _canonical_sha256(result)
    _write_json(preflight_root / "preflight.json", result)
    return result


def _result_summary(result: Any) -> dict[str, Any]:
    return {
        "status": result.status,
        "reason_code": result.reason_code,
        "run_id": result.run_id,
        "state_version": result.state_version,
        "complete_repair_success": result.complete_repair_success,
        "successful_artifact_publishable": result.successful_artifact_publishable,
        "artifacts": dict(result.artifacts),
    }


def _safe_artifact_path(run_root: Path, relative: str) -> Path:
    path = (run_root / relative).resolve()
    path.relative_to(run_root.resolve())
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _strict_reopen_verification(
    runtime: Path,
    final: Mapping[str, Any],
) -> dict[str, Any]:
    if not final.get("successful_artifact_publishable"):
        return {
            "status": "not_applicable",
            "l0_pass": None,
            "l1_pass": None,
            "l2_pass": None,
            "preservation_status": PROOF_VALIDATION_PENDING,
            "ground_truth_isolation_status": PROOF_VALIDATION_PENDING,
            "proof_validation_status": PROOF_VALIDATION_PENDING,
        }
    try:
        runs_root = (runtime / "runs").resolve()
        run_root = (runs_root / str(final["run_id"])).resolve()
        run_root.relative_to(runs_root)
        artifacts = final.get("artifacts")
        if not isinstance(artifacts, Mapping):
            raise ValueError("LIVE_RESULT_ARTIFACTS_MISSING")
        manifest_path = _safe_artifact_path(run_root, str(artifacts["manifest"]))
        evaluation_path = _safe_artifact_path(
            run_root, str(artifacts["evaluation"])
        )
        repaired_path = _safe_artifact_path(
            run_root, str(artifacts["successful_ifc"])
        )
        manifest = _read_json(manifest_path)
        entries = manifest.get("artifacts")
        if not isinstance(entries, list) or not entries:
            raise ValueError("LIVE_MANIFEST_EMPTY")
        for entry in entries:
            path = _safe_artifact_path(run_root, str(entry["path"]))
            if (
                path.stat().st_size != int(entry["size_bytes"])
                or _path_sha256(path).removeprefix("sha256:")
                != str(entry["sha256"]).removeprefix("sha256:")
            ):
                raise ValueError("LIVE_MANIFEST_HASH_MISMATCH")
        state = _read_json(run_root / "state.json")
        source = state.get("source")
        if not isinstance(source, Mapping):
            raise ValueError("LIVE_SOURCE_BINDING_MISSING")
        source_path = Path(str(source["reference"])).resolve()
        if source_path != SOURCE.resolve():
            raise ValueError("LIVE_SOURCE_PATH_MISMATCH")
        if not source_path.is_file():
            raise ValueError("LIVE_SOURCE_MISSING")
        if (
            _path_sha256(source_path) != FROZEN_SOURCE_SHA256
            or str(source.get("sha256")) != FROZEN_SOURCE_SHA256
        ):
            raise ValueError("LIVE_SOURCE_HASH_MISMATCH")
        damaged = ifcopenshell.open(str(source_path))
        repaired = ifcopenshell.open(str(repaired_path))
        if str(repaired.schema) != "IFC2X3":
            raise ValueError("LIVE_REPAIRED_SCHEMA_INVALID")
        changeset_path = run_root / "changeset" / "bound-changeset.json"
        if not changeset_path.is_file():
            changeset_path = run_root / "changeset.json"
        changeset = _read_json(changeset_path)
        evidence_path = manifest_path.parent / "terminal" / "evidence.json"
        evidence = _read_json(evidence_path).get("evidence")
        if not isinstance(evidence, Mapping):
            raise ValueError("LIVE_APPLICATION_EVIDENCE_MISSING")
        application = evidence.get("application")
        if not isinstance(application, Mapping):
            raise ValueError("LIVE_APPLICATION_EVIDENCE_MISSING")
        evaluation = _read_json(evaluation_path)
        operations = changeset.get("operations")
        if not isinstance(operations, list) or not operations:
            raise ValueError("LIVE_CHANGESET_OPERATIONS_MISSING")
        l0 = (
            changeset.get("binding_status") == "bound"
            and changeset.get("base_model_fingerprint") == source.get("sha256")
            and application.get("valid") is True
            and application.get("published") is True
            and evaluation.get("status") == "passed"
            and evaluation.get("complete_repair_success") is True
            and evaluation.get("successful_artifact_publishable") is True
            and len(application.get("operations", ())) == len(operations)
        )
        if not l0:
            raise ValueError("LIVE_L0_RECOMPUTE_FAILED")
        recomputed = audit_repaired_operations(
            changeset=changeset,
            application=application,
            damaged_model=damaged,
            repaired_model=repaired,
        )
        l1 = recomputed["l1_operation_count"] == len(operations)
        l2 = recomputed["l2_operation_count"] == len(operations)
        if not l1 or not l2:
            raise ValueError("LIVE_L1_L2_RECOMPUTE_FAILED")
        return {
            "status": "passed",
            "l0_pass": True,
            "l1_pass": l1,
            "l2_pass": l2,
            "preservation_status": PROOF_VALIDATION_PENDING,
            "ground_truth_isolation_status": PROOF_VALIDATION_PENDING,
            "proof_validation_status": PROOF_VALIDATION_PENDING,
            "operation_count": len(operations),
            "reopened_schema": str(repaired.schema),
            "successful_ifc_sha256": _path_sha256(repaired_path),
            "changeset_sha256": _path_sha256(changeset_path),
            "evaluation_sha256": _path_sha256(evaluation_path),
        }
    except Exception as error:
        return {
            "status": "failed",
            "l0_pass": False,
            "l1_pass": False,
            "l2_pass": False,
            "preservation_status": PROOF_VALIDATION_PENDING,
            "ground_truth_isolation_status": PROOF_VALIDATION_PENDING,
            "proof_validation_status": PROOF_VALIDATION_PENDING,
            "reason_code": str(error).split(":", 1)[0][:128],
        }


def _offered_candidate_token_for_property_identity(
    clarification: Any,
    property_identity: str,
) -> str:
    matches = [
        str(candidate.token)
        for candidate in getattr(clarification, "candidates", ())
        if getattr(candidate, "public_id", None) == property_identity
        and isinstance(getattr(candidate, "token", None), str)
        and str(candidate.token).strip()
    ]
    if len(matches) != 1:
        raise ValueError("LIVE_CASE_PROPERTY_IDENTITY_NOT_OFFERED")
    return matches[0]


def _production_case_executor(
    case: LiveCase,
    provider: TranscriptProvider,
    case_root: Path,
    *,
    property_knowledge_runtime: Any | None = None,
    source_path: Path | str = SOURCE,
    expected_source_sha256: str = FROZEN_SOURCE_SHA256,
) -> dict[str, Any]:
    runtime = case_root / "runtime"
    source = Path(source_path).resolve()
    source_sha256_before = _path_sha256(source)
    if source_sha256_before != expected_source_sha256:
        raise ValueError("LIVE_SOURCE_HASH_MISMATCH")
    knowledge_runtime = (
        create_property_runtime_from_environment(project_root=ROOT)
        if property_knowledge_runtime is None
        else property_knowledge_runtime
    )
    api = RepairAPI(
        runtime,
        provider=provider,
        intent_schema_version=REPAIR_INTENT_SCHEMA_VERSION_0_8,
        property_knowledge_runtime=knowledge_runtime,
    )
    provider.set_lineage("initial")
    initial = api.start(source, case.request)
    clarification = initial.clarification
    clarification_payload = (
        None
        if clarification is None
        else {
            "clarification_id": clarification.clarification_id,
            "reason_code": clarification.reason_code,
            "question": clarification.question,
            "answer_modes": list(clarification.answer_modes),
        }
    )
    final = initial
    answer_applied = False
    if case.feedback is not None and clarification is not None:
        provider.set_lineage("clarification-resume")
        if case.feedback_kind == "select_candidate":
            answer = {
                "kind": "select_candidate",
                "candidate_token": (
                    _offered_candidate_token_for_property_identity(
                        clarification,
                        case.feedback,
                    )
                ),
            }
        elif case.feedback_kind == "add_detail":
            answer = {"kind": "add_detail", "detail": case.feedback}
        else:
            raise ValueError("LIVE_CASE_FEEDBACK_KIND_REQUIRED")
        final = api.continue_with_answer(
            initial.run_id,
            answer,
            clarification_id=clarification.clarification_id,
            expected_state_version=initial.state_version,
        )
        answer_applied = True
    final_summary = _result_summary(final)
    candidate_output_paths = sorted(
        str(value)
        for key, value in final_summary.get("artifacts", {}).items()
        if key in {"successful_ifc", "diagnostic_candidate"} and value
    )
    program_guard_evidence = None
    if case.case_id == "program-guard":
        source_sha256_after = _path_sha256(source)
        stage2_attempts = sum(
            1
            for attempt in provider.attempts
            if attempt.get("case_id") == case.case_id
            and attempt.get("stage") == "stage2"
        )
        program_guard_evidence = {
            "source_reference": str(source),
            "source_sha256_before": source_sha256_before,
            "source_sha256_after": source_sha256_after,
            "source_unchanged": source_sha256_before == source_sha256_after,
            "stage2_attempts": stage2_attempts,
            "candidate_output_paths": candidate_output_paths,
            "mutation_attempted": bool(stage2_attempts or candidate_output_paths),
        }
    return {
        **final_summary,
        "initial": _result_summary(initial),
        "clarification": clarification_payload,
        "clarification_answer_applied": answer_applied,
        "request_sha256": _text_sha256(case.request),
        "feedback_sha256": (
            None if case.feedback is None else _text_sha256(case.feedback)
        ),
        "program_guard_evidence": program_guard_evidence,
        "strict_reopen_verification": _strict_reopen_verification(
            runtime,
            final_summary,
        ),
    }


_ORIGINAL_PRODUCTION_CASE_EXECUTOR = _production_case_executor


def _counts(attempts: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    result = {"stage1": 0, "property_resolution": 0, "stage2": 0}
    for attempt in attempts:
        stage = str(attempt.get("stage"))
        if stage in result:
            result[stage] += 1
    return result


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


def _live_attempt_evidence_pass(
    attempts: Sequence[Mapping[str, Any]],
) -> bool:
    if not attempts:
        return False
    for attempt in attempts:
        metadata = attempt.get("metadata")
        usage = attempt.get("usage")
        fallback_flags = attempt.get("fallback_flags")
        profile_ids = attempt.get("profile_ids")
        profile_versions = attempt.get("profile_versions")
        profile_hashes = attempt.get("profile_hashes")
        few_shot_bindings = attempt.get("few_shot_bindings")
        if not isinstance(metadata, Mapping):
            return False
        if not isinstance(usage, Mapping) or not usage:
            return False
        if not isinstance(fallback_flags, Mapping):
            return False
        stage = attempt.get("stage")
        if stage == "property_resolution":
            template_id = attempt.get("template_id")
            template_hash = attempt.get("template_hash")
            if (
                template_id != PROPERTY_RESOLUTION_TEMPLATE_ID
                or template_hash != PROPERTY_RESOLUTION_TEMPLATE_HASH
            ):
                return False
        elif (
            not isinstance(profile_ids, list)
            or not profile_ids
            or not isinstance(profile_versions, list)
            or not profile_versions
            or not isinstance(profile_hashes, list)
            or not profile_hashes
        ):
            return False
        if stage == "stage2":
            try:
                expected_selection = select_prompt_profiles(
                    list(map(str, profile_ids))
                ).to_dict()
            except (KeyError, TypeError, ValueError):
                return False
            expected_versions = [
                str(profile["profile_version"])
                for profile in expected_selection["profiles"]
            ]
            actual_binding_map = _few_shot_binding_map(few_shot_bindings)
            expected_binding_map = dict(
                zip(
                    expected_selection["few_shot_ids"],
                    expected_selection["few_shot_hashes"],
                    strict=True,
                )
            )
            if (
                profile_ids != expected_selection["profile_ids"]
                or profile_versions != expected_versions
                or profile_hashes != expected_selection["profile_hashes"]
                or actual_binding_map != expected_binding_map
            ):
                return False
        if (
            attempt.get("evidence_class") != LIVE_EVIDENCE_MODE
            or metadata.get("evidence_class") != LIVE_EVIDENCE_MODE
            or attempt.get("http_status") != 200
            or attempt.get("error") is not None
            or attempt.get("private_evidence_detected") is not False
            or not isinstance(attempt.get("provider"), str)
            or not str(attempt.get("provider")).strip()
            or not isinstance(attempt.get("model"), str)
            or not str(attempt.get("model")).strip()
            or not isinstance(metadata.get("response_id"), str)
            or not str(metadata.get("response_id")).strip()
            or not isinstance(metadata.get("transport_attempts"), int)
            or int(metadata.get("transport_attempts", 0)) < 1
            or any(value is not False for value in fallback_flags.values())
        ):
            return False
    return True


def _case_contract_pass(
    case: LiveCase,
    final: Mapping[str, Any],
    counts: Mapping[str, int],
) -> bool:
    published = bool(
        final.get("complete_repair_success")
        and final.get("successful_artifact_publishable")
    )
    if case.case_id == "complete":
        strict = final.get("strict_reopen_verification")
        strict_ok = (
            isinstance(strict, Mapping)
            and strict.get("status") == "passed"
            and strict.get("l0_pass") is True
            and strict.get("l1_pass") is True
            and strict.get("l2_pass") is True
        )
        return (
            final.get("status") == "succeeded"
            and published
            and counts.get("stage1", 0) == 1
            and counts.get("property_resolution", 0) == 2
            and counts.get("stage2", 0) == 1
            and strict_ok
        )
    if case.case_id == "clarification-resume":
        strict = final.get("strict_reopen_verification")
        initial = final.get("initial")
        clarification = final.get("clarification")
        strict_ok = (
            isinstance(strict, Mapping)
            and strict.get("status") == "passed"
            and strict.get("l0_pass") is True
            and strict.get("l1_pass") is True
            and strict.get("l2_pass") is True
        )
        initial_stop_ok = (
            isinstance(initial, Mapping)
            and initial.get("status") == "clarification_required"
            and initial.get("complete_repair_success") is False
            and initial.get("successful_artifact_publishable") is False
            and isinstance(clarification, Mapping)
            and isinstance(clarification.get("clarification_id"), str)
            and bool(str(clarification.get("clarification_id")).strip())
            and isinstance(clarification.get("reason_code"), str)
            and bool(str(clarification.get("reason_code")).strip())
            and isinstance(clarification.get("question"), str)
            and bool(str(clarification.get("question")).strip())
            and isinstance(clarification.get("answer_modes"), list)
            and bool(clarification.get("answer_modes"))
        )
        return (
            final.get("status") == "succeeded"
            and published
            and final.get("clarification_answer_applied") is True
            and counts.get("stage1") == 1
            and counts.get("property_resolution") == 1
            and counts.get("stage2") == 1
            and strict_ok
            and initial_stop_ok
            and clarification.get("reason_code") == "property_resolution"
            and clarification.get("answer_modes")
            == [
                "select_candidate",
                "add_detail",
                "cancel",
            ]
        )
    if case.case_id == "window-semantic-canary":
        strict = final.get("strict_reopen_verification")
        strict_ok = (
            isinstance(strict, Mapping)
            and strict.get("status") == "passed"
            and strict.get("l0_pass") is True
            and strict.get("l1_pass") is True
            and strict.get("l2_pass") is True
        )
        return (
            final.get("status") == "succeeded"
            and published
            and counts.get("stage1") == 1
            and counts.get("property_resolution") == 1
            and counts.get("stage2") == 1
            and strict_ok
        )
    if case.case_id == "program-guard":
        guard = final.get("program_guard_evidence")
        guard_ok = (
            isinstance(guard, Mapping)
            and guard.get("source_reference") == str(SOURCE.resolve())
            and guard.get("source_sha256_before") == FROZEN_SOURCE_SHA256
            and guard.get("source_sha256_after") == FROZEN_SOURCE_SHA256
            and guard.get("source_unchanged") is True
            and guard.get("stage2_attempts") == 0
            and guard.get("candidate_output_paths") == []
            and guard.get("mutation_attempted") is False
        )
        return (
            final.get("status") == "unsupported"
            and final.get("reason_code") == PROGRAM_GUARD_REASON
            and not published
            and counts.get("stage1") == 1
            and counts.get("property_resolution") == 0
            and counts.get("stage2") == 0
            and guard_ok
        )
    return False


def _base_result(*, evidence_mode: str) -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/phase12-live-uat/0.1",
        "evidence_mode": evidence_mode,
        "synthetic_fallback_used": False,
        "token_guard": {
            "max_input_tokens": TOKEN_GUARD,
            "max_completion_tokens": TOKEN_GUARD,
        },
        "transport_calls": 0,
        "transport_calls_by_stage": {
            "stage1": 0,
            "property_resolution": 0,
            "stage2": 0,
        },
        "provider_models": [],
        "cases": [],
    }


def _close_property_runtime(runtime: Any | None) -> None:
    if runtime is None:
        return
    close = getattr(getattr(runtime, "vector_index", None), "close", None)
    if callable(close):
        close()


def _open_property_runtime(
    factory: Callable[[], Any],
) -> tuple[Any | None, dict[str, Any]]:
    try:
        runtime = factory()
    except Exception as error:
        return None, {
            "status": "not_ready",
            "reason_code": str(error).split(":", 1)[0][:128]
            or type(error).__name__,
            "acceptance_eligible": False,
        }
    health = getattr(runtime, "health", None)
    readiness = (
        dict(health.to_dict())
        if health is not None and callable(getattr(health, "to_dict", None))
        else {
            "status": "not_ready",
            "reason_code": "PROPERTY_RUNTIME_HEALTH_REQUIRED",
            "acceptance_eligible": False,
        }
    )
    if (
        readiness.get("status") == "ready"
        and readiness.get("acceptance_eligible") is True
    ):
        return runtime, readiness
    _close_property_runtime(runtime)
    return None, readiness


def run_live_uat(
    output_root: Path | str,
    *,
    transport_factory: Callable[[], Any],
    command_runner: Callable[..., subprocess.CompletedProcess[str]] = (
        _default_command_runner
    ),
    case_executor: Callable[[LiveCase, TranscriptProvider, Path], Mapping[str, Any]] = (
        _production_case_executor
    ),
    cases: Sequence[LiveCase] = DEFAULT_CASES,
    proof_root: Path | str = DEFAULT_PROOF_ROOT,
    evidence_mode: str = LIVE_EVIDENCE_MODE,
    preflight_only: bool = False,
    property_runtime_factory: Callable[[], Any] | None = None,
    admission_evidence_path: Path | str | None = None,
) -> dict[str, Any]:
    """Execute live cases only after independently verified preflight."""

    output = Path(output_root).resolve()
    output.mkdir(parents=True, exist_ok=False)
    result = _base_result(evidence_mode=evidence_mode)
    if evidence_mode != LIVE_EVIDENCE_MODE:
        result.update(
            {
                "status": "blocked",
                "reason_code": "LIVE_EVIDENCE_MODE_REQUIRED",
                "preflight": {"status": "not_run", "checks": []},
            }
        )
        _write_json(output / "live-uat-result.json", result)
        return result

    injected_preflight = command_runner is not _default_command_runner
    injected_executor = case_executor is not _production_case_executor
    if injected_preflight != injected_executor:
        result.update(
            {
                "status": "blocked",
                "reason_code": "LIVE_TEST_SEAMS_MUST_BE_PAIRED",
                "preflight": {"status": "not_run", "checks": []},
            }
        )
        _write_json(output / "live-uat-result.json", result)
        return result

    test_injected = injected_preflight and injected_executor
    result.update(
        {
            "execution_mode": (
                "preflight_only"
                if preflight_only
                else ("test_injected" if test_injected else "production_live")
            ),
            "provider_evidence_mode": (
                "not_run"
                if preflight_only
                else ("test_injected" if test_injected else LIVE_EVIDENCE_MODE)
            ),
            "runner_contract_eligible": not test_injected and not preflight_only,
            # The live runner proves the Plan 12-13 transcript contract only.
            # Plan 12-14 separately recomputes preservation and Ground Truth
            # isolation before any run can enter accepted Proof.
            "acceptance_eligible": False,
            "proof_acceptance_eligible": False,
            "proof_validation_status": PROOF_VALIDATION_PENDING,
        }
    )

    if admission_evidence_path is None:
        preflight = run_preflight(
            output / "preflight",
            proof_root=Path(proof_root).resolve(),
            command_runner=command_runner,
        )
    else:
        try:
            preflight = _load_changed_scope_admission(
                admission_evidence_path
            )
        except Exception as error:
            preflight = {
                "schema_version": CHANGED_SCOPE_ADMISSION_SCHEMA,
                "status": "failed",
                "mode": "changed_scope_evidence_reuse",
                "reason_code": str(error).split(":", 1)[0][:128],
                "network_transport_attempted": False,
            }
    result["preflight"] = preflight
    if preflight["status"] != "passed":
        result.update(
            {
                "status": "preflight_failed",
                "reason_code": "LIVE_PREFLIGHT_NOT_GREEN",
            }
        )
        _write_json(output / "live-uat-result.json", result)
        return result

    if preflight_only:
        if case_executor is _ORIGINAL_PRODUCTION_CASE_EXECUTOR:
            factory = property_runtime_factory or (
                lambda: create_property_runtime_from_environment(
                    project_root=ROOT
                )
            )
            runtime, readiness = _open_property_runtime(factory)
            result["property_runtime_readiness"] = readiness
            if runtime is None:
                result.update(
                    {
                        "status": "preflight_failed",
                        "reason_code": readiness.get("reason_code")
                        or "PROPERTY_RUNTIME_NOT_READY",
                    }
                )
                _write_json(output / "live-uat-result.json", result)
                return result
            _close_property_runtime(runtime)
        result.update(
            {
                "status": "preflight_passed",
                "reason_code": None,
                "evidence_mode": "not_run",
                "transport_calls": 0,
                "transport_calls_by_stage": {
                    "stage1": 0,
                    "property_resolution": 0,
                    "stage2": 0,
                },
                "provider_models": [],
                "cases": [],
            }
        )
        _write_json(output / "live-uat-result.json", result)
        return result

    case_ids = tuple(case.case_id for case in cases)
    required_case_matrix_sha256 = FROZEN_CASE_MATRIX_SHA256
    current_default_case_matrix_sha256 = _case_matrix_sha256(DEFAULT_CASES)
    provided_case_matrix_sha256 = _case_matrix_sha256(cases)
    if (
        case_ids != REQUIRED_CASE_IDS
        or current_default_case_matrix_sha256 != required_case_matrix_sha256
        or provided_case_matrix_sha256 != required_case_matrix_sha256
    ):
        result.update(
            {
                "status": "blocked",
                "reason_code": "LIVE_CASE_MATRIX_REQUIRED",
                "required_case_ids": list(REQUIRED_CASE_IDS),
                "provided_case_ids": list(case_ids),
                "required_case_matrix_sha256": required_case_matrix_sha256,
                "current_default_case_matrix_sha256": (
                    current_default_case_matrix_sha256
                ),
                "provided_case_matrix_sha256": provided_case_matrix_sha256,
            }
        )
        _write_json(output / "live-uat-result.json", result)
        return result

    transport = transport_factory()
    production_transport_valid = _approved_deepseek_transport(transport)
    if not test_injected and not production_transport_valid:
        result.update(
            {
                "status": "blocked",
                "reason_code": "LIVE_DEEPSEEK_TRANSPORT_REQUIRED",
                "runner_contract_eligible": False,
                "acceptance_eligible": False,
            }
        )
        _write_json(output / "live-uat-result.json", result)
        return result

    property_runtime = None
    if case_executor is _ORIGINAL_PRODUCTION_CASE_EXECUTOR:
        factory = property_runtime_factory or (
            lambda: create_property_runtime_from_environment(project_root=ROOT)
        )
        property_runtime, readiness = _open_property_runtime(factory)
        result["property_runtime_readiness"] = readiness
        if property_runtime is None:
            result.update(
                {
                    "status": "blocked",
                    "reason_code": readiness.get("reason_code")
                    or "PROPERTY_RUNTIME_NOT_READY",
                    "runner_contract_eligible": False,
                    "acceptance_eligible": False,
                }
            )
            _write_json(output / "live-uat-result.json", result)
            return result
    provider = TranscriptProvider(transport)
    case_results: list[dict[str, Any]] = []
    for case in cases:
        provider.set_case(case.case_id)
        before = len(provider.attempts)
        case_root = output / "cases" / case.case_id
        case_root.mkdir(parents=True)
        try:
            if property_runtime is None:
                final = dict(case_executor(case, provider, case_root))
            else:
                final = dict(
                    case_executor(
                        case,
                        provider,
                        case_root,
                        property_knowledge_runtime=property_runtime,
                    )
                )
        except Exception as error:
            final = {
                "status": "provider_failed",
                "reason_code": str(
                    getattr(error, "code", None)
                    or str(error)
                    or type(error).__name__
                )[:128],
                "complete_repair_success": False,
                "successful_artifact_publishable": False,
            }
        final_private_evidence = _private_evidence_detected(final)
        final = _redact_for_evidence(final)
        attempts = provider.attempts[before:]
        call_counts = _counts(attempts)
        live_evidence_pass = _live_attempt_evidence_pass(attempts)
        contract_pass = (
            live_evidence_pass
            and not final_private_evidence
            and _case_contract_pass(
                case,
                final,
                call_counts,
            )
        )
        case_result = {
            "case_id": case.case_id,
            "status": "passed" if contract_pass else "failed",
            "request_sha256": _text_sha256(case.request),
            "feedback_sha256": (
                None if case.feedback is None else _text_sha256(case.feedback)
            ),
            "final": final,
            "attempts": attempts,
            "transport_calls": len(attempts),
            "transport_calls_by_stage": call_counts,
            "synthetic_fallback_used": False,
            "live_evidence_pass": live_evidence_pass,
            "private_evidence_detected": final_private_evidence,
            "contract_pass": contract_pass,
            "proof_acceptance_eligible": False,
            "proof_validation_status": PROOF_VALIDATION_PENDING,
        }
        _write_json(case_root / "case-result.json", case_result)
        case_results.append(case_result)

    aggregate_counts = _counts(provider.attempts)
    models = sorted(
        {
            (str(item.get("provider")), str(item.get("model")))
            for item in provider.attempts
            if item.get("provider") and item.get("model")
        }
    )
    result.update(
        {
            "status": (
                ("test_passed" if test_injected else "passed")
                if all(item["contract_pass"] for item in case_results)
                else "failed"
            ),
            "reason_code": (
                None
                if all(item["contract_pass"] for item in case_results)
                else "LIVE_CASE_CONTRACT_FAILED"
            ),
            "transport_calls": len(provider.attempts),
            "transport_calls_by_stage": aggregate_counts,
            "provider_models": [
                {"provider": provider_name, "model": model}
                for provider_name, model in models
            ],
            "cases": case_results,
        }
    )
    _close_property_runtime(property_runtime)
    _write_json(output / "live-uat-result.json", result)
    return result


def _environment(path: Path) -> dict[str, str]:
    values = dict(os.environ)
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _config(environment: Mapping[str, str]) -> dict[str, Any]:
    value = load_openai_compatible_config(dict(environment))
    ready = (
        bool(value.get("configured"))
        and value.get("max_input_tokens") == TOKEN_GUARD
        and value.get("max_completion_tokens") == TOKEN_GUARD
    )
    return {
        "status": "ready" if ready else "not_configured",
        "provider": value.get("provider"),
        "provider_key": value.get("provider_key"),
        "model": value.get("model"),
        "max_input_tokens": value.get("max_input_tokens"),
        "max_completion_tokens": value.get("max_completion_tokens"),
        "secret_redacted": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--provider", choices=("deepseek",), default="deepseek")
    parser.add_argument("--require-green-preflight", action="store_true")
    parser.add_argument("--changed-scope-admission", type=Path)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--proof-root", type=Path, default=DEFAULT_PROOF_ROOT)
    parser.add_argument("--evidence-mode", default=LIVE_EVIDENCE_MODE)
    args = parser.parse_args(argv)
    if args.preflight_only:
        if args.check_config:
            parser.error("--check-config and --preflight-only are mutually exclusive")
        run_dir = args.output_root / datetime.now(timezone.utc).strftime(
            "preflight-%Y%m%dT%H%M%S%fZ"
        )

        def forbidden_transport_factory() -> Any:
            raise AssertionError("preflight-only must not construct Provider transport")

        environment = _environment(args.env_file)

        result = run_live_uat(
            run_dir,
            transport_factory=forbidden_transport_factory,
            proof_root=args.proof_root,
            evidence_mode=args.evidence_mode,
            preflight_only=True,
            property_runtime_factory=lambda: (
                create_property_runtime_from_environment(
                    environment,
                    project_root=ROOT,
                )
            ),
            admission_evidence_path=args.changed_scope_admission,
        )
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "transport_calls": result["transport_calls"],
                    "result": str(run_dir / "live-uat-result.json"),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0 if result["status"] == "preflight_passed" else 2

    environment = _environment(args.env_file)
    config = _config(environment)
    if args.check_config:
        print(json.dumps(config, ensure_ascii=False, sort_keys=True))
        return 0 if config["status"] == "ready" else 2
    if not args.require_green_preflight:
        parser.error("--require-green-preflight is mandatory for live execution")
    if (
        config["status"] != "ready"
        or config.get("provider_key") != args.provider
    ):
        print(json.dumps(config, ensure_ascii=False, sort_keys=True))
        return 2
    run_dir = args.output_root / datetime.now(timezone.utc).strftime(
        "uat-%Y%m%dT%H%M%S%fZ"
    )

    def transport_factory() -> OpenAICompatibleLiveProvider:
        runtime = load_openai_compatible_runtime_config(environment)
        return OpenAICompatibleLiveProvider(config=runtime)

    result = run_live_uat(
        run_dir,
        transport_factory=transport_factory,
        proof_root=args.proof_root,
        evidence_mode=args.evidence_mode,
        property_runtime_factory=lambda: (
            create_property_runtime_from_environment(
                environment,
                project_root=ROOT,
            )
        ),
        admission_evidence_path=args.changed_scope_admission,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "transport_calls": result["transport_calls"],
                "result": str(run_dir / "live-uat-result.json"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
