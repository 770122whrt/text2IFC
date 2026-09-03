"""Immutable public terminal artifacts and Evaluation-authoritative IFC promotion."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import ifcopenshell

from .evaluation_projection import PrivateCanaryLeakError, assert_public_bundle_has_no_canaries


ARTIFACT_MANIFEST_SCHEMA_VERSION = "text2ifc/ifc-repair-artifact-manifest/0.1"
MAX_MANIFEST_ARTIFACTS = 64


class RunArtifactError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(code if not detail else f"{code}: {detail}")


@dataclass(frozen=True)
class TerminalArtifacts:
    evaluation_path: str
    evidence_path: str
    manifest_path: str
    successful_ifc: str | None
    diagnostic_candidate: str | None
    prepared_root: str | None = None


def publish_terminal_artifacts(
    *,
    run_directory: Path | str,
    terminal_status: str,
    evaluation: Mapping[str, Any],
    candidate_ifc_path: Path | str | None,
    evidence: Mapping[str, Any],
    expected_candidate_sha256: str | None = None,
    private_canaries: tuple[str, ...] = (),
    promote: bool = True,
) -> TerminalArtifacts:
    """Build a verified terminal bundle and optionally promote it immediately.

    ``promote=False`` is the durable-run path.  It leaves the complete bundle
    under a hidden prepared name so :class:`RunStore` can bind promotion and
    the terminal state transition through its recovery journal.
    """

    root = Path(run_directory).resolve()
    root.mkdir(parents=True, exist_ok=True)
    public_evaluation = _json_copy(evaluation)
    public_evidence = _json_copy(evidence)
    if public_evaluation.get("schema_version") != "text2ifc/ifc-repair-evaluation-public/0.2":
        raise RunArtifactError("INVALID_PUBLIC_EVALUATION_VERSION")
    publishable = public_evaluation.get("successful_artifact_publishable") is True
    if publishable != (public_evaluation.get("complete_repair_success") is True):
        raise RunArtifactError("INVALID_PUBLICATION_FLAGS")
    candidate = None
    if candidate_ifc_path is not None:
        candidate = _contained_candidate(root, Path(candidate_ifc_path))
        _verify_candidate(candidate, expected_candidate_sha256)
    if publishable and candidate is None:
        raise RunArtifactError("PUBLISHABLE_CANDIDATE_MISSING")
    if private_canaries:
        _scan_canaries(
            {"status": terminal_status, "evaluation": public_evaluation, "evidence": public_evidence, "candidate": candidate},
            private_canaries,
        )

    publication_id = uuid.uuid4().hex
    destination_root = root / "published"
    if promote and destination_root.exists():
        raise RunArtifactError("ARTIFACT_ALREADY_EXISTS", "published")
    stage_root = root / (
        f".terminal-stage-{publication_id}"
        if promote
        else f".terminal-prepared-{publication_id}"
    )
    stage_root.mkdir(exist_ok=False)
    evaluation_path = stage_root / "evaluation" / "public-evaluation.json"
    evidence_path = stage_root / "terminal" / "evidence.json"
    manifest_path = stage_root / "manifest.json"
    _write_json(evaluation_path, public_evaluation)
    _write_json(evidence_path, {"terminal_status": terminal_status, "evidence": public_evidence})

    successful: Path | None = None
    diagnostic: Path | None = None
    if candidate is not None:
        destination = stage_root / ("successful/repaired.ifc" if publishable else "diagnostic/repaired-candidate.ifc")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(candidate, destination)
        successful, diagnostic = (destination, None) if publishable else (None, destination)

    manifest_prefix = (
        "published" if promote else f".terminal-bundles/{publication_id}"
    )
    _write_json(manifest_path, _manifest(stage_root, prefix=manifest_prefix))
    if private_canaries:
        _scan_canaries(tuple(path for path in stage_root.rglob("*") if path.is_file()), private_canaries)
    _fsync_tree(stage_root)
    if not promote:
        return TerminalArtifacts(
            evaluation_path=str(evaluation_path),
            evidence_path=str(evidence_path),
            manifest_path=str(manifest_path),
            successful_ifc=None if successful is None else str(successful),
            diagnostic_candidate=None if diagnostic is None else str(diagnostic),
            prepared_root=str(stage_root),
        )
    os.replace(stage_root, destination_root)
    evaluation_path = destination_root / "evaluation" / "public-evaluation.json"
    evidence_path = destination_root / "terminal" / "evidence.json"
    manifest_path = destination_root / "manifest.json"
    successful = None if successful is None else destination_root / successful.relative_to(stage_root)
    diagnostic = None if diagnostic is None else destination_root / diagnostic.relative_to(stage_root)
    return TerminalArtifacts(
        evaluation_path=str(evaluation_path),
        evidence_path=str(evidence_path),
        manifest_path=str(manifest_path),
        successful_ifc=None if successful is None else str(successful),
        diagnostic_candidate=None if diagnostic is None else str(diagnostic),
        prepared_root=None,
    )


def _contained_candidate(root: Path, candidate: Path) -> Path:
    if candidate.is_symlink():
        raise RunArtifactError("CANDIDATE_SYMLINK_FORBIDDEN")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise RunArtifactError("CANDIDATE_OUTSIDE_RUN") from error
    if not resolved.is_file():
        raise RunArtifactError("CANDIDATE_MISSING")
    return resolved


def _verify_candidate(candidate: Path, expected_sha256: str | None) -> None:
    actual = "sha256:" + hashlib.sha256(candidate.read_bytes()).hexdigest()
    if expected_sha256 is not None and actual != _normalize_sha256(expected_sha256):
        raise RunArtifactError("CANDIDATE_HASH_MISMATCH")
    try:
        reopened = ifcopenshell.open(str(candidate))
    except Exception as error:
        raise RunArtifactError("CANDIDATE_REOPEN_FAILED", type(error).__name__) from error
    if reopened.schema != "IFC2X3":
        raise RunArtifactError("CANDIDATE_SCHEMA_MISMATCH", reopened.schema)


def _manifest(root: Path, *, prefix: str = "") -> dict[str, Any]:
    files = sorted(path for path in root.rglob("*") if path.is_file() and path.name != "manifest.json")
    if len(files) > MAX_MANIFEST_ARTIFACTS:
        raise RunArtifactError("ARTIFACT_LIMIT_EXCEEDED", str(len(files)))
    artifacts = []
    for path in files:
        relative = path.relative_to(root)
        if relative.is_absolute() or ".." in relative.parts:
            raise RunArtifactError("INVALID_MANIFEST_PATH")
        payload = path.read_bytes()
        role = "public_evidence"
        if relative.parts[0] == "successful":
            role = "successful_ifc"
        elif relative.parts[0] == "diagnostic":
            role = "diagnostic_candidate"
        elif relative.parts[0] == "evaluation":
            role = "public_evaluation"
        public_path = (Path(prefix) / relative).as_posix() if prefix else relative.as_posix()
        artifacts.append({"path": public_path, "sha256": hashlib.sha256(payload).hexdigest(), "size_bytes": len(payload), "role": role})
    return {"schema_version": ARTIFACT_MANIFEST_SCHEMA_VERSION, "artifacts": artifacts}


def _scan_canaries(bundle: Any, canaries: tuple[str, ...]) -> None:
    try:
        assert_public_bundle_has_no_canaries(bundle, canaries)
    except PrivateCanaryLeakError as error:
        raise RunArtifactError("PRIVATE_CANARY_DETECTED") from error


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists():
        raise RunArtifactError("ARTIFACT_TEMP_ALREADY_EXISTS", temporary.name)
    temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _fsync_tree(root: Path) -> None:
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        with path.open("r+b") as stream:
            os.fsync(stream.fileno())


def _json_copy(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))


def _normalize_sha256(value: str) -> str:
    return value if value.startswith("sha256:") else f"sha256:{value}"


__all__ = ["RunArtifactError", "TerminalArtifacts", "publish_terminal_artifacts"]
