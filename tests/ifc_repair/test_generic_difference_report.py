from pathlib import Path
import json
import subprocess
import sys

import ifcopenshell

from text2ifc_ifc_repair import compare as compare_module


OLD_BEAM_ID = "0AAAAAAAAAAAAAAAAAAAAA"
NEW_BEAM_ID = "1AAAAAAAAAAAAAAAAAAAAA"
TYPE_ID = "2AAAAAAAAAAAAAAAAAAAAA"
TYPE_REL_ID = "3AAAAAAAAAAAAAAAAAAAAA"
ROOT = Path(__file__).resolve().parents[2]


def _beam_model(*, beam_id: str, tag: str, value: str) -> ifcopenshell.file:
    model = ifcopenshell.file(schema="IFC2X3")
    beam = model.create_entity(
        "IfcBeam",
        GlobalId=beam_id,
        Name="Compared beam",
        Tag=tag,
    )
    beam_type = model.create_entity(
        "IfcBeamType",
        GlobalId=TYPE_ID,
        Name="Surviving beam type",
        PredefinedType="BEAM",
    )
    model.create_entity(
        "IfcRelDefinesByType",
        GlobalId=TYPE_REL_ID,
        RelatedObjects=[beam],
        RelatingType=beam_type,
    )
    prop = model.create_entity(
        "IfcPropertySingleValue",
        Name="Reference",
        NominalValue=model.create_entity("IfcIdentifier", value),
    )
    pset = model.create_entity(
        "IfcPropertySet",
        GlobalId=("4" if beam_id == OLD_BEAM_ID else "5") + "A" * 21,
        Name="Pset_BeamCommon",
        HasProperties=[prop],
    )
    model.create_entity(
        "IfcRelDefinesByProperties",
        GlobalId=("6" if beam_id == OLD_BEAM_ID else "7") + "A" * 21,
        RelatedObjects=[beam],
        RelatingPropertyDefinition=pset,
    )
    return model


def test_generic_difference_report_discovers_replacements_without_tag_rules(
    tmp_path: Path,
) -> None:
    before = tmp_path / "before.ifc"
    after = tmp_path / "after.ifc"
    _beam_model(
        beam_id=OLD_BEAM_ID,
        tag="original-tag",
        value="before",
    ).write(str(before))
    _beam_model(
        beam_id=NEW_BEAM_ID,
        tag="provider-chose-this-operation-id",
        value="after",
    ).write(str(after))
    build_report = getattr(
        compare_module,
        "build_ifc_difference_report",
        None,
    )
    assert callable(build_report)

    report = build_report(before, after)

    products = {
        (item["change_kind"], item["global_id"]): item
        for item in report["changed_products"]
    }
    removed = products[("removed", OLD_BEAM_ID)]["before"]
    created = products[("created", NEW_BEAM_ID)]["after"]
    assert removed["tag"] == "original-tag"
    assert created["tag"] == "provider-chose-this-operation-id"
    assert removed["type_global_ids"] == [TYPE_ID]
    assert created["type_global_ids"] == [TYPE_ID]
    assert removed["direct_properties"] == [
        {
            "property_set_global_id": "4" + "A" * 21,
            "set_name": "Pset_BeamCommon",
            "property_name": "Reference",
            "value_type": "IfcIdentifier",
            "value": "before",
        }
    ]
    assert created["direct_properties"][0]["value"] == "after"
    assert report["summary"]["changed_product_count"] == 2
    assert report["summary"]["changed_product_classes"] == {"IfcBeam": 2}


def test_generic_difference_report_cli_writes_json(tmp_path: Path) -> None:
    before = tmp_path / "before.ifc"
    after = tmp_path / "after.ifc"
    output = tmp_path / "difference.json"
    _beam_model(
        beam_id=OLD_BEAM_ID,
        tag="original-tag",
        value="before",
    ).write(str(before))
    _beam_model(
        beam_id=NEW_BEAM_ID,
        tag="any-provider-operation-id",
        value="after",
    ).write(str(after))

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "ifc_repair" / "compare_ifc_files.py"),
            str(before),
            str(after),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["summary"]["changed_product_classes"] == {"IfcBeam": 2}
