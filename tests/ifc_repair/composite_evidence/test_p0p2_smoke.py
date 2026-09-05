"""P0/P2 smoke: storey-12 fix + exact_property restoration on C1 (sixty5)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import ifcopenshell
import pytest

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
for p in (str(ROOT), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

import importlib.util

spec = importlib.util.spec_from_file_location(
    "dmg", ROOT / "tests/ifc_repair/composite_evidence/test_damage_restoration_c1_c5.py"
)
dmg = importlib.util.module_from_spec(spec)
sys.modules["dmg"] = dmg
spec.loader.exec_module(dmg)


def test_c1_storey12_and_exact_property_restoration(tmp_path: Path) -> None:
    case = dmg.FREEZE["cases"][0]
    for b in case["damage"]["beams"]:
        b["storey"] = "12 twaalfde verdieping"

    original_beam_op = dmg._beam_op

    def beam_op_with_props(operation_id: str, member: dict) -> dict:
        op = original_beam_op(operation_id, member)
        op["property_intents"] = [
            {
                "intent_kind": "exact_property",
                "set_name": "Pset_BeamCommon",
                "property_name": "LoadBearing",
                "raw_value": True,
                "raw_unit": None,
                "requested_value_type": "IfcBoolean",
                "scope": "occurrence_direct",
                "source": dmg.SOURCE,
            },
            {
                "intent_kind": "exact_property",
                "set_name": "Pset_BeamCommon",
                "property_name": "FireRating",
                "raw_value": "120",
                "raw_unit": None,
                "requested_value_type": "IfcLabel",
                "scope": "occurrence_direct",
                "source": dmg.SOURCE,
            },
        ]
        return op

    dmg._beam_op = beam_op_with_props
    try:
        scratch = tmp_path / "scratch"
        scratch.mkdir()
        damaged = dmg._apply_damage(case, scratch)
        provider = dmg._ReplayProvider(case)
        api = dmg.RepairAPI(
            tmp_path / "runs",
            provider=provider,
            orchestrator_factory=dmg._orchestrator_factory,
            intent_schema_version="text2ifc/ifc-repair-intent/0.8",
        )
        final = api.start(str(damaged), str(case["request"]))
        assert final.status == "succeeded", final.reason_code
        runs_root = tmp_path / "runs"
        run_root = (
            runs_root / "runs" / str(final.run_id)
            if (runs_root / "runs" / str(final.run_id)).is_dir()
            else runs_root / str(final.run_id)
        )
        repaired = run_root / final.artifacts["successful_ifc"]
        model = ifcopenshell.open(str(repaired))

        restored = [
            e
            for e in model.by_type("IfcBeam")
            if "Text2IFC" in str(e.Name)
        ]
        assert len(restored) == 2
        for e in restored:
            props = {}
            for rel in model.by_type("IfcRelDefinesByProperties"):
                if e in rel.RelatedObjects:
                    pd = rel.RelatingPropertyDefinition
                    if pd.is_a("IfcPropertySet"):
                        for p in pd.HasProperties:
                            if p.NominalValue is not None:
                                props[f"{pd.Name}.{p.Name}"] = (
                                    p.NominalValue.wrappedValue
                                )
            assert props.get("Pset_BeamCommon.LoadBearing") is True, props
            assert props.get("Pset_BeamCommon.FireRating") == "120", props

        # storey identity: restored beams must sit on storey 12 (world z ~39m).
        for e in restored:
            storey = None
            for rel in model.by_type("IfcRelContainedInSpatialStructure"):
                if e in rel.RelatedElements and rel.RelatingStructure.is_a(
                    "IfcBuildingStorey"
                ):
                    storey = rel.RelatingStructure
                    break
            assert storey is not None
            assert storey.Name == "12 twaalfde verdieping", storey.Name
            assert abs(float(storey.Elevation) - 39700.0) < 1.0
    finally:
        dmg._beam_op = original_beam_op
