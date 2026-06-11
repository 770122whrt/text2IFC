# text2IFC Architecture Overview

## Goal

The system will accept natural-language building requirements and produce a
valid IFC model. When required information is missing or ambiguous, a future
agent will ask the user targeted follow-up questions before generation.

## Target Pipeline

```text
Natural language
  -> intent and parameter extraction
  -> clarification loop
  -> validated BIM JSON
  -> deterministic IFC compiler
  -> IFC schema and semantic verification
  -> IFC file
```

The model does not directly generate IFC STEP text. It generates a constrained
BIM JSON document that deterministic code compiles into IFC.

## Offline Dataset Construction

The training-data path runs in the opposite direction:

```text
Authorized source IFC
  -> deterministic supported-subset extraction
  -> BIM JSON 1.1 ground truth + provenance + loss report
  -> natural-language descriptions and instructions
  -> paired Text-to-JSON dataset
```

This reverse path exists only to create labels from IFC assets that already
contain the building truth. It is not called when an end user asks the system
to create a new model.

## Current Capabilities

- 25 IFC2X3 Coordination View source models.
- Official IFC2X3 TC1 EXPRESS schema.
- IFC-to-JSON extraction prototypes.
- Canonical `bim-json/1.0` JSON Schema and deterministic validator.
- Canonical `text2ifc_compiler` package using IfcOpenShell 0.8.5.
- Validated, atomically written IFC2X3 with exact hierarchy and containment.
- All nine supported element classes with measurable basic dimensions.
- Stable BIM-ID-to-GlobalId mapping and selected property preservation.
- Reopened IFC schema verification and a bounded file compiler CLI.

The supported compiler command is:

```powershell
python scripts/bim_json/compile_ifc.py input.json output.ifc
```

It emits one JSON result object and exits `0` on success, `1` for contract or
IFC validation failure, and `2` for usage or input-file errors.

`scripts/ifc_pipeline/roundtrip.py` is retained only as a legacy research
prototype for the earlier informal JSON format. Product code must use
`text2ifc_compiler` and must not call the prototype compiler.

## Phase Boundaries

### Phase 1: BIM JSON 1.0 Contract and Validator

Deliver one versioned contract with deterministic validation for:

- project, site, building, and storey hierarchy
- supported building element types
- basic dimensions
- selected common properties
- required and optional field semantics
- migration or explicit rejection of existing project JSON

### Phase 2: Minimum IFC2X3 Compiler

Compile BIM JSON 1.0 to reopenable IFC2X3 with hierarchy, element counts,
basic dimensions, selected properties, stable identity, atomic output, and
schema-level verification.

### Phase 2.5: BIM JSON 1.1 Spatial Ground Truth

Add hierarchical placement, spaces, opening/filling relationships, deterministic
IFC ground-truth extraction, explicit losses, 1.0 migration, and minimum
spatial compiler support.

### Phase 3: Text-to-JSON Dataset and Baseline

Create provenance-linked BIM JSON 1.1 pairs from the Phase 2.5 ground truth,
evaluate structured-output baselines, and run the first spatial
Text-to-JSON-to-IFC demonstration.

### Phase 4: High-fidelity IFC Round Trip

Add material/type fidelity, complex geometry, broader product classes,
connection topology preservation, and explicit loss reports.

### Phase 5: Multi-turn Clarification Agent

Ask targeted questions when a natural-language request cannot satisfy BIM JSON
requirements.

### Phase 6: Data Expansion, Fine-tuning, and Deployment

Expand license-reviewed data, compare prompting and fine-tuning, and deploy the
selected complete pipeline.

## Architectural Principle

Every probabilistic output is validated before it reaches the deterministic
IFC compiler. Invalid or incomplete input must produce actionable errors or
clarification questions, not silently invented building data.

The JSON Schema at `schemas/bim-json/1.0/schema.json` is the only structural
truth for compiler input. The compiler consumes the Phase 1 validator and does
not maintain a second independent BIM data model.
