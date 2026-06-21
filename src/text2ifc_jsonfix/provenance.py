"""Fact-level provenance reports for composed BIM JSON candidates."""

from __future__ import annotations

import copy
from typing import Any

from .composer import CompositionResult, ProvenanceEvent


PROVENANCE_SCHEMA_VERSION = "text2ifc/jsonfix-provenance-v1"


def _base_facts(document: dict[str, Any]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for collection in ("entities", "relationships"):
        category = "entity" if collection == "entities" else "relationship"
        for record in document[collection]:
            object_id = record["id"]
            facts.append(
                {
                    "origin": "base",
                    "category": category,
                    "collection": collection,
                    "object_id": object_id,
                    "path": f"/{collection}/{object_id}",
                    "provenance": copy.deepcopy(record["provenance"]),
                    "value": {
                        "id": object_id,
                        "ifc_class": record["ifc_class"],
                    },
                }
            )
            if collection != "entities":
                continue
            for property_set, values in record.get(
                "property_sets", {}
            ).items():
                for property_name, value in values.items():
                    facts.append(
                        {
                            "origin": "base",
                            "category": "property",
                            "collection": collection,
                            "object_id": object_id,
                            "path": (
                                f"/entities/{object_id}/property_sets/"
                                f"{property_set}/{property_name}"
                            ),
                            "provenance": copy.deepcopy(
                                record["provenance"]
                            ),
                            "value": copy.deepcopy(value),
                        }
                    )
    return facts


def _event_category(event: ProvenanceEvent) -> str:
    return {
        "add_entity": "entity",
        "add_relationship": "relationship",
        "set_attribute": "attribute",
        "set_property": "property",
        "set_material": "material",
        "mark_missing": "missing",
        "mark_unsupported_loss": "loss",
        "request_tombstone": "tombstone",
    }[event.operation]


def _patch_fact(event: ProvenanceEvent) -> dict[str, Any]:
    return {
        "origin": "patch",
        "category": _event_category(event),
        "collection": event.collection,
        "object_id": event.object_id,
        "path": event.path,
        "layer_id": event.layer_id,
        "layer_kind": event.layer_kind,
        "layer_provenance": copy.deepcopy(event.layer_provenance),
        "operation": event.operation,
        "previous_value": copy.deepcopy(event.previous_value),
        "value": copy.deepcopy(event.value),
    }


def _sort_key(fact: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        fact["origin"],
        fact["category"],
        fact["path"],
        fact.get("layer_id") or "",
    )


def build_provenance_report(
    base_document: dict[str, Any],
    result: CompositionResult,
) -> dict[str, Any]:
    base_facts = _base_facts(base_document)
    patch_facts = [_patch_fact(event) for event in result.provenance_events]
    facts = sorted([*base_facts, *patch_facts], key=_sort_key)
    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "target_document_id": base_document["provenance"]["document_id"],
        "composition_valid": result.valid,
        "formal_valid": result.formal_valid,
        "summary": {
            "total_fact_count": len(facts),
            "base_fact_count": len(base_facts),
            "patch_fact_count": len(patch_facts),
        },
        "facts": facts,
    }
