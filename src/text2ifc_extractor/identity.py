"""Stable source identity without STEP-line dependence."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _scalar_signature(entity) -> dict[str, Any]:
    values: dict[str, Any] = {"ifc_class": entity.is_a()}
    for name in ("Name", "Description", "ObjectType", "Tag"):
        value = getattr(entity, name, None)
        if isinstance(value, (str, int, float, bool)):
            values[name] = value
    placement = getattr(entity, "ObjectPlacement", None)
    if placement is not None:
        relative = getattr(placement, "RelativePlacement", None)
        location = getattr(relative, "Location", None)
        coordinates = getattr(location, "Coordinates", None)
        if coordinates is not None:
            values["local_origin"] = list(coordinates)
    return values


def semantic_id(entity, source_sha256: str) -> str:
    global_id = getattr(entity, "GlobalId", None)
    if global_id:
        token = global_id
    else:
        payload = json.dumps(
            _scalar_signature(entity),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        token = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:22]
    return f"ifc2x3:{source_sha256[:12]}:{entity.is_a()}:{token}"
