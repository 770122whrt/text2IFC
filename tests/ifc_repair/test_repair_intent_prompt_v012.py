from __future__ import annotations

from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_ifc_repair.repair_intent import REPAIR_INTENT_SCHEMA_VERSION_0_8
from text2ifc_ifc_repair.request_stage import _INTENT_CONTRACTS


PROMPT_ID = "ifc-repair-intent.v0.12"


def test_zcode_v012_historical_precision_contract_is_preserved() -> None:
    from pathlib import Path
    rendered = (Path(__file__).resolve().parents[2] / "archive/zcode-local-20260905/published-contracts/ifc-repair-intent-v0.12.md").read_text(encoding="utf-8")

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
