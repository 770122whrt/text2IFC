# Phase 1: BIM JSON 1.0 Contract and Validator - Research

**Researched:** 2026-06-11
**Domain:** Versioned JSON contracts, deterministic validation, legacy migration
**Confidence:** HIGH

<user_constraints>
## User Constraints

### Locked Decisions

- One canonical `bim-json/1.0` contract.
- IFC2X3 is the initial target schema.
- Length units are explicit and no required value is silently invented.
- Existing JSON is converted or rejected with a complete audit.
- New behavior follows RED-GREEN-REFACTOR TDD.

### the agent's Discretion

- Internal Python organization and helper types.
- Generated reference prose.

### Deferred Ideas

- IFC generation, natural-language parsing, exact geometry, materials,
  openings, and the clarification agent.
</user_constraints>

<architectural_responsibility_map>
## Architectural Responsibility Map

Single-tier Python library and CLI. The contract package owns schema loading,
validation, migration, and reference rendering. IfcOpenShell is deliberately
outside this phase's runtime path.
</architectural_responsibility_map>

<research_summary>
## Summary

The repository has 53 current top-level JSON model artifacts: 25 records in
`ifc_parsed_data.json`, 25 in `ifc_parsed_enhanced.json`, and 3 files under
`roundtrip_json/`. They disagree on hierarchy cardinality, field names
(`elevation`/`elev`, `width`/`w`, `height`/`h`), identifiers, and dimension
coverage. The current compiler also supplies default hierarchy names, a default
storey, and fallback geometry dimensions. Those behaviors make the old shapes
unsuitable as the Text-to-JSON contract.

Use JSON Schema Draft 2020-12 as the one structural source of truth and
`jsonschema.Draft202012Validator.iter_errors()` to collect all structural
errors. Add a small semantic pass for constraints JSON Schema does not express
cleanly across collections: global ID uniqueness and storey-reference
resolution. Sort diagnostics by path and code so tests, agent correction, and
future evaluation receive stable output.

Migration should be an audit, not a best-effort cleanup. Normalize known legacy
aliases, generate deterministic IDs only when provenance is recorded, reject a
whole model when required Phase 1 values are absent, and record every
out-of-contract omission. Render the contract reference from schema metadata
and fail CI when the checked-in Markdown differs.

**Primary recommendation:** Implement a JSON-Schema-first contract package with
one diagnostic API, a deterministic legacy audit, and generated reference
documentation.
</research_summary>

<standard_stack>
## Standard Stack

### Core

| Library | Version | Purpose | Why |
|---|---:|---|---|
| Python | 3.12.4 | Package and CLI runtime | Current repository runtime |
| jsonschema | 4.19.2 installed | Draft 2020-12 validation | Mature standards implementation with complete error iteration |
| pytest | 7.4.4 installed | RED-GREEN-REFACTOR tests | Existing repository convention |

### Supporting

| Library | Purpose | When to use |
|---|---|---|
| `dataclasses` | Immutable diagnostic records | Public Python result type |
| `pathlib` | Fixed-root input/output traversal | Migration and CLI paths |
| `hashlib` | Source immutability checks | Migration tests |
| `json` | Deterministic serialization | Schema, audit, and CLI output |

### Alternatives Considered

| Instead of | Could use | Tradeoff |
|---|---|---|
| JSON Schema as source of truth | Pydantic models | Better Python ergonomics but creates schema drift unless generated one-way |
| `jsonschema` | Hand-written type checks | Reimplements nested paths, combinators, enums, and standards behavior |
| Generated reference | Manually maintained field table | Human docs will drift from validation |
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### System Architecture Diagram

```text
JSON file / Python mapping
          |
          v
Schema loader -> Draft 2020-12 structural validation
          |                    |
          | invalid            v
          |              normalized diagnostics
          v
Semantic validation: unique IDs + resolved storey references
          |
          +---- valid contract ----> Phase 2 compiler boundary

Legacy JSON sources -> deterministic adapter -> validate -> converted/rejected
JSON Schema -> reference renderer -> checked-in Markdown consistency check
```

### Recommended Project Structure

```text
schemas/bim-json/1.0/schema.json
src/text2ifc_contract/
  __init__.py
  schema.py
  validation.py
  migration.py
  reference.py
scripts/bim_json/
  validate.py
  migrate_existing.py
  generate_reference.py
tests/contract/
  fixtures/complete.json
  test_schema_validation.py
  test_semantic_validation.py
  test_migration.py
  test_reference.py
docs/reference/bim-json-1.0.md
```

### Pattern 1: Schema-first structural validation

Load the checked-in schema by package-relative repository path, call
`Draft202012Validator.check_schema()` once, and use `iter_errors()` for complete
error collection. Map validator keywords to project codes and convert
`error.absolute_path` to a stable pointer-like path.

### Pattern 2: Explicit semantic pass

Run semantic checks only after structural validation succeeds. This prevents
semantic code from crashing on malformed input and keeps responsibility clear.
Build one global ID index, one storey-ID set, then emit duplicate and unresolved
reference diagnostics.

### Pattern 3: Pure migration plus filesystem orchestration

Keep `migrate_model(source, provenance)` pure and testable. A separate audit
function discovers the fixed source set, hashes sources, invokes the adapter,
validates converted documents, and writes deterministic outputs.

### Anti-Patterns to Avoid

- Maintaining both hand-written Pydantic models and hand-written JSON Schema.
- Calling IfcOpenShell from validation.
- Using `dict.get(..., default)` for required contract data.
- Dropping unsupported or incomplete elements while still reporting success.
- Resolving remote schema references at runtime.
</architecture_patterns>

<contract_recommendation>
## Contract Recommendation

The top-level document should require:

- `contract_version`: constant `bim-json/1.0`
- `target_schema`: constant `IFC2X3`
- `units.length`: constant `MILLIMETRE`
- `project`, `site`, `building`: objects with non-empty `id` and `name`
- `storeys`: non-empty array of `id`, `name`, and numeric `elevation`
- `elements`: array discriminated by `kind`

Every element requires `id`, `kind`, `name`, `storey_id`, and a family-specific
`dimensions` object:

| Kind | Required dimensions | Selected properties |
|---|---|---|
| wall | `length`, `height`, `thickness` | `is_external`, `load_bearing` |
| column | `width`, `depth`, `height` | `load_bearing` |
| beam | `length`, `width`, `height` | `load_bearing` |
| slab | `length`, `width`, `thickness` | `predefined_type` |
| door | `width`, `height` | `predefined_type` |
| window | `width`, `height` | `predefined_type` |
| stair | `length`, `width`, `height` | `predefined_type` |
| stair_flight | `width`, `rise`, `run` | `predefined_type` |
| roof | `length`, `width`, `thickness` | `predefined_type` |

All dimensions are strictly positive. Unknown fields are rejected with
`additionalProperties: false`. Names are required and non-empty. IDs are
non-empty strings and are checked for global uniqueness in the semantic pass.
</contract_recommendation>

<migration_recommendation>
## Migration Recommendation

The audit discovers exactly the current 53 top-level models. Each result stores:

- source path and model index or filename
- source SHA-256
- disposition: `converted` or `rejected`
- output path when converted
- diagnostics and explicit omission notes

Known aliases are normalized without guessing: `elev` to `elevation`, `w` to
`width`, `h` to `height`, and `pretype` to `predefined_type`. Existing IDs are
retained when valid; missing IDs use stable family/ordinal IDs and receive a
provenance note. Storey display names may map to IDs only when the name is
unique. Missing dimensions, ambiguous storeys, or unsupported source structure
reject the model. Materials, MEP, and opening counts may be omitted because
they are explicitly outside Phase 1 only when the audit records that loss.
</migration_recommendation>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---|---|---|---|
| Nested structural validation | Recursive `isinstance` checks | JSON Schema | Correct paths, enums, composition, required fields |
| Schema validation | Informal test-only assumptions | `check_schema()` | Detects an invalid contract before validating documents |
| Documentation field inventory | Separate Markdown tables | Schema renderer | Prevents contract drift |
| Path joining | String concatenation | `pathlib.Path` fixed roots | Avoids traversal and platform errors |
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Error paths become unstable

**Risk:** Tests and agent correction cannot identify the same field reliably.
**Avoidance:** Normalize to pointer-like paths and sort by `(path, code,
message)`.

### `oneOf` emits opaque parent errors

**Risk:** Users see only "not valid under any schema."
**Avoidance:** Prefer a `kind` discriminator with `if`/`then` branches and map
useful child contexts when available.

### Migration accidentally invents geometry

**Risk:** A converted document validates but does not represent source facts.
**Avoidance:** Generate IDs only with provenance; never generate required
dimensions, hierarchy names, or storey relationships.

### Generated documentation is nondeterministic

**Risk:** Every run changes ordering or line endings.
**Avoidance:** Traverse schema properties in source order, sort enumerations,
use LF, and end with exactly one newline.
</common_pitfalls>

<validation_architecture>
## Validation Architecture

- Quick structural tests: under 5 seconds.
- Semantic and documentation tests: under 10 seconds.
- Migration audit test: allowed up to 30 seconds because it reads 53 models.
- Full Phase 1 command:
  `python -m pytest tests/contract -q`
- Existing regression command:
  `python -m pytest tests -q`
- Every TDD plan must demonstrate a failing behavioral assertion before
  implementation, not merely an import or syntax failure.
- All behaviors have automated verification; no manual-only checks are needed.
</validation_architecture>

<security_considerations>
## Security Considerations

- The schema must contain no remote `$ref`; validation must not perform network
  resolution.
- CLI input size and collected error count should be bounded to prevent
  pathological files from exhausting memory.
- Migration discovery uses fixed repository paths and never accepts an output
  path derived directly from untrusted JSON.
- Source files are hash-checked before and after migration tests.
</security_considerations>

<sources>
## Sources

### Primary

- https://json-schema.org/draft/2020-12 - JSON Schema Draft 2020-12.
- https://python-jsonschema.readthedocs.io/en/stable/validate/ -
  `Draft202012Validator`, `check_schema`, and `iter_errors`.
- https://docs.pytest.org/en/stable/explanation/goodpractices.html - pytest
  project and test organization guidance.
- Local installed versions and repository source files inspected on
  2026-06-11.
</sources>

<metadata>
## Metadata

**Research scope:** contract design, validation API, migration audit,
documentation generation, security boundaries, and TDD verification.

**Confidence breakdown:**

- Standard stack: HIGH - installed and already compatible with Python 3.12.
- Architecture: HIGH - small single-tier package with clear pure functions.
- Migration rules: MEDIUM-HIGH - all current source shapes were inventoried,
  but conversion yield will only be known after execution.
- Validation: HIGH - every requirement maps to automated tests.

**Research date:** 2026-06-11
**Valid until:** 2026-09-11
</metadata>

---

*Phase: 01-bim-json-1-0-contract-and-validator*
*Research completed: 2026-06-11*
*Ready for planning: yes*
