"""Damage-restoration roundtrip: vvo beam removed then restored.

Validates the semantic the user requested for the composite milestone:
original (native beams) -> damage (remove one beam) -> repair (re-add at the
same storey-local axis and section) -> repaired compared with original
(class counts restored, restored member geometry aligned).
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import ifcopenshell

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
for p in (str(ROOT), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from text2ifc_agent.providers import ProviderOutput  # noqa: E402
from text2ifc_ifc_repair.api import RepairAPI  # noqa: E402
from text2ifc_ifc_repair.mutation import remove_structural_members  # noqa: E402

VVO = ROOT / "dataset/ifc/train/vvo.ifc"
BEAM_GID = "17tPjyQtf2L9JnbXXmcT8w"
STOREY_NAME = "标高7"
AXIS = {
    "start": {"x_mm": -7452.2, "y_mm": -14836.2, "z_mm": 0.0},
    "end": {"x_mm": -3549.2, "y_mm": -14836.2, "z_mm": 0.0},
}
SECTION = {"shape": "rectangle", "width_mm": 570.0, "height_mm": 400.0}
SOURCE = {
    "source_kind": "user_request",
    "reference": "request:/text",
    "excerpt": "restore the damaged beam",
}


def _section_json(prompt: str, heading: str) -> dict:
    part = prompt.split(f"## {heading}", 1)[1].split("\n## ", 1)[0].strip()
    return json.loads(part)


def _intent_body() -> dict:
    return {
        "schema_version": "text2ifc/ifc-repair-intent-body/0.8",
        "operations": [
            {
                "operation_id": "restore-beam-1",
                "operation_type": "add_beam",
                "routing_intent": {
                    "component_family": "beam",
                    "action": "add",
                    "operation_profile": "beam.add.v0.3",
                    "source": SOURCE,
                },
                "target_query": {
                    "schema_version": "text2ifc/ifc-target-query/0.1",
                    "allowed_ifc_classes": ["IfcBuildingStorey"],
                    "names": [STOREY_NAME],
                },
                "parameters": {"axis": AXIS, "section": SECTION},
                "attribute_intents": [],
                "property_intents": [],
                "semantic_bundle_refs": [],
                "quantity_intents": [],
                "occurrence_reuse_intent": None,
                "prototype_intent": None,
                "provenance": [SOURCE],
            }
        ],
        "semantic_bundles": [],
        "provenance": [SOURCE],
        "unsupported_requests": [],
    }


class _ReplayProvider:
    """Deterministic two-stage provider mirroring the frozen composite replay."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate_candidate(self, **kwargs) -> ProviderOutput:
        self.calls.append(kwargs)
        stage = kwargs["state"]["stage"]
        if stage == "ifc_repair_intent":
            return ProviderOutput(
                text=json.dumps(_intent_body(), ensure_ascii=False),
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
                    "draft_id": "draft-restore-beam-1",
                    "base_model_fingerprint": bindings["model"],
                    "source_request_hash": bindings["source request"],
                    "semantic_manifest_ref": bindings["semantic manifest ref"],
                    "semantic_manifest_sha256": bindings["semantic manifest hash"],
                    "semantic_summary": _section_json(prompt, "Semantic group counts"),
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


def test_vvo_beam_damage_restoration_roundtrip(tmp_path: Path) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    remove_structural_members(
        source_path=VVO,
        output_dir=scratch / "mutation",
        beam_global_ids=(BEAM_GID,),
    )
    damaged = scratch / "mutation" / "damaged.ifc"
    damaged_model = ifcopenshell.open(str(damaged))
    assert len(damaged_model.by_type("IfcBeam")) == 5

    provider = _ReplayProvider()
    api = RepairAPI(
        tmp_path / "runs",
        provider=provider,
        intent_schema_version="text2ifc/ifc-repair-intent/0.8",
    )
    final = api.start(str(damaged), "restore the beam")

    assert final.status == "succeeded", final.reason_code
    repaired = (
        tmp_path / "runs" / final.run_directory / final.artifacts["successful_ifc"]
    )
    repaired_model = ifcopenshell.open(str(repaired))
    original_model = ifcopenshell.open(str(VVO))

    # Class counts restored to the original values.
    for ifc_class in ("IfcBeam", "IfcColumn", "IfcWall", "IfcDoor", "IfcWindow"):
        assert len(repaired_model.by_type(ifc_class)) == len(
            original_model.by_type(ifc_class)
        ), ifc_class

    # The restored beam aligns with the removed member's storey-local axis and section.
    restored = [
        beam
        for beam in repaired_model.by_type("IfcBeam")
        if beam.Tag == "restore-beam-1"
    ]
    assert len(restored) == 1
    beam = restored[0]
    placement = beam.ObjectPlacement.RelativePlacement.Location.Coordinates
    assert abs(placement[0] - AXIS["start"]["x_mm"]) < 1.0
    assert abs(placement[1] - AXIS["start"]["y_mm"]) < 1.0
    solid = beam.Representation.Representations[0].Items[0]
    assert abs(float(solid.SweptArea.XDim) - SECTION["width_mm"]) < 1.0
    assert abs(float(solid.SweptArea.YDim) - SECTION["height_mm"]) < 1.0


COLUMN_GID = "1rsYNObuDC4euALdw6WUK4"
COLUMN_STOREY_NAME = "标高0"
COLUMN_AXIS = {
    "base": {"x_mm": -3307.4, "y_mm": -9061.8, "z_mm": 0.0},
    "top": {"x_mm": -3307.4, "y_mm": -9061.8, "z_mm": 3712.1},
}
COLUMN_SECTION = {
    "shape": "rectangle",
    "width_mm": 500.0,
    "depth_mm": 500.0,
    "orientation": {"x": 0, "y": 1},
}

BEAM_2_GID = "17tPjyQtf2L9JnbXXmcTUF"
BEAM_2_AXIS = {
    "start": {"x_mm": -3316.6, "y_mm": -3863.5, "z_mm": 0.0},
    "end": {"x_mm": -3316.6, "y_mm": -8803.5, "z_mm": 0.0},
}
BEAM_2_SECTION = {"shape": "rectangle", "width_mm": 570.0, "height_mm": 455.0}


def _intent_body_multi(operations_spec: list[dict]) -> dict:
    return {
        "schema_version": "text2ifc/ifc-repair-intent-body/0.8",
        "operations": operations_spec,
        "semantic_bundles": [],
        "provenance": [SOURCE],
        "unsupported_requests": [],
    }


def _beam_op(operation_id: str, axis: dict, section: dict) -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": "add_beam",
        "routing_intent": {
            "component_family": "beam",
            "action": "add",
            "operation_profile": "beam.add.v0.3",
            "source": SOURCE,
        },
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcBuildingStorey"],
            "names": [STOREY_NAME],
        },
        "parameters": {"axis": axis, "section": section},
        "attribute_intents": [],
        "property_intents": [],
        "semantic_bundle_refs": [],
        "quantity_intents": [],
        "occurrence_reuse_intent": None,
        "prototype_intent": None,
        "provenance": [SOURCE],
    }


def _column_op(operation_id: str, axis: dict, section: dict) -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": "add_column",
        "routing_intent": {
            "component_family": "column",
            "action": "add",
            "operation_profile": "column.add.v0.3",
            "source": SOURCE,
        },
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcBuildingStorey"],
            "names": [COLUMN_STOREY_NAME],
        },
        "parameters": {"axis": axis, "section": section},
        "attribute_intents": [],
        "property_intents": [],
        "semantic_bundle_refs": [],
        "quantity_intents": [],
        "occurrence_reuse_intent": None,
        "prototype_intent": None,
        "provenance": [SOURCE],
    }


class _MultiReplayProvider(_ReplayProvider):
    def __init__(self, body_builder) -> None:
        super().__init__()
        self._body_builder = body_builder

    def generate_candidate(self, **kwargs) -> ProviderOutput:
        stage = kwargs["state"]["stage"]
        if stage == "ifc_repair_intent":
            return ProviderOutput(
                text=json.dumps(self._body_builder(), ensure_ascii=False),
                metadata={"provider": "fixture", "model": "fixture-model"},
            )
        return _ReplayProvider.generate_candidate(self, **kwargs)


def _run_restoration(tmp_path: Path, provider, damaged: Path, request: str):
    api = RepairAPI(
        tmp_path / "runs",
        provider=provider,
        intent_schema_version="text2ifc/ifc-repair-intent/0.8",
    )
    return api.start(str(damaged), request)


def test_vvo_column_damage_restoration_roundtrip(tmp_path: Path) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    remove_structural_members(
        source_path=VVO,
        output_dir=scratch / "mutation",
        column_global_ids=(COLUMN_GID,),
    )
    damaged = scratch / "mutation" / "damaged.ifc"
    damaged_model = ifcopenshell.open(str(damaged))
    assert len(damaged_model.by_type("IfcColumn")) == 4

    provider = _MultiReplayProvider(
        lambda: _intent_body_multi([_column_op("restore-column-1", COLUMN_AXIS, COLUMN_SECTION)])
    )
    final = _run_restoration(
        tmp_path, provider, damaged, "restore the column"
    )

    assert final.status == "succeeded", final.reason_code
    repaired = (
        tmp_path / "runs" / final.run_directory / final.artifacts["successful_ifc"]
    )
    repaired_model = ifcopenshell.open(str(repaired))
    original_model = ifcopenshell.open(str(VVO))
    assert len(repaired_model.by_type("IfcColumn")) == len(
        original_model.by_type("IfcColumn")
    )
    restored = [
        column
        for column in repaired_model.by_type("IfcColumn")
        if column.Tag == "restore-column-1"
    ]
    assert len(restored) == 1
    placement = restored[0].ObjectPlacement.RelativePlacement.Location.Coordinates
    assert abs(placement[0] - COLUMN_AXIS["base"]["x_mm"]) < 1.0
    assert abs(placement[1] - COLUMN_AXIS["base"]["y_mm"]) < 1.0


def test_vvo_two_beams_atomic_damage_restoration(tmp_path: Path) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    remove_structural_members(
        source_path=VVO,
        output_dir=scratch / "mutation",
        beam_global_ids=(BEAM_GID, BEAM_2_GID),
    )
    damaged = scratch / "mutation" / "damaged.ifc"
    damaged_model = ifcopenshell.open(str(damaged))
    assert len(damaged_model.by_type("IfcBeam")) == 4

    def body() -> dict:
        return _intent_body_multi(
            [
                _beam_op("restore-beam-1", AXIS, SECTION),
                _beam_op("restore-beam-2", BEAM_2_AXIS, BEAM_2_SECTION),
            ]
        )

    provider = _MultiReplayProvider(body)
    final = _run_restoration(
        tmp_path, provider, damaged, "restore both beams atomically"
    )

    assert final.status == "succeeded", final.reason_code
    repaired = (
        tmp_path / "runs" / final.run_directory / final.artifacts["successful_ifc"]
    )
    repaired_model = ifcopenshell.open(str(repaired))
    original_model = ifcopenshell.open(str(VVO))
    for ifc_class in ("IfcBeam", "IfcColumn"):
        assert len(repaired_model.by_type(ifc_class)) == len(
            original_model.by_type(ifc_class)
        ), ifc_class
    tags = {beam.Tag for beam in repaired_model.by_type("IfcBeam")}
    assert {"restore-beam-1", "restore-beam-2"} <= tags
