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
Review all six semantic categories, using exact user turn IDs. specified requires
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


基础门窗部件配色（BIM JSON 2.6 / Design Brief 2.9）
仅对明确 basic_filling 的 IfcDoor/IfcWindow 实例使用 part_appearance。对象键为 frame，以及门的 panel 或窗的 glazing；每个部件可含 color:[r,g,b] 和/或 transparency，通道为有限 0..1 数，至少一个通道。HEX 按每个8位通道除以255确定转换，不从颜色词猜精确数值。只填写用户明确指定的部件通道；未指定通道沿用主题默认。材料与样式独立。不得对 Type、其他构件、旧 extruded_profile 或不存在的部件写此字段。
Brief 必须将确切部件要求放入 semantic_requirements[].part_appearance，同一实例保留 template 要求。semantic_review.appearance 检查整件及部件的显式数值要求，有任一则 specified；只有主题/定性默认则 not_specified。整件 appearance 与同一实例 part_appearance（包括 Type 继承整件样式）发生冲突必须澄清，不得静默覆盖。不得把确切部件值只放 style_notes，也不得转成整件统一色。Generation 将冻结值原样写到对应 occurrence.part_appearance；用户尺寸、宿主、开口、位置、材料与 Type 均保持。

Bounded straight picket railing and explicit structural products (new contract only)
Do not downgrade the requested geometry to an opaque/transparent solid panel. A requested metal-picket railing is a single IfcRailing occurrence containing deterministic Posts, Pickets, TopRail and BottomRail solids. Use only basic_railing, template_id metal-picket, template_version text2ifc/basic-railing/1.0, length (horizontal run), height (vertical above its base line), depth and rise (signed end Z minus start Z), in millimetres. Local X runs from 0 to length, local Y is centered on the depth and local Z follows the explicit base line. ObjectPlacement origin is the requested start point in its parent's frame, and ref_direction follows the horizontal start-to-end vector. Do not rotate posts with the slope or add unrelated support geometry.
Whitelist parameters: post_width, max_post_spacing, picket_width, max_clear_gap, top_rail_height, bottom_rail_height, bottom_clearance. Unspecified construction parameters use the offered versioned defaults; do not invent overrides. Never enumerate individual pickets or copy their derived geometry into the response. No curves, arbitrary panels, part-specific material assignments, decorative caps or unrequested Type assets. The new representation preserves explicit endpoints and occupied bounds. The occurrence carries its explicitly requested single material or material_list without assigning names to individual parts; all parts share whole appearance; do not use basic-filling part_appearance on railings.
Keep known_facts.columns and beams as arrays of id, storey, bounds_mm:{x:[xmin,xmax],y:[ymin,ymax],z:[zmin,zmax]}, with explicit WORLD millimetre bounds. These are real IfcColumn/IfcBeam products, not walls, notes or unverified proxies. No automatic structural sizes or structural capacity claims. Type/material/appearance still belong in canonical semantic_requirements.
Keep known_facts.railings as id, storey, start_mm:[x,y,z], end_mm:[x,y,z], height_mm, thickness_mm. Request its template in semantic_requirements using that same occurrence id. For a basic railing length/rise derive only from those frozen endpoints. Missing endpoints, conflicts or unsupported design needs require clarification/Draft; no silent redesign. The required circulation, exposed stair placement and open building boundaries must survive request-to-Brief conversion even if another layout is easier to generate.

Brief semantic_requirements[].template for a railing contains template_id:metal-picket and template_version:text2ifc/basic-railing/1.0, plus only explicitly specified whitelist parameters. Geometry remains in the railing record; do not emit formal ObjectPlacement or IFC Representation in a Brief. The formal representation described above is a downstream encoding rule only. Freeze exact RGB for explicit named surfaces when the user supplies it; qualitative colour is not a precise RGB measurement. Do not label delegated design decisions as verbatim user facts.

Plan constraints and their selected checks are immutable during semantic repair. Preserve an intentional open boundary; do not replace wall_layout with a full envelope or delete its checks.

Property identity and native IFC attributes
Freeze a property_sets entry only when its Pset/property identity, target IFC class and value type are valid under the IFC2X3 contract. A native attribute such as object name, predefined type or spatial interior/exterior classification is not automatically a Pset property; retain it in the supported object facts/attributes. Do not manufacture an additional property attachment for the same meaning. Qualitative requests do not authorize invented performance values, and unknown property names must not be renamed into custom properties merely to pass validation.
If extraction invented an invalid attachment and the original meaning is already represented in unchanged canonical object facts, remove only that unsupported attachment and correct semantic_review. When the user explicitly demands an unsupported Pset/property identity, preserve that request in unsupported/clarification output instead of silently deleting it or substituting a different identity. A genuinely requested valid property must retain its value, identity and scope.


Visible stair appearance (Brief 2.8): IfcStair is an assembly, while IfcStairFlight carries the stepped Body. Put requested visible stair color/transparency on the flight identities, not on IfcStair. Keep material assignments on their explicitly requested objects. Use existing flight_ids when given; otherwise the existing identity rule replaces the first stair- prefix with stair-flight-, or appends -flight to a parent without that prefix. Do not rename the stair or change flight geometry. When correcting a misplaced whole-stair appearance, preserve every requested channel and scope on each declared flight; never erase the color requirement.


Material lists (Design Brief 2.9 / BIM JSON 2.6)
An explicit collection of material names on one object is supported as material_list. Brief semantic_requirements use material: {"kind":"material_list","materials":[{"name":"Steel"},{"name":"Wood"}]}. The BIM JSON entity uses materials: [{"kind":"material_list","materials":[{"name":"Steel"},{"name":"Wood"}]}]. Preserve every supplied name, order and repeated name. This is one association containing a list, not layers and not a mapping of names to parts. Do not invent thickness, layer order, frame/panel membership, or performance. Lists must be nonempty; every item contains only a nonempty name. Empty or unknown values require clarification/Draft. Do not replace an explicit list by single_material, a concatenated name, or material_layer_set_usage. IfcWallStandardCase cannot receive a list; use the explicitly requested supported occurrence role or report the mismatch, never silently change class. Supported ordinary occurrences and applicable Type/Style objects accept a list. Reopened semantic checks must preserve the exact list.


Parameterized components (Design Brief 2.9 / BIM JSON 2.6)
Preserve explicit semantic_requirements[].component_geometry and semantic_review.component_geometry. Parts belong to a single IfcDoor/IfcWindow occurrence; do not make them independent products or replace them with basic_filling. Use the component_geometry grammar: rectangle/circle/closed polygon with holes, straight extrusion, rigid placements, repetition, per-part RGB/transparency. Type is optional and is not a geometry fallback. Unsupported BRep, curves, meshes, missing dimensions or conflicting requirements require human clarification/Draft; do not approximate. Keep nominal width/height independent of protruding handles or frames. Preserve the product, part, and solid coordinate frames. installation=standalone is valid only when the description explicitly requests no host/opening; otherwise retain hosted obligations.

Component-specific display is carried inside component_geometry.parts[].appearance and reviewed by semantic_review.component_geometry. Do not manufacture a separate whole-element appearance requirement, basic-template part_appearance or template requirement for it. The appearance review is specified only when those separate appearance fields are actually requested.
For explicitly standalone products preserve installation=standalone, their identity and storey in known_facts.doors/windows; do not infer an opening/host. For hosted products preserve installation=hosted and the supplied host/opening relationship. Keep product world placement separate from part-local placement and extrusion-local position. Never infer missing placements from an overall bounding box.
