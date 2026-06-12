from __future__ import annotations

from pathlib import Path

import pytest

from text2ifc_extractor import extract_ifc2x3


ROOT = Path(__file__).resolve().parents[2]
HXP = ROOT / "dataset" / "ifc" / "train" / "hxp.ifc"
I5N = ROOT / "dataset" / "ifc" / "train" / "i5n.ifc"
VT2_1 = ROOT / "dataset" / "ifc" / "train" / "vt2_1.ifc"


@pytest.fixture(scope="session")
def hxp_result():
    return extract_ifc2x3(HXP)


@pytest.fixture(scope="session")
def i5n_result():
    return extract_ifc2x3(I5N)


@pytest.fixture(scope="session")
def vt2_result():
    return extract_ifc2x3(VT2_1)
