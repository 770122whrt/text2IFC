"""Deterministic support for the versioned IFC2Text outline/section/merge pipeline."""

from __future__ import annotations

from typing import Any


def build_fact_index(facts: dict[str, Any]) -> dict[str, Any]:
    """Project machine facts to prompt-safe local references.

    Source IFC identity and file paths stay outside the writing model context.  The
    index uses the stable local labels produced by ``extract_building_facts``.
    """
    records: list[dict[str, Any]] = []
    records.append(
        {
            "fact_ref": "building",
            "kind": "building",
            "storey": None,
            "name": facts.get("building", {}).get("building_name"),
            "project_name": facts.get("building", {}).get("project_name"),
            "storey_count": facts.get("building", {}).get("storey_count"),
        }
    )
    for storey in facts.get("storeys", []):
        storey_ref = str(storey["label"])
        records.append(
            {
                "fact_ref": storey_ref,
                "kind": "storey",
                "storey": storey_ref,
                "name": storey.get("name"),
                "elevation_mm": storey.get("elevation_mm"),
            }
        )
        for category, kind in (
            ("spaces", "ifc_space"),
            ("derived_spaces", "derived_enclosed_region"),
            ("walls", "wall"),
            ("openings", "opening"),
            ("doors", "door"),
            ("windows", "window"),
            ("stairs", "stair"),
        ):
            for item in storey.get(category, []):
                record = {
                    key: value
                    for key, value in item.items()
                    if key not in {"source_global_id", "host_global_id", "opening_global_id", "filling_global_id"}
                }
                record["fact_ref"] = str(item["label"])
                record["kind"] = kind
                record["storey"] = storey_ref
                records.append(record)
    issues = [
        {
            "issue_ref": f"issue-{index:03d}",
            **{key: value for key, value in issue.items() if key not in {"source_global_id", "source_path"}},
        }
        for index, issue in enumerate(facts.get("issues", []), 1)
    ]
    return {
        "schema_version": "text2ifc/ifc2text-fact-index/0.1",
        "records": records,
        "issues": issues,
    }


def assemble_sectioned_description(
    *,
    outline: dict[str, Any],
    section_results: list[dict[str, Any]],
    merge_result: dict[str, Any],
) -> str:
    """Assemble accepted section bodies without allowing the merge stage to rewrite them."""
    planned = {section["section_id"] for section in outline["sections"]}
    by_id = {section["section_id"]: section for section in section_results}
    order = list(merge_result["section_order"])
    if len(order) != len(set(order)):
        raise ValueError("IFC2TEXT_MERGE_DUPLICATE_SECTION")
    if not set(order).issubset(planned):
        raise ValueError("IFC2TEXT_MERGE_UNKNOWN_SECTION")
    if not set(order).issubset(by_id):
        raise ValueError("IFC2TEXT_MERGE_MISSING_SECTION_RESULT")
    blocked = set(merge_result.get("blocked_sections", []))
    if blocked.difference(planned):
        raise ValueError("IFC2TEXT_MERGE_UNKNOWN_BLOCKED_SECTION")
    if blocked.intersection(order):
        raise ValueError("IFC2TEXT_MERGE_BLOCKED_SECTION_ORDERED")
    if planned != set(order).union(blocked):
        raise ValueError("IFC2TEXT_MERGE_UNACCOUNTED_SECTION")

    for section_id in order:
        result = by_id[section_id]
        if result.get("omitted_required_fact_refs"):
            raise ValueError(f"IFC2TEXT_SECTION_REQUIRED_FACT_OMITTED:{section_id}")

    transitions = {
        item["before_section_id"]: item["text"].strip()
        for item in merge_result.get("transition_text", [])
        if item.get("text", "").strip()
    }
    unknown_transitions = set(transitions).difference(order)
    if unknown_transitions:
        raise ValueError("IFC2TEXT_MERGE_UNKNOWN_TRANSITION_TARGET")

    chunks: list[str] = []
    for section_id in order:
        transition = transitions.get(section_id)
        if transition:
            chunks.append(transition)
        body = str(by_id[section_id]["text"]).strip()
        if body:
            chunks.append(body)
    limitations = [str(value).strip() for value in merge_result.get("limitations", []) if str(value).strip()]
    if limitations:
        chunks.append("已知限制：" + "；".join(limitations) + "。")
    return "\n\n".join(chunks).strip() + "\n"
