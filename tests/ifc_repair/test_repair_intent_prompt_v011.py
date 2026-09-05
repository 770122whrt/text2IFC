from __future__ import annotations

from copy import deepcopy

from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.repair_intent import REPAIR_INTENT_SCHEMA_VERSION_0_8
from text2ifc_ifc_repair.request_stage import (
    _INTENT_CONTRACTS,
    generate_repair_intent,
)
from tests.ifc_repair.test_repair_intent_v08 import (
    BODY_VERSION,
    Provider,
    SOURCE,
    _operation,
)


PROMPT_ID = "ifc-repair-intent.v0.11"


def test_v011_remains_registered_and_forbids_implicit_root_attribute_inference() -> None:
    assert _INTENT_CONTRACTS[REPAIR_INTENT_SCHEMA_VERSION_0_8][1] != PROMPT_ID

    rendered = render_prompt(
        template_id=PROMPT_ID,
        inputs={
            "REPAIR_REQUEST": "EXAMPLE_ONLY",
            "SUPPORTED_OPERATIONS": [],
            "REPAIR_INTENT_SCHEMA": {},
            "VALIDATION_FEEDBACK": [],
        },
    )["text"]

    for exact in (
        "Property claims are not implicit IFC root attributes",
        "authorizes `attribute_intents` only when it explicitly names",
        "identifier-shaped value does not authorize an IFC",
        "preserve the user's property phrase as",
        "`natural_language_property` so Stage 1.5 can resolve it",
        "Explicit `IFC Tag` or `Tag` attribute wording",
        "does not create a phrase table",
    ):
        assert exact in rendered
    for forbidden_case_hook in ("B-NEW-01", "M2", "1fc01d35"):
        assert forbidden_case_hook not in rendered


def test_v011_public_stage1_accepts_property_and_explicit_tag_boundaries(
    tmp_path,
) -> None:
    property_operation = _operation("beam")
    property_operation["property_intents"] = [
        {
            "intent_kind": "natural_language_property",
            "property_phrase": "member identifier",
            "raw_value": "REF-42",
            "raw_unit": None,
            "scope": "occurrence_direct",
            "source": SOURCE,
        }
    ]
    property_body = {
        "schema_version": BODY_VERSION,
        "operations": [property_operation],
        "unsupported_requests": [],
        "semantic_bundles": [],
        "provenance": [SOURCE],
    }
    property_result = generate_repair_intent(
        provider=Provider(property_body),
        request_id="property-identity-boundary",
        repair_request=(
            "Add a beam and set its member identifier to REF-42."
        ),
        registry=create_default_registry(),
        output_dir=tmp_path / "property",
        max_attempts=1,
        intent_schema_version=REPAIR_INTENT_SCHEMA_VERSION_0_8,
    )

    explicit_tag_operation = deepcopy(_operation("beam"))
    explicit_tag_operation["attribute_intents"] = [
        {
            "intent_kind": "attribute",
            "name": "Tag",
            "value": "TAG-42",
            "source": SOURCE,
        }
    ]
    explicit_tag_body = {
        **property_body,
        "operations": [explicit_tag_operation],
    }
    tag_result = generate_repair_intent(
        provider=Provider(explicit_tag_body),
        request_id="explicit-tag-boundary",
        repair_request="Add a beam and set its IFC Tag attribute to TAG-42.",
        registry=create_default_registry(),
        output_dir=tmp_path / "tag",
        max_attempts=1,
        intent_schema_version=REPAIR_INTENT_SCHEMA_VERSION_0_8,
    )

    assert property_result["valid"] is True
    assert property_result["attempts"][0]["normalizations"] == []
    property = property_result["intent"].operations[0]
    assert property.attribute_intents == ()
    assert property.property_intents[0].property_phrase == "member identifier"
    assert tag_result["valid"] is True
    tag = tag_result["intent"].operations[0]
    assert tag.property_intents == ()
    assert tag.attribute_intents[0].name == "Tag"
