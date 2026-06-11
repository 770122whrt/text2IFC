from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from text2ifc_knowledge.registry import RegistryDriftError, check_registry_files


def test_express_file_generation_isolated_from_late_bound_schema_cleanup(
    tmp_path: Path,
) -> None:
    express = tmp_path / "TEST.exp"
    express.write_text(
        "SCHEMA TEST;\n"
        "TYPE TestLabel = STRING;\n"
        "END_TYPE;\n"
        "ENTITY TestRoot;\n"
        "  Name : OPTIONAL TestLabel;\n"
        "END_ENTITY;\n"
        "END_SCHEMA;\n",
        encoding="ascii",
    )
    code = (
        "from text2ifc_knowledge.express_registry import "
        "build_declaration_registry; "
        f"result=build_declaration_registry({str(express)!r}); "
        "print(result['schema'], result['counts']['declarations'])"
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        str(path) for path in sys.path if path
    )

    completed = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "TEST 2"


def test_ifc2x3_registry_has_complete_declaration_counts(declaration_registry) -> None:
    assert declaration_registry["schema"] == "IFC2X3"
    assert declaration_registry["counts"] == {
        "declarations": 980,
        "entities": 653,
    }


@pytest.mark.parametrize(
    ("name", "supertype", "required_attributes"),
    [
        ("IfcWall", "IfcBuildingElement", {"GlobalId", "ObjectPlacement", "Tag"}),
        (
            "IfcSpace",
            "IfcSpatialStructureElement",
            {"GlobalId", "ObjectPlacement", "InteriorOrExteriorSpace"},
        ),
        (
            "IfcOpeningElement",
            "IfcFeatureElementSubtraction",
            {"GlobalId", "ObjectPlacement", "Tag"},
        ),
        (
            "IfcRelVoidsElement",
            "IfcRelConnects",
            {"RelatingBuildingElement", "RelatedOpeningElement"},
        ),
        (
            "IfcRelFillsElement",
            "IfcRelConnects",
            {"RelatingOpeningElement", "RelatedBuildingElement"},
        ),
    ],
)
def test_representative_entities_preserve_inheritance_and_attributes(
    declaration_registry,
    name: str,
    supertype: str,
    required_attributes: set[str],
) -> None:
    record = declaration_registry["declarations"][name]

    assert record["kind"] == "entity"
    assert record["supertype"] == supertype
    assert required_attributes <= {attribute["name"] for attribute in record["attributes"]}


def test_selects_and_enumerations_preserve_exact_items(declaration_registry) -> None:
    value_select = declaration_registry["declarations"]["IfcValue"]
    wall_enum = declaration_registry["declarations"]["IfcWallTypeEnum"]

    assert value_select["kind"] == "select"
    assert value_select["items"] == [
        "IfcDerivedMeasureValue",
        "IfcMeasureValue",
        "IfcSimpleValue",
    ]
    assert wall_enum["kind"] == "enumeration"
    assert {"STANDARD", "POLYGONAL", "SHEAR", "USERDEFINED", "NOTDEFINED"} <= set(
        wall_enum["items"]
    )


def test_changed_generated_registry_fails_drift_check(
    project_root: Path, tmp_path: Path
) -> None:
    generated = project_root / "schemas" / "ifc" / "generated" / "IFC2X3"
    copied = tmp_path / "project"
    target = copied / "schemas" / "ifc" / "generated" / "IFC2X3"
    target.mkdir(parents=True)
    for path in generated.glob("*.json"):
        (target / path.name).write_bytes(path.read_bytes())
    declarations = target / "declarations.json"
    assert declarations.exists(), "generated declarations registry does not exist yet"
    payload = json.loads(declarations.read_text(encoding="utf-8"))
    payload["schema"] = "TAMPERED"
    declarations.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RegistryDriftError):
        check_registry_files(copied)
