from __future__ import annotations

from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_ifc_repair.repair_intent import REPAIR_INTENT_SCHEMA_VERSION_0_8
from text2ifc_ifc_repair.request_stage import _INTENT_CONTRACTS


PROMPT_ID = "ifc-repair-intent.v0.12"


def test_v012_is_current_and_preserves_declared_geometry_precision() -> None:
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
        "Geometry constraint tolerance preserves stated precision",
        "emit `tolerance_mm: 0.1`",
        "explicitly requires exact or zero-tolerance matching",
        "emit `tolerance_mm: 0`",
        "Do not treat a rounded decimal as an exact stored coordinate",
    ):
        assert exact in rendered
    for forbidden_case_hook in (
        "C2",
        "580.3",
        "580.341581",
        "2AJ6T3vZDDZRJL7kCpGl86",
    ):
        assert forbidden_case_hook not in rendered
