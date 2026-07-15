"""Stable-ID index and semantic hashes for BIM JSON candidates."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from text2ifc_agent.revisions import hash_bim_json_candidate, hash_json_value


class CandidateIndexError(ValueError):
    """Raised when a candidate cannot be indexed without ambiguity."""


def build_candidate_index(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Index one candidate without relying on collection order."""

    entities = _index_collection(candidate.get("entities"), "entity")
    relationships = _index_collection(candidate.get("relationships"), "relationship")
    collisions = sorted(set(entities) & set(relationships))
    if collisions:
        raise CandidateIndexError(
            f"ID {collisions[0]!r} is used by both entity and relationship collections"
        )

    components = {**entities, **relationships}
    return {
        "candidate_hash": hash_bim_json_candidate(candidate),
        "entities": copy.deepcopy(entities),
        "relationships": copy.deepcopy(relationships),
        "component_hashes": {
            component_id: hash_json_value(component)
            for component_id, component in sorted(components.items())
        },
    }


def _index_collection(value: Any, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        raise CandidateIndexError(f"candidate {label} collection must be a list")
    result: dict[str, dict[str, Any]] = {}
    for index, component in enumerate(value):
        if not isinstance(component, Mapping):
            raise CandidateIndexError(f"{label} at index {index} must be an object")
        component_id = component.get("id")
        if not isinstance(component_id, str) or not component_id:
            raise CandidateIndexError(f"{label} at index {index} has no stable id")
        if component_id in result:
            raise CandidateIndexError(f"duplicate {label} id {component_id!r}")
        result[component_id] = copy.deepcopy(dict(component))
    return result
