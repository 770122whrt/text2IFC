from __future__ import annotations

from pathlib import Path

from text2ifc_extractor import extract_ifc2x3


ROOT = Path(__file__).resolve().parents[2]
EXTRACT_ONLY_PRODUCT_FIXTURES = [
    ROOT / "dataset" / "ifc" / "train" / "e9z.ifc",
    ROOT / "dataset" / "ifc" / "train" / "px4_1.ifc",
]


def test_extract_only_product_class_losses_are_explicit() -> None:
    results = [extract_ifc2x3(path) for path in EXTRACT_ONLY_PRODUCT_FIXTURES]
    class_losses = [
        loss
        for result in results
        for loss in result.losses
        if loss["kind"] == "CLASS_CAPABILITY"
    ]

    assert class_losses
    for loss in class_losses:
        assert loss["source_item_class"] in {
            "IfcBuildingElementProxy",
            "IfcFurnishingElement",
        }
        assert loss["source_capability"] == "extract-only"
        assert loss["substitution"] == "none"
