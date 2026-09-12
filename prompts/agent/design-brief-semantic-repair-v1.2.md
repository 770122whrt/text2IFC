Return exactly one bare JSON object satisfying DESIGN_BRIEF_SCHEMA. No Markdown.
You are correcting incomplete semantic extraction in a text2IFC Design Brief.
Original user request: {{USER_REQUEST}}
Frozen conversation: {{CONVERSATION}}
Initial Brief: {{PREVIOUS_BRIEF}}
Validation issues: {{VALIDATION_ISSUES}}
Complete target schema: {{DESIGN_BRIEF_SCHEMA}}

Only known_facts.semantic_requirements and known_facts.semantic_review may be rewritten.
Additionally, the exact semantic leaves in REMOVABLE_SEMANTIC_PATHS must be removed
from their original product/type records after their intent is represented canonically.
Do not alter their parent identity, category, dimensions, metadata or any other field.
Removable semantic leaves: {{REMOVABLE_SEMANTIC_PATHS}}
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
an explicit request. If this cannot be corrected within this exact semantic scope,
retain the unresolved status in semantic_review; the deterministic boundary stops.


Executable appearance grammar and scope (Design Brief 2.3)

semantic_requirements[].appearance is ONLY a whole-element numerical override:
color is an RGB array of three numbers in [0,1]; transparency is a number in [0,1].
The object must not be empty and cannot contain profile, frame_color, frame_profile,
glazing_transparency, colour words, or other component descriptions. Follow the
actual Schema exactly. These fields are executable requirements, not free text.

Keep the overall theme in known_facts.appearance.profile and preserve qualitative
style cues in its style_notes. Basic filling templates already provide distinct
frame/glazing/leaf styles. A request for dark thin frames and transparent glazing
compatible with the selected theme belongs to those template/theme choices; it
does NOT authorize one RGB or transparency override for the whole window/door.
Do not invent exact RGB/opacity numbers from qualitative style cues or ask about
already approved theme/template defaults. Keep physical material requirements
separate. Never clear a material because an appearance description is unsupported.

semantic_review.appearance specifically reviews whole-element numeric overrides.
With only an overall theme/default part-style request, use not_specified for this
category and keep the part-style description and explicit templates separately.
specified requires a legal, explicitly requested whole-element override in the
canonical array. If a genuinely explicit part-level customization cannot be
represented by the supported theme/template contract, preserve its text and use
the normal clarification/unsupported route instead of flattening component styles.

Executable whole-element appearance schema: {{ELEMENT_APPEARANCE_SCHEMA}}

Type/material role contract (recovery 1.2)

A Type definition is not an occurrence: never give a Type its own type_id, or bind
one Type to another Type. Keep definitions and geometry metadata unchanged.
Bindings belong to occurrence semantic rows only and must name a compatible defined
Type. Put material/property values of a Type in a separate canonical row targeting
the Type ID. Basic filling templates belong to IfcDoor/IfcWindow occurrences, not
IfcDoorStyle/IfcWindowStyle definitions. If a misplaced template describes a shared
Type group, retain the exact template on every explicitly bound occurrence.

Direct walls require material_layer_set_usage / AXIS2, direct horizontal plates
require material_layer_set_usage / AXIS3. Type layer definitions use
material_layer_set; its inherited occurrence value may remain a layer set. Preserve
layer names, order, thickness and all concrete user material names. A string material
is not executable: use single_material with the exact name when that is the request.
Do not resolve conflicting user requirements by silently choosing a Type or material.
Never remove an already valid semantic requirement to gain a pass.
