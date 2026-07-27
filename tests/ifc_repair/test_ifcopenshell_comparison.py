from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

import ifcopenshell

from text2ifc_ifc_repair.compare import (
    compare_ifc_with_ifcdiff,
    compare_mapped_elements,
)


def _write_window(
    path: Path,
    *,
    global_id: str,
    name: str,
    fire_rating: str,
) -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    owner = model.create_entity(
        "IfcOwnerHistory",
        OwningUser=model.create_entity(
            "IfcPersonAndOrganization",
            ThePerson=model.create_entity("IfcPerson"),
            TheOrganization=model.create_entity("IfcOrganization"),
        ),
        OwningApplication=model.create_entity(
            "IfcApplication",
            ApplicationDeveloper=model.create_entity("IfcOrganization"),
            Version="1",
            ApplicationFullName="fixture",
            ApplicationIdentifier="fixture",
        ),
        ChangeAction="ADDED",
        CreationDate=0,
    )
    window = model.create_entity(
        "IfcWindow",
        GlobalId=global_id,
        OwnerHistory=owner,
        Name=name,
        ObjectType="M_Fixed:0915 x 1830mm",
        OverallHeight=1830.0,
        OverallWidth=915.0,
    )
    prop = model.create_entity(
        "IfcPropertySingleValue",
        Name="FireRating",
        NominalValue=model.create_entity("IfcLabel", fire_rating),
    )
    pset = model.create_entity(
        "IfcPropertySet",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner,
        Name="Pset_WindowCommon",
        HasProperties=[prop],
    )
    model.create_entity(
        "IfcRelDefinesByProperties",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner,
        RelatedObjects=[window],
        RelatingPropertyDefinition=pset,
    )
    model.write(str(path))


def test_official_ifcdiff_reports_same_guid_property_change(tmp_path: Path) -> None:
    before = tmp_path / "before.ifc"
    after = tmp_path / "after.ifc"
    guid = "0AAAAAAAAAAAAAAAAAAAAA"
    _write_window(before, global_id=guid, name="W-01", fire_rating="EI30")
    _write_window(after, global_id=guid, name="W-01", fire_rating="EI60")

    report = compare_ifc_with_ifcdiff(
        before,
        after,
        relationships=("attributes", "property", "type", "container", "classification"),
    )

    assert report["engine"] == "IfcOpenShell.IfcDiff/0.8.5"
    assert report["added_ids"] == []
    assert report["deleted_ids"] == []
    assert guid in report["changed"]
    assert report["changed"][guid]["properties_changed"] is not None


def test_mapped_element_comparison_handles_replacement_guid(tmp_path: Path) -> None:
    before = tmp_path / "before.ifc"
    after = tmp_path / "after.ifc"
    _write_window(
        before,
        global_id="0AAAAAAAAAAAAAAAAAAAAA",
        name="Original",
        fire_rating="EI30",
    )
    _write_window(
        after,
        global_id="0BBBBBBBBBBBBBBBBBBBBB",
        name="Replacement",
        fire_rating="EI30",
    )

    report = compare_mapped_elements(
        before,
        after,
        mappings=(
            {
                "role": "window",
                "before_global_id": "0AAAAAAAAAAAAAAAAAAAAA",
                "after_global_id": "0BBBBBBBBBBBBBBBBBBBBB",
            },
        ),
    )

    window = report["elements"][0]
    assert window["identity_changed"] is True
    assert window["direct_properties"]["complete_match"] is True
    assert window["effective_properties"]["complete_match"] is True
    assert window["attributes"]["changed"]["Name"] == {
        "before": "Original",
        "after": "Replacement",
    }


def test_comparison_cli_writes_human_occurrence_report_and_ownership_is_nonblocking(
    tmp_path: Path,
) -> None:
    before = tmp_path / "before.ifc"
    after = tmp_path / "after.ifc"
    original_guid = "0AAAAAAAAAAAAAAAAAAAAA"
    repaired_guid = "0BBBBBBBBBBBBBBBBBBBBB"
    _write_window(
        before,
        global_id=original_guid,
        name="W-01",
        fire_rating="EI30",
    )
    _write_window(
        after,
        global_id=repaired_guid,
        name="W-01",
        fire_rating="EI30",
    )
    mapping = tmp_path / "mapping.json"
    mapping.write_text(
        json.dumps(
            {
                "windows": [
                    {
                        "deleted_window_name": "W-01",
                        "original_window_global_id": original_guid,
                        "repaired_window_global_id": repaired_guid,
                        "authorization_ledger": [
                            "window_occurrence:pset:Pset_WindowCommon.FireRating"
                        ],
                        "required_fact_keys": [
                            "window_occurrence:pset:Pset_WindowCommon.FireRating"
                        ],
                        "complete_replication": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    report = tmp_path / "comparison.json"
    occurrence = tmp_path / "occurrence.json"
    markdown = tmp_path / "comparison.md"
    script = (
        Path(__file__).resolve().parents[2]
        / "scripts/ifc_repair/compare_ifc.py"
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            str(before),
            str(after),
            "--window-mapping",
            str(mapping),
            "--output",
            str(report),
            "--occurrence-json-output",
            str(occurrence),
            "--markdown-output",
            str(markdown),
            "--blocking",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert completed.returncode == 0, completed.stderr
    occurrence_payload = json.loads(occurrence.read_text(encoding="utf-8"))
    detail = occurrence_payload["windows"][0]["report"]
    assert detail["counts"]["ownership_only"] >= 1
    rendered = markdown.read_text(encoding="utf-8")
    assert "W-01" in rendered
    assert original_guid in rendered and repaired_guid in rendered
    for status in (
        "geometry_relationship_success",
        "semantic_fidelity_success",
        "occurrence_fidelity_success",
        "authoring_exactness",
    ):
        assert status in rendered


def test_comparison_cli_blocking_mode_exits_nonzero_for_wrong_required_value(
    tmp_path: Path,
) -> None:
    before = tmp_path / "before.ifc"
    after = tmp_path / "after.ifc"
    original_guid = "0AAAAAAAAAAAAAAAAAAAAA"
    repaired_guid = "0BBBBBBBBBBBBBBBBBBBBB"
    _write_window(
        before,
        global_id=original_guid,
        name="W-01",
        fire_rating="EI30",
    )
    _write_window(
        after,
        global_id=repaired_guid,
        name="W-01",
        fire_rating="EI60",
    )
    key = "window_occurrence:pset:Pset_WindowCommon.FireRating"
    mapping = tmp_path / "mapping.json"
    mapping.write_text(
        json.dumps(
            [
                {
                    "original_window_global_id": original_guid,
                    "repaired_window_global_id": repaired_guid,
                    "authorization_ledger": [key],
                    "required_fact_keys": [key],
                    "complete_replication": False,
                }
            ]
        ),
        encoding="utf-8",
    )
    script = (
        Path(__file__).resolve().parents[2]
        / "scripts/ifc_repair/compare_ifc.py"
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            str(before),
            str(after),
            "--window-mapping",
            str(mapping),
            "--blocking",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert completed.returncode == 2
