from __future__ import annotations

from pathlib import Path

from text2ifc_extractor import extract_ifc2x3


GEOMETRY_LOSS_KINDS = {
    "BOOLEAN_GEOMETRY",
    "FACETED_BREP_GEOMETRY",
    "MAPPED_GEOMETRY",
    "SURFACE_MODEL_GEOMETRY",
    "TESSELLATED_GEOMETRY",
    "UNSUPPORTED_GEOMETRY",
}
ROOT = Path(__file__).resolve().parents[2]
REPRESENTATIVE_IFC = [
    ROOT / "dataset" / "ifc" / "train" / "hxp.ifc",
    ROOT / "dataset" / "ifc" / "train" / "i5n.ifc",
    ROOT / "dataset" / "ifc" / "train" / "vt2_1.ifc",
]


def test_unsupported_complex_geometry_losses_record_no_substitution() -> None:
    results = [extract_ifc2x3(path) for path in REPRESENTATIVE_IFC]
    geometry_losses = [
        loss
        for result in results
        for loss in result.losses
        if loss["kind"] in GEOMETRY_LOSS_KINDS
    ]

    assert geometry_losses
    for loss in geometry_losses:
        assert loss["substitution"] == "none"
        assert loss["source_item_class"].startswith("Ifc")
