from __future__ import annotations

import json
import stat
import zipfile
from pathlib import Path

import ifcopenshell
import pytest

from text2ifc_knowledge.express_registry import build_declaration_registry


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def source_manifest_path(project_root: Path) -> Path:
    return project_root / "schemas" / "ifc" / "IFC2X3_TC1.sources.json"


@pytest.fixture(scope="session")
def declaration_registry(project_root: Path):
    schema = ifcopenshell.schema_by_name("IFC2X3")
    return build_declaration_registry(
        project_root / "schemas" / "ifc" / "IFC2X3_TC1.exp",
        schema=schema,
    )


@pytest.fixture
def psd_zip_factory(tmp_path: Path):
    def create(entries: dict[str, str], *, symlink: str | None = None) -> Path:
        path = tmp_path / "psd.zip"
        with zipfile.ZipFile(path, "w") as archive:
            for name, content in entries.items():
                archive.writestr(name, content)
            if symlink:
                info = zipfile.ZipInfo(symlink)
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(info, "target")
        return path

    return create


def property_set_xml(name: str, applicable: str, properties: list[tuple[str, str]]) -> str:
    property_defs = "".join(
        (
            "<PropertyDef>"
            f"<Name>{property_name}</Name>"
            "<PropertyType><TypePropertySingleValue>"
            f'<DataType type="{data_type}"/>'
            "</TypePropertySingleValue></PropertyType>"
            "</PropertyDef>"
        )
        for property_name, data_type in properties
    )
    return (
        '<?xml version="1.0"?>'
        "<PropertySetDef>"
        f"<Name>{name}</Name>"
        "<ApplicableClasses>"
        f"<ClassName>{applicable}</ClassName>"
        "</ApplicableClasses>"
        f"<PropertyDefs>{property_defs}</PropertyDefs>"
        "</PropertySetDef>"
    )


@pytest.fixture
def representative_psd_zip(psd_zip_factory):
    return psd_zip_factory(
        {
            "R2x3_TC1/psd/IfcSharedBldgElements/Pset_WallCommon.xml": property_set_xml(
                "Pset_WallCommon",
                "IfcWall",
                [("IsExternal", "IfcBoolean"), ("LoadBearing", "IfcBoolean")],
            ),
            "R2x3_TC1/psd/IfcProductExtension/Pset_SpaceCommon.xml": property_set_xml(
                "Pset_SpaceCommon",
                "IfcSpace",
                [("Reference", "IfcIdentifier")],
            ),
            "R2x3_TC1/psd/IfcSharedBldgElements/Pset_OpeningElementCommon.xml": property_set_xml(
                "Pset_OpeningElementCommon",
                "IfcOpeningElement",
                [("FireExit", "IfcBoolean")],
            ),
        }
    )
