import os
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REFERENCE_PATH = ROOT / "docs" / "reference" / "bim-json-1.0.md"
REGENERATION_COMMAND = "python scripts/bim_json/generate_reference.py"


def _resolve(schema: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    current = node
    while "$ref" in current:
        reference = current["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/$defs/"):
            raise ValueError(f"Only local $defs references are supported: {reference!r}")
        name = reference.removeprefix("#/$defs/")
        current = schema["$defs"][name]
    return current


def _required(required: set[str], field: str) -> str:
    return "Yes" if field in required else "No"


def _inline_values(values: list[str] | tuple[str, ...]) -> str:
    return ", ".join(f"`{value}`" for value in values)


def _constraint(schema: dict[str, Any], node: dict[str, Any]) -> str:
    resolved = _resolve(schema, node)
    if "const" in resolved:
        return f"Constant `{resolved['const']}`"
    if "enum" in resolved:
        return f"One of {_inline_values(resolved['enum'])}"

    value_type = resolved.get("type", "value")
    parts = [str(value_type)]
    if "minLength" in resolved:
        parts.append(f"minimum length `{resolved['minLength']}`")
    if "minItems" in resolved:
        parts.append(f"at least `{resolved['minItems']}` item")
    if "exclusiveMinimum" in resolved:
        parts.append(f"greater than `{resolved['exclusiveMinimum']}`")
    return "; ".join(parts)


def _table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def _kind_rules(
    schema: dict[str, Any], element: dict[str, Any]
) -> dict[str, tuple[list[str], list[str]]]:
    rules: dict[str, tuple[list[str], list[str]]] = {}
    for conditional in element["allOf"]:
        kind_condition = conditional["if"]["properties"]["kind"]
        kinds = (
            [kind_condition["const"]]
            if "const" in kind_condition
            else kind_condition["enum"]
        )
        then_properties = conditional["then"]["properties"]
        dimensions = then_properties["dimensions"]["required"]
        properties = then_properties["properties"]["propertyNames"]["enum"]
        for kind in kinds:
            rules[kind] = (dimensions, properties)
    return rules


def render_reference(schema: dict[str, Any]) -> str:
    top_properties = schema["properties"]
    top_required = set(schema["required"])
    named_object = _resolve(schema, top_properties["project"])
    storey = _resolve(schema, top_properties["storeys"]["items"])
    storey_required = set(storey["required"])
    element = _resolve(schema, top_properties["elements"]["items"])
    element_required = set(element["required"])
    kinds = element["properties"]["kind"]["enum"]
    rules = _kind_rules(schema, element)
    positive_length = _resolve(
        schema, schema["$defs"]["dimensions"]["properties"]["length"]
    )

    lines = [
        "<!-- Generated from schemas/bim-json/1.0/schema.json. Do not edit. -->",
        "<!-- Regenerate with: python scripts/bim_json/generate_reference.py -->",
        "",
        "# BIM JSON 1.0 Contract Reference",
        "",
        schema["description"],
        "",
        "## Metadata",
        "",
    ]
    metadata_rows = []
    for field in ("contract_version", "target_schema", "units"):
        node = top_properties[field]
        constraint = _constraint(schema, node)
        if field == "units":
            units = _resolve(schema, node)
            constraint = _constraint(schema, units["properties"]["length"])
            constraint = f"Object with required `length`: {constraint}"
        metadata_rows.append(
            (f"`{field}`", _required(top_required, field), constraint)
        )
    lines.extend(_table(("Field", "Required", "Constraint"), metadata_rows))

    lines.extend(["", "## Hierarchy", ""])
    hierarchy_rows = []
    named_fields = _inline_values(named_object["required"])
    for field in ("project", "site", "building"):
        hierarchy_rows.append(
            (
                f"`{field}`",
                _required(top_required, field),
                named_fields,
                "Both values are non-empty strings",
            )
        )
    lines.extend(
        _table(
            ("Object", "Required", "Required fields", "Constraint"),
            hierarchy_rows,
        )
    )

    lines.extend(["", "## Storeys", ""])
    lines.append(
        f"`storeys` is required and contains at least "
        f"`{top_properties['storeys']['minItems']}` item."
    )
    lines.append("")
    storey_rows = [
        (
            f"`{field}`",
            _required(storey_required, field),
            _constraint(schema, node),
        )
        for field, node in storey["properties"].items()
    ]
    lines.extend(_table(("Field", "Required", "Constraint"), storey_rows))

    lines.extend(["", "## Common Element Fields", ""])
    element_rows = [
        (
            f"`{field}`",
            _required(element_required, field),
            _constraint(schema, node)
            if field not in {"dimensions", "properties"}
            else ("Object; kind-specific fields below"),
        )
        for field, node in element["properties"].items()
    ]
    lines.extend(_table(("Field", "Required", "Constraint"), element_rows))
    lines.extend(
        [
            "",
            "Selected optional properties are "
            f"{_inline_values(tuple(schema['$defs']['elementProperties']['properties']))}.",
            (
                "Every supplied dimension must be greater than "
                f"`{positive_length['exclusiveMinimum']}`."
            ),
        ]
    )

    lines.extend(["", "## Element Kinds", ""])
    for kind in kinds:
        dimensions, properties = rules[kind]
        lines.extend(
            [
                f"### `{kind}`",
                "",
                f"- Required dimensions: {_inline_values(dimensions)}.",
                (
                    f"- Allowed optional properties: {_inline_values(properties)}."
                    if properties
                    else "- Allowed optional properties: none."
                ),
                (
                    "- Dimension constraint: every value must be greater than "
                    f"`{positive_length['exclusiveMinimum']}`."
                ),
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def check_reference(
    schema: dict[str, Any], path: Path = DEFAULT_REFERENCE_PATH
) -> tuple[bool, str]:
    expected = render_reference(schema)
    try:
        actual = path.read_text(encoding="utf-8")
    except OSError:
        actual = None

    if actual == expected:
        return True, f"Reference is current: {path}"
    return False, f"Reference is stale. Regenerate with `{REGENERATION_COMMAND}`."


def write_reference(
    schema: dict[str, Any], path: Path = DEFAULT_REFERENCE_PATH
) -> None:
    content = render_reference(schema)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
