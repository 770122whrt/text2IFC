from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from text2ifc_compiler import compile_document
from text2ifc_ifc2text import (
    compare_ifc_buildings,
    extract_building_facts,
    render_design_description,
)
from text2ifc_ifc2text.roundtrip import prepare_roundtrip_baseline
from text2ifc_ifc2text.text2ifc_public import reconstruct_description_with_public_text2ifc


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def _document() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _compile(tmp_path: Path, name: str, document: dict) -> Path:
    output = tmp_path / name
    result = compile_document(document, output)
    assert result.success, (result.input_issues, result.ifc_issues)
    return output


def test_extracts_reconstructable_facts_and_description_without_source_guids(tmp_path: Path) -> None:
    source = _compile(tmp_path, "source.ifc", _document())
    facts = extract_building_facts(source)
    assert facts["source"]["ifc_schema"] == "IFC2X3"
    assert facts["capability"]["wall_count"] == 1
    assert facts["capability"]["door_count"] == 1
    assert facts["capability"]["window_count"] == 1
    assert facts["capability"]["explicit_space_count"] == 1
    wall = facts["storeys"][0]["walls"][0]
    assert wall["measurement_status"] == "measured"
    assert wall["length_mm"] == pytest.approx(5000.0, abs=1.0)

    description = render_design_description(facts)
    assert "墙体布置" in description
    assert "门窗与开口" in description
    assert "中心轴从" in description
    for storey in facts["storeys"]:
        for category in ("walls", "doors", "windows", "openings", "spaces"):
            for item in storey[category]:
                if item.get("source_global_id"):
                    assert item["source_global_id"] not in description


def test_no_space_inference_closes_normal_wall_corner_gaps_without_semantic_use() -> None:
    from text2ifc_ifc2text.facts import _infer_enclosed_regions

    storey = {
        "label": "S01",
        "walls": [
            {"axis_start_mm": [100, 0, 0], "axis_end_mm": [3900, 0, 0], "thickness_mm": 200},
            {"axis_start_mm": [4000, 100, 0], "axis_end_mm": [4000, 2900, 0], "thickness_mm": 200},
            {"axis_start_mm": [3900, 3000, 0], "axis_end_mm": [100, 3000, 0], "thickness_mm": 200},
            {"axis_start_mm": [0, 2900, 0], "axis_end_mm": [0, 100, 0], "thickness_mm": 200},
        ],
    }
    regions, issues = _infer_enclosed_regions(storey)
    assert issues == []
    assert len(regions) == 1
    assert regions[0]["semantic_use"] == "unknown"
    assert regions[0]["area_m2"] == pytest.approx(12.0, abs=0.2)


def test_roundtrip_prepare_writes_only_text_as_reconstruction_input(tmp_path: Path) -> None:
    source = _compile(tmp_path, "source.ifc", _document())
    bundle = tmp_path / "bundle"
    manifest = prepare_roundtrip_baseline(source, bundle)
    assert Path(manifest["reconstruction_input_path"]).read_text(encoding="utf-8").startswith("# 建筑设计说明")
    assert manifest["truth_boundary"]["reconstruction_receives"] == ["design-description.md"]
    assert (bundle / "source-facts.json").is_file()
    assert (bundle / "roundtrip.json").is_file()


def test_compare_ignores_guids_but_detects_missing_moved_and_resized_components(tmp_path: Path) -> None:
    source_doc = _document()
    source = _compile(tmp_path, "source.ifc", source_doc)
    independent = _compile(tmp_path, "independent.ifc", copy.deepcopy(source_doc))
    equal_report = compare_ifc_buildings(source, independent, allow_global_translation=False)
    assert equal_report["status"]["reconstruction_consistent"] is True
    assert equal_report["summary"] == {
        "missing_count": 0,
        "extra_count": 0,
        "deviation_count": 0,
        "relationship_difference_count": 0,
    }

    missing_doc = copy.deepcopy(source_doc)
    missing_doc["entities"] = [item for item in missing_doc["entities"] if item["id"] != "door-1"]
    missing_doc["relationships"] = [item for item in missing_doc["relationships"] if item["id"] != "fill-1"]
    missing = _compile(tmp_path, "missing-door.ifc", missing_doc)
    missing_report = compare_ifc_buildings(source, missing, allow_global_translation=False)
    assert {item["name"] for item in missing_report["components"]["doors"]["missing"]} == {"Door"}
    assert missing_report["status"]["reconstruction_consistent"] is False

    moved_doc = copy.deepcopy(source_doc)
    window = next(item for item in moved_doc["entities"] if item["id"] == "window-1")
    window["attributes"]["ObjectPlacement"]["origin"][0] += 400
    moved = _compile(tmp_path, "moved-window.ifc", moved_doc)
    moved_report = compare_ifc_buildings(source, moved, allow_global_translation=False)
    assert moved_report["components"]["windows"]["deviations"]

    resized_doc = copy.deepcopy(source_doc)
    window = next(item for item in resized_doc["entities"] if item["id"] == "window-1")
    window["attributes"]["OverallWidth"] = 1500
    window["attributes"]["Representation"]["profile"]["x"] = 1500
    resized = _compile(tmp_path, "resized-window.ifc", resized_doc)
    resized_report = compare_ifc_buildings(source, resized, allow_global_translation=False)
    assert resized_report["components"]["windows"]["deviations"]


def test_public_text2ifc_bridge_passes_description_only(monkeypatch) -> None:
    recorded: dict[str, object] = {}

    class Store:
        def create_session(self, *, original_input: str):
            recorded["original_input"] = original_input
            return SimpleNamespace(session_id="s1", session_hash="h1")

    def fake_brief(**kwargs):
        recorded["brief_kwargs"] = kwargs
        return SimpleNamespace(status="ready", session_id="s1", session_hash="h1")

    def fake_ready(**kwargs):
        recorded["ready_kwargs"] = kwargs
        return SimpleNamespace(
            status="success",
            session_id="s1",
            session_hash="h1",
            ifc_path=Path("out.ifc"),
            report_path=Path("report.json"),
            generator_status="accepted",
            audit_status="accepted",
        )

    import text2ifc_agent.interactive_cli_flow as flow

    monkeypatch.setattr(flow, "run_design_brief_clarification_loop", fake_brief)
    monkeypatch.setattr(flow, "run_ready_session_to_ifc", fake_ready)
    result = reconstruct_description_with_public_text2ifc(
        "only-design-description",
        store=Store(),
        invoke_design_brief=lambda *_: None,
        provider_factory=lambda: object(),
    )
    assert recorded["original_input"] == "only-design-description"
    assert "source_ifc" not in recorded["brief_kwargs"]
    assert "source_facts" not in recorded["brief_kwargs"]
    assert result["public_path"] == "run_ready_session_to_ifc"
