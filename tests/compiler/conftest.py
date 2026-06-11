import copy
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
COMPLETE_FIXTURE = ROOT / "tests" / "contract" / "fixtures" / "complete.json"


@pytest.fixture
def complete_document() -> dict:
    document = json.loads(COMPLETE_FIXTURE.read_text(encoding="utf-8"))
    return copy.deepcopy(document)


@pytest.fixture
def canonical_ids(complete_document: dict) -> set[str]:
    document = complete_document
    return {
        document["project"]["id"],
        document["site"]["id"],
        document["building"]["id"],
        *(storey["id"] for storey in document["storeys"]),
        *(element["id"] for element in document["elements"]),
    }

