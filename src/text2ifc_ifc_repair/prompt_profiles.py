"""Immutable, bounded Prompt Profile registry for IFC repair operations."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator
from text2ifc_agent.prompt_registry import (
    PromptRegistryError,
    load_prompt_registry,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-prompt-profile-0.1.schema.json"
)
DEFAULT_PROFILE_DIR = PROJECT_ROOT / "prompts" / "agent" / "ifc-repair-profiles"
PROFILE_SCHEMA_VERSION = "text2ifc/ifc-repair-prompt-profile/0.1"
MAX_PROFILE_COUNT = 32
MAX_PROFILE_BYTES = 64 * 1024
MAX_FEW_SHOT_BYTES = 32 * 1024
MAX_SELECTED_BYTES = 256 * 1024
MAX_SELECTED_FEW_SHOTS = 16


class PromptProfileError(ValueError):
    """Stable fail-closed profile loading or selection error."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class PromptProfile:
    profile_id: str
    profile_version: str
    component_family: str
    action: str
    operation_type: str
    target_ifc_classes: tuple[str, ...]
    document: Mapping[str, Any]
    profile_hash: str
    profile_bytes: int

    def compact_projection(self) -> dict[str, Any]:
        """Return only Stage 1 classification and slot information."""

        return {
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "profile_hash": self.profile_hash,
            "component_family": self.component_family,
            "action": self.action,
            "operation_type": self.operation_type,
            "target_ifc_classes": list(self.target_ifc_classes),
            "classification_terms": list(self.document["classification_terms"]),
            "slot_summary": self.document["slot_summary"],
            "required_slots": list(self.document["required_slots"]),
            "conditional_slots": list(self.document["conditional_slots"]),
            "program_derived_slots": list(
                self.document["program_derived_slots"]
            ),
            "supported_capabilities": list(
                self.document["supported_capabilities"]
            ),
            "unsupported_capabilities": list(
                self.document["unsupported_capabilities"]
            ),
        }

    def full_projection(self) -> dict[str, Any]:
        value = _plain(self.document)
        value["profile_hash"] = self.profile_hash
        return value


@dataclass(frozen=True)
class SelectedPromptProfiles:
    profiles: tuple[Mapping[str, Any], ...]
    few_shots: tuple[Mapping[str, Any], ...]
    profile_ids: tuple[str, ...]
    profile_hashes: tuple[str, ...]
    few_shot_ids: tuple[str, ...]
    few_shot_hashes: tuple[str, ...]
    input_bytes: int

    @property
    def estimated_tokens(self) -> int:
        return (self.input_bytes + 3) // 4

    def to_dict(self) -> dict[str, Any]:
        return {
            "profiles": [_plain(item) for item in self.profiles],
            "few_shots": [_plain(item) for item in self.few_shots],
            "profile_ids": list(self.profile_ids),
            "profile_hashes": list(self.profile_hashes),
            "few_shot_ids": list(self.few_shot_ids),
            "few_shot_hashes": list(self.few_shot_hashes),
            "input_bytes": self.input_bytes,
            "estimated_tokens": self.estimated_tokens,
        }


@lru_cache(maxsize=1)
def _profile_schema() -> dict[str, Any]:
    schema = json.loads(PROFILE_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def load_prompt_profiles(
    profile_dir: Path | str = DEFAULT_PROFILE_DIR,
) -> Mapping[str, PromptProfile]:
    """Load all checked-in profiles, verifying schema, identity and hashes."""

    directory = Path(profile_dir).resolve()
    if not directory.is_dir():
        raise PromptProfileError("PROFILE_DIRECTORY_MISSING", str(directory))
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise PromptProfileError("PROFILE_SET_EMPTY", str(directory))
    if len(paths) > MAX_PROFILE_COUNT:
        raise PromptProfileError("PROFILE_COUNT_LIMIT_EXCEEDED", str(len(paths)))

    validator = Draft202012Validator(_profile_schema())
    loaded: dict[str, PromptProfile] = {}
    for path in paths:
        raw = path.read_bytes()
        if len(raw) > MAX_PROFILE_BYTES:
            raise PromptProfileError("PROFILE_BYTE_LIMIT_EXCEEDED", path.name)
        try:
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise PromptProfileError("PROFILE_JSON_INVALID", path.name) from error
        errors = sorted(
            validator.iter_errors(document),
            key=lambda error: tuple(str(item) for item in error.absolute_path),
        )
        if errors:
            error = errors[0]
            pointer = "/" + "/".join(str(item) for item in error.absolute_path)
            raise PromptProfileError(
                "PROFILE_SCHEMA_INVALID", f"{path.name}:{pointer}:{error.message}"
            )
        profile_id = str(document["profile_id"])
        if profile_id in loaded:
            raise PromptProfileError("DUPLICATE_PROFILE_ID", profile_id)
        operation_type = str(document["operation_type"])
        _validate_few_shots(document)
        loaded[profile_id] = PromptProfile(
            profile_id=profile_id,
            profile_version=str(document["profile_version"]),
            component_family=str(document["component_family"]),
            action=str(document["action"]),
            operation_type=operation_type,
            target_ifc_classes=tuple(
                str(item) for item in document["target_ifc_classes"]
            ),
            document=_freeze(document),
            profile_hash=_sha256(raw),
            profile_bytes=len(raw),
        )
    return MappingProxyType(loaded)


def compact_profile_catalog(
    profiles: Mapping[str, PromptProfile] | None = None,
    *,
    include_profile_ids: Iterable[str] | None = None,
) -> tuple[dict[str, Any], ...]:
    registry = profiles or load_prompt_profiles()
    selected = (
        set(registry)
        if include_profile_ids is None
        else {str(item) for item in include_profile_ids}
    )
    unknown = selected - set(registry)
    if unknown:
        raise PromptProfileError("UNKNOWN_PROFILE_ID", sorted(unknown)[0])
    return tuple(
        registry[profile_id].compact_projection()
        for profile_id in sorted(selected)
    )


def select_prompt_profiles(
    profile_ids: Iterable[str],
    profiles: Mapping[str, PromptProfile] | None = None,
) -> SelectedPromptProfiles:
    registry = profiles or load_prompt_profiles()
    selected_ids = tuple(sorted(set(str(item) for item in profile_ids)))
    if not selected_ids:
        raise PromptProfileError("PROFILE_SELECTION_EMPTY", "no profiles")
    unknown = set(selected_ids) - set(registry)
    if unknown:
        raise PromptProfileError("UNKNOWN_PROFILE_ID", sorted(unknown)[0])

    full_profiles: list[Mapping[str, Any]] = []
    few_shots: dict[str, tuple[str, Mapping[str, Any]]] = {}
    profile_hashes: list[str] = []
    total_bytes = 0
    for profile_id in selected_ids:
        profile = registry[profile_id]
        _validate_profile_registry_binding(profile)
        full_profiles.append(profile.full_projection())
        profile_hashes.append(profile.profile_hash)
        total_bytes += profile.profile_bytes
        for reference in profile.document["few_shots"]:
            example_id = str(reference["example_id"])
            path = _project_file(str(reference["path"]))
            raw = path.read_bytes()
            document = json.loads(raw.decode("utf-8"))
            previous = few_shots.get(example_id)
            candidate = (str(reference["sha256"]), _freeze(document))
            if previous is not None and previous != candidate:
                raise PromptProfileError("FEW_SHOT_ID_CONFLICT", example_id)
            few_shots[example_id] = candidate
            total_bytes += len(raw)
    if len(few_shots) > MAX_SELECTED_FEW_SHOTS:
        raise PromptProfileError(
            "SELECTED_FEW_SHOT_LIMIT_EXCEEDED", str(len(few_shots))
        )
    if total_bytes > MAX_SELECTED_BYTES:
        raise PromptProfileError(
            "SELECTED_PROFILE_BYTES_EXCEEDED", str(total_bytes)
        )
    ordered_examples = tuple(sorted(few_shots))
    return SelectedPromptProfiles(
        profiles=tuple(_freeze(item) for item in full_profiles),
        few_shots=tuple(few_shots[item][1] for item in ordered_examples),
        profile_ids=selected_ids,
        profile_hashes=tuple(profile_hashes),
        few_shot_ids=ordered_examples,
        few_shot_hashes=tuple(few_shots[item][0] for item in ordered_examples),
        input_bytes=total_bytes,
    )


def validate_profile_operation_binding(
    profile: PromptProfile,
    *,
    operation_type: str,
    target_ifc_classes: Iterable[str],
) -> None:
    if profile.operation_type != operation_type:
        raise PromptProfileError(
            "PROFILE_OPERATION_MISMATCH",
            f"{profile.profile_id}:{operation_type}",
        )
    if frozenset(profile.target_ifc_classes) != frozenset(target_ifc_classes):
        raise PromptProfileError(
            "PROFILE_TARGET_CLASS_MISMATCH",
            f"{profile.profile_id}:{sorted(target_ifc_classes)}",
        )


def _validate_profile_registry_binding(profile: PromptProfile) -> None:
    """Require selected full profiles to match their external hash record."""

    try:
        prompt_registry = load_prompt_registry()
    except PromptRegistryError as error:
        raise PromptProfileError("PROFILE_REGISTRY_INVALID", str(error)) from error
    record = prompt_registry.get(profile.profile_id)
    if record is None:
        raise PromptProfileError(
            "PROFILE_REGISTRY_ENTRY_MISSING", profile.profile_id
        )
    expected_path = (
        f"prompts/agent/ifc-repair-profiles/{profile.profile_id}.json"
    )
    if str(record.get("path")) != expected_path:
        raise PromptProfileError(
            "PROFILE_REGISTRY_PATH_MISMATCH", profile.profile_id
        )
    if str(record.get("sha256")) != profile.profile_hash:
        raise PromptProfileError("PROFILE_HASH_MISMATCH", profile.profile_id)


def _validate_few_shots(document: Mapping[str, Any]) -> None:
    seen: set[str] = set()
    for reference in document["few_shots"]:
        example_id = str(reference["example_id"])
        if example_id in seen:
            raise PromptProfileError("DUPLICATE_FEW_SHOT_ID", example_id)
        seen.add(example_id)
        path = _project_file(str(reference["path"]))
        raw = path.read_bytes()
        if len(raw) > MAX_FEW_SHOT_BYTES:
            raise PromptProfileError("FEW_SHOT_BYTE_LIMIT_EXCEEDED", path.name)
        if str(reference["sha256"]) != _sha256(raw):
            raise PromptProfileError("FEW_SHOT_HASH_MISMATCH", example_id)
        try:
            example = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise PromptProfileError("FEW_SHOT_JSON_INVALID", example_id) from error
        if (
            example.get("example_id") != example_id
            or example.get("profile_id") != document["profile_id"]
        ):
            raise PromptProfileError("FEW_SHOT_BINDING_MISMATCH", example_id)
        if "EXAMPLE_ONLY" not in str(example):
            raise PromptProfileError("FEW_SHOT_SENTINEL_MISSING", example_id)


def _project_file(relative_path: str) -> Path:
    path = (PROJECT_ROOT / relative_path).resolve()
    try:
        path.relative_to(PROJECT_ROOT)
    except ValueError as error:
        raise PromptProfileError("PROFILE_PATH_ESCAPE", relative_path) from error
    if not path.is_file():
        raise PromptProfileError("PROFILE_FILE_MISSING", relative_path)
    return path


def _sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return copy.deepcopy(value)


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return copy.deepcopy(value)


__all__ = [
    "PROFILE_SCHEMA_VERSION",
    "PromptProfile",
    "PromptProfileError",
    "SelectedPromptProfiles",
    "compact_profile_catalog",
    "load_prompt_profiles",
    "select_prompt_profiles",
    "validate_profile_operation_binding",
]
