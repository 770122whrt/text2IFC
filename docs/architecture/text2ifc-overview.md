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

## Current Capabilities

- 25 IFC2X3 Coordination View source models.
- Official IFC2X3 TC1 EXPRESS schema.
- IFC-to-JSON extraction prototypes.
- JSON-to-IFC generation prototype using IfcOpenShell.
- Basic round-trip checks for entity counts and wall names.
- Tests for storey elevations, wall common properties, and door/window sizes.

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
basic dimensions, and selected properties.

### Phase 3: Text-to-JSON Dataset and Baseline

Create provenance-linked text/JSON pairs, evaluate structured-output baselines,
and run the first Text-to-JSON-to-IFC demonstration.

### Phase 4: High-fidelity IFC Round Trip

Add precise placement, orientation, openings, filling relationships, material
assignments, topology preservation, and explicit loss reports.

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
