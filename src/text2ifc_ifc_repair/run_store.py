"""Atomic, append-only persistence for repair-scoped orchestration runs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Iterator, Mapping

from jsonschema import Draft202012Validator, ValidationError
from .run_models import (
    CLARIFICATION_SCHEMA_PATH,
    RESULT_SCHEMA_PATH,
    RUN_STATE_SCHEMA_PATH,
    TERMINAL_STAGES,
    Clarification,
    RunResult,
    RunStage,
    RunState,
    RunStoreCode,
    RunStoreError,
    RunTransition,
    SourceBinding,
    canonical_json,
    freeze_json,
    hash_json,
    load_run_schema,
    thaw_json,
)


_RUN_ID = re.compile(r"^repair-[a-z0-9][a-z0-9-]{0,95}$")
_PUBLIC_RECORD_LIMIT = 16 * 1024
_STAGE_PAYLOAD_LIMIT = 256 * 1024
_PRIVATE_CANARIES = (
    "private_original_ifc",
    "mutation_manifest.private.json",
    "mutation_mapping",
    "benchmark_gold",
    "provider_secret",
    "api_key",
)
_PUBLICATION_JOURNAL = ".terminal-publication.json"
_PROGRESS = (
    RunStage.CREATED,
    RunStage.SOURCE_VALIDATED,
    RunStage.INDEX_READY,
    RunStage.INTENT_READY,
    RunStage.TARGETS_RESOLVED,
    RunStage.CHANGESET_READY,
    RunStage.APPLICATION_READY,
    RunStage.EVALUATED,
)
_FAILURES = TERMINAL_STAGES - {RunStage.SUCCEEDED}


def _is_link_or_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    reparse_flag = getattr(__import__("stat"), "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


class RunStore:
    """Filesystem store with one exclusive mutation lock per generated run."""

    def __init__(self, root: Path | str) -> None:
        requested = Path(root)
        if requested.exists() and requested.is_symlink():
            raise RunStoreError(RunStoreCode.SYMLINK_REJECTED, "output root is a symlink")
        requested.mkdir(parents=True, exist_ok=True)
        self.root = requested.resolve()
        self.runs_root = self.root / "runs"
        if self.runs_root.exists() and self.runs_root.is_symlink():
            raise RunStoreError(RunStoreCode.SYMLINK_REJECTED, "runs root is a symlink")
        self.runs_root.mkdir(parents=True, exist_ok=True)

    def start_run(
        self,
        *,
        source_path: Path | str,
        request_id: str,
        request_text: str | None = None,
        source_request_hash: str | None = None,
        run_id: str | None = None,
    ) -> RunState:
        active_id = self._new_run_id() if run_id is None else run_id
        self._validate_run_id(active_id)
        if not request_id or len(request_id) > 128:
            raise RunStoreError(RunStoreCode.PUBLIC_RECORD_INVALID, "request_id is invalid")
        if (request_text is None) == (source_request_hash is None):
            raise RunStoreError(
                RunStoreCode.PUBLIC_RECORD_INVALID,
                "provide exactly one of request_text or source_request_hash",
            )
        request_hash = (
            self._hash_bytes(request_text.encode("utf-8"))
            if request_text is not None
            else str(source_request_hash)
        )
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", request_hash):
            raise RunStoreError(RunStoreCode.PUBLIC_RECORD_INVALID, "request hash is invalid")

        source_input = Path(source_path)
        if source_input.is_symlink():
            raise RunStoreError(RunStoreCode.SYMLINK_REJECTED, "source IFC is a symlink")
        source = source_input.resolve(strict=True)
        if not source.is_file():
            raise RunStoreError(RunStoreCode.SOURCE_INVALID, "source IFC is not a file")
        source_bytes = source.read_bytes()
        if not source_bytes:
            raise RunStoreError(RunStoreCode.SOURCE_INVALID, "source IFC is empty")
        binding = SourceBinding(
            reference=str(source),
            sha256=self._hash_bytes(source_bytes),
            size_bytes=len(source_bytes),
        )

        run_dir = self._run_dir(active_id, require_exists=False)
        try:
            run_dir.mkdir(exist_ok=False)
        except FileExistsError as error:
            raise RunStoreError(
                RunStoreCode.RUN_ALREADY_EXISTS, f"run already exists: {active_id}"
            ) from error
        (run_dir / "transitions").mkdir(exist_ok=False)
        try:
            initial = self._build_transition(
                transition_id=0,
                from_stage=None,
                to_stage=RunStage.CREATED,
                previous_hash=None,
                stage_payload={
                    "request_hash": request_hash,
                    "source_sha256": binding.sha256,
                },
            )
            state = RunState(
                run_id=active_id,
                state_version=0,
                request_id=request_id,
                request_hash=request_hash,
                source=binding,
                stage=RunStage.CREATED,
                transitions=(initial,),
            )
            self._validate_state(state)
            self._write_transition(run_dir, initial)
            self._atomic_write_json(run_dir / "state.json", state.to_dict())
            return state
        except Exception:
            # A newly-created run that never obtained a committed state is not a run.
            self._remove_empty_start(run_dir)
            raise

    def load(self, run_id: str) -> RunState:
        run_dir = self._run_dir(run_id, require_exists=True)
        self._recover_terminal_publication(run_dir)
        state = self._read_state(run_dir)
        self._validate_source(state.source)
        return state

    def _read_state(self, run_dir: Path) -> RunState:
        state_path = run_dir / "state.json"
        try:
            document = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "state.json is unreadable") from error
        try:
            self._state_validator().validate(document)
            state = RunState.from_dict(document)
        except (ValidationError, KeyError, TypeError, ValueError) as error:
            raise RunStoreError(RunStoreCode.SCHEMA_INVALID, str(error)) from error
        self._validate_loaded_state(run_dir, state)
        return state

    def commit_terminal_publication(
        self,
        run_id: str,
        *,
        prepared_root: str,
        to_stage: RunStage,
        expected_state_version: int,
        reason_code: str | None,
        stage_payload: Mapping[str, Any],
        result_artifacts: Mapping[str, str],
        answer: Mapping[str, Any] | None = None,
        clarification_id: str | None = None,
        fault_injector: Any | None = None,
    ) -> RunState:
        """Promote one hidden bundle and commit its terminal state recoverably."""

        run_dir = self._run_dir(run_id, require_exists=True)
        with self._exclusive_lock(run_dir):
            current = self._read_state(run_dir)
            self._validate_source(current.source)
            if current.state_version != expected_state_version:
                raise RunStoreError(
                    RunStoreCode.STATE_CONFLICT,
                    f"expected version {expected_state_version}, found {current.state_version}",
                )
            clean_answer = None
            if answer is not None:
                clarification = current.clarification
                if (
                    current.stage is not RunStage.CLARIFICATION_REQUIRED
                    or clarification is None
                    or clarification.clarification_id != clarification_id
                ):
                    raise RunStoreError(RunStoreCode.STATE_CONFLICT, "clarification binding is stale")
                clean_answer = self._validate_answer(clarification, answer)
                if clean_answer["kind"] not in {"cancel", "eof"} or to_stage is not RunStage.CANCELLED:
                    raise RunStoreError(RunStoreCode.ANSWER_INVALID, "terminal answer must cancel")
                self._validate_transition(
                    current.stage, to_stage, resume_stage=clarification.resume_stage
                )
            else:
                self._validate_transition(current.stage, to_stage)

            prepared = self._safe_run_child(run_dir, prepared_root, require_exists=True, require_directory=True)
            match = re.fullmatch(r"\.terminal-prepared-([0-9a-f]{32})", prepared.name)
            if match is None or prepared.parent != run_dir:
                raise RunStoreError(RunStoreCode.PATH_ESCAPE, "invalid prepared publication root")
            bundle_rel = f".terminal-bundles/{match.group(1)}"
            bundles_root = self._safe_run_child(
                run_dir, ".terminal-bundles", require_exists=False
            )
            if bundles_root.exists() and _is_link_or_reparse(bundles_root):
                raise RunStoreError(RunStoreCode.PATH_ESCAPE, "publication root follows a link")
            bundles_root.mkdir(exist_ok=True)
            destination = self._safe_run_child(run_dir, bundle_rel, require_exists=False)
            if destination.exists():
                raise RunStoreError(RunStoreCode.STATE_CONFLICT, "publication bundle already exists")

            mapped = self._map_prepared_artifacts(
                run_dir, prepared, bundle_rel, result_artifacts
            )
            self._verify_prepared_manifest(prepared, bundle_rel, mapped)
            manifest = prepared / Path(mapped["manifest"]).relative_to(bundle_rel)
            payload = thaw_json(freeze_json(stage_payload))
            payload["manifest"] = {
                "path": mapped["manifest"],
                "sha256": self._hash_bytes(manifest.read_bytes()),
                "schema_version": "text2ifc/ifc-repair-artifact-manifest/0.1",
            }
            new_version = current.state_version + 1
            transition = self._build_transition(
                transition_id=new_version,
                from_stage=current.stage,
                to_stage=to_stage,
                previous_hash=current.transitions[-1].record_hash,
                stage_payload=payload,
                answer=clean_answer,
                reason_code=reason_code,
                result_artifacts=mapped,
            )
            state = replace(
                current,
                state_version=new_version,
                stage=to_stage,
                transitions=(*current.transitions, transition),
                clarification=None,
                reason_code=reason_code,
                result_artifacts=mapped,
            )
            self._validate_state(state)
            journal = {
                "schema_version": "text2ifc/ifc-repair-terminal-publication/0.1",
                "expected_state_version": expected_state_version,
                "prepared_root": prepared.name,
                "destination_root": bundle_rel,
                "transition": transition.to_dict(),
                "state": state.to_dict(),
            }
            journal_path = run_dir / _PUBLICATION_JOURNAL
            if journal_path.exists():
                raise RunStoreError(RunStoreCode.STATE_CONFLICT, "publication recovery pending")
            self._atomic_write_json(journal_path, journal, replace_existing=False)
            if fault_injector is not None:
                fault_injector("after_journal")
            os.replace(prepared, destination)
            self._fsync_directory(destination.parent)
            if fault_injector is not None:
                fault_injector("after_promotion")
            self._write_transition(run_dir, transition)
            if fault_injector is not None:
                fault_injector("before_state_replace")
            self._atomic_write_json(run_dir / "state.json", state.to_dict())
            if fault_injector is not None:
                fault_injector("after_state_replace")
            journal_path.unlink()
            self._fsync_directory(run_dir)
            return state

    def prepare_stage_directory(self, run_id: str, relative: str) -> Path:
        """Create or validate a no-follow stage directory below one run."""
        run_dir = self._run_dir(run_id, require_exists=True)
        path = self._safe_run_child(run_dir, relative, require_exists=False)
        with self._exclusive_lock(run_dir):
            if path.exists():
                self._safe_run_child(run_dir, relative, require_exists=True, require_directory=True)
            else:
                path.mkdir(parents=False, exist_ok=False)
                self._safe_run_child(run_dir, relative, require_exists=True, require_directory=True)
        return path

    def artifact_binding(self, run_id: str, relative: str, schema_version: str) -> dict[str, Any]:
        run_dir = self._run_dir(run_id, require_exists=True)
        path = self._safe_run_child(run_dir, relative, require_exists=True)
        if not path.is_file():
            raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "bound artifact is not a file")
        return {
            "path": relative.replace("\\", "/"),
            "sha256": self._hash_bytes(path.read_bytes()),
            "schema_version": schema_version,
        }

    def transition(
        self,
        run_id: str,
        *,
        to_stage: RunStage,
        expected_state_version: int,
        stage_payload: Mapping[str, Any] | None = None,
        clarification: Clarification | None = None,
        answer: Mapping[str, Any] | None = None,
        reason_code: str | None = None,
        result_artifacts: Mapping[str, str] | None = None,
    ) -> RunState:
        run_dir = self._run_dir(run_id, require_exists=True)
        with self._exclusive_lock(run_dir):
            current = self.load(run_id)
            if current.state_version != expected_state_version:
                raise RunStoreError(
                    RunStoreCode.STATE_CONFLICT,
                    f"expected version {expected_state_version}, found {current.state_version}",
                )
            self._validate_transition(current.stage, to_stage)
            new_version = current.state_version + 1
            if to_stage is RunStage.CLARIFICATION_REQUIRED:
                if clarification is None:
                    raise RunStoreError(
                        RunStoreCode.PUBLIC_RECORD_INVALID,
                        "clarification_required needs a clarification record",
                    )
                self._validate_clarification(clarification, current.run_id, new_version)
            elif clarification is not None:
                raise RunStoreError(
                    RunStoreCode.PUBLIC_RECORD_INVALID,
                    "clarification is only valid for clarification_required",
                )
            artifacts = self._validate_artifacts(run_dir, result_artifacts or {})
            payload = {} if stage_payload is None else thaw_json(freeze_json(stage_payload))
            if len(canonical_json(payload).encode("utf-8")) > _STAGE_PAYLOAD_LIMIT:
                raise RunStoreError(
                    RunStoreCode.PUBLIC_RECORD_TOO_LARGE, "stage payload exceeds limit"
                )
            transition = self._build_transition(
                transition_id=new_version,
                from_stage=current.stage,
                to_stage=to_stage,
                previous_hash=current.transitions[-1].record_hash,
                stage_payload=payload,
                clarification=clarification,
                answer=answer,
                reason_code=reason_code,
                result_artifacts=artifacts,
            )
            state = replace(
                current,
                state_version=new_version,
                stage=to_stage,
                transitions=(*current.transitions, transition),
                clarification=clarification,
                reason_code=reason_code,
                result_artifacts=artifacts,
            )
            self._validate_state(state)
            self._write_transition(run_dir, transition)
            self._atomic_write_json(run_dir / "state.json", state.to_dict())
            return state

    def continue_with_answer(
        self,
        run_id: str,
        *,
        clarification_id: str,
        expected_state_version: int,
        answer: Mapping[str, Any],
        stage_payload: Mapping[str, Any] | None = None,
        result_artifacts: Mapping[str, str] | None = None,
    ) -> RunState:
        run_dir = self._run_dir(run_id, require_exists=True)
        with self._exclusive_lock(run_dir):
            current = self.load(run_id)
            if current.state_version != expected_state_version:
                raise RunStoreError(
                    RunStoreCode.STATE_CONFLICT,
                    f"expected version {expected_state_version}, found {current.state_version}",
                )
            clarification = current.clarification
            if current.stage is not RunStage.CLARIFICATION_REQUIRED or clarification is None:
                raise RunStoreError(RunStoreCode.STATE_CONFLICT, "run is not awaiting an answer")
            if clarification.clarification_id != clarification_id:
                raise RunStoreError(RunStoreCode.STATE_CONFLICT, "clarification token is stale")
            clean_answer = self._validate_answer(clarification, answer)
            target = (
                RunStage.CANCELLED
                if clean_answer["kind"] in {"cancel", "eof"}
                else clarification.resume_stage
            )
            # The lock is already held, so append directly instead of recursively locking.
            self._validate_transition(current.stage, target, resume_stage=clarification.resume_stage)
            new_version = current.state_version + 1
            transition = self._build_transition(
                transition_id=new_version,
                from_stage=current.stage,
                to_stage=target,
                previous_hash=current.transitions[-1].record_hash,
                stage_payload={"clarification_id": clarification_id, **dict(stage_payload or {})},
                answer=clean_answer,
                reason_code=("USER_CANCELLED" if target is RunStage.CANCELLED else None),
                result_artifacts=result_artifacts,
            )
            state = replace(
                current,
                state_version=new_version,
                stage=target,
                transitions=(*current.transitions, transition),
                clarification=None,
                reason_code=transition.reason_code,
                result_artifacts=MappingProxyType(dict(result_artifacts or {})),
            )
            self._validate_state(state)
            self._write_transition(run_dir, transition)
            self._atomic_write_json(run_dir / "state.json", state.to_dict())
            return state

    def read_result(self, run_id: str) -> RunResult:
        state = self.load(run_id)
        if state.stage in TERMINAL_STAGES and state.result_artifacts:
            self._verify_terminal_artifacts(self.runs_root / run_id, state)
        success = state.stage is RunStage.SUCCEEDED
        result = RunResult(
            run_id=state.run_id,
            state_version=state.state_version,
            status=state.stage.value,
            reason_code=state.reason_code,
            complete_repair_success=success,
            successful_artifact_publishable=success,
            run_directory=f"runs/{state.run_id}",
            artifacts=state.result_artifacts,
            clarification=state.clarification,
        )
        payload = result.to_dict()
        try:
            self._result_validator().validate(payload)
        except ValidationError as error:
            raise RunStoreError(RunStoreCode.SCHEMA_INVALID, error.message) from error
        if len(canonical_json(payload).encode("utf-8")) > _PUBLIC_RECORD_LIMIT:
            raise RunStoreError(RunStoreCode.PUBLIC_RECORD_TOO_LARGE, "result exceeds limit")
        return result

    @staticmethod
    def _new_run_id() -> str:
        return f"repair-{uuid.uuid4().hex}"

    def _run_dir(self, run_id: str, *, require_exists: bool) -> Path:
        self._validate_run_id(run_id)
        candidate = self.runs_root / run_id
        if candidate.exists() and candidate.is_symlink():
            if require_exists:
                raise RunStoreError(RunStoreCode.PATH_ESCAPE, "run directory is a symlink")
            return candidate
        resolved = candidate.resolve(strict=require_exists)
        try:
            resolved.relative_to(self.runs_root.resolve())
        except ValueError as error:
            raise RunStoreError(RunStoreCode.PATH_ESCAPE, "run path escapes root") from error
        if require_exists and (not resolved.is_dir() or resolved.is_symlink()):
            raise RunStoreError(RunStoreCode.RUN_NOT_FOUND, f"unknown run: {run_id}")
        return resolved

    def _safe_run_child(
        self, run_dir: Path, relative: str, *, require_exists: bool,
        require_directory: bool = False,
    ) -> Path:
        normalized = relative.replace("\\", "/")
        parts = PurePosixPath(normalized).parts
        if not parts or PurePosixPath(normalized).is_absolute() or ".." in parts:
            raise RunStoreError(RunStoreCode.PATH_ESCAPE, "unsafe run child")
        current = run_dir
        for part in parts:
            current = current / part
            if current.exists() and _is_link_or_reparse(current):
                raise RunStoreError(RunStoreCode.PATH_ESCAPE, "run child follows link/reparse point")
        if require_exists and not current.exists():
            raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "bound artifact is missing")
        if require_directory and not current.is_dir():
            raise RunStoreError(RunStoreCode.PATH_ESCAPE, "stage path is not a directory")
        try:
            current.resolve(strict=require_exists).relative_to(run_dir.resolve())
        except ValueError as error:
            raise RunStoreError(RunStoreCode.PATH_ESCAPE, "run child escapes run") from error
        return current

    @staticmethod
    def _validate_run_id(run_id: str) -> None:
        if not _RUN_ID.fullmatch(run_id):
            raise RunStoreError(RunStoreCode.INVALID_RUN_ID, f"unsafe run ID: {run_id!r}")

    @staticmethod
    def _hash_bytes(value: bytes) -> str:
        return "sha256:" + hashlib.sha256(value).hexdigest()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="microseconds")

    def _build_transition(
        self,
        *,
        transition_id: int,
        from_stage: RunStage | None,
        to_stage: RunStage,
        previous_hash: str | None,
        stage_payload: Mapping[str, Any],
        clarification: Clarification | None = None,
        answer: Mapping[str, Any] | None = None,
        reason_code: str | None = None,
        result_artifacts: Mapping[str, str] | None = None,
    ) -> RunTransition:
        frozen_payload = freeze_json(stage_payload)
        stage_hash = hash_json({"stage": to_stage.value, "payload": stage_payload})
        base = RunTransition(
            transition_id=transition_id,
            state_version=transition_id,
            from_stage=from_stage,
            to_stage=to_stage,
            created_at=self._utc_now(),
            previous_hash=previous_hash,
            stage_hash=stage_hash,
            record_hash="sha256:" + "0" * 64,
            stage_payload=frozen_payload,
            clarification=clarification,
            answer=None if answer is None else freeze_json(answer),
            reason_code=reason_code,
            result_artifacts=MappingProxyType(dict(result_artifacts or {})),
        )
        return replace(base, record_hash=hash_json(base.hash_payload()))

    @staticmethod
    def _validate_transition(
        current: RunStage, target: RunStage, *, resume_stage: RunStage | None = None
    ) -> None:
        if current in TERMINAL_STAGES:
            raise RunStoreError(RunStoreCode.TERMINAL_IMMUTABLE, current.value)
        if current is RunStage.CLARIFICATION_REQUIRED:
            if target not in {resume_stage, RunStage.CANCELLED}:
                raise RunStoreError(RunStoreCode.INVALID_TRANSITION, f"{current.value}->{target.value}")
            return
        allowed: set[RunStage] = set(_FAILURES) | {RunStage.CLARIFICATION_REQUIRED}
        index = _PROGRESS.index(current)
        if index + 1 < len(_PROGRESS):
            allowed.add(_PROGRESS[index + 1])
        if current is RunStage.CHANGESET_READY:
            allowed.add(RunStage.SUCCEEDED)
        elif current is RunStage.EVALUATED:
            allowed.update({RunStage.SUCCEEDED, RunStage.NOT_PUBLISHABLE})
        if target not in allowed:
            raise RunStoreError(RunStoreCode.INVALID_TRANSITION, f"{current.value}->{target.value}")

    def _validate_clarification(
        self, clarification: Clarification, run_id: str, state_version: int
    ) -> None:
        payload = clarification.to_dict()
        if clarification.run_id != run_id or clarification.state_version != state_version:
            raise RunStoreError(
                RunStoreCode.PUBLIC_RECORD_INVALID, "clarification run/version binding mismatch"
            )
        if clarification.resume_stage in TERMINAL_STAGES or clarification.resume_stage is RunStage.CLARIFICATION_REQUIRED:
            raise RunStoreError(RunStoreCode.PUBLIC_RECORD_INVALID, "invalid resume stage")
        tokens = [candidate.token for candidate in clarification.candidates]
        if len(tokens) != len(set(tokens)):
            raise RunStoreError(RunStoreCode.PUBLIC_RECORD_INVALID, "candidate tokens must be unique")
        encoded = canonical_json(payload).encode("utf-8")
        if len(encoded) > _PUBLIC_RECORD_LIMIT:
            raise RunStoreError(RunStoreCode.PUBLIC_RECORD_TOO_LARGE, "clarification exceeds limit")
        lowered = encoded.decode("utf-8").casefold()
        if any(canary in lowered for canary in _PRIVATE_CANARIES):
            raise RunStoreError(RunStoreCode.PUBLIC_RECORD_INVALID, "private authority in public record")
        try:
            self._clarification_validator().validate(payload)
        except ValidationError as error:
            raise RunStoreError(RunStoreCode.PUBLIC_RECORD_INVALID, error.message) from error

    @staticmethod
    def _validate_answer(
        clarification: Clarification, answer: Mapping[str, Any]
    ) -> dict[str, Any]:
        try:
            clean = json.loads(canonical_json(answer))
        except (TypeError, ValueError) as error:
            raise RunStoreError(RunStoreCode.ANSWER_INVALID, "answer is not JSON") from error
        kind = clean.get("kind")
        if kind != "eof":
            try:
                Draft202012Validator(clarification.answer_schema).validate(clean)
            except ValidationError as error:
                raise RunStoreError(RunStoreCode.ANSWER_INVALID, error.message) from error
        allowed_keys = {
            "select_candidate": {"kind", "candidate_token"},
            "add_detail": {"kind", "detail"},
            "authorize_prototype": {"kind", "candidate_token", "authorized"},
            "confirm_property": {"kind", "preview_hash"},
            "reject_property": {"kind", "preview_hash"},
            "cancel": {"kind"},
            "eof": {"kind"},
        }
        if kind not in allowed_keys or set(clean) != allowed_keys[kind]:
            raise RunStoreError(RunStoreCode.ANSWER_INVALID, "answer shape is invalid")
        if kind not in clarification.answer_modes and kind != "eof":
            raise RunStoreError(RunStoreCode.ANSWER_INVALID, "answer mode is not allowed")
        if kind in {"select_candidate", "authorize_prototype"}:
            tokens = {candidate.token for candidate in clarification.candidates}
            if clean.get("candidate_token") not in tokens:
                raise RunStoreError(RunStoreCode.ANSWER_INVALID, "candidate is not in stored set")
        if kind == "authorize_prototype" and clean.get("authorized") is not True:
            raise RunStoreError(RunStoreCode.ANSWER_INVALID, "prototype needs explicit authorization")
        if kind in {"confirm_property", "reject_property"}:
            preview = clarification.property_preview
            expected = None if preview is None else preview.get("preview_hash")
            if clean.get("preview_hash") != expected:
                raise RunStoreError(
                    RunStoreCode.ANSWER_INVALID,
                    "property preview hash does not match stored question",
                )
        if kind == "add_detail":
            detail = clean.get("detail")
            if not isinstance(detail, str) or not detail.strip() or len(detail) > 4096:
                raise RunStoreError(RunStoreCode.ANSWER_INVALID, "detail is invalid")
        return clean

    @staticmethod
    def _validate_artifacts(
        run_dir: Path, value: Mapping[str, str]
    ) -> Mapping[str, str]:
        clean: dict[str, str] = {}
        for key, raw_path in value.items():
            if not key or len(key) > 128:
                raise RunStoreError(RunStoreCode.PUBLIC_RECORD_INVALID, "artifact key is invalid")
            normalized = str(raw_path).replace("\\", "/")
            path = PurePosixPath(normalized)
            if path.is_absolute() or ".." in path.parts or normalized in {"", "."}:
                raise RunStoreError(RunStoreCode.PATH_ESCAPE, "artifact path is unsafe")
            disk_path = run_dir.joinpath(*path.parts)
            current = run_dir
            for part in path.parts:
                current = current / part
                if current.exists() and current.is_symlink():
                    raise RunStoreError(
                        RunStoreCode.PATH_ESCAPE, "artifact path follows a symlink"
                    )
            if disk_path.exists():
                try:
                    disk_path.resolve().relative_to(run_dir.resolve())
                except ValueError as error:
                    raise RunStoreError(
                        RunStoreCode.PATH_ESCAPE, "artifact path escapes run directory"
                    ) from error
            clean[str(key)] = normalized
        return MappingProxyType(clean)

    def _validate_state(self, state: RunState) -> None:
        try:
            self._state_validator().validate(state.to_dict())
        except ValidationError as error:
            raise RunStoreError(RunStoreCode.SCHEMA_INVALID, error.message) from error

    def _validate_loaded_state(self, run_dir: Path, state: RunState) -> None:
        if state.run_id != run_dir.name or state.state_version != len(state.transitions) - 1:
            raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "state identity/version mismatch")
        if not state.transitions or state.stage is not state.transitions[-1].to_stage:
            raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "state head mismatch")
        head = state.transitions[-1]
        if state.clarification != head.clarification or state.reason_code != head.reason_code:
            raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "state metadata differs from head")
        if dict(state.result_artifacts) != dict(head.result_artifacts):
            raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "artifact state differs from head")
        previous: str | None = None
        for index, transition in enumerate(state.transitions):
            if transition.transition_id != index or transition.state_version != index:
                raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "transition sequence is invalid")
            expected_from = None if index == 0 else state.transitions[index - 1].to_stage
            if transition.from_stage is not expected_from or transition.previous_hash != previous:
                raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "transition chain is invalid")
            if hash_json(transition.hash_payload()) != transition.record_hash:
                raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "transition hash is invalid")
            if hash_json(
                {"stage": transition.to_stage.value, "payload": thaw_json(transition.stage_payload)}
            ) != transition.stage_hash:
                raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "stage hash is invalid")
            transition_path = run_dir / "transitions" / f"{index:06d}.json"
            try:
                stored = json.loads(transition_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "transition is unreadable") from error
            if stored != transition.to_dict():
                raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "transition copy differs")
            self._verify_stage_bindings(run_dir, thaw_json(transition.stage_payload))
            previous = transition.record_hash

    def _verify_stage_bindings(self, run_dir: Path, value: Any) -> None:
        if isinstance(value, Mapping):
            if set(value) == {"path", "sha256", "schema_version"}:
                path = self._safe_run_child(run_dir, str(value["path"]), require_exists=True)
                if not path.is_file() or self._hash_bytes(path.read_bytes()) != str(value["sha256"]):
                    raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "stage artifact hash mismatch")
                if not str(value["schema_version"]):
                    raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "stage artifact schema missing")
                return
            for item in value.values():
                self._verify_stage_bindings(run_dir, item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                self._verify_stage_bindings(run_dir, item)

    def _verify_terminal_artifacts(self, run_dir: Path, state: RunState) -> None:
        manifest_ref = state.result_artifacts.get("manifest")
        if not manifest_ref:
            raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "terminal manifest missing")
        manifest_path = self._safe_run_child(run_dir, manifest_ref, require_exists=True)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "terminal manifest unreadable") from error
        if manifest.get("schema_version") != "text2ifc/ifc-repair-artifact-manifest/0.1":
            raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "terminal manifest schema mismatch")
        declared: dict[str, str] = {}
        for item in manifest.get("artifacts", ()):
            relative = str(item.get("path", ""))
            path = self._safe_run_child(run_dir, relative, require_exists=True)
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != str(item.get("sha256", "")):
                raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "terminal artifact hash mismatch")
            declared[relative] = actual
        for name, relative in state.result_artifacts.items():
            if name != "manifest" and relative not in declared:
                raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "terminal artifact is not manifest-bound")

    def _recover_terminal_publication(self, run_dir: Path) -> None:
        journal_path = run_dir / _PUBLICATION_JOURNAL
        if not journal_path.exists():
            return
        with self._exclusive_lock(run_dir):
            if not journal_path.exists():
                return
            try:
                journal = json.loads(journal_path.read_text(encoding="utf-8"))
                if journal.get("schema_version") != "text2ifc/ifc-repair-terminal-publication/0.1":
                    raise ValueError("journal schema")
                expected = int(journal["expected_state_version"])
                prepared_name = str(journal["prepared_root"])
                destination_rel = str(journal["destination_root"])
                transition = RunTransition.from_dict(journal["transition"])
                recovered = RunState.from_dict(journal["state"])
            except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                raise RunStoreError(
                    RunStoreCode.TAMPER_DETECTED, "publication journal is invalid"
                ) from error
            current = self._read_state(run_dir)
            if recovered.state_version != expected + 1 or transition != recovered.transitions[-1]:
                raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "publication journal chain mismatch")
            if current.state_version == expected:
                if current.transitions != recovered.transitions[:-1]:
                    raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "publication base state changed")
                prepared = self._safe_run_child(
                    run_dir, prepared_name, require_exists=False
                )
                destination = self._safe_run_child(
                    run_dir, destination_rel, require_exists=False
                )
                if destination.exists():
                    if prepared.exists():
                        raise RunStoreError(
                            RunStoreCode.TAMPER_DETECTED, "both prepared and promoted bundles exist"
                        )
                elif prepared.exists():
                    destination.parent.mkdir(exist_ok=True)
                    os.replace(prepared, destination)
                    self._fsync_directory(destination.parent)
                else:
                    raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "publication bundle is missing")
                transition_path = run_dir / "transitions" / f"{transition.transition_id:06d}.json"
                if transition_path.exists():
                    try:
                        stored = json.loads(transition_path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError) as error:
                        raise RunStoreError(
                            RunStoreCode.TAMPER_DETECTED, "publication transition is unreadable"
                        ) from error
                    if stored != transition.to_dict():
                        raise RunStoreError(
                            RunStoreCode.TAMPER_DETECTED, "publication transition differs"
                        )
                else:
                    self._write_transition(run_dir, transition)
                self._atomic_write_json(run_dir / "state.json", recovered.to_dict())
            elif current.state_version == recovered.state_version:
                if current != recovered:
                    raise RunStoreError(
                        RunStoreCode.TAMPER_DETECTED, "committed publication differs from journal"
                    )
            else:
                raise RunStoreError(
                    RunStoreCode.STATE_CONFLICT, "publication recovery version conflict"
                )
            self._verify_terminal_artifacts(run_dir, recovered)
            journal_path.unlink()
            self._fsync_directory(run_dir)

    def _map_prepared_artifacts(
        self,
        run_dir: Path,
        prepared: Path,
        bundle_rel: str,
        artifacts: Mapping[str, str],
    ) -> Mapping[str, str]:
        mapped: dict[str, str] = {}
        for name, raw in artifacts.items():
            stage_path = self._safe_run_child(run_dir, str(raw), require_exists=True)
            try:
                within = stage_path.relative_to(prepared)
            except ValueError as error:
                raise RunStoreError(
                    RunStoreCode.PATH_ESCAPE, "terminal artifact is outside prepared bundle"
                ) from error
            if not stage_path.is_file():
                raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "prepared artifact is not a file")
            mapped[str(name)] = (PurePosixPath(bundle_rel) / PurePosixPath(within.as_posix())).as_posix()
        if "manifest" not in mapped:
            raise RunStoreError(RunStoreCode.PUBLIC_RECORD_INVALID, "terminal manifest missing")
        return self._validate_artifacts(run_dir, mapped)

    def _verify_prepared_manifest(
        self,
        prepared: Path,
        bundle_rel: str,
        artifacts: Mapping[str, str],
    ) -> None:
        manifest_relative = Path(artifacts["manifest"]).relative_to(bundle_rel)
        manifest_path = prepared / manifest_relative
        try:
            document = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "prepared manifest unreadable") from error
        if document.get("schema_version") != "text2ifc/ifc-repair-artifact-manifest/0.1":
            raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "prepared manifest schema mismatch")
        declared: set[str] = set()
        prefix = PurePosixPath(bundle_rel)
        for item in document.get("artifacts", ()):
            relative = PurePosixPath(str(item.get("path", "")))
            try:
                within = relative.relative_to(prefix)
            except ValueError as error:
                raise RunStoreError(
                    RunStoreCode.TAMPER_DETECTED, "prepared manifest path is outside bundle"
                ) from error
            disk_path = prepared.joinpath(*within.parts)
            if not disk_path.is_file():
                raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "prepared artifact missing")
            if hashlib.sha256(disk_path.read_bytes()).hexdigest() != str(item.get("sha256", "")):
                raise RunStoreError(RunStoreCode.TAMPER_DETECTED, "prepared artifact hash mismatch")
            declared.add(relative.as_posix())
        for name, relative in artifacts.items():
            if name != "manifest" and relative not in declared:
                raise RunStoreError(
                    RunStoreCode.TAMPER_DETECTED, "prepared terminal artifact is not manifest-bound"
                )

    def _validate_source(self, binding: SourceBinding) -> None:
        path = Path(binding.reference)
        if path.is_symlink() or not path.is_file():
            raise RunStoreError(RunStoreCode.SOURCE_CHANGED, "bound source is unavailable")
        data = path.read_bytes()
        if len(data) != binding.size_bytes or self._hash_bytes(data) != binding.sha256:
            raise RunStoreError(RunStoreCode.SOURCE_CHANGED, "bound source changed")

    @contextmanager
    def _exclusive_lock(self, run_dir: Path) -> Iterator[None]:
        lock_path = run_dir / ".transition.lock"
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR)
        except OSError as error:
            raise RunStoreError(
                RunStoreCode.LOCKED, "run mutation lock cannot be opened"
            ) from error
        try:
            if os.name == "nt":
                import msvcrt
                os.lseek(descriptor, 0, os.SEEK_SET)
                if os.fstat(descriptor).st_size == 0:
                    try:
                        os.write(descriptor, b"0")
                    except OSError as error:
                        raise RunStoreError(
                            RunStoreCode.LOCKED, "run mutation lock is being initialized"
                        ) from error
                os.lseek(descriptor, 0, os.SEEK_SET)
                try:
                    msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
                except OSError as error:
                    raise RunStoreError(RunStoreCode.LOCKED, "run mutation lock is held") from error
            else:
                import fcntl
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as error:
                    raise RunStoreError(RunStoreCode.LOCKED, "run mutation lock is held") from error
            # Keep the byte used by Windows locking present while metadata is
            # refreshed.  A transient zero-length file lets a racing opener
            # attempt an unauthorized pre-lock write.
            os.ftruncate(descriptor, 1)
            os.lseek(descriptor, 1, os.SEEK_SET)
            os.write(descriptor, f"pid={os.getpid()} nonce={uuid.uuid4().hex}\n".encode("ascii"))
            os.fsync(descriptor)
            yield
        finally:
            os.close(descriptor)

    def _write_transition(self, run_dir: Path, transition: RunTransition) -> None:
        target = run_dir / "transitions" / f"{transition.transition_id:06d}.json"
        if target.exists():
            self._discard_uncommitted_tail(target, transition)
        self._atomic_write_json(target, transition.to_dict(), replace_existing=False)

    @staticmethod
    def _discard_uncommitted_tail(target: Path, replacement: RunTransition) -> None:
        """Remove only a validated tail not referenced by the committed state head."""

        try:
            document = json.loads(target.read_text(encoding="utf-8"))
            orphan = RunTransition.from_dict(document)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise RunStoreError(
                RunStoreCode.TAMPER_DETECTED, "uncommitted transition tail is invalid"
            ) from error
        same_chain_position = (
            orphan.transition_id == replacement.transition_id
            and orphan.state_version == replacement.state_version
            and orphan.from_stage is replacement.from_stage
            and orphan.previous_hash == replacement.previous_hash
        )
        if not same_chain_position or hash_json(orphan.hash_payload()) != orphan.record_hash:
            raise RunStoreError(
                RunStoreCode.TAMPER_DETECTED, "unexpected transition already occupies next version"
            )
        target.unlink()
        RunStore._fsync_directory(target.parent)

    @staticmethod
    def _atomic_write_json(
        target: Path, payload: Mapping[str, Any], *, replace_existing: bool = True
    ) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.parent / f".{target.name}.{uuid.uuid4().hex}.tmp"
        data = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        try:
            with temporary.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            if not replace_existing and target.exists():
                raise RunStoreError(RunStoreCode.STATE_CONFLICT, "target already exists")
            os.replace(temporary, target)
            RunStore._fsync_directory(target.parent)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        if os.name == "nt":
            return
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    @staticmethod
    def _remove_empty_start(run_dir: Path) -> None:
        # Cleanup is tightly bounded to the just-created run and known filenames.
        transitions = run_dir / "transitions"
        if transitions.exists():
            for path in transitions.iterdir():
                if path.name.startswith(".") and path.suffix == ".tmp":
                    path.unlink(missing_ok=True)
            try:
                transitions.rmdir()
            except OSError:
                return
        for name in ("state.json", ".transition.lock"):
            (run_dir / name).unlink(missing_ok=True)
        try:
            run_dir.rmdir()
        except OSError:
            pass

    @classmethod
    def _state_validator(cls) -> Draft202012Validator:
        return Draft202012Validator(load_run_schema(RUN_STATE_SCHEMA_PATH))

    @classmethod
    def _clarification_validator(cls) -> Draft202012Validator:
        return Draft202012Validator(load_run_schema(CLARIFICATION_SCHEMA_PATH))

    @classmethod
    def _result_validator(cls) -> Draft202012Validator:
        return Draft202012Validator(load_run_schema(RESULT_SCHEMA_PATH))


__all__ = ["RunStore"]
