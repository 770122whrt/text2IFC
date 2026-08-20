"""Preflight-gated, transcript-preserving Phase 12 live structural UAT.

The transport factory is deliberately invoked only after all six offline
preflight gates have been executed and machine-verified.  Tests inject a mock
transport at this public seam; the CLI creates the live Provider lazily after
the same gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence
from urllib.parse import urlsplit

import ifcopenshell


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scripts.ifc_repair.validate_success_cases import (  # noqa: E402
    audit_repaired_operations,
)
from text2ifc_agent.openai_compat import (  # noqa: E402
    OpenAICompatibleLiveProvider,
    load_openai_compatible_config,
    load_openai_compatible_runtime_config,
)
from text2ifc_agent.providers import (  # noqa: E402
    ProviderOutputError,
    redact_provider_payload,
)
from text2ifc_ifc_repair.api import RepairAPI  # noqa: E402
from text2ifc_ifc_repair.repair_intent import (  # noqa: E402
    REPAIR_INTENT_SCHEMA_VERSION_0_8,
)
from text2ifc_knowledge.property_search import (  # noqa: E402
    create_default_property_resolver,
)


DEFAULT_OUTPUT = ROOT / "dataset/processed/ifc-repair-runs/phase12-live"
DEFAULT_PROOF_ROOT = (
    ROOT / "dataset/processed/proof/ifc-repair-success-cases"
)
SOURCE = (
    DEFAULT_PROOF_ROOT
    / "structural/batch/phase12-d7n-beam-column-atomic/damaged.ifc"
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
    'On the IFC Building Storey named "Level 1", add one vertical rectangular '
    "Column. The complete center axis, rectangular section dimensions, and "
    "local width direction are not specified; do not infer them."
)
CLARIFICATION_ANSWER = (
    'Use a vertical Column on the IFC Building Storey named "Level 1". Its '
    "center axis is base (120000, 120000, 0) mm to top "
    "(120000, 120000, 6000) mm; its rectangular section is 400 mm wide and "
    "600 mm deep, with local width direction (0, 1)."
)
PROGRAM_GUARD_REQUEST = (
    'On the IFC Building Storey named "Level 1", add a straight rectangular '
    "Beam and attach a structural analysis node; structural analysis "
    "relationships are outside this operation contract."
)
PROGRAM_GUARD_REASON = "STRUCTURAL_ANALYSIS_UNSUPPORTED"


class LiveCase:
    """One fixed public live case; intentionally simple for importlib seams."""

    __slots__ = ("case_id", "request", "feedback")

    def __init__(
        self,
        *,
        case_id: str,
        request: str,
        feedback: str | None = None,
    ) -> None:
        if not case_id or not request.strip():
            raise ValueError("LIVE_CASE_ID_AND_REQUEST_REQUIRED")
        self.case_id = case_id
        self.request = request
        self.feedback = feedback


DEFAULT_CASES = (
    LiveCase(case_id="complete", request=COMPLETE_REQUEST),
    LiveCase(
        case_id="clarification-resume",
        request=CLARIFICATION_REQUEST,
        feedback=CLARIFICATION_ANSWER,
    ),
    LiveCase(case_id="program-guard", request=PROGRAM_GUARD_REQUEST),
)
REQUIRED_CASE_IDS = tuple(case.case_id for case in DEFAULT_CASES)
FROZEN_CASE_MATRIX_SHA256 = (
    "sha256:1b9b181f42ca9eccdda5cffac323cb5c"
    "ec67633bf4859c1000e9f7324681fd2b"
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


def _prompt_identities(prompt: str) -> dict[str, list[str]]:
    hash_pattern = r"(sha256:[0-9a-f]{64})"
    explicit_few_shot_hashes = _unique_matches(
        rf'"(?:example_hash|few_shot_hash)"\s*:\s*"{hash_pattern}"',
        prompt,
    )
    referenced_few_shot_hashes = _unique_matches(
        rf'"example_id"\s*:\s*"[^"]+"[\s\S]{{0,320}}?'
        rf'"sha256"\s*:\s*"{hash_pattern}"',
        prompt,
    )
    return {
        "profile_ids": _unique_matches(
            r'"profile_id"\s*:\s*"([^"]+)"', prompt
        ),
        "profile_versions": _unique_matches(
            r'"profile_version"\s*:\s*"([^"]+)"', prompt
        ),
        "profile_hashes": _unique_matches(
            rf'"profile_hash"\s*:\s*"{hash_pattern}"', prompt
        ),
        "few_shot_ids": _unique_matches(
            r'"(?:example_id|few_shot_id)"\s*:\s*"([^"]+)"',
            prompt,
        ),
        "few_shot_hashes": list(
            dict.fromkeys(
                [*explicit_few_shot_hashes, *referenced_few_shot_hashes]
            )
        ),
    }


def _correction_reason(prompt: str, stage_attempt: int) -> str | None:
    if stage_attempt <= 1:
        return None
    codes = _unique_matches(r'"code"\s*:\s*"([A-Z0-9_]+)"', prompt)
    return codes[-1] if codes else "VALIDATION_CORRECTION"


def _stage_name(raw: Any) -> str:
    stage = str(raw)
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
    if tuple(command[1:]) == ("-m", "pytest", "tests/ifc_repair", "-q"):
        timeout_seconds = 7_200
    elif "test_phase12_live_uat.py" in rendered:
        timeout_seconds = 180
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
    offline_output = preflight_root / "offline-matrix"
    return (
        (
            "focused",
            (
                python,
                "-m",
                "pytest",
                "tests/ifc_repair/test_phase12_live_uat.py",
                "-q",
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
            (python, "-m", "pytest", "tests/ifc_repair", "-q"),
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
            == "text2ifc/ifc-repair-proof-validation/0.1"
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
    preflight_root.mkdir(parents=True, exist_ok=True)
    logs = preflight_root / "logs"
    logs.mkdir()
    checks: list[dict[str, Any]] = []
    for name, command in _preflight_commands(preflight_root, proof_root):
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
        record = {
            "name": name,
            "command": list(command),
            "exit_code": int(completed.returncode),
            "status": "passed" if reason is None else "failed",
            "reason_code": reason,
            "stdout_sha256": _text_sha256(stdout),
            "stderr_sha256": _text_sha256(stderr),
            "artifacts": [
                _artifact_record(path, root=preflight_root)
                for path in artifact_paths
            ],
        }
        record["result_sha256"] = _canonical_sha256(record)
        checks.append(record)
    status = "passed" if all(item["status"] == "passed" for item in checks) else "failed"
    result = {
        "schema_version": "text2ifc/phase12-live-preflight/0.1",
        "status": status,
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


def _production_case_executor(
    case: LiveCase,
    provider: TranscriptProvider,
    case_root: Path,
) -> dict[str, Any]:
    runtime = case_root / "runtime"
    source_sha256_before = _path_sha256(SOURCE)
    if source_sha256_before != FROZEN_SOURCE_SHA256:
        raise ValueError("LIVE_SOURCE_HASH_MISMATCH")
    api = RepairAPI(
        runtime,
        provider=provider,
        intent_schema_version=REPAIR_INTENT_SCHEMA_VERSION_0_8,
        property_knowledge_resolver=create_default_property_resolver(),
    )
    provider.set_lineage("initial")
    initial = api.start(SOURCE, case.request)
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
        final = api.continue_with_answer(
            initial.run_id,
            {"kind": "add_detail", "detail": case.feedback},
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
        source_sha256_after = _path_sha256(SOURCE)
        stage2_attempts = sum(
            1
            for attempt in provider.attempts
            if attempt.get("case_id") == case.case_id
            and attempt.get("stage") == "stage2"
        )
        program_guard_evidence = {
            "source_reference": str(SOURCE.resolve()),
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


def _counts(attempts: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    result = {"stage1": 0, "stage2": 0}
    for attempt in attempts:
        stage = str(attempt.get("stage"))
        if stage in result:
            result[stage] += 1
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
        few_shot_ids = attempt.get("few_shot_ids")
        few_shot_hashes = attempt.get("few_shot_hashes")
        if not isinstance(metadata, Mapping):
            return False
        if not isinstance(usage, Mapping) or not usage:
            return False
        if not isinstance(fallback_flags, Mapping):
            return False
        if (
            not isinstance(profile_ids, list)
            or not profile_ids
            or not isinstance(profile_versions, list)
            or not profile_versions
            or not isinstance(profile_hashes, list)
            or not profile_hashes
        ):
            return False
        if attempt.get("stage") == "stage2" and (
            not isinstance(few_shot_ids, list)
            or not few_shot_ids
            or not isinstance(few_shot_hashes, list)
            or not few_shot_hashes
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
            and counts.get("stage1", 0) >= 1
            and counts.get("stage2", 0) >= 1
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
            and counts.get("stage1") == 2
            and counts.get("stage2") == 1
            and strict_ok
            and initial_stop_ok
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
            and counts.get("stage2") == 0
            and guard_ok
        )
    return True


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
        "transport_calls_by_stage": {"stage1": 0, "stage2": 0},
        "provider_models": [],
        "cases": [],
    }


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

    preflight = run_preflight(
        output / "preflight",
        proof_root=Path(proof_root).resolve(),
        command_runner=command_runner,
    )
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
        result.update(
            {
                "status": "preflight_passed",
                "reason_code": None,
                "evidence_mode": "not_run",
                "transport_calls": 0,
                "transport_calls_by_stage": {"stage1": 0, "stage2": 0},
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
    provider = TranscriptProvider(transport)
    case_results: list[dict[str, Any]] = []
    for case in cases:
        provider.set_case(case.case_id)
        before = len(provider.attempts)
        case_root = output / "cases" / case.case_id
        case_root.mkdir(parents=True)
        try:
            final = dict(case_executor(case, provider, case_root))
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

        result = run_live_uat(
            run_dir,
            transport_factory=forbidden_transport_factory,
            proof_root=args.proof_root,
            evidence_mode=args.evidence_mode,
            preflight_only=True,
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
