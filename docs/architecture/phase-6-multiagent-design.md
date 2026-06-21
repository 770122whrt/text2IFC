# Phase 6 Multi-agent Design

## Purpose

Phase 6 keeps one product boundary:

```text
Chinese natural language
  -> Design Brief
  -> Formal BIM JSON 2.0 or Draft
  -> deterministic validation and IFC2X3 compilation
  -> deterministic quality gates
  -> semantic audit and run report
```

The model layer does not generate IFC or STEP text. BIM JSON Schema remains
the only structural truth for BIM JSON. Deterministic checks decide whether a
Formal candidate can be compiled and accepted.

## Design Brief Agent

### What it does

The Design Brief Agent translates the original Chinese request into explicit
known facts, missing facts, ambiguities, corrections, clarification targets,
and provenance. It produces a Design Brief record, not BIM JSON.

### Why it exists

User requests often mix intent, partial measurements, and spatial language.
Separating understanding from schema construction makes missing information
visible and gives later generation and audit stages the same intent record.

### What it must not do

- It must not emit BIM JSON entities or relationships.
- It must not emit IFC, STEP text, or compiler objects.
- It must not fill missing dimensions, placements, or relationships.

## BIM JSON Generator Agent

### What it does

The Generator consumes the Design Brief, BIM JSON schema and capability
context, named few-shot assets, and any deterministic feedback. It produces
either Formal BIM JSON 2.0 or a Draft update with clarification questions.

### Why it exists

BIM JSON is the validated semantic boundary between language understanding and
IFC compilation. A focused generator is easier to measure and repair than a
single prompt responsible for understanding, low-level IFC, and self-review.

### What it must not do

- It must not output raw IFC, STEP text, STEP IDs, `IfcCartesianPoint`,
  `IfcDirection`, `IfcOwnerHistory`, or compiler-only objects.
- It must not compile IFC or bypass BIM JSON validation.
- It must not turn unknown user facts into defaults.

## Conditional Failure Routing

### What it does

Every generation run records exactly one route:

- `no_repair_needed`: the first Formal candidate passes the required gates.
- `repair_attempted`: known facts are sufficient and structured feedback can
  be used for a bounded generator retry.
- `draft_required`: user facts are missing or ambiguous, so the system asks
  for clarification.
- `blocked_failure`: the failure is unsafe, inconsistent, or not recoverable
  automatically.

Repair is conditional. A successful first pass records zero repair attempts.
Repair begins as a mode of the BIM JSON Generator because both generation and
repair have the same Formal-or-Draft output contract.

### Why it exists

Failure routing prevents repeated model calls from being mistaken for
improvement. It exposes whether a failure came from missing user information,
repairable model output, or a blocking system/provider problem.

### What it must not do

- It must not repair missing user facts by invention.
- It must not retry indefinitely.
- It must not hide before/after diagnostics or issue-count changes.

## Audit Agent

### What it does

The Audit Agent compares the original request, Design Brief, BIM JSON,
validator feedback, generated IFC metrics, and artifact references. It reports
intent coverage, mismatches, unsupported facts, and human-review notes.

### Why it exists

Schema and geometry gates can prove structural properties but cannot fully
decide whether the result reflects the user's intended meaning. A separate
review role reduces generator self-review bias.

### What it must not do

- Audit cannot override deterministic gates.
- It must not modify BIM JSON, repair candidates, or compile IFC.
- It must not recommend acceptance when required evidence is absent.

## Observer Loop

### What it does

The Observer Loop records prompt identity, renderer inputs, rendered prompt,
raw and parsed outputs, validation and geometry feedback, failure route,
repair attempts, audit result, metrics, and artifact paths. It generates the
human-facing `report.md` from those trace artifacts.

### Why it exists

Prompt changes are experiments. They are accepted only when a stable case,
failure classification, and measured result show an improvement without
weakening safety or data-split guarantees.

### What it must not do

- It must not describe a hard-coded candidate as live provider output.
- It must not write provider tokens, headers, or private URLs to artifacts.
- It must not accept a hand-written report as run evidence.

## Prompt And Trace Contract

Every provider-backed call uses `prompts/agent/registry.json`. The registry
defines the template ID, role, mode, path, content hash, required inputs, and
forbidden output classes. The renderer validates the hash before use.

A reproducible provider trace records at least:

- template ID and template hash;
- structured renderer input path and rendered prompt path;
- raw response and parsed response paths;
- validation feedback and metrics paths;
- the complete artifact-path manifest.

Later Phase 6 waves extend the same trace with Design Brief, geometry,
failure-routing, repair, audit, and generated report artifacts.

## Evidence Boundary

`dataset/processed/agent-demo/geometry-gate/two-room-suite` is a deterministic
geometry-gate fixture. Its candidate is defined in
`scripts/agent/run_geometry_gate_demo.py`; it does not prove a live provider
call, multi-turn behavior, or unified prompt control.

Live, replayed, and deterministic runs must be labeled separately. Provider
behavior can be claimed only when prompt metadata, raw provider output, and
artifact provenance all agree. Expired credentials, unclear provider output,
hard-coded evidence presented as live output, or secret leakage blocks the
claim and must be reported.
