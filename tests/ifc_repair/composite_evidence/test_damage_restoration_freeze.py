"""Frozen damage-restoration case set: full offline verification.

Semantics (user-requested, replacing the earlier addition/renovation
semantics): the building natively contains the members; damage removes them
deterministically; the repair restores them at their own storey-local
geometry; the repaired model is compared with the original.

Per case, verified here: damage removed exactly the requested members; the
public API chain succeeded; class counts returned to the original values;
each restored member sits at the removed member's placement with the removed
member's section; the global comparator changed only the restoration set.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import ifcopenshell
import pytest

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
for p in (str(ROOT), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from text2ifc_agent.providers import ProviderOutput  # noqa: E402
from text2ifc_ifc_repair.api import RepairAPI  # noqa: E402
from text2ifc_ifc_repair.compare import compare_ifc_models  # noqa: E402
from text2ifc_ifc_repair.mutation import (  # noqa: E402
    remove_structural_members,
)

FREEZE = json.loads(
    (
        ROOT
        / "docs/validation/repair-composite-milestone/damage-restoration-freeze.json"
    ).read_text(encoding="utf-8")
)
VVO = ROOT / "dataset/ifc/train/vvo.ifc"
SOURCE = {
    "source_kind": "user_request",
    "reference": "request:/text",
    "excerpt": "restore the damaged structural members",
}

MEMBERS = {
    "17tPjyQtf2L9JnbXXmcT8w": {
        "family": "beam",
        "storey_name": "标高7",
        "axis": {
            "start": {"x_mm": -7452.2, "y_mm": -14836.2, "z_mm": 0.0},
            "end": {"x_mm": -3549.2, "y_mm": -14836.2, "z_mm": 0.0},
        },
        "section": {"shape": "rectangle", "width_mm": 570.0, "height_mm": 400.0},
    },
    "17tPjyQtf2L9JnbXXmcTUF": {
        "family": "beam",
        "storey_name": "标高7",
        "axis": {
            "start": {"x_mm": -3316.6, "y_mm": -3863.5, "z_mm": 0.0},
            "end": {"x_mm": -3316.6, "y_mm": -8803.5, "z_mm": 0.0},
        },
        "section": {"shape": "rectangle", "width_mm": 570.0, "height_mm": 455.0},
    },
    "1rsYNObuDC4euALdw6WUK4": {
        "family": "column",
        "storey_name": "标高0",
        "axis": {
            "base": {"x_mm": -3307.4, "y_mm": -9061.8, "z_mm": 0.0},
            "top": {"x_mm": -3307.4, "y_mm": -9061.8, "z_mm": 3712.1},
        },
        "section": {
            "shape": "rectangle",
            "width_mm": 500.0,
            "depth_mm": 500.0,
            "orientation": {"x": 0, "y": 1},
        },
    },
}
EXPECTED_TAG = {
    "17tPjyQtf2L9JnbXXmcT8w": "restore-beam-t8w",
    "17tPjyQtf2L9JnbXXmcTUF": "restore-beam-tuf",
    "1rsYNObuDC4euALdw6WUK4": "restore-column-k4",
}


def _section_json(prompt: str, heading: str) -> dict:
    part = prompt.split(f"## {heading}", 1)[1].split("\n## ", 1)[0].strip()
    return json.loads(part)


def _operation_for(gid: str) -> dict:
    member = MEMBERS[gid]
    family = member["family"]
    return {
        "operation_id": EXPECTED_TAG[gid],
        "operation_type": f"add_{family}",
        "routing_intent": {
            "component_family": family,
            "action": "add",
            "operation_profile": f"{family}.add.v0.3",
            "source": SOURCE,
        },
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcBuildingStorey"],
            "names": [member["storey_name"]],
        },
        "parameters": {"axis": member["axis"], "section": member["section"]},
        "attribute_intents": [],
        "property_intents": [],
        "semantic_bundle_refs": [],
        "quantity_intents": [],
        "occurrence_reuse_intent": None,
        "prototype_intent": None,
        "provenance": [SOURCE],
    }


def _intent_body(gids: list[str]) -> dict:
    return {
        "schema_version": "text2ifc/ifc-repair-intent-body/0.8",
        "operations": [_operation_for(gid) for gid in gids],
        "semantic_bundles": [],
        "provenance": [SOURCE],
        "unsupported_requests": [],
    }


class _ReplayProvider:
    """Deterministic provider replaying the frozen restoration intents."""

    def __init__(self, gids: list[str]) -> None:
        self._gids = gids
        self.calls: list[dict] = []

    def generate_candidate(self, **kwargs) -> ProviderOutput:
        self.calls.append(kwargs)
        stage = kwargs["state"]["stage"]
        if stage == "ifc_repair_intent":
            return ProviderOutput(
                text=json.dumps(_intent_body(self._gids), ensure_ascii=False),
                metadata={"provider": "fixture", "model": "fixture-model"},
            )
        prompt = kwargs["prompt"]
        schema = kwargs["schema"]
        projection = _section_json(prompt, "Resolved operation projection")
        operations = [
            {
                "operation_id": op["operation_id"],
                "operation_type": op["operation_type"],
                "target": op["target"],
                "parameters": op["parameters"],
                "evidence_refs": list(op["evidence_refs"]),
            }
            for op in projection["operations"]
        ]
        scope = sorted(
            {
                str(value)
                for op in projection["operations"]
                for value in op.get("scope_ids", ())
                or [op["target"].get(k) for k in op["target"]]
            }
        )
        evidence = sorted(
            {str(v) for op in projection["operations"] for v in op["evidence_refs"]}
        )
        binding_lines = prompt.split("## Immutable bindings", 1)[1].split(
            "## Resolved operation projection", 1
        )[0]
        bindings = dict(
            re.findall(r"^- ([^:]+): (.+)$", binding_lines, flags=re.MULTILINE)
        )
        return ProviderOutput(
            text=json.dumps(
                {
                    "schema_version": str(schema["$id"]),
                    "draft_id": "draft-damage-restoration",
                    "base_model_fingerprint": bindings["model"],
                    "source_request_hash": bindings["source request"],
                    "semantic_manifest_ref": bindings["semantic manifest ref"],
                    "semantic_manifest_sha256": bindings["semantic manifest hash"],
                    "semantic_summary": _section_json(
                        prompt, "Semantic group counts"
                    ),
                    "scope": {"target_ids": scope, "forbidden_ids": []},
                    "evidence_refs": evidence,
                    "preconditions": [],
                    "postconditions": [],
                    "operations": operations,
                },
                ensure_ascii=False,
            ),
            metadata={"provider": "fixture", "model": "fixture-model"},
        )


@pytest.mark.parametrize("case", FREEZE["cases"], ids=lambda c: c["case_id"])
def test_damage_restoration_case(case: dict, tmp_path: Path) -> None:
    gids = list(case["damage"]["beam_global_ids"]) + list(
        case["damage"]["column_global_ids"]
    )
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    remove_structural_members(
        source_path=VVO,
        output_dir=scratch / "mutation",
        beam_global_ids=tuple(case["damage"]["beam_global_ids"]),
        column_global_ids=tuple(case["damage"]["column_global_ids"]),
    )
    damaged = scratch / "mutation" / "damaged.ifc"
    damaged_model = ifcopenshell.open(str(damaged))
    original_model = ifcopenshell.open(str(VVO))
    assert len(damaged_model.by_type("IfcBeam")) == len(
        original_model.by_type("IfcBeam")
    ) - len(case["damage"]["beam_global_ids"])
    assert len(damaged_model.by_type("IfcColumn")) == len(
        original_model.by_type("IfcColumn")
    ) - len(case["damage"]["column_global_ids"])

    provider = _ReplayProvider(gids)
    api = RepairAPI(
        tmp_path / "runs",
        provider=provider,
        intent_schema_version="text2ifc/ifc-repair-intent/0.8",
    )
    final = api.start(str(damaged), str(case["request"]))

    assert final.status == "succeeded", final.reason_code
    repaired = (
        tmp_path / "runs" / final.run_directory / final.artifacts["successful_ifc"]
    )
    repaired_model = ifcopenshell.open(str(repaired))

    for ifc_class in (
        "IfcBeam",
        "IfcColumn",
        "IfcWall",
        "IfcDoor",
        "IfcWindow",
        "IfcOpeningElement",
    ):
        assert len(repaired_model.by_type(ifc_class)) == len(
            original_model.by_type(ifc_class)
        ), ifc_class

    for gid in gids:
        member = MEMBERS[gid]
        ifc_class = f"Ifc{member['family'].title()}"
        restored = [
            entity
            for entity in repaired_model.by_type(ifc_class)
            if entity.Tag == EXPECTED_TAG[gid]
        ]
        assert len(restored) == 1, gid
        placement = restored[0].ObjectPlacement.RelativePlacement.Location.Coordinates
        origin_key = "start" if member["family"] == "beam" else "base"
        assert abs(placement[0] - member["axis"][origin_key]["x_mm"]) < 1.0, gid
        assert abs(placement[1] - member["axis"][origin_key]["y_mm"]) < 1.0, gid
        solid = restored[0].Representation.Representations[0].Items[0]
        section = member["section"]
        if member["family"] == "beam":
            assert abs(float(solid.SweptArea.XDim) - section["width_mm"]) < 1.0
            assert abs(float(solid.SweptArea.YDim) - section["height_mm"]) < 1.0
        else:
            assert abs(float(solid.SweptArea.XDim) - section["width_mm"]) < 1.0
            assert abs(float(solid.SweptArea.YDim) - section["depth_mm"]) < 1.0

    comparison = compare_ifc_models(
        VVO, repaired, allowed_changed_ids=()
    )
    report = comparison
    assert report["comparison_status"] == "passed", report.get(
        "comparison_error_code"
    )
    added = set(report.get("added_ids") or [])
    assert added
