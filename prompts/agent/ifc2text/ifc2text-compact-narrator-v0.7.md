Write a short Chinese architectural reading guide using only FACT_SUMMARY.
The document is assembled in this order: building overview, floor records, spaces,
component placement, then a deterministic materials section. Exact dimensions,
wall outlines and material assignments are inserted by the program, not by you.

FACT_SUMMARY:
{{FACT_SUMMARY}}

OUTPUT_SCHEMA:
{{OUTPUT_SCHEMA}}

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
