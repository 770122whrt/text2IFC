# Phase 12: Beam and Column Operations - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution
> agents. Decisions are captured in CONTEXT.md; this log preserves the
> alternatives considered.

**Date:** 2026-08-03
**Phase:** 12-beam-and-column-operations
**Areas discussed:** structural geometry; placement, containment and
relationships; Type, material, property knowledge and routing; validation and
live proof

---

## Structural geometry

| Option | Description | Selected |
|--------|-------------|----------|
| Rectangular straight members | Horizontal straight Beam and vertical straight Column, with arbitrary horizontal Beam direction | Yes |
| Inclined members | Add sloped Beam and inclined Column geometry in Phase 12 | No |
| Additional profiles | Add round, I/H or arbitrary profiles in Phase 12 | No |

**User's choice:** “目前先支持矩形吧！” and “同意” to the center-axis
canonical placement proposal.

**Notes:** Rectangular-only support is a deterministic capability boundary, not
permission to approximate other profiles. The center axis, rather than a
profile corner or authoring-specific placement origin, is the public geometry
authority.

---

## Placement, containment and relationships

| Option | Description | Selected |
|--------|-------------|----------|
| Storey-local plus structural-axis references | Use explicit Storey-local millimetre coordinates or uniquely resolved existing Beam/Column axes | Yes |
| Formal Grid placement | Add `IfcGrid` indexing and grid-axis intersection resolution | No |
| Structural connectivity | Author analysis members, nodes, ports or automatic joints | No |

**User's choice:** Accepted as part of the complete freeze list with no
requested change.

**Notes:** Beam containment is the selected Storey; Column containment is its
base Storey. Contact at supports is allowed, while automatic trimming, joining
and clash correction remain out of scope.

---

## Type, material, property knowledge and routing

| Option | Description | Selected |
|--------|-------------|----------|
| Exact or deterministic Type; optional authorized material | Type is required; material appears only when requested or inherited through explicitly authorized exact Type reuse | Yes |
| Material required | Clarify every request that omits material | No |
| Invent a default material | Infer concrete, steel, grade or strength from names or common practice | No |

**User's choice:** “T4我一般来讲是如果用户输入有做复用type和其他的限定的话可以进行有材料 如果用户没指定就不用给出”.

**Notes:** This changed the proposed required-material rule. Missing material is
not incomplete. Exact Type reuse preserves existing inherited material
semantics but does not authorize copying occurrence-direct facts. Explicit
conflicts clarify. The existing IFC2X3 PSD corpus remains authoritative; Beam
and Column need index, Type, occurrence-authoring and live-proof completion,
not a new RAG.

---

## Validation and live proof

| Option | Description | Selected |
|--------|-------------|----------|
| Full strict matrix | Real d7n/vvo IFC2X3, both families, mixed atomicity, both RAG paths, real complete and clarification DeepSeek UAT | Yes |
| Representative family only | Prove either Beam or Column and infer the other | No |
| Synthetic acceptance fallback | Replace unavailable or failing live evidence with fixtures or prerecorded output | No |

**User's choice:** Accepted as part of the complete freeze list with no
requested change.

**Notes:** A full BIMNet manifest scan found 11 IFC2X3 files containing Beam or
Column. `d7n.ifc` is the primary test-split scene and `vvo.ifc` supplies
secondary mapped/swept and material-variation evidence. Both are BIMNet, so the
phase may claim cross-scene but not cross-authoring-family validation.

---

## the agent's Discretion

- Internal handler/test module boundaries.
- Deterministic entity naming and GUID seed details.
- Exact implementation layout of the family-neutral proof validator.

## Deferred Ideas

- Inclined, curved and additional/variable structural profiles.
- Formal Grid placement.
- Structural analysis/connectivity authoring.
- Existing structural-member mutation operations.
- Independent non-BIMNet authoring-family acceptance.
- Phase 13 large-context work.
