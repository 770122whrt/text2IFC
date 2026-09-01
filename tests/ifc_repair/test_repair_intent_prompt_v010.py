from __future__ import annotations

from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_ifc_repair.repair_intent import REPAIR_INTENT_SCHEMA_VERSION_0_8
from text2ifc_ifc_repair.request_stage import _INTENT_CONTRACTS


PROMPT_ID = "ifc-repair-intent.v0.10"


def test_v010_is_current_and_freezes_internal_id_boundary() -> None:
    assert _INTENT_CONTRACTS[REPAIR_INTENT_SCHEMA_VERSION_0_8][1] == PROMPT_ID

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
        "Stable internal identifiers are not IFC target identities",
        "^[A-Za-z0-9][A-Za-z0-9._:/-]*$",
        "do not copy or embed a target GlobalId, Tag, Name",
        "IFC target identities belong",
        "only in `target_query`",
        "Property identity and requested value are independent claims",
    ):
        assert exact in rendered
