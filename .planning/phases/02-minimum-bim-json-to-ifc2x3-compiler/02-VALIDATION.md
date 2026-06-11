# Phase 2 Validation Strategy

**Created:** 2026-06-11
**Status:** Planned

## Validation Principle

Every externally observable compiler behavior begins with a failing test.
Tests inspect serialized and reopened IFC whenever the requirement concerns the
artifact, not compiler-side bookkeeping.

## Canonical Commands

```powershell
python -m pytest tests/compiler -q
python -m pytest tests -q
```

The phase-specific suite must finish within 60 seconds on the current machine.

## Wave 0 Test Infrastructure

Create shared helpers in `tests/compiler/conftest.py`:

- load and deep-copy the canonical complete fixture,
- compile into pytest temporary paths,
- reopen IFC through the installed IfcOpenShell runtime,
- measure represented element bounds in millimetres,
- recover psets, hierarchy, containment, and identity.

The helpers must use public compiler/verifier APIs and reopened files.

## Plan Gates

### 02-01 Foundation

RED tests:

- invalid canonical input returns Phase 1 diagnostics,
- invalid input creates no output and does not overwrite a sentinel,
- valid input creates IFC2X3 with one project,
- names, elevations, aggregation, and containment match,
- GlobalIds are unique and stable across two compilations,
- original BIM IDs are retrievable,
- output replacement is atomic on simulated verification failure.

GREEN gate:

```powershell
python -m pytest tests/compiler/test_compiler_boundary.py -q
```

### 02-02 Geometry

RED tests:

- all nine kind-to-class counts match,
- each required dimension is recovered within 1 mm,
- stair-flight `run`, `width`, and total `rise` use the locked interpretation,
- represented products have placements,
- empty-family documents do not create extra classes.

GREEN gate:

```powershell
python -m pytest tests/compiler/test_geometry.py -q
```

### 02-03 Properties

RED tests:

- `is_external` and `load_bearing` round-trip as booleans,
- each source `predefined_type` round-trips as the same string,
- compatible IFC2X3 enum attributes are populated,
- unsupported/custom strings remain retrievable without coercion,
- compilation does not mutate the input document.

GREEN gate:

```powershell
python -m pytest tests/compiler/test_properties.py -q
```

### 02-04 Verification and Acceptance

RED tests:

- complete output returns zero normalized IFC validation issues,
- deliberately malformed IFC returns at least one stable issue,
- CLI success and validation-failure exit codes are stable,
- CLI JSON diagnostics are machine-readable,
- temporary artifacts are removed on every failure path.

GREEN gate:

```powershell
python -m pytest tests/compiler/test_ifc_verification.py tests/compiler/test_complete_compilation.py -q
```

## Regression Gates

After every GREEN commit:

```powershell
python -m pytest tests/compiler -q
python -m pytest tests -q
```

Before phase completion:

```powershell
python -m compileall -q src scripts
python scripts/bim_json/generate_reference.py --check
python -m pytest tests -q
```

## Evidence Rules

- Record the exact failing assertion and RED commit in each plan summary.
- Record GREEN and optional REFACTOR commits separately.
- Never count an import error, missing fixture, or environment failure as RED.
- If a plan changes after research or test evidence, record the reason in its
  summary and update this strategy before proceeding.
- Phase verification must map every IFC-01..05 and VER-01..03 requirement to
  passing automated evidence.

