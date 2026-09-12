# Case 02 — Explicit User RGB + Material Restoration

Status: **PASS**

## Live chain

`original.ifc -> deterministic Beam removal -> damaged.ifc -> RepairIntent 0.9 -> ChangeSet 0.6 -> genuine RepairAPI -> repaired.ifc`

- Final live run: `repair-510a533e43c94b7083ea8824c2221685`
- Requested existing Material: `IfcMaterial C_钢筋砼C30`
- Reopened occurrence Material: `C_钢筋砼C30`
- Requested RGB: `(0.92, 0.12, 0.18)`
- Reopened Body RGB: `(0.92, 0.12, 0.18)`
- Repaired Beam: `3wrIf6EXrKQu4gX$SeDa9j`
- Exact reused IfcBeamType: `17tPjyQtf2L9JnbXXmcTTd`
- Maximum world Body bbox error: approximately `2.63e-7 mm`
- IFCcompare: `unexpected_changed_ids=[]`, `complete_preservation_success=true`

## Why Material was missing in the first appearance run

The original public Case 2 request explicitly authorized exact Type reuse and RGB appearance, but did not explicitly authorize reuse of the occurrence Material. The string `C30` inside the Type name is not sufficient authority to infer an `IfcMaterial`, and Beam does not automatically promote same-Type occurrence Material into executable authority.

After the request was corrected to explicitly reuse `IfcMaterial C_钢筋砼C30`, Stage 1 produced a standard `intent_kind: material`, the semantic manifest produced `authoring_action: reuse_material`, and the Bound ChangeSet carried the Material assignment correctly.

That retry exposed one existing provenance canonicalization defect: semantic Material authoring requires an executable `source_ref` in the canonical `request:/...` namespace, while the Provider may legitimately emit a public provenance label such as `public_request`. Production evidence now canonicalizes explicit Material authority to `request:/text` while preserving the original Provider/public reference in the provenance trail.

## Final restored occurrence

The final Beam simultaneously has:

- exact original `IfcBeamType` relation;
- occurrence-level `IfcRelAssociatesMaterial -> C_钢筋砼C30`;
- direct Body-item SurfaceStyle with RGB `(0.92, 0.12, 0.18)`.

Material identity and presentation colour remain separate: the C30 Material resource is reused, while the red appearance is applied only to the restored Beam occurrence rather than recolouring the shared Material or Type.
