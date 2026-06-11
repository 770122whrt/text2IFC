<!-- Generated from schemas/bim-json/1.0/schema.json. Do not edit. -->
<!-- Regenerate with: python scripts/bim_json/generate_reference.py -->

# BIM JSON 1.0 Contract Reference

Canonical structured input contract for the IFC2X3 compiler.

## Metadata

| Field | Required | Constraint |
| --- | --- | --- |
| `contract_version` | Yes | Constant `bim-json/1.0` |
| `target_schema` | Yes | Constant `IFC2X3` |
| `units` | Yes | Object with required `length`: Constant `MILLIMETRE` |

## Hierarchy

| Object | Required | Required fields | Constraint |
| --- | --- | --- | --- |
| `project` | Yes | `id`, `name` | Both values are non-empty strings |
| `site` | Yes | `id`, `name` | Both values are non-empty strings |
| `building` | Yes | `id`, `name` | Both values are non-empty strings |

## Storeys

`storeys` is required and contains at least `1` item.

| Field | Required | Constraint |
| --- | --- | --- |
| `id` | Yes | string; minimum length `1` |
| `name` | Yes | string; minimum length `1` |
| `elevation` | Yes | number |

## Common Element Fields

| Field | Required | Constraint |
| --- | --- | --- |
| `id` | Yes | string; minimum length `1` |
| `kind` | Yes | One of `wall`, `column`, `beam`, `slab`, `door`, `window`, `stair`, `stair_flight`, `roof` |
| `name` | Yes | string; minimum length `1` |
| `storey_id` | Yes | string; minimum length `1` |
| `dimensions` | Yes | Object; kind-specific fields below |
| `properties` | No | Object; kind-specific fields below |

Selected optional properties are `is_external`, `load_bearing`, `predefined_type`.
Every supplied dimension must be greater than `0`.

## Element Kinds

### `wall`

- Required dimensions: `length`, `height`, `thickness`.
- Allowed optional properties: `is_external`, `load_bearing`.
- Dimension constraint: every value must be greater than `0`.

### `column`

- Required dimensions: `width`, `depth`, `height`.
- Allowed optional properties: `load_bearing`.
- Dimension constraint: every value must be greater than `0`.

### `beam`

- Required dimensions: `length`, `width`, `height`.
- Allowed optional properties: `load_bearing`.
- Dimension constraint: every value must be greater than `0`.

### `slab`

- Required dimensions: `length`, `width`, `thickness`.
- Allowed optional properties: `predefined_type`.
- Dimension constraint: every value must be greater than `0`.

### `door`

- Required dimensions: `width`, `height`.
- Allowed optional properties: `predefined_type`.
- Dimension constraint: every value must be greater than `0`.

### `window`

- Required dimensions: `width`, `height`.
- Allowed optional properties: `predefined_type`.
- Dimension constraint: every value must be greater than `0`.

### `stair`

- Required dimensions: `length`, `width`, `height`.
- Allowed optional properties: `predefined_type`.
- Dimension constraint: every value must be greater than `0`.

### `stair_flight`

- Required dimensions: `width`, `rise`, `run`.
- Allowed optional properties: `predefined_type`.
- Dimension constraint: every value must be greater than `0`.

### `roof`

- Required dimensions: `length`, `width`, `thickness`.
- Allowed optional properties: `predefined_type`.
- Dimension constraint: every value must be greater than `0`.
