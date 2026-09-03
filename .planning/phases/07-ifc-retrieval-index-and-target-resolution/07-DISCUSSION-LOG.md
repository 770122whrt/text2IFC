# Phase 7: IFC Retrieval Index and Target Resolution - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution
> agents. Decisions are captured in `07-CONTEXT.md`; this log preserves the
> alternatives considered.

**Date:** 2026-07-19
**Phase:** 7-IFC Retrieval Index and Target Resolution
**Areas discussed:** vector role, element coverage, entity record, property
handling, constraint semantics, ambiguity, engineering position, context
budget, storage lifecycle, and acceptance

---

## Vector retrieval role

| Option | Description | Selected |
|---|---|---|
| Interface now, implement later | Reserve a pluggable retriever; keep Phase 7 deterministic and evaluate vector retrieval in Phase 13 | Yes |
| Implement in Phase 7 | Add embeddings and vector retrieval to the first index implementation | No |
| No vector boundary | Omit vector-related interfaces entirely | No |

**User's choice:** Use the first option.
**Notes:** Vector retrieval must not override hard IFC constraints and is not a
Phase 7 success dependency.

---

## Initial element coverage

| Option | Description | Selected |
|---|---|---|
| All major IfcProduct targets | Make all common IFC product classes first-class editable targets immediately | No |
| Wall, Door, Window first | Limit initial editable targets while preserving generic adapters | Yes |
| Wall only | Keep the existing Window-host Wall context shape | No |

**User's choice:** Initially cover IFC Wall, Door, and Window, then expand.
**Notes:** The user accepted `IfcSpace` as the default room representation but
wants explicit user-requested semantic variations to remain possible.

---

## Entity record and invalid IFC

| Option | Description | Selected |
|---|---|---|
| Common record plus typed facets | One shared identity/spatial/relationship/geometry/property skeleton with adapters | Yes |
| Per-operation records | Separate record structures for Window, Door, Wall, and future classes | No |

**User's choice:** Accept the common architecture.
**Notes:** Invalid or damaged IFC must be recognized for both user input and
system-produced output. Diagnostic IDs may aid reporting but cannot become
silent mutation identities.

---

## Property-set handling

| Option | Description | Selected |
|---|---|---|
| Small fixed allowlist only | Store and expose only properties needed by the first operation | No |
| Retain broadly, project narrowly | Preserve parseable properties locally and select request-relevant fields for Agent/compiler JSON | Yes |
| Send all properties to Provider | Put the complete property payload in every prompt | No |

**User's choice:** Retain property information as much as practical. The Agent
extracts property intent into JSON for deterministic compiler handling.
**Notes:** Full database retention does not authorize unbounded Provider input;
typed projection and compiler validation remain required.

---

## Target resolution behavior

| Option | Description | Selected |
|---|---|---|
| Deterministic hybrid evidence | GUID, aliases, storey, space/grid, direction, relationships, and geometry combine with field evidence | Yes |
| Name-first lookup | Continue exact storey plus Name selection | No |
| Agent chooses raw candidates | Let the Provider search or guess from raw IFC/JSON | No |

**User's choice:** All recommended defaults.
**Notes:** Hard-constraint failures, conflicts, zero matches, and unresolved
ambiguity stop or clarify; they never silently resolve by candidate order.

---

## Engineering position and openings

| Option | Description | Selected |
|---|---|---|
| Multi-evidence local positioning | Preserve coordinate basis, readable direction, offsets, grids/spaces, nearby elements, and opening relationships | Yes |
| Bare wall-local offset | Expose only a numeric offset from an unexplained axis start | No |

**User's choice:** All recommended defaults.
**Notes:** Existing openings are recorded as current-model entities. Removed
benchmark openings remain private ground-truth evidence and are not leaked to
the Provider.

---

## Context projection and ambiguity

| Option | Description | Selected |
|---|---|---|
| Bounded top-K with evidence | Normal top-5, diagnostic top-10, deterministic byte/token budget and field evidence | Yes |
| Whole IFC JSON | Send all extracted IFC content to the Provider | No |
| Silent top-1 | Always accept the highest score even when close or conflicting | No |

**User's choice:** All recommended defaults.
**Notes:** The comprehensive index stays local; Provider context is operation-
and intent-aware.

---

## Index storage and lifecycle

| Option | Description | Selected |
|---|---|---|
| Embedded SQLite database | Start with a real local database and no external service | Yes |
| JSON sidecar | Store the primary index as serialized JSON | No |
| External database service | Require a separately managed database server | No |

**User's choice:** Use a database directly if feasible.
**Notes:** SQLite is the selected embedded implementation. It is bound to the
source fingerprint and index version; Phase 7 uses deterministic full rebuilds
while preserving a replaceable storage interface.

---

## Acceptance scope

| Option | Description | Selected |
|---|---|---|
| LargeBuilding plus synthetic fixtures | Realistic scale sample plus controlled ambiguity/corruption tests | Yes |
| LargeBuilding only | Rely entirely on one external IFC | No |
| Tiny fixtures only | Defer realistic model behavior | No |

**User's choice:** All recommended defaults.
**Notes:** `IfcSpace` proves generic spatial indexing; curved walls are
classified but not modified; the baseline must pass with vector retrieval off.

## the agent's Discretion

- SQLite schema and migration details.
- Initial deterministic scoring weights, margins, and tolerances, provided they
  are versioned and frozen by tests.
- Exact adapter/module names consistent with the existing registry pattern.

## Deferred Ideas

- Vector implementation and evaluation in Phase 13.
- Space mutation and additional IFC target families after Wall/Door/Window.
- Incremental indexing after scale measurements.
- Curved-wall editing and L3 exactness.
