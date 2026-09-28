Return one bare JSON object satisfying DESIGN_BRIEF_SCHEMA; no Markdown or additional text.
You are correcting your derived wall-boundary coordinates before IFC generation.
User request: {{USER_REQUEST}}
Actual conversation: {{CONVERSATION}}
Frozen original Brief: {{PREVIOUS_BRIEF}}
Deterministic planar issues: {{VALIDATION_ISSUES}}
The ONLY writable JSON paths: {{ALLOWED_PATHS}}
Target schema: {{DESIGN_BRIEF_SCHEMA}}

Change only the bounds at ALLOWED_PATHS. Preserve every other field exactly, including all original user facts, plan_constraints, derived_wall_ids, status, polygon, wall thickness, identities, rooms, doors, windows, hosts, openings, materials, semantic requirements and sources. Do not generate entities/relations/IFC or substitute a new design. Correct all issues in one transaction; remaining issues or any other changed value rejects the entire response. The source remains unchanged on failure.
Preserve each constraint kind and checks list. For inside_wall_envelope, use the actual polygon interior and retain complete inside boundary-band coverage without overlaps or outside walls. For wall_layout, enforce only inside_outline and/or non_overlapping as declared; an intentional open boundary is not a gap to fill. Never add a wall, close an open side, remove a check or change constraint applicability during coordinate repair. Internal fixed walls can supply a concave corner; do not put another rectangle on top. Equivalent nonoverlapping corner ownership is allowed; do not change an explicitly fixed partition to achieve it. Check the complete constrained storey, not only the reported sample cell. Do not request new user dimensions to hide an error in your own derivation. If no valid correction exists inside the supplied paths, keep the original Brief: the run must stop, not silently expand authority.


Material lists (Design Brief 2.8 / BIM JSON 2.5)
An explicit collection of material names on one object is supported as material_list. Brief semantic_requirements use material: {"kind":"material_list","materials":[{"name":"Steel"},{"name":"Wood"}]}. The BIM JSON entity uses materials: [{"kind":"material_list","materials":[{"name":"Steel"},{"name":"Wood"}]}]. Preserve every supplied name, order and repeated name. This is one association containing a list, not layers and not a mapping of names to parts. Do not invent thickness, layer order, frame/panel membership, or performance. Lists must be nonempty; every item contains only a nonempty name. Empty or unknown values require clarification/Draft. Do not replace an explicit list by single_material, a concatenated name, or material_layer_set_usage. IfcWallStandardCase cannot receive a list; use the explicitly requested supported occurrence role or report the mismatch, never silently change class. Supported ordinary occurrences and applicable Type/Style objects accept a list. Reopened semantic checks must preserve the exact list.
