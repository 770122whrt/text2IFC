import hashlib
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .schema import load_schema
from .validation import validate_document


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_ROOT = ROOT / "dataset" / "processed"
DEFAULT_OUTPUT_ROOT = DEFAULT_SOURCE_ROOT / "bim-json-1.0"

SOURCE_FAMILIES = (
    ("walls", "wall"),
    ("columns", "column"),
    ("beams", "beam"),
    ("slabs", "slab"),
    ("doors", "door"),
    ("windows", "window"),
    ("stairs", "stair"),
    ("stair_flights", "stair_flight"),
    ("roofs", "roof"),
)


def _diagnostic(
    code: str,
    path: str,
    message: str,
    severity: str = "error",
) -> dict[str, str]:
    return {
        "code": code,
        "path": path,
        "message": message,
        "severity": severity,
    }


def _sort_diagnostics(
    diagnostics: Iterable[dict[str, str]],
) -> list[dict[str, str]]:
    return sorted(
        diagnostics,
        key=lambda item: (
            item["path"],
            item["code"],
            item["message"],
            item["severity"],
        ),
    )


def _schema_kind_rules() -> dict[str, tuple[tuple[str, ...], tuple[str, ...]]]:
    schema = load_schema()
    element = schema["$defs"]["element"]
    rules: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
    for conditional in element["allOf"]:
        condition = conditional["if"]["properties"]["kind"]
        kinds = [condition["const"]] if "const" in condition else condition["enum"]
        then_properties = conditional["then"]["properties"]
        dimensions = tuple(then_properties["dimensions"]["required"])
        properties = tuple(
            then_properties["properties"]["propertyNames"]["enum"]
        )
        for kind in kinds:
            rules[kind] = (dimensions, properties)
    return rules


def _source_id(
    value: Any,
    generated: str,
    path: str,
    source_ref: str,
    diagnostics: list[dict[str, str]],
) -> str | None:
    if value is None or value == "":
        diagnostics.append(
            _diagnostic(
                "ID_GENERATED",
                path,
                f"Generated {generated!r} because {source_ref} has no ID.",
                "note",
            )
        )
        return generated
    if isinstance(value, str) and value:
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        normalized = str(value)
        diagnostics.append(
            _diagnostic(
                "ID_NORMALIZED",
                path,
                f"Normalized integer ID {value!r} to string {normalized!r}.",
                "note",
            )
        )
        return normalized
    diagnostics.append(
        _diagnostic(
            "INVALID_SOURCE_ID",
            path,
            "Source ID must be a non-empty string or integer.",
        )
    )
    return None


def _singleton(
    source: dict[str, Any],
    field: str,
    diagnostics: list[dict[str, str]],
) -> dict[str, Any] | None:
    value = source.get(field)
    if isinstance(value, dict):
        return value
    if isinstance(value, list) and len(value) == 1:
        if isinstance(value[0], dict):
            return value[0]
        if isinstance(value[0], str):
            return {"name": value[0]}
    diagnostics.append(
        _diagnostic(
            "INVALID_HIERARCHY_SHAPE",
            f"/{field}",
            f"{field} must be an object or a singleton object array.",
        )
    )
    return None


def _named_object(
    source: dict[str, Any] | None,
    kind: str,
    source_ref: str,
    diagnostics: list[dict[str, str]],
) -> dict[str, str] | None:
    if source is None:
        return None
    name = source.get("name")
    if not isinstance(name, str) or not name:
        diagnostics.append(
            _diagnostic(
                "MISSING_REQUIRED_NAME",
                f"/{kind}/name",
                f"{kind} requires an explicit non-empty source name.",
            )
        )
        return None
    object_id = _source_id(
        source.get("id"),
        f"{kind}-0001",
        f"/{kind}/id",
        source_ref,
        diagnostics,
    )
    if object_id is None:
        return None
    return {"id": object_id, "name": name}


def _value(mapping: Any, *names: str) -> Any:
    if not isinstance(mapping, dict):
        return None
    for name in names:
        if name in mapping and mapping[name] is not None:
            return mapping[name]
    return None


def _dimension_value(element: dict[str, Any], kind: str, dimension: str) -> Any:
    aliases = {
        "width": ("width", "w"),
        "height": ("height", "h"),
    }
    direct_names = aliases.get(dimension, (dimension,))
    direct = _value(element, *direct_names)
    if direct is not None:
        return direct

    dimensions = element.get("dimensions")
    nested = _value(dimensions, *direct_names)
    if nested is not None:
        return nested

    legacy_dimensions = element.get("dims")
    if isinstance(legacy_dimensions, dict):
        legacy_maps = {
            "column": {
                "width": ("width", "w"),
                "depth": ("depth_width", "h"),
                "height": ("height", "depth"),
            },
            "beam": {
                "length": ("length", "depth"),
                "width": ("width", "w"),
                "height": ("height", "h"),
            },
        }
        names = legacy_maps.get(kind, {}).get(dimension)
        if names:
            value = _value(legacy_dimensions, *names)
            if value is not None:
                return value

    profile = element.get("profile")
    if not isinstance(profile, dict) or profile.get("type") != "rectangle":
        return None
    profile_maps = {
        "wall": {
            "length": ("x_dim",),
            "thickness": ("y_dim",),
            "height": ("depth",),
        },
        "column": {
            "width": ("x_dim",),
            "depth": ("y_dim",),
            "height": ("depth",),
        },
        "beam": {
            "length": ("depth",),
            "width": ("x_dim",),
            "height": ("y_dim",),
        },
        "slab": {
            "length": ("x_dim",),
            "width": ("y_dim",),
            "thickness": ("depth",),
        },
        "roof": {
            "length": ("x_dim",),
            "width": ("y_dim",),
            "thickness": ("depth",),
        },
    }
    names = profile_maps.get(kind, {}).get(dimension)
    return _value(profile, *names) if names else None


def _property_value(element: dict[str, Any], name: str) -> Any:
    aliases = {
        "predefined_type": ("predefined_type", "pretype"),
    }
    names = aliases.get(name, (name,))
    value = _value(element, *names)
    if value is not None:
        return value
    return _value(element.get("properties"), *names)


def _omissions(source: dict[str, Any]) -> list[str]:
    omissions: set[str] = set()
    if source.get("materials"):
        omissions.add("materials")
    if source.get("material_assignments"):
        omissions.add("material_assignments")
    if source.get("mep"):
        omissions.add("mep")
    if isinstance(source.get("opening_count"), (int, float)) and source[
        "opening_count"
    ]:
        omissions.add("openings")

    site_values = source.get("site")
    if isinstance(site_values, list):
        site_values = site_values[0] if site_values else None
    if isinstance(site_values, dict) and any(
        site_values.get(field) is not None
        for field in ("lat", "lon", "latitude", "longitude")
    ):
        omissions.add("site_geolocation")

    building_values = source.get("building")
    if isinstance(building_values, list):
        building_values = building_values[0] if building_values else None
    if isinstance(building_values, dict) and building_values.get("num_storeys") is not None:
        omissions.add("building_metadata")

    for storey in source.get("storeys") or []:
        if isinstance(storey, dict) and storey.get("above_ground") is not None:
            omissions.add("storey_metadata")

    for family, _ in SOURCE_FAMILIES:
        for element in source.get(family) or []:
            if not isinstance(element, dict):
                continue
            if element.get("material"):
                omissions.add("materials")
            if element.get("profile"):
                omissions.add("geometry_profiles")
    return sorted(omissions)


def _count_source_elements(source: dict[str, Any]) -> int:
    total = 0
    for family, _ in SOURCE_FAMILIES:
        value = source.get(family)
        if isinstance(value, list):
            total += len(value)
    return total


def migrate_model(source: Any, source_ref: str) -> dict[str, Any]:
    if not isinstance(source, dict):
        return {
            "source_ref": source_ref,
            "disposition": "rejected",
            "diagnostics": [
                _diagnostic(
                    "UNKNOWN_SOURCE_SHAPE",
                    "/",
                    "Legacy model must be a JSON object.",
                )
            ],
            "omissions": [],
            "source_element_count": 0,
            "converted_element_count": 0,
            "document": None,
        }

    diagnostics: list[dict[str, str]] = []
    source_element_count = _count_source_elements(source)
    schema_name = source.get("schema")
    if schema_name != "IFC2X3":
        diagnostics.append(
            _diagnostic(
                "UNSUPPORTED_TARGET_SCHEMA",
                "/schema",
                "Legacy model must explicitly declare IFC2X3.",
            )
        )

    project = _named_object(
        _singleton(source, "project", diagnostics),
        "project",
        source_ref,
        diagnostics,
    )
    site = _named_object(
        _singleton(source, "site", diagnostics),
        "site",
        source_ref,
        diagnostics,
    )
    building = _named_object(
        _singleton(source, "building", diagnostics),
        "building",
        source_ref,
        diagnostics,
    )

    storey_values = source.get("storeys")
    if not isinstance(storey_values, list) or not storey_values:
        diagnostics.append(
            _diagnostic(
                "INVALID_STOREY_SHAPE",
                "/storeys",
                "storeys must be a non-empty array.",
            )
        )
        storey_values = []

    storeys: list[dict[str, Any]] = []
    storey_name_counts: Counter[str] = Counter()
    for index, storey_source in enumerate(storey_values):
        path = f"/storeys/{index}"
        if not isinstance(storey_source, dict):
            diagnostics.append(
                _diagnostic(
                    "UNKNOWN_SOURCE_SHAPE",
                    path,
                    "Storey entry must be an object.",
                )
            )
            continue
        name = storey_source.get("name")
        if not isinstance(name, str) or not name:
            diagnostics.append(
                _diagnostic(
                    "MISSING_REQUIRED_NAME",
                    f"{path}/name",
                    "Storey requires an explicit non-empty source name.",
                )
            )
            continue
        storey_name_counts[name] += 1
        elevation = _value(storey_source, "elevation", "elev")
        if not isinstance(elevation, (int, float)) or isinstance(elevation, bool):
            diagnostics.append(
                _diagnostic(
                    "MISSING_STOREY_ELEVATION",
                    f"{path}/elevation",
                    "Storey requires an explicit numeric elevation/elev value.",
                )
            )
            continue
        storey_id = _source_id(
            storey_source.get("id"),
            f"storey-{index + 1:04d}",
            f"{path}/id",
            source_ref,
            diagnostics,
        )
        if storey_id is None:
            continue
        storeys.append(
            {"id": storey_id, "name": name, "elevation": elevation}
        )

    for name, count in sorted(storey_name_counts.items()):
        if count > 1:
            diagnostics.append(
                _diagnostic(
                    "NON_UNIQUE_STOREY_NAME",
                    "/storeys",
                    f"Storey name {name!r} occurs {count} times.",
                )
            )

    storey_ids_by_name = {
        storey["name"]: storey["id"]
        for storey in storeys
        if storey_name_counts[storey["name"]] == 1
    }
    declared_storey_ids = {storey["id"] for storey in storeys}
    rules = _schema_kind_rules()
    elements: list[dict[str, Any]] = []

    for family, kind in SOURCE_FAMILIES:
        family_values = source.get(family, [])
        if family_values is None:
            family_values = []
        if not isinstance(family_values, list):
            diagnostics.append(
                _diagnostic(
                    "UNKNOWN_SOURCE_SHAPE",
                    f"/{family}",
                    f"{family} must be an array.",
                )
            )
            continue

        required_dimensions, allowed_properties = rules[kind]
        for index, element_source in enumerate(family_values):
            path = f"/{family}/{index}"
            if not isinstance(element_source, dict):
                diagnostics.append(
                    _diagnostic(
                        "UNKNOWN_SOURCE_SHAPE",
                        path,
                        f"{family} entry must be an object.",
                    )
                )
                continue

            name = element_source.get("name")
            if not isinstance(name, str) or not name:
                diagnostics.append(
                    _diagnostic(
                        "MISSING_REQUIRED_NAME",
                        f"{path}/name",
                        f"{kind} requires an explicit non-empty source name.",
                    )
                )
                continue

            element_id = _source_id(
                element_source.get("id"),
                f"{kind}-{index + 1:04d}",
                f"{path}/id",
                source_ref,
                diagnostics,
            )
            storey_id = None
            explicit_storey_id = element_source.get("storey_id")
            if isinstance(explicit_storey_id, (str, int)) and not isinstance(
                explicit_storey_id, bool
            ):
                candidate = str(explicit_storey_id)
                if candidate in declared_storey_ids:
                    storey_id = candidate
                else:
                    diagnostics.append(
                        _diagnostic(
                            "UNRESOLVED_STOREY_REFERENCE",
                            f"{path}/storey_id",
                            f"Storey ID {candidate!r} is not declared.",
                        )
                    )
            else:
                storey_name = _value(element_source, "storey", "storey_name")
                if not isinstance(storey_name, str) or not storey_name:
                    diagnostics.append(
                        _diagnostic(
                            "MISSING_STOREY_REFERENCE",
                            f"{path}/storey",
                            f"{kind} requires an explicit storey reference.",
                        )
                    )
                elif storey_name not in storey_ids_by_name:
                    diagnostics.append(
                        _diagnostic(
                            "UNRESOLVED_STOREY_REFERENCE",
                            f"{path}/storey",
                            f"Storey name {storey_name!r} does not resolve uniquely.",
                        )
                    )
                else:
                    storey_id = storey_ids_by_name[storey_name]

            dimensions: dict[str, Any] = {}
            for dimension in required_dimensions:
                value = _dimension_value(element_source, kind, dimension)
                if value is None:
                    diagnostics.append(
                        _diagnostic(
                            "MISSING_REQUIRED_DIMENSION",
                            f"{path}/{dimension}",
                            f"{kind} requires explicit {dimension}.",
                        )
                    )
                elif (
                    not isinstance(value, (int, float))
                    or isinstance(value, bool)
                    or value <= 0
                ):
                    diagnostics.append(
                        _diagnostic(
                            "INVALID_DIMENSION",
                            f"{path}/{dimension}",
                            f"{kind} {dimension} must be a positive number.",
                        )
                    )
                else:
                    dimensions[dimension] = value

            properties: dict[str, Any] = {}
            for property_name in allowed_properties:
                value = _property_value(element_source, property_name)
                if value is not None:
                    properties[property_name] = value

            if (
                element_id is not None
                and storey_id is not None
                and len(dimensions) == len(required_dimensions)
            ):
                element = {
                    "id": element_id,
                    "kind": kind,
                    "name": name,
                    "storey_id": storey_id,
                    "dimensions": dimensions,
                }
                if properties:
                    element["properties"] = properties
                elements.append(element)

    diagnostics.append(
        _diagnostic(
            "UNIT_ASSIGNED_FROM_SOURCE_PIPELINE",
            "/units/length",
            "Assigned MILLIMETRE from the legacy IFC extraction pipeline contract.",
            "note",
        )
    )
    document = {
        "contract_version": "bim-json/1.0",
        "target_schema": "IFC2X3",
        "units": {"length": "MILLIMETRE"},
        "project": project,
        "site": site,
        "building": building,
        "storeys": storeys,
        "elements": elements,
    }

    errors = [
        diagnostic
        for diagnostic in diagnostics
        if diagnostic["severity"] == "error"
    ]
    if not errors:
        for issue in validate_document(document):
            diagnostics.append(
                _diagnostic(
                    "MIGRATED_DOCUMENT_INVALID",
                    issue.path,
                    f"{issue.code}: {issue.message}",
                )
            )
        errors = [
            diagnostic
            for diagnostic in diagnostics
            if diagnostic["severity"] == "error"
        ]

    if errors:
        disposition = "rejected"
        converted_document = None
        converted_count = 0
    else:
        disposition = "converted"
        converted_document = document
        converted_count = len(elements)

    return {
        "source_ref": source_ref,
        "disposition": disposition,
        "diagnostics": _sort_diagnostics(diagnostics),
        "omissions": _omissions(source),
        "source_element_count": source_element_count,
        "converted_element_count": converted_count,
        "document": converted_document,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_bytes(value: Any) -> bytes:
    text = json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return (text + "\n").encode("utf-8")


def _write_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(_json_bytes(value))
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _assert_beneath(root: Path, target: Path) -> None:
    resolved_root = root.resolve()
    resolved_target = target.resolve()
    if resolved_target != resolved_root and resolved_root not in resolved_target.parents:
        raise ValueError(f"Migration path escapes output root: {target}")


def _discover(source_root: Path) -> tuple[list[dict[str, Any]], dict[Path, str]]:
    basic_path = source_root / "ifc_parsed_data.json"
    enhanced_path = source_root / "ifc_parsed_enhanced.json"
    roundtrip_paths = sorted((source_root / "roundtrip_json").glob("*.json"))
    source_paths = [basic_path, enhanced_path, *roundtrip_paths]
    source_hashes = {path: _sha256(path) for path in source_paths}
    discovered: list[dict[str, Any]] = []

    for category, path in (("basic", basic_path), ("enhanced", enhanced_path)):
        models = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(models, list):
            raise ValueError(f"{path} must contain a top-level array.")
        relative_path = path.relative_to(source_root).as_posix()
        for index, model in enumerate(models):
            discovered.append(
                {
                    "record_id": f"{category}-{index + 1:04d}",
                    "category": category,
                    "source_path": relative_path,
                    "source_selector": f"$[{index}]",
                    "source_sha256": source_hashes[path],
                    "model": model,
                }
            )

    for index, path in enumerate(roundtrip_paths):
        discovered.append(
            {
                "record_id": f"roundtrip-{index + 1:04d}",
                "category": "roundtrip",
                "source_path": path.relative_to(source_root).as_posix(),
                "source_selector": "$",
                "source_sha256": source_hashes[path],
                "model": json.loads(path.read_text(encoding="utf-8")),
            }
        )
    return discovered, source_hashes


def audit_existing_models(
    source_root: Path = DEFAULT_SOURCE_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    source_root = Path(source_root)
    output_root = Path(output_root)
    migrated_root = output_root / "migrated"
    audit_path = output_root / "migration-audit.json"
    _assert_beneath(output_root, migrated_root)
    _assert_beneath(output_root, audit_path)

    discovered, before_hashes = _discover(source_root)
    records: list[dict[str, Any]] = []
    converted_documents: dict[str, dict[str, Any]] = {}

    for item in discovered:
        source_ref = f"{item['source_path']}#{item['source_selector']}"
        result = migrate_model(item["model"], source_ref)
        output_path = None
        if result["disposition"] == "converted":
            output_path = f"migrated/{item['record_id']}.json"
            converted_documents[output_path] = result["document"]
        records.append(
            {
                "record_id": item["record_id"],
                "source_path": item["source_path"],
                "source_selector": item["source_selector"],
                "source_sha256": item["source_sha256"],
                "disposition": result["disposition"],
                "output_path": output_path,
                "diagnostics": result["diagnostics"],
                "omissions": result["omissions"],
                "source_element_count": result["source_element_count"],
                "converted_element_count": result["converted_element_count"],
            }
        )

    migrated_root.mkdir(parents=True, exist_ok=True)
    expected_paths = {
        (output_root / relative_path).resolve()
        for relative_path in converted_documents
    }
    for stale_path in migrated_root.glob("*.json"):
        _assert_beneath(output_root, stale_path)
        if stale_path.resolve() not in expected_paths:
            stale_path.unlink()
    for relative_path, document in converted_documents.items():
        output_path = output_root / relative_path
        _assert_beneath(output_root, output_path)
        _write_atomic(output_path, document)

    counts = Counter(record["disposition"] for record in records)
    categories = Counter(item["category"] for item in discovered)
    report = {
        "contract_version": "bim-json/1.0",
        "summary": {
            "total": len(records),
            "converted": counts["converted"],
            "rejected": counts["rejected"],
            "basic": categories["basic"],
            "enhanced": categories["enhanced"],
            "roundtrip": categories["roundtrip"],
        },
        "sources": [
            {
                "path": path.relative_to(source_root).as_posix(),
                "sha256": source_hash,
            }
            for path, source_hash in sorted(
                before_hashes.items(), key=lambda item: item[0].as_posix()
            )
        ],
        "records": records,
    }
    _write_atomic(audit_path, report)

    after_hashes = {path: _sha256(path) for path in before_hashes}
    if after_hashes != before_hashes:
        raise RuntimeError("Migration modified one or more source JSON files.")
    return report
