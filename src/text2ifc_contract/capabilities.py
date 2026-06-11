"""Project-authored IFC2X3 generation capability overlay."""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType

from text2ifc_knowledge.registry import load_ifc2x3_registry


ALLOWED_STATES = {"generate", "extract-only", "compiler-only", "unsupported"}


def load_capabilities(project_root=None):
    root = (
        Path(project_root).resolve()
        if project_root is not None
        else Path(__file__).resolve().parents[2]
    )
    payload = json.loads(
        (
            root / "schemas" / "ifc" / "capabilities" / "IFC2X3.json"
        ).read_text(encoding="utf-8")
    )
    states = payload["entities"]
    registry = load_ifc2x3_registry(root)
    entity_names = {
        name
        for name, record in registry.declarations.items()
        if record["kind"] == "entity"
    }
    if set(states) != entity_names:
        raise ValueError("capability overlay does not cover the IFC2X3 entity universe")
    if set(states.values()) - ALLOWED_STATES:
        raise ValueError("capability overlay contains an unknown state")
    return MappingProxyType(dict(states))
