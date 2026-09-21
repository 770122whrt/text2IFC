Write a short Chinese architectural reading guide using only FACT_SUMMARY.
The document is assembled in this order: building overview, floor records, spaces,
component placement, then a deterministic materials section. Exact dimensions,
wall outlines and material assignments are inserted by the program, not by you.

FACT_SUMMARY:
{"extraction_issues_present": true, "material_descriptions": ["直接层序：默认墙:240.0；AXIS2,NEGATIVE,偏移120.0", "直接层序：默认墙:90.0；AXIS2,NEGATIVE,偏移45.0", "直接层序：默认墙:210.0；AXIS2,NEGATIVE,偏移105.0", "直接层序：默认墙:170.0；AXIS2,NEGATIVE,偏移85.0", "直接层序：默认墙:110.0；AXIS2,NEGATIVE,偏移55.0", "直接层序：默认墙:140.0；AXIS2,NEGATIVE,偏移70.0", "直接层序：默认墙:120.0；AXIS2,NEGATIVE,偏移60.0", "直接层序：默认墙:200.0；AXIS2,NEGATIVE,偏移100.0", "直接材料列表（非分层）：金属漆_冷灰、木材", "直接材料列表（非分层）：抛光不锈钢、玻璃、白油漆", "直接：金属漆_冷灰", "直接层序： <Unnamed>:300.0；AXIS3,POSITIVE,偏移0.0"], "not_described_classes": {}, "storeys": [{"boundary_relation_confirmed": false, "counts": {"coverings": 0, "doors": 7, "openings": 15, "slabs": 1, "spaces": 5, "stairs": 0, "walls": 34, "windows": 3}, "derived_region_count": 0, "id": "S01", "name": "地板标高", "space_evidence_state": "explicit_only", "space_observation": "本层有源显式空间记录，没有几何围合候选记录。"}, {"boundary_relation_confirmed": false, "counts": {"coverings": 0, "doors": 0, "openings": 0, "slabs": 0, "spaces": 0, "stairs": 0, "walls": 0, "windows": 0}, "derived_region_count": 0, "id": "S02", "name": "标高 3", "space_evidence_state": "neither", "space_observation": "本次没有显式空间记录，也未形成几何围合候选；直接描述构件。"}, {"boundary_relation_confirmed": false, "counts": {"coverings": 1, "doors": 0, "openings": 0, "slabs": 0, "spaces": 0, "stairs": 0, "walls": 0, "windows": 0}, "derived_region_count": 0, "id": "S03", "name": "天花板标高", "space_evidence_state": "neither", "space_observation": "本次没有显式空间记录，也未形成几何围合候选；直接描述构件。"}]}

OUTPUT_SCHEMA:
{"$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": {"overview": {"maxLength": 350, "minLength": 1, "type": "string"}, "storey_notes": {"items": false, "maxItems": 3, "minItems": 3, "prefixItems": [{"additionalProperties": false, "properties": {"storey": {"const": "S01"}, "text": {"maxLength": 200, "type": "string"}}, "required": ["storey", "text"], "type": "object"}, {"additionalProperties": false, "properties": {"storey": {"const": "S02"}, "text": {"maxLength": 200, "type": "string"}}, "required": ["storey", "text"], "type": "object"}, {"additionalProperties": false, "properties": {"storey": {"const": "S03"}, "text": {"maxLength": 200, "type": "string"}}, "required": ["storey", "text"], "type": "object"}], "type": "array"}}, "required": ["overview", "storey_notes"], "type": "object"}

Return only JSON matching OUTPUT_SCHEMA. Keep overview under 140 Chinese characters
and each storey note under 70 Chinese characters. Copy storey IDs and their order
exactly, never substituting their display names.

For each floor, use its explicit space_observation and space_evidence_state:
- explicit_only: source space records exist; no derived candidates are recorded.
- candidates_only: geometric candidates exist, not verified functional rooms.
- neither: neither exists; describe recorded components, without inventing rooms.
- explicit_and_candidates: distinguish the two sources.
Unconfirmed boundary associations do not erase an explicit space record.

Storey notes describe ONLY space state and component categories present in counts.
Do NOT discuss materials, material uncertainty, material names, finishes or layers
in storey_notes. A dedicated deterministic section already supplies that information;
a global materials list cannot justify a statement about any particular floor.
The overview may state that materials follow component placement, but may not make
claims about the material content of the building.

Do not infer occupancy, north, number of usable floors, load-bearing function,
walkability or room-to-wall connections. Do not reinterpret recording conventions
as structural defects. Do not mention algorithms, JSON, models or evaluation.
No GUIDs, file paths, invented measurements, or claims of complete correctness.
