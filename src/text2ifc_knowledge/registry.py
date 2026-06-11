"""Offline, read-only access to generated IFC2X3 knowledge."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


class RegistryDriftError(ValueError):
    pass


def _project_root(project_root: str | Path | None) -> Path:
    if project_root is not None:
        return Path(project_root).resolve()
    return Path(__file__).resolve().parents[2]


def _generated_root(project_root: str | Path | None) -> Path:
    return (
        _project_root(project_root)
        / "schemas"
        / "ifc"
        / "generated"
        / "IFC2X3"
    )


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        payload = json.load(stream)
    if not isinstance(payload, dict):
        raise ValueError(f"registry file must contain an object: {path}")
    return payload


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


class IfcKnowledgeRegistry:
    def __init__(
        self,
        declarations: Mapping[str, Any],
        property_sets: Mapping[str, Any],
    ) -> None:
        self._declarations = declarations
        self._property_sets = property_sets

    @property
    def declarations(self):
        return self._declarations

    def declaration(self, name: str):
        return self._declarations.get(name)

    def entity(self, name: str):
        declaration = self.declaration(name)
        if declaration is None or declaration["kind"] != "entity":
            return None
        return declaration

    def property_set(self, name: str):
        return self._property_sets.get(name)


def load_ifc2x3_registry(
    project_root: str | Path | None = None,
) -> IfcKnowledgeRegistry:
    root = _generated_root(project_root)
    declarations = _load_json(root / "declarations.json")["declarations"]
    property_sets = _load_json(root / "property_sets.json")["property_sets"]
    return IfcKnowledgeRegistry(_freeze(declarations), _freeze(property_sets))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_registry_files(project_root: str | Path | None = None) -> dict[str, str]:
    root = _generated_root(project_root)
    try:
        manifest = _load_json(root / "registry-manifest.json")
        outputs = manifest["outputs"]
    except (OSError, KeyError, json.JSONDecodeError, ValueError) as exc:
        raise RegistryDriftError(f"cannot read registry manifest: {exc}") from exc

    checked: dict[str, str] = {}
    for name, record in outputs.items():
        expected = record.get("sha256") if isinstance(record, dict) else None
        if not isinstance(expected, str):
            raise RegistryDriftError(f"manifest has no hash for {name}")
        path = root / name
        try:
            actual = _sha256_file(path)
        except OSError as exc:
            raise RegistryDriftError(f"cannot read generated registry {name}: {exc}") from exc
        if actual != expected:
            raise RegistryDriftError(
                f"generated registry drift for {name}: expected {expected}, got {actual}"
            )
        checked[name] = actual
    return checked
