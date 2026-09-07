from __future__ import annotations

import json
from pathlib import Path

from text2ifc_compiler import compile_document, open_ifc
from text2ifc_presentation import (
    generation_profile_names,
    item_appearance_signatures,
    select_generation_profile,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def _document() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _styled_product_signatures(model):
    result = {}
    for product in model.by_type("IfcProduct"):
        representation = getattr(product, "Representation", None)
        if representation is None:
            continue
        signatures = []
        for shape in representation.Representations:
            for item in shape.Items:
                signatures.extend(item_appearance_signatures(item))
        if signatures:
            result[str(product.GlobalId)] = tuple(signatures)
    return result


def test_generation_profile_selection_is_seeded_and_bounded() -> None:
    allowed = set(generation_profile_names())
    assert {"demo-colorful-v0.1", "warm-residential-v0.1", "modern-cool-v0.1"} <= allowed
    assert select_generation_profile("demo-colorful-v0.1", seed="ignored") == "demo-colorful-v0.1"
    assert select_generation_profile("auto", seed="same") == select_generation_profile(
        "auto", seed="same"
    )
    selected = {select_generation_profile("auto", seed=f"seed-{index}") for index in range(12)}
    assert selected <= allowed
    assert len(selected) > 1


def test_generation_compiler_applies_coordinated_deterministic_profile_without_schema_change(
    tmp_path: Path,
) -> None:
    document = _document()
    first = tmp_path / "first.ifc"
    second = tmp_path / "second.ifc"

    first_result = compile_document(
        document,
        first,
        appearance_profile="demo-colorful-v0.1",
        appearance_seed="case-a",
    )
    second_result = compile_document(
        document,
        second,
        appearance_profile="demo-colorful-v0.1",
        appearance_seed="case-a",
    )

    assert first_result.success and second_result.success
    first_styles = _styled_product_signatures(open_ifc(first))
    second_styles = _styled_product_signatures(open_ifc(second))
    assert first_styles
    assert first_styles == second_styles
    distinct_colours = {
        (signature["red"], signature["green"], signature["blue"])
        for signatures in first_styles.values()
        for signature in signatures
    }
    assert len(distinct_colours) >= 3


def test_generation_profile_does_not_mutate_bim_json_document(tmp_path: Path) -> None:
    document = _document()
    before = json.loads(json.dumps(document))

    result = compile_document(
        document,
        tmp_path / "styled.ifc",
        appearance_profile="warm-residential-v0.1",
        appearance_seed="immutable",
    )

    assert result.success
    assert document == before
