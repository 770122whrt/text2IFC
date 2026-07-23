from __future__ import annotations

import json
from pathlib import Path

from text2ifc_knowledge.property_search import (
    PropertyKnowledgeQuery,
    create_default_property_resolver,
)


def test_checked_in_retrieval_evaluation_has_zero_false_authorizations(
    project_root: Path,
) -> None:
    dataset = json.loads(
        (
            project_root
            / "tests"
            / "fixtures"
            / "knowledge"
            / "phase10_2_property_retrieval.json"
        ).read_text(encoding="utf-8")
    )
    cases = dataset["cases"]
    assert len(cases) >= 40
    assert any(any("\u4e00" <= char <= "\u9fff" for char in case["phrase"]) for case in cases)
    assert any(case["phrase"].isascii() for case in cases)

    resolver = create_default_property_resolver()
    false_authorizations: list[str] = []
    expected_authorizations = 0
    correct_authorizations = 0
    for case in cases:
        try:
            decision = resolver.resolve(
                PropertyKnowledgeQuery(
                    target_ifc_class=case["class"],
                    phrase=case["phrase"],
                    raw_value=case["value"],
                )
            )
        except ValueError:
            decision = None
        authorized_path = None
        if (
            decision is not None
            and decision.status == "standard_resolved"
            and decision.exact_intent is not None
        ):
            authorized_path = (
                f"{decision.exact_intent.set_name}."
                f"{decision.exact_intent.property_name}"
            )
        if case["authorize"]:
            expected_authorizations += 1
            if authorized_path == case["expected"]:
                correct_authorizations += 1
        elif authorized_path is not None:
            false_authorizations.append(case["id"])

    assert false_authorizations == []
    assert correct_authorizations == expected_authorizations
