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
