Return exactly one bare JSON object satisfying DESIGN_BRIEF_SCHEMA. No Markdown.
You are correcting incomplete semantic extraction in a text2IFC Design Brief.
Original user request: {{USER_REQUEST}}
Frozen conversation: {{CONVERSATION}}
Initial Brief: {{PREVIOUS_BRIEF}}
Validation issues: {{VALIDATION_ISSUES}}
Complete target schema: {{DESIGN_BRIEF_SCHEMA}}

Only known_facts.semantic_requirements and known_facts.semantic_review may change.
Copy every other field exactly, including original_request, geometry, status,
identities, storeys, dimensions, locations, decisions and fact sources. Do not
redesign, rename, invent values, reclassify an acknowledged defect or ask the user
to repeat clear facts. Extract from user turns, never from a candidate IFC/JSON.
Review all five semantic categories, using exact user turn IDs. specified requires
matching canonical records; not_specified means no request, never failed extraction.
Place every explicit material/property/Type/element appearance/template requirement
in the canonical array with its exact stable target and scope. Enumerate all targets
of a requested group; preserve explicit negatives. Global theme defaults do not
authorize element overrides or physical materials. No performance value without
an explicit request. If this cannot be corrected within the two allowed fields,
retain the unresolved status in semantic_review; the deterministic boundary stops.
