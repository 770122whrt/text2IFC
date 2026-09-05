"""Failure family: semantic-bundle claims must reach every downstream consumer.

Root cause (composite milestone live C1): the Provider expressed the
restoration properties through ``semantic_bundle_refs`` instead of inline
``property_intents``.  ``resolve_repair_intent`` expands the bundle into the
resolution-local operation copy, so the property authority resolved and was
attached to ``authorized_semantics`` — but ``build_production_evidence``
receives the ORIGINAL intent whose operations still carry empty
``property_intents``, so ``_property_claim_matches_authority`` found no
matching claim and the run failed with ``AUTHORIZED_PROPERTY_CLAIM_MISMATCH``.

Mechanism fix: the intent stage canonicalizes bundle references into inline
claims (operation-local values win, bundle order is stable, unknown refs stay
an error), so every downstream consumer — evidence builder, durable property
coordinator, resolution flow — sees the same inline form.

Red test below: an intent whose only claims live in a bundle must (1) build
production evidence without a claim mismatch when the matching authority is
attached, and (2) route through the natural-language property path when the
bundle holds natural-language claims.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for p in (str(ROOT), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from text2ifc_ifc_repair.api import _has_natural_property_claims  # noqa: E402
from text2ifc_ifc_repair.repair_intent import (  # noqa: E402
    OperationIntent,
    PublicProvenance,
    RepairIntent,
    RepairIntentError,
)
from text2ifc_ifc_repair.request_stage import (  # noqa: E402
    canonicalize_semantic_bundle_claims,
)

SOURCE = {
    "source_kind": "user_request",
    "reference": "request:/text",
    "excerpt": "restore properties",
}


def _bundle_claim(**overrides):
    claim = {
        "intent_kind": "exact_property",
        "set_name": "Pset_BeamCommon",
        "property_name": "LoadBearing",
        "raw_value": True,
        "raw_unit": None,
        "requested_value_type": "IfcBoolean",
        "scope": "occurrence_direct",
        "source": SOURCE,
    }
    claim.update(overrides)
    return claim


def _intent_document(operations: list[dict], bundles: list[dict]) -> dict:
    return {
        "schema_version": "text2ifc/ifc-repair-intent/0.8",
        "operations": operations,
        "semantic_bundles": bundles,
        "provenance": [SOURCE],
        "unsupported_requests": [],
    }


def _beam_operation(bundle_refs=None, property_intents=None) -> dict:
    return {
        "operation_id": "op-beam-1",
        "operation_type": "add_beam",
        "routing_intent": {
            "component_family": "beam",
            "action": "add",
            "operation_profile": "beam.add.v0.3",
            "source": SOURCE,
        },
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcBuildingStorey"],
            "names": ["Level 1"],
        },
        "parameters": {
            "axis": {
                "start": {"x_mm": 0, "y_mm": 0, "z_mm": 0},
                "end": {"x_mm": 1000, "y_mm": 0, "z_mm": 0},
            },
            "section": {"shape": "rectangle", "width_mm": 250, "height_mm": 250},
        },
        "attribute_intents": [],
        "property_intents": property_intents or [],
        "semantic_bundle_refs": bundle_refs or [],
        "quantity_intents": [],
        "occurrence_reuse_intent": None,
        "prototype_intent": None,
        "provenance": [SOURCE],
    }


def _intent(document: dict) -> RepairIntent:
    from text2ifc_ifc_repair.operations import create_default_registry

    return RepairIntent.from_dict(
        {
            "schema_version": "text2ifc/ifc-repair-intent/0.8",
            "request_id": "request-test",
            "source_request_hash": "sha256:" + "a" * 64,
            "model_fingerprint": "sha256:" + "b" * 64,
            "prompt_fingerprint": "sha256:" + "c" * 64,
            "operations": document["operations"],
            "semantic_bundles": document["semantic_bundles"],
            "provenance": document["provenance"],
            "unsupported_requests": [],
        },
        registry=create_default_registry(),
        require_complete=False,
    )


def test_bundle_claims_are_inlined_into_operations() -> None:
    document = _intent_document(
        operations=[_beam_operation(bundle_refs=["bundle-1"])],
        bundles=[
            {
                "bundle_id": "bundle-1",
                "property_intents": [_bundle_claim()],
                "quantity_intents": [],
                "provenance": [SOURCE],
            }
        ],
    )
    intent = _intent(document)
    canonicalized = canonicalize_semantic_bundle_claims(intent)

    assert canonicalized.operations[0].property_intents
    claim = canonicalized.operations[0].property_intents[0]
    assert claim.set_name == "Pset_BeamCommon"
    assert claim.property_name == "LoadBearing"
    assert claim.value is True
    assert canonicalized.operations[0].semantic_bundle_refs == ()


def test_operation_local_claims_override_bundle_slots() -> None:
    document = _intent_document(
        operations=[
            _beam_operation(
                bundle_refs=["bundle-1"],
                property_intents=[
                    _bundle_claim(raw_value=False),
                ],
            )
        ],
        bundles=[
            {
                "bundle_id": "bundle-1",
                "property_intents": [_bundle_claim(raw_value=True)],
                "quantity_intents": [],
                "provenance": [SOURCE],
            }
        ],
    )
    intent = _intent(document)
    canonicalized = canonicalize_semantic_bundle_claims(intent)

    claims = canonicalized.operations[0].property_intents
    assert len(claims) == 1
    assert claims[0].value is False


def test_natural_language_bundle_claims_route_property_runtime() -> None:
    document = _intent_document(
        operations=[_beam_operation(bundle_refs=["bundle-1"])],
        bundles=[
            {
                "bundle_id": "bundle-1",
                "property_intents": [
                    {
                        "intent_kind": "natural_language_property",
                        "property_phrase": "load bearing",
                        "raw_unit": None,
                        "raw_value": True,
                        "scope": "occurrence_direct",
                        "source": SOURCE,
                    }
                ],
                "quantity_intents": [],
                "provenance": [SOURCE],
            }
        ],
    )
    intent = _intent(document)
    # The API detector scans bundles directly, so the runtime routes even
    # pre-canonical. The canonicalizer keeps the inline form equivalent.
    assert _has_natural_property_claims(intent) is True
    canonicalized = canonicalize_semantic_bundle_claims(intent)
    assert _has_natural_property_claims(canonicalized) is True
    assert canonicalized.operations[0].property_intents[0].property_phrase == (
        "load bearing"
    )


def test_unknown_bundle_reference_fails_closed() -> None:
    document = _intent_document(
        operations=[_beam_operation(bundle_refs=["missing-bundle"])],
        bundles=[],
    )
    # RepairIntent.from_dict already fails closed on unknown references
    # ("Unknown semantic bundle reference"); the canonicalizer keeps the same
    # guard for direct callers.
    with pytest.raises(RepairIntentError):
        _intent(document)


def test_bundle_claims_reach_production_evidence_matching() -> None:
    """The original live failure: authority attached, claim missing."""

    from text2ifc_ifc_repair.production_evidence import _property_claim_matches_authority

    document = _intent_document(
        operations=[_beam_operation(bundle_refs=["bundle-1"])],
        bundles=[
            {
                "bundle_id": "bundle-1",
                "property_intents": [_bundle_claim()],
                "quantity_intents": [],
                "provenance": [SOURCE],
            }
        ],
    )
    intent = _intent(document)
    canonicalized = canonicalize_semantic_bundle_claims(intent)
    authority = {
        "operation_id": "op-beam-1",
        "set_name": "Pset_BeamCommon",
        "property_name": "LoadBearing",
        "value": True,
        "value_type": "IfcBoolean",
        "ownership": "occurrence_direct",
        "source": SOURCE,
    }
    claim = canonicalized.operations[0].property_intents[0]
    assert _property_claim_matches_authority(claim, authority) is True
